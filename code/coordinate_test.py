import pandas as pd
from geopy.geocoders import Nominatim
import time
import os
import re

INPUT_FILE = 'analyse_poi.csv'
OUTPUT_FILE = "cordinate_test.csv"

#on cree un agent pour faire les requetes de geocodage
geolocator = Nominatim(user_agent="coordonnees_test")

def cordinate_test(row):
    adresse_reelle = ""
    verdict = "NON_TROUVE" # Valeur par défaut
    lat, lon = row['Latitude'], row['Longitude']
    nom = row.get('Nom', 'Inconnu')
    categorie = row.get('Categorie', 'Inconnu')
    
    try:
        # On récupère les données du CSV
        ville_base = str(row.get('Ville', '')).lower().strip()
        cp_base = str(row.get('Code_Postal', '')).strip()
        rue_base = str(row.get('Rue', '')).lower().strip() 
        
        cp_ok = False
        ville_ok = False
        rue_ok = False

        time.sleep(1) # Respect de l'API
        location = geolocator.reverse(f"{lat}, {lon}", language='fr', timeout=10)
        
        if location:
            adresse_reelle = location.address.lower()
            
            # --- BLOC CODE POSTAL ---
            if len(cp_base) >= 5:
                cp_ok = cp_base in adresse_reelle

            # --- BLOC VILLE ---
            if ville_base != '':
                ville_ok = ville_base in adresse_reelle
                
            # --- BLOC RUE ---
            if rue_base not in ['', 'nan', 'none']:
                mots = rue_base.split()

                # On récupère le premier nombre trouvé dans la rue du CSV
                numeros_csv = [int(m) for m in mots if m.isdigit()]
                
                # On cherche tous les nombres dans l'adresse du GPS
                numeros_gps = [int(n) for n in re.findall(r'\d+', adresse_reelle)]
                
                # Le reste de la logique
                noms_rue = [m for m in mots if len(m) > 3 and not m.isdigit()]
                nom_ok = any(m in adresse_reelle for m in noms_rue) if noms_rue else False
                
                if numeros_csv and numeros_gps:
                    n_csv = numeros_csv[0]
                    # On vérifie si un des nombres du GPS est proche du CSV (marge de 5)
                    num_ok = any(abs(n_csv - n_gps) <= 5 for n_gps in numeros_gps if n_gps < 1000)
                elif numeros_csv and not numeros_gps:
                    #On a un numéro dans la base mais RIEN dans Maps
                    num_ok = True
                else:
                    #Pas de numéro dans la base
                    num_ok = True
                
                rue_ok = num_ok and nom_ok

            # --- DÉTERMINATION DU VERDICT ---
            if cp_ok and ville_ok and rue_ok:
                verdict = "PARFAIT Ville+CP+Rue"
            elif cp_ok and ville_ok:
                verdict = "OK Ville+CP "
            elif cp_ok or ville_ok:
                verdict = "A VERIFIER Ville|CP "
    
    except Exception as e:
        verdict = f"ERREUR_TECHNIQUE: {e}"

    return {
        "Nom": nom,
        "categorie": categorie,
        "Ville" : ville_base,
        "CP" : cp_base,
        "Rue": rue_base,
        "Latitude": lat,
        "Longitude": lon,
        "Verdict": verdict,
        "Adresse_GPS": adresse_reelle
    }


def append_to_csv(row):
    df = pd.DataFrame([row])
    if not os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, index=False, sep=";")
    else:
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False, sep=";")


# --- PIPELINE PRINCIPALE ---
def run_geo_pipeline():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"Ancien fichier {OUTPUT_FILE} supprimé. Création d'un nouveau.")

    # Lecture du fichier source
    df = pd.read_csv(INPUT_FILE, sep=";", engine='python')
    print(f"Début du traitement : {len(df)} lignes à vérifier.")

    for i, row in df.iterrows():
        # On traite la ligne
        result_row = cordinate_test(row)
        
        #On l'ajoute direct au CSV de sortie
        append_to_csv(result_row)
        
        #Affichage du progrès
        if i % 100 == 0:
            print(f"{i}/{len(df)} traités")

# --- LANCEMENT ---
run_geo_pipeline()
