#!/usr/bin/env python3
"""
SMS Message Templates Usage Examples for MINGUS

This file demonstrates how to use the SMS message templates with
cultural relevance for African American professionals, including
A/B testing and response tracking.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.sms_message_templates import sms_message_templates, MessageCategory, MessageTone
from services.sms_ab_testing import SMSABTestingFramework, ABTestConfig, TestStatus, ResponseType

def example_1_critical_financial_alerts():
    """Example 1: Critical Financial Alerts"""
    print("=== Example 1: Critical Financial Alerts ===")
    
    # User profile for Atlanta professional
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'first_name': 'Marcus',
        'age_range': '25-35',
        'income_range': '60k-80k',
        'regional_cost_of_living': 'atlanta',
        'primary_income_source': 'full_time',
        'family_obligations': 200.0,
        'emergency_fund_balance': 2500.0,
        'emergency_fund_target': 10000.0
    }
    
    # Critical alert scenarios
    scenarios = [
        {
            'template_id': 'low_balance_warning',
            'variables': {
                'first_name': 'Marcus',
                'balance': 150.00,
                'days': 3
            },
            'description': 'Low balance warning - 3 days until negative'
        },
        {
            'template_id': 'overdraft_risk',
            'variables': {
                'first_name': 'Marcus',
                'amount': 500.00,
                'date': 'Friday'
            },
            'description': 'Overdraft risk warning'
        },
        {
            'template_id': 'payment_failure',
            'variables': {
                'first_name': 'Marcus',
                'payment_type': 'student loan',
                'support_phone': '+1-800-MINGUS-1'
            },
            'description': 'Payment failure alert'
        },
        {
            'template_id': 'security_alert',
            'variables': {
                'first_name': 'Marcus'
            },
            'description': 'Security alert'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['description']}:")
        message = sms_message_templates.get_message(
            template_id=scenario['template_id'],
            variables=scenario['variables'],
            user_profile=user_profile,
            ab_test=True
        )
        print(f"Message: {message}")
        print(f"Length: {len(message)} characters")
    
    print()

def example_2_engagement_checkins():
    """Example 2: Engagement & Check-ins"""
    print("=== Example 2: Engagement & Check-ins ===")
    
    # User profile for DC Metro professional
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'first_name': 'Aisha',
        'age_range': '25-35',
        'income_range': '80k-100k',
        'regional_cost_of_living': 'dc_metro',
        'primary_income_source': 'full_time',
        'family_obligations': 150.0,
        'emergency_fund_balance': 8000.0,
        'emergency_fund_target': 15000.0
    }
    
    # Engagement scenarios
    scenarios = [
        {
            'template_id': 'weekly_wellness_checkin',
            'variables': {
                'first_name': 'Aisha'
            },
            'description': 'Weekly wellness check-in'
        },
        {
            'template_id': 'exercise_financial_benefits',
            'variables': {
                'first_name': 'Aisha',
                'savings': 1200
            },
            'description': 'Exercise financial benefits'
        },
        {
            'template_id': 'relationship_financial_planning',
            'variables': {
                'first_name': 'Aisha'
            },
            'description': 'Relationship financial planning'
        },
        {
            'template_id': 'goal_milestone_celebration',
            'variables': {
                'first_name': 'Aisha',
                'milestone': 'your $10k emergency fund goal'
            },
            'description': 'Goal milestone celebration'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['description']}:")
        message = sms_message_templates.get_message(
            template_id=scenario['template_id'],
            variables=scenario['variables'],
            user_profile=user_profile,
            ab_test=True
        )
        print(f"Message: {message}")
        print(f"Length: {len(message)} characters")
    
    print()

def example_3_bill_payment_reminders():
    """Example 3: Bill & Payment Reminders"""
    print("=== Example 3: Bill & Payment Reminders ===")
    
    # User profile for Houston professional
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'first_name': 'Jordan',
        'age_range': '25-35',
        'income_range': '40k-60k',
        'regional_cost_of_living': 'houston',
        'primary_income_source': 'gig_work',
        'student_loan_payment': 350.0,
        'rent_mortgage': 1200.0,
        'family_obligations': 300.0
    }
    
    # Bill reminder scenarios
    scenarios = [
        {
            'template_id': 'student_loan_payment',
            'variables': {
                'first_name': 'Jordan',
                'amount': 350.00,
                'days': 3
            },
            'description': 'Student loan payment reminder'
        },
        {
            'template_id': 'subscription_renewal',
            'variables': {
                'first_name': 'Jordan',
                'service': 'Netflix',
                'days': 2,
                'amount': 15.99
            },
            'description': 'Subscription renewal reminder'
        },
        {
            'template_id': 'rent_mortgage_payment',
            'variables': {
                'first_name': 'Jordan',
                'payment_type': 'rent',
                'amount': 1200.00,
                'days': 2,
                'city': 'Houston'
            },
            'description': 'Rent payment reminder'
        },
        {
            'template_id': 'credit_card_payment',
            'variables': {
                'first_name': 'Jordan',
                'amount': 450.00,
                'days': 5
            },
            'description': 'Credit card payment reminder'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['description']}:")
        message = sms_message_templates.get_message(
            template_id=scenario['template_id'],
            variables=scenario['variables'],
            user_profile=user_profile,
            ab_test=True
        )
        print(f"Message: {message}")
        print(f"Length: {len(message)} characters")
    
    print()

def example_4_wealth_building_messages():
    """Example 4: Wealth Building Messages"""
    print("=== Example 4: Wealth Building Messages ===")
    
    # User profile for NYC professional
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'first_name': 'Keisha',
        'age_range': '25-35',
        'income_range': '80k-100k',
        'regional_cost_of_living': 'new_york',
        'primary_income_source': 'full_time',
        'emergency_fund_balance': 12000.0,
        'emergency_fund_target': 20000.0
    }
    
    # Wealth building scenarios
    scenarios = [
        {
            'template_id': 'investment_opportunity',
            'variables': {
                'first_name': 'Keisha'
            },
            'description': 'Investment opportunity for Black professionals'
        },
        {
            'template_id': 'emergency_fund_reminder',
            'variables': {
                'first_name': 'Keisha',
                'current': 12000,
                'target': 20000
            },
            'description': 'Emergency fund progress reminder'
        },
        {
            'template_id': 'home_ownership_progress',
            'variables': {
                'first_name': 'Keisha',
                'amount': 5000
            },
            'description': 'Home ownership progress'
        },
        {
            'template_id': 'financial_education',
            'variables': {
                'first_name': 'Keisha',
                'topic': 'Building Generational Wealth'
            },
            'description': 'Financial education content'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['description']}:")
        message = sms_message_templates.get_message(
            template_id=scenario['template_id'],
            variables=scenario['variables'],
            user_profile=user_profile,
            ab_test=True
        )
        print(f"Message: {message}")
        print(f"Length: {len(message)} characters")
    
    print()

def example_5_community_events():
    """Example 5: Community Events"""
    print("=== Example 5: Community Events ===")
    
    # User profile for LA professional
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'first_name': 'Darnell',
        'age_range': '25-35',
        'income_range': '60k-80k',
        'regional_cost_of_living': 'los_angeles',
        'primary_income_source': 'business',
        'family_obligations': 250.0
    }
    
    # Community event scenarios
    scenarios = [
        {
            'template_id': 'community_event',
            'variables': {
                'first_name': 'Darnell',
                'event_type': 'financial literacy workshop',
                'city': 'Los Angeles'
            },
            'description': 'Community financial literacy event'
        },
        {
            'template_id': 'community_event',
            'variables': {
                'first_name': 'Darnell',
                'event_type': 'networking mixer',
                'city': 'LA'
            },
            'description': 'Professional networking event'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['description']}:")
        message = sms_message_templates.get_message(
            template_id=scenario['template_id'],
            variables=scenario['variables'],
            user_profile=user_profile,
            ab_test=True
        )
        print(f"Message: {message}")
        print(f"Length: {len(message)} characters")
    
    print()

def example_6_ab_testing_setup():
    """Example 6: A/B Testing Setup and Results"""
    print("=== Example 6: A/B Testing Setup and Results ===")
    
    # Mock database session (in real implementation, use actual session)
    class MockDBSession:
        pass
    
    db_session = MockDBSession()
    
    # Create A/B testing framework
    ab_testing = SMSABTestingFramework(db_session)
    
    # Create test configuration
    test_config = ABTestConfig(
        test_id="low_balance_warning_test_001",
        template_id="low_balance_warning",
        test_name="Low Balance Warning Message Optimization",
        description="Testing different tones for low balance warnings",
        variations=["low_balance_warning_A", "low_balance_warning_B", "low_balance_warning_C"],
        traffic_split={"low_balance_warning_A": 33.33, "low_balance_warning_B": 33.33, "low_balance_warning_C": 33.34},
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status=TestStatus.ACTIVE,
        success_metric="conversion_rate",
        min_sample_size=100,
        confidence_level=0.95
    )
    
    print("Creating A/B test...")
    success = ab_testing.create_test(test_config)
    print(f"Test created: {success}")
    
    # Simulate test assignments
    test_users = [
        {"user_id": "user_001", "first_name": "Marcus", "region": "atlanta"},
        {"user_id": "user_002", "first_name": "Aisha", "region": "dc_metro"},
        {"user_id": "user_003", "first_name": "Jordan", "region": "houston"},
        {"user_id": "user_004", "first_name": "Keisha", "region": "new_york"},
        {"user_id": "user_005", "first_name": "Darnell", "region": "los_angeles"}
    ]
    
    print("\nSimulating test assignments:")
    for user in test_users:
        variation = ab_testing.get_variation_for_user(test_config.test_id, user["user_id"])
        print(f"User {user['user_id']} ({user['first_name']} from {user['region']}) → Variation {variation}")
        
        # Simulate message sending
        message_data = {
            "user_id": user["user_id"],
            "first_name": user["first_name"],
            "balance": 150.00,
            "days": 3
        }
        
        ab_testing.track_message_sent(test_config.test_id, variation, user["user_id"], message_data)
        
        # Simulate some responses
        if random.random() < 0.3:  # 30% response rate
            response_type = random.choice([ResponseType.REPLY, ResponseType.ACTION, ResponseType.CONVERSION])
            ab_testing.track_response(test_config.test_id, variation, user["user_id"], response_type)
            print(f"  → User responded with {response_type.value}")
    
    print("\nGetting test results...")
    results = ab_testing.get_test_results(test_config.test_id)
    
    print("Test Results:")
    print(f"Test ID: {results.get('test_id')}")
    print(f"Test Name: {results.get('test_name')}")
    print(f"Status: {results.get('status')}")
    
    print("\nVariation Results:")
    for variation_id, data in results.get('variations', {}).items():
        print(f"\n{variation_id}:")
        print(f"  Sent: {data.get('sent_count', 0)}")
        print(f"  Responses: {data.get('total_responses', 0)}")
        print(f"  Response Rate: {data.get('response_rate', 0):.1f}%")
        print(f"  Conversion Rate: {data.get('conversion_rate', 0):.1f}%")
    
    print(f"\nRecommendation: {results.get('recommendation', {}).get('action', 'N/A')}")
    print(f"Best Variation: {results.get('recommendation', {}).get('best_variation', 'N/A')}")
    print()

def example_7_cultural_personalization():
    """Example 7: Cultural Personalization by Region"""
    print("=== Example 7: Cultural Personalization by Region ===")
    
    # Test different regions with same scenario
    regions = ['atlanta', 'dc_metro', 'new_york', 'los_angeles', 'houston']
    
    base_variables = {
        'first_name': 'Marcus',
        'balance': 150.00,
        'days': 3
    }
    
    for region in regions:
        user_profile = {
            'user_id': str(uuid.uuid4()),
            'first_name': 'Marcus',
            'age_range': '25-35',
            'income_range': '60k-80k',
            'regional_cost_of_living': region,
            'primary_income_source': 'full_time'
        }
        
        print(f"\n{region.upper()} Professional:")
        message = sms_message_templates.get_message(
            template_id='low_balance_warning',
            variables=base_variables,
            user_profile=user_profile,
            ab_test=True
        )
        print(f"Message: {message}")
        
        # Get cultural suggestions
        suggestions = sms_message_templates.get_cultural_message_suggestions(user_profile)
        print(f"Cultural Suggestions: {suggestions[:2]}")  # Show first 2 suggestions
    
    print()

def example_8_response_tracking():
    """Example 8: Response Tracking and Analytics"""
    print("=== Example 8: Response Tracking and Analytics ===")
    
    # Mock database session
    class MockDBSession:
        pass
    
    db_session = MockDBSession()
    ab_testing = SMSABTestingFramework(db_session)
    
    # Simulate tracking various response types
    test_id = "response_tracking_test_001"
    user_id = "user_001"
    variation_id = "low_balance_warning_A"
    
    print("Tracking different response types:")
    
    # Track message sent
    message_data = {
        "user_id": user_id,
        "first_name": "Marcus",
        "balance": 150.00,
        "days": 3
    }
    ab_testing.track_message_sent(test_id, variation_id, user_id, message_data)
    print(f"✓ Message sent tracked")
    
    # Track different response types
    response_types = [
        (ResponseType.REPLY, "User replied with 'HELP'"),
        (ResponseType.ACTION, "User clicked on transfer funds link"),
        (ResponseType.CONVERSION, "User transferred funds"),
        (ResponseType.HELP_REQUEST, "User requested assistance")
    ]
    
    for response_type, description in response_types:
        response_data = {
            "response_content": description,
            "response_time_seconds": random.randint(30, 300)
        }
        ab_testing.track_response(test_id, variation_id, user_id, response_type, response_data)
        print(f"✓ {response_type.value} tracked: {description}")
    
    # Get A/B test results
    results = ab_testing.get_test_results(test_id)
    
    print(f"\nResponse Analytics:")
    if 'variations' in results and variation_id in results['variations']:
        variation_data = results['variations'][variation_id]
        print(f"Total Sent: {variation_data.get('sent_count', 0)}")
        print(f"Total Responses: {variation_data.get('total_responses', 0)}")
        print(f"Response Rate: {variation_data.get('response_rate', 0):.1f}%")
        print(f"Response Breakdown: {variation_data.get('response_counts', {})}")
    
    print()

def example_9_message_effectiveness_analysis():
    """Example 9: Message Effectiveness Analysis"""
    print("=== Example 9: Message Effectiveness Analysis ===")
    
    # Analyze different message categories
    categories = [
        (MessageCategory.CRITICAL_ALERT, "Critical Alerts"),
        (MessageCategory.ENGAGEMENT_CHECKIN, "Engagement Check-ins"),
        (MessageCategory.BILL_REMINDER, "Bill Reminders"),
        (MessageCategory.WEALTH_BUILDING, "Wealth Building"),
        (MessageCategory.COMMUNITY_EVENT, "Community Events")
    ]
    
    user_profile = {
        'user_id': str(uuid.uuid4()),
        'first_name': 'Marcus',
        'age_range': '25-35',
        'income_range': '60k-80k',
        'regional_cost_of_living': 'atlanta',
        'primary_income_source': 'full_time'
    }
    
    print("Message Effectiveness Analysis by Category:")
    
    for category, category_name in categories:
        print(f"\n{category_name}:")
        
        # Get templates for this category
        category_templates = [
            template for template in sms_message_templates.templates.values()
            if template.category == category
        ]
        
        for template in category_templates[:2]:  # Show first 2 templates per category
            # Test with sample variables
            sample_variables = {
                'first_name': 'Marcus',
                'balance': 150.00,
                'days': 3,
                'amount': 350.00,
                'service': 'Netflix',
                'payment_type': 'rent',
                'city': 'Atlanta',
                'milestone': 'your emergency fund goal',
                'current': 2500,
                'target': 10000,
                'topic': 'Building Wealth',
                'event_type': 'financial workshop'
            }
            
            message = sms_message_templates.get_message(
                template_id=template.template_id,
                variables=sample_variables,
                user_profile=user_profile,
                ab_test=False
            )
            
            print(f"  {template.template_id}:")
            print(f"    Length: {len(message)} chars")
            print(f"    Tone: {template.tone.value}")
            print(f"    Cultural Elements: {template.cultural_elements}")
            print(f"    Message: {message[:80]}...")
    
    print()

def run_all_examples():
    """Run all SMS template examples"""
    print("MINGUS SMS Message Templates Examples")
    print("=" * 50)
    print()
    
    example_1_critical_financial_alerts()
    example_2_engagement_checkins()
    example_3_bill_payment_reminders()
    example_4_wealth_building_messages()
    example_5_community_events()
    example_6_ab_testing_setup()
    example_7_cultural_personalization()
    example_8_response_tracking()
    example_9_message_effectiveness_analysis()
    
    print("=" * 50)
    print("All SMS template examples completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Critical financial alerts with cultural relevance")
    print("✅ Engagement check-ins with wellness focus")
    print("✅ Bill payment reminders with support messaging")
    print("✅ Wealth building messages for generational impact")
    print("✅ Community events with networking focus")
    print("✅ A/B testing framework for message optimization")
    print("✅ Cultural personalization by region")
    print("✅ Response tracking and analytics")
    print("✅ Message effectiveness analysis")
    print("\nCultural Elements Highlighted:")
    print("🎯 African American professional focus (25-35, $40k-$100k)")
    print("🏠 Family financial responsibility recognition")
    print("💪 Wealth building and generational impact")
    print("🤝 Community and networking emphasis")
    print("🎓 Education and career advancement support")
    print("🌍 Regional cultural context (Atlanta, DC, NYC, LA, Houston)")

if __name__ == "__main__":
    import random
    run_all_examples() 