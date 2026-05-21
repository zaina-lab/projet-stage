import os
import re
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from ddgs import DDGS 
from fonctions import append_to_csv
from rapidfuzz import fuzz

load_dotenv()
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'GeminiCLI-ProjectStage/1.0 (zainab)'
})

OUTPUT_FILE = 'contacts.csv'
INPUT_FILE = 'analyse_poi.csv'
DELAY_WEB = 1.0  # pour éviter le ban DuckDuckGo

# --- FONCTIONS DE NETTOYAGE ---
def clean_phone(raw):
    if pd.isna(raw) or not str(raw).strip(): return ''
    digits = re.sub(r'\D', '', str(raw))
    if digits.startswith('33') and len(digits) == 11:
        digits = '0' + digits[2:]
    # Si le numéro commence par 0 et fait 10 chiffres, c'est bon
    if len(digits) == 10 and digits.startswith('0'):
        return digits
    return digits if len(digits) >= 10 else ''

def extract_emails(text):
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

def extract_phones(text):
    patterns = [
        r'0[1-9](?:\s?\d{2}){4}',
        r'0[1-9](?:\.\d{2}){4}',
        r'0[1-9](?:-\d{2}){4}'
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, text))
    return [clean_phone(f) for f in found if clean_phone(f)]

# --- LE FILTRE DES MANQUANTS ---
def classifier_et_filtrer_manquants(df):
    mask_vide = (df['Telephone'].fillna('') == '') & (df['Email'].fillna('') == '')
    df_manquants = df[mask_vide].copy()
     
    mots_nature = ['bois', 'forêt', 'foret', 'étang', 'vallée', 'mare', 'parc naturel', 'nature']
    mots_evenements = ['vide-grenier', 'troc plantes', 'fête', 'festival', 'concert', 'tournoi', 'loto', 'Journées', 'Journée']
    mots_trajets = ['boucle', 'circuit', 'randonnée', 'sentier', 'balade', 'vtt', 'parcours', 'véloroute']

    def verifier_contexte(row):
        nom = str(row.get('Nom', '')).lower()
        desc = str(row.get('Petite_Description', '')).lower()
        texte = nom + " " + desc

        if any(m in texte for m in mots_nature + mots_evenements + mots_trajets):
            return 'Non-Etablissement (Non-contactable)'
     
        if re.search(r'\bde\b.*\bà\b|\bentre\b.*\bet\b', nom):
            return 'Non-Etablissement (Non-contactable)'
             
        return 'Etablissement (Contactable)'

    df_manquants.loc[:, 'Diagnostic_Contact'] = df_manquants.apply(verifier_contexte, axis=1)
     
    stats = df_manquants['Diagnostic_Contact'].value_counts()
    a_chercher = df_manquants[df_manquants['Diagnostic_Contact'] == 'Etablissement (Contactable)'].copy()
     
    return a_chercher, stats

# --- LES MOTEURS DE RECHERCHE ---

def extract_contact_from_osm_json(data, nom_cible):
    best_phone, best_email, best_score = '', '', 0
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        name = tags.get('name', '')
        tel   = tags.get('phone') or tags.get('contact:phone') or tags.get('telephone') or ''
        email = tags.get('email') or tags.get('contact:email') or ''
        if tel or email:
            score = fuzz.token_set_ratio(nom_cible, name) if name else 30
            if score > best_score:
                best_score = score
                if tel: best_phone = clean_phone(tel)
                if email: best_email = email.strip()
    return best_phone, best_email, best_score

def search_osm(lat, lon, nom_cible, ville=''):
    overpass_url = "https://overpass-api.de/api/interpreter"
    query_radius = f"[out:json][timeout:30];(node(around:500,{lat},{lon});way(around:500,{lat},{lon});relation(around:500,{lat},{lon}););out tags;"
    
    try:
        response = SESSION.post(overpass_url, data={'data': query_radius}, timeout=15)
        if response.status_code == 200:
            tel, email, score = extract_contact_from_osm_json(response.json(), nom_cible)
            if score > 50: return tel, email, 'OSM (gps)'
    except: pass

    if ville:
        nom_nettoye = nom_cible.split(' - ')[0].split(' : ')[0]
        query_name = f'[out:json][timeout:30];area[name="{ville}"]->.searchArea;(nwr[name~"{nom_nettoye}",i](area.searchArea););out tags;'
        
        try:
            response = SESSION.post(overpass_url, data={'data': query_name}, timeout=15)
            if response.status_code == 200:
                tel, email, score = extract_contact_from_osm_json(response.json(), nom_cible)
                if score > 40: return tel, email, 'OSM (Nom+Ville)'
        except: pass
    return '', '', None

