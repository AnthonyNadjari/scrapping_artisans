"""
Génération d'emails personnalisés pour les artisans
"""
import re
import os
from typing import Dict, Optional
from config.settings import GMAIL_CONFIG

# OpenAI optionnel
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Template HTML de base
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #4CAF50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 5px 5px;
        }}
        .cta-button {{
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Site Web Professionnel pour Artisans</h1>
    </div>
    <div class="content">
        <p>Bonjour {prenom},</p>
        
        <p>{phrase_accroche}</p>
        
        <p>Je me permets de vous contacter car j'ai remarqué que votre entreprise <strong>{nom_entreprise}</strong> à {ville} n'a pas encore de site web professionnel.</p>
        
        <p>Un site web moderne vous permettrait de :</p>
        <ul>
            <li>✅ Attirer de nouveaux clients dans votre région</li>
            <li>✅ Présenter vos réalisations et votre savoir-faire</li>
            <li>✅ Faciliter la prise de contact (formulaire, devis en ligne)</li>
            <li>✅ Renforcer votre crédibilité face à la concurrence</li>
        </ul>
        
        <p>Je propose des sites web sur mesure pour artisans, adaptés à votre métier et à votre budget.</p>
        
        <p>Seriez-vous intéressé par un échange de 15 minutes pour discuter de vos besoins ?</p>
        
        <a href="mailto:{email_expediteur}?subject=Site web pour {nom_entreprise}" class="cta-button">Répondre à cet email</a>
        
        <p>Bien cordialement,<br>
        {nom_expediteur}</p>
    </div>
    <div class="footer">
        <p>Cet email vous a été envoyé car votre entreprise correspond à notre cible.<br>
        Si vous ne souhaitez plus recevoir d'emails, <a href="#">cliquez ici</a>.</p>
    </div>
    
    {tracking_pixel}
</body>
</html>
"""

def generer_phrase_accroche(artisan: Dict, use_ai: bool = False) -> str:
    """
    Génère une phrase d'accroche personnalisée
    """
    if use_ai and OPENAI_AVAILABLE:
        try:
            # Utiliser OpenAI pour générer une phrase d'accroche
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            Génère une phrase d'accroche courte (1-2 phrases) pour un email de prospection à un artisan.
            
            Artisan: {artisan.get('nom_entreprise', '')}
            Métier: {artisan.get('type_artisan', '')}
            Ville: {artisan.get('ville', '')}
            
            La phrase doit être personnalisée, chaleureuse et pertinente.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except:
            pass
    
    # Fallback: phrases d'accroche génériques mais personnalisées
    phrases = [
        f"En tant que {artisan.get('type_artisan', 'artisan')} à {artisan.get('ville', '')}, vous savez l'importance d'avoir une bonne visibilité locale.",
        f"Votre savoir-faire de {artisan.get('type_artisan', 'artisan')} mérite d'être mis en valeur sur le web.",
        f"Les artisans de {artisan.get('ville', 'votre ville')} comme vous ont besoin d'un site web pour se démarquer.",
    ]
    
    import random
    return random.choice(phrases)

def generer_email_personnalise(artisan: Dict, tracking_pixel: str = "", use_ai: bool = False) -> str:
    """
    Génère un email HTML personnalisé pour un artisan
    """
    prenom = artisan.get('prenom', '')
    if not prenom:
        # Extraire prénom du nom d'entreprise si possible
        nom_entreprise = artisan.get('nom_entreprise', '')
        if nom_entreprise:
            parts = nom_entreprise.split()
            prenom = parts[0] if len(parts) > 0 else ''
    
    nom_entreprise = artisan.get('nom_entreprise', 'Votre entreprise')
    ville = artisan.get('ville', 'votre ville')
    type_artisan = artisan.get('type_artisan', 'artisan')
    
    phrase_accroche = generer_phrase_accroche(artisan, use_ai)
    
    email_html = EMAIL_TEMPLATE.format(
        prenom=prenom or 'Monsieur/Madame',
        phrase_accroche=phrase_accroche,
        nom_entreprise=nom_entreprise,
        ville=ville,
        type_artisan=type_artisan,
        email_expediteur=GMAIL_CONFIG.get('email', 'contact@example.com'),
        nom_expediteur=GMAIL_CONFIG.get('display_name', 'Sites Web Artisans'),
        tracking_pixel=tracking_pixel
    )
    
    return email_html

def generer_objet_email(artisan: Dict) -> str:
    """Génère un objet d'email personnalisé"""
    nom_entreprise = artisan.get('nom_entreprise', '')
    ville = artisan.get('ville', '')
    
    objets = [
        f"Site web professionnel pour {nom_entreprise}",
        f"Visibilité en ligne pour votre activité à {ville}",
        f"Site web pour artisans à {ville}",
        f"Boostez votre activité avec un site web professionnel",
    ]
    
    import random
    return random.choice(objets)

