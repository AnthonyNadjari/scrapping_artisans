"""
Page Réponses - Gestion des réponses WhatsApp avec statuts améliorés
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import time
import sqlite3

# Configuration de la page
st.set_page_config(page_title="Réponses WhatsApp", page_icon="💬", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, get_statistiques, sauvegarder_reponse
from whatsapp_database.models import get_connection
from whatsapp.link_generator import WhatsAppLinkGenerator

st.title("💬 Gestion des Réponses")

# Stats
stats = get_statistiques()

col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

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

with col_stat4:
    # Compter les intéressés (tous les statuts positifs)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE statut_reponse IN ('interesse', 'en_negociation', 'devis_envoye', 'client')")
    interesses = cursor.fetchone()[0]
    conn.close()
    
    st.metric("Intéressés", f"{interesses:,}")

st.markdown("---")

# Définir les statuts avec leurs couleurs et icônes
STATUTS_CONFIG = {
    "": {"label": "⏳ En attente", "color": "#808080", "emoji": "⏳"},
    "interesse": {"label": "✅ Intéressé", "color": "#28a745", "emoji": "✅"},
    "pas_interesse": {"label": "❌ Pas intéressé", "color": "#dc3545", "emoji": "❌"},
    "en_negociation": {"label": "💼 En négociation", "color": "#ffc107", "emoji": "💼"},
    "devis_envoye": {"label": "📄 Devis envoyé", "color": "#17a2b8", "emoji": "📄"},
    "client": {"label": "🎉 Client", "color": "#6f42c1", "emoji": "🎉"},
    "a_relancer": {"label": "🔄 À relancer", "color": "#fd7e14", "emoji": "🔄"},
    "ne_pas_contacter": {"label": "🚫 Ne pas contacter", "color": "#6c757d", "emoji": "🚫"}
}

# Tabs pour différents statuts
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🆕 À traiter",
    "✅ Intéressés",
    "❌ Pas intéressés",
    "🔄 À relancer",
    "📋 Toutes les réponses"
])

# Fonction pour mettre à jour le statut
def mettre_a_jour_statut(artisan_id: int, statut: str, commentaire: str = None):
    """Met à jour le statut et le commentaire d'un artisan"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    if statut:
        cursor.execute("""
            UPDATE artisans 
            SET statut_reponse = ?, commentaire = ?, a_repondu = 1, date_reponse = ?
            WHERE id = ?
        """, (statut, commentaire, now, artisan_id))
    else:
        cursor.execute("""
            UPDATE artisans 
            SET commentaire = ?
            WHERE id = ?
        """, (commentaire, artisan_id))
    
    conn.commit()
    conn.close()

# Tab 1: À traiter
with tab1:
    st.subheader("🆕 Artisans à traiter")
    
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Artisans contactés mais sans statut
    cursor.execute("""
        SELECT * FROM artisans 
        WHERE message_envoye = 1 
        AND (statut_reponse IS NULL OR statut_reponse = '')
        ORDER BY date_envoi DESC
        LIMIT 100
    """)
    
    a_traiter = cursor.fetchall()
    conn.close()
    
    if not a_traiter:
        st.success("✅ Tout est à jour ! Aucun artisan à traiter.")
    else:
        st.info(f"📋 {len(a_traiter)} artisans à traiter")
        
        for artisan_row in a_traiter:
            artisan = dict(artisan_row)
            
            with st.container():
                # Carte avec style
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #007bff;">
                    <h4 style="margin: 0; color: #212529;">{artisan.get('nom_entreprise', 'N/A')}</h4>
                    <p style="margin: 0.3rem 0; color: #6c757d; font-size: 0.9rem;">
                        {artisan.get('type_artisan', '')} • {artisan.get('ville', '')} ({artisan.get('departement', '')})
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.caption(f"📱 {artisan.get('telephone', '')}")
                    
                    if artisan.get('date_envoi'):
                        try:
                            dt = datetime.fromisoformat(artisan['date_envoi'].replace('Z', '+00:00'))
                            st.caption(f"📅 Contacté le {dt.strftime('%d/%m/%Y à %H:%M')}")
                        except:
                            pass
                    
                    if artisan.get('derniere_reponse'):
                        st.info(f"💬 **Réponse reçue :** {artisan['derniere_reponse']}")
                
                with col2:
                    statut = st.selectbox(
                        "📊 Statut",
                        ["", "interesse", "pas_interesse", "en_negociation", "devis_envoye", "client", "a_relancer", "ne_pas_contacter"],
                        format_func=lambda x: STATUTS_CONFIG.get(x, {}).get("label", "⏳ En attente") if x else "⏳ En attente",
                        key=f"statut_{artisan['id']}"
                    )
                    
                    commentaire = st.text_area(
                        "💬 Commentaire",
                        value=artisan.get('commentaire', ''),
                        key=f"comment_{artisan['id']}",
                        placeholder="Note personnelle, détails de la conversation...",
                        height=80
                    )
                    
                    if st.button("💾 Sauvegarder", key=f"save_{artisan['id']}"):
                        mettre_a_jour_statut(artisan['id'], statut, commentaire)
                        st.success("✅ Sauvegardé !")
                        time.sleep(0.5)
                        st.experimental_rerun()
                
                st.markdown("---")

