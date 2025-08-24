# Reporting System Guide

This guide covers the comprehensive reporting system for MINGUS, including SQLAlchemy query functions, API endpoints, and analytics capabilities.

## Overview

The reporting system provides:

- **Dashboard Data**: Real-time summary metrics and KPIs
- **Performance Metrics**: Detailed analytics with flexible aggregation
- **Time-Series Analysis**: Trend analysis and historical data
- **User Segmentation**: Behavioral analysis and user categorization
- **Advanced Analytics**: Correlation analysis and predictive insights

## Architecture

### Core Components

1. **ReportingService**: SQLAlchemy query functions for data retrieval
2. **Reporting API**: Flask endpoints for data access
3. **Analytics Models**: Database models for storing metrics
4. **Query Functions**: Optimized SQLAlchemy queries

### Database Models Used

- `CommunicationMetrics`: Message tracking and delivery data
- `UserEngagementMetrics`: User interaction data
- `FinancialImpactMetrics`: ROI and financial outcomes
- `CommunicationPreferences`: User preference data
- `User`: User profile information

---

## SQLAlchemy Query Functions

### 1. Dashboard Data Queries

#### `get_dashboard_summary()`

**Purpose**: Get comprehensive dashboard summary data

**Key Features**:
- Total messages and costs
- Delivery, open, click, and action rates
- Channel breakdown (SMS vs Email)
- Message type breakdown
- Active user count

**SQLAlchemy Query Example**:
```python
# Channel breakdown query
channel_stats = self.db.query(
    CommunicationMetrics.channel,
    func.count(CommunicationMetrics.id).label('total'),
    func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
    func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
    func.sum(case([(CommunicationMetrics.clicked_at.isnot(None), 1)], else_=0)).label('clicked'),
    func.sum(CommunicationMetrics.cost).label('cost')
).filter(
    CommunicationMetrics.sent_at.between(start_date, end_date)
).group_by(CommunicationMetrics.channel).all()
```

**Response Structure**:
```json
{
  "summary": {
    "total_messages": 1250,
    "delivery_rate": 98.5,
    "open_rate": 45.2,
    "click_rate": 12.8,
    "total_cost": 156.75,
    "active_users": 450
  },
  "by_channel": {
    "sms": {
      "total": 800,
      "delivered": 792,
      "delivery_rate": 99.0,
      "cost": 40.0
    },
    "email": {
      "total": 450,
      "delivered": 438,
      "open_rate": 45.1,
      "cost": 116.75
    }
  }
}
```

### 2. Performance Metrics Queries

#### `get_performance_metrics()`

**Purpose**: Get detailed performance metrics with flexible aggregation

**Grouping Options**:
- `day`: Daily performance metrics
- `week`: Weekly aggregated metrics
- `month`: Monthly aggregated metrics
- `channel`: Performance by communication channel
- `message_type`: Performance by message type

**SQLAlchemy Query Example**:
```python
# Time-based grouping with date_trunc
if group_by == 'day':
    date_format = func.date(CommunicationMetrics.sent_at)
elif group_by == 'week':
    date_format = func.date_trunc('week', CommunicationMetrics.sent_at)
elif group_by == 'month':
    date_format = func.date_trunc('month', CommunicationMetrics.sent_at)

metrics = self.db.query(
    date_format.label('period'),
    func.count(CommunicationMetrics.id).label('total_messages'),
    func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
    func.avg(case([(CommunicationMetrics.opened_at.isnot(None), 100)], else_=0)).label('open_rate'),
    func.sum(CommunicationMetrics.cost).label('cost')
).filter(
    CommunicationMetrics.sent_at.between(start_date, end_date)
).group_by(date_format).order_by(date_format).all()
```

### 3. Time-Series Analysis Queries

#### `get_time_series_data()`

**Purpose**: Get time-series data for trend analysis

**Supported Metrics**:
- `messages`: Message count over time
- `delivery_rate`: Delivery rate trends
- `open_rate`: Open rate trends
- `click_rate`: Click rate trends
- `cost`: Cost trends
- `actions`: User action trends

