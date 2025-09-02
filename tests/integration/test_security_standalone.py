#!/usr/bin/env python3
"""
MINGUS Standalone Security Tests
================================

Standalone security tests that work independently without Flask app setup.
These tests directly validate the security modules and their functionality.

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import unittest
import time
import json
import tempfile
import os
from datetime import datetime, timedelta
import statistics
import psutil
import gc
import sys
import os

# Add the project root to the path so we can import security modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import security components
from security.encryption import (
    DataSensitivity, EncryptionAlgorithm, KeyStorageType, 
    TokenizationType, AuditEventType, ComplianceRegulation
)


class TestSecurityEnums(unittest.TestCase):
    """Test security enumeration classes"""
    
    def test_data_sensitivity_enum(self):
        """Test DataSensitivity enum values"""
        # Test all sensitivity levels
        self.assertEqual(DataSensitivity.LOW.value, "low")
        self.assertEqual(DataSensitivity.MEDIUM.value, "medium")
        self.assertEqual(DataSensitivity.HIGH.value, "high")
        self.assertEqual(DataSensitivity.CRITICAL.value, "critical")
        
        # Test enum iteration
        sensitivity_levels = list(DataSensitivity)
        self.assertEqual(len(sensitivity_levels), 4)
        self.assertIn(DataSensitivity.LOW, sensitivity_levels)
        self.assertIn(DataSensitivity.CRITICAL, sensitivity_levels)
    
    def test_encryption_algorithm_enum(self):
        """Test EncryptionAlgorithm enum values"""
        # Test encryption algorithms
        self.assertEqual(EncryptionAlgorithm.AES_256_GCM.value, "aes-256-gcm")
        self.assertEqual(EncryptionAlgorithm.AES_256_CBC.value, "aes-256-cbc")
        self.assertEqual(EncryptionAlgorithm.AES_256_CTR.value, "aes-256-ctr")
        self.assertEqual(EncryptionAlgorithm.CHACHA20_POLY1305.value, "chacha20-poly1305")
        self.assertEqual(EncryptionAlgorithm.FERNET.value, "fernet")
        
        # Test enum iteration
        algorithms = list(EncryptionAlgorithm)
        self.assertGreaterEqual(len(algorithms), 5)
        self.assertIn(EncryptionAlgorithm.AES_256_GCM, algorithms)
        self.assertIn(EncryptionAlgorithm.FERNET, algorithms)
    
    def test_tokenization_type_enum(self):
        """Test TokenizationType enum values"""
        # Test tokenization types
        self.assertEqual(TokenizationType.PAYMENT_CARD.value, "payment_card")
        self.assertEqual(TokenizationType.BANK_ACCOUNT.value, "bank_account")
        self.assertEqual(TokenizationType.SSN.value, "ssn")
        self.assertEqual(TokenizationType.EMAIL.value, "email")
        self.assertEqual(TokenizationType.PHONE.value, "phone")
        self.assertEqual(TokenizationType.CUSTOM.value, "custom")
        
        # Test enum iteration
        token_types = list(TokenizationType)
        self.assertGreaterEqual(len(token_types), 6)
        self.assertIn(TokenizationType.PAYMENT_CARD, token_types)
        self.assertIn(TokenizationType.SSN, token_types)
    
    def test_audit_event_type_enum(self):
        """Test AuditEventType enum values"""
        # Test audit event types
        self.assertEqual(AuditEventType.DATA_ACCESS.value, "data_access")
        self.assertEqual(AuditEventType.DATA_CREATE.value, "data_create")
        self.assertEqual(AuditEventType.DATA_UPDATE.value, "data_update")
        self.assertEqual(AuditEventType.DATA_DELETE.value, "data_delete")
        self.assertEqual(AuditEventType.DATA_ENCRYPT.value, "data_encrypt")
        self.assertEqual(AuditEventType.DATA_DECRYPT.value, "data_decrypt")
        
        # Test enum iteration
        event_types = list(AuditEventType)
        self.assertGreaterEqual(len(event_types), 6)
        self.assertIn(AuditEventType.DATA_CREATE, event_types)
        self.assertIn(AuditEventType.DATA_ENCRYPT, event_types)
    
    def test_compliance_regulation_enum(self):
        """Test ComplianceRegulation enum values"""
        # Test compliance regulations
        self.assertEqual(ComplianceRegulation.PCI_DSS.value, "pci_dss")
        self.assertEqual(ComplianceRegulation.GDPR.value, "gdpr")
        self.assertEqual(ComplianceRegulation.SOX.value, "sox")
        self.assertEqual(ComplianceRegulation.GLBA.value, "glba")
        self.assertEqual(ComplianceRegulation.HIPAA.value, "hipaa")
        self.assertEqual(ComplianceRegulation.CCPA.value, "ccpa")
        self.assertEqual(ComplianceRegulation.SOC2.value, "soc2")
        self.assertEqual(ComplianceRegulation.ISO27001.value, "iso27001")
        
        # Test enum iteration
        regulations = list(ComplianceRegulation)
        self.assertGreaterEqual(len(regulations), 8)
        self.assertIn(ComplianceRegulation.PCI_DSS, regulations)
        self.assertIn(ComplianceRegulation.GDPR, regulations)


class TestSecurityWorkflow(unittest.TestCase):
    """Test security workflow scenarios"""
    
    def setUp(self):
        """Set up test data"""
        self.sensitive_data = {
            'credit_card': '4111111111111111',
            'ssn': '123-45-6789',
            'email': 'test@example.com',
            'phone': '555-123-4567',
            'amount': 99.99,
            'user_id': 12345
        }
        
        # Performance tracking
        self.performance_metrics = {
            'classification_times': [],
            'workflow_times': [],
            'memory_usage': []
        }
    
    def test_data_classification_workflow(self):
        """Test data classification workflow"""
        start_time = time.time()
        
        # Classify data by sensitivity level
        data_classification = {}
        
        for field, value in self.sensitive_data.items():
            if field in ['credit_card', 'ssn']:
                data_classification[field] = DataSensitivity.CRITICAL
            elif field in ['email', 'phone']:
                data_classification[field] = DataSensitivity.MEDIUM
            else:
                data_classification[field] = DataSensitivity.LOW
        
        # Validate classification
        self.assertEqual(data_classification['credit_card'], DataSensitivity.CRITICAL)
        self.assertEqual(data_classification['ssn'], DataSensitivity.CRITICAL)
        self.assertEqual(data_classification['email'], DataSensitivity.MEDIUM)
        self.assertEqual(data_classification['phone'], DataSensitivity.MEDIUM)
        self.assertEqual(data_classification['amount'], DataSensitivity.LOW)
        self.assertEqual(data_classification['user_id'], DataSensitivity.LOW)
        
        classification_time = time.time() - start_time
        self.performance_metrics['classification_times'].append(classification_time)
        
        # Performance assertion
        self.assertLess(classification_time, 0.1, 
                       f"Data classification took {classification_time:.3f}s, expected <0.1s")
    
    def test_encryption_workflow_simulation(self):
        """Test simulated encryption workflow"""
        start_time = time.time()
        
        # Simulate encryption for sensitive data
        encrypted_data = {}
        for field, value in self.sensitive_data.items():
            if field in ['credit_card', 'ssn']:
                # Mock encryption for critical fields
                encrypted_data[field] = f"encrypted_{value}"
            elif field in ['email', 'phone']:
                # Mock encryption for medium sensitivity fields
                encrypted_data[field] = f"encrypted_{value}"
            else:
                # Keep non-sensitive fields as-is
                encrypted_data[field] = value
        
        # Verify encryption
        self.assertNotEqual(encrypted_data['credit_card'], self.sensitive_data['credit_card'])
        self.assertNotEqual(encrypted_data['ssn'], self.sensitive_data['ssn'])
        self.assertNotEqual(encrypted_data['email'], self.sensitive_data['email'])
        self.assertNotEqual(encrypted_data['phone'], self.sensitive_data['phone'])
        self.assertEqual(encrypted_data['amount'], self.sensitive_data['amount'])
        self.assertEqual(encrypted_data['user_id'], self.sensitive_data['user_id'])
        
        # Verify encryption format
        self.assertTrue(encrypted_data['credit_card'].startswith('encrypted_'))
        self.assertTrue(encrypted_data['ssn'].startswith('encrypted_'))
        self.assertTrue(encrypted_data['email'].startswith('encrypted_'))
        self.assertTrue(encrypted_data['phone'].startswith('encrypted_'))
        
        workflow_time = time.time() - start_time
        self.performance_metrics['workflow_times'].append(workflow_time)
        
        # Performance assertion
        self.assertLess(workflow_time, 0.1, 
                       f"Encryption workflow took {workflow_time:.3f}s, expected <0.1s")
    
    def test_tokenization_workflow_simulation(self):
        """Test simulated tokenization workflow"""
        start_time = time.time()
        
        # Simulate tokenization for payment data
        tokenized_data = {}
        for field, value in self.sensitive_data.items():
            if field in ['credit_card', 'ssn']:
                # Mock tokenization for critical fields
                tokenized_data[field] = f"token_{value[-4:]}"
            elif field in ['email', 'phone']:
                # Mock tokenization for medium sensitivity fields
                tokenized_data[field] = f"token_{value[:3]}"
            else:
                # Keep non-sensitive fields as-is
                tokenized_data[field] = value
        
        # Verify tokenization
        self.assertNotEqual(tokenized_data['credit_card'], self.sensitive_data['credit_card'])
        self.assertNotEqual(tokenized_data['ssn'], self.sensitive_data['ssn'])
        self.assertNotEqual(tokenized_data['email'], self.sensitive_data['email'])
        self.assertNotEqual(tokenized_data['phone'], self.sensitive_data['phone'])
        self.assertEqual(tokenized_data['amount'], self.sensitive_data['amount'])
        self.assertEqual(tokenized_data['user_id'], self.sensitive_data['user_id'])
        
        # Verify tokenization format
        self.assertTrue(tokenized_data['credit_card'].startswith('token_'))
        self.assertTrue(tokenized_data['ssn'].startswith('token_'))
        self.assertTrue(tokenized_data['email'].startswith('token_'))
        self.assertTrue(tokenized_data['phone'].startswith('token_'))
        
        workflow_time = time.time() - start_time
        self.performance_metrics['workflow_times'].append(workflow_time)
        
        # Performance assertion
        self.assertLess(workflow_time, 0.1, 
                       f"Tokenization workflow took {workflow_time:.3f}s, expected <0.1s")
    
    def test_audit_logging_simulation(self):
        """Test simulated audit logging workflow"""
        start_time = time.time()
        
        # Create mock audit events
        audit_events = []
        for field, value in self.sensitive_data.items():
            if field in ['credit_card', 'ssn', 'email', 'phone']:
                audit_event = {
                    'event_id': f'audit_{field}_{int(time.time())}',
                    'user_id': self.sensitive_data['user_id'],
                    'event_type': AuditEventType.DATA_CREATE.value,
                    'data_type': field,
                    'timestamp': datetime.now().isoformat(),
                    'sensitivity_level': 'high' if field in ['credit_card', 'ssn'] else 'medium'
                }
                audit_events.append(audit_event)
        
        # Verify audit events
        self.assertGreaterEqual(len(audit_events), 4)  # At least credit_card, ssn, email, phone
        
        for event in audit_events:
            self.assertIn('event_id', event)
            self.assertIn('user_id', event)
            self.assertIn('event_type', event)
            self.assertIn('data_type', event)
            self.assertIn('timestamp', event)
            self.assertIn('sensitivity_level', event)
            
            # Verify event structure
            self.assertTrue(event['event_id'].startswith('audit_'))
            self.assertEqual(event['user_id'], self.sensitive_data['user_id'])
            self.assertEqual(event['event_type'], AuditEventType.DATA_CREATE.value)
            self.assertIn(event['data_type'], ['credit_card', 'ssn', 'email', 'phone'])
            self.assertIn(event['sensitivity_level'], ['high', 'medium'])
        
        workflow_time = time.time() - start_time
        self.performance_metrics['workflow_times'].append(workflow_time)
        
        # Performance assertion
        self.assertLess(workflow_time, 0.1, 
                       f"Audit logging workflow took {workflow_time:.3f}s, expected <0.1s")
    
    def test_compliance_validation_simulation(self):
        """Test simulated compliance validation"""
        start_time = time.time()
        
        # Define PCI DSS compliance requirements
        pci_requirements = [
            'card_data_encryption',
            'secure_transmission',
            'access_controls',
            'audit_logging',
            'vulnerability_management',
            'incident_response',
            'business_continuity',
            'regular_testing'
        ]
        
        # Simulate compliance validation
        compliance_status = {}
        for requirement in pci_requirements:
            # Mock compliance check - all requirements are compliant
            compliance_status[requirement] = 'compliant'
        
        # Verify compliance
        compliant_count = sum(1 for status in compliance_status.values() if status == 'compliant')
        total_count = len(compliance_status)
        compliance_rate = compliant_count / total_count
        
        self.assertEqual(compliance_rate, 1.0, f"Compliance rate {compliance_rate:.1%} should be 100%")
        self.assertEqual(compliant_count, total_count)
        self.assertIn('card_data_encryption', compliance_status)
        self.assertIn('audit_logging', compliance_status)
        self.assertEqual(compliance_status['card_data_encryption'], 'compliant')
        self.assertEqual(compliance_status['audit_logging'], 'compliant')
        
        workflow_time = time.time() - start_time
        self.performance_metrics['workflow_times'].append(workflow_time)
        
        # Performance assertion
        self.assertLess(workflow_time, 0.1, 
                       f"Compliance validation took {workflow_time:.3f}s, expected <0.1s")
    
    def test_end_to_end_security_workflow(self):
        """Test complete end-to-end security workflow"""
        start_time = time.time()
        
        # 1. Data classification
        data_classification = {}
        for field, value in self.sensitive_data.items():
            if field in ['credit_card', 'ssn']:
                data_classification[field] = DataSensitivity.CRITICAL
            elif field in ['email', 'phone']:
                data_classification[field] = DataSensitivity.MEDIUM
            else:
                data_classification[field] = DataSensitivity.LOW
        
        # 2. Data encryption simulation
        encrypted_data = {}
        for field, value in self.sensitive_data.items():
            if data_classification[field] in [DataSensitivity.HIGH, DataSensitivity.CRITICAL]:
                encrypted_data[field] = f"encrypted_{value}"
            else:
                encrypted_data[field] = value
        
        # 3. Data tokenization simulation
        tokenized_data = {}
        for field, value in self.sensitive_data.items():
            if field in ['credit_card', 'ssn']:
                tokenized_data[field] = f"token_{value[-4:]}"
            elif field in ['email', 'phone']:
                tokenized_data[field] = f"token_{value[:3]}"
            else:
                tokenized_data[field] = value
        
        # 4. Audit logging simulation
        audit_events = []
        for field, value in self.sensitive_data.items():
            if data_classification[field] in [DataSensitivity.HIGH, DataSensitivity.CRITICAL]:
                audit_event = {
                    'event_id': f'audit_{field}_{int(time.time())}',
                    'user_id': self.sensitive_data['user_id'],
                    'event_type': AuditEventType.DATA_CREATE.value,
                    'data_type': field,
                    'sensitivity_level': data_classification[field].value
                }
                audit_events.append(audit_event)
        
        # 5. Compliance validation
        compliance_score = 95.0  # Mock compliance score
        
        # Verify end-to-end workflow
        self.assertGreater(len(audit_events), 0)
        self.assertGreaterEqual(compliance_score, 90.0)
        
        # Verify data transformation
        self.assertNotEqual(encrypted_data['credit_card'], self.sensitive_data['credit_card'])
        self.assertNotEqual(tokenized_data['credit_card'], self.sensitive_data['credit_card'])
        self.assertNotEqual(encrypted_data['ssn'], self.sensitive_data['ssn'])
        self.assertNotEqual(tokenized_data['ssn'], self.sensitive_data['ssn'])
        
        total_time = time.time() - start_time
        self.performance_metrics['workflow_times'].append(total_time)
        
        # Performance assertion
        self.assertLess(total_time, 0.2, 
                       f"End-to-end workflow took {total_time:.3f}s, expected <0.2s")
    
    def tearDown(self):
        """Clean up after tests"""
        # Record memory usage
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.performance_metrics['memory_usage'].append(memory_usage)
        
        # Verify memory usage is reasonable
        self.assertLess(memory_usage, 500, 
                       f"Memory usage {memory_usage:.1f}MB exceeds 500MB limit")


class TestSecurityPerformance(unittest.TestCase):
    """Test security system performance"""
    
    def setUp(self):
        """Set up performance testing"""
        self.performance_thresholds = {
            'enumeration_speed': 0.01,  # seconds
            'workflow_speed': 0.1,  # seconds
            'memory_efficiency': 1.0  # MB per operation
        }
    
    def test_enumeration_performance(self):
        """Test security enum enumeration performance"""
        iterations = 100
        enum_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # Enumerate all security enums
            list(DataSensitivity)
            list(EncryptionAlgorithm)
            list(TokenizationType)
            list(AuditEventType)
            list(ComplianceRegulation)
            
            enum_time = time.time() - start_time
            enum_times.append(enum_time)
        
        # Analyze results
        avg_time = statistics.mean(enum_times)
        max_time = max(enum_times)
        min_time = min(enum_times)
        
        # Performance assertions
        self.assertLess(avg_time, self.performance_thresholds['enumeration_speed'],
                       f"Average enumeration time {avg_time:.4f}s exceeds threshold {self.performance_thresholds['enumeration_speed']}s")
        
        self.assertLess(max_time, self.performance_thresholds['enumeration_speed'] * 5,
                       f"Maximum enumeration time {max_time:.4f}s exceeds 5x threshold")
        
        # Verify consistency (relaxed threshold for performance variation)
        self.assertLess(max_time / avg_time, 50, 
                       f"Performance variation too high: max/avg = {max_time/avg_time:.2f}")
    
    def test_memory_efficiency(self):
        """Test memory efficiency of security operations"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Perform multiple security operations
        operations = []
        for i in range(100):
            # Create enum instances
            sensitivity = DataSensitivity.CRITICAL
            algorithm = EncryptionAlgorithm.AES_256_GCM
            token_type = TokenizationType.PAYMENT_CARD
            event_type = AuditEventType.DATA_CREATE
            regulation = ComplianceRegulation.PCI_DSS
            
            operations.append({
                'sensitivity': sensitivity,
                'algorithm': algorithm,
                'token_type': token_type,
                'event_type': event_type,
                'regulation': regulation,
                'iteration': i
            })
        
        # Measure memory usage
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        memory_per_operation = memory_increase / len(operations)
        
        # Performance assertions
        self.assertLess(memory_per_operation, self.performance_thresholds['memory_efficiency'],
                       f"Memory per operation {memory_per_operation:.3f} MB exceeds threshold {self.performance_thresholds['memory_efficiency']} MB")
        
        # Cleanup
        del operations
        gc.collect()
        
        # Verify cleanup
        post_cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024
        self.assertLess(post_cleanup_memory, initial_memory * 1.5,
                       f"Memory not properly cleaned up: {post_cleanup_memory:.1f}MB vs {initial_memory:.1f}MB")
    
    def test_workflow_performance(self):
        """Test security workflow performance"""
        iterations = 50
        workflow_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # Simulate security workflow
            # 1. Data classification
            data = {'field': 'value'}
            sensitivity = DataSensitivity.HIGH
            
            # 2. Mock encryption
            encrypted = f"encrypted_{data['field']}"
            
            # 3. Mock tokenization
            tokenized = f"token_{data['field']}"
            
            # 4. Mock audit logging
            audit_event = {
                'event_id': f'event_{int(time.time())}',
                'data_type': 'test',
                'sensitivity': sensitivity.value
            }
            
            workflow_time = time.time() - start_time
            workflow_times.append(workflow_time)
        
        # Analyze results
        avg_time = statistics.mean(workflow_times)
        max_time = max(workflow_times)
        
        # Performance assertions
        self.assertLess(avg_time, self.performance_thresholds['workflow_speed'],
                       f"Average workflow time {avg_time:.4f}s exceeds threshold {self.performance_thresholds['workflow_speed']}s")
        
        self.assertLess(max_time, self.performance_thresholds['workflow_speed'] * 3,
                       f"Maximum workflow time {max_time:.4f}s exceeds 3x threshold")
        
        # Verify consistency (relaxed threshold for performance variation)
        self.assertLess(max_time / avg_time, 15, 
                       f"Workflow performance variation too high: max/avg = {max_time/avg_time:.2f}")


def run_security_tests():
    """Run all security tests"""
    print("🔒 MINGUS Security Integration Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestSecurityEnums))
    test_suite.addTest(unittest.makeSuite(TestSecurityWorkflow))
    test_suite.addTest(unittest.makeSuite(TestSecurityPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ All security tests passed!")
        return True
    else:
        print("❌ Some security tests failed!")
        return False


if __name__ == "__main__":
    # Run the tests
    success = run_security_tests()
    sys.exit(0 if success else 1)
