"""
Database migration script to add is_quickplay column to Game table
Run this once to update your existing database
"""
import sqlite3
import os

def migrate_database():
    """Add is_quickplay column to Game table"""
    db_path = os.path.join('instance', 'rps.db')

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(game)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_quickplay' in columns:
            print("Column 'is_quickplay' already exists. Migration not needed.")
        else:
            # Add the new column
            cursor.execute("ALTER TABLE game ADD COLUMN is_quickplay BOOLEAN DEFAULT 0")
            conn.commit()
            print("Successfully added 'is_quickplay' column to Game table!")

    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
