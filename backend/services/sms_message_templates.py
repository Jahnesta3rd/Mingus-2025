import logging
import json
import redis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid
import os

logger = logging.getLogger(__name__)

class MessageCategory(Enum):
    """SMS message categories"""
    CRITICAL_ALERT = "critical_alert"
    ENGAGEMENT_CHECKIN = "engagement_checkin"
    BILL_REMINDER = "bill_reminder"
    GOAL_CELEBRATION = "goal_celebration"
    WEALTH_BUILDING = "wealth_building"
    COMMUNITY_EVENT = "community_event"

class MessageTone(Enum):
    """Message tone variations for A/B testing"""
    SUPPORTIVE = "supportive"
    MOTIVATIONAL = "motivational"
    DIRECT = "direct"
    COMMUNITY_FOCUSED = "community_focused"
    FAMILY_ORIENTED = "family_oriented"

@dataclass
class SMSTemplate:
    """SMS template configuration"""
    template_id: str
    category: MessageCategory
    tone: MessageTone
    message_template: str
    variables: List[str] = field(default_factory=list)
    max_length: int = 160
    priority: int = 1
    cultural_elements: List[str] = field(default_factory=list)
    target_demographic: List[str] = field(default_factory=list)
    a_b_test_group: str = "control"

@dataclass
class MessageVariation:
    """Message variation for A/B testing"""
    variation_id: str
    template_id: str
    message_template: str
    tone: MessageTone
    cultural_elements: List[str]
    test_group: str  # A, B, C, etc.

