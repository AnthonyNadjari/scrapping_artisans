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
    metier = st.selectbox(
        "Type d'artisan",
        options=["plombier", "electricien", "chauffagiste", "menuisier", "peintre", "macon", "couvreur", "carreleur"],
        help="Type d'artisan à rechercher"
    )

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
    departement = st.selectbox(
        "Département",
        options=departements_liste,
        index=departements_liste.index("77") if "77" in departements_liste else 0,
        help="Le système scrapera automatiquement plusieurs petites villes de ce département"
    )

col_config3, col_config4 = st.columns(2)

with col_config3:
    max_results = st.slider(
        "Nombre max de résultats",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="Nombre maximum d'établissements à scraper"
    )

with col_config4:
    headless = st.checkbox(
        "Mode headless (navigateur invisible)",
        value=True,
        help="Mode headless activé par défaut (plus rapide). Décochez pour voir le navigateur."
    )

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

# Boutons de contrôle
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("🚀 LANCER LE SCRAPING", disabled=st.session_state.scraping_running):
        st.session_state.scraping_running = True
        st.session_state.scraped_results = []
        st.session_state.departement_selected = departement
        st.session_state.metier_selected = metier
        st.session_state.scraping_started = False  # Réinitialiser pour permettre un nouveau lancement
        
        # Créer un nouveau scraper (réinitialiser)
        st.session_state.scraper = GoogleMapsScraper(headless=headless)
        st.session_state.scraper.is_running = True  # S'assurer qu'il est en cours
        
        # Initialiser les fichiers JSON pour la communication thread-safe
        results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_temp.json"
        status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
        
        # Vider le fichier de résultats
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        # Marquer comme en cours
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({'running': True, 'started': True}, f)
        
        st.experimental_rerun()

with col_btn2:
    if st.button("⏹️ ARRÊTER", disabled=not st.session_state.scraping_running):
        if st.session_state.scraper:
            st.session_state.scraper.stop()
        st.session_state.scraping_running = False
        
        # Marquer comme arrêté dans le fichier
        status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({'running': False, 'started': False}, f)
        except:
            pass
        
        st.success("⏹️ Scraping arrêté. Les résultats déjà scrapés sont sauvegardés.")
        st.experimental_rerun()

