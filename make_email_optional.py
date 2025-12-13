"""
Migration script to make email field optional in User model
Run this with: python make_email_optional.py
"""

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Check current schema
            result = conn.execute(db.text("PRAGMA table_info(user)"))
            columns = {row[1]: row for row in result}

            print("Current user table schema:")
            for col_name, col_info in columns.items():
                print(f"  {col_name}: nullable={col_info[3] == 0}")

            # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
            print("\nMaking email field optional...")

            # Step 1: Create new table with updated schema
            conn.execute(db.text("""
                CREATE TABLE user_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    email VARCHAR(120),
                    password_hash VARCHAR(200) NOT NULL,
                    elo_rating INTEGER DEFAULT 1200,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    games_lost INTEGER DEFAULT 0,
                    games_tied INTEGER DEFAULT 0,
                    created_at DATETIME
                )
            """))

            # Step 2: Copy data from old table to new table
            conn.execute(db.text("""
                INSERT INTO user_new
                SELECT id, username, email, password_hash, elo_rating,
                       games_played, games_won, games_lost, games_tied, created_at
                FROM user
            """))

            # Step 3: Drop old table
            conn.execute(db.text("DROP TABLE user"))

            # Step 4: Rename new table to original name
            conn.execute(db.text("ALTER TABLE user_new RENAME TO user"))

            conn.commit()

            print("✓ Email field is now optional (nullable)")
            print("✓ Email unique constraint removed")
            print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        print("\nNote: If you're using a fresh database or this migration fails,")
        print("you can delete the database file and run init_db.py to start fresh.")
