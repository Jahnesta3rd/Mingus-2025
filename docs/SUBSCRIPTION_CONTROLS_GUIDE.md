# Subscription Controls Guide

## Overview

The Subscription Controls system provides comprehensive integration between subscription controls and all MINGUS application features to ensure proper tier access and upgrade prompts. It manages feature access, usage limits, upgrade recommendations, and seamless integration with the application.

## Feature Overview

### Purpose
- **Feature Access Control**: Ensure users can only access features appropriate for their subscription tier
- **Usage Limit Management**: Track and enforce usage limits for different features
- **Upgrade Prompt Generation**: Create intelligent upgrade prompts based on user behavior
- **Analytics Integration**: Provide comprehensive analytics for feature usage and optimization
- **Seamless Integration**: Integrate with all MINGUS application features

### Key Benefits
- **Tier-Based Access**: Proper access control based on subscription levels
- **Usage Optimization**: Intelligent usage tracking and limit enforcement
- **Conversion Optimization**: Strategic upgrade prompts to maximize conversions
- **User Experience**: Seamless feature access with clear upgrade paths
- **Analytics Insights**: Comprehensive usage analytics for optimization

## Feature Categories

### Budgeting Features
```python
class FeatureCategory(Enum):
    BUDGETING = "budgeting"           # Budget tracking and management
    INVESTMENT = "investment"         # Investment analysis and tracking
    RETIREMENT = "retirement"         # Retirement planning tools
    TAX_OPTIMIZATION = "tax_optimization"  # Tax optimization features
    DEBT_MANAGEMENT = "debt_management"    # Debt management tools
    INSURANCE = "insurance"           # Insurance planning
    ESTATE_PLANNING = "estate_planning"    # Estate planning features
    ANALYTICS = "analytics"           # Financial analytics
    REPORTING = "reporting"           # Reporting features
    EXPORT = "export"                 # Data export features
    API_ACCESS = "api_access"         # API access features
    PREMIUM_SUPPORT = "premium_support"     # Support features
```

### Access Levels
```python
class AccessLevel(Enum):
    FREE = "free"                     # Free tier access
    BASIC = "basic"                   # Basic tier access
    PREMIUM = "premium"               # Premium tier access
    PROFESSIONAL = "professional"     # Professional tier access
    ENTERPRISE = "enterprise"         # Enterprise tier access
```

## Feature Definitions

### Budgeting Features
```python
# Budget Tracker - Free Tier
'budget_tracker': FeatureDefinition(
    feature_id='budget_tracker',
    name='Budget Tracker',
    description='Track income and expenses with detailed categorization',
    category=FeatureCategory.BUDGETING,
    access_level=AccessLevel.FREE,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'transactions_per_month': 100, 'categories': 10},
    upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
    dependencies=[]
)

# Expense Categorizer - Basic Tier
'expense_categorizer': FeatureDefinition(
    feature_id='expense_categorizer',
    name='Expense Categorizer',
    description='Automatically categorize expenses with AI',
    category=FeatureCategory.BUDGETING,
    access_level=AccessLevel.BASIC,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'categorizations_per_month': 500},
    upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
    dependencies=['budget_tracker']
)

# Savings Goals - Basic Tier
'savings_goals': FeatureDefinition(
    feature_id='savings_goals',
    name='Savings Goals',
    description='Set and track savings goals with progress visualization',
    category=FeatureCategory.BUDGETING,
    access_level=AccessLevel.BASIC,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'goals': 5, 'goal_amount': 10000},
    upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
    dependencies=['budget_tracker']
)
```

