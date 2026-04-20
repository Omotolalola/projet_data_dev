"""
cleaner.py
----------
Classe AirbnbCleaner : transformations et nettoyage des champs bruts.

Responsabilité unique : convertir des chaînes brutes issues de l'API
en valeurs typées (float, int, str nettoyée) et extraire des
sous-informations (note numérique, nb d'avis, prix numérique).

Aucun appel réseau ici, aucune logique de parsing JSON de l'API.
"""

import re
import logging

logger = logging.getLogger(__name__)


class AirbnbCleaner:
    """
    Nettoie et normalise les champs bruts issus du parser.

    Méthodes publiques
    ------------------
    clean_text(text)             → str | None
    clean_price(price_raw)       → str | None   (ex: "279 €")
    to_float_price(price_str)    → float | None (ex: 279.0)
    to_float_rating(rating_str)  → float | None (ex: 4.95)
    to_int_reviews(rating_str)   → int | None   (ex: 131)
    is_new_listing(rating_str)   → bool
    split_title(title)           → (room_type, city)
    """

    # Séparateurs utilisés par Airbnb dans le champ 'title'
    # ex: "Appartement ⋅ Paris", "Hébergement · Ivry-sur-Seine"
    TITLE_SEPARATORS = ["⋅", "·", "—", " - "]

    # ── Méthodes de nettoyage de base ─────────────────────────────────────────

    def clean_text(self, text) -> str | None:
        """Supprime les espaces superflus ; retourne None si vide."""
        if not text:
            return None
        cleaned = str(text).strip()
        return cleaned if cleaned else None

    def clean_price(self, price_raw) -> str | None:
        """
        Conserve uniquement les chiffres, espaces, virgules, points et €.
        Entrée : "279 €"  → Sortie : "279 €"
        Entrée : None     → Sortie : None
        """
        if not price_raw:
            return None
        cleaned = re.sub(r"[^\d\s,\.€]", "", str(price_raw)).strip()
        return cleaned if cleaned else None

    # ── Conversions numériques ─────────────────────────────────────────────────

    def to_float_price(self, price_str) -> float | None:
        """
        Extrait le nombre depuis une chaîne prix nettoyée.
        "279 €" → 279.0  |  None → None
        """
        if not price_str:
            return None
        digits = re.sub(r"[^\d,\.]", "", str(price_str)).replace(",", ".")
        try:
            return float(digits)
        except ValueError:
            logger.debug("to_float_price : impossible de convertir '%s'", price_str)
            return None

    def to_float_rating(self, rating_str) -> float | None:
        """
        Extrait la note numérique depuis la chaîne localisée.
        "4,95 (131)" → 4.95  |  "Nouveau" → None
        """
        if not rating_str or self.is_new_listing(rating_str):
            return None
        match = re.search(r"(\d+[,\.]\d+)", str(rating_str))
        if match:
            return float(match.group(1).replace(",", "."))
        logger.debug("to_float_rating : pattern non trouvé dans '%s'", rating_str)
        return None

    def to_int_reviews(self, rating_str) -> int | None:
        """
        Extrait le nombre d'avis depuis la chaîne localisée.
        "4,95 (131)" → 131  |  "Nouveau" → None
        """
        if not rating_str:
            return None
        match = re.search(r"\((\d+)\)", str(rating_str))
        if match:
            return int(match.group(1))
        return None

    # ── Logique métier ─────────────────────────────────────────────────────────

    def is_new_listing(self, rating_str) -> bool:
        """Retourne True si l'annonce est trop récente pour avoir des avis."""
        if not rating_str:
            return False
        return str(rating_str).strip().lower() == "nouveau"

    def split_title(self, title: str) -> tuple[str | None, str | None]:
        """
        Décompose le champ 'title' en (room_type, city).

        Exemples :
            "Appartement ⋅ Paris"          → ("Appartement", "Paris")
            "Hébergement · Ivry-sur-Seine"  → ("Hébergement", "Ivry-sur-Seine")
            "Studio sans séparateur"        → ("Studio sans séparateur", None)
        """
        if not title:
            return None, None

        for sep in self.TITLE_SEPARATORS:
            if sep in title:
                parts = [p.strip() for p in title.split(sep, 1)]
                room_type = parts[0] if parts[0] else None
                city = parts[1] if len(parts) > 1 and parts[1] else None
                return room_type, city

        # Aucun séparateur trouvé : on considère tout comme room_type
        return title.strip() or None, None
