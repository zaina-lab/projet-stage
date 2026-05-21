import requests
import pandas as pd
import time
import os
from fonctions import append_to_csv, haversine

OUTPUT_FILE = "img_panoramax.csv"

#Créer une bbox autour d’un point
def create_bbox(lat, lon, delta=0.001):
    return [lon - delta, lat - delta, lon + delta, lat + delta]

# Recherche Panoramax
def search_panoramax(lat, lon, limit=10):
    url = "https://api.panoramax.xyz/api/search"
    bbox = create_bbox(lat, lon)
    
    params = {
        "bbox": ",".join(map(str, bbox)), 
        "limit": limit
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("features", [])
    except Exception as e:
        # print(f"Erreur sur {url} avec params {params} : {e}")
        return []

#Extraire la meilleure image proche
def best_image_for_poi(poi_lat, poi_lon, features):
    best_dist = float("inf")
    best_img = None

    for f in features:
        coords = f.get("geometry", {}).get("coordinates", None)
        if not coords:
            continue

        img_lon, img_lat = coords
        dist = haversine(poi_lat, poi_lon, img_lat, img_lon)

        if dist < best_dist and dist < 50:  #seuil de 50m
            best_dist = dist
            best_img = f

    return best_dist, best_img

#Pipeline principal
def run_pipeline(df):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"Ancien fichier {OUTPUT_FILE} supprimé. Création d'un nouveau.")

    for i, row in df.iterrows():
        id_poi = row["id_poi"]
        poi_name = row["Nom"]
        lat = row["Latitude"]
        lon = row["Longitude"]

        features = search_panoramax(lat, lon)
        dist, best_img = best_image_for_poi(lat, lon, features)

        if best_img:
            img_id = best_img["id"]
            api_lon, api_lat = best_img["geometry"]["coordinates"]
            assets = best_img.get("assets", {})
            img_url = assets.get("sd", {}).get("href") or assets.get("thumb", {}).get("href")
        else:
            img_id = None
            img_url = None
            api_lon = None
            api_lat = None
            dist = None
        result = {
            "id_poi": id_poi,
            "poi": poi_name,
            "lat": lat,
            "lon": lon,
            "found": best_img is not None,
            "distance_m": round(dist, 2) if dist else None,
            "api_lat": api_lat, 
            "api_lon": api_lon,
            "image_url": img_url,
            "nb_results": len(features)
        }

        append_to_csv(result, OUTPUT_FILE)
        time.sleep(0.5)
        if i % 50 == 0:
            print(f"{i}/{len(df)} traités")


#Chargement POI
df = pd.read_csv("analyse_poi.csv", sep=";")
run_pipeline(df)