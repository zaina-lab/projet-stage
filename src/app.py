
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from lecture import analyse_datatourisme
from fonctions import CHAMPS_GENERAUX, MATRICE_CRITICITE, LISTE_CHAMPS

#=========================== COULEURS ET PALETTE =========================================
COLORS = {
    "plot": "#E3E5E8",   

    "violet": "#6c495d",
    "bleu": "#59839f",
    "vert": "#306860",
    "rouge" : "#922A15"
}

palette = [
    "#59839f",       
    "#A5B8C4",            
    "#306860",
    '#6b6f4e',
    "#DCD3D3",            
    "#922A15",     
    "#922A15" ,
    '#694646'            
]

app = Dash(
    __name__, 
    external_stylesheets=[dbc.icons.BOOTSTRAP], # On ne prend QUE les icônes
    update_title=None
)#=========================== LECTURE DES DONNÉES =========================================

# dossier du script actuel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(BASE_DIR, "..", "analyse_poi.csv")
df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')

# On crée df_brut en s'assurant que 'Types' devient une liste pour l'explode
df_brut = df.copy()
df_brut['Types'] = df_brut['Types'].fillna("").apply(
    lambda x: x.split(', ') if isinstance(x, str) and x != "" else []
)

csv_geo = os.path.join(BASE_DIR, "..", "cordinate_verif.csv")
df_geo = pd.read_csv(csv_geo, sep=';')

# Chargement des enrichissements
df_europeana = pd.read_csv(os.path.join(BASE_DIR, "..", "img_europeana.csv"), sep=';')
df_panoramax = pd.read_csv(os.path.join(BASE_DIR, "..", "img_panoramax.csv"), sep=';')

# Fusionner les données pour avoir les catégories dans l'analyse de fiabilité
df_fiabilite_europeana = pd.merge(
    df[['id_poi', 'Nom', 'Categorie']], 
    df_europeana[['id_poi', 'best_score', 'found']], 
    on='id_poi', 
    how='left'
)

df_fiabilite_panoramax = pd.merge(
    df,
    df_panoramax[['id_poi', 'found', 'distance_m', 'image_url']],
    on='id_poi', 
    how='left'
)

#=========================== CHARGEMENT ET PRÉPARATION DES DONNÉES =========================================

df["Categorie"] = df["Categorie"].fillna("Inconnu")



#=========================== la bulle d'aide des graphes et KPIs =========================================
 
def avec_aide(id_unique, description, composant_dash):
    return html.Div([
        html.Div([
            html.I(
                className="bi bi-info-circle", 
                id=f"aide-{id_unique}",
                style={
                    "cursor": "help", 
                    "color": "#59839f", 
                    "fontSize": "1.2rem",
                    "opacity": "0.7"
                }
            ),
            dbc.Tooltip(
                description,
                target=f"aide-{id_unique}",
                placement="left",
                style={
                    "whiteSpace": "pre-line", 
                    "textAlign": "left",
                    "backgroundColor": "rgba(0, 0, 0, 0.9)", 
                    "color": "white",      
                    "padding": "20px",
                    "maxWidth": "500px", 
                    "borderRadius": "10px",
                    "fontSize": "1.1rem",
                    "lineHeight": "1.5",
                    "zIndex": "9999"
                }
            ),
        ], style={
            "position": "absolute", 
            "top": "10px", 
            "right": "15px", 
            "zIndex": "10"
        }),
        composant_dash
    ], style={"position": "relative"})

description_g1 = [

    html.B("📌 CE QUE C'EST"), html.Br(),
    "Un treemap est un graphe en rectangles imbriqués où la taille de chaque rectangle est proportionnelle à une valeur. "
    "Ici, chaque rectangle représente un type de POI (ex : hôtel, Restaurant, Museum …).", 
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "•La colonne 'Types' du fichier 'analyse_poi.csv' ", html.Br(),
    "• Cette colonne peut contenir plusieurs types séparés par des virgules (ex : 'museum, culture'),  le code les explose d'abord avec '.explode()' pour traiter chaque type individuellement", html.Br(),
    "• Il compte ensuite le nombre d'occurrences de chaque type avec '.value_counts()'", html.Br(), html.Br(),
    
    html.B("📊 AFFICHE"), html.Br(),
    "• Chaque case = un type de POI", html.Br(),
    "• La taille de la case = le nombre de POI", html.Br(),
    "• Au survol = le nom du type + le nombre exact", html.Br(), html.Br(),
    
]

description_g2 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
    "Même principe que le Graphe 1,"
     " mais cette fois on visualise les catégories (groupes de haut niveau) et non les types fins.",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• La colonne 'Categorie' du DataFrame principal 'df'",html.Br(), html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Chaque case =  une catégorie de POI", html.Br(),
    "• La taille = le nombre de POI dans cette catégorie", html.Br(),
    "• Au survol = le nom de la catégorie + nombre de POI", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Les grandes cases = les categories les plus représentés dans la base."
    "Si 'évènement'  est énorme et 'Culture' est minuscule, cela signifie que la base est dominée par les évènements."

]

description_g3 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     " Un graphe en barres horizontales qui montre, pour chaque colonne du fichier CSV, combien de POI ont une valeur renseignée (non nulle).",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Tous les champs du DataFrame 'df' (Nom, Ville, Latitude, Téléphone, Email, etc.)",html.Br(),
    "• Il utilise '.notna().sum()' pour compter le nombre de valeurs présentes par colonne", html.Br(), html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Axe Y : le nom de chaque champ", html.Br(),
    "• Axe X : le nombre de POI ayant ce champ renseigné", html.Br(),
    "• Couleur : dégradé du rouge (peu rempli) au bleu (très rempli)", html.Br(),
    "• Trié du moins rempli au plus rempli pour repérer immédiatement les champs problématiques", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Les barres courtes et rouges = les champs souvent manquants.",html.Br(),
    "Les barres longues et bleues = les champs bien renseignés."

]