### Investment Features
```python
# Investment Analysis - Premium Tier
'investment_analysis': FeatureDefinition(
    feature_id='investment_analysis',
    name='Investment Analysis',
    description='Analyze investment opportunities and portfolio performance',
    category=FeatureCategory.INVESTMENT,
    access_level=AccessLevel.PREMIUM,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'analyses_per_month': 10, 'portfolios': 3},
    upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
    dependencies=['budget_tracker']
)

# Portfolio Tracker - Premium Tier
'portfolio_tracker': FeatureDefinition(
    feature_id='portfolio_tracker',
    name='Portfolio Tracker',
    description='Track investment portfolio with real-time updates',
    category=FeatureCategory.INVESTMENT,
    access_level=AccessLevel.PREMIUM,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'portfolios': 5, 'holdings_per_portfolio': 50},
    upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
    dependencies=['investment_analysis']
)

# Risk Assessment - Professional Tier
'risk_assessment': FeatureDefinition(
    feature_id='risk_assessment',
    name='Risk Assessment',
    description='Assess investment risk tolerance and portfolio risk',
    category=FeatureCategory.INVESTMENT,
    access_level=AccessLevel.PROFESSIONAL,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'assessments_per_month': 5},
    upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
    dependencies=['portfolio_tracker']
)
```

### Retirement Features
```python
# Retirement Planner - Premium Tier
'retirement_planner': FeatureDefinition(
    feature_id='retirement_planner',
    name='Retirement Planner',
    description='Plan for retirement with comprehensive analysis',
    category=FeatureCategory.RETIREMENT,
    access_level=AccessLevel.PREMIUM,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'plans': 3, 'scenarios_per_plan': 5},
    upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
    dependencies=['budget_tracker']
)

# Social Security Optimizer - Professional Tier
'social_security_optimizer': FeatureDefinition(
    feature_id='social_security_optimizer',
    name='Social Security Optimizer',
    description='Optimize Social Security claiming strategy',
    category=FeatureCategory.RETIREMENT,
    access_level=AccessLevel.PROFESSIONAL,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'optimizations_per_month': 3},
    upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
    dependencies=['retirement_planner']
)
```

### Tax Optimization Features
```python
# Tax Optimizer - Professional Tier
'tax_optimizer': FeatureDefinition(
    feature_id='tax_optimizer',
    name='Tax Optimizer',
    description='Optimize tax strategy and identify deductions',
    category=FeatureCategory.TAX_OPTIMIZATION,
    access_level=AccessLevel.PROFESSIONAL,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'optimizations_per_year': 10},
    upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
    dependencies=['budget_tracker', 'investment_analysis']
)

# Tax Loss Harvesting - Professional Tier
'tax_loss_harvesting': FeatureDefinition(
    feature_id='tax_loss_harvesting',
    name='Tax Loss Harvesting',
    description='Identify tax loss harvesting opportunities',
    category=FeatureCategory.TAX_OPTIMIZATION,
    access_level=AccessLevel.PROFESSIONAL,
    status=FeatureStatus.AVAILABLE,
    usage_limits={'harvests_per_year': 12},
    upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
    dependencies=['portfolio_tracker', 'tax_optimizer']
)
```

## Feature Access Control

### Access Level Checking
```python
def _check_access_level(self, user_tier: str, required_level: AccessLevel) -> bool:
    """Check if user tier meets required access level"""
    tier_hierarchy = {
        'free': 0,
        'basic': 1,
        'premium': 2,
        'professional': 3,
        'enterprise': 4
    }
    
    user_level = tier_hierarchy.get(user_tier, 0)
    required_level_value = tier_hierarchy.get(required_level.value, 0)
    
    return user_level >= required_level_value
```

### Usage Example
```python
# Check feature access
access_result = feature_manager.check_feature_access(user_id, 'investment_analysis')

if access_result['has_access']:
    print("User has access to investment analysis")
else:
    print(f"Access denied: {access_result['reason']}")
    if access_result['upgrade_required']:
        print(f"Upgrade to {access_result['recommended_tier']} required")
```

