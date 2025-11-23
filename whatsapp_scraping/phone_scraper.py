"""
Scraper simplifié - Téléphones uniquement
"""
import re
import time
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneScraper:
    """Scraper pour extraire uniquement les téléphones d'artisans"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
    
    def scraper_google_maps(self, metier: str, ville: str, max_results: int = 20) -> List[Dict]:
        """
        Scrape Google Maps pour trouver téléphones d'artisans
        """
        logger.info(f"🔍 Recherche: {metier} à {ville}")
        
        artisans = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                query = f"{metier} {ville}"
                url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3)
                
                # Scroller pour charger plus de résultats
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                # Extraire les résultats
                result_cards = page.query_selector_all('div[role="article"]')
                
                for card in result_cards[:max_results]:
                    try:
                        artisan = self._extraire_info_carte(card, metier, ville)
                        if artisan and artisan.get('telephone'):
                            artisan['source'] = 'google_maps'
                            artisans.append(artisan)
                    except Exception as e:
                        logger.warning(f"Erreur extraction: {e}")
                        continue
                
                browser.close()
        
        except Exception as e:
            logger.error(f"Erreur scraping Google Maps: {e}")
        
        logger.info(f"✅ {len(artisans)} artisans trouvés avec téléphone")
        return artisans
    
    def _extraire_info_carte(self, card, metier: str, ville: str) -> Optional[Dict]:
        """Extrait les infos minimales d'une carte"""
        try:
            artisan = {
                'type_artisan': metier,
                'ville': ville
            }
            
            # Nom entreprise
            nom_elem = card.query_selector('div[role="heading"]')
            if nom_elem:
                artisan['nom_entreprise'] = nom_elem.inner_text().strip()
            
            # Téléphone (PRIORITÉ)
            tel_elem = card.query_selector('button[data-item-id*="phone"]')
            if tel_elem:
                tel_text = tel_elem.get_attribute('aria-label') or tel_elem.inner_text()
                tel_match = re.search(r'(\d{2}[\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2})', tel_text)
                if tel_match:
                    tel_clean = re.sub(r'[\s.]', '', tel_match.group(1))
                    artisan['telephone'] = tel_clean
            
            # Adresse (pour département)
            adresse_elem = card.query_selector('span[aria-label*="Adresse"]')
            if not adresse_elem:
                adresse_elem = card.query_selector('button[data-item-id*="address"]')
            if adresse_elem:
                adresse = adresse_elem.inner_text().strip()
                match = re.search(r'(\d{5})', adresse)
                if match:
                    code_postal = match.group(1)
                    artisan['departement'] = code_postal[:2]
            
            return artisan if artisan.get('telephone') else None
            
        except Exception as e:
            logger.warning(f"Erreur extraction carte: {e}")
            return None
    
    def scraper_pages_jaunes(self, metier: str, ville: str, max_results: int = 20) -> List[Dict]:
        """
        Scrape Pages Jaunes pour téléphones
        """
        logger.info(f"🔍 Pages Jaunes: {metier} à {ville}")
        
        artisans = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                query = f"{metier} {ville}"
                url = f"https://www.pagesjaunes.fr/recherche?quoiqui={metier}&ou={ville}"
                
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3)
                
                # Extraire résultats
                result_items = page.query_selector_all('.bi-content')
                
                for item in result_items[:max_results]:
                    try:
                        artisan = self._extraire_pages_jaunes(item, metier, ville)
                        if artisan and artisan.get('telephone'):
                            artisan['source'] = 'pages_jaunes'
                            artisans.append(artisan)
                    except Exception as e:
                        logger.warning(f"Erreur extraction PJ: {e}")
                        continue
                
                browser.close()
        
        except Exception as e:
            logger.error(f"Erreur scraping Pages Jaunes: {e}")
        
        logger.info(f"✅ {len(artisans)} artisans trouvés (Pages Jaunes)")
        return artisans
    
    def _extraire_pages_jaunes(self, item, metier: str, ville: str) -> Optional[Dict]:
        """Extrait infos depuis Pages Jaunes"""
        try:
            artisan = {
                'type_artisan': metier,
                'ville': ville
            }
            
            # Nom
            nom_elem = item.query_selector('.denomination-links')
            if nom_elem:
                artisan['nom_entreprise'] = nom_elem.inner_text().strip()
            
            # Téléphone
            tel_elem = item.query_selector('.number')
            if tel_elem:
                tel_text = tel_elem.inner_text()
                tel_match = re.search(r'(\d{2}[\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2})', tel_text)
                if tel_match:
                    tel_clean = re.sub(r'[\s.]', '', tel_match.group(1))
                    artisan['telephone'] = tel_clean
            
            return artisan if artisan.get('telephone') else None
            
        except Exception as e:
            return None

