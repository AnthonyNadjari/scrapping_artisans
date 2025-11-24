# 🚨 PROMPT CRITIQUE - PROBLÈME : 0 ÉTABLISSEMENTS TROUVÉS

## 📊 SITUATION ACTUELLE

**Problème :** Le scraper trouve **0 établissements** même après avoir accepté le consentement et être arrivé sur Google Maps.

### ✅ CE QUI FONCTIONNE
1. ✅ Consentement Google détecté et accepté avec succès
2. ✅ Redirection vers Google Maps réussie
3. ✅ Popups fermés
4. ✅ Panneau de résultats détecté (`div[jsaction]`)
5. ✅ Scroll effectué (0 scrolls car hauteur stable)

### ❌ CE QUI NE FONCTIONNE PAS
- **0 établissements trouvés** dans toute la page
- `div[role='article']: 0`
- `a[href*='/maps/place/']: 0`
- `Tous les liens: 2` (seulement 2 liens dans toute la page !)

## 🔍 HYPOTHÈSES

### Hypothèse 1 : TIMING - Les résultats ne sont pas encore chargés ⏱️
**Probabilité : 80%**

Le consentement est accepté, mais Google Maps charge les résultats **de manière asynchrone via JavaScript**. Le scraper cherche les établissements **trop tôt**, avant que le JavaScript n'ait fini de charger les résultats.

**Preuve :**
- Le panneau est détecté (`div[jsaction]`)
- Mais aucun établissement n'est présent
- Seulement 2 liens dans toute la page (normalement il devrait y en avoir des dizaines)

**Solution possible :**
- Attendre plus longtemps après l'acceptation du consentement
- Attendre que des éléments spécifiques apparaissent (ex: `div[role="article"]`)
- Utiliser `WebDriverWait` pour attendre que les résultats se chargent

### Hypothèse 2 : Structure HTML différente 🏗️
**Probabilité : 15%**

Google Maps a changé sa structure HTML. Les établissements ne sont plus dans `a[href*="/maps/place/"]` mais dans un autre format.

**Solution possible :**
- Analyser le HTML sauvegardé (`data/debug/debug_etablissements_page_source.html`)
- Identifier la vraie structure
- Adapter les sélecteurs

### Hypothèse 3 : Blocage/CAPTCHA invisible 🚫
**Probabilité : 5%**

Google Maps détecte le scraper et bloque les résultats (même sans CAPTCHA visible).

**Solution possible :**
- Améliorer l'anti-détection
- Ajouter plus de délais aléatoires
- Utiliser un profil Chrome avec historique

## 📋 FICHIERS DISPONIBLES POUR ANALYSE

1. **`data/debug/debug_etablissements_page_source.html`** - HTML complet de la page
2. **`data/debug/debug_etablissements_screenshot.png`** - Screenshot visuel

## 🔧 CODE ACTUEL À ANALYSER

### Méthode `_rechercher_etablissements()` (lignes ~755-857)

```python
def _rechercher_etablissements(self, recherche: str, ville: str) -> tuple[bool, Optional[str]]:
    # ...
    # ÉTAPE 1.5 : Vérifier et accepter le consentement Google si nécessaire
    if self._est_page_consentement():
        logger.info("   🍪 Page de consentement détectée, acceptation...")
        if not self._accepter_consentement():
            logger.error("   ❌ Échec acceptation consentement")
            return False, None
        # Attendre que Google Maps se charge après consentement
        logger.info("   ⏳ Attente chargement Google Maps après consentement...")
        time.sleep(5)  # ⚠️ PROBLÈME : 5 secondes peuvent ne pas suffire !
    
    # ÉTAPE 2 : Fermer les popups
    self._fermer_tous_popups()
    time.sleep(1)
    
    # ÉTAPE 3 : Attendre que le panneau de résultats soit chargé
    # ⚠️ PROBLÈME : On attend le panneau, mais pas les RÉSULTATS dans le panneau !
    selecteurs_panneau = [
        ('div[role="feed"]', 20),
        ('div[role="main"]', 10),
        ('div[jsaction]', 10),
        # ...
    ]
    # ...
```

**Problème identifié :** 
- Après acceptation du consentement, on attend seulement 5 secondes
- On attend que le panneau apparaisse, mais **pas que les résultats se chargent dans le panneau**
- Il faut attendre que `div[role="article"]` ou `a[href*="/maps/place/"]` apparaissent

## 🎯 MISSION

### 1. Analyser le HTML sauvegardé

**Question :** Les établissements existent-ils dans le HTML sauvegardé ?

**À vérifier :**
- Chercher `a[href*="/maps/place/"]` dans le HTML
- Chercher `div[role="article"]` dans le HTML
- Chercher des patterns de noms d'établissements (ex: "plombier", "Plomberie")
- Vérifier si les données sont dans du JavaScript (scripts)
- Vérifier s'il y a un message "Aucun résultat" ou "No results"

