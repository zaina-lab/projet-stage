import os
import pandas as pd
from fonctions import append_to_csv

INPUT_FILE = "analyse_poi.csv"
OUTPUT_FILE = "public_cible.csv"

# TYPES À IGNORER
TYPES_IGNORES = {
    "PointOfInterest", "PlaceOfInterest", "SportsAndLeisurePlace",
    "Tour", "olo:OrderedList", "schema:LocalBusiness", "Product",
    "Practice", "schema:Product", "schema:CivicStructure",
    "ConvenientService", "Transport", "schema:StadiumOrArena",
    "LeisureSportActivityProvider", "ActivityProvider",
}

TYPE = {
    "WalkingTour": ["Familles", "Adultes", "Randonneurs"],
    "CyclingTour": ["Adultes", "Sportifs"],
    "HorseTour": ["Adultes", "Enfants"],
    "RoadTour": ["Adultes", "Familles"],
    "EducationalTrail": ["Familles", "Enfants", "Groupes scolaires"],
    "EquestrianCenter": ["Adultes", "Enfants"],
    "CulturalActivityProvider": ["Adultes", "Familles"],
    "NauticalCentre": ["Adultes", "Familles"],
    "SightseeingBoat": ["Familles", "Adultes"],
    "AccompaniedPractice": ["Adultes", "Débutants"],
    "Marina": ["Adultes"],
    "SwimmingPool": ["Familles", "Enfants", "Adultes"],
    "TennisComplex": ["Adultes", "Enfants"],
    "GolfCourse": ["Adultes"],
    "schema:GolfCourse": ["Adultes"],
    "ClimbingWall": ["Adultes", "Adolescents"],
    "IceSkatingRink": ["Familles", "Enfants", "Adultes"],
    "BowlingAlley": ["Familles", "Adultes"],
    "MiniGolf": ["Familles", "Enfants"],
    "TrackRollerOrSkateBoard": ["Adolescents", "Enfants"],
    "SportsClub": ["Adultes"],
    "SportsHall": ["Adultes", "Groupes"],
    "Stadium": ["Adultes", "Familles"],
    "Racetrack": ["Adultes", "Familles"],
    "RacingCircuit": ["Adultes"],
    "MultiActivity": ["Familles", "Adultes", "Enfants"],
    "LeisureComplex": ["Familles", "Adultes", "Enfants"],
    "KidsClub": ["Enfants", "Familles"],
    "PlayArea": ["Enfants", "Familles"],
    "TeachingFarm": ["Familles", "Enfants", "Groupes scolaires"],
    "ThemePark": ["Familles", "Enfants"],
    "schema:AmusementPark": ["Familles", "Enfants"],
    "Theater": ["Adultes", "Familles"],
    "Casino": ["Adultes"],
    "schema:Casino": ["Adultes"],
    "NightClub": ["Adultes"],
    "schema:NightClub": ["Adultes"],
    "SchoolOrTrainingCentre": ["Adultes", "Débutants"],
    "Traineeship": ["Adultes", "Groupes"],
    "TouristInformationCenter": ["Adultes", "Familles"],
    "schema:TouristInformationCenter": ["Adultes", "Familles"],
    "LocalTouristOffice": ["Adultes", "Familles"],
    "TouristTrain": ["Familles", "Adultes"],
    "TouristBus": ["Adultes", "Familles"],
    "TrainStation": ["Adultes", "Familles"],
    "schema:TrainStation": ["Adultes", "Familles"],
    "Airport": ["Adultes"],
    "schema:Airport": ["Adultes"],
    "TastingProvider": ["Adultes"],
    "PicnicArea": ["Familles", "Adultes"],
}

