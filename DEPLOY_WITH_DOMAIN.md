# Deploy to Your Custom Domain - Quick Guide

## How Hard Is It?
**Difficulty: 3/10** - It's easier than you think!
**Time: 1-2 hours** (mostly waiting for DNS)
**Cost: $5-12/month**

---

## What I Just Fixed (Security)

✅ **Secret Key** - Now uses environment variables (was hardcoded)
✅ **Rate Limiting** - Added (200 requests/day, 50/hour per IP)
✅ **CORS Protection** - Configured to only allow your domain
✅ **Requirements** - Cleaned up for production deployment

---

## Step-by-Step: Deploy to Railway (EASIEST)

### 1. Push Your Code to GitHub (2 min)
```bash
cd /Users/prangonbarua/Billboard-Hot-100-Website
git add .
git commit -m "Production ready with security fixes"
git push
```

### 2. Deploy to Railway (5 min)
1. Go to https://railway.app
2. Click "Login" → Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your Billboard repo
6. Railway auto-detects everything and deploys!

### 3. Add Environment Variables (3 min)
In Railway dashboard → Your project → Variables tab:

```
SECRET_KEY = abc123def456...
```
(Generate with: `python3 -c "import os; print(os.urandom(24).hex())"`)

```
ALLOWED_ORIGINS = https://yourdomain.com,https://www.yourdomain.com
```
(Replace with YOUR actual domain)

### 4. Connect Your Domain (10 min)
**In Railway:**
- Go to Settings → Networking → Custom Domain
- Enter: `yourdomain.com`
- Railway will show you DNS settings

**In Your Domain Registrar** (GoDaddy, Namecheap, etc.):
- Go to DNS Settings
- Add a CNAME record:
  - **Type:** CNAME
  - **Name:** @ (or leave blank for root)
  - **Value:** [the URL Railway gave you]
  - **TTL:** Automatic

- Add another CNAME for www:
  - **Type:** CNAME
  - **Name:** www
  - **Value:** [same URL]
  - **TTL:** Automatic

### 5. Wait (30-60 min)
DNS takes time to propagate worldwide. Check status at:
https://dnschecker.org

### 6. Done! 🎉
Your site is now live at:
- `https://yourdomain.com`
- `https://www.yourdomain.com`

Railway automatically handles HTTPS/SSL certificates!

---

## Alternative: Render (Has Free Tier)

### Steps:
1. Go to https://render.com → Sign in with GitHub
2. New → Web Service → Connect your repo
3. Configure:
   - **Name:** billboard-hot100
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Add environment variables (same as Railway)
5. Settings → Custom Domain → Add your domain
6. Update DNS at your registrar (same process as Railway)

**Note:** Free tier sleeps after 15 min inactive (takes 30s to wake)

---

## DNS Configuration Cheatsheet

Wherever you bought your domain (GoDaddy, Namecheap, Google Domains, etc.):

1. Login to your domain registrar
2. Find "DNS Management" or "DNS Settings"
3. Delete any existing A or CNAME records for @ and www
4. Add these records:

```
Type: CNAME
Name: @
Value: [your-app.railway.app or your-app.onrender.com]

Type: CNAME
Name: www
Value: [your-app.railway.app or your-app.onrender.com]
```

5. Save and wait 30-60 minutes

---

## Cost Breakdown

| Platform | Cost/Month | Free Tier? | Auto HTTPS? | My Rating |
|----------|------------|------------|-------------|-----------|
| **Railway** | $5-10 | $5 free credit | ✅ Yes | ⭐⭐⭐⭐⭐ Best |
| **Render** | $0 or $7 | ✅ 750 hrs/month | ✅ Yes | ⭐⭐⭐⭐ Good |
| **DigitalOcean** | $12 | ❌ No | ✅ Yes | ⭐⭐⭐ More control |
| **Vercel** | Free | ✅ Unlimited | ✅ Yes | ⭐⭐ Not ideal for this |

---

## Troubleshooting

### "Application Error" after deployment
- Check environment variables are set correctly
- Check logs in Railway/Render dashboard
- Make sure `hot100.csv` file is in your repo

### Domain not working after 1 hour
- Verify DNS records at https://dnschecker.org
- Make sure you REMOVED old DNS records
- Check you're using CNAME, not A records
- Try accessing with `https://` (not just `http://`)

### Site is slow
- Railway: Upgrade to $5/month plan (no cold starts)
- Render: Paid plan removes sleep ($7/month)
- Your 35MB CSV is fine, not the problem

### Weekly updates not running
- Add a cron job in Railway/Render
- Schedule: Every Saturday at 12pm
- Command: `python3 weekly_update.py`

---

## After Deployment - Updating Your Site

To make changes:
```bash
cd /Users/prangonbarua/Billboard-Hot-100-Website
# Make your changes
git add .
git commit -m "Update description"
git push
```

Railway/Render will automatically redeploy in 2-3 minutes!

---

## What You Get

✅ **Your site on your domain** (`yourdomain.com`)
✅ **Automatic HTTPS/SSL** (secure padlock in browser)
✅ **Rate limiting** (prevents abuse)
✅ **CORS protection** (only your domain can access API)
✅ **Weekly data updates** (can add cron job)
✅ **Auto-deploy** (push to GitHub = auto update site)

---

## My Recommendation

**Use Railway** because it's:
1. Easiest to set up (literally 3 clicks)
2. No cold starts (site stays fast)
3. Great logs and monitoring
4. Perfect for Flask apps
5. Generous free tier to test first
6. Excellent documentation
7. Built-in SSL/HTTPS
8. Can handle your 35MB CSV easily

**Total time:** 1-2 hours (mostly waiting for DNS)
**Difficulty:** 3/10 (easier than setting up WordPress!)
**Result:** Professional, fast, secure website on your domain

---

## Need Help?

1. Check platform logs first (Railway/Render dashboard)
2. Verify environment variables are set
3. Check DNS propagation: https://dnschecker.org
4. Test without custom domain first (use Railway URL)

---

## Ready? Let's Deploy!

**Right now, your next steps:**
1. ✅ Code is ready (I fixed security)
2. ✅ Files are configured (requirements.txt, Procfile)
3. ⬜ Push to GitHub
4. ⬜ Sign up for Railway
5. ⬜ Deploy (3 clicks)
6. ⬜ Add environment variables
7. ⬜ Connect domain
8. ⬜ Wait for DNS
9. ⬜ 🎉 You're live!

Good luck! Your site will be professional and secure.
