"""
src/data_processor.py
Responsabilité : nettoyage, transformation et ingénierie des features
à partir du DataFrame brut fourni par DataLoader.

Pipeline recommandé :
    processor = DataProcessor(df_raw)
    df_clean  = processor.clean()
    df_feat   = processor.build_features()
    X, y      = processor.get_Xy()
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Modalités de host_type qui sont en réalité des données de lit mal parsées
_BAD_HOST_TYPES = {"2 lits", "1\xa0lit queen size", "5 lits", "1 lit"}

# Regroupement des types de logements rares
_RARE_ROOM_TYPES = {
    "Hôtel",
    "Hotel Apollinaire",
    "Appartement en résidence",
    "Chambre d'hôtel",
}


class DataProcessor:
    """Nettoie et transforme le DataFrame Airbnb en vue de la régression."""

    PRICE_CAP_PERCENTILE = 0.95   # on plafonne les outliers hauts à P95
    PARIS_LAT = 48.8566
    PARIS_LON = 2.3522

    def __init__(self, df: pd.DataFrame):
        self._raw = df.copy()
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Étape 1 – Nettoyage
    # ------------------------------------------------------------------

    def clean(self) -> pd.DataFrame:
        """
        Supprime les lignes inutilisables, corrige les types et les modalités
        aberrantes. Renvoie un DataFrame nettoyé (stocké dans self._df).
        """
        df = self._raw.copy()

        # 1. Supprimer les lignes sans prix (variable cible absente)
        before = len(df)
        df = df.dropna(subset=["price_eur"])
        logger.info("Lignes sans price_eur supprimées : %d", before - len(df))

        # 2. Supprimer person_capacity (100 % manquante)
        df = df.drop(columns=["person_capacity"], errors="ignore")

        # 3. Corriger host_type : remplacer les valeurs de lit mal parsées par NaN
        mask_bad = df["host_type"].isin(_BAD_HOST_TYPES)
        df.loc[mask_bad, "host_type"] = np.nan
        logger.info("host_type mal parsé → NaN : %d lignes", mask_bad.sum())

        # 4. Regrouper les types de logements rares
        df["room_type"] = df["room_type"].apply(
            lambda x: "Autre" if x in _RARE_ROOM_TYPES else x
        )

        # 5. Plafonner les prix à P95 (outliers hauts)
        cap = df["price_eur"].quantile(self.PRICE_CAP_PERCENTILE)
        n_capped = (df["price_eur"] > cap).sum()
        df["price_eur"] = df["price_eur"].clip(upper=cap)
        logger.info("Prix plafonnés à P95 (%.0f €) : %d lignes", cap, n_capped)

        # 6. Supprimer la colonne city (ville peu discriminante vs lat/lon)
        #    et les colonnes _str (doublons textuels)
        df = df.drop(columns=["price_str", "rating_str", "city"], errors="ignore")

        self._df = df
        logger.info("Nettoyage terminé → %d lignes, %d colonnes", *df.shape)
        return self._df.copy()

    # ------------------------------------------------------------------
    # Étape 2 – Ingénierie des features
    # ------------------------------------------------------------------

    def build_features(self) -> pd.DataFrame:
        """
        Crée les features numériques finales :
        - distance au centre de Paris
        - flag has_reviews + imputation rating / nb_reviews
        - encodage one-hot de room_type et host_type
        - log du prix (variable cible transformée)
        Renvoie un DataFrame prêt pour la modélisation.
        """
        if self._df is None:
            raise RuntimeError("Appelez clean() avant build_features().")

        df = self._df.copy()

        # --- Feature géographique ---
        df["dist_centre_km"] = self._haversine(
            df["latitude"], df["longitude"],
            self.PARIS_LAT, self.PARIS_LON,
        )

        # --- Flag nouvelles annonces (sans avis) ---
        df["has_reviews"] = (~df["is_new_listing"]).astype(int)

        # --- Imputation rating et nb_reviews ---
        # Les nouvelles annonces n'ont pas d'avis : on impute à 0
        df["rating"] = df["rating"].fillna(0.0)
        df["nb_reviews"] = df["nb_reviews"].fillna(0.0)

        # --- Variable cible log-transformée ---
        df["log_price"] = np.log(df["price_eur"])

        # --- Encodage one-hot ---
        df = pd.get_dummies(df, columns=["room_type", "host_type"], drop_first=False)

        # --- Conversion booléen → int ---
        df["is_new_listing"] = df["is_new_listing"].astype(int)

        # --- Supprimer id et name (non utiles à la régression) ---
        df = df.drop(columns=["id", "name"], errors="ignore")

        logger.info(
            "Features construites → %d colonnes disponibles", df.shape[1]
        )
        return df

    # ------------------------------------------------------------------
    # Étape 3 – Séparation X / y
    # ------------------------------------------------------------------

    def get_Xy(
        self,
        df_feat: pd.DataFrame,
        target: str = "log_price",
        drop_cols: list[str] | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Retourne (X, y) en excluant la variable cible et les colonnes
        spécifiées dans drop_cols.

        Parameters
        ----------
        df_feat   : DataFrame issu de build_features()
        target    : nom de la colonne cible (défaut : 'log_price')
        drop_cols : colonnes supplémentaires à exclure (ex. 'price_eur')
        """
        to_drop = [target, "price_eur"] + (drop_cols or [])
        X = df_feat.drop(columns=[c for c in to_drop if c in df_feat.columns])
        y = df_feat[target].values

        # Ne garder que les colonnes numériques (sécurité)
        X = X.select_dtypes(include=[np.number])

        logger.info("X : %s  |  y : %s", X.shape, y.shape)
        return X.values, y

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    @staticmethod
    def _haversine(
        lat1: pd.Series,
        lon1: pd.Series,
        lat2: float,
        lon2: float,
    ) -> pd.Series:
        """Distance haversine en kilomètres entre chaque point et (lat2, lon2)."""
        R = 6371.0
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arcsin(np.sqrt(a))
