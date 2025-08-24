# AI and Analytics Subscription Controls Guide

## Overview

The AI and Analytics Subscription Controls system provides comprehensive subscription gating for MINGUS AI and analytics features, ensuring proper tier access, intelligent depth control, and seamless user experience across all subscription levels.

## Features

### 🤖 AI Insights Generation
- **Budget Tier**: 0 AI insights per month (not available)
- **Mid-Tier**: 50 AI insights per month
- **Professional Tier**: Unlimited AI insights

**Available Insight Types:**
- Financial Trend Analysis
- Spending Pattern Recognition
- Investment Opportunity Identification
- Risk Assessment
- Budget Optimization
- Goal Achievement Tracking
- Cash Flow Prediction
- Portfolio Analysis

### 🔮 Predictive Analytics
- **Budget Tier**: Not available
- **Mid-Tier**: Available (limited models)
- **Professional Tier**: Available (all models)

**Available Model Types:**
- Expense Forecasting
- Income Prediction
- Investment Return Prediction
- Churn Prediction
- Credit Risk Assessment
- Market Trend Analysis
- Budget Deviation Prediction
- Goal Completion Prediction

### 📊 Custom Reports
- **Budget Tier**: 0 custom reports per month (not available)
- **Mid-Tier**: 5 custom reports per month
- **Professional Tier**: Unlimited custom reports

**Available Report Types:**
- Financial Dashboard
- Performance Metrics
- Comparative Analysis
- Trend Report
- Forecasting Report
- Risk Analysis
- Optimization Report
- Executive Summary

### 🧠 Advanced Analytics
- **Budget Tier**: Not available
- **Mid-Tier**: Not available
- **Professional Tier**: Available (all features)

**Available Analysis Types:**
- Cohort Analysis
- Segmentation Analysis
- Correlation Analysis
- Regression Analysis
- Time Series Analysis
- Clustering Analysis
- Anomaly Detection
- Predictive Modeling

## Implementation

### Core Classes

#### AIAnalyticsControls
The main controller class that manages all AI and analytics features.

```python
from backend.features.ai_analytics_controls import AIAnalyticsControls

# Initialize the controls
ai_analytics_controls = AIAnalyticsControls(
    db=your_database,
    subscription_service=your_subscription_service,
    feature_access_manager=your_feature_access_manager
)
```

#### AIAnalyticsDecorator
Provides decorator-based access control for easy integration.

```python
from backend.features.ai_analytics_controls import AIAnalyticsDecorator

decorator = AIAnalyticsDecorator(ai_analytics_controls)
```

### Key Methods

#### Generate AI Insights
```python
result = ai_analytics_controls.generate_ai_insight(
    user_id='user123',
    insight_type=AIInsightType.FINANCIAL_TREND,
    financial_data={
        'income': 75000,
        'expenses': 52000,
        'savings': 23000,
        'investments': 45000,
        'debt': 15000
    }
)

if result['success']:
    print(f"Insight generated: {result['insight_id']}")
    print(f"Confidence: {result['confidence_score']:.1%}")
    print(f"Remaining insights: {result['remaining_insights']}")
else:
    print(f"Upgrade required to: {result['recommended_tier']}")
```

#### Run Predictive Analytics
```python
result = ai_analytics_controls.run_predictive_analytics(
    user_id='user123',
    model_type=PredictiveModelType.EXPENSE_FORECASTING,
    data={
        'historical_expenses': [3500, 3800, 3200, 4100, 3600, 3900],
        'market_conditions': 'stable',
        'economic_indicators': 'positive'
    }
)

if result['success']:
    print(f"Prediction completed: {result['prediction_id']}")
    print(f"Accuracy: {result['accuracy_score']:.1%}")
    print(f"Model version: {result['model_version']}")
else:
    print(f"Feature not available for current tier")
```

