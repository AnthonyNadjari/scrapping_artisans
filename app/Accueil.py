"""
Application principale Streamlit - Page d'accueil
"""
import streamlit as st
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import init_database
from database.queries import get_statistiques
import plotly.express as px
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Prospection Artisans - Cold Email",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialiser la base de données au démarrage
if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True

# Titre principal
st.title("📧 Système de Prospection par Cold Email")
st.markdown("### Pour artisans français - Gestion complète de campagnes")

st.divider()

# Statistiques globales
st.subheader("📊 Vue d'ensemble")

stats = get_statistiques()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total artisans",
        f"{stats.get('total', 0):,}",
        help="Nombre total d'artisans dans la base"
    )

with col2:
    avec_email = stats.get('avec_email', 0)
    total = stats.get('total', 1)
    pourcentage = (avec_email / total * 100) if total > 0 else 0
    st.metric(
        "Avec email",
        f"{avec_email:,}",
        f"{pourcentage:.1f}%",
        help="Artisans ayant une adresse email"
    )

with col3:
    st.metric(
        "Non contactés",
        f"{stats.get('non_contactes', 0):,}",
        help="Artisans n'ayant pas encore reçu d'email"
    )

with col4:
    st.metric(
        "Emails envoyés",
        f"{stats.get('emails_envoyes', 0):,}",
        help="Nombre total d'emails envoyés"
    )

with col5:
    st.metric(
        "Ont répondu",
        f"{stats.get('repondus', 0):,}",
        help="Artisans ayant répondu aux emails"
    )

st.divider()

# Graphiques de performance
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📈 Performance emails")
    
    # Données exemple (à remplacer par vraies données)
    data_perf = {
        'Métrique': ['Envoyés', 'Ouverts', 'Réponses'],
        'Nombre': [
            stats.get('emails_envoyes', 0),
            stats.get('emails_ouverts', 0),
            stats.get('repondus', 0)
        ]
    }
    
    df_perf = pd.DataFrame(data_perf)
    fig_perf = px.bar(
        df_perf,
        x='Métrique',
        y='Nombre',
        color='Nombre',
        color_continuous_scale='Blues',
        title="Performance des campagnes"
    )
    st.plotly_chart(fig_perf, use_container_width=True)

with col_chart2:
    st.subheader("🎯 Taux de conversion")
    
    if stats.get('emails_envoyes', 0) > 0:
        taux_ouverture = (stats.get('emails_ouverts', 0) / stats.get('emails_envoyes', 1)) * 100
        taux_reponse = (stats.get('repondus', 0) / stats.get('emails_envoyes', 1)) * 100
        
        data_taux = {
            'Taux': ['Ouverture', 'Réponse'],
            'Pourcentage': [taux_ouverture, taux_reponse]
        }
        
        df_taux = pd.DataFrame(data_taux)
        fig_taux = px.bar(
            df_taux,
            x='Taux',
            y='Pourcentage',
            color='Pourcentage',
            color_continuous_scale='Greens',
            title="Taux de conversion (%)"
        )
        st.plotly_chart(fig_taux, use_container_width=True)
    else:
        st.info("Aucun email envoyé pour le moment")

st.divider()

# Actions rapides
st.subheader("🚀 Actions rapides")

col_act1, col_act2, col_act3, col_act4 = st.columns(4)

with col_act1:
    if st.button("🔍 Lancer le scraping", type="primary", use_container_width=True):
        st.switch_page("pages/1_🔍_Scraping.py")

with col_act2:
    if st.button("📊 Voir la base de données", use_container_width=True):
        st.switch_page("pages/2_📊_Base_de_Données.py")

with col_act3:
    if st.button("✉️ Gérer les campagnes", use_container_width=True):
        st.switch_page("pages/3_✉️_Campagnes.py")

with col_act4:
    if st.button("📈 Analytics", use_container_width=True):
        st.switch_page("pages/4_📈_Analytics.py")

st.divider()

# Guide de démarrage
with st.expander("📖 Guide de démarrage", expanded=False):
    st.markdown("""
    ### Bienvenue dans le système de prospection par cold email !
    
    **Étapes pour commencer :**
    
    1. **🔍 Scraping** : Lancez le scraping pour collecter des artisans
       - Configurez les sources (Google Maps, Pages Jaunes, SIRENE)
       - Sélectionnez les métiers et départements
       - Priorisez les petites communes pour de meilleurs résultats
    
    2. **📊 Base de données** : Consultez et filtrez vos artisans
       - Enrichissez les emails manquants
       - Vérifiez les doublons
       - Exportez en CSV si besoin
    
    3. **✉️ Campagnes** : Créez et gérez vos campagnes d'emails
       - Sélectionnez les artisans cibles
       - Personnalisez les templates
       - Envoyez par batch avec suivi
    
    4. **📈 Analytics** : Suivez vos performances
       - Taux d'ouverture et de réponse
       - Performance par métier/département
       - Meilleurs jours/heures pour envoyer
    
    5. **⚙️ Paramètres** : Configurez Gmail et autres options
       - Ajoutez vos identifiants Gmail
       - Configurez la sync automatique
       - Personnalisez les templates
    
    **💡 Astuce** : Commencez par scraper quelques communes pour tester, puis lancez une campagne complète !
    """)

# Footer
st.divider()
st.caption("💻 Système de prospection par cold email - Version 1.0")

