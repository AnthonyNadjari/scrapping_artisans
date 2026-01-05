"""
Module d'envoi de SMS via l'API Free Mobile
NOTE: L'API Free Mobile envoie uniquement vers votre propre numéro (notifications)
Pour envoyer à d'autres numéros, utilisez whatsapp/sms_providers.py avec OVH, Twilio, etc.
"""
import requests
from typing import Optional, Dict
from pathlib import Path
import json


def load_sms_config() -> Dict[str, str]:
    """
    Charge la configuration SMS depuis le fichier de config
    
    Returns:
        Dictionnaire avec 'user' et 'pass' (token)
    """
    config_path = Path(__file__).parent.parent / "config" / "sms_config.json"
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    'user': config.get('phone_number', ''),
                    'pass': config.get('token', '')
                }
    except Exception as e:
        print(f"Erreur lors du chargement de la config SMS: {e}")
    
    return {'user': '', 'pass': ''}


def send_sms(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via l'API Free Mobile
    
    Args:
        phone_number: Numéro de téléphone du destinataire (format: 0612345678)
        message: Message à envoyer (max 160 caractères)
    
    Returns:
        Dictionnaire avec:
        - 'success': bool
        - 'message': str (message d'erreur ou de succès)
        - 'status_code': int (code HTTP de la réponse)
    """
    # Charger la configuration
    config = load_sms_config()
    
    if not config['user'] or not config['pass']:
        return {
            'success': False,
            'message': 'Configuration SMS manquante. Veuillez configurer le token et le numéro dans config/sms_config.json',
            'status_code': 0
        }
    
    # Nettoyer le numéro de téléphone (garder seulement les chiffres)
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    
    # Vérifier que le numéro est valide (10 chiffres pour la France)
    if len(cleaned_phone) != 10:
        return {
            'success': False,
            'message': f'Numéro de téléphone invalide: {phone_number}',
            'status_code': 0
        }
    
    # Limiter le message à 160 caractères (limite SMS)
    if len(message) > 160:
        message = message[:157] + "..."
    
    # URL de l'API Free Mobile
    api_url = "https://smsapi.free-mobile.fr/sendmsg"
    
    # Paramètres de l'API
    params = {
        'user': config['user'],
        'pass': config['pass'],
        'msg': message
    }
    
    try:
        # Envoyer la requête
        response = requests.get(api_url, params=params, timeout=10)
        
        # Codes de réponse Free Mobile:
        # 200: SMS envoyé avec succès
        # 400: Un des paramètres obligatoires est manquant
        # 402: Trop de SMS envoyés en peu de temps
        # 403: Service non activé ou identifiants incorrects
        # 500: Erreur serveur côté Free Mobile
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'SMS envoyé avec succès',
                'status_code': 200
            }
        elif response.status_code == 400:
            return {
                'success': False,
                'message': 'Paramètre manquant dans la requête',
                'status_code': 400
            }
        elif response.status_code == 402:
            return {
                'success': False,
                'message': 'Trop de SMS envoyés. Veuillez patienter.',
                'status_code': 402
            }
        elif response.status_code == 403:
            return {
                'success': False,
                'message': 'Service SMS non activé ou identifiants incorrects. Vérifiez votre token dans config/sms_config.json',
                'status_code': 403
            }
        elif response.status_code == 500:
            return {
                'success': False,
                'message': 'Erreur serveur Free Mobile. Réessayez plus tard.',
                'status_code': 500
            }
        else:
            return {
                'success': False,
                'message': f'Erreur inconnue: {response.status_code}',
                'status_code': response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Timeout: La requête a pris trop de temps',
            'status_code': 0
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'Erreur de connexion: {str(e)}',
            'status_code': 0
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur inattendue: {str(e)}',
            'status_code': 0
        }

