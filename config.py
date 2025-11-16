import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

    # Fix for SQLAlchemy compatibility with postgres:// vs postgresql://
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    # Fallback to SQLite for local development
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///rps.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Production settings
    if os.environ.get('VERCEL_ENV') == 'production':
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_SAMESITE = 'Lax'