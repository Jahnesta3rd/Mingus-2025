# MINGUS Behavioral Trigger System

## Overview

The MINGUS Behavioral Trigger System provides intelligent, contextual communication initiation based on user behavior patterns. This system automatically detects behavioral changes and triggers personalized communications to improve user engagement, financial outcomes, and overall user experience.

## Features

### 1. Financial Behavior Triggers
- **Spending Spike Detection**: Monitors for 20%+ increases in spending patterns
- **Income Drop Detection**: Identifies significant decreases in income
- **Savings Goal Stall**: Detects when savings progress has stalled
- **Milestone Achievement**: Celebrates when users reach financial milestones

### 2. Health/Wellness Correlation Triggers
- **Low Exercise + High Spending**: Identifies stress-related spending patterns
- **High Stress + Financial Decisions**: Detects potentially impulsive financial decisions during stress
- **Relationship Status Changes**: Triggers financial planning guidance for life changes

### 3. Career Advancement Triggers
- **Job Market Opportunities**: Alerts users to relevant job opportunities in their field
- **Skill Gap Identification**: Identifies skills that could boost earning potential
- **Salary Below Market**: Detects when users are underpaid compared to market rates

### 4. Life Event Triggers
- **Birthday Approaching**: Provides budget-friendly celebration ideas
- **Lease Renewal Period**: Offers housing cost analysis and relocation insights
- **Student Loan Grace Period Ending**: Provides payment planning guidance

### 5. Engagement Triggers
- **App Usage Decline**: Re-engages users who haven't used the app recently
- **Feature Unused**: Introduces users to valuable features they haven't tried
- **Premium Upgrade Opportunity**: Suggests premium features to high-engagement users

### 6. Machine Learning Integration
- **Pattern Recognition**: Learns user-specific optimal trigger timing
- **Predictive Modeling**: Predicts when interventions will be most effective
- **Success Rate Optimization**: Continuously improves based on historical data

## Database Schema

### Core Tables

#### `behavioral_triggers`
```sql
CREATE TABLE behavioral_triggers (
    id UUID PRIMARY KEY,
    trigger_name VARCHAR(100) NOT NULL,
    trigger_type trigger_type NOT NULL,
    trigger_category trigger_category NOT NULL,
    trigger_conditions JSONB NOT NULL,
    trigger_thresholds JSONB,
    trigger_frequency VARCHAR(20) DEFAULT 'once',
    sms_template VARCHAR(200),
    email_template VARCHAR(200),
    communication_delay_minutes INTEGER DEFAULT 0,
    priority trigger_priority DEFAULT 'medium',
    status trigger_status DEFAULT 'active',
    target_user_segments JSONB,
    target_user_tiers JSONB,
    exclusion_conditions JSONB,
    ml_model_enabled BOOLEAN DEFAULT FALSE,
    ml_model_name VARCHAR(100),
    ml_confidence_threshold FLOAT DEFAULT 0.7,
    success_rate FLOAT DEFAULT 0.0,
    engagement_rate FLOAT DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);
```

