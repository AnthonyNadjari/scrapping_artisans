"""
Requêtes SQL pour la base de données WhatsApp
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from whatsapp_database.models import get_connection
import logging

logger = logging.getLogger(__name__)

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
            print(f"⚠️ ajouter_artisan: Aucune donnée valide à insérer. Données reçues: {data}")
            raise ValueError("Aucune donnée valide à insérer")
        
        placeholders = ', '.join(['?' for _ in fields])
        query = f"INSERT INTO artisans ({', '.join(fields)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, values)
            artisan_id = cursor.lastrowid
            conn.commit()
            conn.close()
            # ✅ Logs réduits - seulement en mode debug
            # print(f"✅ ajouter_artisan: Artisan inséré avec succès (ID: {artisan_id})")
            return artisan_id
        except sqlite3.IntegrityError as e:
            # Si erreur d'intégrité (doublon), essayer de récupérer l'ID existant
            if 'telephone' in str(e).lower() or 'unique' in str(e).lower():
                # Réessayer avec recherche de doublon
                if data.get('telephone'):
                    cursor.execute("SELECT id FROM artisans WHERE telephone = ?", (data['telephone'],))
                    result = cursor.fetchone()
                    if result:
                        conn.commit()
                        conn.close()
                        # ✅ Logs réduits - seulement en mode debug
                        # print(f"ℹ️ ajouter_artisan: Doublon trouvé (ID: {result[0]}) - Mise à jour effectuée")
                        return result[0]
            conn.close()
            print(f"❌ ajouter_artisan: Erreur intégrité: {e}")
            raise

def get_artisans(filtres: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
    """Récupère les artisans avec filtres optionnels
    
    Args:
        filtres: Dictionnaire de filtres optionnels
        limit: Limite du nombre de résultats (None = pas de limite)
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM artisans WHERE 1=1"
    params = []
    
    # Valider et nettoyer filtres - TOUS les paramètres doivent être validés
    if filtres and isinstance(filtres, dict):
        # Filtre par ID (prioritaire)
        if filtres.get('id'):
            try:
                artisan_id = int(filtres['id'])
                query += " AND id = ?"
                params.append(artisan_id)
                # Exécuter directement et retourner
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows]
            except:
                pass
        
        # Métiers
        metiers_raw = filtres.get('metiers')
        if metiers_raw:
            try:
                if isinstance(metiers_raw, list):
                    metiers_list = [str(m).strip() for m in metiers_raw if m and str(m).strip()]
                    if metiers_list:
                        query += " AND type_artisan IN (" + ','.join(['?' for _ in metiers_list]) + ")"
                        params.extend(metiers_list)
            except:
                pass
        
        # Départements
        depts_raw = filtres.get('departements')
        if depts_raw:
            try:
                if isinstance(depts_raw, list):
                    depts_list = [str(d).strip() for d in depts_raw if d and str(d).strip()]
                    if depts_list:
                        query += " AND departement IN (" + ','.join(['?' for _ in depts_list]) + ")"
                        params.extend(depts_list)
            except:
                pass
        
        # a_whatsapp (SQLite stocke BOOLEAN comme INTEGER: 0, 1, ou NULL)
        if 'a_whatsapp' in filtres and filtres['a_whatsapp'] is not None:
            try:
                # Convertir en entier (0 ou 1) de manière sûre
                a_whatsapp_raw = filtres['a_whatsapp']
                if isinstance(a_whatsapp_raw, bool):
                    a_whatsapp_val = 1 if a_whatsapp_raw else 0
                elif isinstance(a_whatsapp_raw, (int, float)):
                    a_whatsapp_val = 1 if int(a_whatsapp_raw) != 0 else 0
                elif isinstance(a_whatsapp_raw, str):
                    a_whatsapp_val = 1 if str(a_whatsapp_raw).lower() in ('true', '1', 'yes', 't') else 0
                else:
                    a_whatsapp_val = 1 if bool(a_whatsapp_raw) else 0
                
                # Utiliser CAST pour s'assurer que la comparaison fonctionne
                # S'assurer que a_whatsapp_val est bien un entier Python
                a_whatsapp_int = int(a_whatsapp_val) if not isinstance(a_whatsapp_val, int) else a_whatsapp_val
                query += " AND CAST(a_whatsapp AS INTEGER) = ?"
                params.append(a_whatsapp_int)
            except:
                # Ignorer silencieusement si conversion échoue
                pass
        
        # Flags booléens (pas de paramètres)
        if filtres.get('non_contactes'):
            query += " AND message_envoye = 0"
        
        if filtres.get('message_envoye'):
            query += " AND message_envoye = 1"
        
        if filtres.get('a_repondu'):
            query += " AND a_repondu = 1"
        
        # Statut réponse
        statut_raw = filtres.get('statut_reponse')
        if statut_raw:
            try:
                statut = str(statut_raw).strip()
                if statut:
                    query += " AND statut_reponse = ?"
                    params.append(statut)
            except:
                pass
        
        # Exclude statuts
        exclude_raw = filtres.get('exclude_statuts')
        if exclude_raw:
            try:
                if isinstance(exclude_raw, list):
                    exclude_list = [str(s).strip() for s in exclude_raw if s and str(s).strip()]
                    if exclude_list:
                        placeholders = ','.join(['?' for _ in exclude_list])
                        query += f" AND (statut_reponse NOT IN ({placeholders}) OR statut_reponse IS NULL)"
                        params.extend(exclude_list)
            except:
                pass
        
        # Recherche
        recherche_raw = filtres.get('recherche')
        if recherche_raw:
            try:
                if isinstance(recherche_raw, str):
                    recherche_str = recherche_raw.strip()
                elif isinstance(recherche_raw, (int, float)):
                    recherche_str = str(recherche_raw).strip()
                else:
                    recherche_str = ""
                
                if recherche_str:
                    query += " AND (nom_entreprise LIKE ? OR nom LIKE ? OR prenom LIKE ? OR ville LIKE ? OR telephone LIKE ?)"
                    search_term = f"%{recherche_str}%"
                    params.extend([search_term, search_term, search_term, search_term, search_term])
            except:
                pass
    
    query += " ORDER BY created_at DESC"
    if limit is not None:
        # S'assurer que limit est un entier
        try:
            limit_int = int(limit)
            if limit_int > 0:
                query += " LIMIT ?"
                params.append(limit_int)
        except (ValueError, TypeError):
            # Ignorer si limit n'est pas un entier valide
            pass
    
    # Exécuter la requête avec gestion d'erreur détaillée
    try:
        cursor.execute(query, params)
    except sqlite3.IntegrityError as e:
        # Log l'erreur pour debug
        error_msg = f"❌ IntegrityError SQL: {e}\n"
        error_msg += f"   Query: {query}\n"
        error_msg += f"   Params count: {len(params)}\n"
        error_msg += f"   Params: {params[:20]}\n"
        error_msg += f"   Params types: {[type(p).__name__ for p in params[:20]]}"
        logger.error(error_msg)
        # Re-lancer l'erreur pour que Streamlit la capture
        raise sqlite3.IntegrityError(f"Erreur SQL: {e}\nQuery: {query[:100]}...\nParams: {len(params)} paramètres")
    except sqlite3.OperationalError as e:
        # Log l'erreur pour debug
        error_msg = f"❌ OperationalError SQL: {e}\n"
        error_msg += f"   Query: {query}\n"
        error_msg += f"   Params count: {len(params)}"
        logger.error(error_msg)
        raise
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

def marquer_message_envoye(artisan_id: int, message_id: str = None):
    """
    Marque un message comme envoyé
    
    Args:
        artisan_id: ID de l'artisan
        message_id: ID du message (optionnel, par défaut généré automatiquement)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Générer un message_id si non fourni
    if not message_id:
        message_id = f"sms_{artisan_id}_{int(datetime.now().timestamp())}"
    
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

