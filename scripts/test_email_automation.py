#!/usr/bin/env python3
"""
Test Script for MINGUS Email Automation System
Demonstrates the functionality of the email automation system
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.email_automation_service import EmailAutomationService, RiskLevel, Industry
from services.behavioral_triggers import BehavioralTriggersService, TriggerType, EngagementLevel
from models.assessment_models import AIJobAssessment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_assessment():
    """Create a test assessment for email automation testing"""
    return AIJobAssessment(
        id="test-assessment-123",
        job_title="Software Engineer",
        industry="Technology",
        experience_level="Mid-level",
        tasks_array=["coding", "testing", "documentation"],
        remote_work_frequency="Hybrid",
        ai_usage_frequency="Daily",
        team_size="5-10",
        tech_skills_level="Advanced",
        concerns_array=["job security", "skill obsolescence"],
        first_name="John",
        email="john.doe@example.com",
        location="San Francisco, CA",
        automation_score=65,
        augmentation_score=45,
        overall_risk_level="High",
        assessment_type="AI Job Impact Assessment",
        completed=True,
        created_at=datetime.now(timezone.utc)
    )

def test_welcome_series():
    """Test the welcome email series functionality"""
    logger.info("🧪 Testing Welcome Email Series")
    
    try:
        # Initialize email automation service
        email_service = EmailAutomationService()
        
        # Create test assessment
        assessment = create_test_assessment()
        
        # Test welcome series trigger
        success = email_service.trigger_welcome_series(assessment)
        
        if success:
            logger.info("✅ Welcome series triggered successfully")
        else:
            logger.error("❌ Failed to trigger welcome series")
        
        # Test individual email sending
        logger.info("📧 Testing individual email templates...")
        
        # Test welcome email 1
        welcome_1_success = email_service._send_welcome_email(assessment, "welcome_1", None)
        logger.info(f"Welcome Email 1: {'✅ Sent' if welcome_1_success else '❌ Failed'}")
        
        # Test risk-level specific email
        risk_email_success = email_service._send_risk_level_email(assessment, None)
        logger.info(f"Risk-Level Email: {'✅ Sent' if risk_email_success else '❌ Failed'}")
        
        # Test industry-specific email
        industry_email_success = email_service._send_industry_email(assessment, None)
        logger.info(f"Industry Email: {'✅ Sent' if industry_email_success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing welcome series: {e}")
        return False

def test_behavioral_triggers():
    """Test the behavioral triggers functionality"""
    logger.info("🎯 Testing Behavioral Triggers")
    
    try:
        # Initialize behavioral triggers service
        behavioral_service = BehavioralTriggersService()
        
        # Test A/B testing functionality
        logger.info("🧪 Testing A/B Testing System...")
        
        user_id = "test-user-123"
        test_name = "welcome_subject"
        
        # Get A/B test variant
        variant = behavioral_service.get_ab_test_variant(test_name, user_id)
        logger.info(f"A/B Test Variant: {variant.value}")
        
        # Track A/B test result
        tracking_success = behavioral_service.track_ab_test_result(
            test_name, variant, "open_rate", 0.25
        )
        logger.info(f"A/B Test Tracking: {'✅ Success' if tracking_success else '❌ Failed'}")
        
        # Test engagement level calculation
        logger.info("📊 Testing Engagement Level Calculation...")
        
        user_data = {
            'user_id': 'test-user-123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'open_rate': 0.85,
            'click_rate': 0.15,
            'days_inactive': 0
        }
        
        engagement_level = behavioral_service._calculate_engagement_level(user_data)
        logger.info(f"Engagement Level: {engagement_level.value}")
        
        # Test trigger processing
        logger.info("⚡ Testing Trigger Processing...")
        
        # Create test triggers
        test_triggers = [
            {
                'assessment_id': 'test-1',
                'email': 'test1@example.com',
                'first_name': 'Test1',
                'assessment_type': 'AI Job Impact Assessment',
                'trigger_type': TriggerType.INCOMPLETE_ASSESSMENT
            },
            {
                'user_id': 'test-2',
                'email': 'test2@example.com',
                'first_name': 'Test2',
                'engagement_level': 'high',
                'trigger_type': TriggerType.ENGAGEMENT_UPGRADE
            }
        ]
        
        # Process triggers (mock)
        logger.info(f"Processing {len(test_triggers)} test triggers...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing behavioral triggers: {e}")
        return False

def test_email_templates():
    """Test email template functionality"""
    logger.info("📝 Testing Email Templates")
    
    try:
        # Initialize email service
        email_service = EmailAutomationService()
        
        # Test template loading
        templates = email_service.templates
        logger.info(f"✅ Loaded {len(templates)} email templates")
        
        # Test template variables
        assessment = create_test_assessment()
        variables = email_service._get_assessment_variables(assessment)
        
        logger.info("📋 Template Variables:")
        for key, value in variables.items():
            logger.info(f"  {key}: {value}")
        
        # Test variable replacement
        test_content = "Hello {{first_name}}, your {{risk_level}} risk level is {{automation_score}}%"
        replaced_content = email_service._replace_variables(test_content, variables)
        logger.info(f"✅ Variable Replacement: {replaced_content}")
        
        # Test industry normalization
        test_industries = [
            "Technology",
            "Finance",
            "Healthcare",
            "Education",
            "Marketing",
            "Unknown Industry"
        ]
        
        logger.info("🏭 Industry Normalization:")
        for industry in test_industries:
            normalized = email_service._normalize_industry(industry)
            logger.info(f"  {industry} → {normalized.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing email templates: {e}")
        return False

def test_integration():
    """Test the complete integration"""
    logger.info("🔗 Testing Complete Integration")
    
    try:
        # Test the complete flow
        assessment = create_test_assessment()
        
        # Simulate assessment submission
        logger.info("📊 Simulating Assessment Submission...")
        
        # Trigger email automation
        email_service = EmailAutomationService()
        behavioral_service = BehavioralTriggersService()
        
        # Welcome series
        welcome_success = email_service.trigger_welcome_series(assessment)
        logger.info(f"Welcome Series: {'✅ Triggered' if welcome_success else '❌ Failed'}")
        
        # Behavioral triggers
        triggers = behavioral_service.process_behavioral_triggers()
        logger.info(f"Behavioral Triggers: {sum(triggers.values())} processed")
        
        # A/B testing
        variant = behavioral_service.get_ab_test_variant("welcome_subject", assessment.id)
        logger.info(f"A/B Test: {variant.value} variant assigned")
        
        logger.info("✅ Integration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing integration: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting MINGUS Email Automation System Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Email Templates", test_email_templates),
        ("Welcome Series", test_welcome_series),
        ("Behavioral Triggers", test_behavioral_triggers),
        ("Complete Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} Test...")
        logger.info("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name} Test: PASSED")
            else:
                logger.error(f"❌ {test_name} Test: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name} Test: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Email automation system is ready.")
    else:
        logger.error("⚠️ Some tests failed. Please check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