#### Create Custom Reports
```python
result = ai_analytics_controls.create_custom_report(
    user_id='user123',
    report_type=CustomReportType.FINANCIAL_DASHBOARD,
    report_config={
        'time_period': '12_months',
        'metrics': ['revenue', 'expenses', 'profit', 'growth'],
        'visualizations': ['charts', 'graphs', 'tables'],
        'export_format': 'pdf'
    }
)

if result['success']:
    print(f"Report created: {result['report_id']}")
    print(f"Customization level: {result['customization_level']}")
    print(f"Remaining reports: {result['remaining_reports']}")
else:
    print(f"Upgrade required to: {result['recommended_tier']}")
```

#### Run Advanced Analytics
```python
result = ai_analytics_controls.run_advanced_analytics(
    user_id='user123',
    analysis_type=AdvancedAnalyticsType.COHORT_ANALYSIS,
    data={
        'user_data': {
            'demographics': ['age', 'income', 'location'],
            'behavioral': ['purchase_history', 'usage_patterns'],
            'financial': ['income', 'expenses', 'investments']
        },
        'time_series_data': [100, 120, 110, 130, 125, 140],
        'analysis_parameters': {
            'confidence_level': 0.95,
            'significance_level': 0.05,
            'sample_size': 1000
        }
    }
)

if result['success']:
    print(f"Analysis completed: {result['analysis_id']}")
    print(f"Complexity level: {result['complexity_level']}")
    print(f"Processing time: {result['processing_time']:.1f}s")
else:
    print(f"Advanced analytics only available for professional tier")
```

### Decorator Usage

#### Require AI Insights Access
```python
@decorator.require_ai_insights_access(AIInsightType.FINANCIAL_TREND)
def analyze_financial_trends(user_id: str, financial_data: Dict[str, Any]):
    """Function automatically checks AI insights access"""
    return perform_trend_analysis(financial_data)
```

#### Require Predictive Analytics Access
```python
@decorator.require_predictive_analytics_access(PredictiveModelType.EXPENSE_FORECASTING)
def forecast_user_expenses(user_id: str, historical_data: List[float]):
    """Function automatically checks predictive analytics access"""
    return run_forecasting_model(historical_data)
```

#### Require Custom Reports Access
```python
@decorator.require_custom_reports_access(CustomReportType.FINANCIAL_DASHBOARD)
def create_user_dashboard(user_id: str, dashboard_config: Dict[str, Any]):
    """Function automatically checks custom reports access"""
    return generate_dashboard(dashboard_config)
```

#### Require Advanced Analytics Access
```python
@decorator.require_advanced_analytics_access(AdvancedAnalyticsType.COHORT_ANALYSIS)
def analyze_user_cohorts(user_id: str, cohort_data: Dict[str, Any]):
    """Function automatically checks advanced analytics access"""
    return perform_cohort_analysis(cohort_data)
```

## Tier Configuration

### Budget Tier ($9.99/month)
- **AI Insights**: 0 per month (not available)
- **Predictive Analytics**: Not available
- **Custom Reports**: 0 per month (not available)
- **Advanced Analytics**: Not available
- **Data Visualizations**: 5 per month

### Mid-Tier ($29.99/month)
- **AI Insights**: 50 per month
  - Financial Trend Analysis
  - Spending Pattern Recognition
  - Budget Optimization
  - Goal Achievement Tracking
- **Predictive Analytics**: Available
  - Expense Forecasting
  - Income Prediction
  - Budget Deviation Prediction
  - Goal Completion Prediction
- **Custom Reports**: 5 per month
  - Financial Dashboard
  - Performance Metrics
  - Comparative Analysis
  - Trend Report
- **Advanced Analytics**: Not available
- **Data Visualizations**: 20 per month

### Professional Tier ($79.99/month)
- **AI Insights**: Unlimited
  - All insight types including Investment Opportunity, Risk Assessment, Cash Flow Prediction, Portfolio Analysis
- **Predictive Analytics**: Available
  - All model types including Investment Return, Churn Prediction, Credit Risk, Market Trend
- **Custom Reports**: Unlimited
  - All report types including Forecasting Report, Risk Analysis, Optimization Report, Executive Summary
- **Advanced Analytics**: Available
  - All analysis types including Cohort Analysis, Segmentation Analysis, Correlation Analysis, Regression Analysis, Time Series Analysis, Clustering Analysis, Anomaly Detection, Predictive Modeling
