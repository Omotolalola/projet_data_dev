"""
main.py
-------
Point d'entrée principal du projet Airbnb.

Enchaîne les étapes dans l'ordre :
    1. Scraping    → data/scraped/airbnb_paris.csv
    2. Chargement  & validation du CSV
    3. Nettoyage   & ingénierie des features
    4. EDA         → notebooks/eda_*.png
    5. Régression  → entraînement from scratch + évaluation

Usage
-----
    python main.py                   # pipeline complet (scraping + EDA + régression)
    python main.py --skip-scraping   # EDA + régression (CSV déjà présent)
    python main.py --skip-scraping --skip-eda   # régression uniquement
"""

import argparse
import logging

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import StandardScaler

from src.scraper        import AirbnbScraper
from src.storage        import AirbnbStorage
from src.data_loader    import DataLoader
from src.data_processor import DataProcessor
from src.regression     import LinearRegressionScratch
from src.evaluator      import Evaluator

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CSV_PATH = "data/scraped/airbnb_paris.csv"


def run_scraping() -> None:
    """Étape 1 — collecte et sauvegarde brute."""
    scraper = AirbnbScraper(
        delay=1.5,
        max_pages=None,
    )
    listings, pages_meta = scraper.run()

    if not listings:
        logger.error("Aucune donnée collectée — vérifiez la connexion ou le hash API.")
        raise RuntimeError("Scraping échoué.")

    storage = AirbnbStorage()
    df = storage.save(listings, pages_meta)
    logger.info("Scraping terminé → %d annonces sauvegardées", len(df))


def run_eda(csv_path: str) -> tuple:
    """
    Étapes 2-4 — chargement, nettoyage, feature engineering, EDA.
    Retourne (X, y, evaluator) pour la suite du pipeline.
    """

    # ── 2. Chargement ──────────────────────────────────────────────────────────
    logger.info("── Chargement des données ──")
    loader = DataLoader(csv_path)
    df_raw = loader.load()
    missing_report = loader.missing_report()
    logger.info("\n%s", missing_report.to_string(index=False))

    # ── 3. Nettoyage & features ────────────────────────────────────────────────
    logger.info("── Nettoyage & ingénierie des features ──")
    processor = DataProcessor(df_raw)
    df_clean  = processor.clean()
    df_feat   = processor.build_features()

    X, y = processor.get_Xy(df_feat, target="log_price")
    logger.info("Jeu d'entraînement prêt → X%s  y%s", X.shape, y.shape)

    # ── 4. EDA ─────────────────────────────────────────────────────────────────
    logger.info("── Génération des graphiques EDA ──")
    evaluator = Evaluator(output_dir="notebooks")
    evaluator.plot_eda(df_raw, missing_report)

    return X, y, evaluator


def run_regression(X: np.ndarray, y: np.ndarray, evaluator: Evaluator) -> None:
    """
    Étape 5 — split, normalisation, entraînement from scratch, évaluation.
    """
    logger.info("── Régression linéaire from scratch ──")

    # ── Split 80 / 20 ──────────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info("Split → Train %s | Test %s", X_train.shape, X_test.shape)

    # ── Normalisation ──────────────────────────────────────────────────────────
    # On fit le scaler UNIQUEMENT sur le train pour éviter le data leakage
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # ── Entraînement ───────────────────────────────────────────────────────────
    model = LinearRegressionScratch(
        learning_rate=0.05,
        n_iterations=2000,
        verbose=200,
    )
    model.fit(X_train, y_train)

    # ── Évaluation ─────────────────────────────────────────────────────────────
    logger.info("\n=== Métriques sur le jeu de TEST ===")
    metrics = model.evaluate(X_test, y_test)
    for k, v in metrics.items():
        logger.info("  %s = %.4f", k.upper(), v)

    # MAE ramenée en euros (espace original)
    y_pred     = model.predict(X_test)
    mae_eur    = np.mean(np.abs(np.exp(y_test) - np.exp(y_pred)))
    logger.info("  MAE en euros (espace original) : %.0f €", mae_eur)

    # ── Graphiques d'évaluation ────────────────────────────────────────────────
    evaluator.plot_regression_results(y_test, y_pred, model.loss_history)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline Airbnb Paris")
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Sauter l'étape de scraping (utilise le CSV déjà présent)",
    )
    parser.add_argument(
        "--skip-eda",
        action="store_true",
        help="Sauter la génération des graphiques EDA",
    )
    args = parser.parse_args()

    if not args.skip_scraping:
        run_scraping()

    X, y, evaluator = run_eda(CSV_PATH)

    if not args.skip_eda:
        pass  # EDA déjà faite dans run_eda, graphiques sauvegardés

    run_regression(X, y, evaluator)


if __name__ == "__main__":
    main()