### Complete Access Check
```python
def check_feature_access(self, user_id: str, feature_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Check if user has access to a feature"""
    # Get user subscription
    subscription = self.subscription_service.get_user_subscription(user_id)
    user_tier = subscription.get('plan_id', 'free')
    
    # Get feature definition
    feature_def = self.feature_definitions.get(feature_id)
    if not feature_def:
        return {
            'has_access': False,
            'reason': 'feature_not_found',
            'upgrade_required': False,
            'trial_available': False
        }
    
    # Check basic access level
    has_access = self._check_access_level(user_tier, feature_def.access_level)
    
    if not has_access:
        return {
            'has_access': False,
            'reason': 'upgrade_required',
            'upgrade_required': True,
            'trial_available': feature_def.status == FeatureStatus.TRIAL_AVAILABLE,
            'recommended_tier': feature_def.access_level.value
        }
    
    # Check usage limits
    usage_check = self._check_usage_limits(user_id, feature_id, feature_def)
    if not usage_check['within_limits']:
        return {
            'has_access': False,
            'reason': 'usage_limit_exceeded',
            'upgrade_required': True,
            'trial_available': False,
            'current_usage': usage_check['current_usage'],
            'usage_limit': usage_check['usage_limit']
        }
    
    # Check dependencies
    dependency_check = self._check_dependencies(user_id, feature_def.dependencies)
    if not dependency_check['all_available']:
        return {
            'has_access': False,
            'reason': 'dependency_not_met',
            'upgrade_required': True,
            'trial_available': False,
            'missing_dependencies': dependency_check['missing_dependencies']
        }
    
    # Update usage tracking
    self._track_feature_usage(user_id, feature_id, context)
    
    return {
        'has_access': True,
        'reason': 'access_granted',
        'upgrade_required': False,
        'trial_available': False,
        'current_usage': usage_check['current_usage'],
        'usage_limit': usage_check['usage_limit']
    }
```

## User Features Management

### Get User Features
```python
def get_user_features(self, user_id: str) -> Dict[str, Any]:
    """Get all features available to user"""
    subscription = self.subscription_service.get_user_subscription(user_id)
    user_tier = subscription.get('plan_id', 'free')
    
    features = {
        'available_features': [],
        'restricted_features': [],
        'trial_features': [],
        'upgrade_recommendations': []
    }
    
    for feature_id, feature_def in self.feature_definitions.items():
        access_check = self.check_feature_access(user_id, feature_id)
        
        if access_check['has_access']:
            features['available_features'].append({
                'feature_id': feature_id,
                'name': feature_def.name,
                'description': feature_def.description,
                'category': feature_def.category.value,
                'current_usage': access_check.get('current_usage', {}),
                'usage_limit': access_check.get('usage_limit', {})
            })
        elif access_check['trial_available']:
            features['trial_features'].append({
                'feature_id': feature_id,
                'name': feature_def.name,
                'description': feature_def.description,
                'category': feature_def.category.value,
                'recommended_tier': feature_def.access_level.value
            })
        else:
            features['restricted_features'].append({
                'feature_id': feature_id,
                'name': feature_def.name,
                'description': feature_def.description,
                'category': feature_def.category.value,
                'recommended_tier': feature_def.access_level.value,
                'upgrade_required': access_check['upgrade_required']
            })
    
    # Generate upgrade recommendations
    features['upgrade_recommendations'] = self._generate_upgrade_recommendations(user_id, features)
    
    return features
```

### Usage Example
```python
# Get user features
features = feature_manager.get_user_features(user_id)

print(f"Available Features: {len(features['available_features'])}")
print(f"Restricted Features: {len(features['restricted_features'])}")
print(f"Trial Features: {len(features['trial_features'])}")
print(f"Upgrade Recommendations: {len(features['upgrade_recommendations'])}")

# Show available features
for feature in features['available_features']:
    print(f"- {feature['name']} ({feature['category']})")

# Show restricted features
for feature in features['restricted_features']:
    print(f"- {feature['name']} -> {feature['recommended_tier']}")
```

## Upgrade Prompts

### Upgrade Trigger Types
```python
class UpgradeTrigger(Enum):
    FEATURE_ACCESS = "feature_access"       # User tries to access restricted feature
    USAGE_LIMIT = "usage_limit"             # User hits usage limit
    DATA_LIMIT = "data_limit"               # User hits data limit
    EXPORT_LIMIT = "export_limit"           # User hits export limit
    API_LIMIT = "api_limit"                 # User hits API limit
    SUPPORT_LIMIT = "support_limit"         # User hits support limit
    CUSTOMIZATION_LIMIT = "customization_limit"  # User hits customization limit
```

