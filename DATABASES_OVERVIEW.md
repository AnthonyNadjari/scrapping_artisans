# 📊 Vue d'ensemble des bases de données et fichiers de stockage

Ce document liste tous les fichiers de base de données et de stockage utilisés dans le projet.

## 🗄️ Base de données SQLite

### `data/whatsapp_artisans.db`

**Type** : Base de données SQLite principale  
**Chemin** : `data/whatsapp_artisans.db`  
**Définition** : `config/whatsapp_settings.py` → `DB_PATH`

**Tables contenues** :

1. **`artisans`** (table principale)
   - Données des artisans scrapés (nom, téléphone, adresse, etc.)
   - Colonnes principales :
     - `id` : Identifiant unique
     - `nom_entreprise`, `nom`, `prenom`
     - `type_artisan` : Métier (plombier, électricien, etc.)
     - `adresse`, `code_postal`, `ville`, `departement`
     - `telephone` : UNIQUE (évite les doublons)
     - `site_web` : URL du site web
     - `note` : Note Google Maps (0-5)
     - `nombre_avis` : Nombre d'avis Google Maps
     - `ville_recherche` : Ville utilisée pour la recherche
     - `source` : Source des données ('google_maps_github_actions', etc.)
     - `phone_type` : Type de téléphone ('mobile', 'landline', etc.)
     - `site_type` : Type de site ('facebook', 'instagram', 'classic', 'none')
     - `last_message_date` : Date du dernier message WhatsApp
     - `last_template_used` : Template de message utilisé
     - `message_envoye`, `a_repondu` : Statuts de campagne
     - `created_at` : Date de création

2. **`scraping_history`**
   - Historique des scrapings effectués
   - Évite les doublons (métier + département + ville)
   - Colonnes : `metier`, `departement`, `ville`, `scraped_at`, `results_count`

3. **`messages_log`**
   - Log des messages WhatsApp envoyés
   - Colonnes : `artisan_id`, `date_envoi`, `message_id`, `statut`, `erreur`

4. **`reponses`**
   - Réponses reçues des artisans
   - Colonnes : `artisan_id`, `date_reception`, `contenu`, `message_id`

**Initialisation** : `whatsapp_database/models.py` → `init_database()`

**Réinitialisation** : `scripts/reset_all_databases.py`

---

## 📄 Fichiers JSON de données

### 1. `data/scraping_results_github_actions.json`

**Type** : Résultats de scraping depuis GitHub Actions  
**Format** : Objet JSON `{"timestamp": "...", "total_results": N, "results": [...]}`  
**Utilisation** :
- **Sur GitHub Actions (runner)** : Mis à jour progressivement pendant le scraping (à chaque établissement trouvé)
- **Upload comme artifact** : Le fichier est uploadé comme artifact GitHub Actions à la fin du workflow (ligne 106-114 de `.github/workflows/scraping.yml`)
- **Local (Streamlit)** : Téléchargé depuis l'artifact GitHub Actions uniquement quand on clique sur "📥 Importer depuis GitHub Actions"
- **Import dans SQLite** : Les données sont importées dans la base SQLite locale uniquement lors de l'import manuel
- **Réinitialisé** : Liste vide `[]`

**⚠️ IMPORTANT** :
- ❌ **PAS de mise à jour en continu automatique** : La base SQLite locale n'est PAS mise à jour automatiquement pendant que le workflow tourne
- ❌ **PAS de transfert automatique** : Il faut cliquer manuellement sur "Importer depuis GitHub Actions" pour télécharger l'artifact et importer dans la base locale
- ✅ **Mise à jour progressive sur GitHub** : Le fichier JSON est mis à jour à chaque établissement trouvé dans le runner GitHub Actions
- ✅ **Base SQLite sur GitHub Actions** : Une base SQLite est aussi créée dans le runner GitHub Actions, mais elle n'est PAS accessible depuis Streamlit (elle est détruite à la fin du workflow)

**Fichiers utilisant ce fichier** :
- `scripts/run_scraping_github_actions.py` : Sauvegarde progressive pendant le scraping (ligne 222)
- `whatsapp_app/pages/2_📊_Base_de_Données.py` : Téléchargement et import depuis l'artifact GitHub Actions

---

### 2. `data/github_actions_status.json`

**Type** : Statut des workflows GitHub Actions  
**Format** : Objet JSON `{}`  
**Utilisation** :
- Stocke le statut des workflows GitHub Actions (en cours, terminés, etc.)
- Suivi des workflows actifs
- **Réinitialisé** : Objet vide `{}`

**Fichiers utilisant ce fichier** :
- `whatsapp_app/pages/1_🔍_Scraping.py` : Affichage du statut des workflows

---

### 3. `data/ville_dept_cache.json`

**Type** : Cache pour mapping ville → département  
**Format** : Objet JSON `{"ville": "departement", ...}`  
**Utilisation** :
- Cache les résultats des appels API `data.gouv.fr` pour éviter les appels répétés
- Accélère l'affichage des cartes
- **Non réinitialisé** : Cache persistant (peut être supprimé manuellement)

**Fichiers utilisant ce fichier** :
- `whatsapp_app/utils/map_utils.py` : Cache pour les cartes

---

### 4. `data/villes_par_departement.json`

**Type** : Liste des villes par département (fallback)  
**Format** : Objet JSON `{"77": ["ville1", "ville2", ...], ...}`  
**Utilisation** :
- Liste de secours si l'API `data.gouv.fr` n'est pas utilisée
- Utilisé uniquement si `use_api_communes = False`
- **Non réinitialisé** : Données statiques

