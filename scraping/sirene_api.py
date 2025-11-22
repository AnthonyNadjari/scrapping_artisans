"""
API Base SIRENE pour récupérer des entreprises artisanales
"""
import requests
import time
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Codes NAF des artisans (exemples principaux)
CODES_NAF_ARTISANS = {
    "plombier": "4322A",
    "chauffagiste": "4322A",
    "électricien": "4321A",
    "maçon": "4120A",
    "menuisier": "4332Z",
    "peintre": "4334Z",
    "carreleur": "4331Z",
    "couvreur": "4391A",
    "serrurier": "2561Z",
    "vitrier": "2512Z",
    "paysagiste": "8130Z",
}

class SireneAPI:
    def __init__(self, api_key: Optional[str] = None):
        """
        API SIRENE nécessite une clé API gratuite
        Inscription: https://api.insee.fr/
        """
        self.api_key = api_key
        self.base_url = "https://api.insee.fr/entreprises/sirene/V3"
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def rechercher_artisans(self, code_naf: str, code_postal: str, limit: int = 100) -> List[Dict]:
        """
        Recherche des entreprises par code NAF et code postal
        """
        if not self.api_key:
            logger.warning("⚠️ Pas de clé API SIRENE, skip")
            return []
        
        try:
            url = f"{self.base_url}/siret"
            params = {
                "q": f"activitePrincipaleUniteLegale:{code_naf} AND codePostalEtablissement:{code_postal}",
                "nombre": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                artisans = []
                
                for etablissement in data.get('etablissements', []):
                    unite_legale = etablissement.get('uniteLegale', {})
                    adresse = etablissement.get('adresseEtablissement', {})
                    
                    artisan = {
                        'nom_entreprise': unite_legale.get('denominationUniteLegale') or \
                                        f"{unite_legale.get('prenom1UniteLegale', '')} {unite_legale.get('nomUniteLegale', '')}".strip(),
                        'prenom': unite_legale.get('prenom1UniteLegale'),
                        'nom': unite_legale.get('nomUniteLegale'),
                        'siret': etablissement.get('siret'),
                        'adresse': f"{adresse.get('numeroVoieEtablissement', '')} {adresse.get('typeVoieEtablissement', '')} {adresse.get('libelleVoieEtablissement', '')}".strip(),
                        'code_postal': adresse.get('codePostalEtablissement'),
                        'ville': adresse.get('libelleCommuneEtablissement'),
                        'departement': adresse.get('codePostalEtablissement', '')[:2] if adresse.get('codePostalEtablissement') else None,
                        'source': 'sirene',
                        'date_creation': unite_legale.get('dateCreationUniteLegale'),
                    }
                    
                    if artisan['nom_entreprise']:
                        artisans.append(artisan)
                
                logger.info(f"✅ {len(artisans)} entreprises trouvées dans SIRENE pour {code_postal}")
                return artisans
            else:
                logger.warning(f"⚠️ Erreur API SIRENE: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur SIRENE: {e}")
            return []
    
    def get_code_naf(self, metier: str) -> Optional[str]:
        """Retourne le code NAF pour un métier"""
        return CODES_NAF_ARTISANS.get(metier.lower())