### Create Upgrade Prompt
```python
def create_upgrade_prompt(self, user_id: str, feature_id: str, trigger_type: UpgradeTrigger, context: Dict[str, Any] = None) -> Optional[UpgradePrompt]:
    """Create upgrade prompt for user"""
    # Get feature definition
    feature_def = self.feature_definitions.get(feature_id)
    if not feature_def:
        return None
    
    # Get user subscription
    subscription = self.subscription_service.get_user_subscription(user_id)
    current_tier = subscription.get('plan_id', 'free')
    
    # Determine recommended tier
    recommended_tier = feature_def.access_level.value
    
    # Generate value proposition
    value_proposition = self._generate_value_proposition(feature_def, trigger_type, context)
    
    # Calculate urgency level
    urgency_level = self._calculate_urgency_level(trigger_type, context)
    
    # Create upgrade prompt
    prompt = UpgradePrompt(
        prompt_id=str(uuid.uuid4()),
        user_id=user_id,
        feature_id=feature_id,
        trigger_type=trigger_type,
        current_tier=current_tier,
        recommended_tier=recommended_tier,
        value_proposition=value_proposition,
        urgency_level=urgency_level,
        context_data=context or {},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    
    return prompt
```

### Value Proposition Generation
```python
def _generate_value_proposition(self, feature_def: FeatureDefinition, trigger_type: UpgradeTrigger, context: Dict[str, Any] = None) -> str:
    """Generate value proposition for upgrade prompt"""
    if trigger_type == UpgradeTrigger.FEATURE_ACCESS:
        return f"Unlock {feature_def.name} to {feature_def.description.lower()}"
    elif trigger_type == UpgradeTrigger.USAGE_LIMIT:
        return f"Get unlimited access to {feature_def.name} and more features"
    elif trigger_type == UpgradeTrigger.DATA_LIMIT:
        return f"Handle larger datasets with {feature_def.name}"
    elif trigger_type == UpgradeTrigger.EXPORT_LIMIT:
        return f"Export more data with {feature_def.name}"
    else:
        return f"Upgrade to access {feature_def.name} and unlock your full potential"
```

### Usage Example
```python
# Create upgrade prompt for feature access
prompt = feature_manager.create_upgrade_prompt(
    user_id, 'investment_analysis', UpgradeTrigger.FEATURE_ACCESS
)

if prompt:
    print(f"Upgrade Prompt Created:")
    print(f"  Feature: {prompt.feature_id}")
    print(f"  Current Tier: {prompt.current_tier}")
    print(f"  Recommended Tier: {prompt.recommended_tier}")
    print(f"  Value Proposition: {prompt.value_proposition}")
    print(f"  Urgency Level: {prompt.urgency_level}")
```

## Usage Tracking

### Track Feature Usage
```python
def track_feature_usage(self, user_id: str, feature_id: str, usage_type: str, usage_data: Dict[str, Any], session_id: str = None) -> None:
    """Track feature usage"""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    usage = FeatureUsage(
        usage_id=str(uuid.uuid4()),
        user_id=user_id,
        feature_id=feature_id,
        usage_type=usage_type,
        usage_data=usage_data,
        timestamp=datetime.now(timezone.utc),
        session_id=session_id
    )
    
    # Save usage
    self._save_feature_usage(usage)
    
    # Check for upgrade triggers
    self._check_upgrade_triggers(user_id, feature_id, usage)
```

### Usage Types
```python
# Different usage types for tracking
usage_types = {
    'access': 'User accessed the feature',
    'categorization': 'User categorized transactions',
    'analysis': 'User performed analysis',
    'optimization': 'User ran optimization',
    'export': 'User exported data',
    'api_call': 'User made API call',
    'dashboard_view': 'User viewed dashboard',
    'report_generation': 'User generated report'
}
```

