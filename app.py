#!/usr/bin/env python3
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import pandas as pd
import tempfile

app = Flask(__name__)
app.secret_key = 'billboard_hot_100_secret_key_change_in_production'

# Billboard Hot 100 data URL (public dataset)
BILLBOARD_DATA_URL = 'https://raw.githubusercontent.com/HipsterVizNinja/random-data/main/Music/hot-100-current.csv'

def process_billboard_data(csv_path, artist_name):
    """Process Billboard data and return Excel file path"""
    # Load the data
    data = pd.read_csv(csv_path, low_memory=False)

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

@app.route('/analyze', methods=['POST'])
def analyze():
    # Check if artist name is provided
    artist_name = request.form.get('artist_name', '').strip()
    if not artist_name:
        flash('Please enter an artist name', 'error')
        return redirect(url_for('index'))

    try:
        # Process the data using online dataset
        output_file, error = process_billboard_data(BILLBOARD_DATA_URL, artist_name)

        if error:
            flash(error, 'error')
            return redirect(url_for('index'))

        # Send the file for download
        return send_file(
            output_file,
            as_attachment=True,
            download_name=f'{artist_name.title().replace(" ", "_")}_Chart_History.xlsx',
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
