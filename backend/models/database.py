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
        db.create_all()
    
    return db

def get_database_url():
    """Get the configured database URL"""
    return os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')