### Usage Example
```python
# Track feature usage
feature_manager.track_feature_usage(
    user_id, 'budget_tracker', 'dashboard_view',
    {'page': 'overview', 'time_spent': 300}
)

# Track categorization usage
feature_manager.track_feature_usage(
    user_id, 'expense_categorizer', 'categorization',
    {'transactions': 5, 'auto_categorized': 3}
)

# Track analysis usage
feature_manager.track_feature_usage(
    user_id, 'investment_analysis', 'analysis',
    {'portfolio_size': 100000, 'analysis_type': 'performance'}
)
```

## Feature Analytics

### Get Feature Analytics
```python
def get_feature_analytics(self, user_id: str) -> Dict[str, Any]:
    """Get feature usage analytics for user"""
    analytics = {
        'user_id': user_id,
        'feature_usage': {},
        'usage_trends': {},
        'upgrade_opportunities': [],
        'recommendations': []
    }
    
    # Get feature usage data
    feature_usage = self._get_user_feature_usage(user_id)
    analytics['feature_usage'] = feature_usage
    
    # Calculate usage trends
    analytics['usage_trends'] = self._calculate_usage_trends(user_id)
    
    # Identify upgrade opportunities
    analytics['upgrade_opportunities'] = self._identify_upgrade_opportunities(user_id, feature_usage)
    
    # Generate recommendations
    analytics['recommendations'] = self._generate_feature_recommendations(user_id, analytics)
    
    return analytics
```

### Analytics Structure
```python
analytics = {
    'user_id': 'user123',
    'feature_usage': {
        'budget_tracker': {'usage_count': 75, 'last_used': '2024-01-15'},
        'expense_categorizer': {'usage_count': 45, 'last_used': '2024-01-14'},
        'savings_goals': {'usage_count': 12, 'last_used': '2024-01-10'}
    },
    'usage_trends': {
        'total_features_used': 8,
        'most_used_features': ['budget_tracker', 'expense_categorizer'],
        'usage_growth_rate': 0.15,
        'feature_adoption_rate': 0.6
    },
    'upgrade_opportunities': [
        {
            'type': 'high_basic_usage',
            'feature_id': 'investment_analysis',
            'recommended_tier': 'premium',
            'confidence': 0.8
        }
    ],
    'recommendations': [
        'Consider upgrading to access advanced features',
        'Explore investment analysis for portfolio growth'
    ]
}
```

### Usage Example
```python
# Get feature analytics
analytics = feature_manager.get_feature_analytics(user_id)

print(f"User ID: {analytics['user_id']}")

print("Feature Usage:")
for feature_id, usage_data in analytics['feature_usage'].items():
    print(f"  {feature_id}: {usage_data.get('usage_count', 0)} uses")

print("Usage Trends:")
trends = analytics['usage_trends']
print(f"  Total Features Used: {trends['total_features_used']}")
print(f"  Usage Growth Rate: {trends['usage_growth_rate']:.1%}")
print(f"  Feature Adoption Rate: {trends['feature_adoption_rate']:.1%}")

print("Upgrade Opportunities:")
for opportunity in analytics['upgrade_opportunities']:
    print(f"  - {opportunity['type']}: {opportunity['feature_id']} -> {opportunity['recommended_tier']}")

print("Recommendations:")
for recommendation in analytics['recommendations']:
    print(f"  - {recommendation}")
```

## Subscription Controls Decorator

### Feature Access Decorator
```python
class SubscriptionControlsDecorator:
    """Decorator for subscription controls"""
    
    def require_feature_access(self, feature_id: str):
        """Decorator to require feature access"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = self._extract_user_id(args, kwargs)
                if not user_id:
                    raise ValueError("user_id not found in function arguments")
                
                # Check feature access
                access_check = self.feature_access_manager.check_feature_access(user_id, feature_id)
                
                if not access_check['has_access']:
                    # Create upgrade prompt if needed
                    if access_check['upgrade_required']:
                        self.feature_access_manager.create_upgrade_prompt(
                            user_id, feature_id, UpgradeTrigger.FEATURE_ACCESS
                        )
                    
                    raise PermissionError(f"Access to {feature_id} requires upgrade")
                
                # Track usage
                self.feature_access_manager.track_feature_usage(
                    user_id, feature_id, 'function_call', {'function': func.__name__}
                )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
```

