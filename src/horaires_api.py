import os
import time
import requests
import pandas as pd
from rapidfuzz import fuzz
from ddgs import DDGS
from fonctions import append_to_csv, haversine, normaliser_nom, get_session, MOTS_A_EXCLURE_GLOBAL, get_acceslibre_76

INPUT_FILE  = "analyse_poi.csv"
OUTPUT_FILE = "horaires.csv"
SEUIL_CONFIANCE = 70 

SESSION = get_session("POI-Horaires-Project/1.2")

def matching_local_acceslibre(nom, ville, df_al):
    """Cherche le POI dans le fichier local AccèsLibre"""
    # On filtre sur la ville pour aller vite
    df_ville = df_al[df_al['commune'].str.lower() == ville.lower()]
    if df_ville.empty: 
        return None

    nom_norm = normaliser_nom(nom)
    best_score = 0
    best_row = None

    for _, row in df_ville.iterrows():
        # AccèsLibre a les horaires dans 'horaires' (format texte ou JSON)
        # On vérifie aussi le nom
        nom_al = str(row.get('nom', ''))
        score = fuzz.token_set_ratio(nom_norm, normaliser_nom(nom_al))
        
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is not None and best_score >= SEUIL_CONFIANCE:
        h = best_row.get('horaires')
        if pd.notna(h) and str(h).strip():
            return {'horaires': h, 'nom_trouve': best_row['nom'], 'score': best_score}
    
    return None

def chercher_horaires_osm(nom, lat, lon, radius=250):
    """Stratégie OSM (Overpass)"""
    query = f"[out:json];(node(around:{radius},{lat},{lon});way(around:{radius},{lat},{lon});relation(around:{radius},{lat},{lon}););out center tags;"
    url = "https://overpass.openstreetmap.fr/api/interpreter"
    
    try:
        response = SESSION.post(url, data={'data': query}, timeout=15)
        if response.status_code != 200: return None
        
        elements = response.json().get('elements', [])
        nom_cible_norm = normaliser_nom(nom)
        
        candidats = []
        for el in elements:
            tags = el.get('tags', {})
            nom_osm = tags.get('name') or tags.get('official_name')
            horaires = tags.get('opening_hours')
            
            if not nom_osm or not horaires: continue
            
            score_nom = fuzz.token_set_ratio(nom_cible_norm, normaliser_nom(nom_osm))
            el_lat = el.get('lat') or el.get('center', {}).get('lat')
            el_lon = el.get('lon') or el.get('center', {}).get('lon')
            dist = haversine(lat, lon, el_lat, el_lon)
            
            score_final = score_nom - (dist / 5)
            candidats.append({'horaires': horaires, 'nom': nom_osm, 'score': score_final})
        
        if not candidats: return None
        candidats.sort(key=lambda x: x['score'], reverse=True)
        best = candidats[0]
        if best['score'] >= SEUIL_CONFIANCE: return best
    except: pass
    return None

def main():
    if not os.path.exists(INPUT_FILE): return
    
    # 1. Préparation AccèsLibre (Automatique)
    path_al = get_acceslibre_76()
    df_al = pd.read_csv(path_al, sep=';', low_memory=False) if path_al else None
    
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)

    df = pd.read_csv(INPUT_FILE, sep=';')
    mask_vide = df['Heure_Ouverture'].isna() | (df['Heure_Ouverture'].astype(str).str.strip() == "")
    df_manquants = df[mask_vide].copy()
    
    # Exclusion rando/nature
    df_propre = df_manquants[~df_manquants['Nom'].str.lower().str.contains('|'.join(MOTS_A_EXCLURE_GLOBAL), na=False)]
    
    total = len(df_propre)
    print(f"📊 {total} POI à analyser (AccèsLibre + OSM)...")

    counts = {"AL": 0, "OSM": 0, "Rien": 0}
    
    for i, (_, row) in enumerate(df_propre.iterrows()):
        nom, ville = str(row.get('Nom', '')).strip(), str(row.get('Ville', '')).strip()
        lat, lon = row.get('Latitude'), row.get('Longitude')
        id_poi = row.get('id_poi')

        print(f"[{i+1}/{total}] {nom} ({ville})")
        
        res_h, source, score = "Inconnu", "Aucun", 0

        # STRATÉGIE 1 : AccèsLibre (Local & Rapide)
        if df_al is not None:
            al_match = matching_local_acceslibre(nom, ville, df_al)
            if al_match:
                res_h, source, score = al_match['horaires'], "AccèsLibre", al_match['score']
                counts["AL"] += 1
                print(f"    AccèsLibre : {str(res_h)[:60]}...")

        # STRATÉGIE 2 : OSM (Si pas trouvé sur AL)
        if res_h == "Inconnu" and lat and lon:
            osm_match = chercher_horaires_osm(nom, lat, lon)
            if osm_match:
                res_h, source, score = osm_match['horaires'], "OSM", osm_match['score']
                counts["OSM"] += 1
                print(f"    ✅ OSM : {res_h}")

        if res_h == "Inconnu":
            counts["Rien"] += 1
            print(f"   ❌ Pas trouvé")

        res_final = {
            'id_poi': id_poi,
            'nom': nom,
            'source': source,
            'score_fiabilite': round(score),
            'Heure_Ouverture': str(res_h).replace(';', ',').replace('\n', ' ')
        }
        append_to_csv(res_final, OUTPUT_FILE)
        
        # On fait une pause uniquement pour OSM pour ne pas être banni
        if source == "OSM": time.sleep(0.4)

    print(f"\n✅ Terminé ! AccèsLibre: {counts['AL']} | OSM: {counts['OSM']} | Inconnus: {counts['Rien']}")

    # 4. NETTOYAGE (On efface le fichier temporaire pour rester propre)
    if path_al and os.path.exists(path_al):
        os.remove(path_al)
        print(f"🧹 Fichier temporaire {path_al} supprimé.")

if __name__ == "__main__":
    main()