def search_wikidata(lat, lon, nom_cible):
    wikidata_url = "https://query.wikidata.org/sparql"
    query = f"""SELECT ?item ?itemLabel ?phone ?email WHERE {{ 
    SERVICE wikibase:around {{ 
        ?item wdt:P625 ?location . 
        bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral . 
        bd:serviceParam wikibase:radius "0.5" . 
    }} 
    OPTIONAL {{ ?item wdt:P1329 ?phone . }} 
    OPTIONAL {{ ?item wdt:P968 ?email . }} 
    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],fr,en". }} 
    }} LIMIT 20"""
    
    try:
        response = SESSION.get(wikidata_url, params={'query': query, 'format': 'json'}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            best_phone, best_email, best_score = '', '', 0
            for row in data.get('results', {}).get('bindings', []):
                name = row.get('itemLabel', {}).get('value', '')
                tel, email = row.get('phone', {}).get('value', ''), row.get('email', {}).get('value', '')
                if tel or email:
                    score = fuzz.token_set_ratio(nom_cible, name)
                    if score > best_score:
                        best_score = score
                        if tel: best_phone = clean_phone(tel)
                        if email: best_email = email.strip()
            if best_score > 50: return best_phone, best_email, 'Wikidata'
    except: pass
    return '', '', None

def search_web_contacts(nom_cible, ville=''):
    query = f"{nom_cible} {ville} Seine-Maritime contact"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            all_text = " ".join([r['body'] + " " + r['title'] for r in results])
         
            emails = extract_emails(all_text)
            phones = extract_phones(all_text)
             
            best_email = emails[0] if emails else ''
            best_phone = phones[0] if phones else ''
             
            if best_email or best_phone:
                return best_phone, best_email, 'Web (DuckDuckGo)'
    except: pass
    return '', '', None

def search_api_gouv(nom_cible, code_insee=None):
    """Recherche ultra-précise via le code INSEE de la commune"""
    url = "https://recherche-entreprises.api.gouv.fr/search"
    nom_nettoye = nom_cible.split(' - ')[0].split(' : ')[0]
     
    params = {
        "q": nom_nettoye,
        "per_page": 1,
        "limite_matching_etablissements": 1
    }
     
    if code_insee:
        params["code_insee"] = str(code_insee)

    try:
        response = SESSION.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if not results: return '', '', None
             
            best_match = results[0]
            nom_officiel = best_match.get('nom_complet', '')
             
            score = fuzz.token_set_ratio(nom_nettoye, nom_officiel)
             
            if score > 50:
                return '', '', f'API Gouv (INSEE {code_insee})'
    except: pass
    return '', '', None

# ---- LA LOGIQUE DE DECISION ---
def process_poi(row):
    id_poi = str(row.get('id_poi', '')).strip()
    nom = str(row.get('Nom', '')).strip()
    categorie = str(row.get('Categorie', '')).strip()
    lat = str(row.get('Latitude', '')).replace(',', '.').strip()
    lon = str(row.get('Longitude', '')).replace(',', '.').strip()
    ville = str(row.get('Ville', '')).strip()
    code_insee = str(row.get('INSEE_Code', '')).strip()

    if not lat or not lon:
        return {'id_poi': id_poi, 'Nom': nom, 'Telephone': '', 'Email': '', 'Source': 'coordonnées manquantes'}

    # OSM
    telephone, email, source = search_osm(lat, lon, nom, ville)
     
    if not telephone and not email and code_insee:
        telephone, email, source = search_api_gouv(nom, code_insee)

    # Wikidata
    if not telephone and not email:
        telephone, email, source = search_wikidata(lat, lon, nom)
         
    # Web DuckDuckGo  
    if not telephone and not email:
        time.sleep(DELAY_WEB)  
        telephone, email, source = search_web_contacts(nom, ville)
     
    return {
        'id_poi': id_poi,
        'Nom': nom,
        'Categorie': categorie,
        'Telephone': telephone,
        'Email': email,
        'Source': source or 'non trouvé'
    }

def main():
    # Chargement sécurisé
    if not os.path.exists('analyse_poi.csv'):
        print("Erreur : analyse_poi.csv non trouvé")
        return
     
    df = pd.read_csv('analyse_poi.csv', sep=';') 

    # Analyse et Filtre
    pois_a_traiter, stats = classifier_et_filtrer_manquants(df)
    print(f"\n📊 STATISTIQUES :\n{stats}") 

    # Confirmation et Exécution
    if len(pois_a_traiter) > 0:
        if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE) 
         
        # La boucle de recherche est intégrée ici directement
        for i, (idx, row) in enumerate(pois_a_traiter.iterrows()):
            print(f"[{i+1}/{len(pois_a_traiter)}] Recherche : {row['Nom']}") 
            res = process_poi(row) 
            append_to_csv(res, OUTPUT_FILE) 
             
        print(f"\n✅ Terminé ! Résultats dans '{OUTPUT_FILE}'") 
    else:
        print("🚫 Opération annulée.") 

if __name__ == "__main__":
    main()