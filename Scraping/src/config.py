"""
config.py
---------
Centralise toute la configuration du scraper Airbnb.
Aucune logique ici : uniquement des constantes et paramètres.
"""

# ── URL et paramètres de l'API Airbnb ─────────────────────────────────────────
# ⚠️ Mettre à jour le hash si Airbnb renvoie une erreur 400/404
# (visible dans l'URL de la requête dans les DevTools navigateur)
API_HASH   = "753d97c7b19a1a402d2fa63882ff4d6802004d11f2499647deef923a19a1641a"
API_URL    = f"https://www.airbnb.fr/api/v3/StaysSearch/{API_HASH}"

API_PARAMS = {
    "operationName": "StaysSearch",
    "locale":        "fr",
    "currency":      "EUR",
}

# ── En-têtes HTTP ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent":                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                                         "Chrome/147.0.0.0 Safari/537.36",
    "x-airbnb-api-key":                  "d306zoyjsyarp7ifhu67rjxn52tv0t20",
    "x-airbnb-supports-airlock-v2":      "true",
    "x-airbnb-graphql-platform":         "web",
    "x-airbnb-graphql-platform-client":  "minimalist-niobe",
    "x-niobe-short-circuited":           "true",
    "x-csrf-without-token":              "1",
    "Content-Type":                      "application/json",
    "origin":                            "https://www.airbnb.fr",
    "referer":                           "https://www.airbnb.fr/s/Paris/homes",
}

# ── Curseur de départ (page 1, offset 0) ──────────────────────────────────────
INITIAL_CURSOR = "eyJzZWN0aW9uX29mZnNldCI6MCwiaXRlbXNfb2Zmc2V0IjowLCJ2ZXJzaW9uIjoxfQ=="

# ── Paramètres géographiques et temporels de la recherche ─────────────────────
SEARCH_PARAMS = {
    "acpId":               "db9f8d81-98a0-4f97-8e5f-51f6987effdb",
    "channel":             "EXPLORE",
    "datePickerType":      "calendar",
    "flexibleTripLengths": "one_week",
    "monthlyEndDate":      "2026-08-01",
    "monthlyLength":       "3",
    "monthlyStartDate":    "2026-05-01",
    "neLat":               "48.93873773658528",
    "neLng":               "2.451401256548337",
    "placeId":             "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
    "priceFilterInputType":"2",
    "priceFilterNumNights":"5",
    "query":               "Paris",
    "refinementPaths":     "/homes",
    "screenSize":          "large",
    "searchByMap":         "true",
    "swLat":               "48.757100363889634",
    "swLng":               "2.1217495888580515",
    "tabId":               "home_tab",
    "version":             "1.8.8",
    "zoomLevel":           "11",
}

# ── Paramètres de comportement du scraper ─────────────────────────────────────
SCRAPER_DELAY_SECONDS = 1.5   # Délai entre requêtes (respecter ≤ 1 req/s recommandé)
SCRAPER_TIMEOUT       = 15    # Timeout HTTP en secondes
SCRAPER_RETRY_WAIT    = 20    # Attente après rate-limit (429)
MAX_PAGES             = None  # None = toutes les pages disponibles

# ── Chemins de sortie ──────────────────────────────────────────────────────────
OUTPUT_CSV      = "data/scraped/airbnb_paris.csv"
OUTPUT_RAW_JSON = "data/raw_html/airbnb_raw_meta.json"

# ── Source documentée (conformité éthique / légale) ───────────────────────────
SOURCE_URL      = "https://www.airbnb.fr/s/Paris/homes"
ROBOTS_TXT_NOTE = (
    "robots.txt consulté — scraping via API interne GraphQL, "
    "pas de crawl HTML. Fréquence limitée à 1 requête/1.5s. "
    "Aucune donnée personnelle collectée."
)
