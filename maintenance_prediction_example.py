#!/usr/bin/env python3
"""
Maintenance Prediction Engine Example
Demonstrates how to use the maintenance prediction engine in the Mingus Flask application
"""

import sys
import os
import json
from datetime import datetime, date

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.maintenance_prediction_engine import (
    MaintenancePredictionEngine, MaintenanceType, ServicePriority
)

def example_basic_usage():
    """Example of basic maintenance prediction usage"""
    print("Maintenance Prediction Engine - Basic Usage Example")
    print("=" * 60)
    
    # Initialize the engine
    engine = MaintenancePredictionEngine()
    
    # Example vehicle data
    vehicle_data = {
        "id": 1,
        "year": 2020,
        "make": "Honda",
        "model": "Civic",
        "current_mileage": 35000,
        "zipcode": "10001"  # New York
    }
    
    print(f"Vehicle: {vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}")
    print(f"Current Mileage: {vehicle_data['current_mileage']:,} miles")
    print(f"Location: {vehicle_data['zipcode']}")
    
    # Generate maintenance predictions
    predictions = engine.predict_maintenance(
        vehicle_id=vehicle_data['id'],
        year=vehicle_data['year'],
        make=vehicle_data['make'],
        model=vehicle_data['model'],
        current_mileage=vehicle_data['current_mileage'],
        zipcode=vehicle_data['zipcode'],
        prediction_horizon_months=12
    )
    
    print(f"\nGenerated {len(predictions)} maintenance predictions:")
    print("-" * 60)
    
    # Display predictions grouped by type
    routine_predictions = [p for p in predictions if p.is_routine]
    age_based_predictions = [p for p in predictions if not p.is_routine]
    
    print(f"\nRoutine Maintenance ({len(routine_predictions)} predictions):")
    for prediction in routine_predictions[:5]:  # Show first 5
        print(f"  • {prediction.service_type}")
        print(f"    Date: {prediction.predicted_date}")
        print(f"    Mileage: {prediction.predicted_mileage:,} miles")
        print(f"    Cost: ${prediction.estimated_cost:.2f}")
        print(f"    Probability: {prediction.probability:.1%}")
        print(f"    MSA: {prediction.msa_name}")
        print()
    
    print(f"\nAge-Based Maintenance ({len(age_based_predictions)} predictions):")
    for prediction in age_based_predictions[:3]:  # Show first 3
        print(f"  • {prediction.service_type}")
        print(f"    Date: {prediction.predicted_date}")
        print(f"    Cost: ${prediction.estimated_cost:.2f}")
        print(f"    Probability: {prediction.probability:.1%}")
        print(f"    Priority: {prediction.priority.value}")
        print()

def example_cash_flow_forecast():
    """Example of cash flow forecasting"""
    print("\n\nCash Flow Forecast Example")
    print("=" * 60)
    
    engine = MaintenancePredictionEngine()
    
    # Generate predictions for a vehicle
    vehicle_id = 1
    predictions = engine.predict_maintenance(
        vehicle_id=vehicle_id,
        year=2020,
        make="Toyota",
        model="Camry",
        current_mileage=45000,
        zipcode="77002",  # Houston
        prediction_horizon_months=12
    )
    
    # Save predictions
    engine._save_predictions(predictions)
    
    # Generate cash flow forecast
    forecast = engine.get_cash_flow_forecast(vehicle_id, months=12)
    
    print(f"12-Month Cash Flow Forecast:")
    print(f"  Total Estimated Cost: ${forecast['total_estimated_cost']:,.2f}")
    print(f"  Routine Maintenance: ${forecast['routine_maintenance_cost']:,.2f}")
    print(f"  Age-Based Maintenance: ${forecast['age_based_maintenance_cost']:,.2f}")
    print(f"  Average Monthly Cost: ${forecast['average_monthly_cost']:,.2f}")
    
    print(f"\nMonthly Breakdown:")
    for month, data in sorted(forecast['monthly_breakdown'].items()):
        if data['total_cost'] > 0:
            print(f"  {month}: ${data['total_cost']:,.2f} ({len(data['predictions'])} services)")

def example_msa_mapping():
    """Example of ZIP code to MSA mapping"""
    print("\n\nZIP Code to MSA Mapping Example")
    print("=" * 60)
    
    engine = MaintenancePredictionEngine()
    
    # Test various ZIP codes
    test_zipcodes = [
        ("10001", "New York, NY"),
        ("30309", "Atlanta, GA"),
        ("77002", "Houston, TX"),
        ("20001", "Washington, DC"),
        ("75201", "Dallas, TX"),
        ("90210", "Los Angeles, CA"),  # Outside coverage
        ("99999", "Invalid ZIP")
    ]
    
    print("ZIP Code to MSA Mapping Results:")
    for zipcode, city in test_zipcodes:
        msa_name, pricing_multiplier = engine.map_zipcode_to_msa(zipcode)
        print(f"  {zipcode} ({city}):")
        print(f"    MSA: {msa_name}")
        print(f"    Pricing Multiplier: {pricing_multiplier:.2f}")
        print(f"    Cost Impact: {((pricing_multiplier - 1) * 100):+.1f}%")
        print()

