from collections import defaultdict
import json

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

# ======== CLEANING ========

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




# ========================== MATRICE DE CRITICITE  ========================

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


LISTE_CHAMPS = sorted(list(set(CHAMPS_GENERAUX.keys()) | set(list(MATRICE_CRITICITE.values())[0].keys())))
