"""
Requêtes SQL pour la base de données WhatsApp
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from whatsapp_database.models import get_connection

def formater_telephone_fr(telephone: str) -> str:
    """
    Convertit un numéro français vers format international
    06 12 34 56 78 -> +33612345678
    """
    # Nettoyer le numéro
    tel_clean = ''.join(filter(str.isdigit, telephone))
    
    # Si commence par 0, remplacer par +33
    if tel_clean.startswith('0'):
        tel_clean = '+33' + tel_clean[1:]
    elif not tel_clean.startswith('+33'):
        # Si pas de préfixe, ajouter +33
        if len(tel_clean) == 10:
            tel_clean = '+33' + tel_clean
    
    return tel_clean

def ajouter_artisan(data: Dict) -> int:
    """
    Ajoute un artisan ou met à jour si doublon (par téléphone ou SIRET)
    Retourne l'ID de l'artisan
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Formater le téléphone si présent
    if data.get('telephone'):
        data['telephone_formate'] = formater_telephone_fr(data['telephone'])
    
    # Vérifier doublon par téléphone (si téléphone présent)
    existing_id = None
    if data.get('telephone'):
        cursor.execute("SELECT id FROM artisans WHERE telephone = ?", (data['telephone'],))
        result = cursor.fetchone()
        if result:
            existing_id = result[0]
    
    # Vérifier doublon par SIRET (si SIRET présent et pas déjà trouvé par téléphone)
    if not existing_id and data.get('siret'):
        cursor.execute("SELECT id FROM artisans WHERE siret = ?", (data['siret'],))
        result = cursor.fetchone()
        if result:
            existing_id = result[0]
    
    if existing_id:
        # Mettre à jour l'artisan existant
        update_fields = []
        update_values = []
        
        for key, value in data.items():
            # Ne pas écraser les champs existants si la nouvelle valeur est vide
            # Sauf pour les champs qui peuvent être mis à jour (nom, prenom, adresse, etc.)
            if value is not None and value != '' and key not in ['id', 'created_at']:
                # Ne pas écraser un téléphone existant si le nouveau est vide
                if key == 'telephone' and not value:
                    continue
                update_fields.append(f"{key} = ?")
                update_values.append(value)
        
        if update_fields:
            update_values.append(existing_id)
            query = f"UPDATE artisans SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        return existing_id
    else:
        # Nouvel artisan
        data['created_at'] = datetime.now().isoformat()
        
        # Filtrer les champs None ou vides pour éviter erreurs
        fields = []
        values = []
        for key, value in data.items():
            if value is not None and value != '':
                fields.append(key)
                values.append(value)
        
        if not fields:
            conn.close()
            raise ValueError("Aucune donnée valide à insérer")
        
        placeholders = ', '.join(['?' for _ in fields])
        query = f"INSERT INTO artisans ({', '.join(fields)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, values)
            artisan_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return artisan_id
        except sqlite3.IntegrityError as e:
            conn.close()
            # Si erreur d'intégrité (doublon), essayer de récupérer l'ID existant
            if 'telephone' in str(e).lower() or 'unique' in str(e).lower():
                # Réessayer avec recherche de doublon
                if data.get('telephone'):
                    cursor2 = conn.cursor()
                    cursor2.execute("SELECT id FROM artisans WHERE telephone = ?", (data['telephone'],))
                    result = cursor2.fetchone()
                    if result:
                        return result[0]
            raise

def get_artisans(filtres: Optional[Dict] = None, limit: int = 10000) -> List[Dict]:
    """Récupère les artisans avec filtres optionnels"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM artisans WHERE 1=1"
    params = []
    
    if filtres:
        if filtres.get('metiers'):
            query += " AND type_artisan IN (" + ','.join(['?' for _ in filtres['metiers']]) + ")"
            params.extend(filtres['metiers'])
        
        if filtres.get('departements'):
            query += " AND departement IN (" + ','.join(['?' for _ in filtres['departements']]) + ")"
            params.extend(filtres['departements'])
        
        if filtres.get('a_whatsapp') is not None:
            query += " AND a_whatsapp = ?"
            params.append(1 if filtres['a_whatsapp'] else 0)
        
        if filtres.get('non_contactes'):
            query += " AND message_envoye = 0"
        
        if filtres.get('message_envoye'):
            query += " AND message_envoye = 1"
        
        if filtres.get('a_repondu'):
            query += " AND a_repondu = 1"
        
        if filtres.get('statut_reponse'):
            query += " AND statut_reponse = ?"
            params.append(filtres['statut_reponse'])
        
        if filtres.get('exclude_statuts'):
            placeholders = ','.join(['?' for _ in filtres['exclude_statuts']])
            query += f" AND (statut_reponse NOT IN ({placeholders}) OR statut_reponse IS NULL)"
            params.extend(filtres['exclude_statuts'])
        
        if filtres.get('recherche'):
            query += " AND (nom_entreprise LIKE ? OR nom LIKE ? OR prenom LIKE ? OR ville LIKE ? OR telephone LIKE ?)"
            search_term = f"%{filtres['recherche']}%"
            params.extend([search_term, search_term, search_term, search_term, search_term])
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in rows]

def mark_scraping_done(metier: str, departement: str, ville: str, results_count: int = 0):
    """Marque une combinaison métier/département/ville comme scrapée"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO scraping_history (metier, departement, ville, scraped_at, results_count)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (metier, departement, ville, results_count))
        conn.commit()
    except Exception as e:
        print(f"Erreur marquage scraping: {e}")
    finally:
        conn.close()

