from flask import Blueprint, render_template
from flask_login import login_required
from services.spotify_oauth import get_playlist_tracks
from services.comparison import compare_playlists
import logging

# Crea un Blueprint per la sezione di confronto delle playlist
compare_bp = Blueprint('compare', __name__)

@compare_bp.route('/compare/<playlist1_id>/<playlist2_id>')
@login_required  # Richiede che l'utente sia autenticato
def compare(playlist1_id, playlist2_id):
    try:
        # Ottiene i dati di confronto tra le due playlist usando un servizio esterno
        comparison_data = compare_playlists(playlist1_id, playlist2_id)

        # Renderizza il template con i dati del confronto (nomi playlist e grafici)
        return render_template('comparison.html', 
                               playlist1_name=comparison_data['playlist1_name'],
                               playlist2_name=comparison_data['playlist2_name'],
                               charts=comparison_data['charts'])
    except Exception as e:
        # In caso di errore, registra il problema nei log e mostra una pagina di errore
        logging.error(f"Errore durante il confronto delle playlist: {e}")
        return render_template('error.html', error="Impossibile confrontare le playlist")
