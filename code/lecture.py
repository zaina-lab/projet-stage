import os
import json
import pandas as pd
from fonctions import map_types_to_category, extract_time_info, extract_booking_contact

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

                    uri_tourisme = data.get('@id', None)

                    # Nom
                    noms = data.get('rdfs:label', {}).get('fr', [])
                    nom = noms[0] if noms else None

                    # Types
                    types = data.get('@type', [])

                    # Valeurs par défaut
                    date_creation = None
                    created_by = None
                    date_update = None
                    date_update_datatourisme = None

                    description = None
                    short_description = None

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
                    reduced_mobility = None

                    insee_code = None
                    media_url = None

                    published_by = []
                    refs_list = []
                    features_list = []
                    cuisine_list = []
                    theme_list = []
                    aud_list = []
                    pricing_final = []
                    payment_methods_poi = set()
                

                    #date de creation ----------------------------------
                    date_creation = data.get('creationDate', None)

                    #Createur -----------------------------------
                    creator = data.get('hasBeenCreatedBy', {})
                    if creator:
                        created_by = {
                            "dc:identifier": creator.get("dc:identifier"),
                            "schema:address": [],
                            "schema:email": creator.get("schema:email", []),
                            "schema:legalName": creator.get("schema:legalName")
                        }
                        # On traite l'adresse
                        adresses = creator.get('schema:address', [])
                        if adresses:
                            addr = adresses[0]
                            # On simplifie le nom de la ville
                            ville_nom = None
                            city_block = addr.get('hasAddressCity', {})
                            if city_block:
                                # On prend le label FR de la ville
                                labels_ville = city_block.get('rdfs:label', {}).get('fr', [])
                                ville_nom = labels_ville[0] if labels_ville else addr.get('schema:addressLocality')
                            
                            # On ajoute l'objet adresse à notre liste schema:address
                            created_by["schema:address"].append({
                                "schema:addressLocality": addr.get("schema:addressLocality"),
                                "schema:postalCode": addr.get("schema:postalCode"),
                                "schema:streetAddress": addr.get("schema:streetAddress", []),
                                "hasAddressCity": ville_nom
                            })
                    # On transforme le dictionnaire en texte JSON pour le CSV
                    string_created_by = json.dumps(created_by, ensure_ascii=False) if created_by else None

                    #published_by -------------------------------------------------------
                    publishers = data.get('hasBeenPublishedBy', [])                    
                    if publishers:
                        pub = publishers[0] 
                        # On construit l'objet selon ta structure
                        obj_pub = {
                            "schema:email": pub.get("schema:email", []),
                            "schema:legalName": pub.get("schema:legalName"),
                            "foaf:homepage": pub.get("foaf:homepage", [])
                        }
                        # On l'ajoute à notre liste (pour avoir le fameux index 0)
                        published_by.append(obj_pub)
                    # Transformation en texte pour le CSV
                    string_published_by = json.dumps(published_by, ensure_ascii=False) if published_by else None


                    # mise à jour------------------------------------------------
                    date_update = data.get('lastUpdate', None)
                    date_update_datatourisme = data.get('lastUpdateDatatourisme', None)


                    #Catégorie ------------------------------------------------------
                    categorie = map_types_to_category(types)


                    #Heure d'ouverture 
                    info_temps = extract_time_info(data)

                    #Références Externes --------------------------------------------------------------
                    external_refs = data.get('hasExternalReference', [])
                    if external_refs:
                        for ref in external_refs:
                            # On récupère l'URL unique de la référence
                            ref_id = ref.get('@id')
                            if ref_id:
                                refs_list.append(ref_id)
                    # Transformation en texte JSON pour le CSV
                    string_external_refs = json.dumps(refs_list, ensure_ascii=False) if refs_list else None

                    # Description------------------------------------------------
                    desc_list = data.get('hasDescription', [])
                    if desc_list:
                        # On prend le premier bloc de description
                        bloc = desc_list[0]
                        
                        # Extraction de la description longue
                        desc_fr = bloc.get('dc:description', {}).get('fr', [])
                        description = desc_fr[0] if desc_fr else None
                        
                        # Extraction de la petite description (au même niveau)
                        short_fr = bloc.get('shortDescription', {}).get('fr', [])
                        short_description = short_fr[0] if short_fr else None


                        creator = data.get('hasBeenCreatedBy', {})
                    if creator:
                        adresses = creator.get('schema:address', [])
                        if adresses:
                            city_block = adresses[0].get('hasAddressCity', {})
                            if city_block:
                                insee_code = city_block.get('insee')


                    # localisation ------------------------------------------------
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

                    # Accessibilité PMR ---------------------------------------------
                    reduced_mobility = data.get('reducedMobilityAccess', None)

                    # Contact ------------------------------------------------
                    contacts = data.get('hasContact', [])
                    if contacts:
                        contact = contacts[0]

                        # Email
                        emails = contact.get('schema:email', [])
                        email = emails[0] if emails else None

                        # Téléphone
                        telephones = contact.get('schema:telephone', [])
                        telephone = telephones[0] if telephones else None

                    # Contact de réservation ------------------------------------------------
                    reserv_email, reserv_telephone = extract_booking_contact(data)


                    # Extraction des Equipements ------------------------------------------------
                    has_features = data.get('hasFeature', [])
                    for item in has_features:
                        # On descend dans la liste 'features' de chaque item
                        sub_features = item.get('features', [])
                        for feature in sub_features:
                            # On récupère le label FR
                            labels_fr = feature.get('rdfs:label', {}).get('fr', [])
                            if labels_fr:
                                features_list.append(labels_fr[0])
                    # On regroupe tout dans une chaîne séparée par des virgules
                    string_features = ", ".join(sorted(list(set(features_list)))) if features_list else None


                    # Types de Cuisine ------------------------------------------------                   
                    cuisine_list = []
                    # On récupère le champ (liste vide par défaut si absent)
                    cuisine_cats = data.get('providesCuisineOfType', [])

                    # Sécurité si DataTourisme renvoie un objet seul au lieu d'une liste
                    if isinstance(cuisine_cats, dict):
                        cuisine_cats = [cuisine_cats]
                        
                    for cat in cuisine_cats:
                        # Extraction du label en français
                        labels = cat.get('rdfs:label', {}).get('fr', [])
                        if labels:
                            cuisine_list.append(labels[0])
                    
                    # On regroupe tout dans une chaîne pour le CSV
                    string_cuisine = ", ".join(cuisine_list) if cuisine_list else None


                    # Thèmes ------------------------------------------------
                    themes = data.get('hasTheme', [])
                    for theme in themes:
                        # On récupère le label FR
                        labels_fr = theme.get('rdfs:label', {}).get('fr', [])
                        if labels_fr:
                            theme_list.append(labels_fr[0])
                    # On nettoie les doublons et on transforme en texte (ou None)
                    string_themes = ", ".join(sorted(list(set(theme_list)))) if theme_list else None


                    # Audience------------------------------------------------
                    offers = data.get('offers', [])
                    for offer in offers:
                        specs = offer.get('schema:priceSpecification', [])
                        for spec in specs:
                            audiences = spec.get('hasAudience', [])
                            for aud in audiences:
                                labels_fr = aud.get('rdfs:label', {}).get('fr', [])
                                if labels_fr:
                                    aud_list.append(labels_fr[0])
                    #On transforme en None si c'est vide, sinon en liste de texte
                    string_audiences = ", ".join(sorted(list(set(aud_list)))) if aud_list else None
                   

                   # priceSpecification----------------------------------------------- ---
                    offers = data.get('offers', [])
                    if offers:
                        # On prépare la structure demandée
                        price_specs_list = []
                        # On parcourt toutes les offres
                        for offer in offers:
                            
                            payment_list = []
                            accepted_payments = offer.get('schema:acceptedPaymentMethod', [])
                            for pm in accepted_payments:
                                label_pm = pm.get('rdfs:label', {}).get('fr', [None])[0]
                                if label_pm:
                                    payment_list.append(label_pm)

                            specs = offer.get('schema:priceSpecification', [])
                            for spec in specs:
                                # --- EXTRACTION DE L'OFFRE
                                label_offre = None
                                pricing_offer_list = spec.get('hasPricingOffer', [])
                                if pricing_offer_list:
                                    # On prend le premier élément, puis le dictionnaire rdfs:label, puis la liste 'fr'
                                    label_offre = pricing_offer_list[0].get('rdfs:label', {}).get('fr', [None])[0]

                                # --- EXTRACTION DU MODE 
                                label_mode = None
                                pricing_mode_list = spec.get('hasPricingMode', [])
                                if pricing_mode_list:
                                    # Même logique : index 0 de la liste, puis rdfs:label, puis index 0 de la liste 'fr'
                                    label_mode = pricing_mode_list[0].get('rdfs:label', {}).get('fr', [None])[0]

                                # On construit l'item
                                item = {
                                    "currency": spec.get("schema:priceCurrency"),
                                    "minPrice": spec.get("schema:minPrice", []),
                                    "maxPrice": spec.get("schema:maxPrice", []),
                                    "offre": label_offre,   
                                    "pricingMode": label_mode 
                                }
                                price_specs_list.append(item)
                        
                        # On assemble le tout dans le format : [ { "priceSpecification": [...] } ]
                        if price_specs_list:
                            pricing_final.append({
                                "paiements": payment_list,
                                "priceSpecification": price_specs_list
                            })
                    # Transformation en texte JSON pour le CSV
                    string_pricing = json.dumps(pricing_final, ensure_ascii=False) if pricing_final else None

                    # Médias------------------------------------------------
                    main_repres = data.get('hasRepresentation', [])
                    if main_repres:
                        # On prend la première représentation
                        repres = main_repres[0]
                    
                        resource = repres.get('ebucore:hasRelatedResource', {})
                        if isinstance(resource, list) and resource:
                            media_url = resource[0].get('@id')
                        elif isinstance(resource, dict):
                            media_url = resource.get('@id')
                        
                        # Si ce n'est pas là, on cherche dans url ou @id direct
                        if not media_url:
                            media_url = repres.get('@id')

                    resultats.append({
                        'URI_DataTourisme': uri_tourisme,
                        'Date_creation': date_creation,
                        'Créateur': string_created_by,
                        'Publié_par' : string_published_by,
                        'Date_update': date_update,
                        'Date_update_Datatourisme': date_update_datatourisme,
                        'Sources Exterieures' : string_external_refs,

                        'Nom': nom,
                        'Types': types,
                        'Categorie': categorie,

                        'Heure_Ouverture': info_temps,

                        'Petite_Description' : short_description,
                        'Description_Longue': description,

                        'INSEE_Code': insee_code,
                        'Ville': ville,
                        'Code_Postal': code_postal,
                        'Rue': rue,
                        'Latitude': lat,
                        'Longitude': lon,

                        'Telephone': telephone,
                        'Email': email, 
                        'Email_Reservation': reserv_email,
                        'Telephone_Reservation': reserv_telephone  ,

                        'Animaux_Autorises': pets_allowed,
                        'Accessibilite_PMR': reduced_mobility,

                        'Equipements': string_features,
                        'Type_Cuisine' : string_cuisine,
                        'Themes': string_themes,

                        'Public_Cible': string_audiences,
                        'specification_prix': string_pricing,
                        'Media': media_url,
                    })

                except Exception as e:
                    print(f"Erreur sur le fichier {fichier}: {e}")

    df_final = pd.DataFrame(resultats)
    df_final.insert(0, 'id_poi', range(len(df_final)))
    return df_final

if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

dossier_du_script = os.path.dirname(os.path.abspath(__file__))
dossier_data = os.path.join(dossier_du_script, '..', 'flux-25899-202604100900', 'objects')
df = analyse_datatourisme(dossier_data)

df_csv = df.copy()
df_csv['Types'] = df_csv['Types'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
df_csv.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8-sig')
#print(f"Ancien fichier supprimé. Nouveau fichier créé avec {len(df)} lignes.")
