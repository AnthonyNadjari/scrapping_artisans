"""
Config Generator for artisan websites.

Generates TypeScript artisan.config.ts files from parsed form data.
"""

import json
from typing import Dict, Any, List
from .trade_defaults import get_trade_services, get_trade_icon, TRADE_DISPLAY_NAMES


def generate_config(parsed_data: Dict[str, Any]) -> str:
    """
    Generate TypeScript config file content from parsed form data.

    Args:
        parsed_data: Dictionary from parser.parse_email_content()

    Returns:
        TypeScript file content as string
    """
    trade_type = parsed_data.get("trade_type", "plumber")

    # Build config object
    config = {
        "business": {
            "name": parsed_data.get("business_name", "Mon Entreprise"),
            "tradeType": trade_type,
            "slogan": parsed_data.get("slogan", ""),
            "description": parsed_data.get("description", ""),
        },
        "contact": {
            "phone": parsed_data.get("phone", ""),
            "phoneDisplay": parsed_data.get("phone_display", ""),
            "email": parsed_data.get("email", f"contact@{_slugify(parsed_data.get('business_name', 'entreprise'))}.fr"),
        },
        "address": {
            "street": parsed_data.get("street", ""),
            "postalCode": parsed_data.get("postal_code", ""),
            "city": parsed_data.get("city", ""),
            "full": parsed_data.get("full_address", ""),
            "coordinates": _get_coordinates(parsed_data),
        },
        "hours": {
            "regular": parsed_data.get("hours", "Lundi - Vendredi: 8h - 18h"),
            "emergency": "Urgences: 24h/24, 7j/7" if "emergencyBanner" in parsed_data.get("features", []) else "",
        },
        "services": _get_services(parsed_data),
        "stats": {
            "experience": "+10 Ans",
            "availability": "24/7" if "emergencyBanner" in parsed_data.get("features", []) else "7j/7",
            "satisfaction": "100%",
            "clients": "+200",
        },
        "branding": {
            "primaryColor": parsed_data.get("primary_color", {"h": 220, "s": 60, "l": 20}),
            "accentColor": parsed_data.get("accent_color", {"h": 25, "s": 85, "l": 50}),
            "style": parsed_data.get("style", "modern"),
            "logoIcon": get_trade_icon(trade_type),
        },
        "features": {
            "booking": "booking" in parsed_data.get("features", []),
            "contactForm": "contactForm" in parsed_data.get("features", []),
            "gallery": "gallery" in parsed_data.get("features", []),
            "quoteRequest": "quoteRequest" in parsed_data.get("features", []),
            "emergencyBanner": "emergencyBanner" in parsed_data.get("features", []),
            "googleReviews": "googleReviews" in parsed_data.get("features", []),
        },
        "reviews": {
            "manual": _generate_sample_reviews(parsed_data),
            "stats": {
                "averageRating": 4.9,
                "totalReviews": 45,
            },
            "googleWidget": {
                "enabled": False,
                "widgetId": "",
                "placeId": "",
            },
        },
        "seo": {
            "title": _generate_seo_title(parsed_data),
            "description": _generate_seo_description(parsed_data),
            "keywords": _generate_keywords(parsed_data),
        },
        "assets": {
            "favicon": "/favicon.svg",
            "heroImage": f"/hero-{trade_type}.jpg",
            "serviceImages": [
                "/assets/service-1.jpg",
                "/assets/service-2.jpg",
            ],
        },
    }

    # Generate TypeScript file
    return _format_typescript(config)


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def _get_coordinates(parsed_data: Dict) -> Dict[str, float]:
    """Get coordinates for address (default to city center or Paris)."""
    # TODO: Implement geocoding with Google Maps API or similar
    # For now, return Paris coordinates as default
    city = parsed_data.get("city", "").lower()

    # Common French cities
    city_coords = {
        "paris": {"lat": 48.8566, "lng": 2.3522},
        "lyon": {"lat": 45.7640, "lng": 4.8357},
        "marseille": {"lat": 43.2965, "lng": 5.3698},
        "toulouse": {"lat": 43.6047, "lng": 1.4442},
        "nice": {"lat": 43.7102, "lng": 7.2620},
        "nantes": {"lat": 47.2184, "lng": -1.5536},
        "strasbourg": {"lat": 48.5734, "lng": 7.7521},
        "montpellier": {"lat": 43.6108, "lng": 3.8767},
        "bordeaux": {"lat": 44.8378, "lng": -0.5792},
        "lille": {"lat": 50.6292, "lng": 3.0573},
    }

    for city_name, coords in city_coords.items():
        if city_name in city:
            return coords

    # Default to Paris
    return {"lat": 48.8566, "lng": 2.3522}


