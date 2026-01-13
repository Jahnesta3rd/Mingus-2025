# Risk-Based Career Protection Analytics Integration

## Overview

This module extends the existing Mingus analytics system to provide comprehensive risk-based career protection analytics. It tracks risk assessments, triggers job recommendations based on risk levels, measures prediction accuracy, and monitors career protection outcomes.

## Features

### 🎯 Core Risk Analytics
- **Risk Assessment Tracking**: Monitor AI risk, layoff risk, and income risk assessments
- **Risk-Triggered Recommendations**: Automatically trigger job recommendations based on risk scores
- **Emergency Unlock System**: Grant premium features to high-risk users
- **Prediction Accuracy Measurement**: Track and validate risk prediction quality
- **Career Protection Outcomes**: Measure successful job transitions before layoffs

### 📊 Advanced Analytics
- **Risk Journey Analysis**: Complete user journey from risk detection to job placement
- **Early Warning Effectiveness**: Calculate advance notice accuracy (3-6 months)
- **Proactive vs Reactive Outcomes**: Compare outcomes for users who act on early warnings
- **Risk Communication Effectiveness**: Measure how well users understand and act on risk alerts

### 🧪 A/B Testing Framework
- **Risk Threshold Optimization**: Test different risk scores for recommendation activation
- **Recommendation Timing Tests**: Optimize when to send risk-based recommendations
- **Risk Alert Fatigue Analysis**: Track user response degradation from too many alerts
- **Communication Style Testing**: Test different risk messaging approaches

## Architecture

### Core Components

```
RiskAnalyticsIntegration
├── AnalyticsIntegration (base analytics)
├── RiskAnalyticsTracker (risk-specific tracking)
├── RiskBasedSuccessMetrics (career protection outcomes)
└── RiskABTestFramework (risk optimization testing)
```

### Database Schema

The system uses SQLite with the following key tables:

- `risk_assessments` - Risk assessment data and scores
- `risk_recommendations` - Risk-triggered job recommendations
- `risk_outcomes` - Prediction accuracy and actual outcomes
- `career_protection_outcomes` - Career protection success metrics
- `early_warning_effectiveness` - Early warning system performance
- `risk_ab_test_results` - A/B testing data for risk optimization

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from backend.analytics.risk_analytics_integration import RiskAnalyticsIntegration; RiskAnalyticsIntegration()"
```

### 2. Basic Usage

```python
from backend.analytics.risk_analytics_integration import RiskAnalyticsIntegration, RiskAssessmentData
from datetime import datetime

# Initialize risk analytics
risk_analytics = RiskAnalyticsIntegration()

# Track risk assessment
risk_data = RiskAssessmentData(
    user_id="user_123",
    assessment_type="ai_risk",
    overall_risk=0.75,
    risk_triggers=["High-risk industry", "Low AI usage"],
    risk_breakdown={"industry_risk": 0.3, "automation_risk": 0.45},
    timeline_urgency="3_months",
    assessment_timestamp=datetime.now(),
    confidence_score=0.85,
    risk_factors={"industry": 0.3, "automation": 0.45}
)

# Track assessment
await risk_analytics.track_risk_assessment_completed("user_123", risk_data)

# Track risk-triggered recommendations
recommendations = {
    "jobs": [
        {
            "job_id": "job_1",
            "tier": "optimal",
            "score": 8.5,
            "salary_increase_potential": 15000
        }
    ]
}

await risk_analytics.track_risk_recommendation_triggered("user_123", risk_data, recommendations)
```

### 3. API Integration

```python
import requests

# Track risk assessment
response = requests.post('http://localhost:5000/api/risk-analytics/track-risk-assessment', json={
    'user_id': 'user_123',
    'assessment_type': 'ai_risk',
    'overall_risk': 0.75,
    'risk_triggers': ['High-risk industry', 'Low AI usage'],
    'timeline_urgency': '3_months'
})

# Track career protection outcome
response = requests.post('http://localhost:5000/api/risk-analytics/track-career-protection-outcome', json={
    'user_id': 'user_123',
    'outcome_data': {
        'outcome_type': 'proactive_switch',
        'salary_impact': 20000,
        'time_to_outcome_days': 45
    }
})
```

## Key Methods

### Risk Event Tracking

```python
# Track risk assessment completion
await risk_analytics.track_risk_assessment_completed(user_id, risk_data)

# Track risk-triggered recommendations
await risk_analytics.track_risk_recommendation_triggered(user_id, risk_data, recommendations)

# Track emergency unlock usage
await risk_analytics.track_emergency_unlock_usage(user_id, unlock_data)

# Track prediction accuracy
await risk_analytics.track_risk_prediction_accuracy(user_id, predicted_risk, actual_outcome)

# Track career protection outcomes
await risk_analytics.track_career_protection_outcomes(user_id, outcome_data)
```

### Risk Journey Analytics

```python
# Analyze complete risk journey
journey_analysis = await risk_analytics.analyze_risk_to_recommendation_flow(user_id, days=30)

# Measure early warning effectiveness
effectiveness = await risk_analytics.measure_early_warning_effectiveness(days=30)
```

### A/B Testing

```python
# Create risk threshold optimization test
test_id = await risk_analytics.optimize_risk_trigger_thresholds(
    "Risk Threshold Test",
    [0.5, 0.6, 0.7, 0.8]
)
```

## Risk Assessment Types

### 1. AI Risk Assessment
- **Industry Risk**: Manufacturing, Retail, Finance (0-30 points)
- **Automation Level**: Very Little to Almost Everything (0-45 points)
- **AI Tool Usage**: Never to Constantly (0-20 points, inverted)
- **Skills Assessment**: AI-resistant skills reduce risk (-20 to 0 points)

### 2. Layoff Risk Assessment
- **Company Size**: Smaller companies are riskier (0-30 points)
- **Tenure**: Shorter tenure is riskier (0-25 points)
- **Performance**: Below expectations increases risk (0-20 points)
- **Company Health**: Major concerns increase risk (0-25 points)
- **Recent Layoffs**: Recent layoffs increase risk (0-30 points)
- **Skills Relevance**: Outdated skills increase risk (0-25 points)

### 3. Income Risk Assessment
- **Salary Growth**: Stagnant salary increases risk
- **Market Position**: Below market rate increases risk
- **Skill Demand**: Low-demand skills increase risk
- **Career Progression**: Limited advancement increases risk

## Risk Levels and Triggers

### Risk Level Classification
- **Low Risk** (0.0-0.4): Minimal intervention needed
- **Medium Risk** (0.4-0.6): Standard recommendations
- **High Risk** (0.6-0.8): Enhanced recommendations + monitoring
- **Critical Risk** (0.8-1.0): Emergency unlock + immediate action

### Emergency Unlock Features
- Advanced job search capabilities
- Priority support and coaching
- Salary negotiation tools
- Skill development resources
- Network expansion tools

## A/B Testing Framework

### Test Types

1. **Risk Threshold Optimization**
   - Test different risk scores for recommendation activation
   - Measure conversion rates and user satisfaction
   - Optimize for maximum career protection outcomes

2. **Recommendation Timing Tests**
   - Immediate vs delayed recommendations
   - Test 24h, 48h, and 1-week delays
   - Measure user response rates and outcomes

3. **Communication Style Testing**
   - Different risk messaging approaches
   - Test urgency levels and tone
   - Measure user understanding and action rates

### Success Metrics

- **Conversion Rate**: Percentage of users who act on recommendations
- **User Satisfaction**: User feedback and engagement scores
- **Outcome Improvement**: Career protection success rates
- **Prediction Accuracy**: Risk prediction validation scores

## Dashboard and Reporting

### Risk Dashboard Overview
- Total risk assessments by type
- High-risk user counts and trends
- Emergency unlock usage statistics
- Prediction accuracy metrics
- Career protection success rates

### User Segments
- **High Risk + High Engagement**: Active users responding to alerts
- **High Risk + Low Engagement**: At-risk users not responding
- **Low Risk + High Engagement**: Proactive users staying ahead
- **Low Risk + Low Engagement**: Stable users with minimal needs

### Risk Trends
- AI risk trends by industry
- Layoff risk trends by company size
- Income risk trends by skill level
- Overall risk landscape changes

## Performance Monitoring

### Key Metrics
- **Risk Assessment Processing Time**: < 2 seconds
- **Recommendation Generation Time**: < 5 seconds
- **Prediction Accuracy**: > 80% target
- **Career Protection Success Rate**: > 70% target
- **Early Warning Accuracy**: > 75% target

### Monitoring Alerts
- High-risk user count spikes
- Prediction accuracy drops below threshold
- Emergency unlock usage anomalies
- A/B test significance alerts

## Testing

### Run Tests
```bash
# Run comprehensive test suite
python test_risk_analytics_integration.py

