"""
Email Parser for Google Form responses.

Parses the email notification content from Google Forms
and extracts structured data for website generation.
"""

import re
from typing import Dict, Any, Optional, List
from .trade_defaults import get_trade_key, get_trade_colors, TRADE_DISPLAY_NAMES

# Mapping of French form field names to config keys
FIELD_MAPPING = {
    "nom de l'entreprise": "business_name",
    "type de métier": "trade_type",
    "type de métier / activité": "trade_type",
    "si \"autre\", précisez": "trade_custom",
    "slogan": "slogan",
    "slogan ou phrase d'accroche": "slogan",
    "description courte": "description",
    "description courte de votre activité": "description",
    "adresse complète": "street",
    "adresse": "street",
    "code postal": "postal_code",
    "ville": "city",
    "téléphone": "phone",
    "horaires d'ouverture": "hours",
    "horaires": "hours",
    "liste de vos services": "services_raw",
    "services": "services_raw",
    "villes ou zones couvertes": "coverage_zones",
    "zones couvertes": "coverage_zones",
    "rayon d'intervention": "coverage_radius",
    "couleur principale": "primary_color",
    "couleur principale souhaitée": "primary_color",
    "couleur secondaire": "accent_color",
    "style du site": "style",
    "style": "style",
    "avez-vous des photos": "has_photos",
    "photos": "has_photos",
    "fonctionnalités souhaitées": "features",
    "fonctionnalités": "features",
    "date souhaitée": "launch_date",
    "nom de domaine": "domain",
    "nom de domaine souhaité": "domain",
    "remarques": "notes",
    "remarques ou demandes particulières": "notes",
    "email": "email",
    "adresse e-mail": "email",
}

# Color name to HSL mapping
COLOR_MAP = {
    # Blues
    "bleu": {"h": 220, "s": 60, "l": 45},
    "bleu foncé": {"h": 220, "s": 60, "l": 25},
    "bleu clair": {"h": 200, "s": 70, "l": 60},
    "bleu marine": {"h": 220, "s": 60, "l": 20},
    "navy": {"h": 220, "s": 60, "l": 20},
    # Reds/Oranges
    "rouge": {"h": 0, "s": 75, "l": 45},
    "orange": {"h": 25, "s": 85, "l": 50},
    "cuivre": {"h": 25, "s": 85, "l": 50},
    "terracotta": {"h": 15, "s": 60, "l": 45},
    # Greens
    "vert": {"h": 140, "s": 50, "l": 40},
    "vert foncé": {"h": 140, "s": 50, "l": 25},
    "vert clair": {"h": 140, "s": 50, "l": 55},
    # Yellows/Golds
    "jaune": {"h": 45, "s": 85, "l": 50},
    "or": {"h": 45, "s": 85, "l": 50},
    "doré": {"h": 45, "s": 85, "l": 50},
    # Purples
    "violet": {"h": 270, "s": 50, "l": 45},
    "pourpre": {"h": 280, "s": 60, "l": 40},
    # Grays/Blacks
    "gris": {"h": 0, "s": 0, "l": 50},
    "gris foncé": {"h": 0, "s": 0, "l": 30},
    "noir": {"h": 0, "s": 0, "l": 10},
    "anthracite": {"h": 0, "s": 0, "l": 20},
    # Browns
    "marron": {"h": 30, "s": 50, "l": 30},
    "brun": {"h": 30, "s": 50, "l": 30},
    "beige": {"h": 40, "s": 30, "l": 75},
    # Others
    "blanc": {"h": 0, "s": 0, "l": 98},
    "rose": {"h": 340, "s": 65, "l": 55},
    "turquoise": {"h": 175, "s": 60, "l": 45},
    "cyan": {"h": 180, "s": 70, "l": 45},
}

# Style mapping
STYLE_MAP = {
    "moderne": "modern",
    "modern": "modern",
    "classique": "classic",
    "classic": "classic",
    "traditionnel": "classic",
    "minimaliste": "minimal",
    "minimal": "minimal",
    "épuré": "minimal",
}


