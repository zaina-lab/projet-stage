import os
import time
import re
import requests
import pandas as pd
from rapidfuzz import fuzz  
from fonctions import append_to_csv
from ddgs import DDGS

INPUT_FILE  = "analyse_poi.csv"
OUTPUT_FILE = "descriptions.csv"
DELAY_API = 0.5
DELAY_WEB = 1.2

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'TourismeProjetStage/3.0 (enrichissement descriptions POI)'
})

DICTIONNAIRE_CATEGORIES = {
    'food':          'restaurant',
    'accommodation': 'hébergement gîte',
    'shop':          'boutique commerce',
    'activity':      'randonnée circuit VTT',
    'culture':       'patrimoine château musée église',
    'nature':        'parc jardin forêt',
    'event':         'fête festival marché',
    'other':         ''
}

def est_description_generique(texte):
    """Détecte immédiatement si c'est une description globale de commune."""
    patterns = [
        'est une commune française', 'est une commune du', 'est un village',
        'est une ville', 'tableau ci-dessous', 'typologie des logements',
        'démographie', 'habitants au dernier recensement', 'habitants sont'
    ]
    texte_lower = texte.lower()
    return any(p in texte_lower for p in patterns)

def valider_description_strict(texte, nom_poi, ville):
    """
    Le seul et unique douanier du script. 
    Soit le texte parle explicitement du POI, soit on le jette (renvoie "").
    """
    if not texte or len(str(texte).strip()) < 40:
        return ""
        
    texte_lc = texte.lower()
    nom_poi_lc = nom_poi.lower()
    ville_lc = ville.lower()
    
    # 1. ÉLIMINATION DES TEXTES DE BOUTONS WEB (Bruit)
    termes_bruits = ["m'y rendre", "comment m'y rendre", "formulaire de contact", "vous êtes *", "getting there"]
    if any(bruit in texte_lc for bruit in termes_bruits) and len(texte) < 150:
        return ""
        
    # 2. ANTIVIRUS POUR COMMUNE GÉNÉRIQUE
    if est_description_generique(texte):
        return ""

    # 3. VERROU DE SÉCURITÉ ABSOLU : VÉRIFICATION DES MOTS DU POI
    # On extrait les mots importants du nom du POI (ex: "Fournil", "Lin" pour "Le Fournil du Lin")
    mots_interdits = {'gare', 'de', 'le', 'la', 'les', 'du', 'et', 'au', 'en', 'circuit', 'randonnée', 'vtt'}
    mots_cles_poi = [m for m in re.findall(r'\w+', nom_poi_lc) if len(m) > 3 and m not in mots_interdits]
    
    # Si aucun mot important du POI n'est écrit dans le texte, c'est un hors-sujet complet (ex: la Norvège)
    if mots_cles_poi and not any(mot in texte_lc for mot in mots_cles_poi):
        return ""

    # 4. LE SCORE STRICT SUR LE TITRE DE LA PAGE / DÉBUT DU TEXTE
    # Empêche la Gare de Paris-Saint-Lazare de remplacer la gare de Le Houlme
    score_strict = fuzz.token_sort_ratio(nom_poi_lc, texte_lc[:len(nom_poi_lc) + 20])
    
    # Si le score strict est trop bas ET que le nom exact n'est pas du tout au début du texte, on rejette
    if score_strict < 45 and nom_poi_lc not in texte_lc[:100]:
        return ""

    # Nettoyage des caractères gênants pour le fichier final
    texte_propre = texte.replace('·', '-').replace('>', ' ').replace(';', ',').replace('"', "'")
    return " ".join(texte_propre.split())


# ============ WIKIPEDIA ============

def chercher_wikipedia(nom_poi, ville, categorie_brute):
    url_api = "https://fr.wikipedia.org/w/api.php"
    mot_cle = DICTIONNAIRE_CATEGORIES.get(categorie_brute, '')
    requete = f"{mot_cle} {nom_poi} {ville} Seine-Maritime".strip()

    try:
        response = SESSION.get(url_api, params={
            "action": "query", "list": "search", "srsearch": requete, "format": "json"
        }, timeout=10)
        if response.status_code != 200:
            return None
            
        resultats = response.json().get("query", {}).get("search", [])
        if not resultats:
            return None

        # On teste uniquement le premier résultat car Wikipédia est très structuré
        titre = resultats[0]["title"]
        
        # Comparaison stricte du titre de la page avec le nom de notre POI
        if fuzz.token_sort_ratio(nom_poi.lower(), titre.lower()) < 50:
            return None

        response_texte = SESSION.get(url_api, params={
            "action": "query", "prop": "extracts", "exintro": True, "explaintext": True, "titles": titre, "format": "json"
        }, timeout=10)

        if response_texte.status_code == 200:
            pages = response_texte.json().get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    extract = page_data.get("extract", "")
                    description_valide = valider_description_strict(extract, nom_poi, ville)
                    if description_valide:
                        return description_valide
    except: pass
    return None


