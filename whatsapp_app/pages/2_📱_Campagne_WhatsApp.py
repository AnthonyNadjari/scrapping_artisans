"""
Page Campagne WhatsApp - Envoi contrôlé de messages
"""
import streamlit as st
import sys
from pathlib import Path
import time
import threading

# Configuration de la page
st.set_page_config(page_title="Campagne WhatsApp", page_icon="📱", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, get_statistiques, marquer_message_envoye
from whatsapp.whatsapp_web_manager import WhatsAppWebManager
from whatsapp.rate_limiter import RateLimiter
from config.whatsapp_settings import METIERS, DEPARTEMENTS_PRIORITAIRES

st.title("📱 Campagne WhatsApp")

# Vérifier connexion WhatsApp
if 'whatsapp_manager' not in st.session_state:
    st.session_state.whatsapp_manager = None
if 'whatsapp_connected' not in st.session_state:
    st.session_state.whatsapp_connected = False

# Section connexion WhatsApp
st.markdown("### 🔌 Connexion WhatsApp Web")

if not st.session_state.whatsapp_connected:
    col_conn1, col_conn2 = st.columns([2, 1])
    
    with col_conn1:
        st.info("""
        **Pour envoyer des messages, vous devez vous connecter à WhatsApp Web :**
        1. Cliquez sur "Se connecter"
        2. Un navigateur s'ouvrira avec WhatsApp Web
        3. Scannez le QR code avec votre téléphone
        4. Une fois connecté, vous pourrez envoyer des messages
        """)
    
    with col_conn2:
        if st.button("🔌 Se connecter à WhatsApp Web", type="primary"):
            with st.spinner("Connexion en cours..."):
                manager = WhatsAppWebManager(headless=False)
                success, message, qr_url = manager.connecter(wait_for_qr=False)
                
                if success:
                    st.session_state.whatsapp_manager = manager
                    st.session_state.whatsapp_connected = True
                    st.success("✅ Connecté à WhatsApp Web !")
                    st.rerun()
                else:
                    st.error(f"❌ Erreur: {message}")
                    if qr_url:
                        st.info(f"Ouvrez cette URL dans votre navigateur: {qr_url}")
else:
    col_conn1, col_conn2 = st.columns([2, 1])
    
    with col_conn1:
        st.success("✅ Connecté à WhatsApp Web")
    
    with col_conn2:
        if st.button("🔌 Déconnecter"):
            if st.session_state.whatsapp_manager:
                st.session_state.whatsapp_manager.deconnecter()
            st.session_state.whatsapp_manager = None
            st.session_state.whatsapp_connected = False
            st.rerun()

st.markdown("---")

# Configuration rate limiting
st.markdown("### ⚙️ Configuration Rate Limiting (Anti-Ban)")

col_rate1, col_rate2, col_rate3 = st.columns(3)

with col_rate1:
    messages_per_minute = st.slider("Messages par minute", 1, 20, 10,
                                   help="Limite de messages par minute")

with col_rate2:
    messages_per_hour = st.slider("Messages par heure", 50, 500, 200,
                                 help="Limite de messages par heure")

with col_rate3:
    messages_per_day = st.slider("Messages par jour", 500, 2000, 1000,
                                help="Limite de messages par jour")

random_delay = st.checkbox("Délai aléatoire entre messages (3-10s)", value=True,
                          help="Humanise l'envoi pour éviter les bans")

st.markdown("---")

# Sélection cible
st.markdown("### 🎯 Sélection des Artisans")

col_filtre1, col_filtre2 = st.columns(2)

with col_filtre1:
    filtre_metiers = st.multiselect("Métiers", options=METIERS, default=["plombier", "électricien"])

with col_filtre2:
    filtre_depts = st.multiselect("Départements", options=DEPARTEMENTS_PRIORITAIRES, default=["77", "78"])

filtres = {}
if filtre_metiers:
    filtres['metiers'] = filtre_metiers
if filtre_depts:
    filtres['departements'] = filtre_depts
filtres['a_whatsapp'] = True  # Uniquement ceux avec WhatsApp
filtres['non_contactes'] = True  # Uniquement non contactés

artisans_cibles = get_artisans(filtres, limit=10000)

st.info(f"📊 **{len(artisans_cibles)} artisans ciblés** (avec WhatsApp, non contactés)")

st.markdown("---")

# Message
st.markdown("### 💬 Message WhatsApp")

message_template = st.text_area(
    "Message à envoyer",
    value="""Bonjour,

Je suis Anthony, développeur web.

Je crée des sites pour artisans à 200€ tout compris :
• Hébergement inclus 1 an
• Design professionnel
• Sans abonnement

Exemple : plomberie-fluide.vercel.app

Intéressé ? 😊""",
    height=200,
    help="Le message sera envoyé à tous les artisans sélectionnés"
)

st.markdown("---")

# Contrôles campagne
st.markdown("### 🎮 Contrôles de Campagne")

# Initialiser rate limiter
if 'rate_limiter' not in st.session_state:
    st.session_state.rate_limiter = RateLimiter(
        messages_per_minute=messages_per_minute,
        messages_per_hour=messages_per_hour,
        messages_per_day=messages_per_day,
        random_delay=random_delay
    )

# Mettre à jour rate limiter
st.session_state.rate_limiter.messages_per_minute = messages_per_minute
st.session_state.rate_limiter.messages_per_hour = messages_per_hour
st.session_state.rate_limiter.messages_per_day = messages_per_day
st.session_state.rate_limiter.random_delay = random_delay

col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

with col_btn1:
    demarrer = st.button("🚀 DÉMARRER", type="primary")

with col_btn2:
    pause = st.button("⏸️ PAUSE")

with col_btn3:
    reprendre = st.button("▶️ REPRENDRE")

with col_btn4:
    stop = st.button("⏹️ STOP")

# Gestion des boutons
if 'campagne_active' not in st.session_state:
    st.session_state.campagne_active = False
if 'campagne_pause' not in st.session_state:
    st.session_state.campagne_pause = False

if demarrer and not st.session_state.campagne_active:
    if not st.session_state.whatsapp_connected:
        st.error("❌ Vous devez d'abord vous connecter à WhatsApp Web")
    elif len(artisans_cibles) == 0:
        st.error("❌ Aucun artisan ciblé")
    else:
        st.session_state.campagne_active = True
        st.session_state.campagne_pause = False
        st.session_state.campagne_envoyes = 0
        st.session_state.campagne_erreurs = 0
        st.session_state.campagne_logs = []
        st.session_state.rate_limiter.reset()

if pause:
    st.session_state.campagne_pause = True
    if st.session_state.rate_limiter:
        st.session_state.rate_limiter.pause()

if reprendre:
    st.session_state.campagne_pause = False
    if st.session_state.rate_limiter:
        st.session_state.rate_limiter.resume()

if stop:
    st.session_state.campagne_active = False
    st.session_state.campagne_pause = False
    if st.session_state.rate_limiter:
        st.session_state.rate_limiter.stop()

# Affichage état campagne
if st.session_state.campagne_active:
    st.markdown("---")
    st.subheader("📊 Campagne en cours")
    
    # Métriques
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("Envoyés", st.session_state.get('campagne_envoyes', 0))
    
    with col_stat2:
        restants = len(artisans_cibles) - st.session_state.get('campagne_envoyes', 0)
        st.metric("Restants", restants)
    
    with col_stat3:
        st.metric("Erreurs", st.session_state.get('campagne_erreurs', 0))
    
    with col_stat4:
        if st.session_state.campagne_pause:
            st.metric("État", "⏸️ En pause")
        else:
            st.metric("État", "🟢 En cours")
    
    # Stats rate limiter
    if st.session_state.rate_limiter:
        stats = st.session_state.rate_limiter.get_stats()
        
        col_lim1, col_lim2, col_lim3 = st.columns(3)
        
        with col_lim1:
            st.metric("Limite minute", f"{stats['minute']['envoyes']}/{stats['minute']['limite']}")
        
        with col_lim2:
            st.metric("Limite heure", f"{stats['heure']['envoyes']}/{stats['heure']['limite']}")
        
        with col_lim3:
            st.metric("Limite jour", f"{stats['jour']['envoyes']}/{stats['jour']['limite']}")
        
        # Temps d'attente
        wait_time = st.session_state.rate_limiter.get_wait_time()
        st.info(f"⏱️ Prochain envoi dans : {int(wait_time)} secondes")
    
    # Logs
    with st.expander("📝 Logs en direct", expanded=True):
        logs_text = "\n".join(st.session_state.get('campagne_logs', [])[-30:])
        st.text_area("", value=logs_text, height=200, disabled=True, label_visibility="collapsed")
    
    # Lancer la campagne dans un thread
    if 'campagne_thread_started' not in st.session_state:
        st.session_state.campagne_thread_started = True
        
        def run_campagne():
            manager = st.session_state.whatsapp_manager
            limiter = st.session_state.rate_limiter
            
            for artisan in artisans_cibles:
                if not st.session_state.campagne_active:
                    break
                
                if st.session_state.campagne_pause:
                    time.sleep(1)
                    continue
                
                # Vérifier rate limit
                can_send, reason = limiter.can_send()
                if not can_send:
                    log_entry = f"[{time.strftime('%H:%M:%S')}] ⏸️ {reason}"
                    st.session_state.campagne_logs.append(log_entry)
                    time.sleep(5)
                    continue
                
                # Envoyer message
                try:
                    if not manager.est_connecte():
                        log_entry = f"[{time.strftime('%H:%M:%S')}] ⚠️ Déconnecté de WhatsApp Web"
                        st.session_state.campagne_logs.append(log_entry)
                        st.session_state.campagne_active = False
                        break
                    
                    success, msg_id, error = manager.envoyer_message(
                        artisan['telephone'],
                        message_template
                    )
                    
                    if success:
                        marquer_message_envoye(artisan['id'], msg_id)
                        st.session_state.campagne_envoyes += 1
                        limiter.record_send()
                        
                        log_entry = f"[{time.strftime('%H:%M:%S')}] ✓ Envoyé à {artisan.get('nom_entreprise', 'N/A')}"
                        st.session_state.campagne_logs.append(log_entry)
                    else:
                        st.session_state.campagne_erreurs += 1
                        log_entry = f"[{time.strftime('%H:%M:%S')}] ✗ Erreur {artisan.get('nom_entreprise', 'N/A')}: {error}"
                        st.session_state.campagne_logs.append(log_entry)
                        
                        # Si erreur spam, arrêter
                        if error and "spam" in error.lower():
                            st.session_state.campagne_logs.append("🚨 SPAM DETECTÉ - Arrêt immédiat !")
                            st.session_state.campagne_active = False
                            break
                
                except Exception as e:
                    st.session_state.campagne_erreurs += 1
                    log_entry = f"[{time.strftime('%H:%M:%S')}] ✗ Exception: {str(e)}"
                    st.session_state.campagne_logs.append(log_entry)
                
                # Attendre avant prochain message
                wait_time = limiter.get_wait_time()
                time.sleep(wait_time)
            
            st.session_state.campagne_active = False
            st.session_state.campagne_logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Campagne terminée")
        
        thread = threading.Thread(target=run_campagne, daemon=True)
        thread.start()
    
    time.sleep(2)
    st.rerun()

