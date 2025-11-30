"""
Détection de prénoms et classification du type d'entreprise
"""
import re
from pathlib import Path
from typing import Optional


def load_prenoms() -> set:
    """
    Charge le fichier prenoms_fr.txt
    
    Returns:
        Set de prénoms en minuscules pour recherche rapide
    """
    prenoms_file = Path(__file__).parent.parent / "data" / "prenoms_fr.txt"
    
    if not prenoms_file.exists():
        return set()
    
    try:
        with open(prenoms_file, 'r', encoding='utf-8') as f:
            prenoms = {line.strip().lower() for line in f if line.strip()}
        return prenoms
    except Exception:
        return set()


def detect_prenom(nom_entreprise: str) -> Optional[str]:
    """
    Analyse le nom de l'entreprise pour trouver un prénom
    
    Logique:
    - Séparer la chaîne en tokens (espaces, tirets, underscores)
    - Vérifier les 2-3 premiers tokens contre la liste de prénoms
    - Si un match est trouvé, retourner le prénom avec majuscule initiale
    
    Args:
        nom_entreprise: Nom de l'entreprise à analyser
    
    Returns:
        Prénom détecté (ex: "Jean") ou None
    """
    if not nom_entreprise:
        return None
    
    prenoms_set = load_prenoms()
    if not prenoms_set:
        return None
    
    # Nettoyer et normaliser
    nom_clean = nom_entreprise.strip()
    
    # Séparer en tokens (espaces, tirets, underscores, apostrophes)
    tokens = re.split(r'[\s\-_\'"]+', nom_clean)
    
    # Vérifier les 2-3 premiers tokens
    for i, token in enumerate(tokens[:3]):
        if not token:
            continue
        
        # Nettoyer le token (enlever ponctuation)
        token_clean = re.sub(r'[^\w]', '', token.lower())
        
        if not token_clean:
            continue
        
        # Vérifier si c'est un prénom
        if token_clean in prenoms_set:
            # Retourner avec majuscule initiale
            return token.capitalize()
    
    return None


def detect_company_type(nom_entreprise: str) -> str:
    """
    Catégorise le type d'entreprise
    
    Returns:
        "individuel", "societe", ou "indetermine"
    """
    if not nom_entreprise:
        return "indetermine"
    
    nom_upper = nom_entreprise.upper()
    nom_lower = nom_entreprise.lower()
    
    # Indices pour "societe"
    societe_keywords = [
        'sarl', 'sas', 'eurl', 'sa', 'sas', 'sci', 'snc',
        'ets', 'etablissement', 'établissement',
        'entreprise', 'societe', 'société',
        '&', 'fils', 'freres', 'frères', 'group', 'groupe',
        'services', 'solutions', 'plomberie', 'electricite', 'électricité'
    ]
    
    # Vérifier les mots-clés de société
    for keyword in societe_keywords:
        if keyword in nom_lower:
            return "societe"
    
    # Nom en majuscules complet (souvent nom commercial)
    if nom_entreprise.isupper() and len(nom_entreprise.split()) > 1:
        return "societe"
    
    # Indices pour "individuel"
    prenom = detect_prenom(nom_entreprise)
    if prenom:
        # Format "Prénom Nom" ou "Prénom Nom Métier"
        tokens = nom_entreprise.split()
        if len(tokens) >= 2:
            # Si le premier token est un prénom, probablement individuel
            if tokens[0].capitalize() == prenom:
                return "individuel"
    
    return "indetermine"


def get_salutation(nom_entreprise: str) -> str:
    """
    Génère la formule de salutation appropriée
    
    Si prénom détecté → "Bonjour {Prénom}"
    Sinon → "Bonjour"
    
    Args:
        nom_entreprise: Nom de l'entreprise
    
    Returns:
        Formule de salutation
    """
    prenom = detect_prenom(nom_entreprise)
    if prenom:
        return f"Bonjour {prenom}"
    return "Bonjour"

