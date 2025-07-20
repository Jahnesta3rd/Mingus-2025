"""
Configuration management for the application.
Import this module to access configuration values.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from tests.mock_supabase import MockSupabaseClient

load_dotenv()

class Config:
    """Base configuration."""
    TESTING = False
    DEBUG = False
    PORT = int(os.getenv('PORT', 5000))
    SUPABASE_URL = "https://qjvhwqjvhwqjvhwqjvhw.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqdmh3cWp2aHdxanZod3Fqdmh3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODg4ODg4ODgsImV4cCI6MjAwNDQ2NDg4OH0.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567"
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'your-service-role-key')

    @property
    def supabase_client(self) -> Client:
        """Create and return a Supabase client."""
        if not hasattr(self, '_supabase_client'):
            self._supabase_client = create_client(
                self.SUPABASE_URL,
                self.SUPABASE_KEY
            )
        return self._supabase_client

    @classmethod
    def get_supabase_url(cls):
        return cls.SUPABASE_URL
    
    @classmethod
    def get_supabase_key(cls):
        return cls.SUPABASE_KEY
    
    @classmethod
    def get_port(cls):
        return int(os.getenv('FLASK_RUN_PORT', os.getenv('PORT', cls.PORT)))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SUPABASE_URL = "https://test-project.supabase.co"
    SUPABASE_KEY = "test-key"
    SUPABASE_SERVICE_ROLE_KEY = "test-service-role-key"

    @property
    def supabase_client(self) -> Client:
        """Return a mock Supabase client for testing."""
        if not hasattr(self, '_supabase_client'):
            self._supabase_client = MockSupabaseClient()
        return self._supabase_client

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

# Dictionary to map environment names to config classes
config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}