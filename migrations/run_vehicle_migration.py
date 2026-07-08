#!/usr/bin/env python3
"""
Vehicle Management Migration Runner
Runs Alembic migration for vehicle management tables
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime
from pathlib import Path

def check_alembic_installed():
    """Check if Alembic is installed"""
    try:
        import alembic
        print("✅ Alembic is installed")
        return True
    except ImportError:
        print("❌ Alembic is not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "alembic"])
            print("✅ Alembic installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Alembic")
            return False

def check_database_exists():
    """Check if the database exists and has the users table"""
    db_path = "mingus_vehicles.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table not found in database")
            conn.close()
            return False
        
        # Check if vehicle tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        if cursor.fetchone():
            print("⚠️  Vehicle tables already exist")
            conn.close()
            return False
        
        print("✅ Database and users table found")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def create_alembic_version_table():
    """Create Alembic version table if it doesn't exist"""
    db_path = "mingus_vehicles.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create alembic_version table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(128) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        ''')
        
        # Check if we need to set initial version
        cursor.execute("SELECT version_num FROM alembic_version")
        if not cursor.fetchone():
            # Set initial version to 003_seed_initial_data
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('003_seed_initial_data')")
        
        conn.commit()
        conn.close()
        print("✅ Alembic version table ready")
        return True
        
    except Exception as e:
        print(f"❌ Error creating Alembic version table: {e}")
        return False

def run_migration():
    """Run the vehicle management migration"""
    try:
        # Change to migrations directory
        os.chdir("migrations")
        
        # Run Alembic upgrade
        print("🚀 Running Alembic migration...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            print("Migration output:")
            print(result.stdout)
            return True
        else:
            print("❌ Migration failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False
    finally:
        # Change back to project root
        os.chdir("..")

def verify_migration():
    """Verify that the migration was successful"""
    db_path = "mingus_vehicles.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all vehicle tables exist
        required_tables = [
            'vehicles',
            'maintenance_predictions', 
            'commute_scenarios',
            'msa_gas_prices'
        ]
        
        print("\n🔍 Verifying migration...")
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"✅ {table} table created")
            else:
                print(f"❌ {table} table missing")
                return False
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        print(f"✅ {len(indexes)} indexes created")
        
        # Check MSA gas prices data
        cursor.execute("SELECT COUNT(*) FROM msa_gas_prices")
        count = cursor.fetchone()[0]
        print(f"✅ {count} MSA gas prices inserted")
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_list(vehicles)")
        fk_constraints = cursor.fetchall()
        print(f"✅ {len(fk_constraints)} foreign key constraints on vehicles table")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function"""
    print("🚗 Mingus Vehicle Management Migration")
    print("=" * 50)
    
    # Check prerequisites
    if not check_alembic_installed():
        return 1
    
    if not check_database_exists():
        print("\n💡 To create the database, run:")
        print("   python backend/models/init_vehicle_db.py")
        return 1
    
    if not create_alembic_version_table():
        return 1
    
    # Run migration
    if not run_migration():
        return 1
    
    # Verify migration
    if not verify_migration():
        return 1
    
    print("\n🎉 Vehicle management migration completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Test the API endpoints: /api/vehicles/*")
    print("   2. Create sample data: python backend/models/init_vehicle_db.py")
    print("   3. Run tests: python test_vehicle_models.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
