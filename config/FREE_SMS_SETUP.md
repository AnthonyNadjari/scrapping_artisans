# Configuration SMS 100% GRATUIT

⚠️ **ATTENTION** : Les services SMS vraiment gratuits ont des limitations importantes. Pour un usage professionnel, un service payant est recommandé.

## 🆓 Options Gratuites Disponibles

### Option 1: TextFlow - Votre Téléphone Android (100% GRATUIT) ⭐

**Avantages** :
- ✅ **100% GRATUIT** si vous avez un forfait avec SMS illimités
- ✅ Pas de limite (selon votre forfait mobile)
- ✅ Utilise votre propre numéro de téléphone
- ✅ Pas besoin de service tiers

**Comment ça marche** :
- Installez l'app TextFlow sur votre téléphone Android
- L'app transforme votre téléphone en serveur SMS
- Vous envoyez des SMS via API depuis votre ordinateur
- Les SMS partent de votre téléphone (utilise votre forfait)

**Configuration** :

1. Installez l'app TextFlow : https://play.google.com/store/apps/details?id=me.textflow
2. Configurez l'app et récupérez votre clé API
3. Configurez dans `config/sms_config.json` :

```json
{
    "provider": "textflow",
    "textflow_api_key": "votre_cle_api",
    "textflow_api_url": "https://api.textflow.me/send-sms"
}
```

**Documentation** : https://docs.textflow.me/

---

### Option 2: Twilio Trial Account

**Avantages** :
- ✅ Service fiable et professionnel
- ✅ Crédit gratuit au démarrage (~$15)
- ✅ Documentation excellente

**Limitations** :
- ⚠️ Ne peut envoyer qu'à des numéros vérifiés dans votre compte
- ⚠️ Compte d'essai uniquement (pas pour production)
- ⚠️ Limite de crédit gratuit

**Configuration** :

1. Créez un compte gratuit : https://www.twilio.com/try-twilio
2. Vérifiez votre numéro de téléphone dans le dashboard
3. Pour chaque numéro de destination, vous devez :
   - L'ajouter dans "Phone Numbers" > "Verified Caller IDs"
   - Vérifier le numéro (Twilio envoie un code)
4. Récupérez votre Account SID et Auth Token
5. Configurez dans `config/sms_config.json` :

```json
{
    "provider": "twilio_trial",
    "twilio_account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "twilio_auth_token": "votre_auth_token",
    "twilio_from_number": "+33612345678"
}
```

**Installation** :
```bash
pip install twilio
```

---

### Option 2: TextBelt (Très limité)

**Avantages** :
- ✅ Gratuit
- ✅ Simple à utiliser

**Limitations** :
- ⚠️ **1 SMS par jour seulement** (gratuit)
- ⚠️ Peut être instable
- ⚠️ Pas fiable pour production

**Configuration** :

1. Créez un compte gratuit : https://textbelt.com/
2. Récupérez votre clé API gratuite
3. Configurez dans `config/sms_config.json` :

```json
{
    "provider": "textbelt",
    "textbelt_api_key": "votre_cle_api"
}
```

---

### Option 3: Email vers SMS (Non garanti)

**Avantages** :
- ✅ 100% gratuit
- ✅ Pas de limite (théoriquement)

**Limitations** :
- ⚠️ Fonctionne uniquement avec certains opérateurs
- ⚠️ Peut être bloqué comme spam
- ⚠️ Pas garanti de fonctionner
- ⚠️ Nécessite un serveur email configuré

**Format** :
- Orange: `numero@orange.fr`
- SFR: `numero@sfr.fr`
- Bouygues: `numero@bmsms.fr`
- Free: `numero@mobile.free.fr`

**Configuration** :

```json
{
    "provider": "email",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "votre_email@gmail.com",
    "email_password": "votre_mot_de_passe_app"
}
```

---

## 📝 Configuration Complète

```json
{
    "provider": "twilio_trial",
    
    "twilio_account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "twilio_auth_token": "votre_auth_token",
    "twilio_from_number": "+33612345678",
    
    "textbelt_api_key": "",
    
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "",
    "email_password": ""
}
```

## ⚠️ Recommandation

Pour un usage professionnel, même avec un budget limité :
- **Twilio Trial** : Meilleur compromis (gratuit au début, puis ~0.05€/SMS)
- **OVH SMS** : ~0.05€/SMS en France (très abordable)

Les services vraiment gratuits sont trop limités pour un usage professionnel.

## 🔄 Utilisation

Le code détecte automatiquement le provider configuré :

```python
from whatsapp.sms_free_providers import send_sms

# Envoi automatique
result = send_sms("0612345678", "Votre message")
```

