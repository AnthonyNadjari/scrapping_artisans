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
    Ajoute un artisan ou met à jour si doublon (par téléphone)
    Retourne l'ID de l'artisan
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Formater le téléphone
    if data.get('telephone'):
        data['telephone_formate'] = formater_telephone_fr(data['telephone'])
    
    # Vérifier doublon par téléphone
    cursor.execute("SELECT id FROM artisans WHERE telephone = ?", (data['telephone'],))
    result = cursor.fetchone()
    
    if result:
        # Mettre à jour l'artisan existant
        doublon_id = result[0]
        update_fields = []
        update_values = []
        
        for key, value in data.items():
            if value and key != 'id' and key != 'telephone':
                update_fields.append(f"{key} = ?")
                update_values.append(value)
        
        if update_fields:
            update_values.append(doublon_id)
            query = f"UPDATE artisans SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        return doublon_id
    else:
        # Nouvel artisan
        data['created_at'] = datetime.now().isoformat()
        
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in fields])
        
        query = f"INSERT INTO artisans ({', '.join(fields)}) VALUES ({placeholders})"
        cursor.execute(query, values)
        
        artisan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return artisan_id

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
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE telephone IS NOT NULL AND telephone != ''")
    stats['avec_telephone'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE a_whatsapp = 1")
    stats['avec_whatsapp'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE message_envoye = 1")
    stats['messages_envoyes'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM artisans WHERE a_repondu = 1")
    stats['repondus'] = cursor.fetchone()[0]
    
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

