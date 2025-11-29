#!/usr/bin/env python3
"""
Script pour réinitialiser TOUTES les bases de données et fichiers de données
"""
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from whatsapp_database.models import get_connection, DB_PATH
import sqlite3

def reset_all_databases():
    """Réinitialise toutes les bases de données et fichiers de données"""
    
    print("=" * 60)
    print("REINITIALISATION COMPLETE DES BASES DE DONNEES")
    print("=" * 60)
    
    # 1. Vider la base de données SQLite
    print("\n[1/2] Vidage de la base de donnees SQLite...")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Désactiver les foreign keys temporairement
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Supprimer toutes les données de toutes les tables
        tables = ['reponses', 'messages_log', 'artisans', 'scraping_history']
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                count = cursor.rowcount
                print(f"  [OK] {count} ligne(s) supprimee(s) de la table '{table}'")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    print(f"  [WARN] Table '{table}' n'existe pas (ignorée)")
                else:
                    raise
        
        # Réinitialiser les séquences AUTOINCREMENT
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('artisans', 'messages_log', 'reponses', 'scraping_history')")
        except:
            pass  # Ignorer si la table n'existe pas
        
        # Réactiver les foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print(f"  [OK] Base de donnees SQLite videe: {DB_PATH}")
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] Erreur lors du vidage SQLite: {e}")
        return False
    finally:
        conn.close()
    
    # 2. Réinitialiser les fichiers JSON de données (seulement ceux utilisés)
    print("\n[2/2] Reinitialisation des fichiers JSON...")
    
    data_dir = Path(__file__).parent.parent / "data"
    # ✅ Seulement 2 fichiers JSON nécessaires :
    # - scraping_results_github_actions.json : pour l'artifact GitHub Actions
    # - github_actions_status.json : pour le statut des workflows GitHub Actions
    json_files_to_reset = [
        "scraping_results_github_actions.json",
        "github_actions_status.json"
    ]
    
    # ✅ Supprimer les fichiers JSON inutiles (vestiges du mode local)
    json_files_to_delete = [
        "scraping_results_temp.json",
        "scraping_status.json",
        "scraping_checkpoint.json",
        "scraping_logs.json",
        "saved_count.json"
    ]
    
    # Supprimer les fichiers inutiles
    for json_file in json_files_to_delete:
        file_path = data_dir / json_file
        try:
            if file_path.exists():
                file_path.unlink()
                print(f"  [OK] {json_file} supprime (inutile)")
        except Exception as e:
            print(f"  [WARN] Erreur suppression {json_file}: {e}")
    
    # Réinitialiser les fichiers nécessaires
    for json_file in json_files_to_reset:
        file_path = data_dir / json_file
        try:
            if json_file == "scraping_results_github_actions.json":
                # Fichier de résultats = liste vide
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
            elif json_file == "github_actions_status.json":
                # Fichier de statut = objet vide
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=2, ensure_ascii=False)
            
            print(f"  [OK] {json_file} reinitialise")
        except Exception as e:
            print(f"  [WARN] {json_file}: {e}")
    
    print("\n" + "=" * 60)
    print("REINITIALISATION TERMINEE AVEC SUCCES")
    print("=" * 60)
    print(f"\nBase de donnees: {DB_PATH}")
    print(f"Fichiers JSON reinitialises: {len(json_files_to_reset)}")
    print("\nToutes les donnees ont ete supprimees.")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Mode non-interactif si --force est passé
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if force:
        print("Mode force active - reinitialisation sans confirmation\n")
        success = reset_all_databases()
        if success:
            print("\nOperation terminee avec succes")
            sys.exit(0)
        else:
            print("\nErreur lors de l'operation")
            sys.exit(1)
    else:
        print("\n[ATTENTION] Cette operation va supprimer TOUTES les donnees!")
        print("   - Base de donnees SQLite (artisans, messages, reponses, etc.)")
        print("   - Tous les fichiers JSON de scraping et de statut")
        print()
        confirm = input("Etes-vous sur de vouloir continuer ? (oui/non): ")
        if confirm.lower() in ['oui', 'o', 'yes', 'y']:
            success = reset_all_databases()
            if success:
                print("\nOperation terminee avec succes")
            else:
                print("\nErreur lors de l'operation")
                sys.exit(1)
        else:
            print("\nOperation annulee")

