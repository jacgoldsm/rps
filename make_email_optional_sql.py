"""
Simple SQL-only migration script to make email field optional
This version doesn't depend on Flask or SocketIO
Run this with: python make_email_optional_sql.py
"""

import sqlite3
import os

# Get database path from environment or use default
database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

# Check if we're using SQLite or PostgreSQL
if database_url and 'postgresql' in database_url:
    print("PostgreSQL database detected")
    print("For PostgreSQL, use this SQL command directly:")
    print()
    print("ALTER TABLE \"user\" ALTER COLUMN email DROP NOT NULL;")
    print("ALTER TABLE \"user\" DROP CONSTRAINT IF EXISTS user_email_key;")
    print()
    print("Connect to your Railway PostgreSQL and run the above commands.")
else:
    # SQLite migration
    db_path = 'instance/rps.db'

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Creating a new database with the correct schema...")
        # Database will be created when app runs
        print("Please run the app once to create the database with the new schema.")
    else:
        print(f"Found database at {db_path}")
        print("Migrating SQLite database...")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check current schema
            cursor.execute("PRAGMA table_info(user)")
            columns = cursor.fetchall()

            print("\nCurrent user table schema:")
            for col in columns:
                col_name = col[1]
                col_nullable = col[3]  # 0 = nullable, 1 = not null
                print(f"  {col_name}: {'NOT NULL' if col_nullable else 'NULL'}")

            print("\nMaking email field optional...")

            # SQLite doesn't support ALTER COLUMN, so we recreate the table
            cursor.execute("""
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
            """)

            # Copy data
            cursor.execute("""
                INSERT INTO user_new
                SELECT id, username, email, password_hash, elo_rating,
                       games_played, games_won, games_lost, games_tied, created_at
                FROM user
            """)

            # Drop old table and rename
            cursor.execute("DROP TABLE user")
            cursor.execute("ALTER TABLE user_new RENAME TO user")

            conn.commit()
            conn.close()

            print("✓ Email field is now optional (nullable)")
            print("✓ Email unique constraint removed")
            print("✓ Migration completed successfully!")

        except Exception as e:
            print(f"Error during migration: {e}")
            print("\nIf migration failed, you can:")
            print("1. Delete the database file: rm instance/rps.db")
            print("2. Run the app to create a fresh database with the new schema")
