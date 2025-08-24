from supabase import create_client
from dotenv import load_dotenv
import os

def test_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Supabase credentials from environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        # Print debug information
        print("Debug Information:")
        print(f"SUPABASE_URL found: {'Yes' if supabase_url else 'No'}")
        print(f"SUPABASE_KEY found: {'Yes' if supabase_key else 'No'}")
        print(f"Current working directory: {os.getcwd()}")
        print(f".env file exists: {'Yes' if os.path.exists('.env') else 'No'}")
        print("\n")
        
        if not supabase_url or not supabase_key:
            raise EnvironmentError(
                "Missing Supabase credentials. Please ensure SUPABASE_URL and SUPABASE_KEY "
                "are set in your .env file."
            )
        
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test the connection by trying to access system information
        response = supabase.auth.get_session()
        
        print("✅ Successfully connected to Supabase!")
        print(f"Connected to: {supabase_url}")
        print("\nConnection is working properly!")
        
    except Exception as e:
        print("❌ Failed to connect to Supabase!")
        print(f"Error: {str(e)}")
        print("\nPlease check:")
        print("1. Your .env file exists with SUPABASE_URL and SUPABASE_KEY")
        print("2. Your Supabase credentials are correct")
        print("3. Your network connection is working")

if __name__ == "__main__":
    test_connection() 