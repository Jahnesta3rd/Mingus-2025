# Onboarding Subscription Flow Guide

## Overview

The Onboarding Subscription Flow system provides intelligent tier upgrade prompts during onboarding based on feature usage and optimizes trial upgrade experiences to demonstrate premium features, maximizing conversion rates and user satisfaction.

## Feature Overview

### Purpose
- **Smart Upgrade Prompts**: Trigger tier upgrades based on user behavior and feature usage
- **Trial Experience Optimization**: Demonstrate premium features through strategic trial experiences
- **Conversion Tracking**: Monitor and optimize conversion events throughout onboarding
- **Personalized Recommendations**: Tailor upgrade prompts to user segments and goals
- **Progressive Engagement**: Guide users through natural upgrade progression

### Key Benefits
- **Increased Conversions**: Strategic upgrade prompts at optimal moments
- **Better User Experience**: Seamless trial experiences that demonstrate value
- **Data-Driven Optimization**: Comprehensive analytics for continuous improvement
- **Personalized Journeys**: Customized experiences based on user behavior
- **Revenue Growth**: Optimized conversion paths for maximum revenue

## Onboarding Stages

### Stage Progression
```python
class OnboardingStage(Enum):
    WELCOME = "welcome"                    # Initial welcome and introduction
    PROFILE_SETUP = "profile_setup"        # User profile and preferences
    GOAL_SETTING = "goal_setting"          # Financial goal identification
    FEATURE_EXPLORATION = "feature_exploration"  # Basic feature exploration
    TRIAL_EXPERIENCE = "trial_experience"  # Premium feature trials
    UPGRADE_PROMOTION = "upgrade_promotion"  # Strategic upgrade prompts
    SUBSCRIPTION_SETUP = "subscription_setup"  # Subscription configuration
    COMPLETION = "completion"              # Onboarding completion
```

### Stage Flow
```python
onboarding_stages = [
    OnboardingStage.WELCOME,
    OnboardingStage.PROFILE_SETUP,
    OnboardingStage.GOAL_SETTING,
    OnboardingStage.FEATURE_EXPLORATION,
    OnboardingStage.TRIAL_EXPERIENCE,
    OnboardingStage.UPGRADE_PROMOTION,
    OnboardingStage.SUBSCRIPTION_SETUP,
    OnboardingStage.COMPLETION
]
```

#### Usage Example
```python
# Initialize onboarding
flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
progress = flow_system.initialize_onboarding(user_id, user_data)

# Advance through stages
progress = flow_system.advance_onboarding_stage(user_id, OnboardingStage.PROFILE_SETUP, {
    'profile_completed': True,
    'goals_identified': 3
})

print(f"Current Stage: {progress.current_stage.value}")
print(f"Completed Stages: {[s.value for s in progress.completed_stages]}")
```

## Upgrade Prompts

### Prompt Types

#### Feature Usage Based Prompts
```python
basic_feature_usage_prompt = UpgradePrompt(
    prompt_id='basic_feature_usage',
    trigger_type=UpgradeTrigger.FEATURE_USAGE,
    stage=OnboardingStage.FEATURE_EXPLORATION,
    feature_category=FeatureCategory.BASIC_FEATURES,
    title='Unlock Advanced Financial Tools',
    description='You\'ve mastered the basics! Upgrade to access advanced budgeting, investment tracking, and personalized financial planning.',
    value_proposition='Get 3x more insights and save 5 hours per month on financial planning',
    cta_text='Upgrade to Mid-Tier',
    cta_action='upgrade_to_mid_tier',
    priority=1,
    conditions={
        'min_feature_usage': 3,
        'min_time_spent': 10,
        'required_features': ['budget_tracker', 'expense_categorizer']
    },
    timing={
        'delay_minutes': 5,
        'max_show_count': 2,
        'cooldown_hours': 24
    },
    personalization={
        'dynamic_title': True,
        'goal_alignment': True,
        'usage_based_messaging': True
    }
)
```

