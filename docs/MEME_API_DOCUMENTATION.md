# Meme Splash Page API Documentation

This document provides comprehensive documentation for the Meme Splash Page API endpoints in the Mingus personal finance application.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [API Endpoints](#api-endpoints)
5. [Error Handling](#error-handling)
6. [Examples](#examples)
7. [Testing](#testing)

## Overview

The Meme Splash Page API provides endpoints for:
- Retrieving personalized memes for users
- Tracking user interactions with memes
- Managing user preferences for meme categories and frequency
- Admin functionality for meme management

### Base URL
```
/api
```

### Content Type
All requests should use `application/json` content type.

## Authentication

All endpoints require authentication via session-based authentication. The user must be logged in and have a valid session.

**Headers Required:**
```
Content-Type: application/json
```

**Session Management:**
- User authentication is handled via Flask session
- User ID is retrieved from `session.get('user_id')`
- Unauthenticated requests return `401 Unauthorized`

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **GET endpoints**: 30-50 requests per minute
- **POST endpoints**: 100 requests per minute
- **PUT endpoints**: 20 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 49
X-RateLimit-Reset: 1640995200
```

When rate limit is exceeded, the API returns `429 Too Many Requests`.

## API Endpoints

### 1. Get User Meme

**Endpoint:** `GET /api/user-meme/{user_id}`

**Description:** Returns a personalized meme for the specified user based on their preferences and viewing history.

**Parameters:**
- `user_id` (path parameter): The ID of the user requesting the meme

**Response:**
```json
{
  "success": true,
  "meme": {
    "id": "uuid-string",
    "image_url": "https://example.com/meme.jpg",
    "caption": "Monday motivation: Building wealth one paycheck at a time 💼💪",
    "category": "monday_career",
    "alt_text": "A person in business attire flexing muscles with money symbols",
    "tags": ["career", "motivation", "wealth", "monday", "business"]
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

**No Meme Available:**
```json
{
  "message": "No meme available at this time",
  "meme": null,
  "next_available": null
}
```

**Error Responses:**
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User trying to access another user's meme
- `404 Not Found`: User not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 2. Track Meme Analytics

**Endpoint:** `POST /api/meme-analytics`

**Description:** Records user interactions with memes for analytics and personalization.

**Request Body:**
```json
{
  "meme_id": "uuid-string",
  "interaction_type": "viewed",
  "time_spent_seconds": 15,
  "source_page": "meme_splash"
}
```

**Required Fields:**
- `meme_id`: The ID of the meme being interacted with
- `interaction_type`: Type of interaction (viewed, skipped, continued, liked, shared, reported)

**Optional Fields:**
- `time_spent_seconds`: Time spent viewing the meme
- `source_page`: Page where the meme was displayed

**Response:**
```json
{
  "success": true,
  "message": "Viewed interaction recorded",
  "interaction_id": "uuid-string",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid interaction type or missing required fields
- `401 Unauthorized`: User not authenticated
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 3. Get User Meme Preferences

**Endpoint:** `GET /api/user-meme-preferences/{user_id}`

**Description:** Returns user's meme preferences and interaction analytics.

**Parameters:**
- `user_id` (path parameter): The ID of the user

**Response:**
```json
{
  "success": true,
  "preferences": {
    "memes_enabled": true,
    "preferred_categories": ["monday_career", "tuesday_health"],
    "frequency_setting": "daily",
    "custom_frequency_days": 1,
    "last_meme_shown_at": "2025-01-27T09:00:00Z",
    "opt_out_reason": null,
    "opt_out_date": null
  },
  "analytics": {
    "total_interactions": 25,
    "interactions_by_type": {
      "view": 20,
      "like": 3,
      "skip": 2
    },
    "favorite_categories": ["monday_career", "friday_entertainment"],
    "skip_rate": 8.0,
    "engagement_rate": 15.0,
    "last_updated": "2025-01-27T10:30:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User trying to access another user's preferences
- `404 Not Found`: User not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 4. Update User Meme Preferences

**Endpoint:** `PUT /api/user-meme-preferences/{user_id}`

**Description:** Updates user's meme preferences and settings.

**Parameters:**
- `user_id` (path parameter): The ID of the user

**Request Body:**
```json
{
  "memes_enabled": true,
  "preferred_categories": ["monday_career", "tuesday_health", "friday_entertainment"],
  "frequency_setting": "daily",
  "custom_frequency_days": 1,
  "opt_out_reason": "Not interested in memes"
}
```

**All fields are optional.** Valid values:

**memes_enabled:** boolean
- `true`: Enable memes
- `false`: Disable memes

**preferred_categories:** array of strings
- `monday_career`: Career and business content
- `tuesday_health`: Health and wellness content
- `wednesday_home`: Home and transportation content
- `thursday_relationships`: Relationships and family content
- `friday_entertainment`: Entertainment and fun content
- `saturday_kids`: Kids and education content
- `sunday_faith`: Faith and reflection content

**frequency_setting:** string
- `daily`: Show memes daily
- `weekly`: Show memes weekly
- `disabled`: Disable memes
- `custom`: Use custom frequency

**custom_frequency_days:** integer (1-30)
- Only used when frequency_setting is "custom"

**Response:**
```json
{
  "success": true,
  "message": "Preferences updated successfully",
  "preferences": {
    "memes_enabled": true,
    "preferred_categories": ["monday_career", "tuesday_health", "friday_entertainment"],
    "frequency_setting": "daily",
    "custom_frequency_days": 1,
    "last_meme_shown_at": "2025-01-27T09:00:00Z",
    "opt_out_reason": null,
    "opt_out_date": null
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid field values
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User trying to update another user's preferences
- `404 Not Found`: User not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 5. Health Check

**Endpoint:** `GET /api/meme-health`

**Description:** Health check endpoint for the meme service.

**Response:**
```json
{
  "status": "healthy",
  "service": "meme-api",
  "database": "connected",
  "total_memes": 42,
  "timestamp": "2025-01-27T10:30:00Z"
}
```

**Error Response:**
```json
{
  "status": "unhealthy",
  "service": "meme-api",
  "error": "Database connection failed",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

### 6. Admin Endpoints

#### Get All Memes (Admin)

**Endpoint:** `GET /api/admin/memes`

**Description:** Admin endpoint to retrieve all memes for management purposes.

**Query Parameters:**
- `category` (optional): Filter by meme category
- `limit` (optional): Number of memes to return (max 100, default 50)
- `offset` (optional): Number of memes to skip (default 0)

**Response:**
```json
{
  "success": true,
  "memes": [
    {
      "id": "uuid-string",
      "image_url": "https://example.com/meme.jpg",
      "category": "monday_career",
      "caption_text": "Monday motivation...",
      "is_active": true,
      "view_count": 150,
      "like_count": 25,
      "engagement_score": 0.17
    }
  ],
  "total_count": 50,
  "limit": 50,
  "offset": 0,
  "timestamp": "2025-01-27T10:30:00Z"
}
```

#### Get Meme Analytics (Admin)

**Endpoint:** `GET /api/admin/meme-analytics`

**Description:** Admin endpoint to retrieve overall meme analytics.

**Response:**
```json
{
  "success": true,
  "analytics": {
    "memes_by_category": {
      "monday_career": 15,
      "tuesday_health": 12,
      "wednesday_home": 8
    },
    "top_memes": [
      {
        "id": "uuid-string",
        "engagement_score": 0.25,
        "view_count": 200
      }
    ],
    "today_interactions": 150
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

## Error Handling

### Standard Error Response Format

All error responses follow this format:
```json
{
  "error": "Error message description",
  "message": "Additional error details (optional)",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Common Error Messages

| Error | Description | Solution |
|-------|-------------|----------|
| `Authentication required` | User not logged in | Log in to the application |
| `Unauthorized access` | User trying to access another user's data | Use your own user ID |
| `User not found` | Specified user doesn't exist | Check user ID |
| `Invalid interaction type` | Invalid interaction_type value | Use one of: viewed, skipped, continued, liked, shared, reported |
| `Rate limit exceeded` | Too many requests | Wait before making more requests |
| `Missing required field` | Required field not provided | Include all required fields |

## Examples

### Frontend Integration Example

```javascript
// Get user's meme
async function getUserMeme(userId) {
  try {
    const response = await fetch(`/api/user-meme/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include' // Include session cookies
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.meme;
  } catch (error) {
    console.error('Error fetching meme:', error);
    return null;
  }
}

// Track meme interaction
async function trackMemeInteraction(memeId, interactionType, timeSpent = 0) {
  try {
    const response = await fetch('/api/meme-analytics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        meme_id: memeId,
        interaction_type: interactionType,
        time_spent_seconds: timeSpent,
        source_page: 'meme_splash'
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Analytics recorded:', data.message);
  } catch (error) {
    console.error('Error tracking analytics:', error);
  }
}

// Update user preferences
async function updatePreferences(userId, preferences) {
  try {
    const response = await fetch(`/api/user-meme-preferences/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(preferences)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Preferences updated:', data.message);
  } catch (error) {
    console.error('Error updating preferences:', error);
  }
}

// Usage example
const userId = 123;
const meme = await getUserMeme(userId);

if (meme) {
  // Display meme
  displayMeme(meme);
  
  // Track view
  trackMemeInteraction(meme.id, 'viewed');
  
  // When user interacts
  document.getElementById('like-button').onclick = () => {
    trackMemeInteraction(meme.id, 'liked');
  };
  
  document.getElementById('skip-button').onclick = () => {
    trackMemeInteraction(meme.id, 'skipped');
  };
}
```

### cURL Examples

```bash
# Get user meme
curl -X GET "http://localhost:5000/api/user-meme/123" \
  -H "Content-Type: application/json" \
  -b "session=your-session-cookie"

# Track interaction
curl -X POST "http://localhost:5000/api/meme-analytics" \
  -H "Content-Type: application/json" \
  -b "session=your-session-cookie" \
  -d '{
    "meme_id": "uuid-string",
    "interaction_type": "liked",
    "time_spent_seconds": 30
  }'

# Get preferences
curl -X GET "http://localhost:5000/api/user-meme-preferences/123" \
  -H "Content-Type: application/json" \
  -b "session=your-session-cookie"

# Update preferences
curl -X PUT "http://localhost:5000/api/user-meme-preferences/123" \
  -H "Content-Type: application/json" \
  -b "session=your-session-cookie" \
  -d '{
    "memes_enabled": true,
    "preferred_categories": ["monday_career", "friday_entertainment"],
    "frequency_setting": "daily"
  }'
```

## Testing

### Health Check
```bash
curl -X GET "http://localhost:5000/api/meme-health"
```

### Test User Flow
1. **Get meme**: `GET /api/user-meme/{user_id}`
2. **Track view**: `POST /api/meme-analytics` with `interaction_type: "viewed"`
3. **Track like**: `POST /api/meme-analytics` with `interaction_type: "liked"`
4. **Get preferences**: `GET /api/user-meme-preferences/{user_id}`
5. **Update preferences**: `PUT /api/user-meme-preferences/{user_id}`

### Error Testing
- Test with invalid user ID
- Test with missing authentication
- Test rate limiting by making many requests
- Test with invalid interaction types
- Test with invalid preference values

## Security Considerations

1. **Authentication**: All endpoints require valid session authentication
2. **Authorization**: Users can only access their own data
3. **Rate Limiting**: Prevents abuse and ensures fair usage
4. **Input Validation**: All inputs are validated and sanitized
5. **CORS**: Cross-origin requests are properly handled
6. **Logging**: All interactions are logged for security monitoring

## Performance Considerations

1. **Caching**: Meme selection results are cached for 5 minutes
2. **Database Indexing**: Proper indexes on frequently queried fields
3. **Rate Limiting**: Prevents excessive database queries
4. **Connection Pooling**: Efficient database connection management
5. **Error Handling**: Graceful degradation on errors

## Monitoring

The API includes comprehensive logging for:
- User interactions
- Error conditions
- Performance metrics
- Security events

Logs are structured and include:
- User ID
- Timestamp
- Action performed
- Error details (if applicable)
- Performance metrics

## Support

For issues or questions about the Meme API:
1. Check the health endpoint: `GET /api/meme-health`
2. Review error messages in the response
3. Check application logs for detailed error information
4. Contact the development team with specific error details
