"""
Simplest migration - uses only psycopg2 (no Flask, no SQLAlchemy)
Run this with: railway run python make_email_optional_simple.py
"""

import os
import psycopg2

# Get database URL
database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if not database_url:
    print("ERROR: No database URL found")
    exit(1)

# Parse the URL (format: postgresql://user:password@host:port/database)
# psycopg2 can use the URL directly
print("Connecting to database...")

try:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    print("Connected successfully!")
    print("\nMaking email field optional...")

    # Remove NOT NULL constraint
    cursor.execute('ALTER TABLE "user" ALTER COLUMN email DROP NOT NULL')
    print("✓ Email is now nullable")

    # Try to remove UNIQUE constraint
    try:
        # Find constraint name
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'user'
            AND constraint_type = 'UNIQUE'
            AND constraint_name LIKE '%email%'
        """)

        result = cursor.fetchone()
        if result:
            constraint_name = result[0]
            cursor.execute(f'ALTER TABLE "user" DROP CONSTRAINT {constraint_name}')
            print(f"✓ Removed UNIQUE constraint: {constraint_name}")
        else:
            print("  (No email UNIQUE constraint found)")
    except Exception as e:
        print(f"  Note: {e}")

    # Commit changes
    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ Migration completed successfully!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    exit(1)
