import pandas as pd
import plotly.express as px
from services.spotify_oauth import get_playlist_tracks

def analyze_and_visualize(playlist_id):
    # Recupera le tracce della playlist dal servizio Spotify
    tracks = get_playlist_tracks(playlist_id)

    if not tracks:
        print("Nessun dato disponibile per l'analisi.")
        return None

    # Estrae e struttura i dati rilevanti da ciascuna traccia
    data = [
        {
            "artist": track["artist"],
            "album": track["album"],
            "track_name": track["name"],
            "popularity": track.get("popularity", 0),
            "genre": track.get("genre", "Sconosciuto"),
            "duration": track.get("duration", "0:00"),
            "release_year": track.get("release_year", "Sconosciuto"),
        }
        for track in tracks
    ]

    df = pd.DataFrame(data)

    if df.empty:
        print("DataFrame vuoto, impossibile generare il grafico.")
        return None

    # === GRAFICO: Top 5 Artisti più popolari ===
    top_artists = df.groupby("artist")["popularity"].sum().nlargest(5).reset_index()
    fig_artists = px.bar(
        top_artists, x="artist", y="popularity",
        title="Top 5 Artisti più popolari",
        labels={"artist": "Artista", "popularity": "Popolarità"}
    )

    # === GRAFICO: Top 5 Album più popolari ===
    top_albums = df.groupby("album")["popularity"].sum().nlargest(5).reset_index()
    fig_albums = px.bar(
        top_albums, x="album", y="popularity",
        title="Top 5 Album più popolari",
        labels={"album": "Album", "popolarity": "Popolarità"}
    )

    # === GRAFICO: Distribuzione dei generi musicali ===
    genre_counts = df["genre"].str.split(", ", expand=True).stack().value_counts().reset_index()
    genre_counts.columns = ["genre", "count"]
    genre_counts = genre_counts[genre_counts["genre"] != "Sconosciuto"]
    fig_genres = px.pie(
        genre_counts, names="genre", values="count",
        title="Distribuzione dei Generi Musicali",
        labels={"genre": "Genere", "count": "Numero di brani"}
    )

    # === GRAFICO: Brani per anno di pubblicazione ===
    release_year_counts = df["release_year"].value_counts().reset_index()
    release_year_counts.columns = ["release_year", "count"]
    release_year_counts = release_year_counts.sort_values("release_year")
    fig_release_year = px.line(
        release_year_counts, x="release_year", y="count",
        title="Distribuzione Temporale dei Brani",
        labels={"release_year": "Anno di Pubblicazione", "count": "Numero di Brani"}
    )

    # === GRAFICO: Durata dei brani per intervallo ===
    df["duration_minutes"] = df["duration"].apply(
        lambda x: int(x.split(":")[0]) + int(x.split(":")[1]) / 60 if ":" in x else 0
    )

    bins = [0, 2, 4, 6, 8, 10, 15, 20]
    labels = ["<2", "<4", "<6", "<8", "<10", "<15", "<20"]
    df["duration_range"] = pd.cut(df["duration_minutes"], bins=bins, labels=labels, include_lowest=True)

    duration_counts = df["duration_range"].value_counts().sort_index().reset_index()
    duration_counts.columns = ["duration_range", "count"]

    fig_duration = px.bar(
        duration_counts, x="duration_range", y="count",
        title="Distribuzione della Durata dei Brani",
        labels={"duration_range": "Intervallo di Durata (min)", "count": "Numero di Brani"},
        category_orders={"duration_range": labels}
    )

    # === GRAFICO: Istogramma della popolarità ===
    fig_popularity = px.histogram(
        df, x="popularity", nbins=10,
        title="Distribuzione della Popolarità",
        labels={"popularity": "Livello di Popolarità"}
    )

    # === GRAFICO: Evoluzione della popolarità media nel tempo ===
    df_time = df[df["release_year"] != "Sconosciuto"].copy()
    df_time["release_year"] = pd.to_numeric(df_time["release_year"], errors='coerce')
    df_time.dropna(inplace=True)
    df_time = df_time.groupby("release_year")["popularity"].mean().reset_index()

    fig_evolution = px.line(
        df_time, x="release_year", y="popularity",
        title="Evoluzione della Popolarità nel Tempo",
        labels={"release_year": "Anno di Pubblicazione", "popularity": "Popolarità Media"}
    )

    # Ritorna i grafici convertiti in HTML per essere incorporati nei template
    return {
        "fig_artists": fig_artists.to_html(full_html=False),
        "fig_albums": fig_albums.to_html(full_html=False),
        "fig_genres": fig_genres.to_html(full_html=False),
        "fig_release_year": fig_release_year.to_html(full_html=False),
        "fig_duration": fig_duration.to_html(full_html=False),
        "fig_popularity": fig_popularity.to_html(full_html=False),
        "fig_evolution": fig_evolution.to_html(full_html=False),
    }