# Run specific test categories
python -m pytest test_risk_analytics_integration.py::RiskAnalyticsIntegrationTester::test_risk_assessment_tracking
```

### Test Coverage
- Risk event tracking functionality
- Risk-based recommendation system
- Career protection outcome measurement
- A/B testing framework validation
- Dashboard and reporting features
- End-to-end workflow testing

## Configuration

### Environment Variables
```bash
# Database configuration
RISK_ANALYTICS_DB_PATH=backend/analytics/risk_analytics.db

# Risk thresholds
DEFAULT_RISK_THRESHOLD=0.6
EMERGENCY_UNLOCK_THRESHOLD=0.7
CRITICAL_RISK_THRESHOLD=0.8

# A/B testing configuration
AB_TEST_MIN_SAMPLE_SIZE=1000
AB_TEST_DURATION_DAYS=14
AB_TEST_SUCCESS_THRESHOLD=10.0
```

### Database Configuration
```python
# Initialize with custom database path
risk_analytics = RiskAnalyticsIntegration("custom/path/risk_analytics.db")

# Initialize database schema
risk_analytics.risk_tracker._init_risk_tables()
```

## Integration with Existing Systems

### Mingus Job Recommendation Engine
- Seamlessly integrates with existing recommendation system
- Extends recommendation triggers based on risk assessment
- Maintains existing performance and reliability standards

### Analytics Integration
- Extends existing AnalyticsIntegration class
- Maintains compatibility with current analytics endpoints
- Adds risk-specific tracking without disrupting existing functionality

### User Behavior Analytics
- Integrates with existing user behavior tracking
- Adds risk-specific interaction tracking
- Maintains existing session and engagement metrics

## Best Practices

### Risk Assessment
1. **Regular Assessments**: Encourage quarterly risk assessments
2. **Multi-Factor Analysis**: Use multiple risk types for comprehensive view
3. **Confidence Scoring**: Include confidence levels for prediction accuracy
4. **Timeline Urgency**: Set appropriate urgency levels for action

### Recommendation Timing
1. **Immediate for Critical Risk**: Act fast for high-risk users
2. **Gradual for Medium Risk**: Allow time for consideration
3. **Proactive for Low Risk**: Maintain engagement and awareness
4. **Personalized Timing**: Consider user behavior patterns

### A/B Testing
1. **Clear Hypotheses**: Define specific test objectives
2. **Adequate Sample Sizes**: Ensure statistical significance
3. **Sufficient Duration**: Allow time for meaningful results
4. **Multiple Metrics**: Track various success indicators

### Data Privacy
1. **Anonymization**: Remove personally identifiable information
2. **Consent Management**: Ensure user consent for risk tracking
3. **Data Retention**: Implement appropriate data retention policies
4. **Security**: Encrypt sensitive risk assessment data

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database file permissions
   - Verify database path configuration
   - Ensure SQLite is properly installed

2. **Risk Assessment Failures**
   - Validate input data format
   - Check risk calculation algorithms
   - Verify confidence score ranges

3. **Recommendation Trigger Issues**
   - Check risk threshold configuration
   - Verify recommendation generation logic
   - Test emergency unlock conditions

4. **A/B Testing Problems**
   - Verify test configuration
   - Check sample size requirements
   - Validate statistical significance calculations

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize with debug mode
risk_analytics = RiskAnalyticsIntegration(debug=True)
```

## Future Enhancements

### Planned Features
- **Machine Learning Integration**: Advanced risk prediction models
- **Real-time Risk Monitoring**: Continuous risk assessment updates
- **Predictive Analytics**: Forecast risk trends and patterns
- **Advanced A/B Testing**: Multi-armed bandit optimization
- **Risk Mitigation Strategies**: Automated risk reduction recommendations

### Integration Opportunities
- **External Risk Data**: Industry and economic risk indicators
- **Social Media Monitoring**: Career risk signals from social platforms
- **Market Intelligence**: Real-time job market risk analysis
- **Skills Gap Analysis**: Dynamic skills demand and supply tracking

## Support

For technical support or questions about the risk analytics integration:

1. Check the troubleshooting section above
2. Review the test suite for examples
3. Examine the API documentation
4. Contact the development team

## License

This module is part of the Mingus Personal Finance Application and follows the same licensing terms.
