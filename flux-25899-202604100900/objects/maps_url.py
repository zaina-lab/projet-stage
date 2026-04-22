import pandas as pd
import urllib.parse
import os

INPUT_FILE = 'analyse_poi.csv'
OUTPUT_FILE = 'maps_urls.csv'

#Charger le fichier CSV des POIs
try:
    df = pd.read_csv(INPUT_FILE, sep=None, engine='python', encoding='utf-8')
except Exception as e:
    print(f"Erreur lors de la lecture : {e}")


df_maps = pd.DataFrame()

#Fonction pour construire l'URL 
def creer_url_google(row):
    # On récupère le nom, la ville, lat, lon
    nom = str(row['Nom'])
    lat = str(row['Latitude'])
    lon = str(row['Longitude'])
    
    # On encode pour que les espaces et accents deviennent lisibles par URL
    query = urllib.parse.quote(f"{lat},{lon}({nom})")
    
    # On construit l'URL finale avec les coordonnées pour être ultra précis
    return f"https://www.google.com/maps/search/?api=1&query={query}"

df_maps['Nom'] = df['Nom']
df_maps['latitude'] = df['Latitude']
df_maps['longitude'] = df['Longitude']
df_maps['found'] = df['Latitude'].notna()

#On crée la nouvelle colonne 'google_maps_url'
#La fonction s'applique à chaque ligne (axis=1)
df_maps['google_maps_url'] = df.apply(creer_url_google, axis=1)


if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"Ancien fichier {OUTPUT_FILE} supprimé. Création d'un nouveau.")


#on sauvegarde le résultat dans un nouveau fichier CSV
df_maps.to_csv(OUTPUT_FILE, sep=';', index=False, encoding='utf-8-sig')
