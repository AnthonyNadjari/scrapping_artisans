#!/usr/bin/env python3
"""
Script pour vider complètement la base de données
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from whatsapp_database.models import get_connection, DB_PATH
import sqlite3

def empty_database():
    """Vide complètement toutes les tables de la base de données"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Désactiver les foreign keys temporairement
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Supprimer toutes les données de toutes les tables
        tables = ['reponses', 'messages_log', 'artisans', 'scraping_history']
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            count = cursor.rowcount
            print(f"[OK] {count} ligne(s) supprimee(s) de la table '{table}'")
        
        # Réinitialiser les séquences AUTOINCREMENT
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('artisans', 'messages_log', 'reponses', 'scraping_history')")
        
        # Réactiver les foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print(f"\n[OK] Base de donnees videe avec succes: {DB_PATH}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERREUR] Erreur lors du vidage: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    # Mode non-interactif si --force est passé
    force = '--force' in sys.argv or '-f' in sys.argv
    
    print("Vidage de la base de donnees...")
    print(f"Fichier: {DB_PATH}\n")
    
    if force:
        print("Mode force active - vidage sans confirmation")
        success = empty_database()
        if success:
            print("\nOperation terminee avec succes")
        else:
            print("\nErreur lors de l'operation")
            sys.exit(1)
    else:
        confirm = input("Etes-vous sur de vouloir vider TOUTE la base de donnees ? (oui/non): ")
        if confirm.lower() in ['oui', 'o', 'yes', 'y']:
            success = empty_database()
            if success:
                print("\nOperation terminee avec succes")
            else:
                print("\nErreur lors de l'operation")
        else:
            print("Operation annulee")

