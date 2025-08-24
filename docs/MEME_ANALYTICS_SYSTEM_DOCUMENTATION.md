# Meme Analytics System Documentation

## Overview

The Meme Analytics System is a comprehensive solution for tracking the success of the meme splash page feature in the MINGUS personal finance application. It provides event tracking, dashboard queries, automated alerts, and data visualization capabilities.

## Features

### 1. Event Tracking
- **Meme Views**: Track when users view memes
- **Skip Rates**: Monitor how often users skip memes
- **Time Spent**: Measure engagement duration
- **Conversions**: Track when users complete wellness check-ins after viewing memes
- **User Demographics**: Analyze performance by user segments
- **Category Performance**: Compare different meme categories

### 2. Dashboard Queries
- **Daily/Weekly Engagement Rates**: Monitor trends over time
- **Category Popularity**: Identify best and worst performing categories
- **User Retention Correlation**: Analyze meme usage impact on retention
- **Performance Metrics**: Track load times and error rates

### 3. Automated Alerts
- **High Skip Rates** (>70%): Alert when users are skipping too frequently
- **Technical Errors**: Monitor for system issues
- **Unusual Usage Patterns**: Detect anomalies in user behavior

### 4. Data Export
- **CSV Export**: For spreadsheet analysis
- **JSON Export**: For programmatic analysis
- **Sample Reports**: Pre-built reports for non-technical users

## Architecture

### Backend Components

#### 1. Analytics Service (`backend/analytics/meme_analytics.py`)
```python
class MemeAnalyticsService:
    - track_meme_event()
    - get_meme_engagement_metrics()
    - get_category_performance_metrics()
    - get_user_demographics_metrics()
    - get_daily_engagement_trends()
    - check_alert_conditions()
    - export_analytics_data()
    - generate_visualization_charts()
```

#### 2. API Routes (`backend/routes/meme_analytics_routes.py`)
- `/api/meme-analytics/dashboard/metrics` - Get dashboard metrics
- `/api/meme-analytics/dashboard/charts` - Generate visualization charts
- `/api/meme-analytics/alerts` - Get current alerts
- `/api/meme-analytics/export` - Export data
- `/api/meme-analytics/track/event` - Track meme events
- `/api/meme-analytics/sample-queries` - Get sample queries
- `/api/meme-analytics/sample-reports` - Get sample reports

#### 3. Frontend Components
- `MemeAnalyticsDashboard.tsx` - Main dashboard component
- `MemeAnalyticsAdminPage.tsx` - Admin page with navigation

## Database Schema

### Existing Tables (from migration 014)
```sql
-- Memes table
CREATE TABLE memes (
    id VARCHAR(36) PRIMARY KEY,
    image_url VARCHAR(500) NOT NULL,
    category VARCHAR(20) NOT NULL,
    caption_text TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    engagement_score FLOAT DEFAULT 0.0,
    priority INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW()
);

-- User meme history table
CREATE TABLE user_meme_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    meme_id VARCHAR(36) NOT NULL,
    viewed_at DATETIME NOT NULL,
    time_spent_seconds INTEGER DEFAULT 0,
    interaction_type VARCHAR(20) DEFAULT 'view',
    session_id VARCHAR(100),
    source_page VARCHAR(200),
    device_type VARCHAR(50),
    user_agent TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE
);

-- User meme preferences table
CREATE TABLE user_meme_preferences (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    memes_enabled BOOLEAN DEFAULT TRUE,
    preferred_categories TEXT,
    frequency_setting VARCHAR(20) DEFAULT 'daily',
    custom_frequency_days INTEGER DEFAULT 1,
    last_meme_shown_at DATETIME,
    last_meme_shown_id VARCHAR(36),
    opt_out_reason TEXT,
    opt_out_date DATETIME,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (last_meme_shown_id) REFERENCES memes(id) ON DELETE SET NULL
);
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install plotly matplotlib pandas
npm install recharts
```

### 2. Register Blueprint
Add to your Flask app:
```python
from backend.routes.meme_analytics_routes import meme_analytics_bp
app.register_blueprint(meme_analytics_bp)
```

### 3. Import Components
```typescript
import MemeAnalyticsDashboard from '../components/MemeAnalyticsDashboard';
import MemeAnalyticsAdminPage from '../pages/meme-analytics-admin';
```

## Usage Examples

### 1. Tracking Meme Events

