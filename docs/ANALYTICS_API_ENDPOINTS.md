# Analytics API Endpoints Documentation

This document provides comprehensive documentation for the Flask analytics API endpoints that provide insights into communication effectiveness, user engagement, channel performance, and cost tracking.

## Overview

The analytics API endpoints provide real-time insights into:

- **Communication Summary**: Overall communication performance metrics
- **User Engagement**: Detailed user-specific engagement analytics
- **Channel Effectiveness**: SMS vs Email performance comparison
- **Cost Tracking**: Detailed cost analysis and ROI tracking

## Authentication

All endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Base URL

```
https://api.mingus.com/api/analytics
```

---

## 1. Communication Summary

### Endpoint
```
GET /api/analytics/communication-summary
```

### Description
Get comprehensive communication analytics summary with breakdowns by channel and message type.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date for analysis (YYYY-MM-DD) |
| `end_date` | string | No | End date for analysis (YYYY-MM-DD) |
| `user_id` | integer | No | Filter by specific user ID |
| `channel` | string | No | Filter by channel (sms/email) |
| `message_type` | string | No | Filter by message type |

### Example Request

```bash
curl -X GET "https://api.mingus.com/api/analytics/communication-summary?start_date=2025-01-01&end_date=2025-01-31&channel=sms" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Response

```json
{
  "summary": {
    "total_messages": 1250,
    "delivery_rate": 98.5,
    "open_rate": 45.2,
    "click_rate": 12.8,
    "total_cost": 156.75,
    "average_cost_per_message": 0.1254
  },
  "by_channel": {
    "sms": {
      "total": 800,
      "delivered": 792,
      "opened": 0,
      "clicked": 0,
      "cost": 40.0,
      "delivery_rate": 99.0,
      "open_rate": 0.0,
      "click_rate": 0.0,
      "avg_cost": 0.05
    },
    "email": {
      "total": 450,
      "delivered": 438,
      "opened": 203,
      "clicked": 58,
      "cost": 116.75,
      "delivery_rate": 97.3,
      "open_rate": 45.1,
      "click_rate": 12.9,
      "avg_cost": 0.2594
    }
  },
  "by_message_type": {
    "low_balance": {
      "total": 300,
      "delivered": 297,
      "opened": 0,
      "clicked": 0,
      "cost": 15.0,
      "delivery_rate": 99.0,
      "open_rate": 0.0,
      "click_rate": 0.0,
      "avg_cost": 0.05
    },
    "weekly_checkin": {
      "total": 950,
      "delivered": 933,
      "opened": 203,
      "clicked": 58,
      "cost": 141.75,
      "delivery_rate": 98.2,
      "open_rate": 21.4,
      "click_rate": 6.1,
      "avg_cost": 0.1492
    }
  },
  "time_period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }
}
```

---

## 2. User Engagement

### Endpoint
```
GET /api/analytics/user-engagement/{user_id}
```

### Description
Get detailed user engagement analytics for a specific user, including communication history, response patterns, and channel preferences.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to analyze |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date for analysis (YYYY-MM-DD) |
| `end_date` | string | No | End date for analysis (YYYY-MM-DD) |
| `limit` | integer | No | Number of recent messages to include (default: 50) |

### Example Request

```bash
curl -X GET "https://api.mingus.com/api/analytics/user-engagement/123?start_date=2025-01-01&limit=25" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Response

```json
{
  "user_id": 123,
  "engagement_summary": {
    "total_messages_received": 45,
    "delivery_rate": 97.8,
    "open_rate": 51.1,
    "click_rate": 15.6,
    "response_rate": 22.2,
    "average_response_time_hours": 3.45
  },
  "channel_preferences": {
    "sms": {
      "total": 20,
      "delivered": 20,
      "opened": 0,
      "clicked": 0,
      "actions": 5,
      "delivery_rate": 100.0,
      "open_rate": 0.0,
      "click_rate": 0.0,
      "action_rate": 25.0
    },
    "email": {
      "total": 25,
      "delivered": 24,
      "opened": 23,
      "clicked": 7,
      "actions": 5,
      "delivery_rate": 96.0,
      "open_rate": 92.0,
      "click_rate": 28.0,
      "action_rate": 20.0
    }
  },
  "message_type_engagement": {
    "low_balance": {
      "total": 15,
      "delivered": 15,
      "opened": 0,
      "clicked": 0,
      "actions": 3,
      "delivery_rate": 100.0,
      "open_rate": 0.0,
      "click_rate": 0.0,
      "action_rate": 20.0
    },
    "weekly_checkin": {
      "total": 30,
      "delivered": 29,
      "opened": 23,
      "clicked": 7,
      "actions": 7,
      "delivery_rate": 96.7,
      "open_rate": 76.7,
      "click_rate": 23.3,
      "action_rate": 23.3
    }
  },
  "recent_communications": [
    {
      "id": 456,
      "message_type": "weekly_checkin",
      "channel": "email",
      "status": "delivered",
      "sent_at": "2025-01-27T10:00:00Z",
      "delivered_at": "2025-01-27T10:00:05Z",
      "opened_at": "2025-01-27T13:30:00Z",
      "clicked_at": null,
      "action_taken": "viewed_forecast",
      "cost": 0.001
    }
  ],
  "response_patterns": {
    "hour_of_day": {
      "9": 3,
      "10": 5,
      "13": 8,
      "14": 4,
      "15": 3
    },
    "day_of_week": {
      "0": 5,
      "1": 8,
      "2": 6,
      "3": 4,
      "4": 3,
      "5": 2,
      "6": 1
    },
    "response_delay": {
      "immediate": 5,
      "same_day": 15,
      "next_day": 3,
      "never": 22
    }
  }
}
```