#### Value Demonstration Prompts
```python
premium_feature_demo_prompt = UpgradePrompt(
    prompt_id='premium_feature_demo',
    trigger_type=UpgradeTrigger.VALUE_DEMONSTRATION,
    stage=OnboardingStage.TRIAL_EXPERIENCE,
    feature_category=FeatureCategory.PREMIUM_FEATURES,
    title='Experience Premium Financial Planning',
    description='Try our advanced investment analysis, retirement planning, and tax optimization tools for free.',
    value_proposition='See how you could save $2,000+ annually with professional financial planning',
    cta_text='Start Premium Trial',
    cta_action='start_premium_trial',
    priority=2,
    conditions={
        'min_engagement_score': 0.6,
        'goal_alignment_score': 0.5,
        'trial_eligibility': True
    },
    timing={
        'delay_minutes': 2,
        'max_show_count': 1,
        'cooldown_hours': 48
    },
    personalization={
        'goal_based_messaging': True,
        'value_calculation': True,
        'social_proof': True
    }
)
```

#### Goal Alignment Prompts
```python
goal_alignment_prompt = UpgradePrompt(
    prompt_id='goal_alignment_upgrade',
    trigger_type=UpgradeTrigger.GOAL_ALIGNMENT,
    stage=OnboardingStage.GOAL_SETTING,
    feature_category=FeatureCategory.ADVANCED_FEATURES,
    title='Achieve Your Financial Goals Faster',
    description='Your goals require advanced planning tools. Upgrade to get personalized strategies and expert guidance.',
    value_proposition='Reach your goals 40% faster with professional planning tools',
    cta_text='Get Professional Planning',
    cta_action='upgrade_to_professional',
    priority=3,
    conditions={
        'goal_complexity_score': 0.7,
        'goal_value': 50000,
        'planning_need_score': 0.8
    },
    timing={
        'delay_minutes': 3,
        'max_show_count': 2,
        'cooldown_hours': 72
    },
    personalization={
        'goal_specific_messaging': True,
        'timeline_calculation': True,
        'roi_demonstration': True
    }
)
```

### Prompt Trigger Types
```python
class UpgradeTrigger(Enum):
    FEATURE_USAGE = "feature_usage"           # Based on feature usage patterns
    GOAL_ALIGNMENT = "goal_alignment"         # Based on goal complexity and value
    USAGE_PATTERN = "usage_pattern"           # Based on usage behavior patterns
    TIME_BASED = "time_based"                 # Based on time spent in onboarding
    ENGAGEMENT_LEVEL = "engagement_level"     # Based on engagement scores
    VALUE_DEMONSTRATION = "value_demonstration"  # Based on value demonstrated
```

### Prompt Conditions
```python
def _check_prompt_conditions(self, prompt: UpgradePrompt, progress: OnboardingProgress, context: Dict[str, Any] = None) -> bool:
    """Check if prompt conditions are met"""
    conditions = prompt.conditions
    
    # Check feature usage conditions
    if 'min_feature_usage' in conditions:
        total_usage = sum(progress.feature_usage.values())
        if total_usage < conditions['min_feature_usage']:
            return False
    
    # Check time spent conditions
    if 'min_time_spent' in conditions:
        if progress.total_time_spent < conditions['min_time_spent']:
            return False
    
    # Check required features
    if 'required_features' in conditions:
        for feature in conditions['required_features']:
            if feature not in progress.feature_usage:
                return False
    
    # Check engagement score
    if 'min_engagement_score' in conditions:
        engagement_score = self._calculate_engagement_score(progress)
        if engagement_score < conditions['min_engagement_score']:
            return False
    
    # Check goal alignment
    if 'goal_alignment_score' in conditions:
        goal_alignment = self._calculate_goal_alignment_score(progress)
        if goal_alignment < conditions['goal_alignment_score']:
            return False
    
    return True
```

