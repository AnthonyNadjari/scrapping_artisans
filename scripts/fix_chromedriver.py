#!/usr/bin/env python3
"""
Script pour forcer la mise à jour de ChromeDriver
Vide le cache et télécharge la version compatible avec Chrome
"""
import os
import shutil
import sys
from pathlib import Path

def fix_chromedriver():
    """Vide le cache ChromeDriver et force le téléchargement de la bonne version"""
    cache_path = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver")
    
    print("🔧 Correction du problème ChromeDriver...")
    print(f"📂 Cache: {cache_path}")
    
    if os.path.exists(cache_path):
        try:
            # Lister les versions dans le cache
            versions = [d for d in os.listdir(cache_path) if os.path.isdir(os.path.join(cache_path, d))]
            print(f"📋 Versions trouvées dans le cache: {versions}")
            
            # Trouver les anciennes versions (114 ou inférieures)
            old_versions = []
            for v in versions:
                try:
                    major = int(v.split(".")[0])
                    if major < 140:
                        old_versions.append(v)
                except:
                    pass
            
            if old_versions:
                print(f"⚠️  Anciennes versions détectées: {old_versions}")
                print("🗑️  Suppression des anciennes versions...")
                
                # Supprimer seulement les anciennes versions, pas tout le cache
                for old_v in old_versions:
                    old_path = os.path.join(cache_path, old_v)
                    try:
                        if os.path.exists(old_path):
                            shutil.rmtree(old_path)
                            print(f"✅ Version {old_v} supprimée")
                    except PermissionError:
                        print(f"⚠️  Impossible de supprimer {old_v} (fichier en cours d'utilisation)")
                        print("💡 Fermez tous les navigateurs Chrome et réessayez")
                    except Exception as e:
                        print(f"⚠️  Erreur suppression {old_v}: {e}")
            else:
                print("✅ Aucune ancienne version détectée")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'analyse du cache: {e}")
    else:
        print("ℹ️  Cache ChromeDriver n'existe pas encore")
    
    print("\n✅ Prochain lancement, ChromeDriverManager téléchargera automatiquement la version compatible")
    print("💡 Si le problème persiste, fermez tous les navigateurs Chrome et relancez")

if __name__ == "__main__":
    fix_chromedriver()

