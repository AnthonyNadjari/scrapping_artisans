@echo off
REM Script de lancement Windows

echo 🚀 Démarrage du système de prospection...

REM Installer les dépendances
pip install -r requirements.txt

REM Installer Playwright
playwright install chromium

REM Initialiser la base de données
python database/models.py

REM Lancer Streamlit
streamlit run app/Accueil.py --server.port 8501

pause

