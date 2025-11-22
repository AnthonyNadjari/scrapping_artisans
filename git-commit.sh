#!/bin/bash
# Script helper pour les commits Git avec message automatique

if [ -z "$1" ]; then
    echo "Usage: ./git-commit.sh <message>"
    echo "Exemple: ./git-commit.sh 'feat: Ajout du scraper Google Maps'"
    exit 1
fi

git add .
git commit -m "$1"
echo "✅ Commit créé avec le message: $1"

