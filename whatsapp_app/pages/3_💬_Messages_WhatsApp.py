"""
Page Messages WhatsApp - Génération et gestion de messages personnalisés
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Messages WhatsApp", page_icon="💬", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, marquer_message_envoye
from whatsapp.message_builder import prepare_batch, detect_site_type
from whatsapp.phone_utils import is_mobile, is_landline, format_display

st.title("💬 Messages WhatsApp")

# Initialiser session state
if 'prepared_messages' not in st.session_state:
    st.session_state.prepared_messages = []
if 'messages_sent_count' not in st.session_state:
    st.session_state.messages_sent_count = 0

# Récupérer tous les artisans pour les filtres
all_artisans = get_artisans(limit=10000)

# Statistiques globales
total_artisans = len(all_artisans)
artisans_with_whatsapp = sum(1 for a in all_artisans if is_mobile(a.get('telephone', '')))
artisans_contacted = sum(1 for a in all_artisans if a.get('message_envoye'))

# Header avec statistiques
col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.metric("Total artisans", f"{total_artisans:,}")
with col_stat2:
    st.metric("Avec WhatsApp", f"{artisans_with_whatsapp:,}")
with col_stat3:
    st.metric("Déjà contactés", f"{artisans_contacted:,}")

st.markdown("---")

# Sidebar : Filtres
with st.sidebar:
    st.header("🔍 Filtres")
    
    # Type de contact
    contact_type = st.radio(
        "Type de contact",
        ["Tous", "WhatsApp uniquement (06/07)", "Cold Call uniquement (01-05)"],
        key="filter_contact_type"
    )
    
    # Type de site web
    site_types = st.multiselect(
        "Type de site web",
        ["Pas de site", "Facebook", "Instagram", "Site web classique"],
        key="filter_site_type"
    )
    
    # Métier
    metiers = sorted(list(set([a.get('type_artisan') for a in all_artisans if a.get('type_artisan')])))
    metiers_selected = st.multiselect(
        "Métier",
        metiers,
        key="filter_metier"
    )
    
    # Département
    depts = sorted(list(set([a.get('departement') for a in all_artisans if a.get('departement')])))
    depts_selected = st.multiselect(
        "Département",
        depts,
        key="filter_dept"
    )
    
    # Note Google
    note_filter = st.selectbox(
        "Note Google",
        ["Toutes", "4.5+", "4.0+", "3.5+", "< 3.5"],
        key="filter_note"
    )
    
    # Nombre d'avis
    avis_filter = st.selectbox(
        "Nombre d'avis",
        ["Tous", "50+ avis", "20-50 avis", "10-20 avis", "< 10 avis"],
        key="filter_avis"
    )
    
    # Statut message
    statut_filter = st.radio(
        "Statut message",
        ["Tous", "Non contactés uniquement", "Déjà contactés"],
        key="filter_statut"
    )

# Appliquer les filtres
filtered_artisans = all_artisans.copy()

# Filtre type de contact
if contact_type == "WhatsApp uniquement (06/07)":
    filtered_artisans = [a for a in filtered_artisans if is_mobile(a.get('telephone', ''))]
elif contact_type == "Cold Call uniquement (01-05)":
    filtered_artisans = [a for a in filtered_artisans if is_landline(a.get('telephone', ''))]

    # Filtre type de site
    if site_types:
        def match_site_type(artisan_site, selected_types):
            """Vérifie si le type de site correspond aux sélections"""
            site_type = detect_site_type(artisan_site)
            for stype in selected_types:
                if stype == "Pas de site" and site_type == "none":
                    return True
                elif stype == "Facebook" and site_type == "facebook":
                    return True
                elif stype == "Instagram" and site_type == "instagram":
                    return True
                elif stype == "Site web classique" and site_type == "website":
                    return True
            return False
        
        filtered_artisans = [a for a in filtered_artisans if match_site_type(a.get('site_web'), site_types)]

# Filtre métier
if metiers_selected:
    filtered_artisans = [a for a in filtered_artisans if a.get('type_artisan') in metiers_selected]

# Filtre département
if depts_selected:
    filtered_artisans = [a for a in filtered_artisans if a.get('departement') in depts_selected]

# Filtre note
if note_filter != "Toutes":
    if note_filter == "4.5+":
        filtered_artisans = [a for a in filtered_artisans if a.get('note') and float(a.get('note', 0)) >= 4.5]
    elif note_filter == "4.0+":
        filtered_artisans = [a for a in filtered_artisans if a.get('note') and float(a.get('note', 0)) >= 4.0]
    elif note_filter == "3.5+":
        filtered_artisans = [a for a in filtered_artisans if a.get('note') and float(a.get('note', 0)) >= 3.5]
    elif note_filter == "< 3.5":
        filtered_artisans = [a for a in filtered_artisans if a.get('note') and float(a.get('note', 0)) < 3.5]

# Filtre nombre d'avis
if avis_filter != "Tous":
    if avis_filter == "50+ avis":
        filtered_artisans = [a for a in filtered_artisans if a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 50]
    elif avis_filter == "20-50 avis":
        filtered_artisans = [a for a in filtered_artisans if a.get('nombre_avis') and 20 <= int(a.get('nombre_avis', 0)) < 50]
    elif avis_filter == "10-20 avis":
        filtered_artisans = [a for a in filtered_artisans if a.get('nombre_avis') and 10 <= int(a.get('nombre_avis', 0)) < 20]
    elif avis_filter == "< 10 avis":
        filtered_artisans = [a for a in filtered_artisans if a.get('nombre_avis') and int(a.get('nombre_avis', 0)) < 10]

# Filtre statut
if statut_filter == "Non contactés uniquement":
    filtered_artisans = [a for a in filtered_artisans if not a.get('message_envoye')]
elif statut_filter == "Déjà contactés":
    filtered_artisans = [a for a in filtered_artisans if a.get('message_envoye')]

# Zone principale
st.subheader(f"📋 {len(filtered_artisans)} artisan(s) correspondent aux filtres")

# Bouton pour préparer les messages
if st.button("🚀 Préparer les messages"):
    with st.spinner("Génération des messages en cours..."):
        st.session_state.prepared_messages = prepare_batch(filtered_artisans)
        st.success(f"✅ {len(st.session_state.prepared_messages)} message(s) préparé(s) !")
        st.experimental_rerun()

# Afficher les messages préparés
if st.session_state.prepared_messages:
    st.markdown("---")
    st.subheader("📨 Messages préparés")
    
    # Compteur de messages envoyés cette session
    st.info(f"📊 {st.session_state.messages_sent_count} message(s) marqué(s) comme envoyé(s) cette session")
    
    # Pagination
    items_per_page = 20
    total_pages = (len(st.session_state.prepared_messages) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1), key="pagination")
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        messages_to_show = st.session_state.prepared_messages[start_idx:end_idx]
    else:
        messages_to_show = st.session_state.prepared_messages
    
    # Afficher chaque artisan
    for idx, prepared in enumerate(messages_to_show):
        with st.expander(
            f"**{prepared['nom_entreprise']}** - {prepared['telephone_display']}",
            expanded=False
        ):
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                # Badge catégorie
                if prepared['category'] == 'whatsapp':
                    st.markdown("🟢 **WhatsApp**")
                elif prepared['category'] == 'cold_call':
                    st.markdown("🟡 **Cold Call**")
                else:
                    st.markdown("🔴 **Invalide**")
                
                st.write(f"**Ville:** {prepared.get('ville', 'N/A')}")
                st.write(f"**Département:** {prepared.get('departement', 'N/A')}")
                
                # Note et avis
                note = prepared.get('note', '')
                avis = prepared.get('nombre_avis', '')
                if note or avis:
                    st.write(f"**Note:** {note}/5 ({avis} avis)" if note and avis else f"**Note:** {note}/5" if note else f"**Avis:** {avis}")
            
            with col_info2:
                # Type de site
                site_type = prepared['site_type']
                if site_type == 'facebook':
                    st.markdown("📘 **Facebook**")
                elif site_type == 'instagram':
                    st.markdown("📷 **Instagram**")
                elif site_type == 'website':
                    st.markdown("🌐 **Site web**")
                else:
                    st.markdown("❌ **Pas de site**")
                
                st.write(f"**Template:** {prepared['template_name']}")
                if prepared['prenom_detected']:
                    st.write(f"**Prénom détecté:** {prepared['prenom_detected']}")
            
            # Message
            st.markdown("---")
            st.markdown("**Message généré:**")
            # Message éditable
            edited_message = st.text_area(
                "Message (éditable)",
                value=prepared['message'],
                height=150,
                key=f"message_{prepared['artisan_id']}",
                help="Vous pouvez modifier le message. Utilisez Ctrl+A puis Ctrl+C pour copier."
            )
            
            # Actions
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                if prepared['wa_link']:
                    # Utiliser le message édité si modifié
                    message_to_send = edited_message if edited_message != prepared['message'] else prepared['message']
                    # Régénérer le lien avec le message édité
                    from whatsapp.phone_utils import generate_wa_link
                    wa_link_updated = generate_wa_link(prepared['telephone'], message_to_send)
                    if wa_link_updated:
                        st.markdown(f"[📲 Ouvrir WhatsApp]({wa_link_updated})")
                    else:
                        st.markdown(f"[📲 Ouvrir WhatsApp]({prepared['wa_link']})")
                else:
                    st.write("📲 WhatsApp non disponible (numéro fixe)")
            
            with col_act2:
                st.info("💡 Ctrl+A puis Ctrl+C pour copier le message")
            
            with col_act3:
                if st.button("✅ Marquer comme envoyé", key=f"sent_{prepared['artisan_id']}"):
                    try:
                        marquer_message_envoye(prepared['artisan_id'])
                        st.session_state.messages_sent_count += 1
                        st.success("✅ Marqué comme envoyé !")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

# Export CSV
if st.session_state.prepared_messages:
    st.markdown("---")
    if st.button("📥 Exporter en CSV"):
        # Préparer les données pour l'export
        export_data = []
        for prepared in st.session_state.prepared_messages:
            export_data.append({
                'ID': prepared['artisan_id'],
                'Entreprise': prepared['nom_entreprise'],
                'Téléphone': prepared['telephone_display'],
                'Catégorie': prepared['category'],
                'Ville': prepared.get('ville', ''),
                'Département': prepared.get('departement', ''),
                'Template': prepared['template_name'],
                'Message': prepared['message'],
                'Lien WhatsApp': prepared['wa_link'] or ''
            })
        
        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            "Télécharger CSV",
            csv,
            f"messages_whatsapp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )

