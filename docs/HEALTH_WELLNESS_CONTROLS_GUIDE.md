# Health & Wellness Subscription Controls Guide

## Overview

The Health & Wellness Subscription Controls system provides comprehensive subscription gating for MINGUS health and wellness features, including health check-in submissions, health correlation insights, and wellness recommendations with appropriate tier limits and depth.

## Feature Overview

### Purpose
- **Health Check-in Submissions**: Manage tier-appropriate limits for health check-ins (4/12/unlimited)
- **Health Correlation Insights**: Provide tier-appropriate depth for health insights (basic/advanced)
- **Wellness Recommendations**: Deliver tier-appropriate wellness guidance and recommendations
- **Subscription Gating**: Ensure proper access control based on subscription tiers

### Key Benefits
- **Tier-Appropriate Limits**: Proper limits based on subscription levels
- **Intelligent Depth Control**: Advanced features for higher tiers
- **Personalized Recommendations**: Tailored wellness guidance
- **Usage Optimization**: Smart tracking and limit management
- **Upgrade Paths**: Clear upgrade recommendations based on usage

## Health Feature Categories

### Health Check-in Types
```python
class HealthCheckinType(Enum):
    DAILY_CHECKIN = "daily_checkin"           # Daily health check-ins
    MOOD_TRACKING = "mood_tracking"           # Mood tracking
    SLEEP_TRACKING = "sleep_tracking"         # Sleep tracking
    EXERCISE_TRACKING = "exercise_tracking"   # Exercise tracking
    NUTRITION_TRACKING = "nutrition_tracking" # Nutrition tracking
    STRESS_TRACKING = "stress_tracking"       # Stress tracking
    ENERGY_LEVELS = "energy_levels"           # Energy level tracking
    SYMPTOM_TRACKING = "symptom_tracking"     # Symptom tracking
```

### Correlation Insight Types
```python
class CorrelationInsightType(Enum):
    BASIC_CORRELATION = "basic_correlation"       # Basic health correlations
    ADVANCED_CORRELATION = "advanced_correlation" # Advanced correlations
    PREDICTIVE_INSIGHTS = "predictive_insights"   # Predictive health insights
    TREND_ANALYSIS = "trend_analysis"             # Trend analysis
    PATTERN_DETECTION = "pattern_detection"       # Pattern detection
    RISK_ASSESSMENT = "risk_assessment"           # Risk assessment
```

### Wellness Recommendation Types
```python
class WellnessRecommendationType(Enum):
    BASIC_TIPS = "basic_tips"                     # Basic wellness tips
    PERSONALIZED_ADVICE = "personalized_advice"   # Personalized advice
    ACTION_PLANS = "action_plans"                 # Action plans
    EXPERT_GUIDANCE = "expert_guidance"           # Expert guidance
    HOLISTIC_APPROACH = "holistic_approach"       # Holistic approach
    INTEGRATED_WELLNESS = "integrated_wellness"   # Integrated wellness
```

## Tier Configuration

### Subscription Tiers
```python
class HealthAccessLevel(Enum):
    FREE = "free"                     # Free tier access
    BUDGET = "budget"                 # Budget tier access
    MID_TIER = "mid_tier"             # Mid-tier access
    PROFESSIONAL = "professional"     # Professional tier access
    UNLIMITED = "unlimited"           # Unlimited access
```

### Tier Limits Configuration
```python
tier_limits = {
    'budget': {
        'health_checkins_per_month': 4,
        'correlation_insights_per_month': 2,
        'wellness_recommendations_per_month': 5,
        'health_goals': 2,
        'analytics_reports_per_month': 1
    },
    'mid_tier': {
        'health_checkins_per_month': 12,
        'correlation_insights_per_month': 8,
        'wellness_recommendations_per_month': 15,
        'health_goals': 5,
        'analytics_reports_per_month': 3
    },
    'professional': {
        'health_checkins_per_month': -1,  # Unlimited
        'correlation_insights_per_month': -1,  # Unlimited
        'wellness_recommendations_per_month': -1,  # Unlimited
        'health_goals': 10,
        'analytics_reports_per_month': -1  # Unlimited
    }
}
```