### 2. Si les établissements N'EXISTENT PAS dans le HTML

**Causes possibles :**
- Timing : Le HTML a été sauvegardé avant que les résultats ne se chargent
- Blocage : Google Maps bloque les résultats
- Structure différente : Les résultats sont dans un format différent

**Solution :**
- Augmenter les délais d'attente
- Attendre explicitement que les résultats apparaissent avec `WebDriverWait`
- Utiliser `_attendre_chargement_complet()` après consentement

### 3. Si les établissements EXISTENT dans le HTML

**Causes possibles :**
- Sélecteurs incorrects
- Structure HTML différente
- Résultats dans un iframe

**Solution :**
- Identifier les vrais sélecteurs
- Adapter le code pour utiliser les bons sélecteurs

## 🔧 CODE À CRÉER/MODIFIER

### Option 1 : Attendre explicitement les résultats (RECOMMANDÉ)

```python
def _rechercher_etablissements(self, recherche: str, ville: str) -> tuple[bool, Optional[str]]:
    # ... (code existant jusqu'à acceptation consentement)
    
    if self._est_page_consentement():
        if not self._accepter_consentement():
            return False, None
        # ✅ NOUVEAU : Attendre que Google Maps charge COMPLÈTEMENT
        logger.info("   ⏳ Attente chargement complet Google Maps...")
        self._attendre_chargement_complet(timeout=30)
        
        # ✅ NOUVEAU : Attendre explicitement que les RÉSULTATS apparaissent
        logger.info("   ⏳ Attente des résultats de recherche...")
        try:
            # Attendre que des établissements apparaissent
            WebDriverWait(self.driver, 30).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')) > 0 or
                          len(d.find_elements(By.CSS_SELECTOR, 'div[role="article"]')) > 0
            )
            logger.info("   ✅ Résultats de recherche détectés")
        except TimeoutException:
            logger.warning("   ⚠️ Timeout attente résultats, mais on continue...")
    
    # ... (reste du code)
```

### Option 2 : Analyser le HTML pour identifier la structure

Créer un script d'analyse :
```python
from bs4 import BeautifulSoup
from pathlib import Path

html_file = Path("data/debug/debug_etablissements_page_source.html")
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 1. Chercher tous les liens
all_links = soup.find_all('a', href=True)
print(f"Total liens: {len(all_links)}")
for link in all_links[:20]:
    print(f"  - {link.get('href', '')[:100]}")

# 2. Chercher div[role="article"]
articles = soup.find_all('div', role='article')
print(f"\nTotal div[role='article']: {len(articles)}")

# 3. Chercher des patterns "plombier" ou noms d'établissements
import re
text = soup.get_text()
if 'plombier' in text.lower():
    print("\n✅ Mot 'plombier' trouvé dans le HTML")
    # Chercher le contexte
    matches = re.finditer(r'.{0,50}plombier.{0,50}', text, re.I)
    for match in list(matches)[:5]:
        print(f"  - {match.group()}")
else:
    print("\n❌ Mot 'plombier' NON trouvé dans le HTML")

# 4. Chercher dans les scripts JavaScript
scripts = soup.find_all('script')
for script in scripts:
    script_text = script.string or ''
    if 'place' in script_text.lower() or 'result' in script_text.lower():
        print(f"\n✅ Script avec 'place' ou 'result' trouvé ({len(script_text)} chars)")
```

## 📊 RÉSULTAT ATTENDU

Après analyse, fournir :

1. **Rapport d'analyse :**
   - Les établissements existent-ils dans le HTML ? OUI/NON
   - Si OUI : Structure identifiée
   - Si NON : Raison (timing/blocage/structure)

2. **Code corrigé :**
   - Modifications à apporter à `_rechercher_etablissements()`
   - Délais d'attente à ajouter
   - Sélecteurs à utiliser

3. **Test :**
   - Vérifier que les résultats apparaissent après correction

## ⚠️ POINTS CRITIQUES

1. **Timing est crucial** - Google Maps charge les résultats de manière asynchrone
2. **Attendre les résultats, pas juste le panneau** - Le panneau peut exister sans résultats
3. **Utiliser WebDriverWait** - Plus fiable que `time.sleep()`
4. **Analyser le HTML réel** - Ne pas deviner la structure

## 🎯 OBJECTIF FINAL

Un code qui :
1. ✅ Accepte le consentement
2. ✅ Attend que Google Maps charge complètement
3. ✅ Attend explicitement que les RÉSULTATS apparaissent
4. ✅ Trouve les établissements (au lieu de 0)

---

**ANALYSE LE FICHIER HTML ET FOURNIS LA SOLUTION POUR ATTENDRE LES RÉSULTATS ! 🔍**

