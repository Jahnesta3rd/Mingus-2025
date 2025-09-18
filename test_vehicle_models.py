#!/usr/bin/env python3
"""
Test script for vehicle management SQLAlchemy models
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from backend.models.database import init_database
from backend.models.user_models import User
from backend.models.vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice

def test_models():
    """Test the vehicle management models"""
    print("🚗 Testing Mingus Vehicle Management Models")
    print("=" * 50)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///test_mingus_vehicles.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    
    # Initialize database
    init_database(app)
    
    with app.app_context():
        # Test User creation
        print("1. Testing User model...")
        user = User(
            user_id='test_user_001',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            referral_code='TEST001',
            feature_unlocked=True
        )
        
        from backend.models.database import db
        db.session.add(user)
        db.session.flush()
        print(f"   ✅ User created: {user.email}")
        
        # Test Vehicle creation
        print("2. Testing Vehicle model...")
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
        
        db.session.add(vehicle)
        db.session.flush()
        print(f"   ✅ Vehicle created: {vehicle.year} {vehicle.make} {vehicle.model}")
        
        # Test MaintenancePrediction creation
        print("3. Testing MaintenancePrediction model...")
        prediction = MaintenancePrediction(
            vehicle_id=vehicle.id,
            service_type='Oil Change',
            description='Regular oil change service',
            predicted_date=date.today() + timedelta(days=30),
            predicted_mileage=46200,
            estimated_cost=Decimal('45.00'),
            probability=0.95,
            is_routine=True
        )
        
        db.session.add(prediction)
        db.session.flush()
        print(f"   ✅ Maintenance prediction created: {prediction.service_type}")
        
        # Test CommuteScenario creation
        print("4. Testing CommuteScenario model...")
        scenario = CommuteScenario(
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
        )
        
        db.session.add(scenario)
        db.session.flush()
        print(f"   ✅ Commute scenario created: {scenario.job_location}")
        
        # Test MSAGasPrice creation
        print("5. Testing MSAGasPrice model...")
        gas_price = MSAGasPrice(
            msa_name='Los Angeles-Long Beach-Anaheim, CA',
            current_price=Decimal('4.25')
        )
        
        db.session.add(gas_price)
        db.session.flush()
        print(f"   ✅ MSA gas price created: {gas_price.msa_name}")
        
        # Test relationships
        print("6. Testing model relationships...")
        print(f"   User has {len(user.vehicles)} vehicles")
        print(f"   Vehicle has {len(vehicle.maintenance_predictions)} maintenance predictions")
        print(f"   Vehicle has {len(vehicle.commute_scenarios)} commute scenarios")
        
        # Test JSON serialization
        print("7. Testing JSON serialization...")
        user_dict = user.to_dict()
        vehicle_dict = vehicle.to_dict()
        prediction_dict = prediction.to_dict()
        scenario_dict = scenario.to_dict()
        gas_price_dict = gas_price.to_dict()
        
        print(f"   ✅ User serialized: {len(user_dict)} fields")
        print(f"   ✅ Vehicle serialized: {len(vehicle_dict)} fields")
        print(f"   ✅ Prediction serialized: {len(prediction_dict)} fields")
        print(f"   ✅ Scenario serialized: {len(scenario_dict)} fields")
        print(f"   ✅ Gas price serialized: {len(gas_price_dict)} fields")
        
        # Commit all changes
        db.session.commit()
        print("\n✅ All models tested successfully!")
        print("✅ Database operations completed!")
        
        # Clean up test database
        os.remove('test_mingus_vehicles.db')
        print("✅ Test database cleaned up!")

if __name__ == '__main__':
    test_models()
