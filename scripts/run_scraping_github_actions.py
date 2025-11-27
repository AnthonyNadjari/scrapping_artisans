#!/usr/bin/env python3
"""
Script pour exécuter le scraping depuis GitHub Actions
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.google_maps_scraper import GoogleMapsScraper
import requests
from whatsapp_database.queries import ajouter_artisan, mark_scraping_done
from whatsapp_database.models import init_database

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
        # Préparer les données pour la BDD
        data = {
            'nom': artisan_data.get('nom'),
            'telephone': artisan_data.get('telephone'),
            'site_web': artisan_data.get('site_web'),
            'adresse': artisan_data.get('adresse'),
            'code_postal': artisan_data.get('code_postal'),
            'ville': artisan_data.get('ville'),
            'departement': artisan_data.get('departement'),
            'note': artisan_data.get('note'),
            'nombre_avis': artisan_data.get('nb_avis'),
            'ville_recherche': artisan_data.get('ville_recherche'),
            'source': 'google_maps',
            'source_telephone': 'google_maps',
            'type_artisan': artisan_data.get('recherche')
        }
        
        # Sauvegarder dans la BDD
        artisan_id = ajouter_artisan(data)
        print(f"✅ Artisan sauvegardé (ID: {artisan_id}): {data.get('nom', 'N/A')}")
        return artisan_id
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde artisan: {e}")
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
        
        # ✅ Callback pour sauvegarder directement dans la BDD
        def progress_callback(index, total, info):
            if info:
                info['ville_recherche'] = ville_actuelle
                info['recherche'] = metier_actuel
                info['departement'] = departement_actuel
                save_callback(info)
        
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
    
    print(f'🚀 Démarrage scraping GitHub Actions')
    print(f'📋 Métiers: {metiers}')
    print(f'📍 Départements: {departements}')
    print(f'🔢 Max résultats: {max_results}')
    print(f'🧵 Threads: {num_threads}')
    print(f'💾 Sauvegarde directe dans la BDD activée')
    
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

