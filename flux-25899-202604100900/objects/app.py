
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from lecture import analyse_datatourisme

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

app = Dash(__name__)

#=========================== LECTURE DES DONNÉES =========================================

# dossier du script actuel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df_brut = analyse_datatourisme(BASE_DIR)

# chemin vers le CSV 
csv_path = os.path.join(BASE_DIR, "..", "../analyse_poi.csv")
df = pd.read_csv(csv_path, sep=';')

csv_geo = os.path.join(BASE_DIR, "..", "../cordinate_test.csv")
df_geo = pd.read_csv(csv_geo, sep=';')

# Chargement des enrichissements
df_europeana = pd.read_csv(os.path.join(BASE_DIR, "..", "../europeana.csv"), sep=';')
df_panoramax = pd.read_csv(os.path.join(BASE_DIR, "..", "../panoramax.csv"), sep=';')

# Fusionner les données pour avoir les catégories dans l'analyse de fiabilité
df_fiabilite_europeana = pd.merge(
    df[['id_poi', 'Nom', 'Categorie']], 
    df_europeana[['id_poi', 'best_score', 'found']], 
    on='id_poi', 
    how='left'
)
print(f"Taille finale : {len(df_fiabilite_europeana)}")

df_fiabilite_panoramax = pd.merge(
    df,
    df_panoramax[['id_poi', 'found', 'distance_m', 'image_url']],
    on='id_poi', 
    how='left'
)

print(f"Taille finale : {len(df_fiabilite_panoramax)}")

#=========================== CHARGEMENT ET PRÉPARATION DES DONNÉES =========================================

df["Categorie"] = df["Categorie"].fillna("Inconnu")

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

def calc_score_individuel(df):
    return (
        # CRITIQUE 
        3 * ((df["Latitude"].notna()) & (df["Longitude"].notna())).astype(int) +
        3 * ((df["Telephone"].notna()) | (df["Email"].notna())).astype(int) +

        # IMPORTANT
        2 * df["Nom"].notna().astype(int) +
        2 * df["Description"].notna().astype(int) +
        2 * df["Ville"].notna().astype(int) +
        1 * ((df["Rue"].notna()) & (df["Code_Postal"].notna())).astype(int) +

        # NORMAL
        1 * ((df["Email_Reservation"].notna()) | (df["Telephone_Reservation"].notna())).astype(int) +
        1 * df["Info_Dates"].notna().astype(int) +
        1 * df["Animaux_autorises"].notna().astype(int)
    ) / 16 *100

df_analyse = df.copy()
df_analyse["score_completude"] = calc_score_individuel(df)

# Score de présence géographique (normalisé sur 100)
df_analyse["score_geo"] = (
    ((df["Latitude"].notna()) & (df["Longitude"].notna())).astype(int) +
    df["Ville"].notna().astype(int) +
    ((df["Rue"].notna()) & (df["Code_Postal"].notna())).astype(int)
) / 3 * 100

df_analyse["nb_types"] = df["Types"].fillna("").apply(lambda x: len(x.split(",")) if x != "" else 1)
df_analyse["types_liste"] = df["Types"].fillna("").apply(lambda x: "<br>".join([t.strip() for t in x.split(",")]) if x != "" else "")
df_analyse["richesse_desc"] = df_analyse["Description"].fillna("").str.len()

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
# la moyenne de de la moyenne du taux de remplissage de chaque POI avec pondération des champs les plus importants
def kpi_score_qualite(df):
    return round(calc_score_individuel(df).mean(), 1)


# KPI 2 — CONTACTABILITÉ : au moins UN (téléphone ou email)
def kpi_contactables(df):
    return round(((df["Telephone"].notna()) | (df["Email"].notna())).mean() * 100, 1)

# KPI 3 — POI RÉSERVATION
def kpi_reservation(df):
    return round(((df["Email_Reservation"].notna()) | (df["Telephone_Reservation"].notna())).mean() * 100, 1)

# KPI 4 — POI animaux autorisés
def kpi_animaux(df):
    return round(df["Animaux_autorises"].notna().mean() * 100, 1)

# KPI 5 — RICHESSE DES DONNÉES : Longueur du texte > 200 caractères donc c'est riche
def kpi_description_riche(df):
    return round((df["Description"].fillna("").str.len() > 200).mean() * 100, 1)

# KPI 6 — POI avec informations de dates exploitables
def kpi_dates_exploitables(df):
    return round(df["Info_Dates"].apply(lambda x: isinstance(x, str) and len(x) > 10).mean() * 100, 1)

# KPI 7 — GÉOLOCALISATION
def kpi_geo_complet(df):
    return round(
        ((df["Latitude"].notna()) & (df["Longitude"].notna())).mean() * 100, 1)

