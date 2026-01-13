#!/usr/bin/env python3
"""
Mingus Application - Database Configuration
SQLAlchemy database setup and configuration
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_database(app: Flask):
    """
    Initialize database with the Flask app
    
    Args:
        app: Flask application instance
    """
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')
    
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': database_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    })
    
    # Initialize database with app
    db.init_app(app)
    
    # Create all tables
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            # Handle duplicate table/index errors gracefully
            error_str = str(e).lower()
            if 'duplicate' in error_str or 'already exists' in error_str:
                # These are expected in production - tables/indexes already exist
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Some database objects already exist (this is normal): {e}")
            else:
                # Re-raise unexpected errors
                raise
    
    return db

def get_database_url():
    """Get the configured database URL"""
    return os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')