# TES MOTS-CLÉS DE DESCRIPTION
DESC_KEYWORDS = {
    "en famille": ["Familles"],
    "toute la famille": ["Familles", "Enfants"],
    "petits et grands": ["Familles", "Enfants"],
    "de 7 à 77": ["Familles", "Enfants", "Adultes"],
    "de 3 ans": ["Familles", "Enfants"],
    "enfant": ["Enfants", "Familles"],
    "bébé": ["Familles", "Enfants"],
    "adolescent": ["Adolescents"],
    " ado ": ["Adolescents"],
    "groupes scolaires": ["Groupes scolaires"],
    "classes scolaires": ["Groupes scolaires"],
    "sorties scolaires": ["Groupes scolaires"],
    "accueil scolaire": ["Groupes scolaires"],
    "visites scolaires": ["Groupes scolaires"],
    "adulte": ["Adultes"],
    "senior": ["Seniors"],
    "3ème âge": ["Seniors"],
    "handicap": ["PMR"],
    "pmr": ["PMR"],
    "mobilité réduite": ["PMR"],
    "débutant": ["Débutants"],
    "initiation": ["Débutants", "Adultes"],
    "sportif": ["Sportifs"],
    "groupes": ["Groupes"],
    "randonnée": ["Adultes", "Randonneurs"],
    "baignade": ["Familles", "Adultes", "Enfants"],
    "bien-être": ["Adultes"],
    "spa": ["Adultes"],
    "massage": ["Adultes"],
    "jet ski": ["Adultes"],
    "parachut": ["Adultes"],
    "ulm": ["Adultes"],
    "hélicoptère": ["Adultes"],
    "montgolfière": ["Adultes", "Familles"],
    "planeur": ["Adultes"],
    "aéroclub": ["Adultes"],
    "plongée": ["Adultes", "Sportifs"],
    "kayak": ["Familles", "Adultes"],
    "paddle": ["Familles", "Adultes"],
    "canoë": ["Familles", "Adultes"],
    "canoe": ["Familles", "Adultes"],
    "voile": ["Adultes", "Familles"],
    "surf": ["Adultes", "Adolescents"],
    "skate": ["Adolescents", "Enfants"],
    "escalade": ["Adultes", "Adolescents"],
    "grimpe": ["Familles", "Enfants"],
    "accrobranche": ["Familles", "Enfants"],
    "parcours aventure": ["Familles", "Enfants"],
    "pêche": ["Adultes", "Familles"],
    "golf": ["Adultes"],
    "équitation": ["Adultes", "Enfants"],
    "cheval": ["Adultes", "Enfants"],
    "bowling": ["Familles", "Adultes"],
    "laser game": ["Familles", "Adultes", "Adolescents"],
    "escape game": ["Familles", "Adultes"],
    "escape": ["Familles", "Adultes"],
    "paintball": ["Adultes", "Adolescents"],
    "casino": ["Adultes"],
    "théâtre": ["Adultes", "Familles"],
    "spectacle": ["Adultes", "Familles"],
    "laser": ["Familles", "Adultes", "Adolescents"],
    "black jack": ["Adultes"],
    "roulette": ["Adultes"],
    "poker": ["Adultes"],
    "machines à sous": ["Adultes"],
    "parc animalier": ["Familles", "Enfants"],
    "animaux": ["Familles", "Enfants"],
    "permis": ["Adultes"],
    "trottinette": ["Adultes", "Familles"],
    "padel": ["Adultes"],
    "atelier": ["Adultes", "Familles"],
    "croisière": ["Adultes", "Familles"],
    "voilier": ["Adultes", "Familles"],
    "tank": ["Adultes"],
    "mécanique": ["Adultes"],
    "van": ["Adultes", "Familles"],
    "visites organisées": ["Familles", "Adultes"],
    "médiation culturelle": ["Adultes", "Familles"],
    "jardinage": ["Familles", "Adultes"],
    "aquaponie": ["Adultes", "Familles"],
    "ferme": ["Familles", "Enfants"],
    "dessin": ["Adultes", "Familles"],
    "street art": ["Adultes", "Familles"],
    "balade": ["Familles", "Adultes", "Randonneurs"],
    "visite": ["Familles", "Adultes"],
    "chèvrerie": ["Familles", "Enfants"],
    "cerf": ["Familles", "Enfants"],
    "2cv": ["Adultes", "Familles"],
    "dyane": ["Adultes", "Familles"],
    "location de": ["Adultes", "Familles"],
    "ludo-éducatif": ["Familles", "Enfants", "Groupes scolaires"],
    "observation": ["Familles", "Adultes"],
    "parcours": ["Familles", "Adultes"],
}

def classer_cible(row):
    types_str = str(row.get("Types", "") or "")
    desc = (
        str(row.get("Petite_Description", "") or "") + " " +
        str(row.get("Description_Longue", "") or "")
    ).lower()
    
    publics = set()
    #Règles par Types
    for raw_type in types_str.split(","):
        t = raw_type.strip()
        if t in TYPES_IGNORES: 
            continue
        if t in TYPE:
            publics.update(TYPE[t])

    #Règles par Description
    for d, vals in DESC_KEYWORDS.items():
        if d in desc:
            publics.update(vals)
    # Filtrage final
    publics = publics
    return ", ".join(sorted(publics)) if publics else "Inconnu"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} introuvable.")
        return

    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    df = pd.read_csv(INPUT_FILE, sep=";")
    
    # On cible uniquement la catégorie 'activity'
    df_manquants = df[df["Categorie"] == "activity"].copy()

    total = len(df_manquants)
    print(f" {total} POI 'activity' à enrichir...")
    for i, (_, row) in enumerate(df_manquants.iterrows()):
        id_poi = row.get('id_poi', '')
        nom = row.get('Nom', '')
        cat = row.get('Categorie', '')
        types = row.get('Types', '')
        # Nettoyage de la description pour le CSV : pas de sauts de ligne ET pas de points-virgules
        desc_brute = (str(row.get("Petite_Description", "") or "") + " " + str(row.get("Description_Longue", "") or ""))
        desc_propre = " ".join(desc_brute.split()).replace(';', ',')[:300]

        public = classer_cible(row)

        resultat = {
            'id_poi': id_poi,
            'nom': nom,
            'categorie': cat,
            'types': types,
            'description_analyse': desc_propre,
            'public_cible': public
        }
        append_to_csv(resultat, OUTPUT_FILE)
        
        if (i+1) % 100 == 0:
            print(f"   Progression: {i+1}/{total} traités...")

    print(f"\n✅ Terminé ! Résultats dans '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()