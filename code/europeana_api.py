import requests
from rapidfuzz import fuzz
import pandas as pd
import time
import os

api_key =" sartgumettl"
INPUT_FILE = "analyse_poi.csv"
OUTPUT_FILE = "europeana.csv"

#fonction de recherche dans l'API Europeana
def search_europeana(poi, api_key, rows=5):
    url = "https://api.europeana.eu/record/v2/search.json"
    params = {
        "query": poi,
        "wskey": api_key,
        "rows": rows
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return data.get("items", [])
    except:
        return []


#fonction pour calculer le score de similarité entre le nom du POI et les titres des résultats de l'API
def best_match_score(poi, items):
    best_score = 0
    best_title = None
    for item in items:
        titles = item.get("title", [])
        for title in titles:
            score = fuzz.ratio(poi.lower(), title.lower()) / 100
            if score > best_score:
                best_score = score
                best_title = title

    return best_score, best_title

#fonction pour ajouter une ligne au fichier CSV
def append_to_csv(row):
    df = pd.DataFrame([row])
    if not os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, index=False, sep=";")
    else:
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False, sep=";")

#Fonction principale 
def run_pipeline(poi_data, api_key):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"Ancien fichier {OUTPUT_FILE} supprimé. Création d'un nouveau.")

    for i, (id_poi, nom_poi) in enumerate(poi_data):
        items = search_europeana(nom_poi, api_key)
        score, best_title = best_match_score(nom_poi, items)
        row = {
            "id_poi": id_poi,
            "poi": nom_poi,
            "found": len(items) > 0,
            "best_score": score,
            "best_match": best_title,
            "nb_results": len(items)
        }
        append_to_csv(row)
        time.sleep(0.5)
        if i % 100 == 0:
            print(f"{i}/{len(poi_data)} traités")

df = pd.read_csv(INPUT_FILE, sep=";")

poi_data = list(zip(df["id_poi"], df["Nom"]))

run_pipeline(poi_data, api_key)