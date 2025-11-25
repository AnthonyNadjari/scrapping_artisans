# PROMPT TECHNIQUE - CORRECTION CONTAMINATION PANNEAU GOOGLE MAPS

## CONTEXTE

Le scraper extrait correctement les téléphones et sites web, mais certains établissements **sans site web** se voient attribuer le site web de l'établissement **précédent** (contamination du panneau).

**Exemple observé dans les logs :**
- `[7] GT Plomberie77` → Site: `https://www.etspicard.fr/...` (mauvais)
- `[11] Julien BREUVART PLOMBERIE` → Site: `https://www.etspicard.fr/...` (mauvais)
- `[20] Bati'eau - Plombier Chauffagiste` → Site: `https://www.etspicard.fr/...` (mauvais)
- `[21] Brice Gerwig plomberie` → Site: `https://www.etspicard.fr/...` (mauvais)

**Pattern observé :** Ces établissements utilisent la méthode "aria" (backup) et récupèrent le site du panneau précédent qui n'a pas encore été rafraîchi.

## CODE ACTUEL À CORRIGER

### Fichier : `scraping/google_maps_scraper.py`

### Section 1 : Délai après le clic (ligne ~1880)

```python
# Cliquer pour ouvrir le détail
try:
    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    try:
        element.click()
    except:
        self.driver.execute_script("arguments[0].click();", element)
    time.sleep(2.5)  # ✅ FIX CRITIQUE : Augmenter le délai pour éviter la contamination du panneau
except Exception as e:
    logger.debug(f"  Erreur clic panneau [{index}]: {e}")
```

### Section 2 : Extraction du site web (lignes ~1979-2050)

```python
# ==================== EXTRACTION SITE WEB ====================
try:
    # Attendre que le panneau soit mis à jour (déjà fait avec le délai de 2.5s après le clic)
    
    # Priorité 1 : a[data-item-id*="authority"] (le plus fiable)
    site_links = search_context.find_elements(By.CSS_SELECTOR, 
        'a[data-item-id*="authority"]'
    )
    
    if site_links:
        for site_link in site_links:
            try:
                href = site_link.get_attribute('href')
                
                if href and ('http://' in href or 'https://' in href):
                    # Filtrer les liens Google Maps
                    if 'google.com' not in href.lower() and \
                       'maps' not in href.lower() and \
                       'goo.gl' not in href.lower() and \
                       'googleapis.com' not in href.lower() and \
                       'aclk' not in href.lower():
                        # Prendre le premier site valide trouvé
                        info['site_web'] = href
                        logger.info(f"  [{index}] ✅ Site web trouvé: {href}")
                        break
            except:
                continue
    
    # Priorité 2 : aria-label "Visiter le site Web" (backup si méthode 1 échoue)
    if not info.get('site_web'):
        try:
            site_links = search_context.find_elements(By.CSS_SELECTOR, 
                'a[aria-label*="Visiter le site Web"], a[aria-label*="site Web"], a[aria-label*="Website"], a[aria-label*="Site"]'
            )
            for site_link in site_links:
                try:
                    href = site_link.get_attribute('href')
                    if href and ('http://' in href or 'https://' in href):
                        if 'google.com' not in href.lower() and \
                           'maps' not in href.lower() and \
                           'goo.gl' not in href.lower() and \
                           'googleapis.com' not in href.lower() and \
                           'aclk' not in href.lower():
                            info['site_web'] = href
                            logger.info(f"  [{index}] ✅ Site web trouvé (aria): {href}")
                            break
                except:
                    continue
        except:
            pass
    
    # Si toujours pas trouvé
    if not info.get('site_web'):
        logger.debug(f"  [{index}] ⚠️ Aucun site web trouvé pour {info.get('nom', 'établissement')}")
except Exception as e:
    logger.debug(f"  Erreur extraction site web (panneau): {e}")
```

## PROBLÈME IDENTIFIÉ

1. **Le délai de 2.5 secondes n'est pas suffisant** pour que le panneau se rafraîchisse complètement
2. **La méthode "aria" (backup) trouve toujours le site du panneau précédent** car elle cherche dans toute la page, pas seulement dans le panneau mis à jour
3. **Aucune vérification que le panneau est bien mis à jour** avant d'extraire le site web

## SOLUTION À IMPLÉMENTER

### Étape 1 : Vérifier que le panneau est mis à jour AVANT d'extraire le site web

**Ajouter cette vérification juste avant l'extraction du site web :**

