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
    
    # Table artisans (ultra-simple)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artisans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Identité minimale
            nom_entreprise TEXT,
            type_artisan TEXT,
            
            -- Localisation
            ville TEXT,
            departement TEXT,
            
            -- Contact (CLÉ PRINCIPALE)
            telephone TEXT UNIQUE NOT NULL,
            telephone_formate TEXT,
            
            -- WhatsApp
            a_whatsapp BOOLEAN DEFAULT NULL,
            date_verification_whatsapp DATETIME,
            
            -- Campagne
            message_envoye BOOLEAN DEFAULT 0,
            date_envoi DATETIME,
            
            a_repondu BOOLEAN DEFAULT 0,
            date_reponse DATETIME,
            derniere_reponse TEXT,
            
            -- Meta
            source TEXT,
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
    
    # Index pour performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telephone ON artisans(telephone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_a_whatsapp ON artisans(a_whatsapp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_envoye ON artisans(message_envoye)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_a_repondu ON artisans(a_repondu)")
    
    conn.commit()
    conn.close()
    
    print(f"Base de donnees initialisee : {DB_PATH}")

def get_connection():
    """Retourne une connexion à la base de données"""
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_database()

