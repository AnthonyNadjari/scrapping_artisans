"""
Scraper Google Maps pour trouver des artisans
"""
import time
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleMapsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def rechercher_artisans(self, metier: str, ville: str, max_results: int = 20) -> List[Dict]:
        """
        Recherche des artisans sur Google Maps
        """
        logger.info(f"🔍 Recherche: {metier} à {ville}")
        
        query = f"{metier} {ville}"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        try:
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)  # Attendre le chargement
            
            # Scroller pour charger plus de résultats
            for _ in range(3):
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            
            # Extraire les résultats
            artisans = []
            
            # Sélecteur pour les cartes de résultats
            result_cards = self.page.query_selector_all('div[role="article"]')
            
            for card in result_cards[:max_results]:
                try:
                    artisan = self._extraire_info_carte(card)
                    if artisan:
                        artisan['source'] = 'google_maps'
                        artisan['type_artisan'] = metier
                        artisan['ville'] = ville
                        artisans.append(artisan)
                except Exception as e:
                    logger.warning(f"Erreur extraction carte: {e}")
                    continue
            
            logger.info(f"✅ {len(artisans)} artisans trouvés pour {metier} à {ville}")
            return artisans
            
        except PlaywrightTimeout:
            logger.error(f"⏱️ Timeout pour {metier} à {ville}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur recherche {metier} à {ville}: {e}")
            return []
    
    def _extraire_info_carte(self, card) -> Optional[Dict]:
        """Extrait les informations d'une carte de résultat"""
        try:
            artisan = {}
            
            # Nom de l'entreprise
            nom_elem = card.query_selector('div[role="heading"]')
            if nom_elem:
                artisan['nom_entreprise'] = nom_elem.inner_text().strip()
            
            # Adresse
            adresse_elem = card.query_selector('span[aria-label*="Adresse"]')
            if not adresse_elem:
                adresse_elem = card.query_selector('button[data-item-id*="address"]')
            if adresse_elem:
                artisan['adresse'] = adresse_elem.inner_text().strip()
                # Extraire code postal et ville
                match = re.search(r'(\d{5})\s+(.+)', artisan['adresse'])
                if match:
                    artisan['code_postal'] = match.group(1)
                    artisan['ville'] = match.group(2)
                    artisan['departement'] = artisan['code_postal'][:2]
            
            # Téléphone
            tel_elem = card.query_selector('button[data-item-id*="phone"]')
            if tel_elem:
                tel_text = tel_elem.get_attribute('aria-label') or tel_elem.inner_text()
                tel_match = re.search(r'(\d{2}[\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2}[\s.]?\d{2})', tel_text)
                if tel_match:
                    artisan['telephone'] = re.sub(r'[\s.]', '', tel_match.group(1))
            
            # Site web
            site_elem = card.query_selector('a[href^="http"]')
            if site_elem:
                href = site_elem.get_attribute('href')
                if href and 'google.com' not in href:
                    artisan['site_web'] = href
                    artisan['a_site_web'] = True
            
            # Note et avis
            note_elem = card.query_selector('span[aria-label*="étoiles"]')
            if note_elem:
                note_text = note_elem.get_attribute('aria-label') or ''
                note_match = re.search(r'(\d+[.,]\d+)', note_text)
                if note_match:
                    artisan['avis_google_note'] = float(note_match.group(1).replace(',', '.'))
            
            avis_elem = card.query_selector('span[aria-label*="avis"]')
            if avis_elem:
                avis_text = avis_elem.get_attribute('aria-label') or ''
                avis_match = re.search(r'(\d+)', avis_text)
                if avis_match:
                    artisan['avis_google_count'] = int(avis_match.group(1))
            
            # Lien Google Maps
            link_elem = card.query_selector('a[href*="/maps/place/"]')
            if link_elem:
                artisan['lien_google_maps'] = link_elem.get_attribute('href')
            
            # Extraire prénom/nom si possible
            if artisan.get('nom_entreprise'):
                # Tenter d'extraire prénom/nom du nom d'entreprise
                nom_parts = artisan['nom_entreprise'].split()
                if len(nom_parts) >= 2:
                    artisan['prenom'] = nom_parts[0]
                    artisan['nom'] = ' '.join(nom_parts[1:])
            
            return artisan if artisan.get('nom_entreprise') else None
            
        except Exception as e:
            logger.warning(f"Erreur extraction: {e}")
            return None
    
    def scraper_metier_ville(self, metier: str, ville: str, max_results: int = 20) -> List[Dict]:
        """Méthode principale pour scraper un métier dans une ville"""
        return self.rechercher_artisans(metier, ville, max_results)

