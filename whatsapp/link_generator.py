"""
Générateur de liens WhatsApp wa.me
"""
import urllib.parse
from typing import Dict, Optional

class WhatsAppLinkGenerator:
    """Génère des liens wa.me pour contacter les artisans"""
    
    def formater_numero(self, telephone: str) -> str:
        """
        Convertit numéro français en format wa.me
        
        Entrée : "06 12 34 56 78" ou "0612345678"
        Sortie : "33612345678" (sans le +)
        """
        # ✅ Vérifier que telephone n'est pas None
        if not telephone:
            return ""
        
        # Nettoyer le numéro
        tel_clean = ''.join(filter(str.isdigit, str(telephone)))
        
        # Si commence par 0, remplacer par 33
        if tel_clean.startswith('0'):
            tel_clean = '33' + tel_clean[1:]
        elif tel_clean.startswith('+33'):
            tel_clean = tel_clean[3:]
        elif tel_clean.startswith('33'):
            pass  # Déjà bon format
        else:
            # Si ne commence ni par 0 ni par 33, ajouter 33
            if len(tel_clean) == 9:
                tel_clean = '33' + tel_clean
        
        return tel_clean
    
    def generer_message(self, artisan: Dict, template: str) -> str:
        """
        Personnalise le message avec variables
        
        Variables disponibles :
        - {prenom} : Prénom artisan (ou "Bonjour" si vide)
        - {nom} : Nom artisan
        - {entreprise} : Nom entreprise
        - {ville} : Ville
        - {metier} : Type artisan
        """
        message = template
        
        # Remplacer les variables (s'assurer que toutes les valeurs sont des strings, pas None)
        prenom = artisan.get('prenom') or ''
        if not prenom:
            nom_entreprise = artisan.get('nom_entreprise') or ''
            if nom_entreprise:
                prenom = nom_entreprise.split()[0] if nom_entreprise.split() else ''
        if not prenom:
            prenom = "Bonjour"
        
        nom = artisan.get('nom') or ''
        entreprise = artisan.get('nom_entreprise') or ''
        ville = artisan.get('ville') or ''
        metier = artisan.get('type_artisan') or ''
        
        message = message.replace('{prenom}', str(prenom))
        message = message.replace('{nom}', str(nom))
        message = message.replace('{entreprise}', str(entreprise))
        message = message.replace('{ville}', str(ville))
        message = message.replace('{metier}', str(metier))
        
        return message
    
    def generer_lien(self, artisan: Dict, template: str) -> str:
        """
        Génère le lien wa.me complet
        
        Retourne : "https://wa.me/33612345678?text=Bonjour%20Jean..."
        """
        # Formater le numéro
        tel_formate = self.formater_numero(artisan.get('telephone', ''))
        
        # Générer le message personnalisé
        message = self.generer_message(artisan, template)
        
        # Encoder le message en URL
        message_encode = urllib.parse.quote(message)
        
        # Construire l'URL
        lien = f"https://wa.me/{tel_formate}?text={message_encode}"
        
        return lien