---

## 3. Channel Effectiveness

### Endpoint
```
GET /api/analytics/channel-effectiveness
```

### Description
Get channel effectiveness comparison between SMS and Email, including performance metrics, cost analysis, and optimization recommendations.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date for analysis (YYYY-MM-DD) |
| `end_date` | string | No | End date for analysis (YYYY-MM-DD) |
| `user_id` | integer | No | Filter by specific user ID |
| `message_type` | string | No | Filter by message type |

### Example Request

```bash
curl -X GET "https://api.mingus.com/api/analytics/channel-effectiveness?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Response

```json
{
  "channel_comparison": {
    "sms": {
      "total_messages": 800,
      "delivery_rate": 99.0,
      "open_rate": 0.0,
      "click_rate": 0.0,
      "action_rate": 18.5,
      "total_cost": 40.0,
      "average_cost_per_message": 0.05
    },
    "email": {
      "total_messages": 450,
      "delivery_rate": 97.3,
      "open_rate": 45.1,
      "click_rate": 12.9,
      "action_rate": 15.6,
      "total_cost": 116.75,
      "average_cost_per_message": 0.2594
    }
  },
  "performance_metrics": {
    "sms": {
      "effectiveness_score": 35.5,
      "engagement_score": 7.4,
      "cost_efficiency": 370.0
    },
    "email": {
      "effectiveness_score": 52.8,
      "engagement_score": 32.1,
      "cost_efficiency": 60.2
    }
  },
  "cost_analysis": {
    "sms": {
      "total_spent": 40.0,
      "cost_per_delivery": 0.0505,
      "cost_per_action": 0.2703,
      "roi_percentage": 362.5
    },
    "email": {
      "total_spent": 116.75,
      "cost_per_delivery": 0.2666,
      "cost_per_action": 1.7089,
      "roi_percentage": 33.7
    }
  },
  "recommendations": [
    {
      "type": "delivery_rate",
      "recommendation": "SMS has significantly higher delivery rate",
      "priority": "high",
      "action": "Consider using SMS for critical communications"
    },
    {
      "type": "engagement",
      "recommendation": "Email drives higher user actions",
      "priority": "medium",
      "action": "Use email for detailed content and complex actions"
    },
    {
      "type": "cost",
      "recommendation": "SMS is significantly more cost-effective",
      "priority": "medium",
      "action": "Use SMS for low-volume, high-impact communications"
    }
  ]
}
```

---

## 4. Cost Tracking

### Endpoint
```
GET /api/analytics/cost-tracking
```

### Description
Get detailed cost tracking and analysis with breakdowns by time, channel, message type, and ROI analysis.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date for analysis (YYYY-MM-DD) |
| `end_date` | string | No | End date for analysis (YYYY-MM-DD) |
| `user_id` | integer | No | Filter by specific user ID |
| `channel` | string | No | Filter by channel (sms/email) |
| `message_type` | string | No | Filter by message type |
| `group_by` | string | No | Group by (day/week/month/channel/message_type) |

### Example Request

```bash
curl -X GET "https://api.mingus.com/api/analytics/cost-tracking?start_date=2025-01-01&group_by=channel" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Response

