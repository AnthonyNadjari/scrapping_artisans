#!/usr/bin/env python3
"""
Script pour exécuter le scraping depuis GitHub Actions
Avec commits périodiques pour sauvegarder les résultats même en cas de timeout
"""
import json
import sys
import os
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.google_maps_scraper import GoogleMapsScraper
import requests
from whatsapp_database.queries import ajouter_artisan, mark_scraping_done
from whatsapp_database.models import init_database

# Variable globale pour contrôler le thread de commit périodique
stop_periodic_commit = threading.Event()
last_commit_count = 0


def git_commit_and_push(message: str) -> bool:
    """Commit et push les résultats vers GitHub"""
    try:
        # Vérifier si on est dans un environnement GitHub Actions
        if not os.environ.get('GITHUB_TOKEN'):
            print("⚠️ Pas de GITHUB_TOKEN, commit ignoré")
            return False

        results_file = Path('data/scraping_results_github_actions.json')
        status_file = Path('data/github_actions_status.json')

        if not results_file.exists():
            print("⚠️ Pas de fichier de résultats à commiter")
            return False

        # ✅ Vérifier que le fichier contient des données
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total = data.get('total_results', 0)
                print(f"📄 Fichier de résultats: {total} résultats")
        except Exception as e:
            print(f"⚠️ Erreur lecture fichier: {e}")

        # ✅ Pull avant push pour éviter les conflits
        print("🔄 git pull --rebase...")
        pull_result = subprocess.run(
            ['git', 'pull', '--rebase', 'origin', 'main'],
            capture_output=True, text=True, check=False
        )
        if pull_result.returncode != 0:
            print(f"⚠️ git pull: {pull_result.stderr}")
            # Continuer quand même

        # Ajouter les fichiers
        print("📁 git add...")
        add_result = subprocess.run(['git', 'add', str(results_file), str(status_file)],
                      capture_output=True, text=True, check=False)
        if add_result.returncode != 0:
            print(f"⚠️ git add stderr: {add_result.stderr}")

        # Vérifier s'il y a des changements à commiter
        result = subprocess.run(['git', 'status', '--porcelain'],
                               capture_output=True, text=True, check=False)
        print(f"📋 git status: '{result.stdout.strip()}'")
        if not result.stdout.strip():
            print("ℹ️ Aucun changement à commiter")
            return True

        # Commit
        print(f"💾 git commit -m '{message[:50]}...'")
        commit_result = subprocess.run(
            ['git', 'commit', '-m', message],
            capture_output=True, text=True, check=False
        )

        if commit_result.returncode != 0:
            print(f"⚠️ Erreur commit (code {commit_result.returncode})")
            print(f"   stdout: {commit_result.stdout}")
            print(f"   stderr: {commit_result.stderr}")
            return False
        else:
            print(f"✅ Commit OK: {commit_result.stdout.strip()}")

        # Push
        print("🚀 git push...")
        push_result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            capture_output=True, text=True, check=False
        )

        if push_result.returncode != 0:
            print(f"⚠️ Erreur push (code {push_result.returncode})")
            print(f"   stdout: {push_result.stdout}")
            print(f"   stderr: {push_result.stderr}")
            return False
        else:
            print(f"✅ Push OK: {push_result.stdout.strip()}")

        print(f"✅ Commit et push réussis: {message}")
        return True

    except Exception as e:
        print(f"❌ Erreur git: {e}")
        import traceback
        traceback.print_exc()
        return False


