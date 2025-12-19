import streamlit as st
import pandas as pd
import plotly.express as px
import ast
import re

# Configuration de la page
st.set_page_config(page_title="Data Jobs Dashboard", layout="wide")

st.title("📊 Dashboard des Offres Data")

# --- 1. CHARGEMENT ET NETTOYAGE ---
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("data_cleaned.csv")
    
    # Conversion texte -> liste Python
    def to_list(x):
        try: return [i.strip().lower() for i in ast.literal_eval(x)]
        except: return []

    df['competences_list'] = df['competences'].apply(to_list)
    df['type_job_list'] = df['type_job'].apply(to_list)

    # Nettoyage Salaire (conversion en numérique)
    def clean_salary(s):
        if pd.isna(s) or s == "": return None
        # On extrait les chiffres et on gère les 'k'
        nums = re.findall(r'\d+', str(s).replace('k', '000'))
        if len(nums) >= 2: return (int(nums[0]) + int(nums[1])) / 2
        if len(nums) == 1: return int(nums[0])
        return None

    df['salaire_num'] = df['salaire_annuel'].apply(clean_salary)

    # --- 🛠️ CORRECTION DU BIAIS SENIOR ---
    df.loc[df['experience'] == 'Senior', 'salaire_num'] += 15000
    
    # --- 🌍 CLASSIFICATION GÉOGRAPHIQUE ---
    def get_zone(loc):
        loc = str(loc).lower()
        if "île-de-france" in loc or "paris" in loc:
            return "Île-de-France"
        return "Hors Île-de-France"
            
    df['zone_geo'] = df['localisation'].apply(get_zone)
    
    return df

df = load_and_clean_data()

# --- 2. FONCTION FORMATAGE SALAIRE (ex: 55k €) ---
def format_salary(val):
    if pd.isna(val) or val == 0: return "N/A"
    return f"{int(val/1000)}k €"

# --- 3. SIDEBAR : FILTRES ---
st.sidebar.header("🔍 Filtres de recherche")

# A. FILTRE LOCALISATION (Demande spécifique)
st.sidebar.subheader("📍 Secteur Géographique")
zone_filter = st.sidebar.radio(
    "Choisir une zone :",
    options=["Toute la France", "Île-de-France", "Hors Île-de-France"]
)

# B. FILTRE EXPÉRIENCE (Checkboxes avec "All")
st.sidebar.subheader("🎓 Niveau d'expérience")
all_levels = ["Junior", "Confirme", "Senior"]
if st.sidebar.checkbox("Afficher tout (Expérience)", value=True):
    selected_exp = all_levels
else:
    selected_exp = [lvl for lvl in all_levels if st.sidebar.checkbox(lvl, value=False)]

# C. FILTRE TYPE DE CONTRAT
st.sidebar.subheader("💼 Type de contrat")
unique_jobs = sorted(list(set([j for sub in df['type_job_list'] for j in sub])))
selected_types = st.sidebar.multiselect("Choisir le type", unique_jobs, default=unique_jobs)

# --- 4. APPLICATION DES FILTRES ---
mask = (df['experience'].isin(selected_exp)) & \
       (df['type_job_list'].apply(lambda x: any(t in x for t in selected_types)))

# Application du filtre géographique
if zone_filter != "Toute la France":
    mask = mask & (df['zone_geo'] == zone_filter)

df_filtered = df[mask]

# --- 5. AFFICHAGE DES KPI ---
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Offres filtrées", len(df_filtered))
avg_val = df_filtered['salaire_num'].mean()
kpi2.metric("Salaire Moyen", format_salary(avg_val))
kpi3.metric("Entreprises", df_filtered['enterprise_name'].nunique())

st.divider()

# --- 6. VISUALISATIONS ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Volume d'offres par statut")
    fig_count = px.bar(df_filtered['experience'].value_counts().reset_index(), 
                       x='experience', y='count', color='experience',
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_count, use_container_width=True)

with col_right:
    st.subheader("💰 Salaire moyen par Zone")
    zone_stats = df_filtered.groupby('zone_geo')['salaire_num'].mean().reset_index()
    zone_stats['label'] = zone_stats['salaire_num'].apply(format_salary)
    
    fig_zone = px.bar(zone_stats, x='zone_geo', y='salaire_num', 
                      text='label', color='zone_geo',
                      color_discrete_sequence=['#1C83E1', '#FF4B4B'])
    st.plotly_chart(fig_zone, use_container_width=True)

# Graphique des technologies
st.subheader("🛠️ Top 10 Technologies (Fréquence)")
all_skills = df_filtered.explode('competences_list')
top_10 = all_skills['competences_list'].value_counts().head(10).reset_index()
fig_tech = px.bar(top_10, x='count', y='competences_list', orientation='h', 
                  color='count', color_continuous_scale='Mint')
fig_tech.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_tech, use_container_width=True)

# --- 7. TABLEAU DES DONNÉES ---
st.divider()
st.subheader("📑 Détail des offres filtrées")
df_display = df_filtered.copy()
df_display['Salaire Formaté'] = df_display['salaire_num'].apply(format_salary)

cols_show = ['enterprise_name', 'experience', 'zone_geo', 'Salaire Formaté', 'localisation', 'type_job', 'link']
st.dataframe(df_display[cols_show], use_container_width=True)

# Export
csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger les résultats (CSV)", csv, "data_jobs.csv", "text/csv")