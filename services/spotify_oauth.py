import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from flask import session, redirect, url_for, request, render_template
import random
import logging

SPOTIFY_CLIENT_ID = "d74cb805ae4f4e9c87c5d361d8adade3"
SPOTIFY_CLIENT_SECRET = "3a61d65da5914d1789080bccbc68e0fd"
SPOTIFY_REDIRECT_URI = "https://super-engine-pjrq5q4674prf7r99-5000.app.github.dev/callback"
SCOPE = "user-read-private playlist-read-private playlist-read-collaborative"


logging.basicConfig(level=logging.INFO)

def get_spotify_auth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )

def get_spotify_client():
    token_info = session.get("token_info")
    if token_info:
        auth_manager = get_spotify_auth()
        if auth_manager.is_token_expired(token_info):
            logging.info("Token scaduto, aggiornamento in corso...")
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            session["token_info"] = token_info
        return spotipy.Spotify(auth=token_info.get("access_token"))
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

def get_random_playlists():
    sp = get_spotify_client()
    query = "music"
    results = sp.search(q=query, type="playlist", limit=50)
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




def get_playlist_tracks(playlist_id):
    sp = get_spotify_client()
    try:
        # Ottieni prima le informazioni della playlist
        playlist_info = sp.playlist(playlist_id)
        playlist_name = playlist_info.get('name', 'Senza titolo')
        playlist_owner = playlist_info.get('owner', {}).get('display_name', 'Sconosciuto')
        
        results = sp.playlist_tracks(playlist_id)
        tracks = []

        for track in results["items"]:
            track_info = track["track"]
            if not track_info:  
                continue

            # Estrai informazioni sugli artisti
            artists = track_info["artists"]
            artist_ids = [artist["id"] for artist in artists]
            
            # Estrai generi musicali
            genres = set()
            if artist_ids:
                artists_info = sp.artists(artist_ids)["artists"]
                for artist in artists_info:
                    genres.update(artist.get("genres", []))

            # Estrai copertina album
            cover = None
            if track_info["album"]["images"]:
                cover = track_info["album"]["images"][0]["url"]
            
            # Calcola durata in formato mm:ss
            duration_ms = track_info.get("duration_ms", 0)
            duration_min = duration_ms // 60000
            duration_sec = (duration_ms % 60000) // 1000
            duration = f"{duration_min}:{duration_sec:02d}"
            
            # Estrai anno di pubblicazione
            release_year = track_info["album"].get("release_date", "Sconosciuto")[:4]
            
            # Aggiungi tutte le informazioni al dizionario del brano
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




def spotify_login():
    
    auth_manager = get_spotify_auth()
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

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

def get_user_playlists():
    
    if 'token_info' not in session:
        logging.warning("Nessun token_info nella sessione.")
        return []

    sp = get_spotify_client()
    try:
        results = sp.current_user_playlists(limit=50)
        logging.info("Risultati API Spotify: %s", results)
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