"""
Script d'analyse du HTML Google Maps pour identifier les vrais sélecteurs
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from bs4 import BeautifulSoup
from pathlib import Path
import re

# Charger le HTML de debug
debug_file = Path(__file__).parent / "data" / "debug" / "debug_page_source.html"

if not debug_file.exists():
    print(f"ERREUR: Fichier non trouve: {debug_file}")
    exit(1)

print("="*80)
print("ANALYSE HTML GOOGLE MAPS")
print("="*80)
print(f"\nFichier analyse: {debug_file}\n")

with open(debug_file, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 1. Chercher TOUS les inputs
print("="*80)
print("📋 TOUS LES INPUTS (<input>):")
print("="*80)
all_inputs = soup.find_all('input')
print(f"   Total: {len(all_inputs)} inputs trouvés\n")

for idx, inp in enumerate(all_inputs[:30], 1):  # Limiter à 30
    print(f"   [{idx}] Type: {inp.get('type', 'N/A')}")
    print(f"       ID: {inp.get('id', 'N/A')}")
    print(f"       Class: {inp.get('class', 'N/A')}")
    print(f"       Aria-label: {inp.get('aria-label', 'N/A')[:80]}")
    print(f"       Placeholder: {inp.get('placeholder', 'N/A')[:80]}")
    print(f"       Name: {inp.get('name', 'N/A')}")
    print(f"       Autocomplete: {inp.get('autocomplete', 'N/A')}")
    print(f"       Role: {inp.get('role', 'N/A')}")
    print()

# 2. Chercher des éléments contenant "search" ou "recherch"
print("="*80)
print("🔎 ÉLÉMENTS CONTENANT 'search' OU 'recherch':")
print("="*80)
search_elements = soup.find_all(lambda tag: 
    tag.name and (
        'search' in str(tag.get('id', '')).lower() or
        'search' in str(tag.get('class', '')).lower() or
        'search' in str(tag.get('aria-label', '')).lower() or
        'recherch' in str(tag.get('aria-label', '')).lower() or
        'search' in str(tag.get('placeholder', '')).lower() or
        'recherch' in str(tag.get('placeholder', '')).lower()
    )
)

print(f"   Total: {len(search_elements)} éléments\n")
for idx, elem in enumerate(search_elements[:20], 1):
    print(f"   [{idx}] Tag: {elem.name}")
    print(f"       ID: {elem.get('id', 'N/A')}")
    print(f"       Class: {elem.get('class', 'N/A')}")
    print(f"       Aria-label: {elem.get('aria-label', 'N/A')[:80]}")
    print(f"       Placeholder: {elem.get('placeholder', 'N/A')[:80]}")
    print(f"       HTML: {str(elem)[:150]}...")
    print()

# 3. Chercher des iframes
print("="*80)
print("🖼️  IFRAMES:")
print("="*80)
iframes = soup.find_all('iframe')
print(f"   Total: {len(iframes)} iframes trouvés\n")
for idx, iframe in enumerate(iframes, 1):
    print(f"   [{idx}] Src: {iframe.get('src', 'N/A')[:100]}...")
    print(f"       ID: {iframe.get('id', 'N/A')}")
    print(f"       Name: {iframe.get('name', 'N/A')}")
    print(f"       Class: {iframe.get('class', 'N/A')}")
    print()

# 4. Chercher role="search"
print("="*80)
print("🔍 ÉLÉMENTS AVEC role='search':")
print("="*80)
search_roles = soup.find_all(attrs={'role': 'search'})
print(f"   Total: {len(search_roles)} éléments\n")
for idx, elem in enumerate(search_roles, 1):
    print(f"   [{idx}] Tag: {elem.name}")
    print(f"       ID: {elem.get('id', 'N/A')}")
    print(f"       Class: {elem.get('class', 'N/A')}")
    print(f"       HTML: {str(elem)[:300]}...")
    # Chercher des inputs dedans
    inputs_inside = elem.find_all('input')
    print(f"       Inputs dedans: {len(inputs_inside)}")
    for inp in inputs_inside:
        print(f"          - Input ID: {inp.get('id', 'N/A')}, Type: {inp.get('type', 'N/A')}")
    print()

# 5. Chercher des divs/sections qui pourraient contenir la recherche
print("="*80)
print("📦 CONTENEURS POTENTIELS (header, nav, search):")
print("="*80)
containers = soup.find_all(['header', 'nav', 'div'], 
                          attrs={'role': lambda x: x in ['search', 'navigation', 'banner'] if x else False})
print(f"   Total: {len(containers)} conteneurs\n")
for idx, cont in enumerate(containers[:10], 1):
    print(f"   [{idx}] Tag: {cont.name}")
    print(f"       Role: {cont.get('role', 'N/A')}")
    print(f"       ID: {cont.get('id', 'N/A')}")
    print(f"       Class: {cont.get('class', 'N/A')}")
    # Chercher des inputs dedans
    inputs_inside = cont.find_all('input')
    print(f"       Inputs dedans: {len(inputs_inside)}")
    for inp in inputs_inside:
        print(f"          - Input ID: {inp.get('id', 'N/A')}, Type: {inp.get('type', 'N/A')}, Placeholder: {inp.get('placeholder', 'N/A')}")
    print()

# 6. Chercher des éléments contenteditable
print("="*80)
print("✏️  ÉLÉMENTS CONTENTEDITABLE (peut-être la barre de recherche?):")
print("="*80)
contenteditable = soup.find_all(attrs={'contenteditable': True})
print(f"   Total: {len(contenteditable)} éléments\n")
for idx, elem in enumerate(contenteditable[:10], 1):
    print(f"   [{idx}] Tag: {elem.name}")
    print(f"       ID: {elem.get('id', 'N/A')}")
    print(f"       Class: {elem.get('class', 'N/A')}")
    print(f"       Role: {elem.get('role', 'N/A')}")
    print(f"       Aria-label: {elem.get('aria-label', 'N/A')[:80]}")
    print(f"       HTML: {str(elem)[:200]}...")
    print()

# 7. Chercher des textarea
print("="*80)
print("📝 TEXTAREAS:")
print("="*80)
textareas = soup.find_all('textarea')
print(f"   Total: {len(textareas)} textareas trouvés\n")
for idx, ta in enumerate(textareas[:10], 1):
    print(f"   [{idx}] ID: {ta.get('id', 'N/A')}")
    print(f"       Class: {ta.get('class', 'N/A')}")
    print(f"       Placeholder: {ta.get('placeholder', 'N/A')[:80]}")
    print(f"       Aria-label: {ta.get('aria-label', 'N/A')[:80]}")
    print()

# 8. Chercher des éléments avec aria-label contenant "search" ou "recherch"
print("="*80)
print("🏷️  ÉLÉMENTS AVEC ARIA-LABEL CONTENANT 'search'/'recherch':")
print("="*80)
aria_search = soup.find_all(attrs={'aria-label': re.compile(r'search|recherch', re.I)})
print(f"   Total: {len(aria_search)} éléments\n")
for idx, elem in enumerate(aria_search[:15], 1):
    print(f"   [{idx}] Tag: {elem.name}")
    print(f"       ID: {elem.get('id', 'N/A')}")
    print(f"       Class: {elem.get('class', 'N/A')}")
    print(f"       Aria-label: {elem.get('aria-label', 'N/A')}")
    print(f"       HTML: {str(elem)[:200]}...")
    print()

# 9. Chercher des éléments avec data-* attributes liés à search
print("="*80)
print("🔖 ÉLÉMENTS AVEC DATA-* ATTRIBUTES (data-*search*):")
print("="*80)
data_search = soup.find_all(attrs=lambda x: x and any('search' in str(k).lower() or 'search' in str(v).lower() 
                                                       for k, v in x.items() if k.startswith('data-')))
print(f"   Total: {len(data_search)} éléments\n")
for idx, elem in enumerate(data_search[:15], 1):
    print(f"   [{idx}] Tag: {elem.name}")
    print(f"       ID: {elem.get('id', 'N/A')}")
    attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
    print(f"       Data attributes: {attrs}")
    print(f"       HTML: {str(elem)[:200]}...")
    print()

# 10. Résumé des inputs de type text
print("="*80)
print("📊 RÉSUMÉ: INPUTS DE TYPE TEXT:")
print("="*80)
text_inputs = [inp for inp in all_inputs if inp.get('type') == 'text' or inp.get('type') is None]
print(f"   Total: {len(text_inputs)} inputs de type text\n")
for idx, inp in enumerate(text_inputs[:20], 1):
    print(f"   [{idx}] ID: {inp.get('id', 'N/A')}")
    print(f"       Class: {inp.get('class', 'N/A')}")
    print(f"       Placeholder: {inp.get('placeholder', 'N/A')[:60]}")
    print(f"       Aria-label: {inp.get('aria-label', 'N/A')[:60]}")
    print()

print("="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80)

