import ast
import sys

files = [
    "whatsapp_app/pages/1_🔍_Scraping.py",
    "whatsapp_app/pages/2_📊_Base_de_Données.py"
]

for f in files:
    try:
        with open(f, encoding='utf-8') as file:
            ast.parse(file.read())
        print(f"OK: {f}")
    except SyntaxError as e:
        print(f"ERROR: {f} - Line {e.lineno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {f} - {e}")
        sys.exit(1)

print("All files OK!")