### Usage Example
```python
# Get upgrade prompts
upgrade_prompts = flow_system.get_upgrade_prompts(user_id, {
    'feature_id': 'budget_tracker',
    'time_spent': 15,
    'engagement_score': 0.7
})

for prompt in upgrade_prompts:
    print(f"Prompt: {prompt.title}")
    print(f"Description: {prompt.description}")
    print(f"Value Proposition: {prompt.value_proposition}")
    print(f"CTA: {prompt.cta_text}")
    print(f"Priority: {prompt.priority}")
```

## Trial Feature Experience

### Trial Feature Types

#### Feature Preview Trials
```python
investment_analysis_trial = TrialFeature(
    feature_id='investment_analysis',
    name='Investment Portfolio Analysis',
    description='Get a comprehensive analysis of your investment portfolio with optimization recommendations',
    category=FeatureCategory.PREMIUM_FEATURES,
    trial_type=TrialExperience.FEATURE_PREVIEW,
    duration_minutes=30,
    usage_limit=1,
    value_demonstration='See how you could improve your portfolio returns by 15%',
    upgrade_path='mid_tier',
    engagement_metrics=['time_spent', 'interactions', 'savings_calculated']
)
```

#### Limited Access Trials
```python
retirement_planner_trial = TrialFeature(
    feature_id='retirement_planner',
    name='Retirement Planning Suite',
    description='Plan your retirement with advanced tools and personalized strategies',
    category=FeatureCategory.ADVANCED_FEATURES,
    trial_type=TrialExperience.LIMITED_ACCESS,
    duration_minutes=60,
    usage_limit=3,
    value_demonstration='Discover how to retire 5 years earlier with optimal planning',
    upgrade_path='professional',
    engagement_metrics=['goals_created', 'scenarios_explored', 'savings_identified']
)
```

#### Value Demonstration Trials
```python
tax_optimizer_trial = TrialFeature(
    feature_id='tax_optimizer',
    name='Tax Optimization Tools',
    description='Optimize your tax strategy and identify potential savings opportunities',
    category=FeatureCategory.PROFESSIONAL_FEATURES,
    trial_type=TrialExperience.VALUE_DEMONSTRATION,
    duration_minutes=45,
    usage_limit=2,
    value_demonstration='Find $1,500+ in potential tax savings',
    upgrade_path='professional',
    engagement_metrics=['savings_calculated', 'strategies_explored', 'confidence_score']
)
```

### Trial Experience Types
```python
class TrialExperience(Enum):
    FEATURE_PREVIEW = "feature_preview"           # Preview of feature capabilities
    LIMITED_ACCESS = "limited_access"             # Limited access to full feature
    TIME_LIMITED = "time_limited"                 # Time-limited access
    USAGE_LIMITED = "usage_limited"               # Usage-limited access
    VALUE_DEMONSTRATION = "value_demonstration"   # Demonstrate specific value
```

### Trial Management
```python
# Start trial feature
trial_result = flow_system.start_trial_feature(user_id, 'investment_analysis')

print(f"Trial Started: {trial_result['trial_started']}")
print(f"Feature Name: {trial_result['feature_name']}")
print(f"Duration: {trial_result['duration_minutes']} minutes")
print(f"Usage Limit: {trial_result['usage_limit']}")
print(f"Value Demonstration: {trial_result['value_demonstration']}")
print(f"Upgrade Path: {trial_result['upgrade_path']}")

# Track trial usage
usage_result = flow_system.track_trial_usage(user_id, 'investment_analysis', {
    'time_spent': 600,
    'interactions': 25,
    'savings_calculated': 2500
})

print(f"Trial Active: {usage_result['trial_active']}")
print(f"Usage Count: {usage_result['usage_count']}")
print(f"Value Demonstrated: {usage_result['value_demonstrated']:.1%}")
print(f"Conversion Triggered: {usage_result['conversion_triggered']}")
```

## Feature Usage Tracking

### Feature Categories
```python
class FeatureCategory(Enum):
    BASIC_FEATURES = "basic_features"           # Budget tracking, expense categorization
    PREMIUM_FEATURES = "premium_features"       # Investment analysis, portfolio tracking
    ADVANCED_FEATURES = "advanced_features"     # Retirement planning, tax optimization
    PROFESSIONAL_FEATURES = "professional_features"  # Estate planning, comprehensive advisory
```

### Feature Definitions
```python
features = {
    'budget_tracker': {
        'name': 'Budget Tracker',
        'category': FeatureCategory.BASIC_FEATURES,
        'tier': 'budget',
        'value_score': 0.7
    },
    'expense_categorizer': {
        'name': 'Expense Categorizer',
        'category': FeatureCategory.BASIC_FEATURES,
        'tier': 'budget',
        'value_score': 0.6
    },
    'investment_analysis': {
        'name': 'Investment Analysis',
        'category': FeatureCategory.PREMIUM_FEATURES,
        'tier': 'mid_tier',
        'value_score': 0.9
    },
    'retirement_planner': {
        'name': 'Retirement Planner',
        'category': FeatureCategory.ADVANCED_FEATURES,
        'tier': 'mid_tier',
        'value_score': 0.95
    },
    'tax_optimizer': {
        'name': 'Tax Optimizer',
        'category': FeatureCategory.PROFESSIONAL_FEATURES,
        'tier': 'professional',
        'value_score': 0.9
    }
}
```

### Usage Tracking
```python
# Track feature usage
result = flow_system.track_feature_usage(user_id, 'budget_tracker', {
    'time_spent': 300,
    'interactions': 15,
    'data_entered': True
})

print(f"Feature Usage Count: {result['feature_usage_count']}")
print(f"Feature Category: {result['feature_category']}")
print(f"Upgrade Prompts Available: {len(result['upgrade_prompts_available'])}")
```

## Conversion Tracking

### Conversion Event Processing
```python
# Process upgrade conversion
conversion_result = flow_system.process_upgrade_conversion(user_id, 'basic_feature_usage', {
    'action': 'upgrade_to_mid_tier',
    'offer_amount': 24.99,
    'offer_currency': 'USD',
    'conversion_source': 'feature_usage_prompt',
    'user_segment': 'intermediate',
    'engagement_score': 0.75
})

print(f"Conversion Recorded: {conversion_result['conversion_recorded']}")
print(f"Prompt ID: {conversion_result['prompt_id']}")
print(f"Stage: {conversion_result['stage']}")
print(f"Next Action: {conversion_result['next_action']}")
```

### Conversion Triggers
```python
def _check_conversion_trigger(self, progress: OnboardingProgress, feature_id: str, value_demonstrated: float) -> bool:
    """Check if conversion should be triggered"""
    triggers = self.config.conversion_triggers
    
    # Check value demonstration threshold
    if value_demonstrated >= triggers['value_demonstration_threshold']:
        return True
    
    # Check engagement score
    engagement_score = self._calculate_engagement_score(progress)
    if engagement_score >= triggers['engagement_score']:
        return True
    
    return False
```

## Personalization

### User Segmentation
```python
def _determine_user_segment(self, user_data: Dict[str, Any]) -> str:
    """Determine user segment based on user data"""
    financial_knowledge = user_data.get('financial_knowledge', 'beginner')
    income_level = user_data.get('income_level', 'medium')
    goals_complexity = user_data.get('goals_complexity', 'basic')
    
    if financial_knowledge == 'advanced' or income_level == 'high':
        return 'advanced'
    elif financial_knowledge == 'intermediate' or goals_complexity == 'complex':
        return 'intermediate'
    else:
        return 'beginner'
```

### Dynamic Personalization
```python
def _personalize_single_prompt(self, prompt: UpgradePrompt, progress: OnboardingProgress, context: Dict[str, Any] = None) -> UpgradePrompt:
    """Personalize a single upgrade prompt"""
    personalized = UpgradePrompt(...)  # Create copy
    
    # Personalize title
    if prompt.personalization.get('dynamic_title'):
        personalized.title = self._generate_dynamic_title(prompt, progress, context)
    
    # Personalize description
    if prompt.personalization.get('goal_alignment'):
        personalized.description = self._generate_goal_aligned_description(prompt, progress, context)
    
    # Personalize value proposition
    if prompt.personalization.get('value_calculation'):
        personalized.value_proposition = self._calculate_personalized_value(prompt, progress, context)
    
    return personalized_prompt
```

