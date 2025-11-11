#!/usr/bin/env python3
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import pandas as pd
import tempfile
from pathlib import Path
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime, timedelta
import sys

app = Flask(__name__)
# Use environment variable for production, fallback for development
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production_' + str(os.urandom(24).hex()))

# Security: CORS Protection (only allow your domain in production)
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get('ALLOWED_ORIGINS', '*').split(',')
    }
})

# Security: Rate Limiting (prevent abuse)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Spotify API setup (using environment variables for credentials)
# Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in environment
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    SPOTIFY_ENABLED = True
except Exception as e:
    print(f"⚠️  Spotify API not configured: {e}")
    SPOTIFY_ENABLED = False

# Rate limiting disabled
DOWNLOAD_LIMIT = None
download_tracker = {}

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

# Try current directory first, then data directory, then Desktop
def find_data_file():
    # Check current directory
    for name in ['hot-100-current.csv', 'hot100.csv', 'billboard_hot_100.csv']:
        filepath = Path(name)
        if filepath.exists():
            return filepath
    # Check data directory
    if DATA_DIR.exists():
        for name in ['hot-100-current.csv', 'hot100.csv', 'billboard_hot_100.csv']:
            filepath = DATA_DIR / name
            if filepath.exists():
                return filepath
    # Check desktop
    if DESKTOP_PATH.exists():
        return DESKTOP_PATH
    raise FileNotFoundError("Billboard data not found! Run auto_update_data.py first.")

BILLBOARD_DATA_PATH = find_data_file()

# Load data once at startup (cached)
print(f"Loading Billboard Hot 100 data from {BILLBOARD_DATA_PATH.name}...")
BILLBOARD_DATA = pd.read_csv(BILLBOARD_DATA_PATH, low_memory=False)
print(f"Loaded {len(BILLBOARD_DATA)} records!")

# Load Billboard 200 data
BILLBOARD_200_PATH = Path('billboard200.csv')
if BILLBOARD_200_PATH.exists():
    print(f"Loading Billboard 200 data from {BILLBOARD_200_PATH.name}...")
    BILLBOARD_200_DATA = pd.read_csv(BILLBOARD_200_PATH, low_memory=False)
    print(f"Loaded {len(BILLBOARD_200_DATA)} Billboard 200 records!")
else:
    print("⚠️  Billboard 200 data not found. Billboard 200 chart will be unavailable.")
    BILLBOARD_200_DATA = None

def check_download_limit(ip_address):
    """Rate limiting disabled - always allow downloads"""
    return True, 0  # Always allowed

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

@app.route('/about')
def about():
    return render_template('about.html')

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
        peak_position = int(song_df['Rank'].min())

        songs_list.append({
            'name': song,
            'song_only': song_name_only,
            'artist_only': artist_proper,
            'peak': peak_position,
            'weeks': len(song_df),
            'first_date': first_date.strftime('%b %Y'),
            'first_date_sort': first_date,  # For sorting
            'is_number_one': peak_position == 1  # Flag for #1 songs
        })

    # Sort by #1 status first (all #1s at top), then by first chart date
    songs_list.sort(key=lambda x: (not x['is_number_one'], x['first_date_sort']))

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

@app.route('/api/song-image/<path:artist_name>/<path:song_name>')
def get_song_image(artist_name, song_name):
    """API endpoint to get song/album artwork from iTunes API (path: allows slashes in names)"""

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

