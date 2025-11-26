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

def scrape_ville(task_info, max_results):
    """Scrape une ville"""
    metier_actuel = task_info['metier']
    ville_actuelle = task_info['ville']
    try:
        scraper = GoogleMapsScraper(headless=True)
        scraper.is_running = True
        resultats = scraper.scraper(
            recherche=metier_actuel,
            ville=ville_actuelle,
            max_results=max_results,
            progress_callback=None
        )
        scraper.quit()
        if resultats:
            for r in resultats:
                r['ville_recherche'] = ville_actuelle
        return resultats or []
    except Exception as e:
        print(f"❌ Erreur {ville_actuelle}: {e}")
        return []

if __name__ == "__main__":
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
    
    # Multi-threading
    tous_resultats = []
    if num_threads > 1:
        print(f'🚀 Multi-threading activé ({num_threads} threads)')
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(scrape_ville, task, max_results): task for task in toutes_villes}
            for future in as_completed(futures):
                try:
                    resultats = future.result()
                    if resultats:
                        tous_resultats.extend(resultats)
                        print(f'✅ {len(resultats)} résultats ajoutés (total: {len(tous_resultats)})')
                except Exception as e:
                    print(f'❌ Erreur thread: {e}')
    else:
        # Mode séquentiel
        for i, task in enumerate(toutes_villes, 1):
            print(f'🔍 [{i}/{len(toutes_villes)}] {task["metier"]} - {task["departement"]} - {task["ville"]}')
            resultats = scrape_ville(task, max_results)
            if resultats:
                tous_resultats.extend(resultats)
                print(f'✅ {len(resultats)} résultats (total: {len(tous_resultats)})')
    
    print(f'✅ Scraping terminé: {len(tous_resultats)} résultats au total')
    
    # Sauvegarder les résultats
    output_file = 'data/scraping_results_github_actions.json'
    os.makedirs('data', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_results': len(tous_resultats),
            'results': tous_resultats
        }, f, ensure_ascii=False, indent=2)
    
    print(f'💾 Résultats sauvegardés: {output_file}')