def periodic_commit_thread(interval_minutes: int = 10):
    """Thread qui fait des commits périodiques des résultats"""
    global last_commit_count

    interval_seconds = interval_minutes * 60
    print(f"🔄 Thread de commit périodique démarré (intervalle: {interval_minutes} min)")

    # ✅ FIX: Attendre un peu avant le premier check (30 secondes) pour laisser le scraping démarrer
    # puis vérifier régulièrement
    first_check_delay = 30  # Première vérification après 30 secondes

    # Premier délai court
    if stop_periodic_commit.wait(first_check_delay):
        print("🔄 Thread de commit périodique arrêté (avant premier check)")
        return

    while True:
        try:
            # Lire le nombre actuel de résultats
            results_file = Path('data/scraping_results_github_actions.json')
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    current_count = data.get('total_results', 0)

                # Ne commiter que s'il y a de nouveaux résultats
                if current_count > last_commit_count:
                    new_results = current_count - last_commit_count
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message = f"🤖 Auto-save: {current_count} résultats (+{new_results}) - {timestamp}"

                    print(f"🔄 Tentative de commit: {current_count} résultats...")
                    if git_commit_and_push(message):
                        last_commit_count = current_count
                        print(f"💾 Commit périodique réussi: {current_count} résultats sauvegardés")
                    else:
                        print(f"⚠️ Échec du commit périodique (voir logs ci-dessus)")
                else:
                    print(f"ℹ️ Pas de nouveaux résultats depuis le dernier commit ({current_count} total)")
            else:
                print(f"⏳ Fichier de résultats pas encore créé...")
        except Exception as e:
            print(f"❌ Erreur dans le thread de commit: {e}")
            import traceback
            traceback.print_exc()

        # Attendre l'intervalle ou arrêt
        if stop_periodic_commit.wait(interval_seconds):
            break

    print("🔄 Thread de commit périodique arrêté")


