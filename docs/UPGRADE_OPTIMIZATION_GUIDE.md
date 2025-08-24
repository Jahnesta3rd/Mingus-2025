# Upgrade Optimization Guide

## Overview

The Upgrade Optimization system provides comprehensive optimization features including smart trial reminder timing, usage-based upgrade prompts, social proof and testimonials, limited-time upgrade offers, and conversion funnel A/B testing to maximize conversion rates and user engagement.

## Feature Overview

### Purpose
- **Smart Trial Reminders**: Optimize trial reminder timing based on user behavior
- **Usage-Based Prompts**: Generate upgrade prompts based on feature usage patterns
- **Social Proof**: Provide personalized testimonials and success stories
- **Limited-Time Offers**: Create urgency with time-limited upgrade offers
- **A/B Testing**: Optimize conversion funnels through systematic testing

### Key Benefits
- **Increased Conversions**: Optimized timing and messaging improve conversion rates
- **Better User Experience**: Personalized and relevant upgrade prompts
- **Data-Driven Optimization**: A/B testing provides evidence-based improvements
- **Social Validation**: Testimonials and success stories build trust
- **Urgency Creation**: Limited-time offers drive immediate action

## Smart Trial Reminders

### Reminder Types

#### Trial Expiry Reminders
```python
class ReminderType(Enum):
    TRIAL_EXPIRY = "trial_expiry"           # Reminders before trial expires
    FEATURE_USAGE = "feature_usage"         # Based on feature usage patterns
    VALUE_DEMONSTRATION = "value_demonstration"  # Based on value shown
    ENGAGEMENT_DROP = "engagement_drop"     # When engagement decreases
    GOAL_ALIGNMENT = "goal_alignment"       # Based on goal alignment
```

#### Reminder Configuration
```python
trial_reminder_settings = {
    'trial_expiry_reminders': [24, 12, 6, 2, 1],  # hours before expiry
    'feature_usage_thresholds': {
        'low_usage': 0.3,
        'medium_usage': 0.6,
        'high_usage': 0.8
    },
    'engagement_drop_threshold': 0.5,
    'goal_alignment_threshold': 0.7,
    'max_reminders_per_trial': 5,
    'reminder_cooldown_hours': 6
}
```

#### Usage Example
```python
# Create trial expiry reminder
reminder = optimization_system.create_smart_trial_reminder(
    user_id, 'investment_analysis', ReminderType.TRIAL_EXPIRY,
    {
        'trial_end_time': datetime.now(timezone.utc) + timedelta(hours=24),
        'hours_before_expiry': 24
    }
)

print(f"Reminder Type: {reminder.reminder_type.value}")
print(f"Priority: {reminder.priority}")
print(f"Scheduled At: {reminder.scheduled_at}")
print(f"Message: {reminder.message_template}")
```

### Timing Optimization

#### Dynamic Timing Calculation
```python
def _calculate_reminder_timing(self, reminder_type: ReminderType, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Calculate optimal timing for trial reminder"""
    if reminder_type == ReminderType.TRIAL_EXPIRY:
        # Use predefined reminder schedule
        reminder_hours = self.config.trial_reminder_settings['trial_expiry_reminders']
        current_hour = reminder_hours[0]  # Start with 24 hours before expiry
        
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=current_hour)
        
        return {
            'reminder_hours': reminder_hours,
            'current_reminder': current_hour,
            'scheduled_time': scheduled_time,
            'next_reminder_hour': reminder_hours[1] if len(reminder_hours) > 1 else None
        }
    
    elif reminder_type == ReminderType.FEATURE_USAGE:
        # Calculate based on usage patterns
        usage_threshold = context.get('usage_threshold', 0.5)
        current_usage = context.get('current_usage', 0)
        
        if current_usage < usage_threshold:
            # Remind immediately for low usage
            scheduled_time = datetime.now(timezone.utc) + timedelta(hours=2)
        else:
            # Remind after some time for moderate usage
            scheduled_time = datetime.now(timezone.utc) + timedelta(hours=12)
        
        return {
            'usage_threshold': usage_threshold,
            'current_usage': current_usage,
            'scheduled_time': scheduled_time
        }
```

#### Priority Calculation
```python
def _calculate_reminder_priority(self, reminder_type: ReminderType, context: Dict[str, Any] = None) -> int:
    """Calculate reminder priority"""
    priority_scores = {
        ReminderType.TRIAL_EXPIRY: 10,
        ReminderType.VALUE_DEMONSTRATION: 8,
        ReminderType.ENGAGEMENT_DROP: 6,
        ReminderType.FEATURE_USAGE: 4,
        ReminderType.GOAL_ALIGNMENT: 3
    }
    
    base_priority = priority_scores.get(reminder_type, 1)
    
    # Adjust based on context
    if context:
        if context.get('high_value_user', False):
            base_priority += 2
        if context.get('engagement_drop', False):
            base_priority += 1
        if context.get('trial_expiring_soon', False):
            base_priority += 3
    
    return min(base_priority, 10)  # Max priority of 10
```

## Usage-Based Prompts

### Usage Analysis

#### Usage Pattern Analysis
```python
def _analyze_usage_patterns(self, feature_usage_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user usage patterns"""
    analysis = {
        'total_usage': 0,
        'feature_breakdown': {},
        'usage_frequency': 0,
        'usage_duration': 0,
        'usage_depth': 0,
        'value_demonstrated': 0
    }
    
    # Calculate total usage
    for feature, usage in feature_usage_data.get('features', {}).items():
        analysis['total_usage'] += usage.get('count', 0)
        analysis['feature_breakdown'][feature] = usage
    
    # Calculate usage frequency
    analysis['usage_frequency'] = analysis['total_usage'] / max(1, feature_usage_data.get('days_active', 1))
    
    # Calculate usage duration
    total_time = sum(usage.get('time_spent', 0) for usage in analysis['feature_breakdown'].values())
    analysis['usage_duration'] = total_time / 3600  # Convert to hours
    
    # Calculate usage depth
    features_used = len([f for f, u in analysis['feature_breakdown'].items() if u.get('count', 0) > 0])
    total_features = len(self.config.usage_based_prompts['feature_usage_thresholds'])
    analysis['usage_depth'] = features_used / max(1, total_features)
    
    # Calculate value demonstrated
    analysis['value_demonstrated'] = self._calculate_value_demonstrated(analysis)
    
    return analysis
```

#### Usage Thresholds
```python
usage_based_prompts = {
    'feature_usage_thresholds': {
        'budget_tracker': 5,
        'expense_categorizer': 3,
        'savings_goals': 2,
        'investment_analysis': 1,
        'retirement_planner': 1
    },
    'usage_pattern_weights': {
        'frequency': 0.4,
        'duration': 0.3,
        'depth': 0.3
    },
    'value_demonstration_threshold': 0.6,
    'confidence_score_threshold': 0.7
}
```

#### Usage Example
```python
# Generate usage-based prompt
feature_usage_data = {
    'features': {
        'budget_tracker': {'count': 8, 'time_spent': 4800},
        'expense_categorizer': {'count': 6, 'time_spent': 3600},
        'savings_goals': {'count': 5, 'time_spent': 3000}
    },
    'days_active': 14,
    'total_time_spent': 11400
}

prompt = optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)

if prompt:
    print(f"Trigger Feature: {prompt.trigger_feature}")
    print(f"Usage Threshold: {prompt.usage_threshold}")
    print(f"Value Demonstrated: {prompt.value_demonstrated:.1%}")
    print(f"Upgrade Recommendation: {prompt.upgrade_recommendation}")
    print(f"Confidence Score: {prompt.confidence_score:.1%}")
```

### Value Demonstration

#### Value Calculation
```python
def _calculate_value_demonstrated(self, usage_analysis: Dict[str, Any]) -> float:
    """Calculate value demonstrated through usage"""
    # Mock implementation - in production, use actual value calculation
    base_value = usage_analysis['total_usage'] * 10  # $10 per usage
    frequency_bonus = usage_analysis['usage_frequency'] * 50  # Bonus for frequent usage
    depth_bonus = usage_analysis['usage_depth'] * 100  # Bonus for using many features
    
    total_value = base_value + frequency_bonus + depth_bonus
    return min(total_value / 1000, 1.0)  # Normalize to 0-1
```

#### Confidence Scoring
```python
def _calculate_usage_confidence_score(self, usage_analysis: Dict[str, Any]) -> float:
    """Calculate confidence score for usage-based prompt"""
    weights = self.config.usage_based_prompts['usage_pattern_weights']
    
    confidence_score = (
        usage_analysis['usage_frequency'] * weights['frequency'] +
        usage_analysis['usage_duration'] * weights['duration'] +
        usage_analysis['usage_depth'] * weights['depth']
    )
    
    return min(confidence_score, 1.0)
```

## Social Proof and Testimonials

### Social Proof Types

