from collections import defaultdict
from rapidfuzz import fuzz
import pandas as pd
import os
import math
import json
import re
import unicodedata
import requests

# ====== LES CATÉGORIES ======

TYPE_MAPPING = {
    # --- FOOD ---
    "Restaurant": "food",
    "FoodEstablishment": "food",
    "CafeOrTeahouse": "food",
    "CafeOrCoffeeShop": "food",
    "FastFoodRestaurant": "food",
    "BrasserieOrTavern": "food",
    "BarOrPub": "food",
    "BistroOrWineBar": "food",
    "SelfServiceCafeteria": "food",
    "FarmhouseInn": "food",
    "Winery": "food",
    "Distillery": "food",
    "TastingProvider": "food",

    # --- ACCOMMODATION ---
    "Hotel": "accommodation",
    "HotelTrade": "accommodation",
    "LodgingBusiness": "accommodation",
    "Accommodation": "accommodation",
    "Camping": "accommodation",
    "CampingAndCaravanning": "accommodation",
    "FarmCamping": "accommodation",
    "Guesthouse": "accommodation",
    "BedAndBreakfast": "accommodation",
    "RentalAccommodation": "accommodation",
    "SelfCateringAccommodation": "accommodation",
    "HolidayResort": "accommodation",
    "StopOverOrGroupLodge": "accommodation",
    "ClubOrHolidayVillage": "accommodation",
    "Hostel": "accommodation",
    "YouthHostelAndInternationalCenter": "accommodation",
    "CollectiveHostel": "accommodation",
    "CollectiveAccommodation": "accommodation",
    "HolidayCentre": "accommodation",
    "CamperVanArea": "accommodation",
    "Hut": "accommodation",
    "TreeHouse": "accommodation",
    "Yurt": "accommodation",
    "Tipi": "accommodation",
    "Tent": "accommodation",
    "Bubble": "accommodation",
    "Dungeon": "accommodation",
    "HotelRestaurant": "accommodation",
    "AccommodationProduct": "accommodation",
    "House": "accommodation",

    # --- EVENT ---
    "Event": "event",
    "EntertainmentAndEvent": "event",
    "CulturalEvent": "event",
    "SportsEvent": "event",
    "Festival": "event",
    "Exhibition": "event",
    "Concert": "event",
    "MusicEvent": "event",
    "ShowEvent": "event",
    "SaleEvent": "event",
    "SocialEvent": "event",
    "ReligiousEvent": "event",
    "ChildrensEvent": "event",
    "VisualArtsEvent": "event",
    "FairOrShow": "event",
    "Parade": "event",
    "Carnival": "event",
    "TraditionalCelebration": "event",
    "Commemoration": "event",
    "Recital": "event",
    "Conference": "event",
    "OpenDay": "event",
    "Traineeship": "event",
    "Rally": "event",
    "PilgrimageAndProcession": "event",
    "ExhibitionEvent": "event",
    "SportsCompetition": "event",
    "LocalAnimation": "event",

    # --- CULTURE & HERITAGE ---
    "Museum": "culture",
    "Castle": "culture",
    "FortifiedCastle": "culture",
    "ReligiousSite": "culture",
    "Church": "culture",
    "Abbey": "culture",
    "Cathedral": "culture",
    "Chapel": "culture",
    "Monastery": "culture",
    "Convent": "culture",
    "Cloister": "culture",
    "Collegiate": "culture",
    "ArcheologicalSite": "culture",
    "RemarkableBuilding": "culture",
    "RemarkableHouse": "culture",
    "CityHeritage": "culture",
    "TechnicalHeritage": "culture",
    "IndustrialSite": "culture",
    "RemembranceSite": "culture",
    "MilitaryCemetery": "culture",
    "CivilCemetery": "culture",
    "Tower": "culture",
    "Bridge": "culture",
    "Mill": "culture",
    "Palace": "culture",
    "InterpretationCentre": "culture",
    "Library": "culture",
    "Cinema": "culture",
    "MovieTheater": "culture",
    "Theater": "culture",
    "Opera": "culture",
    "ArtsCentre": "culture",
    "CulturalSite": "culture",
    "DefenceSite": "culture",
    "Ruins": "culture",
    "PigeonLoft": "culture",
    "FortifiedSet": "culture",
    "Cabaret": "culture",
    "Calvary": "culture",
    "Bishopric": "culture",
    "CivicStructure": "culture",
    "Commanderie": "culture",

    # --- NATURE ---
    "Landform": "nature",
    "ParkAndGarden": "nature",
    "Park": "nature",
    "NaturalHeritage": "nature",
    "NaturalPark": "nature",
    "Forest": "nature",
    "Bocage": "nature",
    "Swamp": "nature",
    "Cliff": "nature",
    "Valley": "nature",
    "Beach": "nature",
    "Landes": "nature",
    "Lighthouse": "nature",
    "ZooAnimalPark": "nature",
    "Zoo": "nature",
    "PicnicArea": "nature",

    # --- ACTIVITY & SPORTS ---
    "Tour": "activity",
    "WalkingTour": "activity",
    "Rambling": "activity",
    "CyclingTour": "activity",
    "HorseTour": "activity",
    "EducationalTrail": "activity",
    "SportsClub": "activity",
    "SportsHall": "activity",
    "SportsAndLeisurePlace": "activity",
    "GolfCourse": "activity",
    "EquestrianCenter": "activity",
    "TennisComplex": "activity",
    "BowlingAlley": "activity",
    "IceSkatingRink": "activity",
    "SwimmingPool": "activity",
    "NauticalCentre": "activity",
    "Marina": "activity",
    "LeisureComplex": "activity",
    "ThemePark": "activity",
    "AmusementPark": "activity",
    "Casino": "activity",
    "MiniGolf": "activity",
    "RacingCircuit": "activity",
    "Racetrack": "activity",
    "Practice": "activity",
    "AccompaniedPractice": "activity",
    "MultiActivity": "activity",
    "PlayArea": "activity",
    "KidsClub": "activity",
    "Farm": "activity",
    "SightseeingBoat": "activity",
    "TeachingFarm": "activity",
    "RoadTour": "activity",
    "TouristTrain": "activity",
    "NightClub": "activity",
    "Arena": "activity",
    "Stadium": "activity",
    "StadiumOrArena": "activity",
    "ClimbingWall": "activity",
    "TrackRollerOrSkateBoard": "activity",
    "TouristBus": "activity",
    "SchoolOrTrainingCentre": "activity",
    
    "Transport": "activity",
    "TouristInformationCenter": "activity",
    "LocalTouristOffice": "activity",
    "TrainStation": "activity",
    "Airport": "activity",
    "TaxiCompany": "activity",
    "MedicalPlace": "activity",
    "HealthcareProfessional": "activity",
    "ConvenientService": "activity",

    # --- SHOP ---
    "Store": "shop",
    "BoutiqueOrLocalShop": "shop",
    "LocalProductsShop": "shop",
    "CraftsmanShop": "shop",
    "Market": "shop",
    "AntiqueAndSecondhandGoodDealer": "shop",
    "BricABrac": "shop",
    "EquipmentRentalShop": "shop",
    "EquipmentRepairShop": "shop",
    "Rental": "shop",
}



