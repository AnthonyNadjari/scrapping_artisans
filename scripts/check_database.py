"""Script pour vérifier le contenu de la base de données"""
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.whatsapp_settings import DB_PATH

print(f"Base de donnees: {DB_PATH}")
print(f"Existe: {DB_PATH.exists()}")
if DB_PATH.exists():
    print(f"Taille: {DB_PATH.stat().st_size} bytes")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Compter les artisans
    cursor.execute('SELECT COUNT(*) FROM artisans')
    total = cursor.fetchone()[0]
    print(f"\nTotal artisans: {total}")
    
    # Compter ceux de la dernière heure
    cursor.execute('SELECT COUNT(*) FROM artisans WHERE created_at >= datetime("now", "-1 hour")')
    derniere_heure = cursor.fetchone()[0]
    print(f"Artisans derniere heure: {derniere_heure}")
    
    # Compter ceux avec téléphone
    cursor.execute('SELECT COUNT(*) FROM artisans WHERE telephone IS NOT NULL AND telephone != ""')
    avec_tel = cursor.fetchone()[0]
    print(f"Avec telephone: {avec_tel}")
    
    # Compter ceux avec site web
    cursor.execute('SELECT COUNT(*) FROM artisans WHERE site_web IS NOT NULL AND site_web != ""')
    avec_site = cursor.fetchone()[0]
    print(f"Avec site web: {avec_site}")
    
    # Afficher les 10 derniers artisans
    cursor.execute('''
        SELECT id, nom_entreprise, telephone, site_web, ville_recherche, created_at 
        FROM artisans 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    print(f"\nDerniers 10 artisans:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} | Tel: {row[2]} | Site: {row[3]} | Ville: {row[4]} | Cree: {row[5]}")
    
    conn.close()
else:
    print("ERREUR: La base de donnees n'existe pas !")

