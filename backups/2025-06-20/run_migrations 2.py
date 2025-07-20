import os
import sys
from config import DevelopmentConfig
from supabase import create_client, Client

def run_migrations():
    """Run migrations using Supabase REST API"""
    try:
        # Initialize Supabase client with service role key
        config = DevelopmentConfig()
        supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
        
        print("Running migrations...")
        
        # Get list of migration files
        migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])
        
        # Get list of executed migrations
        result = supabase.table('migrations').select('migration_name').execute()
        executed_migrations = {row['migration_name'] for row in result.data}
        
        for migration_file in migration_files:
            if migration_file in executed_migrations:
                print(f"Skipping already executed migration: {migration_file}")
                continue
                
            print(f"Running migration: {migration_file}")
            
            # Read migration file
            with open(os.path.join(migration_dir, migration_file), 'r') as f:
                migration_sql = f.read()
            
            try:
                # Execute migration SQL directly
                supabase.rpc('exec_sql', {'query': migration_sql}).execute()
                
                # Record migration
                supabase.table('migrations').insert({
                    'migration_name': migration_file
                }).execute()
                
                print(f"Completed migration: {migration_file}")
            except Exception as e:
                print(f"Error in migration {migration_file}: {str(e)}")
                raise
        
        print("\nAll migrations completed successfully!")
        
    except Exception as e:
        print(f"Error running migrations: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations() 