def parse_email_content(email_text: str) -> Dict[str, Any]:
    """
    Parse Google Form email notification content.

    Args:
        email_text: Raw email content (copy-pasted from email)

    Returns:
        Dictionary with parsed form data
    """
    # Initialize result
    parsed = {
        "business_name": "",
        "trade_type": "plumber",
        "slogan": "",
        "description": "",
        "street": "",
        "postal_code": "",
        "city": "",
        "phone": "",
        "email": "",
        "hours": "Lundi - Vendredi: 8h - 18h",
        "services_raw": "",
        "coverage_zones": "",
        "coverage_radius": "",
        "primary_color": None,
        "accent_color": None,
        "style": "modern",
        "has_photos": False,
        "features": [],
        "launch_date": "",
        "domain": "",
        "notes": "",
    }

    # Normalize text
    text = email_text.strip()

    # Try different parsing strategies

    # Strategy 1: Key: Value format (common in email notifications)
    lines = text.split('\n')
    current_key = None
    current_value_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this line is a field label
        # Pattern: "Field Name:" or "Field Name :" or "* Field Name:"
        label_match = re.match(r'^[\*\-]?\s*([^:]+?)\s*:\s*(.*)$', line)

        if label_match:
            # Save previous field if exists
            if current_key:
                _save_field(parsed, current_key, '\n'.join(current_value_lines))

            label = label_match.group(1).strip().lower()
            value = label_match.group(2).strip()

            # Find matching config key
            current_key = None
            for field_pattern, config_key in FIELD_MAPPING.items():
                if field_pattern in label:
                    current_key = config_key
                    break

            current_value_lines = [value] if value else []
        else:
            # Continuation of previous value
            if current_key:
                current_value_lines.append(line)

    # Save last field
    if current_key:
        _save_field(parsed, current_key, '\n'.join(current_value_lines))

    # Post-processing
    parsed = _post_process(parsed)

    return parsed


def _save_field(parsed: Dict, key: str, value: str):
    """Save a field value with appropriate type conversion."""
    value = value.strip()

    if not value or value.lower() in ['n/a', 'non renseigné', '-', 'aucun']:
        return

    if key == "trade_type":
        # Convert French trade name to key
        parsed[key] = get_trade_key(value)
    elif key == "primary_color" or key == "accent_color":
        # Convert color name to HSL
        parsed[key] = _parse_color(value)
    elif key == "style":
        # Convert style name
        parsed[key] = STYLE_MAP.get(value.lower(), "modern")
    elif key == "has_photos":
        parsed[key] = value.lower() in ['oui', 'yes', 'true', '1']
    elif key == "features":
        # Parse checkboxes/multi-select
        parsed[key] = _parse_features(value)
    elif key == "phone":
        # Normalize phone number
        parsed[key] = _normalize_phone(value)
    else:
        parsed[key] = value


def _parse_color(color_str: str) -> Optional[Dict[str, int]]:
    """Parse color string to HSL dict."""
    color_str = color_str.lower().strip()

    # Direct match
    if color_str in COLOR_MAP:
        return COLOR_MAP[color_str]

    # Partial match
    for name, hsl in COLOR_MAP.items():
        if name in color_str or color_str in name:
            return hsl

    # Try to parse hex color
    hex_match = re.search(r'#([0-9a-fA-F]{6})', color_str)
    if hex_match:
        return _hex_to_hsl(hex_match.group(1))

    return None


def _hex_to_hsl(hex_color: str) -> Dict[str, int]:
    """Convert hex color to HSL."""
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2

    if max_c == min_c:
        h = s = 0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)

        if max_c == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6

    return {
        "h": round(h * 360),
        "s": round(s * 100),
        "l": round(l * 100)
    }