### Usage Limits Decorator
```python
def check_usage_limits(self, feature_id: str, usage_type: str):
    """Decorator to check usage limits"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id from args or kwargs
            user_id = self._extract_user_id(args, kwargs)
            if not user_id:
                raise ValueError("user_id not found in function arguments")
            
            # Check usage limits
            access_check = self.feature_access_manager.check_feature_access(user_id, feature_id)
            
            if not access_check['has_access'] and access_check['reason'] == 'usage_limit_exceeded':
                # Create upgrade prompt
                self.feature_access_manager.create_upgrade_prompt(
                    user_id, feature_id, UpgradeTrigger.USAGE_LIMIT,
                    access_check.get('context_data', {})
                )
                
                raise PermissionError(f"Usage limit exceeded for {feature_id}")
            
            # Track usage
            self.feature_access_manager.track_feature_usage(
                user_id, feature_id, usage_type, {'function': func.__name__}
            )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

### Usage Example
```python
# Create decorator
decorator = SubscriptionControlsDecorator(feature_manager)

# Decorate function with feature access requirement
@decorator.require_feature_access('investment_analysis')
def analyze_investment(user_id: str, portfolio_data: Dict[str, Any]):
    """Analyze investment portfolio"""
    return {
        'analysis_id': str(uuid.uuid4()),
        'user_id': user_id,
        'portfolio_value': portfolio_data.get('value', 0),
        'recommendations': ['diversify', 'rebalance']
    }

# Decorate function with usage limits
@decorator.check_usage_limits('data_export', 'export')
def export_data(user_id: str, data_type: str, format: str):
    """Export financial data"""
    return {
        'export_id': str(uuid.uuid4()),
        'user_id': user_id,
        'data_type': data_type,
        'format': format,
        'file_size': '2.5MB'
    }

# Use decorated functions
try:
    result = analyze_investment('premium_user', {'value': 100000})
    print(f"Analysis successful: {result['analysis_id']}")
except PermissionError as e:
    print(f"Access denied: {e}")

try:
    result = export_data('basic_user', 'transactions', 'csv')
    print(f"Export successful: {result['export_id']}")
except PermissionError as e:
    print(f"Export failed: {e}")
```

## Integration Examples

### API Integration
```python
def api_check_feature_access(user_id: str, feature_id: str):
    """API endpoint for checking feature access"""
    feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
    
    access_result = feature_manager.check_feature_access(user_id, feature_id)
    
    return {
        'success': True,
        'has_access': access_result['has_access'],
        'reason': access_result['reason'],
        'upgrade_required': access_result['upgrade_required'],
        'recommended_tier': access_result.get('recommended_tier'),
        'current_usage': access_result.get('current_usage', {}),
        'usage_limit': access_result.get('usage_limit', {})
    }

def api_get_user_features(user_id: str):
    """API endpoint for getting user features"""
    feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
    
    features = feature_manager.get_user_features(user_id)
    
    return {
        'success': True,
        'features': features
    }

def api_create_upgrade_prompt(user_id: str, feature_id: str, trigger_type: str, context: Dict[str, Any] = None):
    """API endpoint for creating upgrade prompts"""
    feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
    
    prompt = feature_manager.create_upgrade_prompt(
        user_id, feature_id, UpgradeTrigger(trigger_type), context
    )
    
    if prompt:
        return {
            'success': True,
            'prompt': {
                'prompt_id': prompt.prompt_id,
                'feature_id': prompt.feature_id,
                'current_tier': prompt.current_tier,
                'recommended_tier': prompt.recommended_tier,
                'value_proposition': prompt.value_proposition,
                'urgency_level': prompt.urgency_level
            }
        }
    else:
        return {'success': False, 'message': 'Could not create upgrade prompt'}

def api_track_feature_usage(user_id: str, feature_id: str, usage_type: str, usage_data: Dict[str, Any]):
    """API endpoint for tracking feature usage"""
    feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
    
    feature_manager.track_feature_usage(user_id, feature_id, usage_type, usage_data)
    
    return {'success': True}

