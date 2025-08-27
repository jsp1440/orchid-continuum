# Orchid Continuum Deployment Guide

## Quick Start
This Flask application can be deployed on:
- **Heroku** (easiest)
- **DigitalOcean App Platform**
- **AWS Elastic Beanstalk**
- **Google Cloud Run**
- **Any VPS with Python**

## Required Files
- `app.py` - Main Flask application
- `models.py` - Database models
- `routes.py` - Web routes
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates
- `static/` - CSS, JS, images
- `orchid_continuum.db` - Your database (12KB)
- Your photos in `static/orchid_photos/`

## Environment Variables Needed
```
DATABASE_URL=sqlite:///orchid_continuum.db
FLASK_SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key (optional)
```

## Simple Heroku Deployment
1. Download your project as ZIP
2. Extract and add `Procfile`: `web: gunicorn app:app`
3. Add `runtime.txt`: `python-3.11.0`
4. Upload to Heroku
5. Set environment variables in Heroku dashboard

## Your Working Files
- Database: `orchid_continuum.db` (4 orchid records)
- Photos: `attached_assets/*.png` (copy to `static/orchid_photos/`)
- Main code: All `.py` files in root directory

## Database Setup
The database already exists with your 4 orchid records. Just copy `orchid_continuum.db` to your new hosting.

## Photo Setup
Copy your photos from `attached_assets/` to `static/orchid_photos/` and update database image URLs to match.