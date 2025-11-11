# Deployment Guide - Billboard Hot 100 Website

## Quick Deploy to Railway (Easiest)

1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Create Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repo**: Choose your Billboard-Hot-100-Website repo
4. **Auto Deploy**: Railway will automatically:
   - Detect Flask application
   - Install dependencies from requirements.txt
   - Deploy your app
5. **Get URL**: Railway will provide a public URL like `your-app.railway.app`

### Environment Variables (Optional)
If you want Spotify integration:
- `SPOTIPY_CLIENT_ID`: Your Spotify client ID
- `SPOTIPY_CLIENT_SECRET`: Your Spotify client secret

---

## Deploy to Render.com (Free Tier)

1. **Sign up**: Go to [render.com](https://render.com) and sign up
2. **New Web Service**: Click "New" → "Web Service"
3. **Connect GitHub**: Authorize and select your repo
4. **Configure**:
   - **Name**: billboard-hot100
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. **Deploy**: Click "Create Web Service"
6. **URL**: Get your public URL at `your-app.onrender.com`

**Note**: Free tier spins down after 15 minutes of inactivity (takes 30s to spin up)

---

## Deploy to PythonAnywhere (Free Tier)

1. **Sign up**: Go to [pythonanywhere.com](https://www.pythonanywhere.com) and create account
2. **Upload Files**:
   - Go to "Files" tab
   - Upload your project files
   - Upload hot100.csv to your home directory
3. **Web Tab**:
   - Click "Add a new web app"
   - Choose "Flask" framework
   - Select Python 3.9
4. **Configure WSGI**:
   - Edit the WSGI configuration file
   - Point to your app.py file
5. **Install Dependencies**:
   - Open Bash console
   - Run: `pip3 install --user -r requirements.txt`
6. **Reload**: Click "Reload" on Web tab
7. **URL**: `yourusername.pythonanywhere.com`

---

## Deploy to Fly.io (Advanced)

1. **Install flyctl**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Launch**: `fly launch` (in project directory)
4. **Deploy**: `fly deploy`

---

## Important Notes

### Data File Considerations
Your `hot100.csv` file (34.8MB) options:
1. **Include in repo**: GitHub allows files up to 100MB
2. **Auto-download**: Use your existing `auto_update_data.py` script
3. **Cloud storage**: Store on S3/GCS and download on startup

### Production Checklist
- [ ] Change `app.secret_key` in app.py to a secure random string
- [ ] Set `debug=False` in production
- [ ] Use environment variables for sensitive data
- [ ] Consider adding rate limiting back for production
- [ ] Monitor usage and costs

### Recommended: Railway
**Why**:
- Easiest deployment (one click)
- Automatic HTTPS
- Good performance
- $5/month (first $5 free)
- No cold starts
- Can handle large CSV files

### For Friends Access
Once deployed, just share the URL:
- Railway: `https://your-app.railway.app/hot100`
- Render: `https://your-app.onrender.com/hot100`
- PythonAnywhere: `https://yourusername.pythonanywhere.com/hot100`

---

## Support Resources
- Railway Docs: https://docs.railway.app/
- Render Docs: https://render.com/docs
- PythonAnywhere Help: https://help.pythonanywhere.com/