def is_already_scraped(metier: str, departement: str, ville: str) -> bool:
    """Vérifie si une combinaison métier/département/ville a déjà été scrapée"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM scraping_history
            WHERE metier = ? AND departement = ? AND ville = ?
        """, (metier, departement, ville))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()

def get_scraping_history(metier: str = None, departement: str = None) -> List[Dict]:
    """Récupère l'historique des scrapings"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM scraping_history WHERE 1=1"
    params = []
    
    if metier:
        query += " AND metier = ?"
        params.append(metier)
    
    if departement:
        query += " AND departement = ?"
        params.append(departement)
    
    query += " ORDER BY scraped_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_statistiques() -> Dict:
    """Retourne les statistiques globales"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM artisans")
    stats['total'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE telephone IS NOT NULL AND telephone != ''")
    stats['avec_telephone'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE telephone IS NOT NULL AND telephone != ''")
    stats['avec_telephone'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE a_whatsapp = 1")
    stats['avec_whatsapp'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE message_envoye = 1")
    stats['messages_envoyes'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE a_repondu = 1")
    stats['repondus'] = cursor.fetchone()[0]
    
    # Sites web (si la colonne existe)
    try:
        cursor.execute("SELECT COUNT(*) FROM artisans WHERE site_web IS NOT NULL AND site_web != ''")
        stats['avec_site_web'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM artisans WHERE (site_web IS NULL OR site_web = '') AND telephone IS NOT NULL")
        stats['sans_site_web'] = cursor.fetchone()[0]
    except:
        stats['avec_site_web'] = 0
        stats['sans_site_web'] = 0
    
    # Messages envoyés aujourd'hui
    cursor.execute("""
        SELECT COUNT(*) FROM artisans 
        WHERE message_envoye = 1 
        AND date(date_envoi) = date('now')
    """)
    stats['messages_aujourdhui'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def marquer_whatsapp_verifie(artisan_id: int, a_whatsapp: bool):
    """Marque un artisan comme vérifié sur WhatsApp"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE artisans 
        SET a_whatsapp = ?, date_verification_whatsapp = ?
        WHERE id = ?
    """, (1 if a_whatsapp else 0, now, artisan_id))
    
    conn.commit()
    conn.close()

def marquer_message_envoye(artisan_id: int, message_id: str):
    """Marque un message comme envoyé"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE artisans 
        SET message_envoye = 1, date_envoi = ?
        WHERE id = ?
    """, (now, artisan_id))
    
    cursor.execute("""
        INSERT INTO messages_log (artisan_id, date_envoi, message_id, statut)
        VALUES (?, ?, ?, 'envoye')
    """, (artisan_id, now, message_id))
    
    conn.commit()
    conn.close()

def sauvegarder_reponse(artisan_id: int, contenu: str, message_id: str):
    """Sauvegarde une réponse WhatsApp"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO reponses (artisan_id, date_reception, contenu, message_id)
        VALUES (?, ?, ?, ?)
    """, (artisan_id, now, contenu, message_id))
    
    cursor.execute("""
        UPDATE artisans 
        SET a_repondu = 1, date_reponse = ?, derniere_reponse = ?
        WHERE id = ?
    """, (now, contenu, artisan_id))
    
    conn.commit()
    conn.close()

def get_artisan_par_telephone(telephone: str) -> Optional[Dict]:
    """Récupère un artisan par son téléphone"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM artisans WHERE telephone = ? OR telephone_formate = ?", 
                   (telephone, telephone))
    row = cursor.fetchone()
    
    conn.close()
    return dict(row) if row else None

