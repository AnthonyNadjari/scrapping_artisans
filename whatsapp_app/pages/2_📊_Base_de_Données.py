"""
Page Base de Données - Accès à la base et génération liens WhatsApp
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Base de Données", page_icon="📊", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, get_statistiques, marquer_message_envoye
from whatsapp_database.models import get_connection
from whatsapp.link_generator import WhatsAppLinkGenerator
import sqlite3

st.title("📊 Base de Données - Artisans")

# Stats globales
stats = get_statistiques()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total artisans", f"{stats.get('total', 0):,}")
with col2:
    st.metric("Avec téléphone", f"{stats.get('avec_telephone', 0):,}")
with col3:
    st.metric("Messages envoyés", f"{stats.get('messages_envoyes', 0):,}")
with col4:
    st.metric("Ont répondu", f"{stats.get('repondus', 0):,}")

st.markdown("---")

# Template de message
st.subheader("📝 Template de Message WhatsApp")

template_defaut = """Bonjour {prenom},

Je suis Anthony, développeur web.
Je crée des sites professionnels pour artisans :

• 200€ tout compris
• Hébergement inclus 1 an
• Sans abonnement

Exemple : plomberie-fluide.vercel.app

Intéressé ? 😊"""

template = st.text_area(
    "Votre message (utilisez {prenom}, {ville}, {metier}, {entreprise})",
    value=template_defaut,
    height=200,
    help="Variables disponibles : {prenom}, {nom}, {entreprise}, {ville}, {metier}"
)

# Preview avec exemple
with st.expander("👁️ Aperçu du message", expanded=False):
    link_gen = WhatsAppLinkGenerator()
    # Prendre un artisan exemple
    artisans_exemple = get_artisans(limit=1)
    if artisans_exemple:
        exemple_artisan = artisans_exemple[0]
        # S'assurer que toutes les valeurs sont des strings
        exemple_artisan = {k: (v if v is not None else '') for k, v in exemple_artisan.items()}
        try:
            message_preview = link_gen.generer_message(exemple_artisan, template)
            st.code(message_preview)
            nb_chars = len(message_preview)
            if nb_chars > 1000:
                st.warning(f"⚠️ Message long ({nb_chars} caractères)")
            else:
                st.success(f"✅ {nb_chars} caractères")
        except Exception as e:
            st.error(f"❌ Erreur génération message: {e}")
            st.info("💡 Vérifiez que le template utilise les bonnes variables")
    else:
        st.info("💡 Aucun artisan en base. Lancez d'abord l'acquisition SIRENE.")

st.markdown("---")

# Filtres
st.subheader("🔍 Filtres de Recherche")

col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    filtre_statut = st.selectbox(
        "Statut message",
        ["Tous", "Non contactés", "Contactés", "Ont répondu"]
    )

with col_f2:
    filtre_metier = st.multiselect(
        "Métier",
        options=["plombier", "électricien", "menuisier", "peintre", "chauffagiste", "carreleur", "maçon", "charpentier"],
        default=[]
    )

with col_f3:
    filtre_dept = st.text_input(
        "Département",
        placeholder="77, 78, 91..."
    )

with col_f4:
    filtre_recherche = st.text_input(
        "Recherche",
        placeholder="Nom, ville, téléphone..."
    )

# Construire filtres
filtres = {}
if filtre_statut == "Non contactés":
    filtres['non_contactes'] = True
elif filtre_statut == "Contactés":
    filtres['message_envoye'] = True
elif filtre_statut == "Ont répondu":
    filtres['a_repondu'] = True

if filtre_metier:
    filtres['metiers'] = filtre_metier

if filtre_dept:
    depts = [d.strip() for d in filtre_dept.split(',')]
    filtres['departements'] = depts

if filtre_recherche:
    filtres['recherche'] = filtre_recherche

# ✅ Bouton pour requêter la BDD (rafraîchir)
col_refresh1, col_refresh2 = st.columns([1, 4])
with col_refresh1:
    if st.button("🔄 Rafraîchir la base de données", help="Recharge les données depuis la base de données"):
        st.experimental_rerun()

# Récupérer artisans
artisans = get_artisans(filtres=filtres, limit=500)

st.markdown("---")

# Affichage des artisans
st.subheader(f"📋 Liste des Artisans ({len(artisans)} trouvés)")

if not artisans:
    st.info("Aucun artisan trouvé avec ces filtres")
else:
    # Mode d'affichage
    mode_affichage = st.radio(
        "Mode d'affichage",
        ["📋 Liste compacte", "📄 Vue détaillée"],
        horizontal=True
    )
    
    link_gen = WhatsAppLinkGenerator()
    
    if mode_affichage == "📋 Liste compacte":
        # Tableau compact avec TOUTES les informations scrapées
        data = []
        for artisan in artisans:
            lien_whatsapp = link_gen.generer_lien(artisan, template)
            row = {
                'ID': artisan.get('id'),
                'Entreprise': artisan.get('nom_entreprise', 'N/A'),
                'Métier': artisan.get('type_artisan', ''),
                'Ville': artisan.get('ville', ''),
                'Ville recherche': artisan.get('ville_recherche', ''),
                'Département': artisan.get('departement', ''),
                'Adresse': artisan.get('adresse', ''),
                'Code postal': artisan.get('code_postal', ''),
                'Téléphone': artisan.get('telephone', ''),
                'Site web': artisan.get('site_web', ''),
                'Note': f"{artisan.get('note', 'N/A')}/5" if artisan.get('note') else 'N/A',
                'Nombre avis': artisan.get('nombre_avis', 'N/A') if artisan.get('nombre_avis') else 'N/A',
                'Message envoyé': '✅' if artisan.get('message_envoye') else '❌',
                'A répondu': '✅' if artisan.get('a_repondu') else '❌',
                'Lien WhatsApp': lien_whatsapp
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # ✅ CSS pour améliorer l'affichage du tableau
        st.markdown("""
        <style>
        div[data-testid="stDataFrame"] {
            width: 100% !important;
        }
        div[data-testid="stDataFrame"] table {
            width: 100% !important;
        }
        div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True, height=600)
        
    else:
        # Vue détaillée avec cartes
        for i, artisan in enumerate(artisans):
            with st.container():
                col_a1, col_a2, col_a3 = st.columns([3, 2, 1])
                
                with col_a1:
                    st.markdown(f"### {i+1}. {artisan.get('nom_entreprise', 'N/A')}")
                    st.caption(f"**Métier :** {artisan.get('type_artisan', '')} | **Ville :** {artisan.get('ville', '')} ({artisan.get('departement', '')})")
                    if artisan.get('ville_recherche'):
                        st.caption(f"**Ville recherche :** {artisan.get('ville_recherche', '')}")
                    st.caption(f"**Téléphone :** {artisan.get('telephone', '')}")
                    if artisan.get('site_web'):
                        st.caption(f"**Site web :** [{artisan.get('site_web', '')}]({artisan.get('site_web', '')})")
                    if artisan.get('note'):
                        st.caption(f"**Note :** ⭐ {artisan.get('note', '')}/5 ({artisan.get('nombre_avis', 0)} avis)")
                    if artisan.get('adresse'):
                        st.caption(f"**Adresse :** {artisan.get('adresse', '')}")
                    
                    # Statuts
                    if artisan.get('message_envoye'):
                        st.success("✅ Message envoyé")
                        if artisan.get('date_envoi'):
                            try:
                                dt = datetime.fromisoformat(artisan['date_envoi'].replace('Z', '+00:00'))
                                st.caption(f"Le {dt.strftime('%d/%m/%Y à %H:%M')}")
                            except:
                                pass
                    else:
                        st.warning("❌ Non contacté")
                    
                    if artisan.get('a_repondu'):
                        st.info("💬 A répondu")
                        if artisan.get('date_reponse'):
                            try:
                                dt = datetime.fromisoformat(artisan['date_reponse'].replace('Z', '+00:00'))
                                st.caption(f"Le {dt.strftime('%d/%m/%Y à %H:%M')}")
                            except:
                                pass
                    else:
                        st.caption("Pas de réponse")
                
                with col_a2:
                    # Lien WhatsApp
                    lien_whatsapp = link_gen.generer_lien(artisan, template)
                    message_preview = link_gen.generer_message(artisan, template)
                    
                    with st.expander("📝 Voir le message", expanded=False):
                        st.code(message_preview)
                    
                    st.link_button(
                        "💬 Ouvrir WhatsApp",
                        lien_whatsapp
                    )
                
                with col_a3:
                    # Actions
                    if not artisan.get('message_envoye'):
                        if st.button("✓ Marquer envoyé", key=f"envoye_{artisan['id']}"):
                            marquer_message_envoye(artisan['id'], f"manual_{int(datetime.now().timestamp())}")
                            st.success("✅ Marqué comme envoyé !")
                            st.experimental_rerun()
                    else:
                        st.success("✅ Déjà envoyé")
                    
                    if st.button("📝 Voir détails", key=f"details_{artisan['id']}"):
                        st.session_state[f'show_details_{artisan["id"]}'] = True
                
                # Détails (si demandé)
                if st.session_state.get(f'show_details_{artisan["id"]}', False):
                    with st.expander("🔍 Détails complets", expanded=True):
                        st.json(artisan)
                        if st.button("Fermer", key=f"close_{artisan['id']}"):
                            st.session_state[f'show_details_{artisan["id"]}'] = False
                            st.experimental_rerun()
                
                st.markdown("---")
    
    # Actions rapides
    st.markdown("---")
    st.subheader("⚡ Actions Rapides")
    
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("📥 Exporter en CSV"):
            df_export = pd.DataFrame(artisans)
            csv = df_export.to_csv(index=False)
            st.download_button(
                "Télécharger CSV",
                csv,
                f"artisans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col_act2:
        if st.button("📋 Copier tous les numéros"):
            numeros = [a.get('telephone', '') for a in artisans if a.get('telephone')]
            st.code("\n".join(numeros))
    
    with col_act3:
        if st.button("🔄 Rafraîchir"):
            st.experimental_rerun()