### Feature Access by Tier
```python
feature_access = {
    'health_checkin': {
        'budget': ['daily_checkin', 'mood_tracking'],
        'mid_tier': ['daily_checkin', 'mood_tracking', 'sleep_tracking', 'exercise_tracking'],
        'professional': ['daily_checkin', 'mood_tracking', 'sleep_tracking', 'exercise_tracking', 'nutrition_tracking', 'stress_tracking', 'energy_levels', 'symptom_tracking']
    },
    'health_correlation': {
        'budget': ['basic_correlation'],
        'mid_tier': ['basic_correlation', 'advanced_correlation', 'trend_analysis'],
        'professional': ['basic_correlation', 'advanced_correlation', 'trend_analysis', 'predictive_insights', 'pattern_detection', 'risk_assessment']
    },
    'wellness_recommendations': {
        'budget': ['basic_tips'],
        'mid_tier': ['basic_tips', 'personalized_advice', 'action_plans'],
        'professional': ['basic_tips', 'personalized_advice', 'action_plans', 'expert_guidance', 'holistic_approach', 'integrated_wellness']
    }
}
```

## Health Check-in Submissions

### Submit Health Check-in
```python
def submit_health_checkin(self, user_id: str, checkin_type: HealthCheckinType, checkin_data: Dict[str, Any]) -> Dict[str, Any]:
    """Submit health check-in with tier limits"""
    # Get user subscription
    subscription = self.subscription_service.get_user_subscription(user_id)
    user_tier = subscription.get('plan_id', 'budget')
    
    # Check if check-in type is available for user tier
    available_types = self.config.feature_access['health_checkin'].get(user_tier, [])
    if checkin_type.value not in available_types:
        return {
            'success': False,
            'error': 'feature_not_available',
            'message': f'Health check-in type {checkin_type.value} not available for {user_tier} tier',
            'upgrade_required': True,
            'recommended_tier': self._get_next_tier(user_tier)
        }
    
    # Check monthly limit
    monthly_limit = self.config.tier_limits[user_tier]['health_checkins_per_month']
    current_usage = self._get_monthly_checkin_usage(user_id)
    
    if monthly_limit > 0 and current_usage >= monthly_limit:
        return {
            'success': False,
            'error': 'limit_exceeded',
            'message': f'Monthly health check-in limit ({monthly_limit}) exceeded',
            'upgrade_required': True,
            'recommended_tier': self._get_next_tier(user_tier),
            'current_usage': current_usage,
            'monthly_limit': monthly_limit
        }
    
    # Create and save check-in record
    checkin_record = HealthCheckinRecord(
        checkin_id=str(uuid.uuid4()),
        user_id=user_id,
        checkin_type=checkin_type,
        checkin_data=checkin_data,
        timestamp=datetime.now(timezone.utc),
        tier_used=user_tier,
        is_within_limit=True
    )
    
    return {
        'success': True,
        'checkin_id': checkin_record.checkin_id,
        'tier_used': user_tier,
        'monthly_usage': current_usage + 1,
        'monthly_limit': monthly_limit,
        'remaining_checkins': max(0, monthly_limit - (current_usage + 1)) if monthly_limit > 0 else -1
    }
```

### Usage Example
```python
# Submit health check-in
checkin_data = {
    'mood_score': 8,
    'energy_level': 7,
    'sleep_hours': 7.5,
    'stress_level': 4,
    'notes': 'Feeling productive today'
}

result = health_controls.submit_health_checkin(
    user_id, HealthCheckinType.DAILY_CHECKIN, checkin_data
)

if result['success']:
    print(f"Check-in submitted: {result['checkin_id']}")
    print(f"Remaining check-ins: {result['remaining_checkins']}")
else:
    print(f"Check-in failed: {result['message']}")
    if result.get('upgrade_required'):
        print(f"Upgrade to {result['recommended_tier']} required")
```

## Health Correlation Insights

### Get Health Correlation Insights
```python
def get_health_correlation_insights(self, user_id: str, insight_type: CorrelationInsightType, health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get health correlation insights with tier-appropriate depth"""
    # Get user subscription
    subscription = self.subscription_service.get_user_subscription(user_id)
    user_tier = subscription.get('plan_id', 'budget')
    
    # Check if insight type is available for user tier
    available_insights = self.config.feature_access['health_correlation'].get(user_tier, [])
    if insight_type.value not in available_insights:
        return {
            'success': False,
            'error': 'feature_not_available',
            'message': f'Health correlation insight type {insight_type.value} not available for {user_tier} tier',
            'upgrade_required': True,
            'recommended_tier': self._get_next_tier(user_tier)
        }
    
    # Check monthly limit
    monthly_limit = self.config.tier_limits[user_tier]['correlation_insights_per_month']
    current_usage = self._get_monthly_insight_usage(user_id)
    
    if monthly_limit > 0 and current_usage >= monthly_limit:
        return {
            'success': False,
            'error': 'limit_exceeded',
            'message': f'Monthly correlation insight limit ({monthly_limit}) exceeded',
            'upgrade_required': True,
            'recommended_tier': self._get_next_tier(user_tier),
            'current_usage': current_usage,
            'monthly_limit': monthly_limit
        }
    
    # Generate tier-appropriate insights
    insight_data = self._generate_correlation_insights(user_id, insight_type, health_data, user_tier)
    
    return {
        'success': True,
        'insight_id': str(uuid.uuid4()),
        'insight_type': insight_type.value,
        'tier_level': user_tier,
        'correlation_data': insight_data['correlation_data'],
        'confidence_score': insight_data['confidence_score'],
        'recommendations': insight_data['recommendations'],
        'monthly_usage': current_usage + 1,
        'monthly_limit': monthly_limit,
        'remaining_insights': max(0, monthly_limit - (current_usage + 1)) if monthly_limit > 0 else -1
    }
```

