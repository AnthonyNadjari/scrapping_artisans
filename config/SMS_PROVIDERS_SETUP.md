# Configuration des Providers SMS

Ce document explique comment configurer différents providers SMS pour envoyer des messages à d'autres numéros.

## 🎯 Providers Disponibles

### 1. OVH SMS (Recommandé pour la France 🇫🇷)

**Avantages** :
- Service français, fiable
- Tarifs compétitifs
- Bon support

**Configuration** :

1. Créez un compte sur https://www.ovh.com/
2. Commandez un service SMS dans votre espace client
3. Créez une application API :
   - Allez dans "API" > "Créer une application"
   - Notez : Application Key, Application Secret
   - Générez un Consumer Key

4. Ajoutez dans `config/sms_config.json` :

```json
{
    "provider": "ovh",
    "ovh_service_name": "sms-xxxxx-1", 
    "ovh_app_key": "votre_app_key",
    "ovh_app_secret": "votre_app_secret",
    "ovh_consumer_key": "votre_consumer_key",
    "ovh_sender": "VotreNom"
}
```

**Installation** :
```bash
pip install ovh
```

---

### 2. Twilio (International 🌍)

**Avantages** :
- Très fiable et populaire
- Documentation excellente
- Support international

**Configuration** :

1. Créez un compte sur https://www.twilio.com/
2. Récupérez votre Account SID et Auth Token
3. Achetez un numéro Twilio (ou utilisez un numéro d'essai)

4. Ajoutez dans `config/sms_config.json` :

```json
{
    "provider": "twilio",
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

### 3. MessageBird (Europe 🇪🇺)

**Avantages** :
- Bon pour l'Europe
- API simple
- Tarifs compétitifs

**Configuration** :

1. Créez un compte sur https://www.messagebird.com/
2. Récupérez votre API Key

3. Ajoutez dans `config/sms_config.json` :

```json
{
    "provider": "messagebird",
    "messagebird_api_key": "votre_api_key",
    "messagebird_originator": "VotreNom"
}
```

**Installation** :
```bash
pip install messagebird
```

---

## 📝 Exemple de Configuration Complète

```json
{
    "provider": "ovh",
    
    "ovh_service_name": "sms-xxxxx-1",
    "ovh_app_key": "votre_app_key",
    "ovh_app_secret": "votre_app_secret",
    "ovh_consumer_key": "votre_consumer_key",
    "ovh_sender": "VotreNom",
    
    "twilio_account_sid": "",
    "twilio_auth_token": "",
    "twilio_from_number": "",
    
    "messagebird_api_key": "",
    "messagebird_originator": "SMS"
}
```

## 🔄 Utilisation dans le Code

Le code détecte automatiquement le provider configuré :

```python
from whatsapp.sms_providers import send_sms

# Envoi automatique (détection du provider)
result = send_sms("0612345678", "Votre message")

# Ou spécifier explicitement
result = send_sms("0612345678", "Votre message", provider="ovh")
```

## 💰 Tarifs Approximatifs

- **OVH** : ~0.05€ par SMS en France
- **Twilio** : ~0.05-0.10€ par SMS selon le pays
- **MessageBird** : ~0.04-0.08€ par SMS en Europe

## ⚠️ Important

- Tous les providers nécessitent un compte actif et des crédits
- Les numéros doivent être au format international (+33 pour la France)
- Limite de 160 caractères par SMS (standard GSM)




