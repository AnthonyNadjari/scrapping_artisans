# ✅ FIX APPLIQUÉ - Relance de la recherche après consentement

## 🎯 PROBLÈME IDENTIFIÉ

**Observation critique :** Après l'acceptation du consentement, Google Maps redirige vers une **page vide** avec juste la barre de recherche (curseur visible dans le screenshot). La recherche initiale est **perdue**.

**Symptômes :**
- ✅ Consentement accepté avec succès
- ✅ Redirection vers Google Maps réussie
- ❌ **Page vide** - Pas de résultats de recherche
- ❌ Curseur visible dans la barre de recherche (page d'accueil Google Maps)

## 📝 SOLUTION IMPLÉMENTÉE

### Relance automatique de la recherche après consentement

**Code ajouté :**
```python
# Après acceptation consentement
self._attendre_chargement_complet(timeout=30)

# ✅ CRITIQUE : Vérifier si la recherche est toujours active
logger.info("   🔍 Vérification si la recherche est toujours active...")
time.sleep(2)

# Vérifier si on a des résultats (si non, c'est une page vide)
nb_resultats = len(self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]'))
nb_articles = len(self.driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))

if nb_resultats == 0 and nb_articles == 0:
    logger.info("   ⚠️ Page vide détectée après consentement, relance de la recherche...")
    # Relancer la recherche avec l'URL complète
    url_recherche = f"https://www.google.com/maps/search/{quote(query)}"
    logger.info(f"   🔄 Relance recherche: {url_recherche}")
    self.driver.get(url_recherche)
    time.sleep(5)
    
    # Vérifier à nouveau si on est sur consentement (peut réapparaître)
    if self._est_page_consentement():
        logger.info("   🍪 Consentement réapparu, nouvelle acceptation...")
        if not self._accepter_consentement():
            logger.warning("   ⚠️ Échec acceptation consentement après relance")
        else:
            time.sleep(3)
    
    # Attendre le chargement après relance
    self._attendre_chargement_complet(timeout=30)
    logger.info("   ✅ Recherche relancée, attente des résultats...")
```

## 🔄 FLUX COMPLET

1. **Ouvrir URL de recherche** → `https://www.google.com/maps/search/plombier%20Meaux`
2. **Détecter consentement** → Page de consentement Google
3. **Accepter consentement** → Redirection vers Google Maps
4. **Vérifier résultats** → ❌ Page vide détectée (0 résultats)
5. **Relancer recherche** → `driver.get(url_recherche)` avec la même URL
6. **Vérifier consentement** → Peut réapparaître (géré)
7. **Attendre résultats** → ✅ Résultats chargés

## ✅ AVANTAGES

1. ✅ **Détection automatique** de la page vide
2. ✅ **Relance automatique** de la recherche
3. ✅ **Gestion du consentement** qui peut réapparaître
4. ✅ **Logs détaillés** pour debug

## 🚀 RÉSULTAT ATTENDU

Les logs devraient maintenant afficher :

```
🍪 Page de consentement détectée, acceptation...
✅ Bouton consentement trouvé, clic...
✅ Redirection vers Google Maps réussie
⏳ Attente chargement complet Google Maps...
🔍 Vérification si la recherche est toujours active...
⚠️ Page vide détectée après consentement, relance de la recherche...
🔄 Relance recherche: https://www.google.com/maps/search/plombier%20Meaux
✅ Recherche relancée, attente des résultats...
✅ Résultats de recherche détectés: 15 liens /maps/place/, 15 articles  ← Plus de 0 !
```

## ⚠️ CAS PARTICULIERS GÉRÉS

1. **Consentement qui réapparaît** après relance → Acceptation automatique
2. **Timeout** → Continue quand même (peut-être que les résultats sont là avec un format différent)
3. **Page vide persistante** → Debug lancé automatiquement

---

**Date :** 2025-11-24  
**Version :** 6.0 - Relance recherche après consentement  
**Status :** ✅ Implémenté  
**Observation :** Excellente identification du problème par l'utilisateur !

