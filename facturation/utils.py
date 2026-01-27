"""
Utilitaires pour le module de facturation
"""
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import json


def get_config_dir():
    """Retourne le répertoire de configuration"""
    return Path(__file__).parent.parent / "data"


def get_excel_path():
    """Retourne le chemin du fichier Excel de facturation"""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)
    return config_dir / "factures.xlsx"


def get_invoices_dir():
    """Retourne le répertoire de stockage des PDF"""
    base_dir = Path(__file__).parent.parent
    invoices_dir = base_dir / "invoices"
    invoices_dir.mkdir(exist_ok=True)
    return invoices_dir


def init_excel_if_needed():
    """Initialise le fichier Excel s'il n'existe pas"""
    excel_path = get_excel_path()
    
    if not excel_path.exists():
        # Créer l'onglet FACTURES avec les colonnes requises
        factures_df = pd.DataFrame(columns=[
            'numero',
            'date_emission',
            'client_nom',
            'client_ref',
            'client_adresse',
            'client_email',
            'client_siret',
            'description',
            'quantite',
            'prix_unitaire',
            'montant',
            'statut',
            'chemin_pdf',
            'created_at',
            'locked'
        ])
        
        # Créer l'onglet CONFIG avec les valeurs par défaut hardcodées
        config_data = {
            'cle': [
                'entreprise_nom',
                'entreprise_adresse',
                'entreprise_siren',
                'entreprise_siret',
                'entreprise_tva',
                'representant_legal',
                'tva_mention',
                'conditions_paiement'
            ],
            'valeur': [
                'TOM&CO',
                '54 RUE DU MONT VALERIEN\n92210 SAINT-CLOUD',
                '945171288',
                '94517128800018',
                'FR79945171288',
                'MONSIEUR LUKSIC THOMAS',
                'TVA non applicable, art. 293 B du CGI',
                'Paiement à réception'
            ]
        }
        config_df = pd.DataFrame(config_data)
        
        # Écrire dans Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            factures_df.to_excel(writer, sheet_name='FACTURES', index=False)
            config_df.to_excel(writer, sheet_name='CONFIG', index=False)
        
        return True
    return False


def load_factures():
    """Charge toutes les factures depuis l'Excel"""
    excel_path = get_excel_path()
    
    if not excel_path.exists():
        init_excel_if_needed()
        return pd.DataFrame()
    
    try:
        # Lire l'Excel
        df = pd.read_excel(excel_path, sheet_name='FACTURES')
        
        # Debug: vérifier ce qui est chargé
        print(f"DEBUG: DataFrame chargé - Shape: {df.shape}, Colonnes: {list(df.columns)}")
        
        # Si le DataFrame est vide ou n'a que des colonnes sans données
        if df.empty or len(df) == 0:
            print("DEBUG: DataFrame vide après lecture")
            return pd.DataFrame()
        
        # Vérifier combien de lignes avant filtrage
        print(f"DEBUG: Nombre de lignes avant filtrage: {len(df)}")
        
        # S'assurer que les colonnes quantite et prix_unitaire existent (pour compatibilité avec anciennes factures)
        if 'quantite' not in df.columns:
            df['quantite'] = 1.0
        if 'prix_unitaire' not in df.columns:
            # Calculer le prix unitaire à partir du montant si disponible
            df['prix_unitaire'] = df.apply(
                lambda row: row.get('montant', 0.0) / row.get('quantite', 1.0) if row.get('quantite', 1.0) > 0 else row.get('montant', 0.0),
                axis=1
            )
        
        # Convertir les dates si présentes
        if 'date_emission' in df.columns and not df.empty:
            df['date_emission'] = pd.to_datetime(df['date_emission'], errors='coerce')
        if 'created_at' in df.columns and not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # Filtrer les lignes où le numéro est vide (lignes vides)
        if 'numero' in df.columns:
            before_filter = len(df)
            df = df[df['numero'].notna() & (df['numero'] != '')]
            after_filter = len(df)
            print(f"DEBUG: Après filtrage des numéros vides: {before_filter} -> {after_filter} lignes")
            if before_filter > after_filter:
                print(f"DEBUG: {before_filter - after_filter} lignes filtrées car numéro vide")
        
        print(f"DEBUG: DataFrame final - Shape: {df.shape}")
        return df
    except Exception as e:
        import traceback
        print(f"Erreur lors du chargement des factures: {e}")
        print(traceback.format_exc())
        return pd.DataFrame()