def _get_services(parsed_data: Dict) -> List[Dict]:
    """Get services list - custom or from trade defaults."""
    services_raw = parsed_data.get("services_raw", "")
    trade_type = parsed_data.get("trade_type", "plumber")

    if services_raw:
        # Parse custom services
        lines = [l.strip() for l in services_raw.split('\n') if l.strip()]
        if len(lines) >= 3:
            # Use custom services
            custom_services = []
            icons = ["Wrench", "AlertTriangle", "Home", "Shield", "Sparkles", "Zap"]

            for i, line in enumerate(lines[:6]):
                custom_services.append({
                    "icon": icons[i % len(icons)],
                    "title": line,
                    "description": f"Service professionnel de {line.lower()}.",
                    "features": ["Intervention rapide", "Devis gratuit", "Garantie"],
                })

            return custom_services

    # Use trade defaults
    return get_trade_services(trade_type)


def _generate_sample_reviews(parsed_data: Dict) -> List[Dict]:
    """Generate sample reviews for the business."""
    business_name = parsed_data.get("business_name", "l'entreprise")
    city = parsed_data.get("city", "la région")
    trade_type = parsed_data.get("trade_type", "plumber")
    trade_name = TRADE_DISPLAY_NAMES.get(trade_type, "artisan").lower()

    return [
        {
            "author": "Marie L.",
            "rating": 5,
            "text": f"Excellent service de {trade_name}. {business_name} est intervenu rapidement et a résolu notre problème efficacement. Je recommande vivement !",
            "location": city,
            "verified": True,
        },
        {
            "author": "Pierre M.",
            "rating": 5,
            "text": f"Très professionnel et ponctuel. Le travail a été fait dans les règles de l'art. Merci à {business_name} pour cette prestation de qualité.",
            "location": city,
            "verified": True,
        },
        {
            "author": "Sophie D.",
            "rating": 5,
            "text": f"Service impeccable du début à la fin. Prix transparent, travail soigné. {business_name} est maintenant notre {trade_name} attitré.",
            "location": city,
            "verified": True,
        },
    ]


def _generate_seo_title(parsed_data: Dict) -> str:
    """Generate SEO-optimized page title."""
    business_name = parsed_data.get("business_name", "")
    trade_type = parsed_data.get("trade_type", "plumber")
    trade_name = TRADE_DISPLAY_NAMES.get(trade_type, "Artisan")
    city = parsed_data.get("city", "")

    if city:
        return f"{business_name} - {trade_name} Professionnel {city} | Dépannage 24/7"
    return f"{business_name} - {trade_name} Professionnel | Dépannage 24/7"


def _generate_seo_description(parsed_data: Dict) -> str:
    """Generate SEO-optimized meta description."""
    business_name = parsed_data.get("business_name", "")
    trade_type = parsed_data.get("trade_type", "plumber")
    trade_name = TRADE_DISPLAY_NAMES.get(trade_type, "Artisan").lower()
    city = parsed_data.get("city", "")
    description = parsed_data.get("description", "")

    if description and len(description) > 50:
        # Truncate to ~150 chars for SEO
        return description[:150].rsplit(' ', 1)[0] + "..."

    location = f"à {city}" if city else "près de chez vous"
    return f"{business_name}, votre {trade_name} de confiance {location}. Interventions rapides, devis gratuit. Disponible 24h/24 pour les urgences."


