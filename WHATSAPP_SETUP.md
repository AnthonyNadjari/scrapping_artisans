# 📱 Configuration WhatsApp Business API

## 🎯 Ce dont vous avez besoin

Pour connecter votre compte WhatsApp et envoyer des messages, vous devez configurer **WhatsApp Business API** via Meta (Facebook).

### ✅ Éléments nécessaires :

1. **Access Token** - Token d'authentification Meta
2. **Phone Number ID** - ID de votre numéro WhatsApp Business
3. **Business Account ID** - ID de votre compte business Meta

---

## 📋 ÉTAPE PAR ÉTAPE

### Étape 1 : Créer un compte Meta Business

1. Allez sur https://business.facebook.com/
2. Créez un compte Business (gratuit)
3. Vérifiez votre compte

### Étape 2 : Créer une application Meta

1. Allez sur https://developers.facebook.com/
2. Cliquez sur **"Mes applications"** > **"Créer une application"**
3. Sélectionnez **"Business"** comme type
4. Donnez un nom à votre application

### Étape 3 : Ajouter WhatsApp Business API

1. Dans votre application, allez dans **"Ajouter un produit"**
2. Cherchez **"WhatsApp"** et cliquez sur **"Configurer"**
3. Suivez les instructions pour configurer WhatsApp Business API

### Étape 4 : Obtenir votre numéro de test (GRATUIT)

**Pour tester gratuitement :**

1. Dans la console Meta, allez dans **WhatsApp** > **API Setup**
2. Vous verrez un numéro de test (ex: +1 234 567 8900)
3. Ce numéro permet d'envoyer des messages GRATUITEMENT pendant la période de test

**Limites du compte de test :**
- 1000 conversations par mois
- Numéro de test uniquement
- Messages uniquement vers numéros vérifiés

### Étape 5 : Obtenir vos identifiants

1. **Access Token** :
   - Allez dans **WhatsApp** > **API Setup**
   - Copiez le **"Temporary access token"** (valide 24h)
   - Pour un token permanent, créez un **System User** dans Business Settings

2. **Phone Number ID** :
   - Dans **API Setup**, vous verrez **"Phone number ID"**
   - Copiez cet ID (ex: 123456789012345)

3. **Business Account ID** :
   - Allez dans **Business Settings** > **Accounts** > **WhatsApp Accounts**
   - Copiez l'ID du compte (ex: 987654321098765)

### Étape 6 : Configurer dans l'application

1. Créez le fichier `config/whatsapp_config.json` :

```json
{
    "access_token": "VOTRE_ACCESS_TOKEN_ICI",
    "phone_number_id": "VOTRE_PHONE_NUMBER_ID_ICI",
    "business_account_id": "VOTRE_BUSINESS_ACCOUNT_ID_ICI"
}
```

2. **⚠️ IMPORTANT** : Ce fichier est dans `.gitignore` - ne sera jamais commité

3. Testez la connexion dans l'application (page Paramètres)

---

## 🔑 Token Permanent (Recommandé)

Le token temporaire expire après 24h. Pour un token permanent :

1. Allez dans **Business Settings** > **System Users**
2. Créez un nouveau System User
3. Assignez-lui le rôle **"Admin"**
4. Générez un token pour ce System User
5. Sélectionnez les permissions : `whatsapp_business_messaging`, `whatsapp_business_management`

---

## 📱 Numéro WhatsApp Business (Production)

Pour utiliser votre propre numéro :

1. **Option 1 : Numéro existant**
   - Vérifiez votre numéro dans Meta Business
   - Suivez le processus de vérification

2. **Option 2 : Nouveau numéro**
   - Achetez un numéro via Meta
   - Coût : ~$1-5/mois selon pays

---

## ⚠️ LIMITES ET COÛTS

### Compte de test (GRATUIT) :
- 1000 conversations/mois
- Numéro de test uniquement
- Messages vers numéros vérifiés uniquement

### Compte production :
- **Conversations** : Payantes après les 1000 premières
- **Coût** : Variable selon pays (ex: €0.005-0.10 par conversation)
- **Numéro** : ~$1-5/mois

---

## 🧪 Tester la connexion

1. Lancez l'application Streamlit
2. Allez dans **⚙️ Paramètres**
3. Remplissez vos identifiants
4. Cliquez sur **"🧪 Tester connexion"**
5. Vous devriez voir "✅ Connexion réussie"

---

## 📚 Ressources utiles

- **Documentation Meta** : https://developers.facebook.com/docs/whatsapp
- **API Reference** : https://developers.facebook.com/docs/whatsapp/cloud-api
- **Support** : https://business.facebook.com/help

---

## 🔒 Sécurité

- ⚠️ **NE JAMAIS** commit le fichier `whatsapp_config.json`
- ⚠️ **NE JAMAIS** partager vos tokens
- ✅ Le fichier est automatiquement dans `.gitignore`
- ✅ Utilisez des tokens avec permissions minimales

---

## ❓ Problèmes courants

### "Invalid access token"
- Vérifiez que le token n'a pas expiré
- Régénérez un nouveau token

### "Phone number not found"
- Vérifiez que le Phone Number ID est correct
- Assurez-vous que le numéro est bien configuré dans Meta

### "Rate limit exceeded"
- Vous avez dépassé les limites
- Attendez ou augmentez vos limites dans Meta

---

**Une fois configuré, vous pouvez commencer à scraper et envoyer des messages ! 🚀**

