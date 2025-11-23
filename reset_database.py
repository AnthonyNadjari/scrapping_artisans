"""
Script pour réinitialiser complètement la base de données
avec le nouveau schéma SIRENE
"""
import os
from pathlib import Path
from whatsapp_database.models import DB_PATH, init_database

def reset_database():
    """Supprime et recrée la base de données"""
    print("Reinitialisation de la base de donnees...")
    
    # Supprimer l'ancienne base si elle existe
    if DB_PATH.exists():
        print(f"Suppression de l'ancienne base: {DB_PATH}")
        DB_PATH.unlink()
    
    # Recréer avec le nouveau schéma
    print("Creation de la nouvelle base de donnees...")
    init_database()
    
    print("Base de donnees reinitialisee avec succes !")
    print(f"Emplacement: {DB_PATH}")

if __name__ == "__main__":
    reset_database()

