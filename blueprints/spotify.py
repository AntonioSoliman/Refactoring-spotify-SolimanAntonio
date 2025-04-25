from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from flask_login import login_required, current_user
from models import db, Playlist, UserPlaylist
from services.spotify_oauth import (
    get_playlist_tracks, get_user_playlists, 
    spotify_login as spotify_login_service, 
    get_spotify_auth
)
from services.analisi import analyze_and_visualize

# Crea un Blueprint per le rotte legate all'integrazione con Spotify
spotify_bp = Blueprint('spotify', __name__)

@spotify_bp.route('/spotify_login')
def spotify_login():
    # Avvia il processo di login con Spotify
    return spotify_login_service()

@spotify_bp.route('/spotify_logout')
def spotify_logout():
    # Rimuove il token dalla sessione e mostra un messaggio di successo
    session.pop("token_info", None)
    flash('Logout da Spotify effettuato con successo.', 'success')
    return redirect(url_for('home.home'))

@spotify_bp.route('/saved_playlists')
@login_required
def saved_playlists():
    # Controlla che l'utente sia autenticato (ridondante ma di sicurezza)
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Recupera le playlist salvate dall'utente nel database
    user_playlists = UserPlaylist.query.filter_by(user_id=current_user.id).all()
    public_playlists = []

    for up in user_playlists:
        playlist = Playlist.query.get(up.playlist_id)
        if playlist:
            # Aggiunge le playlist trovate all'elenco da mostrare
            public_playlists.append({
                'id': playlist.id,
                'name': playlist.name,
                'owner': playlist.owner,
                'image': playlist.image
            })
        else:
            # Rimuove eventuali riferimenti a playlist eliminate
            db.session.delete(up)
            db.session.commit()

    return render_template('saved_playlists.html', playlists=public_playlists)

@spotify_bp.route('/private_playlists')
@login_required
def private_playlists():
    # Verifica che ci sia un token Spotify valido nella sessione
    if 'token_info' not in session:
        flash('Devi effettuare il login con Spotify per visualizzare le playlist private.', 'warning')
        return redirect(url_for('spotify.spotify_login')) 

    # Recupera le playlist dell'utente da Spotify
    spotify_playlists = get_user_playlists()  
    return render_template('private_playlists.html', playlists=spotify_playlists)

@spotify_bp.route('/playlist/<playlist_id>')
def playlist(playlist_id):
    # Recupera le tracce della playlist da Spotify
    tracks = get_playlist_tracks(playlist_id)

    if not tracks:
        flash("Impossibile recuperare la playlist. Verifica il collegamento con Spotify.", "danger")
        return redirect(url_for('home.home'))

    # Analizza la playlist e genera i grafici
    charts = analyze_and_visualize(playlist_id)

    # Ottiene il nome utente, oppure "Ospite" se non autenticato
    username = current_user.username if current_user.is_authenticated else "Ospite"

    return render_template('playlist.html', username=username, tracks=tracks, charts=charts)

@spotify_bp.route('/save_playlist', methods=['POST'])
@login_required
def save_playlist():
    # Controllo di sicurezza (ridondante con @login_required)
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Recupera i dati della playlist dal form
    playlist_id = request.form.get('playlist_id')
    playlist_name = request.form.get('playlist_name')
    playlist_owner = request.form.get('playlist_owner')
    playlist_image = request.form.get('playlist_image')

    # Verifica se la playlist è già presente nel database
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        # Se non esiste, la crea
        playlist = Playlist(id=playlist_id, name=playlist_name, owner=playlist_owner, image=playlist_image)
        db.session.add(playlist)
        db.session.commit()

    # Verifica se la playlist è già stata salvata dall'utente
    user_playlist = UserPlaylist.query.filter_by(user_id=current_user.id, playlist_id=playlist_id).first()
    if not user_playlist:
        # Se non è ancora stata salvata, la associa all'utente
        user_playlist = UserPlaylist(user_id=current_user.id, playlist_id=playlist_id)
        db.session.add(user_playlist)
        db.session.commit()
        flash('Playlist salvata con successo!', 'success')
    else:
        flash('Hai già salvato questa playlist.', 'info')

    return redirect(url_for('home.home'))

@spotify_bp.route('/callback')
def spotify_callback():
    # Gestisce il callback dopo l'autenticazione Spotify
    auth_manager = get_spotify_auth()
    code = request.args.get("code")

    if not code:
        return "Errore: Codice di autorizzazione mancante.", 400

    try:
        # Scambia il codice per un token di accesso
        token_info = auth_manager.get_access_token(code)
        # Salva il token nella sessione
        session["token_info"] = token_info
        return redirect(url_for('home.home'))
    except Exception as e:
        return f"Errore durante il callback di Spotify: {e}", 500