# ========================== MATRICE DE CRITICITE  ========================

MATRICE_CRITICITE = {
    "event": {
        "Heure_Ouverture": 4, 
        "Telephone": 2, 
        "Email": 2, 
        "Email_Reservation" : 2,
        "Telephone_Reservation": 2,
        "Animaux_Autorises": 0,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 3, 
        "Equipements" : 0,
        "Type_Cuisine":0,
        "Themes":2,
        "Public_Cible": 3, 
        "specification_prix": 2,
        "Media" : 1
    },
    "accommodation": {
        "Heure_Ouverture": 2, 
        "Telephone": 4, 
        "Email": 4, 
        "Email_Reservation" : 4,
        "Telephone_Reservation": 4,
        "Animaux_Autorises": 3,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 3, 
        "Equipements" : 3,
        "Type_Cuisine":1,
        "Themes":0,
        "Public_Cible": 1, 
        "specification_prix": 3,
        "Media" : 3
    },
    "activity": {
        "Heure_Ouverture": 4, 
        "Telephone": 3, 
        "Email": 3, 
        "Email_Reservation" : 3,
        "Telephone_Reservation": 3,
        "Animaux_Autorises": 1,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 3, 
        "Equipements" : 1,
        "Type_Cuisine":0,
        "Themes":2,
        "Public_Cible": 2, 
        "specification_prix": 2,
        "Media" : 1
    },
    "shop": {
        "Heure_Ouverture": 4, 
        "Telephone": 3, 
        "Email": 3, 
        "Email_Reservation" : 0,
        "Telephone_Reservation": 0,
        "Animaux_Autorises": 2,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 2, 
        "Equipements" : 0,
        "Type_Cuisine":0,
        "Themes":0,
        "Public_Cible": 0, 
        "specification_prix": 2,
        "Media" : 3
    },
    "culture": {
        "Heure_Ouverture": 3, 
        "Telephone": 3, 
        "Email": 3, 
        "Email_Reservation" : 0,
        "Telephone_Reservation": 0,
        "Animaux_Autorises": 2,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 3, 
        "Equipements" : 0,
        "Type_Cuisine":0,
        "Themes":2,
        "Public_Cible": 2, 
        "specification_prix": 3,
        "Media" : 3
    },
    "food": {
        "Heure_Ouverture": 4, 
        "Telephone": 4, 
        "Email": 4, 
        "Email_Reservation" : 4,
        "Telephone_Reservation": 4,
        "Animaux_Autorises": 3,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 2, 
        "Equipements" : 0,
        "Type_Cuisine":3,
        "Themes":0,
        "Public_Cible": 0, 
        "specification_prix": 3,
        "Media" : 3
    },
    "nature": {
        "Heure_Ouverture": 2, 
        "Telephone": 0, 
        "Email": 0, 
        "Email_Reservation" : 0,
        "Telephone_Reservation": 0,
        "Animaux_Autorises": 3,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 2, 
        "Equipements" : 0,
        "Type_Cuisine":0,
        "Themes":0,
        "Public_Cible": 0, 
        "specification_prix": 0,
        "Media" : 1
    },
    "other": {
        "Heure_Ouverture": 1, 
        "Telephone": 1, 
        "Email": 1, 
        "Email_Reservation" : 0,
        "Telephone_Reservation": 0,
        "Animaux_Autorises": 0,
        "Accessibilite_PMR":1,
        "Description_Longue": 1,
        "Petite_Description": 1, 
        "Equipements" : 0,
        "Type_Cuisine":0,
        "Themes":0,
        "Public_Cible": 0, 
        "specification_prix": 0,
        "Media" : 1
    },
}