### Tier-Appropriate Insight Generation
```python
def _generate_correlation_insights(self, user_id: str, insight_type: CorrelationInsightType, health_data: Dict[str, Any], user_tier: str) -> Dict[str, Any]:
    """Generate tier-appropriate correlation insights"""
    if user_tier == 'budget':
        # Basic correlation insights
        return {
            'correlation_data': {
                'type': 'basic_correlation',
                'factors': ['sleep', 'mood'],
                'strength': 'moderate',
                'description': 'Basic correlation between sleep quality and mood'
            },
            'confidence_score': 0.6,
            'recommendations': [
                'Track your sleep patterns regularly',
                'Note mood changes after different sleep durations'
            ]
        }
    elif user_tier == 'mid_tier':
        # Advanced correlation insights
        return {
            'correlation_data': {
                'type': 'advanced_correlation',
                'factors': ['sleep', 'mood', 'exercise', 'stress'],
                'strength': 'strong',
                'description': 'Advanced correlation analysis with multiple health factors',
                'trends': ['weekly_patterns', 'monthly_variations']
            },
            'confidence_score': 0.8,
            'recommendations': [
                'Exercise appears to improve both sleep and mood',
                'Stress levels correlate strongly with sleep quality',
                'Consider stress management techniques for better sleep'
            ]
        }
    else:  # professional
        # Predictive insights
        return {
            'correlation_data': {
                'type': 'predictive_insights',
                'factors': ['sleep', 'mood', 'exercise', 'stress', 'nutrition', 'energy'],
                'strength': 'very_strong',
                'description': 'Predictive analysis with comprehensive health factor correlation',
                'trends': ['weekly_patterns', 'monthly_variations', 'seasonal_trends'],
                'predictions': ['optimal_sleep_window', 'mood_forecast', 'energy_prediction']
            },
            'confidence_score': 0.95,
            'recommendations': [
                'Your optimal sleep window is 10 PM - 6 AM',
                'Exercise in the morning correlates with better mood throughout the day',
                'Stress peaks on Wednesdays - consider mid-week relaxation techniques',
                'Nutrition quality directly impacts energy levels and mood stability'
            ]
        }
```

### Usage Example
```python
# Get health correlation insights
health_data = {
    'sleep_data': {'avg_hours': 7.5, 'quality_score': 8.5},
    'mood_data': {'avg_score': 8.0, 'variability': 1.5},
    'exercise_data': {'frequency': 5, 'intensity': 'high'},
    'stress_data': {'avg_level': 3.0, 'peaks': ['friday']}
}

result = health_controls.get_health_correlation_insights(
    user_id, CorrelationInsightType.ADVANCED_CORRELATION, health_data
)

if result['success']:
    print(f"Insights generated: {result['insight_id']}")
    print(f"Confidence score: {result['confidence_score']:.1%}")
    print(f"Remaining insights: {result['remaining_insights']}")
    
    for rec in result['recommendations']:
        print(f"- {rec}")
else:
    print(f"Insights failed: {result['message']}")
```

## Wellness Recommendations

