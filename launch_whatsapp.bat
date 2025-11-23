@echo off
echo Lancement du dashboard WhatsApp Streamlit...
echo.
echo Le dashboard sera accessible sur http://localhost:8501
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.
streamlit run whatsapp_app/Accueil.py --server.port 8501
pause

