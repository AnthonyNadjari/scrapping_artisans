"""
Page Scraping - Google Maps
Extraction des artisans depuis Google Maps
"""
import streamlit as st
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration de la page
st.set_page_config(page_title="Scraping Google Maps", page_icon="🔍", layout="wide")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.google_maps_scraper import GoogleMapsScraper
from whatsapp_database.queries import ajouter_artisan, get_statistiques
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
            help="Permet de reprendre le scraping où il s'est arrêté"
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

# Boutons de contrôle
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🚀 LANCER LE SCRAPING", disabled=st.session_state.scraping_running):
        if not metiers or not departements:
            st.error("⚠️ Veuillez sélectionner au moins un métier et un département")
        else:
            st.session_state.scraping_running = True
            st.session_state.scraped_results = []
            st.session_state.saved_count = 0
            st.session_state.logs_buffer = []
            st.session_state.departements_selected = departements
            st.session_state.metiers_selected = metiers
            st.session_state.scraping_started = False
            
            # Créer un nouveau scraper
            st.session_state.scraper = GoogleMapsScraper(headless=headless)
            st.session_state.scraper.is_running = True
            
            # Initialiser les fichiers JSON
            results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_temp.json"
            status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
            logs_file = Path(__file__).parent.parent.parent / "data" / "scraping_logs.json"
            checkpoint_file = Path(__file__).parent.parent.parent / "data" / "scraping_checkpoint.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({'running': True, 'started': True}, f)
            
            with open(logs_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            if not enable_resume:
                # Supprimer le checkpoint si resume désactivé
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
            
            st.experimental_rerun()

with col_btn2:
    if st.button("⏹️ ARRÊTER", disabled=not st.session_state.scraping_running):
        if st.session_state.scraper:
            st.session_state.scraper.stop()
        st.session_state.scraping_running = False
        
        status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({'running': False, 'started': False}, f)
        except:
            pass
        
        st.success("⏹️ Scraping arrêté. Les résultats déjà scrapés sont sauvegardés.")
        st.experimental_rerun()

st.markdown("---")

# Zone de scraping
if st.session_state.scraping_running:
    st.subheader("🔄 Scraping en cours...")
    
    progress_container = st.container()
    logs_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_text = st.empty()
    
    with logs_container:
        logs_expander = st.expander("📋 Logs en temps réel", expanded=True)
        logs_display = logs_expander.empty()
    
    # Initialiser le scraper si nécessaire
    if not st.session_state.scraper:
        st.session_state.scraper = GoogleMapsScraper(headless=headless)
    
    if st.session_state.scraper:
        st.session_state.scraper.is_running = True
    
    # ✅ Fonction de sauvegarde automatique en BDD
    def save_to_db_auto(info, metier_actuel):
        """Sauvegarde automatique en BDD"""
        try:
            artisan_data = {
                'nom_entreprise': info.get('nom', 'N/A'),
                'telephone': info.get('telephone', '').replace(' ', '') if info.get('telephone') else None,
                'adresse': info.get('adresse', ''),
                'code_postal': info.get('code_postal', ''),
                'ville': info.get('ville', ''),
                'type_artisan': metier_actuel,
                'source': 'google_maps'
            }
            
            if info.get('site_web'):
                artisan_data['site_web'] = info.get('site_web')
            
            ajouter_artisan(artisan_data)
            return True
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint" not in error_msg and "duplicate" not in error_msg.lower():
                logger.error(f"Erreur sauvegarde auto: {e}")
            return False
    
    # Lancer le scraping dans un thread
    if 'scraping_started' not in st.session_state or not st.session_state.scraping_started:
        st.session_state.scraping_started = True
        
        scraper_instance = st.session_state.scraper
        departements_capture = st.session_state.departements_selected
        metiers_capture = st.session_state.metiers_selected
        max_results_capture = max_results
        use_api_capture = use_api_communes
        min_pop_capture = min_pop if use_api_communes else 0
        max_pop_capture = max_pop if use_api_communes else 50000
        num_threads_capture = num_threads
        enable_resume_capture = enable_resume
        
        def run_scraping():
            try:
                max_results_actuel = max_results_capture
                results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_temp.json"
                logs_file = Path(__file__).parent.parent.parent / "data" / "scraping_logs.json"
                checkpoint_file = Path(__file__).parent.parent.parent / "data" / "scraping_checkpoint.json"
                
                # ✅ Charger le checkpoint si resume activé
                checkpoint_data = {}
                if enable_resume_capture and checkpoint_file.exists():
                    try:
                        with open(checkpoint_file, 'r', encoding='utf-8') as f:
                            checkpoint_data = json.load(f)
                        logger.info(f"📂 Checkpoint chargé: {checkpoint_data}")
                    except:
                        checkpoint_data = {}
                
                # ✅ Fonction pour ajouter un log
                def add_log(message):
                    try:
                        if logs_file.exists():
                            with open(logs_file, 'r', encoding='utf-8') as f:
                                logs = json.load(f)
                        else:
                            logs = []
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'message': message
                        })
                        # Garder seulement les 100 derniers logs
                        logs = logs[-100:]
                        with open(logs_file, 'w', encoding='utf-8') as f:
                            json.dump(logs, f, ensure_ascii=False, indent=2)
                    except:
                        pass
                
                # ✅ Callback amélioré avec sauvegarde automatique et logs
                def save_callback(idx, total, info):
                    if info:
                        # S'assurer que ville_recherche est présent
                        if 'ville_recherche' not in info:
                            info['ville_recherche'] = info.get('ville_recherche', '')
                        
                        # Lire les résultats existants
                        if results_file.exists():
                            try:
                                with open(results_file, 'r', encoding='utf-8') as f:
                                    existing_results = json.load(f)
                            except:
                                existing_results = []
                        else:
                            existing_results = []
                        
                        # Ajouter le nouveau résultat s'il n'existe pas déjà
                        if info not in existing_results:
                            existing_results.append(info)
                            with open(results_file, 'w', encoding='utf-8') as f:
                                json.dump(existing_results, f, ensure_ascii=False, indent=2)
                            
                            # ✅ Sauvegarde automatique en BDD
                            ville_recherche = info.get('ville_recherche', '')
                            metier_actuel = metiers_capture[0] if metiers_capture else "plombier"
                            if save_to_db_auto(info, metier_actuel):
                                # Compter les sauvegardes
                                saved_file = Path(__file__).parent.parent.parent / "data" / "saved_count.json"
                                try:
                                    if saved_file.exists():
                                        with open(saved_file, 'r') as f:
                                            count_data = json.load(f)
                                            count = count_data.get('count', 0)
                                    else:
                                        count = 0
                                    count += 1
                                    with open(saved_file, 'w') as f:
                                        json.dump({'count': count}, f)
                                except:
                                    pass
                            
                            # ✅ Ajouter un log
                            nom = info.get('nom', 'N/A')
                            tel = info.get('telephone', 'N/A')
                            site = "Oui" if info.get('site_web') else "Non"
                            add_log(f"[{idx}/{total}] {nom} | 📞 {tel} | 🌐 {site} | 📍 {ville_recherche}")
                
                tous_resultats = []
                
                # ✅ Préparer la liste des villes à scraper
                toutes_villes = []
                for dept in departements_capture:
                    if use_api_capture:
                        # Utiliser l'API data.gouv.fr
                        communes = get_communes_from_api(dept, min_pop_capture, max_pop_capture)
                        villes_dept = [c['nom'] for c in communes]
                        add_log(f"📡 API: {len(villes_dept)} communes trouvées pour {dept}")
                    else:
                        # Utiliser le fichier JSON
                        villes_dept = villes_par_dept.get(dept, [])
                        if not villes_dept:
                            villes_dept = [f"{metiers_capture[0]} {dept}"]
                    
                    for metier_actuel in metiers_capture:
                        for ville in villes_dept:
                            # ✅ Vérifier le checkpoint
                            task_key = f"{metier_actuel}_{dept}_{ville}"
                            if enable_resume_capture and checkpoint_data.get(task_key, {}).get('completed', False):
                                add_log(f"⏭️  Checkpoint: {task_key} déjà fait, on passe")
                                continue
                            toutes_villes.append({
                                'metier': metier_actuel,
                                'departement': dept,
                                'ville': ville
                            })
                
                add_log(f"🚀 Démarrage: {len(toutes_villes)} tâches à exécuter")
                
                # ✅ Fonction pour scraper une ville
                def scrape_ville(task_info):
                    metier_actuel = task_info['metier']
                    dept_actuel = task_info['departement']
                    ville_actuelle = task_info['ville']
                    task_key = f"{metier_actuel}_{dept_actuel}_{ville_actuelle}"
                    
                    try:
                        # Créer un scraper pour ce thread
                        scraper = GoogleMapsScraper(headless=headless)
                        scraper.is_running = True
                        
                        add_log(f"🔍 [{threading.current_thread().name}] {metier_actuel} - {dept_actuel} - {ville_actuelle}")
                        
                        resultats = scraper.scraper(
                            recherche=metier_actuel,
                            ville=ville_actuelle,
                            max_results=max_results_actuel,
                            progress_callback=save_callback
                        )
                        
                        # ✅ Sauvegarder le checkpoint
                        if enable_resume_capture:
                            try:
                                if checkpoint_file.exists():
                                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                                        checkpoint = json.load(f)
                                else:
                                    checkpoint = {}
                                checkpoint[task_key] = {
                                    'completed': True,
                                    'timestamp': datetime.now().isoformat(),
                                    'results_count': len(resultats) if resultats else 0
                                }
                                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                                    json.dump(checkpoint, f, ensure_ascii=False, indent=2)
                            except:
                                pass
                        
                        # Fermer le scraper
                        scraper.quit()
                        
                        if resultats:
                            for r in resultats:
                                r['ville_recherche'] = ville_actuelle
                            add_log(f"✅ [{threading.current_thread().name}] {len(resultats)} résultats pour {ville_actuelle}")
                            return resultats
                        else:
                            add_log(f"⚠️ [{threading.current_thread().name}] Aucun résultat pour {ville_actuelle}")
                            return []
                    except Exception as e:
                        add_log(f"❌ [{threading.current_thread().name}] Erreur {ville_actuelle}: {str(e)[:100]}")
                        return []
                
                # ✅ Multi-threading
                if num_threads_capture > 1:
                    add_log(f"🚀 Multi-threading activé ({num_threads_capture} threads)")
                    with ThreadPoolExecutor(max_workers=num_threads_capture) as executor:
                        futures = {executor.submit(scrape_ville, task): task for task in toutes_villes}
                        for future in as_completed(futures):
                            if not scraper_instance.is_running:
                                break
                            try:
                                resultats = future.result()
                                if resultats:
                                    tous_resultats.extend(resultats)
                            except Exception as e:
                                add_log(f"❌ Erreur thread: {str(e)[:100]}")
                else:
                    # Mode séquentiel
                    for task in toutes_villes:
                        if not scraper_instance.is_running:
                            break
                        resultats = scrape_ville(task)
                        if resultats:
                            tous_resultats.extend(resultats)
                
                add_log(f"✅ Scraping terminé: {len(tous_resultats)} résultats au total")
                
                # Marquer comme terminé
                status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump({'running': False, 'started': False}, f)
                
            except Exception as e:
                import traceback
                logger.error(f"❌ Erreur lors du scraping: {e}\n{traceback.format_exc()}")
                add_log(f"❌ Erreur fatale: {str(e)[:200]}")
                status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
                try:
                    with open(status_file, 'w', encoding='utf-8') as f:
                        json.dump({'running': False, 'started': False}, f)
                except:
                    pass
        
        st.session_state.scraping_thread = threading.Thread(target=run_scraping, daemon=True)
        st.session_state.scraping_thread.start()
    
    # ✅ Charger les résultats depuis le fichier JSON
    results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_temp.json"
    if results_file.exists():
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results_from_file = json.load(f)
                for r in results_from_file:
                    if r not in st.session_state.scraped_results:
                        st.session_state.scraped_results.append(r)
        except:
            pass
    
    # ✅ Charger et afficher les logs en temps réel
    logs_file = Path(__file__).parent.parent.parent / "data" / "scraping_logs.json"
    try:
        if logs_file.exists():
            with open(logs_file, 'r', encoding='utf-8') as f:
                logs_data = json.load(f)
                # Afficher les 50 derniers logs
                recent_logs = logs_data[-50:] if len(logs_data) > 50 else logs_data
                if recent_logs:
                    logs_html = "<div style='font-family: monospace; font-size: 0.85em; max-height: 500px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;'>"
                    for log_entry in recent_logs:
                        timestamp = log_entry.get('timestamp', '')
                        message = log_entry.get('message', '')
                        # Formater le timestamp
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            time_str = dt.strftime('%H:%M:%S')
                        except:
                            time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
                        logs_html += f"<div style='margin: 3px 0; padding: 6px; border-left: 3px solid #007bff; padding-left: 10px; background: white; border-radius: 3px;'><span style='color: #6c757d; font-weight: bold;'>{time_str}</span> <span style='color: #212529;'>{message}</span></div>"
                    logs_html += "</div>"
                    logs_display.markdown(logs_html, unsafe_allow_html=True)
                else:
                    logs_display.info("⏳ En attente des premiers logs...")
        else:
            logs_display.info("⏳ En attente des premiers logs...")
    except Exception as e:
        logs_display.error(f"Erreur chargement logs: {e}")
    
    # Charger le compteur de sauvegardes
    saved_file = Path(__file__).parent.parent.parent / "data" / "saved_count.json"
    if saved_file.exists():
        try:
            with open(saved_file, 'r') as f:
                count_data = json.load(f)
                st.session_state.saved_count = count_data.get('count', 0)
        except:
            st.session_state.saved_count = 0
    
    # Vérifier l'état depuis le fichier JSON
    status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
    if status_file.exists():
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                if not status_data.get('running', True):
                    st.session_state.scraping_running = False
                    st.session_state.scraping_started = False
        except:
            pass
    
    # Mettre à jour l'affichage
    if st.session_state.scraped_results:
        avec_tel = sum(1 for r in st.session_state.scraped_results if r.get('telephone'))
        avec_site = sum(1 for r in st.session_state.scraped_results if r.get('site_web'))
        sans_site = len(st.session_state.scraped_results) - avec_site
        
        stats_text.success(
            f"📊 **{len(st.session_state.scraped_results)}** scrapés | "
            f"📞 {avec_tel} avec téléphone | "
            f"🌐 {avec_site} avec site | "
            f"⭐ {sans_site} SANS site (prospects !) | "
            f"💾 {st.session_state.saved_count} sauvegardés"
        )
    
    # Auto-refresh
    if st.session_state.scraping_running:
        time.sleep(2)
        st.experimental_rerun()

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
        dept = st.session_state.get('departements_selected', [departement])[0] if st.session_state.get('departements_selected') else departement
        metier_export = st.session_state.get('metiers_selected', [metier])[0] if st.session_state.get('metiers_selected') else metier
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
            dept = st.session_state.get('departements_selected', [departement])[0] if st.session_state.get('departements_selected') else departement
            metier_export = st.session_state.get('metiers_selected', [metier])[0] if st.session_state.get('metiers_selected') else metier
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
            dept = st.session_state.get('departements_selected', [departement])[0] if st.session_state.get('departements_selected') else departement
            metier_export = st.session_state.get('metiers_selected', [metier])[0] if st.session_state.get('metiers_selected') else metier
            st.download_button(
                "⭐ CSV SANS site web (PROSPECTS)",
                csv_sans,
                f"{metier_export}_{dept}_SANS_site_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