kpi1 = f"{kpi_score_qualite(df)} %"
kpi2 = f"{kpi_contactables(df)} %"
kpi3 = f"{kpi_reservation(df)} %"
kpi4 = f"{kpi_animaux(df)} %"
kpi5 = f"{kpi_description_riche(df)} %"
kpi6 = f"{kpi_dates_exploitables(df)} %"
kpi7 = f"{kpi_geo_complet(df)} %"   
 

#=========================== TOP 3 OPI ========================


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
    size=df["Description"].fillna("").str.len(),
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
            "A VERIFIER Ville|CP": COLORS["violet"],
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
        color_continuous_scale='RdYlGn', # Du rouge (erreur) au vert (parfait)
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
    
    # on garde que > 0.5 = Match sérieux
    df_merge['Statut'] = df_merge['best_score'].apply(
        lambda s: "Score élevé" if s > 0.5 else "Score faible"
    )
    
    fig = px.bar(
        df_merge.groupby(['Categorie', 'Statut']).size().reset_index(name='Nombre'),
        x="Nombre",
        y="Categorie",
        color="Statut",
        orientation='h',
        color_discrete_map={
            "Score élevé": COLORS["vert"],
            "Score Faible": COLORS["rouge"]
        }
    )
    fig.update_layout(
        title="Qualité de l'enrichissement Europeana",
        title_x=0.5,
        paper_bgcolor='white', 
        plot_bgcolor=COLORS["plot"], 
    )
    
    return fig


# __________________________ Graphique 9 : Précision Panoramax _____________________

def create_panoramax_dist(df_p):
    # Filtrer uniquement là où on a trouvé une image
    df_found = df_p[df_p['found'] == True].copy()
    
    fig = px.histogram(
        df_found,
        x="distance_m",
        nbins=20,
        title="Distance POI vs Photo Panoramax (m)",
        color_discrete_sequence=[COLORS["bleu"]]
    )
    # Ajouter une ligne verticale pour le seuil de 20m (très précis)
    fig.add_vline(x=20, line_dash="dash", line_color=COLORS["rouge"], annotation_text="Seuil de précision")
    
    fig.update_layout(paper_bgcolor='white', plot_bgcolor=COLORS["plot"], title_x=0.5)
    return fig
#=========================== DASH INTERFACE ========================

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

                                    dcc.Graph(
                                        id="g1",
                                        figure=fig_tree,
                                        config={'displayModeBar': False}
                                    ),

                                    dcc.Graph(
                                        id="g2",
                                        figure=fig_tree_cat,
                                        config={'displayModeBar': False}
                                    ),

                                    dcc.Graph(
                                        id="g3",
                                        figure=fig_missing,
                                        config={'displayModeBar': False}
                                    ),

                                    dcc.Graph(
                                        id="g5",
                                        figure=fig_scatter,
                                        config={'displayModeBar': False},  
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
                                                        src="/assets/graphe.png",
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
                                                        src="/assets/velo.png",
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
                                                        src="/assets/velo.png",
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
                                                        src="/assets/vert.png",
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
                                                        src="/assets/critique.png",
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
                                                                "POI avec informations de dates exploitablese", 
                                                                className="kpi_label")
                                                ]),
                                                html.Div(
                                                    html.Img( 
                                                        src="/assets/kpi6.png",
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
                                                        src="/assets/critique.png",
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
                                                figure=top_3_poi(top_bad, "TOP 3 - POI les moins complets", COLORS["rouge"]),
                                                config={'displayModeBar': False},
                                                id="top3_bad",
                                                className = "top3_poi"
                                            ),    
                                        ]
                                    ),

                                    html.Div(   
                                        className="Les_Graphes",                                        children=[ 
                                            dcc.Graph(
                                                id="g4",
                                                figure=fig_hist_score,
                                                config={'displayModeBar': False}
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
                                dcc.Graph(
                                    className="carte_graph_1",
                                    id="map1",
                                    figure=fig_map,
                                    config={'displayModeBar': False},
                                )
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
                                        dcc.Graph(
                                            id="sunburst-qualite",
                                            figure=geo_sunburst(df_geo), 
                                            config={'displayModeBar': False}
                                        ),
                                    ]
                                ),
                            ),
                            html.Td(
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        dcc.Graph(
                                            id="heatmap-qualite",
                                            figure=geo_heatmap(df_geo), 
                                            config={'displayModeBar': False}
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
                                        dcc.Graph(
                                            id="europeana-bar",
                                            figure=europeana_fiabilite(df_fiabilite_europeana), 
                                            config={'displayModeBar': False}
                                        ),
                                    ]
                                ),
                            ),
                            html.Td(
                                html.Div(
                                    className="Les_Graphes", 
                                    children=[
                                        dcc.Graph(
                                            id="panoramax-hist",
                                            figure=create_panoramax_dist(df_fiabilite_panoramax), 
                                            config={'displayModeBar': False}
                                        ),
                                    ]
                                ),
                            ),

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
        size=dff_map["Description"].fillna("").str.len(),
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

if __name__ == "__main__":
    app.run(debug=True, port=8051)