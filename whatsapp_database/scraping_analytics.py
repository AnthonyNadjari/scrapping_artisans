"""
Module d'analytics pour le suivi des recherches de scraping
Fournit des métriques de couverture, sessions, et statistiques stratégiques
"""
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from whatsapp_database.models import get_connection
from whatsapp_database.queries import get_scraping_history
import requests


def get_coverage_metrics(metier: Optional[str] = None, departement: Optional[str] = None) -> Dict:
    """
    Calcule les métriques de couverture pour un métier/département
    
    Returns:
        Dict avec:
        - villes_scrapees: nombre de villes scrapées
        - villes_disponibles: nombre total de villes disponibles (via API)
        - taux_couverture: pourcentage de couverture
        - artisans_trouves: nombre total d'artisans trouvés
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer l'historique filtré
    historique = get_scraping_history(metier=metier, departement=departement)
    
    villes_scrapees = len(set((h['ville'], h.get('departement', '')) for h in historique))
    artisans_trouves = sum(h.get('results_count', 0) for h in historique)
    
    # Essayer de récupérer le nombre de villes disponibles via API
    villes_disponibles = None
    taux_couverture = None
    
    if departement:
        try:
            url = f"https://geo.api.gouv.fr/departements/{departement}/communes"
            params = {"fields": "nom,code", "format": "json"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                communes = response.json()
                villes_disponibles = len(communes)
                if villes_disponibles > 0:
                    taux_couverture = (villes_scrapees / villes_disponibles) * 100
        except:
            pass
    
    conn.close()
    
    return {
        'villes_scrapees': villes_scrapees,
        'villes_disponibles': villes_disponibles,
        'taux_couverture': taux_couverture,
        'artisans_trouves': artisans_trouves,
        'nombre_scrapings': len(historique)
    }


def get_metier_statistics() -> List[Dict]:
    """
    Retourne les statistiques par métier
    
    Returns:
        Liste de dicts avec: metier, departements_couverts, villes_scrapees, 
        artisans_trouves, taux_couverture_moyen
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer tous les métiers uniques
    cursor.execute("SELECT DISTINCT metier FROM scraping_history WHERE metier IS NOT NULL")
    metiers = [row[0] for row in cursor.fetchall()]
    
    stats_metiers = []
    
    for metier in metiers:
        historique = get_scraping_history(metier=metier)
        
        departements = set(h.get('departement', '') for h in historique if h.get('departement'))
        villes = set((h['ville'], h.get('departement', '')) for h in historique)
        artisans_trouves = sum(h.get('results_count', 0) for h in historique)
        
        # Calculer taux de couverture moyen par département
        taux_couverture_total = 0
        depts_avec_couverture = 0
        
        for dept in departements:
            coverage = get_coverage_metrics(metier=metier, departement=dept)
            if coverage['taux_couverture'] is not None:
                taux_couverture_total += coverage['taux_couverture']
                depts_avec_couverture += 1
        
        taux_couverture_moyen = (taux_couverture_total / depts_avec_couverture) if depts_avec_couverture > 0 else None
        
        stats_metiers.append({
            'metier': metier,
            'departements_couverts': len(departements),
            'villes_scrapees': len(villes),
            'artisans_trouves': artisans_trouves,
            'taux_couverture_moyen': taux_couverture_moyen,
            'nombre_scrapings': len(historique)
        })
    
    conn.close()
    return sorted(stats_metiers, key=lambda x: x['artisans_trouves'], reverse=True)


