"""
Templates de messages WhatsApp personnalisés
"""
from typing import Optional
from whatsapp.name_detector import get_salutation


# Définition des templates
TEMPLATES = [
    {
        "id": "no_website",
        "name": "Pas de site web",
        "priority": 100,
        "condition": lambda a: not a.get('site_web') or str(a.get('site_web', '')).strip() == '',
        "body": """{salutation}, je crée des sites web pour les artisans {metier}s autour de {ville}.

Un site simple mais efficace qui vous ramène des clients via Google.

Ça vous intéresse d'en discuter 2 min ?"""
    },
    {
        "id": "social_media",
        "name": "Site Facebook/Instagram",
        "priority": 90,
        "condition": lambda a: a.get('site_web') and (
            'facebook.com' in str(a.get('site_web', '')).lower() or
            'instagram.com' in str(a.get('site_web', '')).lower() or
            'fb.me' in str(a.get('site_web', '')).lower()
        ),
        "body": """{salutation}, j'ai vu votre page sur les réseaux.

Je crée des sites pro pour artisans — ça aide à apparaître sur Google quand les gens cherchent "{metier} {ville}".

Ça pourrait vous intéresser ?"""
    },
    {
        "id": "existing_website",
        "name": "Site web existant",
        "priority": 80,
        "condition": lambda a: a.get('site_web') and str(a.get('site_web', '')).strip() != '' and
                              'facebook.com' not in str(a.get('site_web', '')).lower() and
                              'instagram.com' not in str(a.get('site_web', '')).lower() and
                              'fb.me' not in str(a.get('site_web', '')).lower(),
        "body": """{salutation}, j'ai vu votre site en cherchant un {metier} vers {ville}.

Je refais des sites pour artisans avec un design moderne et optimisé pour Google. Souvent ça double les appels entrants.

Vous seriez ouvert à un avis gratuit sur votre site actuel ?"""
    },
    {
        "id": "high_rating_bonus",
        "name": "Bonus excellente note",
        "priority": 70,
        "condition": lambda a: a.get('note') and float(a.get('note', 0)) >= 4.5 and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 10,
        "body": """Félicitations pour vos {nombre_avis} avis et votre note de {note}/5 👏"""
    },
    {
        "id": "fallback",
        "name": "Générique",
        "priority": 10,
        "condition": lambda a: True,  # Toujours True (fallback)
        "body": """{salutation}, je crée des sites web pour artisans.

Un site bien fait = plus de clients via Google.

Intéressé d'en parler rapidement ?"""
    }
]


def select_template(artisan: dict) -> dict:
    """
    Sélectionne le template le plus approprié pour un artisan
    
    Args:
        artisan: Dictionnaire avec les données de l'artisan
    
    Returns:
        Template sélectionné (celui avec la plus haute priorité qui matche)
    """
    matching_templates = []
    
    for template in TEMPLATES:
        try:
            if template["condition"](artisan):
                matching_templates.append(template)
        except Exception:
            continue
    
    if not matching_templates:
        # Fallback sur le template générique
        return TEMPLATES[-1]
    
    # Retourner celui avec la plus haute priorité
    return max(matching_templates, key=lambda t: t["priority"])


def build_message(artisan: dict, template: dict) -> str:
    """
    Construit le message final en remplaçant les placeholders
    
    Args:
        artisan: Dictionnaire avec les données de l'artisan
        template: Template sélectionné
    
    Returns:
        Message final avec placeholders remplacés
    """
    from whatsapp.name_detector import detect_prenom
    
    # Préparer les variables
    salutation = get_salutation(artisan.get('nom_entreprise', ''))
    prenom = detect_prenom(artisan.get('nom_entreprise', '')) or ''
    entreprise = artisan.get('nom_entreprise', '') or ''
    ville = artisan.get('ville') or artisan.get('ville_recherche') or ''
    metier = artisan.get('type_artisan', 'artisan') or 'artisan'
    note = str(artisan.get('note', '')) if artisan.get('note') else ''
    nombre_avis = str(artisan.get('nombre_avis', '')) if artisan.get('nombre_avis') else ''
    site_web = artisan.get('site_web', '') or ''
    
    # Remplacer les placeholders
    message = template["body"]
    message = message.replace('{salutation}', salutation)
    message = message.replace('{prenom}', prenom)
    message = message.replace('{entreprise}', entreprise)
    message = message.replace('{ville}', ville)
    message = message.replace('{metier}', metier)
    message = message.replace('{note}', note)
    message = message.replace('{nombre_avis}', nombre_avis)
    message = message.replace('{site_web}', site_web)
    
    # Nettoyer les doubles espaces et lignes vides
    lines = [line.strip() for line in message.split('\n') if line.strip()]
    message = '\n'.join(lines)
    
    # Nettoyer les doubles espaces
    import re
    message = re.sub(r' +', ' ', message)
    
    return message


def get_template_by_id(template_id: str) -> Optional[dict]:
    """
    Récupère un template par son ID
    
    Args:
        template_id: ID du template
    
    Returns:
        Template ou None si non trouvé
    """
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    return None

