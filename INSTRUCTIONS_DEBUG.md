# 🔍 Instructions pour Debug Structure HTML

## Problème actuel
Le scraper extrait les noms des établissements mais ne trouve pas :
- ❌ Téléphone
- ❌ Site web
- ❌ Adresse
- ❌ Code postal / Ville
- ❌ Note / Nombre d'avis

## Solution : Fonction de debug ajoutée

Une fonction de debug a été ajoutée qui sauvegarde automatiquement la structure HTML du panneau de détail pour le **premier établissement** scrapé.

### Fichiers générés (dans `data/debug/`) :

1. **`debug_panneau_detail_1_page_source.html`**
   - HTML complet de la page après clic sur le premier établissement
   - **À COPIER-COLLER** pour analyse

2. **`debug_panneau_detail_1_panneau.html`**
   - HTML du panneau latéral uniquement
   - **À COPIER-COLLER** pour analyse

3. **`debug_panneau_detail_1_screenshot.png`**
   - Screenshot de la page
   - Pour visualiser la structure

4. **`debug_panneau_detail_1_selecteurs.txt`**
   - Résultats des tests de sélecteurs CSS
   - Montre quels sélecteurs trouvent des éléments

## Comment utiliser

1. **Lancer le scraping** (au moins 1 établissement)
2. **Aller dans** `data/debug/`
3. **Ouvrir** `debug_panneau_detail_1_panneau.html` (ou `page_source.html`)
4. **Copier tout le contenu** et le coller ici pour que je puisse analyser la structure réelle de Google Maps

## Ce que je vais faire

Une fois que vous m'aurez fourni le HTML, je pourrai :
- ✅ Identifier les vrais sélecteurs CSS pour téléphone, site web, adresse
- ✅ Corriger le code d'extraction
- ✅ Tester avec la structure réelle de Google Maps

---

**Note** : La fonction de debug s'active automatiquement pour le premier établissement (index=1). Si vous voulez debugger un autre établissement, modifiez la condition `if index == 1:` dans le code.

