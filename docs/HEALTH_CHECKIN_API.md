# Health Check-in API Documentation

## Overview

The Health Check-in API provides endpoints for users to track their weekly wellness metrics and correlate them with their financial health. The system enforces a weekly check-in schedule (one check-in per week per user) and provides comprehensive analytics and history tracking.

## Base URL

```
/api/health
```

## Authentication

Most endpoints require user authentication via session. The `@require_auth` decorator is used to protect routes. Unauthenticated requests will receive a `401 Unauthorized` response.

## Endpoints

### 1. Demo Form (No Authentication Required)

**GET** `/api/health/demo`

Renders the health check-in form for testing purposes without requiring authentication.

**Response:**
- **200 OK**: HTML form page
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl http://localhost:5002/api/health/demo
```

### 2. Health Check-in Form

**GET** `/api/health/checkin`

Renders the health check-in form for authenticated users.

**Headers:**
- Requires valid session cookie

**Response:**
- **200 OK**: HTML form page with last check-in date
- **401 Unauthorized**: User not authenticated
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -b session_cookie.txt http://localhost:5002/api/health/checkin
```

### 3. Submit Health Check-in

**POST** `/api/health/checkin`

Submits a weekly health check-in. Users can only submit one check-in per week.

**Headers:**
- `Content-Type: application/json`
- Requires valid session cookie

**Request Body:**
```json
{
  "physical_activity_minutes": 30,
  "physical_activity_level": "moderate",
  "relationships_rating": 8,
  "relationships_notes": "Had a great conversation with family",
  "mindfulness_minutes": 15,
  "mindfulness_type": "meditation",
  "stress_level": 4,
  "energy_level": 7,
  "mood_rating": 8
}
```

**Field Validation:**
- `relationships_rating` (required): 1-10
- `stress_level` (required): 1-10
- `energy_level` (required): 1-10
- `mood_rating` (required): 1-10
- `physical_activity_minutes` (optional): 0-480
- `mindfulness_minutes` (optional): 0-120
- `physical_activity_level` (optional): "low", "moderate", "high"
- `mindfulness_type` (optional): "meditation", "prayer", "journaling", "other"
- `relationships_notes` (optional): string

**Response:**
- **201 Created**: Check-in submitted successfully
```json
{
  "message": "Weekly health check-in submitted successfully",
  "checkin_id": 123,
  "checkin_date": "2025-06-20",
  "week_start": "2025-06-16"
}
```
- **400 Bad Request**: Invalid data
- **401 Unauthorized**: User not authenticated
- **409 Conflict**: Already submitted check-in for this week
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -b session_cookie.txt \
  -d '{"relationships_rating": 8, "stress_level": 4, "energy_level": 7, "mood_rating": 8}' \
  http://localhost:5002/api/health/checkin
```

### 4. Get Latest Check-in

**GET** `/api/health/checkin/latest`

Retrieves the user's most recent health check-in data.

**Headers:**
- Requires valid session cookie

**Response:**
- **200 OK**: Latest check-in data
```json
{
  "checkin": {
    "id": 123,
    "checkin_date": "2025-06-20",
    "physical_activity_minutes": 30,
    "physical_activity_level": "moderate",
    "relationships_rating": 8,
    "relationships_notes": "Had a great conversation with family",
    "mindfulness_minutes": 15,
    "mindfulness_type": "meditation",
    "stress_level": 4,
    "energy_level": 7,
    "mood_rating": 8,
    "created_at": "2025-06-20T10:30:00"
  }
}
```
- **200 OK**: No check-ins found
```json
{
  "message": "No check-ins found",
  "checkin": null
}
```
- **401 Unauthorized**: User not authenticated
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -b session_cookie.txt http://localhost:5002/api/health/checkin/latest
```

### 5. Get Check-in History

**GET** `/api/health/checkin/history`

Retrieves the user's check-in history for the specified number of weeks.

**Headers:**
- Requires valid session cookie

**Query Parameters:**
- `weeks` (optional): Number of weeks to retrieve (1-52, default: 12)

**Response:**
- **200 OK**: Check-in history
```json
{
  "checkins": [
    {
      "id": 123,
      "checkin_date": "2025-06-20",
      "physical_activity_minutes": 30,
      "physical_activity_level": "moderate",
      "relationships_rating": 8,
      "relationships_notes": "Had a great conversation with family",
      "mindfulness_minutes": 15,
      "mindfulness_type": "meditation",
      "stress_level": 4,
      "energy_level": 7,
      "mood_rating": 8,
      "created_at": "2025-06-20T10:30:00"
    }
  ],
  "total": 1,
  "period": {
    "start_date": "2025-03-28",
    "end_date": "2025-06-20",
    "weeks": 12
  }
}
```
- **400 Bad Request**: Invalid weeks parameter
- **401 Unauthorized**: User not authenticated
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -b session_cookie.txt "http://localhost:5002/api/health/checkin/history?weeks=8"
```

### 6. Check Weekly Status

**GET** `/api/health/status`

Checks if the user has completed this week's check-in and provides streak information.

**Headers:**
- Requires valid session cookie

**Response:**
- **200 OK**: Weekly status
```json
{
  "current_week": {
    "start_date": "2025-06-16",
    "end_date": "2025-06-22",
    "completed": true,
    "checkin_date": "2025-06-20"
  },
  "last_checkin": {
    "date": "2025-06-20",
    "days_ago": 0
  },
  "streak_weeks": 3
}
```
- **401 Unauthorized**: User not authenticated
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -b session_cookie.txt http://localhost:5002/api/health/status
```

### 7. Get Paginated Check-ins

**GET** `/api/health/checkins`

Retrieves paginated health check-ins for the user.