### Personalization Examples
```python
# Dynamic title generation
def _generate_dynamic_title(self, prompt: UpgradePrompt, progress: OnboardingProgress, context: Dict[str, Any] = None) -> str:
    user_segment = progress.metadata.get('user_segment', 'beginner')
    
    if user_segment == 'beginner':
        return f"Ready for the Next Level? {prompt.title}"
    elif user_segment == 'intermediate':
        return f"Take Your Planning Further - {prompt.title}"
    else:
        return f"Professional Tools Await - {prompt.title}"

# Goal-aligned description
def _generate_goal_aligned_description(self, prompt: UpgradePrompt, progress: OnboardingProgress, context: Dict[str, Any] = None) -> str:
    goals = progress.goals_set
    if not goals:
        return prompt.description
    
    primary_goal = goals[0] if goals else "financial success"
    return f"Your goal of {primary_goal} requires advanced tools. {prompt.description}"

# Personalized value calculation
def _calculate_personalized_value(self, prompt: UpgradePrompt, progress: OnboardingProgress, context: Dict[str, Any] = None) -> str:
    base_value = 1000
    user_segment = progress.metadata.get('user_segment', 'beginner')
    
    if user_segment == 'advanced':
        base_value = 3000
    elif user_segment == 'intermediate':
        base_value = 2000
    
    return f"See how you could save ${base_value:,}+ annually with {prompt.feature_category.value.replace('_', ' ')}"
```

## Analytics and Insights

### Onboarding Analytics
```python
# Get comprehensive analytics
analytics = flow_system.get_onboarding_analytics(user_id)

print(f"Current Stage: {analytics['current_stage']}")
print(f"Completed Stages: {len(analytics['completed_stages'])}")
print(f"Total Time Spent: {analytics['total_time_spent']} minutes")

# Feature usage summary
usage_summary = analytics['feature_usage_summary']
print(f"Total Usage: {usage_summary['total_usage']}")
print(f"Unique Features: {usage_summary['unique_features']}")
print(f"Category Breakdown: {usage_summary['category_breakdown']}")
print(f"Most Used Feature: {usage_summary['most_used_feature']}")

# Conversion metrics
print(f"Upgrade Prompts Shown: {analytics['upgrade_prompts_shown']}")
print(f"Trial Features Accessed: {analytics['trial_features_accessed']}")
print(f"Conversion Events: {analytics['conversion_events']}")
print(f"Engagement Score: {analytics['engagement_score']:.1%}")
print(f"Conversion Probability: {analytics['conversion_probability']:.1%}")

# Recommended actions
print("Recommended Actions:")
for action in analytics['recommended_actions']:
    print(f"  - {action}")
```

### Engagement Scoring
```python
def _calculate_engagement_score(self, progress: OnboardingProgress) -> float:
    """Calculate user engagement score"""
    feature_usage = len(progress.feature_usage)
    time_spent = progress.total_time_spent
    goals_set = len(progress.goals_set)
    
    engagement_score = (
        min(1.0, feature_usage / 5) * 0.4 +
        min(1.0, time_spent / 30) * 0.3 +
        min(1.0, goals_set / 3) * 0.3
    )
    
    return engagement_score
```

### Conversion Probability
```python
def _calculate_conversion_probability(self, progress: OnboardingProgress) -> float:
    """Calculate conversion probability"""
    engagement_score = self._calculate_engagement_score(progress)
    upgrade_prompts_shown = len(progress.upgrade_prompts_shown)
    trial_features_accessed = len(progress.trial_features_accessed)
    
    conversion_probability = (
        engagement_score * 0.5 +
        min(1.0, upgrade_prompts_shown / 3) * 0.3 +
        min(1.0, trial_features_accessed / 2) * 0.2
    )
    
    return conversion_probability
```

## Configuration Options

### Subscription Flow Configuration
```python
@dataclass
class SubscriptionFlowConfig:
    onboarding_stages: List[OnboardingStage] = None
    upgrade_prompts: Dict[str, UpgradePrompt] = None
    trial_features: Dict[str, TrialFeature] = None
    conversion_triggers: Dict[str, Any] = None
    personalization_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conversion_triggers is None:
            self.conversion_triggers = {
                'feature_usage_threshold': 3,
                'time_spent_threshold': 15,  # minutes
                'goal_alignment_score': 0.7,
                'engagement_score': 0.8,
                'value_demonstration_threshold': 0.6
            }
        
        if self.personalization_rules is None:
            self.personalization_rules = {
                'user_segment_weights': {
                    'beginner': 0.3,
                    'intermediate': 0.5,
                    'advanced': 0.2
                },
                'feature_preferences': {
                    'investment_focused': ['investment_analysis', 'portfolio_tracking'],
                    'debt_focused': ['debt_tracker', 'payment_optimizer'],
                    'savings_focused': ['savings_goals', 'budget_tracker'],
                    'retirement_focused': ['retirement_planner', 'social_security_optimizer']
                }
            }
```

## Integration Examples

### API Integration
```python
def api_initialize_onboarding(user_id: str, user_data: Dict[str, Any]):
    """API endpoint for onboarding initialization"""
    flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
    
    progress = flow_system.initialize_onboarding(user_id, user_data)
    
    return {
        'success': True,
        'onboarding_progress': {
            'user_id': progress.user_id,
            'current_stage': progress.current_stage.value,
            'completed_stages': [stage.value for stage in progress.completed_stages],
            'user_segment': progress.metadata['user_segment']
        }
    }

def api_track_feature_usage(user_id: str, feature_id: str, usage_data: Dict[str, Any]):
    """API endpoint for feature usage tracking"""
    flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
    
    result = flow_system.track_feature_usage(user_id, feature_id, usage_data)
    
    return {
        'success': True,
        'feature_usage': {
            'usage_count': result['feature_usage_count'],
            'feature_category': result['feature_category'],
            'upgrade_prompts_available': len(result['upgrade_prompts_available'])
        }
    }

def api_get_upgrade_prompts(user_id: str, context: Dict[str, Any] = None):
    """API endpoint for upgrade prompts"""
    flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
    
    prompts = flow_system.get_upgrade_prompts(user_id, context)
    
    return {
        'success': True,
        'upgrade_prompts': [
            {
                'prompt_id': prompt.prompt_id,
                'title': prompt.title,
                'description': prompt.description,
                'value_proposition': prompt.value_proposition,
                'cta_text': prompt.cta_text,
                'cta_action': prompt.cta_action,
                'priority': prompt.priority
            }
            for prompt in prompts
        ]
    }

def api_start_trial_feature(user_id: str, feature_id: str):
    """API endpoint for starting trial features"""
    flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
    
    result = flow_system.start_trial_feature(user_id, feature_id)
    
    return {
        'success': result['trial_started'],
        'trial_feature': {
            'feature_name': result['feature_name'],
            'duration_minutes': result['duration_minutes'],
            'usage_limit': result['usage_limit'],
            'value_demonstration': result['value_demonstration'],
            'upgrade_path': result['upgrade_path']
        }
    }

def api_process_conversion(user_id: str, prompt_id: str, conversion_data: Dict[str, Any]):
    """API endpoint for processing conversions"""
    flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
    
    result = flow_system.process_upgrade_conversion(user_id, prompt_id, conversion_data)
    
    return {
        'success': result['conversion_recorded'],
        'conversion': {
            'prompt_id': result['prompt_id'],
            'stage': result['stage'],
            'next_action': result['next_action']
        }
    }

def api_get_onboarding_analytics(user_id: str):
    """API endpoint for onboarding analytics"""
    flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
    
    analytics = flow_system.get_onboarding_analytics(user_id)
    
    return {
        'success': True,
        'analytics': analytics
    }
```

