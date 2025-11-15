"""
Database initialization script for production deployment
Run this script once after setting up your Vercel Postgres database
"""
import os
import sys

# Ensure we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import db

def init_database():
    """Initialize the database with tables"""
    app = create_app()

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nTables created: {', '.join(tables)}")

if __name__ == '__main__':
    print("=== Database Initialization ===")
    print(f"Database URL: {os.environ.get('DATABASE_URL', 'Not set')}\n")

    if not os.environ.get('DATABASE_URL') and not os.environ.get('POSTGRES_URL'):
        print("WARNING: No DATABASE_URL or POSTGRES_URL environment variable set!")
        print("Please set your database connection string before running this script.")
        sys.exit(1)

    try:
        init_database()
        print("\n=== Initialization Complete ===")
    except Exception as e:
        print(f"\nERROR: Failed to initialize database: {e}")
        sys.exit(1)
