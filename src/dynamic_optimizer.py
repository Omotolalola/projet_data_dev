"""
src/dynamic_optimizer.py
------------------------
Programmation dynamique pour un problème de planning de type knapsack :
sélectionner les annonces/tâches maximisant une valeur totale sous
contrainte de durée disponible.

Chaque item doit contenir au minimum :
    - id
    - value
    - duration_hours

La classe reconstruit la solution optimale et expose quelques indicateurs.
"""

from __future__ import annotations

import logging
from math import ceil

logger = logging.getLogger(__name__)


class KnapsackPlanner:
    """
    Planificateur par programmation dynamique (0/1 knapsack).

    Parameters
    ----------
    capacity_hours : float
        Horizon total disponible, par exemple 8.0 heures.
    time_unit_minutes : int
        Granularité temporelle utilisée pour discrétiser les durées.
        Exemple : 30 => une durée de 1h devient 2 unités.
    """

    def __init__(self, capacity_hours: float, time_unit_minutes: int = 30):
        if capacity_hours <= 0:
            raise ValueError("capacity_hours doit être > 0.")
        if time_unit_minutes <= 0:
            raise ValueError("time_unit_minutes doit être > 0.")

        self.capacity_hours = capacity_hours
        self.time_unit_minutes = time_unit_minutes
        self.capacity_units = self._hours_to_units(capacity_hours)

        self.items_: list[dict] = []
        self.dp_table_: list[list[float]] | None = None
        self.selected_items_: list[dict] = []
        self.total_value_: float = 0.0
        self.used_hours_: float = 0.0

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def solve(self, items: list[dict]) -> dict:
        """
        Résout le problème de knapsack et retourne la solution optimale.

        Parameters
        ----------
        items : list[dict]
            Chaque dict doit contenir :
                - id
                - value
                - duration_hours

        Returns
        -------
        dict
            {
                "selected_items": [...],
                "total_value": ...,
                "used_hours": ...,
                "capacity_hours": ...,
                "occupancy_rate": ...
            }
        """
        if not items:
            raise ValueError("La liste d'items est vide.")

        prepared = self._prepare_items(items)
        n = len(prepared)
        W = self.capacity_units

        dp = [[0.0 for _ in range(W + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            item = prepared[i - 1]
            weight = item["duration_units"]
            value = item["value"]

            for w in range(W + 1):
                if weight <= w:
                    dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - weight] + value)
                else:
                    dp[i][w] = dp[i - 1][w]

        selected = self._reconstruct_solution(prepared, dp)
        total_value = sum(item["value"] for item in selected)
        used_units = sum(item["duration_units"] for item in selected)
        used_hours = used_units * self.time_unit_minutes / 60

        self.items_ = prepared
        self.dp_table_ = dp
        self.selected_items_ = selected
        self.total_value_ = total_value
        self.used_hours_ = used_hours

        result = {
            "selected_items": selected,
            "total_value": total_value,
            "used_hours": used_hours,
            "capacity_hours": self.capacity_hours,
            "occupancy_rate": used_hours / self.capacity_hours if self.capacity_hours else 0.0,
        }

        logger.info(
            "DP terminée | items=%d | sélectionnés=%d | valeur=%.2f | heures=%.2f/%.2f",
            len(items),
            len(selected),
            total_value,
            used_hours,
            self.capacity_hours,
        )
        return result

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _prepare_items(self, items: list[dict]) -> list[dict]:
        prepared = []

        for raw in items:
            if "id" not in raw:
                raise KeyError("Chaque item doit contenir une clé 'id'.")
            if "value" not in raw:
                raise KeyError("Chaque item doit contenir une clé 'value'.")
            if "duration_hours" not in raw:
                raise KeyError("Chaque item doit contenir une clé 'duration_hours'.")

            duration_hours = float(raw["duration_hours"])
            value = float(raw["value"])

            if duration_hours <= 0:
                continue
            if value < 0:
                continue

            item = dict(raw)
            item["duration_hours"] = duration_hours
            item["value"] = value
            item["duration_units"] = self._hours_to_units(duration_hours)
            prepared.append(item)

        if not prepared:
            raise ValueError("Aucun item valide après préparation.")

        return prepared

    def _reconstruct_solution(
        self,
        items: list[dict],
        dp: list[list[float]],
    ) -> list[dict]:
        selected = []
        i = len(items)
        w = self.capacity_units

        while i > 0 and w >= 0:
            if abs(dp[i][w] - dp[i - 1][w]) > 1e-9:
                item = items[i - 1]
                selected.append(item)
                w -= item["duration_units"]
            i -= 1

        selected.reverse()
        return selected

    def _hours_to_units(self, hours: float) -> int:
        minutes = hours * 60
        return max(1, int(ceil(minutes / self.time_unit_minutes)))
