# 🚨 Railway Deployment Fix Guide

## Common Issues & Solutions

### Issue 1: "Application Failed to Respond" or Crash Loop

**Most likely causes:**
1. Missing `hot100.csv` data file
2. Not enough memory to load 35MB CSV
3. Wrong Python version
4. Missing dependencies

### ✅ Solution: Upload Data File to Railway

**Option A: Include CSV in Git (Recommended)**

```bash
# Copy CSV to project root
cp ~/Desktop/hot100.csv /Users/prangonbarua/Billboard-Hot-100-Website/

# Add to git
cd /Users/prangonbarua/Billboard-Hot-100-Website
git add hot100.csv
git commit -m "Add data file for Railway"
git push

# Railway will automatically redeploy
```

**Option B: Environment Variable (if file too large)**

1. In Railway dashboard, go to your project
2. Click "Variables" tab
3. Add: `SKIP_DATA_UPDATE=true`
4. Upload `hot100.csv` manually via Railway CLI or link to external storage

---

### Issue 2: Port Configuration

Railway provides a `PORT` environment variable. Make sure your app uses it.

**Already fixed in your code:**
```python
port = int(os.environ.get('PORT', 5001))
```

---

### Issue 3: Memory Issues (35MB CSV)

**Fix: Optimize Memory**

In Railway dashboard:
1. Go to Settings
2. Increase memory limit (if on paid plan)
3. Or optimize CSV loading (already done in code)

---

### Issue 4: Missing Dependencies

**Check `requirements.txt`:**
```bash
cat requirements.txt
```

Should include:
- Flask
- pandas
- gunicorn
- openpyxl
- requests

---

## 🔍 Debug Railway Logs

1. **View Logs in Railway**:
   - Go to Railway project
   - Click "Deployments"
   - Click latest deployment
   - View "Build Logs" and "Deploy Logs"

2. **Look for these errors**:
   - `FileNotFoundError: Billboard data not found`
     → **Fix**: Upload hot100.csv to git

   - `MemoryError` or `Killed`
     → **Fix**: Upgrade Railway plan or optimize data loading

   - `ModuleNotFoundError`
     → **Fix**: Check requirements.txt has all dependencies

   - `Address already in use`
     → **Fix**: Already handled by $PORT variable

---

## 📋 Railway Deployment Checklist

Before deploying, ensure:

- [ ] `hot100.csv` is in project root OR data/ directory
- [ ] `requirements.txt` includes gunicorn
- [ ] `Procfile` has correct start command
- [ ] Git repo is up to date
- [ ] Railway is connected to correct GitHub repo
- [ ] Railway auto-deploys are enabled

---

## 🚀 Quick Fix Commands

```bash
# 1. Make sure CSV is in project
cp ~/Desktop/hot100.csv /Users/prangonbarua/Billboard-Hot-100-Website/

# 2. Check file exists
ls -lh hot100.csv

# 3. Test locally with gunicorn (production mode)
gunicorn app:app --bind 0.0.0.0:5001

# 4. If works locally, push to git
git add .
git commit -m "Fix: Add data file and Railway config"
git push

# Railway will auto-redeploy
```

---

## 🔧 Railway Configuration Files

I've created these files for you:

1. **railway.json** - Railway-specific config
2. **nixpacks.toml** - Build configuration
3. **Procfile** - Start command with proper timeouts
4. **.gitignore** - Excludes unnecessary files

---

## 🆘 Still Crashing? Try This:

### Step 1: Check Railway Build Logs
Look for the EXACT error message in Railway's deploy logs.

### Step 2: Test Locally with Gunicorn
```bash
# Install gunicorn
pip3 install gunicorn

# Run like Railway does
PORT=5001 gunicorn app:app --bind 0.0.0.0:5001 --workers 2 --timeout 120

# Visit http://localhost:5001
```

If it works locally but not on Railway, it's likely a data file issue.

### Step 3: Verify Data File
```bash
# In Railway dashboard, check "Files" or logs:
# Should show: "✓ Found data file: hot100.csv"
```

---

## 📊 Alternative: Use Smaller Data File

If 35MB is too large for Railway free tier:

1. **Filter to recent years only**:
```python
# Add to app.py after loading CSV
BILLBOARD_DATA = BILLBOARD_DATA[
    pd.to_datetime(BILLBOARD_DATA['Date']) >= '2020-01-01'
]
```

2. **Save smaller file**:
```bash
# Creates a smaller CSV with only recent data
python3 -c "
import pandas as pd
df = pd.read_csv('hot100.csv')
df = df[pd.to_datetime(df['Date']) >= '2020-01-01']
df.to_csv('hot100_recent.csv', index=False)
"
```

---

## 💡 Pro Tips

1. **Monitor Railway Usage**: Check if you're hitting memory limits
2. **Enable Auto-Deploy**: Railway will redeploy on every git push
3. **Use Environment Variables**: For API keys and secrets
4. **Check Build Time**: Should complete in 1-2 minutes

---

## 📞 Need Help?

**Railway Support**: https://railway.app/help

**Copy this error info when asking for help:**
- Deployment logs (from Railway dashboard)
- Error message
- Your Python version: `python3 --version`
- File sizes: `ls -lh hot100.csv`
