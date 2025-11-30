"""
Utilitaires pour la manipulation et validation des numéros de téléphone
"""
import re
from urllib.parse import quote
from typing import Optional


def clean_phone(phone: str) -> str:
    """
    Supprime tous les caractères non numériques d'un numéro
    
    Args:
        phone: Numéro de téléphone (ex: "06 12 34 56 78" ou "+33 6 12 34 56 78")
    
    Returns:
        Numéro nettoyé (ex: "0612345678" ou "33612345678")
    """
    if not phone:
        return ""
    return re.sub(r'\D', '', str(phone))


def normalize_for_whatsapp(phone: str) -> Optional[str]:
    """
    Convertit un numéro français au format international sans le "+"
    
    Règles:
    - Si commence par "0" et a 10 chiffres → remplacer "0" par "33"
    - Si commence par "33" et a 11 chiffres → garder tel quel
    - Si commence par "+33" → retirer le "+"
    - Si commence par "0033" → retirer les deux premiers "0"
    
    Args:
        phone: Numéro de téléphone à normaliser
    
    Returns:
        Numéro au format international (ex: "33612345678") ou None si invalide
    """
    if not phone:
        return None
    
    cleaned = clean_phone(phone)
    
    if not cleaned:
        return None
    
    # Si commence par 0033, retirer les deux premiers 0
    if cleaned.startswith("0033") and len(cleaned) == 13:
        cleaned = cleaned[2:]  # Retirer "00"
    
    # Si commence par +33 (déjà nettoyé, donc juste "33")
    if cleaned.startswith("33") and len(cleaned) == 11:
        return cleaned
    
    # Si commence par 0 et a 10 chiffres, remplacer 0 par 33
    if cleaned.startswith("0") and len(cleaned) == 10:
        return "33" + cleaned[1:]
    
    # Si déjà au bon format (11 chiffres commençant par 33)
    if cleaned.startswith("33") and len(cleaned) == 11:
        return cleaned
    
    # Numéro invalide
    return None


def is_mobile(phone: str) -> bool:
    """
    Détermine si c'est un numéro mobile (peut recevoir WhatsApp)
    
    Un numéro mobile français commence par:
    - "06" ou "07" (format local)
    - "336" ou "337" (format international)
    
    Args:
        phone: Numéro de téléphone
    
    Returns:
        True si mobile, False sinon
    """
    if not phone:
        return False
    
    cleaned = clean_phone(phone)
    
    if not cleaned:
        return False
    
    # Format international (11 chiffres)
    if len(cleaned) == 11 and cleaned.startswith("33"):
        return cleaned.startswith("336") or cleaned.startswith("337")
    
    # Format local (10 chiffres)
    if len(cleaned) == 10:
        return cleaned.startswith("06") or cleaned.startswith("07")
    
    return False


def is_landline(phone: str) -> bool:
    """
    Détermine si c'est un numéro fixe (ne peut pas recevoir WhatsApp)
    
    Les numéros commençant par 01, 02, 03, 04, 05, 08, 09 sont des fixes
    
    Args:
        phone: Numéro de téléphone
    
    Returns:
        True si fixe, False sinon
    """
    if not phone:
        return False
    
    cleaned = clean_phone(phone)
    
    if not cleaned:
        return False
    
    # Format international (11 chiffres)
    if len(cleaned) == 11 and cleaned.startswith("33"):
        # 01 → 331, 02 → 332, etc.
        return cleaned.startswith("331") or cleaned.startswith("332") or \
               cleaned.startswith("333") or cleaned.startswith("334") or \
               cleaned.startswith("335") or cleaned.startswith("338") or \
               cleaned.startswith("339")
    
    # Format local (10 chiffres)
    if len(cleaned) == 10:
        return cleaned.startswith("01") or cleaned.startswith("02") or \
               cleaned.startswith("03") or cleaned.startswith("04") or \
               cleaned.startswith("05") or cleaned.startswith("08") or \
               cleaned.startswith("09")
    
    return False


def format_display(phone: str) -> str:
    """
    Formate un numéro pour l'affichage lisible
    
    Args:
        phone: Numéro de téléphone
    
    Returns:
        Numéro formaté (ex: "06 12 34 56 78")
    """
    if not phone:
        return ""
    
    cleaned = clean_phone(phone)
    
    if not cleaned:
        return phone  # Retourner l'original si on ne peut pas nettoyer
    
    # Si format international (11 chiffres), retirer le 33 et ajouter 0
    if len(cleaned) == 11 and cleaned.startswith("33"):
        cleaned = "0" + cleaned[2:]
    
    # Formater en groupes de 2 chiffres
    if len(cleaned) == 10:
        return f"{cleaned[0:2]} {cleaned[2:4]} {cleaned[4:6]} {cleaned[6:8]} {cleaned[8:10]}"
    
    # Si format non standard, retourner tel quel
    return phone


def generate_wa_link(phone: str, message: str) -> Optional[str]:
    """
    Génère un lien WhatsApp cliquable
    
    Format: https://wa.me/{numero_international}?text={message_encodé}
    
    Args:
        phone: Numéro de téléphone
        message: Message à envoyer
    
    Returns:
        Lien WhatsApp ou None si le numéro n'est pas mobile ou invalide
    """
    if not phone or not message:
        return None
    
    # Vérifier que c'est un mobile
    if not is_mobile(phone):
        return None
    
    # Normaliser le numéro
    normalized = normalize_for_whatsapp(phone)
    if not normalized:
        return None
    
    # Encoder le message
    encoded_message = quote(message)
    
    # Générer le lien
    return f"https://wa.me/{normalized}?text={encoded_message}"

