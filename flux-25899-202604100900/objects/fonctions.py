from collections import defaultdict

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

# --------Extraction des horaires d'ouverture-----
def extract_opening_hours(data):
    # On récupère la liste des localisations
    locations = data.get('isLocatedAt', [])
    if not locations:
        return None

    all_periods = []
    #pour chaque lieu
    for loc in locations:
        specs = loc.get('schema:openingHoursSpecification', [])
        #pour chaque horaire
        for spec in specs:
            opens = spec.get('schema:opens')
            closes = spec.get('schema:closes')
            
            # Extraction et nettoyage des jours au finale on part de "schema:Sunday" à "Sunday""
            days_raw = spec.get('schema:dayOfWeek', [])
            days = [d.get('@id', '').split(':')[-1] for d in days_raw]
            
            v_from = spec.get('schema:validFrom')
            v_to = spec.get('schema:validThrough')

            # Extraction des dates de validité
            valid_from = v_from.split('T')[0] if v_from else None
            valid_to = v_to.split('T')[0] if v_to else None
            
            if opens and closes:
                days_str = ", ".join(days) if days else None
                if valid_from and valid_to:
                    period_info = f"{days_str} ({opens}-{closes}) du {valid_from} au {valid_to}"  
                else:
                    period_info = f"{days_str} ({opens}-{closes})"
                all_periods.append(period_info)

    return " | ".join(all_periods) if all_periods else None
 
# --------Extraction des dates d'événements----
def extract_event_dates(data):
    # Extraction des dates
    start_list = data.get("schema:startDate", [])
    end_list = data.get("schema:endDate", [])

    # On récupère la première valeur de chaque liste si elle existe
    start = start_list[0] if isinstance(start_list, list) and len(start_list) > 0 else None
    end = end_list[0] if isinstance(end_list, list) and len(end_list) > 0 else None

    if not start and not end:
        return None
    if start == end:
        return f"Le {start}" 
    
    start_display = start if start else "?"
    end_display = end if end else "?"

    return f"Du {start_display} au {end_display}"
    

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