#### Proof Categories
```python
class SocialProofType(Enum):
    TESTIMONIAL = "testimonial"                     # User testimonials
    CASE_STUDY = "case_study"                       # Detailed case studies
    SUCCESS_STORY = "success_story"                 # Success narratives
    USER_COUNT = "user_count"                       # User statistics
    SAVINGS_DEMONSTRATION = "savings_demonstration"  # Savings examples
    REVIEW = "review"                               # User reviews
```

#### Social Proof Configuration
```python
social_proof_settings = {
    'testimonial_categories': {
        'budget_tier': ['savings_success', 'debt_reduction', 'financial_education'],
        'mid_tier': ['investment_growth', 'retirement_planning', 'tax_savings'],
        'professional_tier': ['comprehensive_planning', 'estate_planning', 'wealth_preservation']
    },
    'relevance_score_threshold': 0.7,
    'conversion_rate_threshold': 0.05,
    'max_proofs_per_prompt': 3,
    'rotation_frequency_hours': 24
}
```

#### Social Proof Content
```python
social_proof_content = {
    'budget_tier': [
        SocialProof(
            proof_id=str(uuid.uuid4()),
            proof_type=SocialProofType.TESTIMONIAL,
            title="Saved $2,000 in 3 months!",
            content="I was struggling with my budget until I found MINGUS. The budget tracker helped me identify unnecessary expenses and I saved $2,000 in just 3 months!",
            author="Sarah M.",
            user_segment="budget_tier",
            relevance_score=0.9,
            conversion_rate=0.08,
            usage_count=0
        ),
        SocialProof(
            proof_id=str(uuid.uuid4()),
            proof_type=SocialProofType.SUCCESS_STORY,
            title="Finally debt-free!",
            content="After using MINGUS for 6 months, I paid off all my credit card debt. The debt management tools showed me exactly how to prioritize payments.",
            author="Mike R.",
            user_segment="budget_tier",
            relevance_score=0.85,
            conversion_rate=0.06,
            usage_count=0
        )
    ],
    'mid_tier': [
        SocialProof(
            proof_id=str(uuid.uuid4()),
            proof_type=SocialProofType.CASE_STUDY,
            title="Retired 5 years early!",
            content="The retirement planning tools helped me optimize my savings and investment strategy. I'm now on track to retire 5 years earlier than planned.",
            author="Jennifer L.",
            user_segment="mid_tier",
            relevance_score=0.95,
            conversion_rate=0.12,
            usage_count=0
        ),
        SocialProof(
            proof_id=str(uuid.uuid4()),
            proof_type=SocialProofType.SAVINGS_DEMONSTRATION,
            title="$15,000 in tax savings!",
            content="The tax optimization tools identified deductions I never knew about. I saved $15,000 on my taxes this year!",
            author="David K.",
            user_segment="mid_tier",
            relevance_score=0.88,
            conversion_rate=0.10,
            usage_count=0
        )
    ]
}
```

#### Usage Example
```python
# Get personalized social proof
social_proofs = optimization_system.get_social_proof(user_id, {
    'user_segment': 'mid_tier',
    'feature_interest': 'investment_planning',
    'goals': ['save_money', 'invest_for_future']
})

for proof in social_proofs:
    print(f"Title: {proof.title}")
    print(f"Content: {proof.content}")
    print(f"Author: {proof.author}")
    print(f"Relevance Score: {proof.relevance_score:.1%}")
    print(f"Conversion Rate: {proof.conversion_rate:.1%}")
```

## Limited-Time Offers

### Offer Types

#### Offer Categories
```python
class OfferType(Enum):
    PERCENTAGE_DISCOUNT = "percentage_discount"  # Percentage off
    FIXED_DISCOUNT = "fixed_discount"            # Fixed amount off
    FREE_MONTHS = "free_months"                  # Free months
    FEATURE_UPGRADE = "feature_upgrade"          # Feature upgrade
    BONUS_FEATURES = "bonus_features"            # Bonus features
    EARLY_ACCESS = "early_access"                # Early access
```

#### Offer Configuration
```python
limited_time_offers = {
    'offer_duration_hours': 48,
    'discount_ranges': {
        'budget_to_mid': {'min': 20, 'max': 40},
        'mid_to_professional': {'min': 25, 'max': 50},
        'budget_to_professional': {'min': 30, 'max': 60}
    },
    'free_months_range': {'min': 1, 'max': 3},
    'eligibility_criteria': {
        'min_engagement_score': 0.5,
        'min_feature_usage': 2,
        'trial_eligibility': True
    }
}
```