CHAMPS_GENERAUX = {
    "URI_DataTourisme": 3,
    "Date_creation": 2,
    "Créateur": 2,
    "Publié_par": 2,
    "Date_update": 2,
    "Date_update_Datatourisme": 2,
    "Sources Exterieures": 1,
    "Nom": 3,
    "Types": 3,
    "INSEE_Code": 2,
    "Ville": 2,
    "Code_Postal": 2,
    "Rue": 1,
    "Latitude": 2,
    "Longitude": 2,
}

LISTE_CHAMPS = sorted(list(set(CHAMPS_GENERAUX.keys()) | set(list(MATRICE_CRITICITE.values())[0].keys())))


# ======================= CLEANING & NORMALIZATION ===========================

TYPE_GENERAUX = {"PointOfInterest", "PlaceOfInterest", "Product", "LocalBusiness", "OrderedList", "Visit", "ActivityProvider", "ServiceProvider", "LeisureSportActivityProvider", "CulturalActivityProvider"} 

def clean_type(t):
    if not isinstance(t, str):
        return ""
    return (
        t.replace("schema:", "")
         .replace("olo:", "")
         .replace("dc:", "")
         .replace("foaf:", "")
         .replace("kb:", "")
         .strip()
    )

def normaliser_nom(nom):
    """Nettoyage poussé pour comparer ce qui est comparable (utile pour le fuzzy matching)"""
    if not nom or not isinstance(nom, str): return ""
    # Bas en casse et suppression accents
    s = "".join(c for c in unicodedata.normalize('NFD', nom.lower()) if unicodedata.category(c) != 'Mn')
    # Garder uniquement lettres et chiffres
    s = re.sub(r'[^a-z0-9]', ' ', s)
    # Supprimer mots trop génériques qui faussent le score
    mots_vides = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'l', 'd', 'au', 'aux', 'hotel', 'restaurant', 'cafe', 'musee', 'gite', 'logis', 'chez'}
    mots = [m for m in s.split() if m not in mots_vides and len(m) > 1]
    return " ".join(mots)

