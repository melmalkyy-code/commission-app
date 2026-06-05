# Deployment Guide — Streamlit Cloud + Supabase

## Step 1: Create Supabase Database (5 min)
1. Go to https://supabase.com → Sign up free
2. Click "New Project" → Name it "commission-app"
3. Choose a strong password → remember it
4. Region: choose closest to you (e.g. EU West or US East)
5. Wait ~2 min for project to be ready
6. Go to: Settings → Database → Connection string → URI
7. Copy the connection string — looks like:
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres

## Step 2: Push Code to GitHub (3 min)
1. Go to github.com → New Repository → name: "commission-app" → Public → Create
2. On your computer, open CMD in the `web/` folder:
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/commission-app.git
   git push -u origin main

## Step 3: Deploy on Streamlit Cloud (3 min)
1. Go to https://share.streamlit.io → Sign in with GitHub
2. Click "New app"
3. Select your GitHub repo: commission-app
4. Main file path: Home.py
5. Click "Advanced settings" → Secrets → paste this:

[database]
url = "postgresql://postgres:YOUR_PASSWORD@db.YOURREF.supabase.co:5432/postgres"

6. Click "Deploy" — takes about 2 min
7. Your app is live at: https://YOUR_USERNAME-commission-app-home-XXXX.streamlit.app

## Step 4: Share the URL
Send the URL to your team. Anyone with the link can access it from any browser!

## Database Auto-Setup
The app automatically creates all tables and seeds sample data on first run.
No manual database setup needed.