class MINGUSSMSMessageTemplates:
    """SMS message templates for MINGUS financial app"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
        
        # Regional cultural references
        self.regional_context = {
            'atlanta': {
                'city_name': 'Atlanta',
                'cultural_refs': ['ATL', 'Black Wall Street', 'HBCU', 'civil rights'],
                'cost_of_living': 'moderate',
                'community_focus': 'entrepreneurship'
            },
            'houston': {
                'city_name': 'Houston',
                'cultural_refs': ['H-Town', 'energy capital', 'diversity', 'space city'],
                'cost_of_living': 'affordable',
                'community_focus': 'energy_industry'
            },
            'dc_metro': {
                'city_name': 'DC Metro',
                'cultural_refs': ['DMV', 'government', 'Howard University', 'policy'],
                'cost_of_living': 'high',
                'community_focus': 'government_careers'
            },
            'new_york': {
                'city_name': 'New York',
                'cultural_refs': ['NYC', 'Brooklyn', 'Harlem', 'Wall Street'],
                'cost_of_living': 'very_high',
                'community_focus': 'finance_careers'
            },
            'los_angeles': {
                'city_name': 'Los Angeles',
                'cultural_refs': ['LA', 'Hollywood', 'South LA', 'entertainment'],
                'cost_of_living': 'high',
                'community_focus': 'entertainment_tech'
            },
            'chicago': {
                'city_name': 'Chicago',
                'cultural_refs': ['Chi-Town', 'South Side', 'business', 'Midwest'],
                'cost_of_living': 'moderate',
                'community_focus': 'business_careers'
            },
            'miami': {
                'city_name': 'Miami',
                'cultural_refs': ['MIA', 'Magic City', 'diversity', 'international'],
                'cost_of_living': 'moderate',
                'community_focus': 'international_business'
            },
            'dallas': {
                'city_name': 'Dallas',
                'cultural_refs': ['Big D', 'DFW', 'tech', 'energy'],
                'cost_of_living': 'affordable',
                'community_focus': 'tech_energy'
            }
        }
        
        # Initialize templates
        self._init_templates()
        self._init_ab_test_variations()
    
    def _init_templates(self):
        """Initialize SMS message templates"""
        self.templates = {
            # Critical Financial Alerts
            'low_balance_warning': SMSTemplate(
                template_id='low_balance_warning',
                category=MessageCategory.CRITICAL_ALERT,
                tone=MessageTone.SUPPORTIVE,
                message_template="⚠️ {first_name}, your balance is ${balance}. You'll go negative in {days} days. Let's protect your financial foundation. Reply HELP for support.",
                variables=['first_name', 'balance', 'days'],
                cultural_elements=['financial_foundation', 'support_network'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'overdraft_risk': SMSTemplate(
                template_id='overdraft_risk',
                category=MessageCategory.CRITICAL_ALERT,
                tone=MessageTone.DIRECT,
                message_template="🚨 {first_name}, overdraft risk: ${amount} needed by {date}. Transfer funds now to avoid fees. Your future self will thank you.",
                variables=['first_name', 'amount', 'date'],
                cultural_elements=['future_self', 'avoiding_fees'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'payment_failure': SMSTemplate(
                template_id='payment_failure',
                category=MessageCategory.CRITICAL_ALERT,
                tone=MessageTone.SUPPORTIVE,
                message_template="💳 {first_name}, your {payment_type} payment failed. Update payment method to keep building your wealth. Call {support_phone} for help.",
                variables=['first_name', 'payment_type', 'support_phone'],
                cultural_elements=['wealth_building', 'support_network'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'security_alert': SMSTemplate(
                template_id='security_alert',
                category=MessageCategory.CRITICAL_ALERT,
                tone=MessageTone.DIRECT,
                message_template="🔒 {first_name}, unusual activity on your account. Protect your financial legacy. Review transactions at mingusapp.com/security",
                variables=['first_name'],
                cultural_elements=['financial_legacy', 'protection'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            # Engagement & Check-ins
            'weekly_wellness_checkin': SMSTemplate(
                template_id='weekly_wellness_checkin',
                category=MessageCategory.ENGAGEMENT_CHECKIN,
                tone=MessageTone.SUPPORTIVE,
                message_template="💪 {first_name}, how's your financial wellness? Reply 1-10 (1=stressed, 10=thriving). We're here to support your journey.",
                variables=['first_name'],
                cultural_elements=['wellness_journey', 'support_network'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'exercise_financial_benefits': SMSTemplate(
                template_id='exercise_financial_benefits',
                category=MessageCategory.ENGAGEMENT_CHECKIN,
                tone=MessageTone.MOTIVATIONAL,
                message_template="🏃‍♂️ {first_name}, did you know? Regular exercise can save you ${savings}/year in healthcare costs. Track your workout + boost your wealth!",
                variables=['first_name', 'savings'],
                cultural_elements=['health_wealth_connection', 'savings'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'relationship_financial_planning': SMSTemplate(
                template_id='relationship_financial_planning',
                category=MessageCategory.ENGAGEMENT_CHECKIN,
                tone=MessageTone.COMMUNITY_FOCUSED,
                message_template="❤️ {first_name}, healthy relationships + healthy finances = generational wealth. How's your financial communication with loved ones?",
                variables=['first_name'],
                cultural_elements=['generational_wealth', 'healthy_relationships'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'goal_milestone_celebration': SMSTemplate(
                template_id='goal_milestone_celebration',
                category=MessageCategory.GOAL_CELEBRATION,
                tone=MessageTone.MOTIVATIONAL,
                message_template="🎉 {first_name}! You've reached {milestone}! Your dedication to building wealth is inspiring. Keep pushing forward!",
                variables=['first_name', 'milestone'],
                cultural_elements=['dedication', 'inspiration', 'wealth_building'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            # Bill & Payment Reminders
            'student_loan_payment': SMSTemplate(
                template_id='student_loan_payment',
                category=MessageCategory.BILL_REMINDER,
                tone=MessageTone.SUPPORTIVE,
                message_template="🎓 {first_name}, your student loan payment of ${amount} is due in {days} days. Education is an investment in your future. Reply HELP for options.",
                variables=['first_name', 'amount', 'days'],
                cultural_elements=['education_investment', 'future_focus'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'subscription_renewal': SMSTemplate(
                template_id='subscription_renewal',
                category=MessageCategory.BILL_REMINDER,
                tone=MessageTone.DIRECT,
                message_template="📱 {first_name}, your {service} subscription renews in {days} days for ${amount}. Review at mingusapp.com/subscriptions",
                variables=['first_name', 'service', 'days', 'amount'],
                cultural_elements=['financial_review', 'conscious_spending'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'rent_mortgage_payment': SMSTemplate(
                template_id='rent_mortgage_payment',
                category=MessageCategory.BILL_REMINDER,
                tone=MessageTone.COMMUNITY_FOCUSED,
                message_template="🏠 {first_name}, your {payment_type} payment of ${amount} is due in {days} days. Building your foundation in {city}. Set up autopay?",
                variables=['first_name', 'payment_type', 'amount', 'days', 'city'],
                cultural_elements=['foundation_building', 'community_connection'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'credit_card_payment': SMSTemplate(
                template_id='credit_card_payment',
                category=MessageCategory.BILL_REMINDER,
                tone=MessageTone.SUPPORTIVE,
                message_template="💳 {first_name}, credit card payment of ${amount} due in {days} days. Avoid fees, build credit, build wealth. You've got this!",
                variables=['first_name', 'amount', 'days'],
                cultural_elements=['credit_building', 'wealth_building', 'encouragement'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            # Wealth Building Messages
            'investment_opportunity': SMSTemplate(
                template_id='investment_opportunity',
                category=MessageCategory.WEALTH_BUILDING,
                tone=MessageTone.MOTIVATIONAL,
                message_template="📈 {first_name}, new investment opportunity for Black professionals. Build generational wealth. Learn more: mingusapp.com/invest",
                variables=['first_name'],
                cultural_elements=['generational_wealth', 'black_professionals'],
                target_demographic=['25-35', '60k-100k']
            ),
            
            'emergency_fund_reminder': SMSTemplate(
                template_id='emergency_fund_reminder',
                category=MessageCategory.WEALTH_BUILDING,
                tone=MessageTone.FAMILY_ORIENTED,
                message_template="🛡️ {first_name}, your emergency fund is at ${current} of ${target} goal. Protect your family's future. Every dollar counts!",
                variables=['first_name', 'current', 'target'],
                cultural_elements=['family_protection', 'future_focus'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'home_ownership_progress': SMSTemplate(
                template_id='home_ownership_progress',
                category=MessageCategory.WEALTH_BUILDING,
                tone=MessageTone.COMMUNITY_FOCUSED,
                message_template="🏡 {first_name}, you're ${amount} closer to homeownership! Building equity, building legacy. Keep pushing!",
                variables=['first_name', 'amount'],
                cultural_elements=['equity_building', 'legacy_creation'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            # Community Events
            'community_event': SMSTemplate(
                template_id='community_event',
                category=MessageCategory.COMMUNITY_EVENT,
                tone=MessageTone.COMMUNITY_FOCUSED,
                message_template="🤝 {first_name}, join our {event_type} event for Black professionals in {city}. Network, learn, grow. Register: mingusapp.com/events",
                variables=['first_name', 'event_type', 'city'],
                cultural_elements=['community_connection', 'professional_networking'],
                target_demographic=['25-35', '40k-100k']
            ),
            
            'financial_education': SMSTemplate(
                template_id='financial_education',
                category=MessageCategory.WEALTH_BUILDING,
                tone=MessageTone.SUPPORTIVE,
                message_template="🎓 {first_name}, new financial education content: {topic}. Knowledge is power, wealth is freedom. Read: mingusapp.com/learn",
                variables=['first_name', 'topic'],
                cultural_elements=['knowledge_power', 'wealth_freedom'],
                target_demographic=['25-35', '40k-100k']
            )
        }
    
    def _init_ab_test_variations(self):
        """Initialize A/B test variations for key templates"""
        self.ab_variations = {
            'low_balance_warning': [
                MessageVariation(
                    variation_id='low_balance_warning_A',
                    template_id='low_balance_warning',
                    message_template="⚠️ {first_name}, your balance is ${balance}. You'll go negative in {days} days. Let's protect your financial foundation. Reply HELP for support.",
                    tone=MessageTone.SUPPORTIVE,
                    cultural_elements=['financial_foundation', 'support_network'],
                    test_group='A'
                ),
                MessageVariation(
                    variation_id='low_balance_warning_B',
                    template_id='low_balance_warning',
                    message_template="🚨 {first_name}, ${balance} left. Negative in {days} days. Time to act! Transfer funds now to protect your wealth. Reply HELP.",
                    tone=MessageTone.DIRECT,
                    cultural_elements=['wealth_protection', 'action_oriented'],
                    test_group='B'
                ),
                MessageVariation(
                    variation_id='low_balance_warning_C',
                    template_id='low_balance_warning',
                    message_template="💪 {first_name}, you're ${balance} away from negative balance in {days} days. Your future self needs you to act now. Reply HELP.",
                    tone=MessageTone.MOTIVATIONAL,
                    cultural_elements=['future_self', 'self_empowerment'],
                    test_group='C'
                )
            ],
            
            'weekly_wellness_checkin': [
                MessageVariation(
                    variation_id='wellness_checkin_A',
                    template_id='weekly_wellness_checkin',
                    message_template="💪 {first_name}, how's your financial wellness? Reply 1-10 (1=stressed, 10=thriving). We're here to support your journey.",
                    tone=MessageTone.SUPPORTIVE,
                    cultural_elements=['wellness_journey', 'support_network'],
                    test_group='A'
                ),
                MessageVariation(
                    variation_id='wellness_checkin_B',
                    template_id='weekly_wellness_checkin',
                    message_template="🔥 {first_name}, financial wellness check! Rate your money mindset 1-10. Building wealth starts with mindset. Reply now!",
                    tone=MessageTone.MOTIVATIONAL,
                    cultural_elements=['money_mindset', 'wealth_building'],
                    test_group='B'
                ),
                MessageVariation(
                    variation_id='wellness_checkin_C',
                    template_id='weekly_wellness_checkin',
                    message_template="❤️ {first_name}, how's your financial health? 1-10 scale. Your community is here to support your success. Reply with your number.",
                    tone=MessageTone.COMMUNITY_FOCUSED,
                    cultural_elements=['community_support', 'financial_health'],
                    test_group='C'
                )
            ],
            
            'student_loan_payment': [
                MessageVariation(
                    variation_id='student_loan_A',
                    template_id='student_loan_payment',
                    message_template="🎓 {first_name}, your student loan payment of ${amount} is due in {days} days. Education is an investment in your future. Reply HELP for options.",
                    tone=MessageTone.SUPPORTIVE,
                    cultural_elements=['education_investment', 'future_focus'],
                    test_group='A'
                ),
                MessageVariation(
                    variation_id='student_loan_B',
                    template_id='student_loan_payment',
                    message_template="📚 {first_name}, student loan payment: ${amount} due in {days} days. Your degree is paying off! Reply HELP for repayment strategies.",
                    tone=MessageTone.MOTIVATIONAL,
                    cultural_elements=['degree_value', 'repayment_strategies'],
                    test_group='B'
                ),
                MessageVariation(
                    variation_id='student_loan_C',
                    template_id='student_loan_payment',
                    message_template="💡 {first_name}, ${amount} student loan payment due in {days} days. Knowledge is power, debt is temporary. Reply HELP for guidance.",
                    tone=MessageTone.DIRECT,
                    cultural_elements=['knowledge_power', 'debt_temporary'],
                    test_group='C'
                )
            ]
        }
    
    def get_message(self, template_id: str, variables: Dict[str, Any], 
                   user_profile: Dict[str, Any] = None, 
                   ab_test: bool = False) -> str:
        """
        Get formatted SMS message
        
        Args:
            template_id: Template ID
            variables: Template variables
            user_profile: User profile for personalization
            ab_test: Whether to use A/B testing
        
        Returns:
            Formatted SMS message
        """
        try:
            # Get template
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # A/B testing logic
            if ab_test and template_id in self.ab_variations:
                variation = self._get_ab_test_variation(template_id, user_profile)
                message_template = variation.message_template
                tone = variation.tone
                test_group = variation.test_group
            else:
                message_template = template.message_template
                tone = template.tone
                test_group = None
            
            # Personalize message
            personalized_vars = self._personalize_variables(variables, user_profile)
            
            # Format message
            message = message_template.format(**personalized_vars)
            
            # Ensure message length
            if len(message) > template.max_length:
                message = self._truncate_message(message, template.max_length)
            
            # Track A/B test if applicable
            if ab_test and test_group:
                self._track_ab_test(template_id, test_group, user_profile)
            
            return message
            
        except Exception as e:
            logger.error(f"Error getting message for template {template_id}: {e}")
            return f"Hi {variables.get('first_name', 'there')}, you have an important financial update. Check your MINGUS app for details."
    
    def _get_ab_test_variation(self, template_id: str, user_profile: Dict[str, Any]) -> MessageVariation:
        """Get A/B test variation for user"""
        variations = self.ab_variations.get(template_id, [])
        if not variations:
            return None
        
        # Use user ID to consistently assign test group
        user_id = user_profile.get('user_id', 'default')
        test_group_index = hash(user_id) % len(variations)
        return variations[test_group_index]
    
    def _personalize_variables(self, variables: Dict[str, Any], 
                             user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize variables based on user profile"""
        personalized = variables.copy()
        
        if user_profile:
            # Add regional context
            region = user_profile.get('regional_cost_of_living', 'atlanta')
            regional_context = self.regional_context.get(region, self.regional_context['atlanta'])
            
            # Replace generic city references
            if 'city' in personalized:
                personalized['city'] = regional_context['city_name']
            
            # Add cultural references based on region
            if region == 'atlanta' and 'community' in personalized:
                personalized['community'] = 'ATL community'
            elif region == 'dc_metro' and 'professional' in personalized:
                personalized['professional'] = 'DMV professional'
            
            # Add income-based personalization
            income_range = user_profile.get('income_range', '40k-60k')
            if income_range == '80k-100k':
                personalized['wealth_focus'] = 'wealth preservation'
            elif income_range == '60k-80k':
                personalized['wealth_focus'] = 'wealth building'
            else:
                personalized['wealth_focus'] = 'financial foundation'
        
        return personalized
    
    def _truncate_message(self, message: str, max_length: int) -> str:
        """Truncate message to fit SMS length limit"""
        if len(message) <= max_length:
            return message
        
        # Try to truncate at word boundary
        truncated = message[:max_length-3] + "..."
        
        # Find last complete word
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we can find a good break point
            truncated = truncated[:last_space] + "..."
        
        return truncated
    
    def _track_ab_test(self, template_id: str, test_group: str, user_profile: Dict[str, Any]):
        """Track A/B test assignment"""
        try:
            user_id = user_profile.get('user_id', 'unknown')
            tracking_data = {
                'template_id': template_id,
                'test_group': test_group,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'user_demographics': {
                    'age_range': user_profile.get('age_range'),
                    'income_range': user_profile.get('income_range'),
                    'region': user_profile.get('regional_cost_of_living')
                }
            }
            
            # Store in Redis
            tracking_key = f"ab_test:{template_id}:{user_id}"
            self.redis_client.setex(tracking_key, 86400 * 30, json.dumps(tracking_data))  # 30 days
            
            # Track assignment count
            count_key = f"ab_test_count:{template_id}:{test_group}"
            self.redis_client.incr(count_key)
            
        except Exception as e:
            logger.error(f"Error tracking A/B test: {e}")
    
    def track_message_response(self, template_id: str, test_group: str, 
                             user_id: str, response_type: str, response_data: Dict[str, Any] = None):
        """
        Track message response for A/B testing
        
        Args:
            template_id: Template ID
            test_group: A/B test group (A, B, C, etc.)
            user_id: User ID
            response_type: Type of response (click, reply, action, etc.)
            response_data: Additional response data
        """
        try:
            tracking_data = {
                'template_id': template_id,
                'test_group': test_group,
                'user_id': user_id,
                'response_type': response_type,
                'response_data': response_data or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store response
            response_key = f"ab_test_response:{template_id}:{user_id}"
            self.redis_client.setex(response_key, 86400 * 30, json.dumps(tracking_data))
            
            # Track response count
            response_count_key = f"ab_test_response_count:{template_id}:{test_group}:{response_type}"
            self.redis_client.incr(response_count_key)
            
        except Exception as e:
            logger.error(f"Error tracking message response: {e}")
    
    def get_ab_test_results(self, template_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get A/B test results for a template
        
        Args:
            template_id: Template ID
            days: Number of days to analyze
        
        Returns:
            A/B test results
        """
        try:
            results = {
                'template_id': template_id,
                'test_groups': {},
                'total_sent': 0,
                'total_responses': 0,
                'best_performing': None
            }
            
            # Get all test groups for this template
            if template_id in self.ab_variations:
                test_groups = [v.test_group for v in self.ab_variations[template_id]]
            else:
                return results
            
            for test_group in test_groups:
                # Get sent count
                sent_key = f"ab_test_count:{template_id}:{test_group}"
                sent_count = int(self.redis_client.get(sent_key) or 0)
                
                # Get response counts
                response_types = ['click', 'reply', 'action', 'conversion']
                response_counts = {}
                total_responses = 0
                
                for response_type in response_types:
                    response_key = f"ab_test_response_count:{template_id}:{test_group}:{response_type}"
                    count = int(self.redis_client.get(response_key) or 0)
                    response_counts[response_type] = count
                    total_responses += count
                
                # Calculate response rate
                response_rate = (total_responses / sent_count * 100) if sent_count > 0 else 0
                
                results['test_groups'][test_group] = {
                    'sent_count': sent_count,
                    'response_counts': response_counts,
                    'total_responses': total_responses,
                    'response_rate': response_rate
                }
                
                results['total_sent'] += sent_count
                results['total_responses'] += total_responses
            
            # Find best performing group
            best_rate = 0
            for test_group, data in results['test_groups'].items():
                if data['response_rate'] > best_rate:
                    best_rate = data['response_rate']
                    results['best_performing'] = test_group
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting A/B test results: {e}")
            return {'error': str(e)}
    
    def get_cultural_message_suggestions(self, user_profile: Dict[str, Any]) -> List[str]:
        """
        Get cultural message suggestions based on user profile
        
        Args:
            user_profile: User profile data
        
        Returns:
            List of cultural message suggestions
        """
        suggestions = []
        
        try:
            region = user_profile.get('regional_cost_of_living', 'atlanta')
            income_range = user_profile.get('income_range', '40k-60k')
            age_range = user_profile.get('age_range', '25-35')
            
            # Regional suggestions
            regional_context = self.regional_context.get(region, {})
            if region == 'atlanta':
                suggestions.append("Connect with ATL's Black business community")
                suggestions.append("Leverage HBCU network for career advancement")
            elif region == 'dc_metro':
                suggestions.append("Explore government career opportunities")
                suggestions.append("Network with DMV professionals")
            elif region == 'new_york':
                suggestions.append("Access Wall Street investment opportunities")
                suggestions.append("Connect with NYC finance professionals")
            
            # Income-based suggestions
            if income_range == '80k-100k':
                suggestions.append("Focus on wealth preservation strategies")
                suggestions.append("Consider legacy planning for generational wealth")
            elif income_range == '60k-80k':
                suggestions.append("Build investment portfolio for wealth growth")
                suggestions.append("Explore homeownership opportunities")
            else:
                suggestions.append("Build emergency fund foundation")
                suggestions.append("Focus on debt management and savings")
            
            # Age-based suggestions
            if age_range == '25-35':
                suggestions.append("Invest in career development and networking")
                suggestions.append("Start building generational wealth early")
                suggestions.append("Balance family obligations with financial goals")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting cultural suggestions: {e}")
            return ["Focus on building wealth while maintaining healthy relationships"]

# Create singleton instance
sms_message_templates = MINGUSSMSMessageTemplates() 