### Frontend Integration
```javascript
// Initialize onboarding
async function initializeOnboarding(userId, userData) {
    const response = await fetch('/api/onboarding/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            user_data: userData
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.onboarding_progress;
    }
}

// Track feature usage
async function trackFeatureUsage(userId, featureId, usageData) {
    const response = await fetch('/api/onboarding/track-feature-usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            feature_id: featureId,
            usage_data: usageData
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.feature_usage;
    }
}

// Get upgrade prompts
async function getUpgradePrompts(userId, context = null) {
    const response = await fetch('/api/onboarding/upgrade-prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            context: context
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.upgrade_prompts;
    }
    return [];
}

// Start trial feature
async function startTrialFeature(userId, featureId) {
    const response = await fetch('/api/onboarding/start-trial', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            feature_id: featureId
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.trial_feature;
    }
}

// Process conversion
async function processConversion(userId, promptId, conversionData) {
    const response = await fetch('/api/onboarding/process-conversion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            prompt_id: promptId,
            conversion_data: conversionData
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.conversion;
    }
}

// Get analytics
async function getOnboardingAnalytics(userId) {
    const response = await fetch(`/api/onboarding/analytics?user_id=${userId}`);
    const result = await response.json();
    
    if (result.success) {
        return result.analytics;
    }
    return {};
}

// Example usage
async function completeOnboardingJourney(userId) {
    // Initialize onboarding
    const progress = await initializeOnboarding(userId, {
        financial_knowledge: 'intermediate',
        income_level: 'medium',
        goals_complexity: 'moderate'
    });
    
    console.log(`Onboarding started for user ${userId}`);
    console.log(`Current stage: ${progress.current_stage}`);
    console.log(`User segment: ${progress.user_segment}`);
    
    // Track feature usage
    const usageResult = await trackFeatureUsage(userId, 'budget_tracker', {
        time_spent: 300,
        interactions: 15
    });
    
    console.log(`Feature usage tracked: ${usageResult.usage_count}`);
    
    // Get upgrade prompts
    const prompts = await getUpgradePrompts(userId, {
        feature_id: 'budget_tracker',
        time_spent: 15
    });
    
    if (prompts.length > 0) {
        console.log(`Upgrade prompts available: ${prompts.length}`);
        prompts.forEach(prompt => {
            console.log(`  - ${prompt.title}: ${prompt.value_proposition}`);
        });
    }
    
    // Start trial feature
    const trialResult = await startTrialFeature(userId, 'investment_analysis');
    if (trialResult) {
        console.log(`Trial started: ${trialResult.feature_name}`);
        console.log(`Duration: ${trialResult.duration_minutes} minutes`);
        console.log(`Value demonstration: ${trialResult.value_demonstration}`);
    }
    
    // Get analytics
    const analytics = await getOnboardingAnalytics(userId);
    console.log(`Engagement score: ${(analytics.engagement_score * 100).toFixed(1)}%`);
    console.log(`Conversion probability: ${(analytics.conversion_probability * 100).toFixed(1)}%`);
}
```

## Best Practices

### Onboarding Design
1. **Progressive Disclosure**: Reveal features gradually based on user readiness
2. **Value Demonstration**: Show concrete value before asking for upgrades
3. **Personalized Timing**: Trigger prompts at optimal moments for each user
4. **Clear Progression**: Provide clear upgrade paths and next steps
5. **Engagement Tracking**: Monitor user engagement to optimize timing

### Upgrade Prompt Optimization
1. **Contextual Triggers**: Base prompts on user behavior and needs
2. **Value-First Messaging**: Lead with value before asking for commitment
3. **Personalized Content**: Tailor messaging to user segment and goals
4. **Strategic Timing**: Show prompts when users are most receptive
5. **A/B Testing**: Continuously test and optimize prompt effectiveness

### Trial Experience Design
1. **Value Demonstration**: Focus on demonstrating concrete value
2. **Limited Scope**: Provide enough access to show value without overwhelming
3. **Clear Upgrade Path**: Make the path to full access obvious
4. **Engagement Tracking**: Monitor trial usage to optimize conversion
5. **Seamless Transition**: Make upgrade process smooth and frictionless