def get_communes_from_api(dept, min_pop, max_pop):
    """Récupère les communes d'un département depuis l'API data.gouv.fr"""
    try:
        url = f"https://geo.api.gouv.fr/departements/{dept}/communes"
        params = {
            "fields": "nom,code,codesPostaux,population,centre",
            "format": "json"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            communes = response.json()
            filtered = []
            for c in communes:
                pop = c.get('population', 0)
                if min_pop <= pop <= max_pop:
                    centre = c.get('centre', {})
                    filtered.append({
                        'nom': c['nom'],
                        'code_postal': c.get('codesPostaux', [c.get('code', '')])[0] if c.get('codesPostaux') else c.get('code', ''),
                        'population': pop,
                        'latitude': centre.get('coordinates', [None, None])[1] if centre else None,
                        'longitude': centre.get('coordinates', [None, None])[0] if centre else None
                    })
            filtered.sort(key=lambda x: x['population'])
            return filtered
    except Exception as e:
        print(f"Erreur API communes: {e}")
    return []

def save_callback(artisan_data):
    """Callback pour sauvegarder directement dans la BDD à chaque établissement trouvé"""
    try:
        # Vérifier que artisan_data contient au moins une donnée valide
        if not artisan_data:
            print("⚠️ save_callback: artisan_data est None ou vide")
            return None
        
        # Préparer les données pour la BDD
        # ✅ FIX : Utiliser 'nom_entreprise' au lieu de 'nom' pour correspondre au schéma de la BDD
        import re
        
        # ✅ NETTOYER l'adresse : enlever "Closed", "Fermé", sauts de ligne, etc.
        adresse_brute = artisan_data.get('adresse', '')
        if adresse_brute:
            adresse_clean = re.sub(r'\s*(Closed|Closes|Closes soon|Fermé|Fermée|Ouvert|Open|Opens|Opening|Soon)\s*', '', str(adresse_brute), flags=re.IGNORECASE)
            adresse_clean = re.sub(r'\s*\n\s*', ' ', adresse_clean)  # Remplacer sauts de ligne par espaces
            adresse_clean = re.sub(r'\s+', ' ', adresse_clean).strip()  # Normaliser les espaces
        else:
            adresse_clean = ''
        
        # ✅ Stocker le département de recherche pour référence (mais ne pas l'utiliser comme département réel)
        departement_recherche = artisan_data.get('departement_recherche') or artisan_data.get('departement')

        data = {
            'nom_entreprise': artisan_data.get('nom'),  # ✅ FIX : nom_entreprise au lieu de nom
            'telephone': artisan_data.get('telephone'),
            'site_web': artisan_data.get('site_web'),
            'google_maps_url': artisan_data.get('google_maps_url'),  # URL directe vers la fiche Google Maps
            'adresse': adresse_clean,  # ✅ Adresse nettoyée
            'code_postal': artisan_data.get('code_postal'),
            'ville': artisan_data.get('ville'),
            'departement': None,  # ✅ FIX: Sera dérivé du code_postal, pas du département recherché
            'note': artisan_data.get('note'),
            'nombre_avis': artisan_data.get('nb_avis') or artisan_data.get('nombre_avis'),  # ✅ Support des deux formats
            'ville_recherche': artisan_data.get('ville_recherche'),
            'departement_recherche': departement_recherche,  # ✅ Garder trace du département de recherche
            'source': 'google_maps',
            'source_telephone': 'google_maps',
            'type_artisan': artisan_data.get('recherche') or artisan_data.get('type_artisan')  # ✅ Support des deux formats
        }

        # ✅ PRIORITÉ 1: Extraire le code postal depuis l'adresse si manquant
        if not data.get('code_postal') and data.get('adresse'):
            cp_match = re.search(r'\b(\d{5})\b', data['adresse'])
            if cp_match:
                data['code_postal'] = cp_match.group(1)

        # ✅ PRIORITÉ 2: Extraire le département depuis le code postal (la source la plus fiable)
        if data.get('code_postal'):
            code_postal = str(data['code_postal']).strip()
            # Valider que c'est un code postal français valide (5 chiffres)
            if re.match(r'^\d{5}$', code_postal):
                # Pour les départements d'outre-mer (97x, 98x), prendre les 3 premiers chiffres
                if code_postal.startswith('97') or code_postal.startswith('98'):
                    data['departement'] = code_postal[:3]
                else:
                    data['departement'] = code_postal[:2]

        # ✅ FALLBACK: Utiliser le département recherché seulement si on n'a pas pu l'extraire du CP
        if not data.get('departement') and departement_recherche:
            data['departement'] = departement_recherche
        
        # ✅ Extraire la ville depuis l'adresse si manquante (amélioré)
        if not data.get('ville') and data.get('adresse'):
            adresse = str(data['adresse'])
            # Pattern 1: "code_postal ville" (format français standard)
            ville_match = re.search(r'\b\d{5}\s+([A-Za-zÀ-ÿ\s-]+?)(?:\s|$|,|;|France|Closed|Fermé)', adresse, re.IGNORECASE)
            if ville_match:
                ville = ville_match.group(1).strip()
                # Nettoyer la ville (enlever "France", "Closed", etc.)
                ville = re.sub(r'\s*(France|FR|FRANCE|Closed|Fermé|Fermée)\s*$', '', ville, flags=re.IGNORECASE).strip()
                # ✅ Vérifier que ce n'est pas un nom d'entreprise
                mots_interdits = ['rue', 'avenue', 'boulevard', 'place', 'allée', 'chemin', 'route', 
                                 'plomberie', 'solution', 'eaux', 'cernoise', 'services', 'entreprise']
                if ville and ville.lower() not in mots_interdits and not any(mot in ville.lower() for mot in ['plombier', 'plomberie', 'solution']):
                    data['ville'] = ville
            # Pattern 2: Si pas trouvé, chercher après le dernier chiffre
            if not data.get('ville'):
                ville_match2 = re.search(r'\d{5}\s+(.+?)(?:\s*$|,|;|France|Closed|Fermé)', adresse)
                if ville_match2:
                    ville = ville_match2.group(1).strip()
                    ville = re.sub(r'\s*(France|FR|FRANCE|Closed|Fermé|Fermée)\s*$', '', ville, flags=re.IGNORECASE).strip()
                    # ✅ Vérifier que ce n'est pas un nom d'entreprise
                    mots_interdits = ['rue', 'avenue', 'boulevard', 'place', 'allée', 'chemin', 'route', 
                                     'plomberie', 'solution', 'eaux', 'cernoise', 'services', 'entreprise']
                    if ville and ville.lower() not in mots_interdits and not any(mot in ville.lower() for mot in ['plombier', 'plomberie', 'solution']):
                        data['ville'] = ville
        
        # ✅ Si toujours pas de ville, utiliser ville_recherche (PRIORITÉ)
        if not data.get('ville'):
            ville_recherche = artisan_data.get('ville_recherche') or artisan_data.get('ville')
            if ville_recherche:
                data['ville'] = ville_recherche
                data['ville_recherche'] = ville_recherche
        
        # ✅ FALLBACK : Si on a la ville mais pas le code postal, chercher via l'API data.gouv.fr
        if not data.get('code_postal') and data.get('ville'):
            try:
                ville_nom = data['ville']
                # Chercher le code postal via l'API
                url = f"https://geo.api.gouv.fr/communes?nom={ville_nom}&fields=nom,code,codesPostaux"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    communes = response.json()
                    if communes:
                        # Prendre la première commune trouvée
                        codes_postaux = communes[0].get('codesPostaux', [])
                        if codes_postaux:
                            data['code_postal'] = codes_postaux[0]
                            # Extraire le département
                            if len(data['code_postal']) >= 2:
                                if data['code_postal'].startswith('97') or data['code_postal'].startswith('98'):
                                    data['departement'] = data['code_postal'][:3]
                                else:
                                    data['departement'] = data['code_postal'][:2]
            except Exception as e:
                # Silencieux - ne pas bloquer si l'API échoue
                pass
        
        # ✅ VALIDATION : Note et nombre d'avis doivent être cohérents
        if data.get('note') is not None and data.get('nombre_avis') is None:
            data['nombre_avis'] = 0
        
        # ✅ Vérifier qu'on a au moins une donnée valide avant d'insérer
        has_valid_data = any([
            data.get('nom_entreprise'),
            data.get('telephone'),
            data.get('site_web'),
            data.get('adresse')
        ])
        
        if not has_valid_data:
            print(f"⚠️ save_callback: Aucune donnée valide pour sauvegarder. Données reçues: {artisan_data}")
            return None
        
        # Sauvegarder dans la BDD
        artisan_id = ajouter_artisan(data)
        if artisan_id:
            print(f"✅ Artisan sauvegardé (ID: {artisan_id})")
        else:
            print(f"⚠️ save_callback: ajouter_artisan a retourné None pour: {data.get('nom_entreprise', 'N/A')}")
        return artisan_id
    except ValueError as e:
        # Erreur de validation (pas de données valides)
        print(f"⚠️ Erreur validation artisan: {e} - Données: {artisan_data}")
        return None
    except Exception as e:
        print(f"❌ Erreur sauvegarde artisan: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def scrape_ville(task_info, max_results, status_file):
    """Scrape une ville et met à jour le statut"""
    metier_actuel = task_info['metier']
    ville_actuelle = task_info['ville']
    departement_actuel = task_info['departement']
    
    # ✅ Vérifier si déjà scrapé (optionnel - peut être désactivé pour re-scraping)
    # if is_already_scraped(metier_actuel, departement_actuel, ville_actuelle):
    #     print(f"⏭️ {metier_actuel} - {departement_actuel} - {ville_actuelle} déjà scrapé, ignoré")
    #     update_status_file(status_file, task_info, 0, 'skipped')
    #     return []
    
    try:
        scraper = GoogleMapsScraper(headless=True)
        scraper.is_running = True
        
        # ✅ Callback pour sauvegarder directement dans la BDD ET dans le fichier JSON
        # Définir le chemin du fichier une seule fois
        results_file = Path('data') / 'scraping_results_github_actions.json'
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        def progress_callback(index, total, info):
            if info:
                info['ville_recherche'] = ville_actuelle
                info['recherche'] = metier_actuel
                info['departement_recherche'] = departement_actuel  # ✅ Stocker le département recherché séparément
                # Ne pas écraser le département extrait depuis le code postal, mais utiliser le département recherché en priorité
                if not info.get('departement'):
                    info['departement'] = departement_actuel
                # Sauvegarder dans la BDD
                save_callback(info)
                # ✅ Sauvegarder aussi dans le fichier JSON progressivement (à chaque établissement)
                try:
                    save_progress(results_file, [info])
                except Exception as e:
                    print(f"⚠️ Erreur sauvegarde JSON progressive: {e}")
        
        resultats = scraper.scraper(
            recherche=metier_actuel,
            ville=ville_actuelle,
            max_results=max_results,
            progress_callback=progress_callback
        )
        scraper.quit()
        
        # ✅ Marquer comme scrapé dans l'historique
        mark_scraping_done(metier_actuel, departement_actuel, ville_actuelle, len(resultats) if resultats else 0)
        
        # ✅ Mettre à jour le statut après chaque ville
        update_status_file(status_file, task_info, len(resultats) if resultats else 0, 'completed')
        
        return resultats or []
    except Exception as e:
        print(f"❌ Erreur {ville_actuelle}: {e}")
        update_status_file(status_file, task_info, 0, 'failed', str(e))
        return []

def update_status_file(status_file, task_info, results_count, status, error=None):
    """Met à jour le fichier de statut"""
    try:
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
        else:
            status_data = {
                'started_at': datetime.now().isoformat(),
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'total_results': 0,
                'tasks': {}
            }
        
        task_key = f"{task_info['metier']}_{task_info['departement']}_{task_info['ville']}"
        status_data['tasks'][task_key] = {
            'status': status,
            'results_count': results_count,
            'completed_at': datetime.now().isoformat(),
            'error': error
        }
        
        # Mettre à jour les compteurs
        status_data['completed_tasks'] = sum(1 for t in status_data['tasks'].values() if t['status'] == 'completed')
        status_data['failed_tasks'] = sum(1 for t in status_data['tasks'].values() if t['status'] == 'failed')
        status_data['total_results'] = sum(t['results_count'] for t in status_data['tasks'].values())
        status_data['last_updated'] = datetime.now().isoformat()
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        # ✅ Logger la progression pour visibilité dans les logs GitHub
        if status_data['total_tasks'] > 0:
            progress_pct = (status_data['completed_tasks'] / status_data['total_tasks'] * 100)
            print(f"📊 Progression: {status_data['completed_tasks']}/{status_data['total_tasks']} villes ({progress_pct:.1f}%) | {status_data['total_results']} résultats trouvés")
    except Exception as e:
        print(f"⚠️ Erreur mise à jour statut: {e}")

def save_progress(results_file, new_results):
    """Sauvegarde les résultats progressivement"""
    try:
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                'timestamp': datetime.now().isoformat(),
                'total_results': 0,
                'results': []
            }
        
        # Ajouter les nouveaux résultats (éviter les doublons)
        existing_ids = {f"{r.get('nom', '')}_{r.get('telephone', '')}_{r.get('ville_recherche', '')}" for r in data['results']}
        for r in new_results:
            r_id = f"{r.get('nom', '')}_{r.get('telephone', '')}_{r.get('ville_recherche', '')}"
            if r_id not in existing_ids:
                data['results'].append(r)
        
        data['total_results'] = len(data['results'])
        data['last_updated'] = datetime.now().isoformat()
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde progressive: {e}")

if __name__ == "__main__":
    # ✅ Initialiser la base de données
    init_database()

    # Récupérer les paramètres depuis les variables d'environnement
    metiers = json.loads(os.environ.get('METIERS', '[]'))
    departements = json.loads(os.environ.get('DEPARTEMENTS', '[]'))
    max_results = int(os.environ.get('MAX_RESULTS', '50'))
    num_threads = int(os.environ.get('NUM_THREADS', '3'))
    use_api_communes = os.environ.get('USE_API_COMMUNES', 'false').lower() == 'true'
    min_pop = int(os.environ.get('MIN_POP', '0'))
    max_pop = int(os.environ.get('MAX_POP', '50000'))

    # Paramètres de commit périodique
    enable_periodic_commits = os.environ.get('ENABLE_PERIODIC_COMMITS', 'false').lower() == 'true'
    commit_interval = int(os.environ.get('COMMIT_INTERVAL_MINUTES', '10'))

    print(f'🚀 Démarrage scraping GitHub Actions')
    print(f'📋 Métiers: {metiers}')
    print(f'📍 Départements: {departements}')
    print(f'🔢 Max résultats: {max_results}')
    print(f'🧵 Threads: {num_threads}')
    print(f'💾 Sauvegarde directe dans la BDD activée')
    if enable_periodic_commits:
        print(f'🔄 Commits périodiques activés (intervalle: {commit_interval} min)')

    # Démarrer le thread de commit périodique si activé
    commit_thread = None
    if enable_periodic_commits:
        commit_thread = threading.Thread(
            target=periodic_commit_thread,
            args=(commit_interval,),
            daemon=True
        )
        commit_thread.start()
    
    # Charger les villes par département
    try:
        with open('data/villes_par_departement.json', 'r', encoding='utf-8') as f:
            villes_par_dept = json.load(f)
    except:
        villes_par_dept = {}
    
    # Préparer la liste des villes
    toutes_villes = []
    for dept in departements:
        if use_api_communes:
            communes = get_communes_from_api(dept, min_pop, max_pop)
            villes_dept = [c['nom'] for c in communes]
            print(f'📡 API: {len(villes_dept)} communes trouvées pour {dept}')
        else:
            villes_dept = villes_par_dept.get(dept, [])
            if not villes_dept:
                villes_dept = [f"{metiers[0]} {dept}"]
        
        for metier in metiers:
            for ville in villes_dept:
                toutes_villes.append({
                    'metier': metier,
                    'departement': dept,
                    'ville': ville
                })
    
    print(f'📊 Total villes à scraper: {len(toutes_villes)}')
    
    # ✅ Fichiers de statut et résultats
    os.makedirs('data', exist_ok=True)
    status_file = Path('data/github_actions_status.json')
    results_file = Path('data/scraping_results_github_actions.json')
    
    # Initialiser le fichier de statut
    initial_status = {
        'started_at': datetime.now().isoformat(),
        'total_tasks': len(toutes_villes),
        'completed_tasks': 0,
        'failed_tasks': 0,
        'total_results': 0,
        'tasks': {}
    }
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(initial_status, f, ensure_ascii=False, indent=2)
    
    # Initialiser le fichier de résultats
    initial_results = {
        'timestamp': datetime.now().isoformat(),
        'total_results': 0,
        'results': []
    }
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(initial_results, f, ensure_ascii=False, indent=2)
    
    # Multi-threading
    tous_resultats = []
    if num_threads > 1:
        print(f'🚀 Multi-threading activé ({num_threads} threads)')
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(scrape_ville, task, max_results, status_file): task for task in toutes_villes}
            for future in as_completed(futures):
                try:
                    resultats = future.result()
                    if resultats:
                        tous_resultats.extend(resultats)
                        # ✅ Sauvegarder progressivement
                        save_progress(results_file, resultats)
                        print(f'✅ {len(resultats)} résultats ajoutés (total: {len(tous_resultats)})')
                except Exception as e:
                    print(f'❌ Erreur thread: {e}')
    else:
        # Mode séquentiel
        for i, task in enumerate(toutes_villes, 1):
            print(f'🔍 [{i}/{len(toutes_villes)}] {task["metier"]} - {task["departement"]} - {task["ville"]}')
            resultats = scrape_ville(task, max_results, status_file)
            if resultats:
                tous_resultats.extend(resultats)
                # ✅ Sauvegarder progressivement
                save_progress(results_file, resultats)
                print(f'✅ {len(resultats)} résultats (total: {len(tous_resultats)})')
    
    print(f'✅ Scraping terminé: {len(tous_resultats)} résultats au total')

    # Arrêter le thread de commit périodique
    if enable_periodic_commits:
        print("🔄 Arrêt du thread de commit périodique...")
        stop_periodic_commit.set()
        if commit_thread:
            commit_thread.join(timeout=5)

    # ✅ Mettre à jour le statut final
    final_status = {
        'started_at': initial_status['started_at'],
        'completed_at': datetime.now().isoformat(),
        'total_tasks': len(toutes_villes),
        'completed_tasks': len([t for t in initial_status['tasks'].values() if t.get('status') == 'completed']),
        'failed_tasks': len([t for t in initial_status['tasks'].values() if t.get('status') == 'failed']),
        'total_results': len(tous_resultats),
        'status': 'completed'
    }
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(final_status, f, ensure_ascii=False, indent=2)

    print(f'💾 Résultats sauvegardés: {results_file}')
    print(f'💾 Statut sauvegardé: {status_file}')

    # Commit final des résultats
    if enable_periodic_commits:
        final_message = f"🤖 Scraping terminé: {len(tous_resultats)} résultats - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        git_commit_and_push(final_message)

