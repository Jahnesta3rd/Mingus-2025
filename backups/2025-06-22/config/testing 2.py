from .base import Config

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    
    # Use test-specific Supabase credentials if needed
    SUPABASE_URL = "https://wiemjrvxlqkpbsukdqnb.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTAxOTcsImV4cCI6MjA2MjMyNjE5N30.9AsxxhX4Nt4Qr3EZerYfpvo4doVPbxuZRMgNSgnapM8"
    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1MDE5NywiZXhwIjoyMDYyMzI2MTk3fQ.pzTybRahJYGjD_y2OrLnhpAX5xq-ylJbd7r4K5xNGCM"
    SUPABASE_JWT_SECRET = "counJW9WSebZaLdlxu2e8+OBsrvgXNYcgsHravbNQrQKy6i/uyfFAL0Ne9QozcrosrXuzbudxltljMCWKpB9hg=="
    
    # Override CORS settings for testing
    CORS_ORIGINS = [
        'http://localhost:5002',
        'http://127.0.0.1:5002',
        'https://wiemjrvxlqkpbsukdqnb.supabase.co',
        'https://accounts.google.com'
    ]
    
    # Override session settings for testing
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour 