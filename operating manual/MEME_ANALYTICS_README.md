# 🎭 Meme Analytics System

A comprehensive analytics system for tracking the success of the meme splash page feature in the Mingus Personal Finance App. This system provides detailed insights into user engagement, content performance, and system health.

## 🚀 Features

### 📊 Event Tracking
- **Meme views by category** - Track which categories are most popular
- **Skip rates by user demographics** - Understand user behavior patterns
- **Time spent viewing memes** - Measure engagement depth
- **Conversion from meme to wellness check-in** - Track feature effectiveness
- **User preference changes over time** - Monitor evolving user behavior

### 📈 Dashboard Queries
- **Daily/weekly meme engagement rates** - Monitor performance trends
- **Most/least popular meme categories** - Identify content winners and losers
- **User retention correlation with meme usage** - Measure feature impact
- **Performance metrics (load times, errors)** - Ensure system health

### 🚨 Automated Alerts
- **High skip rates (>70%)** - Immediate attention for content issues
- **Technical errors** - System health monitoring
- **Unusual usage patterns** - Detect anomalies and trends

### 📋 Reporting & Export
- **CSV export functionality** - For deeper analysis in Excel/Google Sheets
- **Simple admin dashboard** - Visual charts and metrics
- **Non-technical reports** - Easy-to-understand insights for stakeholders

## 📁 System Components

### Core Files
- `meme_analytics_schema.sql` - Database schema for analytics tables
- `meme_analytics_system.py` - Main analytics engine and data processing
- `meme_analytics_api.py` - Flask API endpoints for web integration
- `meme_analytics_dashboard.py` - Desktop GUI dashboard application
- `meme_analytics_reports.py` - Report generation and sample queries

### Database Tables
- `meme_analytics_events` - Individual user interactions
- `user_demographics` - User profile information
- `meme_performance_metrics` - Daily performance aggregations
- `category_performance` - Category-level analytics
- `user_engagement_sessions` - Session-based analysis
- `analytics_alerts` - Alert management
- `daily_analytics_summary` - High-level daily metrics

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements_analytics.txt
```

### 2. Initialize Database
The system will automatically create the analytics database schema when first run. Ensure your main meme database (`mingus_memes.db`) exists.

### 3. Run the Analytics System
```bash
# Start the web API server
python meme_analytics_api.py

# Or run the desktop dashboard
python meme_analytics_dashboard.py

# Or generate reports
python meme_analytics_reports.py
```

## 📊 Usage Examples

### Basic Event Tracking
```python
from meme_analytics_system import MemeAnalyticsSystem, AnalyticsEvent

# Initialize the system
analytics = MemeAnalyticsSystem()

# Track a meme view
event = AnalyticsEvent(
    user_id=123,
    session_id="session_456",
    meme_id=1,
    event_type="view",
    time_spent_seconds=8,
    device_type="mobile"
)
analytics.track_event(event)
```

### Getting Performance Metrics
```python
# Get 30-day performance summary
metrics = analytics.get_performance_metrics(30)
print(f"Total views: {metrics['total_views']}")
print(f"Skip rate: {metrics['skip_rate']:.1f}%")
print(f"Continue rate: {metrics['continue_rate']:.1f}%")
```

### Category Analysis
```python
# Get category performance
category_data = analytics.get_category_performance(30)
print(category_data[['category', 'total_views', 'skip_rate', 'continue_rate']])
```

### Generate Reports
```python
from meme_analytics_reports import MemeAnalyticsReports

reports = MemeAnalyticsReports()
summary = reports.generate_executive_summary(30)
print(summary)
```

## 🌐 Web API Endpoints

### Event Tracking
- `POST /api/analytics/track-event` - Track user interactions
- `POST /api/analytics/user-demographics` - Update user demographics

### Dashboard Data
- `GET /api/analytics/dashboard/daily-engagement` - Daily engagement rates
- `GET /api/analytics/dashboard/category-performance` - Category metrics
- `GET /api/analytics/dashboard/performance-metrics` - Overall performance
- `GET /api/analytics/dashboard/user-retention` - User retention analysis

### Reports & Export
- `GET /api/analytics/reports/generate` - Generate analytics report
- `GET /api/analytics/export/daily-engagement` - Export daily data to CSV
- `GET /api/analytics/export/category-performance` - Export category data to CSV

### Alerts
- `GET /api/analytics/alerts` - Get current alerts
- `POST /api/analytics/alerts/create` - Create new alert

### Dashboard
- `GET /api/analytics/dashboard` - Web-based dashboard interface

## 📱 Integration with Frontend

### React Component Integration
```javascript
// Track meme view
const trackMemeView = async (memeId, timeSpent) => {
  await fetch('/api/analytics/track-event', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      session_id: sessionId,
      meme_id: memeId,
      event_type: 'view',
      time_spent_seconds: timeSpent,
      device_type: 'mobile'
    })
  });
};

