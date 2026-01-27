"""
Module d'envoi de SMS via différentes APIs professionnelles
Support pour OVH, Twilio, et autres services SMS
"""
import requests
from typing import Dict, Optional
from pathlib import Path
import json
import base64


def load_sms_config() -> Dict[str, str]:
    """
    Charge la configuration SMS depuis le fichier de config
    
    Returns:
        Dictionnaire avec les identifiants de l'API choisie
    """
    config_path = Path(__file__).parent.parent / "config" / "sms_config.json"
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de la config SMS: {e}")
    
    return {}


# ============================================================================
# OPTION 1: OVH SMS API (Recommandé pour la France)
# ============================================================================

def send_sms_ovh(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via l'API OVH
    
    Documentation: https://api.ovh.com/
    Nécessite: ServiceName, Application Key, Application Secret, Consumer Key
    
    Args:
        phone_number: Numéro de téléphone du destinataire (format: 0612345678)
        message: Message à envoyer (max 160 caractères)
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    # Configuration OVH
    service_name = config.get('ovh_service_name', '')
    app_key = config.get('ovh_app_key', '')
    app_secret = config.get('ovh_app_secret', '')
    consumer_key = config.get('ovh_consumer_key', '')
    
    if not all([service_name, app_key, app_secret, consumer_key]):
        return {
            'success': False,
            'message': 'Configuration OVH incomplète. Vérifiez config/sms_config.json',
            'status_code': 0
        }
    
    # Nettoyer le numéro (format international: +33612345678)
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    if len(cleaned_phone) == 10 and cleaned_phone.startswith('0'):
        cleaned_phone = '+33' + cleaned_phone[1:]
    elif not cleaned_phone.startswith('+'):
        cleaned_phone = '+33' + cleaned_phone
    
    # Limiter le message
    if len(message) > 160:
        message = message[:157] + "..."
    
    # URL de l'API OVH
    api_url = f"https://api.ovh.com/1.0/sms/{service_name}/jobs"
    
    # Headers avec authentification OVH
    headers = {
        'X-Ovh-Application': app_key,
        'X-Ovh-Consumer': consumer_key,
        'Content-Type': 'application/json'
    }
    
    # Données de la requête
    data = {
        'message': message,
        'receivers': [cleaned_phone],
        'sender': config.get('ovh_sender', 'SMS')  # Nom de l'expéditeur (max 11 caractères)
    }
    
    try:
        # Signature OVH (simplifiée - en production, utiliser la bibliothèque ovh)
        # Pour une implémentation complète, installer: pip install ovh
        response = requests.post(api_url, json=data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            return {
                'success': True,
                'message': 'SMS envoyé avec succès via OVH',
                'status_code': response.status_code,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'message': f'Erreur OVH: {response.status_code} - {response.text}',
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de l\'envoi OVH: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# OPTION 2: Twilio API (International, très fiable)
# ============================================================================

def send_sms_twilio(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via l'API Twilio
    
    Documentation: https://www.twilio.com/docs/sms
    Nécessite: Account SID, Auth Token, et un numéro Twilio
    
    Args:
        phone_number: Numéro de téléphone du destinataire (format: 0612345678)
        message: Message à envoyer (max 160 caractères)
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    account_sid = config.get('twilio_account_sid', '')
    auth_token = config.get('twilio_auth_token', '')
    from_number = config.get('twilio_from_number', '')  # Votre numéro Twilio
    
    if not all([account_sid, auth_token, from_number]):
        return {
            'success': False,
            'message': 'Configuration Twilio incomplète. Vérifiez config/sms_config.json',
            'status_code': 0
        }
    
    # Nettoyer le numéro (format international: +33612345678)
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    if len(cleaned_phone) == 10 and cleaned_phone.startswith('0'):
        cleaned_phone = '+33' + cleaned_phone[1:]
    elif not cleaned_phone.startswith('+'):
        cleaned_phone = '+33' + cleaned_phone
    
    # Limiter le message
    if len(message) > 160:
        message = message[:157] + "..."
    
    # URL de l'API Twilio
    api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    # Authentification basique
    auth = (account_sid, auth_token)
    
    # Données de la requête
    data = {
        'From': from_number,
        'To': cleaned_phone,
        'Body': message
    }
    
    try:
        response = requests.post(api_url, data=data, auth=auth, timeout=10)
        
        if response.status_code in [200, 201]:
            return {
                'success': True,
                'message': 'SMS envoyé avec succès via Twilio',
                'status_code': response.status_code,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'message': f'Erreur Twilio: {response.status_code} - {response.text}',
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de l\'envoi Twilio: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# OPTION 3: MessageBird API (Europe, bon pour la France)
# ============================================================================

def send_sms_messagebird(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via l'API MessageBird
    
    Documentation: https://developers.messagebird.com/api/sms-messaging/
    Nécessite: API Key
    
    Args:
        phone_number: Numéro de téléphone du destinataire (format: 0612345678)
        message: Message à envoyer (max 160 caractères)
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    api_key = config.get('messagebird_api_key', '')
    originator = config.get('messagebird_originator', 'SMS')  # Nom expéditeur
    
    if not api_key:
        return {
            'success': False,
            'message': 'Configuration MessageBird incomplète. Vérifiez config/sms_config.json',
            'status_code': 0
        }
    
    # Nettoyer le numéro (format international: 33612345678)
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    if len(cleaned_phone) == 10 and cleaned_phone.startswith('0'):
        cleaned_phone = '33' + cleaned_phone[1:]
    elif cleaned_phone.startswith('+33'):
        cleaned_phone = cleaned_phone.replace('+', '')
    
    # Limiter le message
    if len(message) > 160:
        message = message[:157] + "..."
    
    # URL de l'API MessageBird
    api_url = "https://rest.messagebird.com/messages"
    
    # Headers avec authentification
    headers = {
        'Authorization': f'AccessKey {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Données de la requête
    data = {
        'originator': originator,
        'recipients': [cleaned_phone],
        'body': message
    }
    
    try:
        response = requests.post(api_url, json=data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            return {
                'success': True,
                'message': 'SMS envoyé avec succès via MessageBird',
                'status_code': response.status_code,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'message': f'Erreur MessageBird: {response.status_code} - {response.text}',
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de l\'envoi MessageBird: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# FONCTION PRINCIPALE - Sélection automatique du provider
# ============================================================================

def send_sms(phone_number: str, message: str, provider: str = 'auto') -> Dict[str, any]:
    """
    Envoie un SMS via le provider configuré
    
    Args:
        phone_number: Numéro de téléphone du destinataire (format: 0612345678)
        message: Message à envoyer (max 160 caractères)
        provider: 'ovh', 'twilio', 'messagebird', ou 'auto' (détection automatique)
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    # Détection automatique du provider
    if provider == 'auto':
        if config.get('ovh_service_name'):
            provider = 'ovh'
        elif config.get('twilio_account_sid'):
            provider = 'twilio'
        elif config.get('messagebird_api_key'):
            provider = 'messagebird'
        else:
            return {
                'success': False,
                'message': 'Aucun provider SMS configuré. Configurez OVH, Twilio ou MessageBird dans config/sms_config.json',
                'status_code': 0
            }
    
    # Appel de la fonction appropriée
    if provider == 'ovh':
        return send_sms_ovh(phone_number, message)
    elif provider == 'twilio':
        return send_sms_twilio(phone_number, message)
    elif provider == 'messagebird':
        return send_sms_messagebird(phone_number, message)
    else:
        return {
            'success': False,
            'message': f'Provider inconnu: {provider}',
            'status_code': 0
        }




