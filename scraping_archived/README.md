# 📦 Code Archivé - SIRENE & Enrichissement

Ce dossier contient le code SIRENE API et d'enrichissement (Pages Blanches, 118712) qui ont été remplacés par le scraper Google Maps.

## Fichiers archivés

- `sirene_api.py` : Interface avec l'API SIRENE de l'INSEE

## Code supprimé (mais peut être recréé si besoin)

- `enrichment/pages_blanches_scraper.py` : Scraper Pages Blanches
- `enrichment/annuaire_118712.py` : Scraper 118712.fr
- `enrichment/enrichment_manager.py` : Gestionnaire d'enrichissement
- `enrichment/nom_prenom_extractor.py` : Extracteur nom/prénom

## Pourquoi archivé ?

Le système utilise maintenant **Google Maps** comme source principale de données car :
- ✅ Plus de téléphones directement disponibles (pas besoin d'enrichissement)
- ✅ Détection automatique des sites web (pour identifier les meilleurs prospects)
- ✅ Notes et avis Google
- ✅ Données plus à jour
- ✅ Plus simple et plus rapide

## Si besoin de réactiver

### SIRENE API
1. Copier `sirene_api.py` dans `scraping/`
2. Créer une page Streamlit pour l'acquisition SIRENE
3. Mettre à jour les imports

### Enrichissement
Le code d'enrichissement a été supprimé. Si besoin, il faudra le recréer depuis zéro ou utiliser une version précédente du dépôt Git.

