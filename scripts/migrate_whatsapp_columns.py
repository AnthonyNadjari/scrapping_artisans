#!/usr/bin/env python3
"""
Script de migration pour ajouter les colonnes WhatsApp à la table artisans
"""
import sqlite3
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from whatsapp.phone_utils import is_mobile, is_landline
from whatsapp.message_builder import detect_site_type

def migrate_database():
    """Ajoute les colonnes et remplit les données existantes"""
    db_path = Path(__file__).parent.parent / "data" / "whatsapp_artisans.db"
    
    if not db_path.exists():
        print(f"[ERROR] Base de donnees non trouvee: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Ajouter les colonnes si elles n'existent pas
        print("Ajout des colonnes...")
        
        try:
            cursor.execute("ALTER TABLE artisans ADD COLUMN phone_type TEXT DEFAULT 'unknown'")
            print("  [OK] Colonne phone_type ajoutee")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  [INFO] Colonne phone_type existe deja")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE artisans ADD COLUMN site_type TEXT DEFAULT 'unknown'")
            print("  [OK] Colonne site_type ajoutee")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  [INFO] Colonne site_type existe deja")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE artisans ADD COLUMN last_message_date TEXT")
            print("  [OK] Colonne last_message_date ajoutee")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  [INFO] Colonne last_message_date existe deja")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE artisans ADD COLUMN last_template_used TEXT")
            print("  [OK] Colonne last_template_used ajoutee")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  [INFO] Colonne last_template_used existe deja")
            else:
                raise
        
        conn.commit()
        
        # Remplir les colonnes pour les artisans existants
        print("\nMise a jour des donnees existantes...")
        
        cursor.execute("SELECT id, telephone, site_web FROM artisans")
        artisans = cursor.fetchall()
        
        updated_count = 0
        for artisan_id, telephone, site_web in artisans:
            # Déterminer phone_type
            phone_type = 'unknown'
            if telephone:
                if is_mobile(telephone):
                    phone_type = 'mobile'
                elif is_landline(telephone):
                    phone_type = 'landline'
                else:
                    phone_type = 'invalid'
            
            # Déterminer site_type
            site_type = detect_site_type(site_web)
            
            # Mettre à jour
            cursor.execute(
                "UPDATE artisans SET phone_type = ?, site_type = ? WHERE id = ?",
                (phone_type, site_type, artisan_id)
            )
            updated_count += 1
        
        conn.commit()
        print(f"  [OK] {updated_count} artisan(s) mis a jour")
        
        print("\nMigration terminee avec succes !")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

