from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from services.spotify_oauth import search_playlists, get_random_playlists
from services.analisi import analyze_and_visualize  

# Crea un Blueprint per le rotte della home
home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
@login_required  # L'accesso richiede che l'utente sia autenticato
def home():
    # Ottiene la query dalla barra di ricerca (se presente)
    query = request.args.get("query")
    
    # Se è presente una query, cerca playlist; altrimenti mostra playlist casuali
    playlists = search_playlists(query) if query else get_random_playlists()

    # Mostra la pagina home con il nome utente e le playlist trovate
    return render_template('home.html', username=current_user.username, playlists=playlists)

@home_bp.route('/playlist/<playlist_id>')
@login_required
def playlist(playlist_id):
    # Importazione locale per evitare dipendenze circolari
    from services.spotify_oauth import get_playlist_tracks

    # Recupera le tracce della playlist specificata
    tracks = get_playlist_tracks(playlist_id)
    
    # Se non ci sono tracce, mostra un messaggio di errore
    if not tracks:
        return render_template('playlist.html', error="Nessun brano trovato.", playlist_id=playlist_id)

    # Mostra la pagina della playlist con le tracce trovate
    return render_template('playlist.html', tracks=tracks, playlist_id=playlist_id)

@home_bp.route('/analisi/<playlist_id>')
@login_required
def analisi(playlist_id):
    # Analizza la playlist e genera i grafici/visualizzazioni
    charts = analyze_and_visualize(playlist_id)

    # Mostra la pagina di analisi con i grafici generati
    return render_template('analisi.html', charts=charts, playlist_id=playlist_id)
