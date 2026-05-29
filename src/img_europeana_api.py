import requests
from rapidfuzz import fuzz
import pandas as pd
import time
import os
import re
import unicodedata
from fonctions import append_to_csv
from dotenv import load_dotenv

load_dotenv()

# API europeana
api_key = os.getenv("EUROPEANA_API_KEY")
INPUT_FILE = "analyse_poi.csv"
OUTPUT_FILE = "img_europeana.csv"

def normaliser(texte):
    if not texte: return ""
    # Bas en casse + suppression accents
    s = "".join(c for c in unicodedata.normalize('NFD', str(texte).lower()) if unicodedata.category(c) != 'Mn')
    # Garder uniquement lettres et chiffres
    s = re.sub(r'[^a-z0-9]', ' ', s)
    return " ".join(s.split())

# Fonction de recherche dans l'API Europeana
def search_europeana(query, api_key, rows=5):
    url = "https://api.europeana.eu/record/v2/search.json"
    params = {"query": query, "wskey": api_key, "rows": rows}
    for _ in range(2):
        try:
            r = requests.get(url, params=params, timeout=20)
            return r.json().get("items", [])
        except:
            time.sleep(1)
    return []

# Fonction pour calculer le score de similarité (plus permissive)
def best_match_score(poi_name, items):
    best_score = 0
    best_title = None
    poi_norm = normaliser(poi_name)
    
    for item in items:
        titles = item.get("title", [])
        for title in titles:
            title_norm = normaliser(title)
            # token_set_ratio est beaucoup plus adapté aux titres longs/archives
            score = fuzz.token_set_ratio(poi_norm, title_norm) / 100
            if score > best_score:
                best_score = score
                best_title = title
    return best_score, best_title

# Fonction principale 
def run_pipeline(poi_data, api_key):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    total = len(poi_data)
    for i, (id_poi, nom_poi, ville_poi, categorie) in enumerate(poi_data):
        query = f"{nom_poi} {ville_poi}"
        items = search_europeana(query, api_key)
        score, best_title = best_match_score(nom_poi, items)
        
        # On garde tes seuils du rapport
        threshold = 0.6 if categorie in ["culture", "nature", "event"] else 0.95
        is_found = score >= threshold

        row = {
            "id_poi": id_poi,
            "poi": nom_poi,
            "ville": ville_poi,
            "categorie": categorie,
            "found": is_found,
            "best_score": score,
            "best_match": best_title,
            "nb_results": len(items)
        }
        append_to_csv(row, OUTPUT_FILE)
        
        if i % 100 == 0:
            print(f"{i}/{total} traités...")

if __name__ == "__main__":
    if not api_key:
        print("Erreur : EUROPEANA_API_KEY non trouvée dans le fichier .env")
    else:
        try:
            # On ajoute on_bad_lines et engine='python' ou quoting pour gérer les textes complexes
            df = pd.read_csv(INPUT_FILE, sep=";", quoting=0, on_bad_lines='skip', low_memory=False)
            
            # On s'assure que les colonnes nécessaires existent
            required_cols = ["id_poi", "Nom", "Ville", "Categorie"]
            
            # Nettoyage rapide au cas où
            df = df.dropna(subset=["Nom", "Ville"])
            
            if all(col in df.columns for col in required_cols):
                # Préparation des données
                poi_data = list(zip(df["id_poi"], df["Nom"], df["Ville"], df["Categorie"]))
                
                print(f"Lancement de l'enrichissement Europeana pour {len(poi_data)} POI.")
                run_pipeline(poi_data, api_key)
            else:
                print(f"Erreur : Colonnes manquantes dans {INPUT_FILE}. Attendu : {required_cols}")
                print(f"Colonnes présentes : {list(df.columns)}")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier {INPUT_FILE} : {e}")
