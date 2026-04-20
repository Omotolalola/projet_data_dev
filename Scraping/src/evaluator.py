"""
src/evaluator.py
Responsabilité : visualisations EDA et évaluation du modèle.

Usage EDA (avant modélisation) :
    from src.data_loader import DataLoader
    from src.evaluator import Evaluator

    loader = DataLoader("data/airbnb_paris.csv")
    df     = loader.load()
    report = loader.missing_report()

    ev = Evaluator()
    ev.plot_eda(df, report)

Usage évaluation (après entraînement) :
    ev.plot_regression_results(y_test, y_pred, history)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ------------------------------------------------------------------
# Palette cohérente avec le projet
# ------------------------------------------------------------------
COLORS = {
    "blue":   "#378ADD",
    "teal":   "#1D9E75",
    "coral":  "#D85A30",
    "amber":  "#BA7517",
    "purple": "#7F77DD",
    "gray":   "#888780",
    "green":  "#639922",
    "pink":   "#D4537E",
    "red":    "#E24B4A",
}
PALETTE = list(COLORS.values())
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
})


class Evaluator:
    """Produit les graphiques EDA et les métriques d'évaluation du modèle."""

    def __init__(self, output_dir: str = "notebooks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ==================================================================
    # EDA
    # ==================================================================

    def plot_eda(self, df: pd.DataFrame, missing_report: pd.DataFrame) -> None:
        """Génère et sauvegarde l'ensemble des graphiques d'exploration."""
        self._plot_missing(missing_report)
        self._plot_price_distribution(df)
        self._plot_room_type(df)
        self._plot_host_type(df)
        self._plot_rating_distribution(df)
        self._plot_price_by_room(df)
        self._plot_price_vs_distance(df)
        self._plot_correlation_heatmap(df)
        print(f"\n✓ Tous les graphiques EDA sauvegardés dans '{self.output_dir}/'")

    # ------------------------------------------------------------------

    def _plot_missing(self, report: pd.DataFrame) -> None:
        fig, ax = plt.subplots(figsize=(8, 4))
        relevant = report[report["nb_manquants"] > 0].copy()
        colors = [
            COLORS["red"] if p > 40 else COLORS["amber"] if p > 10 else COLORS["teal"]
            for p in relevant["pct_manquants"]
        ]
        bars = ax.barh(relevant["colonne"], relevant["pct_manquants"], color=colors)
        ax.set_xlabel("% valeurs manquantes")
        ax.set_title("Valeurs manquantes par colonne")
        ax.xaxis.set_major_formatter(mticker.PercentFormatter())
        for bar, pct in zip(bars, relevant["pct_manquants"]):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{pct:.0f}%", va="center", fontsize=10)
        plt.tight_layout()
        self._save("eda_missing_values")

    def _plot_price_distribution(self, df: pd.DataFrame) -> None:
        prices = df["price_eur"].dropna()
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # Distribution brute
        axes[0].hist(prices, bins=40, color=COLORS["blue"], edgecolor="white")
        axes[0].axvline(prices.median(), color=COLORS["coral"], lw=1.8,
                        linestyle="--", label=f"Médiane : {prices.median():.0f} €")
        axes[0].axvline(prices.mean(), color=COLORS["amber"], lw=1.8,
                        linestyle="-.", label=f"Moyenne : {prices.mean():.0f} €")
        axes[0].set_xlabel("Prix (€/nuit)")
        axes[0].set_ylabel("Nombre d'annonces")
        axes[0].set_title("Distribution des prix (brute)")
        axes[0].legend(fontsize=9)

        # Distribution log-transformée
        log_prices = np.log(prices)
        axes[1].hist(log_prices, bins=40, color=COLORS["teal"], edgecolor="white")
        axes[1].set_xlabel("log(Prix)")
        axes[1].set_ylabel("Nombre d'annonces")
        axes[1].set_title("Distribution des prix (log-transformée)")

        plt.suptitle("Distribution de la variable cible", fontsize=13, y=1.02)
        plt.tight_layout()
        self._save("eda_price_distribution")

    def _plot_room_type(self, df: pd.DataFrame) -> None:
        counts = df["room_type"].value_counts()
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.barh(counts.index, counts.values,
                       color=PALETTE[:len(counts)])
        ax.set_xlabel("Nombre d'annonces")
        ax.set_title("Répartition des types de logement")
        for bar, val in zip(bars, counts.values):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=10)
        plt.tight_layout()
        self._save("eda_room_type")

    def _plot_host_type(self, df: pd.DataFrame) -> None:
        counts = df["host_type"].value_counts(dropna=False).rename(
            index={None: "Non renseigné", np.nan: "Non renseigné"}
        )
        colors = [COLORS["teal"], COLORS["coral"], COLORS["gray"]]
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(counts.index, counts.values,
                      color=colors[:len(counts)], width=0.5)
        ax.set_ylabel("Nombre d'hôtes")
        ax.set_title("Type d'hôte : particulier vs professionnel")
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    str(bar.get_height()), ha="center", fontsize=10)
        plt.tight_layout()
        self._save("eda_host_type")

    def _plot_rating_distribution(self, df: pd.DataFrame) -> None:
        ratings = df["rating"].dropna()
        ratings = ratings[ratings > 0]   # exclure les nouvelles annonces sans note
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(ratings, bins=20, color=COLORS["green"], edgecolor="white")
        ax.set_xlabel("Note")
        ax.set_ylabel("Nombre d'annonces")
        ax.set_title("Distribution des notes (annonces avec avis)")
        ax.axvline(ratings.median(), color=COLORS["coral"], lw=1.8,
                   linestyle="--", label=f"Médiane : {ratings.median():.2f}")
        ax.legend()
        plt.tight_layout()
        self._save("eda_rating_distribution")

    def _plot_price_by_room(self, df: pd.DataFrame) -> None:
        order = (
            df.groupby("room_type")["price_eur"]
            .median()
            .sort_values(ascending=True)
        )
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(order.index, order.values,
                       color=PALETTE[:len(order)])
        ax.set_xlabel("Prix médian (€/nuit)")
        ax.set_title("Prix médian par type de logement")
        for bar, val in zip(bars, order.values):
            ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f} €", va="center", fontsize=10)
        plt.tight_layout()
        self._save("eda_price_by_room_type")

    def _plot_price_vs_distance(self, df: pd.DataFrame) -> None:
        """Scatter prix vs distance au centre (feature géographique clé)."""
        # Calcul inline de la distance (sans dépendre de DataProcessor)
        R = 6371.0
        lat2, lon2 = 48.8566, 2.3522
        phi1 = np.radians(df["latitude"])
        dphi = np.radians(lat2 - df["latitude"])
        dlambda = np.radians(lon2 - df["longitude"])
        a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(np.radians(lat2)) * np.sin(dlambda / 2)**2
        df = df.copy()
        df["dist_km"] = R * 2 * np.arcsin(np.sqrt(a))

        mask = df["price_eur"].notna()
        fig, ax = plt.subplots(figsize=(7, 5))
        sc = ax.scatter(df.loc[mask, "dist_km"], df.loc[mask, "price_eur"],
                        alpha=0.5, s=20, c=COLORS["purple"])
        ax.set_xlabel("Distance au centre de Paris (km)")
        ax.set_ylabel("Prix (€/nuit)")
        ax.set_title("Prix vs distance au centre de Paris")
        plt.tight_layout()
        self._save("eda_price_vs_distance")

    def _plot_correlation_heatmap(self, df: pd.DataFrame) -> None:
        """Heatmap de corrélation des colonnes numériques."""
        num_cols = ["price_eur", "rating", "nb_reviews", "latitude", "longitude"]
        available = [c for c in num_cols if c in df.columns]
        corr = df[available].corr()

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(corr, cmap="RdYlBu_r", vmin=-1, vmax=1)
        plt.colorbar(im, ax=ax, shrink=0.8)
        ax.set_xticks(range(len(available)))
        ax.set_yticks(range(len(available)))
        ax.set_xticklabels(available, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(available, fontsize=9)
        for i in range(len(available)):
            for j in range(len(available)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}",
                        ha="center", va="center", fontsize=9,
                        color="white" if abs(corr.iloc[i, j]) > 0.5 else "black")
        ax.set_title("Corrélations entre variables numériques")
        plt.tight_layout()
        self._save("eda_correlation_heatmap")

    # ==================================================================
    # Évaluation du modèle (après régression)
    # ==================================================================

    def plot_regression_results(
        self,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        loss_history: list[float],
    ) -> None:
        """Graphiques d'évaluation post-entraînement."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # 1. Courbe de loss
        axes[0].plot(loss_history, color=COLORS["blue"], lw=1.5)
        axes[0].set_xlabel("Époque")
        axes[0].set_ylabel("MSE")
        axes[0].set_title("Convergence de la descente de gradient")

        # 2. Valeurs réelles vs prédites
        axes[1].scatter(y_test, y_pred, alpha=0.5, s=20, color=COLORS["teal"])
        lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
        axes[1].plot(lims, lims, "r--", lw=1.5, label="Prédiction parfaite")
        axes[1].set_xlabel("Valeurs réelles")
        axes[1].set_ylabel("Valeurs prédites")
        axes[1].set_title("Réel vs Prédit")
        axes[1].legend(fontsize=9)

        # 3. Résidus
        residuals = y_test - y_pred
        axes[2].hist(residuals, bins=30, color=COLORS["coral"], edgecolor="white")
        axes[2].axvline(0, color="black", lw=1.5, linestyle="--")
        axes[2].set_xlabel("Résidu")
        axes[2].set_ylabel("Fréquence")
        axes[2].set_title("Distribution des résidus")

        plt.suptitle("Évaluation du modèle de régression", fontsize=13, y=1.02)
        plt.tight_layout()
        self._save("model_evaluation")
        print("✓ Graphiques d'évaluation sauvegardés.")

    # ------------------------------------------------------------------

    def _save(self, name: str) -> None:
        path = self.output_dir / f"{name}.png"
        plt.savefig(path, dpi=130, bbox_inches="tight")
        plt.close()
        print(f"  Sauvegardé : {path}")