#### `trigger_events`
```sql
CREATE TABLE trigger_events (
    id UUID PRIMARY KEY,
    trigger_id UUID NOT NULL REFERENCES behavioral_triggers(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    detection_method VARCHAR(50) NOT NULL,
    confidence_score FLOAT DEFAULT 1.0,
    trigger_conditions_met JSONB,
    sms_sent BOOLEAN DEFAULT FALSE,
    email_sent BOOLEAN DEFAULT FALSE,
    sms_message_id VARCHAR(100),
    email_message_id VARCHAR(100),
    user_engaged BOOLEAN DEFAULT FALSE,
    engagement_type VARCHAR(50),
    engagement_time_minutes INTEGER,
    conversion_achieved BOOLEAN DEFAULT FALSE,
    conversion_type VARCHAR(50),
    conversion_value NUMERIC(10, 2),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    engaged_at TIMESTAMP WITH TIME ZONE,
    converted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `user_behavior_patterns`
```sql
CREATE TABLE user_behavior_patterns (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    pattern_confidence FLOAT DEFAULT 0.0,
    pattern_last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
    baseline_value FLOAT,
    variance_threshold FLOAT,
    trend_direction VARCHAR(20),
    times_used_for_triggers INTEGER DEFAULT 0,
    last_used_for_trigger TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `trigger_templates`
```sql
CREATE TABLE trigger_templates (
    id UUID PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_type VARCHAR(20) NOT NULL,
    trigger_category trigger_category NOT NULL,
    subject_line VARCHAR(200),
    message_content TEXT NOT NULL,
    personalization_variables JSONB,
    character_limit INTEGER,
    call_to_action VARCHAR(100),
    urgency_level VARCHAR(20) DEFAULT 'normal',
    is_ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_variants JSONB,
    avg_engagement_rate FLOAT DEFAULT 0.0,
    avg_conversion_rate FLOAT DEFAULT 0.0,
    total_uses INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);
```

#### `ml_models`
```sql
CREATE TABLE ml_models (
    id UUID PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_config JSONB NOT NULL,
    feature_columns JSONB NOT NULL,
    target_column VARCHAR(50) NOT NULL,
    accuracy_score FLOAT DEFAULT 0.0,
    precision_score FLOAT DEFAULT 0.0,
    recall_score FLOAT DEFAULT 0.0,
    f1_score FLOAT DEFAULT 0.0,
    training_data_size INTEGER DEFAULT 0,
    training_date TIMESTAMP WITH TIME ZONE NOT NULL,
    training_duration_minutes INTEGER,
    is_active BOOLEAN DEFAULT FALSE,
    is_production BOOLEAN DEFAULT FALSE,
    model_file_path VARCHAR(500),
    model_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(36)
);
```

## API Endpoints

### Trigger Management

#### Get All Triggers
```
GET /api/behavioral-triggers/triggers
Query Parameters:
- trigger_type: Filter by trigger type
- trigger_category: Filter by trigger category
- status: Filter by status (active, inactive, paused, testing)
- priority: Filter by priority (critical, high, medium, low)
```

#### Create Trigger
```
POST /api/behavioral-triggers/triggers
Body:
{
    "trigger_name": "Spending Spike Alert",
    "trigger_type": "financial_behavior",
    "trigger_category": "spending_spike",
    "trigger_conditions": {
        "condition": "spending_increase",
        "timeframe": "7d",
        "comparison": "baseline"
    },
    "trigger_thresholds": {
        "percentage_increase": 20,
        "minimum_amount": 100
    },
    "sms_template": "Spending Spike SMS",
    "email_template": "Spending Spike Email",
    "priority": "high"
}
```

#### Get Trigger Effectiveness
```
GET /api/behavioral-triggers/triggers/{trigger_id}/effectiveness
Query Parameters:
- time_period: Time period for analysis (7d, 30d, 90d)
```

### Trigger Events

#### Get Trigger Events
```
GET /api/behavioral-triggers/events
Query Parameters:
- user_id: Filter by user ID
- trigger_id: Filter by trigger ID
- event_type: Filter by event type
- start_date: Filter by start date
- end_date: Filter by end date
```

#### Process Trigger Event
```
POST /api/behavioral-triggers/events/{event_id}/process
```

### Template Management

#### Get Templates
```
GET /api/behavioral-triggers/templates
Query Parameters:
- template_type: Filter by template type (sms, email, push)
- trigger_category: Filter by trigger category
- is_active: Filter by active status
```

#### Create Template
```
POST /api/behavioral-triggers/templates
Body:
{
    "template_name": "Spending Spike SMS",
    "template_type": "sms",
    "trigger_category": "spending_spike",
    "message_content": "Hi {{user_name}}, we noticed your spending is {{percentage}}% higher than usual this week. Want to review your budget? Reply YES for insights.",
    "personalization_variables": ["user_name", "percentage"],
    "character_limit": 160,
    "call_to_action": "Reply YES",
    "urgency_level": "high"
}
```

### Machine Learning Models

#### Get ML Models
```
GET /api/behavioral-triggers/ml-models
Query Parameters:
- model_type: Filter by model type
- is_active: Filter by active status
- is_production: Filter by production status
```

#### Train ML Model
```
POST /api/behavioral-triggers/ml-models
Body:
{
    "model_name": "spending_spike_predictor",
    "model_type": "classification",
    "model_version": "1.0.0",
    "model_config": {
        "algorithm": "random_forest",
        "max_depth": 10,
        "n_estimators": 100
    },
    "feature_columns": ["weekly_spending", "income", "savings_rate"],
    "target_column": "spending_spike_likelihood",
    "training_data_size": 10000
}
```

### User Patterns

#### Get User Patterns
```
GET /api/behavioral-triggers/patterns/{user_id}
Query Parameters:
- pattern_type: Filter by pattern type
```

#### Update User Patterns
```
POST /api/behavioral-triggers/patterns/{user_id}
Body:
{
    "pattern_type": "spending",
    "pattern_data": {
        "weekly_averages": [150, 180, 200, 175, 190],
        "trend": "increasing",
        "seasonality": "monthly"
    }
}
```

### Trigger Detection

#### Detect Triggers for User
```
POST /api/behavioral-triggers/detect/{user_id}
Body:
{
    "trigger_types": ["financial", "health_wellness", "career"],
    "financial_data": {
        "weekly_spending": 250,
        "monthly_income": 5000,
        "savings_goals": [...]
    },
    "health_data": {
        "exercise_level": "low",
        "stress_level": "high"
    },
    "career_data": {
        "current_salary": 60000,
        "market_rate": 75000,
        "skill_gaps": [...]
    }
}
```

## Service Architecture

### BehavioralTriggerService

The core service that handles trigger detection and management:

```python
class BehavioralTriggerService:
    def detect_financial_triggers(self, user_id: str, financial_data: Dict[str, Any]) -> List[TriggerEvent]
    def detect_health_wellness_triggers(self, user_id: str, health_data: Dict[str, Any], financial_data: Dict[str, Any]) -> List[TriggerEvent]
    def detect_career_triggers(self, user_id: str, career_data: Dict[str, Any]) -> List[TriggerEvent]
    def detect_life_event_triggers(self, user_id: str, user_profile: Dict[str, Any]) -> List[TriggerEvent]
    def detect_engagement_triggers(self, user_id: str, engagement_data: Dict[str, Any]) -> List[TriggerEvent]
    def process_trigger_event(self, trigger_event: TriggerEvent) -> bool
    def update_user_behavior_patterns(self, user_id: str, pattern_type: str, pattern_data: Dict[str, Any]) -> None
    def get_trigger_effectiveness(self, trigger_id: str = None, time_period: str = "30d") -> Dict[str, Any]
    def train_ml_model(self, model_name: str, model_type: str, training_data: Dict[str, Any]) -> MLModel
```

## Trigger Detection Logic

### Financial Triggers

#### Spending Spike Detection
```python
def _detect_spending_spike(self, user_id: str, financial_data: Dict[str, Any], patterns: List[UserBehaviorPattern]) -> bool:
    current_spending = financial_data.get('weekly_spending', 0)
    baseline = self._get_spending_baseline(patterns)
    
    if baseline:
        percentage_increase = ((current_spending - baseline) / baseline) * 100
        return percentage_increase >= 20  # 20% threshold
    
    return False
```

#### Income Drop Detection
```python
def _detect_income_drop(self, user_id: str, financial_data: Dict[str, Any], patterns: List[UserBehaviorPattern]) -> bool:
    current_income = financial_data.get('monthly_income', 0)
    baseline = self._get_income_baseline(patterns)
    
    if baseline:
        percentage_decrease = ((baseline - current_income) / baseline) * 100
        return percentage_decrease >= 15  # 15% threshold
    
    return False
```

### Health/Wellness Triggers

#### Low Exercise + High Spending Correlation
```python
def _detect_low_exercise_high_spending(self, user_id: str, health_data: Dict[str, Any], financial_data: Dict[str, Any]) -> bool:
    exercise_level = health_data.get('exercise_level', 'normal')
    spending_level = financial_data.get('spending_level', 'normal')
    
    return exercise_level == 'low' and spending_level == 'high'
```

### Career Triggers

#### Salary Below Market Detection
```python
def _detect_salary_below_market(self, user_id: str, career_data: Dict[str, Any]) -> bool:
    current_salary = career_data.get('current_salary', 0)
    market_rate = career_data.get('market_rate', 0)
    
    if market_rate > 0:
        percentage_below = ((market_rate - current_salary) / market_rate) * 100
        return percentage_below >= 10  # 10% below market
    
    return False
```

## Communication Templates

### SMS Templates

#### Spending Spike SMS
```
Hi {{user_name}}, we noticed your spending is {{percentage}}% higher than usual this week. Want to review your budget? Reply YES for insights.
```

#### Income Drop SMS
```
Hi {{user_name}}, we noticed a change in your income pattern. Need help adjusting your budget? Reply HELP for guidance.
```

#### Job Opportunity SMS
```
Hi {{user_name}}, {{job_count}} new opportunities in {{field}} match your profile. Want to explore? Reply JOBS for details.
```

### Email Templates

#### Spending Spike Email
```
Hi {{user_name}},

We noticed your spending this week is {{percentage}}% higher than your usual pattern. This could impact your savings goals.

Key insights:
- Top spending categories: {{top_categories}}
- Potential savings: ${{potential_savings}}
- Impact on goals: {{goal_impact}}

Would you like us to help you adjust your budget?
```

## Machine Learning Integration

### Model Training
```python
def train_ml_model(self, model_name: str, model_type: str, training_data: Dict[str, Any]) -> MLModel:
    # This would integrate with actual ML training pipeline
    model = MLModel(
        model_name=model_name,
        model_type=model_type,
        model_version="1.0.0",
        model_config=training_data.get('config', {}),
        feature_columns=training_data.get('features', []),
        target_column=training_data.get('target', ''),
        training_data_size=training_data.get('data_size', 0),
        accuracy_score=training_data.get('accuracy', 0.0),
        is_active=True
    )
    
    return model
```

### Pattern Analysis
```python
def _calculate_pattern_characteristics(self, pattern: UserBehaviorPattern) -> None:
    data = pattern.pattern_data
    
    if isinstance(data, list) and len(data) > 0:
        # Calculate baseline (mean)
        pattern.baseline_value = statistics.mean(data)
        
        # Calculate variance threshold (standard deviation)
        if len(data) > 1:
            std_dev = statistics.stdev(data)
            pattern.variance_threshold = std_dev * 2  # 2 standard deviations
        
        # Calculate trend direction
        if len(data) >= 3:
            recent_avg = statistics.mean(data[-3:])
            older_avg = statistics.mean(data[:-3])
            
            if recent_avg > older_avg * 1.1:
                pattern.trend_direction = 'increasing'
            elif recent_avg < older_avg * 0.9:
                pattern.trend_direction = 'decreasing'
            else:
                pattern.trend_direction = 'stable'
```

## Effectiveness Tracking

### Metrics Calculation
```python
def get_trigger_effectiveness(self, trigger_id: str = None, time_period: str = "30d") -> Dict[str, Any]:
    # Calculate time range
    end_time = datetime.utcnow()
    if time_period == "7d":
        start_time = end_time - timedelta(days=7)
    elif time_period == "30d":
        start_time = end_time - timedelta(days=30)
    elif time_period == "90d":
        start_time = end_time - timedelta(days=90)
    
    # Get events in time range
    events = self.db.query(TriggerEvent).filter(
        and_(
            TriggerEvent.triggered_at >= start_time,
            TriggerEvent.triggered_at <= end_time
        )
    ).all()
    
    # Calculate metrics
    total_triggers = len(events)
    total_sent = len([e for e in events if e.sms_sent or e.email_sent])
    total_engaged = len([e for e in events if e.user_engaged])
    total_converted = len([e for e in events if e.conversion_achieved])
    
    # Calculate rates
    send_rate = (total_sent / total_triggers * 100) if total_triggers > 0 else 0
    engagement_rate = (total_engaged / total_sent * 100) if total_sent > 0 else 0
    conversion_rate = (total_converted / total_engaged * 100) if total_engaged > 0 else 0
    
    return {
        'total_triggers': total_triggers,
        'total_sent': total_sent,
        'total_engaged': total_engaged,
        'total_converted': total_converted,
        'send_rate': round(send_rate, 2),
        'engagement_rate': round(engagement_rate, 2),
        'conversion_rate': round(conversion_rate, 2)
    }
```

## Integration with Existing Systems

### Communication Preferences
The behavioral trigger system integrates with the communication preferences system to ensure users only receive communications they've opted into.

### Analytics System
Trigger events are tracked in the analytics system to measure effectiveness and optimize future triggers.

### Celery Task System
Trigger processing can be queued as Celery tasks for asynchronous processing and better performance.

## Best Practices

### 1. Trigger Design
- **Specific Conditions**: Define clear, measurable conditions for triggers
- **Appropriate Thresholds**: Set thresholds based on user behavior analysis
- **Frequency Limits**: Implement cooldown periods to avoid overwhelming users
- **Personalization**: Use user-specific data for personalized communications

### 2. Template Design
- **Clear Call-to-Action**: Include specific actions users can take
- **Personalization Variables**: Use available data to personalize messages
- **A/B Testing**: Test different message variations to optimize effectiveness
- **Urgency Levels**: Match urgency to trigger importance

### 3. Machine Learning
- **Feature Engineering**: Use relevant features for model training
- **Regular Retraining**: Retrain models with new data
- **Performance Monitoring**: Track model accuracy and performance
- **Fallback Logic**: Have rule-based fallbacks for ML failures

### 4. Effectiveness Optimization
- **Continuous Monitoring**: Track trigger effectiveness metrics
- **A/B Testing**: Test different trigger conditions and messages
- **User Feedback**: Incorporate user feedback to improve triggers
- **Performance Analysis**: Analyze which triggers drive the best outcomes

## Security and Privacy

### Data Protection
- All user data is encrypted at rest and in transit
- Personalization variables are sanitized to prevent injection attacks
- User consent is required for all communications
- Data retention policies are enforced

### Access Control
- API endpoints require JWT authentication
- Role-based access control for trigger management
- Audit logging for all trigger operations
- Secure communication channels for SMS and email

## Monitoring and Alerting

### System Health
- Monitor trigger processing queue depth
- Track trigger detection accuracy
- Alert on high error rates
- Monitor communication delivery rates

### Business Metrics
- Track trigger effectiveness by category
- Monitor user engagement with triggered communications
- Measure conversion rates and financial impact
- Alert on significant changes in trigger performance

## Future Enhancements

### 1. Advanced ML Models
- Deep learning models for pattern recognition
- Reinforcement learning for optimal trigger timing
- Natural language processing for message optimization

### 2. Real-time Processing
- Stream processing for immediate trigger detection
- Real-time personalization based on current context
- Dynamic threshold adjustment based on user behavior

### 3. Multi-channel Orchestration
- Cross-channel communication sequencing
- Channel-specific message optimization
- Unified user journey tracking

### 4. Predictive Analytics
- Predictive trigger scheduling
- Churn prediction and prevention
- Lifetime value optimization 