"""
Modèles de base de données SQLite
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from config.settings import DB_PATH

def init_database():
    """Initialise la base de données avec toutes les tables"""
    
    # Créer le dossier si nécessaire
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table artisans
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artisans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Identité
            nom_entreprise TEXT,
            prenom TEXT,
            nom TEXT,
            
            -- Activité
            type_artisan TEXT,
            metiers_secondaires TEXT,
            
            -- Localisation
            adresse TEXT,
            code_postal TEXT,
            ville TEXT,
            departement TEXT,
            latitude REAL,
            longitude REAL,
            
            -- Contact
            telephone TEXT,
            telephone_mobile TEXT,
            email TEXT,
            site_web TEXT,
            
            -- Présence en ligne
            lien_google_maps TEXT,
            avis_google_note REAL,
            avis_google_count INTEGER,
            a_site_web BOOLEAN DEFAULT 0,
            
            -- Données entreprise
            siret TEXT,
            forme_juridique TEXT,
            date_creation DATE,
            
            -- Métadonnées scraping
            source TEXT,
            date_scrape DATETIME,
            derniere_mise_a_jour DATETIME,
            
            -- Statut prospection
            statut TEXT DEFAULT 'non_contacte',
            priorite INTEGER DEFAULT 0,
            note_personnelle TEXT,
            
            -- Tracking email
            email_envoye BOOLEAN DEFAULT 0,
            date_envoi DATETIME,
            template_utilise TEXT,
            
            email_ouvert BOOLEAN DEFAULT 0,
            date_premiere_ouverture DATETIME,
            nombre_ouvertures INTEGER DEFAULT 0,
            date_derniere_ouverture DATETIME,
            
            a_repondu BOOLEAN DEFAULT 0,
            date_reponse DATETIME,
            
            -- Timestamps
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table emails_log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artisan_id INTEGER,
            date_envoi DATETIME,
            objet TEXT,
            contenu TEXT,
            statut TEXT,
            erreur TEXT,
            message_id TEXT,
            FOREIGN KEY (artisan_id) REFERENCES artisans(id)
        )
    """)
    
    # Table reponses_emails
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reponses_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artisan_id INTEGER,
            date_reponse DATETIME,
            sujet TEXT,
            contenu TEXT,
            sentiment TEXT,
            FOREIGN KEY (artisan_id) REFERENCES artisans(id)
        )
    """)
    
    # Table tracking_pixels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracking_pixels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artisan_id INTEGER,
            tracking_id TEXT UNIQUE,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            ouvert BOOLEAN DEFAULT 0,
            date_ouverture DATETIME,
            FOREIGN KEY (artisan_id) REFERENCES artisans(id)
        )
    """)
    
    # Table campagnes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campagnes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'active',
            total_cibles INTEGER,
            envoyes INTEGER DEFAULT 0,
            ouverts INTEGER DEFAULT 0,
            reponses INTEGER DEFAULT 0,
            emails_par_jour INTEGER DEFAULT 20
        )
    """)
    
    # Index pour performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ville ON artisans(ville)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_departement ON artisans(departement)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_artisan ON artisans(type_artisan)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_statut ON artisans(statut)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_envoye ON artisans(email_envoye)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telephone ON artisans(telephone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON artisans(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracking_id ON tracking_pixels(tracking_id)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de données initialisée : {DB_PATH}")

def get_connection():
    """Retourne une connexion à la base de données"""
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_database()

