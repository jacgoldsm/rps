"""
PostgreSQL migration script to make email field optional
Run this with: railway run python make_email_optional_postgres.py
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
import sqlalchemy as sa
from sqlalchemy import create_engine, text

# Get database configuration
database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

# Fix for SQLAlchemy compatibility with postgres:// vs postgresql://
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if not database_url:
    print("ERROR: No PostgreSQL database URL found in environment variables")
    print("Make sure DATABASE_URL or POSTGRES_URL is set")
    sys.exit(1)

print(f"Connecting to database...")
print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")

try:
    # Create engine
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            print("\nChecking current schema...")

            # Check if email column exists and is nullable
            result = conn.execute(text("""
                SELECT column_name, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'user' AND column_name = 'email'
            """))

            email_col = result.fetchone()

            if email_col:
                print(f"Current email column: nullable={email_col[1]}")
            else:
                print("ERROR: Email column not found!")
                sys.exit(1)

            if email_col[1] == 'YES':
                print("\n✓ Email column is already nullable. No migration needed.")
            else:
                print("\nMaking email field optional...")

                # Drop NOT NULL constraint
                conn.execute(text('ALTER TABLE "user" ALTER COLUMN email DROP NOT NULL'))
                print("✓ Email NOT NULL constraint removed")

                # Drop UNIQUE constraint if it exists
                try:
                    # First, find the constraint name
                    result = conn.execute(text("""
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_name = 'user'
                        AND constraint_type = 'UNIQUE'
                        AND constraint_name LIKE '%email%'
                    """))
                    constraint = result.fetchone()

                    if constraint:
                        constraint_name = constraint[0]
                        conn.execute(text(f'ALTER TABLE "user" DROP CONSTRAINT {constraint_name}'))
                        print(f"✓ Email UNIQUE constraint ({constraint_name}) removed")
                    else:
                        print("  (No email UNIQUE constraint found)")
                except Exception as e:
                    print(f"  Note: Could not remove UNIQUE constraint: {e}")

            # Commit transaction
            trans.commit()
            print("\n✓ Migration completed successfully!")

        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error during migration: {e}")
            print("\nTransaction rolled back. Database unchanged.")
            sys.exit(1)

except Exception as e:
    print(f"\n✗ Error connecting to database: {e}")
    sys.exit(1)
