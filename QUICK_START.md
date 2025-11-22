# 🚀 Démarrage Rapide

## ⚡ Commandes à Exécuter (dans le terminal)

### Windows (PowerShell ou CMD)

```powershell
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Installer Playwright
playwright install chromium

# 3. Initialiser la base de données
python database/models.py

# 4. Lancer l'application
streamlit run app/Accueil.py
```

**OU** utilisez simplement le script :
```powershell
.\run.bat
```

### Linux/Mac

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Installer Playwright
playwright install chromium

# 3. Initialiser la base de données
python database/models.py

# 4. Lancer l'application
streamlit run app/Accueil.py
```

**OU** utilisez simplement le script :
```bash
bash run.sh
```

## 📝 Explication

- **Les fichiers .md** (Markdown) sont de la **documentation** à lire, pas à exécuter
- **Les commandes ci-dessus** sont à copier-coller dans votre **terminal/console**
- L'application s'ouvrira automatiquement dans votre navigateur sur **http://localhost:8501**

## ✅ Vérification

Après avoir lancé `streamlit run app/Accueil.py`, vous devriez voir :
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Ouvrez cette URL dans votre navigateur !

