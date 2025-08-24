# Meme API Setup Guide

This guide explains how to integrate the Meme Splash Page API routes into your Flask application.

## Prerequisites

1. Flask application with SQLAlchemy database setup
2. User authentication system (session-based)
3. CORS support (flask-cors)
4. Database models for memes (already created)

## Installation Steps

### 1. Register the Blueprint

Add the meme routes blueprint to your main Flask application:

```python
# In your main app.py or app factory
from backend.routes.meme_routes import meme_bp

# Register the blueprint
app.register_blueprint(meme_bp)
```

### 2. Complete Example

Here's a complete example of how to set up the meme API in your Flask application:

```python
# app.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from backend.routes.meme_routes import meme_bp

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, supports_credentials=True)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'
    
    # Initialize database
    db = SQLAlchemy(app)
    app.db = db
    
    # Register blueprints
    app.register_blueprint(meme_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

### 3. Database Setup

Make sure you have the required database tables. The meme tables should already be created via migrations:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('memes', 'user_meme_history', 'user_meme_preferences');
```

### 4. Seed Sample Data (Optional)

To populate the database with sample memes, you can run:

```python
from backend.services.meme_service import MemeService
from backend.database import get_db_session

# Seed sample memes
db_session = get_db_session()
meme_service = MemeService(db_session)
meme_service.seed_sample_memes()
```

## Configuration

### Environment Variables

Set these environment variables in your `.env` file:

```bash
# Database
DATABASE_URL=your_database_connection_string

# Flask
SECRET_KEY=your_secret_key
FLASK_ENV=development

# CORS (if needed)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Rate Limiting Configuration

The API includes built-in rate limiting. You can adjust the limits in the route decorators:

```python
# In meme_routes.py, adjust these values:
@rate_limit(max_requests=50, window_seconds=60)  # 50 requests per minute
```

## Testing the Setup

### 1. Health Check

Test that the API is working:

```bash
curl -X GET "http://localhost:5000/api/meme-health"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "meme-api",
  "database": "connected",
  "total_memes": 42,
  "timestamp": "2025-01-27T10:30:00Z"
}
```

### 2. Run the Test Suite

Use the provided test script:

```bash
python tests/test_meme_api.py
```

### 3. Manual Testing

Test the endpoints manually:

```bash
# Get user meme (requires authentication)
curl -X GET "http://localhost:5000/api/user-meme/123" \
  -H "Content-Type: application/json" \
  -b "session=your-session-cookie"

# Track analytics
curl -X POST "http://localhost:5000/api/meme-analytics" \
  -H "Content-Type: application/json" \
  -b "session=your-session-cookie" \
  -d '{
    "meme_id": "test-meme-id",
    "interaction_type": "viewed"
  }'
```

## Frontend Integration

### React Example

```jsx
import React, { useState, useEffect } from 'react';

function MemeSplashPage({ userId }) {
  const [meme, setMeme] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMeme();
  }, [userId]);

  const fetchMeme = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/user-meme/${userId}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMeme(data.meme);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const trackInteraction = async (interactionType) => {
    if (!meme) return;
    
    try {
      await fetch('/api/meme-analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          meme_id: meme.id,
          interaction_type: interactionType,
          source_page: 'meme_splash'
        })
      });
    } catch (error) {
      console.error('Error tracking interaction:', error);
    }
  };

  if (loading) return <div>Loading meme...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!meme) return <div>No meme available</div>;

  return (
    <div className="meme-splash">
      <img src={meme.image_url} alt={meme.alt_text} />
      <p>{meme.caption}</p>
      <div className="meme-actions">
        <button onClick={() => trackInteraction('liked')}>Like</button>
        <button onClick={() => trackInteraction('skipped')}>Skip</button>
        <button onClick={() => trackInteraction('shared')}>Share</button>
      </div>
    </div>
  );
}

export default MemeSplashPage;
```

### JavaScript Example

```javascript
class MemeAPI {
  constructor(baseURL = '/api') {
    this.baseURL = baseURL;
  }

  async getUserMeme(userId) {
    const response = await fetch(`${this.baseURL}/user-meme/${userId}`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async trackAnalytics(memeId, interactionType, timeSpent = 0) {
    const response = await fetch(`${this.baseURL}/meme-analytics`, {
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
    
    return response.json();
  }

  async getPreferences(userId) {
    const response = await fetch(`${this.baseURL}/user-meme-preferences/${userId}`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async updatePreferences(userId, preferences) {
    const response = await fetch(`${this.baseURL}/user-meme-preferences/${userId}`, {
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
    
    return response.json();
  }
}

// Usage
const memeAPI = new MemeAPI();

// Get user's meme
memeAPI.getUserMeme(123)
  .then(data => {
    if (data.meme) {
      displayMeme(data.meme);
    }
  })
  .catch(error => {
    console.error('Error fetching meme:', error);
  });
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized Errors**
   - Ensure user is logged in and session is valid
   - Check that session cookies are being sent with requests
   - Verify authentication middleware is working

2. **404 Not Found Errors**
   - Check that the blueprint is properly registered
   - Verify the URL paths are correct
   - Ensure the Flask app is running

3. **Database Connection Errors**
   - Verify database connection string
   - Check that database tables exist
   - Ensure database user has proper permissions

4. **CORS Errors**
   - Configure CORS properly for your frontend domain
   - Ensure credentials are included in requests
   - Check that the frontend is making requests to the correct URL

### Debug Mode

Enable debug mode to see detailed error messages:

```python
app.run(debug=True)
```

### Logging

The API includes comprehensive logging. Check your application logs for:

- User interactions
- Error conditions
- Performance metrics
- Security events

## Security Considerations

1. **Authentication**: All endpoints require valid session authentication
2. **Authorization**: Users can only access their own data
3. **Rate Limiting**: Prevents abuse and ensures fair usage
4. **Input Validation**: All inputs are validated and sanitized
5. **CORS**: Cross-origin requests are properly handled
6. **Logging**: All interactions are logged for security monitoring

## Performance Optimization

1. **Caching**: Meme selection results are cached for 5 minutes
2. **Database Indexing**: Proper indexes on frequently queried fields
3. **Rate Limiting**: Prevents excessive database queries
4. **Connection Pooling**: Efficient database connection management
5. **Error Handling**: Graceful degradation on errors

## Monitoring

Monitor the API using:

1. **Health Check Endpoint**: `/api/meme-health`
2. **Application Logs**: Check for errors and performance issues
3. **Database Metrics**: Monitor query performance
4. **Rate Limiting**: Track rate limit violations

## Support

For issues or questions:

1. Check the health endpoint: `GET /api/meme-health`
2. Review error messages in the response
3. Check application logs for detailed error information
4. Run the test suite: `python tests/test_meme_api.py`
5. Contact the development team with specific error details