#### Usage Example
```python
# Create limited-time offer
offer = optimization_system.create_limited_time_offer(
    user_id, OfferType.PERCENTAGE_DISCOUNT,
    {
        'current_tier': 'budget',
        'target_tier': 'mid_tier',
        'engagement_score': 0.7,
        'feature_usage': 5,
        'trial_eligible': True
    }
)

if offer:
    print(f"Offer Type: {offer.offer_type.value}")
    print(f"Title: {offer.title}")
    print(f"Description: {offer.description}")
    print(f"Discount Value: {offer.discount_value}")
    print(f"Discount Type: {offer.discount_type}")
    print(f"Start Date: {offer.start_date}")
    print(f"End Date: {offer.end_date}")
    print(f"Usage Limit: {offer.usage_limit}")
```

### Offer Eligibility

#### Eligibility Checking
```python
def _check_offer_eligibility(self, user_id: str, context: Dict[str, Any] = None) -> bool:
    """Check if user is eligible for limited-time offer"""
    criteria = self.config.limited_time_offers['eligibility_criteria']
    
    # Check engagement score
    if context.get('engagement_score', 0) < criteria['min_engagement_score']:
        return False
    
    # Check feature usage
    if context.get('feature_usage', 0) < criteria['min_feature_usage']:
        return False
    
    # Check trial eligibility
    if criteria['trial_eligibility'] and not context.get('trial_eligible', False):
        return False
    
    return True
```

#### Offer Parameter Determination
```python
def _determine_offer_parameters(self, offer_type: OfferType, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Determine offer parameters"""
    current_tier = context.get('current_tier', 'budget')
    target_tier = context.get('target_tier', 'mid_tier')
    
    if offer_type == OfferType.PERCENTAGE_DISCOUNT:
        tier_key = f"{current_tier}_to_{target_tier.split('_')[0]}"
        discount_range = self.config.limited_time_offers['discount_ranges'].get(tier_key, {'min': 20, 'max': 30})
        discount_value = random.randint(discount_range['min'], discount_range['max'])
        
        return {
            'title': f"{discount_value}% Off {target_tier.title()}",
            'description': f"Limited time offer: Get {discount_value}% off your first year of {target_tier.title()}",
            'discount_value': discount_value,
            'discount_type': 'percentage',
            'eligibility_criteria': {},
            'usage_limit': 1
        }
    
    elif offer_type == OfferType.FREE_MONTHS:
        months_range = self.config.limited_time_offers['free_months_range']
        free_months = random.randint(months_range['min'], months_range['max'])
        
        return {
            'title': f"{free_months} Free Months",
            'description': f"Get {free_months} months free when you upgrade to {target_tier.title()}",
            'discount_value': free_months,
            'discount_type': 'free_months',
            'eligibility_criteria': {},
            'usage_limit': 1
        }
    
    # Default offer
    return {
        'title': 'Limited Time Offer',
        'description': 'Special discount for upgrading',
        'discount_value': 25,
        'discount_type': 'percentage',
        'eligibility_criteria': {},
        'usage_limit': 1
    }
```

## A/B Testing

### Test Types

#### A/B Test Categories
```python
class ABTestType(Enum):
    PROMPT_DESIGN = "prompt_design"       # Different prompt designs
    OFFER_TYPE = "offer_type"             # Different offer types
    TIMING = "timing"                     # Different timing strategies
    MESSAGING = "messaging"               # Different messaging approaches
    SOCIAL_PROOF = "social_proof"         # Different social proof content
    CTA_DESIGN = "cta_design"             # Different call-to-action designs
```

#### A/B Test Configuration
```python
ab_testing_settings = {
    'default_traffic_split': {'A': 0.5, 'B': 0.5},
    'minimum_sample_size': 100,
    'confidence_level': 0.95,
    'test_duration_days': 14,
    'success_metrics': ['conversion_rate', 'revenue_per_user', 'engagement_score'],
    'statistical_significance_threshold': 0.05
}
```