**Headers:**
- Requires valid session cookie

**Query Parameters:**
- `limit` (optional): Number of records per page (1-100, default: 10)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
- **200 OK**: Paginated check-ins
```json
{
  "checkins": [
    {
      "id": 123,
      "checkin_date": "2025-06-20",
      "physical_activity_minutes": 30,
      "physical_activity_level": "moderate",
      "relationships_rating": 8,
      "relationships_notes": "Had a great conversation with family",
      "mindfulness_minutes": 15,
      "mindfulness_type": "meditation",
      "stress_level": 4,
      "energy_level": 7,
      "mood_rating": 8,
      "created_at": "2025-06-20T10:30:00"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```
- **400 Bad Request**: Invalid pagination parameters
- **401 Unauthorized**: User not authenticated
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -b session_cookie.txt "http://localhost:5002/api/health/checkins?limit=5&offset=0"
```

### 8. Get Health Statistics

**GET** `/api/health/stats`

Retrieves aggregated health statistics for the user over a specified period.

**Headers:**
- Requires valid session cookie

**Query Parameters:**
- `days` (optional): Number of days to analyze (1-365, default: 30)

**Response:**
- **200 OK**: Health statistics
```json
{
  "stats": {
    "period": {
      "start_date": "2025-05-21",
      "end_date": "2025-06-20",
      "days": 30
    },
    "total_checkins": 4,
    "averages": {
      "relationships_rating": 7.5,
      "stress_level": 4.2,
      "energy_level": 6.8,
      "mood_rating": 7.2,
      "physical_activity_minutes": 25.0,
      "mindfulness_minutes": 12.5
    },
    "totals": {
      "physical_activity_minutes": 100,
      "mindfulness_minutes": 50
    },
    "distributions": {
      "activity_levels": {
        "moderate": 3,
        "low": 1
      },
      "mindfulness_types": {
        "meditation": 2,
        "prayer": 1,
        "journaling": 1
      }
    }
  }
}
```
- **200 OK**: No check-ins found
```json
{
  "message": "No check-ins found for the specified period",
  "stats": {}
}
```
- **400 Bad Request**: Invalid days parameter
- **401 Unauthorized**: User not authenticated
- **500 Internal Server Error**: Server error

**Usage:**
```bash
curl -b session_cookie.txt "http://localhost:5002/api/health/stats?days=60"
```

## Weekly Check-in Logic

The system enforces a weekly check-in schedule:

- **Week Definition**: Monday (day 0) to Sunday (day 6)
- **One Check-in Per Week**: Users can only submit one check-in per calendar week
- **Streak Tracking**: Consecutive weeks with check-ins are tracked
- **Flexible Timing**: Check-ins can be submitted any day of the week

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- **200**: Success
- **201**: Created (check-in submitted)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **409**: Conflict (duplicate check-in)
- **500**: Internal Server Error

## Data Validation

### Required Fields
- `relationships_rating`: Integer 1-10
- `stress_level`: Integer 1-10
- `energy_level`: Integer 1-10
- `mood_rating`: Integer 1-10

### Optional Fields
- `physical_activity_minutes`: Integer 0-480
- `mindfulness_minutes`: Integer 0-120
- `physical_activity_level`: "low", "moderate", "high"
- `mindfulness_type`: "meditation", "prayer", "journaling", "other"
- `relationships_notes`: String

## Database Schema

The health check-in data is stored in the `user_health_checkins` table:

```sql
CREATE TABLE user_health_checkins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    checkin_date DATE NOT NULL,
    physical_activity_minutes INTEGER,
    physical_activity_level VARCHAR(20),
    relationships_rating INTEGER NOT NULL,
    relationships_notes TEXT,
    mindfulness_minutes INTEGER,
    mindfulness_type VARCHAR(20),
    stress_level INTEGER NOT NULL,
    energy_level INTEGER NOT NULL,
    mood_rating INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Integration Examples

### Frontend Integration

```javascript
// Submit a health check-in
async function submitHealthCheckin(data) {
    const response = await fetch('/api/health/checkin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        const result = await response.json();
        console.log('Check-in submitted:', result);
    } else {
        const error = await response.json();
        console.error('Error:', error);
    }
}

// Get weekly status
async function getWeeklyStatus() {
    const response = await fetch('/api/health/status');
    if (response.ok) {
        const status = await response.json();
        console.log('Weekly status:', status);
    }
}
```

### Python Integration

```python
import requests

# Submit check-in
def submit_checkin(session, data):
    response = session.post(
        'http://localhost:5002/api/health/checkin',
        json=data
    )
    return response.json()

# Get statistics
def get_stats(session, days=30):
    response = session.get(
        f'http://localhost:5002/api/health/stats?days={days}'
    )
    return response.json()
```

## Testing

Use the demo endpoint for testing without authentication:

```bash
curl http://localhost:5002/api/health/demo
```

Run the test suite:

```bash
python test_health_routes.py
python test_health_checkin.py
```

## Security Considerations

1. **Authentication Required**: All endpoints except `/demo` require valid session authentication
2. **Input Validation**: All user inputs are validated for type, range, and format
3. **SQL Injection Protection**: Uses SQLAlchemy ORM with parameterized queries
4. **Rate Limiting**: Consider implementing rate limiting for production use
5. **Data Privacy**: Health data is user-specific and isolated by user_id

## Future Enhancements

1. **Health-Financial Correlation**: Analyze relationships between health metrics and financial behavior
2. **Trend Analysis**: Provide insights on health trends over time
3. **Goal Setting**: Allow users to set health goals and track progress
4. **Notifications**: Remind users of weekly check-ins
5. **Export Data**: Allow users to export their health data
6. **Integration**: Connect with fitness trackers and health apps
