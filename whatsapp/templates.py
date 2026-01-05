"""
Templates de messages WhatsApp personnalisés
"""
import re
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

Je suis tombé sur votre fiche Google en cherchant un {metier} sur {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être mieux positionné ! Je crée des sites simples pour les artisans :
- Présentation claire de vos services.
- Formulaire de contact pour recevoir des demandes directement.

Vous payez une seule fois, quand le site est prêt.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Si ça vous intéresse, je suis dispo pour en discuter !

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

Je suis tombé sur votre page Facebook en cherchant un {metier} sur {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être plus visible ! Je peux vous créer un site simple qui présente vos services et permet aux clients de vous contacter directement.

Vous payez uniquement une fois, à la fin.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Dites-moi si ça vous parle !

Anthony"""
    },
    {
        "id": "credibilite_no_site",
        "name": "CREDIBILITE × Pas de site",
        "priority": 90,
        "condition": lambda a: (not a.get('site_web') or str(a.get('site_web', '')).strip() == '') and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 3,
        "body": """Bonjour,

Je suis tombé sur votre entreprise en cherchant un {metier} vers {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être plus visible et à recevoir plus de demandes !

Je fais des sites simples pour les artisans :
- Présentation de vos services.
- Formulaire pour recevoir des demandes directement.

Vous payez uniquement quand le site est en ligne.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Si vous voulez en savoir plus, je suis là !

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

Je suis tombé sur votre page Facebook en cherchant un {metier} vers {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être plus visible et à attirer plus de clients !

Je peux vous créer un site simple :
- Présentation de vos services.
- Formulaire de contact pour les clients.

Vous payez une seule fois, à la fin.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Dites-moi si ça vous intéresse !

Anthony"""
    },
    {
        "id": "credibilite_website",
        "name": "CREDIBILITE × Site web classique",
        "priority": 88,
        "condition": lambda a: a.get('site_web') and str(a.get('site_web', '')).strip() != '' and
                              not ('facebook.com' in str(a.get('site_web', '')).lower() or
                                   'instagram.com' in str(a.get('site_web', '')).lower() or
                                   'fb.me' in str(a.get('site_web', '')).lower()) and
                              a.get('note') and float(a.get('note', 0)) >= 0 and
                              a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 3,
        "body": """Bonjour,

Je suis tombé sur votre entreprise en cherchant un {metier} vers {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être plus visible et à recevoir plus de demandes !

Je fais des sites simples pour les artisans :
- Présentation de vos services.
- Formulaire de contact pour les clients.

Vous payez uniquement quand le site est en ligne.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Si vous voulez en savoir plus, je suis là !

Anthony"""
    },
    {
        "id": "visibilite_no_site",
        "name": "VISIBILITE × Pas de site",
        "priority": 82,
        "condition": lambda a: (not a.get('site_web') or str(a.get('site_web', '')).strip() == '') and
                              (a.get('note') or a.get('nombre_avis')) and
                              (not a.get('note') or float(a.get('note', 0)) < 4.0 or
                               not a.get('nombre_avis') or int(a.get('nombre_avis', 0)) < 3),
        "body": """Bonjour,

Je suis tombé sur votre fiche Google en cherchant un {metier} sur {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être mieux positionné et à recevoir plus de demandes !

Je fais des sites simples pour les artisans :
- Présentation de vos services.
- Formulaire de contact pour les clients.

Vous payez uniquement quand le site est prêt.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Si ça vous parle, je suis dispo !

Anthony"""
    },
    {
        "id": "visibilite_no_site_sans_avis",
        "name": "VISIBILITE × Pas de site (sans avis)",
        "priority": 81,
        "condition": lambda a: (not a.get('site_web') or str(a.get('site_web', '')).strip() == '') and
                              (not a.get('note') or float(a.get('note', 0)) == 0) and
                              (not a.get('nombre_avis') or int(a.get('nombre_avis', 0)) == 0),
        "body": """Bonjour,

Je suis tombé sur votre fiche Google en cherchant un {metier} sur {ville}. Vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être mieux positionné et à recevoir plus de demandes !

Je fais des sites simples pour les artisans :
- Présentation de vos services.
- Formulaire de contact pour les clients.

Vous payez uniquement quand le site est prêt.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Si ça vous parle, je suis dispo !

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
        ) and (a.get('note') or a.get('nombre_avis')) and not (
            a.get('note') and float(a.get('note', 0)) >= 4.0 and
            a.get('nombre_avis') and int(a.get('nombre_avis', 0)) >= 5
        ),
        "body": """Bonjour,

Je suis tombé sur votre page Facebook en cherchant un {metier} vers {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être mieux référencé sur Google ! Je peux vous en créer un simple pour présenter vos services et recevoir des demandes directement.

Vous payez une seule fois, à la fin.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Dites-moi si ça vous intéresse !

Anthony"""
    },
    {
        "id": "visibilite_social_sans_avis",
        "name": "VISIBILITE × Facebook/Instagram (sans avis)",
        "priority": 79,
        "condition": lambda a: a.get('site_web') and (
            'facebook.com' in str(a.get('site_web', '')).lower() or
            'instagram.com' in str(a.get('site_web', '')).lower() or
            'fb.me' in str(a.get('site_web', '')).lower()
        ) and (not a.get('note') or float(a.get('note', 0)) == 0) and
                              (not a.get('nombre_avis') or int(a.get('nombre_avis', 0)) == 0),
        "body": """Bonjour,

Je suis tombé sur votre page Facebook en cherchant un {metier} vers {ville}. Vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être mieux référencé sur Google ! Je peux vous en créer un simple pour présenter vos services et recevoir des demandes directement.

Vous payez une seule fois, à la fin.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Dites-moi si ça vous intéresse !

Anthony"""
    },
    {
        "id": "fallback",
        "name": "FALLBACK",
        "priority": 10,
        "condition": lambda a: True,  # Toujours True (fallback)
        "body": """Bonjour,

Je suis tombé sur votre entreprise en cherchant un {metier} vers {ville}. J'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, vous n'êtes pas apparu en haut des résultats !

Un site web pourrait vous aider à être plus visible et à recevoir plus de demandes !

Je fais des sites simples pour les artisans :
- Présentation de vos services.
- Formulaire de contact pour les clients.

Vous payez uniquement quand le site est en ligne.

Exemple : [https://plomberie-fluide.vercel.app/](https://plomberie-fluide.vercel.app/)

Si ça vous parle, je suis là !

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


def build_message(artisan: dict, template: dict, prenom: Optional[str] = None) -> str:
    """
    Construit le message final en remplaçant les placeholders
    
    Args:
        artisan: Dictionnaire avec les données de l'artisan
        template: Template sélectionné
        prenom: Prénom détecté (optionnel)
    
    Returns:
        Message final avec placeholders remplacés
    """
    # Préparer les variables
    ville = artisan.get('ville') or artisan.get('ville_recherche') or ''
    metier = artisan.get('type_artisan', 'artisan') or 'artisan'
    
    # Utiliser le prénom si disponible, sinon utiliser "Bonjour"
    salutation = f"Bonjour {prenom}" if prenom else "Bonjour"
    
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
    
    # Remplacer les placeholders
    message = template["body"]
    
    # Remplacer la salutation si un prénom est fourni
    if prenom:
        # Remplacer "Bonjour," par "Bonjour {prenom}," (première occurrence seulement)
        if message.startswith("Bonjour,"):
            message = "Bonjour " + prenom + "," + message[8:]  # Remplacer "Bonjour," par "Bonjour {prenom},"
        elif message.startswith("Bonjour\n"):
            message = "Bonjour " + prenom + ",\n" + message[9:]  # Remplacer "Bonjour\n" par "Bonjour {prenom},\n"
    
    # Remplacer les autres placeholders
    message = message.replace('{ville}', ville)
    message = message.replace('{metier}', metier)
    
    # Gérer note et nombre_avis : si vides, enlever les références dans le message
    if note and nombre_avis:
        message = message.replace('{note}/5 avec {nombre_avis} avis', f'{note}/5 avec {nombre_avis} avis')
        message = message.replace('{note}', note)
        message = message.replace('{nombre_avis}', nombre_avis)
    elif note:
        message = message.replace('{note}/5 avec {nombre_avis} avis', f'{note}/5')
        message = message.replace('{note}', note)
        message = message.replace('{nombre_avis}', '')
        message = message.replace('avec  avis', '')
    elif nombre_avis:
        message = message.replace('{note}/5 avec {nombre_avis} avis', f'{nombre_avis} avis')
        message = message.replace('{note}', '')
        message = message.replace('{nombre_avis}', nombre_avis)
        message = message.replace('/5 avec', 'avec')
    else:
        # Les deux sont vides, enlever toute la référence
        message = message.replace('J\'ai vu que vous avez {note}/5 avec {nombre_avis} avis, mais malgré ça, ', '')
        message = message.replace('{note}/5 avec {nombre_avis} avis', '')
        message = message.replace('{note}', '')
        message = message.replace('{nombre_avis}', '')
    
    # Nettoyer les lignes vides en trop - être plus agressif
    # Remplacer toutes les séquences de lignes vides (2+) par une seule ligne vide
    message = re.sub(r'\n{3,}', '\n\n', message)
    
    # Enlever les lignes vides en début et fin
    message = message.strip()
    
    # Nettoyer les lignes vides autour des puces - pas de ligne vide avant une puce
    lines = message.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Si c'est une ligne vide
        if not stripped:
            # Ne garder la ligne vide que si la ligne suivante n'est pas une puce
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('-'):
                continue  # Ignorer cette ligne vide avant une puce
            # Ne garder qu'une seule ligne vide consécutive
            if cleaned_lines and cleaned_lines[-1].strip() == '':
                continue  # Ignorer les lignes vides consécutives
            cleaned_lines.append('')
        else:
            cleaned_lines.append(line)
    
    message = '\n'.join(cleaned_lines)
    
    # Final cleanup - enlever les lignes vides en début et fin
    message = message.strip()
    
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