// Track user action
const trackUserAction = async (memeId, action) => {
  await fetch('/api/analytics/track-event', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      session_id: sessionId,
      meme_id: memeId,
      event_type: action // 'continue', 'skip', 'auto_advance'
    })
  });
};
```

## 📊 Key Metrics Explained

### Engagement Metrics
- **Continue Rate**: Percentage of users who proceed to the app after seeing a meme
- **Skip Rate**: Percentage of users who skip the meme feature
- **Time Spent**: Average time users spend viewing memes
- **Engagement Rate**: Combined continue and auto-advance rates

### Performance Metrics
- **Total Views**: Number of meme displays
- **Unique Users**: Number of different users who viewed memes
- **Session Count**: Number of user sessions involving memes
- **Error Rate**: Percentage of failed meme loads or interactions

### Retention Metrics
- **User Retention**: How often users return to use the meme feature
- **Session Frequency**: Average number of meme interactions per user
- **Active Days**: Number of days users engage with memes

## 🚨 Alert System

### Alert Types
- **High Skip Rate**: Skip rate exceeds 70% (configurable)
- **Technical Errors**: Error rate exceeds 5%
- **Unusual Usage Patterns**: Sudden drops in activity
- **Performance Degradation**: Slow load times or system issues

### Alert Severity Levels
- **Critical**: Immediate attention required
- **High**: Address within 24 hours
- **Medium**: Address within a week
- **Low**: Monitor and address as needed

## 📈 Sample Reports

### Executive Summary
High-level overview with key metrics, trends, and recommendations in plain English.

### Category Analysis
Detailed breakdown of performance by meme category with rankings and insights.

### User Behavior Report
Analysis of user engagement patterns, retention, and behavior trends.

### Weekly Trend Report
Week-over-week performance comparison with trend analysis and recommendations.

## 🔧 Configuration

### Database Configuration
```python
# Custom database path
analytics = MemeAnalyticsSystem("custom_database.db")
```

### Alert Thresholds
```python
# Customize alert thresholds in the analytics system
# High skip rate threshold (default: 70%)
# Error rate threshold (default: 5%)
# Usage pattern sensitivity (default: 50% drop)
```

### Chart Customization
```python
# Customize chart appearance
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
```

## 🧪 Testing

### Run Sample Data Test
```bash
python meme_analytics_system.py
```

This will:
- Create sample events and demographics
- Generate test reports
- Create sample charts
- Export test data to CSV

### Test API Endpoints
```bash
# Start the API server
python meme_analytics_api.py

# Test endpoints
curl http://localhost:5001/api/analytics/health
curl http://localhost:5001/api/analytics/dashboard/performance-metrics
```

## 📋 Production Checklist

### Before Going Live
- [ ] Database schema created and tested
- [ ] API endpoints tested and secured
- [ ] Alert thresholds configured appropriately
- [ ] Dashboard access controls implemented
- [ ] Data retention policies established
- [ ] Performance monitoring in place
- [ ] Backup procedures documented

### Monitoring
- [ ] Set up automated report generation
- [ ] Configure alert notifications
- [ ] Monitor system performance
- [ ] Track data quality metrics
- [ ] Review analytics accuracy regularly

## 🔒 Security Considerations

### Data Privacy
- User data is anonymized where possible
- Personal information is handled according to privacy policies
- Analytics data is aggregated to protect individual privacy

### API Security
- Implement authentication for admin endpoints
- Use HTTPS in production
- Validate all input data
- Implement rate limiting

### Database Security
- Regular backups of analytics data
- Access controls for database connections
- Audit logging for sensitive operations

## 📞 Support & Troubleshooting

### Common Issues

**Database Connection Errors**
- Check database file permissions
- Ensure SQLite is properly installed
- Verify database path is correct

**Chart Generation Failures**
- Install required visualization libraries
- Check matplotlib backend configuration
- Verify data availability

**API Endpoint Errors**
- Check Flask installation
- Verify CORS configuration
- Review error logs for details

### Getting Help
1. Check the log files (`meme_analytics.log`)
2. Review error messages in the console
3. Verify all dependencies are installed
4. Test with sample data first

## 🚀 Future Enhancements

### Planned Features
- Real-time analytics dashboard
- Advanced machine learning insights
- A/B testing framework
- Custom report builder
- Mobile app integration
- Advanced user segmentation

### Integration Opportunities
- Email marketing platforms
- Customer support systems
- Business intelligence tools
- Data warehouse connections

## 📄 License

This analytics system is part of the Mingus Personal Finance App project.

---

*For technical support or feature requests, contact the development team.*
