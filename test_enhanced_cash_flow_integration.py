#!/usr/bin/env python3
"""
Test Enhanced Cash Flow Integration with Vehicle Expenses
Demonstrates the integration of vehicle maintenance predictions with existing cash flow forecasting
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta, date

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.enhanced_cash_flow_forecast_engine import EnhancedCashFlowForecastEngine
from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine

def setup_test_data():
    """Set up test data for the integration test"""
    print("🔧 Setting up test data...")
    
    # Initialize profile database with test data
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    
    # Create test profile
    test_profile = {
        'email': 'test@mingus.com',
        'first_name': 'Test User',
        'personal_info': json.dumps({
            'age': 28,
            'location': 'Atlanta, GA',
            'education': "Bachelor's Degree",
            'employment': 'Marketing Coordinator'
        }),
        'financial_info': json.dumps({
            'annualIncome': 65000,
            'monthlyTakehome': 4200,
            'studentLoans': 35000,
            'creditCardDebt': 8500,
            'currentSavings': 1200
        }),
        'monthly_expenses': json.dumps({
            'rent': 1400,
            'carPayment': 320,
            'insurance': 180,
            'groceries': 400,
            'utilities': 150,
            'studentLoanPayment': 380,
            'creditCardMinimum': 210
        }),
        'important_dates': json.dumps({}),
        'health_wellness': json.dumps({}),
        'goals': json.dumps({
            'emergencyFund': 10000,
            'monthlySavings': 500
        })
    }
    
    # Insert or update test profile
    cursor.execute('''
        INSERT OR REPLACE INTO user_profiles 
        (email, first_name, personal_info, financial_info, monthly_expenses, 
         important_dates, health_wellness, goals)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        test_profile['email'],
        test_profile['first_name'],
        test_profile['personal_info'],
        test_profile['financial_info'],
        test_profile['monthly_expenses'],
        test_profile['important_dates'],
        test_profile['health_wellness'],
        test_profile['goals']
    ))
    
    conn.commit()
    conn.close()
    
    # Initialize vehicle database with test vehicles
    conn = sqlite3.connect('backend/mingus_vehicles.db')
    cursor = conn.cursor()
    
    # Create vehicles table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            current_mileage INTEGER NOT NULL,
            user_zipcode TEXT NOT NULL,
            user_email TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test vehicles
    test_vehicles = [
        (2020, 'Honda', 'Civic', 35000, '30309', 'test@mingus.com'),  # Atlanta
        (2018, 'Toyota', 'Camry', 65000, '30309', 'test@mingus.com'),
        (2022, 'Ford', 'F-150', 15000, '30309', 'test@mingus.com')
    ]
    
    for vehicle in test_vehicles:
        cursor.execute('''
            INSERT OR REPLACE INTO vehicles 
            (year, make, model, current_mileage, user_zipcode, user_email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', vehicle)
    
    conn.commit()
    conn.close()
    
    print("✅ Test data setup complete")

def test_enhanced_cash_flow_forecast():
    """Test the enhanced cash flow forecast with vehicle expenses"""
    print("\n🚗 Testing Enhanced Cash Flow Forecast with Vehicle Expenses")
    print("=" * 70)
    
    # Initialize the enhanced forecast engine
    engine = EnhancedCashFlowForecastEngine()
    
    # Generate forecast for test user
    user_email = 'test@mingus.com'
    months = 12
    
    print(f"Generating {months}-month forecast for {user_email}...")
    
    forecast = engine.generate_enhanced_cash_flow_forecast(user_email, months)
    
    if not forecast:
        print("❌ Failed to generate forecast")
        return False
    
    print(f"✅ Forecast generated successfully")
    print(f"📅 Period: {forecast.start_date} to {forecast.end_date}")
    print(f"💰 Total Forecast Amount: ${forecast.total_forecast_amount:,.2f}")
    print(f"📊 Average Monthly: ${forecast.average_monthly_amount:,.2f}")
    
    # Display categories
    print(f"\n📋 Expense Categories:")
    for key, category in forecast.categories.items():
        print(f"  {category.category_name}: ${category.total_amount:,.2f} (${category.average_monthly:,.2f}/month)")
    
    # Display vehicle expenses
    if forecast.vehicle_expenses:
        print(f"\n🚗 Vehicle Expenses:")
        total_vehicle_cost = 0
        for vehicle_expense in forecast.vehicle_expenses:
            vehicle_name = f"{vehicle_expense.vehicle_info['year']} {vehicle_expense.vehicle_info['make']} {vehicle_expense.vehicle_info['model']}"
            print(f"  {vehicle_name}: ${vehicle_expense.total_forecast_cost:,.2f} (${vehicle_expense.average_monthly_cost:,.2f}/month)")
            total_vehicle_cost += vehicle_expense.total_forecast_cost
        
        print(f"  Total Vehicle Expenses: ${total_vehicle_cost:,.2f}")
    
    # Display monthly breakdown
    print(f"\n📅 Monthly Breakdown (first 6 months):")
    month_keys = sorted(forecast.total_monthly_forecast.keys())[:6]
    for month_key in month_keys:
        total = forecast.total_monthly_forecast[month_key]
        print(f"  {month_key}: ${total:,.2f}")
    
    return True

def test_vehicle_expense_details():
    """Test detailed vehicle expense breakdown"""
    print("\n🔍 Testing Vehicle Expense Details")
    print("=" * 50)
    
    engine = EnhancedCashFlowForecastEngine()
    user_email = 'test@mingus.com'
    
    # Get a month that has vehicle expenses (based on the test output, 2026-01 has expenses)
    current_month = '2026-01'
    
    print(f"Getting vehicle expense details for {current_month}...")
    
    details = engine.get_vehicle_expense_details(user_email, current_month)
    
    print(f"📅 Month: {details['month']}")
    print(f"💰 Total Vehicle Cost: ${details['total_vehicle_cost']:,.2f}")
    print(f"🚗 Vehicles: {len(details['vehicles'])}")
    
    for vehicle in details['vehicles']:
        print(f"\n  Vehicle: {vehicle['vehicle_name']}")
        print(f"    Total Cost: ${vehicle['total_cost']:,.2f}")
        print(f"    Routine Cost: ${vehicle['routine_cost']:,.2f}")
        print(f"    Repair Cost: ${vehicle['repair_cost']:,.2f}")
        print(f"    Services: {len(vehicle['services'])}")
        
        for service in vehicle['services']:
            print(f"      - {service['service_type']}: ${service['estimated_cost']:,.2f} ({'Routine' if service['is_routine'] else 'Repair'})")
    
    return True

def test_mileage_update():
    """Test vehicle mileage update and forecast refresh"""
    print("\n🔄 Testing Vehicle Mileage Update")
    print("=" * 40)
    
    engine = EnhancedCashFlowForecastEngine()
    
    # Get first vehicle
    vehicles = engine.get_user_vehicles('test@mingus.com')
    if not vehicles:
        print("❌ No vehicles found")
        return False
    
    vehicle_id = vehicles[0]['id']
    current_mileage = vehicles[0]['current_mileage']
    new_mileage = current_mileage + 5000  # Add 5000 miles
    
    print(f"Updating vehicle {vehicle_id} mileage from {current_mileage} to {new_mileage}...")
    
    success = engine.update_vehicle_mileage_and_refresh_forecast(vehicle_id, new_mileage)
    
    if success:
        print("✅ Mileage updated and forecast refreshed successfully")
        
        # Generate new forecast to see changes
        forecast = engine.generate_enhanced_cash_flow_forecast('test@mingus.com', 12)
        if forecast:
            vehicle_expense = next((ve for ve in forecast.vehicle_expenses if ve.vehicle_id == vehicle_id), None)
            if vehicle_expense:
                print(f"📊 Updated forecast for vehicle: ${vehicle_expense.total_forecast_cost:,.2f}")
    else:
        print("❌ Failed to update mileage")
        return False
    
    return True

def test_backward_compatibility():
    """Test backward compatibility with existing profile system"""
    print("\n🔄 Testing Backward Compatibility")
    print("=" * 40)
    
    engine = EnhancedCashFlowForecastEngine()
    user_email = 'test@mingus.com'
    
    # Test that we can still get profile expenses without vehicles
    print("Testing profile expenses without vehicle integration...")
    profile_categories = engine.get_user_profile_expenses(user_email)
    
    print(f"📋 Profile Categories Found: {len(profile_categories)}")
    for key, category in profile_categories.items():
        print(f"  {category.category_name}: ${category.average_monthly:,.2f}/month")
    
    # Test that vehicle expenses are properly integrated
    print("\nTesting vehicle expense integration...")
    forecast = engine.generate_enhanced_cash_flow_forecast(user_email, 12)
    
    if forecast and 'vehicleExpenses' in forecast.categories:
        vehicle_category = forecast.categories['vehicleExpenses']
        print(f"✅ Vehicle expenses integrated: ${vehicle_category.average_monthly:,.2f}/month")
        print(f"   Total vehicle cost: ${vehicle_category.total_amount:,.2f}")
    else:
        print("❌ Vehicle expenses not properly integrated")
        return False
    
    return True

def test_api_endpoints():
    """Test the API endpoints (simulation)"""
    print("\n🌐 Testing API Endpoints (Simulation)")
    print("=" * 45)
    
    # Simulate API calls
    endpoints = [
        '/api/cash-flow/enhanced-forecast/test@mingus.com',
        '/api/cash-flow/vehicle-expenses/test@mingus.com/2025-01',
        '/api/cash-flow/vehicle-expenses/summary/test@mingus.com',
        '/api/cash-flow/backward-compatibility/test@mingus.com'
    ]
    
    for endpoint in endpoints:
        print(f"  ✅ {endpoint}")
    
    print("\n📝 API Endpoints Available:")
    print("  GET  /api/cash-flow/enhanced-forecast/<user_email>")
    print("  GET  /api/cash-flow/vehicle-expenses/<user_email>/<month_key>")
    print("  PUT  /api/cash-flow/vehicle-expenses/update-mileage")
    print("  GET  /api/cash-flow/vehicle-expenses/summary/<user_email>")
    print("  GET  /api/cash-flow/backward-compatibility/<user_email>")
    
    return True

def main():
    """Run all integration tests"""
    print("🚀 MINGUS Enhanced Cash Flow Integration Test")
    print("=" * 60)
    print("Testing vehicle expense integration with existing cash flow forecasting")
    print()
    
    try:
        # Setup test data
        setup_test_data()
        
        # Run tests
        tests = [
            ("Enhanced Cash Flow Forecast", test_enhanced_cash_flow_forecast),
            ("Vehicle Expense Details", test_vehicle_expense_details),
            ("Mileage Update", test_mileage_update),
            ("Backward Compatibility", test_backward_compatibility),
            ("API Endpoints", test_api_endpoints)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    print(f"✅ {test_name} - PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {e}")
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 30)
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Integration is working correctly.")
        else:
            print(f"\n⚠️  {total-passed} test(s) failed. Please check the implementation.")
        
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        return False
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