#### Backend (Python)
```python
from backend.analytics.meme_analytics import track_meme_view, track_meme_skip, track_meme_conversion

# Track a meme view
track_meme_view(
    user_id=123,
    meme_id="meme-456",
    category="faith",
    time_spent=15,
    session_id="session-789",
    source_page="/dashboard",
    device_type="mobile",
    user_agent="Mozilla/5.0...",
    ip_address="192.168.1.1",
    db_session=db_session,
    config=app_config
)

# Track a meme skip
track_meme_skip(
    user_id=123,
    meme_id="meme-456",
    category="faith",
    time_spent=3,  # Time before skipping
    db_session=db_session,
    config=app_config
)

# Track a conversion (wellness check-in completion)
track_meme_conversion(
    user_id=123,
    meme_id="meme-456",
    category="faith",
    time_spent=25,
    db_session=db_session,
    config=app_config
)
```

#### Frontend (JavaScript)
```javascript
// Track meme view
const trackMemeView = async (memeId, category, timeSpent) => {
  const response = await fetch('/api/meme-analytics/track/event', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_type: 'view',
      user_id: currentUser.id,
      meme_id: memeId,
      category: category,
      time_spent_seconds: timeSpent,
      session_id: sessionId,
      source_page: window.location.pathname,
      device_type: getDeviceType(),
      user_agent: navigator.userAgent,
      ip_address: await getClientIP()
    })
  });
  
  return response.json();
};

// Track meme skip
const trackMemeSkip = async (memeId, category, timeSpent) => {
  const response = await fetch('/api/meme-analytics/track/event', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_type: 'skip',
      user_id: currentUser.id,
      meme_id: memeId,
      category: category,
      time_spent_seconds: timeSpent
    })
  });
  
  return response.json();
};
```

### 2. Getting Analytics Data

#### Dashboard Metrics
```javascript
const getDashboardMetrics = async (days = 30, category = null) => {
  const params = new URLSearchParams({ days });
  if (category) params.append('category', category);
  
  const response = await fetch(`/api/meme-analytics/dashboard/metrics?${params}`);
  const data = await response.json();
  
  return data.data;
};
```

#### Export Data
```javascript
const exportData = async (format = 'csv', days = 30) => {
  const params = new URLSearchParams({ format, days });
  const response = await fetch(`/api/meme-analytics/export?${params}`);
  
  if (format === 'csv') {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `meme_analytics_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  } else {
    const data = await response.json();
    console.log(data);
  }
};
```

### 3. Using the Dashboard Component
```tsx
import MemeAnalyticsDashboard from '../components/MemeAnalyticsDashboard';

function AdminPage() {
  return (
    <div className="admin-page">
      <h1>Meme Analytics</h1>
      <MemeAnalyticsDashboard />
    </div>
  );
}
```

## API Reference

### GET `/api/meme-analytics/dashboard/metrics`
Get comprehensive dashboard metrics.

**Query Parameters:**
- `start_date` (optional): Start date in ISO format
- `end_date` (optional): End date in ISO format
- `category` (optional): Filter by meme category

**Response:**
```json
{
  "success": true,
  "data": {
    "engagement_metrics": {
      "total_views": 1234,
      "total_skips": 567,
      "skip_rate": 45.9,
      "engagement_rate": 54.1,
      "avg_time_spent": 12.5,
      "unique_users": 890
    },
    "category_metrics": [...],
    "daily_trends": [...],
    "demographics": [...],
    "retention_analysis": {...}
  }
}
```

### GET `/api/meme-analytics/dashboard/charts`
Generate visualization charts.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "charts": {
      "engagement_dashboard": "<html>...</html>",
      "category_performance": "<html>...</html>"
    },
    "days_analyzed": 30
  }
}
```

