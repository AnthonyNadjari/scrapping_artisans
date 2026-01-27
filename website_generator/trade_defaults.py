"""
Trade-specific defaults for artisan websites.
Python version of the TypeScript trade-defaults.ts
"""

from typing import Dict, List, TypedDict

class ServiceDict(TypedDict):
    icon: str
    title: str
    description: str
    features: List[str]

class ColorDict(TypedDict):
    h: int
    s: int
    l: int

class TradeDefaultsDict(TypedDict):
    icon: str
    services: List[ServiceDict]
    defaultColors: Dict[str, ColorDict]

# Map French trade names to English keys
TRADE_NAME_MAP = {
    "plombier": "plumber",
    "plomberie": "plumber",
    "electricien": "electrician",
    "électricien": "electrician",
    "electricite": "electrician",
    "électricité": "electrician",
    "couvreur": "roofer",
    "toiture": "roofer",
    "peintre": "painter",
    "peinture": "painter",
    "chauffagiste": "hvac",
    "climatisation": "hvac",
    "menuisier": "carpenter",
    "menuiserie": "carpenter",
    "macon": "mason",
    "maçon": "mason",
    "maconnerie": "mason",
    "maçonnerie": "mason",
    "serrurier": "locksmith",
    "serrurerie": "locksmith",
}

# French display names
TRADE_DISPLAY_NAMES = {
    "plumber": "Plomberie",
    "electrician": "Électricité",
    "roofer": "Couverture",
    "painter": "Peinture",
    "hvac": "Chauffage & Climatisation",
    "carpenter": "Menuiserie",
    "mason": "Maçonnerie",
    "locksmith": "Serrurerie",
}