```python
# ==================== VÉRIFICATION PANNEAU MIS À JOUR ====================
# Attendre que le panneau soit VRAIMENT mis à jour en vérifiant le titre
nom_actuel = info.get('nom', '')
if nom_actuel:
    try:
        # Attendre que le titre du panneau corresponde au nom de l'établissement
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                titre_panneau = self.driver.find_element(By.CSS_SELECTOR, 'h1[data-attrid="title"]')
                titre_text = titre_panneau.text.strip()
                
                # Nettoyer les deux noms pour comparaison
                nom_clean = nom_actuel.lower().replace('🏅', '').replace('📌', '').strip()[:30]
                titre_clean = titre_text.lower().strip()[:30]
                
                # Vérifier si le nom correspond au titre (au moins partiellement)
                if nom_clean and titre_clean:
                    # Le nom doit être dans le titre OU le titre doit être dans le nom
                    if nom_clean in titre_clean or titre_clean in nom_clean or \
                       any(word in titre_clean for word in nom_clean.split() if len(word) > 3):
                        logger.debug(f"  [{index}] ✅ Panneau mis à jour (titre: '{titre_text}')")
                        break
                    else:
                        logger.debug(f"  [{index}] ⚠️ Panneau pas encore à jour (tentative {attempt+1}/{max_attempts})")
                        logger.debug(f"  [{index}]    Nom: '{nom_actuel}' vs Titre: '{titre_text}'")
                        time.sleep(0.5)  # Attendre 0.5s de plus
            except:
                time.sleep(0.5)
                continue
    except:
        pass
```

### Étape 2 : Limiter la recherche du site web au panneau de détail uniquement

**Remplacer la section d'extraction du site web par :**

```python
# ==================== EXTRACTION SITE WEB ====================
try:
    # Trouver le panneau de détail ouvert pour limiter la recherche
    panneau_detail = None
    try:
        # Chercher le panneau de détail (le plus à droite, celui qui vient de s'ouvrir)
        panneaux = self.driver.find_elements(By.CSS_SELECTOR, 
            'div[role="complementary"], div[jsaction*="pane"], div[class*="m6QErb"]'
        )
        
        # Prendre le panneau le plus à droite (le plus récent)
        if panneaux:
            # Trier par position X (le plus à droite)
            panneaux_positions = []
            for p in panneaux:
                try:
                    location = p.location
                    panneaux_positions.append((location['x'], p))
                except:
                    continue
            
            if panneaux_positions:
                # Prendre le panneau le plus à droite
                panneau_detail = max(panneaux_positions, key=lambda x: x[0])[1]
                logger.debug(f"  [{index}] Panneau de détail identifié (x={max(panneaux_positions, key=lambda x: x[0])[0]})")
    except:
        pass
    
    # Utiliser le panneau de détail si trouvé, sinon toute la page
    search_context_site = panneau_detail if panneau_detail else search_context
    
    # Priorité 1 : a[data-item-id*="authority"] dans le panneau de détail
    site_links = search_context_site.find_elements(By.CSS_SELECTOR, 
        'a[data-item-id*="authority"]'
    )
    
    if site_links:
        for site_link in site_links:
            try:
                href = site_link.get_attribute('href')
                
                if href and ('http://' in href or 'https://' in href):
                    # Filtrer les liens Google Maps
                    if 'google.com' not in href.lower() and \
                       'maps' not in href.lower() and \
                       'goo.gl' not in href.lower() and \
                       'googleapis.com' not in href.lower() and \
                       'aclk' not in href.lower():
                        info['site_web'] = href
                        logger.info(f"  [{index}] ✅ Site web trouvé: {href}")
                        break
            except:
                continue
    
    # Priorité 2 : aria-label UNIQUEMENT dans le panneau de détail (pas dans toute la page)
    if not info.get('site_web') and panneau_detail:
        try:
            site_links = panneau_detail.find_elements(By.CSS_SELECTOR, 
                'a[aria-label*="Visiter le site Web"], a[aria-label*="site Web"], a[aria-label*="Website"], a[aria-label*="Site"]'
            )
            for site_link in site_links:
                try:
                    href = site_link.get_attribute('href')
                    if href and ('http://' in href or 'https://' in href):
                        if 'google.com' not in href.lower() and \
                           'maps' not in href.lower() and \
                           'goo.gl' not in href.lower() and \
                           'googleapis.com' not in href.lower() and \
                           'aclk' not in href.lower():
                            info['site_web'] = href
                            logger.info(f"  [{index}] ✅ Site web trouvé (aria dans panneau): {href}")
                            break
                except:
                    continue
        except:
            pass
    
    # Si toujours pas trouvé
    if not info.get('site_web'):
        logger.debug(f"  [{index}] ⚠️ Aucun site web trouvé pour {info.get('nom', 'établissement')}")
        
except Exception as e:
    logger.debug(f"  Erreur extraction site web (panneau): {e}")
```

## CHANGEMENTS CLÉS

1. **Vérification du panneau mis à jour** : Attendre que le titre du panneau corresponde au nom de l'établissement avant d'extraire le site web
2. **Limitation de la recherche au panneau de détail** : Identifier le panneau de détail ouvert et chercher le site web UNIQUEMENT dedans, pas dans toute la page
3. **Méthode "aria" limitée au panneau** : La méthode backup (aria-label) ne cherche QUE dans le panneau de détail, pas dans toute la page

## RÉSULTAT ATTENDU

Après ces modifications :
- Les établissements **sans site web** auront `site_web: None` (pas le site du précédent)
- Les établissements **avec site web** auront leur propre site correct
- Plus de contamination du panneau

## ORDRE D'IMPLÉMENTATION

1. Ajouter la vérification du panneau mis à jour (Étape 1)
2. Remplacer la section d'extraction du site web (Étape 2)
3. Tester avec les établissements problématiques (GT Plomberie77, Brice Gerwig, etc.)

