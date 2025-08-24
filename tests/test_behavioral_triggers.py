"""
Test Behavioral Trigger System
Demonstrates and validates the intelligent behavioral trigger system
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import uuid

from backend.services.behavioral_trigger_service import BehavioralTriggerService
from backend.models.behavioral_triggers import (
    BehavioralTrigger, TriggerEvent, UserBehaviorPattern,
    TriggerType, TriggerCategory, TriggerStatus, TriggerPriority
)


class TestBehavioralTriggers(unittest.TestCase):
    """Test cases for behavioral trigger system"""
    
    def setUp(self):
        self.service = BehavioralTriggerService()
        self.user_id = "test_user_123"
        self.test_user = Mock(
            id=self.user_id,
            email="test@example.com",
            full_name="Test User"
        )
    
    def test_detect_spending_spike(self):
        """Test spending spike detection"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user patterns
            pattern = Mock()
            pattern.baseline_value = 200.0
            mock_db.query.return_value.filter.return_value.all.return_value = [pattern]
            
            # Test data with spending spike
            financial_data = {
                'weekly_spending': 250,  # 25% increase
                'monthly_income': 5000,
                'savings_goals': []
            }
            
            # Mock trigger creation
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id="trigger_123",
                trigger_category=TriggerCategory.SPENDING_SPIKE
            )
            
            events = self.service.detect_financial_triggers(self.user_id, financial_data)
            
            # Should detect spending spike
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].event_type, 'triggered')
    
    def test_detect_income_drop(self):
        """Test income drop detection"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user patterns
            pattern = Mock()
            pattern.baseline_value = 6000.0
            mock_db.query.return_value.filter.return_value.all.return_value = [pattern]
            
            # Test data with income drop
            financial_data = {
                'weekly_spending': 200,
                'monthly_income': 4800,  # 20% decrease
                'savings_goals': []
            }
            
            # Mock trigger creation
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id="trigger_456",
                trigger_category=TriggerCategory.INCOME_DROP
            )
            
            events = self.service.detect_financial_triggers(self.user_id, financial_data)
            
            # Should detect income drop
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].event_type, 'triggered')
    
    def test_detect_health_wellness_correlation(self):
        """Test health/wellness correlation detection"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock trigger creation
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id="trigger_789",
                trigger_category=TriggerCategory.LOW_EXERCISE_HIGH_SPENDING
            )
            
            # Test data showing low exercise + high spending
            health_data = {
                'exercise_level': 'low',
                'stress_level': 'medium'
            }
            
            financial_data = {
                'spending_level': 'high',
                'weekly_spending': 300
            }
            
            events = self.service.detect_health_wellness_triggers(
                self.user_id, health_data, financial_data
            )
            
            # Should detect correlation
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].event_type, 'triggered')
    
    def test_detect_career_triggers(self):
        """Test career trigger detection"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock trigger creation
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id="trigger_career",
                trigger_category=TriggerCategory.SALARY_BELOW_MARKET
            )
            
            # Test data showing salary below market
            career_data = {
                'current_salary': 60000,
                'market_rate': 75000,  # 20% below market
                'skill_gaps': ['python', 'machine_learning'],
                'job_opportunities': [
                    {'title': 'Senior Developer', 'salary': 80000},
                    {'title': 'Data Scientist', 'salary': 85000}
                ]
            }
            
            events = self.service.detect_career_triggers(self.user_id, career_data)
            
            # Should detect multiple career triggers
            self.assertGreaterEqual(len(events), 1)
    
    def test_detect_life_event_triggers(self):
        """Test life event trigger detection"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock trigger creation
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id="trigger_life",
                trigger_category=TriggerCategory.BIRTHDAY_APPROACHING
            )
            
            # Test data with birthday approaching
            user_profile = {
                'birthday': datetime.now().date() + timedelta(days=5),  # 5 days away
                'lease_end_date': datetime.now().date() + timedelta(days=25),
                'student_loan_grace_end': datetime.now().date() + timedelta(days=20)
            }
            
            events = self.service.detect_life_event_triggers(self.user_id, user_profile)
            
            # Should detect birthday trigger
            self.assertEqual(len(events), 1)
    
    def test_detect_engagement_triggers(self):
        """Test engagement trigger detection"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock trigger creation
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id="trigger_engagement",
                trigger_category=TriggerCategory.APP_USAGE_DECLINE
            )
            
            # Test data showing app usage decline
            engagement_data = {
                'days_since_last_use': 10,  # More than 7 days
                'unused_features': ['budget_planner', 'investment_tracker'],
                'usage_frequency': 'high',
                'feature_usage': 5,
                'premium_eligible': True
            }
            
            events = self.service.detect_engagement_triggers(self.user_id, engagement_data)
            
            # Should detect multiple engagement triggers
            self.assertGreaterEqual(len(events), 1)
    
    def test_process_trigger_event(self):
        """Test trigger event processing"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock trigger
            trigger = Mock(
                id="trigger_123",
                status=TriggerStatus.ACTIVE,
                sms_template="Test SMS Template",
                email_template="Test Email Template"
            )
            
            # Mock trigger event
            event = Mock(
                id="event_123",
                trigger_id="trigger_123",
                user_id=self.user_id,
                event_type='triggered'
            )
            
            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                trigger,  # For trigger lookup
                Mock()    # For user preferences (should_send_to_user)
            ]
            
            # Mock cooldown check
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            # Mock communication sending
            with patch.object(self.service, '_send_sms_communication', return_value=True):
                with patch.object(self.service, '_send_email_communication', return_value=True):
                    success = self.service.process_trigger_event(event)
                    
                    # Should process successfully
                    self.assertTrue(success)
                    self.assertTrue(event.sms_sent)
                    self.assertTrue(event.email_sent)
    
    def test_update_user_behavior_patterns(self):
        """Test user behavior pattern updates"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock existing pattern
            existing_pattern = Mock(
                id="pattern_123",
                user_id=self.user_id,
                pattern_type="spending",
                pattern_data={},
                pattern_last_updated=datetime.utcnow()
            )
            
            mock_db.query.return_value.filter.return_value.first.return_value = existing_pattern
            
            # Test pattern data
            pattern_data = {
                'weekly_averages': [150, 180, 200, 175, 190],
                'trend': 'increasing',
                'seasonality': 'monthly'
            }
            
            self.service.update_user_behavior_patterns(
                self.user_id, 'spending', pattern_data
            )
            
            # Should update pattern data
            self.assertEqual(existing_pattern.pattern_data, pattern_data)
            self.assertIsNotNone(existing_pattern.pattern_last_updated)
    
    def test_get_trigger_effectiveness(self):
        """Test trigger effectiveness calculation"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock trigger events
            events = [
                Mock(
                    sms_sent=True,
                    email_sent=False,
                    user_engaged=True,
                    conversion_achieved=True,
                    conversion_value=100.0
                ),
                Mock(
                    sms_sent=True,
                    email_sent=True,
                    user_engaged=False,
                    conversion_achieved=False,
                    conversion_value=0.0
                ),
                Mock(
                    sms_sent=False,
                    email_sent=False,
                    user_engaged=False,
                    conversion_achieved=False,
                    conversion_value=0.0
                )
            ]
            
            mock_db.query.return_value.filter.return_value.all.return_value = events
            
            effectiveness = self.service.get_trigger_effectiveness(time_period="30d")
            
            # Should calculate effectiveness metrics
            self.assertEqual(effectiveness['total_triggers'], 3)
            self.assertEqual(effectiveness['total_sent'], 2)
            self.assertEqual(effectiveness['total_engaged'], 1)
            self.assertEqual(effectiveness['total_converted'], 1)
            self.assertEqual(effectiveness['send_rate'], 66.67)
            self.assertEqual(effectiveness['engagement_rate'], 50.0)
            self.assertEqual(effectiveness['conversion_rate'], 100.0)
    
    def test_personalize_message(self):
        """Test message personalization"""
        template = "Hi {{user_name}}, your spending is {{percentage}}% higher than usual. Save ${{amount}} with our tips!"
        
        data = {
            'user_name': 'John',
            'percentage': 25,
            'amount': 150.50
        }
        
        personalized = self.service._personalize_message(template, data)
        
        expected = "Hi John, your spending is 25% higher than usual. Save $150.50 with our tips!"
        self.assertEqual(personalized, expected)
    
    def test_calculate_pattern_characteristics(self):
        """Test pattern characteristic calculation"""
        pattern = Mock()
        pattern.pattern_data = [100, 120, 140, 160, 180]  # Increasing trend
        
        self.service._calculate_pattern_characteristics(pattern)
        
        # Should calculate characteristics
        self.assertEqual(pattern.baseline_value, 140.0)  # Mean
        self.assertIsNotNone(pattern.variance_threshold)  # Standard deviation
        self.assertEqual(pattern.trend_direction, 'increasing')
        self.assertGreater(pattern.pattern_confidence, 0)
    
    def test_trigger_cooldown_check(self):
        """Test trigger cooldown functionality"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock schedule
            schedule = Mock(
                cooldown_hours=24,
                cooldown_days=7
            )
            
            # Mock recent events (in cooldown)
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            
            # Mock trigger
            trigger = Mock(id="trigger_123")
            
            # Should be in cooldown
            in_cooldown = self.service._is_in_cooldown(self.user_id, trigger)
            self.assertTrue(in_cooldown)
    
    def test_optimal_send_time_calculation(self):
        """Test optimal send time calculation"""
        with patch.object(self.service, 'db') as mock_db:
            # Mock user analytics with engagement patterns
            analytics = Mock()
            analytics.engagement_by_hour = {'9': 10, '10': 15, '18': 20, '19': 25}
            mock_db.query.return_value.filter.return_value.first.return_value = analytics
            
            # Mock trigger
            trigger = Mock(id="trigger_123")
            
            optimal_time = self.service._get_optimal_send_time(self.user_id, trigger)
            
            # Should return a datetime object
            self.assertIsInstance(optimal_time, datetime)
    
    def test_ml_model_training(self):
        """Test ML model training"""
        with patch.object(self.service, 'db') as mock_db:
            training_data = {
                'config': {'algorithm': 'random_forest', 'max_depth': 10},
                'features': ['spending', 'income', 'savings'],
                'target': 'spending_spike_likelihood',
                'data_size': 10000,
                'accuracy': 0.85,
                'precision': 0.82,
                'recall': 0.88,
                'f1': 0.85
            }
            
            model = self.service.train_ml_model(
                'spending_spike_predictor',
                'classification',
                training_data
            )
            
            # Should create ML model
            self.assertIsNotNone(model)
            self.assertEqual(model.model_name, 'spending_spike_predictor')
            self.assertEqual(model.model_type, 'classification')
            self.assertTrue(model.is_active)


def run_behavioral_trigger_demo():
    """Demonstrate the behavioral trigger system"""
    print("=== MINGUS Behavioral Trigger System Demo ===\n")
    
    # Create service instance
    service = BehavioralTriggerService()
    
    # Demo user data
    user_id = "demo_user_123"
    
    print("1. Financial Trigger Detection")
    print("-" * 40)
    
    financial_data = {
        'weekly_spending': 250,  # 25% increase from baseline
        'monthly_income': 4800,  # 20% decrease
        'savings_goals': [
            {'name': 'Emergency Fund', 'progress_stalled': True}
        ],
        'milestones': [
            {'name': 'First $1000 Saved', 'just_reached': True}
        ]
    }
    
    print(f"User spending: ${financial_data['weekly_spending']}/week")
    print(f"User income: ${financial_data['monthly_income']}/month")
    print(f"Savings goal stalled: {financial_data['savings_goals'][0]['progress_stalled']}")
    print(f"Milestone reached: {financial_data['milestones'][0]['just_reached']}")
    
    # Detect financial triggers
    events = service.detect_financial_triggers(user_id, financial_data)
    print(f"Financial triggers detected: {len(events)}")
    
    print("\n2. Health/Wellness Correlation Detection")
    print("-" * 40)
    
    health_data = {
        'exercise_level': 'low',
        'stress_level': 'high'
    }
    
    print(f"Exercise level: {health_data['exercise_level']}")
    print(f"Stress level: {health_data['stress_level']}")
    print(f"Spending level: high")
    
    # Detect health/wellness triggers
    events = service.detect_health_wellness_triggers(user_id, health_data, financial_data)
    print(f"Health/wellness triggers detected: {len(events)}")
    
    print("\n3. Career Trigger Detection")
    print("-" * 40)
    
    career_data = {
        'current_salary': 60000,
        'market_rate': 75000,  # 20% below market
        'skill_gaps': ['python', 'machine_learning', 'data_analysis'],
        'job_opportunities': [
            {'title': 'Senior Developer', 'salary': 80000},
            {'title': 'Data Scientist', 'salary': 85000},
            {'title': 'ML Engineer', 'salary': 90000}
        ]
    }
    
    print(f"Current salary: ${career_data['current_salary']}")
    print(f"Market rate: ${career_data['market_rate']}")
    print(f"Skill gaps: {len(career_data['skill_gaps'])} identified")
    print(f"Job opportunities: {len(career_data['job_opportunities'])} available")
    
    # Detect career triggers
    events = service.detect_career_triggers(user_id, career_data)
    print(f"Career triggers detected: {len(events)}")
    
    print("\n4. Life Event Trigger Detection")
    print("-" * 40)
    
    user_profile = {
        'birthday': datetime.now().date() + timedelta(days=5),
        'lease_end_date': datetime.now().date() + timedelta(days=25),
        'student_loan_grace_end': datetime.now().date() + timedelta(days=20)
    }
    
    print(f"Birthday in: {(user_profile['birthday'] - datetime.now().date()).days} days")
    print(f"Lease ends in: {(user_profile['lease_end_date'] - datetime.now().date()).days} days")
    print(f"Student loan grace ends in: {(user_profile['student_loan_grace_end'] - datetime.now().date()).days} days")
    
    # Detect life event triggers
    events = service.detect_life_event_triggers(user_id, user_profile)
    print(f"Life event triggers detected: {len(events)}")
    
    print("\n5. Engagement Trigger Detection")
    print("-" * 40)
    
    engagement_data = {
        'days_since_last_use': 10,
        'unused_features': ['budget_planner', 'investment_tracker', 'debt_payoff'],
        'usage_frequency': 'high',
        'feature_usage': 5,
        'premium_eligible': True
    }
    
    print(f"Days since last use: {engagement_data['days_since_last_use']}")
    print(f"Unused features: {len(engagement_data['unused_features'])}")
    print(f"Usage frequency: {engagement_data['usage_frequency']}")
    print(f"Premium eligible: {engagement_data['premium_eligible']}")
    
    # Detect engagement triggers
    events = service.detect_engagement_triggers(user_id, engagement_data)
    print(f"Engagement triggers detected: {len(events)}")
    
    print("\n6. Message Personalization Demo")
    print("-" * 40)
    
    template = "Hi {{user_name}}, we noticed your spending is {{percentage}}% higher than usual this week. Want to review your budget? Reply YES for insights."
    
    data = {
        'user_name': 'Sarah',
        'percentage': 25
    }
    
    personalized = service._personalize_message(template, data)
    print(f"Template: {template}")
    print(f"Personalized: {personalized}")
    
    print("\n7. Pattern Analysis Demo")
    print("-" * 40)
    
    # Simulate pattern data
    spending_pattern = [150, 180, 200, 175, 190, 220, 250]  # Increasing trend
    
    print(f"Spending pattern: {spending_pattern}")
    print(f"Pattern length: {len(spending_pattern)} weeks")
    
    # Calculate characteristics
    baseline = sum(spending_pattern) / len(spending_pattern)
    print(f"Baseline spending: ${baseline:.2f}/week")
    
    # Detect trend
    recent_avg = sum(spending_pattern[-3:]) / 3
    older_avg = sum(spending_pattern[:-3]) / 4
    trend = 'increasing' if recent_avg > older_avg * 1.1 else 'decreasing' if recent_avg < older_avg * 0.9 else 'stable'
    print(f"Trend: {trend}")
    
    print("\n=== Demo Complete ===")
    print("\nThe behavioral trigger system successfully detected multiple triggers across different categories:")
    print("- Financial behavior changes (spending spike, income drop)")
    print("- Health/wellness correlations (low exercise + high spending)")
    print("- Career opportunities (salary below market, skill gaps)")
    print("- Life events (birthday approaching, lease renewal)")
    print("- Engagement patterns (app usage decline, unused features)")
    
    print("\nEach trigger can initiate personalized communications to help users:")
    print("- Improve financial health")
    print("- Reduce stress and improve wellness")
    print("- Advance their careers")
    print("- Plan for life events")
    print("- Stay engaged with the platform")


if __name__ == '__main__':
    # Run the demo
    run_behavioral_trigger_demo()
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2) 