"""
scraper.py
----------
Classe AirbnbScraper : orchestre les appels HTTP, la pagination,
la déduplication et la journalisation.

Responsabilité unique : gérer le cycle de vie de la collecte
(requête → validation → délégation au parser → pagination).

Ne fait pas de nettoyage de données (→ cleaner.py)
Ne fait pas de parsing JSON (→ parser.py)
Ne fait pas de sauvegarde sur disque (→ storage.py)
"""

import json
import logging
import time
from datetime import datetime

import requests

from src.config import (
    API_URL,
    API_PARAMS,
    HEADERS,
    INITIAL_CURSOR,
    SEARCH_PARAMS,
    API_HASH,
    SCRAPER_DELAY_SECONDS,
    SCRAPER_TIMEOUT,
    SCRAPER_RETRY_WAIT,
    MAX_PAGES,
)
from src.parser import AirbnbParser

logger = logging.getLogger(__name__)


class AirbnbScraper:
    """
    Scrape toutes les pages de résultats Airbnb pour Paris.

    Paramètres du constructeur
    --------------------------
    delay     : float — délai en secondes entre chaque requête (défaut : config)
    max_pages : int | None — limite de pages ; None = toutes (défaut : config)

    Méthodes publiques
    ------------------
    run() → tuple[list[dict], list[dict]]
        Lance le scraping et retourne (listings, pages_meta).

    Attributs publics après run()
    -----------------------------
    listings   : list[dict] — annonces parsées et dédupliquées
    pages_meta : list[dict] — métadonnées de chaque page collectée
    """

    def __init__(
        self,
        delay: float = SCRAPER_DELAY_SECONDS,
        max_pages: int | None = MAX_PAGES,
    ):
        self.delay      = delay
        self.max_pages  = max_pages
        self._parser    = AirbnbParser()
        self.listings   = []
        self.pages_meta = []
        self._seen_ids  = set()

    # ── Point d'entrée public ──────────────────────────────────────────────────

    def run(self) -> tuple[list[dict], list[dict]]:
        """
        Lance le scraping complet et retourne les données collectées.

        Retourne
        --------
        listings   : list[dict] — annonces dédupliquées et normalisées
        pages_meta : list[dict] — log de chaque page (page, cursor, nb_resultats)
        """
        self.listings   = []
        self.pages_meta = []
        self._seen_ids  = set()

        cursor = INITIAL_CURSOR
        page   = 0

        logger.info("=" * 60)
        logger.info("AIRBNB SCRAPER — Paris — démarrage")
        logger.info("=" * 60)

        while True:
            page += 1

            if self.max_pages and page > self.max_pages:
                logger.info("Limite de %d pages atteinte.", self.max_pages)
                break

            logger.info("--- Page %d (cursor: %s...) ---", page, cursor[:50])

            data = self._fetch_page(cursor)
            if data is None:
                break

            results = self._extract_results(data)
            if results is None:
                break

            search_results = results.get("searchResults", [])
            logger.info("  Annonces reçues : %d", len(search_results))

            if not search_results:
                logger.info("  Aucun résultat — fin.")
                break

            self._record_page_meta(page, cursor, len(search_results))
            new_count = self._process_items(search_results)
            logger.info(
                "  Nouvelles : %d | Total cumulé : %d", new_count, len(self.listings)
            )

            next_cursor = self._parser.get_next_cursor(results)
            if not next_cursor:
                logger.info("  Fin de pagination — pas de nextPageCursor.")
                break
            if next_cursor == cursor:
                logger.warning("  Cursor identique détecté — boucle, arrêt.")
                break

            cursor = next_cursor
            time.sleep(self.delay)

        logger.info("=" * 60)
        logger.info(
            "TERMINÉ : %d annonces | %d page(s)", len(self.listings), page
        )
        logger.info("=" * 60)

        return self.listings, self.pages_meta

    # ── Méthodes privées ───────────────────────────────────────────────────────

    def _fetch_page(self, cursor: str) -> dict | None:
        """
        Envoie la requête POST pour une page donnée.
        Gère le rate-limit (429) et les erreurs réseau.

        Retourne le JSON parsé ou None en cas d'erreur bloquante.
        """
        payload = self._build_payload(cursor)

        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                params=API_PARAMS,
                json=payload,
                timeout=SCRAPER_TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Erreur réseau : %s", exc)
            return None

        logger.debug("  HTTP %d", response.status_code)

        if response.status_code == 429:
            logger.warning("  Rate limit (429) — attente %ds...", SCRAPER_RETRY_WAIT)
            time.sleep(SCRAPER_RETRY_WAIT)
            return self._fetch_page(cursor)  # une seule réessai

        if response.status_code != 200:
            logger.error(
                "  Erreur HTTP %d : %s", response.status_code, response.text[:300]
            )
            return None

        try:
            return response.json()
        except ValueError as exc:
            logger.error("  JSON invalide : %s", exc)
            return None

    def _extract_results(self, data: dict) -> dict | None:
        """
        Navigue jusqu'au nœud 'results' dans la réponse GraphQL.
        Retourne None si la structure est inattendue.
        """
        try:
            return data["data"]["presentation"]["staysSearch"]["results"]
        except (KeyError, TypeError) as exc:
            logger.error("Structure inattendue : %s", exc)
            logger.debug("Réponse brute : %s", json.dumps(data)[:600])
            return None

    def _process_items(self, search_results: list) -> int:
        """
        Itère sur les items d'une page, déduplique par id,
        délègue le parsing à AirbnbParser, et accumule dans self.listings.

        Retourne le nombre de nouvelles annonces ajoutées.
        """
        new_count = 0
        for i, item in enumerate(search_results):
            try:
                parsed = self._parser.parse_item(item)
                listing_id = parsed.get("id")

                if listing_id and listing_id in self._seen_ids:
                    continue
                if listing_id:
                    self._seen_ids.add(listing_id)

                if parsed.get("name") or parsed.get("price_str"):
                    self.listings.append(parsed)
                    new_count += 1

            except Exception as exc:  # noqa: BLE001
                logger.warning("  Item %d ignoré : %s", i, exc)

        return new_count

    def _record_page_meta(self, page: int, cursor: str, nb_results: int) -> None:
        """Enregistre les métadonnées de la page pour le rapport de collecte."""
        self.pages_meta.append({
            "page":          page,
            "date_collecte": datetime.now().isoformat(),
            "cursor":        cursor,
            "nb_resultats":  nb_results,
        })

    def _build_payload(self, cursor: str) -> dict:
        """
        Construit le corps de la requête GraphQL pour une page donnée.
        Les paramètres de recherche sont lus depuis config.SEARCH_PARAMS.
        """
        raw_params = [
            {"filterName": k, "filterValues": [v]}
            for k, v in SEARCH_PARAMS.items()
        ]

        return {
            "operationName": "StaysSearch",
            "variables": {
                "aiSearchEnabled":    False,
                "isLeanTreatment":    False,
                "staysMapSearchRequestV2": {
                    "cursor":              cursor,
                    "metadataOnly":        False,
                    "requestedPageType":   "STAYS_SEARCH",
                    "treatmentFlags": [
                        "feed_map_decouple_m11_treatment",
                        "recommended_amenities_2024_treatment_b",
                    ],
                    "rawParams": raw_params,
                },
            },
            "extensions": {
                "persistedQuery": {
                    "version":    1,
                    "sha256Hash": API_HASH,
                }
            },
        }
