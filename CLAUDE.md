# Scrapping Artisans - Project Context

## Overview

This is a **lead generation pipeline** for artisan website sales in France. The system scrapes artisan businesses from Google Maps, manages outreach via WhatsApp, and generates custom websites for interested clients.

## Architecture

```
Google Maps Scraper → SQLite DB → WhatsApp Outreach → Google Form → Email
                                                                      ↓
                                            Website Generator ← Config Parser
                                                    ↓
                                            GitHub Repo → Vercel Deploy
```

## Directory Structure

```
scrapping_artisans/
├── config/                     # Configuration files
│   └── whatsapp_settings.py    # DB paths, trade types list
├── data/                       # Data storage
│   ├── whatsapp_artisans.db    # Main SQLite database
│   └── villes_par_departement.json
├── docs/                       # Documentation
│   └── Guide_Commercial_*.pdf  # Sales training PDF
├── scraping/                   # Web scraping modules
│   └── google_maps_scraper.py  # Main Google Maps scraper (Selenium)
├── scripts/                    # Automation scripts
│   └── run_scraping_github_actions.py  # GitHub Actions scraper
├── website_generator/          # Website generation module
│   ├── parser.py               # Email content parser
│   ├── config_generator.py     # TypeScript config generator
│   ├── deployer.py             # GitHub + Vercel deployment
│   └── trade_defaults.py       # Trade-specific defaults
├── whatsapp/                   # WhatsApp messaging
│   └── sms_providers.py        # SMS/WhatsApp providers
├── whatsapp_app/               # Streamlit UI
│   ├── app.py                  # Main Streamlit entry
│   └── pages/                  # Streamlit pages
│       ├── 1_🔍_Scraping.py
│       ├── 2_📊_Base_de_Données.py
│       ├── 3_📱_WhatsApp.py
│       ├── 4_📄_Facturation.py
│       └── 5_🌐_Generation_Site.py
└── whatsapp_database/          # Database layer
    ├── models.py               # SQLite schema & migrations
    └── queries.py              # Database queries
```

## Database Schema (artisans table)

Key columns:
- `id`, `nom_entreprise`, `telephone`, `site_web`, `google_maps_url`
- `adresse`, `code_postal`, `ville`, `departement`
- `note` (0-5), `nombre_avis`
- `type_artisan` (plombier, electricien, etc.)
- `ville_recherche`, `departement_recherche` (search context)
- `a_whatsapp`, `message_envoye`, `a_repondu`, `statut_reponse`
- `source` ('google_maps', 'sirene', 'pages_jaunes')

## Trade Types Supported

French artisan trades:
- plombier, chauffagiste, climatisation
- electricien, domotique
- macon, maconnerie
- menuisier, charpentier, ebeniste
- peintre, platrier
- carreleur, moquettiste
- couvreur, zingueur
- serrurier
- facade, isolation

## Key Technical Details

### Google Maps Scraper
- Uses Selenium with Chrome WebDriver
- Extracts: name, phone, website, address, rating, reviews, **Google Maps URL**
- Handles pagination and detail panels
- Anti-detection measures (random delays, user agents)

### Database
- SQLite with automatic migrations in `models.py`
- Dynamic field insertion in `queries.py` (handles new columns automatically)
- Deduplication by phone number and name+address hash

### Website Generator
- Template: React 18 + TypeScript + Vite + Tailwind CSS
- Config system: `artisan.config.ts` (single source of truth)
- Dynamic theming via CSS variables (HSL colors)
- Trade-specific defaults (icons, services, colors)
- Deployment: GitHub CLI (`gh`) + Vercel CLI

### Streamlit App
- Run with: `streamlit run whatsapp_app/app.py`
- Launch script: `launch_streamlit.bat`
- Older Streamlit version - some features need try/except wrappers

## Common Tasks

### Run Local Scraping
```bash
cd whatsapp_app
streamlit run app.py
# Navigate to Scraping page
```

### Run GitHub Actions Scraping
Set environment variables `METIERS` and `DEPARTEMENTS` as JSON arrays.

### Generate Website
1. Paste Google Form email in Generation Site page
2. Click "Analyser"
3. Review config
4. Click "Deployer" (requires `gh auth login` and `vercel login`)

### Reset Database
Delete `data/whatsapp_artisans.db` - it will be recreated on next run.

## Environment Requirements

- Python 3.8+ with packages: streamlit, selenium, pandas, openpyxl, fpdf2
- Node.js 18+ (for website generation)
- Chrome/Chromium (for Selenium)
- GitHub CLI (`gh`) - for repo creation
- Vercel CLI - for deployment

## Important Notes

1. **Phone numbers** are unique identifiers - duplicates are rejected
2. **Department** is extracted from postal code (2 first digits), not from search params
3. **Google Maps URL** is captured at scraping time for easy access to original listing
4. **Website template** is in separate repo: `plomberie-fluide-1`
5. **Streamlit compatibility** - use try/except for features like `disabled` param, `st.rerun()`

## Files Modified Recently

- `scraping/google_maps_scraper.py` - Added `google_maps_url` extraction
- `whatsapp_database/models.py` - Added `google_maps_url` column migration
- `whatsapp_app/pages/1_🔍_Scraping.py` - Display Google Maps URL
- `whatsapp_app/pages/2_📊_Base_de_Données.py` - Display Google Maps URL
- `scripts/run_scraping_github_actions.py` - Pass through Google Maps URL
- `website_generator/` - New module for automated website generation
- `docs/Guide_Commercial_Sites_Artisans.pdf` - Sales training document