description_g5 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Un scatter plot met en relation 4 dimensions pour chaque POI. ",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• 'richesse_desc' : longueur de la 'Description_Longue' en nombre de caractères.",html.Br(),
    "• 'score_completude' : score calculé par la fonction 'calc_score()'.",html.Br(),
    "• 'nb_types' : nombre de types associés au POI. ",html.Br(),
    "• 'Categorie' : pour la couleur.", html.Br(), html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Axe Y : richesse de la description (nb de caractères)", html.Br(),
    "• Axe X : score de complétude (0% à 100%)", html.Br(),
    "• Taille du point : nombre de types auquelle il appatient le POI", html.Br(),
    "• Couleur : catégorie du POI", html.Br(),
    "• Au survol : nom, ville, catégorie, description et score de complétude, types", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "En haut à droite = POI riches et bien renseignés. ",html.Br(),
    "En bas à gauche = POI pauvres.",html.Br(),
    "Un POI avec une longue description mais un faible score signifie qu'il a du texte mais manque d'infos pratiques (téléphone, adresse, etc.)."

]

description_g4 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Un histogramme qui montre la distribution des scores de complétude de tous les POI, regroupé par catégorie. ",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• La colonne 'score_completude' calculée par 'calc_score()'",html.Br(),
    "• La colonne 'Categorie' ", html.Br(), html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Axe Y : nombre de POI dans chaque intervalle", html.Br(),
    "• Axe X : valeurs de score (de 0 à 100%)", html.Br(),
    "• Couleur : catégorie", html.Br(),
    "• Les barres sont groupées côte à côte (barmode='group'", html.Br(),html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Si la majorité des barres sont à droite (score > 70%), la base est de bonne qualité globale. ",html.Br(),
    "Si elles sont concentrées à gauche, beaucoup de POI sont incomplets. Comparer les catégories permet de voir laquelle est la mieux documentée.",html.Br(),

]

description_carte = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Une carte géographique interactive affichant tous les POI de la Seine-Maritime. Elle est aussi dynamique : un menu déroulant permet de filtrer par catégorie et de zoomer sur un POI précis.",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Les colonnes 'Latitude' et 'Longitude' du DataFrame",html.Br(),
    "• La colonne 'Description_Longue' : sa longueur détermine la taille du point sur la carte",html.Br(),
    "• La colonne 'Categorie' : détermine la couleur",html.Br(),
    "• La colonne 'Ville' : affichée au survol ", html.Br(), html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Un point par POI géolocalisé", html.Br(),
    "• Taille du point proportionnelle à la richesse de la description ", html.Br(),
    "• Couleur par catégorie", html.Br(),
    "• Au survol : nom du POI, ville, catégorie", html.Br(),
    "• Fond de carte OpenStreetMap", html.Br(),html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Les grands points = POI bien décrits.",html.Br(),
    "Les petits points = peu de description. ",html.Br(),
    "Les zones denses = là où se concentre l'offre touristique.",html.Br(),

]

description_g6 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Un graphe soleil (sunburst) à deux niveaux qui montre la qualité des coordonnées géographiques de chaque POI, décomposée par ville.",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Le fichier 'cordinate_verif.csv'",html.Br(),
    "• La colonne 'Verdict' : résultat de la vérification des coordonnées",html.Br(),
    "• La colonne 'Ville' : ville du POI",html.Br(),
    "• Les villes avec moins de 15 POI sont regroupées dans 'petites villes' pour la lisibilité",html.Br(),html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Anneau intérieur : répartition par verdict ", html.Br(),
    "• Anneau extérieur : décomposition par ville pour chaque verdict", html.Br(),
    "• Au survol : nombre de POI + pourcentage dans le groupe parent", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Plus le vert domine l'anneau intérieur, meilleure est la qualité géographique globale."
     "Les sections rouges ou violettes indiquent des zones à corriger en priorité.",html.Br(),

]


description_g7 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Une heatmap qui croise les catégories de POI (lignes) avec les verdicts de géolocalisation (colonnes). Chaque cellule montre le pourcentage de POI de cette catégorie ayant ce verdict.",
    html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "•Le DataFrame df_geo avec les colonnes categorie et Verdict",html.Br(),
    "•Un tableau croisé (pd.crosstab) normalisé en pourcentages par ligne",html.Br(),html.Br(),

    html.B("📊 AFFICHE"), html.Br(),
    "• Lignes : catégories de POI (food, culture, nature…) ", html.Br(),
    "• Colonnes : verdicts (PARFAIT, OK, ERREUR…)", html.Br(),
    "• Cellule : % des POI de cette catégorie avec ce verdict", html.Br(),
    "• Couleur : du rouge (haut) au bleu (bas) via l'échelle RdBu_r", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Une ligne toute verte = catégorie bien géolocalisée.",html.Br(),
    "Une ligne avec du rouge = catégorie problématique.",html.Br(),
    "Cela permet de prioriser les efforts de correction par type de lieu.",html.Br(),

]

description_g8 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Un graphe en barres empilées horizontales qui montre, pour chaque catégorie,"
     " la proportion de POI ayant obtenu un score de correspondance élevé ou faible avec la base Europeana (base de données culturelle européenne).", html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Le fichier 'europeana.csv' fusionné avec les données POI",html.Br(),
    "• La colonne 'best_score' : score de similarité entre le POI et une fiche Europeana (entre 0 et 1)",html.Br(),
    "• La colonne 'Categorie'",html.Br(),html.Br(),


    html.B("📊 AFFICHE"), html.Br(),
    "• Axe Y : catégories", html.Br(),
    "• Axe X : nombre de POI", html.Br(),
    "• bleu  = Score élevé (bonne correspondance Europeana", html.Br(),
    "• violet = Score faible (correspondance douteuse ou absente) ", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Une barre majoritairement verte foncé = la catégorie est bien enrichie via Europeana. ",html.Br(),
    "Une barre verte claire dominante = peu de POI de cette catégorie ont trouvé une correspondance fiable dans la base culturelle européenne.",html.Br(), html.Br(),

]

