"""
Module d'envoi de SMS via des services GRATUITS (limités)
ATTENTION: Ces services ont des limitations importantes (quotas, fiabilité, etc.)
"""
import requests
from typing import Dict
from pathlib import Path
import json
import time


def load_sms_config() -> Dict[str, str]:
    """Charge la configuration SMS"""
    config_path = Path(__file__).parent.parent / "config" / "sms_config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de la config SMS: {e}")
    return {}


# ============================================================================
# OPTION 1: Twilio Trial Account (GRATUIT mais LIMITÉ)
# ============================================================================

def send_sms_twilio_trial(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via Twilio Trial (GRATUIT mais limité)
    
    LIMITATIONS:
    - Ne peut envoyer qu'à des numéros vérifiés dans votre compte Twilio
    - Compte d'essai uniquement (pas pour production)
    - Limite de crédit gratuit
    
    Pour utiliser:
    1. Créez un compte Twilio gratuit: https://www.twilio.com/try-twilio
    2. Vérifiez votre numéro de téléphone dans le dashboard
    3. Ajoutez les numéros de destination à vérifier (limité)
    
    Args:
        phone_number: Numéro de téléphone du destinataire (doit être vérifié dans Twilio)
        message: Message à envoyer
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    account_sid = config.get('twilio_account_sid', '')
    auth_token = config.get('twilio_auth_token', '')
    from_number = config.get('twilio_from_number', '')  # Numéro Twilio d'essai
    
    if not all([account_sid, auth_token, from_number]):
        return {
            'success': False,
            'message': 'Configuration Twilio incomplète. Créez un compte gratuit sur https://www.twilio.com/try-twilio',
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
                'message': 'SMS envoyé avec succès via Twilio (gratuit)',
                'status_code': response.status_code,
                'data': response.json()
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', response.text)
            return {
                'success': False,
                'message': f'Erreur Twilio: {error_msg}',
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de l\'envoi Twilio: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# OPTION 2: TextBelt (GRATUIT mais très limité)
# ============================================================================

def send_sms_textbelt(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via TextBelt (GRATUIT mais très limité)
    
    LIMITATIONS:
    - 1 SMS par jour gratuitement
    - Nécessite une clé API (gratuite mais limitée)
    - Peut être instable
    
    Pour utiliser:
    1. Créez un compte gratuit sur https://textbelt.com/
    2. Récupérez votre clé API gratuite
    
    Args:
        phone_number: Numéro de téléphone du destinataire
        message: Message à envoyer
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    api_key = config.get('textbelt_api_key', '')
    
    if not api_key:
        return {
            'success': False,
            'message': 'Configuration TextBelt incomplète. Créez un compte gratuit sur https://textbelt.com/',
            'status_code': 0
        }
    
    # Nettoyer le numéro (format international: 33612345678)
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    if len(cleaned_phone) == 10 and cleaned_phone.startswith('0'):
        cleaned_phone = '33' + cleaned_phone[1:]
    
    # Limiter le message
    if len(message) > 160:
        message = message[:157] + "..."
    
    # URL de l'API TextBelt
    api_url = "https://textbelt.com/text"
    
    # Données de la requête
    data = {
        'phone': cleaned_phone,
        'message': message,
        'key': api_key
    }
    
    try:
        response = requests.post(api_url, data=data, timeout=10)
        result = response.json()
        
        if result.get('success', False):
            return {
                'success': True,
                'message': 'SMS envoyé avec succès via TextBelt (gratuit)',
                'status_code': 200,
                'data': result
            }
        else:
            return {
                'success': False,
                'message': f'Erreur TextBelt: {result.get("error", "Erreur inconnue")}',
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de l\'envoi TextBelt: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# OPTION 3: Solution de contournement - Email vers SMS (GRATUIT)
# ============================================================================

def send_sms_via_email(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via email (GRATUIT mais limité)
    
    LIMITATIONS:
    - Fonctionne uniquement avec certains opérateurs
    - Format: numero@operateur.sms
    - Pas garanti de fonctionner partout
    - Peut être bloqué comme spam
    
    Opérateurs français:
    - Orange: numero@orange.fr
    - SFR: numero@sfr.fr
    - Bouygues: numero@bmsms.fr
    - Free: numero@mobile.free.fr
    
    Args:
        phone_number: Numéro de téléphone du destinataire
        message: Message à envoyer
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    # Configuration email (nécessite un serveur SMTP)
    smtp_server = config.get('smtp_server', 'smtp.gmail.com')
    smtp_port = config.get('smtp_port', 587)
    email_from = config.get('email_from', '')
    email_password = config.get('email_password', '')
    
    if not email_from or not email_password:
        return {
            'success': False,
            'message': 'Configuration email manquante. Configurez email_from et email_password dans config/sms_config.json',
            'status_code': 0
        }
    
    # Détecter l'opérateur (simplifié - nécessiterait une base de données)
    # Pour l'instant, on essaie Free Mobile
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    
    # Mapping opérateurs (simplifié)
    # En production, utiliser une vraie base de données de numéros
    operator_emails = {
        '06': '@mobile.free.fr',  # Free Mobile
        '07': '@mobile.free.fr',  # Free Mobile
    }
    
    prefix = cleaned_phone[:2] if len(cleaned_phone) >= 2 else '06'
    email_to = f"{cleaned_phone}{operator_emails.get(prefix, '@mobile.free.fr')}"
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(message)
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = 'SMS'
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_from, email_password)
        server.sendmail(email_from, [email_to], msg.as_string())
        server.quit()
        
        return {
            'success': True,
            'message': f'SMS envoyé via email vers {email_to} (gratuit mais non garanti)',
            'status_code': 200
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur envoi email-SMS: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# OPTION 4: TextFlow - Utiliser votre propre téléphone Android (100% GRATUIT)
# ============================================================================

def send_sms_textflow(phone_number: str, message: str) -> Dict[str, any]:
    """
    Envoie un SMS via TextFlow (utilise votre propre téléphone Android)
    
    AVANTAGES:
    - ✅ 100% GRATUIT si vous avez un forfait avec SMS illimités
    - ✅ Pas de limite (selon votre forfait)
    - ✅ Utilise votre propre numéro
    
    CONFIGURATION:
    1. Installez l'app TextFlow sur votre téléphone Android
    2. Configurez un serveur API (peut être hébergé localement)
    3. Récupérez votre clé API depuis l'app
    
    Documentation: https://docs.textflow.me/
    
    Args:
        phone_number: Numéro de téléphone du destinataire
        message: Message à envoyer
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    api_key = config.get('textflow_api_key', '')
    api_url = config.get('textflow_api_url', 'https://api.textflow.me/send-sms')
    
    if not api_key:
        return {
            'success': False,
            'message': 'Configuration TextFlow incomplète. Installez l\'app TextFlow et configurez textflow_api_key dans config/sms_config.json',
            'status_code': 0
        }
    
    # Nettoyer le numéro
    import re
    cleaned_phone = re.sub(r'\D', '', phone_number)
    if len(cleaned_phone) == 10 and cleaned_phone.startswith('0'):
        cleaned_phone = '+33' + cleaned_phone[1:]
    elif not cleaned_phone.startswith('+'):
        cleaned_phone = '+33' + cleaned_phone
    
    # Limiter le message
    if len(message) > 160:
        message = message[:157] + "..."
    
    # Headers avec authentification
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Données de la requête
    data = {
        'phone_number': cleaned_phone,
        'message': message
    }
    
    try:
        response = requests.post(api_url, json=data, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            return {
                'success': True,
                'message': 'SMS envoyé avec succès via TextFlow (gratuit via votre téléphone)',
                'status_code': response.status_code,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'message': f'Erreur TextFlow: {response.status_code} - {response.text}',
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erreur lors de l\'envoi TextFlow: {str(e)}',
            'status_code': 0
        }


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def send_sms(phone_number: str, message: str, provider: str = 'auto') -> Dict[str, any]:
    """
    Envoie un SMS via un service GRATUIT
    
    Args:
        phone_number: Numéro de téléphone du destinataire
        message: Message à envoyer
        provider: 'twilio_trial', 'textbelt', 'email', ou 'auto'
    
    Returns:
        Dictionnaire avec 'success', 'message', 'status_code'
    """
    config = load_sms_config()
    
    # Détection automatique
    if provider == 'auto':
        if config.get('textflow_api_key'):
            provider = 'textflow'  # Priorité à TextFlow (vraiment gratuit)
        elif config.get('twilio_account_sid'):
            provider = 'twilio_trial'
        elif config.get('textbelt_api_key'):
            provider = 'textbelt'
        elif config.get('email_from'):
            provider = 'email'
        else:
            return {
                'success': False,
                'message': 'Aucun service gratuit configuré. Configurez TextFlow, Twilio Trial, TextBelt ou Email dans config/sms_config.json',
                'status_code': 0
            }
    
    # Appel de la fonction appropriée
    if provider == 'textflow':
        return send_sms_textflow(phone_number, message)
    elif provider == 'twilio_trial':
        return send_sms_twilio_trial(phone_number, message)
    elif provider == 'textbelt':
        return send_sms_textbelt(phone_number, message)
    elif provider == 'email':
        return send_sms_via_email(phone_number, message)
    else:
        return {
            'success': False,
            'message': f'Provider inconnu: {provider}',
            'status_code': 0
        }

