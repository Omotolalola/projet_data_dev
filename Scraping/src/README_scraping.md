# Module Scraping — Airbnb Paris

## Structure des fichiers

```
├── main.py                  ← Point d'entrée : lance le scraping
├── src/
│   ├── config.py            ← Constantes : URL, headers, chemins, paramètres
│   ├── cleaner.py           ← Classe AirbnbCleaner  : nettoyage et typage des champs
│   ├── parser.py            ← Classe AirbnbParser   : navigation dans le JSON brut
│   ├── scraper.py           ← Classe AirbnbScraper  : HTTP, pagination, déduplication
│   └── storage.py           ← Classe AirbnbStorage  : CSV, JSON, rapports qualité
├── data/
│   ├── scraped/             ← airbnb_paris.csv (dataset structuré)
│   └── raw_html/            ← airbnb_raw_meta.json (métadonnées de collecte)
```

## Lancement

```bash
pip install requests pandas
python main.py
```

## Architecture POO

| Classe | Responsabilité |
|---|---|
| `AirbnbCleaner` | Transforme les chaînes brutes en valeurs typées (float, int, str nettoyée) |
| `AirbnbParser` | Navigue dans la structure JSON et délègue à AirbnbCleaner |
| `AirbnbScraper` | Orchestre les requêtes HTTP, la pagination, la déduplication |
| `AirbnbStorage` | Sauvegarde CSV/JSON et affiche les rapports de qualité |

Chaque classe a **une seule responsabilité** (principe SRP).  
Les dépendances vont dans un seul sens : `Scraper → Parser → Cleaner`, `Scraper → Storage`.

## Source et conformité éthique

- **Source** : `https://www.airbnb.fr/s/Paris/homes`
- **Date de collecte** : enregistrée automatiquement dans `airbnb_raw_meta.json`
- **robots.txt** : consulté — l'API GraphQL interne n'est pas couverte par une interdiction explicite
- **Fréquence** : 1 requête / 1,5 s (configurable dans `config.py`)
- **Données personnelles** : aucune (pas de nom d'hôte, pas d'email, pas d'adresse précise)
- **Champs collectés** : id, name, city, room_type, host_type, badges, price_eur, rating, nb_reviews, latitude, longitude

## Mise à jour du hash API

Si Airbnb renvoie une erreur 400 ou 404, le hash de l'API a changé.  
Ouvrir les DevTools → Réseau → filtrer `StaysSearch` → copier le hash dans l'URL → mettre à jour `API_HASH` dans `config.py`.
