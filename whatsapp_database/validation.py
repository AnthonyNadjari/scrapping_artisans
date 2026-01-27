"""
Data Validation Module for Artisan Database
============================================
Provides validation and normalization functions to ensure data integrity.
"""
import re
import hashlib
from typing import Optional, Dict, Tuple


def normalize_phone(phone: str) -> Optional[str]:
    """
    Normalize French phone number to international format.

    Args:
        phone: Raw phone number string

    Returns:
        Normalized phone in +33XXXXXXXXX format, or None if invalid
    """
    if not phone:
        return None

    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', str(phone))

    # Handle French formats
    if cleaned.startswith('0') and len(cleaned) == 10:
        # Convert 0612345678 to +33612345678
        cleaned = '+33' + cleaned[1:]
    elif cleaned.startswith('33') and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    elif cleaned.startswith('+33'):
        pass  # Already correct format
    else:
        # Invalid format
        return None

    # Validate length (+33 + 9 digits = 12 characters)
    if len(cleaned) != 12:
        return None

    # Validate it starts with valid French mobile/landline prefixes
    suffix = cleaned[3:]  # Remove +33
    if not suffix[0] in '123456789':
        return None

    return cleaned


def normalize_address(address: str) -> str:
    """
    Normalize address for deduplication comparison.

    Args:
        address: Raw address string

    Returns:
        Normalized address string
    """
    if not address:
        return ""

    normalized = str(address).lower().strip()

    # Remove common noise words
    noise_words = ['france', 'closed', 'fermé', 'fermée', 'ouvert', 'open',
                   'closes', 'opens', 'soon', 'opening']
    for word in noise_words:
        normalized = normalized.replace(word, '')

    # Remove punctuation and extra whitespace
    normalized = re.sub(r'[,;.\n\r]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def normalize_name(name: str) -> str:
    """
    Normalize business name for deduplication comparison.

    Args:
        name: Raw business name

    Returns:
        Normalized name string
    """
    if not name:
        return ""

    normalized = str(name).lower().strip()

    # Remove common business suffixes
    suffixes = ['sarl', 'sas', 'eurl', 'sa', 'sasu', 'snc']
    for suffix in suffixes:
        normalized = re.sub(rf'\b{suffix}\b', '', normalized)

    # Remove punctuation and extra whitespace
    normalized = re.sub(r'[,;.\-\'\"]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def extract_department_from_postal_code(code_postal: str) -> Optional[str]:
    """
    Extract French department code from postal code.

    Args:
        code_postal: French postal code (5 digits)

    Returns:
        Department code (2 or 3 digits for overseas) or None if invalid
    """
    if not code_postal:
        return None

    cp = str(code_postal).strip()

    # French postal codes are exactly 5 digits
    if not re.match(r'^\d{5}$', cp):
        return None

    # Basic range validation (01000-98999)
    cp_int = int(cp)
    if cp_int < 1000 or cp_int > 98999:
        return None

    # Overseas departments use 3 digits (97x, 98x)
    if cp.startswith('97') or cp.startswith('98'):
        return cp[:3]

    # Metropolitan France uses 2 digits
    return cp[:2]


def is_valid_french_postal_code(code_postal: str) -> bool:
    """
    Validate if a string is a valid French postal code.

    Args:
        code_postal: String to validate

    Returns:
        True if valid French postal code
    """
    return extract_department_from_postal_code(code_postal) is not None


def generate_dedup_key(data: Dict) -> str:
    """
    Generate a deduplication key from artisan data.

    Priority order:
    1. Phone number (if present and valid)
    2. SIRET (if present)
    3. Name + normalized address hash

    Args:
        data: Artisan data dictionary

    Returns:
        Deduplication key string
    """
    # Priority 1: Phone number
    phone = data.get('telephone')
    if phone:
        normalized_phone = normalize_phone(phone)
        if normalized_phone:
            return f"phone:{normalized_phone}"

    # Priority 2: SIRET
    siret = data.get('siret')
    if siret:
        cleaned_siret = re.sub(r'\D', '', str(siret))
        if len(cleaned_siret) == 14:
            return f"siret:{cleaned_siret}"

    # Priority 3: Name + Address hash
    name = normalize_name(data.get('nom_entreprise', ''))
    address = normalize_address(data.get('adresse', ''))

    if name and address:
        combined = f"{name}|{address}"
        hash_val = hashlib.md5(combined.encode()).hexdigest()[:16]
        return f"name_addr:{hash_val}"

    # Fallback: Cannot deduplicate
    return None


def validate_artisan_data(data: Dict) -> Tuple[bool, Dict, list]:
    """
    Validate and clean artisan data before insertion.

    Args:
        data: Raw artisan data dictionary

    Returns:
        Tuple of (is_valid, cleaned_data, errors)
    """
    errors = []
    cleaned = {}

    # Required: At least one of these must be present
    has_phone = bool(data.get('telephone'))
    has_site = bool(data.get('site_web'))
    has_name = bool(data.get('nom_entreprise') and
                    data.get('nom_entreprise') != 'N/A' and
                    len(str(data.get('nom_entreprise', ''))) >= 2)

    if not (has_phone or has_site or has_name):
        errors.append("Record must have phone, website, or valid name")
        return False, {}, errors

    # Clean phone number
    if data.get('telephone'):
        cleaned['telephone'] = normalize_phone(data['telephone'])
        if not cleaned['telephone'] and has_phone:
            # Phone was provided but is invalid
            cleaned['telephone'] = None  # Store as NULL

    # Clean and validate postal code / department
    code_postal = data.get('code_postal', '')
    if code_postal:
        cp = str(code_postal).strip()
        if re.match(r'^\d{5}$', cp):
            cleaned['code_postal'] = cp
            cleaned['departement'] = extract_department_from_postal_code(cp)
        else:
            errors.append(f"Invalid postal code: {code_postal}")

    # Fallback department from departement_recherche
    if not cleaned.get('departement') and data.get('departement_recherche'):
        cleaned['departement'] = data['departement_recherche']

    # Copy other fields with basic cleaning
    text_fields = ['nom_entreprise', 'adresse', 'ville', 'ville_recherche',
                   'departement_recherche', 'type_artisan', 'source',
                   'source_telephone', 'site_web', 'siret', 'nom', 'prenom',
                   'code_naf', 'statut_reponse', 'commentaire']

    for field in text_fields:
        if data.get(field):
            value = str(data[field]).strip()
            if value:
                cleaned[field] = value

    # Numeric fields
    if data.get('note') is not None:
        try:
            cleaned['note'] = float(data['note'])
        except (ValueError, TypeError):
            pass

    if data.get('nombre_avis') is not None:
        try:
            cleaned['nombre_avis'] = int(data['nombre_avis'])
        except (ValueError, TypeError):
            pass

    # Boolean fields
    for bool_field in ['a_whatsapp', 'message_envoye', 'a_repondu']:
        if data.get(bool_field) is not None:
            cleaned[bool_field] = 1 if data[bool_field] else 0

    return True, cleaned, errors


def clean_address(address: str) -> str:
    """
    Clean address by removing noise words and normalizing format.

    Args:
        address: Raw address string

    Returns:
        Cleaned address string
    """
    if not address:
        return ''

    cleaned = str(address)

    # Remove status words (Closed, Open, etc.)
    noise_patterns = [
        r'\s*(Closed|Closes|Closes soon|Fermé|Fermée|Ouvert|Open|Opens|Opening|Soon)\s*',
    ]
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Replace newlines with spaces
    cleaned = re.sub(r'\s*\n\s*', ' ', cleaned)

    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned
