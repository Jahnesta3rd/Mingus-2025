# Unified Risk Analytics API Documentation

## Overview

The Unified Risk Analytics API provides comprehensive risk-based career protection functionality, seamlessly integrating with the existing job recommendation system. This API extends the current 44 RESTful endpoints with risk-specific functionality, real-time monitoring, and analytics tracking.

## Table of Contents

1. [API Architecture](#api-architecture)
2. [Authentication & Authorization](#authentication--authorization)
3. [Core Risk Analytics Endpoints](#core-risk-analytics-endpoints)
4. [Real-Time Risk Monitoring](#real-time-risk-monitoring)
5. [Risk A/B Testing Integration](#risk-ab-testing-integration)
6. [WebSocket Integration](#websocket-integration)
7. [Performance Optimization](#performance-optimization)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Integration Examples](#integration-examples)
11. [Testing](#testing)

## API Architecture

### Base URL
```
https://api.mingus.com/api/risk
```

### Response Format
All responses follow a consistent JSON format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Authentication & Authorization

### Required Headers
```http
Authorization: Bearer <jwt_token>
X-CSRF-Token: <csrf_token>
Content-Type: application/json
```

### User Roles
- **Standard User**: Access to personal risk analytics
- **Admin User**: Access to comprehensive analytics and system management

## Core Risk Analytics Endpoints

### 1. Risk Assessment with Full Tracking

**POST** `/api/risk/assess-and-track`

Performs comprehensive risk assessment with full analytics tracking.

#### Request Body
```json
{
  "assessment_type": "comprehensive",
  "include_recommendations": true,
  "track_analytics": true
}
```

#### Response
```json
{
  "success": true,
  "risk_analysis": {
    "overall_risk": 0.7,
    "risk_breakdown": {
      "ai_displacement_probability": 0.6,
      "layoff_probability": 0.4,
      "industry_risk_level": 0.5
    },
    "risk_triggers": [
      {
        "factor": "AI automation",
        "score": 0.8,
        "timeline": "6_months"
      }
    ],
    "confidence_score": 0.85
  },
  "recommendations_triggered": true,
  "recommendations": {
    "conservative": [...],
    "optimal": [...],
    "stretch": [...]
  },
  "analytics_tracked": true,
  "assessment_performance": {
    "processing_time": 1.2,
    "meets_targets": true
  }
}
```

### 2. Risk Dashboard

**GET** `/api/risk/dashboard/{user_id}`

Retrieves comprehensive risk dashboard with analytics.

#### Query Parameters
- `days` (optional): Analysis period in days (default: 30)

#### Response
```json
{
  "success": true,
  "user_id": "user_123",
  "career_protection_metrics": {
    "success_rate": 0.85,
    "total_interventions": 150,
    "risk_reduction_avg": 0.3
  },
  "risk_trends": [
    {
      "date": "2024-01-15T00:00:00Z",
      "risk_score": 0.7,
      "primary_factor": "AI automation",
      "triggers": [...]
    }
  ],
  "performance_data": {
    "avg_response_time": 250.0,
    "success_rate": 0.98
  },
  "active_experiments": [
    {
      "test_id": "risk_threshold_001",
      "test_name": "Risk Threshold Optimization",
      "variant": "treatment"
    }
  ],
  "dashboard_generated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Trigger Risk-Based Recommendations

**POST** `/api/risk/trigger-recommendations`

Triggers risk-based recommendations with tracking.

#### Request Body
```json
{
  "risk_data": {
    "overall_risk": 0.7,
    "risk_breakdown": {...},
    "risk_triggers": [...]
  },
  "recommendation_tiers": ["conservative", "optimal", "stretch"],
  "max_recommendations_per_tier": 5
}
```

#### Response
```json
{
  "success": true,
  "recommendations": {
    "conservative": [
      {
        "job_id": "job_123",
        "title": "Software Engineer",
        "company": "Tech Corp",
        "match_score": 0.85,
        "risk_mitigation": "Stable role with growth potential"
      }
    ],
    "optimal": [...],
    "stretch": [...]
  },
  "analytics_tracked": true,
  "triggered_at": "2024-01-15T10:30:00Z"
}
```

### 4. Career Protection Effectiveness

**GET** `/api/risk/analytics/effectiveness`

Gets career protection effectiveness metrics.

#### Query Parameters
- `days` (optional): Analysis period in days (default: 30)

#### Response
```json
{
  "success": true,
  "effectiveness_metrics": {
    "success_rate": 0.85,
    "intervention_effectiveness": 0.78,
    "user_engagement": 0.92
  },
  "prediction_accuracy": {
    "overall_accuracy": 0.82,
    "accuracy_by_risk_level": {
      "low": 0.95,
      "medium": 0.80,
      "high": 0.75
    }
  },
  "engagement_metrics": {
    "active_users_7d": 1250,
    "avg_engagement_score": 0.88
  },
  "analysis_period_days": 30
}
```

### 5. Track Risk Intervention Outcome

**POST** `/api/risk/outcome/track`

Tracks outcomes from risk-based interventions.

#### Request Body
```json
{
  "outcome_type": "job_saved",
  "original_risk_score": 0.7,
  "intervention_date": "2024-01-01",
  "actual_outcome": "success",
  "outcome_data": {
    "income_increase_percentage": 15.0,
    "time_to_success_days": 45,
    "skills_developed": ["Python", "Machine Learning"]
  },
  "experiment_variant": "treatment"
}
```

#### Response
```json
{
  "success": true,
  "outcome_tracked": true,
  "success_story_id": "story_123",
  "analytics_updated": true
}
```

## Real-Time Risk Monitoring

### 1. Risk System Health

**GET** `/api/risk/monitor/status`

Real-time risk system health monitoring.

#### Response
```json
{
  "success": true,
  "system_health": {
    "health_score": 85.0,
    "performance_metrics": {
      "avg_response_time": 250.0,
      "success_rate": 0.98
    },
    "system_status": "healthy"
  },
  "active_alerts": 2,
  "monitoring_status": "active",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 2. Trigger Risk Alert

**POST** `/api/risk/alert/trigger`

Triggers risk alerts with analytics tracking.

#### Request Body
```json
{
  "alert_type": "high_risk",
  "risk_level": "critical",
  "message": "High risk detected in user profile",
  "alert_data": {
    "risk_factors": ["AI automation", "Industry disruption"],
    "urgency": "immediate"
  }
}
```

#### Response
```json
{
  "success": true,
  "alert_triggered": true,
  "alert_id": "alert_123",
  "analytics_tracked": true
}
```

### 3. Live Risk Trends

**GET** `/api/risk/trends/live`

Live risk trend data for dashboard.

#### Response
```json
{
  "success": true,
  "live_trends": {
    "ai_risk_trend": "increasing",
    "layoff_risk_trend": "stable",
    "industry_risk_trend": "decreasing"
  },
  "user_trends": {
    "personal_risk_trajectory": "improving",
    "risk_reduction_rate": 0.15
  },
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### 4. Active Risk Predictions

**GET** `/api/risk/predictions/active`

Active risk predictions requiring attention.

#### Response
```json
{
  "success": true,
  "active_predictions": [
    {
      "prediction_id": "pred_123",
      "risk_level": "high",
      "predicted_timeline": "3_months",
      "confidence": 0.85,
      "recommended_actions": [
        "Update skills in AI/ML",
        "Build network in target industry"
      ]
    }
  ],
  "prediction_count": 1,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

## Risk A/B Testing Integration

### 1. Active Risk Experiments

**GET** `/api/risk/experiments/active`

Active risk-related A/B tests.

#### Response
```json
{
  "success": true,
  "active_experiments": [
    {
      "test_id": "risk_threshold_001",
      "test_name": "Risk Threshold Optimization",
      "test_type": "risk_threshold_optimization",
      "status": "active",
      "start_date": "2024-01-01",
      "expected_end_date": "2024-02-01"
    }
  ],
  "experiment_count": 1
}
```

### 2. Assign User to Risk Experiment

**POST** `/api/risk/experiments/assign`

Assigns user to risk experiment variant.

#### Request Body
```json
{
  "test_id": "risk_threshold_001",
  "variant": "treatment"
}
```

#### Response
```json
{
  "success": true,
  "assignment_created": true,
  "test_id": "risk_threshold_001",
  "variant": "treatment"
}
```

### 3. Track Experiment Outcome

**POST** `/api/risk/experiments/outcome`

Tracks experiment outcome for risk tests.

#### Request Body
```json
{
  "test_id": "risk_threshold_001",
  "outcome_type": "conversion",
  "outcome_data": {
    "conversion_rate": 0.15,
    "time_to_conversion": 7,
    "user_engagement": 0.85
  }
}
```

#### Response
```json
{
  "success": true,
  "outcome_tracked": true,
  "test_id": "risk_threshold_001"
}
```

## WebSocket Integration

### Connection
```javascript
const socket = io('https://api.mingus.com', {
  auth: {
    token: 'your_jwt_token'
  }
});
```

### Event Handlers

#### Subscribe to Risk Updates
```javascript
socket.emit('subscribe_risk_updates', {
  update_types: ['risk_scores', 'recommendations', 'alerts']
});

socket.on('risk_score_updated', (data) => {
  console.log('Risk score updated:', data);
});

socket.on('recommendation_notification', (data) => {
  console.log('New recommendation:', data);
});

socket.on('performance_alert', (data) => {
  console.log('Performance alert:', data);
});
```

#### Real-Time Dashboard Updates
```javascript
socket.emit('request_risk_dashboard');

socket.on('risk_dashboard_data', (data) => {
  updateDashboard(data.dashboard_data);
});
```

## Performance Optimization

### Response Caching
- Dashboard queries: 5 minutes
- Analytics calculations: 10 minutes
- User-specific data: 2 minutes

### Rate Limiting
- Dashboard queries: 60 requests/minute
- Analytics calculations: 12 requests/minute
- Recommendations: 60 requests/minute
- Monitoring: 120 requests/minute

### Performance Targets
- API response times < 500ms for dashboard queries
- Real-time updates delivered < 1 second
- 99.9% uptime for risk monitoring endpoints

## Error Handling

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: User not authenticated
- `AUTHORIZATION_DENIED`: Insufficient permissions
- `MISSING_FIELDS`: Required fields missing
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_DATA`: Invalid request data
- `SYSTEM_ERROR`: Internal server error

### Error Response Example
```json
{
  "success": false,
  "error": "Authentication required",
  "error_code": "AUTHENTICATION_REQUIRED",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration Examples

### Frontend Integration (React)

```javascript
import { useState, useEffect } from 'react';

const RiskDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch('/api/risk/dashboard/user_123', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-CSRF-Token': csrfToken
          }
        });
        
        const data = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error('Error fetching dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>Risk Dashboard</h2>
      <div>Success Rate: {dashboardData.career_protection_metrics.success_rate}</div>
      {/* Render dashboard components */}
    </div>
  );
};
```

### Backend Integration (Python)

```python
import requests
import asyncio

class RiskAnalyticsClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    async def assess_risk(self, user_data):
        response = requests.post(
            f'{self.base_url}/api/risk/assess-and-track',
            json=user_data,
            headers=self.headers
        )
        return response.json()
    
    async def get_dashboard(self, user_id):
        response = requests.get(
            f'{self.base_url}/api/risk/dashboard/{user_id}',
            headers=self.headers
        )
        return response.json()
    
    async def trigger_recommendations(self, risk_data):
        response = requests.post(
            f'{self.base_url}/api/risk/trigger-recommendations',
            json=risk_data,
            headers=self.headers
        )
        return response.json()

# Usage
client = RiskAnalyticsClient('https://api.mingus.com', 'your_token')
risk_assessment = await client.assess_risk(user_profile)
```

## Testing

### Running Tests
```bash
# Run all tests
pytest tests/test_risk_analytics_api.py -v

# Run specific test categories
pytest tests/test_risk_analytics_api.py::TestRiskAnalyticsAPI -v
pytest tests/test_risk_analytics_api.py::TestPerformanceMonitoring -v

# Run with coverage
pytest tests/test_risk_analytics_api.py --cov=backend.api.unified_risk_analytics_api
```

### Test Categories
1. **Unit Tests**: Individual endpoint functionality
2. **Integration Tests**: End-to-end workflows
3. **Performance Tests**: Response time and throughput
4. **Authentication Tests**: Security and authorization
5. **Error Handling Tests**: Edge cases and error scenarios

### Test Data
Test data is automatically generated and cleaned up after each test run. No external dependencies required.

## Success Metrics

### API Performance
- ✅ API response times < 500ms for dashboard queries
- ✅ Real-time updates delivered < 1 second
- ✅ 99.9% uptime for risk monitoring endpoints

### Analytics Tracking
- ✅ Complete analytics tracking for all risk interactions
- ✅ Real-time performance monitoring
- ✅ Comprehensive success metrics

### Integration
- ✅ Seamless integration with existing 44 RESTful endpoints
- ✅ Backward compatibility maintained
- ✅ Unified authentication and security patterns

## Support

For technical support or questions about the Risk Analytics API:

- **Documentation**: This comprehensive guide
- **API Status**: `/api/risk/health`
- **System Status**: `/health`
- **Support Email**: api-support@mingus.com

---

*Last Updated: January 15, 2024*
*API Version: 1.0.0*
