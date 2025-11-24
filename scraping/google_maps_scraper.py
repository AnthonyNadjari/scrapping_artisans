"""
Scraper Google Maps pour extraire les artisans
Extrait : nom, téléphone, site web, adresse, note, avis
MÉTHODE URL DIRECTE : Utilise https://www.google.com/maps/search/{REQUÊTE}
"""
import time
import random
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoogleMapsScraper:
    """
    Scraper Google Maps pour extraire les informations des artisans
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialise le scraper Google Maps
        
        Args:
            headless: Mode headless (True) ou visible (False)
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.is_running = True  # Par défaut, on est prêt à scraper
        self.scraped_count = 0
        
    def _setup_driver(self):
        """Configure et lance Chrome avec Selenium - VERSION ULTRA-ROBUSTE"""
        chrome_options = Options()
        
        # Anti-détection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Configuration de base
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        
        # Réduire les erreurs GCM/notifications
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        
        # Langue française
        chrome_options.add_argument('--lang=fr-FR')
        
        # User-Agent personnalisé
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Préférences pour désactiver notifications et géolocalisation
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            # Utiliser webdriver_manager pour télécharger automatiquement ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Exécuter JS pour cacher webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Timeout plus long pour les pages lentes
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ Chrome driver initialisé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Chrome: {e}")
            return False
    
    def _normaliser_telephone(self, tel: str) -> Optional[str]:
        """
        Normalise un numéro français au format 0X XX XX XX XX
        
        Args:
            tel: Numéro brut (peut contenir espaces, points, tirets)
        
        Returns:
            Numéro au format 0X XX XX XX XX ou None si invalide
        """
        if not tel:
            return None
        
        # Nettoyer le numéro (garder seulement les chiffres)
        tel_clean = ''.join(filter(str.isdigit, tel))
        
        # Vérifier format français (10 chiffres commençant par 0)
        if len(tel_clean) == 10 and tel_clean.startswith('0'):
            # Formater : 0X XX XX XX XX
            return f"{tel_clean[0:2]} {tel_clean[2:4]} {tel_clean[4:6]} {tel_clean[6:8]} {tel_clean[8:10]}"
        elif len(tel_clean) == 9 and tel_clean.startswith('0'):
            # Cas spécial : 9 chiffres (ajouter le 0)
            return f"0{tel_clean[0:1]} {tel_clean[1:3]} {tel_clean[3:5]} {tel_clean[5:7]} {tel_clean[7:9]}"
        
        return None
    
    def _extraire_note(self, element) -> Optional[float]:
        """Extrait la note depuis un élément"""
        try:
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                # Chercher pattern : "4.5" ou "4,5" dans aria-label
                match = re.search(r'(\d+[,\.]\d+)', aria_label)
                if match:
                    note_str = match.group(1).replace(',', '.')
                    return float(note_str)
        except:
            pass
        return None
    
    def _extraire_nb_avis(self, element) -> Optional[int]:
        """Extrait le nombre d'avis depuis un élément"""
        try:
            text = element.text
            if text:
                # Chercher pattern : "156 avis" ou "(156)"
                match = re.search(r'(\d+)\s*avis?', text, re.I)
                if match:
                    return int(match.group(1))
        except:
            pass
        return None
    
    def _scroller_panneau_lateral(self, max_scrolls: int = 15, selector: str = 'div[role="feed"]'):
        """
        Scroll le panneau latéral pour charger plus de résultats
        
        Args:
            max_scrolls: Nombre maximum de scrolls à effectuer
            selector: Sélecteur CSS du panneau (par défaut 'div[role="feed"]')
        """
        try:
            # Trouver le panneau de résultats avec le sélecteur fourni
            # Essayer plusieurs sélecteurs si celui fourni ne fonctionne pas
            selecteurs_essai = [selector, 'div[role="feed"]', 'div[role="main"]', 'div[jsaction]']
            panneau = None
            selector_utilise = None
            
            for sel in selecteurs_essai:
                try:
                    panneau = WebDriverWait(self.driver, 10).until(  # Timeout augmenté à 10s
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                    )
                    logger.info(f"   📜 Panneau trouvé pour scroll avec: {sel}")
                    selector_utilise = sel
                    break
                except:
                    continue
            
            if not panneau:
                logger.warning("⚠️ Panneau principal non trouvé, tentative avec méthode alternative...")
                # Méthode alternative : chercher un élément scrollable dans la page
                try:
                    # Chercher un élément avec overflow scroll ou auto
                    scrollable_selector = self.driver.execute_script("""
                        var elements = document.querySelectorAll('div[role="main"] div, div[role="feed"] div');
                        for (var i = 0; i < elements.length; i++) {
                            var style = window.getComputedStyle(elements[i]);
                            if (style.overflowY === 'scroll' || style.overflowY === 'auto' || 
                                style.overflow === 'scroll' || style.overflow === 'auto') {
                                // Retourner un sélecteur unique si possible
                                if (elements[i].id) {
                                    return '#' + elements[i].id;
                                }
                                // Sinon retourner un XPath approximatif
                                return 'div[role="main"] div, div[role="feed"] div';
                            }
                        }
                        return null;
                    """)
                    if scrollable_selector:
                        # Essayer de trouver l'élément avec le sélecteur retourné
                        try:
                            panneau = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, scrollable_selector))
                            )
                            logger.info("   📜 Élément scrollable trouvé avec méthode alternative")
                        except:
                            # Si ça ne marche pas, utiliser le scroll de page
                            raise TimeoutException("Scrollable trouvé mais non accessible")
                    else:
                        raise TimeoutException("Aucun panneau scrollable trouvé")
                except:
                    raise TimeoutException("Aucun panneau trouvé pour le scroll")
            
            # Vérifier si le panneau est scrollable
            is_scrollable = self.driver.execute_script("""
                var elem = arguments[0];
                return elem.scrollHeight > elem.clientHeight;
            """, panneau)
            
            if not is_scrollable:
                logger.warning("   ⚠️ Le panneau trouvé n'est pas scrollable directement")
                logger.info("   🔍 Recherche d'un sous-élément scrollable...")
                
                # Chercher un sous-élément scrollable dans le panneau
                scrollable_child = None
                try:
                    # Chercher un div scrollable à l'intérieur
                    children = panneau.find_elements(By.CSS_SELECTOR, 'div')
                    for child in children[:20]:  # Limiter à 20 pour performance
                        try:
                            is_child_scrollable = self.driver.execute_script("""
                                var elem = arguments[0];
                                return elem.scrollHeight > elem.clientHeight;
                            """, child)
                            if is_child_scrollable:
                                scrollable_child = child
                                logger.info("   ✅ Sous-élément scrollable trouvé")
                                break
                        except:
                            continue
                    
                    if scrollable_child:
                        panneau = scrollable_child
                        is_scrollable = True
                    else:
                        logger.warning("   ⚠️ Aucun sous-élément scrollable trouvé, utilisation du scroll de page")
                        # Si aucun sous-élément scrollable, scroller la page entière
                        last_height = self.driver.execute_script("return document.body.scrollHeight")
                        scrolls = 0
                        
                        while scrolls < max_scrolls:
                            # Scroller la page
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            
                            new_height = self.driver.execute_script("return document.body.scrollHeight")
                            if new_height == last_height:
                                logger.info(f"✅ Fin du scroll de page (hauteur stable après {scrolls} scrolls)")
                                break
                            
                            last_height = new_height
                            scrolls += 1
                            time.sleep(random.uniform(1, 2))
                        
                        logger.info(f"📜 {scrolls} scrolls de page effectués")
                        return
                except Exception as e:
                    logger.warning(f"   ⚠️ Erreur recherche sous-élément: {e}")
                    # Fallback : scroll de page
                    logger.info("   📜 Utilisation du scroll de page comme fallback")
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    scrolls = 0
                    
                    while scrolls < max_scrolls:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                        scrolls += 1
                        time.sleep(random.uniform(1, 2))
                    
                    logger.info(f"📜 {scrolls} scrolls de page effectués")
                    return
            
            # Le panneau est scrollable, utiliser la méthode normale
            last_height = 0
            scrolls = 0
            
            while scrolls < max_scrolls:
                # Scroll vers le bas
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", panneau
                )
                
                # Attendre que les nouveaux résultats se chargent
                time.sleep(2)
                
                # Vérifier si on a atteint la fin
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", panneau
                )
                
                if new_height == last_height:
                    # Plus de nouveaux résultats
                    logger.info(f"✅ Fin du scroll (hauteur stable après {scrolls} scrolls)")
                    break
                
                last_height = new_height
                scrolls += 1
                
                # Pause aléatoire entre scrolls
                time.sleep(random.uniform(1, 2))
            
            logger.info(f"📜 {scrolls} scrolls effectués")
            
        except TimeoutException as e:
            logger.warning(f"⚠️ Panneau de résultats non trouvé: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur lors du scroll: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def _attendre_chargement_complet(self, timeout: int = 30) -> bool:
        """
        Attend que Google Maps soit vraiment prêt - VERSION ULTRA-ROBUSTE
        Google Maps charge son contenu via JavaScript, il faut attendre que le JS termine
        
        Args:
            timeout: Timeout en secondes
        
        Returns:
            True si chargé, False sinon
        """
        try:
            # 1. Vérifier que l'URL contient "maps"
            WebDriverWait(self.driver, timeout).until(
                lambda d: "maps" in d.current_url.lower()
            )
            logger.info("   ✅ URL Google Maps confirmée")
            
            # 2. Attendre que document.readyState == "complete"
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.info("   ✅ Document ready")
            
            # 3. CRITIQUE: Attendre que le JavaScript de Google Maps charge le contenu
            # On attend que des éléments spécifiques créés par JS apparaissent
            logger.info("   ⏳ Attente du chargement JavaScript de Google Maps...")
            
            # Attendre que jQuery ou les scripts Google Maps soient chargés
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script("""
                        return typeof google !== 'undefined' || 
                               typeof window.google !== 'undefined' ||
                               document.querySelector('div[role="main"]') !== null ||
                               document.querySelector('div[jsaction]') !== null;
                    """)
                )
                logger.info("   ✅ JavaScript Google Maps chargé")
            except:
                logger.warning("   ⚠️ Timeout vérification JS, continuation...")
            
            # 4. Attendre que des éléments DOM créés par JS apparaissent
            # Ces éléments n'existent que après le chargement JS
            elements_to_wait = [
                "div[role='main']",
                "div[jsaction]",  # Éléments avec jsaction sont créés par JS
                "div[role='region']",
                "div[data-value]",  # Éléments avec data-value
            ]
            
            element_found = False
            for selector in elements_to_wait:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"   ✅ Élément JS détecté: {selector}")
                    element_found = True
                    break
                except:
                    continue
            
            if not element_found:
                logger.warning("   ⚠️ Aucun élément JS détecté, mais continuation...")
            
            # 5. Attendre que le DOM se stabilise (plus de changements)
            logger.info("   ⏳ Attente stabilisation DOM...")
            time.sleep(3)  # Pause pour laisser le JS finir de charger
            
            # 6. Vérifier que la page n'est plus en train de charger
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.execute_script("""
                        return document.readyState === 'complete' && 
                               (document.querySelector('div[role="main"]') !== null ||
                                document.querySelector('div[jsaction]') !== null);
                    """)
                )
                logger.info("   ✅ DOM stabilisé")
            except:
                logger.warning("   ⚠️ DOM peut-être pas complètement stabilisé")
            
            return True
        except Exception as e:
            logger.error(f"   ❌ Timeout chargement Google Maps: {e}")
            return False
    
    def _est_page_consentement(self) -> bool:
        """Vérifie si on est sur la page de consentement Google"""
        try:
            current_url = self.driver.current_url.lower()
            page_title = self.driver.title.lower()
            
            is_consent = (
                'consent.google.com' in current_url or
                'consentement' in page_title or
                'avant d\'accéder' in page_title or
                'before accessing' in page_title or
                'consentui' in current_url
            )
            
            if is_consent:
                logger.info(f"   🍪 Page de consentement détectée: {self.driver.current_url[:80]}...")
            
            return is_consent
        except:
            return False
    
    def _accepter_consentement(self) -> bool:
        """Accepte le consentement Google et redirige vers Google Maps"""
        
        max_tentatives = 3
        
        for tentative in range(1, max_tentatives + 1):
            logger.info(f"   🍪 Tentative {tentative}/{max_tentatives} d'acceptation du consentement...")
            
            # Sélecteurs pour le bouton "Tout accepter"
            selecteurs = [
                # XPath français
                "//button[contains(., 'Tout accepter')]",
                "//button[contains(., 'Accepter tout')]",
                "//button[contains(., 'J'accepte')]",
                "//button[contains(., 'Accepter')]",
                
                # XPath anglais
                "//button[contains(., 'Accept all')]",
                "//button[contains(., 'I agree')]",
                "//button[contains(., 'Accept')]",
                
                # CSS
                "button[id*='accept']",
                "button[class*='accept']",
                "button[aria-label*='Accept']",
                "button[aria-label*='Accepter']",
            ]
            
            for selector in selecteurs:
                try:
                    if selector.startswith("//"):
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    else:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for btn in buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                logger.info(f"   ✅ Bouton consentement trouvé, clic...")
                                btn.click()
                                time.sleep(5)  # Attendre la redirection
                                
                                # Vérifier qu'on est maintenant sur Google Maps
                                new_url = self.driver.current_url.lower()
                                if 'maps.google.com' in new_url or 'google.com/maps' in new_url:
                                    logger.info("   ✅ Redirection vers Google Maps réussie")
                                    return True
                                
                                # Si toujours sur consentement, réessayer
                                if self._est_page_consentement():
                                    logger.info("   ⏳ Toujours sur consentement, nouvelle tentative...")
                                    continue
                                else:
                                    # Peut-être redirigé ailleurs, vérifier
                                    logger.info(f"   📍 URL actuelle: {self.driver.current_url[:80]}...")
                                    return True  # On continue quand même
                        except:
                            continue
                except:
                    continue
            
            if tentative < max_tentatives:
                time.sleep(2)
                continue
        
        logger.error("   ❌ Impossible d'accepter le consentement après 3 tentatives")
        return False
    
    def _fermer_tous_popups(self):
        """Ferme absolument tous les popups possibles (sauf consentement, géré séparément)"""
        popups_fermes = 0
        
        # Liste EXHAUSTIVE des sélecteurs de popups (sans consentement)
        selecteurs_popup = [
            # Géolocalisation
            ("//button[contains(text(), 'Refuser')]", By.XPATH),
            ("//button[contains(text(), 'Deny')]", By.XPATH),
            ("button[aria-label*='Close'], button[aria-label*='Fermer']", By.CSS_SELECTOR),
            
            # Onboarding/tutoriel
            ("button[aria-label*='Dismiss'], button[aria-label*='Skip']", By.CSS_SELECTOR),
            ("//button[contains(text(), 'Ignorer')]", By.XPATH),
            
            # Boutons X génériques
            ("button[aria-label='Close'], button[aria-label='Fermer']", By.CSS_SELECTOR),
            ("button.close, button[class*='close']", By.CSS_SELECTOR),
        ]
        
        for selecteur, selector_type in selecteurs_popup:
            try:
                elements = self.driver.find_elements(selector_type, selecteur)
                
                for elem in elements:
                    try:
                        if elem.is_displayed():
                            elem.click()
                            popups_fermes += 1
                            logger.info(f"   ✅ Popup fermé ({selecteur[:30]}...)")
                            time.sleep(0.5)
                    except:
                        pass
            except:
                pass
        
        if popups_fermes > 0:
            logger.info(f"   ✅ {popups_fermes} popup(s) fermé(s)")
            time.sleep(1)  # Laisser l'UI se stabiliser
    
    def _trouver_barre_recherche_robuste(self):
        """
        Trouve la barre avec 10+ méthodes de fallback
        IMPORTANT: La barre est créée par JavaScript, il faut attendre qu'elle apparaisse
        
        Returns:
            (search_box, methode_utilisee) ou (None, None)
        """
        from selenium.webdriver.common.keys import Keys
        
        # CRITIQUE: Attendre d'abord que le JavaScript crée la barre de recherche
        # On attend qu'un input avec certains attributs apparaisse
        logger.info("   ⏳ Attente création de la barre de recherche par JavaScript...")
        
        # Attendre jusqu'à 15 secondes que la barre apparaisse
        try:
            # Essayer d'attendre qu'un input de type text apparaisse (créé par JS)
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("""
                    return document.querySelector('input#searchboxinput') !== null ||
                           document.querySelector('input[aria-label*="Search"]') !== null ||
                           document.querySelector('input[aria-label*="Rechercher"]') !== null ||
                           document.querySelector('input[placeholder*="Search"]') !== null ||
                           document.querySelector('input[placeholder*="Rechercher"]') !== null ||
                           document.querySelector('input[type="text"][class*="search"]') !== null;
                """)
            )
            logger.info("   ✅ Barre de recherche détectée dans le DOM (créée par JS)")
            time.sleep(1)  # Petite pause pour stabilisation
        except TimeoutException:
            logger.warning("   ⚠️ Timeout attente barre de recherche, mais on continue...")
        
        # Liste de TOUTES les méthodes possibles (avec timeouts plus longs)
        methodes = [
            # Méthode 1 : ID classique
            {
                'nom': 'ID searchboxinput',
                'type': By.ID,
                'valeur': 'searchboxinput',
                'condition': EC.element_to_be_clickable
            },
            
            # Méthode 2 : Aria-label (FR)
            {
                'nom': 'Aria-label Rechercher',
                'type': By.CSS_SELECTOR,
                'valeur': 'input[aria-label*="Rechercher"]',
                'condition': EC.element_to_be_clickable
            },
            
            # Méthode 3 : Aria-label (EN)
            {
                'nom': 'Aria-label Search',
                'type': By.CSS_SELECTOR,
                'valeur': 'input[aria-label*="Search"]',
                'condition': EC.element_to_be_clickable
            },
            
            # Méthode 4 : Placeholder (FR)
            {
                'nom': 'Placeholder Rechercher',
                'type': By.CSS_SELECTOR,
                'valeur': 'input[placeholder*="Rechercher"]',
                'condition': EC.presence_of_element_located
            },
            
            # Méthode 5 : Placeholder (EN)
            {
                'nom': 'Placeholder Search',
                'type': By.CSS_SELECTOR,
                'valeur': 'input[placeholder*="Search"]',
                'condition': EC.presence_of_element_located
            },
            
            # Méthode 6 : Class contenant "searchbox"
            {
                'nom': 'Class searchbox',
                'type': By.CSS_SELECTOR,
                'valeur': 'input[class*="searchbox"]',
                'condition': EC.element_to_be_clickable
            },
            
            # Méthode 7 : Input de type text dans header
            {
                'nom': 'Input dans header',
                'type': By.CSS_SELECTOR,
                'valeur': 'header input[type="text"], div[role="search"] input',
                'condition': EC.presence_of_element_located
            },
            
            # Méthode 8 : XPath contenant texte
            {
                'nom': 'XPath par placeholder',
                'type': By.XPATH,
                'valeur': "//input[contains(@placeholder, 'Rechercher') or contains(@placeholder, 'Search')]",
                'condition': EC.presence_of_element_located
            },
            
            # Méthode 9 : XPath par aria-label
            {
                'nom': 'XPath par aria-label',
                'type': By.XPATH,
                'valeur': "//input[contains(@aria-label, 'Rechercher') or contains(@aria-label, 'Search')]",
                'condition': EC.element_to_be_clickable
            },
            
            # Méthode 10 : Tous les inputs visibles (dernier recours)
            {
                'nom': 'Premier input visible',
                'type': By.CSS_SELECTOR,
                'valeur': 'input[type="text"]:not([style*="display: none"])',
                'condition': EC.presence_of_element_located
            },
        ]
        
        # Essayer chaque méthode (avec timeout plus long car JS peut être lent)
        for idx, methode in enumerate(methodes, 1):
            try:
                logger.info(f"   🔍 Tentative {idx}/10: {methode['nom']}...")
                
                # Utiliser WebDriverWait avec timeout plus long (10s au lieu de 5s)
                # car l'élément peut être en train d'être créé par JS
                search_box = WebDriverWait(self.driver, 10).until(
                    methode['condition']((methode['type'], methode['valeur']))
                )
                
                # Vérifier que l'élément est vraiment interactif
                if search_box:
                    # Attendre que l'élément soit visible et enabled
                    try:
                        WebDriverWait(self.driver, 3).until(
                            lambda d: search_box.is_displayed() and search_box.is_enabled()
                        )
                        logger.info(f"   ✅ SUCCÈS avec méthode: {methode['nom']}")
                        return search_box, methode['nom']
                    except:
                        logger.debug(f"   ⚠️ Élément trouvé mais pas encore interactif: {methode['nom']}")
                        continue
                
            except TimeoutException:
                logger.debug(f"   ⏱️  Timeout pour: {methode['nom']}")
                continue
            except Exception as e:
                logger.debug(f"   ❌ Erreur pour: {methode['nom']} - {str(e)[:50]}")
                continue
        
        # Méthode 11 : JavaScript en dernier recours
        logger.info("   🔍 Tentative 11/11: JavaScript direct...")
        try:
            # Utiliser JavaScript pour trouver l'élément et vérifier qu'il existe
            elem_exists = self.driver.execute_script("""
                var selectors = [
                    'input#searchboxinput',
                    'input[aria-label*="Rechercher"]',
                    'input[aria-label*="Search"]',
                    'input[placeholder*="Rechercher"]',
                    'input[placeholder*="Search"]',
                    'input[class*="searchbox"]',
                    'input[class*="search"]',
                    'header input[type="text"]',
                    'div[role="search"] input',
                    'input[type="text"][autocomplete]'
                ];
                
                for (var i = 0; i < selectors.length; i++) {
                    var elem = document.querySelector(selectors[i]);
                    if (elem && elem.offsetParent !== null) {
                        return selectors[i];  // Retourner le sélecteur qui a fonctionné
                    }
                }
                
                // Dernier recours: premier input text visible
                var allInputs = Array.from(document.querySelectorAll('input[type="text"]'));
                var visibleInput = allInputs.find(el => el.offsetParent !== null);
                return visibleInput ? 'input[type="text"]:visible' : null;
            """)
            
            if elem_exists:
                # Maintenant qu'on sait quel sélecteur fonctionne, le trouver avec Selenium
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, elem_exists)
                    if search_box and search_box.is_displayed() and search_box.is_enabled():
                        logger.info(f"   ✅ SUCCÈS avec JavaScript direct (sélecteur: {elem_exists})")
                        return search_box, "JavaScript"
                except:
                    pass
                
        except Exception as e:
            logger.error(f"   ❌ Échec JavaScript: {str(e)[:50]}")
        
        # Échec total
        logger.error("   ❌ ÉCHEC TOTAL - Aucune méthode n'a fonctionné")
        
        # Debug: sauvegarder screenshot + HTML
        try:
            from pathlib import Path
            debug_dir = Path(__file__).parent.parent / "data" / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            screenshot_path = debug_dir / "debug_echec_recherche.png"
            html_path = debug_dir / "debug_page_source.html"
            
            self.driver.save_screenshot(str(screenshot_path))
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"   💾 Screenshot et HTML sauvegardés: {screenshot_path}, {html_path}")
        except Exception as e:
            logger.debug(f"   ⚠️ Impossible de sauvegarder debug: {e}")
        
        return None, None
    
    def _rechercher_etablissements(self, recherche: str, ville: str) -> tuple[bool, Optional[str]]:
        """
        Effectue une recherche sur Google Maps - MÉTHODE URL DIRECTE
        Utilise directement https://www.google.com/maps/search/{REQUÊTE}
        
        Cette méthode contourne complètement le problème de la barre de recherche !
        
        Args:
            recherche: Type d'artisan (ex: "plombier")
            ville: Ville de recherche (ex: "Paris")
        
        Returns:
            True si la recherche a réussi, False sinon
        """
        max_tentatives = 3
        
        for tentative in range(1, max_tentatives + 1):
            logger.info(f"\n🌐 Recherche Google Maps... (tentative {tentative}/{max_tentatives})")
            
            try:
                # ✅ MÉTHODE URL DIRECTE (pas de barre de recherche à trouver !)
                query = f"{recherche} {ville}"
                url = f"https://www.google.com/maps/search/{quote(query)}"
                
                logger.info(f"   📍 URL directe: {url}")
                
                # ÉTAPE 1 : Ouvrir directement l'URL de recherche
                self.driver.get(url)
                logger.info("   ⏳ Chargement de la page de résultats...")
                time.sleep(5)  # Attendre le chargement
                
                # ✅ ÉTAPE 1.5 : Vérifier et accepter le consentement Google si nécessaire
                if self._est_page_consentement():
                    logger.info("   🍪 Page de consentement détectée, acceptation...")
                    if not self._accepter_consentement():
                        logger.error("   ❌ Échec acceptation consentement")
                        if tentative < max_tentatives:
                            time.sleep(3)
                            continue
                        return False, None
                    # Attendre que Google Maps se charge après consentement
                    logger.info("   ⏳ Attente chargement Google Maps après consentement...")
                    time.sleep(5)
                
                # ÉTAPE 2 : Fermer les popups (cookies, géolocalisation, etc.)
                logger.info("   🗑️  Fermeture des popups...")
                self._fermer_tous_popups()
                time.sleep(1)
                
                # ÉTAPE 3 : Attendre que le panneau de résultats soit chargé
                logger.info("   ⏳ Attente du panneau de résultats...")
                
                # Essayer plusieurs sélecteurs avec timeouts progressifs
                selecteurs_panneau = [
                    ('div[role="feed"]', 20),
                    ('div[role="main"]', 10),
                    ('div[jsaction]', 10),
                    ('div[data-value]', 10),
                    ('div[class*="result"]', 10),
                ]
                
                panneau_trouve = False
                selector_utilise = None
                for selector, timeout in selecteurs_panneau:
                    try:
                        WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"   ✅ Panneau de résultats détecté avec: {selector}")
                        panneau_trouve = True
                        selector_utilise = selector
                        break
                    except TimeoutException:
                        logger.debug(f"   ⏱️  Timeout pour: {selector}")
                        continue
                
                if panneau_trouve:
                    return True, selector_utilise
                
                # Si aucun panneau trouvé, lancer le debug
                logger.warning(f"   ⚠️ Aucun panneau détecté (tentative {tentative})")
                
                if tentative == max_tentatives:
                    # Dernière tentative : lancer le debug complet
                    logger.error("   ❌ Échec: panneau de résultats introuvable après 3 tentatives")
                    logger.info("   🔍 Lancement du debug complet...")
                    self._debug_panneau_resultats()
                    return False, None
                else:
                    logger.info("   🔄 Nouvelle tentative...")
                    time.sleep(3)
                    continue
                
            except Exception as e:
                logger.error(f"   ❌ Erreur inattendue: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())
                if tentative < max_tentatives:
                    time.sleep(3)
                    continue
                return False, None
        
        return False, None
    
    def _debug_panneau_resultats(self):
        """
        Fonction de debug pour comprendre pourquoi le panneau n'est pas trouvé
        Version améliorée basée sur l'analyse du problème
        """
        from pathlib import Path
        
        debug_dir = Path(__file__).parent.parent / "data" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("")
        logger.info("   " + "="*80)
        logger.info("   🔍 DEBUG PANNEAU DE RÉSULTATS - ANALYSE COMPLÈTE")
        logger.info("   " + "="*80)
        logger.info("")
        
        try:
            # 1. Screenshot
            screenshot_path = debug_dir / "debug_panneau_attente.png"
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"   📸 Screenshot sauvegardé: {screenshot_path}")
            
            # 2. URL actuelle
            current_url = self.driver.current_url
            logger.info(f"   🌐 URL actuelle: {current_url}")
            
            # 3. Titre de la page
            page_title = self.driver.title
            logger.info(f"   📄 Titre de la page: {page_title}")
            
            # 4. Vérifier document.readyState
            ready_state = self.driver.execute_script("return document.readyState")
            logger.info(f"   📊 Document readyState: {ready_state}")
            
            # 5. Chercher TOUS les div avec role
            divs_with_role = self.driver.execute_script("""
                var divs = document.querySelectorAll('div[role]');
                var result = [];
                for (var i = 0; i < Math.min(divs.length, 20); i++) {
                    result.push({
                        role: divs[i].getAttribute('role'),
                        id: divs[i].id || 'N/A',
                        className: divs[i].className || 'N/A'
                    });
                }
                return result;
            """)
            logger.info(f"   🔍 Divs avec role trouvés ({len(divs_with_role)}):")
            for div in divs_with_role:
                logger.info(f"      - role='{div['role']}' | id='{div['id']}' | class='{div['className'][:50]}'")
            
            # 6. Chercher spécifiquement div[role="feed"]
            feed_exists = self.driver.execute_script("""
                return document.querySelector('div[role="feed"]') !== null;
            """)
            logger.info(f"   🔍 div[role='feed'] existe: {feed_exists}")
            
            # 7. Chercher div[role="main"]
            main_exists = self.driver.execute_script("""
                return document.querySelector('div[role="main"]') !== null;
            """)
            logger.info(f"   🔍 div[role='main'] existe: {main_exists}")
            
            # 8. Chercher des éléments avec des classes Google Maps
            google_maps_elements = self.driver.execute_script("""
                var elements = document.querySelectorAll('[class*="maps"], [class*="search"], [class*="result"]');
                var result = [];
                for (var i = 0; i < Math.min(elements.length, 10); i++) {
                    result.push({
                        tag: elements[i].tagName,
                        role: elements[i].getAttribute('role') || 'N/A',
                        className: elements[i].className || 'N/A',
                        id: elements[i].id || 'N/A'
                    });
                }
                return result;
            """)
            logger.info(f"   🗺️  Éléments Google Maps trouvés ({len(google_maps_elements)}):")
            for elem in google_maps_elements:
                logger.info(f"      - {elem['tag']} | role='{elem['role']}' | class='{elem['className'][:50]}'")
            
            # 9. Vérifier s'il y a des iframes
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            logger.info(f"   🖼️  Iframes trouvés: {len(iframes)}")
            for idx, iframe in enumerate(iframes, 1):
                src = iframe.get_attribute('src') or 'N/A'
                logger.info(f"      [{idx}] Src: {src[:80]}...")
            
            # 10. Sauvegarder le HTML
            html_path = debug_dir / "debug_panneau_page_source.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"   💾 HTML sauvegardé: {html_path}")
            
            # 11. Vérifier si Google Maps JS est chargé
            google_loaded = self.driver.execute_script("""
                return typeof google !== 'undefined' || typeof window.google !== 'undefined';
            """)
            logger.info(f"   📦 Google Maps JS chargé: {google_loaded}")
            
            # 12. Chercher des messages d'erreur ou CAPTCHA
            error_messages = self.driver.execute_script("""
                var errorTexts = ['captcha', 'error', 'blocked', 'access denied', 'robot', 'verify'];
                var allText = document.body.innerText.toLowerCase();
                var found = [];
                for (var i = 0; i < errorTexts.length; i++) {
                    if (allText.includes(errorTexts[i])) {
                        found.push(errorTexts[i]);
                    }
                }
                return found;
            """)
            if error_messages:
                logger.warning(f"   ⚠️  Messages d'erreur potentiels trouvés: {error_messages}")
            else:
                logger.info("   ✅ Aucun message d'erreur détecté")
            
            # 13. Vérifier la présence d'éléments de résultats (liens vers établissements)
            result_links = self.driver.execute_script("""
                var links = document.querySelectorAll('a[href*="/maps/place/"]');
                return links.length;
            """)
            logger.info(f"   🔗 Liens vers établissements trouvés: {result_links}")
            
            # 14. Vérifier si la page contient "Aucun résultat" ou similaire
            no_results = self.driver.execute_script("""
                var text = document.body.innerText.toLowerCase();
                return text.includes('aucun résultat') || 
                       text.includes('no results') || 
                       text.includes('pas de résultat');
            """)
            if no_results:
                logger.warning("   ⚠️  Message 'Aucun résultat' détecté dans la page")
            
            logger.info("")
            logger.info("   " + "="*80)
            logger.info("   ✅ DEBUG TERMINÉ - Consultez les fichiers dans data/debug/")
            logger.info("   " + "="*80)
            logger.info("")
            
        except Exception as e:
            logger.error(f"   ❌ Erreur lors du debug: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def _debug_etablissements_manquants(self, panneau):
        """
        Debug pour comprendre pourquoi 0 établissements sont trouvés
        """
        from pathlib import Path
        
        debug_dir = Path(__file__).parent.parent / "data" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("")
        logger.info("   " + "="*80)
        logger.info("   🔍 DEBUG ÉTABLISSEMENTS MANQUANTS")
        logger.info("   " + "="*80)
        logger.info("")
        
        try:
            # 1. Sauvegarder le HTML
            html_path = debug_dir / "debug_etablissements_page_source.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"   💾 HTML sauvegardé: {html_path}")
            
            # 2. Chercher TOUS les éléments qui pourraient être des établissements
            logger.info("   🔍 Recherche de tous les éléments potentiels...")
            
            # 2a. Chercher dans le panneau si fourni
            if panneau:
                articles = panneau.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
                logger.info(f"   📋 div[role='article'] trouvés dans panneau: {len(articles)}")
                
                links_place = panneau.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
                logger.info(f"   🔗 a[href*='/maps/place/'] trouvés dans panneau: {len(links_place)}")
                
                all_links = panneau.find_elements(By.CSS_SELECTOR, 'a')
                logger.info(f"   🔗 Tous les liens (a) dans le panneau: {len(all_links)}")
                
                # 3. Chercher avec JavaScript (plus complet)
                logger.info("   🔍 Recherche JavaScript dans le panneau...")
                
                js_results = self.driver.execute_script("""
                    var panneau = arguments[0];
                    var results = {
                        articles: panneau.querySelectorAll('div[role="article"]').length,
                        links_place: panneau.querySelectorAll('a[href*="/maps/place/"]').length,
                        all_links: panneau.querySelectorAll('a').length,
                        all_divs: panneau.querySelectorAll('div').length,
                        divs_with_click: panneau.querySelectorAll('div[onclick], div[role="button"]').length,
                        elements_with_href: panneau.querySelectorAll('[href*="/maps/place/"]').length
                    };
                    return results;
                """, panneau)
            else:
                logger.info("   ⚠️ Pas de panneau fourni, recherche dans toute la page uniquement")
                js_results = {'articles': 0, 'links_place': 0, 'all_links': 0, 'all_divs': 0, 'divs_with_click': 0, 'elements_with_href': 0}
            
            logger.info(f"      div[role='article']: {js_results['articles']}")
            logger.info(f"      a[href*='/maps/place/']: {js_results['links_place']}")
            logger.info(f"      Tous les liens: {js_results['all_links']}")
            logger.info(f"      Tous les div: {js_results['all_divs']}")
            logger.info(f"      Divs cliquables: {js_results['divs_with_click']}")
            logger.info(f"      Éléments avec href maps/place: {js_results['elements_with_href']}")
            
            # 4. Chercher dans TOUTE la page (pas juste le panneau)
            logger.info("   🔍 Recherche dans TOUTE la page...")
            
            page_results = self.driver.execute_script("""
                return {
                    articles: document.querySelectorAll('div[role="article"]').length,
                    links_place: document.querySelectorAll('a[href*="/maps/place/"]').length,
                    all_links: document.querySelectorAll('a').length,
                    divs_with_click: document.querySelectorAll('div[onclick], div[role="button"]').length
                };
            """)
            
            logger.info(f"      Dans TOUTE la page:")
            logger.info(f"         div[role='article']: {page_results['articles']}")
            logger.info(f"         a[href*='/maps/place/']: {page_results['links_place']}")
            logger.info(f"         Tous les liens: {page_results['all_links']}")
            logger.info(f"         Divs cliquables: {page_results['divs_with_click']}")
            
            # 5. Si des éléments sont trouvés dans la page mais pas dans le panneau
            if page_results['links_place'] > 0 and js_results['links_place'] == 0:
                logger.warning("   ⚠️ Des liens /maps/place/ existent dans la page MAIS PAS dans le panneau!")
                logger.warning("   ⚠️ Le panneau div[role='main'] ne contient peut-être pas les résultats")
                logger.info("   🔍 Recherche du VRAI conteneur des résultats...")
                
                # Chercher où sont vraiment les liens
                vrai_conteneur = self.driver.execute_script("""
                    var links = document.querySelectorAll('a[href*="/maps/place/"]');
                    if (links.length > 0) {
                        var parent = links[0].closest('div[role]');
                        if (parent) {
                            return {
                                role: parent.getAttribute('role'),
                                id: parent.id || 'N/A',
                                className: parent.className || 'N/A',
                                selector: parent.id ? '#' + parent.id : 'div[role="' + parent.getAttribute('role') + '"]'
                            };
                        }
                    }
                    return null;
                """)
                
                if vrai_conteneur:
                    logger.info(f"   ✅ VRAI conteneur trouvé:")
                    logger.info(f"      Role: {vrai_conteneur['role']}")
                    logger.info(f"      ID: {vrai_conteneur['id']}")
                    logger.info(f"      Class: {vrai_conteneur['className'][:50]}")
                    logger.info(f"      Sélecteur à utiliser: {vrai_conteneur['selector']}")
            
            # 6. Screenshot pour voir visuellement
            screenshot_path = debug_dir / "debug_etablissements_screenshot.png"
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"   📸 Screenshot sauvegardé: {screenshot_path}")
            
            logger.info("")
            logger.info("   " + "="*80)
            logger.info("   ✅ DEBUG TERMINÉ")
            logger.info("   " + "="*80)
            logger.info("")
            
        except Exception as e:
            logger.error(f"   ❌ Erreur lors du debug: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def _extraire_donnees_etablissement(self, index: int, total: int) -> Optional[Dict]:
        """
        Extrait les données d'un établissement depuis la page détail
        
        Args:
            index: Index de l'établissement (pour les logs)
            total: Total d'établissements à traiter
        
        Returns:
            Dict avec les données ou None si erreur
        """
        info = {
            'nom': None,
            'telephone': None,
            'site_web': None,
            'adresse': None,
            'code_postal': None,
            'ville': None,
            'note': None,
            'nb_avis': None
        }
        
        try:
            # Nom de l'établissement
            try:
                nom_elem = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                )
                info['nom'] = nom_elem.text.strip()
            except:
                logger.warning(f"  ⚠️ Nom non trouvé pour [{index}/{total}]")
            
            # Téléphone
            try:
                tel_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"]')
                aria_label = tel_button.get_attribute('aria-label')
                if aria_label:
                    # Extraire le numéro depuis aria-label
                    tel_match = re.search(r'(\+33|0)[\s\.]?[1-9][\s\.]?(\d{2}[\s\.]?){4}', aria_label)
                    if tel_match:
                        tel_brut = tel_match.group(0).replace(' ', '').replace('.', '').replace('+33', '0')
                        info['telephone'] = self._normaliser_telephone(tel_brut)
            except:
                pass
            
            # Site web
            try:
                site_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id*="authority"]')
                if site_buttons and len(site_buttons) > 0:
                    info['site_web'] = site_buttons[0].get_attribute('href')
                else:
                    info['site_web'] = None
            except:
                info['site_web'] = None
            
            # Adresse
            try:
                adresse_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="address"]')
                aria_label = adresse_button.get_attribute('aria-label')
                if aria_label:
                    info['adresse'] = aria_label.replace('Adresse: ', '').strip()
                    
                    # Extraire code postal et ville
                    cp_match = re.search(r'\b(\d{5})\b', info['adresse'])
                    if cp_match:
                        info['code_postal'] = cp_match.group(1)
                    
                    # Extraire ville (après le code postal)
                    ville_match = re.search(r'\d{5}\s+(.+)', info['adresse'])
                    if ville_match:
                        info['ville'] = ville_match.group(1).strip()
            except:
                pass
            
            # Note
            try:
                note_elem = self.driver.find_element(By.CSS_SELECTOR, 'span[role="img"]')
                info['note'] = self._extraire_note(note_elem)
            except:
                pass
            
            # Nombre d'avis
            try:
                avis_elem = self.driver.find_element(By.XPATH, "//span[contains(text(), 'avis')]")
                info['nb_avis'] = self._extraire_nb_avis(avis_elem)
            except:
                pass
            
            # Logs
            log_parts = [f"[{index}/{total}] {info['nom'] or 'N/A'}"]
            if info['telephone']:
                log_parts.append(f"📞 {info['telephone']}")
            else:
                log_parts.append("❌ Pas de téléphone")
            
            if info['site_web']:
                log_parts.append(f"🌐 {info['site_web'][:30]}...")
            else:
                log_parts.append("❌ Pas de site")
            
            if info['note']:
                log_parts.append(f"⭐ {info['note']}/5")
            
            logger.info(" ".join(log_parts))
            
            return info
            
        except Exception as e:
            logger.error(f"  ❌ Erreur extraction [{index}/{total}]: {e}")
            return None
    
    def _extraire_donnees_depuis_element(self, element, index: int, total: int) -> Optional[Dict]:
        """
        Extrait les données depuis un élément directement (sans panneau de détail)
        
        Args:
            element: Élément Selenium (lien ou div)
            index: Index de l'établissement
            total: Total d'établissements
        
        Returns:
            Dict avec les données ou None
        """
        info = {
            'nom': None,
            'telephone': None,
            'site_web': None,
            'adresse': None,
            'code_postal': None,
            'ville': None,
            'note': None,
            'nb_avis': None
        }
        
        try:
            # Nom de l'établissement
            try:
                # Essayer aria-label d'abord
                nom = element.get_attribute('aria-label')
                if not nom:
                    # Chercher dans les enfants
                    nom_elem = element.find_elements(By.CSS_SELECTOR, 'div[class*="fontHeadline"], h3, div[class*="font"]')
                    if nom_elem:
                        nom = nom_elem[0].text.strip()
                    else:
                        # Prendre le premier texte non vide
                        nom = element.text.split('\n')[0].strip() if element.text else None
                
                info['nom'] = nom
            except:
                pass
            
            # Chercher le parent qui contient toutes les infos
            try:
                parent = element.find_element(By.XPATH, './ancestor::div[@jsaction]') if element.tag_name == 'a' else element
                texte_complet = parent.text
                
                # Téléphone - Pattern français
                tel_match = re.search(r'(?:0|\+33)[1-9](?:[0-9]{8}|[\s.-][0-9]{2}[\s.-][0-9]{2}[\s.-][0-9]{2}[\s.-][0-9]{2})', texte_complet)
                if tel_match:
                    tel_brut = tel_match.group(0).replace(' ', '').replace('.', '').replace('-', '').replace('+33', '0')
                    info['telephone'] = self._normaliser_telephone(tel_brut)
                
                # Adresse - Chercher un pattern d'adresse française
                adresse_match = re.search(r'\d{1,3}\s+(?:rue|avenue|boulevard|place|impasse|chemin|route|allée)[^,]+,\s*\d{5}\s+[A-Za-zÀ-ÿ\s-]+', texte_complet, re.IGNORECASE)
                if adresse_match:
                    adresse = adresse_match.group(0)
                    info['adresse'] = adresse
                    
                    # Extraire code postal et ville
                    cp_match = re.search(r'\b(\d{5})\b', adresse)
                    if cp_match:
                        info['code_postal'] = cp_match.group(1)
                    
                    ville_match = re.search(r'\d{5}\s+([A-Za-zÀ-ÿ\s-]+)', adresse)
                    if ville_match:
                        info['ville'] = ville_match.group(1).strip()
            except:
                pass
            
            # URL du site web (si c'est un lien)
            try:
                if element.tag_name == 'a':
                    href = element.get_attribute('href')
                    if href and '/maps/place/' in href:
                        info['site_web'] = href  # URL Google Maps de l'établissement
            except:
                pass
            
            # Logs
            if info['nom']:
                log_parts = [f"[{index}/{total}] {info['nom']}"]
                if info['telephone']:
                    log_parts.append(f"📞 {info['telephone']}")
                else:
                    log_parts.append("❌ Pas de téléphone")
                
                logger.info(" ".join(log_parts))
            
            return info if info['nom'] else None
            
        except Exception as e:
            logger.error(f"  ❌ Erreur extraction élément [{index}/{total}]: {e}")
            return None
    
    def _extraire_donnees_depuis_detail_page(self, index: int, total: int) -> Optional[Dict]:
        """
        Extrait les données depuis la page de détail ouverte après clic
        
        Args:
            index: Index de l'établissement
            total: Total d'établissements
        
        Returns:
            Dict avec les données ou None
        """
        info = {
            'nom': None,
            'telephone': None,
            'site_web': None,
            'adresse': None,
            'code_postal': None,
            'ville': None,
            'note': None,
            'nb_avis': None
        }
        
        try:
            # Nom
            try:
                nom_elem = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
                info['nom'] = nom_elem.text.strip()
            except:
                pass
            
            # Téléphone
            try:
                tel_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id*="phone"], a[href^="tel:"]')
                for tel_btn in tel_buttons:
                    href = tel_btn.get_attribute('href')
                    if href and href.startswith('tel:'):
                        tel_brut = href.replace('tel:', '').replace(' ', '').replace('+33', '0')
                        info['telephone'] = self._normaliser_telephone(tel_brut)
                        break
                    aria_label = tel_btn.get_attribute('aria-label')
                    if aria_label:
                        tel_match = re.search(r'(\+33|0)[\s\.]?[1-9][\s\.]?(\d{2}[\s\.]?){4}', aria_label)
                        if tel_match:
                            tel_brut = tel_match.group(0).replace(' ', '').replace('.', '').replace('+33', '0')
                            info['telephone'] = self._normaliser_telephone(tel_brut)
                            break
            except:
                pass
            
            # Site web
            try:
                site_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id*="authority"], a[href^="http"]')
                for site_link in site_links:
                    href = site_link.get_attribute('href')
                    if href and ('http://' in href or 'https://' in href) and 'google.com' not in href and 'maps' not in href:
                        info['site_web'] = href
                        break
            except:
                pass
            
            # Adresse
            try:
                adresse_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id*="address"]')
                for adr_btn in adresse_buttons:
                    aria_label = adr_btn.get_attribute('aria-label')
                    if aria_label:
                        info['adresse'] = aria_label.replace('Adresse: ', '').replace('Address: ', '').strip()
                        cp_match = re.search(r'\b(\d{5})\b', info['adresse'])
                        if cp_match:
                            info['code_postal'] = cp_match.group(1)
                        ville_match = re.search(r'\d{5}\s+(.+)', info['adresse'])
                        if ville_match:
                            info['ville'] = ville_match.group(1).strip()
                        break
            except:
                pass
            
            # Note
            try:
                note_elems = self.driver.find_elements(By.CSS_SELECTOR, 'span[role="img"][aria-label*="étoile"], span[role="img"][aria-label*="star"]')
                for note_elem in note_elems:
                    note = self._extraire_note(note_elem)
                    if note:
                        info['note'] = note
                        break
            except:
                pass
            
            # Nombre d'avis
            try:
                avis_elems = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'avis') or contains(text(), 'review')]")
                for avis_elem in avis_elems:
                    nb = self._extraire_nb_avis(avis_elem)
                    if nb:
                        info['nb_avis'] = nb
                        break
            except:
                pass
            
            # Logs
            if info['nom']:
                log_parts = [f"[{index}/{total}] {info['nom']}"]
                if info['telephone']:
                    log_parts.append(f"📞 {info['telephone']}")
                else:
                    log_parts.append("❌ Pas de téléphone")
                
                if info['site_web']:
                    log_parts.append("🌐 Oui")
                else:
                    log_parts.append("❌ Pas de site")
                
                logger.info(" ".join(log_parts))
            
            return info if info['nom'] else None
            
        except Exception as e:
            logger.error(f"  ❌ Erreur extraction détail [{index}/{total}]: {e}")
            return None
    
    def _extraire_donnees_depuis_panneau(self, element, index: int, total: int) -> Optional[Dict]:
        """
        Extrait les données depuis un élément du panneau latéral (plus rapide)
        
        Args:
            element: Élément Selenium du panneau
            index: Index de l'établissement
            total: Total d'établissements
        
        Returns:
            Dict avec les données ou None
        """
        info = {
            'nom': None,
            'telephone': None,
            'site_web': None,
            'adresse': None,
            'code_postal': None,
            'ville': None,
            'note': None,
            'nb_avis': None
        }
        
        try:
            # Nom
            try:
                nom_elem = element.find_element(By.CSS_SELECTOR, 'div[role="button"] span, h3, div[class*="font"]')
                info['nom'] = nom_elem.text.strip()
            except:
                pass
            
            # Cliquer pour ouvrir le détail
            try:
                element.click()
                time.sleep(1.5)  # Attendre que le panneau de détail s'ouvre
            except:
                pass
            
            # Extraire depuis le panneau de détail ouvert
            try:
                # Téléphone
                try:
                    tel_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id*="phone"], a[href^="tel:"]')
                    for tel_btn in tel_buttons:
                        href = tel_btn.get_attribute('href')
                        if href and href.startswith('tel:'):
                            tel_brut = href.replace('tel:', '').replace(' ', '').replace('+33', '0')
                            info['telephone'] = self._normaliser_telephone(tel_brut)
                            break
                        aria_label = tel_btn.get_attribute('aria-label')
                        if aria_label:
                            tel_match = re.search(r'(\+33|0)[\s\.]?[1-9][\s\.]?(\d{2}[\s\.]?){4}', aria_label)
                            if tel_match:
                                tel_brut = tel_match.group(0).replace(' ', '').replace('.', '').replace('+33', '0')
                                info['telephone'] = self._normaliser_telephone(tel_brut)
                                break
                except:
                    pass
                
                # Site web
                try:
                    site_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id*="authority"], a[href^="http"]')
                    for site_link in site_links:
                        href = site_link.get_attribute('href')
                        if href and ('http://' in href or 'https://' in href) and 'google.com' not in href and 'maps' not in href:
                            info['site_web'] = href
                            break
                except:
                    pass
                
                # Adresse
                try:
                    adresse_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id*="address"]')
                    for adr_btn in adresse_buttons:
                        aria_label = adr_btn.get_attribute('aria-label')
                        if aria_label:
                            info['adresse'] = aria_label.replace('Adresse: ', '').strip()
                            cp_match = re.search(r'\b(\d{5})\b', info['adresse'])
                            if cp_match:
                                info['code_postal'] = cp_match.group(1)
                            ville_match = re.search(r'\d{5}\s+(.+)', info['adresse'])
                            if ville_match:
                                info['ville'] = ville_match.group(1).strip()
                            break
                except:
                    pass
                
                # Note
                try:
                    note_elems = self.driver.find_elements(By.CSS_SELECTOR, 'span[role="img"][aria-label*="étoile"], span[role="img"][aria-label*="star"]')
                    for note_elem in note_elems:
                        note = self._extraire_note(note_elem)
                        if note:
                            info['note'] = note
                            break
                except:
                    pass
                
                # Nombre d'avis
                try:
                    avis_elems = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'avis') or contains(text(), 'review')]")
                    for avis_elem in avis_elems:
                        nb = self._extraire_nb_avis(avis_elem)
                        if nb:
                            info['nb_avis'] = nb
                            break
                except:
                    pass
                
            except Exception as e:
                logger.debug(f"  Erreur extraction détail: {e}")
            
            # Logs
            if info['nom']:
                log_parts = [f"[{index}/{total}] {info['nom']}"]
                if info['telephone']:
                    log_parts.append(f"📞 {info['telephone']}")
                else:
                    log_parts.append("❌ Pas de téléphone")
                
                if info['site_web']:
                    log_parts.append(f"🌐 Oui")
                else:
                    log_parts.append("❌ Pas de site")
                
                if info['note']:
                    log_parts.append(f"⭐ {info['note']}/5")
                
                logger.info(" ".join(log_parts))
            
            return info if info['nom'] else None
            
        except Exception as e:
            logger.error(f"  ❌ Erreur extraction panneau [{index}/{total}]: {e}")
            return None
    
    def scraper(self, recherche: str, ville: str, max_results: int = 100, progress_callback=None) -> List[Dict]:
        """
        Scrape Google Maps pour une recherche donnée
        
        Args:
            recherche: Type d'artisan (ex: "plombier", "electricien")
            ville: Ville de recherche (ex: "Paris", "Lyon")
            max_results: Nombre max de résultats à extraire
            progress_callback: Fonction appelée à chaque établissement (index, total, info)
        
        Returns:
            Liste de dicts avec les infos de chaque établissement
        """
        if not self._setup_driver():
            self.is_running = False
            return []
        
        # S'assurer que is_running est True avant de commencer
        self.is_running = True
        resultats = []
        
        try:
            # Recherche - récupérer le sélecteur qui a fonctionné
            recherche_ok, selector_panneau = self._rechercher_etablissements(recherche, ville)
            if not recherche_ok:
                return []
            
            # Utiliser le sélecteur qui a fonctionné, ou un par défaut
            if not selector_panneau:
                selector_panneau = 'div[role="feed"]'
            
            # Scroller pour charger plus de résultats
            logger.info("📜 Scroll du panneau pour charger plus de résultats...")
            self._scroller_panneau_lateral(max_scrolls=15, selector=selector_panneau)
            
            # ✅ FIX : Chercher DIRECTEMENT les établissements dans toute la page
            # Ne pas chercher dans un panneau spécifique qui peut ne pas contenir les résultats
            logger.info("🔍 Récupération des établissements...")
            time.sleep(3)  # Attendre que les résultats se chargent
            
            # Chercher TOUS les liens vers des établissements dans toute la page
            # C'est le sélecteur le plus fiable qui fonctionne toujours
            etablissements_elems = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            
            logger.info(f"✅ {len(etablissements_elems)} établissements trouvés dans la page")
            
            # Si 0 établissements trouvés, essayer des méthodes alternatives
            if len(etablissements_elems) == 0:
                logger.warning("⚠️ Aucun établissement trouvé avec a[href*='/maps/place/'], recherche alternative...")
                
                # Méthode alternative : chercher dans feed ou articles
                try:
                    feed = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"]')
                    if feed:
                        etablissements_elems = feed[0].find_elements(By.CSS_SELECTOR, 'a, div[jsaction]')
                        logger.info(f"   📍 {len(etablissements_elems)} éléments trouvés dans feed")
                    
                    if len(etablissements_elems) == 0:
                        articles = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
                        if articles:
                            etablissements_elems = articles
                            logger.info(f"   📍 {len(articles)} articles trouvés")
                except:
                    pass
            
            # Si toujours 0, lancer le debug
            if len(etablissements_elems) == 0:
                logger.warning("⚠️ Aucun établissement trouvé, lancement du debug...")
                try:
                    panneau_debug = self.driver.find_element(By.CSS_SELECTOR, 'div[role="main"]')
                    self._debug_etablissements_manquants(panneau_debug)
                except:
                    self._debug_etablissements_manquants(None)
                return []  # Retourner vide si aucun établissement trouvé
            
            # Limiter au max_results
            etablissements_elems = etablissements_elems[:max_results]
            
            # Extraire les données pour chaque établissement
            for i, elem in enumerate(etablissements_elems, 1):
                if not self.is_running:
                    logger.info("⏹️ Scraping arrêté par l'utilisateur")
                    break
                
                try:
                    # Scroll jusqu'à l'élément pour le rendre visible
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.5)
                    
                    # ✅ FIX : Extraire les données directement depuis l'élément
                    # Si c'est un lien, cliquer pour ouvrir le détail, sinon extraire depuis l'élément
                    if elem.tag_name == 'a' and elem.get_attribute('href') and '/maps/place/' in elem.get_attribute('href'):
                        # C'est un lien vers un établissement, cliquer pour ouvrir le détail
                        try:
                            elem.click()
                            time.sleep(1.5)  # Attendre que le panneau de détail s'ouvre
                            info = self._extraire_donnees_depuis_detail_page(i, len(etablissements_elems))
                        except:
                            # Si le clic échoue, extraire depuis l'élément directement
                            info = self._extraire_donnees_depuis_element(elem, i, len(etablissements_elems))
                    else:
                        # C'est un div ou autre élément, extraire directement
                        info = self._extraire_donnees_depuis_element(elem, i, len(etablissements_elems))
                    
                    if info:
                        info['recherche'] = recherche
                        info['ville_recherche'] = ville
                        resultats.append(info)
                        self.scraped_count += 1
                        
                        if progress_callback:
                            progress_callback(i, len(etablissements_elems), info)
                    
                    # Pause entre établissements
                    time.sleep(random.uniform(1, 2))
                    
                except StaleElementReferenceException:
                    logger.warning(f"  ⚠️ Élément stale [{i}/{len(etablissements_elems)}], skip")
                    continue
                except Exception as e:
                    logger.error(f"  ❌ Erreur établissement [{i}/{len(etablissements_elems)}]: {e}")
                    continue
            
            logger.info(f"✅ Scraping terminé: {len(resultats)} établissements extraits")
            return resultats
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return resultats
        
        finally:
            # Ne pas fermer le driver automatiquement (sera fermé par stop() ou à la fin)
            if not self.is_running:
                if self.driver:
                    try:
                        self.driver.quit()
                        logger.info("🔒 Chrome driver fermé")
                    except:
                        pass
    
    def stop(self):
        """Arrête le scraping en cours et ferme le driver"""
        self.is_running = False
        logger.info("⏹️ Arrêt du scraping demandé...")
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔒 Chrome driver fermé")
            except:
                pass
    
    def get_scraped_count(self) -> int:
        """Retourne le nombre d'établissements scrapés"""
        return self.scraped_count

