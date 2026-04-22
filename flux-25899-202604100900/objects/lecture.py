import os
import json
import pandas as pd
from fonctions import map_types_to_category, extract_event_dates, extract_opening_hours, extract_booking_contact

OUTPUT_FILE = "analyse_poi.csv"

def analyse_datatourisme(dossier_racine):
    resultats = []

    for racine, dirs, fichiers in os.walk(dossier_racine):
        for fichier in fichiers:
            if fichier.endswith('.json'):
                chemin_complet = os.path.join(racine, fichier)

                try:
                    with open(chemin_complet, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Nom
                    noms = data.get('rdfs:label', {}).get('fr', [])
                    nom = noms[0] if noms else None

                    # Types
                    types = data.get('@type', [])

                    # Valeurs par défaut
                    date_creation = None
                    date_update = None
                    description = None
                    ville = None
                    code_postal = None
                    rue = None
                    telephone = None
                    email = None
                    reserv_telephone = None
                    reserv_email = None 
                    lat = None
                    lon = None
                    pets_allowed = None

                    #creation et mise à jour
                    date_creation = data.get('creationDate', None)
                    date_update = data.get('lastUpdate', None)

                    categorie = map_types_to_category(types)

                    if categorie == "event":
                        info_temps = extract_event_dates(data)
                    else:
                        info_temps = extract_opening_hours(data)

                    # Description
                    desc_list = data.get('hasDescription', [])
                    if desc_list:
                        desc = desc_list[0].get('dc:description', {}).get('fr', [])
                        description = desc[0] if desc else None

                    # Extraction localisation
                    located_list = data.get('isLocatedAt', [])
                    if located_list:
                        lieu = located_list[0]

                        # Adresse
                        adresse_list = lieu.get('schema:address', [])
                        if adresse_list:
                            adresse_dict = adresse_list[0]
                            ville = adresse_dict.get('schema:addressLocality', None)
                            code_postal = adresse_dict.get('schema:postalCode', None)
                            rues = adresse_dict.get('schema:streetAddress') or []
                            rue = rues[0] if rues else None

                        # Geo
                        geo = lieu.get('schema:geo', {})
                        if geo:
                            if geo.get('schema:latitude'):
                                lat = float(geo.get('schema:latitude'))
                            if geo.get('schema:longitude'):
                                lon = float(geo.get('schema:longitude'))

                        # Animaux autorisés ?
                        pets_allowed = lieu.get('petsAllowed', None)

                    # Contact
                    contacts = data.get('hasContact', [])
                    if contacts:
                        contact = contacts[0]

                        # Email
                        emails = contact.get('schema:email', [])
                        email = emails[0] if emails else None

                        # Téléphone
                        telephones = contact.get('schema:telephone', [])
                        telephone = telephones[0] if telephones else None

                    # Contact de réservation
                    reserv_email, reserv_telephone = extract_booking_contact(data)

                    resultats.append({
                        'Fichier': fichier,
                        'Date_creation': date_creation,
                        'Date_modification': date_update,
                        'Nom': nom,
                        'Types': types,
                        'Categorie': categorie,
                        'Info_Dates': info_temps,
                        'Description': description,
                        'Ville': ville,
                        'Code_Postal': code_postal,
                        'Rue': rue,
                        'Telephone': telephone,
                        'Email': email, 
                        'Email_Reservation': reserv_email,
                        'Telephone_Reservation': reserv_telephone  ,
                        'Latitude': lat,
                        'Longitude': lon,
                        'Animaux_autorises': pets_allowed
                    })

                except Exception as e:
                    print(f"Erreur sur le fichier {fichier}: {e}")

    df_final = pd.DataFrame(resultats)
    df_final.insert(0, 'id_poi', range(len(df_final)))
    return df_final

if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

dossier_du_script = os.path.dirname(os.path.abspath(__file__))
df = analyse_datatourisme(dossier_du_script)

df_csv = df.copy()
df_csv['Types'] = df_csv['Types'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
df_csv.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8-sig')
print(f"Ancien fichier supprimé. Nouveau fichier créé avec {len(df)} lignes.")
