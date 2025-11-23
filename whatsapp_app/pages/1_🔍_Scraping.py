"""
Page Scraping - Scraping téléphones et vérification WhatsApp
"""
import streamlit as st
import sys
from pathlib import Path
import time
import threading

# Configuration de la page
st.set_page_config(page_title="Scraping Artisans", page_icon="🔍", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_scraping.scraper_manager import WhatsAppScraperManager
from config.whatsapp_settings import METIERS, DEPARTEMENTS_PRIORITAIRES
from whatsapp_database.queries import get_statistiques

st.title("🔍 Scraping d'Artisans - Téléphones uniquement")

# Configuration scraping
col1, col2 = st.columns(2)

with col1:
    st.subheader("📡 Sources de données")
    source_google = st.checkbox("Google Maps", value=True)
    source_pj = st.checkbox("Pages Jaunes", value=False)
    
    st.subheader("✅ Vérification WhatsApp")
    verifier_whatsapp = st.checkbox("Vérifier automatiquement WhatsApp", value=True,
                                   help="Vérifie si chaque numéro est sur WhatsApp après scraping")

with col2:
    st.subheader("🗺️ Zones géographiques")
    
    dept_selection = st.multiselect(
        "Départements",
        options=DEPARTEMENTS_PRIORITAIRES,
        default=DEPARTEMENTS_PRIORITAIRES[:4]
    )
    
    st.subheader("🎯 Priorité ciblage")
    priorite = st.radio(
        "Taille des communes",
        ["Villages < 5,000 hab (PRIORITÉ)", "Villes 5,000-20,000", "Toutes tailles"]
    )

# Métiers à scraper
st.subheader("🔧 Métiers à scraper")
metiers_selectionnes = st.multiselect(
    "Sélectionnez les métiers",
    options=METIERS,
    default=["plombier", "électricien", "menuisier", "peintre"]
)

# Boutons de contrôle
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    lancer_scraping = st.button("🚀 LANCER LE SCRAPING")

with col_btn2:
    pause_scraping = st.button("⏸️ PAUSE")

with col_btn3:
    stop_scraping = st.button("⏹️ STOP")

# Initialiser session state
if 'scraping_actif' not in st.session_state:
    st.session_state.scraping_actif = False
if 'scraping_pause' not in st.session_state:
    st.session_state.scraping_pause = False
if 'scraping_stats' not in st.session_state:
    st.session_state.scraping_stats = {
        'total_trouves': 0,
        'total_ajoutes': 0,
        'avec_whatsapp': 0,
        'sans_whatsapp': 0,
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
    st.markdown("---")
    st.subheader("📊 Scraping en cours...")
    
    # Métriques
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    stats = st.session_state.scraping_stats
    
    with col_m1:
        st.metric("Artisans trouvés", f"{stats['total_trouves']:,}")
    
    with col_m2:
        st.metric("Artisans ajoutés", f"{stats['total_ajoutes']:,}")
    
    with col_m3:
        st.metric("Avec WhatsApp", f"{stats['avec_whatsapp']:,}")
    
    with col_m4:
        st.metric("Sans WhatsApp", f"{stats['sans_whatsapp']:,}")
    
    with col_m5:
        taux_whatsapp = (stats['avec_whatsapp'] / max(1, stats['avec_whatsapp'] + stats['sans_whatsapp'])) * 100
        st.metric("Taux WhatsApp", f"{taux_whatsapp:.1f}%")
    
    # Statut actuel
    status_container = st.empty()
    if 'current_status' in st.session_state:
        status_container.info(st.session_state.current_status)
    
    # Logs
    with st.expander("📝 Logs détaillés", expanded=True):
        logs_text = "\n".join(st.session_state.scraping_logs[-50:])
        st.text_area("", value=logs_text, height=300, disabled=True)
    
    # Lancer le scraping
    if 'scraping_thread_started' not in st.session_state:
        st.session_state.scraping_thread_started = True
        
        def run_scraping():
            try:
                manager = WhatsAppScraperManager(verifier_whatsapp=verifier_whatsapp)
                
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
                    use_google_maps=source_google,
                    use_pages_jaunes=source_pj,
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
    
    time.sleep(2)
    st.experimental_rerun()

else:
    stats_globales = get_statistiques()
    st.info(f"📊 Base actuelle : {stats_globales.get('total', 0)} artisans, {stats_globales.get('avec_whatsapp', 0)} avec WhatsApp")

