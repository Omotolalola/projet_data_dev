"""
storage.py
----------
Classe AirbnbStorage : sauvegarde les données collectées sur disque
et affiche les statistiques de qualité.

Responsabilité unique : persistance (CSV, JSON) et reporting.
Aucun appel réseau, aucune transformation de données.
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd

from src.config import (
    OUTPUT_CSV,
    OUTPUT_RAW_JSON,
    SOURCE_URL,
    ROBOTS_TXT_NOTE,
)

logger = logging.getLogger(__name__)


class AirbnbStorage:
    """
    Sauvegarde les annonces Airbnb scrappées en CSV et JSON.

    Méthodes publiques
    ------------------
    save(listings, pages_meta) → pd.DataFrame
        Sauvegarde CSV + JSON et affiche les statistiques.

    print_quality_report(df)
        Affiche le taux de complétude de chaque colonne.

    print_stats(df)
        Affiche les statistiques descriptives (prix, note, villes…).
    """

    def __init__(
        self,
        csv_path:  str = OUTPUT_CSV,
        json_path: str = OUTPUT_RAW_JSON,
    ):
        self.csv_path  = csv_path
        self.json_path = json_path

    # ── Point d'entrée public ──────────────────────────────────────────────────

    def save(
        self,
        listings:    list[dict],
        pages_meta:  list[dict],
    ) -> pd.DataFrame:
        """
        Sauvegarde les données et retourne le DataFrame.

        Paramètres
        ----------
        listings   : list[dict] — annonces normalisées (sortie de AirbnbScraper)
        pages_meta : list[dict] — métadonnées de collecte (sortie de AirbnbScraper)

        Retourne
        --------
        pd.DataFrame correspondant au CSV sauvegardé.
        """
        self._create_dirs()

        df = pd.DataFrame(listings)
        self._save_csv(df)
        self._save_json_meta(listings, pages_meta)
        self.print_quality_report(df)
        self.print_stats(df)

        return df

    # ── Rapports ──────────────────────────────────────────────────────────────

    def print_quality_report(self, df: pd.DataFrame) -> None:
        """Affiche le taux de remplissage de chaque colonne (barre visuelle)."""
        total = len(df)
        if total == 0:
            logger.warning("DataFrame vide — pas de rapport qualité.")
            return

        logger.info("\n=== Complétude des colonnes ===")
        for col in df.columns:
            n   = df[col].notna().sum()
            pct = n / total * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            logger.info("  %-20s %s %4d/%d (%d%%)", col, bar, n, total, pct)

    def print_stats(self, df: pd.DataFrame) -> None:
        """Affiche les statistiques descriptives principales."""
        logger.info("\n=== Statistiques ===")

        if "price_eur" in df.columns and df["price_eur"].notna().any():
            logger.info("  Prix moyen   : %.0f €", df["price_eur"].mean())
            logger.info("  Prix médian  : %.0f €", df["price_eur"].median())
            logger.info("  Prix min/max : %.0f € / %.0f €",
                        df["price_eur"].min(), df["price_eur"].max())

        if "rating" in df.columns and df["rating"].notna().any():
            logger.info("  Note moyenne : %.2f", df["rating"].mean())

        if "city" in df.columns:
            top_cities = df["city"].value_counts().head(10)
            logger.info("\n  Top 10 villes :\n%s", top_cities.to_string())

        if "room_type" in df.columns:
            top_types = df["room_type"].value_counts().head(10)
            logger.info("\n  Types de logement :\n%s", top_types.to_string())

    # ── Méthodes privées ──────────────────────────────────────────────────────

    def _create_dirs(self) -> None:
        """Crée les dossiers de sortie si nécessaire."""
        os.makedirs(os.path.dirname(self.csv_path),  exist_ok=True)
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)

    def _save_csv(self, df: pd.DataFrame) -> None:
        """Sauvegarde le DataFrame au format CSV (UTF-8 avec BOM pour Excel)."""
        df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")
        abs_path = os.path.abspath(self.csv_path)
        logger.info("\nCSV sauvegardé : %s", abs_path)
        logger.info("Lignes : %d | Colonnes : %s", len(df), list(df.columns))

    def _save_json_meta(
        self,
        listings:   list[dict],
        pages_meta: list[dict],
    ) -> None:
        """
        Sauvegarde les métadonnées de collecte en JSON.
        (source, date, fréquence, nb résultats — pas les données brutes API)
        """
        meta = {
            "source":        SOURCE_URL,
            "date_collecte": datetime.now().isoformat(),
            "robots_txt":    ROBOTS_TXT_NOTE,
            "nb_resultats":  len(listings),
            "nb_pages":      len(pages_meta),
            "pages_meta":    pages_meta,
        }
        with open(self.json_path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)

        abs_path = os.path.abspath(self.json_path)
        logger.info("JSON méta sauvegardé : %s", abs_path)
