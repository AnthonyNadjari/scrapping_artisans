import ast
import sys
import os

files = []
for f in os.listdir("whatsapp_app/pages"):
    if f.endswith(".py"):
        files.append(os.path.join("whatsapp_app/pages", f))

for f in files:
    try:
        with open(f, encoding='utf-8') as file:
            ast.parse(file.read())
        print(f"OK: {f}")
    except SyntaxError as e:
        print(f"ERROR: {f} - Line {e.lineno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {f} - {str(e)}")
        sys.exit(1)

print("All files OK!")