### Conversion Optimization
1. **Multiple Touchpoints**: Provide upgrade opportunities throughout journey
2. **Value Accumulation**: Build value demonstration over time
3. **Social Proof**: Include testimonials and success stories
4. **Urgency Creation**: Use time-limited offers strategically
5. **Friction Reduction**: Minimize barriers to conversion

### Analytics and Optimization
1. **Comprehensive Tracking**: Monitor all user interactions and behaviors
2. **Conversion Funnel Analysis**: Identify and optimize conversion bottlenecks
3. **A/B Testing**: Continuously test different approaches
4. **Personalization Optimization**: Refine personalization based on results
5. **Performance Monitoring**: Track system performance and optimize

## Troubleshooting

### Common Issues

#### Onboarding Initialization Issues
```python
def debug_onboarding_initialization(user_id: str, user_data: Dict[str, Any]):
    """Debug onboarding initialization issues"""
    try:
        flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
        progress = flow_system.initialize_onboarding(user_id, user_data)
        print(f"Onboarding initialized successfully for user {user_id}")
        print(f"Current Stage: {progress.current_stage.value}")
        print(f"User Segment: {progress.metadata['user_segment']}")
    except Exception as e:
        print(f"Onboarding initialization failed: {e}")
```

#### Feature Usage Tracking Issues
```python
def debug_feature_usage_tracking(user_id: str, feature_id: str, usage_data: Dict[str, Any]):
    """Debug feature usage tracking issues"""
    try:
        flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
        result = flow_system.track_feature_usage(user_id, feature_id, usage_data)
        print(f"Feature usage tracked successfully for user {user_id}")
        print(f"Usage Count: {result['feature_usage_count']}")
        print(f"Feature Category: {result['feature_category']}")
        print(f"Upgrade Prompts: {len(result['upgrade_prompts_available'])}")
    except Exception as e:
        print(f"Feature usage tracking failed: {e}")
```

#### Upgrade Prompt Issues
```python
def debug_upgrade_prompts(user_id: str, context: Dict[str, Any] = None):
    """Debug upgrade prompt issues"""
    try:
        flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
        prompts = flow_system.get_upgrade_prompts(user_id, context)
        print(f"Upgrade prompts retrieved successfully for user {user_id}")
        print(f"Available Prompts: {len(prompts)}")
        for prompt in prompts:
            print(f"  - {prompt.title}: {prompt.trigger_type.value}")
    except Exception as e:
        print(f"Upgrade prompt retrieval failed: {e}")
```

#### Trial Feature Issues
```python
def debug_trial_features(user_id: str, feature_id: str):
    """Debug trial feature issues"""
    try:
        flow_system = OnboardingSubscriptionFlow(db, subscription_service, analytics_service, notification_service)
        result = flow_system.start_trial_feature(user_id, feature_id)
        print(f"Trial feature started successfully for user {user_id}")
        print(f"Feature: {result['feature_name']}")
        print(f"Duration: {result['duration_minutes']} minutes")
        print(f"Usage Limit: {result['usage_limit']}")
    except Exception as e:
        print(f"Trial feature start failed: {e}")
```

## Conclusion

The Onboarding Subscription Flow system provides comprehensive tier upgrade prompts and trial experience optimization, enabling:

- **Smart Upgrade Prompts**: Contextual prompts based on user behavior and needs
- **Optimized Trial Experiences**: Strategic value demonstration through trials
- **Comprehensive Conversion Tracking**: Monitor and optimize conversion events
- **Personalized Journeys**: Customized experiences based on user segments
- **Data-Driven Optimization**: Analytics for continuous improvement
- **Seamless Integration**: Easy API and frontend integration
- **Scalable Architecture**: Production-ready implementation

This system ensures users receive the most appropriate upgrade prompts at optimal moments, maximizing conversion rates while providing valuable trial experiences that demonstrate premium feature benefits. 