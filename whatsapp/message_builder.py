"""
Orchestration de la génération de messages personnalisés
"""
from typing import Optional
from whatsapp.phone_utils import (
    is_mobile, is_landline, 
    format_display
)
from whatsapp.name_detector import detect_prenom, detect_company_type
from whatsapp.templates import select_template, build_message


def detect_site_type(site_web: Optional[str]) -> str:
    """
    Détecte le type de site web
    
    Args:
        site_web: URL du site web
    
    Returns:
        "none", "facebook", "instagram", "linkedin", ou "website"
    """
    if not site_web or not str(site_web).strip():
        return "none"
    
    site_lower = str(site_web).lower()
    
    if 'facebook.com' in site_lower or 'fb.me' in site_lower:
        return "facebook"
    
    if 'instagram.com' in site_lower:
        return "instagram"
    
    if 'linkedin.com' in site_lower:
        return "linkedin"
    
    # Si c'est une URL valide, c'est un site web
    if site_lower.startswith('http://') or site_lower.startswith('https://'):
        return "website"
    
    return "none"


def prepare_artisan_message(artisan: dict) -> dict:
    """
    Prépare le message personnalisé pour un artisan
    
    Args:
        artisan: Dictionnaire avec les colonnes de la table artisans
    
    Returns:
        Dictionnaire enrichi avec les informations de message
    """
    telephone = artisan.get('telephone', '') or ''
    site_web = artisan.get('site_web')
    
    # Détecter le type de site
    site_type = detect_site_type(site_web)
    
    # Détecter le prénom
    prenom_detected = detect_prenom(artisan.get('nom_entreprise', ''))
    
    # Vérifier le type de téléphone
    is_mobile_phone = is_mobile(telephone)
    is_landline_phone = is_landline(telephone)
    
    # Catégoriser
    if is_mobile_phone:
        category = "whatsapp"
    elif is_landline_phone:
        category = "cold_call"
    else:
        category = "invalid"
    
    # Sélectionner le template
    template = select_template(artisan)
    
    # Construire le message avec le prénom détecté
    message = build_message(artisan, template, prenom_detected)
    
    # Déterminer si SMS peut être envoyé (seulement si mobile)
    sms_available = is_mobile_phone
    
    # Format d'affichage du téléphone
    telephone_display = format_display(telephone)
    
    # Extraire le département depuis le code postal si manquant
    departement = artisan.get('departement', '')
    if not departement and artisan.get('code_postal'):
        code_postal = str(artisan.get('code_postal', '')).strip()
        if len(code_postal) >= 2:
            # Pour les départements d'outre-mer (97x, 98x), prendre les 3 premiers chiffres
            if code_postal.startswith('97') or code_postal.startswith('98'):
                departement = code_postal[:3]
            else:
                departement = code_postal[:2]
    
    # Récupérer les autres champs de l'artisan pour l'affichage
    return {
        "artisan_id": artisan.get('id'),
        "nom_entreprise": artisan.get('nom_entreprise', ''),
        "telephone": telephone,
        "telephone_display": telephone_display,
        "is_mobile": is_mobile_phone,
        "is_landline": is_landline_phone,
        "template_used": template.get('id', ''),
        "template_name": template.get('name', ''),
        "message": message,
        "sms_available": sms_available,
        "site_type": site_type,
        "prenom_detected": prenom_detected,
        "category": category,
        "ville": artisan.get('ville', '') or artisan.get('ville_recherche', ''),
        "departement": departement,
        "code_postal": artisan.get('code_postal', ''),
        "adresse": artisan.get('adresse', ''),
        "type_artisan": artisan.get('type_artisan', '') or artisan.get('recherche', '') or artisan.get('metier', ''),
        "site_web": artisan.get('site_web', ''),
        "note": artisan.get('note'),
        "nombre_avis": artisan.get('nombre_avis'),
        # Ajouter tous les autres champs de la DB pour l'export
        "ville_recherche": artisan.get('ville_recherche', ''),
        "source": artisan.get('source', ''),
        "created_at": artisan.get('created_at', '')
    }


def prepare_batch(artisans: list[dict]) -> list[dict]:
    """
    Prépare les messages pour une liste d'artisans
    
    Args:
        artisans: Liste de dictionnaires avec les données des artisans
    
    Returns:
        Liste enrichie, triée par catégorie (whatsapp en premier)
    """
    results = []
    
    for artisan in artisans:
        try:
            prepared = prepare_artisan_message(artisan)
            results.append(prepared)
        except Exception as e:
            # En cas d'erreur, créer un résultat minimal
            results.append({
                "artisan_id": artisan.get('id'),
                "nom_entreprise": artisan.get('nom_entreprise', ''),
                "telephone": artisan.get('telephone', ''),
                "telephone_display": format_display(artisan.get('telephone', '')),
                "is_mobile": False,
                "is_landline": False,
                "template_used": "error",
                "template_name": "Erreur",
                "message": f"Erreur lors de la génération: {str(e)}",
                "sms_available": False,
                "site_type": "none",
                "prenom_detected": None,
                "category": "invalid"
            })
    
    # Trier par catégorie (whatsapp > cold_call > invalid)
    category_order = {"whatsapp": 0, "cold_call": 1, "invalid": 2}
    results.sort(key=lambda x: category_order.get(x.get("category", "invalid"), 2))
    
    return results

