# AI Job Impact Calculator Analytics Implementation

## Overview

This implementation provides comprehensive analytics for the AI Job Impact Calculator, including Google Analytics 4 events, custom dashboard, A/B testing framework, performance monitoring, and business intelligence features.

## Features Implemented

### 1. Google Analytics 4 Events
- `ai_calculator_opened` - Tracks when calculator is opened with source/medium/campaign
- `calculator_step_completed` - Tracks step completion with timing data
- `assessment_submitted` - Tracks assessment submission with job/industry/risk data
- `conversion_offer_viewed` - Tracks when conversion offers are viewed
- `paid_upgrade_clicked` - Tracks paid upgrade clicks with revenue attribution

### 2. Custom Analytics Dashboard
- **Funnel Analysis**: Calculator completion funnel by step with dropoff rates
- **Conversion Tracking**: Conversion rates by risk level and demographics
- **Revenue Attribution**: Revenue tracking by traffic source
- **Popular Content**: Most assessed job titles and industries
- **Geographic Distribution**: Geographic spread of assessments

### 3. A/B Testing Framework
- **Risk Algorithm Testing**: Test different AI risk calculation algorithms
- **Conversion Offer Testing**: Test different conversion offers and pricing
- **Personalization Testing**: Test different personalization strategies
- **Urgency Messaging Testing**: Test different urgency messaging approaches

### 4. Performance Monitoring
- **Calculator Load Times**: Track page and step load performance
- **Database Performance**: Monitor query times and slow queries
- **Error Tracking**: Comprehensive error tracking and alerting
- **Email Delivery**: Track email delivery rates and open rates
- **Payment Processing**: Monitor payment success rates and processing times

### 5. Business Intelligence
- **Weekly Reports**: Automated weekly performance reports
- **Cohort Analysis**: User retention and conversion by cohort
- **Lifetime Value Analysis**: Customer LTV by segments and risk levels
- **Market Intelligence**: Job sector analysis and AI concern levels
- **Lead Source Comparison**: Calculator leads vs other sources

## Architecture

```
backend/analytics/
├── ai_calculator_analytics.py      # Main analytics service
├── ai_calculator_dashboard.py      # Dashboard and reporting
├── ai_calculator_ab_testing.py     # A/B testing framework
├── ai_calculator_performance.py    # Performance monitoring
└── ai_calculator_business_intelligence.py  # BI and insights

backend/routes/
└── analytics_routes.py             # API endpoints

ai-job-impact-calculator.html       # Frontend with analytics integration
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements-analytics.txt
```

Required packages:
- `statsd` - For metrics collection
- `google-analytics-data` - For GA4 integration
- `plotly` - For chart generation
- `psutil` - For system monitoring
- `pandas` - For data analysis

### 2. Configure Environment Variables

```bash
# Analytics Configuration
STATSD_HOST=localhost
STATSD_PORT=8125
GA4_PROPERTY_ID=your_ga4_property_id
GA4_CREDENTIALS_PATH=path/to/service_account.json

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/mingus_db

# Monitoring Configuration
ALERT_WEBHOOK_URL=https://hooks.slack.com/your/webhook
PAGERDUTY_API_KEY=your_pagerduty_key
```

### 3. Database Setup

Run the analytics schema migrations:

```sql
-- Analytics events table
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    session_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assessments table
CREATE TABLE assessments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    session_id VARCHAR(100) NOT NULL,
    job_title VARCHAR(200),
    industry VARCHAR(100),
    risk_level VARCHAR(50),
    completion_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- A/B tests table
CREATE TABLE ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Register Analytics Routes

Add to your Flask app:

```python
from backend.routes.analytics_routes import analytics_bp

app.register_blueprint(analytics_bp)
```

## Usage Examples

### 1. Basic Event Tracking

```javascript
// Frontend - Track calculator opened
trackCalculatorOpened();

// Frontend - Track step completion
trackStepCompleted(1, 45.2); // step 1, 45.2 seconds

// Frontend - Track assessment submission
trackAssessmentSubmitted('Software Engineer', 'Technology', 'low');
```

### 2. Dashboard Data Retrieval

```python
# Get funnel data
from backend.analytics.ai_calculator_dashboard import ai_calculator_dashboard

