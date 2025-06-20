from supabase import create_client
from config import DevelopmentConfig
import os

def is_ddl_statement(sql: str) -> bool:
    """Check if a SQL statement is a DDL statement"""
    ddl_keywords = [
        'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'RENAME', 'GRANT', 'REVOKE'
    ]
    upper_sql = sql.upper()
    return any(keyword in upper_sql.split() for keyword in ddl_keywords)

def run_migrations():
    """Run all migrations in sequence"""
    try:
        # Initialize Supabase client
        config = DevelopmentConfig()
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        # Get all migration files in order
        migration_files = sorted([f for f in os.listdir('migrations') if f.endswith('.sql')])
        
        print("\nRunning migrations...")
        print("=" * 80)
        
        for migration_file in migration_files:
            print(f"\nExecuting {migration_file}...")
            
            # Read migration file
            with open(f'migrations/{migration_file}', 'r') as f:
                sql = f.read()
            
            # Split into statements
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                print(f"\nExecuting statement {i}/{len(statements)}:")
                print("-" * 40)
                print(statement)
                print("-" * 40)
                
                try:
                    if is_ddl_statement(statement):
                        # Use exec_ddl for DDL statements
                        result = supabase.postgrest.rpc('exec_ddl', {'ddl_query': statement}).execute()
                    else:
                        # Use exec_sql for DML statements
                        result = supabase.postgrest.rpc('exec_sql', {'query': statement}).execute()
                    print(f"Success!")
                except Exception as e:
                    print(f"Error executing statement: {str(e)}")
                    return False
            
            print(f"\nCompleted {migration_file}")
            
        print("\nAll migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error running migrations: {str(e)}")
        return False

if __name__ == "__main__":
    if not run_migrations():
        exit(1) 