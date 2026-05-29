import os
import time
import pandas as pd
from fonctions import append_to_csv,acceslibre_data, chercher_pmr_overpass

INPUT_FILE = "analyse_poi.csv"
OUTPUT_FILE = "PMR.csv"
AL_FILE = "acceslibre.csv"
SEUIL = 85

MOTS_EXCLUS = ['randonnee', 'vtt', 'velo', 'nature', 'circuit', 'boucle', 'itineraire', 'promenade', 'bois', 'foret', 'etang']

def determiner_pmr(row, source):
    """Verdict basé sur le plain-pied (AL) ou wheelchair (OSM)"""
    
    if source == "AccèsLibre":
        val = str(row.get('entree_plain_pied', '')).lower().strip()
        return "Oui" if val in ['true', '1', 'oui', 't'] else ("Non" if val in ['false', '0', 'non', 'f'] else "Inconnu")
    # Pour OSM
    mapping = {"yes": "Oui", "no": "Non", "limited": "Partiel"}
    return mapping.get((row.get('wheelchair') or "").lower().strip(), "Inconnu")

def main():
    if not os.path.exists(INPUT_FILE): return
    df = pd.read_csv(INPUT_FILE, sep=';', encoding='utf-8-sig')

    acceslibre_data(df)
    df_al = pd.read_csv(AL_FILE, sep=';').set_index('id_poi_datatourisme') if os.path.exists(AL_FILE) else None
    #Cible : Uniquement les manquants non exclus (Mots clés + Itinéraires "De... à...")
    df_todo = df[df['Accessibilite_PMR'].isna() | (df['Accessibilite_PMR'] == "")].copy()

    # Filtre 1 : Mots clés exclus
    mask_exclus = df_todo['Nom'].str.lower().str.contains('|'.join(MOTS_EXCLUS), na=False)
    # Filtre 2 : Structure "De ... à ..." (itinéraires)
    mask_itineraires = df_todo['Nom'].str.contains(r'^[Dd]e .* [àa] .*', regex=True, na=False)

    df_todo = df_todo[~(mask_exclus | mask_itineraires)]

    print(f"🚀 Enrichissement de {len(df_todo)} POIs (Itinéraires exclus)...")
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    for i, (_, row) in enumerate(df_todo.iterrows()):
        id_poi, nom, ville, lat, lon, cat = row['id_poi'], row['Nom'], row['Ville'], row['Latitude'], row['Longitude'], row['Categorie']
        pmr, src_nom, score, source = "Inconnu", "Aucun", 0, "Aucune"

        # Priorité AccèsLibre
        if df_al is not None and id_poi in df_al.index:
            match = df_al.loc[id_poi]
            pmr, src_nom, score, source = determiner_pmr(match, "AccèsLibre"), match['name'], match['match_score'], "AccèsLibre"

        # Fallback OSM
        elif lat and lat != 0 and not pd.isna(lat):
            res = chercher_pmr_overpass(nom, lat, lon, cat)
            if res:
                pmr, src_nom, score, source = determiner_pmr(res, "OSM"), res['nom'], res['score'], "OSM"

        # On enregistre TOUT, même les échecs
        print(f"[{i+1}] {nom} -> {pmr} ({source})")
        append_to_csv({
            'id_poi': id_poi, 
            'poi': nom, 
            'poi_api': src_nom,
            'source': source, 
            'verdict': pmr, 
            'score': round(score),
            
        }, OUTPUT_FILE)

        time.sleep(0.05)
if __name__ == "__main__":
    main()