def example_mileage_update():
    """Example of updating predictions when mileage changes"""
    print("\n\nMileage Update Example")
    print("=" * 60)
    
    engine = MaintenancePredictionEngine()
    
    vehicle_id = 1
    initial_mileage = 30000
    new_mileage = 40000
    
    print(f"Updating vehicle mileage from {initial_mileage:,} to {new_mileage:,} miles")
    
    # Generate initial predictions
    initial_predictions = engine.predict_maintenance(
        vehicle_id=vehicle_id,
        year=2019,
        make="Ford",
        model="F-150",
        current_mileage=initial_mileage,
        zipcode="60601",  # Chicago
        prediction_horizon_months=12
    )
    
    print(f"Initial predictions: {len(initial_predictions)}")
    
    # Update predictions for new mileage
    updated_predictions = engine.update_predictions_for_mileage_change(
        vehicle_id, new_mileage
    )
    
    print(f"Updated predictions: {len(updated_predictions)}")
    
    # Show how predictions changed
    if initial_predictions and updated_predictions:
        print(f"\nPrediction Changes:")
        print(f"  Next oil change:")
        print(f"    Before: {initial_predictions[0].predicted_date} at {initial_predictions[0].predicted_mileage:,} miles")
        print(f"    After:  {updated_predictions[0].predicted_date} at {updated_predictions[0].predicted_mileage:,} miles")

def example_api_usage():
    """Example of using the maintenance prediction via API endpoints"""
    print("\n\nAPI Usage Example")
    print("=" * 60)
    
    print("To use the maintenance prediction engine via API endpoints:")
    print("\n1. Generate Maintenance Predictions:")
    print("   POST /api/vehicles/{vehicle_id}/maintenance-predictions/generate")
    print("   Body: {\"prediction_horizon_months\": 24}")
    
    print("\n2. Get Maintenance Predictions:")
    print("   GET /api/vehicles/{vehicle_id}/maintenance-predictions")
    
    print("\n3. Update Mileage:")
    print("   PUT /api/vehicles/{vehicle_id}/maintenance-predictions/update-mileage")
    print("   Body: {\"new_mileage\": 40000}")
    
    print("\n4. Get Cash Flow Forecast:")
    print("   GET /api/vehicles/{vehicle_id}/maintenance-predictions/cash-flow?months=12")
    
    print("\n5. Map ZIP Code to MSA:")
    print("   POST /api/vehicles/maintenance-predictions/msa-mapping")
    print("   Body: {\"zipcode\": \"10001\"}")
    
    print("\n6. Get Service Status:")
    print("   GET /api/vehicles/maintenance-predictions/status")
    
    print("\nExample cURL commands:")
    print("\n# Generate predictions")
    print('curl -X POST http://localhost:5000/api/vehicles/1/maintenance-predictions/generate \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"prediction_horizon_months": 12}\'')
    
    print("\n# Get cash flow forecast")
    print('curl -X GET "http://localhost:5000/api/vehicles/1/maintenance-predictions/cash-flow?months=12"')
    
    print("\n# Update mileage")
    print('curl -X PUT http://localhost:5000/api/vehicles/1/maintenance-predictions/update-mileage \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"new_mileage": 40000}\'')

def example_service_status():
    """Example of checking service status"""
    print("\n\nService Status Example")
    print("=" * 60)
    
    engine = MaintenancePredictionEngine()
    
    status = engine.get_service_status()
    
    print("Maintenance Prediction Service Status:")
    print(f"  Status: {status['status']}")
    print(f"  Total Predictions: {status['total_predictions']}")
    print(f"  MSA Centers: {status['msa_centers_count']}")
    print(f"  Maintenance Schedules: {status['maintenance_schedules_count']}")
    print(f"  Fallback Pricing Multiplier: {status['fallback_pricing_multiplier']}")
    
    if 'predictions_by_type' in status:
        print(f"\nPredictions by Type:")
        for maint_type, count in status['predictions_by_type'].items():
            print(f"  {maint_type}: {count}")
    
    if 'predictions_by_msa' in status:
        print(f"\nPredictions by MSA:")
        for msa, count in status['predictions_by_msa'].items():
            print(f"  {msa}: {count}")

def example_integration_with_vehicle_management():
    """Example of integrating with vehicle management system"""
    print("\n\nVehicle Management Integration Example")
    print("=" * 60)
    
    print("Integration with existing vehicle management system:")
    print("\n1. When a vehicle is added:")
    print("   - Generate initial maintenance predictions")
    print("   - Map ZIP code to MSA for regional pricing")
    print("   - Store predictions in MaintenancePrediction model")
    
    print("\n2. When vehicle mileage is updated:")
    print("   - Recalculate all mileage-based predictions")
    print("   - Update predicted dates and costs")
    print("   - Maintain prediction history")
    
    print("\n3. For cash flow planning:")
    print("   - Generate monthly maintenance cost forecasts")
    print("   - Integrate with overall financial planning")
    print("   - Provide budget recommendations")
    
    print("\n4. For maintenance scheduling:")
    print("   - Prioritize high-probability, high-cost services")
    print("   - Schedule routine maintenance in advance")
    print("   - Alert users to upcoming maintenance needs")

if __name__ == "__main__":
    try:
        example_basic_usage()
        example_cash_flow_forecast()
        example_msa_mapping()
        example_mileage_update()
        example_api_usage()
        example_service_status()
        example_integration_with_vehicle_management()
        
        print("\n" + "=" * 60)
        print("Example completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\n\nExample failed with error: {e}")