#### A/B Test Example
```python
# Prompt design A/B test
prompt_design_test = ABTest(
    test_id=str(uuid.uuid4()),
    test_type=ABTestType.PROMPT_DESIGN,
    test_name="Upgrade Prompt Design Optimization",
    description="Test different prompt designs to optimize conversion rates",
    variants=[
        {
            'id': 'A',
            'name': 'Value-First Design',
            'title_template': 'Save ${amount} annually with {feature}',
            'description_template': 'Join {count} users who saved an average of ${amount} per year',
            'cta_text': 'Start Saving Now',
            'cta_color': '#28a745'
        },
        {
            'id': 'B',
            'name': 'Feature-First Design',
            'title_template': 'Unlock {feature} Today',
            'description_template': 'Get access to {feature} and {other_features}',
            'cta_text': 'Upgrade Now',
            'cta_color': '#007bff'
        }
    ],
    traffic_split={'A': 0.5, 'B': 0.5},
    success_metrics=['conversion_rate', 'click_through_rate'],
    minimum_sample_size=100,
    confidence_level=0.95,
    start_date=datetime.now(timezone.utc),
    end_date=datetime.now(timezone.utc) + timedelta(days=14)
)
```

#### Usage Example
```python
# Assign user to A/B test variant
ab_assignment = optimization_system.assign_ab_test_variant(
    user_id, ABTestType.PROMPT_DESIGN, {
        'user_segment': 'mid_tier',
        'engagement_score': 0.7
    }
)

print(f"Variant: {ab_assignment['variant']}")
print(f"Test ID: {ab_assignment['test_id']}")
print(f"Config: {ab_assignment['config']}")

# Record A/B test result
optimization_system.record_ab_test_result(
    user_id, ab_assignment['test_id'], ab_assignment['variant'],
    {
        'conversion_rate': 0.08,
        'click_through_rate': 0.18,
        'revenue_per_user': 25.0,
        'engagement_score': 0.7
    }
)
```

### Variant Assignment

#### Consistent Hashing
```python
def _assign_variant(self, user_id: str, test: ABTest) -> str:
    """Assign user to A/B test variant using consistent hashing"""
    # Use user ID hash for consistent assignment
    user_hash = hash(user_id) % 100
    
    cumulative_prob = 0
    for variant, probability in test.traffic_split.items():
        cumulative_prob += probability * 100
        if user_hash < cumulative_prob:
            return variant
    
    return list(test.traffic_split.keys())[0]  # Default to first variant
```

#### Statistical Analysis
```python
def _check_statistical_significance(self, test_id: str) -> None:
    """Check for statistical significance in A/B test results"""
    # Get test results
    test_results = self._get_test_results(test_id)
    
    if not test_results:
        return
    
    # Perform statistical analysis
    for metric in test_results['success_metrics']:
        variant_a_results = test_results['variants']['A'].get(metric, [])
        variant_b_results = test_results['variants']['B'].get(metric, [])
        
        if len(variant_a_results) >= test_results['minimum_sample_size'] and \
           len(variant_b_results) >= test_results['minimum_sample_size']:
            
            # Calculate p-value using t-test
            p_value = self._calculate_p_value(variant_a_results, variant_b_results)
            
            if p_value < test_results['statistical_significance_threshold']:
                # Statistically significant result
                self._mark_test_significant(test_id, metric, p_value)
```

## Analytics and Optimization

### Optimization Analytics

#### Analytics Structure
```python
def get_optimization_analytics(self, user_id: str) -> Dict[str, Any]:
    """Get optimization analytics for user"""
    analytics = {
        'user_id': user_id,
        'trial_reminders': self._get_trial_reminder_analytics(user_id),
        'usage_prompts': self._get_usage_prompt_analytics(user_id),
        'social_proof_usage': self._get_social_proof_analytics(user_id),
        'offer_interactions': self._get_offer_analytics(user_id),
        'ab_test_participation': self._get_ab_test_analytics(user_id),
        'conversion_metrics': self._get_conversion_metrics(user_id),
        'optimization_recommendations': self._get_optimization_recommendations(user_id)
    }
    
    return analytics
```

#### Usage Example
```python
# Get comprehensive analytics
analytics = optimization_system.get_optimization_analytics(user_id)

print(f"User ID: {analytics['user_id']}")
print(f"Trial Reminders: {len(analytics['trial_reminders'])}")
print(f"Usage Prompts: {len(analytics['usage_prompts'])}")
print(f"Social Proof Usage: {len(analytics['social_proof_usage'])}")
print(f"Offer Interactions: {len(analytics['offer_interactions'])}")
print(f"A/B Test Participation: {len(analytics['ab_test_participation'])}")

print("Conversion Metrics:")
for key, value in analytics['conversion_metrics'].items():
    if isinstance(value, float):
        print(f"  {key}: {value:.1%}")
    else:
        print(f"  {key}: {value}")

print("Optimization Recommendations:")
for recommendation in analytics['optimization_recommendations']:
    print(f"  - {recommendation}")
```

