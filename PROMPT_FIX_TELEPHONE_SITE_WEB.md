# PROMPT POUR CORRIGER L'EXTRACTION DU TÉLÉPHONE ET DU SITE WEB

## 🎯 CONTEXTE

Vous travaillez sur un scraper Google Maps en Python qui extrait des informations sur des artisans (plombiers, etc.). 

**✅ CE QUI FONCTIONNE MAINTENANT :**
- ✅ **Noms** : Correctement extraits (ex: "Ets Picard Et Fils", "Attelann Meaux", "GT Plomberie77")
- ✅ **Détection du téléphone** : Le code trouve bien les téléphones (logs montrent "✅ Téléphone trouvé via aria-label (panneau): 06 73 87 88 61")

**❌ PROBLÈMES CRITIQUES :**

1. **Téléphone trouvé mais non stocké** : 
   - Les logs montrent "✅ Téléphone trouvé via aria-label (panneau): 06 73 87 88 61"
   - Mais ensuite "❌ Pas de téléphone" dans les logs finaux
   - Résultat dans la base : `<NA>` pour tous les téléphones

2. **Site web non détecté** :
   - Tous les sites web sont `<NA>` dans les résultats
   - Pourtant, dans l'image fournie, on voit des boutons "Site Web" pour plusieurs établissements

3. **Autres données manquantes** :
   - Adresse : `<NA>`
   - Ville : `<NA>`
   - Note : `<NA>`
   - Nombre d'avis : `<NA>`

## 📊 EXEMPLE DE DONNÉES ACTUELLES (INCORRECTES)

```
0	Pereira🏅	<NA>	<NA>	<NA>	<NA>	<NA>	<NA>
1	Ets Picard Et Fils	<NA>	<NA>	<NA>	<NA>	<NA>	<NA>
2	Attelann Meaux	<NA>	<NA>	<NA>	<NA>	<NA>	<NA>
```

## 🔍 ANALYSE DU PROBLÈME

### Problème 1 : Téléphone trouvé mais non stocké

**Logs observés :**
```
[1] ✅ Téléphone trouvé via aria-label (panneau): 06 73 87 88 61
[1/31] Pereira🏅 ❌ Pas de téléphone
```

**Cause probable :**
- Le téléphone est trouvé et normalisé avec `_normaliser_telephone()`
- Mais `info['telephone']` n'est pas correctement assigné ou est réinitialisé
- Ou la fonction `_normaliser_telephone()` retourne `None` dans certains cas

**Code actuel (lignes ~1930-1936) :**
```python
tel_match = re.search(r'(\+33|0)\s*[1-9](?:\s*\d{2}){4}', aria_label)
if tel_match:
    tel_brut = tel_match.group(0).replace(' ', '').replace('+33', '0')
    tel_normalise = self._normaliser_telephone(tel_brut)
    if tel_normalise:
        info['telephone'] = tel_normalise
        logger.info(f"  [{index}] ✅ Téléphone trouvé via aria-label (panneau): {info['telephone']}")
        break
```

**Problème identifié :** Le log montre que le téléphone est trouvé, mais il n'est pas stocké dans `info['telephone']` ou est perdu après.

### Problème 2 : Site web non détecté

**Cause probable :**
- Le code cherche dans le panneau de détail avec des sélecteurs qui ne fonctionnent plus
- Les sélecteurs `a[data-item-id*="authority"]` ou `a[aria-label*="Visiter le site Web"]` ne trouvent rien
- Le panneau de détail n'est peut-être pas correctement identifié

**Code actuel (lignes ~1963-2008) :**
```python
# Priorité 1 : a[data-item-id*="authority"]
site_links = search_context_site.find_elements(By.CSS_SELECTOR, 
    'a[data-item-id*="authority"]'
)
# Priorité 2 : aria-label "Visiter le site Web"
site_links = panneau_detail.find_elements(By.CSS_SELECTOR, 
    'a[aria-label*="Visiter le site Web"]'
)
```

## 📁 FICHIER À CORRIGER

**Fichier** : `scraping/google_maps_scraper.py`

**Méthode** : `_extraire_donnees_depuis_panneau(self, element, index: int, total: int)`

**Sections à corriger :**
1. Extraction du téléphone (lignes ~1916-1957)
2. Extraction du site web (lignes ~1949-2010)
3. Extraction de l'adresse (lignes ~2012-2060)
4. Extraction de la note et avis (lignes ~2062-2094)

## 🎯 CE QUI DOIT ÊTRE CORRIGÉ

### 1. Téléphone : S'assurer que `info['telephone']` est bien assigné

**Solution proposée :**
```python
# Après avoir trouvé le téléphone
tel_normalise = self._normaliser_telephone(tel_brut)
if tel_normalise:
    info['telephone'] = tel_normalise
    logger.info(f"  [{index}] ✅ Téléphone stocké: {info['telephone']}")
    # Vérifier immédiatement après
    if not info.get('telephone'):
        logger.error(f"  [{index}] ❌ ERREUR: Téléphone non stocké malgré normalisation réussie!")
    break
```

**Vérifications à ajouter :**
- Logger le résultat de `_normaliser_telephone()` pour voir s'il retourne `None`
- Vérifier que `info['telephone']` est bien assigné après la normalisation
- S'assurer qu'aucun code ne réinitialise `info['telephone']` après