description_g9 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Un histogramme qui montre la distance en mètres entre un POI et la photo Panoramax la plus proche trouvée lors de l'enrichissement.",html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Le fichier 'panoramax.csv' fusionné avec les données POI",html.Br(),
    "• La colonne 'found' : booléen indiquant si une photo a été trouvée Seuls les POI avec 'found == True' sont inclus",html.Br(),
    "• La colonne 'distance_m' : distance en mètres entre le POI et la photo",html.Br(),html.Br(),


    html.B("📊 AFFICHE"), html.Br(),
    "• Axe X : distance en mètres", html.Br(),
    "• Axe Y : nombre de POI", html.Br(),
    "• Ligne rouge pointillée : seuil de 20m (précision considérée comme excellente)", html.Br(),
    "• 20 intervalles pour couvrir la distribution ", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Si la majorité des barres sont à gauche du seuil rouge (< 20m),"
    " les photos Panoramax sont très précises et proches des POI. Les barres à droite indiquent des photos trouvées mais éloignées: à vérifier manuellement. ",html.Br(),

]

description_g10 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Un graphique radar (ou toile d'araignée) qui évalue la qualité d'une catégorie de POI selon 9 piliers métier pondérés.",html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Le DataFrame filtré sur la catégorie sélectionnée via le dropdown",html.Br(),
    "• La MATRICE_CRITICITE : définit le poids de chaque champ selon la catégorie ",html.Br(),
    "• Pour chaque pilier, le score = moyenne pondérée des taux de remplissage de ses champs",html.Br(),html.Br(),


    html.B("📊 AFFICHE"), html.Br(),
    "• Une forme en toile pour la catégorie choisie", html.Br(),
    "• Chaque axe va de 0% à 100%", html.Br(),
    "• Plus la surface est grande, meilleure est la qualité globale", html.Br(),
    "• Au survol : score du pilier + liste des champs analysés ", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Un radar aplati sur certains axes = des lacunes dans ces piliers. "
    "Par exemple, un axe 'Contact' à 20% pour les restaurants signifie que 80% des restaurants n'ont pas de téléphone/email renseigné. Idéal pour identifier les points faibles par catégorie."

]

description_g11 = [
    
    html.B("📌 CE QUE C'EST"), html.Br(),
     "Une jauge de style compteur de vitesse qui indique le taux de remplissage d'un champ spécifique pour une catégorie donnée, et évalue si ce manque est critique ou non.",html.Br(), html.Br(),
    
    html.B("📥 EN ENTRÉE"), html.Br(),
    "• Dropdown 1 : la catégorie (ex : food, 'culture', 'activity'…)",html.Br(),
    "• Dropdown 2 : le champ à analyser (ex : 'Telephone', 'Latitude'…) ",html.Br(),
    "• Le 'poids' du champ est récupéré depuis MATRICE_CRITICITE pour la catégorie choisie",html.Br(),
    "• Le taux = % de POI de cette catégorie ayant ce champ renseigné",html.Br(),html.Br(),


    html.B("📊 AFFICHE"), html.Br(),
    "• Une jauge de 0 à 100%", html.Br(),
    "• La valeur numérique du taux en grand", html.Br(),
    "• Le verdict + le poids du champ dans le titre", html.Br(),
    "• Des zones colorées selon le niveau d'alerte ", html.Br(), html.Br(),
    
    html.B("💡 COMMENT LE LIRE"), html.Br(),
    "Si la jauge est dans le rouge avec un poids élevé (ex : Latitude pour les restaurants), c'est une donnée critique manquante qui bloque l'exploitation touristique.  "

]

#=========================== LES GRAPHES DU DIV 1  =========================================

# __________________________Graphique 1 :treemap des types des POI  _____________________

#on explose mes miste des types
df_exploded = df_brut.explode("Types")
#on compte le nombre d'occurences de chaque type + transformation en dataframe
df_types = df_exploded["Types"].value_counts().reset_index()
df_types.columns = ["Type", "Nombre"]

fig_tree = px.treemap(
    df_types,
    path=["Type"],
    values="Nombre",
    title="Treemap des types de POI",
    color_discrete_sequence= palette,
)

fig_tree.update_layout(
    title="Répartition des Types des POI",
    title_x=0.5,
    paper_bgcolor="white",
    plot_bgcolor=COLORS["plot"]
)
fig_tree.update_traces(
    hovertemplate="<b>%{label}</b><br>Nombre : %{value}",
    insidetextfont=dict(size=30),
    texttemplate="<b>%{label}</b><br>%{value}",
)


# __________________________Graphique 2 :treemap de catégories  _____________________

df_tree_cat = df["Categorie"].value_counts().reset_index()
df_tree_cat.columns = ["Categorie", "Nombre"]

fig_tree_cat = px.treemap(
    df_tree_cat,
    path=["Categorie"],
    values="Nombre",
    title="Répartition des catégories des POI",
    color_discrete_sequence=palette,
)
fig_tree_cat.update_layout(
    title="Répartition des catégories de POI",
    title_x=0.5,
    paper_bgcolor="white",
    plot_bgcolor=COLORS["plot"],

)
fig_tree_cat.update_traces(
    hovertemplate="<b>%{label}</b><br>Nombre : %{value}",
    insidetextfont=dict(size=30),
    texttemplate="<b>%{label}</b><br>%{value}",
)


# __________________________Graphique 3 : Taux de remplissage par champ _____________________

custom_colorscale = [COLORS["rouge"], "#59839f"]

# On calcule le nombre de valeurs présentes (non-nulles) pour chaque colonne
df_missing = df.notna().sum().reset_index()
df_missing.columns = ["Champ", "Nombre"]

# On trie par le plus rempli pour que ce soit plus lisible
df_missing = df_missing.sort_values(by="Nombre", ascending=True)

fig_missing = px.bar(
    df_missing,
    x="Nombre",
    y="Champ",
    orientation='h',  
    text="Nombre", 
    color="Nombre",
    color_continuous_scale= custom_colorscale
)

fig_missing.update_layout(
    title="Nombre de valeurs renseignées par champ",
    title_x=0.5,
        paper_bgcolor="white",
        plot_bgcolor=COLORS["plot"],
        xaxis=dict(
            title = "Nombre_Present",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
        ),
        yaxis=dict(
            title = "Champs",
            showgrid=False
        ),

        margin=dict(l=100, r=40, t=60, b=40),
        coloraxis_showscale=False
)

fig_missing.update_traces(
    textposition="outside",
    hovertemplate="Champ : %{y}<br>Remplis : %{x}"
)

