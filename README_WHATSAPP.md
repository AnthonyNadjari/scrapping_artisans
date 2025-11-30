# 📱 Guide d'utilisation - Onglet Messages WhatsApp

## Vue d'ensemble

L'onglet **"💬 Messages WhatsApp"** permet de générer automatiquement des messages personnalisés pour contacter les artisans scrapés depuis Google Maps. Le système analyse les données disponibles (type de téléphone, site web, note Google, etc.) et sélectionne automatiquement le meilleur template de message.

## 🎯 Fonctionnalités principales

### 1. Filtrage avancé des artisans

Dans la **sidebar (barre latérale)**, vous pouvez filtrer les artisans selon plusieurs critères :

#### Type de contact
- **Tous** : Affiche tous les artisans
- **WhatsApp uniquement (06/07)** : Seulement les numéros mobiles (peuvent recevoir WhatsApp)
- **Cold Call uniquement (01-05)** : Seulement les numéros fixes (appel téléphonique nécessaire)

#### Type de site web
- **Pas de site** : Artisans sans site web
- **Facebook** : Artisans avec une page Facebook
- **Instagram** : Artisans avec un compte Instagram
- **Site web classique** : Artisans avec un site web professionnel

#### Métier
Liste dynamique des métiers trouvés dans la base de données (ex: plombier, électricien, etc.)

#### Département
Liste dynamique des départements (ex: 77, 78, 91, etc.)

#### Note Google
- **Toutes** : Aucun filtre
- **4.5+** : Note supérieure ou égale à 4.5/5
- **4.0+** : Note supérieure ou égale à 4.0/5
- **3.5+** : Note supérieure ou égale à 3.5/5
- **< 3.5** : Note inférieure à 3.5/5

#### Nombre d'avis
- **Tous** : Aucun filtre
- **50+ avis** : Artisans avec beaucoup d'avis
- **20-50 avis** : Artisans avec un nombre moyen d'avis
- **10-20 avis** : Artisans avec peu d'avis
- **< 10 avis** : Artisans avec très peu d'avis

#### Statut message
- **Tous** : Affiche tous les artisans
- **Non contactés uniquement** : Artisans qui n'ont jamais reçu de message
- **Déjà contactés** : Artisans qui ont déjà reçu un message

## 🚀 Génération des messages

### Étape 1 : Filtrer les artisans

Utilisez les filtres dans la sidebar pour sélectionner les artisans que vous souhaitez contacter.

### Étape 2 : Préparer les messages

Cliquez sur le bouton **"🚀 Préparer les messages"**. Le système va :

1. **Analyser chaque artisan** selon les critères suivants :
   - Type de téléphone (mobile vs fixe)
   - Type de site web (Facebook, Instagram, site classique, aucun)
   - Note Google et nombre d'avis
   - Présence d'un prénom dans le nom de l'entreprise

2. **Sélectionner automatiquement le meilleur template** selon les données disponibles

3. **Générer le message personnalisé** en remplaçant les variables :
   - `{salutation}` → "Bonjour" ou "Bonjour [Prénom]" si détecté
   - `{ville}` → Ville de l'artisan
   - `{metier}` → Type d'artisan (plombier, électricien, etc.)
   - `{note}` → Note Google Maps
   - `{nombre_avis}` → Nombre d'avis Google Maps
   - `{site_web}` → URL du site actuel (si existe)

4. **Générer le lien WhatsApp** (uniquement pour les numéros mobiles 06/07)

### Étape 3 : Consulter et modifier les messages

Une fois les messages préparés, chaque artisan apparaît dans une **card expandable** avec :

- **Informations de l'artisan** :
  - Nom de l'entreprise
  - Téléphone formaté (ex: "06 12 34 56 78")
  - Badge de catégorie : 🟢 WhatsApp / 🟡 Cold Call / 🔴 Invalide
  - Ville et département
  - Note Google et nombre d'avis
  - Type de site web détecté
  - Template utilisé
  - Prénom détecté (si trouvé)

- **Message généré** :
  - Zone de texte éditable pour modifier le message si besoin
  - Le message est pré-rempli avec le template sélectionné

- **Actions disponibles** :
  - **📲 Ouvrir WhatsApp** : Lien cliquable qui ouvre WhatsApp avec le message pré-rempli (uniquement pour numéros mobiles)
  - **💡 Aide copie** : Instructions pour copier le message (Ctrl+A puis Ctrl+C)
  - **✅ Marquer comme envoyé** : Met à jour la base de données pour indiquer que le message a été envoyé

## 📋 Templates de messages

Le système utilise 5 templates différents, sélectionnés automatiquement selon les données :

### Template 1 : Pas de site web (Priorité: 100)
**Condition** : Artisan sans site web

**Message** :
```
Bonjour [Prénom],

Je crée des sites web pour les artisans [métier]s autour de [ville].

Un site simple mais efficace qui vous ramène des clients via Google.

Ça vous intéresse d'en discuter 2 min ?
```

### Template 2 : Site Facebook/Instagram (Priorité: 90)
**Condition** : Artisan avec page Facebook ou Instagram

**Message** :
```
Bonjour [Prénom],

J'ai vu votre page sur les réseaux.

Je crée des sites pro pour artisans — ça aide à apparaître sur Google quand les gens cherchent "[métier] [ville]".

Ça pourrait vous intéresser ?
```