TRADE_DEFAULTS: Dict[str, TradeDefaultsDict] = {
    "plumber": {
        "icon": "Wrench",
        "services": [
            {
                "icon": "AlertTriangle",
                "title": "Dépannage d'urgence",
                "description": "Intervention rapide 24h/24 et 7j/7 pour tous vos problèmes de plomberie urgents.",
                "features": ["Fuites d'eau", "Canalisations bouchées", "Chauffe-eau en panne", "Dégâts des eaux"]
            },
            {
                "icon": "Droplets",
                "title": "Recherche de fuite",
                "description": "Détection précise des fuites cachées avec équipement professionnel.",
                "features": ["Détection acoustique", "Caméra thermique", "Test de pression", "Rapport détaillé"]
            },
            {
                "icon": "Wrench",
                "title": "Installation sanitaire",
                "description": "Installation complète de vos équipements sanitaires par des experts.",
                "features": ["Salle de bain", "WC et lavabos", "Douche italienne", "Baignoire balnéo"]
            },
            {
                "icon": "Flame",
                "title": "Chauffage & Chaudière",
                "description": "Installation, entretien et dépannage de tous types de systèmes de chauffage.",
                "features": ["Chaudière gaz/fioul", "Pompe à chaleur", "Plancher chauffant", "Radiateurs"]
            },
            {
                "icon": "Home",
                "title": "Rénovation plomberie",
                "description": "Rénovation complète de votre installation de plomberie.",
                "features": ["Remplacement tuyauterie", "Mise aux normes", "Création salle d'eau", "Optimisation"]
            },
            {
                "icon": "Sparkles",
                "title": "Débouchage",
                "description": "Débouchage professionnel de toutes vos canalisations.",
                "features": ["Évier et lavabo", "WC et douche", "Colonne d'immeuble", "Hydrocurage"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 220, "s": 60, "l": 20},
            "accent": {"h": 25, "s": 85, "l": 50}
        }
    },
    "electrician": {
        "icon": "Zap",
        "services": [
            {
                "icon": "AlertTriangle",
                "title": "Dépannage électrique",
                "description": "Intervention rapide pour tous vos problèmes électriques urgents.",
                "features": ["Panne de courant", "Court-circuit", "Disjoncteur", "Urgence 24/7"]
            },
            {
                "icon": "Zap",
                "title": "Installation électrique",
                "description": "Installation complète et mise aux normes de votre réseau électrique.",
                "features": ["Tableau électrique", "Prises et interrupteurs", "Mise à la terre", "Certification"]
            },
            {
                "icon": "Lightbulb",
                "title": "Éclairage",
                "description": "Installation et dépannage de tous types d'éclairages.",
                "features": ["LED", "Spots encastrés", "Éclairage extérieur", "Domotique"]
            },
            {
                "icon": "Home",
                "title": "Rénovation électrique",
                "description": "Rénovation complète de votre installation électrique.",
                "features": ["Mise aux normes NF C 15-100", "Remplacement câblage", "Extension réseau", "Diagnostic"]
            },
            {
                "icon": "Shield",
                "title": "Sécurité électrique",
                "description": "Installation de systèmes de sécurité et protection.",
                "features": ["Alarme", "Vidéosurveillance", "Interphone", "Contrôle d'accès"]
            },
            {
                "icon": "Smartphone",
                "title": "Domotique",
                "description": "Automatisation et contrôle intelligent de votre habitat.",
                "features": ["Maison connectée", "Volets roulants", "Thermostat intelligent", "Commande vocale"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 45, "s": 80, "l": 45},
            "accent": {"h": 210, "s": 70, "l": 45}
        }
    },
    "roofer": {
        "icon": "Home",
        "services": [
            {
                "icon": "AlertTriangle",
                "title": "Réparation urgente",
                "description": "Intervention rapide pour fuites et dégâts sur toiture.",
                "features": ["Fuite de toit", "Tuiles cassées", "Infiltration", "Bâchage urgence"]
            },
            {
                "icon": "Home",
                "title": "Réfection toiture",
                "description": "Rénovation complète ou partielle de votre couverture.",
                "features": ["Tuiles", "Ardoises", "Zinc", "Toit terrasse"]
            },
            {
                "icon": "Droplets",
                "title": "Étanchéité",
                "description": "Travaux d'étanchéité pour protéger votre habitat.",
                "features": ["Toiture terrasse", "Balcon", "Membrane", "Garantie décennale"]
            },
            {
                "icon": "Wind",
                "title": "Isolation toiture",
                "description": "Isolation thermique performante de votre toiture.",
                "features": ["Combles perdus", "Combles aménagés", "Sarking", "Aides financières"]
            },
            {
                "icon": "Wrench",
                "title": "Zinguerie",
                "description": "Travaux de zinguerie et évacuation des eaux.",
                "features": ["Gouttières", "Chéneaux", "Descentes", "Habillage"]
            },
            {
                "icon": "Sun",
                "title": "Velux & Fenêtres de toit",
                "description": "Installation et remplacement de fenêtres de toit.",
                "features": ["Pose Velux", "Remplacement", "Store", "Volet roulant"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 15, "s": 60, "l": 35},
            "accent": {"h": 35, "s": 75, "l": 50}
        }
    },
    "painter": {
        "icon": "Paintbrush",
        "services": [
            {
                "icon": "Paintbrush",
                "title": "Peinture intérieure",
                "description": "Peinture complète de vos espaces intérieurs.",
                "features": ["Murs et plafonds", "Boiseries", "Peinture décorative", "Laque"]
            },
            {
                "icon": "Home",
                "title": "Peinture extérieure",
                "description": "Ravalement et peinture de façades.",
                "features": ["Façade", "Volets", "Portail", "Protection"]
            },
            {
                "icon": "Layers",
                "title": "Papier peint",
                "description": "Pose de papiers peints et revêtements muraux.",
                "features": ["Papier classique", "Vinyle", "Intissé", "Panoramique"]
            },
            {
                "icon": "Sparkles",
                "title": "Décoration",
                "description": "Techniques décoratives et finitions personnalisées.",
                "features": ["Enduit décoratif", "Effet béton", "Stuc", "Patine"]
            },
            {
                "icon": "Wrench",
                "title": "Préparation surfaces",
                "description": "Préparation complète avant mise en peinture.",
                "features": ["Lessivage", "Ponçage", "Enduit", "Impression"]
            },
            {
                "icon": "Shield",
                "title": "Traitement",
                "description": "Traitements spéciaux et protections.",
                "features": ["Anti-humidité", "Antifongique", "Isolation", "Imperméabilisant"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 200, "s": 40, "l": 30},
            "accent": {"h": 340, "s": 65, "l": 55}
        }
    },
    "hvac": {
        "icon": "Thermometer",
        "services": [
            {
                "icon": "Flame",
                "title": "Chauffage",
                "description": "Installation et entretien de systèmes de chauffage.",
                "features": ["Chaudière", "Pompe à chaleur", "Poêle", "Radiateurs"]
            },
            {
                "icon": "Wind",
                "title": "Climatisation",
                "description": "Installation et maintenance de climatisation.",
                "features": ["Split", "Gainable", "Réversible", "Multi-split"]
            },
            {
                "icon": "Wrench",
                "title": "Entretien annuel",
                "description": "Contrats d'entretien pour votre tranquillité.",
                "features": ["Chaudière gaz", "PAC", "Climatisation", "Attestation"]
            },
            {
                "icon": "AlertTriangle",
                "title": "Dépannage",
                "description": "Intervention rapide en cas de panne.",
                "features": ["Chauffage en panne", "Clim HS", "Urgence", "Diagnostic"]
            },
            {
                "icon": "Leaf",
                "title": "Énergies renouvelables",
                "description": "Solutions écologiques pour votre confort.",
                "features": ["Pompe à chaleur", "Solaire thermique", "Chaudière biomasse", "Aides"]
            },
            {
                "icon": "Home",
                "title": "Ventilation",
                "description": "Installation de systèmes de ventilation.",
                "features": ["VMC simple flux", "VMC double flux", "Extracteur", "Purification"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 200, "s": 65, "l": 40},
            "accent": {"h": 15, "s": 80, "l": 50}
        }
    },
    "carpenter": {
        "icon": "Hammer",
        "services": [
            {
                "icon": "DoorOpen",
                "title": "Portes & Fenêtres",
                "description": "Fabrication et pose de menuiseries.",
                "features": ["Portes intérieures", "Portes extérieures", "Fenêtres bois", "Volets"]
            },
            {
                "icon": "Layers",
                "title": "Placards & Rangements",
                "description": "Création de solutions de rangement sur mesure.",
                "features": ["Dressing", "Placard", "Bibliothèque", "Aménagement"]
            },
            {
                "icon": "Sofa",
                "title": "Mobilier sur mesure",
                "description": "Fabrication de meubles personnalisés.",
                "features": ["Table", "Meuble TV", "Bureau", "Tête de lit"]
            },
            {
                "icon": "Home",
                "title": "Agencement intérieur",
                "description": "Aménagement complet de vos espaces.",
                "features": ["Cuisine", "Salle de bain", "Commerce", "Bureau"]
            },
            {
                "icon": "Wrench",
                "title": "Réparation",
                "description": "Réparation et restauration de menuiseries.",
                "features": ["Porte qui grince", "Fenêtre bloquée", "Tiroir cassé", "Restauration"]
            },
            {
                "icon": "TreeDeciduous",
                "title": "Terrasse bois",
                "description": "Construction de terrasses et aménagements extérieurs.",
                "features": ["Terrasse", "Pergola", "Clôture", "Bardage"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 30, "s": 50, "l": 30},
            "accent": {"h": 35, "s": 70, "l": 45}
        }
    },
    "mason": {
        "icon": "Landmark",
        "services": [
            {
                "icon": "Home",
                "title": "Construction",
                "description": "Construction de bâtiments et extensions.",
                "features": ["Maison individuelle", "Extension", "Garage", "Dépendances"]
            },
            {
                "icon": "Wrench",
                "title": "Rénovation",
                "description": "Rénovation complète de votre habitat.",
                "features": ["Gros œuvre", "Ouverture mur", "Reprise fondation", "Consolidation"]
            },
            {
                "icon": "Layers",
                "title": "Façade",
                "description": "Travaux de façade et ravalement.",
                "features": ["Ravalement", "Enduit", "Crépi", "Isolation extérieure"]
            },
            {
                "icon": "Square",
                "title": "Dalles & Chapes",
                "description": "Réalisation de dalles et chapes.",
                "features": ["Dalle béton", "Chape", "Terrasse", "Allée"]
            },
            {
                "icon": "Fence",
                "title": "Clôtures & Murets",
                "description": "Construction de clôtures et murets.",
                "features": ["Mur de clôture", "Muret", "Piliers", "Portail"]
            },
            {
                "icon": "Droplets",
                "title": "Assainissement",
                "description": "Travaux d'assainissement et drainage.",
                "features": ["Fosse septique", "Drainage", "Cuvelage", "Étanchéité"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 25, "s": 30, "l": 35},
            "accent": {"h": 200, "s": 50, "l": 45}
        }
    },
    "locksmith": {
        "icon": "Key",
        "services": [
            {
                "icon": "AlertTriangle",
                "title": "Ouverture de porte",
                "description": "Ouverture de porte en urgence 24h/24.",
                "features": ["Porte claquée", "Clé perdue", "Clé cassée", "Sans dégât"]
            },
            {
                "icon": "Lock",
                "title": "Changement de serrure",
                "description": "Remplacement de serrures toutes marques.",
                "features": ["Serrure 3 points", "Cylindre", "Blindage", "Haute sécurité"]
            },
            {
                "icon": "Shield",
                "title": "Blindage de porte",
                "description": "Renforcement et blindage de vos portes.",
                "features": ["Porte blindée", "Blindage sur existant", "Certifié A2P", "Garantie"]
            },
            {
                "icon": "Key",
                "title": "Reproduction de clés",
                "description": "Copie de clés de toutes marques.",
                "features": ["Clé plate", "Clé sécurisée", "Badge", "Télécommande"]
            },
            {
                "icon": "Home",
                "title": "Sécurité habitat",
                "description": "Installation de systèmes de sécurité.",
                "features": ["Verrou", "Judas", "Entrebâilleur", "Alarme"]
            },
            {
                "icon": "Wrench",
                "title": "Dépannage serrurerie",
                "description": "Réparation de serrures et fermetures.",
                "features": ["Serrure bloquée", "Gonds", "Ferme-porte", "Entretien"]
            }
        ],
        "defaultColors": {
            "primary": {"h": 210, "s": 50, "l": 25},
            "accent": {"h": 45, "s": 85, "l": 50}
        }
    }
}


def get_trade_key(trade_name: str) -> str:
    """Convert French trade name to English key."""
    normalized = trade_name.lower().strip()
    return TRADE_NAME_MAP.get(normalized, "plumber")


def get_trade_services(trade_type: str) -> List[ServiceDict]:
    """Get services for a specific trade type."""
    return TRADE_DEFAULTS.get(trade_type, TRADE_DEFAULTS["plumber"])["services"]


def get_trade_icon(trade_type: str) -> str:
    """Get icon name for a specific trade type."""
    return TRADE_DEFAULTS.get(trade_type, TRADE_DEFAULTS["plumber"])["icon"]


def get_trade_colors(trade_type: str) -> Dict[str, ColorDict]:
    """Get default colors for a specific trade type."""
    return TRADE_DEFAULTS.get(trade_type, TRADE_DEFAULTS["plumber"])["defaultColors"]


def get_trade_display_name(trade_type: str) -> str:
    """Get French display name for a trade type."""
    return TRADE_DISPLAY_NAMES.get(trade_type, "Artisan")
