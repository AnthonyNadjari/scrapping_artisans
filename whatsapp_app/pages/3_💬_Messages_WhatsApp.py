"""
Page Messages SMS - Génération et gestion de messages personnalisés
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Messages SMS", page_icon="💬", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, marquer_message_envoye
from whatsapp_database.models import init_database

# ✅ Initialiser la base de données au démarrage (ajoute les nouvelles colonnes si nécessaire)
try:
    init_database()
except Exception as e:
    # Ne pas bloquer si erreur, mais logger
    import logging
    logging.warning(f"Erreur initialisation BDD: {e}")
from whatsapp.message_builder import prepare_batch, detect_site_type
from whatsapp.phone_utils import is_mobile, is_landline, format_display
# Utiliser sms_free_providers pour services gratuits (Twilio Trial, TextBelt, etc.)
# ou sms_providers pour services payants (OVH, Twilio payant, etc.)
# ou sms_sender pour Free Mobile (notifications uniquement - ne fonctionne pas pour d'autres numéros)
try:
    from whatsapp.sms_free_providers import send_sms
except ImportError:
    try:
        from whatsapp.sms_providers import send_sms
    except ImportError:
        # Fallback sur Free Mobile si autres modules ne sont pas disponibles
        from whatsapp.sms_sender import send_sms

st.title("💬 Messages SMS")

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
    st.metric("Avec SMS", f"{artisans_with_whatsapp:,}")
with col_stat3:
    st.metric("Déjà contactés", f"{artisans_contacted:,}")

st.markdown("---")

# Sidebar : Filtres
with st.sidebar:
    st.header("🔍 Filtres")
    
    # Type de contact
    contact_type = st.radio(
        "Type de contact",
        ["Tous", "SMS uniquement (06/07)", "Cold Call uniquement (01-05)"],
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
    
    # Note Google (multiselect avec tags)
    note_options = ["4.5+", "4.0+", "3.5+", "< 3.5", "Sans note (NA)"]
    note_filters = st.multiselect(
        "Note Google",
        note_options,
        key="filter_note"
    )
    
    # Nombre d'avis (multiselect avec tags)
    avis_options = ["50+ avis", "20-50 avis", "10-20 avis", "< 10 avis", "Sans avis (NA)"]
    avis_filters = st.multiselect(
        "Nombre d'avis",
        avis_options,
        key="filter_avis"
    )

# Appliquer les filtres
filtered_artisans = all_artisans.copy()

# Filtre type de contact
if contact_type == "SMS uniquement (06/07)":
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

# Filtre note (multiselect - peut sélectionner plusieurs critères)
if note_filters:
    def match_note(artisan_note):
        """Vérifie si la note correspond à au moins un des filtres sélectionnés"""
        if not artisan_note or artisan_note == '':
            return "Sans note (NA)" in note_filters
        
        try:
            note_val = float(artisan_note)
            for note_filter in note_filters:
                if note_filter == "4.5+" and note_val >= 4.5:
                    return True
                elif note_filter == "4.0+" and note_val >= 4.0:
                    return True
                elif note_filter == "3.5+" and note_val >= 3.5:
                    return True
                elif note_filter == "< 3.5" and note_val < 3.5:
                    return True
            return False
        except:
            return "Sans note (NA)" in note_filters
    
    filtered_artisans = [a for a in filtered_artisans if match_note(a.get('note'))]

# Filtre nombre d'avis (multiselect - peut sélectionner plusieurs critères)
if avis_filters:
    def match_avis(artisan_avis):
        """Vérifie si le nombre d'avis correspond à au moins un des filtres sélectionnés"""
        if not artisan_avis or artisan_avis == '':
            return "Sans avis (NA)" in avis_filters
        
        try:
            avis_val = int(artisan_avis)
            for avis_filter in avis_filters:
                if avis_filter == "50+ avis" and avis_val >= 50:
                    return True
                elif avis_filter == "20-50 avis" and 20 <= avis_val < 50:
                    return True
                elif avis_filter == "10-20 avis" and 10 <= avis_val < 20:
                    return True
                elif avis_filter == "< 10 avis" and avis_val < 10:
                    return True
            return False
        except:
            return "Sans avis (NA)" in avis_filters
    
    filtered_artisans = [a for a in filtered_artisans if match_avis(a.get('nombre_avis'))]

# Zone principale
st.subheader(f"📋 {len(filtered_artisans)} artisan(s) correspondent aux filtres")