# __________________________Graphique 4 : longueur de la description vs Remplissage des champs _____________________

def calc_score(df):
    def calculer_ligne(row):
        cat = str(row["Categorie"]).lower()
        weights_spec = MATRICE_CRITICITE.get(cat, {})
        full_config = CHAMPS_GENERAUX.copy()
        full_config.update(weights_spec)
        
        #On définit nos groupes (L'un ou l'autre suffit)
        groupes = {
            'contact': ['Telephone', 'Email'],
            'reservation': ['Telephone_Reservation', 'Email_Reservation']
        }
        
        score_obtenu = 0
        totale = 0
        tous_les_champs_groupes = [item for sublist in groupes.values() for item in sublist]

        #Traitement des groupes, Logique du MAX
        for nom_groupe, liste_champs in groupes.items():
            poids_presents = []
            for c in liste_champs:
                val = row.get(c)
                if pd.notna(val) and str(val).strip() not in ["", "nan", "NaN"]:
                    poids_presents.append(full_config.get(c, 0))
                else:
                    poids_presents.append(0)
            
            # On ajoute le meilleur score du groupe au score obtenu
            score_obtenu += max(poids_presents) if poids_presents else 0
            # On ajoute le poids maximal possible du groupe au dénominateur (total)
            totale += max([full_config.get(c, 0) for c in liste_champs]) if liste_champs else 0

        #Traitement de tous les autres champs 
        for champ, poids in full_config.items():
            if poids <= 0 or champ in tous_les_champs_groupes:
                continue
            totale += poids
            if champ in row:
                valeur = row[champ]
                if pd.notna(valeur) and str(valeur).strip() not in ["", "nan", "NaN"]:
                    score_obtenu += poids
        if totale == 0: 
            return 0
        return (score_obtenu / totale) * 100
    return df.apply(calculer_ligne, axis=1)


df_analyse = df.copy()
df_analyse["score_completude"] = calc_score(df)

# Score de présence géographique (normalisé sur 100)
df_analyse["score_geo"] = (
    ((df["Latitude"].notna()) & (df["Longitude"].notna())).astype(int) +
    df["Ville"].notna().astype(int) +
    ((df["Rue"].notna()) & (df["Code_Postal"].notna())).astype(int)
) / 3 * 100

df_analyse["nb_types"] = df["Types"].fillna("").apply(lambda x: len(x.split(",")) if x != "" else 1)
df_analyse["types_liste"] = df["Types"].fillna("").apply(lambda x: "<br>".join([t.strip() for t in x.split(",")]) if x != "" else "")
df_analyse["richesse_desc"] = df_analyse["Description_Longue"].fillna("").str.len()

fig_scatter = px.scatter(
    df_analyse,
    x="richesse_desc",
    y="score_completude",
    size="nb_types",
    color="Categorie",
    color_discrete_sequence=palette,
    title="Longueur de la description vs Remplissage des champs ",
    size_max=40,
    opacity=0.6,
)

fig_scatter.update_traces(
    customdata=df_analyse[[
        "Nom",
        "Ville",
        "Categorie",
        "types_liste",
        "nb_types"
    ]],
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"   
        "📍 %{customdata[1]}<br>"       
        "🏷️ %{customdata[2]}<br>"       
        "──────────────────<br>"
        "Description : %{x} caractères<br>"
        "Complétude : %{y:.1f}%<br>"
        "Types : %{customdata[4]}<br>"
        "──────────────────<br>"
        "<i>%{customdata[3]}</i>"
        "<extra></extra>"
    )
)

fig_scatter.update_layout(
    title_x=0.5,
    paper_bgcolor="white",
    plot_bgcolor=COLORS["plot"],
    xaxis=dict(
        title="nombre de caractères de la description",
        showgrid=True, 
        gridcolor="rgba(0,0,0,0.05)"
    ),
    yaxis=dict(
        title="Complétude (%)", 
        showgrid=True, 
        gridcolor="rgba(0,0,0,0.05)"),
        legend=dict(title="Catégorie"
    ),
    margin=dict(l=60, r=40, t=60, b=40),

)
# __________________________Graphique 5 : Histogramme du score de complétude _____________________

fig_hist_score = px.histogram(
    df_analyse,
    x="score_completude",
    nbins=15,
    color="Categorie",
    barmode="group",
    opacity=0.65,
    color_discrete_sequence=palette,
    title="Distribution de la qualité des POI",
)

fig_hist_score.update_layout(
    bargap=0.05,  
    paper_bgcolor="white",
    plot_bgcolor=COLORS["plot"],
    title_x=0.5
)


#=========================== CALCUL DES KPIs ========================


# KPI 1 — Score de complétude globale :
def kpi_score_qualite(df):
    return round(calc_score(df).mean(), 1)


# KPI 2 — CONTACTABILITÉ : au moins UN (téléphone ou email)
# KPI 3 — POI RÉSERVATION
# KPI 4 — POI animaux autorisés
# KPI 6 — POI avec informations de dates exploitables

def kpi_pondere(df, champs, test=None):
    score_total_obtenu = 0
    score_total_max_possible = 0
    for index, row in df.iterrows():
        cat = str(row["Categorie"]).lower()
        weights_spec = MATRICE_CRITICITE.get(cat, {})
        
        # Le poids max (si un seul champ, c'est juste le poids du champ)
        poids_max_cat = max([weights_spec.get(c, 0) for c in champs])
        if poids_max_cat == 0: 
            continue 
        if test:
            est_valide = any(test(row.get(c)) for c in champs)
        else:
            est_valide = any(pd.notna(row.get(c)) and str(row.get(c)).strip() not in ["", "nan", "NaN"] for c in champs)
        
        if est_valide:
            score_total_obtenu += poids_max_cat
        score_total_max_possible += poids_max_cat

    return round((score_total_obtenu / score_total_max_possible) * 100, 1) if score_total_max_possible > 0 else 0


# KPI 5 — RICHESSE DES DONNÉES : Longueur du texte > 200 caractères donc c'est riche
def kpi_description_riche(df):
    return round((df["Description_Longue"].fillna("").str.len() > 200).mean() * 100, 1)


# KPI 7 — GÉOLOCALISATION
def kpi_geo_complet(df):
    return round(
        ((df["Latitude"].notna()) & (df["Longitude"].notna())).mean() * 100, 1)

#On définit la règle du jeu pour les dates
test_horaire = lambda x: isinstance(x, str) and len(x) > 10 #mpour eviter les "Sur rdv" et accepter les "09:00-12:00, 14:00-18:00" (25 caractères)

kpi1 = f"{kpi_score_qualite(df)} %"
kpi2 = f"{kpi_pondere(df, ['Telephone', 'Email'])} %"
kpi3 = f"{kpi_pondere(df, ['Telephone_Reservation', 'Email_Reservation'])} %"
kpi4 = f"{kpi_pondere(df, ['Animaux_Autorises'])} %"
kpi5 = f"{kpi_description_riche(df)} %"
kpi6 = f"{kpi_pondere(df, ['Heure_Ouverture'], test=test_horaire)} %"
kpi7 = f"{kpi_geo_complet(df)} %"   
 

#=========================== TOP 3 POI ========================


top_bad = df_analyse.sort_values("score_completude").head(3)
top_good = df_analyse.sort_values("score_completude", ascending=False).head(3)

def top_3_poi(df, titre, couleur):
    df = df.copy()
    # On trie et on arrondit
    df = df.sort_values("score_completude", ascending=True)
    df["score_arrondi"] = df["score_completude"].round(1)

    fig = go.Figure()

    # Barre de fond (Grise à 100%)
    fig.add_trace(go.Bar(
        y=df["Nom"],
        x=[100] * len(df),
        orientation='h',
        marker_color="#EEEEEE",
        hoverinfo='skip',
        showlegend=False,
        width=0.5
    ))

    # Barre de progression (La vraie valeur)
    fig.add_trace(go.Bar(
        y=df["Nom"],
        x=df["score_arrondi"],
        orientation='h',
        marker_color=couleur,
        text=df["score_arrondi"].astype(str) + " %",
        textposition="outside",
        showlegend=False,
        width=0.5
    ))

    # Mise en page
    fig.update_layout(
        barmode="overlay", # superposition
        title=dict(text=titre, x=0.5, font=dict(size=14)),
        height=250,
        margin=dict(l=150, r=60, t=50, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 115]),
        yaxis=dict(showgrid=False, zeroline=False, automargin=True),
    )

    fig.update_traces(cliponaxis=False)

    return fig

#=========================== CARTES ========================
palette = [
    "#284f6b",  # bleu fort
    "#702222",  # rouge
    "#225122",  # vert
    "#934806",  # orange
    "#4b3d58",  # violet
    "#26757e",  # cyan
]

fig_map = px.scatter_map(
    df,
    lat="Latitude",
    lon="Longitude",
    size=df["Description_Longue"].fillna("").str.len(),
    size_max=30,
    zoom=8,
    hover_name="Nom",
    custom_data=["Ville", "Categorie"],
    color="Categorie",
    color_discrete_sequence= palette,
)

fig_map.update_traces(
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "📍 %{customdata[0]}<br>"
        "🏷️ %{customdata[1]}"
        "<extra></extra>"
    )
)

fig_map.update_layout(
    map_style="open-street-map",
    margin=dict(l=0, r=0, t=0, b=0),
    height=500
)
#=========================== LES GRAPHES DU DIV 1  =========================================

# __________________________Graphique 6 : Sunburst de la qualité des coordonnées geographqiues  _____________________


def geo_sunburst(df_geo):
    dff = df_geo.copy()
    
    #on harmonise les noms de villes
    dff['Ville'] = dff['Ville'].fillna('Inconnue').str.upper().str.strip()
    
    #On groupe les "petites" villes (moins de 15 POI) pour la lisibilité
    counts = dff['Ville'].value_counts()
    villes_principales = counts[counts >= 15].index
    dff['Ville_Affichee'] = dff['Ville'].apply(lambda x: x if x in villes_principales else "petites villes")

    #Création du Sunburst
    # Centre : Verdict et Extérieur : Ville
    fig = px.sunburst(
        dff,
        path=['Verdict', 'Ville_Affichee'],
        color='Verdict',
        color_discrete_map={
            "PARFAIT Ville+CP+Rue": COLORS["vert"],
            "OK Ville+CP ": COLORS["bleu"],
            "A VERIFIER Ville|CP ": "#4b3d58",
            "ERREUR": COLORS["rouge"],
            "NON_TROUVE": "#DCD3D3"
        }
    )

    fig.update_layout(
        title="Précision des Coordonnées par ville",
        title_x=0.5,
        margin=dict(l=60, r=40, t=60, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600
    )

    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Nombre de POI : %{value}<br>Part : %{percentParent:.1%}"
    )
    return fig

# __________________________Graphique 7 : Heatmap de la qualité des coordonnées geographqiues par catécorie   _____________________

def geo_heatmap(df_geo):
    if df_geo.empty:
        return go.Figure().update_layout(title="Aucune donnée")

    # On crée un tableau croisé : Catégorie vs Verdict
    df_pivot = pd.crosstab(df_geo['categorie'], df_geo['Verdict'], normalize='index') * 100

    fig = px.imshow(
        df_pivot,
        labels=dict(x="Verdict", y="Categorie de lieu", color="Pourcentage (%)"),
        x=df_pivot.columns,
        y=df_pivot.index,
        color_continuous_scale='RdBu_r',
        aspect="auto"
    )

    fig.update_layout(
        title="Fiabilité selon le type de point d'intérêt",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600
    )
    
    return fig

# __________________________ Graphique 8 : Fiabilité Europeana _____________________