**Fichiers utilisant ce fichier** :
- `whatsapp_app/pages/1_🔍_Scraping.py` : Liste des villes (mode non-API)
- `scripts/run_scraping_github_actions.py` : Liste des villes (mode non-API)

---

### 5. `data/codes_naf.json`

**Type** : Codes NAF (activités économiques)  
**Format** : Objet JSON  
**Utilisation** :
- Codes NAF pour catégoriser les artisans
- **Non réinitialisé** : Données statiques

---

### 6. `config/github_config.json`

**Type** : Configuration GitHub Actions  
**Format** : Objet JSON  
**Utilisation** :
- Configuration des workflows GitHub Actions
- Token GitHub, repository, etc.
- **Non réinitialisé** : Configuration

---

### 7. `config/api_config.json`

**Type** : Configuration API  
**Format** : Objet JSON  
**Utilisation** :
- Configuration des APIs externes (data.gouv.fr, etc.)
- **Non réinitialisé** : Configuration

---

## 🗑️ Fichiers JSON obsolètes (supprimés automatiquement)

Ces fichiers ne sont **plus utilisés** (vestiges du mode scraping local) et sont supprimés par `scripts/reset_all_databases.py` :

- `data/scraping_results_temp.json` ❌
- `data/scraping_status.json` ❌
- `data/scraping_checkpoint.json` ❌
- `data/scraping_logs.json` ❌
- `data/saved_count.json` ❌

---

## 📋 Résumé

| Fichier | Type | Réinitialisé ? | Utilisation principale |
|---------|------|----------------|------------------------|
| `data/whatsapp_artisans.db` | SQLite | ✅ Oui | Base de données principale (artisans, messages, etc.) |
| `data/scraping_results_github_actions.json` | JSON | ✅ Oui | Résultats temporaires GitHub Actions |
| `data/github_actions_status.json` | JSON | ✅ Oui | Statut workflows GitHub Actions |
| `data/ville_dept_cache.json` | JSON | ❌ Non | Cache ville→département (performance) |
| `data/villes_par_departement.json` | JSON | ❌ Non | Liste villes fallback (si API désactivée) |
| `data/codes_naf.json` | JSON | ❌ Non | Codes NAF (données statiques) |
| `config/github_config.json` | JSON | ❌ Non | Configuration GitHub |
| `config/api_config.json` | JSON | ❌ Non | Configuration API |

---

## 🔄 Flux de données GitHub Actions → Streamlit

### Pendant le scraping (sur GitHub Actions)

1. **Scraping en cours** :
   - Chaque établissement trouvé est sauvegardé dans :
     - ✅ **Base SQLite locale du runner** : `data/whatsapp_artisans.db` (via `ajouter_artisan()`)
     - ✅ **Fichier JSON** : `data/scraping_results_github_actions.json` (via `save_progress()`)
   - Les deux sont mis à jour **progressivement** à chaque établissement

2. **Fin du workflow** :
   - Le fichier JSON est **uploadé comme artifact** GitHub Actions (ligne 106-114 de `.github/workflows/scraping.yml`)
   - La base SQLite du runner est **détruite** (le runner est supprimé après le workflow)
   - ⚠️ **La base SQLite sur GitHub Actions n'est PAS accessible depuis Streamlit**

### Import dans Streamlit (local)

1. **Clic sur "📥 Importer depuis GitHub Actions"** :
   - Télécharge l'artifact `scraping-results` depuis GitHub Actions
   - Extrait `scraping_results_github_actions.json` depuis le ZIP
   - Parse le JSON et importe chaque artisan dans la **base SQLite locale** via `ajouter_artisan()`

2. **⚠️ IMPORTANT** :
   - ❌ **PAS de mise à jour automatique** : La base SQLite locale n'est PAS mise à jour pendant que le workflow tourne
   - ❌ **PAS de transfert en continu** : Il faut cliquer manuellement sur "Importer" pour récupérer les résultats
   - ✅ **Import manuel uniquement** : Les données sont importées uniquement quand vous cliquez sur le bouton d'import

### Résumé du flux

```
GitHub Actions Runner:
  └─ Scraping → save_callback() → Base SQLite (runner) + JSON (runner)
  └─ Fin workflow → Upload artifact (JSON uniquement)
  
Streamlit Local:
  └─ Clic "Importer" → Télécharge artifact → Parse JSON → Base SQLite (local)
```

---

## 🔄 Réinitialisation

Pour réinitialiser **toutes** les bases de données :

```bash
python scripts/reset_all_databases.py
```

Ou en mode non-interactif :

```bash
python scripts/reset_all_databases.py --force
```

**Ce qui est réinitialisé** :
- ✅ Base SQLite locale : Toutes les tables vidées
- ✅ `scraping_results_github_actions.json` local : Liste vide
- ✅ `github_actions_status.json` local : Objet vide
- ❌ Cache et fichiers de configuration : **Non réinitialisés**
- ⚠️ **Les artifacts GitHub Actions ne sont PAS supprimés** (ils expirent après 7 jours automatiquement)

---

## 📍 Emplacements

- **Base SQLite** : `data/whatsapp_artisans.db`
- **Fichiers JSON de données** : `data/*.json`
- **Fichiers de configuration** : `config/*.json`

---

## 🔍 Vérification

Pour voir le contenu de la base SQLite :

```bash
python scripts/analyze_database.py
```

Pour voir les fichiers JSON :

```bash
# Lister tous les fichiers JSON
ls -la data/*.json
ls -la config/*.json
```

