"""
Migration script to add ELO change fields to Game model
Run this with: python add_elo_fields.py
"""

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    # Add the new columns using raw SQL
    try:
        with db.engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(db.text("PRAGMA table_info(game)"))
            columns = [row[1] for row in result]

            if 'player1_elo_change' not in columns:
                conn.execute(db.text("ALTER TABLE game ADD COLUMN player1_elo_change INTEGER DEFAULT 0"))
                conn.commit()
                print("Added player1_elo_change column")
            else:
                print("player1_elo_change column already exists")

            if 'player2_elo_change' not in columns:
                conn.execute(db.text("ALTER TABLE game ADD COLUMN player2_elo_change INTEGER DEFAULT 0"))
                conn.commit()
                print("Added player2_elo_change column")
            else:
                print("player2_elo_change column already exists")

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        print("If you're using a fresh database, you can simply delete the database file and run init_db.py again")
