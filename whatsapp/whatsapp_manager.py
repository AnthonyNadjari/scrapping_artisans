"""
Gestionnaire WhatsApp - Vérification et envoi de messages
"""
import requests
import time
from typing import Dict, Optional, Tuple, List
import logging

from config.whatsapp_settings import WHATSAPP_CONFIG
from whatsapp_database.queries import (
    marquer_whatsapp_verifie, marquer_message_envoye,
    get_artisan_par_telephone, formater_telephone_fr
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppManager:
    """
    Gère les interactions avec l'API WhatsApp Business
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or WHATSAPP_CONFIG
        self.base_url = f"https://graph.facebook.com/v18.0/{self.config.get('phone_number_id')}"
        self.headers = {
            "Authorization": f"Bearer {self.config.get('access_token')}",
            "Content-Type": "application/json"
        }
    
    def verifier_whatsapp(self, telephone: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si un numéro est sur WhatsApp
        Retourne (is_whatsapp, error_message)
        """
        if not telephone:
            return False, "Numéro vide"
        
        # Formater le numéro
        tel_formate = formater_telephone_fr(telephone)
        
        try:
            url = f"{self.base_url}/contacts"
            payload = {
                "blocking": "wait",
                "contacts": [tel_formate]
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier si wa_id est présent (signe que le numéro est sur WhatsApp)
                if 'contacts' in data and len(data['contacts']) > 0:
                    contact = data['contacts'][0]
                    if 'wa_id' in contact:
                        return True, None
                    else:
                        return False, "Numéro non présent sur WhatsApp"
                else:
                    return False, "Aucun contact trouvé"
            else:
                error_msg = response.json().get('error', {}).get('message', 'Erreur API')
                logger.error(f"Erreur vérification WhatsApp: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau vérification: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Erreur vérification: {e}")
            return False, str(e)
    
    def envoyer_message(self, telephone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Envoie un message WhatsApp
        Retourne (success, message_id, error_message)
        """
        if not telephone:
            return False, None, "Numéro vide"
        
        # Formater le numéro
        tel_formate = formater_telephone_fr(telephone)
        
        try:
            url = f"{self.base_url}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": tel_formate,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get('messages', [{}])[0].get('id')
                return True, message_id, None
            else:
                error_data = response.json().get('error', {})
                error_code = error_data.get('code')
                error_msg = error_data.get('message', 'Erreur API')
                
                # Détecter erreurs critiques
                if error_code in [131047, 131048]:  # Spam detected
                    logger.critical(f"⚠️ SPAM DETECTÉ - Arrêter immédiatement: {error_msg}")
                    return False, None, f"SPAM DETECTÉ: {error_msg}"
                
                logger.error(f"Erreur envoi message: {error_msg}")
                return False, None, error_msg
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau envoi: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Erreur envoi: {e}")
            return False, None, str(e)
    
    def recuperer_messages(self, limit: int = 50) -> List[Dict]:
        """
        Récupère les messages reçus depuis WhatsApp
        Retourne liste de messages avec (telephone, contenu, message_id)
        """
        try:
            # Note: L'API WhatsApp utilise webhooks pour les messages entrants
            # Cette fonction est pour récupérer via l'API si disponible
            # Sinon, utiliser les webhooks (voir documentation Meta)
            
            url = f"https://graph.facebook.com/v18.0/{self.config.get('phone_number_id')}/messages"
            params = {
                "limit": limit
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                messages = []
                
                # Parser les messages (structure dépend de l'API)
                for msg in data.get('data', []):
                    if msg.get('from') and msg.get('text'):
                        messages.append({
                            'telephone': msg['from'],
                            'contenu': msg['text'].get('body', ''),
                            'message_id': msg.get('id'),
                            'timestamp': msg.get('timestamp')
                        })
                
                return messages
            else:
                logger.warning(f"Impossible de récupérer messages: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur récupération messages: {e}")
            return []
    
    def tester_connexion(self) -> Tuple[bool, str]:
        """
        Teste la connexion à l'API WhatsApp
        Retourne (success, message)
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{self.config.get('phone_number_id')}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return True, "✅ Connexion réussie"
            else:
                error = response.json().get('error', {})
                return False, f"❌ Erreur: {error.get('message', 'Connexion échouée')}"
        except Exception as e:
            return False, f"❌ Erreur: {str(e)}"

