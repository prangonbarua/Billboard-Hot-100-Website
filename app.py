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

    stats = {
        'total_songs': len(filtered_data['Song_Artist'].unique()),
        'total_weeks': len(filtered_data),
        'peak_position': int(filtered_data['Rank'].min())
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
            total_weeks=viz_data['stats']['total_weeks'],
            peak_position=viz_data['stats']['peak_position']
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
    """API endpoint for artist information (Spotify image + Billboard stats)"""

    # Generate Billboard-based description
    modern_data = BILLBOARD_DATA[pd.to_datetime(BILLBOARD_DATA['Date'], errors='coerce') >= '1990-01-01']
    artist_data = modern_data[modern_data['Artist'].str.strip().str.lower() == artist_name.lower()].copy()

    if artist_data.empty:
        return jsonify({'error': 'Artist not found in Billboard data'}), 404

    # Calculate Billboard statistics
    artist_data['Date'] = pd.to_datetime(artist_data['Date'], errors='coerce')
    total_songs = artist_data['Song'].nunique()
    total_weeks = len(artist_data)
    peak_position = int(artist_data['Rank'].min())
    first_chart = artist_data['Date'].min().strftime('%B %Y')
    latest_chart = artist_data['Date'].max().strftime('%B %Y')
    number_ones = len(artist_data[artist_data['Rank'] == 1])
    top_10_hits = artist_data[artist_data['Rank'] <= 10]['Song'].nunique()

    # Generate description
    description = f"Billboard Hot 100 artist with {total_songs} charted songs and {total_weeks} total weeks on the chart. "
    if number_ones > 0:
        description += f"Achieved {number_ones} #1 hit{'s' if number_ones > 1 else ''} and "
    description += f"{top_10_hits} top 10 hit{'s' if top_10_hits != 1 else ''}. "
    description += f"Chart presence from {first_chart} to {latest_chart}."

    # Try to get Spotify profile image
    image_url = None
    spotify_url = None

    if SPOTIFY_ENABLED:
        try:
            results = sp.search(q=artist_name, type='artist', limit=1)
            if results['artists']['items']:
                artist = results['artists']['items'][0]
                image_url = artist['images'][0]['url'] if artist['images'] else None
                spotify_url = artist['external_urls']['spotify']
        except Exception as e:
            print(f"Spotify API error: {e}")

    return jsonify({
        'name': artist_data['Artist'].iloc[0].strip(),
        'image_url': image_url,
        'description': description,
        'spotify_url': spotify_url,
        'stats': {
            'total_songs': total_songs,
            'total_weeks': total_weeks,
            'peak_position': peak_position,
            'number_ones': number_ones,
            'top_10_hits': top_10_hits
        }
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
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
