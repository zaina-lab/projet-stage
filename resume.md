# 🌍 Projet POI-Intelligence : Synthèse Technique & Opérationnelle

## 📌 Vision du Projet

Ce projet est dédiée à l'enrichissement et à la fiabilisation des **Points d'Intérêt (POI)** de la Seine-Maritime. L'objectif est de transformer des données brutes (souvent incomplètes) en une base de connaissances structurée, vérifiée et exploitable pour le secteur du tourisme.

---

## 🛠️ Architecture du Pipeline d'Enrichissement

Le système repose sur une architecture modulaire où chaque composant cible un aspect spécifique de la donnée.

### 1. 📞 Module Contacts (`contact_api.py`)

Recherche et valide les coordonnées de contact (Téléphone, Email) via une approche hybride :

- **Sources** : OpenStreetMap (Overpass), Wikidata, API Gouv, et DuckDuckGo.
- **Objectif** : Maximiser la "contactabilité" des établissements.

### 2. 📖 Module Descriptions (`descriptions_api.py`)

Génère des contenus textuels riches pour chaque POI.

- **Sources** : Wikipedia API et DuckDuckGo Search.
- **Fiabilisation** : Un algorithme de nettoyage élimine les textes non pertinents (mentions légales, menus de navigation) et vérifie la présence du nom du POI dans le texte.

### 3. 📸 Module Médias & Images

Une cascade de sourcing pour garantir une couverture visuelle maximale :

- **Wikipedia/Wikimedia** : Photos haute résolution filtrées.
- **Europeana** : Archives historiques et culturelles.
- **Panoramax** : Vues de terrain (Street-view open source) par calcul de proximité géographique.

### 4. 🕒 Module Horaires (`horaires_api.py`)

Extraction et normalisation des plages d'ouverture pour permettre une exploitation temporelle des données.

### 5. ♿ Module Accessibilité PMR (`PMR_api.py`)

Analyse automatisée de l'accessibilité pour les personnes à mobilité réduite, basée sur les données d'infrastructure et les tags géographiques.

### 6. 🎯 Module Public Cible (`public_cible.py`)

Identification des audiences (familles, enfants, groupes, etc.) pour une meilleure segmentation marketing.

### 7. 🗺️ Fiabilisation Géographique

- **Vérification** (`coordinate_verif.py`) : Compare la position déclarée avec l'adresse réelle pour détecter les erreurs de placement.
- **Correction** (`coordinate_correction.py`) : Repositionne automatiquement les POI mal localisés via les données d'OpenStreetMap.

---

## 📊 Diagnostic & Scoring de Qualité

Le moteur (`fonctions.py`) évalue chaque POI via une **Matrice de Criticité**. Le score de qualité n'est pas fixe mais dépend de la catégorie (ex: un email est plus critique pour un hôtel que pour un monument naturel).

**Catégories gérées :**

- Hébergement (`accommodation`)
- Restauration (`food`)
- Culture & Patrimoine (`culture`)
- Événements (`event`)
- Activités (`activity`)
- Boutiques (`shop`)
- Nature (`nature`)

---

## 🖥️ Dashboard Interactif (`app.py`)

Une interface développée avec **Plotly Dash** permet de visualiser l'état de la base de données :

- **KPIs en temps réel** : Taux de complétude global et par module.
- **Cartographie dynamique** : Visualisation spatiale des POI avec filtres de qualité.
- **Analyse Radar** : Comparaison des performances sur les 9 piliers métier.

---

## 📂 Organisation des Données

Le projet traite les données sous forme de fichiers CSV pour chaque étape de l'enrichissement :

- `analyse_poi.csv` : Base de données principale issue de DataTourisme.
- `contacts.csv`, `descriptions.csv`, `horaires.csv` : Résultats des enrichissements API.
- `cordinate_verif.csv`, `cordinate_correction.csv` : Rapports de fiabilité géo.
- `PMR.csv`, `public_cible.csv` : Données thématiques.

_(Note : il reste qulque colonne qui n'ont pas encore été traité)_

---

## 🛠️ Stack Technique

- **Langage** : Python 3.10
- **Frontend** : Plotly Dash.
- **Data** : Pandas, NumPy, RapidFuzz.
- **Sources Externes** : Wikidata, Wikipedia,Ducksuckgo , OSM (Overpass), Europeana, Panoramax, API Gouv.