### Get Wellness Recommendations
```python
def get_wellness_recommendations(self, user_id: str, recommendation_type: WellnessRecommendationType, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Get wellness recommendations with tier-appropriate depth"""
    # Get user subscription
    subscription = self.subscription_service.get_user_subscription(user_id)
    user_tier = subscription.get('plan_id', 'budget')
    
    # Check if recommendation type is available for user tier
    available_recommendations = self.config.feature_access['wellness_recommendations'].get(user_tier, [])
    if recommendation_type.value not in available_recommendations:
        return {
            'success': False,
            'error': 'feature_not_available',
            'message': f'Wellness recommendation type {recommendation_type.value} not available for {user_tier} tier',
            'upgrade_required': True,
            'recommended_tier': self._get_next_tier(user_tier)
        }
    
    # Check monthly limit
    monthly_limit = self.config.tier_limits[user_tier]['wellness_recommendations_per_month']
    current_usage = self._get_monthly_recommendation_usage(user_id)
    
    if monthly_limit > 0 and current_usage >= monthly_limit:
        return {
            'success': False,
            'error': 'limit_exceeded',
            'message': f'Monthly wellness recommendation limit ({monthly_limit}) exceeded',
            'upgrade_required': True,
            'recommended_tier': self._get_next_tier(user_tier),
            'current_usage': current_usage,
            'monthly_limit': monthly_limit
        }
    
    # Generate tier-appropriate recommendations
    recommendation_data = self._generate_wellness_recommendations(user_id, recommendation_type, user_context, user_tier)
    
    return {
        'success': True,
        'recommendation_id': str(uuid.uuid4()),
        'recommendation_type': recommendation_type.value,
        'tier_level': user_tier,
        'recommendation_data': recommendation_data['recommendation_data'],
        'personalization_level': recommendation_data['personalization_level'],
        'action_items': recommendation_data['action_items'],
        'monthly_usage': current_usage + 1,
        'monthly_limit': monthly_limit,
        'remaining_recommendations': max(0, monthly_limit - (current_usage + 1)) if monthly_limit > 0 else -1
    }
```

### Tier-Appropriate Recommendation Generation
```python
def _generate_wellness_recommendations(self, user_id: str, recommendation_type: WellnessRecommendationType, user_context: Dict[str, Any], user_tier: str) -> Dict[str, Any]:
    """Generate tier-appropriate wellness recommendations"""
    if user_tier == 'budget':
        # Basic tips
        return {
            'recommendation_data': {
                'type': 'basic_tips',
                'focus_areas': ['sleep', 'mood'],
                'complexity': 'simple',
                'time_commitment': 'low'
            },
            'personalization_level': 'basic',
            'action_items': [
                'Aim for 7-8 hours of sleep per night',
                'Track your mood daily',
                'Take short walks when feeling stressed'
            ]
        }
    elif user_tier == 'mid_tier':
        # Personalized advice
        return {
            'recommendation_data': {
                'type': 'personalized_advice',
                'focus_areas': ['sleep', 'mood', 'exercise', 'stress'],
                'complexity': 'moderate',
                'time_commitment': 'medium',
                'personalization': 'moderate'
            },
            'personalization_level': 'moderate',
            'action_items': [
                'Based on your patterns, exercise before 6 PM for better sleep',
                'Practice 10-minute meditation when stress levels are high',
                'Adjust your sleep schedule gradually by 15 minutes each day',
                'Track nutrition impact on your energy levels'
            ]
        }
    else:  # professional
        # Expert guidance with holistic approach
        return {
            'recommendation_data': {
                'type': 'expert_guidance',
                'focus_areas': ['sleep', 'mood', 'exercise', 'stress', 'nutrition', 'energy', 'recovery'],
                'complexity': 'advanced',
                'time_commitment': 'high',
                'personalization': 'high',
                'holistic_approach': True
            },
            'personalization_level': 'high',
            'action_items': [
                'Implement circadian rhythm optimization: gradual light exposure in morning',
                'Create personalized stress management protocol based on your triggers',
                'Develop nutrition plan that supports your specific energy patterns',
                'Establish recovery protocols for optimal performance',
                'Integrate mindfulness practices throughout your daily routine',
                'Schedule regular health check-ins with your wellness coach'
            ]
        }
```

### Usage Example
```python
# Get wellness recommendations
user_context = {
    'age': 35,
    'lifestyle': 'active',
    'health_goals': ['better_sleep', 'stress_management', 'energy_optimization'],
    'current_challenges': ['work_stress', 'irregular_sleep'],
    'preferences': ['natural_remedies', 'exercise', 'mindfulness']
}

result = health_controls.get_wellness_recommendations(
    user_id, WellnessRecommendationType.ACTION_PLANS, user_context
)

if result['success']:
    print(f"Recommendations generated: {result['recommendation_id']}")
    print(f"Personalization level: {result['personalization_level']}")
    print(f"Remaining recommendations: {result['remaining_recommendations']}")
    
    print("Action Items:")
    for item in result['action_items']:
        print(f"- {item}")
else:
    print(f"Recommendations failed: {result['message']}")
```

## Health Feature Status

