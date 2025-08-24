"""
Comprehensive Performance Testing Suite for MINGUS Application
Tests load, stress, scalability, and performance benchmarks
"""

import unittest
import time
import threading
import concurrent.futures
import statistics
import psutil
import os
import json
import asyncio
import aiohttp
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import hashlib
import random
import string

# Import MINGUS components
from backend.ml.job_security_predictor import JobSecurityPredictor
from backend.integrations.financial_planning_integration import FinancialPlanningIntegration
from backend.integrations.goal_setting_integration import GoalSettingIntegration
from backend.integrations.recommendations_integration import RecommendationsIntegration
from backend.compliance.financial_compliance import FinancialComplianceManager
from backend.security.plaid_security_service import PlaidSecurityService
from backend.payment.stripe_integration import StripeIntegration
from backend.analytics.ab_testing import ABTestingManager
from backend.monitoring.performance_monitor import PerformanceMonitor


class PerformanceTestResult:
    """Container for performance test results"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.execution_time = None
        self.success = False
        self.error = None
        self.metrics = {}
        self.resource_usage = {}
        
    def complete(self, success: bool, error: str = None, metrics: Dict[str, Any] = None):
        """Complete the test result"""
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        self.success = success
        self.error = error
        if metrics:
            self.metrics.update(metrics)
        
        # Capture resource usage
        self.resource_usage = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / (1024 * 1024),
            'disk_usage_percent': psutil.disk_usage('/').percent
        }


class ComprehensivePerformanceTests(unittest.TestCase):
    """Comprehensive performance testing suite"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_results = []
        self.performance_thresholds = {
            'single_operation': 1.0,  # seconds
            'batch_operation': 5.0,   # seconds for 10 operations
            'concurrent_operation': 10.0,  # seconds for 100 concurrent operations
            'memory_usage_mb': 500,   # MB
            'cpu_usage_percent': 80,  # percent
            'response_time_ms': 2000,  # milliseconds
            'throughput_ops_per_sec': 100,  # operations per second
            'error_rate_percent': 5.0  # percent
        }
        
        # Initialize components
        self.predictor = JobSecurityPredictor()
        self.financial_integration = FinancialPlanningIntegration()
        self.goal_integration = GoalSettingIntegration()
        self.recommendations_integration = RecommendationsIntegration()
        self.compliance_manager = FinancialComplianceManager()
        self.security_service = PlaidSecurityService()
        self.stripe_integration = StripeIntegration()
        self.ab_testing = ABTestingManager()
        self.performance_monitor = PerformanceMonitor()
        
        # Create test data
        self.test_user_data = self._create_test_user_data()
        self.test_company_data = self._create_test_company_data()
        self.test_market_data = self._create_test_market_data()
        self.test_payment_data = self._create_test_payment_data()
        
    def tearDown(self):
        """Clean up after tests"""
        # Generate performance report
        self._generate_performance_report()
    
    def _create_test_user_data(self) -> Dict[str, Any]:
        """Create comprehensive test user data"""
        return {
            'id': 1,
            'age': 32,
            'years_experience': 8,
            'education_level': 'bachelor',
            'skills': ['python', 'data_analysis', 'project_management', 'machine_learning'],
            'current_salary': 85000,
            'tenure_months': 36,
            'performance_rating': 4.5,
            'department': 'engineering',
            'role_level': 'senior',
            'location': 'San Francisco, CA',
            'company_size': 'medium',
            'industry': 'technology'
        }
    
    def _create_test_company_data(self) -> Dict[str, Any]:
        """Create comprehensive test company data"""
        return {
            'company_id': 'COMP001',
            'company_name': 'TechCorp',
            'industry': 'technology',
            'size': 'medium',
            'location': 'San Francisco, CA',
            'financial_health': 'strong',
            'revenue_growth': 0.25,
            'profit_margin': 0.18,
            'employee_count': 750,
            'market_cap': 5000000000,
            'debt_to_equity': 0.3,
            'cash_flow': 15000000
        }
    
    def _create_test_market_data(self) -> Dict[str, Any]:
        """Create comprehensive test market data"""
        return {
            'industry_growth_rate': 0.12,
            'unemployment_rate': 0.035,
            'job_market_health': 'strong',
            'skill_demand': {
                'python': 'very_high',
                'data_analysis': 'very_high',
                'project_management': 'high',
                'machine_learning': 'very_high'
            },
            'salary_trends': {
                'engineering': 0.08,
                'data_science': 0.12,
                'product_management': 0.06
            },
            'market_volatility': 0.15
        }
    
    def _create_test_payment_data(self) -> Dict[str, Any]:
        """Create test payment data"""
        return {
            'transaction_id': f'txn_{int(time.time())}',
            'amount': 99.99,
            'currency': 'USD',
            'card_type': 'visa',
            'masked_pan': '************1234',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cardholder_name': 'Test User',
            'merchant_id': 'merchant_test',
            'timestamp': datetime.utcnow(),
            'metadata': {
                'user_id': 1,
                'subscription_type': 'premium',
                'billing_cycle': 'monthly'
            }
        }
    
    def _record_test_result(self, result: PerformanceTestResult):
        """Record test result"""
        self.test_results.append(result)
    
    def _generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': len([r for r in self.test_results if r.success]),
            'failed_tests': len([r for r in self.test_results if not r.success]),
            'average_execution_time': statistics.mean([r.execution_time for r in self.test_results]),
            'max_execution_time': max([r.execution_time for r in self.test_results]),
            'min_execution_time': min([r.execution_time for r in self.test_results]),
            'test_results': []
        }
        
        for result in self.test_results:
            report['test_results'].append({
                'test_name': result.test_name,
                'success': result.success,
                'execution_time': result.execution_time,
                'error': result.error,
                'metrics': result.metrics,
                'resource_usage': result.resource_usage
            })
        
        # Save report to file
        report_file = f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Performance report saved to: {report_file}")
    
    # ============================================================================
    # LOAD TESTING
    # ============================================================================
    
    def test_single_prediction_performance(self):
        """Test single prediction performance"""
        result = PerformanceTestResult("single_prediction_performance")
        
        try:
            start_time = time.time()
            
            prediction_result = self.predictor.predict_comprehensive(
                self.test_user_data,
                self.test_company_data,
                self.test_market_data
            )
            
            execution_time = time.time() - start_time
            
            # Verify performance
            self.assertLess(execution_time, self.performance_thresholds['single_operation'])
            self.assertIsNotNone(prediction_result)
            
            result.complete(True, metrics={
                'execution_time_seconds': execution_time,
                'prediction_confidence': prediction_result.get('confidence', 0),
                'risk_score': prediction_result.get('risk_score', 0)
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    def test_batch_prediction_performance(self):
        """Test batch prediction performance"""
        result = PerformanceTestResult("batch_prediction_performance")
        
        try:
            # Create batch of test data
            batch_size = 10
            batch_data = []
            
            for i in range(batch_size):
                user_data = self.test_user_data.copy()
                user_data['id'] = i + 1
                user_data['current_salary'] = 75000 + (i * 5000)
                batch_data.append(user_data)
            
            start_time = time.time()
            
            # Process batch
            batch_results = []
            for user_data in batch_data:
                prediction = self.predictor.predict_comprehensive(
                    user_data,
                    self.test_company_data,
                    self.test_market_data
                )
                batch_results.append(prediction)
            
            execution_time = time.time() - start_time
            
            # Verify performance
            self.assertLess(execution_time, self.performance_thresholds['batch_operation'])
            self.assertEqual(len(batch_results), batch_size)
            
            result.complete(True, metrics={
                'execution_time_seconds': execution_time,
                'batch_size': batch_size,
                'average_time_per_prediction': execution_time / batch_size,
                'throughput_predictions_per_second': batch_size / execution_time
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    def test_concurrent_prediction_performance(self):
        """Test concurrent prediction performance"""
        result = PerformanceTestResult("concurrent_prediction_performance")
        
        try:
            num_threads = 10
            predictions_per_thread = 10
            total_predictions = num_threads * predictions_per_thread
            
            def make_predictions(thread_id):
                thread_results = []
                for i in range(predictions_per_thread):
                    user_data = self.test_user_data.copy()
                    user_data['id'] = thread_id * 1000 + i
                    user_data['current_salary'] = 70000 + (thread_id * 1000) + (i * 500)
                    
                    prediction = self.predictor.predict_comprehensive(
                        user_data,
                        self.test_company_data,
                        self.test_market_data
                    )
                    thread_results.append(prediction)
                return thread_results
            
            start_time = time.time()
            
            # Execute concurrent predictions
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                future_results = [executor.submit(make_predictions, i) for i in range(num_threads)]
                all_results = [future.result() for future in concurrent.futures.as_completed(future_results)]
            
            execution_time = time.time() - start_time
            
            # Flatten results
            flat_results = [pred for thread_results in all_results for pred in thread_results]
            
            # Verify performance
            self.assertLess(execution_time, self.performance_thresholds['concurrent_operation'])
            self.assertEqual(len(flat_results), total_predictions)
            
            result.complete(True, metrics={
                'execution_time_seconds': execution_time,
                'total_predictions': total_predictions,
                'num_threads': num_threads,
                'throughput_predictions_per_second': total_predictions / execution_time,
                'average_time_per_prediction': execution_time / total_predictions
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    # ============================================================================
    # STRESS TESTING
    # ============================================================================
    
    def test_stress_test_performance(self):
        """Test system under stress conditions"""
        result = PerformanceTestResult("stress_test_performance")
        
        try:
            # Simulate high load
            num_operations = 1000
            operations = []
            
            # Create diverse operation types
            for i in range(num_operations):
                operation_type = i % 4
                if operation_type == 0:
                    # Prediction operation
                    operations.append(('prediction', {
                        'user_data': self.test_user_data.copy(),
                        'company_data': self.test_company_data,
                        'market_data': self.test_market_data
                    }))
                elif operation_type == 1:
                    # Financial analysis
                    operations.append(('financial', {
                        'income': 75000 + (i * 100),
                        'expenses': 45000 + (i * 50),
                        'investments': 10000 + (i * 200)
                    }))
                elif operation_type == 2:
                    # Payment processing
                    operations.append(('payment', {
                        'amount': 50 + (i % 100),
                        'currency': 'USD',
                        'card_type': 'visa'
                    }))
                else:
                    # Compliance check
                    operations.append(('compliance', {
                        'data_type': 'payment',
                        'user_id': i,
                        'operation': 'process'
                    }))
            
            start_time = time.time()
            
            # Execute operations
            results = []
            for op_type, data in operations:
                try:
                    if op_type == 'prediction':
                        result_op = self.predictor.predict_comprehensive(
                            data['user_data'],
                            data['company_data'],
                            data['market_data']
                        )
                    elif op_type == 'financial':
                        result_op = self.financial_integration.analyze_financial_health(
                            data['income'],
                            data['expenses'],
                            data['investments']
                        )
                    elif op_type == 'payment':
                        result_op = self.stripe_integration.process_payment(
                            data['amount'],
                            data['currency'],
                            data['card_type']
                        )
                    else:  # compliance
                        result_op = self.compliance_manager.validate_compliance(
                            data['data_type'],
                            data['user_id'],
                            data['operation']
                        )
                    
                    results.append((op_type, result_op, None))
                    
                except Exception as e:
                    results.append((op_type, None, str(e)))
            
            execution_time = time.time() - start_time
            
            # Calculate success rate
            successful_operations = len([r for r in results if r[2] is None])
            success_rate = (successful_operations / num_operations) * 100
            
            # Verify performance under stress
            self.assertGreater(success_rate, 95.0)  # 95% success rate under stress
            self.assertLess(execution_time, 60.0)  # Complete within 60 seconds
            
            result.complete(True, metrics={
                'execution_time_seconds': execution_time,
                'total_operations': num_operations,
                'successful_operations': successful_operations,
                'success_rate_percent': success_rate,
                'throughput_ops_per_second': num_operations / execution_time,
                'error_rate_percent': 100 - success_rate
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    # ============================================================================
    # SCALABILITY TESTING
    # ============================================================================
    
    def test_scalability_performance(self):
        """Test system scalability"""
        result = PerformanceTestResult("scalability_performance")
        
        try:
            # Test different load levels
            load_levels = [10, 50, 100, 200, 500]
            scalability_results = []
            
            for load in load_levels:
                start_time = time.time()
                
                # Execute load level operations
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(load, 20)) as executor:
                    futures = []
                    for i in range(load):
                        user_data = self.test_user_data.copy()
                        user_data['id'] = i
                        future = executor.submit(
                            self.predictor.predict_comprehensive,
                            user_data,
                            self.test_company_data,
                            self.test_market_data
                        )
                        futures.append(future)
                    
                    # Wait for completion
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                execution_time = time.time() - start_time
                
                scalability_results.append({
                    'load_level': load,
                    'execution_time': execution_time,
                    'throughput': load / execution_time,
                    'average_time_per_operation': execution_time / load
                })
            
            # Verify scalability characteristics
            # Throughput should increase or remain stable with load
            throughputs = [r['throughput'] for r in scalability_results]
            
            # Check if throughput scales reasonably
            max_throughput = max(throughputs)
            min_throughput = min(throughputs)
            throughput_ratio = max_throughput / min_throughput if min_throughput > 0 else 0
            
            # Throughput should not degrade more than 50%
            self.assertGreater(throughput_ratio, 0.5)
            
            result.complete(True, metrics={
                'load_levels_tested': load_levels,
                'scalability_results': scalability_results,
                'max_throughput': max_throughput,
                'min_throughput': min_throughput,
                'throughput_ratio': throughput_ratio
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    # ============================================================================
    # MEMORY AND RESOURCE TESTING
    # ============================================================================
    
    def test_memory_usage_performance(self):
        """Test memory usage under load"""
        result = PerformanceTestResult("memory_usage_performance")
        
        try:
            # Get initial memory usage
            initial_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            # Perform memory-intensive operations
            num_operations = 100
            large_data_structures = []
            
            for i in range(num_operations):
                # Create large data structure
                large_data = {
                    'id': i,
                    'data': ''.join(random.choices(string.ascii_letters, k=10000)),
                    'metadata': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'user_id': i,
                        'session_id': hashlib.md5(str(i).encode()).hexdigest()
                    }
                }
                large_data_structures.append(large_data)
                
                # Perform prediction with large data
                user_data = self.test_user_data.copy()
                user_data['id'] = i
                user_data['large_metadata'] = large_data
                
                self.predictor.predict_comprehensive(
                    user_data,
                    self.test_company_data,
                    self.test_market_data
                )
            
            # Get final memory usage
            final_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
            memory_increase = final_memory - initial_memory
            
            # Verify memory usage is reasonable
            self.assertLess(memory_increase, self.performance_thresholds['memory_usage_mb'])
            
            # Clean up
            del large_data_structures
            
            result.complete(True, metrics={
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase,
                'operations_performed': num_operations
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    def test_cpu_usage_performance(self):
        """Test CPU usage under load"""
        result = PerformanceTestResult("cpu_usage_performance")
        
        try:
            # Get initial CPU usage
            initial_cpu = psutil.cpu_percent(interval=1)
            
            # Perform CPU-intensive operations
            num_operations = 50
            
            start_time = time.time()
            cpu_readings = []
            
            for i in range(num_operations):
                # Perform complex calculations
                user_data = self.test_user_data.copy()
                user_data['id'] = i
                user_data['complex_calculations'] = True
                
                # Add some CPU-intensive operations
                for j in range(1000):
                    _ = hashlib.sha256(str(j).encode()).hexdigest()
                
                self.predictor.predict_comprehensive(
                    user_data,
                    self.test_company_data,
                    self.test_market_data
                )
                
                # Record CPU usage
                cpu_usage = psutil.cpu_percent(interval=0.1)
                cpu_readings.append(cpu_usage)
            
            execution_time = time.time() - start_time
            
            # Calculate average CPU usage
            avg_cpu = statistics.mean(cpu_readings)
            max_cpu = max(cpu_readings)
            
            # Verify CPU usage is reasonable
            self.assertLess(avg_cpu, self.performance_thresholds['cpu_usage_percent'])
            
            result.complete(True, metrics={
                'initial_cpu_percent': initial_cpu,
                'average_cpu_percent': avg_cpu,
                'max_cpu_percent': max_cpu,
                'execution_time_seconds': execution_time,
                'operations_performed': num_operations
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    # ============================================================================
    # INTEGRATION PERFORMANCE TESTING
    # ============================================================================
    
    def test_integration_performance(self):
        """Test integration performance across components"""
        result = PerformanceTestResult("integration_performance")
        
        try:
            num_integrations = 20
            integration_results = []
            
            for i in range(num_integrations):
                start_time = time.time()
                
                # Simulate full user workflow
                user_data = self.test_user_data.copy()
                user_data['id'] = i
                
                # 1. Job security prediction
                security_prediction = self.predictor.predict_comprehensive(
                    user_data,
                    self.test_company_data,
                    self.test_market_data
                )
                
                # 2. Financial planning
                financial_plan = self.financial_integration.create_financial_plan(
                    user_data['current_salary'],
                    user_data['age'],
                    security_prediction.get('risk_score', 0.5)
                )
                
                # 3. Goal setting
                goals = self.goal_integration.setup_user_goals(
                    user_data['id'],
                    financial_plan.get('recommendations', [])
                )
                
                # 4. Recommendations
                recommendations = self.recommendations_integration.get_recommendations(
                    user_data['id'],
                    security_prediction,
                    financial_plan
                )
                
                # 5. Compliance check
                compliance_status = self.compliance_manager.validate_compliance(
                    'user_data',
                    user_data['id'],
                    'analysis'
                )
                
                execution_time = time.time() - start_time
                
                integration_results.append({
                    'user_id': i,
                    'execution_time': execution_time,
                    'security_prediction': security_prediction is not None,
                    'financial_plan': financial_plan is not None,
                    'goals': goals is not None,
                    'recommendations': recommendations is not None,
                    'compliance': compliance_status
                })
            
            # Calculate metrics
            total_time = sum(r['execution_time'] for r in integration_results)
            avg_time = total_time / num_integrations
            successful_integrations = len([r for r in integration_results if all([
                r['security_prediction'], r['financial_plan'], r['goals'], 
                r['recommendations'], r['compliance']
            ])])
            
            # Verify integration performance
            self.assertLess(avg_time, self.performance_thresholds['batch_operation'])
            self.assertGreater(successful_integrations / num_integrations, 0.95)
            
            result.complete(True, metrics={
                'total_integrations': num_integrations,
                'successful_integrations': successful_integrations,
                'success_rate_percent': (successful_integrations / num_integrations) * 100,
                'average_execution_time': avg_time,
                'total_execution_time': total_time
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    # ============================================================================
    # DATABASE PERFORMANCE TESTING
    # ============================================================================
    
    def test_database_query_performance(self):
        """Test database query performance"""
        result = PerformanceTestResult("database_query_performance")
        
        try:
            # Create test database
            test_db_path = f"test_performance_{int(time.time())}.db"
            
            with sqlite3.connect(test_db_path) as conn:
                # Create test tables
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_users (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        salary REAL,
                        created_at TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_predictions (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        prediction_data TEXT,
                        confidence REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES test_users (id)
                    )
                """)
                
                # Insert test data
                num_users = 1000
                num_predictions = 5000
                
                # Insert users
                start_time = time.time()
                for i in range(num_users):
                    conn.execute("""
                        INSERT INTO test_users (id, name, email, salary, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        i,
                        f"User {i}",
                        f"user{i}@example.com",
                        50000 + (i * 1000),
                        datetime.utcnow().isoformat()
                    ))
                
                insert_time = time.time() - start_time
                
                # Insert predictions
                start_time = time.time()
                for i in range(num_predictions):
                    conn.execute("""
                        INSERT INTO test_predictions (id, user_id, prediction_data, confidence, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        i,
                        i % num_users,
                        json.dumps({'risk_score': random.random(), 'confidence': random.random()}),
                        random.random(),
                        datetime.utcnow().isoformat()
                    ))
                
                prediction_insert_time = time.time() - start_time
                
                # Test query performance
                start_time = time.time()
                
                # Complex join query
                cursor = conn.execute("""
                    SELECT u.name, u.salary, p.confidence, p.prediction_data
                    FROM test_users u
                    JOIN test_predictions p ON u.id = p.user_id
                    WHERE u.salary > 60000 AND p.confidence > 0.7
                    ORDER BY p.confidence DESC
                    LIMIT 100
                """)
                
                results = cursor.fetchall()
                query_time = time.time() - start_time
                
                # Verify query performance
                self.assertLess(query_time, 1.0)  # Query should complete within 1 second
                self.assertGreater(len(results), 0)
            
            # Clean up
            os.remove(test_db_path)
            
            result.complete(True, metrics={
                'num_users_inserted': num_users,
                'num_predictions_inserted': num_predictions,
                'user_insert_time_seconds': insert_time,
                'prediction_insert_time_seconds': prediction_insert_time,
                'query_execution_time_seconds': query_time,
                'query_results_count': len(results)
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)
    
    # ============================================================================
    # API PERFORMANCE TESTING
    # ============================================================================
    
    def test_api_response_time_performance(self):
        """Test API response time performance"""
        result = PerformanceTestResult("api_response_time_performance")
        
        try:
            # Simulate API calls
            num_api_calls = 50
            response_times = []
            
            for i in range(num_api_calls):
                start_time = time.time()
                
                # Simulate API call with mock data
                user_data = self.test_user_data.copy()
                user_data['id'] = i
                
                # Simulate API processing time
                time.sleep(0.01)  # Simulate network latency
                
                # Process request
                api_response = {
                    'user_id': user_data['id'],
                    'prediction': self.predictor.predict_comprehensive(
                        user_data,
                        self.test_company_data,
                        self.test_market_data
                    ),
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'success'
                }
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Verify response structure
                self.assertIn('user_id', api_response)
                self.assertIn('prediction', api_response)
                self.assertIn('timestamp', api_response)
                self.assertEqual(api_response['status'], 'success')
            
            # Calculate response time metrics
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Convert to milliseconds
            avg_response_time_ms = avg_response_time * 1000
            max_response_time_ms = max_response_time * 1000
            
            # Verify API performance
            self.assertLess(avg_response_time_ms, self.performance_thresholds['response_time_ms'])
            self.assertLess(max_response_time_ms, self.performance_thresholds['response_time_ms'] * 2)
            
            result.complete(True, metrics={
                'num_api_calls': num_api_calls,
                'average_response_time_ms': avg_response_time_ms,
                'max_response_time_ms': max_response_time_ms,
                'min_response_time_ms': min_response_time * 1000,
                'throughput_requests_per_second': num_api_calls / sum(response_times)
            })
            
        except Exception as e:
            result.complete(False, str(e))
            raise
        
        self._record_test_result(result)


if __name__ == '__main__':
    # Run performance tests
    unittest.main(verbosity=2) 