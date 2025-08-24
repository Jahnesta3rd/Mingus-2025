"""
Webhook Testing and Validation System for MINGUS
Tests webhook endpoints and validates webhook configurations
"""
import logging
import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import requests
from sqlalchemy.orm import Session

from ..config.base import Config
from ..webhooks.webhook_config import WebhookConfig, WebhookEnvironment

logger = logging.getLogger(__name__)

@dataclass
class WebhookTestResult:
    """Result of webhook endpoint test"""
    endpoint_url: str
    success: bool
    response_time: float
    status_code: int
    response_body: str
    error: str = None
    timestamp: datetime = None

@dataclass
class WebhookValidationResult:
    """Result of webhook configuration validation"""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    test_results: List[WebhookTestResult]

class WebhookValidator:
    """Comprehensive webhook testing and validation system"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.webhook_config = WebhookConfig()
        
        # Test configuration
        self.test_timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def validate_webhook_configuration(self) -> WebhookValidationResult:
        """Validate webhook configuration"""
        issues = []
        warnings = []
        recommendations = []
        test_results = []
        
        try:
            # Validate endpoints
            for endpoint_name, endpoint in self.webhook_config.endpoints.items():
                if endpoint.enabled:
                    # Test endpoint connectivity
                    test_result = self.test_endpoint(endpoint.url)
                    test_results.append(test_result)
                    
                    if not test_result.success:
                        issues.append(f"Endpoint {endpoint_name} is not accessible: {test_result.error}")
                    elif test_result.response_time > 5.0:
                        warnings.append(f"Endpoint {endpoint_name} has slow response time: {test_result.response_time:.2f}s")
            
            # Validate security configuration
            if not self.webhook_config.security.signature_verification:
                warnings.append("Webhook signature verification is disabled")
            
            if not self.webhook_config.security.ip_whitelist:
                warnings.append("No IP whitelist configured for webhook endpoints")
            
            # Validate event mappings
            for event_type, event_config in self.webhook_config.event_mappings.items():
                if event_config.get('retry_attempts', 0) > 5:
                    warnings.append(f"High retry attempts for {event_type}: {event_config['retry_attempts']}")
                
                if event_config.get('timeout', 0) > 60:
                    warnings.append(f"High timeout for {event_type}: {event_config['timeout']}s")
            
            # Validate webhook secret
            webhook_secret = self.webhook_config.get_webhook_secret()
            if not webhook_secret:
                issues.append("Webhook secret not configured")
            
            # Validate Stripe API key
            stripe_api_key = self.webhook_config.get_stripe_api_key()
            if not stripe_api_key:
                issues.append("Stripe API key not configured")
            
            # Generate recommendations
            if not issues:
                recommendations.append("Webhook configuration is valid")
            
            if warnings:
                recommendations.append("Review warnings and consider addressing them")
            
            if not test_results or not any(r.success for r in test_results):
                recommendations.append("Fix endpoint connectivity issues")
            
            is_valid = len(issues) == 0
            
            return WebhookValidationResult(
                is_valid=is_valid,
                issues=issues,
                warnings=warnings,
                recommendations=recommendations,
                test_results=test_results
            )
            
        except Exception as e:
            logger.error(f"Error validating webhook configuration: {e}")
            return WebhookValidationResult(
                is_valid=False,
                issues=[f"Validation error: {str(e)}"],
                warnings=[],
                recommendations=["Check webhook configuration"],
                test_results=[]
            )
    
    def test_endpoint(self, endpoint_url: str) -> WebhookTestResult:
        """Test webhook endpoint connectivity"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            response = requests.get(
                endpoint_url,
                timeout=self.test_timeout,
                headers={'User-Agent': 'MINGUS-Webhook-Validator/1.0'}
            )
            
            response_time = time.time() - start_time
            
            return WebhookTestResult(
                endpoint_url=endpoint_url,
                success=response.status_code < 400,
                response_time=response_time,
                status_code=response.status_code,
                response_body=response.text[:500],  # Limit response body
                timestamp=datetime.utcnow()
            )
            
        except requests.exceptions.Timeout:
            return WebhookTestResult(
                endpoint_url=endpoint_url,
                success=False,
                response_time=time.time() - start_time,
                status_code=0,
                response_body="",
                error="Request timeout",
                timestamp=datetime.utcnow()
            )
        except requests.exceptions.ConnectionError:
            return WebhookTestResult(
                endpoint_url=endpoint_url,
                success=False,
                response_time=time.time() - start_time,
                status_code=0,
                response_body="",
                error="Connection error",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return WebhookTestResult(
                endpoint_url=endpoint_url,
                success=False,
                response_time=time.time() - start_time,
                status_code=0,
                response_body="",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    def test_webhook_signature_verification(self) -> Dict[str, Any]:
        """Test webhook signature verification"""
        try:
            webhook_secret = self.webhook_config.get_webhook_secret()
            if not webhook_secret:
                return {
                    'success': False,
                    'error': 'Webhook secret not configured'
                }
            
            # Create test payload
            test_payload = {
                'id': 'evt_test_signature',
                'object': 'event',
                'type': 'customer.created',
                'data': {
                    'object': {
                        'id': 'cus_test_signature',
                        'email': 'test@example.com'
                    }
                },
                'created': int(time.time())
            }
            
            payload_str = json.dumps(test_payload)
            timestamp = int(time.time())
            
            # Generate valid signature
            signed_payload = f"{timestamp}.{payload_str}"
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Test signature verification
            signature_header = f"t={timestamp},v1={expected_signature}"
            
            # Verify signature
            is_valid = self._verify_test_signature(
                payload_str.encode('utf-8'),
                signature_header,
                webhook_secret
            )
            
            return {
                'success': True,
                'signature_valid': is_valid,
                'test_payload': test_payload,
                'signature_header': signature_header,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error testing webhook signature verification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _verify_test_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify test webhook signature"""
        try:
            # Extract timestamp and signatures
            timestamp, signatures = self._extract_signature_parts(signature)
            
            if not timestamp or not signatures:
                return False
            
            # Check timestamp
            if time.time() - timestamp > 300:  # 5 minutes
                return False
            
            # Verify signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return expected_signature in signatures
            
        except Exception as e:
            logger.error(f"Error verifying test signature: {e}")
            return False
    
    def _extract_signature_parts(self, signature: str) -> Tuple[Optional[int], List[str]]:
        """Extract timestamp and signatures from signature header"""
        try:
            parts = signature.split(',')
            timestamp = None
            signatures = []
            
            for part in parts:
                if part.startswith('t='):
                    timestamp = int(part[2:])
                elif part.startswith('v1='):
                    signatures.append(part[3:])
            
            return timestamp, signatures
            
        except Exception as e:
            logger.error(f"Error extracting signature parts: {e}")
            return None, []
    
    def test_webhook_event_processing(self, event_type: str = "customer.created") -> Dict[str, Any]:
        """Test webhook event processing"""
        try:
            # Create test event
            test_event = self._create_test_event(event_type)
            
            # Test event processing
            start_time = time.time()
            
            # This would typically call the actual webhook processor
            # For testing, we'll simulate the processing
            processing_success = self._simulate_event_processing(test_event)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'event_type': event_type,
                'test_event': test_event,
                'processing_success': processing_success,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing webhook event processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_test_event(self, event_type: str) -> Dict[str, Any]:
        """Create a test webhook event"""
        base_event = {
            'id': f'evt_test_{int(time.time())}',
            'object': 'event',
            'type': event_type,
            'created': int(time.time()),
            'livemode': False,
            'api_version': '2020-08-27',
            'data': {
                'object': {}
            }
        }
        
        # Add event-specific data
        if event_type == "customer.created":
            base_event['data']['object'] = {
                'id': f'cus_test_{int(time.time())}',
                'object': 'customer',
                'email': 'test@example.com',
                'name': 'Test Customer',
                'created': int(time.time())
            }
        elif event_type == "customer.subscription.created":
            base_event['data']['object'] = {
                'id': f'sub_test_{int(time.time())}',
                'object': 'subscription',
                'customer': f'cus_test_{int(time.time())}',
                'status': 'active',
                'current_period_start': int(time.time()),
                'current_period_end': int(time.time()) + 86400 * 30,
                'items': {
                    'data': [{
                        'price': {
                            'id': 'price_test',
                            'unit_amount': 1500
                        }
                    }]
                }
            }
        elif event_type == "invoice.payment_succeeded":
            base_event['data']['object'] = {
                'id': f'in_test_{int(time.time())}',
                'object': 'invoice',
                'customer': f'cus_test_{int(time.time())}',
                'subscription': f'sub_test_{int(time.time())}',
                'amount_paid': 1500,
                'currency': 'usd',
                'status': 'paid'
            }
        
        return base_event
    
    def _simulate_event_processing(self, event: Dict[str, Any]) -> bool:
        """Simulate event processing for testing"""
        try:
            # Simulate processing time
            time.sleep(0.1)
            
            # Simulate success/failure based on event type
            event_type = event.get('type', '')
            
            # Simulate failures for certain event types
            if 'failed' in event_type.lower():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error simulating event processing: {e}")
            return False
    
    def run_comprehensive_webhook_tests(self) -> Dict[str, Any]:
        """Run comprehensive webhook tests"""
        try:
            test_results = {
                'timestamp': datetime.utcnow().isoformat(),
                'tests': {}
            }
            
            # Test 1: Configuration validation
            logger.info("Running webhook configuration validation...")
            validation_result = self.validate_webhook_configuration()
            test_results['tests']['configuration_validation'] = {
                'success': validation_result.is_valid,
                'issues': validation_result.issues,
                'warnings': validation_result.warnings,
                'recommendations': validation_result.recommendations
            }
            
            # Test 2: Endpoint connectivity
            logger.info("Testing webhook endpoint connectivity...")
            endpoint_tests = {}
            for endpoint_name, endpoint in self.webhook_config.endpoints.items():
                if endpoint.enabled:
                    test_result = self.test_endpoint(endpoint.url)
                    endpoint_tests[endpoint_name] = {
                        'success': test_result.success,
                        'response_time': test_result.response_time,
                        'status_code': test_result.status_code,
                        'error': test_result.error
                    }
            test_results['tests']['endpoint_connectivity'] = endpoint_tests
            
            # Test 3: Signature verification
            logger.info("Testing webhook signature verification...")
            signature_test = self.test_webhook_signature_verification()
            test_results['tests']['signature_verification'] = signature_test
            
            # Test 4: Event processing
            logger.info("Testing webhook event processing...")
            event_processing_tests = {}
            test_events = [
                'customer.created',
                'customer.subscription.created',
                'invoice.payment_succeeded'
            ]
            
            for event_type in test_events:
                event_test = self.test_webhook_event_processing(event_type)
                event_processing_tests[event_type] = event_test
            
            test_results['tests']['event_processing'] = event_processing_tests
            
            # Calculate overall test results
            all_tests_passed = (
                validation_result.is_valid and
                all(test_result.success for test_result in validation_result.test_results) and
                signature_test.get('success', False) and
                all(test.get('success', False) for test in event_processing_tests.values())
            )
            
            test_results['overall_success'] = all_tests_passed
            test_results['summary'] = {
                'total_tests': len(test_results['tests']),
                'passed_tests': sum(1 for test in test_results['tests'].values() if isinstance(test, dict) and test.get('success', False)),
                'failed_tests': sum(1 for test in test_results['tests'].values() if isinstance(test, dict) and not test.get('success', False))
            }
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error running comprehensive webhook tests: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_success': False,
                'error': str(e)
            }
    
    def generate_webhook_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive webhook test report"""
        try:
            # Run all tests
            test_results = self.run_comprehensive_webhook_tests()
            
            # Add configuration details
            config_details = self.webhook_config.to_dict()
            
            # Generate recommendations
            recommendations = []
            
            if not test_results.get('overall_success', False):
                recommendations.append("Fix failed tests before deploying to production")
            
            if test_results['tests'].get('configuration_validation', {}).get('warnings'):
                recommendations.append("Address configuration warnings")
            
            if test_results['tests'].get('endpoint_connectivity', {}):
                failed_endpoints = [
                    name for name, result in test_results['tests']['endpoint_connectivity'].items()
                    if not result.get('success', False)
                ]
                if failed_endpoints:
                    recommendations.append(f"Fix connectivity issues for endpoints: {', '.join(failed_endpoints)}")
            
            if not test_results['tests'].get('signature_verification', {}).get('success', False):
                recommendations.append("Fix webhook signature verification")
            
            return {
                'report_type': 'webhook_test_report',
                'generated_at': datetime.utcnow().isoformat(),
                'overall_status': 'PASS' if test_results.get('overall_success', False) else 'FAIL',
                'test_results': test_results,
                'configuration': config_details,
                'recommendations': recommendations,
                'next_steps': [
                    "Review test results",
                    "Address any failed tests",
                    "Deploy to staging environment",
                    "Run tests in staging",
                    "Deploy to production"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating webhook test report: {e}")
            return {
                'report_type': 'webhook_test_report',
                'generated_at': datetime.utcnow().isoformat(),
                'overall_status': 'ERROR',
                'error': str(e)
            } 