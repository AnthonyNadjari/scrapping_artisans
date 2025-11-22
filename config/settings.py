"""
Configuration globale de l'application
"""
import os
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "artisans.db"
CONFIG_DIR = BASE_DIR / "config"

# Créer les dossiers si nécessaire
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Métiers d'artisans
METIERS = [
    # Plomberie & Chauffage
    "plombier", "chauffagiste", "plombier chauffagiste",
    "climatisation", "pompe à chaleur", "sanitaire",
    
    # Électricité
    "électricien", "électricien bâtiment", "électricité générale",
    "domotique", "installation électrique",
    
    # Maçonnerie & Gros œuvre
    "maçon", "maçonnerie", "maçon bâtiment", "gros œuvre",
    
    # Menuiserie & Charpente
    "menuisier", "menuiserie", "charpentier", "charpente",
    "ébéniste", "parqueteur", "agenceur", "menuisier poseur",
    
    # Peinture & Finitions
    "peintre", "peintre en bâtiment", "peinture décoration",
    "plâtrier", "plâtrerie", "staff",
    
    # Carrelage & Revêtements
    "carreleur", "carrelage", "faïencier", "mosaïste",
    "moquettiste", "pose de sol",
    
    # Couverture & Toiture
    "couvreur", "couverture", "zingueur", "étanchéité",
    "charpente couverture",
    
    # Isolation & Ravalement
    "isolation", "isolation thermique", "façadier",
    "ravalement", "ravalement de façade", "ITE",
    
    # Serrurerie & Métallerie
    "serrurier", "serrurerie", "métallier", "ferronnier",
    "métallerie", "serrurerie métallerie",
    
    # Vitrerie & Miroiterie
    "vitrier", "vitrerie", "miroitier", "miroiterie",
    
    # Jardins & Extérieurs
    "paysagiste", "jardinier", "paysagiste créateur",
    "élagueur", "élagage", "terrassement", "maçon paysagiste",
    "piscine", "arrosage automatique",
    
    # Autres spécialités
    "cuisiniste", "cuisine", "salle de bain",
    "aménagement intérieur", "placards",
]

# Départements prioritaires
DEPARTEMENTS_PRIORITAIRES = [
    "77",  # Seine-et-Marne
    "78",  # Yvelines  
    "91",  # Essonne
    "95",  # Val-d'Oise
    "60",  # Oise
    "89",  # Yonne
    "45",  # Loiret
    "28",  # Eure-et-Loir
]

# Configuration Gmail (à charger depuis .env)
GMAIL_CONFIG = {
    "email": os.getenv("GMAIL_EMAIL", ""),
    "app_password": os.getenv("GMAIL_APP_PASSWORD", ""),
    "display_name": "Sites Web Artisans",
}

# Limites d'envoi
EMAILS_PAR_JOUR = 50
DELAI_ENTRE_EMAILS = 30  # secondes

# API Geo France
GEO_API_BASE = "https://geo.api.gouv.fr"

# API SIRENE
SIRENE_API_BASE = "https://api.insee.fr/entreprises/sirene/V3"

