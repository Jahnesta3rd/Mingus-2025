#!/usr/bin/env python3
"""
Start the main Flask app with assessment routes
"""

import os
import sys
from flask import Flask

# Add backend to path
sys.path.append('backend')

try:
    from backend.app_factory import create_app
    
    # Create the Flask app
    app = create_app('development')
    
    print("Starting Flask app with assessment routes...")
    print("Available routes:")
    
    # Print all registered routes
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} [{', '.join(rule.methods)}]")
    
    # Start the app
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5001, debug=True)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
except Exception as e:
    print(f"Error starting Flask app: {e}")
    import traceback
    traceback.print_exc()