### Conversion Metrics

#### Key Metrics
```python
def _get_conversion_metrics(self, user_id: str) -> Dict[str, Any]:
    """Get conversion metrics for user"""
    return {
        'overall_conversion_rate': 0.08,
        'trial_to_paid_conversion': 0.12,
        'prompt_click_through_rate': 0.25,
        'offer_acceptance_rate': 0.15,
        'social_proof_effectiveness': 0.18,
        'ab_test_conversion_lift': 0.05,
        'average_revenue_per_user': 45.0,
        'customer_lifetime_value': 540.0
    }
```

#### Optimization Recommendations
```python
def _get_optimization_recommendations(self, user_id: str) -> List[str]:
    """Get optimization recommendations for user"""
    recommendations = []
    
    # Analyze user behavior and generate recommendations
    user_analytics = self._get_user_analytics(user_id)
    
    if user_analytics.get('low_engagement', False):
        recommendations.append("Increase engagement through personalized content")
    
    if user_analytics.get('high_value_demonstration', False):
        recommendations.append("Leverage value demonstration for conversion")
    
    if user_analytics.get('social_proof_ineffective', False):
        recommendations.append("Optimize social proof relevance and timing")
    
    if user_analytics.get('offer_resistance', False):
        recommendations.append("Test different offer types and messaging")
    
    return recommendations
```

## Integration Examples

### API Integration
```python
def api_create_trial_reminder(user_id: str, trial_feature_id: str, reminder_type: str, context: Dict[str, Any] = None):
    """API endpoint for creating trial reminders"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    reminder = optimization_system.create_smart_trial_reminder(
        user_id, trial_feature_id, ReminderType(reminder_type), context
    )
    
    return {
        'success': True,
        'reminder': {
            'reminder_id': reminder.reminder_id,
            'reminder_type': reminder.reminder_type.value,
            'priority': reminder.priority,
            'scheduled_at': reminder.scheduled_at.isoformat(),
            'message_template': reminder.message_template
        }
    }

def api_generate_usage_prompt(user_id: str, feature_usage_data: Dict[str, Any]):
    """API endpoint for generating usage-based prompts"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    prompt = optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)
    
    if prompt:
        return {
            'success': True,
            'prompt': {
                'prompt_id': prompt.prompt_id,
                'trigger_feature': prompt.trigger_feature,
                'value_demonstrated': prompt.value_demonstrated,
                'upgrade_recommendation': prompt.upgrade_recommendation,
                'confidence_score': prompt.confidence_score
            }
        }
    else:
        return {'success': False, 'message': 'No prompt generated'}

def api_get_social_proof(user_id: str, context: Dict[str, Any] = None):
    """API endpoint for getting social proof"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    proofs = optimization_system.get_social_proof(user_id, context)
    
    return {
        'success': True,
        'social_proofs': [
            {
                'proof_id': proof.proof_id,
                'proof_type': proof.proof_type.value,
                'title': proof.title,
                'content': proof.content,
                'author': proof.author,
                'relevance_score': proof.relevance_score,
                'conversion_rate': proof.conversion_rate
            }
            for proof in proofs
        ]
    }

def api_create_limited_time_offer(user_id: str, offer_type: str, context: Dict[str, Any] = None):
    """API endpoint for creating limited-time offers"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    offer = optimization_system.create_limited_time_offer(user_id, OfferType(offer_type), context)
    
    if offer:
        return {
            'success': True,
            'offer': {
                'offer_id': offer.offer_id,
                'offer_type': offer.offer_type.value,
                'title': offer.title,
                'description': offer.description,
                'discount_value': offer.discount_value,
                'discount_type': offer.discount_type,
                'start_date': offer.start_date.isoformat(),
                'end_date': offer.end_date.isoformat()
            }
        }
    else:
        return {'success': False, 'message': 'User not eligible for offer'}

def api_assign_ab_test_variant(user_id: str, test_type: str, context: Dict[str, Any] = None):
    """API endpoint for A/B test variant assignment"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    assignment = optimization_system.assign_ab_test_variant(user_id, ABTestType(test_type), context)
    
    return {
        'success': True,
        'assignment': assignment
    }

def api_record_ab_test_result(user_id: str, test_id: str, variant: str, result_data: Dict[str, Any]):
    """API endpoint for recording A/B test results"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    optimization_system.record_ab_test_result(user_id, test_id, variant, result_data)
    
    return {'success': True}

def api_get_optimization_analytics(user_id: str):
    """API endpoint for optimization analytics"""
    optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
    
    analytics = optimization_system.get_optimization_analytics(user_id)
    
    return {
        'success': True,
        'analytics': analytics
    }
```

