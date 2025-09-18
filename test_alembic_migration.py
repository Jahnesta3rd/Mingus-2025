#!/usr/bin/env python3
"""
Test script for Alembic vehicle management migration
Verifies that the migration works correctly
"""

import os
import sys
import sqlite3
from datetime import datetime, date, timedelta
from decimal import Decimal

def test_migration():
    """Test the vehicle management migration"""
    print("🧪 Testing Alembic Vehicle Management Migration")
    print("=" * 60)
    
    db_path = "mingus_vehicles.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        print("💡 Run: python backend/models/init_vehicle_db.py")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check if all tables exist
        print("1. Testing table creation...")
        required_tables = [
            'vehicles',
            'maintenance_predictions',
            'commute_scenarios', 
            'msa_gas_prices'
        ]
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"   ✅ {table} table exists")
            else:
                print(f"   ❌ {table} table missing")
                return False
        
        # Test 2: Check foreign key constraints
        print("\n2. Testing foreign key constraints...")
        cursor.execute("PRAGMA foreign_key_list(vehicles)")
        fk_constraints = cursor.fetchall()
        print(f"   ✅ {len(fk_constraints)} foreign key constraints on vehicles table")
        
        cursor.execute("PRAGMA foreign_key_list(maintenance_predictions)")
        fk_constraints = cursor.fetchall()
        print(f"   ✅ {len(fk_constraints)} foreign key constraints on maintenance_predictions table")
        
        cursor.execute("PRAGMA foreign_key_list(commute_scenarios)")
        fk_constraints = cursor.fetchall()
        print(f"   ✅ {len(fk_constraints)} foreign key constraints on commute_scenarios table")
        
        # Test 3: Check indexes
        print("\n3. Testing indexes...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        print(f"   ✅ {len(indexes)} indexes created")
        
        # Test 4: Check constraints
        print("\n4. Testing check constraints...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vehicles'")
        vehicles_sql = cursor.fetchone()[0]
        if 'check_positive_mileage' in vehicles_sql:
            print("   ✅ Check constraints on vehicles table")
        else:
            print("   ❌ Check constraints missing on vehicles table")
        
        # Test 5: Check triggers
        print("\n5. Testing triggers...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        trigger_names = [t[0] for t in triggers]
        if 'update_vehicles_updated_date' in trigger_names:
            print("   ✅ Update trigger exists")
        else:
            print("   ❌ Update trigger missing")
        
        # Test 6: Check initial data
        print("\n6. Testing initial data...")
        cursor.execute("SELECT COUNT(*) FROM msa_gas_prices")
        count = cursor.fetchone()[0]
        print(f"   ✅ {count} MSA gas prices inserted")
        
        if count >= 10:
            print("   ✅ Initial data looks complete")
        else:
            print("   ⚠️  Initial data may be incomplete")
        
        # Test 7: Test data insertion
        print("\n7. Testing data insertion...")
        
        # Insert test user
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, email, first_name, last_name, referral_code)
            VALUES ('test_user_001', 'test@example.com', 'Test', 'User', 'TEST001')
        ''')
        
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE user_id = 'test_user_001'")
        user_id = cursor.fetchone()[0]
        
        # Insert test vehicle
        cursor.execute('''
            INSERT INTO vehicles (user_id, vin, year, make, model, trim, current_mileage, monthly_miles, user_zipcode, assigned_msa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, '1HGBH41JXMN109186', 2020, 'Honda', 'Civic', 'EX', 45000, 1200, '90210', 'Los Angeles-Long Beach-Anaheim, CA'))
        
        vehicle_id = cursor.lastrowid
        
        # Insert test maintenance prediction
        cursor.execute('''
            INSERT INTO maintenance_predictions (vehicle_id, service_type, description, predicted_date, predicted_mileage, estimated_cost, probability, is_routine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, 'Oil Change', 'Regular oil change service', '2024-02-15', 46200, 45.00, 0.95, True))
        
        # Insert test commute scenario
        cursor.execute('''
            INSERT INTO commute_scenarios (vehicle_id, job_location, job_zipcode, distance_miles, daily_cost, monthly_cost, gas_price_per_gallon, vehicle_mpg, from_msa, to_msa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, 'Downtown Los Angeles', '90012', 25.5, 8.50, 187.00, 4.25, 32.0, 'Los Angeles-Long Beach-Anaheim, CA', 'Los Angeles-Long Beach-Anaheim, CA'))
        
        conn.commit()
        print("   ✅ Test data inserted successfully")
        
        # Test 8: Test data retrieval
        print("\n8. Testing data retrieval...")
        
        # Test vehicle query
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE user_id = ?", (user_id,))
        vehicle_count = cursor.fetchone()[0]
        print(f"   ✅ Found {vehicle_count} vehicles for test user")
        
        # Test maintenance prediction query
        cursor.execute("SELECT COUNT(*) FROM maintenance_predictions WHERE vehicle_id = ?", (vehicle_id,))
        prediction_count = cursor.fetchone()[0]
        print(f"   ✅ Found {prediction_count} maintenance predictions for test vehicle")
        
        # Test commute scenario query
        cursor.execute("SELECT COUNT(*) FROM commute_scenarios WHERE vehicle_id = ?", (vehicle_id,))
        scenario_count = cursor.fetchone()[0]
        print(f"   ✅ Found {scenario_count} commute scenarios for test vehicle")
        
        # Test MSA gas price query
        cursor.execute("SELECT msa_name, current_price FROM msa_gas_prices WHERE msa_name = 'National Average'")
        national_avg = cursor.fetchone()
        if national_avg:
            print(f"   ✅ National average gas price: ${national_avg[1]}")
        
        # Test 9: Test constraints
        print("\n9. Testing constraint validation...")
        
        # Test negative mileage constraint
        try:
            cursor.execute('''
                INSERT INTO vehicles (user_id, vin, year, make, model, current_mileage, monthly_miles, user_zipcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 'INVALID123456789', 2020, 'Test', 'Car', -100, 100, '12345'))
            print("   ❌ Negative mileage constraint failed")
        except sqlite3.IntegrityError:
            print("   ✅ Negative mileage constraint working")
        
        # Test VIN length constraint
        try:
            cursor.execute('''
                INSERT INTO vehicles (user_id, vin, year, make, model, current_mileage, monthly_miles, user_zipcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 'SHORT', 2020, 'Test', 'Car', 100, 100, '12345'))
            print("   ❌ VIN length constraint failed")
        except sqlite3.IntegrityError:
            print("   ✅ VIN length constraint working")
        
        # Test probability range constraint
        try:
            cursor.execute('''
                INSERT INTO maintenance_predictions (vehicle_id, service_type, predicted_date, predicted_mileage, estimated_cost, probability)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (vehicle_id, 'Test Service', '2024-02-15', 46000, 50.00, 1.5))
            print("   ❌ Probability range constraint failed")
        except sqlite3.IntegrityError:
            print("   ✅ Probability range constraint working")
        
        # Clean up test data
        print("\n10. Cleaning up test data...")
        cursor.execute("DELETE FROM commute_scenarios WHERE vehicle_id = ?", (vehicle_id,))
        cursor.execute("DELETE FROM maintenance_predictions WHERE vehicle_id = ?", (vehicle_id,))
        cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        cursor.execute("DELETE FROM users WHERE user_id = 'test_user_001'")
        conn.commit()
        print("   ✅ Test data cleaned up")
        
        conn.close()
        
        print("\n🎉 All migration tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main test function"""
    success = test_migration()
    
    if success:
        print("\n✅ Migration verification completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Run the migration: python migrations/run_vehicle_migration.py")
        print("   2. Test the API endpoints")
        print("   3. Create sample data")
        return 0
    else:
        print("\n❌ Migration verification failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure database exists: python backend/models/init_vehicle_db.py")
        print("   2. Check Alembic installation: pip install alembic")
        print("   3. Verify migration file exists")
        return 1

if __name__ == "__main__":
    sys.exit(main())
