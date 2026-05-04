from lecture import analyse_datatourisme
from fonctions import map_types_to_category
import pandas as pd
import plotly.express as px
import os

# ======= DATA LOAD ======

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

dossier_du_script = os.path.dirname(os.path.abspath(__file__))

FICHIER_CSV = os.path.join(dossier_du_script, "..", "analyse_poi.csv")

if os.path.exists(FICHIER_CSV):
    df = pd.read_csv(FICHIER_CSV, sep=';', encoding='utf-8-sig') 
    df['Types'] = df['Types'].apply(lambda x: x.split(', ') if isinstance(x, str) else [])
    print(f" Fichier {FICHIER_CSV} chargé avec succès ({len(df)} lignes).")
else:
    print(f"Erreur : Le fichier {FICHIER_CSV} n'existe pas. Lance ton script d'analyse d'abord.")
    exit()


# ===== ANALYSE TYPES BRUTS =====

nb_types = df.explode('Types')['Types'].value_counts()

print("\nNombre de types :", len(nb_types))
#print("\nListe des types uniques :")
#print(nb_types.index.tolist())

df_types = nb_types.reset_index()
df_types.columns = ["Type", "Nombre"]

# ===== VISUALISATION =====

fig = px.treemap(
    df_types,
    path=["Type"],
    values="Nombre",
    title="Treemap des types de POI"
)

fig.update_traces(
    hovertemplate="<b>%{label}</b><br>Nombre : %{value}"
)

fig.show()

# ===== CATÉGORISATION =====

df["category"] = df["Types"].apply(map_types_to_category)

print("\nRépartition des catégories :")
print(df["category"].value_counts())

# ===== INFO =====

print("\n--- INFO DATAFRAME ---")
df.info()

#print("\n--- DESCRIBE ---")
#print(df.describe(include='all'))

# Combien de POI n'ont ni mail ni téléphone
no_contact = df[(df["Telephone"].isna()) & (df["Email"].isna())]
print("\nNombre de POI sans téléphone ET sans email :", len(no_contact))

