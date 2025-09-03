#!/usr/bin/env python3
"""
Test CORS Configuration Loading
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.config.unified_security_config import UnifiedSecurityConfig
    
    print("🔍 Testing CORS Configuration Loading")
    print("=" * 50)
    
    # Test the unified security config
    config = UnifiedSecurityConfig()
    
    print(f"CORS_ENABLED: {config.CORS_ENABLED}")
    print(f"CORS_ORIGINS: {config.CORS_ORIGINS}")
    print(f"CORS_METHODS: {config.CORS_METHODS}")
    print(f"CORS_ALLOW_HEADERS: {config.CORS_ALLOW_HEADERS}")
    print(f"CORS_SUPPORTS_CREDENTIALS: {config.CORS_SUPPORTS_CREDENTIALS}")
    
    print("\n🔧 Environment Variables:")
    print(f"CORS_ENABLED: {os.getenv('CORS_ENABLED', 'NOT SET')}")
    print(f"CORS_ORIGINS: {os.getenv('CORS_ORIGINS', 'NOT SET')}")
    
    print("\n✅ Configuration loaded successfully!")
    
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    import traceback
    traceback.print_exc()