# ======== CONTACT HELPERS ========

def clean_phone(raw):
    """Nettoie et formate un numéro de téléphone français"""
    if pd.isna(raw) or not str(raw).strip(): return ''
    digits = re.sub(r'\D', '', str(raw))
    if digits.startswith('33') and len(digits) == 11:
        digits = '0' + digits[2:]
    if len(digits) == 10 and digits.startswith('0'):
        return digits
    return digits if len(digits) >= 10 else ''

def extract_emails(text):
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

# ======== REQUÊTES & SESSIONS ========

def get_session(user_agent='POI-Intelligence-Project/1.0'):
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})
    return session

# ======== mapping principal ========

def map_types_to_category(types):
    if not isinstance(types, list):
        return "other"

    # Nettoyage + suppression des types généraux
    cleaned = []
    for t in types:
        ct = clean_type(t)
        if ct not in TYPE_GENERAUX:
            cleaned.append(ct)

    # Compteur des catégories
    scores = defaultdict(int)

    for t in cleaned:
        if t in TYPE_MAPPING:
            cat = TYPE_MAPPING[t]
            scores[cat] += 1

    if not scores:
        return "other"

    return max(scores, key=scores.get)

# ======== catégoriser la collecte des données========

def extract_time_info(data):
    # Initialisation du moule unique
    time_dict = {
        "start_date": None,
        "end_date": None,
        "opening_hours": []
    }

    #RÉCUPÉRATION DES DATES
    start_list = data.get("schema:startDate", [])
    end_list = data.get("schema:endDate", [])
    
    if start_list and isinstance(start_list, list):
        time_dict["start_date"] = start_list[0]
    if end_list and isinstance(end_list, list):
        time_dict["end_date"] = end_list[0]

    #RÉCUPÉRATION DES HORAIRES ET VALIDITÉS 
    locations = data.get('isLocatedAt', [])
    for loc in locations:
        specs = loc.get('schema:openingHoursSpecification', [])
        for spec in specs:
            # Extraction des jours (nettoyage du format schema:Monday à Monday)
            days = [d.get('@id', '').split(':')[-1].split('#')[-1] 
                    for d in spec.get('schema:dayOfWeek', [])]
            
            period = {
                "days": days,
                "opens": spec.get('schema:opens'),
                "closes": spec.get('schema:closes'),
                # On prend aussi les dates de validité internes si elles existent
                "valid_from": spec.get('schema:validFrom', '').split('T')[0] if spec.get('schema:validFrom') else None,
                "valid_through": spec.get('schema:validThrough', '').split('T')[0] if spec.get('schema:validThrough') else None
            }
            
            # On ajoute le créneau si on a soit des jours, soit des heures, soit une validité
            if period["days"] or period["opens"] or period["valid_from"]:
                time_dict["opening_hours"].append(period)

    #SÉCURITÉ : Si tout est vide, on renvoie None pour ne pas polluer le CSV
    if not any([time_dict["start_date"], time_dict["end_date"], time_dict["opening_hours"]]):
        return None

    return json.dumps(time_dict, ensure_ascii=False)

