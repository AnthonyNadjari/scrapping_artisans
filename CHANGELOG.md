# Changelog - Nettoyage et optimisation

## ✅ Problème OneDrive résolu

### Fichiers créés
- **`.onedriveignore`** : Empêche OneDrive de synchroniser automatiquement les fichiers modifiés
- **`force_local_files.ps1`** : Script PowerShell pour forcer les fichiers à rester en local (toujours disponible hors ligne)

### Utilisation
1. Exécutez `force_local_files.ps1` pour configurer les fichiers en local
2. Les fichiers ne s'ouvriront plus automatiquement lors des modifications

## 🧹 Nettoyage du code

### Fichiers supprimés
- `FIX_APPLIQUE.md` - Documentation obsolète
- `PROMPT_ANALYSE_HTML_CRITIQUE.md` - Fichier de prompt inutile
- `PROMPT_FIX_CONSENTEMENT.md` - Fichier de prompt inutile

### Fichiers de debug ignorés
- `data/debug/` - Dossier de debug ajouté au `.gitignore`
- `data/debug_scraping/` - Dossier de debug ajouté au `.gitignore`
- Fichiers JSON temporaires de scraping ajoutés au `.gitignore`

## 📝 Structure du projet

Le projet est maintenant prêt pour un nouveau départ avec :
- Code nettoyé
- Configuration OneDrive optimisée
- Fichiers de debug ignorés par Git

## ⚡ Optimisations MAX - Version ultra-rapide (2025-11-24)

### Corrections
- ✅ Erreur Streamlit `use_container_width` corrigée
- ✅ Détection correcte du site web (exclut Google Maps)
- ✅ Tous les établissements scrapés (plus de limite à 5)

### Optimisations de vitesse
- ✅ Délais réduits au minimum (50-60% plus rapide)
- ✅ Ordre d'extraction optimisé (extraction directe d'abord)
- ✅ Scroll optimisé (délais réduits, plus de scrolls)

### Nettoyage
- ✅ Fichiers de documentation inutiles supprimés
- ✅ Code optimisé et prêt pour production

