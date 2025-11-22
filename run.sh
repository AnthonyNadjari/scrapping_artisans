#!/bin/bash
# Script de lancement de l'application

echo "🚀 Démarrage du système de prospection..."

# Installer les dépendances si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "🌐 Installation de Playwright..."
playwright install chromium

echo "🗄️ Initialisation de la base de données..."
python database/models.py

echo "✅ Démarrage de Streamlit..."
streamlit run app/Accueil.py --server.port 8501

