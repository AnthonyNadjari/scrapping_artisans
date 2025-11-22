"""
Page Paramètres - Configuration de l'application
"""
import streamlit as st
import sys
from pathlib import Path
import json
import os
import threading
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sync.gmail_sync import GmailSync
from config.settings import GMAIL_CONFIG, CONFIG_DIR

st.set_page_config(page_title="Paramètres", page_icon="⚙️", layout="wide")

st.title("⚙️ Paramètres")

# Config Gmail
st.subheader("📧 Configuration Gmail")

config_file = CONFIG_DIR / "gmail_config.json"

# Charger config existante
if config_file.exists():
    with open(config_file, 'r') as f:
        saved_config = json.load(f)
else:
    saved_config = {}

with st.form("config_gmail"):
    email_adresse = st.text_input(
        "Adresse email Gmail",
        value=saved_config.get('email', GMAIL_CONFIG.get('email', '')),
        help="Votre adresse Gmail (ex: siteswebartisans@gmail.com)"
    )
    
    st.info("⚠️ **Important** : Utilisez un App Password Gmail, pas votre mot de passe principal !")
    st.markdown("""
    Pour créer un App Password :
    1. Allez sur https://myaccount.google.com/apppasswords
    2. Créez un nouveau mot de passe pour "Mail"
    3. Copiez le mot de passe généré (16 caractères)
    """)
    
    app_password = st.text_input(
        "App Password",
        type="password",
        value=saved_config.get('app_password', ''),
        help="Mot de passe d'application Gmail (16 caractères)"
    )
    
    display_name = st.text_input(
        "Nom d'affichage",
        value=saved_config.get('display_name', 'Sites Web Artisans'),
        help="Nom qui apparaîtra dans les emails envoyés"
    )
    
    test_email = st.text_input(
        "Email de test",
        placeholder="votre-email@example.com",
        help="Email pour tester l'envoi"
    )
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        if st.form_submit_button("💾 Sauvegarder", type="primary"):
            config = {
                'email': email_adresse,
                'app_password': app_password,
                'display_name': display_name
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            st.success("✅ Configuration sauvegardée !")
    
    with col_t2:
        if st.form_submit_button("📤 Tester l'envoi"):
            if email_adresse and app_password and test_email:
                try:
                    from emails.sender import EmailSender
                    sender = EmailSender({
                        'email': email_adresse,
                        'app_password': app_password,
                        'display_name': display_name
                    })
                    
                    # Créer artisan test
                    artisan_test = {
                        'id': 999999,
                        'nom_entreprise': 'Test',
                        'prenom': 'Test',
                        'ville': 'Test',
                        'email': test_email
                    }
                    
                    success, message = sender.envoyer_email(artisan_test, use_tracking=False)
                    
                    if success:
                        st.success(f"✅ Email de test envoyé à {test_email} !")
                    else:
                        st.error(f"❌ Erreur : {message}")
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
            else:
                st.warning("Veuillez remplir tous les champs")

st.divider()

# Sync Gmail
st.subheader("🔄 Synchronisation Gmail")

col_sync1, col_sync2 = st.columns(2)

with col_sync1:
    derniere_sync = st.session_state.get('derniere_sync', 'Jamais')
    st.metric("Dernière sync", derniere_sync)

with col_sync2:
    nouvelles_reponses = st.session_state.get('nouvelles_reponses', 0)
    st.metric("Nouvelles réponses", nouvelles_reponses)

if st.button("🔄 Synchroniser maintenant", type="primary"):
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if config.get('email') and config.get('app_password'):
            with st.spinner("Synchronisation en cours..."):
                sync = GmailSync(config)
                stats = sync.synchroniser_boite_reception()
                
                st.session_state.derniere_sync = time.strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.nouvelles_reponses = stats.get('reponses_trouvees', 0)
                
                st.success(f"✅ Sync terminée : {stats.get('reponses_trouvees', 0)} nouvelles réponses trouvées")
        else:
            st.error("Veuillez d'abord configurer Gmail")
    else:
        st.error("Veuillez d'abord configurer Gmail")

auto_sync = st.checkbox(
    "Synchronisation automatique (toutes les 30 min)",
    value=st.session_state.get('auto_sync_enabled', False)
)

if auto_sync:
    st.session_state.auto_sync_enabled = True
    st.info("La synchronisation automatique sera activée au prochain démarrage")
else:
    st.session_state.auto_sync_enabled = False

st.divider()

# Paramètres avancés
st.subheader("⚙️ Paramètres avancés")

col_adv1, col_adv2 = st.columns(2)

with col_adv1:
    rate_limit = st.slider("Emails max par jour", 10, 200, 50)
    st.session_state.rate_limit = rate_limit

with col_adv2:
    delai_entre_emails = st.slider("Délai entre emails (secondes)", 5, 120, 30)
    st.session_state.delai_entre_emails = delai_entre_emails

retry_failed = st.checkbox("Réessayer les emails échoués", value=True)
st.session_state.retry_failed = retry_failed

st.divider()

# Templates d'emails
st.subheader("📝 Templates d'emails")

st.info("Les templates sont définis dans le code. Pour les modifier, éditez `emails/generator.py`")

if st.button("Voir le template actuel"):
    from emails.generator import EMAIL_TEMPLATE
    st.code(EMAIL_TEMPLATE, language='html')

