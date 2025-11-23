"""
API SIRENE - Interface avec l'API INSEE
Récupère les artisans par code NAF et département
100% GRATUIT - Données publiques
Utilise une clé API unique pour l'authentification
"""
import requests
import time
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SireneAPI:
    """
    Interface avec l'API SIRENE de l'INSEE
    Récupère les artisans par code NAF et département
    Utilise une clé API unique pour l'authentification (header X-INSEE-Api-Key-Integration)
    
    IMPORTANT: Cette classe n'accepte qu'UN SEUL argument: api_key
    """
    
    def __init__(self, api_key: str):
        """
        Initialise l'API SIRENE avec une clé API unique
        
        Args:
            api_key: Clé API INSEE unique (utilisée dans le header X-INSEE-Api-Key-Integration)
        
        Raises:
            TypeError: Si api_key n'est pas fourni
        """
        if not api_key:
            raise ValueError("api_key est requis")
        
        self.api_key = str(api_key)
        # Nouvelle URL de l'API SIRENE (2024/2025)
        self.base_url = "https://api.insee.fr/api-sirene/3.11"
    
    def chercher_artisans(self, code_naf: str, departement: str, limite: int = 1000) -> List[Dict]:
        """
        Cherche artisans par code NAF et département
        
        Args:
            code_naf: Code NAF (ex: "43.22A" pour plomberie)
            departement: Code département (ex: "77")
            limite: Nombre max de résultats (max 10000 par requête)
        
        Returns:
            Liste d'artisans avec leurs informations
        """
        url = f"{self.base_url}/siret"
        
        headers = {
            "X-INSEE-Api-Key-Integration": self.api_key,
            "Accept": "application/json"
        }
        
        # Construire la requête avec la syntaxe correcte de l'API 3.11
        # Syntaxe qui fonctionne : codePostalEtablissement:{departement}* AND activitePrincipaleUniteLegale:{code_naf}
        # Note: La syntaxe departementUniteLegale ne fonctionne pas avec le paramètre champs
        query = f"codePostalEtablissement:{departement}* AND activitePrincipaleUniteLegale:{code_naf}"
        
        params = {
            "q": query,
            "nombre": min(limite, 10000),  # Max 10000 par requête
            # Champs disponibles selon la doc API 3.11
            "champs": "siret,denominationUniteLegale,nomUniteLegale,prenomUsuelUniteLegale,numeroVoieEtablissement,typeVoieEtablissement,libelleVoieEtablissement,codePostalEtablissement,libelleCommuneEtablissement,activitePrincipaleUniteLegale"
        }
        
        artisans = []
        page = 1
        nombre_par_page = 20  # Nouvelle API limite à 20 par page
        # Limiter à 20 pages max (400 résultats) pour éviter rate limit
        # L'utilisateur peut ajuster la limite dans l'interface
        max_pages = min((limite // nombre_par_page) + 1, 20)  # Max 20 pages = 400 résultats
        
        try:
            while len(artisans) < limite and page <= max_pages:
                params["nombre"] = nombre_par_page
                params["debut"] = (page - 1) * nombre_par_page
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 401:
                    # Clé API invalide
                    logger.error("❌ ERREUR 401: Clé API invalide ou expirée")
                    logger.error("📋 SOLUTION:")
                    logger.error("   1. Va sur https://portail-api.insee.fr/")
                    logger.error("   2. Connexion avec ton compte")
                    logger.error("   3. 'Mes applications' > ton app")
                    logger.error("   4. Copie la clé API (Consumer Key)")
                    raise Exception("Clé API INSEE invalide. Vérifiez votre clé dans la configuration.")
                
                if response.status_code == 403:
                    logger.error("❌ ERREUR 403: Pas d'accès à l'API SIRENE")
                    logger.error("📋 Il faut souscrire à l'API sur le portail")
                    raise Exception("Pas d'accès à l'API SIRENE. Souscrivez à l'API sur le portail.")
                
                if response.status_code == 404:
                    logger.error("❌ ERREUR 404: URL incorrecte")
                    logger.error(f"   URL testée: {url}")
                    raise Exception("URL de l'API incorrecte. Vérifiez la configuration.")
                
                if response.status_code == 429:
                    # Rate limit atteint - attendre plus longtemps et augmenter délai suivant
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"⚠️ Rate limit atteint, attente {retry_after}s...")
                    logger.info("💡 Conseil: Réduisez la limite de résultats ou augmentez les délais")
                    time.sleep(retry_after)
                    # Augmenter le délai après rate limit
                    time.sleep(2)
                    continue
                
                if response.status_code != 200:
                    logger.error(f"❌ Erreur API SIRENE: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                etablissements = data.get("etablissements", [])
                
                if not etablissements:
                    break
                
                for etab in etablissements:
                    unite_legale = etab.get("uniteLegale", {})
                    
                    # Nom entreprise ou nom + prénom (format comme dans le code fourni)
                    nom_entreprise = unite_legale.get("denominationUniteLegale")
                    if not nom_entreprise:
                        nom_entreprise = unite_legale.get("nomUniteLegale", "")
                    
                    # Si toujours pas de nom, utiliser nom + prénom
                    if not nom_entreprise:
                        nom = unite_legale.get("nomUniteLegale", "")
                        prenom = unite_legale.get("prenomUsuelUniteLegale", "")
                        nom_entreprise = f"{nom} {prenom}".strip() if prenom else nom
                    
                    if not nom_entreprise:
                        nom_entreprise = "Inconnu"
                    
                    # Extraire les champs d'adresse
                    # Si on utilise le paramètre "champs", les données sont dans adresseEtablissement
                    # Sinon, elles sont directement dans etab
                    adresse_etab = etab.get("adresseEtablissement", {})
                    if not adresse_etab:
                        # Si pas d'objet adresseEtablissement, les champs sont directement dans etab
                        adresse_dict = {
                            "numeroVoieEtablissement": etab.get("numeroVoieEtablissement", ""),
                            "typeVoieEtablissement": etab.get("typeVoieEtablissement", ""),
                            "libelleVoieEtablissement": etab.get("libelleVoieEtablissement", ""),
                            "codePostalEtablissement": etab.get("codePostalEtablissement", ""),
                            "libelleCommuneEtablissement": etab.get("libelleCommuneEtablissement", "")
                        }
                    else:
                        # Structure complète avec adresseEtablissement
                        adresse_dict = {
                            "numeroVoieEtablissement": adresse_etab.get("numeroVoieEtablissement", ""),
                            "typeVoieEtablissement": adresse_etab.get("typeVoieEtablissement", ""),
                            "libelleVoieEtablissement": adresse_etab.get("libelleVoieEtablissement", ""),
                            "codePostalEtablissement": adresse_etab.get("codePostalEtablissement", ""),
                            "libelleCommuneEtablissement": adresse_etab.get("libelleCommuneEtablissement", "")
                        }
                    
                    artisan = {
                        "siret": etab.get("siret"),
                        "nom_entreprise": nom_entreprise or "N/A",
                        "nom": unite_legale.get("nomUniteLegale", ""),
                        "prenom": unite_legale.get("prenomUsuelUniteLegale", ""),
                        "adresse": self._formater_adresse(adresse_dict),
                        "code_postal": adresse_dict.get("codePostalEtablissement", ""),
                        "ville": adresse_dict.get("libelleCommuneEtablissement", ""),
                        "departement": departement,
                        "code_naf": code_naf,
                        "source": "sirene"
                    }
                    
                    artisans.append(artisan)
                
                logger.info(f"📊 Page {page}: {len(etablissements)} établissements, total: {len(artisans)}")
                
                # Si moins de résultats que demandé, on a fini
                if len(etablissements) < nombre_par_page:
                    logger.info(f"✅ Fin des résultats (page {page})")
                    break
                
                page += 1
                # Délai entre pages pour éviter rate limit (1-2 secondes)
                # Plus de pages = plus de délai pour être sûr
                if page <= 10:
                    time.sleep(1.0)  # 1 seconde pour les 10 premières pages
                else:
                    time.sleep(2.0)  # 2 secondes pour les pages suivantes
                
                if len(artisans) >= limite:
                    break
            
            logger.info(f"✅ {len(artisans)} artisans récupérés pour {code_naf} dans {departement}")
            return artisans
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche SIRENE: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return artisans
    
    def _formater_adresse(self, adresse: dict) -> str:
        """Formate l'adresse complète"""
        parts = []
        
        if adresse.get("numeroVoieEtablissement"):
            parts.append(str(adresse["numeroVoieEtablissement"]))
        
        if adresse.get("typeVoieEtablissement"):
            parts.append(adresse["typeVoieEtablissement"])
        
        if adresse.get("libelleVoieEtablissement"):
            parts.append(adresse["libelleVoieEtablissement"])
        
        return " ".join(parts).strip()
    
    def chercher_par_metier(self, metier: str, code_naf: str, departements: List[str], limite_par_dept: int = 1000) -> List[Dict]:
        """
        Cherche artisans pour un métier dans plusieurs départements
        
        Args:
            metier: Nom du métier (ex: "plombier")
            code_naf: Code NAF correspondant
            departements: Liste des départements
            limite_par_dept: Limite par département
        
        Returns:
            Liste complète d'artisans avec type_artisan ajouté
        """
        tous_artisans = []
        
        for dept in departements:
            logger.info(f"🔍 Recherche {metier} dans {dept}...")
            artisans = self.chercher_artisans(code_naf, dept, limite_par_dept)
            
            # Ajouter type_artisan
            for artisan in artisans:
                artisan["type_artisan"] = metier
            
            tous_artisans.extend(artisans)
            # Pause entre départements pour éviter rate limit (2-3 secondes)
            time.sleep(2.5)
        
        logger.info(f"✅ Total {metier}: {len(tous_artisans)} artisans")
        return tous_artisans
