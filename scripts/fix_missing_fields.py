#!/usr/bin/env python3
"""
Script pour corriger les champs manquants dans la base de données
- Extrait le département depuis le code postal si manquant
- Extrait la ville depuis l'adresse si manquante
"""
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from whatsapp_database.models import get_connection
import sqlite3

def fix_missing_fields():
    """Corrige les champs manquants dans la base de données"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer tous les artisans
    cursor.execute("SELECT id, code_postal, adresse, departement, ville FROM artisans")
    artisans = cursor.fetchall()
    
    updated_count = 0
    
    for artisan in artisans:
        artisan_id, code_postal, adresse, departement, ville = artisan
        
        updates = []
        params = []
        
        # Extraire le département depuis le code postal si manquant
        if not departement and code_postal:
            code_postal_str = str(code_postal).strip()
            if len(code_postal_str) >= 2:
                # Pour les départements d'outre-mer (97x, 98x), prendre les 3 premiers chiffres
                if code_postal_str.startswith('97') or code_postal_str.startswith('98'):
                    new_departement = code_postal_str[:3]
                else:
                    new_departement = code_postal_str[:2]
                updates.append("departement = ?")
                params.append(new_departement)
        
        # Extraire la ville depuis l'adresse si manquante
        if not ville and adresse:
            ville_match = re.search(r'\d{5}\s+([A-Za-zÀ-ÿ\s-]+)', str(adresse))
            if ville_match:
                new_ville = ville_match.group(1).strip()
                updates.append("ville = ?")
                params.append(new_ville)
        
        # Mettre à jour si nécessaire
        if updates:
            params.append(artisan_id)
            query = f"UPDATE artisans SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            updated_count += 1
            print(f"Artisan {artisan_id} mis a jour: {', '.join(updates)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n{updated_count} artisan(s) mis a jour sur {len(artisans)} total")
    return updated_count

if __name__ == "__main__":
    print("Correction des champs manquants dans la base de donnees...")
    fix_missing_fields()
    print("Termine !")

