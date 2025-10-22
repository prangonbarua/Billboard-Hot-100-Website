# Billboard Hot 100 Website

A modern web application for analyzing Billboard Hot 100 chart performance by artist.

## Features

- **Black-on-Black Aesthetic**: Sleek, minimalist design with pure black background
- **Simple Interface**: Just enter an artist name and download their chart history
- **No Upload Required**: Uses hosted Billboard Hot 100 dataset
- **Excel Export**: Download complete chart history as Excel files
- **Mobile Responsive**: Works on all devices

## Live Demo

[Coming Soon - Deploy to Render/Railway]

## Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py
```

Then open your browser to `http://localhost:5000`

## Deploy to Production

See [DEPLOYMENT_README.md](DEPLOYMENT_README.md) for detailed deployment instructions to:
- Render (Free hosting)
- Railway (Free hosting)

## Tech Stack

- **Backend**: Flask (Python)
- **Data Processing**: Pandas
- **Excel Generation**: openpyxl
- **Design**: Pure CSS with black-on-black theme
- **Font**: Arial

## How It Works

1. Enter an artist name
2. App fetches Billboard Hot 100 data from online dataset
3. Processes chart history for that artist
4. Generates Excel file with chart positions by date
5. Downloads automatically to your device

## Project Structure

```
Billboard-Hot-100-Website/
├── app.py                    # Flask application
├── templates/
│   └── index.html           # Main web interface
├── static/
│   └── style.css            # Black-on-black theme
├── requirements.txt         # Python dependencies
├── render.yaml             # Render deployment config
├── runtime.txt             # Python version
└── README.md               # This file
```

## License

MIT License - Feel free to use and modify!

## Created By

Prangon Barua