```json
{
  "cost_summary": {
    "total_cost": 156.75,
    "total_messages": 1250,
    "average_cost_per_message": 0.1254,
    "cost_per_delivery": 0.1272,
    "cost_per_action": 0.5231
  },
  "cost_breakdown": {
    "sms": {
      "total_cost": 40.0,
      "message_count": 800,
      "delivered_count": 792,
      "action_count": 148,
      "average_cost_per_message": 0.05,
      "cost_per_delivery": 0.0505,
      "cost_per_action": 0.2703,
      "delivery_rate": 99.0,
      "action_rate": 18.5
    },
    "email": {
      "total_cost": 116.75,
      "message_count": 450,
      "delivered_count": 438,
      "action_count": 70,
      "average_cost_per_message": 0.2594,
      "cost_per_delivery": 0.2666,
      "cost_per_action": 1.6679,
      "delivery_rate": 97.3,
      "action_rate": 15.6
    }
  },
  "cost_trends": [
    {
      "date": "2025-01-01",
      "total_cost": 5.25,
      "message_count": 42,
      "action_count": 8,
      "average_cost_per_message": 0.125
    },
    {
      "date": "2025-01-02",
      "total_cost": 4.80,
      "message_count": 38,
      "action_count": 7,
      "average_cost_per_message": 0.1263
    }
  ],
  "roi_analysis": {
    "total_investment": 156.75,
    "total_value_generated": 2180.0,
    "net_return": 2023.25,
    "roi_percentage": 1290.8,
    "value_per_action": 10.0,
    "break_even_point": 16
  },
  "budget_status": {
    "monthly_budget": 1000.0,
    "current_month_cost": 156.75,
    "budget_utilization_percentage": 15.68,
    "budget_remaining": 843.25,
    "budget_status": "under_budget"
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "error": "Invalid parameters"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to get analytics data"
}
```

---

## Usage Examples

### Frontend Integration

```javascript
// Get communication summary
async function getCommunicationSummary(startDate, endDate) {
  const response = await fetch(
    `/api/analytics/communication-summary?start_date=${startDate}&end_date=${endDate}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
}

// Get user engagement
async function getUserEngagement(userId) {
  const response = await fetch(
    `/api/analytics/user-engagement/${userId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
}

// Get channel effectiveness
async function getChannelEffectiveness() {
  const response = await fetch(
    '/api/analytics/channel-effectiveness',
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
}

// Get cost tracking
async function getCostTracking(groupBy = 'day') {
  const response = await fetch(
    `/api/analytics/cost-tracking?group_by=${groupBy}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
}
```

### Dashboard Integration

```javascript
// Dashboard component example
class AnalyticsDashboard extends React.Component {
  state = {
    summary: null,
    userEngagement: null,
    channelEffectiveness: null,
    costTracking: null
  };

  async componentDidMount() {
    const [summary, userEngagement, channelEffectiveness, costTracking] = await Promise.all([
      getCommunicationSummary('2025-01-01', '2025-01-31'),
      getUserEngagement(this.props.userId),
      getChannelEffectiveness(),
      getCostTracking('day')
    ]);

    this.setState({
      summary,
      userEngagement,
      channelEffectiveness,
      costTracking
    });
  }

  render() {
    const { summary, userEngagement, channelEffectiveness, costTracking } = this.state;
    
    return (
      <div className="analytics-dashboard">
        <CommunicationSummaryCard data={summary} />
        <UserEngagementCard data={userEngagement} />
        <ChannelEffectivenessCard data={channelEffectiveness} />
        <CostTrackingCard data={costTracking} />
      </div>
    );
  }
}
```

---

## Performance Considerations

### Caching
- Consider implementing caching for analytics data that doesn't change frequently
- Use appropriate cache headers for time-based data
- Cache user engagement data for 5-15 minutes depending on usage patterns

### Rate Limiting
- Analytics endpoints may be rate-limited to prevent abuse
- Implement client-side throttling for dashboard updates
- Use pagination for large datasets

### Data Retention
- Analytics data is retained based on your data retention policy
- Historical data may be aggregated for performance
- Consider data archiving for long-term analytics

---

## Best Practices

### 1. Date Ranges
- Use reasonable date ranges to avoid performance issues
- Default to last 30 days if no date range specified
- Consider timezone handling for global applications

### 2. Filtering
- Use specific filters to reduce data volume
- Combine filters for more targeted insights
- Consider user permissions when filtering by user_id

### 3. Error Handling
- Always handle API errors gracefully
- Implement retry logic for transient failures
- Show appropriate loading states during API calls

### 4. Data Visualization
- Use appropriate chart types for different metrics
- Implement real-time updates for live dashboards
- Consider mobile responsiveness for analytics displays

### 5. Security
- Ensure proper authentication for all analytics endpoints
- Implement role-based access control for sensitive data
- Log analytics access for audit purposes 