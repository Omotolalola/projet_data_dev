````markdown
# Projet Airbnb Paris — Data, IA & Optimisation

Pipeline complet : **scraping → nettoyage → EDA → régression linéaire from scratch → optimisation par programmation dynamique → planning exploitable**

---

# Présentation

Ce projet met en œuvre un pipeline complet de **Data Engineering**, **Machine Learning** et **Optimisation Algorithmique** appliqué à des annonces Airbnb situées à Paris.

## Objectifs :

1. Collecter automatiquement des données Airbnb via scraping.
2. Nettoyer et structurer les données.
3. Réaliser une analyse exploratoire des données (EDA).
4. Construire une régression linéaire from scratch (sans scikit-learn pour le cœur du modèle).
5. Utiliser les prédictions pour résoudre un problème d’optimisation.
6. Générer un planning exploitable au format CSV.

---

# Structure du projet

```text
├── main.py
├── requirements.txt
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── cleaner.py
│   ├── parser.py
│   ├── scraper.py
│   ├── storage.py
│   ├── data_loader.py
│   ├── data_processor.py
│   ├── regression.py
│   ├── evaluator.py
│   ├── dynamic_optimizer.py
│   └── planning.py
│
├── data/
│   ├── scraped/
│   │   └── airbnb_paris.csv
│   └── raw_html/
│       └── airbnb_raw_meta.json
│
├── notebooks/
│   ├── eda_*.png
│   └── model_evaluation.png
│
├── outputs/
│   ├── planning_optimal.csv
│   ├── selected_items.csv
│   └── optimization_summary.csv
│
└── tests/
    ├── conftest.py
    ├── test_cleaner.py
    ├── test_optimizer.py
    ├── test_regression.py
    └── test_planning.py
````

---

# Installation

## 1. Créer un environnement virtuel

### Windows

```bash
python -m venv myvenv
myvenv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv myvenv
source myvenv/bin/activate
```

---

## 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

# Lancement du projet

## Pipeline complet

```bash
python main.py
```

Exécute :

* scraping
* nettoyage
* EDA
* régression
* optimisation
* planning

---

## Utiliser le CSV existant

```bash
python main.py --skip-scraping
```

---

## Sans scraping + sans EDA

```bash
python main.py --skip-scraping --skip-eda
```

---

# Tests automatisés

Lancer :

```bash
pytest -v
```

Résultat obtenu :

```text
5 passed
```

Les tests couvrent :

* nettoyage des prix,
* parsing des annonces,
* régression from scratch,
* optimisation dynamique,
* planning.

---

# Architecture orientée objet

| Classe                  | Responsabilité                      |
| ----------------------- | ----------------------------------- |
| AirbnbCleaner           | Nettoyage et typage des données     |
| AirbnbParser            | Lecture du JSON Airbnb              |
| AirbnbScraper           | Collecte HTTP, pagination           |
| AirbnbStorage           | Sauvegarde CSV / JSON               |
| DataLoader              | Chargement et validation du dataset |
| DataProcessor           | Nettoyage + feature engineering     |
| LinearRegressionScratch | Régression from scratch             |
| Evaluator               | Graphiques et métriques             |
| KnapsackPlanner         | Optimisation dynamique              |
| PlanningBuilder         | Génération du planning              |

Chaque classe respecte le principe **Single Responsibility Principle (SRP)**.

---

# Pipeline global

```text
Scraping Airbnb
      ↓
CSV structuré
      ↓
Nettoyage
      ↓
Feature Engineering
      ↓
Régression Linéaire
      ↓
Prédiction des prix
      ↓
Programmation Dynamique
      ↓