### 2. Site web : Améliorer les sélecteurs et la recherche

**Solution proposée :**
```python
# Chercher le site web dans le panneau de détail ouvert
# Priorité 1 : a[aria-label*="Visiter le site Web"] (le plus fiable)
site_links = search_context.find_elements(By.CSS_SELECTOR, 
    'a[aria-label*="Visiter le site Web"], a[aria-label*="site Web"]'
)
for site_link in site_links:
    try:
        href = site_link.get_attribute('href')
        aria_label = site_link.get_attribute('aria-label')
        if href and ('http://' in href or 'https://' in href):
            # Filtrer les URLs Google Maps
            if 'google.com' not in href.lower() and \
               'maps' not in href.lower() and \
               'goo.gl' not in href.lower() and \
               'aclk' not in href.lower():
                info['site_web'] = href
                logger.info(f"  [{index}] ✅ Site web trouvé: {info['site_web']}")
                break
    except:
        continue

# Priorité 2 : Chercher tous les liens http/https dans le panneau
if not info.get('site_web'):
    all_links = search_context.find_elements(By.CSS_SELECTOR, 'a[href^="http"]')
    for link in all_links:
        href = link.get_attribute('href')
        if href and 'google.com' not in href.lower() and 'maps' not in href.lower():
            info['site_web'] = href
            logger.info(f"  [{index}] ✅ Site web trouvé (fallback): {info['site_web']}")
            break
```

### 3. Adresse : Vérifier les sélecteurs

**Solution proposée :**
```python
# Chercher l'adresse avec plusieurs méthodes
# Priorité 1 : button avec aria-label contenant "Adresse"
adresse_buttons = search_context.find_elements(By.CSS_SELECTOR, 
    'button[aria-label*="Adresse"], button[aria-label*="Address"]'
)
for adr_btn in adresse_buttons:
    try:
        aria_label = adr_btn.get_attribute('aria-label')
        if aria_label and ('Adresse' in aria_label or 'Address' in aria_label):
            info['adresse'] = aria_label.replace('Adresse: ', '').replace('Address: ', '').strip()
            # Extraire code postal et ville
            cp_match = re.search(r'\b(\d{5})\b', info['adresse'])
            if cp_match:
                info['code_postal'] = cp_match.group(1)
            ville_match = re.search(r'\d{5}\s+(.+?)(?:,|$)', info['adresse'])
            if ville_match:
                info['ville'] = ville_match.group(1).strip()
            logger.info(f"  [{index}] ✅ Adresse trouvée: {info['adresse']}")
            break
    except:
        continue
```

### 4. Note et avis : Vérifier les sélecteurs

**Solution proposée :**
```python
# Note
try:
    note_elems = search_context.find_elements(By.CSS_SELECTOR, 
        'span[role="img"][aria-label*="étoile"], span[role="img"][aria-label*="star"]'
    )
    for note_elem in note_elems:
        note = self._extraire_note(note_elem)
        if note:
            info['note'] = note
            logger.info(f"  [{index}] ✅ Note trouvée: {info['note']}")
            break
except:
    pass

# Nombre d'avis
try:
    avis_elems = search_context.find_elements(By.XPATH, 
        "//span[contains(text(), 'avis') or contains(text(), 'review')]"
    )
    for avis_elem in avis_elems:
        nb = self._extraire_nb_avis(avis_elem)
        if nb:
            info['nb_avis'] = nb
            logger.info(f"  [{index}] ✅ Nombre d'avis trouvé: {info['nb_avis']}")
            break
except:
    pass
```

## ⚠️ CONTRAINTES IMPORTANTES

1. **Ne pas casser ce qui fonctionne** : Les noms sont maintenant corrects, ne pas les modifier
2. **Utiliser `info.get('telephone')` au lieu de `info['telephone']`** pour éviter les KeyError
3. **Ajouter des logs détaillés** pour comprendre pourquoi les données ne sont pas stockées
4. **Vérifier que `search_context` est bien défini** (doit être le panneau de détail ou `self.driver`)

## 📝 RÉSULTAT ATTENDU

Après correction, les données devraient ressembler à :
```
0	Pereira🏅	06 73 87 88 61	<NA>	<NA>	<NA>	4.8	142
1	Ets Picard Et Fils	01 60 29 40 65	https://www.etspicard.fr/	26 Pl. Jean Bureau...	Meaux	4.8	63
2	Attelann Meaux	01 60 09 46 72	https://www.attelann.fr/	30 Rue Pierre Brasseur...	Meaux	4.8	38
```

## 🧪 TEST

Après correction, tester avec une recherche "plombier Meaux" et vérifier que :
- Les téléphones sont stockés correctement
- Les sites web sont détectés et stockés
- Les adresses sont extraites avec code postal et ville
- Les notes et avis sont extraits

## 🔍 DEBUGGING

Ajouter des logs pour :
1. Vérifier que `_normaliser_telephone()` ne retourne pas `None`
2. Vérifier que `info['telephone']` est bien assigné après normalisation
3. Vérifier que `search_context` contient bien le panneau de détail
4. Logger tous les liens trouvés pour le site web
5. Logger tous les boutons trouvés pour l'adresse

---

**IMPORTANT** : Les noms fonctionnent maintenant. Ne pas modifier l'extraction des noms. Seulement corriger téléphone, site web, adresse, note et avis.