**Time Intervals**:
- `hour`: Hourly data points
- `day`: Daily data points
- `week`: Weekly data points
- `month`: Monthly data points

**SQLAlchemy Query Example**:
```python
# Time-series query with flexible grouping
if interval == 'hour':
    time_group = func.date_trunc('hour', CommunicationMetrics.sent_at)
elif interval == 'day':
    time_group = func.date(CommunicationMetrics.sent_at)
elif interval == 'week':
    time_group = func.date_trunc('week', CommunicationMetrics.sent_at)
elif interval == 'month':
    time_group = func.date_trunc('month', CommunicationMetrics.sent_at)

# Metric-specific queries
if metric == 'messages':
    query = self.db.query(
        time_group.label('timestamp'),
        func.count(CommunicationMetrics.id).label('value')
    )
elif metric == 'delivery_rate':
    query = self.db.query(
        time_group.label('timestamp'),
        func.avg(case([(CommunicationMetrics.status == 'delivered', 100)], else_=0)).label('value')
    )
```

### 4. User Segmentation Queries

#### `get_user_segments()`

**Purpose**: Analyze user behavior and create segments

**Segmentation Criteria**:
- **High Engagement**: >80% open rate, >20% action rate
- **Medium Engagement**: 40-80% open rate
- **Low Engagement**: <40% open rate
- **Inactive**: No communication in last 30 days

**SQLAlchemy Query Example**:
```python
# High engagement users
high_engagement = self.db.query(func.count(func.distinct(CommunicationMetrics.user_id))).filter(
    and_(
        CommunicationMetrics.opened_at.isnot(None),
        CommunicationMetrics.action_taken.isnot(None)
    )
).scalar()

# Inactive users (no communication in last 30 days)
thirty_days_ago = datetime.utcnow() - timedelta(days=30)
inactive_users = self.db.query(func.count(func.distinct(User.id))).filter(
    ~User.id.in_(
        self.db.query(func.distinct(CommunicationMetrics.user_id)).filter(
            CommunicationMetrics.sent_at >= thirty_days_ago
        )
    )
).scalar()
```

### 5. Advanced Analytics Queries

#### `get_correlation_analysis()`

**Purpose**: Analyze correlations between different metrics

**Correlation Analysis**:
- Message count vs delivery rate
- Message count vs open rate
- Message count vs action rate
- Delivery rate vs open rate
- Delivery rate vs action rate
- Open rate vs action rate

**SQLAlchemy Query Example**:
```python
# Daily aggregated data for correlation analysis
daily_data = self.db.query(
    func.date(CommunicationMetrics.sent_at).label('date'),
    func.count(CommunicationMetrics.id).label('message_count'),
    func.avg(case([(CommunicationMetrics.status == 'delivered', 100)], else_=0)).label('delivery_rate'),
    func.avg(case([(CommunicationMetrics.opened_at.isnot(None), 100)], else_=0)).label('open_rate'),
    func.avg(case([(CommunicationMetrics.action_taken.isnot(None), 100)], else_=0)).label('action_rate')
).filter(
    CommunicationMetrics.sent_at.between(start_date, end_date)
).group_by(func.date(CommunicationMetrics.sent_at)).all()
```

#### `get_trend_analysis()`

**Purpose**: Compare performance between time periods

**Analysis Features**:
- Period comparison (first half vs second half)
- Trend direction calculation
- Percentage change analysis
- Moving averages

**SQLAlchemy Query Example**:
```python
# Split period into two halves for comparison
mid_date = start_date + (end_date - start_date) / 2

# First half metrics
first_half = self.db.query(
    func.count(CommunicationMetrics.id).label('total_messages'),
    func.sum(case([(CommunicationMetrics.status == 'delivered', 1)], else_=0)).label('delivered'),
    func.sum(case([(CommunicationMetrics.opened_at.isnot(None), 1)], else_=0)).label('opened'),
    func.sum(case([(CommunicationMetrics.action_taken.isnot(None), 1)], else_=0)).label('actions')
).filter(
    CommunicationMetrics.sent_at.between(start_date, mid_date)
).first()
```

---

## API Endpoints

