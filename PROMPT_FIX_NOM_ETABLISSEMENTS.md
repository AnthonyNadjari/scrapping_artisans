# PROMPT POUR CORRIGER L'EXTRACTION DES NOMS D'ÉTABLISSEMENTS

## 🎯 CONTEXTE

Vous travaillez sur un scraper Google Maps en Python qui extrait des informations sur des artisans (plombiers, etc.). Le code fonctionne globalement bien MAIS il y a un problème critique : **tous les établissements ont le même nom "Pereira"** au lieu de leurs vrais noms.

## ✅ CE QUI FONCTIONNE

- ✅ **Téléphone** : Correctement extrait (ex: "06 73 87 88 61", "01 60 29 40 65")
- ✅ **Site web** : Correctement extrait (ex: "https://www.etspicard.fr/", "https://plomberie-24.fr/")
- ✅ **Adresse** : Correctement extraite (ex: "26 Pl. Jean Bureau, 77100 Meaux, France")
- ✅ **Note et avis** : Correctement extraits (ex: "4.8000", "142")
- ✅ **Scraping général** : Le scraper trouve bien tous les établissements

## ❌ PROBLÈME CRITIQUE

**Tous les établissements ont le nom "Pereira"** alors qu'ils devraient avoir des noms différents comme :
- "Ets Picard Et Fils"
- "GT Plomberie77"
- "Ets Latour"
- "Plomberie 24/7"
- etc.

## 📊 EXEMPLE DE DONNÉES ACTUELLES (INCORRECTES)

```
0	Pereira	06 73 87 88 61	<NA>	<NA>	<NA>	4.8000	142
1	Pereira	01 60 29 40 65	https://www.etspicard.fr/	26 Pl. Jean Bureau...	4.8000	63
2	Pereira	06 65 22 22 93	http://dmissas.site-solocal.com/	<NA>	4.8000	115
```

## 🔍 ANALYSE DU PROBLÈME

D'après les logs de debug précédents, le code trouve bien les noms dans le panneau :
- Il trouve 33 éléments `div[class*="fontHeadline"]` dans le panneau
- Le premier est "Pereira🏅" (qui est dans le panneau de détail ouvert)
- Le deuxième est "Ets Picard Et Fils" (qui est dans la liste de résultats à gauche)

**Le problème** : Le code prend toujours le premier élément `fontHeadline[0]` qui est "Pereira" (le panneau de détail du premier établissement reste ouvert).

## 📁 FICHIER À CORRIGER

**Fichier** : `scraping/google_maps_scraper.py`

**Méthode** : `_extraire_donnees_depuis_panneau(self, element, index: int, total: int)`

## 🎯 CE QUI DOIT ÊTRE CORRIGÉ

1. **Extraire le nom depuis l'élément cliqué AVANT d'ouvrir le panneau de détail**
   - Le nom devrait être extrait directement depuis l'élément `element` dans la liste de résultats
   - Utiliser les sélecteurs : `div[class*="fontHeadline"]`, `h1`, `h2`, `h3` dans l'élément lui-même

2. **OU extraire le nom depuis le panneau de détail APRÈS le clic, mais s'assurer que c'est le bon panneau**
   - Si le panneau de détail contient plus de 5 `fontHeadline`, c'est probablement le panneau de résultats (liste), pas le panneau de détail d'un établissement
   - Dans ce cas, extraire depuis l'élément cliqué directement

3. **S'assurer que chaque établissement a son propre nom**
   - Ne pas réutiliser le nom du premier établissement
   - Réinitialiser le nom à `None` avant chaque extraction

## 🔧 STRUCTURE ACTUELLE DU CODE

La méthode `_extraire_donnees_depuis_panneau` :
1. Clique sur l'élément pour ouvrir le panneau de détail
2. Trouve le panneau de détail
3. Extrait le nom depuis le panneau de détail
4. Extrait téléphone, site web, adresse depuis le panneau de détail

## 💡 SOLUTION PROPOSÉE

**Option 1 (RECOMMANDÉE)** : Extraire le nom depuis l'élément AVANT le clic
```python
# AVANT de cliquer pour ouvrir le panneau
nom_elem = element.find_element(By.CSS_SELECTOR, 'div[class*="fontHeadline"], h1, h2, h3')
if nom_elem:
    texte = nom_elem.text.strip()
    texte_clean = texte.replace('🏅', '').replace('📌', '').replace('', '').strip()
    if texte_clean and texte_clean.lower() not in ['résultats', 'results', 'sponsorisé', 'sponsored', '']:
        info['nom'] = texte_clean
```

**Option 2** : Si le panneau de détail contient trop d'éléments (>5), extraire depuis l'élément cliqué
```python
if len(headline_elems) > 5:
    # C'est le panneau de résultats, extraire depuis l'élément cliqué
    nom_elem = element.find_element(By.CSS_SELECTOR, 'div[class*="fontHeadline"], h1, h2, h3')
    # ... extraction
```

## ⚠️ CONTRAINTES IMPORTANTES

1. **Ne pas casser ce qui fonctionne** : Téléphone, site web, adresse doivent continuer à fonctionner
2. **Gérer les cas limites** : "Résultats", "Sponsorisé", emojis doivent être ignorés
3. **Performance** : Ne pas ralentir le scraping
4. **Robustesse** : Gérer les cas où le nom n'est pas trouvé

## 📝 RÉSULTAT ATTENDU

Après correction, les données devraient ressembler à :
```
0	Pereira	06 73 87 88 61	<NA>	<NA>	<NA>	4.8000	142
1	Ets Picard Et Fils	01 60 29 40 65	https://www.etspicard.fr/	26 Pl. Jean Bureau...	4.8000	63
2	D.M.I.S SAS	06 65 22 22 93	http://dmissas.site-solocal.com/	<NA>	4.8000	115
3	GT Plomberie77	06 66 06 70 73	<NA>	<NA>	4.8000	34
```

## 🧪 TEST

Après correction, tester avec une recherche "plombier Meaux" et vérifier que :
- Chaque établissement a un nom unique
- Les noms correspondent aux vrais noms des établissements
- Les autres données (téléphone, site web, adresse) continuent à fonctionner

---

**IMPORTANT** : Cette version du code est la meilleure qu'on ait. Ne pas modifier ce qui fonctionne déjà. Seulement corriger l'extraction du nom.