# Tab 2: Intéressés
with tab2:
    st.subheader("✅ Artisans intéressés")
    
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM artisans 
        WHERE statut_reponse IN ('interesse', 'en_negociation', 'devis_envoye', 'client')
        ORDER BY date_reponse DESC
    """)
    
    interesses = cursor.fetchall()
    conn.close()
    
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    with col_met1:
        st.metric("Total intéressés", len([a for a in interesses if dict(a).get('statut_reponse') == 'interesse']))
    with col_met2:
        st.metric("En négociation", len([a for a in interesses if dict(a).get('statut_reponse') == 'en_negociation']))
    with col_met3:
        st.metric("Devis envoyés", len([a for a in interesses if dict(a).get('statut_reponse') == 'devis_envoye']))
    with col_met4:
        st.metric("Clients", len([a for a in interesses if dict(a).get('statut_reponse') == 'client']))
    
    if interesses:
        for artisan_row in interesses:
            artisan = dict(artisan_row)
            statut = artisan.get('statut_reponse', '')
            config_statut = STATUTS_CONFIG.get(statut, {})
            
            with st.container():
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, {config_statut.get('color', '#007bff')}15 0%, transparent 100%); 
                            padding: 1rem; border-radius: 8px; margin: 0.5rem 0; 
                            border-left: 4px solid {config_statut.get('color', '#007bff')};">
                    <h4 style="margin: 0; color: #212529;">
                        {config_statut.get('emoji', '✅')} {artisan.get('nom_entreprise', 'N/A')} 
                        <span style="font-size: 0.8rem; color: {config_statut.get('color', '#007bff')}; font-weight: normal;">
                            [{config_statut.get('label', statut)}]
                        </span>
                    </h4>
                    <p style="margin: 0.3rem 0; color: #6c757d; font-size: 0.9rem;">
                        {artisan.get('type_artisan', '')} • {artisan.get('ville', '')} ({artisan.get('departement', '')})
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.caption(f"📱 {artisan.get('telephone', '')}")
                    
                    if artisan.get('commentaire'):
                        st.info(f"💬 **Commentaire :** {artisan['commentaire']}")
                    
                    if artisan.get('derniere_reponse'):
                        st.success(f"📨 **Réponse :** {artisan['derniere_reponse']}")
                    
                    if artisan.get('date_reponse'):
                        try:
                            dt = datetime.fromisoformat(artisan['date_reponse'].replace('Z', '+00:00'))
                            st.caption(f"📅 Répondu le {dt.strftime('%d/%m/%Y à %H:%M')}")
                        except:
                            pass
                
                with col2:
                    link_gen = WhatsAppLinkGenerator()
                    template = "Bonjour, merci pour votre intérêt !"
                    lien = link_gen.generer_lien(artisan, template)
                    st.link_button("💬 Recontacter", lien)
                    
                    # Modifier statut
                    nouveau_statut = st.selectbox(
                        "Changer statut",
                        ["interesse", "en_negociation", "devis_envoye", "client", "pas_interesse", "a_relancer"],
                        format_func=lambda x: STATUTS_CONFIG.get(x, {}).get("label", x),
                        index=["interesse", "en_negociation", "devis_envoye", "client", "pas_interesse", "a_relancer"].index(statut) if statut in ["interesse", "en_negociation", "devis_envoye", "client", "pas_interesse", "a_relancer"] else 0,
                        key=f"change_{artisan['id']}"
                    )
                    
                    if nouveau_statut != statut:
                        if st.button("Modifier", key=f"modif_{artisan['id']}"):
                            mettre_a_jour_statut(artisan['id'], nouveau_statut, artisan.get('commentaire'))
                            st.experimental_rerun()
                
                st.markdown("---")
    else:
        st.info("Aucun artisan intéressé pour le moment")

# Tab 3: Pas intéressés / Ne pas contacter
with tab3:
    st.subheader("❌ Artisans pas intéressés / Ne pas contacter")
    
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM artisans 
        WHERE statut_reponse IN ('pas_interesse', 'ne_pas_contacter')
        ORDER BY date_reponse DESC
    """)
    
    pas_interesses = cursor.fetchall()
    conn.close()
    
    col_met1, col_met2 = st.columns(2)
    with col_met1:
        st.metric("Pas intéressés", len([a for a in pas_interesses if dict(a).get('statut_reponse') == 'pas_interesse']))
    with col_met2:
        st.metric("Ne pas contacter", len([a for a in pas_interesses if dict(a).get('statut_reponse') == 'ne_pas_contacter']))
    
    if pas_interesses:
        for artisan_row in pas_interesses:
            artisan = dict(artisan_row)
            statut = artisan.get('statut_reponse', '')
            config_statut = STATUTS_CONFIG.get(statut, {})
            
            with st.container():
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 0.8rem; border-radius: 6px; margin: 0.3rem 0; 
                            border-left: 3px solid {config_statut.get('color', '#dc3545')};">
                    <strong>{config_statut.get('emoji', '❌')} {artisan.get('nom_entreprise', 'N/A')}</strong> 
                    - {artisan.get('ville', '')} ({artisan.get('departement', '')})
                </div>
                """, unsafe_allow_html=True)
                
                if artisan.get('commentaire'):
                    st.caption(f"💬 {artisan['commentaire']}")
                
                if artisan.get('derniere_reponse'):
                    st.caption(f"📨 Réponse : {artisan['derniere_reponse']}")
                
                st.markdown("---")
    else:
        st.info("Aucun artisan marqué comme pas intéressé")

# Tab 4: À relancer
with tab4:
    st.subheader("🔄 Artisans à relancer")
    
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM artisans 
        WHERE statut_reponse = 'a_relancer'
        ORDER BY date_reponse DESC
    """)
    
    a_relancer = cursor.fetchall()
    conn.close()
    
    st.metric("À relancer", len(a_relancer))
    
    if a_relancer:
        for artisan_row in a_relancer:
            artisan = dict(artisan_row)
            
            with st.container():
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, #fd7e1415 0%, transparent 100%); 
                            padding: 1rem; border-radius: 8px; margin: 0.5rem 0; 
                            border-left: 4px solid #fd7e14;">
                    <h4 style="margin: 0; color: #212529;">
                        🔄 {artisan.get('nom_entreprise', 'N/A')} - {artisan.get('ville', '')}
                    </h4>
                    <p style="margin: 0.3rem 0; color: #6c757d; font-size: 0.9rem;">
                        {artisan.get('type_artisan', '')} • {artisan.get('departement', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.caption(f"📱 {artisan.get('telephone', '')}")
                    
                    if artisan.get('commentaire'):
                        st.info(f"💬 **Commentaire :** {artisan['commentaire']}")
                    
                    if artisan.get('derniere_reponse'):
                        st.caption(f"📨 Dernière réponse : {artisan['derniere_reponse']}")
                    
                    if artisan.get('date_reponse'):
                        try:
                            dt = datetime.fromisoformat(artisan['date_reponse'].replace('Z', '+00:00'))
                            st.caption(f"📅 Dernier contact le {dt.strftime('%d/%m/%Y à %H:%M')}")
                        except:
                            pass
                
                with col2:
                    link_gen = WhatsAppLinkGenerator()
                    template = "Bonjour, je relance pour voir si vous êtes toujours intéressé ?"
                    lien = link_gen.generer_lien(artisan, template)
                    st.link_button("💬 Relancer", lien)
                    
                    # Changer statut
                    nouveau_statut = st.selectbox(
                        "Changer statut",
                        ["a_relancer", "interesse", "en_negociation", "pas_interesse", "ne_pas_contacter"],
                        format_func=lambda x: STATUTS_CONFIG.get(x, {}).get("label", x),
                        index=0,
                        key=f"relancer_{artisan['id']}"
                    )
                    
                    if nouveau_statut != "a_relancer":
                        if st.button("Modifier", key=f"modif_relancer_{artisan['id']}"):
                            mettre_a_jour_statut(artisan['id'], nouveau_statut, artisan.get('commentaire'))
                            st.experimental_rerun()
                
                st.markdown("---")
    else:
        st.info("Aucun artisan à relancer")

# Tab 5: Toutes les réponses
with tab5:
    st.subheader("📋 Toutes les réponses")
    
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM artisans 
        WHERE a_repondu = 1
        ORDER BY date_reponse DESC
        LIMIT 200
    """)
    
    toutes = cursor.fetchall()
    conn.close()
    
    st.metric("Total réponses", len(toutes))
    
    if toutes:
        # Filtre par statut
        filtre_statut = st.selectbox(
            "Filtrer par statut",
            ["Tous", "acceptation", "off", "en_cours", "a_relancer", "Sans statut"]
        )
        
        if filtre_statut != "Tous":
            if filtre_statut == "Sans statut":
                toutes = [dict(a) for a in toutes if not a.get('statut_reponse')]
            else:
                toutes = [dict(a) for a in toutes if a.get('statut_reponse') == filtre_statut]
        
        for artisan_row in toutes:
            artisan = dict(artisan_row)
            
            # Badge statut avec style
            statut = artisan.get('statut_reponse', '')
            config_statut = STATUTS_CONFIG.get(statut, STATUTS_CONFIG[""])
            badge_emoji = config_statut.get('emoji', '📋')
            badge_label = config_statut.get('label', 'Sans statut')
            badge_color = config_statut.get('color', '#6c757d')
            
            with st.expander(f"{badge_emoji} {badge_label} - {artisan.get('nom_entreprise', 'N/A')} - {artisan.get('ville', '')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Métier :** {artisan.get('type_artisan', '')}")
                    st.write(f"**Ville :** {artisan.get('ville', '')} ({artisan.get('departement', '')})")
                    st.write(f"**Téléphone :** {artisan.get('telephone', '')}")
                    
                    if artisan.get('derniere_reponse'):
                        st.info(f"📨 Réponse : {artisan['derniere_reponse']}")
                    
                    if artisan.get('date_reponse'):
                        try:
                            dt = datetime.fromisoformat(artisan['date_reponse'].replace('Z', '+00:00'))
                            st.caption(f"Répondu le {dt.strftime('%d/%m/%Y à %H:%M')}")
                        except:
                            pass
                
                with col2:
                    if artisan.get('commentaire'):
                        st.text_area("Commentaire", value=artisan['commentaire'], disabled=True)
                    
                    # Modifier statut et commentaire
                    nouveau_statut = st.selectbox(
                        "Statut",
                        ["", "interesse", "pas_interesse", "en_negociation", "devis_envoye", "client", "a_relancer", "ne_pas_contacter"],
                        format_func=lambda x: STATUTS_CONFIG.get(x, {}).get("label", "⏳ En attente") if x else "⏳ En attente",
                        index=["", "interesse", "pas_interesse", "en_negociation", "devis_envoye", "client", "a_relancer", "ne_pas_contacter"].index(statut) if statut in ["", "interesse", "pas_interesse", "en_negociation", "devis_envoye", "client", "a_relancer", "ne_pas_contacter"] else 0,
                        key=f"all_statut_{artisan['id']}"
                    )
                    
                    nouveau_commentaire = st.text_area(
                        "Commentaire",
                        value=artisan.get('commentaire', ''),
                        key=f"all_comment_{artisan['id']}"
                    )
                    
                    if st.button("💾 Sauvegarder", key=f"all_save_{artisan['id']}"):
                        mettre_a_jour_statut(artisan['id'], nouveau_statut, nouveau_commentaire)
                        st.success("✅ Sauvegardé !")
                        time.sleep(0.5)
                        st.experimental_rerun()
    else:
        st.info("Aucune réponse enregistrée")

st.markdown("---")

# Section pour ajouter manuellement une réponse
with st.expander("✏️ Ajouter une réponse manuellement"):
    with st.form("ajouter_reponse"):
        recherche_tel = st.text_input("Rechercher par téléphone", placeholder="0612345678")
        contenu_reponse = st.text_area("Contenu de la réponse", height=100)
        statut_manuel = st.selectbox(
            "Statut", 
            ["", "interesse", "pas_interesse", "en_negociation", "devis_envoye", "client", "a_relancer", "ne_pas_contacter"],
            format_func=lambda x: STATUTS_CONFIG.get(x, {}).get("label", "⏳ En attente") if x else "⏳ En attente"
        )
        commentaire_manuel = st.text_area("Commentaire", placeholder="Note personnelle...")
        
        if st.form_submit_button("💾 Enregistrer"):
            if recherche_tel and contenu_reponse:
                from whatsapp_database.queries import get_artisan_par_telephone
                artisan = get_artisan_par_telephone(recherche_tel)
                
                if artisan:
                    sauvegarder_reponse(artisan['id'], contenu_reponse, f"manual_{int(time.time())}")
                    if statut_manuel:
                        mettre_a_jour_statut(artisan['id'], statut_manuel, commentaire_manuel)
                    st.success(f"✅ Réponse enregistrée pour {artisan.get('nom_entreprise', 'N/A')}")
                    st.experimental_rerun()
                else:
                    st.error("❌ Artisan non trouvé avec ce numéro")
            else:
                st.warning("Veuillez remplir le téléphone et le contenu")