# Afficher un tableau avec les artisans filtrés (mise à jour directe selon les filtres)
if filtered_artisans:
    # Préparer les données pour le tableau
    table_data = []
    for artisan in filtered_artisans:
        # Extraire le département depuis code_postal si manquant
        departement = artisan.get('departement', '')
        if not departement and artisan.get('code_postal'):
            code_postal = str(artisan.get('code_postal', '')).strip()
            if len(code_postal) >= 2:
                if code_postal.startswith('97') or code_postal.startswith('98'):
                    departement = code_postal[:3]
                else:
                    departement = code_postal[:2]
        
        # Détecter le type de site
        site_type = detect_site_type(artisan.get('site_web'))
        site_display = {
            'facebook': '📘 Facebook',
            'instagram': '📷 Instagram',
            'website': '🌐 Site web',
            'none': '❌ Pas de site'
        }.get(site_type, '❌ Pas de site')
        
        # Catégorie téléphone
        tel = artisan.get('telephone', '')
        if is_mobile(tel):
            category = "🟢 SMS"
        elif is_landline(tel):
            category = "🟡 Cold Call"
        else:
            category = "🔴 Invalide"
        
        # Gérer les valeurs numériques correctement
        nombre_avis = artisan.get('nombre_avis')
        if nombre_avis is not None and nombre_avis != '':
            try:
                avis_display = int(nombre_avis)
            except:
                avis_display = 'N/A'
        else:
            avis_display = 'N/A'
        
        table_data.append({
            'ID': artisan.get('id', ''),
            'Entreprise': artisan.get('nom_entreprise', ''),
            'Téléphone': format_display(tel),
            'Catégorie': category,
            'Ville': artisan.get('ville', '') or artisan.get('ville_recherche', ''),
            'Département': departement or 'N/A',
            'Code postal': artisan.get('code_postal', '') or 'N/A',
            'Métier': artisan.get('type_artisan', '') or 'N/A',
            'Note': f"{artisan.get('note', '')}/5" if artisan.get('note') else 'N/A',
            'Avis': avis_display,
            'Site': site_display,
            'Contacté': '✅' if artisan.get('message_envoye') else '❌'
        })
    
    df_table = pd.DataFrame(table_data)
    # Convertir la colonne Avis en string pour éviter les problèmes de conversion
    df_table['Avis'] = df_table['Avis'].astype(str)
    st.dataframe(df_table, height=400)
    
    st.markdown("---")
    
    # Bouton pour préparer les messages (après avoir vu la liste filtrée)
    if st.button("🚀 Préparer les messages pour ces artisans"):
        with st.spinner("Génération des messages en cours..."):
            st.session_state.prepared_messages = prepare_batch(filtered_artisans)
            st.success(f"✅ {len(st.session_state.prepared_messages)} message(s) préparé(s) !")
            st.experimental_rerun()
else:
    st.info("Aucun artisan ne correspond aux filtres sélectionnés.")

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
    
    # Afficher chaque artisan dans un format simple (sans expanders)
    for idx, prepared in enumerate(messages_to_show):
        # Divider entre chaque artisan
        if idx > 0:
            st.markdown("---")
        
        # Header avec nom et téléphone
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"### {prepared['nom_entreprise']}")
        with col_header2:
            # Badge catégorie
            if prepared['category'] == 'whatsapp':
                st.markdown("🟢 **SMS**")
            elif prepared['category'] == 'cold_call':
                st.markdown("🟡 **Cold Call**")
            else:
                st.markdown("🔴 **Invalide**")
        
        # Informations en 3 colonnes
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.write(f"**Téléphone:** {prepared['telephone_display']}")
            st.write(f"**Ville:** {prepared.get('ville', 'N/A')}")
            
            # Récupérer les données complètes depuis la DB si manquantes
            from whatsapp_database.queries import get_artisans
            artisans_db = get_artisans(filtres={'id': prepared['artisan_id']}, limit=1)
            artisan_db = artisans_db[0] if artisans_db else {}
            
            # Extraire le département depuis code_postal si manquant
            departement_display = prepared.get('departement', '') or artisan_db.get('departement', '')
            code_postal_display = prepared.get('code_postal', '') or artisan_db.get('code_postal', '')
            
            if not departement_display and code_postal_display:
                code_postal_str = str(code_postal_display).strip()
                if len(code_postal_str) >= 2:
                    if code_postal_str.startswith('97') or code_postal_str.startswith('98'):
                        departement_display = code_postal_str[:3]
                    else:
                        departement_display = code_postal_str[:2]
            
            st.write(f"**Département:** {departement_display or 'N/A'}")
            st.write(f"**Code postal:** {code_postal_display or 'N/A'}")
        
        with col_info2:
            # Note et avis
            note = prepared.get('note', '')
            avis = prepared.get('nombre_avis', '')
            if note or avis:
                st.write(f"**Note:** {note}/5 ({avis} avis)" if note and avis else f"**Note:** {note}/5" if note else f"**Avis:** {avis}")
            
            # Type de site
            site_type = prepared['site_type']
            if site_type == 'facebook':
                st.write("📘 **Facebook**")
            elif site_type == 'instagram':
                st.write("📷 **Instagram**")
            elif site_type == 'website':
                st.write("🌐 **Site web**")
            else:
                st.write("❌ **Pas de site**")
        
        with col_info3:
            st.write(f"**Template:** {prepared['template_name']}")
            if prepared['prenom_detected']:
                st.write(f"**Prénom:** {prepared['prenom_detected']}")
            # Récupérer le métier depuis la DB si manquant
            metier_display = prepared.get('type_artisan', '')
            if not metier_display:
                from whatsapp_database.queries import get_artisans
                artisans_db = get_artisans(filtres={'id': prepared['artisan_id']}, limit=1)
                if artisans_db:
                    metier_display = artisans_db[0].get('type_artisan', '')
            st.write(f"**Métier:** {metier_display or 'N/A'}")
        
        # Message éditable
        st.markdown("**Message généré:**")
        edited_message = st.text_area(
            "Message (éditable)",
            value=prepared['message'],
            height=120,
            key=f"message_{prepared['artisan_id']}",
            help="Vous pouvez modifier le message. Utilisez Ctrl+A puis Ctrl+C pour copier."
        )
        
        # Actions en ligne
        col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
        
        with col_act1:
            if prepared['sms_available']:
                # Utiliser le message édité si modifié
                message_to_send = edited_message if edited_message != prepared['message'] else prepared['message']
                
                # Bouton pour envoyer le SMS
                if st.button("📱 Envoyer SMS", key=f"sms_{prepared['artisan_id']}", type="primary"):
                    with st.spinner("Envoi du SMS en cours..."):
                        result = send_sms(prepared['telephone'], message_to_send)
                        
                        if result['success']:
                            # Marquer comme envoyé dans la base de données
                            try:
                                marquer_message_envoye(prepared['artisan_id'], f"sms_{prepared['artisan_id']}")
                                st.session_state.messages_sent_count += 1
                                st.success("✅ SMS envoyé avec succès !")
                                st.experimental_rerun()
                            except Exception as e:
                                st.warning(f"SMS envoyé mais erreur lors de la sauvegarde: {e}")
                        else:
                            st.error(f"❌ Erreur: {result['message']}")
            else:
                st.info("📞 SMS non disponible (numéro fixe)")
        
        with col_act2:
            st.info("💡 Ctrl+A puis Ctrl+C")
        
        with col_act3:
            if st.button("✅ Marquer envoyé", key=f"sent_{prepared['artisan_id']}"):
                try:
                    marquer_message_envoye(prepared['artisan_id'], f"manual_{prepared['artisan_id']}")
                    st.session_state.messages_sent_count += 1
                    st.success("✅ Marqué comme envoyé !")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erreur: {e}")