### Template 3 : Site web existant (Priorité: 80)
**Condition** : Artisan avec site web classique

**Message** :
```
Bonjour [Prénom],

J'ai vu votre site en cherchant un [métier] vers [ville].

Je refais des sites pour artisans avec un design moderne et optimisé pour Google. Souvent ça double les appels entrants.

Vous seriez ouvert à un avis gratuit sur votre site actuel ?
```

### Template 4 : Bonus excellente note (Priorité: 70)
**Condition** : Note >= 4.5 ET nombre d'avis >= 10

**Ligne bonus** (ajoutée aux templates précédents) :
```
Félicitations pour vos [nombre_avis] avis et votre note de [note]/5 👏
```

### Template 5 : Fallback générique (Priorité: 10)
**Condition** : Toujours (si aucun autre template ne correspond)

**Message** :
```
Bonjour [Prénom],

Je crée des sites web pour artisans.

Un site bien fait = plus de clients via Google.

Intéressé d'en parler rapidement ?
```

## 🔍 Détection automatique

### Détection du prénom

Le système analyse le nom de l'entreprise pour détecter un prénom (ex: "Jean Dupont Plomberie" → prénom "Jean" détecté). Si un prénom est trouvé, la salutation devient "Bonjour Jean" au lieu de "Bonjour".

### Détection du type de site

Le système détecte automatiquement :
- **Facebook** : Si l'URL contient "facebook.com" ou "fb.me"
- **Instagram** : Si l'URL contient "instagram.com"
- **LinkedIn** : Si l'URL contient "linkedin.com"
- **Site web classique** : Toute autre URL valide
- **Aucun** : Pas de site web

### Catégorisation des téléphones

- **🟢 WhatsApp** : Numéros mobiles (06, 07) → Lien WhatsApp généré
- **🟡 Cold Call** : Numéros fixes (01-05) → Pas de lien WhatsApp (appel téléphonique nécessaire)
- **🔴 Invalide** : Numéro invalide ou manquant

## 📊 Statistiques

En haut de la page, vous voyez :
- **Total artisans** : Nombre total d'artisans dans la base
- **Avec WhatsApp** : Nombre d'artisans avec numéro mobile (06/07)
- **Déjà contactés** : Nombre d'artisans marqués comme "message envoyé"

## 📥 Export CSV

Un bouton **"📥 Exporter en CSV"** permet d'exporter tous les messages préparés dans un fichier CSV avec :
- ID de l'artisan
- Nom de l'entreprise
- Téléphone formaté
- Catégorie (WhatsApp/Cold Call/Invalide)
- Ville et département
- Template utilisé
- Message généré
- Lien WhatsApp (si disponible)

## 💡 Bonnes pratiques

### Timing d'envoi

- **Meilleurs moments** : 8h-9h30 et 17h-19h en semaine
- **À éviter** : Week-end, jours fériés, pause déjeuner (12h-14h)

### Personnalisation

- Vous pouvez **modifier le message** avant de l'envoyer dans la zone de texte
- Le lien WhatsApp sera automatiquement mis à jour avec le message modifié

### Suivi

- **Marquez comme envoyé** après avoir envoyé le message pour éviter les doublons
- Le compteur "Messages envoyés cette session" vous aide à suivre votre progression

### Workflow recommandé

1. **Filtrer** les artisans selon vos critères (ex: WhatsApp uniquement, non contactés, département 77)
2. **Préparer les messages** pour voir les messages générés
3. **Parcourir** les messages un par un dans les cards expandables
4. **Modifier** si besoin le message pour le personnaliser davantage
5. **Cliquer** sur "Ouvrir WhatsApp" pour envoyer
6. **Marquer comme envoyé** après chaque envoi

## ⚠️ Limitations

- **Pas d'envoi automatisé** : Les messages doivent être envoyés manuellement via WhatsApp (pour éviter les risques de ban)
- **Pas de vérification WhatsApp** : Le système ne vérifie pas si le numéro a réellement WhatsApp (pas de solution gratuite fiable)
- **Liens WhatsApp uniquement pour mobiles** : Les numéros fixes (01-05) ne génèrent pas de lien WhatsApp

## 🔧 Dépannage

### "0 artisan(s) correspondent aux filtres"
- Vérifiez que vous avez des données dans la base (import depuis GitHub Actions ou scraping)
- Assouplissez les filtres (sélectionnez "Tous" pour chaque critère)

### "WhatsApp non disponible (numéro fixe)"
- Normal pour les numéros commençant par 01-05
- Ces numéros nécessitent un appel téléphonique (Cold Call)

### Message non généré
- Vérifiez que l'artisan a au moins un téléphone et un nom d'entreprise
- Le template fallback devrait toujours générer un message

## 📝 Notes techniques

- Les messages sont stockés dans `st.session_state` pour éviter de les regénérer à chaque interaction
- La pagination affiche 20 artisans par page si plus de 20 résultats
- Les colonnes `phone_type` et `site_type` sont automatiquement remplies lors de la migration ou du scraping

---

**Besoin d'aide ?** Consultez le code source dans `whatsapp_app/pages/3_💬_Messages_WhatsApp.py` ou les modules dans le dossier `whatsapp/`.

