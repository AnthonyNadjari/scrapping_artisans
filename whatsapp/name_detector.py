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
    
    # Filtrer les tokens vides et les mots communs non-prénoms
    mots_exclus = {
        # Articles et prépositions
        'le', 'la', 'les', 'du', 'de', 'des', 'et', 'en', 'sur', 'dans', 'pour', 'avec',
        # Formes juridiques
        'sarl', 'eurl', 'sas', 'sa', 'sci', 'snc', 'sas', 'ets', 'ets.',
        # Mots métier
        'plomberie', 'plombier', 'electricite', 'électricité', 'chauffage', 'chauffagiste',
        'artisan', 'artisans', 'sanitaire', 'sanitaires', 'thermique', 'thermiques',
        'urgence', 'urgences', 'depannage', 'dépannage', 'installation', 'installations',
        'renovation', 'rénovation', 'renovations', 'rénovations', 'couverture', 'couvertures',
        'climatisation', 'pompe', 'chaleur', 'energie', 'énergie', 'energies', 'énergies',
        'confort', 'services', 'service', 'entreprise', 'entreprises', 'societe', 'société',
        'societes', 'sociétés', 'freres', 'frères', 'fils', 'fille', 'filles',
        # Mots techniques
        'bati', 'batiment', 'bâtiment', 'materiaux', 'matériaux', 'proximite', 'proximité',
        'home', 'eco', 'atmosphere', 'atmosphère', 'acp', 'apsd', 'js', 'jm', 'dt', 'dte',
        'kds', 'mds', 'srj', 'tplc', 'f2k', 'sl2a', 'dhts', 'help', 'petit',
        'grand', 'nouveau', 'nouvelle', 'express', 'express\'eau', 'toplombier',
        # Noms de lieux communs
        'france', 'paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes', 'strasbourg',
        'montpellier', 'bordeaux', 'lille', 'rennes', 'reims', 'saint', 'sainte',
        'nemours', 'melun', 'bailleul', 'moussy', 'lafforest', 'mebtouche', 'canaliseau',
        'pillon', 'pillaud', 'lusielec', 'energiterm', 'climerson', 'samsara', 'monteiro',
        'sampaio', 'latour', 'baillet', 'baillet', 'both', 'both', 'danes', 'danes',
        'petillat', 'loison', 'benedittis', 'morgano',
        # Retirer "ben" de la liste (c'est un prénom)
        # Retirer "morgan" de la liste (c'est un prénom)
        # Garder "fils", "pere", "père" pour filtrer mais permettre "Maurice" avant
        'fils', 'pere', 'père', 'mere', 'mère'
    }
    
    # Vérifier TOUS les tokens (pas seulement les 3 premiers)
    # Priorité aux tokens en début et fin de nom (plus probable d'être un prénom)
    # Structure typique: "Prénom Nom" ou "Nom Prénom" ou "Entreprise Prénom"
    if len(tokens) > 3:
        # Vérifier d'abord les 2 premiers et 2 derniers tokens
        tokens_to_check = tokens[:2] + tokens[-2:] + tokens[2:-2]
    else:
        tokens_to_check = tokens
    
    for token in tokens_to_check:
        if not token:
            continue
        
        # Nettoyer le token (enlever ponctuation)
        token_clean = re.sub(r'[^\w]', '', token.lower())
        
        if not token_clean or len(token_clean) < 3:
            continue
        
        # Ignorer les mots exclus
        if token_clean in mots_exclus:
            continue
        
        # Vérifier si c'est un prénom (correspondance exacte)
        if token_clean in prenoms_set:
            # Retourner avec majuscule initiale
            return token.capitalize()
        
        # Vérifier les correspondances partielles (pour "Yann" dans "Yannick", etc.)
        # Mais seulement si le token fait au moins 3 caractères et le prénom au moins 4
        for prenom in prenoms_set:
            if len(prenom) < 4 or len(token_clean) < 3:
                continue
            # Correspondance exacte avec préfixe (token commence par prénom)
            if token_clean.startswith(prenom[:min(4, len(prenom))]):
                return token.capitalize()
            # Correspondance exacte avec préfixe (prénom commence par token)
            if len(token_clean) >= 4 and prenom.startswith(token_clean[:4]):
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

