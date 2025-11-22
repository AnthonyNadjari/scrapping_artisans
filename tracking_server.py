"""
Serveur Flask pour le tracking des pixels d'ouverture d'emails
À lancer en parallèle de Streamlit pour tracker les ouvertures
"""
import io
from flask import Flask, send_file, request
from database.queries import marquer_email_ouvert
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Pixel transparent 1x1
PIXEL_GIF = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'

@app.route('/track/<tracking_id>.gif')
def track_open(tracking_id):
    """
    Endpoint appelé quand un email est ouvert
    Le pixel de tracking charge cette image
    """
    try:
        # Marquer comme ouvert dans la BDD
        marquer_email_ouvert(tracking_id)
        
        # Logger l'ouverture
        user_agent = request.headers.get('User-Agent', 'Unknown')
        ip_address = request.remote_addr
        
        logger.info(f"📧 Email ouvert - Tracking ID: {tracking_id} - IP: {ip_address}")
        
        # Retourner le pixel transparent
        return send_file(
            io.BytesIO(PIXEL_GIF),
            mimetype='image/gif',
            as_attachment=False
        )
    
    except Exception as e:
        logger.error(f"Erreur tracking: {e}")
        # Retourner quand même le pixel pour ne pas casser l'email
        return send_file(
            io.BytesIO(PIXEL_GIF),
            mimetype='image/gif'
        )

if __name__ == '__main__':
    logger.info("🚀 Serveur de tracking démarré sur http://localhost:8502")
    logger.info("⚠️ Assurez-vous que ce port est accessible depuis Internet pour le tracking")
    logger.info("💡 Pour un usage local, utilisez ngrok ou un service similaire")
    app.run(host='0.0.0.0', port=8502, debug=False)

