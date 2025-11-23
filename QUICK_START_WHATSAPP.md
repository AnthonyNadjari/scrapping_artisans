# ⚡ Configuration WhatsApp - Guide Rapide

## 🎯 Ce dont vous avez besoin

Pour connecter votre compte WhatsApp et envoyer des messages, vous avez besoin de **3 éléments** :

1. **Access Token** (Token d'authentification Meta)
2. **Phone Number ID** (ID de votre numéro WhatsApp Business)
3. **Business Account ID** (ID de votre compte business Meta)

---

## 📝 Étapes Rapides

### 1. Créer un compte Meta Business (5 min)

1. Allez sur https://business.facebook.com/
2. Créez un compte (gratuit)
3. Vérifiez votre email

### 2. Créer une application Meta (5 min)

1. Allez sur https://developers.facebook.com/
2. Cliquez **"Mes applications"** > **"Créer une application"**
3. Sélectionnez **"Business"**
4. Donnez un nom (ex: "WhatsApp Prospection")

### 3. Ajouter WhatsApp (2 min)

1. Dans votre application, **"Ajouter un produit"**
2. Cherchez **"WhatsApp"** > **"Configurer"**
3. Suivez les instructions

### 4. Obtenir vos identifiants (5 min)

Dans **WhatsApp** > **API Setup**, vous trouverez :

- ✅ **Access Token** : Copiez le token temporaire (valide 24h)
- ✅ **Phone Number ID** : Numéro à 15 chiffres
- ✅ **Business Account ID** : Dans Business Settings > WhatsApp Accounts

### 5. Configurer dans l'application (1 min)

1. Créez le fichier `config/whatsapp_config.json` :

```json
{
    "access_token": "VOTRE_TOKEN_ICI",
    "phone_number_id": "VOTRE_ID_ICI",
    "business_account_id": "VOTRE_ID_ICI"
}
```

2. Testez dans l'app (page Paramètres > Tester connexion)

---

## 🆓 Compte de Test GRATUIT

Meta offre un **compte de test gratuit** avec :
- ✅ 1000 conversations/mois
- ✅ Numéro de test fourni
- ✅ Parfait pour tester

**Limite** : Messages uniquement vers numéros que vous avez vérifiés manuellement.

---

## 💰 Compte Production (Optionnel)

Pour utiliser votre propre numéro et envoyer à n'importe qui :
- Coût : ~€0.005-0.10 par conversation
- Numéro : ~$1-5/mois

---

## ⚠️ Important

- ⚠️ Le token temporaire expire après 24h
- ✅ Pour un token permanent : Créez un System User dans Business Settings
- ✅ Le fichier `whatsapp_config.json` est automatiquement ignoré par Git

---

## 🧪 Tester

1. Lancez l'app : `launch_whatsapp.bat`
2. Allez dans **⚙️ Paramètres**
3. Remplissez vos identifiants
4. Cliquez **"🧪 Tester connexion"**
5. Vous devriez voir "✅ Connexion réussie"

---

**Guide détaillé complet : `WHATSAPP_SETUP.md`**

