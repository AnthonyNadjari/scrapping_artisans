"""
Page Paramètres - Configuration WhatsApp Web
"""
import streamlit as st
import sys
from pathlib import Path

# Configuration de la page
st.set_page_config(page_title="Paramètres", page_icon="⚙️", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp.whatsapp_web_manager import WhatsAppWebManager

st.title("⚙️ Paramètres")

st.markdown("### 📱 Configuration WhatsApp Web")

st.info("""
**WhatsApp Web ne nécessite pas de configuration Meta/Facebook !**

Vous utilisez simplement votre numéro WhatsApp Business existant via WhatsApp Web.

**Comment ça marche :**
1. Cliquez sur "Se connecter" dans la page Campagne
2. Un navigateur s'ouvre avec WhatsApp Web
3. Scannez le QR code avec votre téléphone
4. La session est sauvegardée automatiquement
5. Vous pouvez envoyer des messages !

**Avantages :**
- ✅ Gratuit
- ✅ Utilise votre numéro existant
- ✅ Pas besoin de Meta/Facebook
- ✅ Simple et direct

**Limites :**
- ⚠️ ~50-100 messages/jour recommandés pour éviter les bans
- ⚠️ Nécessite de garder la session active
""")

st.markdown("---")

# Test connexion
st.markdown("### 🧪 Tester la Connexion")

if st.button("🔌 Tester la connexion WhatsApp Web"):
    with st.spinner("Test en cours..."):
        manager = WhatsAppWebManager(headless=True)
        success, message, qr_url = manager.connecter(wait_for_qr=False)
        
        if success:
            st.success("✅ Connexion réussie !")
            manager.deconnecter()
        else:
            st.warning(f"⚠️ {message}")
            if qr_url:
                st.info("Ouvrez WhatsApp Web dans votre navigateur pour scanner le QR code")

st.markdown("---")

# Paramètres avancés
st.markdown("### ⚙️ Paramètres Avancés")

st.info("Les paramètres de rate limiting sont configurés dans la page Campagne WhatsApp")

# Info session
st.markdown("### 💾 Session WhatsApp")

session_path = Path(__file__).parent.parent.parent / "data" / "whatsapp_session"
if session_path.exists():
    st.success(f"✅ Session sauvegardée : {session_path}")
    st.caption("La session est sauvegardée automatiquement pour éviter de rescanner le QR code")
    
    if st.button("🗑️ Supprimer la session"):
        import shutil
        try:
            shutil.rmtree(session_path)
            st.success("✅ Session supprimée")
            st.info("Vous devrez rescanner le QR code à la prochaine connexion")
        except Exception as e:
            st.error(f"Erreur : {e}")
else:
    st.info("Aucune session sauvegardée")

