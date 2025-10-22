# Billboard Hot 100 Chart Analyzer - Web App

A Flask web application for analyzing Billboard Hot 100 chart performance by artist.

## Features

- Clean, modern web interface
- Enter any artist name to generate chart history
- Upload custom CSV files or use default data
- Download Excel files directly from browser
- Mobile-responsive design

## Installation

1. Make sure you have Python 3 installed
2. Run the startup script:
   ```bash
   ./start_webapp.sh
   ```

This will automatically:
- Create a virtual environment
- Install all dependencies
- Start the Flask server

## Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py
```

## Usage

1. Open your browser and go to: `http://localhost:5000`
2. Enter the artist name you want to analyze
3. (Optional) Upload a custom Billboard CSV file
4. Click "Generate Chart History"
5. Your Excel file will download automatically

## Default Data Location

The app looks for `hot100.csv` at: `/Users/prangonbarua/Desktop/hot100.csv`

You can also upload your own CSV file through the web interface.

## CSV Format

Your CSV file should contain these columns:
- **Date** - Chart date
- **Song** - Song title
- **Artist** - Artist name
- **Rank** - Chart position (1-100)

## Stopping the Server

Press `CTRL+C` in the terminal to stop the Flask server.

## Tech Stack

- Python 3
- Flask (web framework)
- Pandas (data processing)
- openpyxl (Excel file generation)
- HTML/CSS (frontend)
