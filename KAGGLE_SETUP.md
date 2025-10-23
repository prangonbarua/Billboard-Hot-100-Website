# Kaggle Auto-Update Setup Guide

This guide shows you how to set up automatic Billboard data updates from Kaggle.

## Step 1: Get Your Kaggle API Key

1. Go to https://www.kaggle.com (create account if needed)
2. Click on your profile picture (top right)
3. Click **"Settings"**
4. Scroll down to **"API"** section
5. Click **"Create New API Token"**
6. A file called `kaggle.json` will download

## Step 2: Install Kaggle API Key

### On Mac/Linux:
```bash
# Create kaggle directory
mkdir -p ~/.kaggle

# Move the downloaded kaggle.json file
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json

# Set proper permissions (important!)
chmod 600 ~/.kaggle/kaggle.json
```

### On Windows:
```cmd
# Create kaggle directory
mkdir %USERPROFILE%\.kaggle

# Move kaggle.json to that folder
move %USERPROFILE%\Downloads\kaggle.json %USERPROFILE%\.kaggle\kaggle.json
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Run the Auto-Updater

### Manual Update:
```bash
python3 auto_update_data.py
```

This will:
- Check if new Billboard data is available
- Download it if there's an update
- Extract CSV files to `data/` folder
- Copy `hot100.csv` to your Desktop

### Auto-Update on Startup:
The Flask app will automatically check for updates when it starts!

Just run:
```bash
python3 app.py
```

## How It Works

- **Dataset Source**: https://www.kaggle.com/datasets/ludmin/billboard/data
- **Update Frequency**: Kaggle dataset is updated weekly
- **Auto-Check**: Script checks for updates every time you run it
- **Smart Updates**: Only downloads if new data is available
- **Metadata Tracking**: Saves last update date in `data/metadata.json`

## Files Created

After running the auto-updater:
```
Billboard-Hot-100-Website/
├── data/
│   ├── hot-100-current.csv (or similar)
│   ├── metadata.json (tracks last update)
│   └── [other Billboard CSVs]
└── auto_update_data.py
```

## Troubleshooting

### "Kaggle API not configured"
- Make sure `kaggle.json` is in `~/.kaggle/`
- Check file permissions: `chmod 600 ~/.kaggle/kaggle.json`

### "kaggle module not found"
- Install it: `pip install kaggle`

### "401 Unauthorized"
- Your API token might be expired
- Generate a new one from Kaggle settings

## Weekly Auto-Updates (Advanced)

### Using Cron (Mac/Linux):
```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9 AM):
0 9 * * 1 cd /Users/prangonbarua/Billboard-Hot-100-Website && python3 auto_update_data.py
```

### Using Task Scheduler (Windows):
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly, Monday, 9:00 AM
4. Action: Run `python3 auto_update_data.py`

## Benefits

- Always have the latest Billboard data
- No manual downloads needed
- Automatically updates all your Billboard projects
- One-time setup, forever automated!
