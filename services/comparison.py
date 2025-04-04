import pandas as pd
import plotly.express as px
from services.spotify_oauth import get_playlist_tracks

def compare_playlists(playlist1_id, playlist2_id):
    try:
        # 1. Recupero dati delle playlist
        playlist1_tracks = get_playlist_tracks(playlist1_id)
        playlist2_tracks = get_playlist_tracks(playlist2_id)
        
        if not playlist1_tracks or not playlist2_tracks:
            raise ValueError("Impossibile recuperare i dati di una o entrambe le playlist")
        
        # 2. Preparazione dati
        playlist1_name = playlist1_tracks[0]['playlist_name'] if playlist1_tracks else "Playlist 1"
        playlist2_name = playlist2_tracks[0]['playlist_name'] if playlist2_tracks else "Playlist 2"
        
        df1 = pd.DataFrame(playlist1_tracks)
        df2 = pd.DataFrame(playlist2_tracks)
        
        # 3. Grafico 1: Brani in comune
        common_tracks = pd.merge(df1, df2, on=['name', 'artist'], how='inner')
        smaller_playlist_size = min(len(df1), len(df2))
        similarity = (len(common_tracks) / smaller_playlist_size * 100) if smaller_playlist_size > 0 else 0
        
        fig_tracks = px.bar(
            x=['Total '+playlist1_name, 'Total '+playlist2_name, 'Brani comuni'],
            y=[len(df1), len(df2), len(common_tracks)],
            title=f'Brani in comune - Somiglianza: {similarity:.1f}%',
            labels={'x': '', 'y': 'Numero di brani'},
            color=[playlist1_name, playlist2_name, 'Comuni'],
            color_discrete_map={
                playlist1_name: '#1DB954',
                playlist2_name: '#191414',
                'Comuni': '#535353'
            }
        )
        
        # 4. Grafico 2: Artisti in comune
        # Normalizza artisti (split su collaborazioni)
        df1['artists_split'] = df1['artist'].str.split(', ')
        df2['artists_split'] = df2['artist'].str.split(', ')

        # Espandi le liste di artisti e conta le occorrenze
        artists1 = df1.explode('artists_split')['artists_split'].value_counts().reset_index()
        artists1.columns = ['artist', 'count1']
        artists2 = df2.explode('artists_split')['artists_split'].value_counts().reset_index()
        artists2.columns = ['artist', 'count2']

        # Unisci e filtra solo gli artisti in comune
        common_artists = pd.merge(artists1, artists2, on='artist', how='inner').sort_values(
            by=['count1', 'count2'], 
            ascending=False
        )

        if not common_artists.empty:
            fig_artists = px.bar(
                common_artists.head(15),  
                x='artist',
                y=['count1', 'count2'],
                barmode='group',
                title='Top artisti in comune',
                labels={
                    'value': 'Numero di brani', 
                    'variable': 'Playlist', 
                    'artist': 'Artista'
                },
                color_discrete_sequence=['#1DB954', '#191414'] 
            )
        else:
            fig_artists = None
        
        # 5. Grafico 3: Popolarità media
        avg_pop1 = df1['popularity'].mean() if not df1.empty else 0
        avg_pop2 = df2['popularity'].mean() if not df2.empty else 0
        
        fig_popularity = px.bar(
            x=[playlist1_name, playlist2_name],
            y=[avg_pop1, avg_pop2],
            title='Confronto popolarità media (0-100)',
            labels={'x': 'Playlist', 'y': 'Popolarità media'},
            color=[playlist1_name, playlist2_name],
            color_discrete_map={
                playlist1_name: '#1DB954',
                playlist2_name: '#191414'
            }
        )
        
        # 6. Grafico 4: Generi musicali
        df1['genres_split'] = df1['genre'].str.split(', ')
        df2['genres_split'] = df2['genre'].str.split(', ')
        
        genres1 = df1.explode('genres_split')['genres_split'].value_counts().reset_index()
        genres1.columns = ['genre', 'count1']
        genres2 = df2.explode('genres_split')['genres_split'].value_counts().reset_index()
        genres2.columns = ['genre', 'count2']
        
        common_genres = pd.merge(genres1, genres2, on='genre', how='outer').fillna(0)
        common_genres = common_genres[common_genres['genre'] != 'Sconosciuto']
        
        if not common_genres.empty:
            fig_genres = px.bar(
                common_genres.sort_values(by=['count1', 'count2'], ascending=False).head(15),
                x='genre',
                y=['count1', 'count2'],
                barmode='group',
                title='Top generi musicali',
                labels={'value': 'Numero di brani', 'variable': 'Playlist', 'genre': 'Genere'},
                color_discrete_sequence=['#1DB954', '#191414']
            )
        else:
            fig_genres = None
        
        # 7. Grafico 5: Distribuzione temporale
        df1['release_year'] = pd.to_numeric(df1['release_year'], errors='coerce')
        df2['release_year'] = pd.to_numeric(df2['release_year'], errors='coerce')
        
        years1 = df1['release_year'].dropna().astype(int).value_counts().sort_index().reset_index()
        years1.columns = ['year', 'count1']
        years2 = df2['release_year'].dropna().astype(int).value_counts().sort_index().reset_index()
        years2.columns = ['year', 'count2']
        
        years_combined = pd.merge(years1, years2, on='year', how='outer').fillna(0)
        
        if not years_combined.empty:
            fig_years = px.line(
                years_combined,
                x='year',
                y=['count1', 'count2'],
                title='Distribuzione temporale dei brani',
                labels={'value': 'Numero di brani', 'variable': 'Playlist', 'year': 'Anno'},
                color_discrete_sequence=['#1DB954', '#191414']
            )
            
            # Aggiungi punti ai dati della linea
            fig_years.update_traces(mode='lines+markers')
        else:
            fig_years = None
        
        # 8. Preparazione output
        charts = {
            'fig_tracks': fig_tracks.to_html(full_html=False),
            'fig_artists': fig_artists.to_html(full_html=False) if fig_artists else None,
            'fig_popularity': fig_popularity.to_html(full_html=False),
            'fig_genres': fig_genres.to_html(full_html=False) if fig_genres else None,
            'fig_years': fig_years.to_html(full_html=False) if fig_years else None,
            'similarity': similarity
        }
        
        return {
            'playlist1_name': playlist1_name,
            'playlist2_name': playlist2_name,
            'charts': charts
        }
        
    except Exception as e:
        import logging
        logging.error(f"Errore durante il confronto delle playlist: {str(e)}")
        return {
            'playlist1_name': "Playlist 1",
            'playlist2_name': "Playlist 2",
            'charts': None,
            'error': str(e)
        }