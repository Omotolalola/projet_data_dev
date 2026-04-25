# Projet Airbnb Paris — Data, IA & Optimisation

Pipeline complet : scraping → nettoyage → EDA → régression linéaire from scratch → optimisation (à venir).

---

## Structure des fichiers

```
├── main.py                      ← Point d'entrée : pipeline complet
├── src/
│   ├── config.py                ← Constantes : URL, headers, chemins, paramètres
│   ├── cleaner.py               ← Classe AirbnbCleaner   : nettoyage et typage des champs
│   ├── parser.py                ← Classe AirbnbParser    : navigation dans le JSON brut
│   ├── scraper.py               ← Classe AirbnbScraper   : HTTP, pagination, déduplication
│   ├── storage.py               ← Classe AirbnbStorage   : CSV, JSON, rapports qualité
│   ├── data_loader.py           ← Classe DataLoader      : chargement et validation du CSV
│   ├── data_processor.py        ← Classe DataProcessor   : nettoyage, features, split X/y
│   ├── regression.py            ← Classe LinearRegressionScratch : descente de gradient
│   └── evaluator.py             ← Classe Evaluator       : graphiques EDA + métriques modèle
├── data/
│   ├── scraped/
│   │   └── airbnb_paris.csv     ← Dataset structuré (sortie du scraping)
│   └── raw_html/
│       └── airbnb_raw_meta.json ← Métadonnées de collecte
└── notebooks/
    ├── 01_eda.py                ← Analyse exploratoire (exécutable seul)
    ├── 02_regression.py         ← Démonstration régression + comparaison sklearn
    └── eda_*.png / model_evaluation.png  ← Graphiques générés
```

---

## Installation

```bash
pip install requests pandas numpy matplotlib scikit-learn
```

---

## Lancement

```bash
# Pipeline complet : scraping + EDA + régression
python main.py

# CSV déjà présent, sauter le scraping
python main.py --skip-scraping

# Régression uniquement (pas de régénération des graphiques EDA)
python main.py --skip-scraping --skip-eda
```

---

## Architecture POO

| Classe | Fichier | Responsabilité |
|---|---|---|
| `AirbnbCleaner` | `src/cleaner.py` | Transforme les chaînes brutes en valeurs typées |
| `AirbnbParser` | `src/parser.py` | Navigue dans la structure JSON et délègue à AirbnbCleaner |
| `AirbnbScraper` | `src/scraper.py` | Orchestre les requêtes HTTP, la pagination, la déduplication |
| `AirbnbStorage` | `src/storage.py` | Sauvegarde CSV/JSON et affiche les rapports de qualité |
| `DataLoader` | `src/data_loader.py` | Charge le CSV, valide le schéma, rapport valeurs manquantes |
| `DataProcessor` | `src/data_processor.py` | Nettoyage, feature engineering, séparation X/y |
| `LinearRegressionScratch` | `src/regression.py` | Régression linéaire + descente de gradient (sans scikit-learn) |
| `Evaluator` | `src/evaluator.py` | Graphiques EDA, courbe de loss, métriques d'évaluation |

Chaque classe a **une seule responsabilité** (principe SRP).  
Les dépendances vont dans un seul sens : `Scraper → Parser → Cleaner`, `Scraper → Storage`, `DataProcessor → DataLoader`, `Evaluator → Regression`.

---

## Pipeline de données

```
AirbnbScraper          AirbnbStorage
(collecte HTTP)   →   (CSV + JSON)
                            ↓
                       DataLoader
                    (validation schéma)
                            ↓
                      DataProcessor
               (nettoyage + feature engineering)
                            ↓
               LinearRegressionScratch
              (entraînement from scratch)
                            ↓
                        Evaluator
                  (métriques + graphiques)
```

---

## Variable cible et features

**Variable cible** : `log_price` — logarithme de `price_eur`.  
La transformation log est appliquée car la distribution des prix est très asymétrique (médiane 756 €, max 6 500 €). Elle rapproche la distribution d'une gaussienne et stabilise la descente de gradient.

**Features utilisées** (après nettoyage) :

| Feature | Type | Description |
|---|---|---|
| `rating` | float | Note moyenne (0 si nouvelle annonce) |
| `nb_reviews` | float | Nombre d'avis (0 si nouvelle annonce) |
| `has_reviews` | int (0/1) | Flag : l'annonce a-t-elle des avis ? |
| `is_new_listing` | int (0/1) | Nouvelle annonce sans historique |
| `latitude` | float | Coordonnée géographique |
| `longitude` | float | Coordonnée géographique |
| `dist_centre_km` | float | Distance au centre de Paris (Haversine) |

**Colonnes exclues** : `person_capacity` (100 % manquante), `badges`, `price_str`, `rating_str`, `city` (redondant avec lat/lon).

---

## Régression linéaire from scratch

Implémentée dans `src/regression.py` **sans scikit-learn** pour le cœur algorithmique.

**Modèle** : `y_hat = X @ w + b`  
**Coût** : `MSE = (1/n) * Σ(y - y_hat)²`  
**Mise à jour** : `w ← w - α * (2/n) * Xᵀ(y_hat - y)`

**Hyperparamètres retenus** :

| Paramètre | Valeur | Justification |
|---|---|---|
| `learning_rate` | 0.05 | Convergence en < 200 époques, pas d'oscillation |
| `n_iterations` | 2 000 | Le plateau est atteint vers l'époque 200 |
| Split train/test | 80/20 | Standard pour 215 observations |

**Résultats sur le jeu de test** :

| Métrique | Valeur | Interprétation |
|---|---|---|
| R² | 0.29 | 29 % de la variance du prix expliquée |
| RMSE | 0.42 | Erreur en espace log |
| MAE | 350 € | Erreur moyenne en euros réels |

**Limites** : les features disponibles via le scraping (localisation, note, type) n'expliquent que 29 % de la variance. La surface, le nombre de chambres et la qualité des photos — non accessibles — expliquent probablement une grande partie des 71 % restants.

---

## Source et conformité éthique

- **Source** : `https://www.airbnb.fr/s/Paris/homes`
- **Date de collecte** : enregistrée automatiquement dans `airbnb_raw_meta.json`
- **robots.txt** : consulté — l'API GraphQL interne n'est pas couverte par une interdiction explicite
- **Fréquence** : 1 requête / 1,5 s (configurable dans `config.py`)
- **Données personnelles** : aucune (pas de nom d'hôte, pas d'email, pas d'adresse précise)
- **Champs collectés** : id, name, city, room_type, host_type, badges, price_eur, rating, nb_reviews, latitude, longitude

---

## Mise à jour du hash API

Si Airbnb renvoie une erreur 400 ou 404, le hash de l'API a changé.  
Ouvrir les DevTools → Réseau → filtrer `StaysSearch` → copier le hash dans l'URL → mettre à jour `API_HASH` dans `config.py`.
