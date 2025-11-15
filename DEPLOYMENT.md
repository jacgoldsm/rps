# Deployment Guide: Vercel + Postgres

This guide will help you deploy your Rock Paper Scissors game to Vercel with Postgres database.

## Prerequisites

- [Vercel Account](https://vercel.com/signup)
- [Vercel CLI](https://vercel.com/cli) (optional but recommended)
- Git repository with your code

## Step 1: Prepare Your Vercel Postgres Database

1. Go to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Click on **Storage** tab
3. Click **Create Database**
4. Select **Postgres**
5. Choose a database name (e.g., `rps-database`)
6. Select your region (choose one close to your users)
7. Click **Create**

## Step 2: Link Database to Your Project

After creating the database, Vercel will provide connection details. You'll need to:

1. Go to your project settings
2. Navigate to **Storage** tab
3. Connect your newly created Postgres database
4. Vercel will automatically add these environment variables:
   - `POSTGRES_URL`
   - `POSTGRES_PRISMA_URL`
   - `POSTGRES_URL_NON_POOLING`
   - And others...

Our app is configured to use `POSTGRES_URL` or `DATABASE_URL`.

## Step 3: Set Environment Variables

In your Vercel project settings, add the following environment variable:

1. Go to **Settings** → **Environment Variables**
2. Add these variables:

```
SECRET_KEY=your-random-secret-key-generate-a-strong-one
FLASK_ENV=production
```

To generate a strong secret key, run:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 4: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard (Recommended for first-time)

1. Go to [Vercel Dashboard](https://vercel.com/new)
2. Click **Import Project**
3. Import your Git repository (GitHub, GitLab, or Bitbucket)
4. Vercel will auto-detect the project configuration from `vercel.json`
5. Click **Deploy**

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI globally
npm i -g vercel

# Login to Vercel
vercel login

# Deploy (from your project directory)
cd /path/to/rps
vercel

# For production deployment
vercel --prod
```

## Step 5: Initialize Database Tables

After your first deployment, you need to create the database tables:

### Option A: Run init script locally

```bash
# Set your production database URL
export DATABASE_URL="your-vercel-postgres-url"

# Run the initialization script
python init_db.py
```

### Option B: Use Vercel CLI to run the script

```bash
# This will run the script on Vercel's infrastructure
vercel env pull .env.production
python init_db.py
```

### Option C: Trigger it via a one-time API call

You could also add a one-time initialization endpoint, but make sure to secure it!

## Step 6: Verify Deployment

1. Visit your deployed URL (e.g., `https://your-app.vercel.app`)
2. Try to register a new account
3. Create a game and test the gameplay
4. Check the leaderboard

## Important Notes

### WebSocket Limitations

Vercel has limitations with long-lived WebSocket connections. Our app is configured to:
- Use **polling as the primary transport** on Vercel
- Fall back to WebSocket if available
- This means the real-time features will work, but with slightly higher latency

The Socket.IO configuration in `app/__init__.py` handles this automatically:
```python
if os.environ.get('VERCEL_ENV'):
    socketio_options['transports'] = ['polling', 'websocket']
```

### Database Connection Pooling

Our configuration uses connection pooling settings optimized for serverless:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

### Session Management

In production, sessions are configured to be secure:
```python
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

## Continuous Deployment

Once connected to Git, Vercel will automatically deploy:
- **Production**: Deployments from `main` branch
- **Preview**: Deployments from other branches (for testing)

## Troubleshooting

### Database Connection Errors

If you see database connection errors:
1. Check that `POSTGRES_URL` or `DATABASE_URL` is set in Vercel environment variables
2. Verify the database is in the same region as your deployment
3. Check that tables are initialized (run `init_db.py`)

### Import Errors

If you see module import errors:
1. Make sure all dependencies are in `requirements.txt`
2. Check that `vercel.json` is configured correctly
3. Verify that `api/index.py` exists

### Socket.IO Not Working

If real-time features aren't working:
1. Check browser console for Socket.IO connection errors
2. Verify CORS settings in `app/__init__.py`
3. The app should automatically fall back to polling mode

### Static Files Not Loading

If CSS/JS files aren't loading:
1. Check the routes in `vercel.json`
2. Verify static files are in `app/static/`
3. Check browser network tab for 404 errors

## Local Development

To test locally with Postgres:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your local Postgres URL:
   ```
   DATABASE_URL=postgresql://user:password@localhost/rps_dev
   ```

3. Run the app:
   ```bash
   python run.py
   ```

## Monitoring and Logs

View logs in Vercel Dashboard:
1. Go to your project
2. Click **Deployments**
3. Select a deployment
4. View **Functions** logs

## Scaling

Vercel automatically scales your application based on traffic. The Postgres database also scales, but you may need to upgrade your plan for:
- More storage
- More concurrent connections
- Better performance

## Cost Estimates

- **Vercel**: Free tier available, Pro plans start at $20/month
- **Vercel Postgres**: Free tier with limitations, Pro plans start at $20/month

## Security Checklist

- [ ] Changed `SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production`
- [ ] Database credentials are secure (managed by Vercel)
- [ ] HTTPS is enabled (automatic on Vercel)
- [ ] Session cookies are secure in production

## Need Help?

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Postgres Docs](https://vercel.com/docs/storage/vercel-postgres)
- [Flask-SocketIO Docs](https://flask-socketio.readthedocs.io/)

---

## Quick Reference

### Environment Variables Needed
- `SECRET_KEY` - Random secret key for Flask sessions
- `POSTGRES_URL` or `DATABASE_URL` - Database connection (auto-set by Vercel)
- `VERCEL_ENV` - Environment name (auto-set by Vercel)

### Key Files for Deployment
- `vercel.json` - Vercel configuration
- `api/index.py` - Serverless function entry point
- `requirements.txt` - Python dependencies
- `config.py` - App configuration with Postgres support
- `init_db.py` - Database initialization script

### Deployment Commands
```bash
# Deploy preview
vercel

# Deploy production
vercel --prod

# View logs
vercel logs

# Pull environment variables
vercel env pull
```