- **Data Visualizations**: Unlimited

## Integration Examples

### Frontend Integration (JavaScript)
```javascript
// Generate AI insight
async function generateAIInsight(userId, insightType, financialData) {
    const response = await fetch('/api/ai-analytics/insights', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
            user_id: userId,
            insight_type: insightType,
            financial_data: financialData
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        displayInsight(result.insight_data);
        updateUsageDisplay(result.monthly_usage, result.monthly_limit);
    } else if (result.upgrade_required) {
        showUpgradePrompt(result.recommended_tier, result.message);
    } else {
        showError(result.message);
    }
}

// Run predictive analytics
async function runPredictiveAnalytics(userId, modelType, data) {
    const response = await fetch('/api/ai-analytics/predictive', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
            user_id: userId,
            model_type: modelType,
            data: data
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        displayPrediction(result.prediction_data);
    } else if (result.upgrade_required) {
        showUpgradePrompt(result.recommended_tier, result.message);
    } else {
        showError(result.message);
    }
}

// Create custom report
async function createCustomReport(userId, reportType, config) {
    const response = await fetch('/api/ai-analytics/custom-reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
            user_id: userId,
            report_type: reportType,
            report_config: config
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        displayReport(result.report_data);
        updateUsageDisplay(result.monthly_usage, result.monthly_limit);
    } else if (result.upgrade_required) {
        showUpgradePrompt(result.recommended_tier, result.message);
    } else {
        showError(result.message);
    }
}

// Run advanced analytics
async function runAdvancedAnalytics(userId, analysisType, data) {
    const response = await fetch('/api/ai-analytics/advanced', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
            user_id: userId,
            analysis_type: analysisType,
            data: data
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        displayAnalysis(result.analysis_data);
    } else if (result.upgrade_required) {
        showUpgradePrompt(result.recommended_tier, result.message);
    } else {
        showError(result.message);
    }
}

// Get feature status
async function getAIAnalyticsStatus(userId) {
    const response = await fetch(`/api/ai-analytics/status/${userId}`, {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    });
    
    const status = await response.json();
    
    displayFeatureStatus(status);
    displayUpgradeRecommendations(status.upgrade_recommendations);
}
```

### API Endpoints

#### Generate AI Insight
```
POST /api/ai-analytics/insights
Content-Type: application/json

{
    "user_id": "user123",
    "insight_type": "financial_trend",
    "financial_data": {
        "income": 75000,
        "expenses": 52000,
        "savings": 23000,
        "investments": 45000,
        "debt": 15000
    }
}
```

#### Run Predictive Analytics
```
POST /api/ai-analytics/predictive
Content-Type: application/json

{
    "user_id": "user123",
    "model_type": "expense_forecasting",
    "data": {
        "historical_expenses": [3500, 3800, 3200, 4100, 3600, 3900],
        "market_conditions": "stable",
        "economic_indicators": "positive"
    }
}
```

#### Create Custom Report
```
POST /api/ai-analytics/custom-reports
Content-Type: application/json

{
    "user_id": "user123",
    "report_type": "financial_dashboard",
    "report_config": {
        "time_period": "12_months",
        "metrics": ["revenue", "expenses", "profit", "growth"],
        "visualizations": ["charts", "graphs", "tables"],
        "export_format": "pdf"
    }
}
```

#### Run Advanced Analytics
```
POST /api/ai-analytics/advanced
Content-Type: application/json

{
    "user_id": "user123",
    "analysis_type": "cohort_analysis",
    "data": {
        "user_data": {
            "demographics": ["age", "income", "location"],
            "behavioral": ["purchase_history", "usage_patterns"],
            "financial": ["income", "expenses", "investments"]
        },
        "time_series_data": [100, 120, 110, 130, 125, 140],
        "analysis_parameters": {
            "confidence_level": 0.95,
            "significance_level": 0.05,
            "sample_size": 1000
        }
    }
}
```

#### Get Feature Status
```
GET /api/ai-analytics/status/{user_id}
Authorization: Bearer {token}
```

## Database Models