### Get Health Feature Status
```python
def get_health_feature_status(self, user_id: str) -> Dict[str, Any]:
    """Get comprehensive health feature status for user"""
    # Get user subscription
    subscription = self.subscription_service.get_user_subscription(user_id)
    user_tier = subscription.get('plan_id', 'budget')
    
    # Get current usage
    checkin_usage = self._get_monthly_checkin_usage(user_id)
    insight_usage = self._get_monthly_insight_usage(user_id)
    recommendation_usage = self._get_monthly_recommendation_usage(user_id)
    
    # Get tier limits
    tier_limits = self.config.tier_limits.get(user_tier, {})
    
    # Get available features
    available_features = {
        'health_checkin': self.config.feature_access['health_checkin'].get(user_tier, []),
        'health_correlation': self.config.feature_access['health_correlation'].get(user_tier, []),
        'wellness_recommendations': self.config.feature_access['wellness_recommendations'].get(user_tier, [])
    }
    
    return {
        'user_id': user_id,
        'tier': user_tier,
        'usage': {
            'health_checkins': {
                'current': checkin_usage,
                'limit': tier_limits.get('health_checkins_per_month', 0),
                'remaining': max(0, tier_limits.get('health_checkins_per_month', 0) - checkin_usage) if tier_limits.get('health_checkins_per_month', 0) > 0 else -1
            },
            'correlation_insights': {
                'current': insight_usage,
                'limit': tier_limits.get('correlation_insights_per_month', 0),
                'remaining': max(0, tier_limits.get('correlation_insights_per_month', 0) - insight_usage) if tier_limits.get('correlation_insights_per_month', 0) > 0 else -1
            },
            'wellness_recommendations': {
                'current': recommendation_usage,
                'limit': tier_limits.get('wellness_recommendations_per_month', 0),
                'remaining': max(0, tier_limits.get('wellness_recommendations_per_month', 0) - recommendation_usage) if tier_limits.get('wellness_recommendations_per_month', 0) > 0 else -1
            }
        },
        'available_features': available_features,
        'upgrade_recommendations': self._generate_health_upgrade_recommendations(user_id, user_tier, checkin_usage, insight_usage, recommendation_usage)
    }
```

### Usage Example
```python
# Get health feature status
status = health_controls.get_health_feature_status(user_id)

print(f"User Tier: {status['tier']}")

print("Usage:")
for feature, usage_data in status['usage'].items():
    print(f"  {feature}: {usage_data['current']}/{usage_data['limit']} (Remaining: {usage_data['remaining']})")

print("Available Features:")
for feature_type, features in status['available_features'].items():
    print(f"  {feature_type}: {', '.join(features)}")

print("Upgrade Recommendations:")
for rec in status['upgrade_recommendations']:
    print(f"  - {rec['type']}: {rec.get('feature', 'N/A')} -> {rec['recommended_tier']}")
```

## Health Wellness Decorator

### Feature Access Decorators
```python
class HealthWellnessDecorator:
    """Decorator for health and wellness subscription controls"""
    
    def require_health_checkin_access(self, checkin_type: HealthCheckinType):
        """Decorator to require health check-in access"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = self._extract_user_id(args, kwargs)
                if not user_id:
                    raise ValueError("user_id not found in function arguments")
                
                # Check if user can submit this type of check-in
                subscription = self.health_controls.subscription_service.get_user_subscription(user_id)
                user_tier = subscription.get('plan_id', 'budget')
                
                available_types = self.health_controls.config.feature_access['health_checkin'].get(user_tier, [])
                if checkin_type.value not in available_types:
                    raise PermissionError(f"Health check-in type {checkin_type.value} not available for {user_tier} tier")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_correlation_insight_access(self, insight_type: CorrelationInsightType):
        """Decorator to require correlation insight access"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = self._extract_user_id(args, kwargs)
                if not user_id:
                    raise ValueError("user_id not found in function arguments")
                
                # Check if user can access this type of insight
                subscription = self.health_controls.subscription_service.get_user_subscription(user_id)
                user_tier = subscription.get('plan_id', 'budget')
                
                available_insights = self.health_controls.config.feature_access['health_correlation'].get(user_tier, [])
                if insight_type.value not in available_insights:
                    raise PermissionError(f"Correlation insight type {insight_type.value} not available for {user_tier} tier")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_wellness_recommendation_access(self, recommendation_type: WellnessRecommendationType):
        """Decorator to require wellness recommendation access"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = self._extract_user_id(args, kwargs)
                if not user_id:
                    raise ValueError("user_id not found in function arguments")
                
                # Check if user can access this type of recommendation
                subscription = self.health_controls.subscription_service.get_user_subscription(user_id)
                user_tier = subscription.get('plan_id', 'budget')
                
                available_recommendations = self.health_controls.config.feature_access['wellness_recommendations'].get(user_tier, [])
                if recommendation_type.value not in available_recommendations:
                    raise PermissionError(f"Wellness recommendation type {recommendation_type.value} not available for {user_tier} tier")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
```

