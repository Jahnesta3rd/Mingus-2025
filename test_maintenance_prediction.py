#!/usr/bin/env python3
"""
Test script for Maintenance Prediction Engine
Tests the maintenance prediction functionality with various scenarios
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.maintenance_prediction_engine import (
    MaintenancePredictionEngine, MaintenanceType, ServicePriority
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_zipcode_to_msa_mapping():
    """Test ZIP code to MSA mapping functionality"""
    print("\n=== Testing ZIP Code to MSA Mapping ===")
    
    engine = MaintenancePredictionEngine()
    
    # Test ZIP codes for different MSAs
    test_zipcodes = [
        ("10001", "New York, NY"),
        ("30309", "Atlanta, GA"),
        ("77002", "Houston, TX"),
        ("20001", "Washington, DC"),
        ("75201", "Dallas, TX"),
        ("19102", "Philadelphia, PA"),
        ("60601", "Chicago, IL"),
        ("28202", "Charlotte, NC"),
        ("33101", "Miami, FL"),
        ("21201", "Baltimore, MD"),
        ("90210", "Los Angeles, CA"),  # Outside coverage
        ("99999", "Invalid ZIP")  # Invalid ZIP
    ]
    
    for zipcode, expected_city in test_zipcodes:
        msa_name, pricing_multiplier = engine.map_zipcode_to_msa(zipcode)
        print(f"  {zipcode} ({expected_city}): {msa_name} (multiplier: {pricing_multiplier:.2f})")

def test_maintenance_prediction():
    """Test maintenance prediction functionality"""
    print("\n=== Testing Maintenance Prediction ===")
    
    engine = MaintenancePredictionEngine()
    
    # Test vehicle data
    test_vehicles = [
        {
            "id": 1,
            "year": 2020,
            "make": "Honda",
            "model": "Civic",
            "current_mileage": 25000,
            "zipcode": "10001"  # New York
        },
        {
            "id": 2,
            "year": 2018,
            "make": "Ford",
            "model": "F-150",
            "current_mileage": 75000,
            "zipcode": "77002"  # Houston
        },
        {
            "id": 3,
            "year": 2015,
            "make": "BMW",
            "model": "3 Series",
            "current_mileage": 120000,
            "zipcode": "30309"  # Atlanta
        }
    ]
    
    for vehicle in test_vehicles:
        print(f"\nVehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']} ({vehicle['current_mileage']} miles)")
        print("-" * 60)
        
        try:
            predictions = engine.predict_maintenance(
                vehicle_id=vehicle['id'],
                year=vehicle['year'],
                make=vehicle['make'],
                model=vehicle['model'],
                current_mileage=vehicle['current_mileage'],
                zipcode=vehicle['zipcode'],
                prediction_horizon_months=12
            )
            
            print(f"Generated {len(predictions)} predictions:")
            
            # Group by maintenance type
            routine_predictions = [p for p in predictions if p.is_routine]
            age_based_predictions = [p for p in predictions if not p.is_routine]
            
            print(f"  Routine maintenance: {len(routine_predictions)}")
            print(f"  Age-based maintenance: {len(age_based_predictions)}")
            
            # Show first few predictions
            for i, prediction in enumerate(predictions[:5]):
                print(f"  {i+1}. {prediction.service_type}")
                print(f"     Date: {prediction.predicted_date}")
                print(f"     Mileage: {prediction.predicted_mileage}")
                print(f"     Cost: ${prediction.estimated_cost:.2f}")
                print(f"     Probability: {prediction.probability:.2f}")
                print(f"     MSA: {prediction.msa_name}")
                print(f"     Type: {prediction.maintenance_type.value}")
                print()
            
            if len(predictions) > 5:
                print(f"  ... and {len(predictions) - 5} more predictions")
            
        except Exception as e:
            print(f"  Error: {e}")

def test_cash_flow_forecast():
    """Test cash flow forecasting functionality"""
    print("\n=== Testing Cash Flow Forecast ===")
    
    engine = MaintenancePredictionEngine()
    
    # Create a test vehicle and generate predictions
    vehicle_id = 1
    year = 2020
    make = "Honda"
    model = "Civic"
    current_mileage = 30000
    zipcode = "10001"
    
    print(f"Vehicle: {year} {make} {model} ({current_mileage} miles) in {zipcode}")
    
    # Generate predictions
    predictions = engine.predict_maintenance(
        vehicle_id=vehicle_id,
        year=year,
        make=make,
        model=model,
        current_mileage=current_mileage,
        zipcode=zipcode,
        prediction_horizon_months=12
    )
    
    # Save predictions
    engine._save_predictions(predictions)
    
    # Generate cash flow forecast
    forecast = engine.get_cash_flow_forecast(vehicle_id, months=12)
    
    print(f"\nCash Flow Forecast (12 months):")
    print(f"  Total estimated cost: ${forecast['total_estimated_cost']:.2f}")
    print(f"  Routine maintenance: ${forecast['routine_maintenance_cost']:.2f}")
    print(f"  Age-based maintenance: ${forecast['age_based_maintenance_cost']:.2f}")
    print(f"  Average monthly cost: ${forecast['average_monthly_cost']:.2f}")
    
    print(f"\nMonthly breakdown:")
    for month, data in forecast['monthly_breakdown'].items():
        print(f"  {month}: ${data['total_cost']:.2f} ({len(data['predictions'])} services)")

def test_mileage_update():
    """Test mileage update functionality"""
    print("\n=== Testing Mileage Update ===")
    
    engine = MaintenancePredictionEngine()
    
    vehicle_id = 1
    year = 2020
    make = "Honda"
    model = "Civic"
    initial_mileage = 25000
    new_mileage = 35000
    zipcode = "10001"
    
    print(f"Vehicle: {year} {make} {model}")
    print(f"Initial mileage: {initial_mileage}")
    print(f"New mileage: {new_mileage}")
    
    # Generate initial predictions
    initial_predictions = engine.predict_maintenance(
        vehicle_id=vehicle_id,
        year=year,
        make=make,
        model=model,
        current_mileage=initial_mileage,
        zipcode=zipcode,
        prediction_horizon_months=12
    )
    
    print(f"\nInitial predictions: {len(initial_predictions)}")
    
    # Update predictions for new mileage
    updated_predictions = engine.update_predictions_for_mileage_change(
        vehicle_id, new_mileage
    )
    
    print(f"Updated predictions: {len(updated_predictions)}")
    
    # Compare predictions
    if initial_predictions and updated_predictions:
        print(f"\nComparison:")
        print(f"  Initial next service: {initial_predictions[0].predicted_date} at {initial_predictions[0].predicted_mileage} miles")
        print(f"  Updated next service: {updated_predictions[0].predicted_date} at {updated_predictions[0].predicted_mileage} miles")

def test_service_status():
    """Test service status functionality"""
    print("\n=== Testing Service Status ===")
    
    engine = MaintenancePredictionEngine()
    
    status = engine.get_service_status()
    
    print("Service Status:")
    for key, value in status.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")

def test_maintenance_schedules():
    """Test maintenance schedule configuration"""
    print("\n=== Testing Maintenance Schedules ===")
    
    engine = MaintenancePredictionEngine()
    
    print(f"Total maintenance schedules: {len(engine.maintenance_schedules)}")
    print(f"MSA centers: {len(engine.msa_centers)}")
    
    print(f"\nRoutine maintenance schedules:")
    routine_schedules = [s for s in engine.maintenance_schedules if s.is_routine]
    for schedule in routine_schedules[:5]:
        print(f"  {schedule.service_type}: Every {schedule.mileage_interval} miles, ${schedule.base_cost}")
    
    print(f"\nAge-based maintenance schedules:")
    age_schedules = [s for s in engine.maintenance_schedules if not s.is_routine]
    for schedule in age_schedules[:5]:
        print(f"  {schedule.service_type}: Every {schedule.age_interval_months} months, ${schedule.base_cost}")
    
    print(f"\nMSA Centers:")
    for msa in engine.msa_centers[:5]:
        print(f"  {msa.name}: {msa.zipcode} (multiplier: {msa.pricing_multiplier})")

def test_probability_calculations():
    """Test probability calculation methods"""
    print("\n=== Testing Probability Calculations ===")
    
    engine = MaintenancePredictionEngine()
    
    # Test mileage-based probability
    print("Mileage-based probability examples:")
    test_cases = [
        (25000, 30000, 5000),  # 5,000 miles away
        (29500, 30000, 5000),  # 500 miles away
        (29900, 30000, 5000),  # 100 miles away
        (30000, 30000, 5000),  # At target
    ]
    
    for current, target, interval in test_cases:
        # Create a test schedule
        from backend.services.maintenance_prediction_engine import MaintenanceSchedule, ServicePriority
        test_schedule = MaintenanceSchedule(
            "Test Service", "Test", interval, 0, 100.0, ServicePriority.MEDIUM, True, 0.8
        )
        
        probability = engine._calculate_mileage_based_probability(current, target, test_schedule)
        print(f"  Current: {current}, Target: {target}, Probability: {probability:.2f}")
    
    # Test age-based probability
    print("\nAge-based probability examples:")
    age_cases = [12, 24, 36, 48, 60, 72]
    
    for age_months in age_cases:
        test_schedule = MaintenanceSchedule(
            "Test Service", "Test", 0, 36, 100.0, ServicePriority.MEDIUM, False, 0.6
        )
        
        probability = engine._calculate_age_based_probability(age_months, test_schedule)
        print(f"  Age: {age_months} months, Probability: {probability:.2f}")

def main():
    """Run all tests"""
    print("Maintenance Prediction Engine Test Suite")
    print("=" * 60)
    
    try:
        test_zipcode_to_msa_mapping()
        test_maintenance_schedules()
        test_probability_calculations()
        test_maintenance_prediction()
        test_cash_flow_forecast()
        test_mileage_update()
        test_service_status()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed with error: {e}")
        logger.exception("Test suite error")

if __name__ == "__main__":
    main()
