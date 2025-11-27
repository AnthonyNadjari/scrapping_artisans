"""
Modèles de base de données SQLite - Version WhatsApp simplifiée
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.whatsapp_settings import DB_PATH

def init_database():
    """Initialise la base de données avec toutes les tables"""
    
    # Créer le dossier si nécessaire
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table artisans (avec données SIRENE)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artisans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Données SIRENE
            siret TEXT,
            nom_entreprise TEXT,
            nom TEXT,
            prenom TEXT,
            code_naf TEXT,
            type_artisan TEXT,
            
            -- Localisation
            adresse TEXT,
            code_postal TEXT,
            ville TEXT,
            departement TEXT,
            
            -- Contact (enrichi)
            telephone TEXT UNIQUE,
            telephone_formate TEXT,
            source_telephone TEXT,  -- 'pages_blanches', '118712', 'google_maps', etc.
            site_web TEXT,  -- URL du site web (si disponible)
            
            -- WhatsApp
            a_whatsapp BOOLEAN DEFAULT NULL,
            date_verification_whatsapp DATETIME,
            
            -- Campagne
            message_envoye BOOLEAN DEFAULT 0,
            date_envoi DATETIME,
            
            a_repondu BOOLEAN DEFAULT 0,
            date_reponse DATETIME,
            derniere_reponse TEXT,
            
            -- Statut réponse
            statut_reponse TEXT,  -- 'acceptation', 'off', 'en_cours', 'a_relancer', NULL
            commentaire TEXT,
            
            -- Meta
            source TEXT,  -- 'sirene', 'google_maps', 'pages_jaunes'
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table messages_log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artisan_id INTEGER,
            date_envoi DATETIME,
            message_id TEXT,
            statut TEXT,
            erreur TEXT,
            FOREIGN KEY (artisan_id) REFERENCES artisans(id)
        )
    """)
    
    # Table reponses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reponses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artisan_id INTEGER,
            date_reception DATETIME,
            contenu TEXT,
            message_id TEXT,
            FOREIGN KEY (artisan_id) REFERENCES artisans(id)
        )
    """)
    
    # Ajouter les nouvelles colonnes si elles n'existent pas (migration)
    nouvelles_colonnes = [
        ("siret", "TEXT"),
        ("nom", "TEXT"),
        ("prenom", "TEXT"),
        ("code_naf", "TEXT"),
        ("adresse", "TEXT"),
        ("code_postal", "TEXT"),
        ("source_telephone", "TEXT"),
        ("statut_reponse", "TEXT"),
        ("commentaire", "TEXT"),
        ("site_web", "TEXT"),
        ("note", "REAL"),  # Note Google Maps (0-5)
        ("nombre_avis", "INTEGER"),  # Nombre d'avis Google Maps
        ("ville_recherche", "TEXT")  # Ville utilisée pour la recherche
    ]
    
    for colonne, type_col in nouvelles_colonnes:
        try:
            cursor.execute(f"ALTER TABLE artisans ADD COLUMN {colonne} {type_col}")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
    
    # Index pour performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telephone ON artisans(telephone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_departement ON artisans(departement)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_artisan ON artisans(type_artisan)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_siret ON artisans(siret)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_a_whatsapp ON artisans(a_whatsapp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_envoye ON artisans(message_envoye)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_a_repondu ON artisans(a_repondu)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_statut_reponse ON artisans(statut_reponse)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_telephone ON artisans(source_telephone)")
    
    conn.commit()
    conn.close()
    
    print(f"Base de donnees initialisee : {DB_PATH}")

def get_connection():
    """Retourne une connexion à la base de données"""
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_database()

