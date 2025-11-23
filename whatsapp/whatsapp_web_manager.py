"""
Gestionnaire WhatsApp Web - Alternative sans Meta API
Utilise WhatsApp Web avec automation Playwright
"""
import time
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dossier pour sauvegarder la session
SESSION_DIR = Path(__file__).parent.parent / "data" / "whatsapp_session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

class WhatsAppWebManager:
    """
    Gère WhatsApp via WhatsApp Web (automation)
    Pas besoin de Meta API - utilise votre numéro existant
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.connected = False
        self.session_path = SESSION_DIR / "browser_context"
    
    def connecter(self, wait_for_qr: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Se connecte à WhatsApp Web
        Retourne (success, message, qr_code_base64)
        Si wait_for_qr=False, attend juste que la connexion soit établie
        """
        try:
            self.playwright = sync_playwright().start()
            
            # Créer un contexte persistant pour sauvegarder la session
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            # Essayer de charger une session existante
            if self.session_path.exists():
                try:
                    self.context = self.browser.new_context(
                        storage_state=str(self.session_path / "state.json")
                    )
                    logger.info("📂 Session existante chargée")
                except:
                    self.context = self.browser.new_context()
            else:
                self.context = self.browser.new_context()
            
            self.page = self.context.new_page()
            
            # Aller sur WhatsApp Web
            self.page.goto("https://web.whatsapp.com", wait_until="networkidle")
            time.sleep(2)
            
            # Vérifier si déjà connecté
            try:
                # Chercher un élément qui indique qu'on est connecté
                self.page.wait_for_selector('div[data-testid="chatlist"]', timeout=5000)
                self.connected = True
                self._sauvegarder_session()
                logger.info("✅ Déjà connecté à WhatsApp Web !")
                return True, "Déjà connecté", None
            except:
                # Pas connecté, attendre QR code
                if wait_for_qr:
                    logger.info("📱 Veuillez scanner le QR code...")
                    
                    # Attendre le QR code
                    try:
                        qr_element = self.page.wait_for_selector('canvas', timeout=10000)
                        # Le QR code est dans un canvas, on ne peut pas l'extraire facilement
                        # On retourne l'URL de la page pour que l'utilisateur scanne
                        return False, "QR code à scanner", self.page.url
                    except:
                        return False, "QR code non trouvé", None
                else:
                    # Attendre que l'utilisateur scanne
                    try:
                        self.page.wait_for_selector('div[data-testid="chatlist"]', timeout=120000)
                        self.connected = True
                        self._sauvegarder_session()
                        logger.info("✅ Connecté à WhatsApp Web !")
                        return True, "Connecté avec succès", None
                    except PlaywrightTimeout:
                        return False, "Timeout - QR code non scanné", None
                
        except Exception as e:
            logger.error(f"Erreur connexion: {e}")
            return False, str(e), None
    
    def _sauvegarder_session(self):
        """Sauvegarde la session pour éviter de rescanner le QR code"""
        try:
            self.context.storage_state(path=str(self.session_path / "state.json"))
            logger.info("💾 Session sauvegardée")
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder la session: {e}")
    
    def verifier_whatsapp(self, telephone: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si un numéro est sur WhatsApp
        En cherchant le numéro dans la barre de recherche
        """
        if not self.connected:
            return False, "Non connecté à WhatsApp Web"
        
        try:
            # Formater le numéro
            tel_clean = self._formater_telephone(telephone)
            
            # Cliquer sur la barre de recherche
            search_selector = 'div[data-testid="chat-list-search"]'
            search_box = self.page.query_selector(search_selector)
            
            if not search_box:
                # Essayer un autre sélecteur
                search_box = self.page.query_selector('div[contenteditable="true"][data-tab="3"]')
            
            if search_box:
                search_box.click()
                time.sleep(1)
                
                # Effacer et taper le numéro
                self.page.keyboard.press("Control+A")
                time.sleep(0.5)
                self.page.keyboard.type(tel_clean)
                time.sleep(3)  # Attendre les résultats
                
                # Vérifier si un résultat apparaît
                # Chercher des éléments de résultat
                results = self.page.query_selector_all('div[data-testid="cell-frame-container"]')
                
                if not results:
                    # Essayer un autre sélecteur
                    results = self.page.query_selector_all('span[title]')
                
                found = False
                for result in results:
                    # Vérifier si le numéro ou un nom apparaît
                    text = result.inner_text()
                    if tel_clean in text or telephone in text:
                        found = True
                        break
                
                # Effacer la recherche
                self.page.keyboard.press("Escape")
                time.sleep(1)
                
                return found, None if found else "Numéro non trouvé sur WhatsApp"
            else:
                return False, "Impossible d'accéder à la recherche"
                
        except Exception as e:
            logger.error(f"Erreur vérification: {e}")
            return False, str(e)
    
    def envoyer_message(self, telephone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Envoie un message WhatsApp
        Retourne (success, message_id, error)
        """
        if not self.connected:
            return False, None, "Non connecté à WhatsApp Web"
        
        try:
            # Formater le numéro
            tel_clean = self._formater_telephone(telephone)
            
            # Ouvrir la conversation directement
            url = f"https://web.whatsapp.com/send?phone={tel_clean}"
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # Vérifier si le numéro est valide (chercher un message d'erreur)
            error_elements = self.page.query_selector_all('text=/invalid|erreur|error/i')
            if error_elements:
                return False, None, "Numéro invalide ou non présent sur WhatsApp"
            
            # Trouver la zone de texte pour écrire le message
            # WhatsApp Web utilise une div contenteditable
            text_box = self.page.query_selector('div[contenteditable="true"][data-tab="10"]')
            
            if not text_box:
                # Essayer d'autres sélecteurs
                text_box = self.page.query_selector('div[contenteditable="true"][role="textbox"]')
            
            if not text_box:
                # Dernier essai
                text_box = self.page.query_selector('div[contenteditable="true"]')
            
            if text_box:
                text_box.click()
                time.sleep(0.5)
                
                # Taper le message
                self.page.keyboard.type(message)
                time.sleep(1)
                
                # Envoyer (Entrée)
                self.page.keyboard.press("Enter")
                time.sleep(2)
                
                # Générer un message_id simple
                message_id = f"web_{int(time.time())}"
                return True, message_id, None
            else:
                return False, None, "Zone de texte non trouvée"
                
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            return False, None, str(e)
    
    def recuperer_messages(self) -> list:
        """
        Récupère les nouveaux messages reçus
        Note: WhatsApp Web ne permet pas facilement de récupérer les messages
        Cette fonction est basique et peut nécessiter des améliorations
        """
        if not self.connected:
            return []
        
        try:
            # Aller sur la page principale
            self.page.goto("https://web.whatsapp.com", wait_until="networkidle")
            time.sleep(2)
            
            # Chercher les conversations non lues
            # WhatsApp Web affiche un badge pour les messages non lus
            unread_chats = self.page.query_selector_all('span[data-testid="icon-unread-count"]')
            
            messages = []
            # Cette implémentation est basique
            # Pour une vraie récupération, il faudrait parser chaque conversation
            # Ce qui est complexe avec WhatsApp Web
            
            return messages
            
        except Exception as e:
            logger.error(f"Erreur récupération messages: {e}")
            return []
    
    def _formater_telephone(self, telephone: str) -> str:
        """Formate le téléphone pour WhatsApp Web"""
        # Nettoyer
        tel_clean = ''.join(filter(str.isdigit, telephone))
        
        # Si commence par 0, remplacer par le code pays
        if tel_clean.startswith('0'):
            tel_clean = '33' + tel_clean[1:]  # France
        
        return tel_clean
    
    def est_connecte(self) -> bool:
        """Vérifie si toujours connecté"""
        if not self.page:
            return False
        
        try:
            # Vérifier si on est toujours sur WhatsApp Web et connecté
            current_url = self.page.url
            if "web.whatsapp.com" not in current_url:
                return False
            
            # Chercher un élément qui indique la connexion
            chatlist = self.page.query_selector('div[data-testid="chatlist"]')
            return chatlist is not None
        except:
            return False
    
    def deconnecter(self):
        """Ferme la connexion"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.connected = False
            logger.info("Déconnecté de WhatsApp Web")
        except Exception as e:
            logger.error(f"Erreur déconnexion: {e}")
