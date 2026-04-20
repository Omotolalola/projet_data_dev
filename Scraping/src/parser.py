"""
parser.py
---------
Classe AirbnbParser : transforme un item JSON brut de l'API Airbnb
en dictionnaire structuré prêt à être stocké.

Responsabilité unique : naviguer dans la structure JSON de la réponse
et déléguer le nettoyage/typage à AirbnbCleaner.

Structure JSON réelle observée (vérifiée sur la réponse du 20/04/2026) :
    item['demandStayListing']['location']['coordinate']     → lat/lng
    item['demandStayListing']['description']['name'][...]   → nom
    item['title']                                           → "Type ⋅ Ville"
    item['avgRatingLocalized']                              → "4,95 (131)"
    item['structuredDisplayPrice']['primaryLine']['price']  → "279 €"
    item['structuredContent']['primaryLine'][0]['body']     → "Particulier"
    item['paymentMessages']                                 → badges
"""

import logging
from src.cleaner import AirbnbCleaner

logger = logging.getLogger(__name__)


class AirbnbParser:
    """
    Parse un item JSON brut issu de l'API Airbnb GraphQL.

    Utilise AirbnbCleaner pour toutes les transformations de valeurs.

    Méthodes publiques
    ------------------
    parse_item(item: dict) → dict
        Retourne un dictionnaire avec les champs normalisés d'une annonce.

    get_next_cursor(results: dict) → str | None
        Extrait le curseur de pagination depuis le bloc 'results'.
    """

    def __init__(self):
        self._cleaner = AirbnbCleaner()

    # ── Parsing d'un item ──────────────────────────────────────────────────────

    def parse_item(self, item: dict) -> dict:
        """
        Transforme un item brut de searchResults en dictionnaire structuré.

        Paramètre
        ---------
        item : dict — un élément de results['searchResults']

        Retourne
        --------
        dict avec les clés : id, name, city, room_type, host_type, badges,
        price_str, price_eur, rating_str, rating, nb_reviews,
        is_new_listing, person_capacity, latitude, longitude
        """
        listing = item.get("demandStayListing") or item.get("listing") or {}

        name          = self._extract_name(item, listing)
        room_type, city = self._extract_room_type_and_city(item)
        lat, lng      = self._extract_coordinates(listing)
        price_raw     = self._extract_price_raw(item)
        rating_raw    = item.get("avgRatingLocalized")
        host_type     = self._extract_host_type(item)
        badges        = self._extract_badges(item)

        # Nettoyage et typage via AirbnbCleaner
        c = self._cleaner
        price_str  = c.clean_price(price_raw)
        rating_str = c.clean_text(str(rating_raw) if rating_raw is not None else None)

        return {
            "id":             listing.get("id"),
            "name":           c.clean_text(name),
            "city":           c.clean_text(city),
            "room_type":      c.clean_text(room_type),
            "host_type":      c.clean_text(host_type),
            "badges":         c.clean_text(badges),
            "price_str":      price_str,
            "price_eur":      c.to_float_price(price_str),
            "rating_str":     rating_str,
            "rating":         c.to_float_rating(rating_str),
            "nb_reviews":     c.to_int_reviews(rating_str),
            "is_new_listing": c.is_new_listing(rating_str),
            "person_capacity":listing.get("personCapacity"),
            "latitude":       lat,
            "longitude":      lng,
        }

    # ── Pagination ─────────────────────────────────────────────────────────────

    def get_next_cursor(self, results: dict) -> str | None:
        """
        Extrait le curseur de la prochaine page.

        Dans la réponse réelle, le champ est :
            results['paginationInfo']['nextPageCursor']
        (et non 'nextCursor' comme dans les versions antérieures de l'API)
        """
        pagination_info = results.get("paginationInfo") or {}
        cursor = pagination_info.get("nextPageCursor")
        if not cursor:
            logger.debug(
                "get_next_cursor : nextPageCursor absent. paginationInfo=%s",
                pagination_info,
            )
        return cursor

    # ── Méthodes privées d'extraction ─────────────────────────────────────────

    def _extract_name(self, item: dict, listing: dict) -> str | None:
        """Cherche le nom dans plusieurs endroits possibles de la réponse."""
        return (
            (listing.get("description") or {})
                .get("name", {})
                .get("localizedStringWithTranslationPreference")
            or (item.get("nameLocalized") or {})
                .get("localizedStringWithTranslationPreference")
            or item.get("subtitle")
        )

    def _extract_room_type_and_city(self, item: dict) -> tuple[str | None, str | None]:
        """
        Décompose item['title'] en (room_type, city) via AirbnbCleaner.
        ex: "Appartement ⋅ Paris" → ("Appartement", "Paris")
        """
        title = item.get("title", "")
        return self._cleaner.split_title(title)

    def _extract_coordinates(self, listing: dict) -> tuple[float | None, float | None]:
        """Extrait (latitude, longitude) depuis listing['location']['coordinate']."""
        coord = (listing.get("location") or {}).get("coordinate") or {}
        return coord.get("latitude"), coord.get("longitude")

    def _extract_price_raw(self, item: dict) -> str | None:
        """Remonte le prix brut depuis structuredDisplayPrice."""
        sdp = item.get("structuredDisplayPrice") or {}
        return (
            (sdp.get("primaryLine") or {}).get("price")
            or (sdp.get("secondaryLine") or {}).get("price")
        )

    def _extract_host_type(self, item: dict) -> str | None:
        """
        Extrait le type d'hôte depuis structuredContent.primaryLine.
        Valeurs observées : "Particulier" / "Professionnel"
        """
        sc = item.get("structuredContent") or {}
        primary_lines = sc.get("primaryLine") or []
        if primary_lines:
            return primary_lines[0].get("body")
        return None

    def _extract_badges(self, item: dict) -> str | None:
        """
        Construit une chaîne de badges depuis paymentMessages.
        ex: "Annulation gratuite | Remise mensuelle"
        """
        msgs = item.get("paymentMessages") or []
        texts = [m.get("text", "") for m in msgs if m.get("text")]
        return " | ".join(texts) if texts else None
