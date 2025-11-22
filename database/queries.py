"""
Requêtes SQL pour la base de données
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from database.models import get_connection

def ajouter_artisan(data: Dict) -> int:
    """
    Ajoute un artisan ou met à jour si doublon
    Retourne l'ID de l'artisan
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Vérifier doublon par téléphone ou email
    doublon_id = None
    
    if data.get('telephone'):
        cursor.execute("SELECT id FROM artisans WHERE telephone = ?", (data['telephone'],))
        result = cursor.fetchone()
        if result:
            doublon_id = result[0]
    
    if not doublon_id and data.get('email'):
        cursor.execute("SELECT id FROM artisans WHERE email = ?", (data['email'],))
        result = cursor.fetchone()
        if result:
            doublon_id = result[0]
    
    if doublon_id:
        # Mettre à jour l'artisan existant (garder les meilleures infos)
        update_fields = []
        update_values = []
        
        for key, value in data.items():
            if value and key != 'id':
                # Si la valeur existante est vide, on la remplace
                cursor.execute(f"SELECT {key} FROM artisans WHERE id = ?", (doublon_id,))
                existing = cursor.fetchone()
                if not existing[0] or (value and len(str(value)) > len(str(existing[0]))):
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
        
        if update_fields:
            update_values.append(datetime.now().isoformat())
            update_values.append(doublon_id)
            query = f"UPDATE artisans SET {', '.join(update_fields)}, derniere_mise_a_jour = ? WHERE id = ?"
            cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        return doublon_id
    else:
        # Nouvel artisan
        data['date_scrape'] = datetime.now().isoformat()
        data['derniere_mise_a_jour'] = datetime.now().isoformat()
        
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in fields])
        
        query = f"INSERT INTO artisans ({', '.join(fields)}) VALUES ({placeholders})"
        cursor.execute(query, values)
        
        artisan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return artisan_id

def get_artisans(filtres: Optional[Dict] = None, limit: int = 1000) -> List[Dict]:
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
        
        if filtres.get('statut'):
            query += " AND statut = ?"
            params.append(filtres['statut'])
        
        if filtres.get('a_email'):
            query += " AND email IS NOT NULL AND email != ''"
        
        if filtres.get('a_site_web'):
            query += " AND a_site_web = 1"
        
        if filtres.get('recherche'):
            query += " AND (nom_entreprise LIKE ? OR ville LIKE ? OR telephone LIKE ?)"
            search_term = f"%{filtres['recherche']}%"
            params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
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
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE email IS NOT NULL AND email != ''")
    stats['avec_email'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE statut = 'non_contacte'")
    stats['non_contactes'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE a_repondu = 1")
    stats['repondus'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE email_envoye = 1")
    stats['emails_envoyes'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE email_ouvert = 1")
    stats['emails_ouverts'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def get_metiers_uniques() -> List[str]:
    """Retourne la liste des métiers uniques"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT type_artisan FROM artisans WHERE type_artisan IS NOT NULL ORDER BY type_artisan")
    result = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return result

def get_departements_uniques() -> List[str]:
    """Retourne la liste des départements uniques"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT departement FROM artisans WHERE departement IS NOT NULL ORDER BY departement")
    result = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return result

def marquer_email_envoye(artisan_id: int, message_id: str, objet: str, contenu: str):
    """Marque un email comme envoyé"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE artisans 
        SET email_envoye = 1, date_envoi = ?, statut = 'email_envoye'
        WHERE id = ?
    """, (now, artisan_id))
    
    cursor.execute("""
        INSERT INTO emails_log (artisan_id, date_envoi, objet, contenu, statut, message_id)
        VALUES (?, ?, ?, ?, 'envoye', ?)
    """, (artisan_id, now, objet, contenu, message_id))
    
    conn.commit()
    conn.close()

def marquer_email_ouvert(tracking_id: str):
    """Marque un email comme ouvert via tracking pixel"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Trouver l'artisan via tracking_id
    cursor.execute("SELECT artisan_id FROM tracking_pixels WHERE tracking_id = ?", (tracking_id,))
    result = cursor.fetchone()
    
    if result:
        artisan_id = result[0]
        now = datetime.now().isoformat()
        
        # Vérifier si première ouverture
        cursor.execute("SELECT email_ouvert FROM artisans WHERE id = ?", (artisan_id,))
        deja_ouvert = cursor.fetchone()[0]
        
        if not deja_ouvert:
            cursor.execute("""
                UPDATE artisans 
                SET email_ouvert = 1, 
                    date_premiere_ouverture = ?,
                    nombre_ouvertures = 1,
                    date_derniere_ouverture = ?,
                    statut = 'ouvert'
                WHERE id = ?
            """, (now, now, artisan_id))
        else:
            cursor.execute("""
                UPDATE artisans 
                SET nombre_ouvertures = nombre_ouvertures + 1,
                    date_derniere_ouverture = ?
                WHERE id = ?
            """, (now, artisan_id))
        
        # Mettre à jour tracking_pixels
        cursor.execute("""
            UPDATE tracking_pixels 
            SET ouvert = 1, date_ouverture = ?
            WHERE tracking_id = ?
        """, (now, tracking_id))
        
        conn.commit()
    
    conn.close()

def sauvegarder_reponse(artisan_id: int, sujet: str, contenu: str, date_reponse: str, sentiment: str = 'neutre'):
    """Sauvegarde une réponse d'email"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO reponses_emails (artisan_id, date_reponse, sujet, contenu, sentiment)
        VALUES (?, ?, ?, ?, ?)
    """, (artisan_id, date_reponse, sujet, contenu, sentiment))
    
    cursor.execute("""
        UPDATE artisans 
        SET a_repondu = 1, date_reponse = ?, statut = 'repondu'
        WHERE id = ?
    """, (date_reponse, artisan_id))
    
    conn.commit()
    conn.close()

def creer_tracking_pixel(artisan_id: int, tracking_id: str):
    """Crée un pixel de tracking"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tracking_pixels (artisan_id, tracking_id)
        VALUES (?, ?)
    """, (artisan_id, tracking_id))
    
    conn.commit()
    conn.close()

def get_artisan(artisan_id: int) -> Optional[Dict]:
    """Récupère un artisan par ID"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM artisans WHERE id = ?", (artisan_id,))
    row = cursor.fetchone()
    
    conn.close()
    if row:
        return dict(row)
    return None

