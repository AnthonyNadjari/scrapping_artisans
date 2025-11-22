"""
Système de tracking des ouvertures d'emails
"""
import hashlib
import uuid

def generer_tracking_pixel(tracking_id: str) -> str:
    """
    Génère le code HTML d'un pixel de tracking
    """
    # URL du serveur de tracking (Flask en parallèle)
    tracking_url = f"http://localhost:8501/track/{tracking_id}.gif"
    
    pixel_html = f'''
    <img src="{tracking_url}" 
         width="1" height="1" 
         style="display:none; visibility:hidden;" 
         alt="" />
    '''
    
    return pixel_html

def generer_tracking_id(artisan_id: int) -> str:
    """Génère un ID de tracking unique"""
    return hashlib.md5(
        f"{artisan_id}{uuid.uuid4()}".encode()
    ).hexdigest()