def _generate_keywords(parsed_data: Dict) -> List[str]:
    """Generate SEO keywords."""
    trade_type = parsed_data.get("trade_type", "plumber")
    trade_name = TRADE_DISPLAY_NAMES.get(trade_type, "artisan").lower()
    city = parsed_data.get("city", "")

    keywords = [
        f"{trade_name} {city}".strip(),
        f"dépannage {trade_name}",
        f"{trade_name} urgence",
        f"{trade_name} professionnel",
    ]

    return [k for k in keywords if k]


def _format_typescript(config: Dict) -> str:
    """Format config dict as TypeScript file content."""

    def format_value(value, indent=2):
        """Format a value for TypeScript."""
        prefix = "  " * indent

        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Escape quotes and newlines
            escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            return f'"{escaped}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            if not value:
                return "[]"
            items = [format_value(v, indent + 1) for v in value]
            if all(isinstance(v, str) for v in value):
                return "[" + ", ".join(items) + "]"
            return "[\n" + ",\n".join(f"{prefix}  {item}" for item in items) + f"\n{prefix}]"
        elif isinstance(value, dict):
            lines = []
            for k, v in value.items():
                formatted_v = format_value(v, indent + 1)
                lines.append(f'{prefix}  {k}: {formatted_v}')
            return "{\n" + ",\n".join(lines) + f"\n{prefix}}}"
        else:
            return str(value)

    # Generate TypeScript content
    ts_content = '''// Main configuration file for the artisan website
// This file is the single source of truth for all customizable content
// Generated automatically from Google Form response

import type { ArtisanConfig } from "./types";
import { tradeDefaults } from "./trade-defaults";

export const config: ArtisanConfig = {
'''

    # Add each section
    sections = ["business", "contact", "address", "hours", "services", "stats", "branding", "features", "reviews", "seo", "assets"]

    for section in sections:
        if section in config:
            if section == "services":
                # Special handling for services - reference trade defaults or inline
                ts_content += f"  // Services offered\n"
                ts_content += f"  services: tradeDefaults.{config['business']['tradeType']}.services,\n\n"
            else:
                value = config[section]
                comment = {
                    "business": "Business identity",
                    "contact": "Contact information",
                    "address": "Location",
                    "hours": "Business hours",
                    "stats": "Statistics",
                    "branding": "Visual branding",
                    "features": "Feature toggles",
                    "reviews": "Reviews",
                    "seo": "SEO / Meta",
                    "assets": "Assets paths",
                }.get(section, section.capitalize())

                ts_content += f"  // {comment}\n"
                ts_content += f"  {section}: {format_value(value, 1)},\n\n"

    ts_content += '''};\n
// Export individual sections for backwards compatibility
export const siteConfig = {
  favicon: { path: config.assets.favicon },
  address: {
    street: config.address.street,
    city: `${config.address.postalCode} ${config.address.city}`,
    full: config.address.full,
    coordinates: config.address.coordinates,
  },
  contact: {
    phone: config.contact.phone,
    email: config.contact.email,
  },
};

export const reviewStats = config.reviews.stats;
export const manualReviews = config.reviews.manual;
export const googleReviewsConfig = config.reviews.googleWidget;

// Helper to get current trade defaults
export function getCurrentTradeDefaults() {
  return tradeDefaults[config.business.tradeType];
}
'''

    return ts_content


def generate_config_file(parsed_data: Dict[str, Any], output_path: str) -> str:
    """
    Generate and write config file.

    Args:
        parsed_data: Dictionary from parser
        output_path: Path to write the config file

    Returns:
        Path to the generated file
    """
    content = generate_config(parsed_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path


if __name__ == "__main__":
    # Test with sample data
    from .parser import extract_from_sample_email

    parsed = extract_from_sample_email()
    config_content = generate_config(parsed)
    print(config_content)
