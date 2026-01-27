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
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Base de Données", page_icon="📊", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans, get_statistiques, ajouter_artisan, importer_artisans_batch
from whatsapp_database.models import get_connection, init_database
from whatsapp.message_builder import detect_site_type
from whatsapp.phone_utils import is_mobile, is_landline
import sqlite3

# ✅ Ensure database and tables exist (ajoute les nouvelles colonnes si nécessaire)
try:
    init_database()
except Exception as e:
    # Ne pas bloquer si erreur, mais logger
    import logging
    logging.warning(f"Erreur initialisation BDD: {e}")
import re

st.title("📊 Base de Données - Artisans")

# Récupérer tous les artisans pour les stats globales (avant filtres)
all_artisans_stats = get_artisans(limit=10000)
stats = get_statistiques()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total artisans", f"{stats.get('total', 0):,}")
with col2:
    st.metric("Avec téléphone", f"{stats.get('avec_telephone', 0):,}")
with col3:
    st.metric("Sans site web", f"{stats.get('sans_site_web', 0):,}")

st.markdown("---")

# ✅ SECTION : Carte de scraping par métier (basée sur la BDD locale)
st.markdown("### 🗺️ Carte des scrapings par métier")
st.caption("Visualisez les départements scrapés pour chaque métier. La taille des points est proportionnelle au nombre d'artisans.")

# Récupérer la liste des métiers depuis la BDD
all_artisans_bdd = get_artisans(limit=10000)
metiers_bdd = sorted(list(set([a.get('type_artisan') for a in all_artisans_bdd if a.get('type_artisan')])))

col_map1, col_map2 = st.columns([1, 3])
with col_map1:
    if metiers_bdd:
        metier_carte = st.selectbox("Sélectionner un métier", ["Tous"] + metiers_bdd, key="map_metier_selection_bdd")
    else:
        metier_carte = "Tous"
        st.info("ℹ️ Aucun métier dans la BDD")

# Importer et utiliser la fonction de carte
try:
    from whatsapp_app.utils.map_utils import create_scraping_map_by_job
    from streamlit_folium import st_folium
    
    with st.spinner("🔄 Génération de la carte..."):
        carte = create_scraping_map_by_job(metier_carte if metier_carte != "Tous" else None)
    
    # Vérifier si des artisans existent pour ce métier
    artisans_filtres = [a for a in all_artisans_bdd if not metier_carte or metier_carte == "Tous" or a.get('type_artisan') == metier_carte]
    
    if carte:
        with col_map2:
            st_folium(carte, width=None, height=500, returned_objects=[])
        
        if not artisans_filtres:
            with col_map2:
                st.warning("⚠️ Aucun artisan trouvé pour ce métier dans la base de données")
    else:
        with col_map2:
            if artisans_filtres:
                st.warning(f"⚠️ {len(artisans_filtres)} artisan(s) trouvé(s) mais aucun département détecté. Vérifiez que les artisans ont un code postal ou un département rempli.")
            else:
                st.info("ℹ️ Aucune donnée de scraping pour ce métier. Lancez un scraping pour voir la carte se remplir.")
except ImportError as e:
    st.warning(f"⚠️ Erreur import map_utils: {e}")
    st.info("💡 Installez les dépendances: `pip install folium streamlit-folium`")
