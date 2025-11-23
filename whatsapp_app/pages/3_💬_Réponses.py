"""
Page Réponses - Gestion des réponses WhatsApp
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import time

# Configuration de la page
st.set_page_config(page_title="Réponses WhatsApp", page_icon="💬", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, get_statistiques, get_artisan_par_telephone, sauvegarder_reponse
from whatsapp_database.models import get_connection
import sqlite3

st.title("💬 Réponses WhatsApp")

# Stats
stats = get_statistiques()

col_stat1, col_stat2, col_stat3 = st.columns(3)

with col_stat1:
    st.metric("Messages envoyés", f"{stats.get('messages_envoyes', 0):,}")

with col_stat2:
    st.metric("Ont répondu", f"{stats.get('repondus', 0):,}")

with col_stat3:
    if stats.get('messages_envoyes', 0) > 0:
        taux = (stats.get('repondus', 0) / stats.get('messages_envoyes', 1)) * 100
        st.metric("Taux de réponse", f"{taux:.1f}%")
    else:
        st.metric("Taux de réponse", "0%")

st.markdown("---")

# Bouton refresh
st.markdown("### 🔄 Récupérer les Réponses")

col_refresh1, col_refresh2 = st.columns([3, 1])

with col_refresh1:
    st.info("""
    **Note :** WhatsApp Web ne permet pas facilement de récupérer automatiquement les messages.
    
    Pour voir les réponses :
    1. Ouvrez WhatsApp Web dans votre navigateur
    2. Consultez vos conversations
    3. Marquez manuellement les réponses dans cette interface
    """)

with col_refresh2:
    if st.button("🔄 Refresh", type="primary"):
        st.info("⚠️ Récupération automatique non disponible avec WhatsApp Web")
        st.info("Consultez WhatsApp Web manuellement et marquez les réponses ci-dessous")

st.markdown("---")

# Afficher les réponses
st.markdown("### 📨 Réponses Reçues")

conn = get_connection()
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Récupérer les artisans qui ont répondu
cursor.execute("""
    SELECT a.*, r.contenu, r.date_reception
    FROM artisans a
    JOIN reponses r ON a.id = r.artisan_id
    ORDER BY r.date_reception DESC
    LIMIT 50
""")

reponses = cursor.fetchall()
conn.close()

if reponses:
    st.write(f"**{len(reponses)} réponses trouvées**")
    
    for reponse in reponses:
        artisan = dict(reponse)
        
        with st.container():
            col_rep1, col_rep2 = st.columns([4, 1])
            
            with col_rep1:
                st.markdown(f"**📱 {artisan.get('nom_entreprise', 'N/A')}** - {artisan.get('type_artisan', '')}")
                st.caption(f"{artisan.get('ville', '')} ({artisan.get('departement', '')}) - {artisan.get('telephone', '')}")
                
                # Date
                date_reception = artisan.get('date_reception', '')
                if date_reception:
                    try:
                        dt = datetime.fromisoformat(date_reception.replace('Z', '+00:00'))
                        st.caption(f"Reçu : {dt.strftime('%d/%m/%Y %H:%M')}")
                    except:
                        st.caption(f"Reçu : {date_reception}")
                
                # Contenu
                contenu = artisan.get('contenu', '')
                st.info(contenu if contenu else "Aucun contenu")
            
            with col_rep2:
                if st.button("✓ Traité", key=f"traite_{artisan['id']}"):
                    st.success("Marqué comme traité")
            
            st.markdown("---")
else:
    st.info("Aucune réponse enregistrée pour le moment")

st.markdown("---")

# Marquer manuellement une réponse
st.markdown("### ✏️ Marquer une Réponse Manuellement")

with st.form("marquer_reponse"):
    recherche_tel = st.text_input("Rechercher par téléphone", placeholder="0612345678")
    
    contenu_reponse = st.text_area("Contenu de la réponse", height=100)
    
    if st.form_submit_button("💾 Enregistrer la réponse"):
        if recherche_tel and contenu_reponse:
            from whatsapp_database.queries import get_artisan_par_telephone, sauvegarder_reponse
            
            artisan = get_artisan_par_telephone(recherche_tel)
            
            if artisan:
                sauvegarder_reponse(artisan['id'], contenu_reponse, f"manual_{int(time.time())}")
                st.success(f"✅ Réponse enregistrée pour {artisan.get('nom_entreprise', 'N/A')}")
            else:
                st.error("❌ Artisan non trouvé avec ce numéro")
        else:
            st.warning("Veuillez remplir tous les champs")

