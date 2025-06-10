from .base import Config

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SUPABASE_URL = "https://qjvhwqjvhwqjvhwqjvhw.supabase.co"  # Your actual Supabase URL
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdmh3cWp2aHdxanZod3Fqdmh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODg4ODg4ODgsImV4cCI6MjAwNDQ2NDg4OH0.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567"  # Your actual anon key
    SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"  # Your actual service role key 