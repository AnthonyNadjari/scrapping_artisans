@echo off
chcp 65001 >nul
echo ========================================
echo LANCEMENT STREAMLIT - PROSPECTION ARTISANS
echo ========================================
echo.
echo Demarrage de l'application...
echo.

cd /d "%~dp0"
streamlit run whatsapp_app/Accueil.py

pause





