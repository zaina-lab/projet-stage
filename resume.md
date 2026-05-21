# 🌍 Projet POI-Intelligence : Synthèse Technique & Opérationnelle

## 📌 Vision du Projet
Ce projet vise à transformer les données brutes des **Points d'Intérêt (POI)** de la Seine-Maritime en une base de connaissances enrichie et fiabilisée. Il combine des techniques de **Data Engineering**, de **Web Scraping** et de **Data Visualization** pour offrir un diagnostic précis de la qualité de l'offre touristique du territoire.

---

## 🏗️ Architecture du Système

### 1. Analyse & Scoring de Qualité
Le moteur de scoring (`fonctions.py`) évalue chaque POI selon une **Matrice de Criticité** dynamique. L'importance d'un champ varie selon la catégorie métier (ex: le téléphone est critique pour un hôtel, mais secondaire pour un site naturel).

*   **Catégories gérées** : Hébergement (`accommodation`), Restauration (`food`), Culture & Patrimoine (`culture`), Événements (`event`), Activités (`activity`), Boutiques (`shop`), Nature (`nature`).
*   **Indicateurs de Performance (KPIs)** : 
    *   **Score de complétude globale** : Moyenne pondérée du remplissage des champs critiques.
    *   **Contactabilité** : Présence d'un téléphone ou d'un email validé.
    *   **Réservation** : Disponibilité de contacts dédiés à la réservation.
    *   **Accessibilité & Services** : Accueil des animaux, accessibilité PMR (wheelchair).
    *   **Richesse Sémantique** : Qualité des descriptions (longueur > 200 car. et pertinence).
    *   **Fiabilité Temporelle** : Présence d'horaires d'ouverture exploitables.

### 2. Pipeline d'Enrichissement Automatisé (ETL)
Le système agrège des données provenant de sources ouvertes via une cascade de recherche intelligente :
*   📞 **Contacts & Identité** (`contact_api.py`) : Recherche hybride via **OpenStreetMap (Overpass)**, **Wikidata**, **API Gouv (INSEE)** pour la fiabilité officielle, et **DuckDuckGo** en dernier recours.
*   📖 **Descriptions & Contexte** (`descriptions_api.py`) : Extraction de résumés via **Wikipedia API** et **DuckDuckGo Search**. Le système intègre un "douanier" (validation stricte) qui vérifie la présence du nom du POI et élimine les textes parasites (navigation, newsletters, erreurs géographiques).
*   📸 **Images & Médias** (`img_*.py`) : 
    *   **Wikipedia/Wikimedia** : Extraction de photos haute résolution avec filtres anti-blasons et anti-biographies.
    *   **Europeana API** : Récupération de documents historiques et culturelles.
    *   **Panoramax API** : Intégration de vues de terrain par calcul de proximité (Haversine).

### 3. Validation Géographique & Fiabilité
*   **Vérification de Localisation** (`coordinate_verif.py`) : Détection d'erreurs de coordonnées GPS via comparaison entre l'adresse déclarée et la position réelle sur la carte (Verdict : Parfait, OK, A vérifier, Erreur).
*   **Correction de Coordonnées** (`coordinate_correction.py`) : Repositionnement automatique des POI mal localisés via les données géographiques d'OpenStreetMap.

---

## 🖥️ Dashboard & Visualisation (Dash/Plotly)
Une interface interactive (`app.py`) permet de piloter la qualité des données :
*   **Diagnostic Global** : Treemaps de répartition, KPI Cards et histogrammes de complétude.
*   **Analyse Radar & Criticité** : Évaluation des 9 piliers métier (Horaires, Localisation, Contact, Description, Prix, etc.).
*   **Cartographie Interactive** : Visualisation des POI avec taille proportionnelle à la richesse de leur description et filtres par verdict de précision.

---

## 🛠️ Stack Technique
- **Langage** : Python 3.10+
- **Frontend** : Plotly Dash, Dash Bootstrap Components
- **Data** : Pandas, NumPy, RapidFuzz (fuzzy matching)
- **APIs & Web** : Wikipedia API, DuckDuckGo Search (DDGS), Overpass API, API Gouv, Europeana, Panoramax.

---

## 📂 Organisation des Sources (`src/`)
- `app.py` : Cœur du Dashboard interactif.
- `fonctions.py` : Logique métier, Matrice de Criticité et utilitaires de calcul.
- `lecture.py` : Pré-traitement et chargement des données DataTourisme (JSON to CSV).
- `main.py` : Analyse statistique et répartition des catégories.
- **Modules d'Enrichissement :**
    - `contact_api.py` : Récupération des informations de contact.
    - `descriptions_api.py` : Recherche et nettoyage des descriptions textuelles.
    - `img_wikipedia2.py` / `img_europeana_api.py` / `img_panoramax_api.py` : Sourcing d'images.
    - `PMR_api.py` : Analyse de l'accessibilité handicapé via GPS.
    - `coordinate_verif.py` & `coordinate_correction.py` : Fiabilisation géographique.

---

## 📈 Impact & Résultats
- **Score de Confiance** : Priorisation automatique des mises à jour pour les gestionnaires de données.
- **Réduction des "Zones Blanches"** : Enrichissement massif des POI sans contact ni description.
- **Qualité Certifiée** : Mise en place de filtres de sécurité pour éviter les descriptions hors-sujet.