### Base URL
```
https://api.mingus.com/api/reporting
```

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <your-jwt-token>
```

### 1. Dashboard Summary

#### Endpoint
```
GET /api/reporting/dashboard-summary
```

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |

#### Example Request
```bash
curl -X GET "https://api.mingus.com/api/reporting/dashboard-summary?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 2. Performance Metrics

#### Endpoint
```
GET /api/reporting/performance-metrics
```

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |
| `group_by` | string | No | Grouping level (day/week/month/channel/message_type) |

#### Example Request
```bash
curl -X GET "https://api.mingus.com/api/reporting/performance-metrics?group_by=channel&start_date=2025-01-01" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 3. Time-Series Data

#### Endpoint
```
GET /api/reporting/time-series
```

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |
| `metric` | string | No | Metric to analyze (messages/delivery_rate/open_rate/cost/actions) |
| `interval` | string | No | Time interval (hour/day/week/month) |

#### Example Request
```bash
curl -X GET "https://api.mingus.com/api/reporting/time-series?metric=messages&interval=day&start_date=2025-01-01" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 4. User Segments

#### Endpoint
```
GET /api/reporting/user-segments
```

#### Example Request
```bash
curl -X GET "https://api.mingus.com/api/reporting/user-segments" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 5. Segment Performance

#### Endpoint
```
GET /api/reporting/segment-performance/{segment}
```

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segment` | string | Yes | Segment type (high_engagement/medium_engagement/low_engagement/inactive) |

#### Example Request
```bash
curl -X GET "https://api.mingus.com/api/reporting/segment-performance/high_engagement?start_date=2025-01-01" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### 6. Comprehensive Report

#### Endpoint
```
GET /api/reporting/comprehensive-report
```

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |
| `include_segments` | boolean | No | Include user segments (default: true) |
| `include_predictions` | boolean | No | Include predictive insights (default: true) |

#### Example Request
```bash
curl -X GET "https://api.mingus.com/api/reporting/comprehensive-report?start_date=2025-01-01&include_segments=true" \
  -H "Authorization: Bearer <your-jwt-token>"
```

---

## Usage Examples

### Frontend Integration

```javascript
// Dashboard integration
class AnalyticsDashboard extends React.Component {
  state = {
    dashboardData: null,
    performanceMetrics: null,
    timeSeriesData: null,
    userSegments: null
  };

  async componentDidMount() {
    const [dashboard, metrics, timeSeries, segments] = await Promise.all([
      this.fetchDashboardSummary(),
      this.fetchPerformanceMetrics(),
      this.fetchTimeSeriesData(),
      this.fetchUserSegments()
    ]);

    this.setState({
      dashboardData: dashboard,
      performanceMetrics: metrics,
      timeSeriesData: timeSeries,
      userSegments: segments
    });
  }

  async fetchDashboardSummary() {
    const response = await fetch('/api/reporting/dashboard-summary?start_date=2025-01-01');
    return response.json();
  }

  async fetchPerformanceMetrics() {
    const response = await fetch('/api/reporting/performance-metrics?group_by=day');
    return response.json();
  }

  async fetchTimeSeriesData() {
    const response = await fetch('/api/reporting/time-series?metric=messages&interval=day');
    return response.json();
  }

  async fetchUserSegments() {
    const response = await fetch('/api/reporting/user-segments');
    return response.json();
  }

  render() {
    const { dashboardData, performanceMetrics, timeSeriesData, userSegments } = this.state;
    
    return (
      <div className="analytics-dashboard">
        <DashboardSummaryCard data={dashboardData} />
        <PerformanceMetricsChart data={performanceMetrics} />
        <TimeSeriesChart data={timeSeriesData} />
        <UserSegmentsCard data={userSegments} />
      </div>
    );
  }
}
```

### Python Integration

```python
from backend.services.reporting_service import ReportingService

# Initialize reporting service
reporting_service = ReportingService()

# Get dashboard summary
dashboard_summary = reporting_service.get_dashboard_summary(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)

# Get performance metrics by channel
channel_metrics = reporting_service.get_performance_metrics(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    group_by='channel'
)

# Get time series data
time_series = reporting_service.get_time_series_data(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    metric='messages',
    interval='day'
)