### AIInsightRecord
```python
@dataclass
class AIInsightRecord:
    insight_id: str
    user_id: str
    insight_type: AIInsightType
    insight_data: Dict[str, Any]
    confidence_score: float
    tier_level: str
    generated_at: datetime
    is_within_limit: bool
    created_at: datetime
```

### PredictiveAnalyticsRecord
```python
@dataclass
class PredictiveAnalyticsRecord:
    prediction_id: str
    user_id: str
    model_type: PredictiveModelType
    prediction_data: Dict[str, Any]
    accuracy_score: float
    tier_level: str
    model_version: str
    training_data_size: int
    created_at: datetime
```

### CustomReportRecord
```python
@dataclass
class CustomReportRecord:
    report_id: str
    user_id: str
    report_type: CustomReportType
    report_data: Dict[str, Any]
    customization_level: str
    tier_level: str
    is_within_limit: bool
    created_at: datetime
```

### AdvancedAnalyticsRecord
```python
@dataclass
class AdvancedAnalyticsRecord:
    analysis_id: str
    user_id: str
    analysis_type: AdvancedAnalyticsType
    analysis_data: Dict[str, Any]
    complexity_level: str
    tier_level: str
    processing_time: float
    created_at: datetime
```

## Configuration

### AIAnalyticsSubscriptionConfig
```python
@dataclass
class AIAnalyticsSubscriptionConfig:
    tier_limits: Dict[str, Dict[str, Any]]
    feature_access: Dict[str, Dict[str, Any]]
    upgrade_triggers: Dict[str, List[str]]
```

### Default Configuration
```python
tier_limits = {
    'budget': {
        'ai_insights_per_month': 0,
        'custom_reports_per_month': 0,
        'predictive_analytics': False,
        'advanced_analytics': False
    },
    'mid_tier': {
        'ai_insights_per_month': 50,
        'custom_reports_per_month': 5,
        'predictive_analytics': True,
        'advanced_analytics': False
    },
    'professional': {
        'ai_insights_per_month': -1,  # Unlimited
        'custom_reports_per_month': -1,  # Unlimited
        'predictive_analytics': True,
        'advanced_analytics': True
    }
}
```

## Error Handling

### Common Error Types
- `feature_not_available`: Feature not available for current tier
- `limit_exceeded`: Monthly limit exceeded
- `system_error`: Internal system error
- `invalid_parameters`: Invalid input parameters

### Error Response Format
```python
{
    'success': False,
    'error': 'limit_exceeded',
    'message': 'Monthly AI insights limit (50) exceeded',
    'upgrade_required': True,
    'recommended_tier': 'professional',
    'current_usage': 50,
    'monthly_limit': 50
}
```

## Monitoring and Analytics

### Usage Tracking
The system automatically tracks:
- Feature usage by user and tier
- Monthly limits and remaining usage
- Upgrade triggers and recommendations
- Performance metrics and processing times

### Performance Metrics
- AI insights generation time
- Predictive analytics processing time
- Custom report creation time
- Advanced analytics processing time
- Feature status retrieval time

### Upgrade Recommendations
The system generates intelligent upgrade recommendations based on:
- Usage approaching limits
- Feature access requirements
- User behavior patterns
- Business value potential

## Best Practices

### 1. Graceful Degradation
Always handle cases where features are not available for the user's tier:
```python
try:
    result = ai_analytics_controls.generate_ai_insight(user_id, insight_type, data)
    if result['success']:
        displayInsight(result['insight_data'])
    else:
        showUpgradePrompt(result['recommended_tier'], result['message'])
except Exception as e:
    logger.error(f"Error generating AI insight: {e}")
    showError("Unable to generate insight at this time")
```

### 2. Usage Monitoring
Regularly check usage limits and provide feedback to users:
```python
status = ai_analytics_controls.get_ai_analytics_feature_status(user_id)
if status['usage']['ai_insights']['remaining'] <= 5:
    showUsageWarning("You're approaching your AI insights limit")
```

