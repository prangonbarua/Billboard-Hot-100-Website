# Billboard Hot 100 Website - Production Deployment Guide

## Overview
This guide covers deploying your Billboard Hot 100 website to a production environment with proper security.

---

## 1. Hosting Options

### Option A: Railway (Recommended - Easiest)
**Pros:**
- Free tier available
- Automatic HTTPS
- GitHub integration
- Auto-deploys on git push
- Built-in domain support

**Steps:**
1. Sign up at https://railway.app
2. Connect your GitHub repository
3. Railway auto-detects Flask app
4. Add environment variables
5. Deploy!

**Cost:** Free tier includes 500 hours/month, $5/month for hobby plan

---

### Option B: Render
**Pros:**
- Generous free tier
- Automatic HTTPS
- Easy setup
- Good for Python apps

**Steps:**
1. Sign up at https://render.com
2. Create new "Web Service"
3. Connect GitHub repo
4. Select "Python" environment
5. Deploy

**Cost:** Free tier available, paid plans from $7/month

---

### Option C: DigitalOcean App Platform
**Pros:**
- Scalable
- Professional-grade
- Good documentation

**Cost:** Starts at $5/month

---

### Option D: VPS (Advanced - Full Control)
**Options:**
- DigitalOcean Droplets ($6/month)
- Linode ($5/month)
- Vultr ($5/month)

**Requires:** More setup (Nginx, SSL, etc.)

---

## 2. Domain Setup

### Getting a Domain
**Registrars:**
- Namecheap (recommended, ~$10/year for .com)
- Google Domains
- Cloudflare Registrar (at-cost pricing)
- GoDaddy

### DNS Configuration
After deploying, point your domain to your hosting:

**For Railway/Render:**
1. Get deployment URL from platform
2. Add CNAME record in DNS:
   - Type: CNAME
   - Name: www
   - Value: your-app.railway.app (or render URL)
3. Add A record for root domain (if supported)

**DNS propagation takes 1-48 hours**

---

## 3. Security Checklist

### CRITICAL SECURITY FIXES

#### 3.1 Change Secret Key
```python
# In app.py, change this line:
app.secret_key = 'billboard_hot_100_secret_key_change_in_production'

# TO (use environment variable):
import os
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
```

**Generate a secure key:**
```bash
python3 -c 'import os; print(os.urandom(24).hex())'
```

#### 3.2 Enable Rate Limiting
Install Flask-Limiter:
```bash
pip install Flask-Limiter
```

Add to `app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Apply to expensive endpoints
@app.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def analyze():
    # ... existing code
```

#### 3.3 Add CORS Protection
```bash
pip install flask-cors
```

```python
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "https://yourdomain.com"}})
```

#### 3.4 Disable Debug Mode
```python
# In app.py, at bottom:
if __name__ == '__main__':
    # Change debug=True to:
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
```

#### 3.5 Use Production WSGI Server
Replace Flask's development server with Gunicorn:

```bash
pip install gunicorn
```

Create `Procfile`:
```
web: gunicorn app:app
```

#### 3.6 Environment Variables
**Never commit sensitive data!**

Create `.env` file (add to .gitignore):
```env
SECRET_KEY=your-generated-secret-key-here
FLASK_ENV=production
SPOTIPY_CLIENT_ID=your-spotify-id
SPOTIPY_CLIENT_SECRET=your-spotify-secret
```

Install python-dotenv:
```bash
pip install python-dotenv
```

In `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

#### 3.7 Add Security Headers
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

#### 3.8 Update .gitignore
```
# Add these to .gitignore
.env
*.pyc
__pycache__/
.DS_Store
*.csv
data/
kaggle.json
.kaggle/
```

---

## 4. Performance Optimizations

### 4.1 Enable Caching
```bash
pip install flask-caching
```

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/artists')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_artists():
    # ... existing code
```

### 4.2 Compress Responses
```bash
pip install flask-compress
```

```python
from flask_compress import Compress
Compress(app)
```

### 4.3 Use CDN for Static Files
Consider hosting fonts/CSS on:
- Cloudflare CDN
- AWS S3 + CloudFront
- Vercel

---

## 5. SSL/HTTPS Setup

### Automatic (Railway/Render)
✅ Automatic HTTPS - no setup needed!

### Manual (VPS)
Use Let's Encrypt (free SSL):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 6. Monitoring & Logging

### 6.1 Add Error Logging
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('error.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)
```

### 6.2 Monitoring Services
- **Sentry** - Error tracking (free tier)
- **UptimeRobot** - Uptime monitoring (free)
- **Google Analytics** - Traffic analytics

---

## 7. Backup Strategy

### 7.1 Automated Backups
Set up weekly CSV backups to:
- AWS S3
- Google Drive
- GitHub (for small files)

### 7.2 Database Snapshots
If using a database, enable automatic backups on your hosting platform.

---

## 8. Legal Considerations

### 8.1 Add Terms of Service
Create `/templates/terms.html` with:
- Data usage policy
- Trademark disclaimer (Billboard™)
- No warranty clause

### 8.2 Add Privacy Policy
Required if collecting any user data:
- Analytics cookies
- IP addresses (for rate limiting)
- User searches

### 8.3 DMCA Compliance
Add DMCA contact info in footer/about page.

---

## 9. Quick Start Deployment (Railway)

### Step-by-Step:

1. **Prepare your repo:**
```bash
cd /Users/prangonbarua/Billboard-Hot-100-Website

# Update requirements.txt
pip freeze > requirements.txt

# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Update .gitignore
echo ".env" >> .gitignore
echo "*.pyc" >> .gitignore
```

2. **Push to GitHub:**
```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

3. **Deploy on Railway:**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Flask
   - Click "Deploy"

4. **Add Environment Variables:**
   - In Railway dashboard → Variables tab
   - Add `SECRET_KEY`
   - Add `FLASK_ENV=production`

5. **Set up Custom Domain:**
   - In Railway → Settings → Domains
   - Add your custom domain
   - Update DNS records as shown

6. **Done!** Your site is live with HTTPS! 🎉

---

## 10. Estimated Costs

### Minimal Setup (Recommended for Starting)
- **Domain:** $10-15/year (Namecheap)
- **Hosting:** $0 (Railway free tier) or $5/month
- **SSL:** $0 (included)
- **Total:** ~$10-15/year + optional $5/month

### Professional Setup
- **Domain:** $10-15/year
- **Hosting:** $12/month (Railway Pro or Render)
- **CDN:** $0 (Cloudflare free)
- **Monitoring:** $0 (free tiers)
- **Total:** ~$150/year

---

## 11. Pre-Deployment Checklist

- [ ] Change secret key to environment variable
- [ ] Add rate limiting
- [ ] Disable debug mode
- [ ] Add security headers
- [ ] Update .gitignore (no sensitive files)
- [ ] Install Gunicorn
- [ ] Create Procfile
- [ ] Test locally with production settings
- [ ] Set up error logging
- [ ] Add terms of service
- [ ] Add privacy policy
- [ ] Configure environment variables on hosting
- [ ] Test all features after deployment
- [ ] Set up monitoring
- [ ] Configure custom domain
- [ ] Enable HTTPS

---

## 12. Post-Deployment

### Regular Maintenance:
1. **Weekly:** Check error logs
2. **Weekly:** Update CSV data (automated via `weekly_update.py`)
3. **Monthly:** Review security updates
4. **Quarterly:** Update dependencies

### Keep Dependencies Updated:
```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Flask Security: https://flask.palletsprojects.com/en/2.3.x/security/
- Let's Encrypt: https://letsencrypt.org

---

**Good luck with your deployment! 🚀**
