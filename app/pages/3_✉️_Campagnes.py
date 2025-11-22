"""
Page Campagnes - Gestion des campagnes d'emails
"""
import streamlit as st
import sys
from pathlib import Path
import time
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.queries import get_artisans, get_statistiques
from emails.sender import EmailSender
from config.settings import METIERS, DEPARTEMENTS_PRIORITAIRES

st.set_page_config(page_title="Campagnes Email", page_icon="✉️", layout="wide")

st.title("✉️ Gestion des Campagnes Email")

# Stats rapides
col_stat1, col_stat2, col_stat3 = st.columns(3)
stats = get_statistiques()

with col_stat1:
    st.metric("Emails envoyés", f"{stats.get('emails_envoyes', 0):,}")

with col_stat2:
    st.metric("Emails ouverts", f"{stats.get('emails_ouverts', 0):,}")

with col_stat3:
    st.metric("Réponses", f"{stats.get('repondus', 0):,}")

st.divider()

# Créer nouvelle campagne
st.subheader("➕ Créer une nouvelle campagne")

with st.form("nouvelle_campagne"):
    nom_campagne = st.text_input("Nom de la campagne", placeholder="Campagne plombiers 77 - Janvier 2024")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        target_metiers = st.multiselect("Métiers", options=METIERS, default=["plombier", "électricien"])
    
    with col_t2:
        target_depts = st.multiselect("Départements", options=DEPARTEMENTS_PRIORITAIRES, default=["77", "78"])
    
    # Filtres supplémentaires
    avec_email_seulement = st.checkbox("Uniquement artisans avec email", value=True)
    non_contactes_seulement = st.checkbox("Uniquement non contactés", value=True)
    
    # Paramètres d'envoi
    emails_par_jour = st.slider("Emails par jour", 10, 100, 20)
    delai_entre_emails = st.slider("Délai entre emails (secondes)", 5, 120, 30)
    
    submitted = st.form_submit_button("Créer et lancer la campagne", type="primary")
    
    if submitted:
        # Récupérer artisans ciblés
        filtres = {}
        if target_metiers:
            filtres['metiers'] = target_metiers
        if target_depts:
            filtres['departements'] = target_depts
        if avec_email_seulement:
            filtres['a_email'] = True
        if non_contactes_seulement:
            filtres['statut'] = 'non_contacte'
        
        artisans_cibles = get_artisans(filtres, limit=10000)
        
        if artisans_cibles:
            st.success(f"✅ {len(artisans_cibles)} artisans ciblés")
            st.session_state.campagne_artisans = artisans_cibles
            st.session_state.campagne_nom = nom_campagne
            st.session_state.campagne_emails_par_jour = emails_par_jour
            st.session_state.campagne_delai = delai_entre_emails
        else:
            st.error("Aucun artisan trouvé avec ces critères")

# Campagne en cours
if 'campagne_artisans' in st.session_state and st.session_state.campagne_artisans:
    st.divider()
    st.subheader("📤 Campagne en cours")
    
    artisans_campagne = st.session_state.campagne_artisans
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        st.metric("Artisans ciblés", len(artisans_campagne))
    
    with col_c2:
        st.metric("Emails par jour", st.session_state.get('campagne_emails_par_jour', 20))
    
    with col_c3:
        if 'campagne_envoyes' in st.session_state:
            st.metric("Envoyés", st.session_state.campagne_envoyes)
        else:
            st.metric("Envoyés", 0)
    
    # Boutons de contrôle
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🚀 Envoyer 20 emails", type="primary"):
            if 'campagne_envoyes' not in st.session_state:
                st.session_state.campagne_envoyes = 0
            
            # Prendre les 20 premiers non envoyés
            artisans_a_envoyer = [
                a for a in artisans_campagne 
                if not a.get('email_envoye')
            ][:20]
            
            if artisans_a_envoyer:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                sender = EmailSender()
                
                for i, artisan in enumerate(artisans_a_envoyer):
                    success, message = sender.envoyer_email(artisan)
                    
                    if success:
                        st.session_state.campagne_envoyes += 1
                        status_text.success(f"✅ Email {i+1}/20 envoyé à {artisan.get('nom_entreprise')}")
                    else:
                        status_text.error(f"❌ Erreur: {message}")
                    
                    progress_bar.progress((i + 1) / len(artisans_a_envoyer))
                    time.sleep(st.session_state.get('campagne_delai', 30))
                
                st.success(f"🎉 {len(artisans_a_envoyer)} emails envoyés !")
            else:
                st.info("Tous les artisans ont déjà reçu un email")
    
    with col_btn2:
        if st.button("⏸️ Pause"):
            st.info("Campagne en pause")
    
    with col_btn3:
        if st.button("⏹️ Arrêter"):
            st.session_state.campagne_artisans = None
            st.rerun()

st.divider()

# Nouvelles réponses (à implémenter avec sync Gmail)
st.subheader("🆕 Nouvelles réponses")

st.info("Les réponses sont synchronisées automatiquement depuis Gmail. Voir la page Paramètres pour configurer la sync.")

