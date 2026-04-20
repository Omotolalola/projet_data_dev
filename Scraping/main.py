"""
main.py
-------
Point d'entrée du module de scraping Airbnb.

Lance la collecte complète et sauvegarde les résultats.

Usage
-----
    python main.py

Le script crée automatiquement les dossiers :
    data/scraped/   → airbnb_paris.csv
    data/raw_html/  → airbnb_raw_meta.json
"""

import logging

from src.scraper  import AirbnbScraper
from src.storage  import AirbnbStorage

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    # 1. Collecte
    scraper = AirbnbScraper(
        delay=1.5,       # secondes entre requêtes
        max_pages=None,  # None = toutes les pages disponibles
    )
    listings, pages_meta = scraper.run()

    if not listings:
        logger.error("Aucune donnée collectée — vérifiez la connexion ou le hash API.")
        return

    # 2. Sauvegarde + rapport
    storage = AirbnbStorage()
    df = storage.save(listings, pages_meta)

    # 3. Aperçu console
    logger.info("\n=== Aperçu des 5 premières lignes ===")
    logger.info("\n%s", df.head(5).to_string())


if __name__ == "__main__":
    main()