def api_get_feature_analytics(user_id: str):
    """API endpoint for feature analytics"""
    feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
    
    analytics = feature_manager.get_feature_analytics(user_id)
    
    return {
        'success': True,
        'analytics': analytics
    }
```

### Frontend Integration
```javascript
// Check feature access
async function checkFeatureAccess(userId, featureId) {
    const response = await fetch('/api/subscription/check-feature-access', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            feature_id: featureId
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result;
    }
    throw new Error('Failed to check feature access');
}

// Get user features
async function getUserFeatures(userId) {
    const response = await fetch('/api/subscription/get-user-features', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.features;
    }
    throw new Error('Failed to get user features');
}

// Create upgrade prompt
async function createUpgradePrompt(userId, featureId, triggerType, context = null) {
    const response = await fetch('/api/subscription/create-upgrade-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            feature_id: featureId,
            trigger_type: triggerType,
            context: context
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.prompt;
    }
    return null;
}

// Track feature usage
async function trackFeatureUsage(userId, featureId, usageType, usageData = {}) {
    const response = await fetch('/api/subscription/track-feature-usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            feature_id: featureId,
            usage_type: usageType,
            usage_data: usageData
        })
    });
    
    const result = await response.json();
    return result.success;
}

// Get feature analytics
async function getFeatureAnalytics(userId) {
    const response = await fetch('/api/subscription/get-feature-analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.analytics;
    }
    throw new Error('Failed to get feature analytics');
}

// Example usage
async function handleFeatureAccess(userId, featureId) {
    try {
        // Check feature access
        const accessResult = await checkFeatureAccess(userId, featureId);
        
        if (accessResult.has_access) {
            // Track usage
            await trackFeatureUsage(userId, featureId, 'access', {
                timestamp: new Date().toISOString(),
                context: 'user_initiated'
            });
            
            // Proceed with feature
            console.log('Feature access granted');
            return true;
        } else {
            // Create upgrade prompt
            const prompt = await createUpgradePrompt(
                userId, featureId, 'feature_access'
            );
            
            if (prompt) {
                // Show upgrade prompt to user
                showUpgradePrompt(prompt);
            }
            
            return false;
        }
    } catch (error) {
        console.error('Error handling feature access:', error);
        return false;
    }
}

// Example feature integration
async function analyzeInvestment(userId, portfolioData) {
    const featureId = 'investment_analysis';
    
    // Check access before proceeding
    const hasAccess = await handleFeatureAccess(userId, featureId);
    
    if (hasAccess) {
        // Perform investment analysis
        const result = await performInvestmentAnalysis(portfolioData);
        
        // Track usage
        await trackFeatureUsage(userId, featureId, 'analysis', {
            portfolio_size: portfolioData.value,
            analysis_type: 'performance'
        });
        
        return result;
    } else {
        throw new Error('Access to investment analysis requires upgrade');
    }
}

