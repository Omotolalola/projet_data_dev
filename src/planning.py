"""
src/planning.py
---------------
Construit un planning exploitable à partir des items retenus par la DP
et l'exporte en CSV.

Le planning produit des créneaux simples à la chaîne :
09:00-10:30, 10:30-12:00, etc.
"""

from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class PlanningBuilder:
    """Construit et exporte un planning tabulaire."""

    def __init__(self, day_label: str = "Jour 1"):
        self.day_label = day_label

    def build_schedule(
        self,
        selected_items: list[dict],
        start_hour: int = 9,
        start_minute: int = 0,
    ) -> pd.DataFrame:
        """
        Transforme les items sélectionnés en planning séquentiel.

        Parameters
        ----------
        selected_items : list[dict]
            Items retenus par le planificateur DP.
        start_hour : int
            Heure de début du planning.
        start_minute : int
            Minute de début du planning.

        Returns
        -------
        pd.DataFrame
            Colonnes :
            day, order, start_time, end_time, duration_hours,
            id, name, room_type, city, predicted_price, value
        """
        rows = []
        current_minutes = start_hour * 60 + start_minute

        for order, item in enumerate(selected_items, start=1):
            duration_hours = float(item["duration_hours"])
            duration_minutes = int(round(duration_hours * 60))

            start_time = self._format_minutes(current_minutes)
            end_time = self._format_minutes(current_minutes + duration_minutes)

            rows.append(
                {
                    "day": self.day_label,
                    "order": order,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_hours": round(duration_hours, 2),
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "room_type": item.get("room_type"),
                    "city": item.get("city"),
                    "predicted_price": round(float(item.get("predicted_price", 0.0)), 2),
                    "value": round(float(item.get("value", 0.0)), 2),
                    "distance_km": round(float(item.get("distance_km", 0.0)), 2),
                }
            )

            current_minutes += duration_minutes

        df = pd.DataFrame(rows)
        logger.info("Planning construit : %d tâche(s)", len(df))
        return df

    def export_csv(self, df: pd.DataFrame, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info("Planning exporté : %s", output_path.resolve())
        return output_path

    @staticmethod
    def _format_minutes(total_minutes: int) -> str:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
