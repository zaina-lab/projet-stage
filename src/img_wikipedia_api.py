import requests
import time
import os
import re
import pandas as pd
from fonctions import append_to_csv
from rapidfuzz import fuzz
from ddgs import DDGS


# CONFIGURATION ----------------------------------------------------------
INPUT_FILE  = 'analyse_poi.csv'
OUTPUT_FILE = 'img_wikipedia1.csv'

SCORE_MIN  = 0.50   # Seuil similarité Wikipedia
GPS_RADIUS = 2000   # Rayon GPS en mètres
THUMB_SIZE = 800    # Taille thumbnail px
DELAY      = 0.5    # Délai entre requêtes

CONTEXTE = "Seine-Maritime tourisme"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "TourismeSeineMaritime/1.0 (contact: stage@example.com)"})


# Outils ----------------------------------------------
def clean(name: str) -> str:
    s = re.sub(r'\[.*?\]', '', str(name))
    s = re.sub(r'[«»"":\-]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def score_sim(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a.lower(), b.lower()) / 100


# SOURCE 1 Wikipedia GPS -------------------------------------
def search_wikipedia_gps(lat: str, lon: str, nom_clean: str):
    url = "https://fr.wikipedia.org/w/api.php"
    try:
        res = SESSION.get(url, params={
            "action": "query",
            "generator": "geosearch",
            "ggscoord": f"{lat}|{lon}",
            "ggsradius": GPS_RADIUS,
            "ggslimit": 10,
            "prop": "pageimages|info",
            "pithumbsize": THUMB_SIZE,
            "piprop": "thumbnail",
            "format": "json"
        }, timeout=8).json()

        pages = res.get("query", {}).get("pages", {})
        best = (None, 0, None)

        for page in pages.values():
            title = page.get("title", "")
            sc    = score_sim(nom_clean, title)
            img   = page.get("thumbnail", {}).get("source")
            if img and sc > best[1]:
                best = (img, sc, title)

        if best[0] and best[1] >= SCORE_MIN:
            return best[0], round(best[1], 2), best[2]

    except: pass
    return None, 0, None

# SOURCE 2 — Wikipedia par nom ----------------------------
def search_wikipedia_nom(nom_clean: str):
    url = "https://fr.wikipedia.org/w/api.php"
    try:
        res = SESSION.get(url, params={
            "action": "query",
            "list": "search",
            "srsearch": nom_clean,
            "srlimit": 5,
            "format": "json"
        }, timeout=8).json()

        for item in res.get("query", {}).get("search", []):
            title = item.get("title", "")
            sc    = score_sim(nom_clean, title)
            if sc < SCORE_MIN:
                continue

            img_res = SESSION.get(url, params={
                "action": "query",
                "titles": title,
                "prop": "pageimages",
                "pithumbsize": THUMB_SIZE,
                "piprop": "thumbnail",
                "format": "json"
            }, timeout=8).json()

            pages = img_res.get("query", {}).get("pages", {})
            for pg in pages.values():
                img = pg.get("thumbnail", {}).get("source")
                if img:
                    return img, round(sc, 2), title

    except: pass
    return None, 0, None

# SOURCE 3 — Wikidata -----------------------------------------------------
def search_wikidata(nom_clean: str):
    url = "https://www.wikidata.org/w/api.php"
    try:
        res = SESSION.get(url, params={
            "action": "wbsearchentities", # Je cherche une "entité" (un objet)
            "search": nom_clean,
            "language": "fr",
            "limit": 5,
            "format": "json"
        }, timeout=8).json()

        for entity in res.get("search", []):
            label = entity.get("label", "")
            sc    = score_sim(nom_clean, label)
            if sc < SCORE_MIN:
                continue

            eid = entity.get("id")
            claims = SESSION.get(url, params={
                "action": "wbgetclaims", # "Donne-moi les données de cette fiche"
                "entity": eid,
                "property": "P18", #le code universel pour l'Image.
                "format": "json"
            }, timeout=8).json().get("claims", {}).get("P18", [])

            if claims:
                filename = claims[0]["mainsnak"]["datavalue"]["value"]
                img = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename.replace(' ', '_')}?width={THUMB_SIZE}"
                return img, round(sc, 3), label

    except: pass
    return None, 0, None

# SOURCE 4 — DuckDuckGo ---------------------------------------------
def search_duckduckgo(query: str):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5))
            if results:
                return results[0]['image'], 0.60, "DuckDuckGo"
    except : pass
    return None, 0, None

# CASCADE PRINCIPALE -----------------------------------------------
def get_image(id_poi, nom, categorie, lat, lon):
    nom_c = clean(nom)
    nom_contexte = f"{nom_c} {CONTEXTE}"

    result = (None, 0, None, 'none')

    # 1. Wikipedia GPS
    if lat and lon:
        img, sc, title = search_wikipedia_gps(lat, lon, nom_c)
        if img:
            result = (img, sc, title, 'wikipedia_gps')

    # 2. Wikipedia nom
    if not result[0]:
        img, sc, title = search_wikipedia_nom(nom_contexte)
        if img:
            result = (img, sc, title, 'wikipedia_nom')

    # 3. Wikidata P18
    if not result[0]:
        img, sc, title = search_wikidata(nom_contexte)
        if img:
            result = (img, sc, title, 'wikidata')

    # 4. DuckDuckGo 
    if not result[0]:
        cat = str(categorie).lower().strip()
        
        # Stratégie de précision par catégorie
        if "event" in cat:
            precision = "événement concert fête"
        elif "accommodation" in cat:
            precision = "hôtel gîte chambre hôtes"
        elif "activity" in cat:
            precision = "loisir activité sport"
        elif "shop" in cat:
            precision = "boutique magasin artisanat"
        elif "culture" in cat:
            precision = "musée monument patrimoine"
        elif "food" in cat:
            precision = "restaurant gastronomie cuisine"
        elif "nature" in cat:
            precision = "parc jardin forêt paysage"
        else:
            precision = "tourisme"

        # Construction de la requête avec ta variable CONTEXTE (Seine-Maritime tourisme)
        # On combine : Nom + Précision + Département
        requete_finale = f"{nom_c} {precision} Seine-Maritime"

        img, sc, title = search_duckduckgo(requete_finale)
        if img:
            result = (img, sc, title, 'duckduckgo')

    append_to_csv({
        'id_poi':    id_poi,
        'poi':       nom,
        'categorie': categorie,
        'source':    result[3],
        'score':     result[1],
        'image_url': result[0] or ''
    }, OUTPUT_FILE)

# Main ---------------------------------------------------
def main():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    if not os.path.exists(INPUT_FILE):
        print(f" Fichier introuvable : {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, sep=';', encoding='utf-8-sig')
    total = len(df)
    print(f"🚀 Extraction sur {total} POIs...\n ")

    for i, row in df.iterrows():
        id_poi = str(row.get('id_poi', '')).strip()
        nom    = str(row.get('Nom', '')).strip()
        categorie = str(row.get('Categorie', '')).strip()
        lat    = str(row.get('Latitude', '')).replace(',', '.').strip()
        lon    = str(row.get('Longitude', '')).replace(',', '.').strip()

        print(f"\r⏳ Progression : {i}/{total} | Actuel : {nom[:30]}...", end="", flush=True)
        get_image(id_poi, nom, categorie, lat, lon)
        time.sleep(DELAY)
   

if __name__ == "__main__":
    main()