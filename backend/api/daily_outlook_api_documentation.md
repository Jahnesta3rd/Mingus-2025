# Daily Outlook API Documentation

## Overview

The Daily Outlook API provides REST endpoints for managing daily outlook features in the Mingus application. This API handles user daily insights, progress tracking, streak management, and relationship status updates.

## Base URL
```
/api/daily-outlook
```

## Authentication

All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Get Today's Outlook
**GET** `/api/daily-outlook/`

Returns today's daily outlook for the authenticated user, updates view timestamp, and increments streak if consecutive day.

#### Response
```json
{
  "success": true,
  "outlook": {
    "id": 123,
    "user_id": 456,
    "date": "2024-01-15",
    "balance_score": 85,
    "financial_weight": 0.30,
    "wellness_weight": 0.25,
    "relationship_weight": 0.25,
    "career_weight": 0.20,
    "primary_insight": "Your financial progress is on track...",
    "quick_actions": [
      {
        "id": "action_1",
        "title": "Review budget",
        "description": "Check your monthly spending"
      }
    ],
    "encouragement_message": "Great job maintaining your streak!",
    "surprise_element": "Did you know...",
    "streak_count": 7,
    "viewed_at": "2024-01-15T10:30:00Z",
    "actions_completed": {
      "action_1": {
        "completed": true,
        "completed_at": "2024-01-15T11:00:00Z",
        "notes": "Completed successfully"
      }
    },
    "user_rating": 4,
    "created_at": "2024-01-15T06:00:00Z"
  },
  "streak_info": {
    "current_streak": 7,
    "viewed_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Responses
- `404` - No outlook available for today
- `403` - Feature not available in current tier
- `500` - Internal server error

---

### 2. Get Outlook History
**GET** `/api/daily-outlook/history`

Retrieves historical daily outlooks with optional date filtering and pagination.

#### Query Parameters
- `start_date` (optional): Start date filter (YYYY-MM-DD)
- `end_date` (optional): End date filter (YYYY-MM-DD)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)

#### Example Request
```
GET /api/daily-outlook/history?start_date=2024-01-01&end_date=2024-01-31&page=1&per_page=10
```

#### Response
```json
{
  "success": true,
  "outlooks": [
    {
      "id": 123,
      "user_id": 456,
      "date": "2024-01-15",
      "balance_score": 85,
      "user_rating": 4,
      "streak_count": 7,
      "viewed_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T06:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_count": 25,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "engagement_metrics": {
    "total_outlooks": 25,
    "average_rating": 4.2,
    "completion_rate": 78.5,
    "streak_high_score": 12
  }
}
```

#### Error Responses
- `400` - Invalid date format or pagination parameters
- `403` - Feature not available in current tier
- `500` - Internal server error

---

### 3. Mark Action as Completed
**POST** `/api/daily-outlook/action-completed`

Marks a specific action as completed or not completed for today's outlook.

#### Request Body
```json
{
  "action_id": "action_1",
  "completion_status": true,
  "completion_notes": "Completed successfully with great results"
}
```

#### Response
```json
{
  "success": true,
  "message": "Action completion status updated",
  "action_id": "action_1",
  "completion_status": true
}
```

#### Error Responses
- `400` - Invalid request data or validation failed
- `403` - Feature not available in current tier
- `404` - No outlook available for today
- `500` - Internal server error

---

### 4. Submit User Rating
**POST** `/api/daily-outlook/rating`

Submits user rating and feedback for today's outlook.

#### Request Body
```json
{
  "rating": 4,
  "feedback": "The insights were very helpful today!"
}
```

#### Response
```json
{
  "success": true,
  "message": "Rating submitted successfully",
  "rating": 4,
  "ab_test_flags": {
    "high_rating_user": true
  }
}
```

#### Error Responses
- `400` - Invalid request data or validation failed
- `403` - Feature not available in current tier
- `404` - No outlook available for today
- `500` - Internal server error

---

### 5. Get Streak Information
**GET** `/api/daily-outlook/streak`

Retrieves current streak information, milestones, and recovery options.

#### Response
```json
{
  "success": true,
  "streak_info": {
    "current_streak": 7,
    "highest_streak": 15,
    "next_milestone": {
      "days": 14,
      "name": "Two Week Champion",
      "reward": "Priority support access"
    },
    "achieved_milestones": [
      {
        "days": 3,
        "name": "Getting Started",
        "reward": "Unlock personalized insights"
      },
      {
        "days": 7,
        "name": "Week Warrior",
        "reward": "Advanced progress tracking"
      }
    ],
    "recovery_options": []
  }
}
```

#### Error Responses
- `403` - Feature not available in current tier
- `500` - Internal server error

---

### 6. Update Relationship Status
**POST** `/api/relationship-status`

Updates user's relationship status and satisfaction scores.

#### Request Body
```json
{
  "status": "dating",
  "satisfaction_score": 8,
  "financial_impact_score": 6
}
```

#### Valid Status Values
- `single_career_focused`
- `single_looking`
- `dating`
- `early_relationship`
- `committed`
- `engaged`
- `married`
- `complicated`

#### Response
```json
{
  "success": true,
  "message": "Relationship status updated successfully",
  "relationship_status": {
    "id": 789,
    "user_id": 456,
    "status": "dating",
    "satisfaction_score": 8,
    "financial_impact_score": 6,
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Responses
- `400` - Invalid request data or validation failed
- `403` - Feature not available in current tier
- `500` - Internal server error

---

## Rate Limiting

Content generation endpoints are rate-limited to prevent abuse:
- **Daily Outlook Generation**: 1 request per day per user
- **History Queries**: 100 requests per hour per user
- **Action Updates**: 50 requests per hour per user
- **Rating Submissions**: 10 requests per hour per user

## Tier-Based Access Control

### Budget Tier
- ✅ Basic daily outlook access
- ✅ History viewing (limited to 30 days)
- ✅ Basic streak tracking
- ❌ Advanced analytics
- ❌ Export functionality

### Mid-Tier
- ✅ All Budget tier features
- ✅ Extended history (1 year)
- ✅ Advanced engagement metrics
- ✅ Priority support
- ❌ Export functionality

### Professional Tier
- ✅ All Mid-Tier features
- ✅ Unlimited history access
- ✅ Export functionality
- ✅ Advanced analytics
- ✅ A/B testing participation

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": ["Additional error details if applicable"]
}
```

Common error types:
- `Authentication required` (401)
- `Feature not available` (403)
- `Validation failed` (400)
- `Not found` (404)
- `Internal server error` (500)

## CSRF Protection

State-changing operations (POST, PUT, DELETE) require CSRF tokens:
```
X-CSRF-Token: <csrf_token>
```

## Swagger/OpenAPI Documentation

The API endpoints are documented with OpenAPI 3.0 specifications and can be accessed at:
```
/api/docs
```

## Example Usage

### JavaScript/Fetch
```javascript
// Get today's outlook
const response = await fetch('/api/daily-outlook/', {
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});

// Submit rating
const ratingResponse = await fetch('/api/daily-outlook/rating', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken
  },
  body: JSON.stringify({
    rating: 5,
    feedback: 'Excellent insights today!'
  })
});
```

### Python/Requests
```python
import requests

# Get today's outlook
response = requests.get(
    '/api/daily-outlook/',
    headers={'Authorization': f'Bearer {token}'}
)

# Mark action completed
response = requests.post(
    '/api/daily-outlook/action-completed',
    headers={
        'Authorization': f'Bearer {token}',
        'X-CSRF-Token': csrf_token
    },
    json={
        'action_id': 'action_1',
        'completion_status': True,
        'completion_notes': 'Done!'
    }
)
```
