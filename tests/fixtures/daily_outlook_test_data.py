#!/usr/bin/env python3
"""
Daily Outlook Test Data Fixtures

Comprehensive test data fixtures for different user scenarios including:
- Persona-based test data (Maya, Marcus, Dr. Williams)
- Tier-specific test scenarios
- Relationship status variations
- Financial goal progressions
- Streak milestone scenarios
- Error condition data
- Performance test data
- Security test payloads
"""

import json
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional


class DailyOutlookTestFixtures:
    """Comprehensive test data fixtures for Daily Outlook functionality"""
    
    # ============================================================================
    # PERSONA-BASED TEST DATA
    # ============================================================================
    
    @staticmethod
    def maya_persona_data() -> Dict[str, Any]:
        """Test data for Maya persona (Budget Tier - Single, Career-Focused)"""
        return {
            'user': {
                'email': 'maya.johnson@email.com',
                'first_name': 'Maya',
                'last_name': 'Johnson',
                'tier': 'budget',
                'age': 24,
                'location': 'Atlanta, GA',
                'occupation': 'Junior Software Developer',
                'income': 45000,
                'financial_goals': [
                    'Build emergency fund',
                    'Pay off student loans',
                    'Save for first home'
                ],
                'relationship_status': 'single_career_focused',
                'satisfaction_score': 8,
                'financial_impact_score': 7
            },
            'outlook_data': {
                'balance_score': 72,
                'financial_weight': 0.40,
                'wellness_weight': 0.20,
                'relationship_weight': 0.15,
                'career_weight': 0.25,
                'primary_insight': "Your career growth is accelerating! Focus on skill development.",
                'quick_actions': [
                    {
                        'id': 'career_1',
                        'title': 'Update LinkedIn profile',
                        'description': 'Add recent projects and skills',
                        'priority': 'high',
                        'estimated_time': '15 min'
                    },
                    {
                        'id': 'financial_1',
                        'title': 'Review budget',
                        'description': 'Track monthly expenses',
                        'priority': 'high',
                        'estimated_time': '10 min'
                    },
                    {
                        'id': 'wellness_1',
                        'title': 'Take a break',
                        'description': 'Step away from computer',
                        'priority': 'medium',
                        'estimated_time': '5 min'
                    }
                ],
                'encouragement_message': "You're building the foundation for financial success!",
                'surprise_element': "Did you know? 78% of software developers see salary increases within 2 years.",
                'streak_count': 12,
                'user_tier': 'budget'
            }
        }
    
    @staticmethod
    def marcus_persona_data() -> Dict[str, Any]:
        """Test data for Marcus persona (Mid-Tier - Dating, Financial Growth)"""
        return {
            'user': {
                'email': 'marcus.davis@email.com',
                'first_name': 'Marcus',
                'last_name': 'Davis',
                'tier': 'mid_tier',
                'age': 28,
                'location': 'Chicago, IL',
                'occupation': 'Marketing Manager',
                'income': 65000,
                'financial_goals': [
                    'Maximize 401k contributions',
                    'Save for engagement ring',
                    'Build investment portfolio'
                ],
                'relationship_status': 'dating',
                'satisfaction_score': 9,
                'financial_impact_score': 8
            },
            'outlook_data': {
                'balance_score': 82,
                'financial_weight': 0.30,
                'wellness_weight': 0.25,
                'relationship_weight': 0.30,
                'career_weight': 0.15,
                'primary_insight': "Your relationship is thriving! Consider financial planning together.",
                'quick_actions': [
                    {
                        'id': 'relationship_1',
                        'title': 'Plan date night',
                        'description': 'Budget for special evening',
                        'priority': 'high',
                        'estimated_time': '30 min'
                    },
                    {
                        'id': 'financial_1',
                        'title': 'Review investment portfolio',
                        'description': 'Check 401k performance',
                        'priority': 'high',
                        'estimated_time': '20 min'
                    },
                    {
                        'id': 'wellness_1',
                        'title': 'Couple\'s workout',
                        'description': 'Exercise together',
                        'priority': 'medium',
                        'estimated_time': '60 min'
                    }
                ],
                'encouragement_message': "Love and financial growth go hand in hand!",
                'surprise_element': "Couples who discuss finances regularly are 30% more likely to stay together.",
                'streak_count': 8,
                'user_tier': 'mid_tier'
            }
        }
    
    @staticmethod
    def dr_williams_persona_data() -> Dict[str, Any]:
        """Test data for Dr. Williams persona (Professional Tier - Married, Established)"""
        return {
            'user': {
                'email': 'dr.williams@email.com',
                'first_name': 'Dr. Sarah',
                'last_name': 'Williams',
                'tier': 'professional',
                'age': 35,
                'location': 'San Francisco, CA',
                'occupation': 'Senior Software Engineer',
                'income': 120000,
                'financial_goals': [
                    'Maximize retirement savings',
                    'College fund for children',
                    'Real estate investment'
                ],
                'relationship_status': 'married',
                'satisfaction_score': 9,
                'financial_impact_score': 9
            },
            'outlook_data': {
                'balance_score': 88,
                'financial_weight': 0.25,
                'wellness_weight': 0.30,
                'relationship_weight': 0.25,
                'career_weight': 0.20,
                'primary_insight': "Your family's financial future is secure. Consider advanced investment strategies.",
                'quick_actions': [
                    {
                        'id': 'financial_1',
                        'title': 'Review retirement portfolio',
                        'description': 'Optimize 401k allocation',
                        'priority': 'high',
                        'estimated_time': '30 min'
                    },
                    {
                        'id': 'family_1',
                        'title': 'Plan family vacation',
                        'description': 'Budget for summer trip',
                        'priority': 'high',
                        'estimated_time': '45 min'
                    },
                    {
                        'id': 'wellness_1',
                        'title': 'Family wellness check',
                        'description': 'Schedule annual physicals',
                        'priority': 'medium',
                        'estimated_time': '15 min'
                    }
                ],
                'encouragement_message': "Your financial wisdom is creating generational wealth!",
                'surprise_element': "Families with comprehensive financial plans are 40% more likely to achieve long-term goals.",
                'streak_count': 15,
                'user_tier': 'professional'
            }
        }
    
    # ============================================================================
    # TIER-SPECIFIC TEST SCENARIOS
    # ============================================================================
    
    @staticmethod
    def budget_tier_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for budget tier users"""
        return [
            {
                'scenario': 'new_budget_user',
                'user_data': {
                    'tier': 'budget',
                    'income': 35000,
                    'financial_goals': ['Build emergency fund', 'Pay off debt'],
                    'relationship_status': 'single_career_focused'
                },
                'outlook_data': {
                    'balance_score': 65,
                    'financial_weight': 0.50,
                    'wellness_weight': 0.20,
                    'relationship_weight': 0.10,
                    'career_weight': 0.20,
                    'primary_insight': "Focus on building your financial foundation!",
                    'quick_actions': [
                        {
                            'id': 'budget_1',
                            'title': 'Create emergency fund',
                            'description': 'Start with $1000 goal',
                            'priority': 'high'
                        }
                    ]
                }
            },
            {
                'scenario': 'budget_user_with_debt',
                'user_data': {
                    'tier': 'budget',
                    'income': 40000,
                    'debt_amount': 15000,
                    'financial_goals': ['Pay off credit cards', 'Build emergency fund']
                },
                'outlook_data': {
                    'balance_score': 55,
                    'financial_weight': 0.60,
                    'wellness_weight': 0.15,
                    'relationship_weight': 0.10,
                    'career_weight': 0.15,
                    'primary_insight': "Debt reduction is your top priority!",
                    'quick_actions': [
                        {
                            'id': 'debt_1',
                            'title': 'Review debt payments',
                            'description': 'Optimize payment strategy',
                            'priority': 'high'
                        }
                    ]
                }
            }
        ]
    
    @staticmethod
    def mid_tier_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for mid-tier users"""
        return [
            {
                'scenario': 'mid_tier_career_growth',
                'user_data': {
                    'tier': 'mid_tier',
                    'income': 60000,
                    'financial_goals': ['Maximize 401k', 'Save for house down payment'],
                    'relationship_status': 'dating'
                },
                'outlook_data': {
                    'balance_score': 78,
                    'financial_weight': 0.35,
                    'wellness_weight': 0.25,
                    'relationship_weight': 0.25,
                    'career_weight': 0.15,
                    'primary_insight': "Your career and relationship are both growing!",
                    'quick_actions': [
                        {
                            'id': 'investment_1',
                            'title': 'Review 401k contributions',
                            'description': 'Increase contribution rate',
                            'priority': 'high'
                        }
                    ]
                }
            }
        ]
    
    @staticmethod
    def professional_tier_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for professional tier users"""
        return [
            {
                'scenario': 'professional_established',
                'user_data': {
                    'tier': 'professional',
                    'income': 100000,
                    'financial_goals': ['Maximize retirement', 'College fund', 'Real estate'],
                    'relationship_status': 'married'
                },
                'outlook_data': {
                    'balance_score': 85,
                    'financial_weight': 0.30,
                    'wellness_weight': 0.30,
                    'relationship_weight': 0.25,
                    'career_weight': 0.15,
                    'primary_insight': "Your financial foundation is solid!",
                    'quick_actions': [
                        {
                            'id': 'retirement_1',
                            'title': 'Optimize retirement portfolio',
                            'description': 'Review asset allocation',
                            'priority': 'high'
                        }
                    ]
                }
            }
        ]
    
    # ============================================================================
    # RELATIONSHIP STATUS VARIATIONS
    # ============================================================================
    
    @staticmethod
    def relationship_status_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for different relationship statuses"""
        return [
            {
                'status': 'single_career_focused',
                'satisfaction_score': 8,
                'financial_impact_score': 7,
                'expected_weights': {
                    'career_weight': 0.30,
                    'financial_weight': 0.35,
                    'relationship_weight': 0.15,
                    'wellness_weight': 0.20
                },
                'quick_actions': [
                    {
                        'id': 'career_focus_1',
                        'title': 'Update professional skills',
                        'description': 'Take online course',
                        'priority': 'high'
                    }
                ]
            },
            {
                'status': 'dating',
                'satisfaction_score': 9,
                'financial_impact_score': 8,
                'expected_weights': {
                    'career_weight': 0.20,
                    'financial_weight': 0.30,
                    'relationship_weight': 0.30,
                    'wellness_weight': 0.20
                },
                'quick_actions': [
                    {
                        'id': 'relationship_focus_1',
                        'title': 'Plan romantic date',
                        'description': 'Budget for special evening',
                        'priority': 'high'
                    }
                ]
            },
            {
                'status': 'married',
                'satisfaction_score': 9,
                'financial_impact_score': 9,
                'expected_weights': {
                    'career_weight': 0.20,
                    'financial_weight': 0.25,
                    'relationship_weight': 0.25,
                    'wellness_weight': 0.30
                },
                'quick_actions': [
                    {
                        'id': 'family_focus_1',
                        'title': 'Plan family activities',
                        'description': 'Budget for family time',
                        'priority': 'high'
                    }
                ]
            }
        ]
    
    # ============================================================================
    # STREAK MILESTONE SCENARIOS
    # ============================================================================
    
    @staticmethod
    def streak_milestone_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for different streak milestones"""
        return [
            {
                'streak_count': 1,
                'milestone_reached': False,
                'next_milestone': 3,
                'progress_percentage': 33,
                'celebration_message': "Great start! Keep building your momentum!",
                'encouragement': "Every day counts! You're building a habit."
            },
            {
                'streak_count': 3,
                'milestone_reached': True,
                'next_milestone': 7,
                'progress_percentage': 43,
                'celebration_message': "🎉 3-day streak! You're building momentum!",
                'encouragement': "Three days strong! You're forming a habit."
            },
            {
                'streak_count': 7,
                'milestone_reached': True,
                'next_milestone': 14,
                'progress_percentage': 50,
                'celebration_message': "🔥 Week streak! You're on fire!",
                'encouragement': "A full week! You're building a strong habit."
            },
            {
                'streak_count': 14,
                'milestone_reached': True,
                'next_milestone': 30,
                'progress_percentage': 47,
                'celebration_message': "💪 Two weeks strong! You're unstoppable!",
                'encouragement': "Two weeks! You're building a lifestyle."
            },
            {
                'streak_count': 30,
                'milestone_reached': True,
                'next_milestone': 60,
                'progress_percentage': 50,
                'celebration_message': "🏆 Monthly streak! You're a champion!",
                'encouragement': "A full month! You've mastered this habit."
            },
            {
                'streak_count': 100,
                'milestone_reached': True,
                'next_milestone': 365,
                'progress_percentage': 27,
                'celebration_message': "🎊 Century streak! You're legendary!",
                'encouragement': "100 days! You're a habit master."
            }
        ]
    
    # ============================================================================
    # ERROR CONDITION DATA
    # ============================================================================
    
    @staticmethod
    def error_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for error conditions"""
        return [
            {
                'error_type': 'network_error',
                'error_message': 'Failed to fetch daily outlook data',
                'error_code': 'NETWORK_ERROR',
                'recovery_action': 'retry_request',
                'user_message': 'Please check your internet connection and try again.'
            },
            {
                'error_type': 'authentication_error',
                'error_message': 'Invalid authentication token',
                'error_code': 'AUTH_ERROR',
                'recovery_action': 'redirect_to_login',
                'user_message': 'Please log in again to continue.'
            },
            {
                'error_type': 'tier_restriction',
                'error_message': 'Feature not available in current tier',
                'error_code': 'TIER_RESTRICTION',
                'recovery_action': 'show_upgrade_prompt',
                'user_message': 'Upgrade to access this feature.'
            },
            {
                'error_type': 'data_validation_error',
                'error_message': 'Invalid input data',
                'error_code': 'VALIDATION_ERROR',
                'recovery_action': 'show_validation_errors',
                'user_message': 'Please check your input and try again.'
            },
            {
                'error_type': 'server_error',
                'error_message': 'Internal server error',
                'error_code': 'SERVER_ERROR',
                'recovery_action': 'retry_later',
                'user_message': 'Something went wrong. Please try again later.'
            }
        ]
    
    # ============================================================================
    # PERFORMANCE TEST DATA
    # ============================================================================
    
    @staticmethod
    def performance_test_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for performance testing"""
        return [
            {
                'scenario': 'high_load',
                'concurrent_users': 100,
                'requests_per_second': 50,
                'expected_response_time': 0.5,
                'expected_success_rate': 95
            },
            {
                'scenario': 'stress_test',
                'concurrent_users': 500,
                'requests_per_second': 200,
                'expected_response_time': 1.0,
                'expected_success_rate': 90
            },
            {
                'scenario': 'spike_test',
                'concurrent_users': 1000,
                'requests_per_second': 500,
                'expected_response_time': 2.0,
                'expected_success_rate': 85
            }
        ]
    
    # ============================================================================
    # SECURITY TEST PAYLOADS
    # ============================================================================
    
    @staticmethod
    def security_test_payloads() -> List[Dict[str, Any]]:
        """Test payloads for security testing"""
        return [
            {
                'test_type': 'sql_injection',
                'payloads': [
                    "'; DROP TABLE daily_outlooks; --",
                    "1' OR '1'='1",
                    "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
                    "1' UNION SELECT * FROM users --"
                ]
            },
            {
                'test_type': 'xss_attacks',
                'payloads': [
                    '<script>alert("xss")</script>',
                    'javascript:alert("xss")',
                    '<img src="x" onerror="alert(\'xss\')">',
                    '<svg onload="alert(\'xss\')">',
                    '"><script>alert("xss")</script>'
                ]
            },
            {
                'test_type': 'input_validation',
                'payloads': [
                    {'action_id': 123, 'completion_status': True},  # Wrong type
                    {'action_id': 'test', 'completion_status': 'true'},  # Wrong type
                    {'rating': 6},  # Out of range
                    {'rating': -1},  # Out of range
                    {'rating': 'invalid'}  # Wrong type
                ]
            },
            {
                'test_type': 'rate_limiting',
                'payloads': [
                    {'requests_per_minute': 100, 'expected_status': 429},
                    {'requests_per_minute': 50, 'expected_status': 200},
                    {'requests_per_minute': 200, 'expected_status': 429}
                ]
            }
        ]
    
    # ============================================================================
    # CACHE TEST SCENARIOS
    # ============================================================================
    
    @staticmethod
    def cache_test_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for cache testing"""
        return [
            {
                'scenario': 'cache_hit',
                'cache_key': 'daily_outlook:user123:2024-01-15',
                'cache_value': {
                    'balance_score': 85,
                    'primary_insight': 'Cached insight',
                    'quick_actions': []
                },
                'ttl': 3600,
                'expected_hit_rate': 0.95
            },
            {
                'scenario': 'cache_miss',
                'cache_key': 'daily_outlook:user456:2024-01-15',
                'cache_value': None,
                'ttl': 0,
                'expected_hit_rate': 0.0
            },
            {
                'scenario': 'cache_expiration',
                'cache_key': 'daily_outlook:user789:2024-01-15',
                'cache_value': {
                    'balance_score': 75,
                    'primary_insight': 'Expired insight',
                    'quick_actions': []
                },
                'ttl': 1,  # 1 second
                'expected_hit_rate': 0.0
            }
        ]
    
    # ============================================================================
    # NOTIFICATION TEST SCENARIOS
    # ============================================================================
    
    @staticmethod
    def notification_test_scenarios() -> List[Dict[str, Any]]:
        """Test scenarios for notification testing"""
        return [
            {
                'scenario': 'daily_outlook_notification',
                'notification_type': 'daily_outlook_ready',
                'user_id': 123,
                'outlook_id': 456,
                'message': 'Your daily outlook is ready!',
                'priority': 'medium',
                'delivery_method': 'push'
            },
            {
                'scenario': 'streak_milestone_notification',
                'notification_type': 'streak_milestone',
                'user_id': 123,
                'streak_count': 7,
                'message': '🎉 7-day streak! You\'re on fire!',
                'priority': 'high',
                'delivery_method': 'push'
            },
            {
                'scenario': 'action_reminder_notification',
                'notification_type': 'action_reminder',
                'user_id': 123,
                'action_id': 'action_1',
                'message': 'Don\'t forget to complete your daily action!',
                'priority': 'low',
                'delivery_method': 'email'
            }
        ]
    
    # ============================================================================
    # ANALYTICS TEST DATA
    # ============================================================================
    
    @staticmethod
    def analytics_test_data() -> List[Dict[str, Any]]:
        """Test data for analytics testing"""
        return [
            {
                'event_type': 'daily_outlook_loaded',
                'user_id': 123,
                'user_tier': 'budget',
                'balance_score': 75,
                'streak_count': 5,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'load_time': 0.5,
                    'cache_hit': True,
                    'device_type': 'mobile'
                }
            },
            {
                'event_type': 'action_completed',
                'user_id': 123,
                'action_id': 'action_1',
                'completion_status': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'completion_time': 0.2,
                    'action_priority': 'high'
                }
            },
            {
                'event_type': 'rating_submitted',
                'user_id': 123,
                'rating': 5,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'rating_context': 'daily_outlook',
                    'user_satisfaction': 'high'
                }
            }
        ]
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    @staticmethod
    def get_all_personas() -> List[Dict[str, Any]]:
        """Get all persona test data"""
        return [
            DailyOutlookTestFixtures.maya_persona_data(),
            DailyOutlookTestFixtures.marcus_persona_data(),
            DailyOutlookTestFixtures.dr_williams_persona_data()
        ]
    
    @staticmethod
    def get_tier_scenarios() -> List[Dict[str, Any]]:
        """Get all tier-specific scenarios"""
        return (
            DailyOutlookTestFixtures.budget_tier_scenarios() +
            DailyOutlookTestFixtures.mid_tier_scenarios() +
            DailyOutlookTestFixtures.professional_tier_scenarios()
        )
    
    @staticmethod
    def get_relationship_scenarios() -> List[Dict[str, Any]]:
        """Get all relationship status scenarios"""
        return DailyOutlookTestFixtures.relationship_status_scenarios()
    
    @staticmethod
    def get_streak_scenarios() -> List[Dict[str, Any]]:
        """Get all streak milestone scenarios"""
        return DailyOutlookTestFixtures.streak_milestone_scenarios()
    
    @staticmethod
    def get_error_scenarios() -> List[Dict[str, Any]]:
        """Get all error scenarios"""
        return DailyOutlookTestFixtures.error_scenarios()
    
    @staticmethod
    def get_security_payloads() -> List[Dict[str, Any]]:
        """Get all security test payloads"""
        return DailyOutlookTestFixtures.security_test_payloads()
    
    @staticmethod
    def get_performance_scenarios() -> List[Dict[str, Any]]:
        """Get all performance test scenarios"""
        return DailyOutlookTestFixtures.performance_test_scenarios()
    
    @staticmethod
    def export_to_json(filename: str) -> None:
        """Export all test data to JSON file"""
        all_data = {
            'personas': DailyOutlookTestFixtures.get_all_personas(),
            'tier_scenarios': DailyOutlookTestFixtures.get_tier_scenarios(),
            'relationship_scenarios': DailyOutlookTestFixtures.get_relationship_scenarios(),
            'streak_scenarios': DailyOutlookTestFixtures.get_streak_scenarios(),
            'error_scenarios': DailyOutlookTestFixtures.get_error_scenarios(),
            'security_payloads': DailyOutlookTestFixtures.get_security_payloads(),
            'performance_scenarios': DailyOutlookTestFixtures.get_performance_scenarios(),
            'cache_scenarios': DailyOutlookTestFixtures.cache_test_scenarios(),
            'notification_scenarios': DailyOutlookTestFixtures.notification_test_scenarios(),
            'analytics_data': DailyOutlookTestFixtures.analytics_test_data()
        }
        
        with open(filename, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

class TestDataGenerator:
    """Generate test data for specific scenarios"""
    
    @staticmethod
    def generate_user_data(tier: str, relationship_status: str, age: int) -> Dict[str, Any]:
        """Generate user data for specific tier and relationship status"""
        base_data = {
            'tier': tier,
            'relationship_status': relationship_status,
            'age': age
        }
        
        if tier == 'budget':
            base_data.update({
                'income': 35000 + (age - 20) * 2000,
                'financial_goals': ['Build emergency fund', 'Pay off debt']
            })
        elif tier == 'mid_tier':
            base_data.update({
                'income': 55000 + (age - 25) * 3000,
                'financial_goals': ['Maximize 401k', 'Save for house']
            })
        elif tier == 'professional':
            base_data.update({
                'income': 80000 + (age - 30) * 5000,
                'financial_goals': ['Maximize retirement', 'College fund', 'Real estate']
            })
        
        return base_data
    
    @staticmethod
    def generate_outlook_data(user_data: Dict[str, Any], streak_count: int) -> Dict[str, Any]:
        """Generate outlook data based on user data and streak count"""
        # Calculate weights based on relationship status
        if user_data['relationship_status'] == 'single_career_focused':
            weights = {'career_weight': 0.30, 'financial_weight': 0.35, 'relationship_weight': 0.15, 'wellness_weight': 0.20}
        elif user_data['relationship_status'] == 'dating':
            weights = {'career_weight': 0.20, 'financial_weight': 0.30, 'relationship_weight': 0.30, 'wellness_weight': 0.20}
        elif user_data['relationship_status'] == 'married':
            weights = {'career_weight': 0.20, 'financial_weight': 0.25, 'relationship_weight': 0.25, 'wellness_weight': 0.30}
        else:
            weights = {'career_weight': 0.25, 'financial_weight': 0.30, 'relationship_weight': 0.25, 'wellness_weight': 0.20}
        
        # Calculate balance score based on tier and streak
        base_score = 60 if user_data['tier'] == 'budget' else 70 if user_data['tier'] == 'mid_tier' else 80
        streak_bonus = min(streak_count * 2, 20)
        balance_score = min(base_score + streak_bonus, 100)
        
        return {
            'balance_score': balance_score,
            **weights,
            'streak_count': streak_count,
            'milestone_reached': streak_count in [3, 7, 14, 30, 100],
            'next_milestone': 3 if streak_count < 3 else 7 if streak_count < 7 else 14 if streak_count < 14 else 30 if streak_count < 30 else 365,
            'progress_percentage': min((streak_count / 30) * 100, 100)
        }
    
    @staticmethod
    def generate_quick_actions(user_data: Dict[str, Any], outlook_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate quick actions based on user data and outlook data"""
        actions = []
        
        # Financial actions based on tier
        if user_data['tier'] == 'budget':
            actions.append({
                'id': 'budget_1',
                'title': 'Review monthly budget',
                'description': 'Track expenses and income',
                'priority': 'high',
                'estimated_time': '15 min'
            })
        elif user_data['tier'] == 'mid_tier':
            actions.append({
                'id': 'investment_1',
                'title': 'Review 401k contributions',
                'description': 'Optimize retirement savings',
                'priority': 'high',
                'estimated_time': '20 min'
            })
        elif user_data['tier'] == 'professional':
            actions.append({
                'id': 'retirement_1',
                'title': 'Review retirement portfolio',
                'description': 'Optimize asset allocation',
                'priority': 'high',
                'estimated_time': '30 min'
            })
        
        # Relationship actions based on status
        if user_data['relationship_status'] == 'dating':
            actions.append({
                'id': 'relationship_1',
                'title': 'Plan date night',
                'description': 'Budget for special evening',
                'priority': 'high',
                'estimated_time': '30 min'
            })
        elif user_data['relationship_status'] == 'married':
            actions.append({
                'id': 'family_1',
                'title': 'Plan family activities',
                'description': 'Budget for family time',
                'priority': 'high',
                'estimated_time': '45 min'
            })
        
        # Wellness actions
        actions.append({
            'id': 'wellness_1',
            'title': 'Take a wellness break',
            'description': 'Focus on mental health',
            'priority': 'medium',
            'estimated_time': '10 min'
        })
        
        return actions


if __name__ == '__main__':
    # Export all test data to JSON
    fixtures = DailyOutlookTestFixtures()
    fixtures.export_to_json('daily_outlook_test_data.json')
    print("Test data exported to daily_outlook_test_data.json")
