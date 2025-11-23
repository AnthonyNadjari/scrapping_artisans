# 📱 Système de Prospection WhatsApp pour Artisans

Système simplifié de prospection par WhatsApp pour artisans français.

## 🚀 Installation Rapide

### 1. Installer les dépendances

```bash
pip install -r requirements_whatsapp.txt
playwright install chromium
```

### 2. Initialiser la base de données

```bash
python whatsapp_database/models.py
```

### 3. Configurer WhatsApp Business API

**⚠️ IMPORTANT :** Vous devez configurer WhatsApp Business API avant d'utiliser l'application.

Voir le guide complet : **`WHATSAPP_SETUP.md`**

**Résumé rapide :**
1. Créez un compte sur https://developers.facebook.com/
2. Créez une application Meta
3. Ajoutez WhatsApp Business API
4. Obtenez vos identifiants :
   - Access Token
   - Phone Number ID
   - Business Account ID

5. Créez le fichier `config/whatsapp_config.json` :
```json
{
    "access_token": "VOTRE_TOKEN",
    "phone_number_id": "VOTRE_ID",
    "business_account_id": "VOTRE_ID"
}
```

### 4. Lancer l'application

**Windows :**
```bash
launch_whatsapp.bat
```

**Linux/Mac :**
```bash
streamlit run whatsapp_app/Accueil.py --server.port 8501
```

## 📋 Fonctionnalités

- ✅ Scraping téléphones uniquement (Google Maps, Pages Jaunes)
- ✅ Vérification automatique WhatsApp
- ✅ Envoi contrôlé avec rate limiting anti-ban
- ✅ Tracking des réponses
- ✅ Interface Streamlit simple

## 📁 Structure

```
whatsapp_app/          # Interface Streamlit
whatsapp/              # Gestion WhatsApp (rate limiter, manager)
whatsapp_scraping/     # Scrapers téléphones
whatsapp_database/     # Base de données SQLite
config/                # Configuration
```

## 🔒 Sécurité

- Le fichier `config/whatsapp_config.json` est dans `.gitignore`
- Ne jamais commit vos tokens
- Respectez les rate limits pour éviter les bans

## 📚 Documentation

- **Configuration WhatsApp** : `WHATSAPP_SETUP.md`
- **Guide complet** : Voir la documentation dans l'application

---

**Bon scraping ! 🚀**

