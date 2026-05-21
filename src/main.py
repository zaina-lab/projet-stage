from fonctions import map_types_to_category
import pandas as pd
import plotly.express as px
import os

# ======= DATA LOAD ======

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

dossier_du_script = os.path.dirname(os.path.abspath(__file__))
FICHIER_CSV = os.path.join(dossier_du_script, "..", "analyse_poi.csv")
OUTPUT_FILE = 'contacts.csv'

if os.path.exists(FICHIER_CSV):
    df = pd.read_csv(FICHIER_CSV, sep=';', encoding='utf-8-sig') 

    df = df.copy()  # Évite les avertissements de pandas sur les copies de DataFrame
    print(f"✅ Fichier {FICHIER_CSV} chargé avec succès ({len(df)} lignes).")
else:
    print(f"Erreur : Le fichier {FICHIER_CSV} n'existe pas.")
    exit()

# ===== ANALYSE TYPES BRUTS =====
types_series = df['Types'].str.replace(';', '').str.split(',')
all_types = types_series.explode().str.strip()
nb_types = all_types.value_counts()

print("\nNombre de types :", len(nb_types))
#print("\nListe des types uniques :")
#print(nb_types.index.tolist())

df_types = nb_types.reset_index()
df_types.columns = ["Type", "Nombre"]

# ===== VISUALISATION =====

# fig = px.treemap(
#     df_types,
#     path=["Type"],
#     values="Nombre",
#     title="Treemap des types de POI"
# )

# fig.update_traces(
#     hovertemplate="<b>%{label}</b><br>Nombre : %{value}"
# )

# fig.show()

# ===== CATÉGORISATION =====

df["category"] = df["Types"].apply(map_types_to_category)

print("\nRépartition des catégories :")
print(df["Categorie"].value_counts())

# ===== INFO =====

print("\n--- INFO DATAFRAME ---")
df.info()

#print("\n--- DESCRIBE ---")
#print(df.describe(include='all'))

# Combien de POI n'ont ni mail ni téléphone
no_contact = df[(df["Telephone"].isna()) & (df["Email"].isna())]
print("\nNombre de POI sans téléphone ET sans email :", len(no_contact))



# ================ ANALYSES DES CONTACTS MANQUANTS =======================
def analyser_resultats(file_path):
    # Charger le CSV
    df = pd.read_csv(file_path, sep=';')
    total = len(df)

    # Calculer les statistiques
    # On considère "trouvé" si la case n'est pas vide et n'est pas une chaîne vide
    tel_trouves = df['Telephone'].dropna().ne('').sum()
    emails_trouves = df['Email'].dropna().ne('').sum()
    
    # Calculer le taux de succès global (au moins une info trouvée)
    au_moins_un = df[(df['Telephone'].fillna('').ne('')) | (df['Email'].fillna('').ne(''))]
    succes_count = len(au_moins_un)

    print(f"=== ANALYSE DU FICHIER : {file_path} ===")
    print(f"Nombre total de lignes : {total}")
    print("-" * 30)
    print(f"📞 Téléphones récupérés : {tel_trouves} ")
    print(f"📧 Emails récupérés     : {emails_trouves} ")
    print(f"✅ Total avec succès    : {succes_count} ")
    print("-" * 30)
    
    echecs = df[df['Source'] == 'non trouvé']
    if not echecs.empty:
        print(f"⚠️  Nombre de POI qui n'ont ni mail ni téléphone : {len(echecs)}")
# test
analyser_resultats('contacts.csv')



# ================ ANALYSE DES DESCRIPTIONS =======================
print("\n=== ANALYSE DES DESCRIPTIONS ===")
print(f"Total POI : {len(df)}")

# Définition des masques de présence
a_longue = df["Description_Longue"].notna() & (df["Description_Longue"].str.strip() != "")
a_courte = df["Petite_Description"].notna() & (df["Petite_Description"].str.strip() != "")

aucune = (~a_longue) & (~a_courte)

total = len(df)
for label, masque in [
    ("Aucune description (ni longue ni courte) ", aucune),
]:
    n = masque.sum()
    print(f"{label} : {n:>5}  ({n/total*100:.1f}%)")



# ================ FONCTIONS D'ANALYSE PAR CHAMPS =======================
def analyser_completude_colonne(df, nom_colonne, nom_propre):
    print(f"\n=== ÉTAT DE : {nom_propre.upper()} PAR CATÉGORIE (PRÉSENTS VS MANQUANTS) ===")
    
    col_temp = f'a_{nom_colonne}'
    df[col_temp] = df[nom_colonne].notna() & (df[nom_colonne].astype(str).str.strip() != "")
    
    #Groupby et pivotement
    stats = df.groupby('Categorie')[col_temp].value_counts().unstack(fill_value=0)
    
    #Renommer les colonnes dynamiquement
    label_avec = f'Avec {nom_propre}'
    label_sans = f'Sans {nom_propre}'
    stats = stats.rename(columns={True: label_avec, False: label_sans})
    
    # S'assurer que les deux colonnes existent (au cas où il y aurait 0% ou 100% de manquants)
    if label_sans not in stats.columns: stats[label_sans] = 0
    if label_avec not in stats.columns: stats[label_avec] = 0
    
    stats = stats.sort_values(by=label_sans, ascending=False)
    # Affichage du tableau
    print(stats[[label_sans, label_avec]]) # On force l'ordre des colonnes pour le visuel
    
    #Totaux globaux
    total_complets = df[col_temp].sum()
    total_manquants = (~df[col_temp]).sum()
    
    print(f"\nTotal des POI AVEC {nom_propre.lower()} (Complets)  : {total_complets}")
    print(f"Total des POI SANS {nom_propre.lower()} (Manquants) : {total_manquants}")


# ================ ANALYSE DES HORAIRES D'OUVERTURE PAR CATÉGORIE =======================
analyser_completude_colonne(df, nom_colonne='Heure_Ouverture', nom_propre='Horaires d\'ouverture')

# ================ ANALYSE DU PUBLIC CIBLE PAR CATÉGORIE  =======================
analyser_completude_colonne(df, nom_colonne='Public_Cible', nom_propre='Public Cible')

# ================ ANALYSE DU PMR PAR CATÉGORIE  =======================
analyser_completude_colonne(df, nom_colonne='Accessibilite_PMR', nom_propre='Accessibilité PMR')

# ================ ANALYSE DU specification_prix PAR CATÉGORIE  =======================Non trouve
analyser_completude_colonne(df, nom_colonne='specification_prix', nom_propre='Spécification de prix')
