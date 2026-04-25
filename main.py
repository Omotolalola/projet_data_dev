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
    6. Optimisation DP → sélection optimale d'annonces
    7. Planning    → outputs/planning_optimal.csv

Usage
-----
    python main.py
    python main.py --skip-scraping
    python main.py --skip-scraping --skip-eda
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.scraper import AirbnbScraper
from src.storage import AirbnbStorage
from src.data_loader import DataLoader
from src.data_processor import DataProcessor
from src.regression import LinearRegressionScratch
from src.evaluator import Evaluator
from src.dynamic_optimizer import KnapsackPlanner
from src.planning import PlanningBuilder

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CSV_PATH = "data/scraped/airbnb_paris.csv"
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# UTILITAIRES MÉTIER
# ==============================================================================

def estimate_distance_km(latitude: float, longitude: float) -> float:
    """Distance haversine entre une annonce et le centre de Paris."""
    paris_lat = 48.8566
    paris_lon = 2.3522
    R = 6371.0

    lat1 = np.radians(latitude)
    lon1 = np.radians(longitude)
    lat2 = np.radians(paris_lat)
    lon2 = np.radians(paris_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(R * 2 * np.arcsin(np.sqrt(a)))


def build_business_items(df_clean: pd.DataFrame, predicted_prices: np.ndarray) -> list[dict]:
    """
    Transforme les annonces Airbnb en items utilisables par la DP.

    Hypothèse métier simple :
    - value = prix prédit par la régression
    - duration_hours = temps estimé pour traiter/visiter/gérer l'annonce
      selon distance + type de logement
    """
    room_duration_bonus = {
        "Logement entier": 0.7,
        "Chambre privée": 0.3,
        "Chambre partagée": 0.2,
        "Autre": 0.5,
    }

    items = []

    for row, pred_price in zip(df_clean.itertuples(index=False), predicted_prices):
        distance_km = estimate_distance_km(row.latitude, row.longitude)
        room_bonus = room_duration_bonus.get(getattr(row, "room_type", None), 0.4)

        duration_hours = 1.0 + (distance_km * 0.12) + room_bonus

        items.append(
            {
                "id": getattr(row, "id", None),
                "name": getattr(row, "name", None),
                "city": getattr(row, "city", None),
                "room_type": getattr(row, "room_type", None),
                "predicted_price": float(pred_price),
                "value": float(pred_price),
                "duration_hours": round(duration_hours, 2),
                "distance_km": round(distance_km, 2),
            }
        )

    return items


# ==============================================================================
# ÉTAPE 1 — SCRAPING
# ==============================================================================

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


# ==============================================================================
# ÉTAPES 2-4 — CHARGEMENT / FEATURE ENGINEERING / EDA
# ==============================================================================

def run_preprocessing(csv_path: str, run_eda_flag: bool = True):
    """
    Étapes 2-4 — chargement, nettoyage, features, EDA éventuelle.

    Retourne :
        df_raw
        df_clean
        df_feat
        X
        y
        evaluator
    """
    logger.info("── Chargement des données ──")
    loader = DataLoader(csv_path)
    df_raw = loader.load()
    missing_report = loader.missing_report()
    logger.info("\n%s", missing_report.to_string(index=False))

    logger.info("── Nettoyage & ingénierie des features ──")
    processor = DataProcessor(df_raw)
    df_clean = processor.clean()
    df_feat = processor.build_features()

    X, y = processor.get_Xy(df_feat, target="log_price")
    logger.info("Jeu prêt → X%s | y%s", X.shape, y.shape)

    evaluator = Evaluator(output_dir="notebooks")

    if run_eda_flag:
        logger.info("── Génération des graphiques EDA ──")
        evaluator.plot_eda(df_raw, missing_report)

    return df_raw, df_clean, df_feat, X, y, evaluator


# ==============================================================================
# ÉTAPE 5 — RÉGRESSION
# ==============================================================================

def run_regression(
    X: np.ndarray,
    y: np.ndarray,
    evaluator: Evaluator,
):
    """
    Étape 5 — split, normalisation, entraînement from scratch, évaluation.

    Retourne :
        model
        scaler
        metrics
    """
    logger.info("── Régression linéaire from scratch ──")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info("Split → Train %s | Test %s", X_train.shape, X_test.shape)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    model = LinearRegressionScratch(
        learning_rate=0.05,
        n_iterations=2000,
        verbose=200,
    )
    model.fit(X_train, y_train)

    logger.info("\n=== Métriques sur le jeu de TEST ===")
    metrics = model.evaluate(X_test, y_test)
    for k, v in metrics.items():
        logger.info("  %s = %.4f", k.upper(), v)

    y_pred = model.predict(X_test)
    mae_eur = np.mean(np.abs(np.exp(y_test) - np.exp(y_pred)))
    logger.info("  MAE en euros (espace original) : %.0f €", mae_eur)

    evaluator.plot_regression_results(y_test, y_pred, model.loss_history)

    return model, scaler, metrics


# ==============================================================================
# ÉTAPES 6-7 — OPTIMISATION + PLANNING
# ==============================================================================

def run_optimization_and_planning(
    model: LinearRegressionScratch,
    scaler: StandardScaler,
    X: np.ndarray,
    df_clean: pd.DataFrame,
) -> None:
    """
    Étapes 6-7 :
    - prédire le prix sur toutes les annonces
    - transformer les annonces en items métier
    - résoudre un knapsack planning
    - construire et exporter un planning concret
    """
    logger.info("── Optimisation par programmation dynamique ──")

    X_scaled = scaler.transform(X)
    y_pred_log = model.predict(X_scaled)
    y_pred_eur = np.exp(y_pred_log)

    items = build_business_items(df_clean.reset_index(drop=True), y_pred_eur)

    planner = KnapsackPlanner(capacity_hours=8.0, time_unit_minutes=30)
    result = planner.solve(items)

    selected_items = result["selected_items"]

    logger.info("\n=== Résultat optimisation ===")
    logger.info("  Tâches retenues       : %d", len(selected_items))
    logger.info("  Valeur totale estimée : %.2f €", result["total_value"])
    logger.info("  Temps utilisé         : %.2f / %.2f h",
                result["used_hours"], result["capacity_hours"])
    logger.info("  Taux d'occupation     : %.1f %%", result["occupancy_rate"] * 100)

    logger.info("── Construction du planning ──")
    planning_builder = PlanningBuilder(day_label="Jour 1")
    schedule_df = planning_builder.build_schedule(
        selected_items,
        start_hour=9,
        start_minute=0,
    )

    planning_path = planning_builder.export_csv(
        schedule_df,
        OUTPUT_DIR / "planning_optimal.csv",
    )

    selected_df = pd.DataFrame(selected_items)
    selected_path = OUTPUT_DIR / "selected_items.csv"
    selected_df.to_csv(selected_path, index=False, encoding="utf-8-sig")

    summary_df = pd.DataFrame([
        {
            "selected_tasks": len(selected_items),
            "total_value_eur": round(result["total_value"], 2),
            "used_hours": round(result["used_hours"], 2),
            "capacity_hours": result["capacity_hours"],
            "occupancy_rate": round(result["occupancy_rate"], 4),
        }
    ])
    summary_path = OUTPUT_DIR / "optimization_summary.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    logger.info("Planning exporté       → %s", planning_path.resolve())
    logger.info("Items retenus exportés → %s", selected_path.resolve())
    logger.info("Résumé optimisation    → %s", summary_path.resolve())

    print("\n── Planning optimal ──")
    if schedule_df.empty:
        print("Aucune tâche sélectionnée.")
    else:
        print(schedule_df.to_string(index=False))


# ==============================================================================
# MAIN
# ==============================================================================

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

    df_raw, df_clean, df_feat, X, y, evaluator = run_preprocessing(
        CSV_PATH,
        run_eda_flag=not args.skip_eda,
    )

    model, scaler, metrics = run_regression(X, y, evaluator)

    run_optimization_and_planning(
        model=model,
        scaler=scaler,
        X=X,
        df_clean=df_clean,
    )


if __name__ == "__main__":
    main()