def _parse_features(features_str: str) -> List[str]:
    """Parse feature checkboxes."""
    features = []

    # Split by common separators
    parts = re.split(r'[,;\n]', features_str)

    feature_map = {
        "réservation": "booking",
        "reservation": "booking",
        "booking": "booking",
        "formulaire": "contactForm",
        "contact": "contactForm",
        "galerie": "gallery",
        "gallery": "gallery",
        "photos": "gallery",
        "devis": "quoteRequest",
        "quote": "quoteRequest",
        "urgence": "emergencyBanner",
        "emergency": "emergencyBanner",
        "24/7": "emergencyBanner",
        "avis": "googleReviews",
        "reviews": "googleReviews",
        "google": "googleReviews",
    }

    for part in parts:
        part = part.strip().lower()
        for keyword, feature in feature_map.items():
            if keyword in part and feature not in features:
                features.append(feature)

    return features


def _normalize_phone(phone: str) -> str:
    """Normalize phone number to international format."""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    # Handle French numbers
    if digits.startswith('0') and len(digits) == 10:
        digits = '33' + digits[1:]
    elif digits.startswith('33') and len(digits) == 11:
        pass  # Already correct
    elif len(digits) == 9:
        digits = '33' + digits

    return '+' + digits if digits else phone


def _format_phone_display(phone: str) -> str:
    """Format phone for display."""
    # Remove +33 and format as 06 XX XX XX XX
    digits = re.sub(r'\D', '', phone)

    if digits.startswith('33'):
        digits = '0' + digits[2:]

    if len(digits) == 10:
        return ' '.join([digits[i:i+2] for i in range(0, 10, 2)])

    return phone


def _post_process(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Post-process parsed data."""

    # Apply trade defaults for colors if not specified
    trade_type = parsed.get("trade_type", "plumber")
    trade_colors = get_trade_colors(trade_type)

    if not parsed.get("primary_color"):
        parsed["primary_color"] = trade_colors.get("primary", {"h": 220, "s": 60, "l": 20})

    if not parsed.get("accent_color"):
        parsed["accent_color"] = trade_colors.get("accent", {"h": 25, "s": 85, "l": 50})

    # Generate phone display format
    if parsed.get("phone"):
        parsed["phone_display"] = _format_phone_display(parsed["phone"])
    else:
        parsed["phone_display"] = ""

    # Default features if none specified
    if not parsed.get("features"):
        parsed["features"] = ["booking", "contactForm", "quoteRequest", "emergencyBanner"]

    # Generate full address
    street = parsed.get("street", "")
    postal = parsed.get("postal_code", "")
    city = parsed.get("city", "")
    parsed["full_address"] = f"{street}, {postal} {city}, France".strip(", ")

    # Generate default slogan if not provided
    if not parsed.get("slogan"):
        trade_name = TRADE_DISPLAY_NAMES.get(trade_type, "Artisan")
        parsed["slogan"] = f"Votre expert en {trade_name.lower()}"

    # Generate default description if not provided
    if not parsed.get("description"):
        trade_name = TRADE_DISPLAY_NAMES.get(trade_type, "artisanat")
        city = parsed.get("city", "votre région")
        parsed["description"] = f"Spécialiste en {trade_name.lower()} à {city}. Service professionnel et interventions rapides."

    return parsed


def extract_from_sample_email():
    """Sample email content for testing."""
    sample = """
    Nouvelle réponse au formulaire: 🎨 Personnalisation de Votre Site Web

    Nom de l'entreprise: Martin Plomberie
    Type de métier / activité: Plombier
    Slogan ou phrase d'accroche: La qualité au service de votre confort
    Description courte de votre activité: Plombier professionnel depuis 10 ans, nous intervenons pour tous vos travaux de plomberie, chauffage et sanitaire.
    Adresse complète: 15 rue des Artisans
    Code postal: 75015
    Ville: Paris
    Téléphone: 06 12 34 56 78
    Horaires d'ouverture: Lundi - Samedi: 7h - 20h
    Liste de vos services: Dépannage urgent
    Réparation fuite
    Installation sanitaire
    Chauffage
    Couleur principale souhaitée: Bleu marine
    Couleur secondaire: Orange
    Style du site: Moderne
    Fonctionnalités souhaitées: Réservation en ligne, Formulaire de contact, Urgences 24/7
    Nom de domaine souhaité: martin-plomberie.fr
    """
    return parse_email_content(sample)


if __name__ == "__main__":
    # Test the parser
    result = extract_from_sample_email()
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
