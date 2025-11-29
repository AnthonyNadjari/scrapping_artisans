# Prompt pour l'implémentation des fonctionnalités WhatsApp

## Contexte du projet

Je développe une application Streamlit pour scraper des données d'artisans depuis Google Maps et gérer l'envoi de messages WhatsApp personnalisés. 

### État actuel du projet

**Partie 1 - Scraping (TERMINÉE ✅)**
- Scraping Google Maps via GitHub Actions (multi-thread)
- Extraction des données : nom, téléphone, site web, adresse, code postal, ville, département, note Google, nombre d'avis
- Base de données SQLite locale avec toutes les données scrapées
- Interface Streamlit avec 2 onglets :
  - **Onglet 1 "Scraping"** : Configuration et lancement des scrapings via GitHub Actions, suivi des workflows
  - **Onglet 2 "Base de Données"** : Visualisation des données scrapées (tableau, carte, filtres, export CSV)

**Partie 2 - Messages WhatsApp (À IMPLÉMENTER 🚧)**
- Créer un **3ème onglet "Messages WhatsApp"** dans Streamlit
- Gérer l'envoi de messages personnalisés aux artisans scrapés

### Structure de la base de données

Table `artisans` avec les champs suivants :
- `id` (INTEGER PRIMARY KEY)
- `nom_entreprise` (TEXT) - Nom de l'entreprise/artisan
- `telephone` (TEXT) - Numéro de téléphone (format: "06 12 34 56 78" ou "+33612345678")
- `site_web` (TEXT) - URL du site web (peut être Facebook, Instagram, site web classique, ou NULL)
- `adresse` (TEXT) - Adresse complète
- `code_postal` (TEXT) - Code postal (5 chiffres)
- `ville` (TEXT) - Ville
- `departement` (TEXT) - Département (2 chiffres)
- `ville_recherche` (TEXT) - Ville utilisée pour la recherche Google Maps
- `type_artisan` (TEXT) - Métier (ex: "plombier", "électricien")
- `note` (REAL) - Note Google Maps (ex: 4.8)
- `nombre_avis` (INTEGER) - Nombre d'avis Google Maps
- `message_envoye` (INTEGER DEFAULT 0) - Flag si message envoyé
- `a_repondu` (INTEGER DEFAULT 0) - Flag si a répondu
- `created_at` (TEXT) - Date de création

## Fonctionnalités à implémenter

### 1. Catégorisation automatique

**1.1 - Cold Call**
- Si le téléphone commence par `01` → Catégoriser comme "Cold Call"
- Afficher ces artisans dans une section dédiée

**1.2 - Analyse des données disponibles**
- **Type d'entreprise** : Détecter si `nom_entreprise` contient un nom/prénom (entreprise individuelle) ou un nom d'entreprise
- **Type de site web** : Analyser `site_web` pour détecter :
  - Site web classique (ex: `https://www.exemple.fr`)
  - Facebook (ex: `https://www.facebook.com/...`)
  - Instagram (ex: `https://www.instagram.com/...`)
  - Autres réseaux sociaux
  - NULL (pas de site web)
- **Note Google** : Utiliser `note` et `nombre_avis` pour personnaliser le message
- **Ville** : Utiliser `ville` ou `ville_recherche` pour personnaliser (ex: "je cherchais un plombier vers [ville]")

### 2. Système de templates de messages

**2.1 - Templates multiples**
Créer plusieurs templates de messages en fonction des données disponibles :

- **Template pour entreprise avec site web classique** :
  - Mentionner qu'on peut améliorer/remplacer leur site actuel
  - Exemple : "Je vois que vous avez déjà un site web. Je peux vous proposer une version moderne et optimisée..."

- **Template pour Facebook/Instagram** :
  - Proposer de remplacer par un vrai site web professionnel
  - Exemple : "Je vois que vous utilisez Facebook/Instagram. Un site web professionnel pourrait améliorer votre visibilité..."

- **Template pour pas de site web** :
  - Proposer la création d'un site web
  - Exemple : "Je crée des sites professionnels pour artisans..."

- **Template avec note positive** :
  - Utiliser la note Google pour renforcer la crédibilité
  - Exemple : "Félicitations pour votre note de {note}/5 avec {nombre_avis} avis ! Un site web pourrait encore améliorer votre visibilité..."

- **Template avec ville** :
  - Personnaliser avec la ville
  - Exemple : "Je cherchais un {metier} vers {ville} et j'ai trouvé votre entreprise..."

**2.2 - Variables disponibles dans les templates**
- `{nom}` - Nom de l'entreprise
- `{prenom}` - Prénom (si détecté dans nom_entreprise)
- `{entreprise}` - Nom de l'entreprise
- `{ville}` - Ville
- `{metier}` - Type d'artisan (plombier, électricien, etc.)
- `{note}` - Note Google Maps
- `{nombre_avis}` - Nombre d'avis Google Maps
- `{site_web}` - Site web actuel (si existe)

