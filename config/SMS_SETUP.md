# Configuration SMS Free Mobile

Ce système utilise l'API Free Mobile pour envoyer des SMS directement depuis l'application.

## 📋 Prérequis

1. **Avoir un abonnement Free Mobile** avec le service SMS activé
2. **Activer les notifications SMS** dans votre espace client Free Mobile

## 🔧 Configuration

1. **Connectez-vous à votre espace client Free Mobile** : https://mobile.free.fr/mon-compte/

2. **Activez les notifications par SMS** :
   - Allez dans "Mes options" > "Notifications par SMS"
   - Activez le service si ce n'est pas déjà fait
   - **Générez ou récupérez votre token API**

3. **Configurez le fichier `config/sms_config.json`** :

```json
{
    "phone_number": "0612345678",
    "token": "VOTRE_TOKEN_ICI",
    "note": "Remplissez votre numéro de téléphone Free Mobile et votre token API. Le token est disponible dans votre espace client Free Mobile > Mes options > Notifications par SMS."
}
```

**Important** :
- `phone_number` : Votre numéro de téléphone Free Mobile (format: 0612345678)
- `token` : Le token API généré dans votre espace client Free Mobile

## ⚠️ Limitations

- **160 caractères maximum** par SMS (les messages plus longs seront tronqués)
- **Limite de débit** : Free Mobile limite le nombre de SMS envoyés par minute
- **Service payant** : Vérifiez les conditions de votre abonnement Free Mobile

## 🐛 Codes d'erreur

- **200** : SMS envoyé avec succès ✅
- **400** : Paramètre manquant dans la requête
- **402** : Trop de SMS envoyés en peu de temps (attendre quelques minutes)
- **403** : Service SMS non activé ou identifiants incorrects (vérifier le token)
- **500** : Erreur serveur Free Mobile (réessayer plus tard)

## 🔒 Sécurité

Le fichier `config/sms_config.json` est dans `.gitignore` et ne sera **pas** commité dans Git pour protéger vos identifiants.




