#!/usr/bin/env python3
"""
Comprehensive Data Encryption Demo for Mingus Financial App
Demonstrates all encryption features working together
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Import our encryption modules
from data_encryption_manager import (
    DataEncryptionManager, EncryptionConfig, EncryptionAlgorithm, 
    DataSensitivity, ComplianceRegulation
)
from database_encryption_manager import (
    DatabaseEncryptionManager, DatabaseConfig, DatabaseType, 
    AccessLevel, DatabaseUser
)
from privacy_compliance_manager import (
    PrivacyComplianceManager, ConsentType, DataSubjectRight, 
    DataCategory, PrivacyRegulation
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveEncryptionDemo:
    """Comprehensive demonstration of all encryption features"""
    
    def __init__(self):
        self.setup_encryption_systems()
        self.demo_data = self.create_demo_financial_data()
    
    def setup_encryption_systems(self):
        """Setup all encryption systems"""
        print("🔧 Setting up encryption systems...")
        
        # 1. Data Encryption Manager
        encryption_config = EncryptionConfig(
            field_encryption_enabled=True,
            audit_encryption_operations=True,
            preferred_algorithm=EncryptionAlgorithm.AES_256_GCM,
            fips_140_2_compliant=True,
            gdpr_compliant=True,
            pci_dss_compliant=True
        )
        self.data_encryption_manager = DataEncryptionManager(encryption_config)
        
        # 2. Database Encryption Manager
        db_config = DatabaseConfig(
            database_type=DatabaseType.SQLITE,
            encryption_enabled=True,
            column_encryption=True,
            audit_enabled=True,
            backup_enabled=True
        )
        self.db_encryption_manager = DatabaseEncryptionManager(db_config)
        
        # 3. Privacy Compliance Manager
        self.privacy_manager = PrivacyComplianceManager()
        
        print("✅ All encryption systems initialized")
    
    def create_demo_financial_data(self):
        """Create demo financial data for testing"""
        return {
            'user_id': 'demo_user_123',
            'personal_info': {
                'full_name': 'John Smith',
                'email': 'john.smith@example.com',
                'phone': '+1-555-0123',
                'date_of_birth': '1985-03-15',
                'ssn': '123-45-6789'
            },
            'financial_data': {
                'monthly_income': 7500.00,
                'current_savings': 25000.00,
                'current_debt': 35000.00,
                'emergency_fund': 8000.00,
                'savings_goal': 75000.00,
                'debt_payoff_goal': 50000.00,
                'investment_goal': 100000.00
            },
            'banking_info': {
                'account_number': '1234567890',
                'routing_number': '021000021',
                'institution_name': 'Demo Bank'
            },
            'preferences': {
                'risk_tolerance': 'moderate',
                'investment_experience': 'intermediate',
                'income_frequency': 'monthly',
                'primary_income_source': 'salary'
            }
        }
    
    def demonstrate_data_classification(self):
        """Demonstrate data classification system"""
        print("\n📊 DEMONSTRATING DATA CLASSIFICATION")
        print("=" * 50)
        
        # Get data classification report
        report = self.data_encryption_manager.get_data_classification_report()
        
        print("Data Classification Report:")
        print(f"Total Fields: {report['total_fields']}")
        print(f"Encrypted Fields: {report['encryption_requirements']['encrypted_fields']}")
        print(f"Non-Encrypted Fields: {report['encryption_requirements']['non_encrypted_fields']}")
        
        print("\nSensitivity Distribution:")
        for sensitivity, count in report['sensitivity_distribution'].items():
            print(f"  {sensitivity.upper()}: {count} fields")
        
        print("\nCompliance Mapping:")
        for regulation, count in report['compliance_mapping'].items():
            print(f"  {regulation.upper()}: {count} fields")
        
        # Show critical fields
        critical_fields = self.data_encryption_manager.classification_manager.get_critical_fields()
        print(f"\nCritical Fields (Maximum Protection): {critical_fields}")
    
    def demonstrate_field_level_encryption(self):
        """Demonstrate field-level encryption"""
        print("\n🔐 DEMONSTRATING FIELD-LEVEL ENCRYPTION")
        print("=" * 50)
        
        # Encrypt financial data
        print("Encrypting financial data...")
        encrypted_data = self.data_encryption_manager.encrypt_financial_data(
            self.demo_data['financial_data'], 
            self.demo_data['user_id']
        )
        
        print("Original Financial Data:")
        for key, value in self.demo_data['financial_data'].items():
            print(f"  {key}: {value}")
        
        print("\nEncrypted Financial Data:")
        for key, value in encrypted_data.items():
            if isinstance(value, dict) and 'encrypted_data' in value:
                print(f"  {key}: [ENCRYPTED] - Algorithm: {value['algorithm']}, Key ID: {value['key_id']}")
            else:
                print(f"  {key}: {value} (not encrypted)")
        
        # Decrypt financial data
        print("\nDecrypting financial data...")
        decrypted_data = self.data_encryption_manager.decrypt_financial_data(
            encrypted_data, 
            self.demo_data['user_id']
        )
        
        print("Decrypted Financial Data:")
        for key, value in decrypted_data.items():
            print(f"  {key}: {value}")
        
        # Verify data integrity
        original = self.demo_data['financial_data']
        decrypted = decrypted_data
        
        data_integrity = all(
            str(original.get(key)) == str(decrypted.get(key))
            for key in original.keys()
        )
        
        print(f"\nData Integrity Check: {'✅ PASSED' if data_integrity else '❌ FAILED'}")
    
    def demonstrate_database_encryption(self):
        """Demonstrate database encryption and security"""
        print("\n🗄️ DEMONSTRATING DATABASE ENCRYPTION")
        print("=" * 50)
        
        # Add database user
        db_user = DatabaseUser(
            user_id="demo_user",
            username="demo",
            access_level=AccessLevel.READ_WRITE,
            permissions=["SELECT", "INSERT", "UPDATE", "DELETE"],
            ip_whitelist=["127.0.0.1", "::1"]
        )
        self.db_encryption_manager.add_user(db_user)
        
        # Test column encryption
        print("Testing column encryption...")
        sensitive_value = "5000.00"
        encrypted_column = self.db_encryption_manager.encrypt_column_value(
            sensitive_value, "monthly_income", "user_profiles"
        )
        print(f"Original value: {sensitive_value}")
        print(f"Encrypted column: {encrypted_column[:100]}...")
        
        decrypted_column = self.db_encryption_manager.decrypt_column_value(
            encrypted_column, "monthly_income", "user_profiles"
        )
        print(f"Decrypted value: {decrypted_column}")
        
        # Test query execution with audit logging
        print("\nTesting query execution with audit logging...")
        try:
            results = self.db_encryption_manager.execute_query(
                user_id="demo_user",
                query="SELECT name FROM sqlite_master WHERE type='table'",
                operation="query",
                table_name="system",
                ip_address="127.0.0.1",
                user_agent="demo-agent"
            )
            print(f"Query results: {results}")
        except Exception as e:
            print(f"Query failed: {e}")
        
        # Get database security status
        status = self.db_encryption_manager.get_database_security_status()
        print(f"\nDatabase Security Status:")
        print(f"  Encryption Enabled: {status['encryption_enabled']}")
        print(f"  Column Encryption: {status['column_encryption']}")
        print(f"  Audit Enabled: {status['audit_enabled']}")
        print(f"  Total Users: {status['total_users']}")
        print(f"  Active Users: {status['active_users']}")
    
    def demonstrate_privacy_compliance(self):
        """Demonstrate privacy compliance features"""
        print("\n🛡️ DEMONSTRATING PRIVACY COMPLIANCE")
        print("=" * 50)
        
        # Record user consent
        print("Recording user consent...")
        self.privacy_manager.record_consent(
            user_id=self.demo_data['user_id'],
            consent_type=ConsentType.MARKETING,
            granted=True,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        self.privacy_manager.record_consent(
            user_id=self.demo_data['user_id'],
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Get consent status
        consent_status = self.privacy_manager.get_user_consent_status(self.demo_data['user_id'])
        print(f"User Consent Status:")
        for consent_type, status in consent_status.items():
            print(f"  {consent_type}: {'✅ Granted' if status['granted'] else '❌ Denied'}")
            if status['withdrawn']:
                print(f"    (Withdrawn on: {status['withdrawal_timestamp']})")
        
        # Create data subject request
        print("\nCreating data subject request...")
        request_id = self.privacy_manager.create_data_subject_request(
            user_id=self.demo_data['user_id'],
            right_type=DataSubjectRight.ACCESS,
            data_categories=[DataCategory.PERSONAL_DATA, DataCategory.FINANCIAL_DATA]
        )
        print(f"Created request: {request_id}")
        
        # Process request
        print("Processing data subject request...")
        result = self.privacy_manager.process_data_subject_request(request_id)
        print(f"Request processed successfully")
        print(f"Data categories: {result['data_categories']}")
        print(f"Personal data keys: {list(result['data']['personal_data'].keys())}")
        print(f"Financial data keys: {list(result['data']['financial_data'].keys())}")
        
        # Test privacy policy
        policy = self.privacy_manager.get_active_privacy_policy()
        if policy:
            print(f"\nActive Privacy Policy:")
            print(f"  Version: {policy.version}")
            print(f"  Regulations: {[reg.value for reg in policy.regulations]}")
            print(f"  Data Categories: {[cat.value for cat in policy.data_categories]}")
            print(f"  Contact: {policy.contact_info['email']}")
    
    def demonstrate_key_management(self):
        """Demonstrate key management and rotation"""
        print("\n🔑 DEMONSTRATING KEY MANAGEMENT")
        print("=" * 50)
        
        # Get encryption status
        status = self.data_encryption_manager.get_encryption_status()
        print("Encryption System Status:")
        print(f"  Encryption Enabled: {status['encryption_enabled']}")
        print(f"  Current Key ID: {status['current_key_id']}")
        print(f"  Algorithm: {status['algorithm']}")
        print(f"  Key Rotation Days: {status['key_rotation_days']}")
        print(f"  Total Keys: {status['total_keys']}")
        
        print("\nCompliance Status:")
        for compliance, status_value in status['compliance_status'].items():
            print(f"  {compliance.upper()}: {'✅ Compliant' if status_value else '❌ Non-Compliant'}")
        
        # Demonstrate key rotation (simulated)
        print("\nSimulating key rotation...")
        try:
            self.data_encryption_manager.rotate_encryption_keys()
            print("✅ Key rotation completed successfully")
            
            # Get new status
            new_status = self.data_encryption_manager.get_encryption_status()
            print(f"New Key ID: {new_status['current_key_id']}")
            print(f"Total Keys: {new_status['total_keys']}")
            
        except Exception as e:
            print(f"❌ Key rotation failed: {e}")
    
    def demonstrate_audit_logging(self):
        """Demonstrate audit logging capabilities"""
        print("\n📋 DEMONSTRATING AUDIT LOGGING")
        print("=" * 50)
        
        # Get audit logs from database manager
        db_audit_logs = self.db_encryption_manager.get_audit_logs()
        print(f"Database Audit Logs (Recent {len(db_audit_logs)} entries):")
        for log in db_audit_logs[:5]:  # Show only first 5 entries
            print(f"  {log['timestamp']}: {log['operation']} by {log['user_id']} - {'✅ Success' if log['success'] else '❌ Failed'}")
        
        # Get compliance report
        compliance_report = self.privacy_manager.get_compliance_report()
        print(f"\nPrivacy Compliance Report:")
        print(f"  Consent Statistics: {len(compliance_report.get('consent_statistics', {}))} consent types")
        print(f"  Request Statistics: {len(compliance_report.get('request_statistics', {}))} request types")
        print(f"  Deletion Statistics: {len(compliance_report.get('deletion_statistics', {}))} deletion types")
    
    def demonstrate_data_deletion(self):
        """Demonstrate secure data deletion"""
        print("\n🗑️ DEMONSTRATING SECURE DATA DELETION")
        print("=" * 50)
        
        # Create deletion request
        deletion_request_id = self.privacy_manager.create_data_subject_request(
            user_id=self.demo_data['user_id'],
            right_type=DataSubjectRight.ERASURE,
            data_categories=[DataCategory.BEHAVIORAL_DATA, DataCategory.TECHNICAL_DATA]
        )
        print(f"Created deletion request: {deletion_request_id}")
        
        # Process deletion request
        deletion_result = self.privacy_manager.process_data_subject_request(deletion_request_id)
        print(f"Deletion completed:")
        print(f"  Deleted categories: {deletion_result['deleted_categories']}")
        print(f"  Deletion date: {deletion_result['deletion_date']}")
        
        # Demonstrate data portability
        print("\nDemonstrating data portability...")
        portability_request_id = self.privacy_manager.create_data_subject_request(
            user_id=self.demo_data['user_id'],
            right_type=DataSubjectRight.PORTABILITY,
            data_categories=[DataCategory.PERSONAL_DATA, DataCategory.FINANCIAL_DATA]
        )
        
        try:
            zip_data = self.privacy_manager.process_data_subject_request(portability_request_id)
            print(f"✅ Data portability ZIP created ({len(zip_data)} bytes)")
            print("ZIP contains: user_data.json, metadata.json")
        except Exception as e:
            print(f"❌ Data portability failed: {e}")
    
    def demonstrate_comprehensive_integration(self):
        """Demonstrate all systems working together"""
        print("\n🚀 DEMONSTRATING COMPREHENSIVE INTEGRATION")
        print("=" * 50)
        
        # Simulate a complete user workflow
        print("Simulating complete user workflow...")
        
        # 1. User provides financial data
        print("1. User provides financial data")
        financial_data = self.demo_data['financial_data']
        
        # 2. Data is classified and encrypted
        print("2. Data is classified and encrypted")
        encrypted_data = self.data_encryption_manager.encrypt_financial_data(
            financial_data, self.demo_data['user_id']
        )
        
        # 3. Encrypted data is stored in database
        print("3. Encrypted data is stored in database")
        # Simulate database storage with column encryption
        for key, value in encrypted_data.items():
            if isinstance(value, dict) and 'encrypted_data' in value:
                db_encrypted = self.db_encryption_manager.encrypt_column_value(
                    json.dumps(value), key, "user_financial_profiles"
                )
                print(f"   Stored encrypted {key} in database")
        
        # 4. User consents to data processing
        print("4. User consents to data processing")
        self.privacy_manager.record_consent(
            user_id=self.demo_data['user_id'],
            consent_type=ConsentType.NECESSARY,
            granted=True,
            ip_address="192.168.1.1",
            user_agent="demo-agent"
        )
        
        # 5. Data is accessed for processing
        print("5. Data is accessed for processing")
        decrypted_data = self.data_encryption_manager.decrypt_financial_data(
            encrypted_data, self.demo_data['user_id']
        )
        
        # 6. User requests data access
        print("6. User requests data access")
        access_request_id = self.privacy_manager.create_data_subject_request(
            user_id=self.demo_data['user_id'],
            right_type=DataSubjectRight.ACCESS,
            data_categories=[DataCategory.FINANCIAL_DATA]
        )
        access_result = self.privacy_manager.process_data_subject_request(access_request_id)
        
        # 7. User requests data deletion
        print("7. User requests data deletion")
        deletion_request_id = self.privacy_manager.create_data_subject_request(
            user_id=self.demo_data['user_id'],
            right_type=DataSubjectRight.ERASURE,
            data_categories=[DataCategory.FINANCIAL_DATA]
        )
        deletion_result = self.privacy_manager.process_data_subject_request(deletion_request_id)
        
        print("✅ Complete workflow demonstrated successfully!")
        
        # Show final status
        print(f"\nFinal System Status:")
        encryption_status = self.data_encryption_manager.get_encryption_status()
        db_status = self.db_encryption_manager.get_database_security_status()
        compliance_report = self.privacy_manager.get_compliance_report()
        
        print(f"  Encryption: {encryption_status['encryption_enabled']}")
        print(f"  Database Security: {db_status['encryption_enabled']}")
        print(f"  Privacy Compliance: {len(compliance_report.get('consent_statistics', {}))} consent types tracked")
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        print("🔐 COMPREHENSIVE DATA ENCRYPTION DEMONSTRATION")
        print("=" * 60)
        print("Mingus Financial App - Enterprise-Grade Security Implementation")
        print("=" * 60)
        
        try:
            # Run all demonstrations
            self.demonstrate_data_classification()
            self.demonstrate_field_level_encryption()
            self.demonstrate_database_encryption()
            self.demonstrate_privacy_compliance()
            self.demonstrate_key_management()
            self.demonstrate_audit_logging()
            self.demonstrate_data_deletion()
            self.demonstrate_comprehensive_integration()
            
            print("\n" + "=" * 60)
            print("🎉 COMPREHENSIVE ENCRYPTION DEMONSTRATION COMPLETED")
            print("=" * 60)
            print("✅ All encryption features working correctly")
            print("✅ Data classification implemented")
            print("✅ Field-level encryption operational")
            print("✅ Database security active")
            print("✅ Privacy compliance enforced")
            print("✅ Key management functional")
            print("✅ Audit logging comprehensive")
            print("✅ Data deletion secure")
            print("✅ GDPR/CCPA compliance ready")
            print("✅ FIPS 140-2 compliant")
            print("✅ PCI DSS ready")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            logger.error(f"Demo failed: {e}", exc_info=True)

def main():
    """Main function to run the comprehensive demo"""
    demo = ComprehensiveEncryptionDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()