// Example dashboard integration
async function loadUserDashboard(userId) {
    try {
        // Get user features
        const features = await getUserFeatures(userId);
        
        // Get analytics
        const analytics = await getFeatureAnalytics(userId);
        
        // Render dashboard
        renderDashboard(features, analytics);
        
        // Track dashboard view
        await trackFeatureUsage(userId, 'dashboard', 'view', {
            page: 'main_dashboard',
            time_spent: 0
        });
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}
```

## Best Practices

### Feature Access Control
1. **Always Check Access**: Check feature access before allowing any feature usage
2. **Graceful Degradation**: Provide alternative options when access is denied
3. **Clear Messaging**: Explain why access is restricted and how to upgrade
4. **Usage Tracking**: Track all feature usage for analytics and optimization
5. **Dependency Management**: Ensure dependencies are available before granting access

### Upgrade Prompt Optimization
1. **Contextual Prompts**: Create prompts based on user behavior and context
2. **Value Demonstration**: Show clear value in upgrade prompts
3. **Urgency Management**: Use appropriate urgency levels based on user behavior
4. **A/B Testing**: Test different prompt strategies and messages
5. **Analytics Integration**: Track prompt performance and optimize accordingly

### Usage Tracking
1. **Comprehensive Tracking**: Track all user interactions with features
2. **Context Preservation**: Include relevant context in usage data
3. **Performance Optimization**: Ensure tracking doesn't impact performance
4. **Privacy Compliance**: Ensure tracking complies with privacy regulations
5. **Analytics Integration**: Use tracking data for optimization and insights

### Integration Guidelines
1. **Decorator Usage**: Use decorators for consistent access control
2. **Error Handling**: Implement proper error handling for access denials
3. **User Experience**: Ensure seamless user experience with clear upgrade paths
4. **Performance**: Optimize for performance in high-traffic scenarios
5. **Scalability**: Design for scalability as user base grows

## Troubleshooting

### Common Issues

#### Feature Access Issues
```python
def debug_feature_access(user_id: str, feature_id: str):
    """Debug feature access issues"""
    try:
        feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
        access_result = feature_manager.check_feature_access(user_id, feature_id)
        
        print(f"Feature Access Debug for {user_id} -> {feature_id}:")
        print(f"  Has Access: {access_result['has_access']}")
        print(f"  Reason: {access_result['reason']}")
        print(f"  Upgrade Required: {access_result['upgrade_required']}")
        print(f"  Recommended Tier: {access_result.get('recommended_tier', 'N/A')}")
        
        if 'current_usage' in access_result:
            print(f"  Current Usage: {access_result['current_usage']}")
        
        if 'usage_limit' in access_result:
            print(f"  Usage Limit: {access_result['usage_limit']}")
        
    except Exception as e:
        print(f"Error debugging feature access: {e}")
```

#### Usage Tracking Issues
```python
def debug_usage_tracking(user_id: str, feature_id: str):
    """Debug usage tracking issues"""
    try:
        feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
        
        # Track usage
        feature_manager.track_feature_usage(
            user_id, feature_id, 'debug', {'debug_session': True}
        )
        
        print(f"Usage tracking debug for {user_id} -> {feature_id}:")
        print("  Usage tracked successfully")
        
        # Get analytics
        analytics = feature_manager.get_feature_analytics(user_id)
        print(f"  Analytics generated: {len(analytics.get('feature_usage', {}))} features")
        
    except Exception as e:
        print(f"Error debugging usage tracking: {e}")
```

#### Upgrade Prompt Issues
```python
def debug_upgrade_prompt(user_id: str, feature_id: str, trigger_type: str):
    """Debug upgrade prompt issues"""
    try:
        feature_manager = FeatureAccessManager(db, subscription_service, upgrade_optimization_service)
        
        prompt = feature_manager.create_upgrade_prompt(
            user_id, feature_id, UpgradeTrigger(trigger_type)
        )
        
        if prompt:
            print(f"Upgrade prompt debug for {user_id} -> {feature_id}:")
            print(f"  Prompt Created: Yes")
            print(f"  Prompt ID: {prompt.prompt_id}")
            print(f"  Current Tier: {prompt.current_tier}")
            print(f"  Recommended Tier: {prompt.recommended_tier}")
            print(f"  Value Proposition: {prompt.value_proposition}")
            print(f"  Urgency Level: {prompt.urgency_level}")
        else:
            print(f"Upgrade prompt debug for {user_id} -> {feature_id}:")
            print(f"  Prompt Created: No")
        
    except Exception as e:
        print(f"Error debugging upgrade prompt: {e}")
```

## Conclusion

The Subscription Controls system provides comprehensive integration between subscription controls and all MINGUS application features, ensuring:

- **Proper Tier Access**: Users can only access features appropriate for their subscription level
- **Usage Limit Management**: Intelligent tracking and enforcement of usage limits
- **Upgrade Prompt Generation**: Strategic upgrade prompts based on user behavior
- **Analytics Integration**: Comprehensive analytics for optimization and insights
- **Seamless Integration**: Easy integration with all MINGUS application features
- **Performance Optimization**: Efficient processing for high-volume usage
- **Scalable Architecture**: Designed for growth and scalability

This system ensures maximum user satisfaction through proper access control, clear upgrade paths, and comprehensive analytics for continuous optimization. 