def save_facture(facture_data):
    """Sauvegarde une nouvelle facture dans l'Excel"""
    excel_path = get_excel_path()
    df = load_factures()
    
    # S'assurer que le DataFrame a les bonnes colonnes
    required_columns = [
        'numero', 'date_emission', 'client_nom', 'client_ref',
        'client_adresse', 'client_email', 'client_siret',
        'description', 'quantite', 'prix_unitaire', 'montant',
        'statut', 'chemin_pdf', 'created_at', 'locked'
    ]
    
    # Si le DataFrame est vide, créer avec les colonnes
    if df.empty:
        df = pd.DataFrame(columns=required_columns)
    else:
        # Ajouter les colonnes manquantes
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
    
    # Ajouter la nouvelle facture
    new_row = pd.DataFrame([facture_data])
    df = pd.concat([df, new_row], ignore_index=True)
    
    # Réécrire l'Excel en préservant les autres onglets
    try:
        # Charger la config si elle existe
        config_df = None
        try:
            config_df = pd.read_excel(excel_path, sheet_name='CONFIG')
        except:
            pass
        
        # Écrire avec ExcelWriter
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Écrire la config si elle existe
            if config_df is not None and not config_df.empty:
                config_df.to_excel(writer, sheet_name='CONFIG', index=False)
            else:
                # Créer la config par défaut si elle n'existe pas
                default_config = {
                    'cle': ['entreprise_nom', 'entreprise_adresse', 'entreprise_siren', 'entreprise_siret', 'entreprise_tva', 'representant_legal', 'tva_mention', 'conditions_paiement'],
                    'valeur': ['TOM&CO', '54 RUE DU MONT VALERIEN\n92210 SAINT-CLOUD', '945171288', '94517128800018', 'FR79945171288', 'MONSIEUR LUKSIC THOMAS', 'TVA non applicable, art. 293 B du CGI', 'Paiement à réception']
                }
                config_df = pd.DataFrame(default_config)
                config_df.to_excel(writer, sheet_name='CONFIG', index=False)
            
            # Écrire les factures
            df.to_excel(writer, sheet_name='FACTURES', index=False)
    except Exception as e:
        import traceback
        raise Exception(f"Erreur lors de la sauvegarde: {e}\n{traceback.format_exc()}")


def load_config():
    """Charge la configuration depuis l'Excel ou retourne les valeurs par défaut hardcodées"""
    excel_path = get_excel_path()
    
    # Configuration hardcodée de l'entreprise (depuis l'image fournie)
    default_config = {
        'entreprise_nom': 'TOM&CO',
        'entreprise_adresse': '54 RUE DU MONT VALERIEN\n92210 SAINT-CLOUD',
        'entreprise_siren': '945171288',
        'entreprise_siret': '94517128800018',
        'entreprise_tva': 'FR79945171288',
        'representant_legal': 'MONSIEUR LUKSIC THOMAS',
        'tva_mention': 'TVA non applicable, art. 293 B du CGI',
        'conditions_paiement': 'Paiement à réception'
    }
    
    if not excel_path.exists():
        init_excel_if_needed()
        # Sauvegarder la config par défaut
        save_config(default_config)
        return default_config
    
    try:
        df = pd.read_excel(excel_path, sheet_name='CONFIG')
        config = dict(zip(df['cle'], df['valeur']))
        # Merger avec les valeurs par défaut pour s'assurer qu'elles sont toujours présentes
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        return config
    except Exception as e:
        return default_config


def save_config(config_dict):
    """Sauvegarde la configuration dans l'Excel"""
    excel_path = get_excel_path()
    
    config_df = pd.DataFrame({
        'cle': list(config_dict.keys()),
        'valeur': list(config_dict.values())
    })
    
    # Réécrire en préservant l'onglet FACTURES
    try:
        factures_df = pd.read_excel(excel_path, sheet_name='FACTURES')
    except:
        factures_df = pd.DataFrame()
    
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        factures_df.to_excel(writer, sheet_name='FACTURES', index=False)
        config_df.to_excel(writer, sheet_name='CONFIG', index=False)


def generate_numero_facture():
    """
    Génère un numéro de facture unique au format YYYYMMDD-XXX
    Règles:
    - XXX est un compteur incrémental par jour
    - Le compteur redémarre à 001 chaque jour
    """
    df = load_factures()
    today = datetime.now().strftime('%Y%m%d')
    
    # Filtrer les factures du jour
    factures_aujourdhui = df[df['numero'].str.startswith(today, na=False)] if not df.empty and 'numero' in df.columns else pd.DataFrame()
    
    if factures_aujourdhui.empty:
        counter = 1
    else:
        # Extraire le dernier numéro de la journée
        max_numero = factures_aujourdhui['numero'].max()
        if pd.isna(max_numero):
            counter = 1
        else:
            try:
                # Extraire la partie XXX du format YYYYMMDD-XXX
                counter = int(max_numero.split('-')[1]) + 1
            except:
                counter = 1
    
    # Formater avec 3 chiffres
    numero = f"{today}-{counter:03d}"
    return numero


def is_facture_locked(numero):
    """Vérifie si une facture est verrouillée (locked = TRUE)"""
    df = load_factures()
    if df.empty:
        return False
    
    facture = df[df['numero'] == numero]
    if facture.empty:
        return False
    
    return facture.iloc[0]['locked'] == True or facture.iloc[0]['locked'] == 'TRUE'


def get_client_slug(client_nom):
    """Génère un slug pour le nom du client (pour les dossiers)"""
    import re
    slug = re.sub(r'[^\w\s-]', '', client_nom.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:50]  # Limiter la longueur

