"""
Page Base de Données - Consultation et gestion des artisans
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.queries import (
    get_artisans, get_statistiques, get_metiers_uniques, 
    get_departements_uniques, get_artisan
)
from enrichment.email_finder import EmailFinder

st.set_page_config(page_title="Base de Données", page_icon="📊", layout="wide")

st.title("📊 Base de Données Artisans")

# Stats globales
col_s1, col_s2, col_s3, col_s4 = st.columns(4)

stats = get_statistiques()

with col_s1:
    st.metric("Total artisans", f"{stats.get('total', 0):,}")

with col_s2:
    avec_email = stats.get('avec_email', 0)
    total = stats.get('total', 1)
    pourcentage = (avec_email / total * 100) if total > 0 else 0
    st.metric("Avec email", f"{avec_email:,}", f"{pourcentage:.1f}%")

with col_s3:
    st.metric("Non contactés", f"{stats.get('non_contactes', 0):,}")

with col_s4:
    st.metric("Ont répondu", f"{stats.get('repondus', 0):,}")

st.divider()

# Filtres
st.subheader("🔍 Filtres")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    metiers_uniques = get_metiers_uniques()
    filtre_metier = st.multiselect(
        "Métier",
        options=metiers_uniques if metiers_uniques else [],
        default=None
    )

with col_f2:
    depts_uniques = get_departements_uniques()
    filtre_dept = st.multiselect(
        "Département",
        options=depts_uniques if depts_uniques else [],
        default=None
    )

with col_f3:
    filtre_statut = st.selectbox(
        "Statut",
        ["Tous", "non_contacte", "email_envoye", "ouvert", "repondu", "interesse"]
    )

# Options supplémentaires
col_o1, col_o2, col_o3 = st.columns(3)

with col_o1:
    filtre_site = st.checkbox("A déjà un site web")

with col_o2:
    filtre_email = st.checkbox("Email trouvé")

with col_o3:
    filtre_village = st.checkbox("Villages < 5,000 hab")

# Barre de recherche
recherche = st.text_input("🔎 Recherche rapide", placeholder="Nom, ville, téléphone...")

# Construire filtres
filtres = {}
if filtre_metier:
    filtres['metiers'] = filtre_metier
if filtre_dept:
    filtres['departements'] = filtre_dept
if filtre_statut and filtre_statut != "Tous":
    filtres['statut'] = filtre_statut
if filtre_site:
    filtres['a_site_web'] = True
if filtre_email:
    filtres['a_email'] = True
if recherche:
    filtres['recherche'] = recherche

# Récupérer les artisans
artisans = get_artisans(filtres, limit=1000)

st.divider()
st.subheader(f"Résultats ({len(artisans)} artisans)")

# Sélection multiple
selected_ids = []

# Afficher tableau
if artisans:
    # Créer DataFrame pour affichage
    df_data = []
    for artisan in artisans[:100]:  # Limiter à 100 pour performance
        df_data.append({
            'ID': artisan.get('id'),
            'Nom entreprise': artisan.get('nom_entreprise', ''),
            'Ville': f"{artisan.get('ville', '')} ({artisan.get('departement', '')})",
            'Métier': artisan.get('type_artisan', ''),
            'Email': artisan.get('email', '❌'),
            'Téléphone': artisan.get('telephone', ''),
            'Statut': artisan.get('statut', 'non_contacte'),
        })
    
    df = pd.DataFrame(df_data)
    
    # Sélection multiple via checkbox
    for idx, row in df.iterrows():
        artisan_id = row['ID']
        checked = st.checkbox("", key=f"check_{artisan_id}")
        if checked:
            selected_ids.append(artisan_id)
    
    # Afficher le tableau
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Actions groupées
    if selected_ids:
        st.divider()
        st.subheader(f"Actions sur {len(selected_ids)} artisan(s) sélectionné(s)")
        
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        
        with col_a1:
            if st.button("📧 Enrichir emails", type="primary"):
                with st.spinner("Enrichissement en cours..."):
                    finder = EmailFinder()
                    enrichis = 0
                    for artisan_id in selected_ids:
                        artisan = get_artisan(artisan_id)
                        if artisan and artisan.get('site_web') and not artisan.get('email'):
                            email = finder.extraire_email_site_web(artisan['site_web'])
                            if email:
                                # Mettre à jour en BDD
                                from database.models import get_connection
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE artisans SET email = ? WHERE id = ?", (email, artisan_id))
                                conn.commit()
                                conn.close()
                                enrichis += 1
                    st.success(f"✅ {enrichis} emails trouvés !")
        
        with col_a2:
            if st.button("📤 Préparer campagne"):
                st.session_state.campagne_artisans = selected_ids
                st.info("Artisans sélectionnés pour la campagne")
        
        with col_a3:
            if st.button("📥 Exporter CSV"):
                artisans_export = [get_artisan(aid) for aid in selected_ids]
                df_export = pd.DataFrame(artisans_export)
                csv = df_export.to_csv(index=False)
                st.download_button(
                    "Télécharger CSV",
                    csv,
                    "artisans.csv",
                    "text/csv"
                )
        
        with col_a4:
            if st.button("🗑️ Supprimer"):
                st.warning("Fonctionnalité à implémenter")
else:
    st.info("Aucun artisan trouvé avec ces filtres")

