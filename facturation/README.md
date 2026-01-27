# 📄 Module de Facturation

Système de facturation complet basé sur Excel comme source de vérité.

## 📋 Structure du Fichier Excel

Le fichier `data/factures.xlsx` contient deux onglets :

### Onglet FACTURES

| Colonne | Description | Type |
|---------|-------------|------|
| numero | Numéro de facture (YYYYMMDD-XXX) | String |
| date_emission | Date d'émission | Date |
| client_nom | Nom du client | String |
| client_ref | Référence client (pour pré-remplissage) | String |
| client_adresse | Adresse complète | String |
| client_email | Email | String |
| client_siret | SIRET | String |
| description | Description de la prestation | String |
| montant | Montant HT en euros | Float |
| statut | brouillon ou payee | String |
| chemin_pdf | Chemin relatif du PDF | String |
| created_at | Date de création | DateTime |
| locked | TRUE/FALSE (verrouillage) | Boolean |

### Onglet CONFIG

| Colonne | Description |
|---------|-------------|
| cle | Nom de la clé |
| valeur | Valeur associée |

Clés disponibles :
- `entreprise_nom`
- `entreprise_adresse`
- `entreprise_siren`
- `entreprise_siret`
- `tva_mention`
- `conditions_paiement`

## 🔢 Numérotation des Factures

Format : `YYYYMMDD-XXX`

Exemples :
- `20260116-001` (première facture du 16 janvier 2026)
- `20260116-002` (deuxième facture du même jour)
- `20260117-001` (première facture du 17 janvier 2026)

**Règles :**
- Le compteur redémarre à 001 chaque jour
- Basé uniquement sur les factures existantes dans l'Excel
- Automatique lors de la création

## 🔒 Système de Verrouillage

Une facture avec `locked = TRUE` :
- ✅ Ne peut plus être modifiée via l'interface
- ✅ Est considérée comme émise définitivement
- ✅ Statut automatiquement mis à "payee" lors du verrouillage

Pour déverrouiller, utiliser le bouton "🔓 Déverrouiller" (modification manuelle de l'Excel possible).

## 📂 Organisation des PDF

Les PDF sont organisés ainsi :

```
invoices/
└── année/
    └── client_slug/
        └── numero_facture_description.pdf
```

Exemple :
```
invoices/
└── 2026/
    └── plomberie-martin/
        └── 20260116-001_Reparation_fuite_urgence.pdf
```

## 🚀 Utilisation

1. **Configuration initiale** : Remplir les informations de l'entreprise dans la sidebar
2. **Créer une facture** :
   - Sélectionner un client (pré-remplissage automatique)
   - Remplir description et montant
   - Cliquer sur "Générer la facture"
3. **Gérer les factures** :
   - Filtrer par client, statut, date
   - Télécharger les PDF
   - Modifier le statut (si non verrouillée)
   - Verrouiller/déverrouiller

## ⚙️ Fonctions Principales

### `utils.py`
- `init_excel_if_needed()` : Initialise le fichier Excel
- `load_factures()` : Charge toutes les factures
- `save_facture()` : Sauvegarde une nouvelle facture
- `generate_numero_facture()` : Génère le numéro unique
- `load_config()` / `save_config()` : Gestion de la configuration

### `pdf_generator.py`
- `generate_invoice_pdf()` : Génère le PDF de facture

### `streamlit_page.py`
- `render_facturation_page()` : Interface Streamlit complète

## 🛡️ Protections

1. **Validation** : Vérification des champs obligatoires
2. **Verrouillage** : Factures verrouillées non modifiables
3. **Numérotation unique** : Impossible d'avoir deux factures avec le même numéro
4. **Dates** : Conversion automatique des dates
5. **Chemins PDF** : Génération automatique des chemins uniques

## 📝 Notes Techniques

- Utilise `pandas` et `openpyxl` pour Excel
- Utilise `reportlab` pour les PDF
- Compatible avec la base de données clients existante (chargement optionnel)
- Aucune dépendance sur la structure de la BDD clients (fonctionne même sans)

