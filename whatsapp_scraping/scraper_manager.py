"""
Gestionnaire de scraping WhatsApp - Téléphones uniquement
"""
import time
import requests
from typing import List, Dict, Optional
from whatsapp_scraping.phone_scraper import PhoneScraper
from whatsapp_database.queries import ajouter_artisan
from config.whatsapp_settings import DEPARTEMENTS_PRIORITAIRES

GEO_API_BASE = "https://geo.api.gouv.fr"
from whatsapp.whatsapp_manager import WhatsAppManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppScraperManager:
    """Gère le scraping et la vérification WhatsApp"""
    
    def __init__(self, verifier_whatsapp: bool = True):
        self.verifier_whatsapp = verifier_whatsapp
        self.whatsapp_manager = WhatsAppManager() if verifier_whatsapp else None
        self.stats = {
            'total_trouves': 0,
            'total_ajoutes': 0,
            'avec_whatsapp': 0,
            'sans_whatsapp': 0,
            'erreurs': 0,
        }
    
    def get_communes_departement(self, code_dept: str) -> List[Dict]:
        """Récupère toutes les communes d'un département"""
        try:
            url = f"{GEO_API_BASE}/departements/{code_dept}/communes"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                communes = response.json()
                # Trier par population (plus petites d'abord)
                return sorted(communes, key=lambda x: x.get('population', 999999))
            return []
        except Exception as e:
            logger.error(f"Erreur récupération communes: {e}")
            return []
    
    def scraper_metier_commune(self, metier: str, commune: Dict, 
                            use_google_maps: bool = True,
                            use_pages_jaunes: bool = False,
                            callback_progress=None) -> int:
        """
        Scrape un métier dans une commune et vérifie WhatsApp
        """
        ville = commune.get('nom', '')
        code_postal = commune.get('codesPostaux', [None])[0]
        population = commune.get('population', 0)
        
        logger.info(f"🔍 {metier} - {ville} ({code_postal}) - {population} hab.")
        
        artisans_trouves = []
        
        # Google Maps
        if use_google_maps:
            try:
                scraper = PhoneScraper(headless=True)
                results = scraper.scraper_google_maps(metier, ville, max_results=20)
                artisans_trouves.extend(results)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Erreur Google Maps: {e}")
                self.stats['erreurs'] += 1
        
        # Pages Jaunes
        if use_pages_jaunes:
            try:
                scraper = PhoneScraper(headless=True)
                results = scraper.scraper_pages_jaunes(metier, ville, max_results=20)
                artisans_trouves.extend(results)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Erreur Pages Jaunes: {e}")
                self.stats['erreurs'] += 1
        
        # Ajouter à la BDD et vérifier WhatsApp
        ajoutes = 0
        for artisan in artisans_trouves:
            try:
                # Compléter infos
                if not artisan.get('code_postal') and code_postal:
                    artisan['departement'] = code_postal[:2]
                
                # Ajouter en BDD (anti-doublons automatique)
                artisan_id = ajouter_artisan(artisan)
                ajoutes += 1
                self.stats['total_ajoutes'] += 1
                
                # Vérifier WhatsApp si demandé
                if self.verifier_whatsapp and self.whatsapp_manager and artisan.get('telephone'):
                    is_whatsapp, error = self.whatsapp_manager.verifier_whatsapp(artisan['telephone'])
                    if is_whatsapp:
                        from whatsapp_database.queries import marquer_whatsapp_verifie
                        marquer_whatsapp_verifie(artisan_id, True)
                        self.stats['avec_whatsapp'] += 1
                    else:
                        from whatsapp_database.queries import marquer_whatsapp_verifie
                        marquer_whatsapp_verifie(artisan_id, False)
                        self.stats['sans_whatsapp'] += 1
                    
                    time.sleep(1)  # Rate limiting vérification
                
            except Exception as e:
                logger.warning(f"Erreur ajout artisan: {e}")
                self.stats['erreurs'] += 1
        
        self.stats['total_trouves'] += len(artisans_trouves)
        
        if callback_progress:
            callback_progress({
                'metier': metier,
                'ville': ville,
                'trouves': len(artisans_trouves),
                'ajoutes': ajoutes,
                'stats': self.stats.copy(),
            })
        
        return ajoutes
    
    def scraper_campagne(self, metiers: List[str], departements: List[str],
                        priorite_villages: bool = True,
                        use_google_maps: bool = True,
                        use_pages_jaunes: bool = False,
                        callback_progress=None):
        """
        Lance une campagne de scraping complète
        """
        logger.info(f"🚀 Démarrage campagne: {len(metiers)} métiers, {len(departements)} départements")
        
        for dept in departements:
            communes = self.get_communes_departement(dept)
            
            if priorite_villages:
                communes = [c for c in communes if c.get('population', 999999) < 5000]
            
            for commune in communes:
                for metier in metiers:
                    self.scraper_metier_commune(
                        metier, commune,
                        use_google_maps=use_google_maps,
                        use_pages_jaunes=use_pages_jaunes,
                        callback_progress=callback_progress
                    )
        
        logger.info(f"✅ Campagne terminée: {self.stats}")
        return self.stats

