"""
Envoi d'emails via SMTP Gmail
"""
import smtplib
import time
import hashlib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple, Optional
from datetime import datetime
import logging

from emails.generator import generer_email_personnalise, generer_objet_email
from emails.tracker import generer_tracking_pixel
from database.queries import marquer_email_envoye, creer_tracking_pixel
from config.settings import GMAIL_CONFIG, DELAI_ENTRE_EMAILS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or GMAIL_CONFIG
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def envoyer_email(self, artisan: Dict, use_tracking: bool = True) -> Tuple[bool, str]:
        """
        Envoie un email à un artisan
        Retourne (success, message_id)
        """
        if not artisan.get('email'):
            return False, "Pas d'email"
        
        if not self.config.get('email') or not self.config.get('app_password'):
            return False, "Configuration Gmail manquante"
        
        try:
            # Générer tracking pixel
            tracking_pixel = ""
            tracking_id = None
            
            if use_tracking:
                tracking_id = hashlib.md5(
                    f"{artisan['id']}{uuid.uuid4()}".encode()
                ).hexdigest()
                tracking_pixel = generer_tracking_pixel(tracking_id)
                creer_tracking_pixel(artisan['id'], tracking_id)
            
            # Générer email
            email_html = generer_email_personnalise(artisan, tracking_pixel)
            objet = generer_objet_email(artisan)
            
            # Créer message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.get('display_name', 'Sites Web Artisans')} <{self.config['email']}>"
            msg['To'] = artisan['email']
            msg['Subject'] = objet
            
            # Ajouter contenu HTML
            msg.attach(MIMEText(email_html, 'html'))
            
            # Envoyer
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.config['email'], self.config['app_password'])
                server.send_message(msg)
            
            message_id = msg['Message-ID']
            
            # Marquer comme envoyé en BDD
            marquer_email_envoye(
                artisan['id'],
                message_id,
                objet,
                email_html
            )
            
            logger.info(f"✅ Email envoyé à {artisan['nom_entreprise']} ({artisan['email']})")
            return True, message_id
            
        except smtplib.SMTPAuthenticationError:
            error = "Erreur authentification Gmail"
            logger.error(error)
            return False, error
        except smtplib.SMTPRecipientsRefused:
            error = "Email refusé"
            logger.error(error)
            return False, error
        except Exception as e:
            error = str(e)
            logger.error(f"Erreur envoi email: {error}")
            return False, error
    
    def envoyer_batch(self, artisans: list, delai: int = DELAI_ENTRE_EMAILS, 
                     callback_progress=None) -> Dict:
        """
        Envoie des emails par batch
        """
        stats = {
            'total': len(artisans),
            'envoyes': 0,
            'erreurs': 0,
            'erreurs_details': []
        }
        
        for i, artisan in enumerate(artisans):
            success, message = self.envoyer_email(artisan)
            
            if success:
                stats['envoyes'] += 1
            else:
                stats['erreurs'] += 1
                stats['erreurs_details'].append({
                    'artisan': artisan.get('nom_entreprise'),
                    'erreur': message
                })
            
            if callback_progress:
                callback_progress({
                    'current': i + 1,
                    'total': len(artisans),
                    'envoyes': stats['envoyes'],
                    'erreurs': stats['erreurs'],
                })
            
            # Délai entre emails (sauf dernier)
            if i < len(artisans) - 1:
                time.sleep(delai)
        
        logger.info(f"✅ Batch terminé: {stats['envoyes']}/{stats['total']} envoyés")
        return stats

