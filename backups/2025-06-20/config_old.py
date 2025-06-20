"""
Configuration management for the application.
Import this module to access configuration values.
"""
import os

class Config:
    # Supabase Configuration
    SUPABASE_URL = "https://wiemjrvxlqkpbsukdqnb.supabase.co"
    SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTAxOTcsImV4cCI6MjA2MjMyNjE5N30.9AsxxhX4Nt4Qr3EZerYfpvo4doVPbxuZRMgNSgnapM8"
    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1MDE5NywiZXhwIjoyMDYyMzI2MTk3fQ.pzTybRahJYGjD_y2OrLnhpAX5xq-ylJbd7r4K5xNGCM"
    # Port Configuration
    PORT = int(os.getenv('FLASK_RUN_PORT', os.getenv('PORT', 5003)))

    @classmethod
    def get_supabase_url(cls):
        # Return the hardcoded value directly, don't check env vars
        return cls.SUPABASE_URL
    
    @classmethod
    def get_supabase_anon_key(cls):
        # Return the hardcoded value directly, don't check env vars
        return cls.SUPABASE_ANON_KEY
    
    @classmethod
    def get_service_role_key(cls):
        # Return the hardcoded value directly, don't check env vars
        return cls.SUPABASE_SERVICE_ROLE_KEY
    
    @classmethod
    def get_port(cls):
        return int(os.getenv('FLASK_RUN_PORT', os.getenv('PORT', cls.PORT)))

# Create a development configuration
class DevelopmentConfig(Config):
    DEBUG = True
    
# Create a production configuration
class ProductionConfig(Config):
    DEBUG = False
    
# Create a testing configuration
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    
# Dictionary to map environment names to config classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}