"""
Page Base de Données - Accès à la base et génération liens WhatsApp
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
import requests

# Configuration de la page
st.set_page_config(page_title="Base de Données", page_icon="📊", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, get_statistiques, marquer_message_envoye, ajouter_artisan
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
    if st.button("🔄 Rafraîchir la base de données", help="Recharge les données depuis la base de données", key="refresh_db_main"):
        # Forcer le rerun pour recharger les données
        st.success("🔄 Rechargement des données...")
        st.experimental_rerun()

# ✅ Bouton pour importer les résultats depuis GitHub Actions
col_import1, col_import2 = st.columns([1, 4])
with col_import1:
    if st.button("📥 Importer depuis GitHub Actions", key="import_from_github", help="Télécharger et importer les résultats depuis GitHub Actions dans la base locale"):
        try:
            # Vérifier si on a la config GitHub
            config_file = Path(__file__).parent.parent.parent / "config" / "github_config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    github_config = json.load(f)
                    # ✅ Support des deux formats : 'token'/'repo' ou 'github_token'/'github_repo'
                    github_token = github_config.get('token') or github_config.get('github_token')
                    github_repo = github_config.get('repo') or github_config.get('github_repo')
                    
                    if github_token and github_repo:
                        # Fonction pour télécharger les artifacts depuis GitHub Actions (copiée depuis 1_🔍_Scraping.py)
                        def download_github_artifact(token, repo, run_id):
                            """Télécharge l'artifact depuis GitHub Actions"""
                            try:
                                # Récupérer la liste des artifacts
                                url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts"
                                headers = {
                                    "Accept": "application/vnd.github+json",
                                    "Authorization": f"Bearer {token}",
                                    "X-GitHub-Api-Version": "2022-11-28"
                                }
                                response = requests.get(url, headers=headers)
                                if response.status_code == 200:
                                    artifacts = response.json().get('artifacts', [])
                                    for artifact in artifacts:
                                        if artifact.get('name') == 'scraping-results':
                                            # Télécharger l'artifact
                                            download_url = artifact.get('archive_download_url')
                                            if download_url:
                                                download_response = requests.get(download_url, headers=headers)
                                                if download_response.status_code == 200:
                                                    # Sauvegarder le zip
                                                    import zipfile
                                                    data_dir = Path(__file__).parent.parent.parent / "data"
                                                    zip_path = data_dir / "github_artifact.zip"
                                                    with open(zip_path, 'wb') as f:
                                                        f.write(download_response.content)
                                                    
                                                    # Extraire le JSON
                                                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                                        zip_ref.extractall(data_dir)
                                                    
                                                    # Lire les fichiers
                                                    results_file = data_dir / "scraping_results_github_actions.json"
                                                    
                                                    result_data = None
                                                    if results_file.exists():
                                                        with open(results_file, 'r', encoding='utf-8') as f:
                                                            result_data = json.load(f)
                                                    
                                                    # Nettoyer
                                                    zip_path.unlink()
                                                    
                                                    # Retourner dans le format attendu
                                                    if result_data and isinstance(result_data, dict) and 'results' in result_data:
                                                        return result_data
                                                    elif result_data and isinstance(result_data, list):
                                                        return {'results': result_data, 'total_results': len(result_data)}
                                                    else:
                                                        return {'results': [], 'total_results': 0}
                                    return None
                                return None
                            except Exception as e:
                                logger.error(f"Erreur téléchargement artifact: {e}")
                                return None
                        
                        # Récupérer les workflows terminés
                        headers = {
                            "Accept": "application/vnd.github+json",
                            "Authorization": f"Bearer {github_token}",
                            "X-GitHub-Api-Version": "2022-11-28"
                        }
                        all_workflows_url = f"https://api.github.com/repos/{github_repo}/actions/runs?per_page=5&status=completed"
                        response = requests.get(all_workflows_url, headers=headers)
                        imported_count = 0
                        
                        if response.status_code == 200:
                            runs = response.json().get('workflow_runs', [])
                            for run in runs:
                                run_id = run.get('id')
                                if run_id:
                                    artifact_data = download_github_artifact(github_token, github_repo, run_id)
                                    if artifact_data:
                                        results_list = artifact_data.get('results', [])
                                        if isinstance(results_list, list) and len(results_list) > 0:
                                            for info in results_list:
                                                try:
                                                    artisan_data = {
                                                        'nom_entreprise': info.get('nom', 'N/A'),
                                                        'telephone': info.get('telephone', '').replace(' ', '') if info.get('telephone') else None,
                                                        'site_web': info.get('site_web'),
                                                        'adresse': info.get('adresse', ''),
                                                        'code_postal': info.get('code_postal', ''),
                                                        'ville': info.get('ville', ''),
                                                        'ville_recherche': info.get('ville_recherche', ''),
                                                        'type_artisan': info.get('recherche', 'plombier'),
                                                        'source': 'google_maps_github_actions',
                                                        'note': info.get('note'),
                                                        'nombre_avis': info.get('nb_avis') or info.get('nombre_avis')
                                                    }
                                                    ajouter_artisan(artisan_data)
                                                    imported_count += 1
                                                except Exception as e:
                                                    if "UNIQUE constraint" not in str(e) and "duplicate" not in str(e).lower():
                                                        st.error(f"Erreur import: {e}")
                            if imported_count > 0:
                                st.success(f"✅ {imported_count} résultat(s) importé(s) !")
                                st.experimental_rerun()
                            else:
                                st.info("ℹ️ Aucun nouveau résultat à importer")
                        else:
                            st.warning("⚠️ Impossible de récupérer les workflows")
                    else:
                        st.warning("⚠️ Configuration GitHub manquante")
            else:
                st.warning("⚠️ Fichier de configuration GitHub non trouvé")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'import: {e}")
            import traceback
            st.code(traceback.format_exc())

# Récupérer artisans (toujours recharger depuis la BDD)
# ✅ Toujours recharger depuis la BDD pour avoir les dernières données
artisans = get_artisans(filtres=filtres, limit=500)

# ✅ Afficher un message si des données sont trouvées
if artisans:
    st.info(f"✅ {len(artisans)} artisan(s) trouvé(s) dans la base de données")
else:
    st.warning("⚠️ Aucun artisan dans la base de données. Les résultats de GitHub Actions doivent être importés manuellement.")

st.markdown("---")

# Affichage des artisans
st.subheader(f"📋 Liste des Artisans ({len(artisans)} trouvés)")

if not artisans:
    st.info("Aucun artisan trouvé avec ces filtres")
else:
    link_gen = WhatsAppLinkGenerator()
    
    # ✅ Suppression de la vue détaillée - on garde seulement la liste compacte
    if True:  # Toujours afficher la liste compacte
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
        
        st.dataframe(df, height=600)
    
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

