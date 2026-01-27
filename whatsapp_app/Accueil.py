"""
Application principale Streamlit - WhatsApp Prospection
"""
import streamlit as st
import sys
from pathlib import Path

# Configuration de la page - DOIT être en premier !
st.set_page_config(
    page_title="Prospection WhatsApp Artisans",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from whatsapp_database.models import init_database
from whatsapp_database.queries import get_statistiques
import plotly.express as px
import pandas as pd

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #25D366 0%, #128C7E 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser la base de données automatiquement (ajoute les nouvelles colonnes si nécessaire)
try:
    init_database()
except Exception as e:
    # Ne pas bloquer si erreur, mais logger
    import logging
    logging.warning(f"Erreur initialisation BDD: {e}")

# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 2.5rem;">📱 Prospection WhatsApp pour Artisans</h1>
    <p style="margin:0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Système simplifié de prospection par WhatsApp</p>
</div>
""", unsafe_allow_html=True)

# Statistiques globales
st.markdown("### 📊 Vue d'ensemble")
st.markdown("---")

stats = get_statistiques()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total artisans", f"{stats.get('total', 0):,}")

with col2:
    avec_whatsapp = stats.get('avec_whatsapp', 0)
    avec_tel = stats.get('avec_telephone', 1)
    pourcentage = (avec_whatsapp / avec_tel * 100) if avec_tel > 0 else 0
    st.metric("Avec WhatsApp", f"{avec_whatsapp:,}", f"{pourcentage:.1f}%")

with col3:
    st.metric("Messages envoyés", f"{stats.get('messages_envoyes', 0):,}")

with col4:
    st.metric("Messages aujourd'hui", f"{stats.get('messages_aujourdhui', 0):,}")

with col5:
    st.metric("Ont répondu", f"{stats.get('repondus', 0):,}")

st.markdown("---")

# Graphiques
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### 📈 Performance messages")
    
    if stats.get('messages_envoyes', 0) > 0:
        data_perf = {
            'Métrique': ['Envoyés', 'Réponses'],
            'Nombre': [
                stats.get('messages_envoyes', 0),
                stats.get('repondus', 0)
            ]
        }
        
        df_perf = pd.DataFrame(data_perf)
        fig_perf = px.bar(
            df_perf,
            x='Métrique',
            y='Nombre',
            color='Nombre',
            color_continuous_scale='Greens',
            title="Performance des campagnes"
        )
        fig_perf.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig_perf, use_container_width=True)
    else:
        st.info("📊 Aucune donnée pour le moment. Lancez votre première campagne !")

with col_chart2:
    st.markdown("#### 🎯 Taux de réponse")
    
    if stats.get('messages_envoyes', 0) > 0:
        taux_reponse = (stats.get('repondus', 0) / stats.get('messages_envoyes', 1)) * 100
        
        st.metric("Taux de réponse", f"{taux_reponse:.1f}%")
        
        # Graphique simple
        fig_taux = px.pie(
            values=[stats.get('repondus', 0), 
                   stats.get('messages_envoyes', 0) - stats.get('repondus', 0)],
            names=['Réponses', 'Pas de réponse'],
            title="Répartition des réponses"
        )
        fig_taux.update_layout(height=300)
        st.plotly_chart(fig_taux, use_container_width=True)
    else:
        st.info("📊 Aucune donnée pour le moment.")

st.markdown("---")

# Guide
st.info("💡 Utilisez le menu de navigation à gauche pour accéder aux différentes pages")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 1rem;'>💻 Système de prospection WhatsApp - Version 1.0</div>", unsafe_allow_html=True)

