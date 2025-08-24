from supabase import create_client
from config import DevelopmentConfig

def verify_schema():
    """Verify database schema"""
    try:
        # Initialize Supabase client
        config = DevelopmentConfig()
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        # List all tables
        tables_query = """
        SELECT array_to_json(array_agg(row_to_json(t)))
        FROM (
            SELECT tablename
            FROM pg_tables 
            WHERE schemaname = 'public'
        ) t;
        """
        
        result = supabase.postgrest.rpc('exec_sql', {'query': tables_query}).execute()
        if result.data and result.data[0]['array_to_json']:
            print("\nTables in public schema:")
            for table in result.data[0]['array_to_json']:
                tablename = table['tablename']
                print(f"- {tablename}")
                
                # Get table details
                details_query = f"""
                SELECT array_to_json(array_agg(row_to_json(c)))
                FROM (
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = '{tablename}'
                ) c;
                """
                
                details = supabase.postgrest.rpc('exec_sql', {'query': details_query}).execute()
                if details.data and details.data[0]['array_to_json']:
                    print("  Columns:")
                    for col in details.data[0]['array_to_json']:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        print(f"    {col['column_name']}: {col['data_type']} {nullable}")
                
                # Get RLS policies
                policies_query = f"""
                SELECT array_to_json(array_agg(row_to_json(p)))
                FROM (
                    SELECT 
                        pol.polname as policy_name,
                        CASE pol.polcmd
                            WHEN 'r' THEN 'SELECT'
                            WHEN 'w' THEN 'UPDATE'
                            WHEN 'a' THEN 'INSERT'
                            WHEN 'd' THEN 'DELETE'
                            WHEN '*' THEN 'ALL'
                        END as command,
                        r.rolname as role_name,
                        pol.polpermissive as is_permissive
                    FROM pg_policy pol
                    JOIN pg_roles r ON r.oid = pol.polrole
                    WHERE pol.polrelid = '{tablename}'::regclass
                ) p;
                """
                
                policies = supabase.postgrest.rpc('exec_sql', {'query': policies_query}).execute()
                if policies.data and policies.data[0]['array_to_json']:
                    print("  Policies:")
                    for pol in policies.data[0]['array_to_json']:
                        enabled = "ENABLED" if pol['is_permissive'] else "DISABLED"
                        print(f"    {pol['policy_name']}: {pol['command']} for {pol['role_name']} ({enabled})")
                print()
        else:
            print("No tables found in public schema!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    verify_schema() 