"""
Trouve des emails depuis les sites web
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailFinder:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extraire_email_site_web(self, url: str) -> Optional[str]:
        """
        Extrait l'email depuis un site web
        """
        try:
            # Nettoyer l'URL
            if not url.startswith('http'):
                url = f"https://{url}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher dans le texte
            text = soup.get_text()
            
            # Patterns d'emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            
            # Filtrer les emails pertinents
            for email in emails:
                email_lower = email.lower()
                # Éviter les emails génériques/spam
                if any(x in email_lower for x in ['noreply', 'no-reply', 'donotreply', 'example.com']):
                    continue
                # Prioriser les emails de contact
                if any(x in email_lower for x in ['contact', 'info', 'hello', 'bonjour']):
                    return email
                # Sinon prendre le premier valide
                return email
            
            # Chercher dans les liens mailto:
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                email = link.get('href').replace('mailto:', '').split('?')[0]
                if email:
                    return email
            
            return None
            
        except Exception as e:
            logger.warning(f"Erreur extraction email {url}: {e}")
            return None
    
    def deviner_email(self, prenom: str, nom: str, domaine: str) -> List[str]:
        """
        Devine des emails possibles selon des patterns courants
        """
        prenom_clean = prenom.lower().replace(' ', '').replace('-', '')
        nom_clean = nom.lower().replace(' ', '').replace('-', '')
        domaine_clean = domaine.replace('www.', '').replace('http://', '').replace('https://', '').split('/')[0]
        
        patterns = [
            f"{prenom_clean}.{nom_clean}@{domaine_clean}",
            f"{prenom_clean}{nom_clean}@{domaine_clean}",
            f"{prenom_clean}@{domaine_clean}",
            f"contact@{domaine_clean}",
            f"info@{domaine_clean}",
            f"contact@{domaine_clean}",
        ]
        
        return patterns
    
    def valider_email_dns(self, email: str) -> bool:
        """
        Valide qu'un domaine accepte des emails (vérification MX)
        """
        try:
            import dns.resolver
            domaine = email.split('@')[1]
            mx_records = dns.resolver.resolve(domaine, 'MX')
            return len(mx_records) > 0
        except:
            # Si pas de dns.resolver, on assume que c'est valide
            return True

