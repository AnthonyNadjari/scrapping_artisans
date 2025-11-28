"""Script pour vérifier le fichier JSON des résultats"""
from pathlib import Path
import json

f = Path('data/scraping_results_github_actions.json')
print(f'JSON exists: {f.exists()}')
if f.exists():
    print(f'Size: {f.stat().st_size} bytes')
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f'Type: {type(data)}')
        if isinstance(data, list):
            print(f'Count: {len(data)}')
            if len(data) > 0:
                print(f'First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else "Not a dict"}')
        elif isinstance(data, dict):
            results = data.get('results', [])
            print(f'Count: {len(results)}')
            if len(results) > 0:
                print(f'First item keys: {list(results[0].keys()) if isinstance(results[0], dict) else "Not a dict"}')
    except Exception as e:
        print(f'Error reading JSON: {e}')
else:
    print('No JSON file found')