def europeana_fiabilite(df_merge):
    # On nettoie les scores
    df_merge['best_score'] = pd.to_numeric(df_merge['best_score'], errors='coerce').fillna(0)
    
    def calcul_statut(row):
        cat = str(row['Categorie']).lower()
        score = row['best_score']
        
        # Pour le culturel, on accepte un score raisonnable
        if cat in ['culture', 'nature', 'event']:
            return "Score élevé" if score >= 0.5 else "Score faible"
        
        # Pour le reste (Hôtels, Restos), on est sera plus exigeant (0.95 minimum) car on veut éviter les homonymes historiques
        else:
            return "Score élevé" if score >= 0.95 else "Score faible"
        
    df_merge['Statut'] = df_merge.apply(calcul_statut, axis=1)
    
    
    fig = px.bar(
        df_merge.groupby(['Categorie', 'Statut']).size().reset_index(name='Nombre'),
        x="Nombre",
        y="Categorie",
        color="Statut",
        barmode="stack",
        orientation='h',
        color_discrete_map={
            "Score élevé": COLORS["bleu"],
            "Score faible": "#4b3d58"
        }
    )
    fig.update_layout(
        title="Qualité de l'enrichissement Europeana",
        title_x=0.5,
        paper_bgcolor='white', 
        plot_bgcolor=COLORS["plot"], 
    )
    
    return fig


# __________________________ Graphique 9 :histgrarmme Précision Panoramax _____________________

def create_panoramax_dist(df_p):
    # Filtrer uniquement là où on a trouvé une image
    df_found = df_p[df_p['found'] == True].copy()
    
    fig = px.histogram(
        df_found,
        x="distance_m",
        nbins=20,
        title="Distance POI vs Photo Panoramax (m)",
        color_discrete_sequence=["#13263b"]
    )
    # Ajouter une ligne verticale pour le seuil de 20m 
    fig.add_vline(x=20, line_dash="dash", line_color=COLORS["rouge"], annotation_text="Seuil de précision")
    
    fig.update_traces(
            marker_line_color="white", # une fine ligne blanche entre les barres
            marker_line_width=1,
            opacity=0.85 # Un peu de transparence 
        )

    fig.update_layout(
        paper_bgcolor='white', 
        plot_bgcolor=COLORS["plot"], 
        title_x=0.5,
        bargap=0.05
    )
    return fig

# __________________________ Graphique 10 :radar chart des pilier suivant _____________________

PILIERS = {
    'Sources' : ['URI_DataTourisme', 'Date_creation', 'Créateur', 'Publié_par','Date_update', 'Date_update_Datatourisme', 'Sources Exterieures', 'INSEE_Code'],
    'Horaires': ['Heure_Ouverture'],
    'Localisation': ['Latitude', 'Longitude', 'Ville', 'Code_Postal', 'Rue'],
    'Contact': ['Telephone', 'Email', 'Telephone_Reservation', 'Email_Reservation'],
    'Description': ['Petite_Description', 'Description_Longue', 'Themes'],
    'Accessibilité': ['Accessibilite_PMR', 'Public_Cible', 'Animaux_Autorises'],
    'Services': ['Equipements', 'Type_Cuisine'],
    'Prix': ['specification_prix'],
    'Media': ['Media']
}

def generer_radar_chart(df, categorie_choisie):
    if categorie_choisie is None:
        return go.Figure()

    # On filtre sur la catégorie
    cat_lower = categorie_choisie.lower()
    df_cat = df[df['Categorie'].str.lower() == cat_lower]
    
    if df_cat.empty:
        return go.Figure()

    # On récupère la config spécifique de cette catégorie
    weights_spec = MATRICE_CRITICITE.get(cat_lower, {})
    full_config = CHAMPS_GENERAUX.copy()
    full_config.update(weights_spec)

    labels = list(PILIERS.keys())
    values = []
    text_hover = []

    #Calcul pondéré par pilier
    for pilier, colonnes in PILIERS.items():
        score_pilier = 0
        poids_total_pilier = 0
        champs_presents = []
        
        for col in colonnes:
            poids = full_config.get(col, 1) # Par défaut 1 si absent
            if poids == 0: 
                continue # On ignore les champs exclus 
            
            # Taux de remplissage de la colonne 
            taux_remplissage = df_cat[col].notna().mean()
            
            # On pondère ce remplissage par l'importance du champ
            score_pilier += (taux_remplissage * poids)
            poids_total_pilier += poids

            champs_presents.append(f"- {col}")
        
        # Calcul du % final pour ce pilier
        if poids_total_pilier > 0:
            values.append((score_pilier / poids_total_pilier) * 100)
        else:
            values.append(0)

        text_hover.append("<br>".join(champs_presents))

    # 4. Création du graphique
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        customdata=text_hover,
        hovertemplate=(
            "<b>Pilier : %{theta}</b><br>" +
            "Score : %{r:.1f}%<br>" +
            "-------------------<br>" +
            "<i>Champs analysés :</i><br>" +
            "%{customdata}" + # Affiche la liste des champs
            "<extra></extra>"
        ),
        line_color="#4C1F16", # Utilisation de ton rouge pour l'alerte qualité
        marker=dict(size=8)
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height = 450,
        title={
            'text': f"Analyse de la Qualité Métier par Pilier — {categorie_choisie.capitalize()}",
            'x': 0.5,
            'xanchor': 'center',
        },
        
    )
    return fig

# __________________________ Graphique 11 :Speedometer de la criticité des champs par rapport a chaque categorie _____________________

