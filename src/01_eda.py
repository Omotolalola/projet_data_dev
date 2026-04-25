"""
notebooks/01_eda.py
-------------------
Analyse exploratoire des données Airbnb Paris.
Peut être exécuté directement :  python notebooks/01_eda.py
Ou converti en notebook :        jupytext --to notebook notebooks/01_eda.py
"""

# %%
import sys
from pathlib import Path

# Ajouter la racine du projet au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import DataLoader
from src.evaluator import Evaluator

# %%
# ==========================================================
# 1. Chargement des données brutes
# ==========================================================
loader = DataLoader("data/airbnb_paris.csv")
df = loader.load()

print("\n── Aperçu des données brutes ──")
print(df.head(3).to_string())

print("\n── Types de colonnes ──")
print(df.dtypes)

# %%
# ==========================================================
# 2. Rapport sur les valeurs manquantes
# ==========================================================
report = loader.missing_report()
print("\n── Valeurs manquantes ──")
print(report.to_string(index=False))

# %%
# ==========================================================
# 3. Statistiques descriptives
# ==========================================================
print("\n── Statistiques descriptives (numériques) ──")
print(df[["price_eur", "rating", "nb_reviews"]].describe().round(2))

print("\n── Répartition room_type ──")
print(df["room_type"].value_counts())

print("\n── Répartition host_type ──")
print(df["host_type"].value_counts(dropna=False))

print(f"\n── Nouvelles annonces (sans avis) : {df['is_new_listing'].sum()} / {len(df)} ──")

# %%
# ==========================================================
# 4. Génération de tous les graphiques EDA
# ==========================================================
ev = Evaluator(output_dir="notebooks")
ev.plot_eda(df, report)

print("\n✓ EDA terminée — graphiques disponibles dans notebooks/")