### 3. Upgrade Optimization
Use upgrade recommendations to guide users to appropriate tiers:
```python
for rec in status['upgrade_recommendations']:
    if rec['type'] == 'usage_based':
        showUpgradePrompt(rec['recommended_tier'], rec['reason'])
```

### 4. Performance Optimization
Cache frequently accessed data and optimize processing:
```python
# Cache user subscription data
subscription_cache = {}

def get_cached_subscription(user_id):
    if user_id not in subscription_cache:
        subscription_cache[user_id] = subscription_service.get_user_subscription(user_id)
    return subscription_cache[user_id]
```

## Testing

### Unit Tests
```python
def test_ai_insights_generation():
    """Test AI insights generation with tier limits"""
    result = ai_analytics_controls.generate_ai_insight(
        'budget_user', AIInsightType.FINANCIAL_TREND, financial_data
    )
    assert not result['success']
    assert result['upgrade_required']
    assert result['recommended_tier'] == 'mid_tier'
```

### Integration Tests
```python
def test_complete_user_journey():
    """Test complete AI and analytics user journey"""
    # Test professional user with full access
    user_id = 'professional_user'
    
    # Generate AI insight
    insight_result = ai_analytics_controls.generate_ai_insight(
        user_id, AIInsightType.INVESTMENT_OPPORTUNITY, financial_data
    )
    assert insight_result['success']
    
    # Run predictive analytics
    prediction_result = ai_analytics_controls.run_predictive_analytics(
        user_id, PredictiveModelType.INVESTMENT_RETURN, data
    )
    assert prediction_result['success']
    
    # Create custom report
    report_result = ai_analytics_controls.create_custom_report(
        user_id, CustomReportType.EXECUTIVE_SUMMARY, report_config
    )
    assert report_result['success']
    
    # Run advanced analytics
    analysis_result = ai_analytics_controls.run_advanced_analytics(
        user_id, AdvancedAnalyticsType.COHORT_ANALYSIS, analysis_data
    )
    assert analysis_result['success']
```

## Security Considerations

### 1. Input Validation
Validate all input parameters before processing:
```python
def validate_financial_data(financial_data: Dict[str, Any]) -> bool:
    required_fields = ['income', 'expenses', 'savings']
    return all(field in financial_data for field in required_fields)
```

### 2. Rate Limiting
Implement rate limiting to prevent abuse:
```python
def check_rate_limit(user_id: str, feature_type: str) -> bool:
    # Implement rate limiting logic
    return True
```

### 3. Data Privacy
Ensure sensitive financial data is handled securely:
```python
def sanitize_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    # Remove sensitive information before logging
    sanitized = data.copy()
    if 'ssn' in sanitized:
        del sanitized['ssn']
    return sanitized
```

## Troubleshooting

### Common Issues

#### 1. Feature Not Available
**Problem**: User receives "feature not available" error
**Solution**: Check user's subscription tier and upgrade if necessary

#### 2. Limit Exceeded
**Problem**: User hits monthly usage limit
**Solution**: Wait for next month or upgrade to higher tier

#### 3. Performance Issues
**Problem**: Slow response times
**Solution**: Check system resources and optimize processing

#### 4. Data Quality Issues
**Problem**: Poor quality insights or predictions
**Solution**: Ensure sufficient and quality input data

### Debug Mode
Enable debug mode for detailed logging:
```python
import logging
logging.getLogger('ai_analytics_controls').setLevel(logging.DEBUG)
```

## Conclusion

The AI and Analytics Subscription Controls system provides comprehensive subscription gating for all MINGUS AI and analytics features. It ensures proper tier access, intelligent depth control, and seamless user experience while maximizing upgrade opportunities and revenue potential.

Key benefits:
- **Proper Tier Gating**: Users can only access AI and analytics features appropriate for their subscription
- **Intelligent Limits**: Monthly usage limits prevent abuse while encouraging upgrades
- **Seamless Integration**: Easy integration with existing code using decorators
- **Comprehensive Monitoring**: Full usage tracking and upgrade recommendations
- **Scalable Architecture**: Easy addition of new AI and analytics features

The system is production-ready and provides a solid foundation for AI and analytics feature monetization in MINGUS. 