except Exception as e:
    st.error(f"❌ Erreur création carte: {e}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

# Sidebar : Filtres (même système que Messages WhatsApp)
with st.sidebar:
    st.header("🔍 Filtres")
    
    # Récupérer tous les artisans pour les filtres
    all_artisans_for_filters = get_artisans(limit=10000)
    
    # Type de contact
    contact_type = st.radio(
        "Type de contact",
        ["Tous", "SMS uniquement (06/07)", "Cold Call uniquement (01-05)"],
        key="filter_contact_type_bdd"
    )
    
    # Type de site web
    site_types = st.multiselect(
        "Type de site web",
        ["Pas de site", "Facebook", "Instagram", "Site web classique"],
        key="filter_site_type_bdd"
    )
    
    # Métier
    metiers = sorted(list(set([a.get('type_artisan') for a in all_artisans_for_filters if a.get('type_artisan')])))
    metiers_selected = st.multiselect(
        "Métier",
        metiers,
        key="filter_metier_bdd"
    )
    
    # Département
    depts = sorted(list(set([a.get('departement') for a in all_artisans_for_filters if a.get('departement')])))
    depts_selected = st.multiselect(
        "Département",
        depts,
        key="filter_dept_bdd"
    )
    
    # Note Google (multiselect avec tags)
    note_options = ["4.5+", "4.0+", "3.5+", "< 3.5", "Sans note (NA)"]
    note_filters = st.multiselect(
        "Note Google",
        note_options,
        key="filter_note_bdd"
    )
    
    # Nombre d'avis (multiselect avec tags)
    avis_options = ["50+ avis", "20-50 avis", "10-20 avis", "< 10 avis", "Sans avis (NA)"]
    avis_filters = st.multiselect(
        "Nombre d'avis",
        avis_options,
        key="filter_avis_bdd"
    )

# Récupérer tous les artisans pour appliquer les filtres
all_artisans = get_artisans(limit=10000)

# Appliquer les filtres (même logique que Messages WhatsApp)
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

# Utiliser les artisans filtrés au lieu de ceux récupérés avec filtres
artisans = filtered_artisans

# ✅ Bouton unique pour synchroniser avec GitHub (git pull + import JSON + import artifacts)
col_sync, col_empty = st.columns([1, 4])
with col_sync:
    if st.button("🔄 Sync GitHub", key="sync_github", help="Git pull + Import JSON + Import Artifacts en un seul clic"):
        import subprocess
        import zipfile

        status_text = st.empty()
        progress_bar = st.progress(0)
        total_imported = 0
        repo_root = Path(__file__).parent.parent.parent
        data_dir = repo_root / "data"

        # === ÉTAPE 1: Stash local changes then Git Pull ===
        status_text.text("📥 Git pull en cours...")
        progress_bar.progress(10)
        try:
            # Stash local changes to data files to avoid conflicts
            stash_result = subprocess.run(
                ['git', 'stash', 'push', '-m', 'auto-stash-before-sync', '--',
                 'data/scraping_results_github_actions.json',
                 'data/github_actions_status.json'],
                capture_output=True, text=True, cwd=str(repo_root)
            )
            did_stash = 'Saved working directory' in stash_result.stdout

            # Now pull from origin
            result = subprocess.run(['git', 'pull', 'origin', 'main'], capture_output=True, text=True, cwd=str(repo_root))
            if result.returncode == 0:
                pull_msg = result.stdout.strip() if result.stdout.strip() else 'Déjà à jour'
                st.success(f"✅ Git pull: {pull_msg}")
            else:
                st.warning(f"⚠️ Git pull: {result.stderr}")

            # Pop stash if we stashed (we'll merge data from artifacts anyway)
            if did_stash:
                subprocess.run(['git', 'stash', 'drop'], capture_output=True, text=True, cwd=str(repo_root))
        except Exception as e:
            st.warning(f"⚠️ Git pull échoué: {e}")

        # === Helper function to transform raw data to artisan format ===
        def transform_to_artisan(info: dict) -> dict:
            """Transform raw JSON record to artisan data format with proper department extraction"""
            code_postal = info.get('code_postal', '')
            dept = None

            # Priority 1: Extract from code_postal (most reliable)
            if code_postal and re.match(r'^\d{5}$', str(code_postal).strip()):
                cp = str(code_postal).strip()
                if cp.startswith('97') or cp.startswith('98'):
                    dept = cp[:3]
                else:
                    dept = cp[:2]

            # Fallback: Use departement_recherche only if no code_postal
            if not dept:
                dept = info.get('departement_recherche') or info.get('departement', '')

            return {
                'nom_entreprise': info.get('nom', 'N/A'),
                'telephone': info.get('telephone', '').replace(' ', '') if info.get('telephone') else None,
                'site_web': info.get('site_web'),
                'adresse': info.get('adresse', ''),
                'code_postal': code_postal,
                'ville': info.get('ville') or info.get('ville_recherche', ''),
                'ville_recherche': info.get('ville_recherche', ''),
                'departement': dept,
                'departement_recherche': info.get('departement_recherche', ''),
                'type_artisan': info.get('recherche') or info.get('type_artisan', 'artisan'),
                'google_maps_url': info.get('google_maps_url'),
                'source': 'google_maps_github_actions',
                'note': info.get('note'),
                'nombre_avis': info.get('nb_avis') or info.get('nombre_avis')
            }

        # === Collect all records to import ===
        all_records_to_import = []

        # === ÉTAPE 2: Load JSON local (après pull) ===
        status_text.text("📄 Chargement JSON local...")
        progress_bar.progress(30)
        results_file = data_dir / "scraping_results_github_actions.json"
        local_results_count = 0

        if results_file.exists():
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                results_list = []
                if isinstance(data, dict) and 'results' in data:
                    results_list = data.get('results', [])
                elif isinstance(data, list):
                    results_list = data

                if results_list:
                    for info in results_list:
                        try:
                            all_records_to_import.append(transform_to_artisan(info))
                        except Exception:
                            pass
                    local_results_count = len(results_list)
                    st.info(f"📄 JSON local: {local_results_count} résultats chargés")
            except Exception as e:
                st.warning(f"⚠️ Erreur lecture JSON: {e}")
        else:
            st.info("📄 Pas de fichier JSON local")

        # === ÉTAPE 3: Load Artifacts GitHub (skip downloading if JSON already has data) ===
        status_text.text("☁️ Vérification Artifacts GitHub...")
        progress_bar.progress(50)
        config_file = repo_root / "config" / "github_config.json"
        artifacts_count = 0

        # Only fetch artifacts if we want to ensure we have all data
        # The JSON file committed to repo should already contain all results
        # Artifacts are just a backup - skip if JSON has enough data
        if local_results_count == 0 and config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    github_config = json.load(f)
                    github_token = github_config.get('token') or github_config.get('github_token')
                    github_repo = github_config.get('repo') or github_config.get('github_repo')

                    if github_token and github_repo:
                        headers = {
                            "Accept": "application/vnd.github+json",
                            "Authorization": f"Bearer {github_token}",
                            "X-GitHub-Api-Version": "2022-11-28"
                        }

                        # Get only the most recent completed run's artifact
                        url = f"https://api.github.com/repos/{github_repo}/actions/runs?per_page=5&status=completed"
                        response = requests.get(url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            runs = response.json().get('workflow_runs', [])
                            for run in runs[:1]:  # Only check the most recent run
                                run_id = run.get('id')
                                if run_id:
                                    artifacts_url = f"https://api.github.com/repos/{github_repo}/actions/runs/{run_id}/artifacts"
                                    art_response = requests.get(artifacts_url, headers=headers, timeout=10)
                                    if art_response.status_code == 200:
                                        artifacts = art_response.json().get('artifacts', [])
                                        for artifact in artifacts:
                                            if artifact.get('name') == 'scraping-results':
                                                download_url = artifact.get('archive_download_url')
                                                if download_url:
                                                    dl_response = requests.get(download_url, headers=headers, timeout=60)
                                                    if dl_response.status_code == 200:
                                                        zip_path = data_dir / f"temp_artifact.zip"
                                                        temp_extract_dir = data_dir / "temp_artifact"

                                                        try:
                                                            with open(zip_path, 'wb') as f:
                                                                f.write(dl_response.content)

                                                            temp_extract_dir.mkdir(exist_ok=True)
                                                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                                                zip_ref.extractall(temp_extract_dir)

                                                            artifact_file = temp_extract_dir / "scraping_results_github_actions.json"
                                                            if artifact_file.exists():
                                                                with open(artifact_file, 'r', encoding='utf-8') as f:
                                                                    artifact_data = json.load(f)

                                                                art_results = []
                                                                if isinstance(artifact_data, dict) and 'results' in artifact_data:
                                                                    art_results = artifact_data.get('results', [])
                                                                elif isinstance(artifact_data, list):
                                                                    art_results = artifact_data

                                                                for info in art_results:
                                                                    try:
                                                                        all_records_to_import.append(transform_to_artisan(info))
                                                                        artifacts_count += 1
                                                                    except:
                                                                        pass
                                                        finally:
                                                            try:
                                                                zip_path.unlink()
                                                            except:
                                                                pass
                                                            try:
                                                                import shutil
                                                                shutil.rmtree(temp_extract_dir)
                                                            except:
                                                                pass
                                                break  # Only process one artifact
                        if artifacts_count > 0:
                            st.info(f"☁️ {artifacts_count} résultats depuis artifact GitHub")
                    else:
                        st.info("☁️ Config GitHub non configurée")
            except Exception as e:
                st.warning(f"⚠️ Erreur artifacts: {e}")
        else:
            if local_results_count > 0:
                st.info("☁️ Artifacts ignorés (JSON local suffisant)")
            else:
                st.info("☁️ Pas de config GitHub")

        # === ÉTAPE 4: Batch import all records ===
        if all_records_to_import:
            status_text.text(f"💾 Import de {len(all_records_to_import)} enregistrements...")
            progress_bar.progress(60)

            # Use batch import for much faster performance
            def update_progress(current, total, message):
                pct = 60 + int((current / total) * 35)  # 60% to 95%
                progress_bar.progress(min(pct, 95))
                status_text.text(f"💾 {message}")

            import_stats = importer_artisans_batch(all_records_to_import, progress_callback=update_progress)
            total_imported = import_stats['imported']
            total_updated = import_stats['updated']
            st.info(f"💾 Import: {import_stats['imported']} nouveaux, {import_stats['updated']} mis à jour, {import_stats['errors']} erreurs")

        # === RÉSULTAT FINAL ===
        status_text.text("✅ Synchronisation terminée!")
        progress_bar.progress(100)
        if total_imported > 0:
            st.success(f"🎉 **{total_imported} nouveau(x) artisan(s) importé(s)!** (JSON: {local_results_count}, Artifacts: {artifacts_count})")
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        else:
            st.info("ℹ️ Aucun nouveau résultat à importer (tous déjà présents)")

# Les artisans sont déjà filtrés ci-dessus dans filtered_artisans

# ✅ Afficher un message avec le nombre d'artisans filtrés
if artisans:
    st.info(f"✅ {len(artisans)} artisan(s) correspondant aux filtres")
else:
    st.warning("⚠️ Aucun artisan ne correspond aux filtres sélectionnés. Essayez de modifier les critères de recherche.")

st.markdown("---")

# Affichage des artisans
st.subheader(f"📋 Liste des Artisans ({len(artisans)} trouvés)")

if not artisans:
    st.info("Aucun artisan trouvé avec ces filtres")
else:
    # ✅ Suppression de la vue détaillée - on garde seulement la liste compacte
    if True:  # Toujours afficher la liste compacte
        # Tableau compact avec TOUTES les informations scrapées
        data = []
        for artisan in artisans:
            # ✅ Formater les valeurs pour éviter les <NA>
            def format_value(value, default=''):
                """Formate une valeur pour l'affichage"""
                if value is None or value == '':
                    return default
                return str(value)
            
            row = {
                'ID': artisan.get('id', ''),
                'Entreprise': format_value(artisan.get('nom_entreprise'), 'N/A'),
                'Métier': format_value(artisan.get('type_artisan')),
                'Ville': format_value(artisan.get('ville')),
                'Ville recherche': format_value(artisan.get('ville_recherche')),
                'Département': format_value(artisan.get('departement')),
                'Adresse': format_value(artisan.get('adresse')),
                'Code postal': format_value(artisan.get('code_postal')),
                'Téléphone': format_value(artisan.get('telephone')),
                'Site web': format_value(artisan.get('site_web')),
                'Google Maps': format_value(artisan.get('google_maps_url')),
                'Note': f"{artisan.get('note')}/5" if artisan.get('note') else 'N/A',
                'Nombre avis': format_value(artisan.get('nombre_avis'), 'N/A')
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
        # Préparer le DataFrame pour l'export (utiliser le même format que l'affichage)
        df_export = pd.DataFrame(data)  # Utiliser 'data' qui est déjà formaté pour l'affichage
        
        # Créer un fichier Excel en mémoire
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Artisans')
        output.seek(0)
        
        st.download_button(
            "📥 Télécharger en XLSX",
            output.getvalue(),
            f"artisans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col_act2:
        if st.button("📋 Copier tous les numéros"):
            numeros = [a.get('telephone', '') for a in artisans if a.get('telephone')]
            st.code("\n".join(numeros))
    
    with col_act3:
        if st.button("🔄 Rafraîchir"):
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()

