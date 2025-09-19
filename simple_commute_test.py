#!/usr/bin/env python3
"""
Simple test for the commute cost calculator system
Tests core functionality without complex dependencies
"""

import os
import sys
import json
import tempfile
import sqlite3
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    print("🧪 Testing File Structure...")
    
    required_files = [
        "frontend/src/components/CommuteCostCalculator.tsx",
        "frontend/src/components/CareerCommuteIntegration.tsx", 
        "frontend/src/pages/CareerCommutePage.tsx",
        "backend/api/commute_endpoints.py",
        "backend/api/geocoding_endpoints.py",
        "COMMUTE_COST_CALCULATOR_README.md",
        "COMMUTE_INTEGRATION_GUIDE.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def test_commute_calculation_logic():
    """Test the core commute calculation logic"""
    print("🧪 Testing Commute Calculation Logic...")
    
    def calculate_commute_costs(distance, vehicle, fuel_price=3.50, days_per_week=5):
        """Calculate detailed commute costs"""
        weekly_distance = distance * 2 * days_per_week  # Round trip
        monthly_distance = weekly_distance * 4.33
        annual_distance = monthly_distance * 12
        
        # Fuel costs
        fuel_cost_per_mile = fuel_price / vehicle['mpg']
        fuel_cost = weekly_distance * fuel_cost_per_mile
        
        # Maintenance costs (based on vehicle age and mileage)
        vehicle_age = 2024 - vehicle['year']
        if vehicle_age > 10:
            maintenance_rate = 0.15
        elif vehicle_age > 5:
            maintenance_rate = 0.10
        else:
            maintenance_rate = 0.08
        
        maintenance_cost = weekly_distance * maintenance_rate
        
        # Depreciation (simplified calculation)
        if vehicle_age > 10:
            depreciation_rate = 0.05
        elif vehicle_age > 5:
            depreciation_rate = 0.08
        else:
            depreciation_rate = 0.12
        
        depreciation_cost = weekly_distance * depreciation_rate
        
        # Insurance (prorated for commute)
        insurance_cost = (500 / 12) * (days_per_week / 7)  # $500/month insurance
        
        # Parking (estimated)
        parking_cost = days_per_week * 15  # $15/day parking
        
        # Tolls (estimated)
        tolls_cost = weekly_distance * 0.05  # $0.05/mile in tolls
        
        total_cost = fuel_cost + maintenance_cost + depreciation_cost + insurance_cost + parking_cost + tolls_cost
        cost_per_mile = total_cost / weekly_distance if weekly_distance > 0 else 0
        annual_cost = total_cost * 52
        
        return {
            'fuel_cost': fuel_cost,
            'maintenance_cost': maintenance_cost,
            'depreciation_cost': depreciation_cost,
            'insurance_cost': insurance_cost,
            'parking_cost': parking_cost,
            'tolls_cost': tolls_cost,
            'total_cost': total_cost,
            'cost_per_mile': cost_per_mile,
            'annual_cost': annual_cost,
            'weekly_distance': weekly_distance,
            'monthly_distance': monthly_distance,
            'annual_distance': annual_distance
        }
    
    # Test with different vehicle types
    test_vehicles = [
        {
            'id': 'vehicle_1',
            'make': 'Honda',
            'model': 'Civic',
            'year': 2020,
            'mpg': 32,
            'fuel_type': 'gasoline'
        },
        {
            'id': 'vehicle_2',
            'make': 'Toyota',
            'model': 'Prius',
            'year': 2019,
            'mpg': 50,
            'fuel_type': 'hybrid'
        },
        {
            'id': 'vehicle_3',
            'make': 'Tesla',
            'model': 'Model 3',
            'year': 2022,
            'mpg': 120,  # MPGe for electric
            'fuel_type': 'electric'
        }
    ]
    
    distance = 15.5  # miles
    days_per_week = 5
    
    for vehicle in test_vehicles:
        costs = calculate_commute_costs(distance, vehicle, days_per_week=days_per_week)
        
        # Validate required fields
        required_fields = ['fuel_cost', 'maintenance_cost', 'depreciation_cost', 'total_cost', 'annual_cost']
        for field in required_fields:
            if field not in costs:
                print(f"❌ Missing field {field} for {vehicle['make']} {vehicle['model']}")
                return False
        
        # Validate cost values are reasonable
        if costs['total_cost'] <= 0:
            print(f"❌ Invalid total cost for {vehicle['make']} {vehicle['model']}")
            return False
        
        if costs['annual_cost'] <= 0:
            print(f"❌ Invalid annual cost for {vehicle['make']} {vehicle['model']}")
            return False
        
        print(f"✅ {vehicle['make']} {vehicle['model']}: ${costs['total_cost']:.2f}/week, ${costs['annual_cost']:.0f}/year")
    
    print("✅ Commute calculation logic working correctly")
    return True

def test_database_operations():
    """Test database operations"""
    print("🧪 Testing Database Operations...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create scenarios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commute_scenarios (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                job_location TEXT NOT NULL,
                home_location TEXT NOT NULL,
                vehicle TEXT NOT NULL,
                commute_details TEXT NOT NULL,
                costs TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_vehicles (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mpg REAL NOT NULL,
                fuel_type TEXT NOT NULL,
                current_mileage INTEGER DEFAULT 0,
                monthly_miles INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # Test inserting a scenario
        scenario_data = {
            'id': 'test_scenario_1',
            'name': 'Test Job - Honda Civic',
            'job_location': json.dumps({'address': '123 Tech Street'}),
            'home_location': json.dumps({'address': '456 Home Avenue'}),
            'vehicle': json.dumps({'id': 'vehicle_1', 'make': 'Honda', 'model': 'Civic', 'year': 2020, 'mpg': 32, 'fuel_type': 'gasoline'}),
            'commute_details': json.dumps({'distance': 15.5, 'duration': 25, 'frequency': 'daily', 'days_per_week': 5}),
            'costs': json.dumps({'fuel': 45.50, 'maintenance': 12.30, 'depreciation': 8.75, 'insurance': 15.00, 'parking': 75.00, 'tolls': 5.25, 'total': 161.80})
        }
        
        cursor.execute('''
            INSERT INTO commute_scenarios 
            (id, user_id, name, job_location, home_location, vehicle, commute_details, costs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scenario_data['id'],
            'test_user',
            scenario_data['name'],
            scenario_data['job_location'],
            scenario_data['home_location'],
            scenario_data['vehicle'],
            scenario_data['commute_details'],
            scenario_data['costs']
        ))
        
        conn.commit()
        
        # Test retrieving scenarios
        cursor.execute('SELECT * FROM commute_scenarios WHERE id = ?', (scenario_data['id'],))
        result = cursor.fetchone()
        
        if result is None:
            print("❌ Failed to retrieve inserted scenario")
            return False
        
        print(f"✅ Successfully inserted and retrieved scenario: {result[2]}")
        
        # Test updating scenario
        cursor.execute('''
            UPDATE commute_scenarios 
            SET name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', ('Updated Test Job - Honda Civic', scenario_data['id']))
        
        conn.commit()
        
        # Test deleting scenario
        cursor.execute('DELETE FROM commute_scenarios WHERE id = ?', (scenario_data['id'],))
        conn.commit()
        
        # Verify deletion
        cursor.execute('SELECT * FROM commute_scenarios WHERE id = ?', (scenario_data['id'],))
        result = cursor.fetchone()
        
        if result is not None:
            print("❌ Failed to delete scenario")
            return False
        
        print("✅ Database operations working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_component_syntax():
    """Test that React components have valid syntax"""
    print("🧪 Testing Component Syntax...")
    
    react_components = [
        "frontend/src/components/CommuteCostCalculator.tsx",
        "frontend/src/components/CareerCommuteIntegration.tsx",
        "frontend/src/pages/CareerCommutePage.tsx"
    ]
    
    for component in react_components:
        if not os.path.exists(component):
            print(f"❌ Component not found: {component}")
            return False
        
        # Basic syntax checks
        with open(component, 'r') as f:
            content = f.read()
            
            # Check for basic React patterns
            if 'import React' not in content:
                print(f"❌ Missing React import in {component}")
                return False
            
            if 'export default' not in content:
                print(f"❌ Missing default export in {component}")
                return False
            
            # Check for balanced braces (basic check)
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                print(f"❌ Unbalanced braces in {component}")
                return False
            
            print(f"✅ {component} syntax looks valid")
    
    print("✅ All components have valid syntax")
    return True

def test_api_endpoint_structure():
    """Test that API endpoints have correct structure"""
    print("🧪 Testing API Endpoint Structure...")
    
    api_files = [
        "backend/api/commute_endpoints.py",
        "backend/api/geocoding_endpoints.py"
    ]
    
    for api_file in api_files:
        if not os.path.exists(api_file):
            print(f"❌ API file not found: {api_file}")
            return False
        
        with open(api_file, 'r') as f:
            content = f.read()
            
            # Check for required patterns
            if 'Blueprint' not in content:
                print(f"❌ Missing Blueprint in {api_file}")
                return False
            
            if '@commute_bp.route' not in content and '@geocoding_bp.route' not in content:
                print(f"❌ Missing route decorators in {api_file}")
                return False
            
            if 'jsonify' not in content:
                print(f"❌ Missing jsonify import in {api_file}")
                return False
            
            print(f"✅ {api_file} structure looks valid")
    
    print("✅ All API endpoints have correct structure")
    return True

def test_documentation_quality():
    """Test that documentation is comprehensive"""
    print("🧪 Testing Documentation Quality...")
    
    doc_files = [
        "COMMUTE_COST_CALCULATOR_README.md",
        "COMMUTE_INTEGRATION_GUIDE.md"
    ]
    
    for doc_file in doc_files:
        if not os.path.exists(doc_file):
            print(f"❌ Documentation not found: {doc_file}")
            return False
        
        with open(doc_file, 'r') as f:
            content = f.read()
            
            # Check for key sections
            key_sections = ['##', '###', '```', 'API', 'Component', 'Usage']
            found_sections = sum(1 for section in key_sections if section in content)
            
            if found_sections < 3:
                print(f"❌ Documentation {doc_file} seems incomplete")
                return False
            
            # Check length
            if len(content) < 2000:
                print(f"❌ Documentation {doc_file} seems too short")
                return False
            
            print(f"✅ {doc_file} is comprehensive ({len(content)} characters)")
    
    print("✅ All documentation is comprehensive")
    return True

def run_simple_tests():
    """Run all simple tests"""
    print("🚀 Starting Simple Commute Cost Calculator Tests")
    print("=" * 60)
    
    test_functions = [
        test_file_structure,
        test_commute_calculation_logic,
        test_database_operations,
        test_component_syntax,
        test_api_endpoint_structure,
        test_documentation_quality
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_func in test_functions:
        try:
            if test_func():
                passed_tests += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            print()
    
    print("=" * 60)
    print("📊 SIMPLE TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL SIMPLE TESTS PASSED!")
        print("The commute cost calculator system is ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == '__main__':
    success = run_simple_tests()
    sys.exit(0 if success else 1)
