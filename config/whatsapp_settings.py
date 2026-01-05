"""
Configuration système de prospection WhatsApp (liens wa.me)
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Créer les dossiers
DATA_DIR.mkdir(exist_ok=True)

# Chemin base de données
DB_PATH = DATA_DIR / "whatsapp_artisans.db"

# Métiers d'artisans (même liste que le système email)
METIERS = [
    "plombier", "chauffagiste", "plombier chauffagiste",
    "climatisation", "pompe à chaleur", "sanitaire",
    "électricien", "électricien bâtiment", "électricité générale",
    "domotique", "installation électrique",
    "maçon", "maçonnerie", "maçon bâtiment", "gros œuvre",
    "menuisier", "menuiserie", "charpentier", "charpente",
    "ébéniste", "parqueteur", "agenceur", "menuisier poseur",
    "peintre", "peintre en bâtiment", "peinture décoration",
    "plâtrier", "plâtrerie", "staff",
    "carreleur", "carrelage", "faïencier", "mosaïste",
    "moquettiste", "pose de sol",
    "couvreur", "couverture", "zingueur", "étanchéité",
    "charpente couverture",
    "isolation", "isolation thermique", "façadier",
    "ravalement", "ravalement de façade", "ITE",
    "serrurier", "serrurerie", "métallier", "ferronnier",
    "métallerie", "serrurerie métallerie",
    "vitrier", "vitrerie", "miroitier", "miroiterie",
    "paysagiste", "jardinier", "paysagiste créateur",
    "élagueur", "élagage", "terrassement", "maçon paysagiste",
    "piscine", "arrosage automatique",
    "cuisiniste", "cuisine", "salle de bain",
    "aménagement intérieur", "placards",
    # Métiers supplémentaires
    "chauffeur livreur", "livreur", "transporteur",
    "nettoyage", "nettoyage professionnel", "nettoyage industriel",
    "déménageur", "déménagement",
    "photographe", "photographe professionnel",
    "coiffeur", "coiffeur à domicile", "salon de coiffure",
    "mécanicien", "mécanicien auto", "garagiste",
    "plombier zingueur", "plombier sanitaire",
]

# Départements prioritaires
DEPARTEMENTS_PRIORITAIRES = [
    "77", "78", "91", "95", "60", "89", "45", "28"
]

