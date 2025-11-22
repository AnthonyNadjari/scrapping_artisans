"""
Page Analytics - Statistiques et performance
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.queries import get_statistiques, get_artisans, get_metiers_uniques

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Analytics & Performance")

# Période sélectionnée
periode = st.selectbox(
    "Période",
    ["7 derniers jours", "30 derniers jours", "Tout le temps"],
    index=2
)

# KPIs globaux
col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)

stats = get_statistiques()

with col_k1:
    st.metric("Emails envoyés", f"{stats.get('emails_envoyes', 0):,}")

with col_k2:
    envoyes = stats.get('emails_envoyes', 1)
    ouverts = stats.get('emails_ouverts', 0)
    taux_ouverture = (ouverts / envoyes * 100) if envoyes > 0 else 0
    st.metric("Taux d'ouverture", f"{taux_ouverture:.1f}%")

with col_k3:
    repondus = stats.get('repondus', 0)
    taux_reponse = (repondus / envoyes * 100) if envoyes > 0 else 0
    st.metric("Taux de réponse", f"{taux_reponse:.1f}%")

with col_k4:
    st.metric("Intéressés", "N/A", help="À calculer depuis les réponses")

with col_k5:
    st.metric("Clients signés", "N/A", help="À suivre manuellement")

st.divider()

# Graphiques
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Performance par métier")
    
    metiers = get_metiers_uniques()
    if metiers:
        # Calculer stats par métier
        stats_metiers = []
        for metier in metiers[:10]:  # Top 10
            artisans_metier = get_artisans({'metiers': [metier]}, limit=1000)
            envoyes = sum(1 for a in artisans_metier if a.get('email_envoye'))
            ouverts = sum(1 for a in artisans_metier if a.get('email_ouvert'))
            repondus = sum(1 for a in artisans_metier if a.get('a_repondu'))
            
            stats_metiers.append({
                'Métier': metier,
                'Envoyés': envoyes,
                'Ouverts': ouverts,
                'Réponses': repondus
            })
        
        if stats_metiers:
            df_metiers = pd.DataFrame(stats_metiers)
            fig_metiers = px.bar(
                df_metiers,
                x='Métier',
                y=['Envoyés', 'Ouverts', 'Réponses'],
                barmode='group',
                title="Performance par métier"
            )
            st.plotly_chart(fig_metiers, use_container_width=True)
    else:
        st.info("Pas encore de données par métier")

with col_chart2:
    st.subheader("🎯 Taux de conversion")
    
    if stats.get('emails_envoyes', 0) > 0:
        data_taux = {
            'Étape': ['Envoyés', 'Ouverts', 'Réponses'],
            'Nombre': [
                stats.get('emails_envoyes', 0),
                stats.get('emails_ouverts', 0),
                stats.get('repondus', 0)
            ]
        }
        
        df_taux = pd.DataFrame(data_taux)
        fig_taux = px.funnel(
            df_taux,
            x='Nombre',
            y='Étape',
            title="Funnel de conversion"
        )
        st.plotly_chart(fig_taux, use_container_width=True)
    else:
        st.info("Aucune donnée pour le moment")

st.divider()

# Performance géographique
st.subheader("🗺️ Performance géographique")

depts = get_artisans({}, limit=10000)
if depts:
    # Grouper par département
    stats_dept = {}
    for artisan in depts:
        dept = artisan.get('departement', 'N/A')
        if dept not in stats_dept:
            stats_dept[dept] = {'envoyes': 0, 'ouverts': 0, 'repondus': 0}
        
        if artisan.get('email_envoye'):
            stats_dept[dept]['envoyes'] += 1
        if artisan.get('email_ouvert'):
            stats_dept[dept]['ouverts'] += 1
        if artisan.get('a_repondu'):
            stats_dept[dept]['repondus'] += 1
    
    if stats_dept:
        df_dept = pd.DataFrame([
            {
                'Département': dept,
                'Envoyés': data['envoyes'],
                'Ouverts': data['ouverts'],
                'Réponses': data['repondus'],
                'Taux réponse': (data['repondus'] / data['envoyes'] * 100) if data['envoyes'] > 0 else 0
            }
            for dept, data in stats_dept.items()
        ])
        
        fig_dept = px.bar(
            df_dept,
            x='Département',
            y='Taux réponse',
            color='Taux réponse',
            color_continuous_scale='RdYlGn',
            title="Taux de réponse par département"
        )
        st.plotly_chart(fig_dept, use_container_width=True)

st.divider()

# Recommandations
st.subheader("💡 Recommandations")

col_rec1, col_rec2 = st.columns(2)

with col_rec1:
    st.info("""
    **Meilleurs jours pour envoyer :**
    - Mardi et Mercredi : meilleur taux d'ouverture
    - Éviter le lundi matin et vendredi après-midi
    """)

with col_rec2:
    st.info("""
    **Meilleures heures :**
    - 9h-11h : meilleur moment
    - 14h-16h : deuxième meilleur créneau
    - Éviter 12h-13h (pause déjeuner)
    """)

