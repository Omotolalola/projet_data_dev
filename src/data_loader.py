"""
src/data_loader.py
Responsabilité : chargement brut du fichier CSV Airbnb,
validation du schéma et rapport initial sur la qualité des données.
"""

import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class DataLoader:
    """Charge le fichier CSV Airbnb et expose un DataFrame brut validé."""

    EXPECTED_COLUMNS = {
        "id": "object",
        "name": "object",
        "city": "object",
        "room_type": "object",
        "host_type": "object",
        "badges": "object",
        "price_str": "object",
        "price_eur": "float64",
        "rating_str": "object",
        "rating": "float64",
        "nb_reviews": "float64",
        "is_new_listing": "bool",
        "person_capacity": "float64",
        "latitude": "float64",
        "longitude": "float64",
    }

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def load(self) -> pd.DataFrame:
        """Charge le CSV, valide le schéma et renvoie le DataFrame brut."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"Fichier introuvable : {self.filepath}")

        logger.info("Chargement de %s …", self.filepath)
        self._df = pd.read_csv(self.filepath, low_memory=False)
        logger.info("  → %d lignes, %d colonnes", *self._df.shape)

        self._validate_schema()
        return self._df.copy()

    def missing_report(self) -> pd.DataFrame:
        """Retourne un DataFrame résumant les valeurs manquantes par colonne."""
        if self._df is None:
            raise RuntimeError("Appelez load() avant missing_report().")

        total = len(self._df)
        missing = self._df.isnull().sum()
        report = pd.DataFrame(
            {
                "colonne": missing.index,
                "nb_manquants": missing.values,
                "pct_manquants": (missing.values / total * 100).round(1),
            }
        ).sort_values("pct_manquants", ascending=False)
        return report.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _validate_schema(self) -> None:
        missing_cols = set(self.EXPECTED_COLUMNS) - set(self._df.columns)
        if missing_cols:
            logger.warning("Colonnes manquantes dans le CSV : %s", missing_cols)
        else:
            logger.info("  → Schéma OK (toutes les colonnes attendues sont présentes)")
