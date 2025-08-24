import os
import sys
from supabase import create_client, Client
from config import DevelopmentConfig

def run_migration():
    """Run the anonymous access fix migration"""
    try:
        # Initialize Supabase client
        config = DevelopmentConfig()
        supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        print("\nStarting migration...")
        print("=" * 80)
        
        # Read and execute the migration SQL
        with open('migrations/004_fix_anon_access.sql', 'r') as f:
            sql = f.read()
        
        # Split into individual statements and execute
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            print(f"\nExecuting statement {i}/{len(statements)}:")
            print("-" * 40)
            print(statement)
            print("-" * 40)
            
            try:
                result = supabase.postgrest.rpc('exec_sql', {'query': statement}).execute()
                print(f"Success! Result: {result.data if result.data else 'No data returned'}")
            except Exception as e:
                print(f"Error executing statement: {str(e)}")
                return False
        
        # Verify the changes
        print("\nVerifying policies after migration...")
        print("=" * 80)
        
        # First check if RLS is enabled
        rls_query = """
        SELECT c.relname, c.relrowsecurity 
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' 
        AND c.relname = 'important_dates';
        """
        
        try:
            result = supabase.postgrest.rpc('exec_sql', {'query': rls_query}).execute()
            if result.data:
                rls_enabled = result.data[0]['relrowsecurity']
                print(f"\nRLS enabled on important_dates: {rls_enabled}")
            else:
                print("\nCould not verify RLS status!")
                return False
                
            # Now check policies
            policy_query = """
            SELECT pol.polname as policy_name,
                   roles.rolname as role_name,
                   CASE pol.polcmd
                     WHEN 'r' THEN 'SELECT'
                     WHEN 'w' THEN 'UPDATE'
                     WHEN 'a' THEN 'INSERT'
                     WHEN 'd' THEN 'DELETE'
                     WHEN '*' THEN 'ALL'
                   END as command,
                   pg_get_expr(pol.polqual, pol.polrelid) as using_expr,
                   pg_get_expr(pol.polwithcheck, pol.polrelid) as with_check_expr
            FROM pg_policy pol
            JOIN pg_roles roles ON pol.polrole = roles.oid
            JOIN pg_class c ON c.oid = pol.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
            AND c.relname = 'important_dates';
            """
            
            result = supabase.postgrest.rpc('exec_sql', {'query': policy_query}).execute()
            
            if not result.data:
                print("No policies found after migration!")
                return False
            
            print("\nCurrent policies:")
            print("-" * 40)
            
            for policy in result.data:
                print(f"\nPolicy: {policy['policy_name']}")
                print(f"Role: {policy['role_name']}")
                print(f"Command: {policy['command']}")
                print(f"USING: {policy['using_expr']}")
                if policy['with_check_expr']:
                    print(f"WITH CHECK: {policy['with_check_expr']}")
                print("-" * 40)
            
        except Exception as e:
            print(f"Error verifying policies: {str(e)}")
            return False
            
        print("\nMigration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error running migration: {str(e)}")
        return False

if __name__ == "__main__":
    if not run_migration():
        sys.exit(1) 