### Frontend Integration
```javascript
// Create trial reminder
async function createTrialReminder(userId, trialFeatureId, reminderType, context = null) {
    const response = await fetch('/api/optimization/create-trial-reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            trial_feature_id: trialFeatureId,
            reminder_type: reminderType,
            context: context
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.reminder;
    }
}

// Generate usage-based prompt
async function generateUsagePrompt(userId, featureUsageData) {
    const response = await fetch('/api/optimization/generate-usage-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            feature_usage_data: featureUsageData
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.prompt;
    }
    return null;
}

// Get social proof
async function getSocialProof(userId, context = null) {
    const response = await fetch('/api/optimization/get-social-proof', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            context: context
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.social_proofs;
    }
    return [];
}

// Create limited-time offer
async function createLimitedTimeOffer(userId, offerType, context = null) {
    const response = await fetch('/api/optimization/create-limited-time-offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            offer_type: offerType,
            context: context
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.offer;
    }
    return null;
}

// Assign A/B test variant
async function assignABTestVariant(userId, testType, context = null) {
    const response = await fetch('/api/optimization/assign-ab-test-variant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            test_type: testType,
            context: context
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.assignment;
    }
    return { variant: 'control', test_id: null };
}

// Record A/B test result
async function recordABTestResult(userId, testId, variant, resultData) {
    const response = await fetch('/api/optimization/record-ab-test-result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            test_id: testId,
            variant: variant,
            result_data: resultData
        })
    });
    
    const result = await response.json();
    return result.success;
}

// Get optimization analytics
async function getOptimizationAnalytics(userId) {
    const response = await fetch(`/api/optimization/analytics?user_id=${userId}`);
    const result = await response.json();
    
    if (result.success) {
        return result.analytics;
    }
    return {};
}

// Example usage
async function optimizeUserJourney(userId) {
    // Create trial reminder
    const reminder = await createTrialReminder(userId, 'investment_analysis', 'trial_expiry', {
        trial_end_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    });
    console.log(`Trial reminder created: ${reminder.reminder_type}`);
    
    // Generate usage prompt
    const featureUsageData = {
        features: {
            budget_tracker: { count: 8, time_spent: 4800 },
            expense_categorizer: { count: 6, time_spent: 3600 }
        },
        days_active: 14
    };
    const prompt = await generateUsagePrompt(userId, featureUsageData);
    if (prompt) {
        console.log(`Usage prompt generated: ${prompt.upgrade_recommendation}`);
    }
    
    // Get social proof
    const socialProofs = await getSocialProof(userId, { user_segment: 'mid_tier' });
    console.log(`Social proofs retrieved: ${socialProofs.length}`);
    
    // Create limited-time offer
    const offer = await createLimitedTimeOffer(userId, 'percentage_discount', {
        current_tier: 'budget',
        target_tier: 'mid_tier'
    });
    if (offer) {
        console.log(`Limited-time offer created: ${offer.offer_type}`);
    }
    
    // Assign A/B test variant
    const abAssignment = await assignABTestVariant(userId, 'prompt_design', {
        user_segment: 'mid_tier'
    });
    console.log(`A/B test variant assigned: ${abAssignment.variant}`);
    
    // Record A/B test result
    await recordABTestResult(userId, abAssignment.test_id, abAssignment.variant, {
        conversion_rate: 0.08,
        click_through_rate: 0.18
    });
    
    // Get analytics
    const analytics = await getOptimizationAnalytics(userId);
    console.log(`Optimization analytics generated with ${analytics.optimization_recommendations.length} recommendations`);
}
```

## Best Practices

### Trial Reminder Optimization
1. **Smart Timing**: Use user behavior to determine optimal reminder timing
2. **Progressive Escalation**: Increase urgency as trial expiration approaches
3. **Personalization**: Tailor messages based on user engagement and goals
4. **Frequency Control**: Limit reminders to avoid user fatigue
5. **A/B Testing**: Test different reminder strategies and messages

### Usage-Based Prompt Optimization
1. **Threshold Analysis**: Set appropriate usage thresholds for different features
2. **Value Demonstration**: Focus on concrete value shown through usage
3. **Confidence Scoring**: Use confidence scores to ensure prompt relevance
4. **Personalization**: Tailor prompts based on user behavior patterns
5. **Continuous Optimization**: Regularly adjust thresholds based on results