def speedometer(cat, champ):
    if not cat or not champ:
        return go.Figure()

    # Calcul du taux
    df_cat = df[df['Categorie'] == cat]
    taux = df_cat[champ].notna().mean() * 100
    
    #Récupération du poids
    poids = MATRICE_CRITICITE.get(cat.lower(), {}).get(champ, CHAMPS_GENERAUX.get(champ, 1))

    #Détermination du Verdict et des Couleurs
    if poids >= 4 and taux < 90:
        verdict = "MANQUE BLOQUANT 🔴"
        couleur_barre = COLORS["rouge"]
        zones = [{'range': [0, 90], 'color': "rgba(146, 42, 21, 0.4)"}, 
                 {'range': [90, 100], 'color': "rgba(48, 104, 96, 0.2)"}]
    elif poids >= 2 and taux < 70:
        verdict = "MANQUE IMPORTANT 🟡"
        couleur_barre = "orange"
        zones = [{'range': [0, 70], 'color': "rgba(255, 165, 0, 0.4)"}, 
                 {'range': [70, 100], 'color': "rgba(48, 104, 96, 0.2)"}]
    else:
        verdict = "PETIT MANQUE | OK 🟢"
        couleur_barre = COLORS["vert"]
        zones = [{'range': [0, 100], 'color': "rgba(48, 104, 96, 0.2)"}]

    #Création de la jauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = taux,
        number = {'suffix': "%", 'font': {'size': 60}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': couleur_barre},
            'steps': zones,
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    fig.update_layout(
        height=400, 
        margin=dict(t=120, b=20, l=30, r=30),
        title={
            'text': (
                f"<b>Niveau de Complétude Critique : {cat}</b><br>"
                f"<span style='font-size:1.1em; color:#2c3e50'>Champ : {champ}</span><br>"
                f"<span style='font-size:0.9em; color:gray'>{verdict} (Poids: {poids})</span>"
            ),
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )
    
    return fig

#=========================== DASH INTERFACE =================================================

app.layout = html.Div([
    # ===== TITRE =====
    html.Div(
        "Analyse des Points d'Intérêt  ",
        className="page-title"

    ),

    html.Div(
        className="main_container_1",
        children=[
            html.Table(
                className="table-principale",
                children=[

                    # 1ERE ligne :
                    # 1IERE cellule: ---------------------------------- GRAPHES-------------------------------------
                    html.Tr([
                        html.Td(
                            html.Div(
                                className="Les_Graphes",
                                children=[
                                    avec_aide(
                                        "aide-g1",
                                        description_g1,
                                        dcc.Graph(
                                            id="g1",
                                            figure=fig_tree,
                                            config={'displayModeBar': False}
                                        ),
                                    ),

                                    avec_aide(
                                        "aide-g2",
                                        description_g2,    
                                        dcc.Graph(
                                            id="g2",
                                            figure=fig_tree_cat,
                                            config={'displayModeBar': False}
                                        ),
                                    ),


                                    avec_aide(
                                        "aide-g3",
                                        description_g3,   
                                        dcc.Graph(
                                            id="g3",
                                            figure=fig_missing,
                                            config={'displayModeBar': False}
                                        ),
                                    ),


                                    avec_aide(
                                        "aide-g5",
                                        description_g5,                                   
                                        dcc.Graph(
                                            id="g5",
                                            figure=fig_scatter,
                                            config={'displayModeBar': False},  
                                        ),
                                    ),
                                ]
                            ),
                            className="colonne-gauche",
                            style={'width': '50%'}
                        ),

                        #2 IEME cellule:----------------------------- KPIs -----------------------------------------------
                        html.Td(
                            html.Div(
                                className="KPIs_1",
                                children=[
                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi1,
                                                                id="kpi1",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "Score de complétude global", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi1.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon"
                                                )
                                            ])
                                        ]
                                    ),

                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi2,
                                                                id="kpi2",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "POI contactables", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi2.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon"
                                                )
                                            ])
                                        ]
                                    ),

                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi3,
                                                                id="kpi3",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "POI avec contact de réservation", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi3.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon")
                                            ])
                                        ]
                                    ),
                                    

                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi4,
                                                                id="kpi4",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "POI acceptant les animaux", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi4.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon")
                                            ])
                                        ]
                                    ),

                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi5,
                                                                id="kpi5",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "POI avec description riche (+200 caractères)", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi5.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon")
                                            ])
                                        ]
                                    ),

                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi6,
                                                                id="kpi6",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "POI avec horaires d'ouverture exploitables", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi6.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon")
                                            ])
                                        ]
                                    ),

                                    html.Div(
                                        className="KPI_box",
                                        children=[
                                            html.Div(
                                                className="kpi_content", 
                                                children=[
                                                    html.Div(
                                                        className="kpi_text", 
                                                        children=[
                                                            html.Div(
                                                                kpi7,
                                                                id="kpi7",
                                                                className="kpi_value"),
                                                            html.Div(
                                                                "POI avec géolocalisation", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="assets/kpi7.png",
                                                        className="kpi_icon_img",
                                                    ),
                                                    className="kpi_icon")
                                            ])
                                        ]
                                    ),

                                    html.Div(
                                        #className="Les_Graphes",
                                        children=[
                                            # carrée du top3 
                                            dcc.Graph(
                                                figure=top_3_poi(top_bad, "TOP 3 - POI les moins complets", "#742727"),
                                                config={'displayModeBar': False},
                                                id="top3_bad",
                                                className = "top3_poi"
                                            ),    
                                        ]
                                    ),

                                    html.Div(   
                                        className="Les_Graphes",                                        
                                        children=[ 
                                            avec_aide(
                                                "aide-g4",
                                                description_g4,   
                                                dcc.Graph(
                                                    id="g4",
                                                    figure=fig_hist_score,
                                                    config={'displayModeBar': False}
                                                ),
                                            ),
                                        ]
                                    ),

                                ]
                            ),
                            className="colonne-droite",
                            style={'width': '50%'}
                        ),  
                ]),

                html.Div([
                    html.Div([
                        # Bloc Catégorie
                        html.Div([
                            html.Label("1. Filtrer par Catégorie :"),
                            dcc.Dropdown(
                                id='select-categorie',
                                options=[{'label': c, 'value': c} for c in sorted(df_analyse['Categorie'].unique())],
                                placeholder="Toutes les catégories",
                                className="dropdown"
                            ),
                        ]),

                        # Bloc POI
                        html.Div([
                            html.Label("2. Rechercher et Zoomer sur un POI :", className="label-filtre"),
                            dcc.Dropdown(
                                id='select-poi', 
                                placeholder="Sélectionnez un lieu...", 
                                className="dropdown"
                            ),
                        ]),

                    ], 
                    className="les_filtres") 

                ]),

                # 3IEME ligne :
                # 1IERE cellule: -----------------------------------------------------------------------
                
                html.Tr([
                    html.Td(
                        html.Div(
                            className="Carte_1",
                            children=[
                                avec_aide(
                                    "aide-carte",
                                    description_carte,   
                                    dcc.Graph(
                                        className="carte_graph_1",
                                        id="map1",
                                        figure=fig_map,
                                        config={'displayModeBar': False},
                                    )
                                ),
                            ]
                        ),
                        colSpan=2
                    ),
                ]),
            ]),  
        ]),
        
        html.Div(
            "Bilan de fiabilité de la base de données",
            className="page-title"

        ), 
        html.Div(
            className="main_container_1",
            children=[
                html.Table(
                    className="table-principale",
                    children=[     

                        html.Tr([
                            html.Td(
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        avec_aide(
                                            "aide-g6",
                                            description_g6,   
                                            dcc.Graph(
                                                id="sunburst-qualite",
                                                figure=geo_sunburst(df_geo), 
                                                config={'displayModeBar': False}
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            html.Td(
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        avec_aide(
                                            "aide-g7",
                                            description_g7,
                                            dcc.Graph(
                                                id="heatmap-qualite",
                                                figure=geo_heatmap(df_geo), 
                                                config={'displayModeBar': False}
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                        ]),

                        # Dans ton app.layout, à l'intérieur de ton html.Table
                        html.Tr([
                            html.Td(
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        avec_aide(
                                            "aide-g8",
                                            description_g8,
                                            dcc.Graph(
                                                id="europeana-bar",
                                                figure=europeana_fiabilite(df_fiabilite_europeana), 
                                                config={'displayModeBar': False}
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                            html.Td(
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        avec_aide(
                                            "aide-g9",
                                            description_g9,
                                            dcc.Graph(
                                                id="panoramax-hist",
                                                figure=create_panoramax_dist(df_fiabilite_panoramax), 
                                                config={'displayModeBar': False}
                                            ),
                                        ),
                                    ]
                                ),
                            ),

                        ]),

                        html.Tr([
                            html.Td([
                                html.Div([
                                    html.Label(" Filtrer par Catégorie :"),
                                    dcc.Dropdown(
                                        id='selection-categorie-radar',
                                        options=[{'label': c, 'value': c} for c in sorted(df_analyse['Categorie'].unique())],
                                        value='food',
                                        clearable=False,
                                        placeholder="Toutes les catégories",
                                        className="dropdown"
                                    ),
                                ]),
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        avec_aide(
                                            "aide-g10",
                                            description_g10,
                                            dcc.Graph(
                                                id='radar-chart-qualite',
                                                figure={}, 
                                                config={'displayModeBar': False}
                                            ),
                                        ),
                                    ]
                                ),
                        ]),
                            html.Td([
                                html.Div([
                                    html.Label("1. Filtrer par Catégorie :"),
                                    dcc.Dropdown(
                                        id='selection-categorie-criticite',
                                        options=[{'label': c, 'value': c} for c in sorted(df_analyse['Categorie'].unique())],
                                        value='activity',
                                        clearable=False,
                                        placeholder="Toutes les catégories",
                                        className="dropdown"
                                    ),
                                ]),

                                html.Div([
                                    html.Label("2. Choisir un Champ à analyser :"),
                                    dcc.Dropdown(
                                        id='selection-champs-criticite',
                                        options=[{'label': c, 'value': c} for c in LISTE_CHAMPS],
                                        value='Nom',
                                        clearable=False,
                                        placeholder="Sélectionnez d'abord une catégorie",
                                        className="dropdown"
                                    ),
                                ]),

                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        avec_aide(
                                            "aide-g11",
                                            description_g11,
                                            dcc.Graph(
                                                id="gauge-criticite",
                                                figure={}, 
                                                config={'displayModeBar': False}
                                            ),
                                        ),
                                    ]
                                ),
                        ]),

                        ]),
                    ]),
            ]),
    ])



# ====================================  SELECIONNER UN POI DANS LA CARTE ===========================# --- CALLBACK 1 : Mise à jour des listes ---

@app.callback(
    Output('select-poi', 'options'),
    Input('select-categorie', 'value'),
)
def update_dropdowns(cat_val):
    dff = df_analyse.copy()
    
    # Si une catégorie est choisie, on filtre les noms
    if cat_val:
        dff = dff[dff['Categorie'] == cat_val]
    
    # On retourne directement la liste des noms
    poi_options = [{'label': n, 'value': n} for n in sorted(dff['Nom'].unique())]
    
    return poi_options

@app.callback(
    Output("map1", "figure"),
    Input("select-poi", "value"),
    Input("select-categorie", "value") 
)

def update_carte(poi, cat_val):
    dff = df_analyse.copy()

    # Si une catégorie est sélectionnée, on filtre les points affichés sur la carte
    if cat_val:
        dff_map = dff[dff['Categorie'] == cat_val]
    else:
        dff_map = dff

    fig = px.scatter_map(
        dff_map, 
        lat="Latitude",
        lon="Longitude",
        size=dff_map["Description_Longue"].fillna("").str.len(),
        size_max=30,
        color="Categorie",
        color_discrete_sequence=palette,
        hover_name="Nom",
        custom_data=["Ville", "Categorie"],
        zoom=8,
        center={"lat": dff["Latitude"].mean(), "lon": dff["Longitude"].mean()}
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "📍 %{customdata[0]}<br>"
            "🏷️ %{customdata[1]}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        map_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0},
        height=500
    )

    # Zoom sur le POI
    if poi:
        poi_data = dff[dff["Nom"] == poi].iloc[0]
        lat, lon = poi_data["Latitude"], poi_data["Longitude"]
        fig.update_layout(
            map=dict(
                center={"lat": lat, "lon": lon},
                zoom=15,
                style="open-street-map"
            ),
        )

        fig.add_trace(
            go.Scattermap(
                lat=[lat],
                lon=[lon],
                mode="markers",
                marker=dict(size=20, color="red"),
                name="",
                hoverinfo="skip",
            )
        )
    return fig


@app.callback(
    Output('radar-chart-qualite', 'figure'),
    Input('selection-categorie-radar', 'value')
)
def update_radar(cat):
    if not cat:
        return go.Figure()
    return generer_radar_chart(df_analyse, cat)

@app.callback(
    Output('gauge-criticite', 'figure'),
    [Input('selection-categorie-criticite', 'value'),
     Input('selection-champs-criticite', 'value')]
)
def update_criticite(cat, champ):
    if not cat or not champ :
        return go.Figure()
    return speedometer(cat, champ)


if __name__ == "__main__":
    app.run(debug=True, port=8051)