@app.route('/api/album-image/<path:artist_name>/<path:album_name>')
def get_album_image(artist_name, album_name):
    """API endpoint to get album artwork from iTunes API (path: allows slashes in names)"""

    try:
        import requests
        from urllib.parse import quote

        # iTunes API search for albums
        query = f"{album_name} {artist_name}"
        itunes_url = f"https://itunes.apple.com/search?term={quote(query)}&media=music&entity=album&limit=3"

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
                            'artist_name': result.get('artistName', ''),
                            'source': 'itunes'
                        })
            except ValueError as json_error:
                print(f"iTunes JSON parse error for album '{album_name}' by {artist_name}: {json_error}")

        return jsonify({'error': 'Album not found'}), 404

    except Exception as e:
        print(f"iTunes API error for album '{album_name}' by {artist_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/hot100')
def hot100():
    """Hot 100 Weekly Chart Viewer"""
    # Get the selected date from query params (default to latest)
    selected_date = request.args.get('date', None)

    # Get unique dates from 1958-2025 (entire Billboard Hot 100 history), sorted descending
    data = BILLBOARD_DATA.copy()
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Filter for 1958-2025 dates (complete Hot 100 history)
    dates_filtered = data[(data['Date'].dt.year >= 1958) & (data['Date'].dt.year <= 2025)]['Date'].unique()
    dates_filtered = sorted(dates_filtered, reverse=True)

    # Convert to string format for display
    available_dates = [pd.Timestamp(d).strftime('%Y-%m-%d') for d in dates_filtered]

    # If no date selected, use the latest
    if not selected_date and available_dates:
        selected_date = available_dates[0]

    # Get chart data for selected date
    chart_songs = []
    if selected_date:
        date_data = data[data['Date'] == pd.to_datetime(selected_date)]
        date_data = date_data.sort_values('Rank')

        selected_date_dt = pd.to_datetime(selected_date)

        # PRE-CALCULATE cumulative weeks for all songs on this chart (PERFORMANCE OPTIMIZATION)
        # Filter data up to selected date once
        historical_data = data[data['Date'] <= selected_date_dt].copy()
        historical_data['Song_Clean'] = historical_data['Song'].str.strip()
        historical_data['Artist_Clean'] = historical_data['Artist'].str.strip()

        # Group by song+artist and count appearances
        weeks_lookup = historical_data.groupby(['Song_Clean', 'Artist_Clean']).size().to_dict()

        for _, row in date_data.iterrows():
            # Helper function to safely convert to int
            def safe_int(val, default=None):
                if pd.isna(val):
                    return default
                if isinstance(val, str) and (val.strip() == '-' or val.strip() == ''):
                    return default
                try:
                    result = int(float(val))
                    return result if result != 0 else default
                except (ValueError, TypeError):
                    return default

            # Get song info
            song_name = row['Song'].strip() if pd.notna(row['Song']) else ''
            artist_name = row['Artist'].strip() if pd.notna(row['Artist']) else ''

            # Lookup cumulative weeks from pre-calculated dictionary
            cumulative_weeks = weeks_lookup.get((song_name, artist_name), 1)

            song_info = {
                'rank': int(row['Rank']),
                'song': song_name,
                'artist': artist_name,
                'last_week': safe_int(row['Last Week']),
                'peak': safe_int(row['Peak Position'], int(row['Rank'])),
                'weeks': cumulative_weeks,
            }

            # Calculate position change
            if song_info['last_week'] is None:
                song_info['change'] = 'new'
                song_info['change_amount'] = 0
            elif song_info['rank'] < song_info['last_week']:
                song_info['change'] = 'up'
                song_info['change_amount'] = song_info['last_week'] - song_info['rank']
            elif song_info['rank'] > song_info['last_week']:
                song_info['change'] = 'down'
                song_info['change_amount'] = song_info['rank'] - song_info['last_week']
            else:
                song_info['change'] = 'same'
                song_info['change_amount'] = 0

            chart_songs.append(song_info)

    return render_template(
        'hot100.html',
        available_dates=available_dates,
        selected_date=selected_date,
        chart_songs=chart_songs
    )

@app.route('/billboard200')
def billboard200():
    """Billboard 200 Weekly Albums Chart Viewer"""
    if BILLBOARD_200_DATA is None:
        flash('Billboard 200 data is not available', 'error')
        return redirect(url_for('index'))

    # Get the selected date from query params (default to latest)
    selected_date = request.args.get('date', None)

    # Get unique dates from Billboard 200 data
    data = BILLBOARD_200_DATA.copy()
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Filter for dates (entire Billboard 200 history)
    dates_filtered = data[(data['Date'].dt.year >= 1963) & (data['Date'].dt.year <= 2025)]['Date'].unique()
    dates_filtered = sorted(dates_filtered, reverse=True)

    # Convert to string format for display
    available_dates = [pd.Timestamp(d).strftime('%Y-%m-%d') for d in dates_filtered]

    # If no date selected, use the latest
    if not selected_date and available_dates:
        selected_date = available_dates[0]

    # Get chart data for selected date
    chart_songs = []
    if selected_date:
        date_data = data[data['Date'] == pd.to_datetime(selected_date)]
        date_data = date_data.sort_values('Rank')

        selected_date_dt = pd.to_datetime(selected_date)

        # PRE-CALCULATE cumulative weeks for all albums on this chart
        historical_data = data[data['Date'] <= selected_date_dt].copy()
        historical_data['Song_Clean'] = historical_data['Song'].str.strip()
        historical_data['Artist_Clean'] = historical_data['Artist'].str.strip()

        # Group by album+artist and count appearances
        weeks_lookup = historical_data.groupby(['Song_Clean', 'Artist_Clean']).size().to_dict()

        for _, row in date_data.iterrows():
            # Helper function to safely convert to int
            def safe_int(val, default=None):
                if pd.isna(val):
                    return default
                if isinstance(val, str) and (val.strip() == '-' or val.strip() == ''):
                    return default
                try:
                    result = int(float(val))
                    return result if result != 0 else default
                except (ValueError, TypeError):
                    return default

            # Get album info
            song_name = row['Song'].strip() if pd.notna(row['Song']) else ''
            artist_name = row['Artist'].strip() if pd.notna(row['Artist']) else ''

            # Lookup cumulative weeks from pre-calculated dictionary
            cumulative_weeks = weeks_lookup.get((song_name, artist_name), 1)

            song_info = {
                'rank': int(row['Rank']),
                'song': song_name,
                'artist': artist_name,
                'last_week': safe_int(row['Last Week']),
                'peak': safe_int(row['Peak Position'], int(row['Rank'])),
                'weeks': cumulative_weeks,
            }

            # Calculate position change
            if song_info['last_week'] is None:
                song_info['change'] = 'new'
                song_info['change_amount'] = 0
            elif song_info['rank'] < song_info['last_week']:
                song_info['change'] = 'up'
                song_info['change_amount'] = song_info['last_week'] - song_info['rank']
            elif song_info['rank'] > song_info['last_week']:
                song_info['change'] = 'down'
                song_info['change_amount'] = song_info['rank'] - song_info['last_week']
            else:
                song_info['change'] = 'same'
                song_info['change_amount'] = 0

            chart_songs.append(song_info)

    return render_template(
        'billboard200.html',
        available_dates=available_dates,
        selected_date=selected_date,
        chart_songs=chart_songs
    )

@app.route('/api/song-history')
def get_song_history():
    """Get full chart history for a specific song (using query parameters to support slashes in names)"""
    artist = request.args.get('artist', '')
    song = request.args.get('song', '')

    if not artist or not song:
        return jsonify({'error': 'Missing artist or song parameter'}), 400

    data = BILLBOARD_DATA.copy()
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Clean and filter
    data['Song_Clean'] = data['Song'].str.strip().str.lower()
    data['Artist_Clean'] = data['Artist'].str.strip().str.lower()

    song_data = data[
        (data['Song_Clean'] == song.lower()) &
        (data['Artist_Clean'] == artist.lower())
    ].copy()

    if song_data.empty:
        return jsonify({'error': 'No history found'}), 404

    # Sort by date
    song_data = song_data.sort_values('Date')

    # Helper function to safely convert to int
    def safe_int(val, default=None):
        if pd.isna(val):
            return default
        if isinstance(val, str) and (val.strip() == '-' or val.strip() == ''):
            return default
        try:
            result = int(float(val))
            return result if result != 0 else default
        except (ValueError, TypeError):
            return default

    history = []
    for idx, (_, row) in enumerate(song_data.iterrows(), start=1):
        # Cumulative weeks = index position (starting from 1)
        history.append({
            'date': row['Date'].strftime('%Y-%m-%d'),
            'rank': int(row['Rank']),
            'weeks': idx
        })

    # Get stats
    peak = int(song_data['Rank'].min())
    total_weeks = len(song_data)

    return jsonify({
        'history': history,
        'peak': peak,
        'total_weeks': total_weeks,
        'song': song,
        'artist': artist
    })

@app.route('/api/album-history')
def get_album_history():
    """Get full chart history for a specific album (using query parameters to support slashes in names)"""
    if BILLBOARD_200_DATA is None:
        return jsonify({'error': 'Billboard 200 data not available'}), 404

    artist = request.args.get('artist', '')
    album = request.args.get('album', '')

    if not artist or not album:
        return jsonify({'error': 'Missing artist or album parameter'}), 400

    data = BILLBOARD_200_DATA.copy()
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])

    # Clean and filter (Song column contains album names in Billboard 200 data)
    data['Album_Clean'] = data['Song'].str.strip().str.lower()
    data['Artist_Clean'] = data['Artist'].str.strip().str.lower()

    album_data = data[
        (data['Album_Clean'] == album.lower()) &
        (data['Artist_Clean'] == artist.lower())
    ].copy()

    if album_data.empty:
        return jsonify({'error': 'No history found'}), 404

    # Sort by date
    album_data = album_data.sort_values('Date')

    # Helper function to safely convert to int
    def safe_int(val, default=None):
        if pd.isna(val):
            return default
        if isinstance(val, str) and (val.strip() == '-' or val.strip() == ''):
            return default
        try:
            result = int(float(val))
            return result if result != 0 else default
        except (ValueError, TypeError):
            return default

    history = []
    for idx, (_, row) in enumerate(album_data.iterrows(), start=1):
        # Cumulative weeks = index position (starting from 1)
        history.append({
            'date': row['Date'].strftime('%Y-%m-%d'),
            'rank': int(row['Rank']),
            'weeks': idx
        })

    # Get stats
    peak = int(album_data['Rank'].min())
    total_weeks = len(album_data)

    return jsonify({
        'history': history,
        'peak': peak,
        'total_weeks': total_weeks,
        'album': album,
        'artist': artist
    })

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
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    print(f"Open your browser and go to: http://localhost:{port}")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
