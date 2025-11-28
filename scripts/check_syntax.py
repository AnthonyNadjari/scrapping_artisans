"""Script pour vérifier la syntaxe de tous les fichiers Python"""
import py_compile
import sys
from pathlib import Path

files_to_check = [
    "whatsapp_app/pages/1_🔍_Scraping.py",
    "whatsapp_app/pages/2_📊_Base_de_Données.py",
    "whatsapp_app/pages/3_💬_Réponses.py"
]

errors_found = False

for file_path in files_to_check:
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"✅ {file_path}: OK")
    except py_compile.PyCompileError as e:
        print(f"❌ {file_path}: {e}")
        errors_found = True
    except Exception as e:
        print(f"⚠️ {file_path}: {e}")
        errors_found = True

if errors_found:
    sys.exit(1)
else:
    print("\n✅ Tous les fichiers sont syntaxiquement corrects !")
    sys.exit(0)

