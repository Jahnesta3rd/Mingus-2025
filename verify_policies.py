import os
import sys
from supabase import create_client
from config import DevelopmentConfig

def verify_policies():
    """Verify table existence and policies"""
    try:
        # Initialize Supabase client
        config = DevelopmentConfig()
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        # Check if table exists
        table_query = """
        SELECT EXISTS (
            SELECT FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'important_dates'
        );
        """
        
        result = supabase.postgrest.rpc('exec_sql', {'query': table_query}).execute()
        if result.data and result.data[0]['exists']:
            print("\nTable 'important_dates' exists")
            
            # Check RLS status
            rls_query = """
            SELECT c.relrowsecurity
            FROM pg_class c
            WHERE c.relname = 'important_dates'
            AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
            """
            
            result = supabase.postgrest.rpc('exec_sql', {'query': rls_query}).execute()
            if result.data:
                print(f"RLS enabled: {result.data[0]['relrowsecurity']}")
            
            # List policies
            policy_query = """
            SELECT pol.polname, r.rolname, 
                   CASE pol.polcmd
                       WHEN 'r' THEN 'SELECT'
                       WHEN 'w' THEN 'UPDATE'
                       WHEN 'a' THEN 'INSERT'
                       WHEN 'd' THEN 'DELETE'
                       WHEN '*' THEN 'ALL'
                   END as cmd
            FROM pg_policy pol
            JOIN pg_roles r ON r.oid = pol.polrole
            WHERE pol.polrelid = 'important_dates'::regclass;
            """
            
            result = supabase.postgrest.rpc('exec_sql', {'query': policy_query}).execute()
            if result.data:
                print("\nPolicies:")
                for policy in result.data:
                    print(f"- {policy['polname']} ({policy['cmd']}) for role {policy['rolname']}")
            else:
                print("No policies found!")
        else:
            print("Table 'important_dates' does not exist!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    verify_policies() 