### Usage Example
```python
# Create decorator
decorator = HealthWellnessDecorator(health_controls)

# Decorate function with health check-in access requirement
@decorator.require_health_checkin_access(HealthCheckinType.SLEEP_TRACKING)
def track_sleep(user_id: str, sleep_data: Dict[str, Any]):
    """Track sleep patterns"""
    return {
        'tracking_id': str(uuid.uuid4()),
        'user_id': user_id,
        'sleep_hours': sleep_data.get('hours', 7.5),
        'quality_score': sleep_data.get('quality', 8.0)
    }

# Decorate function with correlation insight access requirement
@decorator.require_correlation_insight_access(CorrelationInsightType.ADVANCED_CORRELATION)
def analyze_sleep_mood_correlation(user_id: str, data: Dict[str, Any]):
    """Analyze sleep-mood correlation"""
    return {
        'analysis_id': str(uuid.uuid4()),
        'user_id': user_id,
        'correlation_strength': 0.75,
        'insights': ['Better sleep correlates with improved mood']
    }

# Decorate function with wellness recommendation access requirement
@decorator.require_wellness_recommendation_access(WellnessRecommendationType.EXPERT_GUIDANCE)
def get_sleep_recommendations(user_id: str, context: Dict[str, Any]):
    """Get sleep recommendations"""
    return {
        'recommendation_id': str(uuid.uuid4()),
        'user_id': user_id,
        'recommendations': ['Optimize sleep environment', 'Establish consistent bedtime']
    }

# Use decorated functions
try:
    result = track_sleep('mid_tier_user', {'hours': 8.0, 'quality': 9.0})
    print(f"Sleep tracking successful: {result['tracking_id']}")
except PermissionError as e:
    print(f"Access denied: {e}")

try:
    result = analyze_sleep_mood_correlation('professional_user', {'sleep_data': [], 'mood_data': []})
    print(f"Correlation analysis successful: {result['analysis_id']}")
except PermissionError as e:
    print(f"Access denied: {e}")

try:
    result = get_sleep_recommendations('professional_user', {'sleep_issues': ['insomnia']})
    print(f"Sleep recommendations successful: {result['recommendation_id']}")
except PermissionError as e:
    print(f"Access denied: {e}")
```

## Integration Examples

### API Integration
```python
def api_submit_health_checkin(user_id: str, checkin_type: str, checkin_data: Dict[str, Any]):
    """API endpoint for submitting health check-ins"""
    health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
    
    result = health_controls.submit_health_checkin(
        user_id, HealthCheckinType(checkin_type), checkin_data
    )
    
    return result

def api_get_health_correlation_insights(user_id: str, insight_type: str, health_data: Dict[str, Any]):
    """API endpoint for getting health correlation insights"""
    health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
    
    result = health_controls.get_health_correlation_insights(
        user_id, CorrelationInsightType(insight_type), health_data
    )
    
    return result

def api_get_wellness_recommendations(user_id: str, recommendation_type: str, user_context: Dict[str, Any]):
    """API endpoint for getting wellness recommendations"""
    health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
    
    result = health_controls.get_wellness_recommendations(
        user_id, WellnessRecommendationType(recommendation_type), user_context
    )
    
    return result

def api_get_health_feature_status(user_id: str):
    """API endpoint for getting health feature status"""
    health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
    
    status = health_controls.get_health_feature_status(user_id)
    
    return {
        'success': True,
        'status': status
    }
```

