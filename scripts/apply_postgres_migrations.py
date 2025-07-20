import os
import psycopg2
from psycopg2 import sql

MIGRATIONS_DIR = 'migrations'

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable not set')

def get_migration_files():
    files = [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')]
    files.sort()  # Apply in order
    return files

def apply_migration(conn, filepath):
    with open(filepath, 'r') as f:
        sql_code = f.read()
    with conn.cursor() as cur:
        cur.execute(sql_code)
    print(f'Applied migration: {filepath}')

def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        for filename in get_migration_files():
            filepath = os.path.join(MIGRATIONS_DIR, filename)
            apply_migration(conn, filepath)
        conn.commit()
        print('All migrations applied successfully.')
    except Exception as e:
        conn.rollback()
        print(f'Error applying migrations: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    main() 