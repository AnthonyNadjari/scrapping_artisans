# 📁 Structure Complète du Projet

## Vue d'ensemble

```
scrapping_artisans/
│
├── 📱 APP STREAMLIT
│   ├── app/
│   │   ├── Accueil.py              # Page d'accueil principale
│   │   ├── pages/
│   │   │   ├── 1_🔍_Scraping.py    # Interface de scraping
│   │   │   ├── 2_📊_Base_de_Données.py  # Consultation BDD
│   │   │   ├── 3_✉️_Campagnes.py   # Gestion campagnes
│   │   │   ├── 4_📈_Analytics.py   # Statistiques
│   │   │   └── 5_⚙️_Paramètres.py  # Configuration
│   │   └── __init__.py
│
├── 🕷️ SCRAPING
│   ├── scraping/
│   │   ├── google_maps_scraper.py  # Scraper Google Maps (Playwright)
│   │   ├── sirene_api.py           # API Base SIRENE
│   │   ├── scraper_manager.py      # Orchestrateur principal
│   │   └── __init__.py
│
├── 🗄️ BASE DE DONNÉES
│   ├── database/
│   │   ├── models.py               # Schéma SQLite + init
│   │   ├── queries.py              # Requêtes SQL
│   │   └── __init__.py
│   └── data/
│       ├── artisans.db             # Base SQLite (créée auto)
│       └── metiers.json            # Liste des métiers
│
├── 📧 EMAILS
│   ├── emails/
│   │   ├── generator.py             # Génération emails personnalisés
│   │   ├── sender.py                # Envoi SMTP Gmail
│   │   ├── tracker.py               # Génération pixels tracking
│   │   └── __init__.py
│
├── 🔍 ENRICHISSEMENT
│   ├── enrichment/
│   │   ├── email_finder.py          # Trouver emails sur sites web
│   │   └── __init__.py
│
├── 🔄 SYNCHRONISATION
│   ├── sync/
│   │   ├── gmail_sync.py           # Sync Gmail IMAP
│   │   └── __init__.py
│
├── ⚙️ CONFIGURATION
│   ├── config/
│   │   ├── settings.py             # Configuration globale
│   │   ├── gmail_config.json       # Config Gmail (créé après config)
│   │   └── __init__.py
│
├── 📊 TRACKING
│   └── tracking_server.py          # Serveur Flask pour pixels (optionnel)
│
├── 📄 DOCUMENTATION
│   ├── README.md                   # Documentation principale
│   ├── INSTALLATION.md             # Guide d'installation
│   └── STRUCTURE.md                # Ce fichier
│
├── 🚀 SCRIPTS
│   ├── run.sh                      # Script lancement Linux/Mac
│   ├── run.bat                     # Script lancement Windows
│   └── requirements.txt            # Dépendances Python
│
└── 🔒 SÉCURITÉ
    └── .gitignore                  # Fichiers à ignorer (configs sensibles)
```

## Description des Modules

### 🎯 App Streamlit (`app/`)

Interface utilisateur complète avec 5 pages :

1. **Accueil** : Dashboard principal avec stats globales
2. **Scraping** : Interface de scraping avec feedback temps réel
3. **Base de Données** : Consultation, filtres, export
4. **Campagnes** : Création et gestion de campagnes d'emails
5. **Analytics** : Graphiques et statistiques de performance
6. **Paramètres** : Configuration Gmail, sync, templates

### 🕷️ Scraping (`scraping/`)

- **Google Maps Scraper** : Scraping via Playwright
- **SIRENE API** : Récupération données entreprises publiques
- **Scraper Manager** : Orchestration multi-sources avec anti-doublons

### 🗄️ Base de Données (`database/`)

- **Models** : Schéma SQLite complet (artisans, emails_log, reponses, tracking, campagnes)
- **Queries** : Fonctions CRUD avec gestion intelligente des doublons

### 📧 Emails (`emails/`)

- **Generator** : Génération emails HTML personnalisés (avec IA optionnel)
- **Sender** : Envoi SMTP Gmail avec gestion d'erreurs
- **Tracker** : Génération pixels de tracking uniques

### 🔍 Enrichissement (`enrichment/`)

- **Email Finder** : Extraction emails depuis sites web, patterns de devinette

### 🔄 Synchronisation (`sync/`)

- **Gmail Sync** : Lecture IMAP, détection réponses, analyse sentiment

### ⚙️ Configuration (`config/`)

- **Settings** : Métiers, départements, limites, APIs
- **Gmail Config** : Stockage sécurisé des credentials

## Flux de Données

```
1. SCRAPING
   └─> Google Maps / SIRENE
       └─> Scraper Manager
           └─> Base de Données (avec anti-doublons)

2. ENRICHISSEMENT
   └─> Email Finder
       └─> Base de Données (mise à jour emails)

3. CAMPAGNE
   └─> Sélection artisans
       └─> Email Generator
           └─> Email Sender
               └─> Gmail SMTP
                   └─> Tracking Pixel
                       └─> Base de Données (statut)

4. TRACKING
   └─> Pixel chargé (email ouvert)
       └─> Tracking Server
           └─> Base de Données (marquer ouvert)

5. SYNC GMAIL
   └─> IMAP Gmail
       └─> Détection réponses
           └─> Analyse sentiment
               └─> Base de Données (sauvegarder réponse)
```

## Fichiers Clés

### `database/models.py`
- Initialise toutes les tables SQLite
- Schéma complet avec index optimisés

### `scraping/scraper_manager.py`
- Orchestrateur principal du scraping
- Gestion des communes, métiers, départements
- Callbacks pour feedback temps réel

### `emails/generator.py`
- Template HTML responsive
- Génération personnalisée par artisan
- Support OpenAI (optionnel)

### `app/Accueil.py`
- Point d'entrée Streamlit
- Initialisation BDD
- Navigation vers pages

## Technologies Utilisées

- **Streamlit** : Interface utilisateur
- **Playwright** : Scraping Google Maps
- **SQLite** : Base de données
- **SMTP** : Envoi emails Gmail
- **IMAP** : Lecture boîte Gmail
- **Plotly** : Graphiques interactifs
- **BeautifulSoup** : Parsing HTML
- **Requests** : APIs HTTP

## Points d'Extension

### À Implémenter (Futur)

1. **Pages Jaunes Scraper** : `scraping/pages_jaunes_scraper.py`
2. **118712 Scraper** : `scraping/118712_scraper.py`
3. **Serveur Tracking Public** : Déploiement `tracking_server.py`
4. **Export Excel** : Fonctionnalité dans `database/queries.py`
5. **Templates UI** : Interface pour modifier templates dans Streamlit
6. **A/B Testing** : Système de test de variantes d'emails

## Sécurité

- ✅ Credentials Gmail dans `.gitignore`
- ✅ App Passwords (pas mots de passe principaux)
- ✅ Base de données locale (pas de cloud)
- ⚠️ Tracking pixels nécessitent serveur public (ngrok recommandé)

## Performance

- Index SQLite sur colonnes fréquemment filtrées
- Pagination des résultats (limite 1000)
- Rate limiting dans scrapers
- Cache Streamlit pour requêtes fréquentes

---

**Système complet et prêt à l'emploi ! 🚀**

