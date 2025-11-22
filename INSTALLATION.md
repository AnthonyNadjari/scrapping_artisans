# 📦 Guide d'Installation Détaillé

## Prérequis

- **Python 3.8 ou supérieur**
- **Gmail** avec App Password configuré (pour l'envoi d'emails)
- **Connexion Internet** (pour le scraping et les APIs)

## Installation Étape par Étape

### 1. Cloner ou Télécharger le Projet

```bash
# Si vous avez git
git clone <url-du-repo>
cd scrapping_artisans

# Sinon, décompressez l'archive ZIP
```

### 2. Créer un Environnement Virtuel (Recommandé)

**Windows :**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac :**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer Playwright

```bash
playwright install chromium
```

Cette étape peut prendre quelques minutes car elle télécharge le navigateur Chromium.

### 5. Initialiser la Base de Données

```bash
python database/models.py
```

Cela créera le fichier `data/artisans.db` avec toutes les tables nécessaires.

### 6. Configurer Gmail (Optionnel pour commencer)

#### Créer un App Password Gmail :

1. Allez sur https://myaccount.google.com/apppasswords
2. Si nécessaire, activez la validation en 2 étapes
3. Créez un nouveau mot de passe d'application :
   - Sélectionnez "Mail"
   - Sélectionnez "Autre (nom personnalisé)"
   - Entrez "Streamlit App"
   - Cliquez sur "Générer"
4. **Copiez le mot de passe** (16 caractères, format : xxxx xxxx xxxx xxxx)

#### Configurer dans l'Application :

1. Lancez l'application (voir étape 7)
2. Allez dans **⚙️ Paramètres**
3. Entrez votre adresse Gmail
4. Entrez l'App Password (sans espaces)
5. Cliquez sur "Sauvegarder"
6. Testez avec "Tester l'envoi"

### 7. Lancer l'Application

**Windows :**
```bash
streamlit run app/Accueil.py
```

**Linux/Mac :**
```bash
streamlit run app/Accueil.py
```

Ou utilisez les scripts fournis :
- **Windows** : `run.bat`
- **Linux/Mac** : `bash run.sh`

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse :
**http://localhost:8501**

## Vérification de l'Installation

### Test 1 : Base de Données
- Vérifiez que le fichier `data/artisans.db` existe
- L'application devrait démarrer sans erreur

### Test 2 : Scraping
1. Allez sur la page **🔍 Scraping**
2. Sélectionnez un métier (ex: "plombier")
3. Sélectionnez un département (ex: "77")
4. Cliquez sur "LANCER LE SCRAPING"
5. Vous devriez voir des résultats apparaître

### Test 3 : Gmail (si configuré)
1. Allez sur **⚙️ Paramètres**
2. Cliquez sur "Tester l'envoi"
3. Vérifiez votre boîte de réception

## Dépannage

### Erreur : "Module not found"
```bash
pip install -r requirements.txt
```

### Erreur : "Playwright not found"
```bash
playwright install chromium
```

### Erreur : "Database is locked"
- Fermez toutes les instances de l'application
- Redémarrez

### Erreur Gmail : "Authentication failed"
- Vérifiez que vous utilisez un **App Password**, pas votre mot de passe principal
- Vérifiez que l'App Password est correct (16 caractères, sans espaces)
- Assurez-vous que la validation en 2 étapes est activée

### Erreur : "Port 8501 already in use"
```bash
# Utiliser un autre port
streamlit run app/Accueil.py --server.port 8502
```

## Configuration Avancée

### Variables d'Environnement (Optionnel)

Créez un fichier `.env` à la racine :

```env
GMAIL_EMAIL=votre-email@gmail.com
GMAIL_APP_PASSWORD=votre-app-password
OPENAI_API_KEY=votre-clé-openai
SIRENE_API_KEY=votre-clé-sirene
```

### API SIRENE (Optionnel)

Pour utiliser l'API SIRENE :

1. Créez un compte sur https://api.insee.fr/
2. Générez une clé API
3. Utilisez-la dans la page Scraping

### OpenAI (Optionnel)

Pour la génération d'emails avec IA :

1. Créez un compte sur https://platform.openai.com/
2. Générez une clé API
3. Ajoutez-la dans `.env` ou dans les variables d'environnement système

## Première Utilisation

1. **Lancez le scraping** sur quelques communes pour tester
2. **Consultez la base de données** pour voir les résultats
3. **Enrichissez les emails** manquants
4. **Créez une petite campagne** de test (5-10 artisans)
5. **Vérifiez les analytics** pour voir les performances

## Support

En cas de problème :
1. Vérifiez les logs dans la console
2. Consultez le README.md
3. Vérifiez que toutes les dépendances sont installées

---

**Bon scraping ! 🚀**

