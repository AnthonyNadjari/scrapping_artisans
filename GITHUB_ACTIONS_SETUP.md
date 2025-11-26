# 🚀 Configuration GitHub Actions pour le Scraping

Ce guide explique comment configurer le scraping distant via GitHub Actions.

## 📋 Prérequis

1. Un compte GitHub
2. Votre code doit être dans un repository GitHub
3. Un Personal Access Token GitHub avec les permissions `repo` et `workflow`

## 🔑 Créer un Personal Access Token

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur "Generate new token" → "Generate new token (classic)"
3. Donnez un nom (ex: "Streamlit Scraping")
4. Cochez les permissions :
   - ✅ `repo` (toutes les sous-permissions)
   - ✅ `workflow`
5. Cliquez sur "Generate token"
6. **⚠️ IMPORTANT : Copiez le token immédiatement, vous ne pourrez plus le voir après !**

## ⚙️ Configuration dans Streamlit

1. Ouvrez la page **🔍 Scraping** dans Streamlit
2. Cochez **"☁️ Utiliser GitHub Actions (scraping distant, gratuit)"**
3. Entrez votre **Token GitHub** (le Personal Access Token créé ci-dessus)
4. Entrez votre **Repository GitHub** au format `owner/repo` (ex: `votre-username/scrapping_artisans`)
5. Configurez vos paramètres de scraping (métiers, départements, etc.)
6. Cliquez sur **"☁️ LANCER SUR GITHUB ACTIONS"**

## 📊 Suivi du scraping

- Le statut s'affiche en temps réel dans Streamlit
- Vous pouvez aussi suivre sur GitHub : **Actions** → **Workflows** → **Google Maps Scraping**
- Les résultats sont automatiquement téléchargés et sauvegardés en BDD quand le scraping est terminé

## ⏱️ Limitations

- **Quota gratuit** : 2000 minutes/mois (suffisant pour ~33h de scraping)
- **Timeout** : 6 heures maximum par run
- **Latence** : ~30-60 secondes pour démarrer le workflow

## 🔧 Dépannage

### Le workflow ne démarre pas
- Vérifiez que le token a les bonnes permissions
- Vérifiez que le repository est au bon format (`owner/repo`)
- Vérifiez que le workflow existe dans `.github/workflows/scraping.yml`

### Le scraping échoue
- Vérifiez les logs sur GitHub Actions
- Vérifiez que `requirements.txt` contient toutes les dépendances
- Vérifiez que le fichier `data/villes_par_departement.json` existe dans le repo

### Les résultats ne se téléchargent pas
- Vérifiez que le workflow s'est terminé avec succès
- Vérifiez que l'artifact "scraping-results" a été créé
- Vérifiez que le token a toujours les permissions `repo`

## 💡 Astuces

- Vous pouvez fermer Streamlit pendant le scraping, les résultats seront disponibles au retour
- Le scraping continue même si vous fermez la page
- Vous pouvez lancer plusieurs scrapings en parallèle (dans la limite du quota)

