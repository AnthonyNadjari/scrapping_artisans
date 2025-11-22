"""
Page de scraping - Interface de scraping des artisans
"""
import streamlit as st
import sys
from pathlib import Path
import time
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.scraper_manager import ScraperManager
from config.settings import METIERS, DEPARTEMENTS_PRIORITAIRES
from database.queries import get_statistiques

st.set_page_config(page_title="Scraping Artisans", page_icon="🔍", layout="wide")

st.title("🔍 Scraping d'Artisans")

# Configuration scraping
col1, col2 = st.columns(2)

with col1:
    st.subheader("📡 Sources de données")
    source_google = st.checkbox("Google Maps", value=True, help="Scraping via Playwright")
    source_sirene = st.checkbox("Base SIRENE", value=False, help="API publique gratuite (nécessite clé API)")
    
    if source_sirene:
        sirene_api_key = st.text_input("Clé API SIRENE", type="password", help="Inscription: https://api.insee.fr/")

with col2:
    st.subheader("🗺️ Zones géographiques")
    
    dept_selection = st.multiselect(
        "Départements",
        options=DEPARTEMENTS_PRIORITAIRES,
        default=DEPARTEMENTS_PRIORITAIRES[:4],
        help="Sélectionnez les départements à scraper"
    )
    
    st.subheader("🎯 Priorité ciblage")
    priorite = st.radio(
        "Taille des communes",
        ["Villages < 5,000 hab (PRIORITÉ)", "Villes 5,000-20,000", "Toutes tailles"],
        help="Les petites communes sont souvent moins prospectées"
    )

# Métiers à scraper
st.subheader("🔧 Métiers à scraper")
metiers_selectionnes = st.multiselect(
    "Sélectionnez les métiers",
    options=METIERS,
    default=["plombier", "électricien", "menuisier", "peintre"],
    help="Sélectionnez un ou plusieurs métiers"
)

# Boutons de contrôle
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    lancer_scraping = st.button("🚀 LANCER LE SCRAPING", type="primary", use_container_width=True)

with col_btn2:
    pause_scraping = st.button("⏸️ PAUSE", use_container_width=True)

with col_btn3:
    stop_scraping = st.button("⏹️ STOP", use_container_width=True)

# Initialiser session state
if 'scraping_actif' not in st.session_state:
    st.session_state.scraping_actif = False
if 'scraping_pause' not in st.session_state:
    st.session_state.scraping_pause = False
if 'scraping_stats' not in st.session_state:
    st.session_state.scraping_stats = {
        'total_trouves': 0,
        'total_ajoutes': 0,
        'doublons_evites': 0,
        'erreurs': 0,
    }
if 'scraping_logs' not in st.session_state:
    st.session_state.scraping_logs = []

# Gestion des boutons
if lancer_scraping and not st.session_state.scraping_actif:
    st.session_state.scraping_actif = True
    st.session_state.scraping_pause = False
    st.session_state.scraping_logs = []

if pause_scraping:
    st.session_state.scraping_pause = not st.session_state.scraping_pause

if stop_scraping:
    st.session_state.scraping_actif = False
    st.session_state.scraping_pause = False

# Affichage en temps réel
if st.session_state.scraping_actif:
    st.divider()
    st.subheader("📊 Scraping en cours...")
    
    # Métriques en temps réel
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    stats = st.session_state.scraping_stats
    
    with col_m1:
        st.metric("Artisans trouvés", f"{stats['total_trouves']:,}", 
                 f"+{stats['total_ajoutes']}")
    
    with col_m2:
        st.metric("Artisans ajoutés", f"{stats['total_ajoutes']:,}")
    
    with col_m3:
        st.metric("Doublons évités", f"{stats['doublons_evites']:,}")
    
    with col_m4:
        st.metric("Erreurs", f"{stats['erreurs']:,}")
    
    # Progress bar
    if 'current_metier' in st.session_state and 'current_ville' in st.session_state:
        progress_text = f"Scraping : {st.session_state.current_metier} à {st.session_state.current_ville}"
        st.progress(0.5, text=progress_text)
    
    # Statut actuel
    status_container = st.empty()
    if 'current_status' in st.session_state:
        status_container.info(st.session_state.current_status)
    
    # Logs en direct
    with st.expander("📝 Logs détaillés", expanded=True):
        logs_text = "\n".join(st.session_state.scraping_logs[-50:])  # Derniers 50 logs
        st.text_area("", value=logs_text, height=300, disabled=True, label_visibility="collapsed")
    
    # Lancer le scraping dans un thread
    if 'scraping_thread_started' not in st.session_state:
        st.session_state.scraping_thread_started = True
        
        def run_scraping():
            try:
                manager = ScraperManager(
                    use_google_maps=source_google,
                    use_sirene=source_sirene,
                    sirene_api_key=sirene_api_key if source_sirene else None
                )
                
                priorite_villages = priorite == "Villages < 5,000 hab (PRIORITÉ)"
                
                def callback(progress_data):
                    if 'metier' in progress_data:
                        st.session_state.current_metier = progress_data['metier']
                        st.session_state.current_ville = progress_data['ville']
                        st.session_state.current_status = f"🔄 {progress_data['metier']} - {progress_data['ville']} - {progress_data['trouves']} trouvés"
                        
                        log_entry = f"[{time.strftime('%H:%M:%S')}] ✓ {progress_data['metier']} {progress_data['ville']} - {progress_data['trouves']} artisans"
                        st.session_state.scraping_logs.append(log_entry)
                    
                    if 'stats' in progress_data:
                        st.session_state.scraping_stats = progress_data['stats']
                
                manager.scraper_campagne(
                    metiers_selectionnes,
                    dept_selection,
                    priorite_villages=priorite_villages,
                    callback_progress=callback
                )
                
                st.session_state.scraping_actif = False
                st.session_state.current_status = "✅ Scraping terminé !"
                
            except Exception as e:
                st.session_state.scraping_actif = False
                st.session_state.current_status = f"❌ Erreur: {str(e)}"
                st.session_state.scraping_logs.append(f"[ERREUR] {str(e)}")
        
        thread = threading.Thread(target=run_scraping, daemon=True)
        thread.start()
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()

else:
    # Afficher les stats actuelles
    stats_globales = get_statistiques()
    st.info(f"📊 Base actuelle : {stats_globales.get('total', 0)} artisans")

