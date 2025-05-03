
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from flask import session, redirect, url_for, request, render_template
import random
import logging

SPOTIFY_CLIENT_ID = "ef05fc98d68d46298e93a2da2b717946"
SPOTIFY_CLIENT_SECRET = "15e5ce3c623e41b09b85c37d125d2021"
SPOTIFY_REDIRECT_URI = "https://redesigned-halibut-4jj747wpjjx9fw7-5000.app.github.dev/callback"
SCOPE = "user-read-private playlist-read-private playlist-read-collaborative"

# Setup logging
logging.basicConfig(level=logging.INFO)

# Inizializza autenticazione OAuth
def get_spotify_auth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )

# Ottieni client Spotify autenticato
def get_spotify_client():
    token_info = session.get("token_info")
    if token_info:
        auth_manager = get_spotify_auth()
        # Controlla se il token è scaduto
        if auth_manager.is_token_expired(token_info):
            logging.info("Token scaduto, aggiornamento in corso...")
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            session["token_info"] = token_info
        return spotipy.Spotify(auth=token_info.get("access_token"))
    
    # Se l'utente non è loggato, usa autenticazione base
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

# Ricerca e restituisce playlist casuali pubbliche
def get_random_playlists():
    sp = get_spotify_client()
    results = sp.search(q="music", type="playlist", limit=50)
    playlists = results.get("playlists", {}).get("items", [])
    
    valid_playlists = []
    for playlist in playlists:
        if playlist:
            try:
                valid_playlists.append({
                    "id": playlist.get("id"),
                    "name": playlist.get("name", "Senza titolo"),
                    "owner": playlist.get("owner", {}).get("display_name", "Sconosciuto"),
                    "url": playlist.get("external_urls", {}).get("spotify", "#"),
                    "image": playlist["images"][0]["url"] if playlist.get("images") else None
                })
            except Exception as e:
                logging.error(f"Errore con la playlist: {e}, saltata.")
    
    logging.info(f"Playlist trovate: {valid_playlists}")
    return random.sample(valid_playlists, min(5, len(valid_playlists))) if valid_playlists else []

# Ricerca playlist in base a una query
def search_playlists(query):
    sp = get_spotify_client()
    results = sp.search(q=query, type="playlist", limit=50)
    playlists = results.get("playlists", {}).get("items", [])
    return [
        {
            "id": playlist.get("id"),
            "name": playlist.get("name", "Senza titolo"),
            "owner": playlist.get("owner", {}).get("display_name", "Sconosciuto"),
            "url": playlist.get("external_urls", {}).get("spotify", "#"),
            "image": playlist["images"][0]["url"] if playlist.get("images") else None
        }
        for playlist in playlists if playlist
    ]

# Recupera i brani di una playlist con dettagli
def get_playlist_tracks(playlist_id):
    sp = get_spotify_client()
    try:
        # Info generali della playlist
        playlist_info = sp.playlist(playlist_id)
        playlist_name = playlist_info.get('name', 'Senza titolo')
        playlist_owner = playlist_info.get('owner', {}).get('display_name', 'Sconosciuto')
        
        results = sp.playlist_tracks(playlist_id)
        tracks = []

        for track in results["items"]:
            track_info = track["track"]
            if not track_info:
                continue

            # Estrai artisti e generi musicali
            artists = track_info["artists"]
            artist_ids = [artist["id"] for artist in artists]
            
            genres = set()
            if artist_ids:
                artists_info = sp.artists(artist_ids)["artists"]
                for artist in artists_info:
                    genres.update(artist.get("genres", []))

            # Estrai copertina album
            cover = track_info["album"]["images"][0]["url"] if track_info["album"]["images"] else None

            # Calcola durata in mm:ss
            duration_ms = track_info.get("duration_ms", 0)
            duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"

            # Anno di uscita
            release_year = track_info["album"].get("release_date", "Sconosciuto")[:4]
            
            # Costruisci oggetto traccia
            tracks.append({
                "playlist_name": playlist_name,
                "playlist_owner": playlist_owner,
                "name": track_info["name"],
                "artist": ", ".join(artist["name"] for artist in artists),
                "album": track_info["album"]["name"],
                "popularity": track_info.get("popularity", 0),
                "genre": ", ".join(genres) if genres else "Sconosciuto",
                "cover": cover,
                "duration": duration,
                "release_year": release_year,
                "track_url": track_info["external_urls"]["spotify"]
            })

        return tracks

    except Exception as e:
        logging.error(f"Errore durante il recupero dei brani della playlist: {e}")
        return []

# Inizia il login OAuth su Spotify
def spotify_login():
    auth_manager = get_spotify_auth()
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

# Gestisce il callback dopo il login su Spotify
def spotify_callback():
    auth_manager = get_spotify_auth()
    code = request.args.get("code")
    if not code:
        return "Errore: Codice di autorizzazione mancante.", 400
    
    try:
        token_info = auth_manager.get_access_token(code)
        session["token_info"] = token_info
        return redirect(url_for('home.home'))
    except Exception as e:
        return f"Errore durante il callback di Spotify: {e}", 500

# Ottiene le playlist personali dell'utente loggato
def get_user_playlists():
    if 'token_info' not in session:
        logging.warning("Nessun token_info nella sessione.")
        return []

    sp = get_spotify_client()
    try:
        results = sp.current_user_playlists(limit=50)
        playlists = [
            {
                "id": playlist["id"],
                "name": playlist["name"],
                "owner": playlist["owner"]["display_name"],
                "image": playlist["images"][0]["url"] if playlist["images"] else None
            }
            for playlist in results["items"]
        ]
        logging.info(f"Playlist private trovate: {playlists}")
        return playlists
    except Exception as e:
        logging.error("Errore durante il recupero delle playlist personali: %s", e)
        return []