### GET `/api/meme-analytics/alerts`
Get current alerts.

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "alert_id": "high_skip_rate_1234567890",
        "alert_type": "high_skip_rate",
        "severity": "warning",
        "message": "High skip rate detected: 75.2%",
        "threshold": 70,
        "current_value": 75.2,
        "timestamp": "2025-01-27T10:30:00Z",
        "is_resolved": false
      }
    ],
    "total_alerts": 1,
    "critical_alerts": 0,
    "warning_alerts": 1
  }
}
```

### GET `/api/meme-analytics/export`
Export analytics data.

**Query Parameters:**
- `start_date` (optional): Start date in ISO format
- `end_date` (optional): End date in ISO format
- `format`: Export format ('csv' or 'json')

**Response:** File download (CSV) or JSON data

### POST `/api/meme-analytics/track/event`
Track a meme analytics event.

**Request Body:**
```json
{
  "event_type": "view|skip|conversion",
  "user_id": 123,
  "meme_id": "meme-456",
  "category": "faith",
  "time_spent_seconds": 15,
  "session_id": "session-789",
  "source_page": "/dashboard",
  "device_type": "mobile",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

## Sample Queries

### 1. Daily Engagement Overview
```sql
SELECT 
    DATE(viewed_at) as date,
    COUNT(*) as views,
    AVG(time_spent_seconds) as avg_time
FROM user_meme_history 
GROUP BY DATE(viewed_at) 
ORDER BY date;
```

### 2. Category Performance
```sql
SELECT 
    m.category,
    COUNT(h.id) as views,
    AVG(h.time_spent_seconds) as avg_time
FROM user_meme_history h 
JOIN memes m ON h.meme_id = m.id 
GROUP BY m.category;
```

### 3. User Engagement by Device
```sql
SELECT 
    device_type,
    COUNT(*) as views,
    AVG(time_spent_seconds) as avg_time
FROM user_meme_history 
WHERE device_type IS NOT NULL 
GROUP BY device_type;
```

### 4. High Skip Rate Users
```sql
SELECT 
    user_id,
    COUNT(*) as total_views,
    COUNT(CASE WHEN interaction_type = 'skip' THEN 1 END) as skips,
    (COUNT(CASE WHEN interaction_type = 'skip' THEN 1 END) * 100.0 / COUNT(*)) as skip_rate
FROM user_meme_history 
GROUP BY user_id 
HAVING skip_rate > 70;
```

### 5. Conversion Tracking
```sql
SELECT COUNT(*) as conversions 
FROM user_meme_history 
WHERE interaction_type = 'conversion';
```

## Alert Configuration

### Default Thresholds
```python
alert_thresholds = {
    'high_skip_rate': 0.70,      # 70%
    'low_engagement_rate': 0.20,  # 20%
    'high_error_rate': 0.05,      # 5%
    'unusual_usage_pattern': 0.50 # 50% deviation from average
}
```

### Customizing Alerts
```python
# In your analytics service configuration
analytics_config = {
    'alert_thresholds': {
        'high_skip_rate': 0.75,      # Customize to 75%
        'low_engagement_rate': 0.15,  # Customize to 15%
        'high_error_rate': 0.03,      # Customize to 3%
        'unusual_usage_pattern': 0.40 # Customize to 40%
    }
}
```

## Performance Considerations

### 1. Database Indexing
The system includes optimized indexes for common queries:
- `idx_user_meme_history_user_viewed` - User activity queries
- `idx_user_meme_history_interaction` - Interaction type queries
- `idx_memes_category_active` - Category filtering

### 2. Caching
Consider implementing Redis caching for:
- Dashboard metrics (cache for 5-15 minutes)
- Chart generation (cache for 1 hour)
- Alert status (cache for 1 minute)

### 3. Batch Processing
For high-volume tracking:
- Use batch inserts for multiple events
- Implement background job processing
- Consider using message queues

## Troubleshooting

### Common Issues

#### 1. Missing Dependencies
```bash
# Install required packages
pip install plotly matplotlib pandas
npm install recharts
```

#### 2. Database Connection Issues
```python
# Check database connection
from backend.database import get_db_session
session = get_db_session()
# Test query
result = session.execute("SELECT 1").fetchone()
```

#### 3. Chart Generation Errors
```python
# Check if plotly is installed
import plotly.graph_objects as go
# Test chart creation
fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))
```

#### 4. Export Issues
```python
# Check file permissions
import os
export_dir = "/path/to/exports"
os.makedirs(export_dir, exist_ok=True)
```

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger('backend.analytics.meme_analytics').setLevel(logging.DEBUG)
```

## Security Considerations

### 1. Authentication
- All admin endpoints require authentication
- Implement proper role-based access control
- Use session-based authentication

### 2. Data Privacy
- Anonymize sensitive user data in exports
- Implement data retention policies
- Comply with GDPR requirements

### 3. Rate Limiting
- Implement rate limiting on tracking endpoints
- Use IP-based rate limiting for abuse prevention
- Monitor for unusual traffic patterns

## Future Enhancements

### 1. Advanced Analytics
- A/B testing framework
- Predictive analytics
- Machine learning insights

### 2. Real-time Features
- WebSocket-based real-time updates
- Live dashboard updates
- Real-time alert notifications

### 3. Integration
- Email/Slack alert notifications
- Third-party analytics integration
- Custom reporting tools

## Support

For technical support or questions about the Meme Analytics System:

1. Check the troubleshooting section above
2. Review the API documentation
3. Examine the sample queries and reports
4. Contact the development team

## Version History

- **v1.0.0** (2025-01-27): Initial release with basic analytics functionality
- Features: Event tracking, dashboard metrics, alerts, data export
- Components: Analytics service, API routes, React dashboard
