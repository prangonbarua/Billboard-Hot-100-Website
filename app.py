#!/usr/bin/env python3
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import pandas as pd
import tempfile
from pathlib import Path
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)
app.secret_key = 'billboard_hot_100_secret_key_change_in_production'

# Spotify API setup (using environment variables for credentials)
# Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in environment
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    SPOTIFY_ENABLED = True
except Exception as e:
    print(f"⚠️  Spotify API not configured: {e}")
    SPOTIFY_ENABLED = False

# Auto-update Billboard data on startup
print("Checking for Billboard data updates...")
try:
    result = subprocess.run(['python3', 'auto_update_data.py'],
                          capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print("✓ Data check complete!")
except Exception as e:
    print(f"⚠️  Could not check for updates: {e}")

# Find Billboard Hot 100 data file
DATA_DIR = Path('data')
DESKTOP_PATH = Path.home() / 'Desktop' / 'hot100.csv'

# Try data directory first, then Desktop
def find_data_file():
    if DATA_DIR.exists():
        for name in ['hot-100-current.csv', 'hot100.csv', 'billboard_hot_100.csv']:
            filepath = DATA_DIR / name
            if filepath.exists():
                return filepath
    if DESKTOP_PATH.exists():
        return DESKTOP_PATH
    raise FileNotFoundError("Billboard data not found! Run auto_update_data.py first.")

BILLBOARD_DATA_PATH = find_data_file()

# Load data once at startup (cached)
print(f"Loading Billboard Hot 100 data from {BILLBOARD_DATA_PATH.name}...")
BILLBOARD_DATA = pd.read_csv(BILLBOARD_DATA_PATH, low_memory=False)
print(f"Loaded {len(BILLBOARD_DATA)} records!")

def process_billboard_data(artist_name):
    """Process Billboard data and return Excel file path"""
    # Use the pre-loaded data
    data = BILLBOARD_DATA.copy()

    # Check if all required columns are present
    required_cols = {'Date', 'Song', 'Artist', 'Rank'}
    if not required_cols.issubset(data.columns):
        return None, "Missing required columns: Date, Song, Artist, Rank"

    # Convert the 'Date' column to datetime
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Clean text fields
    data['Song'] = data['Song'].str.strip().str.lower()
    data['Artist'] = data['Artist'].str.strip().str.lower()

    # Filter by artist
    filtered_data = data[data['Artist'].str.contains(artist_name.lower(), na=False)]

    if filtered_data.empty:
        return None, f"No results found for artist: {artist_name}"

    # Create a 'Song (Artist)' column
    filtered_data = filtered_data.copy()
    filtered_data['Song_Artist'] = (
        filtered_data['Song'].str.title() + " (" + filtered_data['Artist'].str.title() + ")"
    )

    # Pivot table using actual dates from the data
    pivot_table = filtered_data.pivot_table(
        index='Date',
        columns='Song_Artist',
        values='Rank',
        aggfunc='first'
    )

    # Fill in missing weeks (only those present in the data)
    all_dates = pd.Series(data['Date'].unique())
    all_dates = all_dates[all_dates >= filtered_data['Date'].min()]
    pivot_table = pivot_table.reindex(pd.to_datetime(sorted(all_dates)))

    # Sort columns by first appearance
    first_appearance = filtered_data.groupby('Song_Artist')['Date'].min()
    sorted_columns = first_appearance.sort_values().index
    pivot_table = pivot_table[sorted_columns]

    # Format index as text
    pivot_table.index = pivot_table.index.strftime('%Y-%m-%d')

    # Safe filename for output
    safe_name = artist_name.title().replace(" ", "_")
    output_file = os.path.join(tempfile.gettempdir(), f'{safe_name}_Chart_History.xlsx')

    # Save to Excel
    pivot_table.to_excel(output_file)

    return output_file, None

@app.route('/')
def index():
    return render_template('index.html')

def prepare_visualization_data(artist_name):
    """Prepare data for visualization"""
    # Use the pre-loaded data
    data = BILLBOARD_DATA.copy()

    # Keep original capitalization - only strip whitespace
    data['Song_Clean'] = data['Song'].str.strip()
    data['Artist_Clean'] = data['Artist'].str.strip()

    # Create lowercase versions for matching only
    data['Song_Lower'] = data['Song_Clean'].str.lower()
    data['Artist_Lower'] = data['Artist_Clean'].str.lower()

    # Convert dates first for filtering
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Filter by artist (case-insensitive) and modern era (1990+)
    filtered_data = data[
        (data['Artist_Lower'].str.contains(artist_name.lower(), na=False)) &
        (data['Date'] >= '1990-01-01')
    ].copy()

    if filtered_data.empty:
        return None

    # Get most common capitalization for each song
    def get_proper_name(series):
        # Get the most frequent capitalization
        return series.mode()[0] if len(series.mode()) > 0 else series.iloc[0]

    # Group and get proper capitalization
    song_names = {}
    for song_lower in filtered_data['Song_Lower'].unique():
        song_versions = filtered_data[filtered_data['Song_Lower'] == song_lower]['Song_Clean']
        song_names[song_lower] = get_proper_name(song_versions)

    artist_proper = get_proper_name(filtered_data['Artist_Clean'])

    # Create Song_Artist column with proper capitalization
    filtered_data.loc[:, 'Song_Artist'] = filtered_data['Song_Lower'].map(song_names) + f" ({artist_proper})"

    # Prepare chart data
    chart_data = {}
    for song in filtered_data['Song_Artist'].unique():
        song_data = filtered_data[filtered_data['Song_Artist'] == song][['Date', 'Rank']].copy()
        song_data = song_data.sort_values('Date')
        chart_data[song] = [
            {'date': row['Date'].strftime('%Y-%m-%d'), 'rank': int(row['Rank'])}
            for _, row in song_data.iterrows()
        ]

    # Calculate statistics
    songs_list = []
    for song in filtered_data['Song_Artist'].unique():
        song_df = filtered_data[filtered_data['Song_Artist'] == song]
        # Extract just the song name (before the parenthesis)
        song_name_only = song.split(' (')[0] if ' (' in song else song
        first_date = song_df['Date'].min()

        songs_list.append({
            'name': song,
            'song_only': song_name_only,
            'artist_only': artist_proper,
            'peak': int(song_df['Rank'].min()),
            'weeks': len(song_df),
            'first_date': first_date.strftime('%b %Y'),
            'first_date_sort': first_date  # For sorting
        })

    # Sort by first chart date (chronological order - oldest first)
    songs_list.sort(key=lambda x: x['first_date_sort'])

    # Calculate top 10 hits and #1 songs
    top_10_hits = len(filtered_data[filtered_data['Rank'] <= 10]['Song_Artist'].unique())
    number_ones = len(filtered_data[filtered_data['Rank'] == 1]['Song_Artist'].unique())

    stats = {
        'total_songs': len(filtered_data['Song_Artist'].unique()),
        'top_10_hits': top_10_hits,
        'number_ones': number_ones
    }

    return {
        'chart_data': chart_data,
        'songs': songs_list,
        'stats': stats
    }

@app.route('/analyze', methods=['POST'])
def analyze():
    # Check if artist name is provided
    artist_name = request.form.get('artist_name', '').strip()
    if not artist_name:
        flash('Please enter an artist name', 'error')
        return redirect(url_for('index'))

    try:
        # Prepare visualization data
        viz_data = prepare_visualization_data(artist_name)

        if viz_data is None:
            flash(f'No results found for artist: {artist_name}', 'error')
            return redirect(url_for('index'))

        # Render results page with visualization
        return render_template(
            'results.html',
            artist_name=artist_name.title(),
            chart_data=viz_data['chart_data'],
            songs=viz_data['songs'],
            total_songs=viz_data['stats']['total_songs'],
            top_10_hits=viz_data['stats']['top_10_hits'],
            number_ones=viz_data['stats']['number_ones']
        )

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/artists')
def get_artists():
    """API endpoint for artist autocomplete"""
    query = request.args.get('q', '').lower()

    # Get modern artists (1990+) from the dataset
    modern_data = BILLBOARD_DATA[pd.to_datetime(BILLBOARD_DATA['Date'], errors='coerce') >= '1990-01-01']

    # Get unique artists
    artists = modern_data['Artist'].str.strip().unique()

    # Filter by query if provided - use startswith instead of contains
    if query:
        artists = [a for a in artists if a.lower().startswith(query)]

    # Sort and limit to 50 results
    artists = sorted(artists)[:50]

    return {'artists': list(artists)}

@app.route('/api/artist-info/<artist_name>')
def get_artist_info(artist_name):
    """API endpoint for artist information from Spotify (image) + Wikipedia/Billboard overview"""

    # Get Billboard data for statistics
    modern_data = BILLBOARD_DATA[pd.to_datetime(BILLBOARD_DATA['Date'], errors='coerce') >= '1990-01-01']
    artist_data = modern_data[modern_data['Artist'].str.strip().str.lower() == artist_name.lower()].copy()

    if artist_data.empty:
        return jsonify({'error': 'Artist not found in Billboard data'}), 404

    artist_name_proper = artist_data['Artist'].iloc[0].strip()

    # Calculate Billboard statistics
    artist_data['Date'] = pd.to_datetime(artist_data['Date'], errors='coerce')
    total_songs = artist_data['Song'].nunique()
    total_weeks = len(artist_data)
    peak_position = int(artist_data['Rank'].min())
    first_chart = artist_data['Date'].min().strftime('%B %Y')
    latest_chart = artist_data['Date'].max().strftime('%B %Y')
    number_ones = len(artist_data[artist_data['Rank'] == 1])
    top_10_hits = artist_data[artist_data['Rank'] <= 10]['Song'].nunique()

    # Create comprehensive Billboard-based description
    description_parts = []

    if number_ones > 0:
        if number_ones == 1:
            description_parts.append(f"Billboard Hot 100 chart-topper with {number_ones} #1 hit")
        else:
            description_parts.append(f"Billboard Hot 100 chart-topper with {number_ones} #1 hits")
    elif top_10_hits >= 5:
        description_parts.append(f"Billboard Hot 100 artist with {top_10_hits} top 10 hits")
    else:
        description_parts.append("Billboard Hot 100 charting artist")

    description_parts.append(f"{total_songs} songs charted for {total_weeks} total weeks")

    if first_chart != latest_chart:
        description_parts.append(f"Charting from {first_chart} to {latest_chart}")
    else:
        description_parts.append(f"First charted in {first_chart}")

    description = " • ".join(description_parts)

    # Initialize defaults
    image_url = None
    spotify_url = None
    overview = description  # Use Billboard description as default

    # Try to fetch from Wikipedia first (image + description)
    try:
        import requests

        # Try multiple Wikipedia search variations for disambiguation
        wiki_attempts = [
            artist_name_proper,  # Original name
            f"{artist_name_proper} (musician)",
            f"{artist_name_proper} (rapper)",
            f"{artist_name_proper} (singer)",
            f"{artist_name_proper} (band)"
        ]

        for attempt_name in wiki_attempts:
            try:
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(attempt_name)}"
                response = requests.get(wiki_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 BillboardAnalyzer/1.0'})

                if response.status_code == 200:
                    data = response.json()

                    # Check if this is a disambiguation page
                    page_type = data.get('type', '')
                    if page_type == 'disambiguation':
                        print(f"✗ Disambiguation page for {attempt_name}, trying next...")
                        continue

                    print(f"✓ Wikipedia page found for {attempt_name}")

                    # Get Wikipedia image (try multiple sources)
                    if 'originalimage' in data and data['originalimage'] and 'source' in data['originalimage']:
                        image_url = data['originalimage']['source']
                        print(f"✓ Found originalimage: {image_url}")
                    elif 'thumbnail' in data and data['thumbnail'] and 'source' in data['thumbnail']:
                        # Use larger thumbnail - replace size in URL
                        thumb_url = data['thumbnail']['source']
                        image_url = thumb_url.replace('/50px-', '/600px-').replace('/100px-', '/600px-').replace('/200px-', '/600px-').replace('/300px-', '/600px-')
                        print(f"✓ Found thumbnail (enlarged): {image_url}")

                    # Get Wikipedia description
                    if 'extract' in data and data['extract']:
                        wiki_extract = data['extract']
                        # Use first 2 sentences from Wikipedia
                        sentences = wiki_extract.split('. ')
                        if len(sentences) >= 2:
                            overview = '. '.join(sentences[:2]) + '.'
                        else:
                            overview = wiki_extract
                        print(f"✓ Got Wikipedia description: {len(overview)} chars")

                    # Found valid page, stop trying
                    break

            except Exception as inner_e:
                print(f"✗ Error trying {attempt_name}: {inner_e}")
                continue

        print(f"Wikipedia final: image_url={image_url is not None}, overview_len={len(overview) if overview else 0}")
    except Exception as e:
        print(f"✗ Wikipedia API error for {artist_name_proper}: {e}")

    # Try to get Spotify data as supplement if available
    if SPOTIFY_ENABLED:
        try:
            results = sp.search(q=artist_name, type='artist', limit=1)
            if results['artists']['items']:
                artist_obj = results['artists']['items'][0]
                spotify_url = artist_obj['external_urls']['spotify']

                # Use Spotify image if Wikipedia didn't provide one
                if not image_url and artist_obj['images']:
                    image_url = artist_obj['images'][0]['url']
        except Exception as e:
            print(f"Spotify API error: {e}")

    # If Spotify isn't available, try to construct Spotify URL from iTunes Search API
    if not spotify_url:
        try:
            from urllib.parse import quote

            # Try iTunes Search API which sometimes has Spotify artist IDs or links
            itunes_url = f"https://itunes.apple.com/search?term={quote(artist_name_proper)}&entity=allArtist&limit=1"
            itunes_response = requests.get(itunes_url, timeout=10, headers={'User-Agent': 'BillboardAnalyzer/1.0'})

            if itunes_response.status_code == 200:
                itunes_data = itunes_response.json()
                if itunes_data.get('results') and len(itunes_data['results']) > 0:
                    artist_result = itunes_data['results'][0]

                    # Get artist name from iTunes for potential Spotify search
                    itunes_artist_name = artist_result.get('artistName', artist_name_proper)

                    # Try to construct Spotify search URL (opens Spotify with search)
                    # Format: https://open.spotify.com/search/{artist_name}
                    search_query = quote(itunes_artist_name)
                    spotify_url = f"https://open.spotify.com/search/{search_query}"
                    print(f"✓ Created Spotify search URL: {spotify_url}")
        except Exception as e:
            print(f"iTunes/Spotify URL construction error: {e}")

    return jsonify({
        'name': artist_name_proper,
        'image_url': image_url,
        'spotify_url': spotify_url,
        'overview': overview,
        'stats': {
            'total_songs': total_songs,
            'total_weeks': total_weeks,
            'peak_position': peak_position,
            'number_ones': number_ones,
            'top_10_hits': top_10_hits
        }
    })

@app.route('/api/song-image/<artist_name>/<song_name>')
def get_song_image(artist_name, song_name):
    """API endpoint to get song/album artwork from iTunes API"""

    try:
        import requests
        from urllib.parse import quote

        # iTunes API search
        query = f"{song_name} {artist_name}"
        itunes_url = f"https://itunes.apple.com/search?term={quote(query)}&media=music&entity=song&limit=3"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(itunes_url, timeout=5, headers=headers)

        if response.status_code == 200 and response.text:
            try:
                data = response.json()

                if data.get('resultCount', 0) > 0:
                    result = data['results'][0]
                    # Get high-res artwork (replace 100x100 with 600x600)
                    artwork_url = result.get('artworkUrl100', '').replace('100x100', '600x600')

                    if artwork_url:
                        return jsonify({
                            'image_url': artwork_url,
                            'album_name': result.get('collectionName', ''),
                            'track_name': result.get('trackName', ''),
                            'source': 'itunes'
                        })
            except ValueError as json_error:
                print(f"iTunes JSON parse error for '{song_name}' by {artist_name}: {json_error}")

        return jsonify({'error': 'Track not found'}), 404

    except Exception as e:
        print(f"iTunes API error for '{song_name}' by {artist_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<artist_name>')
def download_excel(artist_name):
    """Download Excel file for artist"""
    try:
        output_file, error = process_billboard_data(artist_name)

        if error:
            flash(error, 'error')
            return redirect(url_for('index'))

        return send_file(
            output_file,
            as_attachment=True,
            download_name=f'{artist_name.replace(" ", "_")}_Chart_History.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Billboard Hot 100 Chart Analyzer - Web App")
    print("="*60)
    print("\nStarting server...")
    print("Open your browser and go to: http://localhost:5001")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
