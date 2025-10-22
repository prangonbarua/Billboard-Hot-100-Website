# Billboard Hot 100 Analyzer - Deployment Guide

## Deploy to Render (Free Hosting)

### Quick Deploy

1. **Push to GitHub**
   - Make sure all changes are committed to the `automation-experiment` branch
   - Push to GitHub: `git push origin automation-experiment`

2. **Sign up for Render**
   - Go to https://render.com
   - Sign up with your GitHub account (it's free!)

3. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub repository: `Billboard-Hot-100-Datacollector`
   - Select the `automation-experiment` branch

4. **Configure Service**
   - **Name**: `billboard-hot-100-analyzer`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

5. **Deploy**
   - Click "Create Web Service"
   - Wait 2-3 minutes for deployment
   - Your app will be live at: `https://billboard-hot-100-analyzer.onrender.com`

### Alternative: Deploy to Railway

1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository and branch
5. Railway will auto-detect Flask and deploy

Your app will be live at a Railway URL like: `https://billboard-hot-100-analyzer.up.railway.app`

### Alternative: Deploy to Vercel

Note: Vercel requires a slightly different setup for Flask apps (using Vercel's serverless functions)

## Features

- Black-on-black aesthetic theme
- Arial font
- No CSV upload required (uses hosted Billboard data)
- Simple one-field form
- Download Excel files directly

## Public URL

Once deployed, share the public URL with anyone to use the analyzer!
