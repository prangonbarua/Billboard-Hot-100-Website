# 🚀 Host Your Billboard Hot 100 Website

## Easiest Option: Railway.app (5 minutes)

### Step-by-Step:

1. **Push to GitHub** (if not already):
   ```bash
   cd /Users/prangonbarua/Billboard-Hot-100-Website
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy to Railway**:
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway automatically detects Flask and deploys!
   - Get your URL: `https://your-app.railway.app`

3. **Share with friends**:
   - Send them: `https://your-app.railway.app/hot100`

### Cost:
- First $5 free
- Then ~$5/month
- No cold starts (always fast)

---

## Free Option: Render.com

1. **Sign up**: https://render.com
2. **New Web Service**:
   - Connect GitHub
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
   - Free tier
3. **Note**: Spins down after 15 min inactivity

---

## Files Already Created for You ✅

- ✅ `requirements.txt` - All dependencies
- ✅ `Procfile` - Start command
- ✅ `.gitignore` - Files to ignore
- ✅ `DEPLOYMENT.md` - Full deployment guide

---

## Before Deploying

### Update Secret Key (Important!):
Open `app.py` and change line 13:
```python
app.secret_key = 'your-secret-random-string-here-make-it-long'
```

Generate a secure key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Data File Handling

Your `hot100.csv` is on Desktop. Options:

### Option 1: Include in Git (Simplest)
```bash
cp ~/Desktop/hot100.csv /Users/prangonbarua/Billboard-Hot-100-Website/
git add hot100.csv
git commit -m "Add data file"
git push
```

### Option 2: Auto-download (Already setup!)
Your `auto_update_data.py` script already handles this.
Just make sure Kaggle credentials are set up.

---

## Test Locally First

```bash
# Install gunicorn
pip3 install gunicorn

# Test production mode
gunicorn app:app

# Visit http://localhost:8000
```

---

## Quick Commands

```bash
# View your files ready for deployment
ls -la

# Check git status
git status

# Push changes
git add .
git commit -m "Ready for deployment"
git push
```

---

## Need Help?

- Railway Support: https://railway.app/help
- Render Docs: https://render.com/docs/deploy-flask
- My guide: See `DEPLOYMENT.md` for detailed options

**Estimated time to deploy: 5-10 minutes** ⚡