with col_btn3:
    if st.button("💾 SAUVEGARDER EN BDD", disabled=len(st.session_state.scraped_results) == 0):
        if st.session_state.scraped_results:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            nb_ajoutes = 0
            nb_erreurs = 0
            nb_duplicates = 0
            
            for i, resultat in enumerate(st.session_state.scraped_results):
                try:
                    # Préparer les données pour la BDD
                    artisan_data = {
                        'nom_entreprise': resultat.get('nom', 'N/A'),
                        'telephone': resultat.get('telephone', '').replace(' ', '') if resultat.get('telephone') else None,
                        'adresse': resultat.get('adresse', ''),
                        'code_postal': resultat.get('code_postal', ''),
                        'ville': resultat.get('ville', ''),
                        'type_artisan': st.session_state.get('metier_selected', metier),
                        'source': 'google_maps'
                    }
                    
                    # Ajouter site web si présent
                    if resultat.get('site_web'):
                        artisan_data['site_web'] = resultat.get('site_web')
                    
                    artisan_id = ajouter_artisan(artisan_data)
                    nb_ajoutes += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    nb_erreurs += 1
                    if "UNIQUE constraint" in error_msg or "duplicate" in error_msg.lower():
                        nb_duplicates += 1
                
                progress_bar.progress((i + 1) / len(st.session_state.scraped_results))
                status_text.info(f"💾 Sauvegarde: {i + 1}/{len(st.session_state.scraped_results)}")
            
            progress_bar.progress(1.0)
            st.success(f"✅ Sauvegarde terminée: {nb_ajoutes} ajoutés, {nb_duplicates} doublons, {nb_erreurs} erreurs")
            st.session_state.scraped_results = []
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
        logs_expander = st.expander("📋 Logs détaillés", expanded=True)
        logs_display = logs_expander.empty()
    
    # Initialiser le scraper si nécessaire
    if not st.session_state.scraper:
        st.session_state.scraper = GoogleMapsScraper(headless=headless)
    
    # S'assurer que is_running est True
    if st.session_state.scraper:
        st.session_state.scraper.is_running = True
    
    # Fonction de callback pour le progrès
    def progress_callback(index, total, info):
        progress = index / total
        progress_bar.progress(progress)
        
        nom = info.get('nom', 'N/A')
        tel = info.get('telephone', 'N/A')
        site_web = info.get('site_web', '')
        # ✅ FIX : Vérifier que c'est un vrai site web, pas l'URL Google Maps
        if site_web:
            # Si l'URL contient 'google.com' ou 'maps', ce n'est pas un vrai site web
            if 'google.com' in site_web.lower() or 'maps' in site_web.lower():
                site_web = None  # Ce n'est pas un vrai site web
                info['site_web'] = None  # Corriger dans les données
        
        site = "✅ Oui" if site_web else "❌ Non"
        site_url = site_web[:50] + "..." if site_web and len(site_web) > 50 else (site_web or "N/A")
        
        status_text.info(f"🔍 [{index}/{total}] **{nom}** | 📞 {tel} | 🌐 Site: {site}")
        
        # ✅ NOUVEAU : Logs détaillés dans Streamlit
        detail_log = f"📋 **{nom}**\n"
        detail_log += f"   📞 Téléphone: {tel}\n"
        detail_log += f"   🌐 Site web: {site_url}\n"
        if info.get('adresse'):
            detail_log += f"   📍 Adresse: {info.get('adresse', 'N/A')}\n"
        if info.get('note'):
            detail_log += f"   ⭐ Note: {info.get('note')}/5 ({info.get('nb_avis', 0)} avis)\n"
        
        logs_display.markdown(detail_log)
        
        # Stats
        avec_tel = sum(1 for r in st.session_state.scraped_results if r.get('telephone'))
        avec_site = sum(1 for r in st.session_state.scraped_results if r.get('site_web'))
        sans_site = len(st.session_state.scraped_results) - avec_site
        
        stats_text.success(
            f"📊 **{len(st.session_state.scraped_results)}** scrapés | "
            f"📞 {avec_tel} avec téléphone | "
            f"🌐 {avec_site} avec site | "
            f"⭐ {sans_site} SANS site (prospects !)"
        )
        
        # Logs
        log_line = f"[{datetime.now().strftime('%H:%M:%S')}] [{index}/{total}] {nom} | Tél: {tel} | Site: {site}"
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        st.session_state.logs.append(log_line)
        logs_display.code("\n".join(st.session_state.logs[-50:]), language=None)
    
    # Lancer le scraping dans un thread
    if 'scraping_started' not in st.session_state or not st.session_state.scraping_started:
        st.session_state.scraping_started = True
        
        # Capturer les variables AVANT le thread (closure)
        scraper_instance = st.session_state.scraper
        departement_capture = departement
        metier_capture = metier
        max_results_capture = max_results
        
        def run_scraping():
            try:
                # Utiliser les variables capturées (pas st.session_state)
                scraper = scraper_instance
                departement_actuel = departement_capture
                metier_actuel = metier_capture
                max_results_actuel = max_results_capture
                
                villes_a_scraper = villes_par_dept.get(departement_actuel, [])
                if not villes_a_scraper:
                    # Si pas de villes définies, utiliser le département comme recherche
                    villes_a_scraper = [f"{metier_actuel} {departement_actuel}"]
                
                # Utiliser un fichier JSON partagé pour stocker les résultats (thread-safe)
                import json
                results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_temp.json"
                
                # Callback qui sauvegarde progressivement dans le fichier
                def save_callback(idx, total, info):
                    if info:
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
                
                tous_resultats = []
                
                # Scraper chaque ville
                for i, ville in enumerate(villes_a_scraper, 1):
                    # Vérifier l'état via le scraper (thread-safe)
                    if not scraper.is_running:
                        logger.info("⏹️ Scraping arrêté par l'utilisateur")
                        break
                    
                    logger.info(f"🔍 Scraping ville {i}/{len(villes_a_scraper)}: {ville}")
                    try:
                        # ✅ FIX : Ne pas diviser max_results par ville, utiliser le max pour chaque ville
                        # L'utilisateur veut scraper le maximum d'établissements par ville
                        resultats = scraper.scraper(
                            recherche=metier_actuel,
                            ville=ville,
                            max_results=max_results_actuel,  # Utiliser le max pour chaque ville
                            progress_callback=save_callback
                        )
                        if resultats:
                            tous_resultats.extend(resultats)
                            logger.info(f"✅ {len(resultats)} résultats pour {ville}")
                        else:
                            logger.warning(f"⚠️ Aucun résultat pour {ville}")
                    except Exception as e:
                        logger.error(f"❌ Erreur scraping {ville}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Continuer avec la ville suivante même en cas d'erreur
                        continue
                
                # Marquer comme terminé dans le fichier
                status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump({'running': False, 'started': False}, f)
                
            except Exception as e:
                import traceback
                logger.error(f"❌ Erreur lors du scraping: {e}\n{traceback.format_exc()}")
                # Marquer comme terminé même en cas d'erreur
                status_file = Path(__file__).parent.parent.parent / "data" / "scraping_status.json"
                try:
                    with open(status_file, 'w', encoding='utf-8') as f:
                        json.dump({'running': False, 'started': False}, f)
                except:
                    pass
        
        st.session_state.scraping_thread = threading.Thread(target=run_scraping, daemon=True)
        st.session_state.scraping_thread.start()
    
    # Charger les résultats depuis le fichier JSON (thread-safe)
    results_file = Path(__file__).parent.parent.parent / "data" / "scraping_results_temp.json"
    if results_file.exists():
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results_from_file = json.load(f)
                # Mettre à jour st.session_state.scraped_results avec les nouveaux résultats
                for r in results_from_file:
                    if r not in st.session_state.scraped_results:
                        st.session_state.scraped_results.append(r)
        except:
            pass
    
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
    
    # Mettre à jour l'affichage avec les résultats actuels
    if st.session_state.scraped_results:
        avec_tel = sum(1 for r in st.session_state.scraped_results if r.get('telephone'))
        avec_site = sum(1 for r in st.session_state.scraped_results if r.get('site_web'))
        sans_site = len(st.session_state.scraped_results) - avec_site
        
        stats_text.success(
            f"📊 **{len(st.session_state.scraped_results)}** scrapés | "
            f"📞 {avec_tel} avec téléphone | "
            f"🌐 {avec_site} avec site | "
            f"⭐ {sans_site} SANS site (prospects !)"
        )
    
    # Auto-refresh pour mettre à jour l'interface (seulement si scraping en cours)
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
    
    # Afficher le tableau avec CSS pour prendre toute la largeur et ajuster les colonnes
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
        table-layout: fixed !important;
    }
    .stDataFrame th {
        background-color: #f0f2f6 !important;
        font-weight: bold !important;
        padding: 8px !important;
    }
    .stDataFrame td {
        padding: 8px !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    .stDataFrame th:nth-child(1), .stDataFrame td:nth-child(1) { width: 20% !important; }
    .stDataFrame th:nth-child(2), .stDataFrame td:nth-child(2) { width: 12% !important; }
    .stDataFrame th:nth-child(3), .stDataFrame td:nth-child(3) { width: 20% !important; }
    .stDataFrame th:nth-child(4), .stDataFrame td:nth-child(4) { width: 20% !important; }
    .stDataFrame th:nth-child(5), .stDataFrame td:nth-child(5) { width: 10% !important; }
    .stDataFrame th:nth-child(6), .stDataFrame td:nth-child(6) { width: 8% !important; }
    .stDataFrame th:nth-child(7), .stDataFrame td:nth-child(7) { width: 10% !important; }
    </style>
    """, unsafe_allow_html=True)
    st.dataframe(
        df_filtre[['nom', 'telephone', 'site_web', 'adresse', 'ville', 'note', 'nb_avis']],
        height=400
    )
    
    # Boutons d'export
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        csv_all = df.to_csv(index=False, encoding='utf-8-sig')
        dept = st.session_state.get('departement_selected', departement)
        metier_export = st.session_state.get('metier_selected', metier)
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
            dept = st.session_state.get('departement_selected', departement)
            metier_export = st.session_state.get('metier_selected', metier)
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
            dept = st.session_state.get('departement_selected', departement)
            metier_export = st.session_state.get('metier_selected', metier)
            st.download_button(
                "⭐ CSV SANS site web (PROSPECTS)",
                csv_sans,
                f"{metier_export}_{dept}_SANS_site_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

