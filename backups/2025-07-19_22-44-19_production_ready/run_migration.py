import os
import sys
from supabase import create_client, Client
from config import DevelopmentConfig

def run_migration():
    """Run the RLS policy migration"""
    try:
        # Initialize Supabase client
        config = DevelopmentConfig()
        supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        # Read and execute the migration SQL
        with open('migrations/003_fix_rls_policies.sql', 'r') as f:
            sql = f.read()
            
        # Execute each statement separately
        statements = sql.split(';')
        for statement in statements:
            if statement.strip():
                supabase.postgrest.rpc('exec_sql', {'query': statement}).execute()
                
        print("Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Error running migration: {str(e)}")
        return False

if __name__ == "__main__":
    if not run_migration():
        sys.exit(1) 