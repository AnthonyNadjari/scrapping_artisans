# 📧 Système de Prospection par Cold Email pour Artisans

Système complet de prospection par cold email pour des artisans français, avec scraping multi-sources, gestion de base de données, génération d'emails personnalisés, tracking et synchronisation Gmail.

## 🚀 Fonctionnalités

### ✅ Scraping Multi-Sources
- **Google Maps** : Scraping via Playwright
- **Base SIRENE** : API publique pour données entreprises
- **Pages Jaunes** : (À implémenter)
- **118712** : (À implémenter)

### ✅ Base de Données
- SQLite avec schéma complet
- Gestion intelligente des doublons
- Index optimisés pour performance
- Filtres avancés et recherche

### ✅ Emails
- Génération personnalisée avec IA (optionnel)
- Templates HTML responsive
- Envoi SMTP Gmail
- Pixel tracking des ouvertures
- Gestion de campagnes

### ✅ Tracking & Analytics
- Suivi des ouvertures d'emails
- Détection des réponses
- Analytics détaillées (métier, géographie, temps)
- Graphiques interactifs Plotly

### ✅ Synchronisation Gmail
- Lecture IMAP de la boîte de réception
- Détection automatique des réponses
- Analyse de sentiment basique
- Sync automatique (optionnel)

## 📦 Installation

### Prérequis
- Python 3.8+
- Gmail avec App Password configuré

### Étapes

1. **Cloner le projet**
```bash
git clone <repo>
cd scrapping_artisans
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Installer Playwright**
```bash
playwright install chromium
```

4. **Initialiser la base de données**
```bash
python database/models.py
```

5. **Configurer Gmail** (optionnel pour commencer)
- Créer un App Password : https://myaccount.google.com/apppasswords
- Configurer dans l'interface Streamlit (page Paramètres)

6. **Lancer l'application**
```bash
streamlit run app/Accueil.py
```

L'application sera accessible sur `http://localhost:8501`

## 🎯 Utilisation

### 1. Scraping d'Artisans

1. Aller sur la page **🔍 Scraping**
2. Sélectionner les sources (Google Maps recommandé)
3. Choisir les départements et métiers
4. Prioriser les petites communes (< 5,000 hab)
5. Cliquer sur **LANCER LE SCRAPING**

Le scraping affiche la progression en temps réel avec :
- Nombre d'artisans trouvés
- Communes scrapées
- Doublons évités
- Logs détaillés

### 2. Consultation Base de Données

1. Aller sur **📊 Base de Données**
2. Utiliser les filtres (métier, département, statut)
3. Sélectionner des artisans
4. Actions disponibles :
   - Enrichir les emails
   - Préparer une campagne
   - Exporter en CSV

### 3. Créer une Campagne

1. Aller sur **✉️ Campagnes**
2. Créer une nouvelle campagne :
   - Nom de la campagne
   - Métiers et départements ciblés
   - Paramètres d'envoi (emails/jour, délai)
3. Lancer l'envoi par batch

### 4. Analytics

1. Aller sur **📈 Analytics**
2. Consulter les performances :
   - Taux d'ouverture et de réponse
   - Performance par métier/département
   - Funnel de conversion

### 5. Configuration

1. Aller sur **⚙️ Paramètres**
2. Configurer Gmail :
   - Adresse email
   - App Password
   - Tester l'envoi
3. Activer la sync automatique (optionnel)

## 📁 Structure du Projet

```
scrapping_artisans/
├── app/
│   ├── Accueil.py                 # Page principale
│   └── pages/
│       ├── 1_🔍_Scraping.py
│       ├── 2_📊_Base_de_Données.py
│       ├── 3_✉️_Campagnes.py
│       ├── 4_📈_Analytics.py
│       └── 5_⚙️_Paramètres.py
│
├── scraping/
│   ├── google_maps_scraper.py
│   ├── sirene_api.py
│   └── scraper_manager.py
│
├── database/
│   ├── models.py
│   └── queries.py
│
├── emails/
│   ├── generator.py
│   ├── sender.py
│   └── tracker.py
│
├── enrichment/
│   └── email_finder.py
│
├── sync/
│   └── gmail_sync.py
│
├── config/
│   ├── settings.py
│   └── gmail_config.json (créé après config)
│
├── data/
│   └── artisans.db (créé automatiquement)
│
├── requirements.txt
└── README.md
```

## ⚙️ Configuration

### Variables d'environnement (optionnel)

Créer un fichier `.env` :
```
GMAIL_EMAIL=votre-email@gmail.com
GMAIL_APP_PASSWORD=votre-app-password
OPENAI_API_KEY=votre-clé-openai (optionnel, pour génération IA)
SIRENE_API_KEY=votre-clé-sirene (optionnel)
```

### App Password Gmail

1. Aller sur https://myaccount.google.com/apppasswords
2. Sélectionner "Mail" et "Autre (nom personnalisé)"
3. Entrer "Streamlit App"
4. Copier le mot de passe généré (16 caractères)
5. L'utiliser dans la page Paramètres

## 🔒 Sécurité

- ⚠️ **Ne jamais commit** les fichiers de configuration avec mots de passe
- Le fichier `config/gmail_config.json` est dans `.gitignore`
- Utiliser des App Passwords, jamais le mot de passe principal
- Respecter les limites d'envoi pour éviter les bans

## 📊 Métiers Supportés

50+ métiers d'artisans :
- Plomberie & Chauffage
- Électricité
- Maçonnerie
- Menuiserie & Charpente
- Peinture & Finitions
- Carrelage
- Couverture
- Isolation
- Serrurerie
- Vitrerie
- Paysagisme
- Et plus...

## 🎯 Départements Prioritaires

Par défaut, focus sur les départements proches de Paris :
- 77 (Seine-et-Marne)
- 78 (Yvelines)
- 91 (Essonne)
- 95 (Val-d'Oise)
- 60 (Oise)
- 89 (Yonne)
- 45 (Loiret)
- 28 (Eure-et-Loir)

## 🐛 Dépannage

### Erreur Playwright
```bash
playwright install chromium
```

### Erreur Gmail SMTP
- Vérifier l'App Password
- Activer "Accès moins sécurisé" (déconseillé, utiliser App Password)
- Vérifier le firewall

### Base de données verrouillée
- Fermer toutes les connexions
- Redémarrer l'application

## 📝 Notes

- Le scraping Google Maps peut être ralenti par les protections anti-bot
- Respecter les rate limits des APIs
- Tester avec peu d'artisans avant de lancer une grande campagne
- Les pixels de tracking nécessitent un serveur Flask (à implémenter)

## 🚧 Améliorations Futures

- [ ] Implémenter Pages Jaunes scraper
- [ ] Implémenter 118712 scraper
- [ ] Serveur Flask pour tracking pixels
- [ ] Export Excel avancé
- [ ] Templates d'emails personnalisables dans l'UI
- [ ] A/B testing des emails
- [ ] Intégration CRM
- [ ] Webhooks pour notifications

## 📄 Licence

Ce projet est fourni "tel quel" pour usage personnel/professionnel.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des issues ou des pull requests.

---

**Bon scraping ! 🚀**

