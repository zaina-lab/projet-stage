import os
import time
import requests
import pandas as pd
from fuzzywuzzy import fuzz
from geopy.geocoders import Nominatim
from fonctions import append_to_csv

INPUT_FILE  = "analyse_poi.csv"
OUTPUT_FILE = "PMR.csv"
SEUIL_FUZZ  = 50  

# Configuration initiale
geolocator = Nominatim(user_agent="poi_pmr_seinemaritime_v2")
MOTS_A_EXCLURE = ['randonnee', 'vtt', 'velo', 'nature', 'circuit', 'boucle', 'itineraire', 'promenade', 'event', 'activity', 'animation', 'festival', 'atelier', 'concert', 'spectacle', 'marche', 'brocante', 'visite guidee', 'exposition temporaire', 'fete']

def chercher_pmr_overpass(nom, lat, lon, radius=200):
    """Cherche sur OSM via Overpass API en utilisant les coordonnées GPS (Plus fiable)"""
    query = f"[out:json];(node(around:{radius},{lat},{lon});way(around:{radius},{lat},{lon});relation(around:{radius},{lat},{lon}););out tags;"
    url = "https://overpass.openstreetmap.fr/api/interpreter"
    headers = {
        'User-Agent': 'POI-Intelligence-Project/1.0'
    }
    try:
        response = requests.post(url, data={'data': query}, headers=headers, timeout=25)
        if response.status_code != 200:
            return None
        
        elements = response.json().get('elements', [])
        best_match = None
        max_score = 0
        
        for el in elements:
            tags = el.get('tags', {})
            nom_osm = tags.get('name') or tags.get('official_name') or tags.get('operator')
            if not nom_osm:
                continue
                
            score = fuzz.token_set_ratio(nom.lower(), nom_osm.lower())
            if score > max_score:
                max_score = score
                best_match = {
                    'nom': nom_osm,
                    'wheelchair': tags.get('wheelchair'),
                    'score': score
                }
        
        if best_match and best_match['score'] >= SEUIL_FUZZ:
            return best_match
    except:
        pass
    return None

def chercher_pmr(nom, ville, lat=None, lon=None):
    """Stratégie hybride : Overpass (GPS) d'abord, Nominatim (Nom) en secours"""
    
    # 🎯 STRATÉGIE 1 : Overpass avec GPS (Le plus précis)
    if lat and lon and lat != 0:
        result = chercher_pmr_overpass(nom, lat, lon)
        if result:
            wheelchair = (result['wheelchair'] or "").lower().strip()
            mapping = {"yes": "Oui", "no": "Non", "limited": "Partiel"}
            return mapping.get(wheelchair, "Inconnu"), result['nom']

    # 🎯 STRATÉGIE 2 : Nominatim (Ancienne méthode si GPS échoue ou absent)
    try:
        time.sleep(1.2) # Un peu plus de délai pour éviter le 429
        
        location = geolocator.geocode(f"{nom}, {ville}, France", language="fr", timeout=10, extratags=True, addressdetails=True)
        
        if not location and ("-" in nom or "(" in nom):
            nom_court = nom.split("-")[0].split("(")[0].strip()
            location = geolocator.geocode(f"{nom_court}, {ville}, France", language="fr", timeout=10, extratags=True, addressdetails=True)
            
        if not location:
            return "Inconnu", "Aucun"
        
        adresse = location.raw.get("address", {})
        nom_osm = adresse.get("amenity") or adresse.get("shop") or adresse.get("tourism") or adresse.get("historic") or adresse.get("building") or location.address.split(",")[0]
        
        wheelchair = (location.raw.get("extratags") or {}).get("wheelchair", "").lower().strip()
        
        if not wheelchair:
            osm_type = location.raw.get("osm_type", "")
            osm_id = location.raw.get("osm_id", "")
            if osm_type and osm_id:
                res = requests.get(f"https://api.openstreetmap.org/api/0.6/{osm_type}/{osm_id}.json", timeout=10)
                tags = res.json().get("elements", [{}])[0].get("tags", {})
                wheelchair = tags.get("wheelchair", "").lower().strip()
        
        mapping = {"yes": "Oui", "no": "Non", "limited": "Partiel"}
        return mapping.get(wheelchair, "Inconnu"), nom_osm
    except:
        return "Inconnu", "Erreur"

def main():
    if not os.path.exists(INPUT_FILE): return

    df = pd.read_csv(INPUT_FILE, sep=';', encoding='utf-8-sig')
    
    # Filtrage des lignes sans info PMR
    df_manquants = df[df['Accessibilite_PMR'].isna() | (df['Accessibilite_PMR'].astype(str).str.strip() == "")].copy()
    
    # Filtrage des catégories/mots exclus
    texte_combine = df_manquants['Nom'].astype(str).str.lower() + " " + df_manquants['Categorie'].astype(str).str.lower()
    df_propre = df_manquants[~texte_combine.str.contains('|'.join(MOTS_A_EXCLURE), na=False)]
    
    total = len(df_propre)
    print(f"📊 {total} POI pertinents à analyser...")
    
    # Reprendre si le fichier existe déjà (Optionnel, ici on repart à zéro comme demandé)
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)

    for i, (_, row) in enumerate(df_propre.iterrows()):
        nom = str(row.get('Nom', '')).strip()
        ville = str(row.get('Ville', '')).strip()
        id_poi = row.get('id_poi', '')
        lat = row.get('Latitude')
        lon = row.get('Longitude')

        print(f"[{i+1}/{total}] {nom} ({ville})")
        
        pmr, nom_osm = chercher_pmr(nom, ville, lat, lon)
        
        if nom_osm in ["Aucun", "Erreur"]:
            score_fuzz = 0
            verdict_fiabilite = "Non trouvé"
            print(f"   ❌ Absent d'OSM")
        else:
            score_fuzz = fuzz.token_set_ratio(nom.lower(), str(nom_osm).lower())
            verdict_fiabilite = "OK" if score_fuzz >= SEUIL_FUZZ else "A verifier"
            print(f"   ✅ Trouvé. OSM: '{nom_osm}' [{pmr}]")
            
        resultat = {
            'id_poi': id_poi, 'poi': nom, 'poi_osm': nom_osm, 
            'score_fuzz': round(score_fuzz), 'verdict_fiabilite': verdict_fiabilite,
            'categorie': row.get('Categorie', ''), 'ville': ville,
            'pmr_apres': pmr, 'statut': 'trouve' if nom_osm not in ["Aucun", "Erreur"] else 'non_trouve'
        }
        append_to_csv(resultat, OUTPUT_FILE)
        
        # Petit sleep pour Overpass si on enchaîne trop vite
        time.sleep(0.5)

if __name__ == "__main__":
    main()