# ============ DUCKDUCKGO ============

def chercher_duckduckgo(nom_poi, ville, categorie_brute):
    mot_cle = DICTIONNAIRE_CATEGORIES.get(categorie_brute, '')
    query = f"{mot_cle} {nom_poi} {ville} Seine-Maritime".strip()

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            for r in results:
                snippet = r.get('body', '')
                
                # On passe le snippet au détecteur de mensonges
                description_valide = valider_description_strict(snippet, nom_poi, ville)
                if description_valide:
                    return description_valide
    except: pass
    return None


# ============ TRAITEMENT PRINCIPAL ============

def process_poi(row):
    id_poi    = row.get('id_poi', '')
    nom       = str(row.get('Nom', '')).strip()        
    categorie = str(row.get('Categorie', '')).strip()
    ville     = str(row.get('Ville', '')).strip()

    # Plan A : Wikipedia
    description = chercher_wikipedia(nom, ville, categorie)
    source = "Wikipedia"

    # Plan B : DuckDuckGo
    if not description:
        time.sleep(DELAY_WEB)
        description = chercher_duckduckgo(nom, ville, categorie)
        source = "DuckDuckGo"

    if description:
        return {
            'id_poi': id_poi, 
            'poi': nom, 
            'ville': ville,
            'categorie': categorie,
            'found': True, 
            'source': source, 
            'description': description
        }
    else:
        return {
            'id_poi': id_poi,
            'poi': nom, 
            'ville': ville,
            'categorie': categorie,
            'found': False, 
            'source': '', 
            'description': ''
        }
    
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, sep=';', encoding='utf-8-sig')
    mask_vide = df['Description_Longue'].isna() | (df['Description_Longue'].astype(str).str.strip() == "")
    df_manquants = df[mask_vide].copy()
    total = len(df_manquants)
    
    print(f"📊 {total} POI à traiter.")
    if total == 0: return

    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)

    trouves, refuses = 0, 0
    for i, (_, row) in enumerate(df_manquants.iterrows()):
        print(f"[{i+1}/{total}] {row['Nom']} ({row['Ville']})")
        resultat = process_poi(row)

        if resultat['found']:
            print(f"   ✅ Trouvé via {resultat['source']}")
            trouves += 1
        else:
            print(f"   ❌ Rejeté (Sécurité stricte).")
            refuses += 1

        append_to_csv(resultat, OUTPUT_FILE)
        time.sleep(DELAY_API)

    print(f"\n🎉 Terminé ! Stats : {trouves} trouvés, {refuses} laissés vides pour sécurité.")

    # --- NETTOYAGE FINAL DES MOTS PARASITES ---
    """    
    Après que la base de données a été donnée à Gemini CLI, qui a identifié les 
    descriptions incohérentes (représentant même pas 10% des descriptions trouvées), 
    on va les supprimer pour être sûr de ne laisser que celles qui sont correctes.
    """
    if os.path.exists(OUTPUT_FILE) and trouves > 0:
        print("Ilimination des descriptions incohérentes...")
        df_output = pd.read_csv(OUTPUT_FILE, sep=';', encoding='utf-8-sig')
        
        IDS_A_SUPPRIMER = [
            397, 522, 643, 1375, 1409, 1562, 1774, 
            2111, 2187, 2539, 2634, 2681, 2728, 2857, 3281
        ]
        
        # On vide la description pour les IDs de la liste noire
        mask_ids = df_output['id_poi'].isin(IDS_A_SUPPRIMER)
        df_output.loc[mask_ids, ['description', 'found', 'source']] = ['', False, '']

        df_output.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8-sig')
        print(f"✨ Nettoyage terminé : {len(IDS_A_SUPPRIMER)} IDs traités. Seules les descriptions correctes sont conservées !")

if __name__ == "__main__":
    main()