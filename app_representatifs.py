import streamlit as st
import pandas as pd
import plotly.express as px


from datetime import datetime
import os

def enregistrer_profil(profil, domaine, lycee):
    output_file = "profils_representatifs.csv"
    new_entry = {
        "Profile URL": profil.get("Profile Public URL", "inconnu"),
        "Domaine": domaine,
        "Lycée": lycee,
        "Timestamp": datetime.now().isoformat()
    }

    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
    else:
        df = pd.DataFrame(columns=["Profile URL", "Domaine", "Lycée", "Timestamp"])

    filtered = df[df["Domaine"] == domaine]
    if len(filtered) >= 3:
        oldest_index = filtered.sort_values("Timestamp").index[0]
        df = df.drop(index=oldest_index)

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(output_file, index=False)

def afficher_parcours_complet(profil):
    def is_valid(val):
        return val and str(val).strip().lower() != "nan"

    parcours = []
    for i in range(1, 6):
        titre = profil.get(f"Diplôme Titre #{i}", "")
        etab = profil.get(f"Établissement Diplôme #{i}", "")
        periode = profil.get(f"Study Period #{i}", "")
        if any([is_valid(titre), is_valid(etab), is_valid(periode)]):
            parcours.append((periode, f"🎓 {titre} – {etab} ({periode})"))

    if any([is_valid(profil.get("Job Title", "")), is_valid(profil.get("Company Name", "")), is_valid(profil.get("Tenure", ""))]):
        parcours.append((profil.get("Tenure", ""), f"💼 {profil.get('Job Title', '')} – {profil.get('Company Name', '')} ({profil.get('Tenure', '')})"))

    for i in range(1, 5):
        poste = profil.get(f"Past Job Title #{i}", "")
        entreprise = profil.get(f"Past Company Name #{i}", "")
        periode = profil.get(f"Past Tenure #{i}", "")
        if any([is_valid(poste), is_valid(entreprise), is_valid(periode)]):
            parcours.append((periode, f"💼 {poste} – {entreprise} ({periode})"))

    def extraire_annee(p):
        if isinstance(p, str):
            for part in p.split():
                if part.isdigit() and len(part) == 4:
                    return int(part)
        return 0

    parcours = sorted(parcours, key=lambda x: extraire_annee(x[0]))
    return [p[1] for p in parcours]

# ----------- 📦 Chargement des données ----------- #
joliot = pd.read_csv("profils-lycée-joliot.csv")
louise = pd.read_csv("profils-lycée-louise.csv")
claude = pd.read_csv("profils-lycée-claude.csv")

# ----------- 🎯 Présentation ----------- #
st.set_page_config(page_title="Cartographie lycéens nanterriens", layout="wide")
st.title("📊 Parcours des lycéens nanterriens")
st.markdown("""
Cette application présente une cartographie des parcours académiques et professionnels de lycéens issus de trois lycées de Nanterre, à partir de données scrappées depuis LinkedIn.

Les lycées étudiés sont : 
- **Lycée Joliot Curie**
- **Lycée Louise Michel**
- **Lycée Claude Chappe**

Elle vous permet de visualiser les **diplômes obtenus** ainsi que les **postes occupés** selon les profils recensés.
""")