# Get user segments
user_segments = reporting_service.get_user_segments()

# Get comprehensive report
comprehensive_report = reporting_service.get_comprehensive_report(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)
```

---

## Performance Optimization

### Database Indexes

Ensure proper indexes for optimal query performance:

```sql
-- Communication metrics indexes
CREATE INDEX idx_comm_metrics_sent_at ON communication_metrics(sent_at);
CREATE INDEX idx_comm_metrics_user_id ON communication_metrics(user_id);
CREATE INDEX idx_comm_metrics_channel ON communication_metrics(channel);
CREATE INDEX idx_comm_metrics_message_type ON communication_metrics(message_type);
CREATE INDEX idx_comm_metrics_status ON communication_metrics(status);

-- Composite indexes for common queries
CREATE INDEX idx_comm_metrics_user_date ON communication_metrics(user_id, sent_at);
CREATE INDEX idx_comm_metrics_channel_date ON communication_metrics(channel, sent_at);
```

### Query Optimization

1. **Use appropriate date ranges**: Limit queries to reasonable time periods
2. **Leverage database functions**: Use `date_trunc` for time-based grouping
3. **Optimize aggregations**: Use `func.sum()` and `func.avg()` efficiently
4. **Index usage**: Ensure queries use indexed columns

### Caching Strategy

```python
# Example caching implementation
from functools import lru_cache
import redis

class CachedReportingService(ReportingService):
    def __init__(self):
        super().__init__()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    @lru_cache(maxsize=128)
    def get_dashboard_summary(self, start_date=None, end_date=None):
        # Check cache first
        cache_key = f"dashboard_summary:{start_date}:{end_date}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Get fresh data
        data = super().get_dashboard_summary(start_date, end_date)
        
        # Cache for 5 minutes
        self.redis_client.setex(cache_key, 300, json.dumps(data))
        
        return data
```

---

## Best Practices

### 1. Query Design
- Use appropriate SQLAlchemy functions for aggregations
- Leverage database indexes effectively
- Implement proper error handling
- Use parameterized queries to prevent SQL injection

### 2. Performance
- Limit date ranges for large datasets
- Use pagination for large result sets
- Implement caching for frequently accessed data
- Monitor query performance and optimize slow queries

### 3. Data Accuracy
- Validate input parameters
- Handle edge cases (empty datasets, null values)
- Implement proper rounding for percentage calculations
- Use appropriate data types for financial calculations

### 4. Security
- Implement proper authentication and authorization
- Validate all input parameters
- Use parameterized queries
- Log access to sensitive data

### 5. Monitoring
- Track API usage and performance
- Monitor database query performance
- Set up alerts for system issues
- Log errors and exceptions for debugging

---

## Error Handling

### Common Error Scenarios

1. **Invalid Date Parameters**
```python
def parse_date_param(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return datetime.utcnow() - timedelta(days=30)
```

2. **Empty Result Sets**
```python
if not metrics:
    return {
        'summary': {
            'total_messages': 0,
            'delivery_rate': 0.0,
            'total_cost': 0.0
        }
    }
```

3. **Database Connection Issues**
```python
try:
    result = self.db.query(CommunicationMetrics).all()
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise
```

### Error Response Format

```json
{
  "error": "Error description",
  "timestamp": "2025-01-27T12:00:00Z",
  "request_id": "unique-request-id"
}
```

---

## Future Enhancements

### Planned Features

1. **Real-time Analytics**: WebSocket-based real-time dashboard updates
2. **Advanced Segmentation**: Machine learning-based user segmentation
3. **Predictive Analytics**: Advanced forecasting and trend prediction
4. **Custom Reports**: User-defined report builder
5. **Data Export**: CSV/Excel export functionality
6. **Scheduled Reports**: Automated report generation and delivery

### Performance Improvements

1. **Materialized Views**: Pre-computed aggregations for faster queries
2. **Read Replicas**: Separate read databases for analytics queries
3. **Query Optimization**: Advanced query optimization techniques
4. **Caching Layers**: Multi-level caching strategy
5. **Data Warehousing**: Dedicated analytics data warehouse 