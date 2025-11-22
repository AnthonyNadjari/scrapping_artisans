@echo off
REM Script helper pour les commits Git sur Windows

if "%1"=="" (
    echo Usage: git-commit.bat ^<message^>
    echo Exemple: git-commit.bat "feat: Ajout du scraper Google Maps"
    exit /b 1
)

git add .
git commit -m "%*"
echo ✅ Commit créé avec le message: %*