### Frontend Integration
```javascript
// Submit health check-in
async function submitHealthCheckin(userId, checkinType, checkinData) {
    const response = await fetch('/api/health/submit-checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            checkin_type: checkinType,
            checkin_data: checkinData
        })
    });
    
    const result = await response.json();
    return result;
}

// Get health correlation insights
async function getHealthCorrelationInsights(userId, insightType, healthData) {
    const response = await fetch('/api/health/get-correlation-insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            insight_type: insightType,
            health_data: healthData
        })
    });
    
    const result = await response.json();
    return result;
}

// Get wellness recommendations
async function getWellnessRecommendations(userId, recommendationType, userContext) {
    const response = await fetch('/api/health/get-wellness-recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            recommendation_type: recommendationType,
            user_context: userContext
        })
    });
    
    const result = await response.json();
    return result;
}

// Get health feature status
async function getHealthFeatureStatus(userId) {
    const response = await fetch('/api/health/get-feature-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    
    const result = await response.json();
    return result.status;
}

// Example usage
async function handleHealthCheckin(userId, checkinType, checkinData) {
    try {
        const result = await submitHealthCheckin(userId, checkinType, checkinData);
        
        if (result.success) {
            console.log(`Check-in submitted: ${result.checkin_id}`);
            console.log(`Remaining check-ins: ${result.remaining_checkins}`);
            
            // Update UI with remaining check-ins
            updateCheckinCounter(result.remaining_checkins);
        } else {
            console.log(`Check-in failed: ${result.message}`);
            
            if (result.upgrade_required) {
                // Show upgrade prompt
                showUpgradePrompt(result.recommended_tier, result.message);
            }
        }
    } catch (error) {
        console.error('Error submitting health check-in:', error);
    }
}

// Example health dashboard integration
async function loadHealthDashboard(userId) {
    try {
        // Get feature status
        const status = await getHealthFeatureStatus(userId);
        
        // Update dashboard with usage information
        updateUsageDisplay(status.usage);
        
        // Update available features
        updateAvailableFeatures(status.available_features);
        
        // Show upgrade recommendations if any
        if (status.upgrade_recommendations.length > 0) {
            showUpgradeRecommendations(status.upgrade_recommendations);
        }
        
        // Load health data based on available features
        if (status.available_features.health_checkin.includes('daily_checkin')) {
            loadHealthCheckins(userId);
        }
        
        if (status.available_features.health_correlation.includes('basic_correlation')) {
            loadCorrelationInsights(userId);
        }
        
        if (status.available_features.wellness_recommendations.includes('basic_tips')) {
            loadWellnessRecommendations(userId);
        }
        
    } catch (error) {
        console.error('Error loading health dashboard:', error);
    }
}

// Example health check-in form
async function submitHealthCheckinForm(userId) {
    const formData = {
        mood_score: parseInt(document.getElementById('mood-score').value),
        energy_level: parseInt(document.getElementById('energy-level').value),
        sleep_hours: parseFloat(document.getElementById('sleep-hours').value),
        stress_level: parseInt(document.getElementById('stress-level').value),
        notes: document.getElementById('health-notes').value
    };
    
    await handleHealthCheckin(userId, 'daily_checkin', formData);
}

// Example correlation analysis
async function analyzeHealthCorrelation(userId) {
    try {
        const healthData = {
            sleep_data: { avg_hours: 7.5, quality_score: 8.0 },
            mood_data: { avg_score: 7.8, variability: 1.5 },
            exercise_data: { frequency: 4, intensity: 'moderate' },
            stress_data: { avg_level: 4.0, peaks: ['monday'] }
        };
        
        const result = await getHealthCorrelationInsights(userId, 'advanced_correlation', health_data);
        
        if (result.success) {
            displayCorrelationInsights(result);
        } else {
            if (result.upgrade_required) {
                showUpgradePrompt(result.recommended_tier, result.message);
            }
        }
    } catch (error) {
        console.error('Error analyzing health correlation:', error);
    }
}

// Example wellness recommendations
async function getPersonalizedWellnessRecommendations(userId) {
    try {
        const userContext = {
            age: 35,
            lifestyle: 'active',
            health_goals: ['better_sleep', 'stress_management'],
            current_challenges: ['work_stress', 'irregular_sleep'],
            preferences: ['natural_remedies', 'exercise']
        };
        
        const result = await getWellnessRecommendations(userId, 'action_plans', userContext);
        
        if (result.success) {
            displayWellnessRecommendations(result);
        } else {
            if (result.upgrade_required) {
                showUpgradePrompt(result.recommended_tier, result.message);
            }
        }
    } catch (error) {
        console.error('Error getting wellness recommendations:', error);
    }
}
```

## Best Practices

### Health Check-in Management
1. **Tier-Appropriate Limits**: Respect monthly limits based on subscription tier
2. **Feature Availability**: Check feature availability before allowing access
3. **Usage Tracking**: Track all check-in usage for analytics and optimization
4. **Upgrade Prompts**: Provide clear upgrade paths when limits are reached
5. **Data Quality**: Ensure check-in data quality and validation

### Correlation Insights
1. **Tier-Appropriate Depth**: Provide insights appropriate for user tier
2. **Data Privacy**: Ensure health data privacy and security
3. **Confidence Scoring**: Include confidence scores for insights
4. **Actionable Recommendations**: Provide actionable recommendations
5. **Continuous Learning**: Improve insights based on user feedback

### Wellness Recommendations
1. **Personalization**: Tailor recommendations to user context and preferences
2. **Tier-Appropriate Complexity**: Match recommendation complexity to user tier
3. **Action Items**: Provide clear, actionable items
4. **Progress Tracking**: Track recommendation effectiveness
5. **Continuous Optimization**: Optimize recommendations based on outcomes

### Integration Guidelines
1. **Decorator Usage**: Use decorators for consistent access control
2. **Error Handling**: Implement proper error handling for access denials
3. **User Experience**: Ensure seamless user experience with clear upgrade paths
4. **Performance**: Optimize for performance in high-traffic scenarios
5. **Scalability**: Design for scalability as user base grows

## Troubleshooting

### Common Issues

#### Health Check-in Issues
```python
def debug_health_checkin(user_id: str, checkin_type: str, checkin_data: Dict[str, Any]):
    """Debug health check-in issues"""
    try:
        health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
        result = health_controls.submit_health_checkin(
            user_id, HealthCheckinType(checkin_type), checkin_data
        )
        
        print(f"Health Check-in Debug for {user_id} -> {checkin_type}:")
        print(f"  Success: {result['success']}")
        if not result['success']:
            print(f"  Error: {result['error']}")
            print(f"  Message: {result['message']}")
            print(f"  Upgrade Required: {result.get('upgrade_required', False)}")
            print(f"  Recommended Tier: {result.get('recommended_tier', 'N/A')}")
        else:
            print(f"  Check-in ID: {result['checkin_id']}")
            print(f"  Remaining Check-ins: {result['remaining_checkins']}")
        
    except Exception as e:
        print(f"Error debugging health check-in: {e}")
```

#### Correlation Insights Issues
```python
def debug_correlation_insights(user_id: str, insight_type: str, health_data: Dict[str, Any]):
    """Debug correlation insights issues"""
    try:
        health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
        result = health_controls.get_health_correlation_insights(
            user_id, CorrelationInsightType(insight_type), health_data
        )
        
        print(f"Correlation Insights Debug for {user_id} -> {insight_type}:")
        print(f"  Success: {result['success']}")
        if not result['success']:
            print(f"  Error: {result['error']}")
            print(f"  Message: {result['message']}")
            print(f"  Upgrade Required: {result.get('upgrade_required', False)}")
            print(f"  Recommended Tier: {result.get('recommended_tier', 'N/A')}")
        else:
            print(f"  Insight ID: {result['insight_id']}")
            print(f"  Confidence Score: {result['confidence_score']:.1%}")
            print(f"  Remaining Insights: {result['remaining_insights']}")
        
    except Exception as e:
        print(f"Error debugging correlation insights: {e}")
```

#### Wellness Recommendations Issues
```python
def debug_wellness_recommendations(user_id: str, recommendation_type: str, user_context: Dict[str, Any]):
    """Debug wellness recommendations issues"""
    try:
        health_controls = HealthWellnessControls(db, subscription_service, feature_access_manager)
        result = health_controls.get_wellness_recommendations(
            user_id, WellnessRecommendationType(recommendation_type), user_context
        )
        
        print(f"Wellness Recommendations Debug for {user_id} -> {recommendation_type}:")
        print(f"  Success: {result['success']}")
        if not result['success']:
            print(f"  Error: {result['error']}")
            print(f"  Message: {result['message']}")
            print(f"  Upgrade Required: {result.get('upgrade_required', False)}")
            print(f"  Recommended Tier: {result.get('recommended_tier', 'N/A')}")
        else:
            print(f"  Recommendation ID: {result['recommendation_id']}")
            print(f"  Personalization Level: {result['personalization_level']}")
            print(f"  Remaining Recommendations: {result['remaining_recommendations']}")
        
    except Exception as e:
        print(f"Error debugging wellness recommendations: {e}")
```

## Conclusion

The Health & Wellness Subscription Controls system provides comprehensive subscription gating for MINGUS health and wellness features, ensuring:

- **Tier-Appropriate Limits**: Health check-ins (4/12/unlimited), correlation insights, and wellness recommendations
- **Intelligent Depth Control**: Basic insights for budget tier, advanced insights for higher tiers
- **Personalized Recommendations**: Tailored wellness guidance based on user context and tier
- **Seamless Integration**: Easy integration with existing MINGUS features
- **Clear Upgrade Paths**: Strategic upgrade prompts based on usage and feature needs
- **Comprehensive Analytics**: Detailed usage tracking and optimization insights
- **Performance Optimization**: Efficient processing for high-volume health data
- **Scalable Architecture**: Designed for growth and new health features

This system ensures maximum user satisfaction through proper access control, tier-appropriate feature depth, and clear upgrade paths for health and wellness features. 