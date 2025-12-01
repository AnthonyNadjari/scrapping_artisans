"""
Templates de messages WhatsApp personnalisés
"""
from typing import Optional
from whatsapp.name_detector import get_salutation


# Définition des templates
TEMPLATES = [
    {
        "id": "reputation_no_site",
        "name": "REPUTATION × Pas de site",
        "priority": 100,
        "condition": lambda a: (not a.get('site_web') or str(a.get('site_web', '')).strip() == '') and
                              a.get('note') and float(a.get('note', 0)) >= 4.0 and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 5,
        "body": """Bonjour,

J'ai consulté votre fiche Google Maps en recherchant un {metier} à {ville} : {note}/5 avec {nombre_avis} avis, vous avez clairement une clientèle satisfaite.

Pourtant, sans site web, les personnes qui recherchent "{metier} {ville}" sur Google ne voient que votre fiche Maps. Un site professionnel permettrait de présenter vos prestations et de recevoir des demandes directement par mail grâce à un formulaire de contact.

Je réalise des sites vitrines pour artisans à des tarifs accessibles. Vous ne payez rien tant que le site n'est pas en ligne.

Voici un exemple : https://plomberie-fluide.vercel.app/

N'hésitez pas à revenir vers moi si ça vous intéresse.

Anthony"""
    },
    {
        "id": "reputation_social",
        "name": "REPUTATION × Facebook/Instagram",
        "priority": 95,
        "condition": lambda a: a.get('site_web') and (
            'facebook.com' in str(a.get('site_web', '')).lower() or
            'instagram.com' in str(a.get('site_web', '')).lower() or
            'fb.me' in str(a.get('site_web', '')).lower()
        ) and a.get('note') and float(a.get('note', 0)) >= 4.0 and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 5,
        "body": """Bonjour,

J'ai trouvé votre entreprise en recherchant un {metier} à {ville} : {note}/5 avec {nombre_avis} avis sur Google, vous avez clairement une bonne réputation.

Je remarque que votre présence en ligne passe principalement par Facebook/Instagram. Ces pages sont utiles, mais elles ressortent moins bien qu'un vrai site web quand un client recherche "{metier} {ville}" sur Google.

Je réalise des sites vitrines pour artisans, optimisés pour le référencement local, avec formulaire de contact intégré. Tarifs accessibles, et vous ne payez rien tant que le site n'est pas livré.

Voici un exemple : https://plomberie-fluide.vercel.app/

N'hésitez pas à revenir vers moi si ça vous intéresse.

Anthony"""
    },
    {
        "id": "credibilite_no_site",
        "name": "CREDIBILITE × Pas de site",
        "priority": 90,
        "condition": lambda a: (not a.get('site_web') or str(a.get('site_web', '')).strip() == '') and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 3,
        "body": """Bonjour,

J'ai trouvé votre entreprise sur Google Maps en recherchant un {metier} à {ville}. Vos {nombre_avis} avis montrent que vous avez une clientèle régulière.

Un site web professionnel vous permettrait d'aller plus loin : présenter vos prestations, montrer des photos de réalisations, et recevoir des demandes de devis directement par mail grâce à un formulaire de contact.

Je crée des sites vitrines pour artisans à des tarifs accessibles. Vous ne payez rien tant que le site n'est pas en ligne.

Voici un exemple : https://plomberie-fluide.vercel.app/

N'hésitez pas à revenir vers moi si ça vous intéresse.

Anthony"""
    },
    {
        "id": "credibilite_social",
        "name": "CREDIBILITE × Facebook/Instagram",
        "priority": 85,
        "condition": lambda a: a.get('site_web') and (
            'facebook.com' in str(a.get('site_web', '')).lower() or
            'instagram.com' in str(a.get('site_web', '')).lower() or
            'fb.me' in str(a.get('site_web', '')).lower()
        ) and a.get('note') and float(a.get('note', 0)) >= 0 and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 3,
        "body": """Bonjour,

J'ai consulté votre page en recherchant un {metier} vers {ville}. Avec {note}/5 et {nombre_avis} avis sur Google, vous avez une bonne réputation.

Une page Facebook est utile, mais elle ne remonte pas aussi bien qu'un site web dans les recherches Google locales. Un site dédié vous donnerait plus de visibilité et un formulaire de contact pour recevoir les demandes par mail.

Je réalise des sites pour artisans à des tarifs accessibles, et vous ne payez rien tant que le site n'est pas livré.

Voici un exemple : https://plomberie-fluide.vercel.app/

N'hésitez pas à revenir vers moi si ça vous intéresse.

Anthony"""
    },
    {
        "id": "visibilite_social",
        "name": "VISIBILITE × Facebook/Instagram",
        "priority": 80,
        "condition": lambda a: a.get('site_web') and (
            'facebook.com' in str(a.get('site_web', '')).lower() or
            'instagram.com' in str(a.get('site_web', '')).lower() or
            'fb.me' in str(a.get('site_web', '')).lower()
        ),
        "body": """Bonjour,

J'ai trouvé votre page en recherchant un {metier} vers {ville}.

Avoir une page Facebook c'est un bon début, mais un site web dédié sera toujours mieux positionné sur Google. Ça vous permettrait aussi d'avoir un formulaire de contact qui vous envoie les demandes directement par mail.

Je crée des sites vitrines pour artisans à des tarifs accessibles. Vous ne payez rien tant que le site n'est pas livré.

Voici un exemple : https://plomberie-fluide.vercel.app/

N'hésitez pas à revenir vers moi si ça vous intéresse.

Anthony"""
    },
    {
        "id": "fallback",
        "name": "FALLBACK",
        "priority": 10,
        "condition": lambda a: True,  # Toujours True (fallback)
        "body": """Bonjour,

Je me permets de vous contacter car je réalise des sites web pour les artisans.

L'idée : un site simple qui vous permet d'apparaître sur Google quand quelqu'un cherche un professionnel dans votre zone, avec un formulaire de contact qui vous envoie les demandes par mail.

Tarifs accessibles et vous ne payez rien tant que le site n'est pas en ligne.

Voici un exemple : https://plomberie-fluide.vercel.app/

N'hésitez pas à revenir vers moi si ça vous intéresse.

Anthony"""
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
    # Préparer les variables
    ville = artisan.get('ville') or artisan.get('ville_recherche') or ''
    metier = artisan.get('type_artisan', 'artisan') or 'artisan'
    
    # Note et nombre d'avis - gérer les cas où ils sont None ou vides
    # Note: le template contient déjà "/5" donc on ne met que la valeur numérique
    note = ''
    if artisan.get('note'):
        try:
            note_val = float(artisan.get('note'))
            note = str(note_val) if note_val > 0 else ''
        except:
            note = ''
    
    nombre_avis = ''
    if artisan.get('nombre_avis'):
        try:
            nombre_avis = str(int(artisan.get('nombre_avis')))
        except:
            nombre_avis = ''
    
    # Si note ou nombre_avis sont vides mais requis par le template, utiliser des valeurs par défaut
    if not note and '{note}' in template["body"]:
        note = 'N/A'
    if not nombre_avis and '{nombre_avis}' in template["body"]:
        nombre_avis = 'N/A'
    
    # Remplacer les placeholders
    message = template["body"]
    message = message.replace('{ville}', ville)
    message = message.replace('{metier}', metier)
    message = message.replace('{note}', note)
    message = message.replace('{nombre_avis}', nombre_avis)
    
    # Nettoyer les lignes vides en trop mais garder la structure
    lines = []
    prev_empty = False
    for line in message.split('\n'):
        stripped = line.strip()
        if stripped:
            lines.append(line)
            prev_empty = False
        elif not prev_empty:
            # Garder une seule ligne vide entre les paragraphes
            lines.append('')
            prev_empty = True
    
    # Enlever les lignes vides en début et fin
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    message = '\n'.join(lines)
    
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

