"""
Utilitaires pour créer des cartes de scraping par métier
"""
import folium
from streamlit_folium import st_folium
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whatsapp_database.queries import get_artisans

# Coordonnées approximatives des départements français (centres)
DEPT_COORDS = {
    '01': (46.2, 5.2), '02': (49.4, 3.4), '03': (46.3, 3.1), '04': (44.1, 6.1), '05': (44.7, 6.1),
    '06': (43.7, 7.3), '07': (44.5, 4.4), '08': (49.8, 4.7), '09': (43.0, 1.6), '10': (48.3, 4.1),
    '11': (43.2, 2.4), '12': (44.3, 2.6), '13': (43.3, 5.4), '14': (49.2, -0.4), '15': (45.0, 2.4),
    '16': (45.6, 0.2), '17': (46.2, -1.2), '18': (47.1, 2.4), '19': (45.3, 1.8), '21': (47.3, 5.0),
    '22': (48.5, -2.8), '23': (46.2, 1.9), '24': (45.2, 0.7), '25': (47.2, 6.0), '26': (44.9, 4.9),
    '27': (49.1, 1.1), '28': (48.4, 1.5), '29': (48.4, -4.5), '30': (44.1, 4.1), '31': (43.6, 1.4),
    '32': (43.6, 0.6), '33': (44.8, -0.6), '34': (43.6, 3.9), '35': (48.1, -1.7), '36': (46.8, 1.7),
    '37': (47.4, 0.7), '38': (45.2, 5.7), '39': (46.7, 5.6), '40': (43.9, -0.5), '41': (47.6, 1.3),
    '42': (45.4, 4.4), '43': (45.0, 3.9), '44': (47.2, -1.6), '45': (47.9, 1.9), '46': (44.4, 1.4),
    '47': (44.2, 0.6), '48': (44.5, 3.5), '49': (47.5, -0.6), '50': (49.1, -1.1), '51': (49.3, 4.0),
    '52': (48.1, 5.1), '53': (48.1, -0.8), '54': (48.7, 6.2), '55': (49.1, 5.4), '56': (47.7, -2.8),
    '57': (49.1, 6.2), '58': (47.0, 3.4), '59': (50.6, 3.1), '60': (49.4, 2.8), '61': (48.4, 0.1),
    '62': (50.3, 2.8), '63': (45.8, 3.1), '64': (43.3, -0.4), '65': (43.2, 0.1), '66': (42.7, 2.9),
    '67': (48.6, 7.8), '68': (47.7, 7.3), '69': (45.8, 4.8), '70': (47.6, 6.2), '71': (46.8, 4.9),
    '72': (48.0, 0.2), '73': (45.6, 5.9), '74': (46.0, 6.1), '75': (48.9, 2.3), '76': (49.4, 1.1),
    '77': (48.6, 2.7), '78': (48.8, 2.1), '79': (46.3, -0.5), '80': (49.9, 2.3), '81': (43.6, 2.1),
    '82': (44.0, 1.4), '83': (43.1, 6.0), '84': (44.0, 5.0), '85': (46.7, -1.4), '86': (46.6, 0.3),
    '87': (45.8, 1.3), '88': (48.2, 6.5), '89': (47.8, 3.6), '90': (47.6, 6.9), '91': (48.6, 2.3),
    '92': (48.9, 2.2), '93': (48.9, 2.4), '94': (48.8, 2.4), '95': (49.1, 2.3)
}

def create_scraping_map_by_job(metier=None):
    """
    Crée une carte montrant les départements scrapés pour un métier donné.
    La taille des points est proportionnelle au nombre d'artisans scrapés.
    
    Args:
        metier: Nom du métier à filtrer (None pour tous les métiers)
    
    Returns:
        folium.Map: Carte Folium ou None si aucune donnée
    """
    # Récupérer les artisans
    artisans = get_artisans(limit=10000)
    
    # ✅ Filtrer par métier si spécifié (avec support pour None/vide)
    if metier and metier != "Tous":
        artisans = [a for a in artisans if a.get('type_artisan') and a.get('type_artisan') == metier]
    else:
        # Si "Tous", inclure tous les artisans qui ont un type_artisan
        artisans = [a for a in artisans if a.get('type_artisan')]
    
    if not artisans:
        return None
    
    # Grouper par département et compter
    dept_counts = {}
    for artisan in artisans:
        dept = artisan.get('departement', '')
        # ✅ Si pas de département, essayer d'extraire depuis code_postal
        if not dept and artisan.get('code_postal'):
            code_postal = str(artisan.get('code_postal', '')).strip()
            if len(code_postal) >= 2:
                if code_postal.startswith('97') or code_postal.startswith('98'):
                    dept = code_postal[:3]
                else:
                    dept = code_postal[:2]
        
        # ✅ Si toujours pas de département, utiliser ville_recherche pour trouver le département
        if not dept and artisan.get('ville_recherche'):
            # Essayer de trouver le département depuis la ville_recherche via l'API
            try:
                from whatsapp_app.pages import get_communes_from_api
                # Chercher dans tous les départements (pas optimal mais fonctionnel)
                for dept_test in ['77', '78', '91', '92', '93', '94', '95']:  # Départements courants
                    communes = get_communes_from_api(dept_test, 0, 1000000)
                    for commune in communes:
                        if commune['nom'].lower() == artisan.get('ville_recherche', '').lower():
                            dept = dept_test
                            break
                    if dept:
                        break
            except:
                pass
        
        if dept:
            if dept not in dept_counts:
                dept_counts[dept] = 0
            dept_counts[dept] += 1
    
    if not dept_counts:
        # ✅ Debug: retourner une carte vide avec un message plutôt que None
        m = folium.Map(location=[46.6, 2.2], zoom_start=6)
        return m
    
    # Créer la carte centrée sur la France
    m = folium.Map(location=[46.6, 2.2], zoom_start=6)
    
    # Calculer min/max pour normaliser les tailles
    counts = list(dept_counts.values())
    min_count = min(counts)
    max_count = max(counts)
    count_range = max_count - min_count if max_count > min_count else 1
    
    # Ajouter les marqueurs pour chaque département
    for dept, count in dept_counts.items():
        if dept in DEPT_COORDS:
            lat, lon = DEPT_COORDS[dept]
            
            # Taille proportionnelle (entre 5 et 25 pixels)
            if count_range > 0:
                normalized = (count - min_count) / count_range
                radius = 5 + (normalized * 20)  # Entre 5 et 25 pixels
            else:
                radius = 10
            
            # Couleur selon le nombre (vert = peu, rouge = beaucoup)
            if count >= 50:
                color = 'red'
            elif count >= 20:
                color = 'orange'
            elif count >= 10:
                color = 'yellow'
            else:
                color = 'green'
            
            # Popup avec informations
            popup_text = f"""
            <b>Département {dept}</b><br>
            <b>Métier:</b> {metier or 'Tous'}<br>
            <b>Artisans scrapés:</b> {count}
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_text, max_width=300),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"Dépt {dept}: {count} artisans"
            ).add_to(m)
    
    # Légende
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 140px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius:5px; padding: 10px">
    <b>Légende</b><br>
    <span style="color:red">●</span> ≥50 artisans<br>
    <span style="color:orange">●</span> 20-49 artisans<br>
    <span style="color:yellow">●</span> 10-19 artisans<br>
    <span style="color:green">●</span> <10 artisans<br>
    <small>Taille proportionnelle au nombre</small>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

