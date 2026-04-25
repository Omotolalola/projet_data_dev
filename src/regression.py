"""
src/regression.py
-----------------
Régression linéaire implémentée from scratch.

Pas de scikit-learn pour le cœur — uniquement NumPy.
La descente de gradient est implémentée en batch (toutes les données
à chaque itération), ce qui est suffisant pour 215 observations.

Usage
-----
    from src.regression import LinearRegressionScratch

    model = LinearRegressionScratch(learning_rate=0.01, n_iterations=1000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = model.evaluate(X_test, y_test)
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


class LinearRegressionScratch:
    """
    Régression linéaire par descente de gradient batch.

    Modèle : y_hat = X @ w + b
    Coût   : MSE = (1/n) * sum((y - y_hat)²)

    Parameters
    ----------
    learning_rate : float
        Taux d'apprentissage (α). Trop grand → divergence,
        trop petit → convergence lente.
    n_iterations : int
        Nombre d'époques de descente de gradient.
    verbose : int
        Affiche la loss tous les `verbose` pas (0 = silence).
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        verbose: int = 100,
    ):
        self.learning_rate = learning_rate
        self.n_iterations  = n_iterations
        self.verbose       = verbose

        # Paramètres appris
        self.weights: np.ndarray | None = None
        self.bias:    float             = 0.0

        # Historique de la loss (pour la courbe de convergence)
        self.loss_history: list[float] = []

    # ------------------------------------------------------------------
    # Entraînement
    # ------------------------------------------------------------------

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearRegressionScratch":
        """
        Entraîne le modèle sur (X, y) par descente de gradient batch.

        Parameters
        ----------
        X : array (n_samples, n_features)   — features normalisées
        y : array (n_samples,)              — variable cible (log_price)
        """
        n_samples, n_features = X.shape

        # Initialisation des poids à zéro
        self.weights = np.zeros(n_features)
        self.bias    = 0.0
        self.loss_history = []

        for epoch in range(self.n_iterations):

            # ── Forward pass ──────────────────────────────────────────
            y_hat = self._predict_raw(X)

            # ── Coût (MSE) ────────────────────────────────────────────
            loss = self._mse(y, y_hat)
            self.loss_history.append(loss)

            # ── Gradients ─────────────────────────────────────────────
            # dL/dw = (2/n) * Xᵀ (y_hat - y)
            # dL/db = (2/n) * sum(y_hat - y)
            error     = y_hat - y
            grad_w    = (2 / n_samples) * X.T @ error
            grad_b    = (2 / n_samples) * np.sum(error)

            # ── Mise à jour ───────────────────────────────────────────
            self.weights -= self.learning_rate * grad_w
            self.bias    -= self.learning_rate * grad_b

            # ── Log ───────────────────────────────────────────────────
            if self.verbose and epoch % self.verbose == 0:
                logger.info("Époque %4d | MSE = %.6f", epoch, loss)

        logger.info("Entraînement terminé | MSE finale = %.6f", self.loss_history[-1])
        return self

    # ------------------------------------------------------------------
    # Prédiction
    # ------------------------------------------------------------------

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Retourne les prédictions pour X."""
        if self.weights is None:
            raise RuntimeError("Le modèle n'est pas entraîné. Appelez fit() d'abord.")
        return self._predict_raw(X)

    # ------------------------------------------------------------------
    # Évaluation
    # ------------------------------------------------------------------

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> dict:
        """
        Calcule MSE, RMSE, MAE et R² sur (X, y).

        Returns
        -------
        dict avec les clés : mse, rmse, mae, r2
        """
        y_pred = self.predict(X)
        n      = len(y)

        mse  = self._mse(y, y_pred)
        rmse = np.sqrt(mse)
        mae  = np.mean(np.abs(y - y_pred))

        # R² = 1 - SS_res / SS_tot
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2     = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

        metrics = {"mse": mse, "rmse": rmse, "mae": mae, "r2": r2}

        logger.info(
            "Évaluation → MSE=%.4f | RMSE=%.4f | MAE=%.4f | R²=%.4f",
            mse, rmse, mae, r2,
        )
        return metrics

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _predict_raw(self, X: np.ndarray) -> np.ndarray:
        """y_hat = X @ w + b"""
        return X @ self.weights + self.bias

    @staticmethod
    def _mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Mean Squared Error."""
        return float(np.mean((y_true - y_pred) ** 2))
