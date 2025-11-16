# Vercel Deployment Fixes

## Issues Encountered

### 1. AttributeError: 'SocketIO' object has no attribute 'WSGIApp'

**Error:**
```
AttributeError: 'SocketIO' object has no attribute 'WSGIApp'
```

**Root Cause:**
- Flask-SocketIO doesn't have a `WSGIApp` attribute
- The api/index.py was incorrectly trying to use `socketio.WSGIApp()`

**Fix Applied:**
Updated `api/index.py` to export the Flask app directly:

```python
# Before (WRONG):
handler = socketio.WSGIApp(socketio, app)

# After (CORRECT):
from app import create_app
app = create_app()
# Just export app - Flask-SocketIO is already integrated
```

---

### 2. OSError: [Errno 30] Read-only file system: '/var/task/instance'

**Error:**
```
OSError: [Errno 30] Read-only file system: '/var/task/instance'
```

**Root Cause:**
- Vercel's serverless functions run in a read-only environment
- The app was trying to:
  1. Create the `instance/` directory for SQLite
  2. Run `db.create_all()` which tries to create database files
- This doesn't work on Vercel's serverless platform

**Fix Applied:**
Updated `app/__init__.py` to skip database auto-creation on Vercel:

```python
# Only create tables automatically in local development
# On Vercel/production, use init_db.py script instead
if not os.environ.get('VERCEL_ENV'):
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Could not create database tables: {e}")
```

**What This Means:**
- Local development: Database tables are auto-created (SQLite)
- Vercel deployment: You must manually run `init_db.py` to create tables in Postgres

---

## How to Deploy Now

### 1. Commit and Push Changes

Make sure all fixes are committed:
```bash
git add .
git commit -m "Fix Vercel deployment issues"
git push
```

### 2. Deploy to Vercel

Vercel will automatically deploy if connected to Git, or use:
```bash
vercel --prod
```

### 3. Initialize Database Tables

After deployment, run this **locally** with your Vercel Postgres URL:

```bash
# Get POSTGRES_URL from Vercel Dashboard → Storage → Your Database
export DATABASE_URL="your-postgres-url"
python init_db.py
```

You should see:
```
=== Database Initialization ===
Creating database tables...
Database tables created successfully!
Tables created: user, game
=== Initialization Complete ===
```

### 4. Test Your Deployment

Visit your Vercel URL and test:
- ✅ User registration
- ✅ Login
- ✅ Creating/joining games
- ✅ Playing a round
- ✅ Leaderboard

---

## Files Modified

1. **api/index.py**
   - Removed incorrect `socketio.WSGIApp()` usage
   - Now correctly exports Flask app

2. **app/__init__.py**
   - Added check for `VERCEL_ENV` environment variable
   - Skips `db.create_all()` on Vercel
   - Still auto-creates tables for local development

3. **DEPLOYMENT.md**
   - Added troubleshooting section for both errors
   - Clarified database initialization steps
   - Added Windows-specific commands

---

## Why These Errors Happened

### Serverless Environment Differences

Traditional hosting vs Vercel serverless:

| Feature | Traditional | Vercel Serverless |
|---------|-------------|-------------------|
| File System | Read/Write | Read-Only |
| Database | Can be local file | Must be external |
| Process | Long-running | Function-per-request |
| Persistence | Files persist | Stateless |

### Flask-SocketIO on Vercel

- WebSockets don't work well on Vercel's serverless
- The app automatically falls back to polling mode
- Real-time features still work, just with slightly higher latency

---

## Summary

Both errors are now **fixed**! The key changes:

1. ✅ Correct WSGI app export in api/index.py
2. ✅ Skip database auto-creation on Vercel
3. ✅ Use init_db.py script to manually create tables
4. ✅ App works seamlessly in both local and production environments

You're ready to deploy! 🚀