def get_departement_statistics(metier: Optional[str] = None) -> List[Dict]:
    """
    Retourne les statistiques par département
    
    Returns:
        Liste de dicts avec: departement, metiers_scrapes, villes_scrapees,
        artisans_trouves, taux_couverture
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Construire la requête
    query = "SELECT DISTINCT departement FROM scraping_history WHERE departement IS NOT NULL"
    params = []
    
    if metier:
        query += " AND metier = ?"
        params.append(metier)
    
    cursor.execute(query, params)
    departements = [row[0] for row in cursor.fetchall()]
    
    stats_departements = []
    
    for dept in departements:
        historique = get_scraping_history(departement=dept, metier=metier)
        
        metiers = set(h.get('metier', '') for h in historique if h.get('metier'))
        villes = set(h['ville'] for h in historique)
        artisans_trouves = sum(h.get('results_count', 0) for h in historique)
        
        # Calculer taux de couverture
        coverage = get_coverage_metrics(departement=dept, metier=metier)
        
        stats_departements.append({
            'departement': dept,
            'metiers_scrapes': len(metiers),
            'villes_scrapees': len(villes),
            'artisans_trouves': artisans_trouves,
            'taux_couverture': coverage['taux_couverture'],
            'villes_disponibles': coverage['villes_disponibles'],
            'nombre_scrapings': len(historique)
        })
    
    conn.close()
    return sorted(stats_departements, key=lambda x: x['artisans_trouves'], reverse=True)


def get_session_statistics(days: int = 30) -> List[Dict]:
    """
    Retourne les statistiques des sessions de scraping des N derniers jours
    
    Args:
        days: Nombre de jours à analyser (par défaut 30)
    
    Returns:
        Liste de dicts avec: date, nombre_sessions, villes_scrapees, 
        artisans_trouves, duree_moyenne
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    date_limit = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute("""
        SELECT 
            DATE(scraped_at) as date,
            COUNT(*) as nombre_scrapings,
            SUM(results_count) as artisans_trouves,
            COUNT(DISTINCT ville) as villes_scrapees,
            AVG(duration_seconds) as duree_moyenne
        FROM scraping_history
        WHERE scraped_at >= ?
        GROUP BY DATE(scraped_at)
        ORDER BY date DESC
    """, (date_limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_priority_suggestions(metier: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Suggère des départements/villes prioritaires à scraper
    
    Args:
        metier: Filtrer par métier (optionnel)
        limit: Nombre de suggestions à retourner
    
    Returns:
        Liste de dicts avec: departement, metier, villes_manquantes, 
        priorite_score
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer les départements déjà scrapés
    query = "SELECT DISTINCT departement, metier FROM scraping_history WHERE 1=1"
    params = []
    
    if metier:
        query += " AND metier = ?"
        params.append(metier)
    
    cursor.execute(query, params)
    scraped_combos = set((row[0], row[1]) for row in cursor.fetchall() if row[0] and row[1])
    
    suggestions = []
    
    # Pour chaque département scrapé, calculer le taux de couverture
    for dept, met in scraped_combos:
        coverage = get_coverage_metrics(metier=met, departement=dept)
        
        if coverage['taux_couverture'] is not None and coverage['taux_couverture'] < 80:
            # Département partiellement couvert - priorité moyenne
            suggestions.append({
                'departement': dept,
                'metier': met,
                'villes_manquantes': coverage.get('villes_disponibles', 0) - coverage['villes_scrapees'],
                'taux_couverture_actuel': coverage['taux_couverture'],
                'priorite_score': 50 + (100 - coverage['taux_couverture']) * 0.5,
                'raison': f"Couverture partielle ({coverage['taux_couverture']:.1f}%)"
            })
    
    conn.close()
    
    # Trier par score de priorité
    suggestions.sort(key=lambda x: x['priorite_score'], reverse=True)
    return suggestions[:limit]


def generate_research_report(metier: Optional[str] = None, 
                            departement: Optional[str] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> Dict:
    """
    Génère un rapport complet de recherche
    
    Args:
        metier: Filtrer par métier
        departement: Filtrer par département
        start_date: Date de début (format ISO)
        end_date: Date de fin (format ISO)
    
    Returns:
        Dict avec toutes les statistiques et métriques
    """
    historique = get_scraping_history(metier=metier, departement=departement)
    
    # Filtrer par dates si fournies
    if start_date or end_date:
        filtered = []
        for h in historique:
            scraped_at = h.get('scraped_at', '')
            if start_date and scraped_at < start_date:
                continue
            if end_date and scraped_at > end_date:
                continue
            filtered.append(h)
        historique = filtered
    
    # Statistiques générales
    total_scrapings = len(historique)
    total_artisans = sum(h.get('results_count', 0) for h in historique)
    villes_uniques = len(set((h['ville'], h.get('departement', '')) for h in historique))
    departements_uniques = len(set(h.get('departement', '') for h in historique if h.get('departement')))
    metiers_uniques = len(set(h.get('metier', '') for h in historique if h.get('metier')))
    
    # Statistiques par métier
    stats_metiers = get_metier_statistics() if not metier else []
    
    # Statistiques par département
    stats_departements = get_departement_statistics(metier=metier) if not departement else []
    
    # Sessions récentes
    sessions = get_session_statistics(days=30)
    
    # Suggestions
    suggestions = get_priority_suggestions(metier=metier, limit=5)
    
    return {
        'periode': {
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': datetime.now().isoformat()
        },
        'statistiques_generales': {
            'total_scrapings': total_scrapings,
            'total_artisans_trouves': total_artisans,
            'villes_scrapees': villes_uniques,
            'departements_couverts': departements_uniques,
            'metiers_scrapes': metiers_uniques,
            'artisans_moyen_par_scraping': total_artisans / total_scrapings if total_scrapings > 0 else 0
        },
        'statistiques_par_metier': stats_metiers,
        'statistiques_par_departement': stats_departements,
        'sessions_recentes': sessions,
        'suggestions_prioritaires': suggestions
    }