# ----------- 🧭 Fonctions d'affichage ----------- #
def show_tabs(df, nom_lycee):
    sous_tabs = st.tabs(["🎓 Diplômes", "💼 Postes"])

    with sous_tabs[0]:
        st.header("🎓 Diplômes")
        st.markdown(f"Données basées sur **{len(df)} profils LinkedIn**")

        niveau_col = "Niveau Diplôme #1"
        domaine_col = "Domaine Large #1"

        if niveau_col in df.columns:
            niveau_data = df[df[niveau_col].notna()]
            fig1 = px.pie(niveau_data, names=niveau_col, title="Répartition par niveau de diplôme")
            st.plotly_chart(fig1, use_container_width=True)

            niveau_selected = st.selectbox(
                "Filtrer un niveau :",
                ["Tous"] + sorted(niveau_data[niveau_col].unique()),
                key=f"niveau_{nom_lycee}"
            )
            filtered_df = df if niveau_selected == "Tous" else df[df[niveau_col] == niveau_selected]
        else:
            st.warning(f"Colonne '{niveau_col}' non trouvée.")
            filtered_df = df

        if domaine_col in df.columns:
            domaine_data = filtered_df[filtered_df[domaine_col].notna()]
            fig2 = px.pie(domaine_data, names=domaine_col, title="Répartition par domaine d'étude")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning(f"Colonne '{domaine_col}' non trouvée.")

    with sous_tabs[1]:
        st.header("💼 Postes")
        st.markdown(f"Données basées sur **{len(df)} profils LinkedIn**")

        domaine_poste_col = "Domaine du dernier poste"
        statut_col = "Catégorie socio-professionnelle"

        if domaine_poste_col in df.columns:
            domaine_poste_data = df[df[domaine_poste_col].notna()]
            fig3 = px.pie(domaine_poste_data, names=domaine_poste_col, title="Répartition par domaine du poste")
            st.plotly_chart(fig3, use_container_width=True)

            domaine_selected = st.selectbox(
                "Filtrer un domaine :",
                ["Tous"] + sorted(domaine_poste_data[domaine_poste_col].unique()),
                key=f"domaine_{nom_lycee}"
            )
            filtered_jobs = df if domaine_selected == "Tous" else df[df[domaine_poste_col] == domaine_selected]
        else:
            st.warning(f"Colonne '{domaine_poste_col}' non trouvée.")
            filtered_jobs = df


        # 🔍 Parcours représentatif
        st.markdown("### 🎯 Exemple de parcours")
        if domaine_poste_col in df.columns and domaine_selected != "Tous":
            profils_domaines = filtered_jobs[filtered_jobs[domaine_poste_col] == domaine_selected]
            if not profils_domaines.empty:
                if st.button("🎲 Afficher un profil exemple", key=f"bouton_random_{nom_lycee}"):
                    profil = profils_domaines.sample(1).iloc[0]
                    st.session_state[f"profil_{nom_lycee}"] = profil.to_dict()

            if f"profil_{nom_lycee}" in st.session_state:
                profil = st.session_state[f"profil_{nom_lycee}"]
                st.markdown(f"**💼 Poste :** {profil.get('Job Title', 'Non spécifié')} chez {profil.get('Company Name', '')}")
                st.markdown(f"**📚 Dernier diplôme :** {profil.get('Diplôme Titre #1', '')} ({profil.get('Niveau Diplôme #1', '')} - {profil.get('Domaine Diplôme #1', '')})")
                st.markdown(f"**🏫 Établissement :** {profil.get('Établissement Diplôme #1', '')}")
                st.markdown(f"**🏷️ Statut :** {profil.get('Catégorie socio-professionnelle', '')}")
                st.markdown(f"**🎓 Domaine :** {profil.get('Domaine du dernier poste', '')}")
                st.markdown("### 🧾 Parcours détaillé")
                for ligne in afficher_parcours_complet(profil):
                    st.markdown(f"- {ligne}")
                if st.button("✅ Valider comme parcours représentatif", key=f"valider_{nom_lycee}"):
                    enregistrer_profil(profil, domaine_selected, nom_lycee)
                    st.success("Profil enregistré avec succès.")

        if statut_col in filtered_jobs.columns:
            statut_data = filtered_jobs[filtered_jobs[statut_col].notna()]
            fig4 = px.pie(statut_data, names=statut_col, title="Répartition par statut")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning(f"Colonne '{statut_col}' non trouvée.")

# ----------- 🏫 Onglets par lycée ----------- #
main_tabs = st.tabs(["🏫 Joliot Curie", "🏫 Louise Michel", "🏫 Claude Chappe"])

with main_tabs[0]:
    show_tabs(joliot, "joliot")

with main_tabs[1]:
    show_tabs(louise, "louise")

with main_tabs[2]:
    show_tabs(claude, "claude")