Planning Optimal
```

---

# Variable cible et features

# Variable cible

```text
log_price = log(price_eur)
```

Le logarithme est utilisé pour :

* réduire l’asymétrie des prix,
* stabiliser la variance,
* améliorer la convergence du gradient.

---

# Features utilisées

| Feature        | Description                 |
| -------------- | --------------------------- |
| rating         | Note moyenne                |
| nb_reviews     | Nombre d’avis               |
| has_reviews    | Présence d’avis             |
| is_new_listing | Nouvelle annonce            |
| latitude       | Coordonnée                  |
| longitude      | Coordonnée                  |
| dist_centre_km | Distance au centre de Paris |

---

# Colonnes exclues

* person_capacity (100 % manquante)
* badges
* price_str
* rating_str
* city

---

# Régression linéaire from scratch

Implémentée sans scikit-learn pour la partie centrale.

## Modèle mathématique

```text
ŷ = Xw + b
```

## Fonction de coût

```text
MSE = (1/n) Σ(y - ŷ)²
```

## Descente de gradient

```text
w = w - α * gradient
```

---

# Hyperparamètres

| Paramètre        | Valeur |
| ---------------- | ------ |
| learning_rate    | 0.05   |
| n_iterations     | 2000   |
| train/test split | 80/20  |

---

# Résultats obtenus

| Métrique             | Valeur |
| -------------------- | ------ |
| R²                   | 0.31   |
| RMSE                 | 0.466  |
| MAE                  | 0.367  |
| MAE estimée en euros | ~370 € |

## Interprétation

Le modèle explique environ **31 % de la variance du prix**.

Résultat cohérent compte tenu :

* du dataset limité,
* du faible nombre de variables,
* de l’absence d’informations comme :

  * surface,
  * nombre de chambres,
  * standing,
  * photos,
  * saisonnalité.

---

# Optimisation par programmation dynamique

## Problème modélisé

Chaque annonce devient une tâche avec :

* une **valeur** = prix prédit,
* une **durée** = temps estimé de traitement,
* une capacité totale de **8 heures**.

## Objectif

```text
Maximiser la valeur totale sous contrainte de temps
```

## Algorithme utilisé

* Knapsack 0/1
* Reconstruction de la solution optimale

---

# Résultat optimisation

| Indicateur            | Valeur    |
| --------------------- | --------- |
| Annonces candidates   | 214       |
| Tâches sélectionnées  | 5         |
| Temps disponible      | 8 h       |
| Temps utilisé         | 8 h       |
| Occupation            | 100 %     |
| Valeur totale estimée | 6324.62 € |

---

# Planning généré

Exemple :

| Début | Fin   | Valeur |
| ----- | ----- | ------ |
| 09:00 | 10:27 | 1288 € |
| 10:27 | 11:56 | 1281 € |
| 11:56 | 13:24 | 1278 € |
| 13:24 | 14:53 | 1290 € |
| 14:53 | 16:33 | 1185 € |

Export :

```text
outputs/planning_optimal.csv
```

---

# Visualisations générées

## EDA

* distribution des prix
* valeurs manquantes
* corrélations
* prix par type de logement
* prix vs distance

## Modèle

* courbe de loss
* prédictions vs valeurs réelles

---

# Source et conformité éthique

* Source : Airbnb France
* Usage pédagogique
* Fréquence limitée des requêtes
* Pas de données personnelles collectées
* Dataset anonymisé

---

# Mise à jour du hash API

Si Airbnb renvoie erreur 400 / 404 :

1. Ouvrir DevTools navigateur
2. Onglet Réseau
3. Filtrer `StaysSearch`
4. Copier le nouveau hash
5. Modifier `API_HASH` dans `config.py`

---

# Limites du projet

* Dataset relativement petit (~214 lignes exploitables)
* Variables incomplètes
* Modèle linéaire simple
* Pas de saisonnalité
* Pas de NLP sur les titres

---

# Améliorations possibles

* Random Forest / XGBoost
* Dashboard Streamlit
* API Flask / FastAPI
* Scraping multi-villes
* Planning multi-journées
* Analyse NLP

---

# Auteur

Projet universitaire — Master 1 Data / IA / Développement

---

# Commandes recommandées

```bash
python main.py --skip-scraping
pytest -v
```

```
```