### Social Proof Optimization
1. **Relevance Matching**: Match social proof to user segment and interests
2. **Conversion Tracking**: Monitor which social proof content drives conversions
3. **Content Rotation**: Rotate content to maintain freshness
4. **Authenticity**: Ensure social proof content is genuine and credible
5. **A/B Testing**: Test different social proof formats and content

### Limited-Time Offer Optimization
1. **Urgency Creation**: Use genuine time limitations to create urgency
2. **Eligibility Targeting**: Target offers to users most likely to convert
3. **Offer Variety**: Test different offer types and discount levels
4. **Scarcity Management**: Control offer availability to maintain value
5. **Performance Tracking**: Monitor offer performance and adjust accordingly

### A/B Testing Best Practices
1. **Clear Hypotheses**: Start with clear hypotheses about what will improve conversions
2. **Statistical Significance**: Ensure adequate sample sizes for reliable results
3. **Consistent Assignment**: Use consistent hashing for reliable variant assignment
4. **Multiple Metrics**: Track multiple success metrics beyond just conversion rate
5. **Continuous Testing**: Maintain a pipeline of ongoing A/B tests

### Analytics and Optimization
1. **Comprehensive Tracking**: Track all user interactions and optimization events
2. **Performance Monitoring**: Monitor system performance and optimization effectiveness
3. **Recommendation Engine**: Use data to generate actionable optimization recommendations
4. **Continuous Improvement**: Regularly review and update optimization strategies
5. **Cross-Channel Optimization**: Optimize across all user touchpoints

## Troubleshooting

### Common Issues

#### Trial Reminder Issues
```python
def debug_trial_reminder_creation(user_id: str, trial_feature_id: str, reminder_type: str, context: Dict[str, Any] = None):
    """Debug trial reminder creation issues"""
    try:
        optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
        reminder = optimization_system.create_smart_trial_reminder(
            user_id, trial_feature_id, ReminderType(reminder_type), context
        )
        print(f"Trial reminder created successfully for user {user_id}")
        print(f"Reminder Type: {reminder.reminder_type.value}")
        print(f"Priority: {reminder.priority}")
        print(f"Scheduled At: {reminder.scheduled_at}")
    except Exception as e:
        print(f"Trial reminder creation failed: {e}")
```

#### Usage Prompt Issues
```python
def debug_usage_prompt_generation(user_id: str, feature_usage_data: Dict[str, Any]):
    """Debug usage prompt generation issues"""
    try:
        optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
        prompt = optimization_system.generate_usage_based_prompt(user_id, feature_usage_data)
        if prompt:
            print(f"Usage prompt generated successfully for user {user_id}")
            print(f"Trigger Feature: {prompt.trigger_feature}")
            print(f"Value Demonstrated: {prompt.value_demonstrated:.1%}")
            print(f"Confidence Score: {prompt.confidence_score:.1%}")
        else:
            print(f"No usage prompt generated for user {user_id} (thresholds not met)")
    except Exception as e:
        print(f"Usage prompt generation failed: {e}")
```

#### A/B Testing Issues
```python
def debug_ab_test_assignment(user_id: str, test_type: str, context: Dict[str, Any] = None):
    """Debug A/B test assignment issues"""
    try:
        optimization_system = UpgradeOptimization(db, subscription_service, analytics_service, notification_service)
        assignment = optimization_system.assign_ab_test_variant(user_id, ABTestType(test_type), context)
        print(f"A/B test assignment successful for user {user_id}")
        print(f"Variant: {assignment['variant']}")
        print(f"Test ID: {assignment['test_id']}")
        print(f"Config: {assignment['config']}")
    except Exception as e:
        print(f"A/B test assignment failed: {e}")
```

## Conclusion

The Upgrade Optimization system provides comprehensive optimization features, enabling:

- **Smart Trial Reminders**: Optimized timing based on user behavior and trial status
- **Usage-Based Prompts**: Intelligent prompts triggered by feature usage patterns
- **Social Proof**: Personalized testimonials and success stories for trust building
- **Limited-Time Offers**: Strategic offers with urgency and scarcity
- **A/B Testing**: Systematic testing for continuous optimization
- **Comprehensive Analytics**: Detailed insights for optimization decisions
- **API Integration**: Easy integration with frontend applications
- **Performance Optimization**: Efficient processing for high-volume usage

This system ensures maximum conversion rates through data-driven optimization, personalized experiences, and continuous improvement based on user behavior and A/B test results. 