# Export XLSX avec toutes les colonnes de la DB + message
if st.session_state.prepared_messages:
    st.markdown("---")
    if st.button("📥 Exporter en XLSX"):
        # Récupérer les données complètes depuis la DB pour chaque artisan
        from whatsapp_database.queries import get_artisans
        
        # Préparer les données pour l'export avec TOUTES les colonnes de la DB
        export_data = []
        for prepared in st.session_state.prepared_messages:
            # Récupérer l'artisan complet depuis la DB par ID
            artisans_db = get_artisans(filtres={'id': prepared['artisan_id']}, limit=1)
            artisan_db = artisans_db[0] if artisans_db else {}
            
            # Extraire le département depuis code_postal si manquant
            departement = prepared.get('departement', '') or artisan_db.get('departement', '')
            if not departement and artisan_db.get('code_postal'):
                code_postal = str(artisan_db.get('code_postal', '')).strip()
                if len(code_postal) >= 2:
                    if code_postal.startswith('97') or code_postal.startswith('98'):
                        departement = code_postal[:3]
                    else:
                        departement = code_postal[:2]
            
            export_data.append({
                'ID': artisan_db.get('id', ''),
                'Nom entreprise': artisan_db.get('nom_entreprise', ''),
                'Nom': artisan_db.get('nom', ''),
                'Prénom': artisan_db.get('prenom', ''),
                'Métier': artisan_db.get('type_artisan', ''),
                'Téléphone': artisan_db.get('telephone', ''),
                'Téléphone formaté': prepared['telephone_display'],
                'Site web': artisan_db.get('site_web', ''),
                'Adresse': artisan_db.get('adresse', ''),
                'Code postal': artisan_db.get('code_postal', ''),
                'Ville': artisan_db.get('ville', '') or artisan_db.get('ville_recherche', ''),
                'Ville recherche': artisan_db.get('ville_recherche', ''),
                'Département': departement,
                'Note': artisan_db.get('note', ''),
                'Nombre avis': artisan_db.get('nombre_avis', ''),
                'Source': artisan_db.get('source', ''),
                'Date création': artisan_db.get('created_at', ''),
                'Message généré': prepared['message'],
                'Template utilisé': prepared['template_name'],
                'SMS disponible': 'Oui' if prepared.get('sms_available', False) else 'Non'
            })
        
        df_export = pd.DataFrame(export_data)
        
        # Créer un fichier Excel en mémoire
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Messages SMS')
        output.seek(0)
        
        st.download_button(
            "📥 Télécharger XLSX",
            output.getvalue(),
            f"messages_sms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