### 3. Interface de filtrage et préparation

**3.1 - Filtres avancés**
- Filtrer par :
  - Type de téléphone (Cold Call 01 vs autres)
  - Type de site web (Facebook, Instagram, site classique, aucun)
  - Type d'entreprise (nom/prénom vs entreprise)
  - Note Google (positive >= 4.5, moyenne 3.5-4.5, faible < 3.5)
  - Nombre d'avis (beaucoup >= 50, moyen 10-50, peu < 10)
  - Département
  - Métier
  - Message déjà envoyé ou non

**3.2 - Préparation des messages**
- Bouton "Préparer les messages" qui :
  - Filtre les artisans selon les critères sélectionnés
  - Sélectionne automatiquement le meilleur template selon les données disponibles
  - Génère les messages personnalisés pour chaque artisan
  - Affiche un aperçu des messages avant envoi

### 4. Vérification WhatsApp

**4.1 - Détection WhatsApp**
- Trouver un moyen de vérifier si un numéro de téléphone a WhatsApp
- Options possibles :
  - API WhatsApp Business (si disponible)
  - Bibliothèque Python pour vérifier (ex: `pywhatkit`, `whatsapp-web.js`)
  - Vérification via numéro international formaté
  - Utiliser l'API officielle WhatsApp Business si possible

**4.2 - Affichage du statut**
- Afficher un indicateur visuel (✅/❌) si le numéro a WhatsApp
- Filtrer pour n'afficher que les numéros avec WhatsApp

### 5. Liens WhatsApp Business

**5.1 - Format des liens**
- Générer des liens WhatsApp Business (pas WhatsApp classique)
- Format attendu : `https://wa.me/33612345678?text=...` ou format WhatsApp Business API
- Encoder correctement le message dans l'URL

**5.2 - Intégration**
- Remplacer les liens WhatsApp classiques par des liens WhatsApp Business
- S'assurer que les liens fonctionnent correctement

## Questions pour l'implémentation

1. **Architecture** : Quelle est la meilleure structure pour organiser le code ?
   - Créer un nouveau fichier `whatsapp_app/pages/3_💬_Messages_WhatsApp.py` ?
   - Créer un module `whatsapp/message_manager.py` pour la logique métier ?
   - Comment structurer les templates (fichier JSON, classe Python, base de données) ?

2. **Détection WhatsApp** : Quelle est la meilleure méthode pour vérifier si un numéro a WhatsApp ?
   - API officielle WhatsApp Business ?
   - Bibliothèque tierce ?
   - Vérification manuelle via interface web ?

3. **Templates** : Comment gérer les templates de manière flexible ?
   - Fichier JSON/YAML pour faciliter l'édition ?
   - Interface dans Streamlit pour créer/modifier les templates ?
   - Système de règles pour sélectionner automatiquement le bon template ?

4. **Personnalisation** : Comment détecter intelligemment :
   - Si `nom_entreprise` contient un prénom/nom (ex: "Jean Dupont Plomberie" vs "Plomberie Solution") ?
   - Le type de site web (Facebook, Instagram, site classique) ?

5. **Envoi en masse** : Comment gérer l'envoi de nombreux messages ?
   - Limite de taux (rate limiting) ?
   - Queue système ?
   - Suivi de l'état d'envoi ?

6. **WhatsApp Business** : Quelle est la différence entre WhatsApp et WhatsApp Business pour les liens ?
   - Les liens `wa.me` fonctionnent-ils pour WhatsApp Business ?
   - Faut-il utiliser l'API WhatsApp Business officielle ?

## Innovations supplémentaires

En plus des fonctionnalités demandées, proposez d'autres idées d'innovation pour améliorer le système :
- Automatisation de l'envoi
- Suivi des réponses
- Analytics et statistiques
- A/B testing des messages
- Intégration avec d'autres canaux (SMS, email)
- Système de scoring pour prioriser les contacts
- etc.

## Contraintes techniques

- **Framework** : Streamlit (Python)
- **Base de données** : SQLite
- **Déploiement** : Application locale (pas de serveur dédié)
- **Budget** : Solutions gratuites ou low-cost de préférence
- **Conformité** : Respecter les règles anti-spam et RGPD

---

**Merci de fournir :**
1. Une architecture détaillée pour implémenter ces fonctionnalités
2. Des exemples de code pour les parties critiques
3. Des recommandations sur les bibliothèques/APIs à utiliser
4. Des idées d'innovation supplémentaires
5. Un plan d'implémentation étape par étape
6. ton avis sur ca avant de tout implementer.