funnel_data = ai_calculator_dashboard.get_calculator_funnel(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Get conversion rates
conversion_data = ai_calculator_dashboard.get_conversion_rates_by_risk_level(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)
```

### 3. A/B Testing

```python
# Create a conversion offer test
from backend.analytics.ai_calculator_ab_testing import ai_calculator_ab_testing

offers = [
    {'name': 'control', 'price': 49.99, 'features': ['basic']},
    {'name': 'premium', 'price': 79.99, 'features': ['basic', 'advanced']},
    {'name': 'pro', 'price': 99.99, 'features': ['basic', 'advanced', 'priority']}
]

test_id = ai_calculator_ab_testing.create_conversion_offer_test(
    'Pricing Optimization Test',
    offers
)

# Start the test
ai_calculator_ab_testing.start_test(test_id)

# Get variant for user
variant = ai_calculator_ab_testing.get_variant(test_id, user_id='user123')
```

### 4. Performance Monitoring

```python
# Start monitoring
from backend.analytics.ai_calculator_performance import ai_calculator_performance

ai_calculator_performance.start_monitoring()

# Track specific metrics
with ai_calculator_performance.track_calculator_load_time():
    # Calculator loading code
    pass

with ai_calculator_performance.track_database_query('get_user_data'):
    # Database query
    pass

# Get performance summary
summary = ai_calculator_performance.get_performance_summary(hours=24)
```

### 5. Business Intelligence

```python
# Generate weekly report
from backend.analytics.ai_calculator_business_intelligence import ai_calculator_bi

weekly_report = ai_calculator_bi.generate_weekly_report()

# Get cohort analysis
cohorts = ai_calculator_bi.analyze_cohorts(
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now()
)

# Get market intelligence
market_data = ai_calculator_bi.get_market_intelligence(time_period_days=30)
```

## API Endpoints

### Event Tracking
- `POST /api/analytics/event` - Track analytics events

### Dashboard Data
- `GET /api/analytics/dashboard/funnel` - Get funnel data
- `GET /api/analytics/dashboard/conversions` - Get conversion data
- `GET /api/analytics/dashboard/popular` - Get popular jobs/industries
- `GET /api/analytics/dashboard/revenue` - Get revenue attribution

### Reports
- `GET /api/analytics/reports/weekly` - Get weekly report
- `GET /api/analytics/reports/cohorts` - Get cohort analysis
- `GET /api/analytics/reports/ltv` - Get lifetime value analysis
- `GET /api/analytics/reports/market-intelligence` - Get market intelligence
- `GET /api/analytics/reports/lead-comparison` - Compare lead sources

### A/B Testing
- `POST /api/analytics/ab-testing/create` - Create A/B test
- `POST /api/analytics/ab-testing/<test_id>/start` - Start A/B test
- `GET /api/analytics/ab-testing/<test_id>/variant` - Get test variant
- `GET /api/analytics/ab-testing/<test_id>/results` - Get test results

### Performance
- `GET /api/analytics/performance/summary` - Get performance summary
- `POST /api/analytics/performance/start-monitoring` - Start monitoring
- `POST /api/analytics/performance/stop-monitoring` - Stop monitoring

## Monitoring and Alerts

### Performance Thresholds
- Calculator load time: > 3 seconds
- Database query time: > 1 second
- API response time: > 2 seconds
- Error rate: > 5%
- Memory usage: > 80%
- CPU usage: > 70%

### Alert Channels
- Slack webhooks for performance issues
- PagerDuty for critical errors
- Email for weekly reports
- Dashboard for real-time monitoring

## Data Privacy and Compliance

### GDPR Compliance
- All user data is anonymized in analytics
- Session IDs are used instead of user IDs where possible
- Data retention policies are configurable
- Users can request data deletion

### Data Security
- All analytics data is encrypted at rest
- API endpoints require authentication
- Sensitive data is masked in logs
- Regular security audits

## Integration with Existing Systems

### StatsD Integration
```python
# Metrics are automatically sent to StatsD
statsd_client.incr('ai_calculator.assessment_submitted')
statsd_client.timing('ai_calculator.load_time', load_time_ms)
statsd_client.gauge('ai_calculator.conversion_rate', rate)
```

### Grafana Dashboards
Pre-built Grafana dashboards are available for:
- Calculator performance metrics
- Conversion funnel visualization
- Revenue attribution charts
- Error rate monitoring
- A/B test results

### Business Reporting Systems
- Weekly reports are automatically generated
- Data is exported to business intelligence tools
- Integration with CRM systems for lead tracking
- Revenue attribution to marketing campaigns

## Troubleshooting

### Common Issues

1. **Events not being tracked**
   - Check browser console for JavaScript errors
   - Verify API endpoint is accessible
   - Check CSRF token configuration

2. **Performance monitoring not working**
   - Ensure StatsD is running and accessible
   - Check firewall settings for StatsD port
   - Verify monitoring threads are started

3. **A/B tests not showing variants**
   - Check test status is 'active'
   - Verify traffic split configuration
   - Check user/session ID consistency

4. **Database queries slow**
   - Check database connection pool
   - Monitor slow query logs
   - Optimize analytics queries with indexes

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('backend.analytics').setLevel(logging.DEBUG)
```

### Health Checks

```bash
# Check analytics service health
curl http://localhost:5000/api/analytics/health

# Check StatsD connectivity
echo "test.metric:1|c" | nc -u localhost 8125

# Check database connectivity
python -c "from backend.database import get_db_session; print('DB OK')"
```

## Performance Optimization

### Database Optimization
- Add indexes on frequently queried columns
- Use materialized views for complex aggregations
- Implement query result caching
- Partition large tables by date

### Caching Strategy
- Cache dashboard data for 5-15 minutes
- Use Redis for session data
- Implement CDN for static assets
- Cache A/B test configurations

### Scaling Considerations
- Use read replicas for analytics queries
- Implement horizontal scaling for API endpoints
- Use message queues for event processing
- Consider data warehouse for historical analysis

## Future Enhancements

### Planned Features
- Real-time analytics dashboard
- Machine learning for conversion prediction
- Advanced segmentation capabilities
- Multi-touch attribution modeling
- Predictive analytics for user behavior

### Integration Roadmap
- Google Analytics 4 enhanced ecommerce
- Facebook Pixel integration
- LinkedIn Insight Tag
- HubSpot analytics integration
- Salesforce analytics connector

## Support and Maintenance

### Regular Maintenance Tasks
- Weekly: Review performance metrics and optimize queries
- Monthly: Update A/B test configurations and analyze results
- Quarterly: Review and update analytics implementation
- Annually: Comprehensive analytics audit and optimization

### Monitoring Checklist
- [ ] Daily error rate monitoring
- [ ] Weekly conversion rate analysis
- [ ] Monthly performance review
- [ ] Quarterly business impact assessment

### Contact Information
For analytics support and questions:
- Email: analytics@mingus.com
- Slack: #analytics-support
- Documentation: https://docs.mingus.com/analytics

---

This analytics implementation provides a comprehensive foundation for tracking, analyzing, and optimizing the AI Job Impact Calculator's performance and business impact.
