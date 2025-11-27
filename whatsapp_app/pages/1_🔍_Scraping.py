"""
Page Scraping - Google Maps
Extraction des artisans depuis Google Maps
"""
import streamlit as st
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
# ✅ Plus besoin de threading/ThreadPoolExecutor - GitHub Actions uniquement

# Configuration de la page
st.set_page_config(page_title="Scraping Google Maps", page_icon="🔍", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import ajouter_artisan, get_statistiques

# ✅ Import des fonctions de tracking (avec fallback si elles n'existent pas)
try:
    from whatsapp_database.queries import is_already_scraped, get_scraping_history, mark_scraping_done
except ImportError:
    # Si les fonctions n'existent pas encore, créer des stubs
    def is_already_scraped(metier: str, departement: str, ville: str) -> bool:
        return False
    
    def get_scraping_history(metier: str = None, departement: str = None):
        return []
    
    def mark_scraping_done(metier: str, departement: str, ville: str, results_count: int = 0):
        pass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les villes par département
try:
    with open(Path(__file__).parent.parent.parent / "data" / "villes_par_departement.json", 'r', encoding='utf-8') as f:
        villes_par_dept = json.load(f)
except:
    villes_par_dept = {}

# ✅ Fonction pour récupérer les communes depuis data.gouv.fr
def get_communes_from_api(departement: str, min_population: int = 0, max_population: int = 50000):
    """Récupère les communes d'un département depuis l'API data.gouv.fr avec coordonnées GPS"""
    try:
        url = f"https://geo.api.gouv.fr/departements/{departement}/communes"
        params = {
            "fields": "nom,code,codesPostaux,population,centre",
            "format": "json"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            communes = response.json()
            # Filtrer par population
            filtered = []
            for c in communes:
                pop = c.get('population', 0)
                if min_population <= pop <= max_population:
                    centre = c.get('centre', {})
                    filtered.append({
                        'nom': c['nom'],
                        'code': c['code'],
                        'code_postal': c.get('codesPostaux', [c.get('code', '')])[0] if c.get('codesPostaux') else c.get('code', ''),
                        'population': pop,
                        'latitude': centre.get('coordinates', [None, None])[1] if centre else None,
                        'longitude': centre.get('coordinates', [None, None])[0] if centre else None
                    })
            # Trier par population (croissant)
            filtered.sort(key=lambda x: x['population'])
            return filtered
    except Exception as e:
        logger.error(f"Erreur API communes: {e}")
    return []

st.title("🔍 Scraping Google Maps - Artisans")

# Stats actuelles
stats = get_statistiques()
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.metric("Total artisans", f"{stats.get('total', 0):,}")
with col_stat2:
    st.metric("Avec téléphone", f"{stats.get('avec_telephone', 0):,}")
with col_stat3:
    st.metric("Avec site web", f"{stats.get('avec_site_web', 0):,}")
with col_stat4:
    st.metric("Sans site web", f"{stats.get('sans_site_web', 0):,}")

st.markdown("---")

# Configuration du scraping
st.subheader("⚙️ Configuration")

col_config1, col_config2 = st.columns(2)

with col_config1:
    # ✅ Multi-select pour les métiers
    metiers_options = ["plombier", "electricien", "chauffagiste", "menuisier", "peintre", "macon", "couvreur", "carreleur"]
    metiers = st.multiselect(
        "Type(s) d'artisan(s)",
        options=metiers_options,
        default=["plombier"],
        help="Sélectionnez un ou plusieurs types d'artisans à rechercher"
    )
    if not metiers:
        st.warning("⚠️ Veuillez sélectionner au moins un métier")
        metier = "plombier"
    else:
        metier = metiers[0]

with col_config2:
    # Liste des départements français
    departements_liste = [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "21",
        "22", "23", "24", "25", "26", "27", "28", "29", "2A", "2B",
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
        "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
        "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
        "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
        "90", "91", "92", "93", "94", "95"
    ]
    # ✅ Multi-select pour les départements
    departements = st.multiselect(
        "Département(s)",
        options=departements_liste,
        default=["77"],
        help="Sélectionnez un ou plusieurs départements à scraper"
    )
    if not departements:
        st.warning("⚠️ Veuillez sélectionner au moins un département")
        departement = "77"
    else:
        departement = departements[0]

col_config3, col_config4 = st.columns(2)

with col_config3:
    max_results = st.slider(
        "Nombre max de résultats",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="Nombre maximum d'établissements à scraper par ville"
    )

with col_config4:
    headless = st.checkbox(
        "Mode headless (navigateur invisible)",
        value=True,
        help="Mode headless activé par défaut (plus rapide). Décochez pour voir le navigateur."
    )

# ✅ Charger la configuration GitHub si elle existe
github_config_file = Path(__file__).parent.parent.parent / "config" / "github_config.json"
github_token_default = ""
github_repo_default = ""

try:
    if github_config_file.exists():
        with open(github_config_file, 'r', encoding='utf-8') as f:
            github_config = json.load(f)
            github_token_default = github_config.get('github_token', '')
            github_repo_default = github_config.get('github_repo', '')
except:
    pass

# ✅ Toggle Local vs GitHub Actions
st.markdown("### 🚀 Mode d'exécution")
# ✅ GitHub Actions est maintenant la SEULE option disponible
# Forcer GitHub Actions à True
use_github_actions = True
st.session_state.use_github_actions = True

# Afficher un message informatif
st.info("☁️ **Mode GitHub Actions activé** - Le scraping s'exécutera sur GitHub Actions (gratuit jusqu'à 2000 min/mois)")

if use_github_actions:
    st.info("ℹ️ Le scraping s'exécutera sur GitHub Actions. Les résultats sont sauvegardés directement dans la BDD en temps réel.")
    
    # ✅ Utiliser les valeurs du fichier de config automatiquement (pas de champs visibles)
    github_token = github_token_default
    github_repo = github_repo_default
    
    if not github_token or not github_repo:
        st.error("⚠️ Configuration GitHub manquante. Vérifiez que config/github_config.json existe avec token et repo.")
else:
    # Si GitHub Actions n'est pas activé, utiliser des valeurs vides
    github_token = ""
    github_repo = ""

# ✅ Section : Gestion des workflows GitHub Actions (VISIBLE EN HAUT, DÈS LE DÉMARRAGE)
# ✅ TOUJOURS AFFICHÉE - même si pas de token (pour montrer qu'il faut configurer)
st.markdown("---")
st.subheader("⚙️ Gestion des Workflows GitHub Actions")

if github_token and github_repo:
    # Lister les workflows en cours
    try:
        workflows_en_cours = list_github_workflows(github_token, github_repo)
    except Exception as e:
        logger.error(f"Erreur récupération workflows: {e}")
        workflows_en_cours = []
    
    if workflows_en_cours:
        # ✅ AFFICHER LE NOMBRE DE WORKFLOWS EN COURS (comme demandé)
        col_count1, col_count2 = st.columns([1, 4])
        with col_count1:
            st.metric("Workflows actifs", len(workflows_en_cours))
        with col_count2:
            if st.button("⏹️ Arrêter tous", key="cancel_all_workflows_top", help="Arrêter tous les workflows en cours"):
                with st.spinner("⏹️ Annulation de tous les workflows..."):
                    success, message = cancel_all_github_workflows(github_token, github_repo)
                    if success:
                        st.success(message)
                    else:
                        st.warning(message)
                    st.experimental_rerun()
        
        # Afficher chaque workflow avec possibilité de le tuer individuellement
        st.markdown("**Détails des workflows :**")
        for workflow in workflows_en_cours:
            col_wf1, col_wf2, col_wf3 = st.columns([3, 1, 1])
            with col_wf1:
                status_emoji = "🟢" if workflow['status'] == 'in_progress' else "🟡"
                status_text = "En cours" if workflow['status'] == 'in_progress' else "En attente"
                created_time = workflow['created_at'][:19].replace('T', ' ')
                st.markdown(f"{status_emoji} **Run #{workflow['run_number']}** - {status_text} - {created_time}")
            with col_wf2:
                github_url = workflow.get('html_url', f"https://github.com/{github_repo}/actions/runs/{workflow['id']}")
                st.markdown(f"[🔗 Voir]({github_url})")
            with col_wf3:
                if st.button(f"⏹️ Arrêter", key=f"cancel_{workflow['id']}"):
                    with st.spinner(f"⏹️ Annulation du workflow #{workflow['run_number']}..."):
                        if cancel_github_workflow(github_token, github_repo, workflow['id']):
                            st.success(f"✅ Workflow #{workflow['run_number']} annulé")
                            st.experimental_rerun()
                        else:
                            st.error(f"❌ Erreur lors de l'annulation du workflow #{workflow['run_number']}")
    else:
        st.success("✅ Aucun workflow en cours")
else:
    st.warning("⚠️ Configuration GitHub manquante. La gestion des workflows nécessite un token et un repository configurés.")
    
st.markdown("---")

# ✅ Initialiser les variables GitHub Actions dans session_state AVANT de les utiliser
if 'github_workflow_id' not in st.session_state:
    st.session_state.github_workflow_id = None
if 'github_workflow_status' not in st.session_state:
    st.session_state.github_workflow_status = None
if 'github_workflow_conclusion' not in st.session_state:
    st.session_state.github_workflow_conclusion = None
# Initialiser aussi scraping_running si nécessaire (pour la vérification ci-dessous)
if 'scraping_running' not in st.session_state:
    st.session_state.scraping_running = False

# ✅ CRITIQUE : Vérifier si on a un workflow GitHub Actions actif au démarrage
# Si oui, maintenir scraping_running = True pour garder le dashboard visible
# Note: get_github_workflow_status est défini plus tard, donc on ne peut pas l'appeler ici
# Cette vérification sera faite dans la section du dashboard GitHub Actions

# ✅ Options avancées
with st.expander("⚙️ Options avancées"):
    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        use_api_communes = st.checkbox(
            "Utiliser API data.gouv.fr pour les communes",
            value=False,
            help="Récupère automatiquement les communes depuis l'API officielle"
        )
        if use_api_communes:
            min_pop = st.number_input("Population minimum", min_value=0, value=0, step=100)
            max_pop = st.number_input("Population maximum", min_value=0, value=50000, step=1000)
            
            # ✅ Bouton pour afficher les communes trouvées
            if st.button("📋 Afficher les communes trouvées"):
                st.session_state.show_communes = True
    with col_adv2:
        enable_resume = st.checkbox(
            "Activer resume/checkpoint",
            value=True,
            disabled=use_github_actions,  # Désactiver pour GitHub Actions
            help="Permet de reprendre le scraping où il s'est arrêté (non disponible avec GitHub Actions)"
        )
        num_threads = st.slider(
            "Nombre de threads",
            min_value=1,
            max_value=20,
            value=3,
            help="Nombre de navigateurs en parallèle (attention: plus de threads = plus rapide mais plus de ressources)"
        )

# ✅ Afficher les communes si demandé
if st.session_state.get('show_communes', False) and use_api_communes and departements:
    st.markdown("---")
    st.subheader("📍 Communes trouvées via API data.gouv.fr")
    
    communes_trouvees = {}
    with st.spinner("🔄 Récupération des communes depuis l'API..."):
        for dept in departements:
            communes = get_communes_from_api(dept, min_pop if use_api_communes else 0, max_pop if use_api_communes else 50000)
            communes_trouvees[dept] = communes
    
    # Afficher un tableau avec toutes les communes
    all_communes = []
    for dept, communes in communes_trouvees.items():
        for commune in communes:
            all_communes.append({
                'Département': dept,
                'Commune': commune['nom'],
                'Code postal': commune['code_postal'],
                'Population': f"{commune['population']:,}" if commune['population'] > 0 else "N/A"
            })
    
    if all_communes:
        st.info(f"📊 Total: {len(all_communes)} communes trouvées")
        
        # ✅ Mise en page côte à côte : tableau et carte
        col_table, col_map = st.columns([1, 1])
        
        with col_table:
            st.subheader("📋 Liste des communes")
            df_communes = pd.DataFrame(all_communes)
            
            # CSS pour autofit toutes les colonnes et éviter la colonne vide
            st.markdown("""
            <style>
            /* Cibler le conteneur du DataFrame */
            div[data-testid="stDataFrame"] {
                width: 100% !important;
            }
            div[data-testid="stDataFrame"] > div {
                width: 100% !important;
                overflow-x: visible !important;
            }
            /* Tableau avec ajustement automatique - largeur 100% mais colonnes auto */
            div[data-testid="stDataFrame"] table {
                width: 100% !important;
                table-layout: auto !important;
                border-collapse: collapse !important;
            }
            /* Colonnes avec ajustement automatique selon le contenu */
            div[data-testid="stDataFrame"] th,
            div[data-testid="stDataFrame"] td {
                white-space: nowrap !important;
                padding: 8px 12px !important;
                width: auto !important;
                max-width: none !important;
            }
            /* Masquer complètement la dernière colonne si elle est vide */
            div[data-testid="stDataFrame"] table thead tr th:last-child:empty,
            div[data-testid="stDataFrame"] table tbody tr td:last-child:empty {
                display: none !important;
                width: 0 !important;
                padding: 0 !important;
                border: none !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Utiliser dataframe sans hide_index (non supporté dans cette version)
            st.dataframe(df_communes, height=600)
            
            # JavaScript pour masquer la colonne vide après le rendu
            st.markdown("""
            <script>
            function hideEmptyColumn() {
                const tables = document.querySelectorAll('div[data-testid="stDataFrame"] table');
                tables.forEach(function(table) {
                    const rows = table.querySelectorAll('tr');
                    if (rows.length > 0) {
                        // Vérifier si la dernière colonne est vide dans toutes les lignes
                        let allEmpty = true;
                        rows.forEach(function(row) {
                            const lastCell = row.querySelector('th:last-child, td:last-child');
                            if (lastCell && lastCell.textContent && lastCell.textContent.trim() !== '') {
                                allEmpty = false;
                            }
                        });
                        
                        // Si toutes les dernières colonnes sont vides, les masquer
                        if (allEmpty) {
                            rows.forEach(function(row) {
                                const lastCell = row.querySelector('th:last-child, td:last-child');
                                if (lastCell) {
                                    lastCell.style.display = 'none';
                                    lastCell.style.width = '0';
                                    lastCell.style.padding = '0';
                                    lastCell.style.border = 'none';
                                }
                            });
                        }
                    }
                });
            }
            // Exécuter après le chargement
            setTimeout(hideEmptyColumn, 100);
            setTimeout(hideEmptyColumn, 500);
            setTimeout(hideEmptyColumn, 1000);
            </script>
            """, unsafe_allow_html=True)
        
        with col_map:
            st.subheader("🗺️ Carte interactive")
            
            # ✅ Carte interactive avec folium
            try:
                import folium
                from streamlit_folium import folium_static
                
                # Filtrer les communes avec coordonnées GPS directement depuis communes_trouvees
                communes_avec_gps = []
                for dept, communes_list in communes_trouvees.items():
                    for comm in communes_list:
                        if comm.get('latitude') and comm.get('longitude'):
                            communes_avec_gps.append({
                                'nom': comm['nom'],
                                'departement': dept,
                                'code_postal': comm.get('code_postal', ''),
                                'population': comm.get('population', 0),
                                'latitude': comm['latitude'],
                                'longitude': comm['longitude']
                            })
                
                if communes_avec_gps:
                    # Calculer le centre de la carte (moyenne des coordonnées)
                    avg_lat = sum(c['latitude'] for c in communes_avec_gps) / len(communes_avec_gps)
                    avg_lon = sum(c['longitude'] for c in communes_avec_gps) / len(communes_avec_gps)
                    
                    # Créer une carte centrée sur les communes
                    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8)
                    
                    # ✅ Calculer les min/max de population POUR LES COMMUNES AFFICHÉES (limitées à 200)
                    sample_communes = communes_avec_gps[:200] if len(communes_avec_gps) > 200 else communes_avec_gps
                    populations = [c['population'] for c in sample_communes if c['population'] > 0]
                    
                    if populations:
                        min_pop_displayed = min(populations)
                        max_pop_displayed = max(populations)
                        pop_range_displayed = max_pop_displayed - min_pop_displayed if max_pop_displayed > min_pop_displayed else 1
                    else:
                        min_pop_displayed = 0
                        max_pop_displayed = 1
                        pop_range_displayed = 1
                    
                    for commune in sample_communes:
                        pop = commune['population']
                        pop_str = f"{pop:,}" if pop > 0 else "N/A"
                        popup_text = f"<b>{commune['nom']}</b><br>Département: {commune['departement']}<br>Code postal: {commune['code_postal']}<br>Population: {pop_str}"
                        
                        # ✅ Taille du marqueur proportionnelle à la population RELATIVE au min/max affichés
                        if pop > 0 and pop_range_displayed > 0:
                            # Normaliser entre 3 et 15 pixels de radius selon le min/max des communes affichées
                            normalized = (pop - min_pop_displayed) / pop_range_displayed
                            radius = 3 + (normalized * 12)  # Entre 3 et 15 pixels
                        else:
                            radius = 3
                        
                        # Couleur selon la population (seuils fixes pour la couleur)
                        if pop > 10000:
                            icon_color = 'red'
                        elif pop > 5000:
                            icon_color = 'orange'
                        elif pop > 2000:
                            icon_color = 'blue'
                        else:
                            icon_color = 'green'
                        
                        folium.CircleMarker(
                            location=[commune['latitude'], commune['longitude']],
                            radius=radius,
                            popup=folium.Popup(popup_text, max_width=200),
                            tooltip=f"{commune['nom']} ({pop:,} hab.)" if pop > 0 else commune['nom'],
                            color=icon_color,
                            fill=True,
                            fillColor=icon_color,
                            fillOpacity=0.6,
                            weight=1
                        ).add_to(m)
                    
                    # Afficher la carte
                    folium_static(m, width=700, height=600)
                    
                    if len(communes_avec_gps) > 200:
                        st.caption(f"🗺️ Affichage de 200 communes sur {len(communes_avec_gps)} avec coordonnées GPS")
                    else:
                        st.caption(f"🗺️ {len(communes_avec_gps)} communes avec coordonnées GPS")
                    
                    # Légende
                    st.markdown("""
                    <div style='background: #f0f0f0; padding: 10px; border-radius: 5px; margin-top: 10px;'>
                        <strong>Légende :</strong><br>
                        🔴 Rouge : > 10 000 hab. | 🟠 Orange : 5 000 - 10 000 hab. | 
                        🔵 Bleu : 2 000 - 5 000 hab. | 🟢 Vert : < 2 000 hab.<br>
                        <small>La taille des points est proportionnelle à la population</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Aucune commune avec coordonnées GPS trouvée")
            except ImportError:
                st.info("💡 Pour afficher une carte interactive, installez: `pip install folium streamlit-folium`")
            except Exception as e:
                st.error(f"Erreur lors de la création de la carte: {e}")
    else:
        st.warning("Aucune commune trouvée avec les critères sélectionnés")
    
    if st.button("❌ Fermer l'affichage des communes"):
        st.session_state.show_communes = False
        st.experimental_rerun()

st.markdown("---")

# État du scraping
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'scraping_running' not in st.session_state:
    st.session_state.scraping_running = False
if 'scraped_results' not in st.session_state:
    st.session_state.scraped_results = []
if 'scraping_thread' not in st.session_state:
    st.session_state.scraping_thread = None
if 'scraping_started' not in st.session_state:
    st.session_state.scraping_started = False
if 'saved_count' not in st.session_state:
    st.session_state.saved_count = 0
if 'logs_buffer' not in st.session_state:
    st.session_state.logs_buffer = []
# Note: github_workflow_id et github_workflow_status sont initialisés plus tôt dans le code

# ✅ CRITIQUE : Vérifier si on a un workflow GitHub Actions actif au démarrage
# Si oui, maintenir scraping_running = True pour garder le dashboard visible
# Cette vérification se fera plus tard, après le chargement de la config GitHub

# ✅ Fonctions pour GitHub Actions
def trigger_github_workflow(token, repo, metiers, departements, max_results, num_threads, use_api_communes, min_pop, max_pop):
    """Déclenche le workflow GitHub Actions"""
    try:
        # ✅ D'abord, récupérer la liste des workflows pour trouver le bon ID
        workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Récupérer les workflows
        workflows_response = requests.get(workflows_url, headers=headers)
        if workflows_response.status_code != 200:
            return False, f"Erreur récupération workflows: {workflows_response.status_code} - {workflows_response.text}"
        
        workflows_data = workflows_response.json()
        workflow_id = None
        
        # Chercher le workflow "Google Maps Scraping" ou "scraping.yml"
        for workflow in workflows_data.get('workflows', []):
            if workflow.get('name') == 'Google Maps Scraping' or workflow.get('path', '').endswith('scraping.yml'):
                workflow_id = workflow.get('id')
                break
        
        if not workflow_id:
            # Essayer avec le nom du fichier directement
            url = f"https://api.github.com/repos/{repo}/actions/workflows/scraping.yml/dispatches"
        else:
            # Utiliser l'ID du workflow (plus fiable)
            url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        
        data = {
            "ref": "main",  # Essayer "main" d'abord
            "inputs": {
                "metiers": json.dumps(metiers),
                "departements": json.dumps(departements),
                "max_results": str(max_results),
                "num_threads": str(num_threads),
                "use_api_communes": str(use_api_communes).lower(),
                "min_pop": str(min_pop),
                "max_pop": str(max_pop)
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        # Si 404 avec "main", essayer "master"
        if response.status_code == 404 and data["ref"] == "main":
            data["ref"] = "master"
            response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 204:
            # ✅ Récupérer le run_id du workflow qui vient d'être lancé
            # Attendre un peu pour que GitHub crée le run
            import time
            time.sleep(2)
            
            # Récupérer le dernier run du workflow
            runs_url = f"https://api.github.com/repos/{repo}/actions/workflows/scraping.yml/runs?per_page=1"
            runs_response = requests.get(runs_url, headers=headers)
            if runs_response.status_code == 200:
                runs_data = runs_response.json().get('workflow_runs', [])
                if runs_data:
                    run_id = runs_data[0].get('id')
                    return True, f"Workflow déclenché avec succès (Run ID: {run_id})", run_id
            
            return True, "Workflow déclenché avec succès"
        else:
            error_msg = response.text
            if response.status_code == 404:
                error_msg += f"\n💡 Vérifiez que le workflow existe dans .github/workflows/scraping.yml et qu'il est commité sur GitHub"
            return False, f"Erreur: {response.status_code} - {error_msg}", None
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def get_github_workflow_status(token, repo, workflow_id=None):
    """Récupère le statut du workflow GitHub Actions"""
    try:
        if workflow_id:
            url = f"https://api.github.com/repos/{repo}/actions/runs/{workflow_id}"
        else:
            # Récupérer le dernier run (non annulé si possible)
            url = f"https://api.github.com/repos/{repo}/actions/workflows/scraping.yml/runs?per_page=10"
        
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            if workflow_id:
                data = response.json()
            else:
                # Récupérer tous les runs et trouver le dernier non-annulé (ou le dernier tout court)
                runs = response.json().get('workflow_runs', [])
                if not runs:
                    return None, None, None
                
                # Chercher le dernier run non-annulé
                for run in runs:
                    if run.get('conclusion') != 'cancelled':
                        data = run
                        break
                else:
                    # Si tous sont annulés, prendre le dernier
                    data = runs[0]
            
            status = data.get('status')  # queued, in_progress, completed
            conclusion = data.get('conclusion')  # success, failure, cancelled, etc.
            run_id = data.get('id')
            return status, conclusion, run_id
        else:
            return None, None, None
    except Exception as e:
        logger.error(f"Erreur récupération statut: {e}")
        return None, None, None

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
                            import io
                            data_dir = Path(__file__).parent.parent.parent / "data"
                            zip_path = data_dir / "github_artifact.zip"
                            with open(zip_path, 'wb') as f:
                                f.write(download_response.content)
                            
                            # Extraire le JSON
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(data_dir)
                            
                            # Lire les fichiers
                            results_file = data_dir / "scraping_results_github_actions.json"
                            status_file = data_dir / "github_actions_status.json"
                            
                            result_data = None
                            status_data = None
                            
                            if results_file.exists():
                                with open(results_file, 'r', encoding='utf-8') as f:
                                    result_data = json.load(f)
                            
                            if status_file.exists():
                                with open(status_file, 'r', encoding='utf-8') as f:
                                    status_data = json.load(f)
                            
                            # Nettoyer
                            zip_path.unlink()
                            
                            # ✅ Retourner dans le format attendu (compatibilité)
                            if result_data and isinstance(result_data, dict) and 'results' in result_data:
                                return result_data  # Format: {'results': [...], 'total_results': ...}
                            elif result_data and isinstance(result_data, list):
                                return {'results': result_data, 'total_results': len(result_data)}
                            else:
                                return {'results': [], 'total_results': 0, 'status': status_data}
            return None
        return None
    except Exception as e:
        logger.error(f"Erreur téléchargement artifact: {e}")
        return None

def get_github_workflow_logs(token, repo, run_id):
    """Récupère les logs du workflow GitHub Actions"""
    try:
        # Récupérer les jobs du workflow
        url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            jobs = response.json().get('jobs', [])
            logs = []
            for job in jobs:
                if job.get('status') == 'completed':
                    # Récupérer les logs du job
                    logs_url = job.get('logs_url')
                    if logs_url:
                        logs_response = requests.get(logs_url, headers=headers)
                        if logs_response.status_code == 200:
                            # Les logs sont dans un format spécifique GitHub
                            logs.append({
                                'job_name': job.get('name'),
                                'status': job.get('conclusion'),
                                'logs_url': logs_url
                            })
            return logs
        return []
    except Exception as e:
        logger.error(f"Erreur récupération logs: {e}")
        return []

def list_github_workflows(token, repo):
    """Liste tous les workflows GitHub Actions en cours"""
    try:
        # Récupérer les runs du workflow scraping
        runs_url = f"https://api.github.com/repos/{repo}/actions/runs"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        params = {
            "status": "in_progress,queued",
            "per_page": 100
        }
        
        response = requests.get(runs_url, headers=headers, params=params)
        if response.status_code != 200:
            return []
        
        runs_data = response.json()
        workflows = []
        
        for run in runs_data.get('workflow_runs', []):
            workflows.append({
                'id': run.get('id'),
                'run_number': run.get('run_number'),
                'status': run.get('status'),
                'conclusion': run.get('conclusion'),
                'created_at': run.get('created_at'),
                'updated_at': run.get('updated_at'),
                'head_branch': run.get('head_branch'),
                'workflow_id': run.get('workflow_id'),
                'html_url': run.get('html_url')
            })
        
        return workflows
    except Exception as e:
        logger.error(f"Erreur liste workflows: {e}")
        return []

def cancel_github_workflow(token, repo, run_id):
    """Annule un workflow GitHub Actions spécifique"""
    try:
        cancel_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/cancel"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        response = requests.post(cancel_url, headers=headers)
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Erreur annulation workflow {run_id}: {e}")
        return False

def cancel_all_github_workflows(token, repo):
    """Annule tous les workflows GitHub Actions en cours (in_progress et queued)"""
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        cancelled_count = 0
        total_runs = 0
        
        # Récupérer les runs "in_progress"
        url_in_progress = f"https://api.github.com/repos/{repo}/actions/runs?status=in_progress&per_page=100"
        response = requests.get(url_in_progress, headers=headers)
        if response.status_code == 200:
            runs = response.json().get('workflow_runs', [])
            total_runs += len(runs)
            for run in runs:
                run_id = run.get('id')
                if run_id:
                    cancel_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/cancel"
                    cancel_response = requests.post(cancel_url, headers=headers)
                    if cancel_response.status_code == 202:
                        cancelled_count += 1
        elif response.status_code != 200:
            logger.warning(f"Erreur récupération runs in_progress: {response.status_code}")
        
        # Récupérer les runs "queued"
        url_queued = f"https://api.github.com/repos/{repo}/actions/runs?status=queued&per_page=100"
        response = requests.get(url_queued, headers=headers)
        if response.status_code == 200:
            runs = response.json().get('workflow_runs', [])
            total_runs += len(runs)
            for run in runs:
                run_id = run.get('id')
                if run_id:
                    cancel_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/cancel"
                    cancel_response = requests.post(cancel_url, headers=headers)
                    if cancel_response.status_code == 202:
                        cancelled_count += 1
        elif response.status_code != 200:
            logger.warning(f"Erreur récupération runs queued: {response.status_code}")
        
        if total_runs == 0:
            return True, "Aucun workflow en cours à annuler"
        elif cancelled_count == total_runs:
            return True, f"✅ {cancelled_count} workflow(s) annulé(s) sur {total_runs} trouvé(s)"
        else:
            return False, f"⚠️ {cancelled_count} workflow(s) annulé(s) sur {total_runs} trouvé(s) (certains n'ont peut-être pas pu être annulés)"
    except Exception as e:
        logger.error(f"Erreur annulation workflows: {e}")
        return False, f"Erreur: {str(e)}"

# ✅ Cette section a été déplacée en haut pour être visible dès le démarrage (voir ligne ~200)

# ✅ Boutons de contrôle SIMPLIFIÉS (comme demandé)
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    # ✅ GitHub Actions uniquement - pas de mode local
    button_disabled = st.session_state.scraping_running or (st.session_state.github_workflow_status == 'in_progress')
    button_text = "☁️ LANCER"
    
    if st.button(button_text, disabled=button_disabled):
        if not metiers or not departements:
            st.error("⚠️ Veuillez sélectionner au moins un métier et un département")
        elif not github_token or not github_repo:
            st.error("⚠️ Veuillez renseigner le token GitHub et le repository")
        else:
            # ✅ Vérifier les villes déjà scrapées
            villes_deja_scrapees = []
            villes_a_scraper = []
            
            # Préparer la liste des villes à scraper
            for dept in departements:
                if use_api_communes:
                    communes = get_communes_from_api(dept, min_pop if use_api_communes else 0, max_pop if use_api_communes else 50000)
                    villes_dept = [c['nom'] for c in communes]
                else:
                    villes_dept = villes_par_dept.get(dept, [])
                
                for metier in metiers:
                    for ville in villes_dept:
                        if is_already_scraped(metier, dept, ville):
                            villes_deja_scrapees.append(f"{metier} - {dept} - {ville}")
                        else:
                            villes_a_scraper.append(f"{metier} - {dept} - {ville}")
            
            # Afficher un avertissement si certaines villes sont déjà scrapées
            if villes_deja_scrapees:
                st.warning(f"⚠️ {len(villes_deja_scrapees)} combinaison(s) métier/département/ville déjà scrapée(s). Elles seront ignorées si vous continuez.")
                with st.expander("📋 Voir les villes déjà scrapées"):
                    for v in villes_deja_scrapees[:20]:  # Limiter à 20 pour l'affichage
                        st.text(v)
                    if len(villes_deja_scrapees) > 20:
                        st.caption(f"... et {len(villes_deja_scrapees) - 20} autres")
            
            if not villes_a_scraper:
                st.error("❌ Toutes les combinaisons sélectionnées ont déjà été scrapées. Veuillez sélectionner d'autres options.")
            else:
                st.info(f"✅ {len(villes_a_scraper)} combinaison(s) à scraper")
                
                # Déclencher le workflow GitHub Actions
                result = trigger_github_workflow(
                    github_token,
                    github_repo,
                    metiers,
                    departements,
                    max_results,
                    num_threads,
                    use_api_communes,
                    min_pop if use_api_communes else 0,
                    max_pop if use_api_communes else 50000
                )
                
                # ✅ Gérer le retour (peut être (success, message) ou (success, message, run_id))
                if len(result) == 3:
                    success, message, run_id = result
                else:
                    success, message = result
                    run_id = None
                
                if success:
                    st.success(f"✅ {message}")
                    st.info("⏳ Le scraping est en cours sur GitHub Actions. Les résultats sont sauvegardés directement dans la BDD.")
                    st.session_state.scraping_running = True
                    st.session_state.github_workflow_status = 'in_progress'
                    st.session_state.departements_selected = departements
                    st.session_state.metiers_selected = metiers
                    
                    # ✅ Stocker le run_id si disponible
                    if run_id:
                        st.session_state.github_workflow_id = run_id
                    # ✅ Marquer qu'on vient de lancer un workflow pour ne pas l'annuler
                    st.session_state.workflow_just_launched = True
                    st.experimental_rerun()
                else:
                    st.error(f"❌ {message}")

with col_btn2:
    # ✅ Bouton ARRÊTER (simplifié - pas de confirmation)
    if github_token and github_repo:
        if st.button("⏹️ ARRÊTER", help="Arrêter tous les workflows GitHub Actions en cours", key="stop_all_workflows"):
            with st.spinner("⏹️ Arrêt des workflows..."):
                success, message = cancel_all_github_workflows(github_token, github_repo)
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.scraping_running = False
                    st.session_state.github_workflow_status = None
                    st.session_state.github_workflow_id = None
                    st.session_state.scraped_results = []
                    st.experimental_rerun()
                else:
                    st.error(f"❌ {message}")

with col_btn3:
    # ✅ Bouton RAFRAÎCHIR
    if st.button("🔄 RAFRAÎCHIR", help="Rafraîchir le statut des workflows et les résultats", key="refresh_workflows"):
        st.experimental_rerun()

st.markdown("---")

# Zone de scraping
# ✅ IMPORTANT: Afficher le dashboard si on a un workflow_id OU si scraping_running est True
# Cela permet de garder le dashboard visible même après un refresh
current_use_github = st.session_state.get('use_github_actions', True)  # Toujours True maintenant
has_workflow_id = st.session_state.get('github_workflow_id') is not None
should_show_dashboard = st.session_state.scraping_running or has_workflow_id

if should_show_dashboard:
    # ✅ Vérifier si on utilise GitHub Actions
    if current_use_github and github_token and github_repo:
        st.subheader("☁️ Dashboard GitHub Actions")
        
        # ✅ Récupérer le statut frais depuis GitHub API (ne pas utiliser l'ancien statut)
        # Si le workflow_id stocké est annulé, récupérer le dernier non-annulé
        current_workflow_id = st.session_state.github_workflow_id
        status, conclusion, run_id = get_github_workflow_status(github_token, github_repo, current_workflow_id)
        
        # ✅ Si le workflow récupéré est annulé mais qu'on a un workflow_id différent, essayer de récupérer le bon
        if conclusion == 'cancelled' and current_workflow_id and run_id == current_workflow_id:
            # Le workflow_id stocké a été annulé, récupérer le dernier non-annulé
            status, conclusion, run_id = get_github_workflow_status(github_token, github_repo, None)
        
        # ✅ Mettre à jour le statut dans session_state avec les données fraîches
        if status:
            st.session_state.github_workflow_status = status
        if conclusion:
            # Stocker aussi la conclusion pour l'affichage
            st.session_state.github_workflow_conclusion = conclusion
        if run_id:
            st.session_state.github_workflow_id = run_id
            # Maintenir scraping_running pour garder le dashboard visible
            # Même si terminé (success, failure, cancelled), on garde le dashboard pour voir les résultats
            st.session_state.scraping_running = True
        
        # ✅ Si le workflow est annulé, mettre à jour le statut mais garder le dashboard visible
        if conclusion == 'cancelled':
            st.session_state.github_workflow_status = 'completed'
            # Ne PAS mettre scraping_running = False pour garder le dashboard visible
            # L'utilisateur peut voir que le workflow a été annulé
        
        # ✅ Si on a un workflow_id mais pas de statut, essayer de le récupérer
        if st.session_state.github_workflow_id and not status:
            status, conclusion, run_id = get_github_workflow_status(github_token, github_repo, st.session_state.github_workflow_id)
            if status:
                st.session_state.github_workflow_status = status
                if conclusion:
                    st.session_state.github_workflow_conclusion = conclusion
                if run_id:
                    st.session_state.github_workflow_id = run_id
                st.session_state.scraping_running = True
        
        # ✅ Dashboard visuel avec colonnes
        col_status, col_progress, col_actions = st.columns([2, 3, 1])
        
        with col_status:
            # Statut avec badge coloré
            if status == 'completed':
                if conclusion == 'success':
                    st.success("✅ **Terminé avec succès**")
                elif conclusion == 'failure':
                    st.error("❌ **Échec**")
                elif conclusion == 'cancelled':
                    st.warning("⏹️ **Annulé**")
                else:
                    st.warning(f"⚠️ **{conclusion or 'Terminé'}**")
            elif status == 'in_progress':
                st.info("🔄 **En cours...**")
            elif status == 'queued':
                st.info("⏳ **En attente...**")
            else:
                st.info(f"📊 **{status}**")
        
        with col_progress:
            # ✅ Essayer de charger le statut depuis le fichier local (si téléchargé)
            status_file = Path(__file__).parent.parent.parent / "data" / "github_actions_status.json"
            if status_file.exists():
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                        total_tasks = status_data.get('total_tasks', 0)
                        completed_tasks = status_data.get('completed_tasks', 0)
                        total_results = status_data.get('total_results', 0)
                        
                        if total_tasks > 0:
                            progress_pct = (completed_tasks / total_tasks) * 100
                            st.progress(progress_pct / 100)
                            st.caption(f"📊 {completed_tasks}/{total_tasks} villes scrapées | {total_results} résultats trouvés")
                        else:
                            st.caption("⏳ Initialisation...")
                except:
                    pass
            else:
                if status == 'in_progress' or status == 'queued':
                    st.caption("⏳ En attente des premières données...")
        
        with col_actions:
            if run_id:
                github_url = f"https://github.com/{github_repo}/actions/runs/{run_id}"
                st.markdown(f"[🔗 Voir logs]({github_url})")
        
        # ✅ Section détaillée
        with st.expander("📋 Détails du workflow", expanded=True):
            # Informations du workflow
            if run_id:
                st.write(f"**Run ID:** `{run_id}`")
                st.write(f"**Statut:** {status}")
                if conclusion:
                    st.write(f"**Conclusion:** {conclusion}")
            
            # ✅ Charger et afficher le statut détaillé
            status_file = Path(__file__).parent.parent.parent / "data" / "github_actions_status.json"
            if status_file.exists():
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                        
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            st.metric("Villes totales", status_data.get('total_tasks', 0))
                        with col_info2:
                            st.metric("Villes complétées", status_data.get('completed_tasks', 0))
                        with col_info3:
                            st.metric("Résultats trouvés", status_data.get('total_results', 0))
                        
                        # ✅ Afficher les résultats progressifs si disponibles (chargés automatiquement au refresh)
                        # Les résultats sont déjà chargés dans session_state par le bouton "Rafraîchir"
                        if st.session_state.get('scraped_results'):
                            results_count = len(st.session_state.scraped_results)
                            st.success(f"📥 {results_count} résultats disponibles")
                            
                            # Afficher un aperçu
                            if results_count > 0:
                                preview_df = pd.DataFrame(st.session_state.scraped_results[:10])
                                if not preview_df.empty:
                                    st.caption("👀 Aperçu des résultats (10 premiers):")
                                    # Sélectionner les colonnes disponibles
                                    available_cols = ['nom', 'telephone', 'site_web', 'ville_recherche']
                                    cols_to_show = [col for col in available_cols if col in preview_df.columns]
                                    if cols_to_show:
                                        st.dataframe(preview_df[cols_to_show].head(10), use_container_width=True)
                        else:
                            # Essayer de charger depuis le fichier si pas encore chargé
                            results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_github_actions.json"
                            if results_file.exists():
                                try:
                                    with open(results_file, 'r', encoding='utf-8') as f:
                                        results_data = json.load(f)
                                        if isinstance(results_data, dict) and 'results' in results_data:
                                            results_list = results_data['results']
                                        elif isinstance(results_data, list):
                                            results_list = results_data
                                        else:
                                            results_list = []
                                        
                                        if results_list:
                                            st.session_state.scraped_results = results_list
                                            st.success(f"📥 {len(results_list)} résultats disponibles")
                                            
                                            # Afficher un aperçu
                                            preview_df = pd.DataFrame(results_list[:10])
                                            if not preview_df.empty:
                                                st.caption("👀 Aperçu des résultats (10 premiers):")
                                                available_cols = ['nom', 'telephone', 'site_web', 'ville_recherche']
                                                cols_to_show = [col for col in available_cols if col in preview_df.columns]
                                                if cols_to_show:
                                                    st.dataframe(preview_df[cols_to_show].head(10), use_container_width=True)
                                except Exception as e:
                                    logger.error(f"Erreur lecture résultats: {e}")
                except Exception as e:
                    st.error(f"Erreur lecture statut: {e}")
        
        # ✅ Boutons de contrôle simplifiés
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            # Bouton pour rafraîchir le statut (remplace auto-refresh)
            if st.button("🔄 Rafraîchir", key="refresh_github"):
                # ✅ CRITIQUE : Maintenir TOUJOURS le workflow_id et scraping_running pour garder le dashboard visible
                saved_workflow_id = st.session_state.get('github_workflow_id')
                
                # Si on a un workflow_id, on le maintient ABSOLUMENT pour garder le dashboard visible
                if saved_workflow_id:
                    st.session_state.github_workflow_id = saved_workflow_id
                    st.session_state.scraping_running = True  # TOUJOURS True si on a un workflow_id
                
                # ✅ Charger automatiquement les résultats progressifs depuis le fichier local
                results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_github_actions.json"
                if results_file.exists():
                    try:
                        with open(results_file, 'r', encoding='utf-8') as f:
                            results_data = json.load(f)
                            if isinstance(results_data, dict) and 'results' in results_data:
                                results_list = results_data['results']
                            elif isinstance(results_data, list):
                                results_list = results_data
                            else:
                                results_list = []
                            
                            if results_list:
                                # Mettre à jour les résultats affichés
                                st.session_state.scraped_results = results_list
                                st.session_state.saved_count = len(results_list)
                    except Exception as e:
                        logger.error(f"Erreur chargement résultats: {e}")
                
                # Le statut sera récupéré frais depuis GitHub API lors du rerun
                # Ne PAS restaurer l'ancien statut - laisser get_github_workflow_status le récupérer frais
                
                # Forcer le rerun pour rafraîchir les données depuis GitHub
                st.experimental_rerun()

        with col_btn2:
            # ✅ Bouton pour télécharger les résultats - TOUJOURS visible si on a un workflow_id
            # Même si le workflow est cancelled ou failed, il peut y avoir des résultats partiels
            if run_id:
                if st.button("📥 Télécharger les résultats", key="download_progress"):
                    # ✅ Télécharger depuis l'artifact ou le fichier local
                    results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_github_actions.json"
                    results_list = []
                    
                    # Essayer d'abord le fichier local (si déjà téléchargé)
                    if results_file.exists():
                        try:
                            with open(results_file, 'r', encoding='utf-8') as f:
                                results_data = json.load(f)
                                if isinstance(results_data, dict) and 'results' in results_data:
                                    results_list = results_data['results']
                                elif isinstance(results_data, list):
                                    results_list = results_data
                        except:
                            pass
                    
                    # Si pas de fichier local et workflow terminé, télécharger l'artifact
                    if not results_list and status == 'completed' and run_id:
                        with st.spinner("📥 Téléchargement depuis GitHub..."):
                            artifact_data = download_github_artifact(github_token, github_repo, run_id)
                            if artifact_data:
                                if isinstance(artifact_data, dict) and 'results' in artifact_data:
                                    results_data = artifact_data['results']
                                    if isinstance(results_data, dict) and 'results' in results_data:
                                        results_list = results_data['results']
                                    elif isinstance(results_data, list):
                                        results_list = results_data
                    
                    if results_list:
                        # Sauvegarder automatiquement en BDD avec TOUTES les données
                        saved_count = 0
                        for info in results_list:
                            try:
                                artisan_data = {
                                    'nom_entreprise': info.get('nom', 'N/A'),
                                    'telephone': info.get('telephone', '').replace(' ', '') if info.get('telephone') else None,
                                    'adresse': info.get('adresse', ''),
                                    'code_postal': info.get('code_postal', ''),
                                    'ville': info.get('ville', ''),
                                    'ville_recherche': info.get('ville_recherche', ''),
                                    'type_artisan': info.get('recherche', metiers[0] if metiers else 'plombier'),
                                    'source': 'google_maps_github_actions'
                                }
                                
                                if info.get('site_web'):
                                    artisan_data['site_web'] = info.get('site_web')
                                
                                # ✅ Ajouter note et nombre_avis
                                if info.get('note'):
                                    artisan_data['note'] = float(info.get('note'))
                                if info.get('nb_avis') or info.get('nombre_avis'):
                                    artisan_data['nombre_avis'] = int(info.get('nb_avis') or info.get('nombre_avis', 0))
                                
                                ajouter_artisan(artisan_data)
                                saved_count += 1
                            except Exception as e:
                                if "UNIQUE constraint" not in str(e) and "duplicate" not in str(e).lower():
                                    logger.error(f"Erreur sauvegarde: {e}")
                        
                        # Mettre à jour les résultats affichés
                        st.session_state.scraped_results = results_list
                        st.session_state.saved_count = saved_count
                        
                        st.success(f"✅ {len(results_list)} résultats téléchargés et {saved_count} sauvegardés en BDD !")
                        st.experimental_rerun()
                    else:
                        st.warning("⚠️ Aucun résultat disponible pour le moment. Le scraping est peut-être encore en cours.")
        
        with col_btn3:
            # Bouton pour arrêter le workflow
            if status == 'in_progress' or status == 'queued':
                if st.button("⏹️ Arrêter", key="stop_github"):
                    try:
                        url = f"https://api.github.com/repos/{github_repo}/actions/runs/{run_id}/cancel"
                        headers = {
                            "Accept": "application/vnd.github+json",
                            "Authorization": f"Bearer {github_token}",
                            "X-GitHub-Api-Version": "2022-11-28"
                        }
                        response = requests.post(url, headers=headers)
                        if response.status_code == 202:
                            st.success("⏹️ Annulation demandée. Le workflow sera arrêté dans quelques instants.")
                            # Mettre à jour le statut localement
                            st.session_state.github_workflow_status = 'cancelled'
                            # Ne pas réinitialiser scraping_running immédiatement pour permettre de voir le statut final
                            time.sleep(1)  # Petite pause pour que l'utilisateur voie le message
                        else:
                            st.warning(f"⚠️ Erreur lors de l'annulation: {response.status_code}")
                            if response.text:
                                logger.error(f"Réponse API: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")
                        logger.error(f"Erreur annulation workflow: {e}")
                    st.experimental_rerun()
        
        # ✅ Gestion des workflows terminés (success, failure, ou cancelled)
        if status == 'completed':
            if conclusion == 'failure':
                st.error("❌ Le scraping a échoué sur GitHub Actions. Vérifiez les logs sur GitHub.")
                st.info("💡 Vous pouvez quand même essayer de télécharger les résultats partiels avec le bouton '📥 Télécharger les résultats' ci-dessus.")
            elif conclusion == 'success':
                st.success("✅ Le scraping est terminé avec succès !")
                st.info("💡 Utilisez le bouton '📥 Télécharger les résultats' ci-dessus pour récupérer les données.")
            elif conclusion == 'cancelled':
                st.warning("⏹️ Le scraping a été annulé.")
                st.info("💡 Si le scraping avait commencé, vous pouvez essayer de télécharger les résultats partiels avec le bouton '📥 Télécharger les résultats' ci-dessus.")
            
            # Bouton pour réinitialiser et permettre un nouveau lancement
            if st.button("🔄 Réinitialiser et permettre nouveau lancement", key="reset_completed"):
                st.session_state.scraping_running = False
                st.session_state.github_workflow_status = None
                st.session_state.github_workflow_id = None
                st.session_state.github_workflow_conclusion = None
                st.success("✅ État réinitialisé. Vous pouvez lancer un nouveau scraping.")
                st.experimental_rerun()
        elif not status:
            # ✅ Si on a un workflow_id mais pas de statut, c'est qu'on attend encore ou erreur API
            if st.session_state.github_workflow_id:
                st.warning("⏳ En attente du statut du workflow...")
                st.info("💡 Cliquez sur 'Rafraîchir' pour vérifier à nouveau")
                # ✅ CRITIQUE : Maintenir scraping_running pour garder le dashboard visible
                st.session_state.scraping_running = True
            else:
                st.warning("⏳ En attente du démarrage du workflow...")
                # Si on n'a pas encore de workflow_id, on peut réinitialiser
                # Mais seulement si l'utilisateur le demande explicitement

elif not should_show_dashboard:
    # ✅ Pas de dashboard à afficher - le formulaire de lancement sera affiché plus haut
    # Mais d'abord, vérifier si on doit annuler les workflows au démarrage
    # ✅ NE PAS annuler si on vient juste de lancer un workflow
    if github_token and github_repo and not st.session_state.get('workflow_just_launched', False):
        # ✅ Tuer automatiquement tous les workflows en cours au démarrage (une seule fois)
        if not st.session_state.get('workflows_cancelled_on_start', False):
            with st.spinner("⏹️ Annulation des workflows GitHub Actions en cours..."):
                success, message = cancel_all_github_workflows(github_token, github_repo)
                if success:
                    st.session_state.workflows_cancelled_on_start = True
                    # Ne pas réinitialiser scraping_running si on a un workflow_id
                    if not st.session_state.get('github_workflow_id'):
                        st.session_state.scraping_running = False
                        st.session_state.github_workflow_status = None
                        st.session_state.github_workflow_id = None
                    st.success(f"✅ {message}")
                else:
                    st.warning(f"⚠️ {message}")
            st.experimental_rerun()
    # ✅ Réinitialiser le flag après le premier rerun
    if st.session_state.get('workflow_just_launched', False):
        st.session_state.workflow_just_launched = False

# ✅ GitHub Actions uniquement - plus de code local

# Afficher les résultats scrapés
if st.session_state.scraped_results:
    st.markdown("---")
    st.subheader("📊 Résultats scrapés")
    
    df = pd.DataFrame(st.session_state.scraped_results)
    
    # Stats
    avec_tel = len(df[df['telephone'].notna()])
    avec_site = len(df[df['site_web'].notna()])
    sans_site = len(df[df['site_web'].isna()])
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    with col_res1:
        st.metric("Total scrapés", len(df))
    with col_res2:
        st.metric("Avec téléphone", f"{avec_tel} ({avec_tel/len(df)*100:.1f}%)")
    with col_res3:
        st.metric("Avec site web", f"{avec_site} ({avec_site/len(df)*100:.1f}%)")
    with col_res4:
        st.metric("⭐ SANS site web", f"{sans_site} ({sans_site/len(df)*100:.1f}%)")
    
    # Filtrer les résultats
    st.markdown("### 🔍 Filtres")
    col_filt1, col_filt2 = st.columns(2)
    
    with col_filt1:
        filtre_tel = st.checkbox("Avec téléphone uniquement", value=False)
    with col_filt2:
        filtre_sans_site = st.checkbox("Sans site web uniquement (prospects)", value=False)
    
    df_filtre = df.copy()
    if filtre_tel:
        df_filtre = df_filtre[df_filtre['telephone'].notna()]
    if filtre_sans_site:
        df_filtre = df_filtre[df_filtre['site_web'].isna()]
    
    # ✅ Afficher le tableau avec colonne ville_recherche et meilleur affichage
    colonnes_afficher = ['nom', 'telephone', 'site_web', 'adresse', 'ville_recherche', 'ville', 'note', 'nb_avis']
    colonnes_disponibles = [col for col in colonnes_afficher if col in df_filtre.columns]
    
    # CSS amélioré pour le tableau
    st.markdown("""
    <style>
    .stDataFrame {
        width: 100% !important;
    }
    .stDataFrame > div {
        width: 100% !important;
    }
    .stDataFrame table {
        width: 100% !important;
        table-layout: auto !important;
    }
    .stDataFrame th, .stDataFrame td {
        padding: 8px !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        white-space: normal !important;
    }
    .stDataFrame th:nth-child(1) { width: 15% !important; } /* Nom */
    .stDataFrame th:nth-child(2) { width: 10% !important; } /* Téléphone */
    .stDataFrame th:nth-child(3) { width: 20% !important; } /* Site web */
    .stDataFrame th:nth-child(4) { width: 20% !important; } /* Adresse */
    .stDataFrame th:nth-child(5) { width: 12% !important; } /* Ville recherchée */
    .stDataFrame th:nth-child(6) { width: 10% !important; } /* Ville */
    .stDataFrame th:nth-child(7) { width: 6% !important; } /* Note */
    .stDataFrame th:nth-child(8) { width: 7% !important; } /* Nb avis */
    </style>
    """, unsafe_allow_html=True)
    
    # ✅ Utiliser width au lieu de use_container_width (compatibilité Streamlit)
    st.dataframe(
        df_filtre[colonnes_disponibles],
        height=600
    )
    
    # ✅ Boutons d'export (gardés car utiles)
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        csv_all = df.to_csv(index=False, encoding='utf-8-sig')
        dept = st.session_state.get('departements_selected', departements)[0] if st.session_state.get('departements_selected') else (departements[0] if departements else '77')
        metier_export = st.session_state.get('metiers_selected', metiers)[0] if st.session_state.get('metiers_selected') else (metiers[0] if metiers else 'plombier')
        st.download_button(
            "📥 Télécharger CSV complet",
            csv_all,
            f"{metier_export}_{dept}_complet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )
    
    with col_exp2:
        df_avec_site = df[df['site_web'].notna()]
        if len(df_avec_site) > 0:
            csv_avec = df_avec_site.to_csv(index=False, encoding='utf-8-sig')
            dept = st.session_state.get('departements_selected', departements)[0] if st.session_state.get('departements_selected') else (departements[0] if departements else '77')
            metier_export = st.session_state.get('metiers_selected', metiers)[0] if st.session_state.get('metiers_selected') else (metiers[0] if metiers else 'plombier')
            st.download_button(
                "📥 CSV avec site web",
                csv_avec,
                f"{metier_export}_{dept}_AVEC_site_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col_exp3:
        df_sans_site = df[df['site_web'].isna()]
        if len(df_sans_site) > 0:
            csv_sans = df_sans_site.to_csv(index=False, encoding='utf-8-sig')
            dept = st.session_state.get('departements_selected', departements)[0] if st.session_state.get('departements_selected') else (departements[0] if departements else '77')
            metier_export = st.session_state.get('metiers_selected', metiers)[0] if st.session_state.get('metiers_selected') else (metiers[0] if metiers else 'plombier')
            st.download_button(
                "⭐ CSV SANS site web (PROSPECTS)",
                csv_sans,
                f"{metier_export}_{dept}_SANS_site_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
