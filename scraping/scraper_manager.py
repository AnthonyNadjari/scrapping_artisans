"""
Gestionnaire principal du scraping
"""
import time
import requests
from typing import List, Dict, Optional
from database.queries import ajouter_artisan
from scraping.google_maps_scraper import GoogleMapsScraper
from scraping.sirene_api import SireneAPI
from config.settings import METIERS, DEPARTEMENTS_PRIORITAIRES, GEO_API_BASE
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperManager:
    def __init__(self, use_google_maps: bool = True, use_sirene: bool = False, sirene_api_key: Optional[str] = None):
        self.use_google_maps = use_google_maps
        self.use_sirene = use_sirene
        self.sirene_api = SireneAPI(sirene_api_key) if use_sirene else None
        self.stats = {
            'total_trouves': 0,
            'total_ajoutes': 0,
            'doublons_evites': 0,
            'erreurs': 0,
        }
    
    def get_communes_departement(self, code_dept: str) -> List[Dict]:
        """Récupère toutes les communes d'un département via API Geo"""
        try:
            url = f"{GEO_API_BASE}/departements/{code_dept}/communes"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                communes = response.json()
                # Trier par population (plus petites d'abord)
                communes_triees = sorted(
                    communes,
                    key=lambda x: x.get('population', 999999)
                )
                return communes_triees
            return []
        except Exception as e:
            logger.error(f"Erreur récupération communes {code_dept}: {e}")
            return []
    
    def scraper_metier_commune(self, metier: str, commune: Dict, callback_progress=None) -> int:
        """
        Scrape un métier dans une commune
        Retourne le nombre d'artisans ajoutés
        """
        ville = commune.get('nom', '')
        code_postal = commune.get('codesPostaux', [None])[0]
        population = commune.get('population', 0)
        
        logger.info(f"🔍 {metier} - {ville} ({code_postal}) - {population} hab.")
        
        artisans_trouves = []
        
        # Google Maps
        if self.use_google_maps:
            try:
                with GoogleMapsScraper(headless=True) as scraper:
                    results = scraper.rechercher_artisans(metier, ville, max_results=20)
                    artisans_trouves.extend(results)
                    time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Erreur Google Maps: {e}")
                self.stats['erreurs'] += 1
        
        # SIRENE
        if self.use_sirene and self.sirene_api and code_postal:
            try:
                code_naf = self.sirene_api.get_code_naf(metier)
                if code_naf:
                    results = self.sirene_api.rechercher_artisans(code_naf, code_postal, limit=50)
                    artisans_trouves.extend(results)
                    time.sleep(1)  # Rate limiting API
            except Exception as e:
                logger.error(f"Erreur SIRENE: {e}")
                self.stats['erreurs'] += 1
        
        # Ajouter à la BDD (avec anti-doublons)
        ajoutes = 0
        for artisan in artisans_trouves:
            try:
                # Compléter les infos manquantes
                if not artisan.get('code_postal') and code_postal:
                    artisan['code_postal'] = code_postal
                if not artisan.get('departement') and code_postal:
                    artisan['departement'] = code_postal[:2]
                
                artisan_id = ajouter_artisan(artisan)
                ajoutes += 1
                self.stats['total_ajoutes'] += 1
                
            except Exception as e:
                logger.warning(f"Erreur ajout artisan: {e}")
                self.stats['doublons_evites'] += 1
        
        self.stats['total_trouves'] += len(artisans_trouves)
        
        if callback_progress:
            callback_progress({
                'metier': metier,
                'ville': ville,
                'trouves': len(artisans_trouves),
                'ajoutes': ajoutes,
            })
        
        return ajoutes
    
    def scraper_campagne(self, metiers: List[str], departements: List[str], 
                        priorite_villages: bool = True, callback_progress=None):
        """
        Lance une campagne de scraping complète
        """
        logger.info(f"🚀 Démarrage campagne: {len(metiers)} métiers, {len(departements)} départements")
        
        total_communes = 0
        communes_scrapees = 0
        
        for dept in departements:
            communes = self.get_communes_departement(dept)
            
            if priorite_villages:
                # Filtrer villages < 5000 hab
                communes = [c for c in communes if c.get('population', 999999) < 5000]
            
            total_communes += len(communes) * len(metiers)
            
            for commune in communes:
                for metier in metiers:
                    if callback_progress and hasattr(callback_progress, '__call__'):
                        # Vérifier si pause demandée
                        if hasattr(self, '_pause') and self._pause:
                            logger.info("⏸️ Pause demandée")
                            while self._pause:
                                time.sleep(1)
                    
                    self.scraper_metier_commune(metier, commune, callback_progress)
                    communes_scrapees += 1
                    
                    if callback_progress:
                        callback_progress({
                            'total_communes': total_communes,
                            'communes_scrapees': communes_scrapees,
                            'stats': self.stats.copy(),
                        })
        
        logger.info(f"✅ Campagne terminée: {self.stats}")
        return self.stats

