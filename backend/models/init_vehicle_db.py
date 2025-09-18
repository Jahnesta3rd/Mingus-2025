#!/usr/bin/env python3
"""
Mingus Application - Vehicle Database Initialization
Initialize the vehicle management database with sample data
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask
from .database import init_database
from .user_models import User
from .vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice

def create_app():
    """Create Flask app for database initialization"""
    app = Flask(__name__)
    
    # Configure database
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': database_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    
    # Initialize database
    init_database(app)
    
    return app

def create_sample_data():
    """Create sample data for testing the vehicle management system"""
    app = create_app()
    
    with app.app_context():
        # Create sample user
        user = User(
            user_id='user_001',
            email='john.doe@example.com',
            first_name='John',
            last_name='Doe',
            referral_code='REF001',
            referral_count=5,
            successful_referrals=3,
            feature_unlocked=True,
            unlock_date=datetime.utcnow() - timedelta(days=30)
        )
        
        # Add user to database
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Create sample vehicle
        vehicle = Vehicle(
            user_id=user.id,
            vin='1HGBH41JXMN109186',
            year=2020,
            make='Honda',
            model='Civic',
            trim='EX',
            current_mileage=45000,
            monthly_miles=1200,
            user_zipcode='90210',
            assigned_msa='Los Angeles-Long Beach-Anaheim, CA'
        )
        
        # Add vehicle to database
        db.session.add(vehicle)
        db.session.flush()  # Get the vehicle ID
        
        # Create sample maintenance predictions
        maintenance_predictions = [
            MaintenancePrediction(
                vehicle_id=vehicle.id,
                service_type='Oil Change',
                description='Regular oil change service',
                predicted_date=date.today() + timedelta(days=30),
                predicted_mileage=46200,
                estimated_cost=Decimal('45.00'),
                probability=0.95,
                is_routine=True
            ),
            MaintenancePrediction(
                vehicle_id=vehicle.id,
                service_type='Brake Pad Replacement',
                description='Front brake pads need replacement',
                predicted_date=date.today() + timedelta(days=90),
                predicted_mileage=48000,
                estimated_cost=Decimal('250.00'),
                probability=0.80,
                is_routine=False
            ),
            MaintenancePrediction(
                vehicle_id=vehicle.id,
                service_type='Tire Rotation',
                description='Regular tire rotation service',
                predicted_date=date.today() + timedelta(days=60),
                predicted_mileage=46800,
                estimated_cost=Decimal('25.00'),
                probability=0.90,
                is_routine=True
            )
        ]
        
        for prediction in maintenance_predictions:
            db.session.add(prediction)
        
        # Create sample commute scenarios
        commute_scenarios = [
            CommuteScenario(
                vehicle_id=vehicle.id,
                job_location='Downtown Los Angeles',
                job_zipcode='90012',
                distance_miles=25.5,
                daily_cost=Decimal('8.50'),
                monthly_cost=Decimal('187.00'),
                gas_price_per_gallon=Decimal('4.25'),
                vehicle_mpg=32.0,
                from_msa='Los Angeles-Long Beach-Anaheim, CA',
                to_msa='Los Angeles-Long Beach-Anaheim, CA'
            ),
            CommuteScenario(
                vehicle_id=vehicle.id,
                job_location='Santa Monica',
                job_zipcode='90401',
                distance_miles=18.2,
                daily_cost=Decimal('6.25'),
                monthly_cost=Decimal('137.50'),
                gas_price_per_gallon=Decimal('4.25'),
                vehicle_mpg=32.0,
                from_msa='Los Angeles-Long Beach-Anaheim, CA',
                to_msa='Los Angeles-Long Beach-Anaheim, CA'
            )
        ]
        
        for scenario in commute_scenarios:
            db.session.add(scenario)
        
        # Create sample MSA gas prices
        msa_gas_prices = [
            MSAGasPrice(
                msa_name='National Average',
                current_price=Decimal('3.45'),
                last_updated=datetime.utcnow()
            ),
            MSAGasPrice(
                msa_name='Los Angeles-Long Beach-Anaheim, CA',
                current_price=Decimal('4.25'),
                last_updated=datetime.utcnow()
            ),
            MSAGasPrice(
                msa_name='New York-Newark-Jersey City, NY-NJ-PA',
                current_price=Decimal('3.85'),
                last_updated=datetime.utcnow()
            ),
            MSAGasPrice(
                msa_name='Chicago-Naperville-Elgin, IL-IN-WI',
                current_price=Decimal('3.65'),
                last_updated=datetime.utcnow()
            ),
            MSAGasPrice(
                msa_name='Houston-The Woodlands-Sugar Land, TX',
                current_price=Decimal('3.15'),
                last_updated=datetime.utcnow()
            )
        ]
        
        for gas_price in msa_gas_prices:
            db.session.add(gas_price)
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Sample data created successfully!")
        print(f"   - 1 User: {user.email}")
        print(f"   - 1 Vehicle: {vehicle.year} {vehicle.make} {vehicle.model}")
        print(f"   - {len(maintenance_predictions)} Maintenance Predictions")
        print(f"   - {len(commute_scenarios)} Commute Scenarios")
        print(f"   - {len(msa_gas_prices)} MSA Gas Prices")

def init_vehicle_database():
    """Initialize the vehicle management database"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Vehicle management database initialized successfully!")
        
        # Check if we should create sample data
        if os.environ.get('CREATE_SAMPLE_DATA', 'false').lower() == 'true':
            create_sample_data()

if __name__ == '__main__':
    init_vehicle_database()
