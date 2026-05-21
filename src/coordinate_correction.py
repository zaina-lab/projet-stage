import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from fonctions import append_to_csv, haversine
from rapidfuzz import fuzz
import time
import os

INPUT_FILE  = "cordinate_verif.csv"   # Fichier issu du script de vérification
OUTPUT_FILE = "cordinate_correction.csv"

geolocator = Nominatim(user_agent="poi_correction_seinemaritime")

# Verdicts à ne pas corriger
VERDICTS_OK = {"PARFAIT Ville+CP+Rue"}


def nettoyer(val):
    """Renvoie une chaîne propre ou '' si vide."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("nan", "none", "0", "0.0", "") else s


def geocoder(query, retries=3, delay=2):
    """Appelle Nominatim avec retries en cas de timeout."""
    for attempt in range(retries):
        try:
            time.sleep(1)  # Respect rate-limit Nominatim (1 req/s)
            return geolocator.geocode(query, language="fr", timeout=10)
        except GeocoderTimedOut:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
        except GeocoderServiceError as e:
            print(f" Erreur service : {e}")
            break
    return None


def construire_requetes(nom, ville, cp, rue):
    requetes = []
    # Nom + Ville (Le plus classique)
    requetes.append({"query": f"{nom}, {ville}, France", "strategie": "nom+ville"})
    
    # Nom + CP (Si la ville est mal écrite)
    if cp:
        requetes.append({"query": f"{nom}, {cp}, France", "strategie": "nom+cp"})
    
    # Adresse seule (Roue de secours si le nom du POI est inconnu d'OSM)
    if rue and ville:
        requetes.append({"query": f"{rue}, {ville}, France", "strategie": "adresse_seule"})
        
    return requetes



# Fonction principale de correction d'une ligne
def corriger_ligne(row):
    id_poi = row.get("id_poi", "")
    verdict = str(row.get("Verdict", "")).strip()
    nom    = nettoyer(row.get("Nom",   ""))
    ville  = nettoyer(row.get("Ville", ""))
    cp     = nettoyer(row.get("CP",    "")).split(".")[0]
    rue    = nettoyer(row.get("Rue",   ""))
    categorie = nettoyer(row.get("categorie", "")) 
    adresse_gps = nettoyer(row.get("Adresse_GPS", ""))
    lat    = row.get("Latitude",  "")
    lon    = row.get("Longitude", "")
    
    result = {
        "id_poi":            id_poi,
        "Nom":               nom,
        "Categorie":         categorie,
        "Ville":             ville,
        "CP":                cp,
        "Rue":               rue,
        "Verdict_initial":   verdict,
        "Adresse_GPS":       adresse_gps,
        "lat_old":           lat,
        "lon_old":           lon,
        "lat_new":           lat,
        "lon_new":           lon,
        "adresse_geocodee":  "",
        "strategie_utilisee": "",
        "correction_status": "✅✅CONSERVE",
    }

    # Pas besoin de corriger
    if verdict in VERDICTS_OK:
        result["correction_status"] = "✅✅CONSERVE_PARFAIT"
        return result

    # Tentatives de géocodage
    requetes = construire_requetes(nom, ville, cp, rue)

    for tentative in requetes:
        location = geocoder(tentative["query"])
        if location:
            nom_cherche = nom.lower()
            nom_trouve = location.address.lower()
            
            # Score ultra-intelligent qui ignore l'ordre des mots
            score = fuzz.token_set_ratio(nom_cherche, nom_trouve)
            # Calcul de la distance
            dist = haversine(lat, lon, location.latitude, location.longitude)
            
            # --- LOGIQUE DE VALIDATION ---
            
            if score >= 70 or (tentative["strategie"] == "adresse_seule" and dist < 2000):
                if dist < 100000:
                    result["lat_new"] = round(location.latitude, 7)
                    result["lon_new"] = round(location.longitude, 7)
                    result["adresse_geocodee"] = location.address
                    result["strategie_utilisee"] = tentative["strategie"]
                    
                    # On compare si c'est EXACTEMENT pareil (ou à moins de 10cm)
                    if dist < 0.1: 
                        result["correction_status"] = "INCHANGE_VALIDE"
                        print(f" ✅ Confirmé (Identique) : {nom}")
                    else:
                        result["correction_status"] = "✅CORRIGE"
                        print(f" ✅ Corrigé ({int(dist)}m) : {nom}")
                    
                    return result

    print(f" ❌ Pas trouvé : {nom}")
    result["correction_status"] = "PAS_TROUVE"
    return result



# Pipeline
def run_correction_pipeline():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"🗑️  Ancien fichier {OUTPUT_FILE} supprimé")

    if not os.path.exists(INPUT_FILE):
        print(f" Fichier introuvable : {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, sep=";", engine="python", encoding="utf-8-sig")
    print(f" {len(df)} lignes lues depuis {INPUT_FILE}")

    total_parfait  = (df["Verdict"] == "PARFAIT Ville+CP+Rue").sum()
    total_a_corriger = len(df) - total_parfait
    print(f"   {total_parfait} PARFAIT | {total_a_corriger} à corriger\n")

    for i, row in df.iterrows():
        result = corriger_ligne(row)
        append_to_csv(result, OUTPUT_FILE)

        if i % 10 == 0:
            print(f"Avancement : {i}/{len(df)}")

    # --- Résumé ---
    df_out = pd.read_csv(OUTPUT_FILE, sep=";", engine="python")
    print("\n" + "="*50)
    print("📊 RÉSUMÉ")
    print("="*50)
    print(df_out["correction_status"].value_counts().to_string())
    print(f"\n✅ Fichier sauvegardé : {OUTPUT_FILE}")
 


if __name__ == "__main__":
    run_correction_pipeline()

