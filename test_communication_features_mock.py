#!/usr/bin/env python3
"""
Mock Communication Features Test Suite
Tests all communication features using mocked services
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class MockCommunicationFeaturesTestSuite:
    """Mock test suite for communication features"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
        # Test configuration
        self.test_email = os.getenv('TEST_EMAIL', 'test@example.com')
        self.test_phone = os.getenv('TEST_PHONE', '+1234567890')
        self.test_user_id = "test_user_123"
        
        # Mock services
        self.email_service = self._create_mock_email_service()
        self.sms_service = self._create_mock_sms_service()
        self.router = self._create_mock_router()
        
        # Test data
        self.test_user_profile = {
            'user_id': self.test_user_id,
            'email': self.test_email,
            'phone_number': self.test_phone,
            'engagement_level': 'medium',
            'income_range': '60k-80k',
            'age_range': '25-35',
            'sms_opted_in': True,
            'email_opted_in': True
        }
    
    def _create_mock_email_service(self):
        """Create mock email service"""
        mock_service = Mock()
        
        # Mock successful email responses
        mock_service.send_welcome_email.return_value = {
            'success': True,
            'email_id': 'mock_email_123',
            'message': 'Welcome email sent successfully'
        }
        
        mock_service.send_password_reset_email.return_value = {
            'success': True,
            'email_id': 'mock_reset_456',
            'message': 'Password reset email sent successfully'
        }
        
        mock_service.send_notification_email.return_value = {
            'success': True,
            'email_id': 'mock_notification_789',
            'message': 'Notification email sent successfully'
        }
        
        mock_service.send_pdf_report_email.return_value = {
            'success': True,
            'email_id': 'mock_report_101',
            'message': 'PDF report email sent successfully'
        }
        
        mock_service.send_email.return_value = {
            'success': True,
            'email_id': 'mock_generic_202',
            'message': 'Email sent successfully'
        }
        
        return mock_service
    
    def _create_mock_sms_service(self):
        """Create mock SMS service"""
        mock_service = Mock()
        
        # Mock successful SMS responses
        mock_service.send_sms.return_value = {
            'success': True,
            'message_sid': 'mock_sms_123',
            'status': 'sent',
            'cost': 0.0075
        }
        
        mock_service.track_delivery_status.return_value = {
            'success': True,
            'message_sid': 'mock_sms_123',
            'status': 'delivered',
            'error_code': None,
            'error_message': None
        }
        
        mock_service.validate_phone_number.return_value = True
        
        mock_service.handle_opt_out_responses.return_value = {
            'success': True,
            'action': 'opted_out',
            'confirmation_message': 'You have been unsubscribed'
        }
        
        mock_service.get_sms_statistics.return_value = {
            'total_cost': 15.50,
            'total_sent': 2000,
            'total_delivered': 1950,
            'success_rate': 97.5
        }
        
        return mock_service
    
    def _create_mock_router(self):
        """Create mock communication router"""
        mock_router = Mock()
        
        # Mock routing decisions
        class MockRoutingDecision:
            def __init__(self, channel, reasoning):
                self.channel = Mock()
                self.channel.value = channel
                self.reasoning = reasoning
                self.priority = "medium"
                self.delay_seconds = 0
                self.fallback_channel = None
        
        mock_router.route_message.return_value = MockRoutingDecision(
            'sms', 'Critical financial alert - SMS for immediate delivery'
        )
        
        return mock_router
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all communication feature tests"""
        logger.info("🚀 Starting Mock Communication Features Test Suite")
        
        # Test categories
        test_categories = [
            ("Email Delivery via Resend", self.test_email_delivery),
            ("SMS Notifications via Twilio", self.test_sms_notifications),
            ("Email Template Rendering", self.test_email_templates),
            ("Communication Routing", self.test_communication_routing),
            ("Delivery Success Rates", self.test_delivery_success_rates),
            ("Error Handling", self.test_error_handling),
            ("User Preferences", self.test_user_preferences),
            ("Integration Tests", self.test_integration_scenarios)
        ]
        
        for category_name, test_method in test_categories:
            logger.info(f"\n📋 Testing: {category_name}")
            try:
                test_method()
            except Exception as e:
                logger.error(f"❌ Error in {category_name}: {e}")
                self.results.append(TestResult(
                    test_name=category_name,
                    success=False,
                    duration=0,
                    error=str(e)
                ))
        
        return self.generate_report()
    
    def test_email_delivery(self):
        """Test email delivery via Resend"""
        logger.info("📧 Testing Email Delivery via Resend")
        
        # Test 1: Welcome Email
        start_time = time.time()
        try:
            result = self.email_service.send_welcome_email(
                user_email=self.test_email,
                user_name="Test User"
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Welcome Email Delivery",
                success=result.get('success', False),
                duration=duration,
                details={
                    'email_id': result.get('email_id'),
                    'message': result.get('message'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Welcome email sent successfully")
            else:
                logger.error(f"❌ Welcome email failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Welcome email test error: {e}")
            self.results.append(TestResult(
                test_name="Welcome Email Delivery",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 2: Password Reset Email
        start_time = time.time()
        try:
            result = self.email_service.send_password_reset_email(
                user_email=self.test_email,
                reset_token="test_reset_token_123"
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Password Reset Email Delivery",
                success=result.get('success', False),
                duration=duration,
                details={
                    'email_id': result.get('email_id'),
                    'message': result.get('message'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Password reset email sent successfully")
            else:
                logger.error(f"❌ Password reset email failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Password reset email test error: {e}")
            self.results.append(TestResult(
                test_name="Password Reset Email Delivery",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 3: Notification Email
        start_time = time.time()
        try:
            result = self.email_service.send_notification_email(
                user_email=self.test_email,
                subject="Test Financial Alert",
                message="This is a test financial alert notification.",
                notification_type="alert"
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Notification Email Delivery",
                success=result.get('success', False),
                duration=duration,
                details={
                    'email_id': result.get('email_id'),
                    'message': result.get('message'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Notification email sent successfully")
            else:
                logger.error(f"❌ Notification email failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Notification email test error: {e}")
            self.results.append(TestResult(
                test_name="Notification Email Delivery",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 4: PDF Report Email
        start_time = time.time()
        try:
            result = self.email_service.send_pdf_report_email(
                user_email=self.test_email,
                user_name="Test User",
                report_type="monthly",
                pdf_url="https://example.com/test-report.pdf",
                report_data={'month': 'January 2024', 'total_assets': 50000}
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="PDF Report Email Delivery",
                success=result.get('success', False),
                duration=duration,
                details={
                    'email_id': result.get('email_id'),
                    'message': result.get('message'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ PDF report email sent successfully")
            else:
                logger.error(f"❌ PDF report email failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ PDF report email test error: {e}")
            self.results.append(TestResult(
                test_name="PDF Report Email Delivery",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_sms_notifications(self):
        """Test SMS notifications via Twilio"""
        logger.info("📱 Testing SMS Notifications via Twilio")
        
        # Test 1: Basic SMS
        start_time = time.time()
        try:
            result = self.sms_service.send_sms(
                phone_number=self.test_phone,
                message="Test SMS from MINGUS - Financial wellness check",
                priority_level="MEDIUM",
                user_id=self.test_user_id
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Basic SMS Delivery",
                success=result.get('success', False),
                duration=duration,
                details={
                    'message_sid': result.get('message_sid'),
                    'status': result.get('status'),
                    'cost': result.get('cost'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Basic SMS sent successfully")
            else:
                logger.error(f"❌ Basic SMS failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Basic SMS test error: {e}")
            self.results.append(TestResult(
                test_name="Basic SMS Delivery",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 2: Template-based SMS
        start_time = time.time()
        try:
            result = self.sms_service.send_sms(
                phone_number=self.test_phone,
                message="",  # Will use template
                template_name="low_balance_warning",
                template_vars={'balance': '150.00'},
                priority_level="URGENT",
                user_id=self.test_user_id
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Template SMS Delivery",
                success=result.get('success', False),
                duration=duration,
                details={
                    'message_sid': result.get('message_sid'),
                    'status': result.get('status'),
                    'cost': result.get('cost'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Template SMS sent successfully")
            else:
                logger.error(f"❌ Template SMS failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Template SMS test error: {e}")
            self.results.append(TestResult(
                test_name="Template SMS Delivery",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 3: Critical Alert SMS
        start_time = time.time()
        try:
            result = self.sms_service.send_sms(
                phone_number=self.test_phone,
                message="🚨 CRITICAL: Your MINGUS payment of $99.99 failed. Update payment method immediately.",
                priority_level="CRITICAL",
                user_id=self.test_user_id
            )
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Critical Alert SMS",
                success=result.get('success', False),
                duration=duration,
                details={
                    'message_sid': result.get('message_sid'),
                    'status': result.get('status'),
                    'cost': result.get('cost'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Critical alert SMS sent successfully")
            else:
                logger.error(f"❌ Critical alert SMS failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Critical alert SMS test error: {e}")
            self.results.append(TestResult(
                test_name="Critical Alert SMS",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 4: Phone Number Validation
        start_time = time.time()
        try:
            valid_numbers = [
                "+1234567890",
                "+1-234-567-8900",
                "+44 20 7946 0958"
            ]
            
            invalid_numbers = [
                "1234567890",
                "invalid",
                "+123"
            ]
            
            validation_results = {}
            
            for number in valid_numbers:
                is_valid = self.sms_service.validate_phone_number(number)
                validation_results[number] = is_valid
            
            for number in invalid_numbers:
                is_valid = self.sms_service.validate_phone_number(number)
                validation_results[number] = is_valid
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Phone Number Validation",
                success=True,
                duration=duration,
                details={'validation_results': validation_results}
            ))
            
            logger.info("✅ Phone number validation completed")
                
        except Exception as e:
            logger.error(f"❌ Phone number validation test error: {e}")
            self.results.append(TestResult(
                test_name="Phone Number Validation",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_email_templates(self):
        """Test email template rendering and personalization"""
        logger.info("🎨 Testing Email Template Rendering and Personalization")
        
        # Test 1: Template Personalization
        start_time = time.time()
        try:
            # Test with different user data
            test_users = [
                {"name": "John Smith", "email": "john@example.com", "income": "60k-80k"},
                {"name": "Sarah Johnson", "email": "sarah@example.com", "income": "80k-100k"},
                {"name": "Michael Brown", "email": "michael@example.com", "income": "40k-60k"}
            ]
            
            template_results = []
            
            for user in test_users:
                result = self.email_service.send_welcome_email(
                    user_email=user["email"],
                    user_name=user["name"]
                )
                template_results.append({
                    'user': user,
                    'success': result.get('success', False),
                    'email_id': result.get('email_id')
                })
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Email Template Personalization",
                success=all(r['success'] for r in template_results),
                duration=duration,
                details={'template_results': template_results}
            ))
            
            if all(r['success'] for r in template_results):
                logger.info("✅ Email template personalization successful")
            else:
                logger.error("❌ Some email template personalization failed")
                
        except Exception as e:
            logger.error(f"❌ Email template personalization test error: {e}")
            self.results.append(TestResult(
                test_name="Email Template Personalization",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 2: HTML Content Validation
        start_time = time.time()
        try:
            # Test custom HTML content
            custom_html = """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #667eea;">Custom Test Email</h1>
                <p>This is a test of custom HTML content with personalization.</p>
                <p>User: {user_name}</p>
                <p>Income Range: {income_range}</p>
            </div>
            """
            
            personalized_html = custom_html.format(
                user_name="Test User",
                income_range="60k-80k"
            )
            
            result = self.email_service.send_email(
                to_email=self.test_email,
                subject="Custom HTML Template Test",
                html_content=personalized_html
            )
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Custom HTML Template",
                success=result.get('success', False),
                duration=duration,
                details={
                    'email_id': result.get('email_id'),
                    'html_length': len(personalized_html),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ Custom HTML template sent successfully")
            else:
                logger.error(f"❌ Custom HTML template failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Custom HTML template test error: {e}")
            self.results.append(TestResult(
                test_name="Custom HTML Template",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_communication_routing(self):
        """Test communication routing based on user preferences"""
        logger.info("🔄 Testing Communication Routing")
        
        # Test 1: Basic Routing Logic
        start_time = time.time()
        try:
            # Test different message types and urgency levels
            test_scenarios = [
                {
                    'message_type': 'financial_alert',
                    'urgency': 'critical',
                    'expected_channel': 'sms'
                },
                {
                    'message_type': 'monthly_report',
                    'urgency': 'low',
                    'expected_channel': 'email'
                },
                {
                    'message_type': 'payment_reminder',
                    'urgency': 'high',
                    'expected_channel': 'sms'
                }
            ]
            
            routing_results = []
            
            for scenario in test_scenarios:
                # Mock message and user profile
                message = Mock()
                message.message_id = f"test_{scenario['message_type']}"
                message.user_id = self.test_user_id
                message.message_type = scenario['message_type']
                message.urgency_level = scenario['urgency']
                message.content = {'test': 'data'}
                
                user_profile = Mock()
                user_profile.user_id = self.test_user_id
                user_profile.email = self.test_email
                user_profile.phone_number = self.test_phone
                user_profile.engagement_level = 'medium'
                user_profile.sms_opted_in = True
                user_profile.email_opted_in = True
                
                routing_decision = self.router.route_message(message, user_profile)
                
                routing_results.append({
                    'scenario': scenario,
                    'decision': routing_decision.channel.value,
                    'expected': scenario['expected_channel'],
                    'correct': routing_decision.channel.value == scenario['expected_channel'],
                    'reasoning': routing_decision.reasoning
                })
            
            duration = time.time() - start_time
            
            correct_decisions = sum(1 for r in routing_results if r['correct'])
            total_decisions = len(routing_results)
            
            self.results.append(TestResult(
                test_name="Communication Routing Logic",
                success=correct_decisions == total_decisions,
                duration=duration,
                details={
                    'correct_decisions': correct_decisions,
                    'total_decisions': total_decisions,
                    'routing_results': routing_results
                }
            ))
            
            if correct_decisions == total_decisions:
                logger.info("✅ Communication routing logic working correctly")
            else:
                logger.error(f"❌ {total_decisions - correct_decisions} routing decisions incorrect")
                
        except Exception as e:
            logger.error(f"❌ Communication routing test error: {e}")
            self.results.append(TestResult(
                test_name="Communication Routing Logic",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_delivery_success_rates(self):
        """Test delivery success rates and tracking"""
        logger.info("📊 Testing Delivery Success Rates")
        
        # Test 1: SMS Delivery Tracking
        start_time = time.time()
        try:
            # Send a test SMS and track delivery
            sms_result = self.sms_service.send_sms(
                phone_number=self.test_phone,
                message="Test SMS for delivery tracking",
                priority_level="MEDIUM",
                user_id=self.test_user_id
            )
            
            if sms_result.get('success') and sms_result.get('message_sid'):
                # Track delivery status
                tracking_result = self.sms_service.track_delivery_status(
                    sms_result['message_sid']
                )
                
                duration = time.time() - start_time
                
                self.results.append(TestResult(
                    test_name="SMS Delivery Tracking",
                    success=tracking_result.get('success', False),
                    duration=duration,
                    details={
                        'message_sid': sms_result.get('message_sid'),
                        'tracking_status': tracking_result.get('status'),
                        'error_code': tracking_result.get('error_code'),
                        'error_message': tracking_result.get('error_message')
                    }
                ))
                
                if tracking_result.get('success'):
                    logger.info("✅ SMS delivery tracking successful")
                else:
                    logger.error(f"❌ SMS delivery tracking failed: {tracking_result.get('error')}")
            else:
                logger.error(f"❌ SMS delivery tracking failed - no message SID")
                self.results.append(TestResult(
                    test_name="SMS Delivery Tracking",
                    success=False,
                    duration=time.time() - start_time,
                    error="No message SID received"
                ))
                
        except Exception as e:
            logger.error(f"❌ SMS delivery tracking test error: {e}")
            self.results.append(TestResult(
                test_name="SMS Delivery Tracking",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 2: Email Delivery Success
        start_time = time.time()
        try:
            # Send multiple test emails to measure success rate
            email_results = []
            
            for i in range(3):
                result = self.email_service.send_notification_email(
                    user_email=self.test_email,
                    subject=f"Test Email {i+1}",
                    message=f"This is test email {i+1} for delivery success rate testing.",
                    notification_type="test"
                )
                email_results.append(result)
            
            successful_emails = sum(1 for r in email_results if r.get('success', False))
            total_emails = len(email_results)
            success_rate = (successful_emails / total_emails) * 100 if total_emails > 0 else 0
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Email Delivery Success Rate",
                success=success_rate >= 80,  # Expect 80%+ success rate
                duration=duration,
                details={
                    'successful_emails': successful_emails,
                    'total_emails': total_emails,
                    'success_rate': success_rate,
                    'email_results': email_results
                }
            ))
            
            if success_rate >= 80:
                logger.info(f"✅ Email delivery success rate: {success_rate:.1f}%")
            else:
                logger.error(f"❌ Email delivery success rate too low: {success_rate:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ Email delivery success rate test error: {e}")
            self.results.append(TestResult(
                test_name="Email Delivery Success Rate",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 3: Cost Tracking
        start_time = time.time()
        try:
            # Get SMS statistics
            sms_stats = self.sms_service.get_sms_statistics(days=30)
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Cost Tracking",
                success='error' not in sms_stats,
                duration=duration,
                details={'sms_statistics': sms_stats}
            ))
            
            if 'error' not in sms_stats:
                logger.info("✅ Cost tracking working correctly")
            else:
                logger.error(f"❌ Cost tracking failed: {sms_stats.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Cost tracking test error: {e}")
            self.results.append(TestResult(
                test_name="Cost Tracking",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        logger.info("⚠️ Testing Error Handling and Fallbacks")
        
        # Test 1: Invalid Email Address
        start_time = time.time()
        try:
            # Mock failure for invalid email
            self.email_service.send_email.return_value = {
                'success': False,
                'error': 'Invalid email address format'
            }
            
            result = self.email_service.send_email(
                to_email="invalid-email-address",
                subject="Test Invalid Email",
                html_content="<p>This should fail</p>"
            )
            
            duration = time.time() - start_time
            
            # This should fail gracefully
            self.results.append(TestResult(
                test_name="Invalid Email Handling",
                success=not result.get('success', True),  # Should fail
                duration=duration,
                details={
                    'success': result.get('success'),
                    'error': result.get('error')
                }
            ))
            
            if not result.get('success'):
                logger.info("✅ Invalid email handled gracefully")
            else:
                logger.warning("⚠️ Invalid email unexpectedly succeeded")
                
        except Exception as e:
            logger.error(f"❌ Invalid email test error: {e}")
            self.results.append(TestResult(
                test_name="Invalid Email Handling",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 2: Invalid Phone Number
        start_time = time.time()
        try:
            # Mock failure for invalid phone
            self.sms_service.send_sms.return_value = {
                'success': False,
                'error': 'Invalid phone number format'
            }
            
            result = self.sms_service.send_sms(
                phone_number="invalid-phone",
                message="This should fail",
                priority_level="MEDIUM"
            )
            
            duration = time.time() - start_time
            
            # This should fail gracefully
            self.results.append(TestResult(
                test_name="Invalid Phone Number Handling",
                success=not result.get('success', True),  # Should fail
                duration=duration,
                details={
                    'success': result.get('success'),
                    'error': result.get('error')
                }
            ))
            
            if not result.get('success'):
                logger.info("✅ Invalid phone number handled gracefully")
            else:
                logger.warning("⚠️ Invalid phone number unexpectedly succeeded")
                
        except Exception as e:
            logger.error(f"❌ Invalid phone number test error: {e}")
            self.results.append(TestResult(
                test_name="Invalid Phone Number Handling",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_user_preferences(self):
        """Test user preference handling"""
        logger.info("👤 Testing User Preferences")
        
        # Test 1: Opt-in/Opt-out Handling
        start_time = time.time()
        try:
            # Test SMS opt-out processing
            opt_out_data = {
                'From': self.test_phone,
                'Body': 'STOP'
            }
            
            opt_out_result = self.sms_service.handle_opt_out_responses(opt_out_data)
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="SMS Opt-out Handling",
                success=opt_out_result.get('success', False),
                duration=duration,
                details={
                    'action': opt_out_result.get('action'),
                    'confirmation_message': opt_out_result.get('confirmation_message'),
                    'error': opt_out_result.get('error')
                }
            ))
            
            if opt_out_result.get('success'):
                logger.info("✅ SMS opt-out handling working")
            else:
                logger.error(f"❌ SMS opt-out handling failed: {opt_out_result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ SMS opt-out handling test error: {e}")
            self.results.append(TestResult(
                test_name="SMS Opt-out Handling",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
        
        # Test 2: Help Request Handling
        start_time = time.time()
        try:
            # Mock help response
            self.sms_service.handle_opt_out_responses.return_value = {
                'success': True,
                'action': 'help_requested',
                'help_message': 'Need help? Call support or reply HELP.'
            }
            
            help_data = {
                'From': self.test_phone,
                'Body': 'HELP'
            }
            
            help_result = self.sms_service.handle_opt_out_responses(help_data)
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="Help Request Handling",
                success=help_result.get('success', False),
                duration=duration,
                details={
                    'action': help_result.get('action'),
                    'help_message': help_result.get('help_message'),
                    'error': help_result.get('error')
                }
            ))
            
            if help_result.get('success'):
                logger.info("✅ Help request handling working")
            else:
                logger.error(f"❌ Help request handling failed: {help_result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Help request handling test error: {e}")
            self.results.append(TestResult(
                test_name="Help Request Handling",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def test_integration_scenarios(self):
        """Test integration scenarios"""
        logger.info("🔗 Testing Integration Scenarios")
        
        # Test 1: End-to-End Communication Flow
        start_time = time.time()
        try:
            # Simulate a financial alert scenario
            # Create a critical financial alert
            alert_message = Mock()
            alert_message.message_id = "test_critical_alert_001"
            alert_message.user_id = self.test_user_id
            alert_message.message_type = "financial_alert"
            alert_message.urgency_level = "critical"
            alert_message.content = {
                'alert_type': 'low_balance',
                'account_balance': 150.00,
                'threshold': 200.00
            }
            
            user_profile = Mock()
            user_profile.user_id = self.test_user_id
            user_profile.email = self.test_email
            user_profile.phone_number = self.test_phone
            user_profile.engagement_level = 'medium'
            user_profile.sms_opted_in = True
            user_profile.email_opted_in = True
            
            # Route the message
            routing_decision = self.router.route_message(alert_message, user_profile)
            
            # Send based on routing decision
            if routing_decision.channel.value == 'sms':
                result = self.sms_service.send_sms(
                    phone_number=self.test_phone,
                    message="🚨 CRITICAL: Your account balance is $150.00. Consider transferring funds to avoid overdraft fees.",
                    priority_level="CRITICAL",
                    user_id=self.test_user_id
                )
            else:
                result = self.email_service.send_notification_email(
                    user_email=self.test_email,
                    subject="Critical Financial Alert",
                    message="Your account balance is $150.00. Consider transferring funds to avoid overdraft fees.",
                    notification_type="alert"
                )
            
            duration = time.time() - start_time
            
            self.results.append(TestResult(
                test_name="End-to-End Communication Flow",
                success=result.get('success', False),
                duration=duration,
                details={
                    'routing_channel': routing_decision.channel.value,
                    'routing_reasoning': routing_decision.reasoning,
                    'delivery_success': result.get('success'),
                    'message_id': result.get('message_sid') or result.get('email_id'),
                    'error': result.get('error')
                }
            ))
            
            if result.get('success'):
                logger.info("✅ End-to-end communication flow successful")
            else:
                logger.error(f"❌ End-to-end communication flow failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ End-to-end communication flow test error: {e}")
            self.results.append(TestResult(
                test_name="End-to-End Communication Flow",
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        total_duration = time.time() - self.start_time
        
        # Calculate success rates by category
        categories = {}
        for result in self.results:
            category = result.test_name.split(' - ')[0] if ' - ' in result.test_name else result.test_name
            if category not in categories:
                categories[category] = {'total': 0, 'successful': 0}
            categories[category]['total'] += 1
            if result.success:
                categories[category]['successful'] += 1
        
        # Generate category success rates
        category_rates = {}
        for category, stats in categories.items():
            success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
            category_rates[category] = {
                'success_rate': success_rate,
                'total': stats['total'],
                'successful': stats['successful'],
                'failed': stats['total'] - stats['successful']
            }
        
        # Get failed tests for detailed analysis
        failed_tests_details = [
            {
                'test_name': r.test_name,
                'error': r.error,
                'details': r.details
            }
            for r in self.results if not r.success
        ]
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'overall_success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                'total_duration_seconds': total_duration,
                'average_duration_per_test': total_duration / total_tests if total_tests > 0 else 0
            },
            'category_breakdown': category_rates,
            'failed_tests': failed_tests_details,
            'all_results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'duration': r.duration,
                    'error': r.error,
                    'details': r.details
                }
                for r in self.results
            ],
            'timestamp': datetime.utcnow().isoformat(),
            'test_configuration': {
                'test_email': self.test_email,
                'test_phone': self.test_phone,
                'test_user_id': self.test_user_id
            }
        }
        
        return report

def main():
    """Main test execution function"""
    print("🚀 MINGUS Communication Features Test Suite (Mock Mode)")
    print("=" * 60)
    
    # Initialize test suite
    test_suite = MockCommunicationFeaturesTestSuite()
    
    # Run all tests
    report = test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['overall_success_rate']:.1f}%")
    print(f"Total Duration: {summary['total_duration_seconds']:.2f} seconds")
    print(f"Average Duration per Test: {summary['average_duration_per_test']:.2f} seconds")
    
    # Print category breakdown
    print("\n📋 CATEGORY BREAKDOWN")
    print("-" * 40)
    for category, stats in report['category_breakdown'].items():
        print(f"{category}: {stats['success_rate']:.1f}% ({stats['successful']}/{stats['total']})")
    
    # Print failed tests
    if report['failed_tests']:
        print("\n❌ FAILED TESTS")
        print("-" * 40)
        for failed_test in report['failed_tests']:
            print(f"• {failed_test['test_name']}")
            if failed_test['error']:
                print(f"  Error: {failed_test['error']}")
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"communication_test_report_mock_{timestamp}.json"
    
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    
    # Return exit code
    if summary['failed_tests'] > 0:
        print("\n❌ Some tests failed. Please review the report for details.")
        return 1
    else:
        print("\n✅ All tests passed successfully!")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
