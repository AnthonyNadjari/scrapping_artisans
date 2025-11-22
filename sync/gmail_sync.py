"""
Synchronisation bidirectionnelle avec Gmail
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import re
from datetime import datetime
import logging

from database.queries import sauvegarder_reponse, get_artisan, get_artisans
from config.settings import GMAIL_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailSync:
    def __init__(self, config: Dict = None):
        self.config = config or GMAIL_CONFIG
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
    
    def decoder_header(self, header):
        """Décode un header d'email"""
        decoded = decode_header(header)
        if decoded:
            parts = []
            for part, encoding in decoded:
                if isinstance(part, bytes):
                    if encoding:
                        parts.append(part.decode(encoding))
                    else:
                        parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    parts.append(part)
            return ''.join(parts)
        return ""
    
    def extraire_corps_email(self, msg) -> str:
        """Extrait le corps d'un email"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" or content_type == "text/html":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        return body
    
    def trouver_artisan_par_email(self, from_email: str) -> Dict:
        """Trouve un artisan par son email"""
        # Extraire l'email depuis le header
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_email)
        if not email_match:
            return None
        
        email_addr = email_match.group(0)
        
        # Chercher dans la BDD
        artisans = get_artisans({'recherche': email_addr}, limit=10)
        
        for artisan in artisans:
            if artisan.get('email') and artisan['email'].lower() == email_addr.lower():
                return artisan
        
        return None
    
    def analyser_sentiment(self, contenu: str) -> str:
        """Analyse basique du sentiment d'une réponse"""
        contenu_lower = contenu.lower()
        
        # Mots positifs
        positifs = ['intéressé', 'intéressant', 'oui', 'ok', 'd\'accord', 'merci', 'parfait', 'super']
        # Mots négatifs
        negatifs = ['pas intéressé', 'ne souhaite pas', 'ne pas', 'stop', 'arrêtez', 'désinscription']
        
        score_positif = sum(1 for word in positifs if word in contenu_lower)
        score_negatif = sum(1 for word in negatifs if word in contenu_lower)
        
        if score_positif > score_negatif:
            return 'positif'
        elif score_negatif > score_positif:
            return 'negatif'
        else:
            return 'neutre'
    
    def synchroniser_boite_reception(self) -> Dict:
        """
        Synchronise la boîte de réception Gmail
        Retourne les statistiques
        """
        stats = {
            'emails_lus': 0,
            'reponses_trouvees': 0,
            'erreurs': 0
        }
        
        if not self.config.get('email') or not self.config.get('app_password'):
            logger.error("Configuration Gmail manquante")
            return stats
        
        try:
            # Connexion IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.config['email'], self.config['app_password'])
            mail.select('inbox')
            
            # Chercher emails non lus
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("Erreur recherche emails")
                return stats
            
            email_ids = messages[0].split()
            stats['emails_lus'] = len(email_ids)
            
            for email_id in email_ids:
                try:
                    # Récupérer email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Parser
                            from_email = self.decoder_header(msg['from'])
                            subject = self.decoder_header(msg['subject'])
                            date_str = msg['date']
                            
                            # Extraire corps
                            body = self.extraire_corps_email(msg)
                            
                            # Chercher artisan correspondant
                            artisan = self.trouver_artisan_par_email(from_email)
                            
                            if artisan:
                                # C'est une réponse !
                                sentiment = self.analyser_sentiment(body)
                                
                                # Parser la date
                                try:
                                    date_obj = email.utils.parsedate_to_datetime(date_str)
                                    date_iso = date_obj.isoformat()
                                except:
                                    date_iso = datetime.now().isoformat()
                                
                                # Sauvegarder
                                sauvegarder_reponse(
                                    artisan['id'],
                                    subject,
                                    body,
                                    date_iso,
                                    sentiment
                                )
                                
                                stats['reponses_trouvees'] += 1
                                logger.info(f"✅ Réponse trouvée de {artisan['nom_entreprise']}")
                
                except Exception as e:
                    logger.error(f"Erreur traitement email {email_id}: {e}")
                    stats['erreurs'] += 1
                    continue
            
            mail.close()
            mail.logout()
            
        except imaplib.IMAP4.error as e:
            logger.error(f"Erreur IMAP: {e}")
            stats['erreurs'] += 1
        except Exception as e:
            logger.error(f"Erreur sync Gmail: {e}")
            stats['erreurs'] += 1
        
        logger.info(f"✅ Sync terminée: {stats}")
        return stats

