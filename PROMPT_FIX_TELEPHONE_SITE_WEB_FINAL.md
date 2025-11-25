# PROMPT POUR CORRIGER L'EXTRACTION TÉLÉPHONE ET SITE WEB

## PROBLÈME CRITIQUE

Le scraper Google Maps trouve et stocke correctement les téléphones et sites web (les logs montrent "✅ Téléphone trouvé et stocké" et "✅ Site web trouvé"), mais ces données ne sont **PAS** sauvegardées dans la base de données ni affichées dans Streamlit.

### Preuve du problème

**Logs montrant que les données SONT trouvées :**
```
[1] ✅ Téléphone trouvé et stocké: 06 73 87 88 61
[1] ✅ Site web trouvé: https://www.etspicard.fr/...
[1] 🔍 VÉRIFICATION FINALE - nom: None, tel: 06 73 87 88 61, site: https://www.etspicard.fr/...
[1] ⚠️ Pas de nom, mais données présentes - tel: 06 73 87 88 61, site: https://www.etspicard.fr/...
[1/31] (Sans nom) 📞 06 73 87 88 61 🌐 Oui ⭐ 4.8/5
```

**Mais ensuite :**
```
[1/31] Pereira🏅 ❌ Pas de téléphone
```

**Résultat final dans Streamlit :**
```
📊 17 scrapés | 📞 0 avec téléphone | 🌐 0 avec site | ⭐ 17 SANS site (prospects !)
```

## CAUSE IDENTIFIÉE

1. **Les données sont stockées dans `info`** : Les logs montrent que `info['telephone']` et `info['site_web']` sont correctement remplis
2. **Le nom est `None`** : L'extraction du nom depuis l'élément avant le clic échoue systématiquement
3. **Le retour de la fonction** : La fonction `_extraire_donnees_depuis_panneau` retourne bien `info` même si le nom est `None` (ligne 2201-2202)
4. **MAIS** : Les données ne sont pas sauvegardées dans la base de données

## FICHIER À CORRIGER

`scraping/google_maps_scraper.py` - Méthode `_extraire_donnees_depuis_panneau`

## POINTS À VÉRIFIER ET CORRIGER

### 1. Extraction du nom depuis l'élément AVANT le clic

**Lignes 1807-1869** : Le code essaie d'extraire le nom depuis l'élément avant le clic, mais échoue systématiquement.

**Problème** : Le sélecteur `div[class*="fontHeadline"]` trouve probablement plusieurs éléments, et le code prend le mauvais (celui du panneau de détail déjà ouvert, qui contient "Pereira").

**Solution demandée** :
- Limiter la recherche du nom **UNIQUEMENT** à l'élément de la liste (`element`), pas à toute la page
- Utiliser des sélecteurs plus spécifiques pour trouver le nom dans l'élément de liste
- Essayer aussi `a[href*="/maps/place/"]` dans l'élément pour extraire le nom depuis le lien
- Essayer `div[role="article"]` et chercher le premier texte significatif qui n'est pas "Résultats", "Sponsorisé", "Pereira", etc.

### 2. Vérifier que les données sont bien retournées

**Lignes 2201-2202** : Le code retourne `info` si des données sont présentes, même sans nom.

**Vérifier** :
- Que `info['telephone']` et `info['site_web']` sont bien des strings (pas `None`, pas vide)
- Que le retour se fait bien avec ces données
- Ajouter des logs pour confirmer ce qui est retourné

### 3. Vérifier l'appelant de `_extraire_donnees_depuis_panneau`

**Chercher où `_extraire_donnees_depuis_panneau` est appelée** et vérifier :
- Que le résultat retourné est bien utilisé
- Que les données sont bien passées à la fonction de sauvegarde
- Qu'il n'y a pas de filtre qui rejette les entrées sans nom

### 4. Extraction du nom depuis le panneau de détail APRÈS le clic

**Lignes 1894-1924** : Le code essaie de mettre à jour le nom depuis le panneau de détail, mais prend toujours "Pereira" (le panneau précédent).

**Solution demandée** :
- Identifier le **BON** panneau de détail (celui qui vient de s'ouvrir, pas celui qui était déjà ouvert)
- Utiliser un sélecteur pour trouver le panneau le plus à droite ou le plus récent
- Vérifier que le nom extrait correspond bien à l'établissement cliqué (en comparant avec l'URL ou d'autres données)

### 5. Logs de debug

**Ajouter des logs** pour tracer exactement ce qui se passe :
- Avant le retour de `_extraire_donnees_depuis_panneau`, logger le contenu complet de `info`
- Dans la fonction appelante, logger ce qui est reçu
- Avant la sauvegarde en base, logger ce qui va être sauvegardé

## CODE ACTUEL (EXTRAITS)

### Extraction du nom (lignes 1807-1869)
```python
# Nom
try:
    # ✅ FIX : Améliorer l'extraction du nom depuis le panneau
    nom = None
    
    # Priorité 1 : div[class*="fontHeadline"] (plus fiable, contient le vrai nom)
    try:
        headline_elems = element.find_elements(By.CSS_SELECTOR, 'div[class*="fontHeadline"]')
        for elem in headline_elems:
            texte = elem.text.strip()
            # Nettoyer les emojis
            texte_clean = texte.replace('🏅', '').replace('📌', '').replace('', '').strip()
            # Ignorer les textes génériques et "Pereira" (qui vient du panneau de détail ouvert)
            if texte_clean and texte_clean.lower() not in ['résultats', 'results', 'voir plus', 'sponsorisé', 'sponsored', 'pereira', ''] and len(texte_clean) > 3:
                nom = texte_clean
                logger.info(f"  [{index}] ✅ Nom extrait depuis élément (fontHeadline): {nom}")
                break
    except:
        pass
```

### Retour de la fonction (lignes 2201-2203)
```python
# ✅ FIX CRITIQUE : Ne pas retourner None si on a des données, même sans nom
# Le nom peut être extrait plus tard ou depuis un autre endroit
if info.get('nom') or info.get('telephone') or info.get('site_web') or info.get('adresse'):
    return info
return None
```

## SOLUTION ATTENDUE

1. **Corriger l'extraction du nom** pour qu'elle fonctionne depuis l'élément de liste
2. **S'assurer que les données sont bien retournées** même si le nom est `None`
3. **Vérifier que les données sont bien sauvegardées** dans la base de données
4. **Ajouter des logs de debug** pour tracer le flux de données
5. **Tester** que les téléphones et sites web apparaissent bien dans Streamlit

## RÉSULTAT ATTENDU

Après correction, on doit voir dans Streamlit :
```
📊 17 scrapés | 📞 17 avec téléphone | 🌐 10 avec site | ⭐ 7 SANS site (prospects !)
```

Et dans la base de données, chaque établissement doit avoir son téléphone et site web (si disponibles) correctement sauvegardés.

## CONTRAINTES

- Ne pas casser le code existant qui fonctionne pour d'autres parties
- Garder la même structure de code
- Les logs doivent rester informatifs mais pas trop verbeux
- Le code doit être robuste et gérer les cas d'erreur

## PRIORITÉ

**CRITIQUE** - Ce bug empêche l'utilisation du scraper pour son objectif principal (collecter les téléphones et sites web des artisans).