# --------Extraction des contacts de réservation----    
def extract_booking_contact(data):
    booking_contacts = data.get('hasBookingContact', [])
    
    if not booking_contacts:
        return None, None
    
    contact = booking_contacts[0]
    
    # Extraction sécurisée de l'email
    emails = contact.get('schema:email', [])
    email = emails[0] if emails else None
    
    # Extraction sécurisée du téléphone
    tels = contact.get('schema:telephone', [])
    tel = tels[0] if tels else None
    
    return email, tel

# ========================== POUR europeana et wikimedea ... les API  ========================

#fonction pour ajouter une ligne au fichier CSV
def append_to_csv(row, OUTPUT_FILE):
    df = pd.DataFrame([row])
    if not os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, index=False, sep=";")
    else:
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False, sep=";")


#Calcul distance 
def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en mètres entre deux points GPS"""
    try:
        R = 6371000 # Rayon de la Terre en m
        phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
        dphi = math.radians(float(lat2) - float(lat1))
        dlambda = math.radians(float(lon2) - float(lon1))
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 999999

def nettoyer(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("nan", "none", "0", "0.0", "") else s


# ======== ACCÈSLIBRE  ==============

def calculate_match_score(nom1, lat1, lon1, nom2, lat2, lon2):
    """
    Logique de matching.
    """
    nom1_n = normaliser_nom(nom1)
    nom2_n = normaliser_nom(nom2)
    if not nom1_n or not nom2_n: return 0, 999999
    # On utilise token_sort_ratio pour être plus strict sur les mots
    score_nom = fuzz.token_sort_ratio(nom1_n, nom2_n)
    # SI le nom est trop différent (score < 40), on rejette direct
    if score_nom < 40: return 0, 999999
    try:
        dist = haversine(lat1, lon1, lat2, lon2)
    except:
        dist = 999999
    # Bonus proximity : +30 si très proche, +15 si proche
    bonus_dist = 30 if dist < 30 else (15 if dist < 150 else 0)
    # Malus distance : -1 point tous les 25m
    malus_dist = dist / 25
    score_final = score_nom + bonus_dist - malus_dist
    return score_final, dist


def acceslibre_data(df_reference, output_path="acceslibre.csv"):
    """Intersection stricte entre Datatourisme et AccèsLibre (Cache automatique)"""
    if os.path.exists(output_path):
        return print(f"✅ Dictionnaire '{output_path}' déjà à jour.")

    url, tmp_file = "https://www.data.gouv.fr/fr/datasets/r/5b0f44f2-e6ea-4a58-874d-6fe364b40342", "acceslibre_complet.csv"
    print("📥 Sync AccèsLibre en cours...")
    try:
        r = requests.get(url, stream=True)
        with open(tmp_file, "wb") as f:
            for chunk in r.iter_content(1024*1024): f.write(chunk)
            
        chunks = pd.read_csv(tmp_file, sep=",", chunksize=20000, low_memory=False)
        df_76 = pd.concat([c[c['postal_code'].astype(str).str.startswith('76', na=False)] for c in chunks if 'postal_code' in c.columns])
        
        matched, ours = [], df_reference[["id_poi", "Nom", "Latitude", "Longitude", "Ville"]].dropna(subset=["Nom"])
        for ville, gp_our in ours.groupby("Ville"):
            gp_al = df_76[df_76["commune"].str.lower() == str(ville).lower()]
            if gp_al.empty: continue
            for _, our in gp_our.iterrows():
                best_m, max_s = None, -999
                for _, al in gp_al.iterrows():
                    s, _ = calculate_match_score(our["Nom"], our["Latitude"], our["Longitude"], al["name"], al["latitude"], al["longitude"])
                    if s > max_s: max_s, best_m = s, al
                if max_s >= 85:
                    res = best_m.to_dict()
                    res.update({"id_poi_datatourisme": our["id_poi"], "match_score": round(max_s, 1)})
                    matched.append(res)

        if matched:
            cols = ['id_poi_datatourisme', 'match_score', 'name', 'siret', 'site_internet', 'contact_url', 'horaires', 'entree_plain_pied']
            pd.DataFrame(matched)[[c for c in cols if c in pd.DataFrame(matched).columns]].to_csv(output_path, index=False, sep=";")
            print(f"✅ {len(matched)} POIs synchronisés dans {output_path}")
    except Exception as e: print(f"❌ Erreur Sync : {e}")
    finally:
        if os.path.exists(tmp_file): os.remove(tmp_file)



def deviner_categorie_osm(tags):
    """Tente de mapper les tags OSM vers tes catégories pour vérifier la cohérence"""
    amenity, tourism, shop, leisure, highway = tags.get('amenity', ''), tags.get('tourism', ''), tags.get('shop', ''), tags.get('leisure', ''), tags.get('highway', '')
    if highway: return 'road'
    if tourism in ['museum', 'gallery', 'castle', 'monument', 'heritage'] or amenity in ['arts_centre', 'library', 'cinema', 'theatre']: return 'culture'
    if amenity in ['restaurant', 'cafe', 'bar', 'pub', 'fast_food']: return 'food'
    if tourism in ['hotel', 'guest_house', 'hostel', 'motel', 'apartment'] or leisure == 'camp_site': return 'accommodation'
    if shop: return 'shop'
    if leisure in ['park', 'garden', 'nature_reserve']: return 'nature'
    if leisure in ['sports_centre', 'swimming_pool', 'stadium'] or tourism == 'information': return 'activity'
    return 'other'


 
def chercher_pmr_overpass(nom, lat, lon, categorie_cible, radius=250):
    """Cherche sur OSM via Overpass avec un scoring pondéré (Nom + Distance + Catégorie)"""
    query = f"[out:json];(node(around:{radius},{lat},{lon});way(around:{radius},{lat},{lon});relation(around:{radius},{lat},{lon}););out center tags;"
    url = "https://overpass.openstreetmap.fr/api/interpreter"
    headers = {'User-Agent': 'POI-Intelligence-Project/1.2'}
    try:
        r = requests.post(url, data={'data': query}, headers=headers, timeout=25)
        if r.status_code != 200: return None
        elements = r.json().get('elements', [])
        nom_cible_norm, candidats = normaliser_nom(nom), []
        for el in elements:
            tags = el.get('tags', {})
            nom_osm = tags.get('name') or tags.get('official_name') or tags.get('operator')
            if not nom_osm: continue
            score_nom = fuzz.token_set_ratio(nom_cible_norm, normaliser_nom(nom_osm))
            el_lat, el_lon = el.get('lat') or el.get('center', {}).get('lat'), el.get('lon') or el.get('center', {}).get('lon')
            dist = haversine(lat, lon, el_lat, el_lon)
            cat_osm, bonus_cat = deviner_categorie_osm(tags), 0
            if (cat_osm == 'road' or any(r in nom_osm.lower() for r in ['rue', 'route', 'chemin'])) and categorie_cible in ['accommodation', 'food', 'shop', 'culture']:
                bonus_cat = -100
            elif cat_osm == categorie_cible: bonus_cat = 30
            elif cat_osm != 'other' and categorie_cible != 'other' and cat_osm != categorie_cible: bonus_cat = -30
            score_final = score_nom - (dist / 5) + bonus_cat
            candidats.append({'nom': nom_osm, 'wheelchair': tags.get('wheelchair'), 'score': score_final})
        if not candidats: return None
        best = sorted(candidats, key=lambda x: x['score'], reverse=True)[0]
        return best if best['score'] >= 70 else None
    except: return None