# Analytics Collection Service Usage Guide

## Overview

The `AnalyticsCollectionService` provides comprehensive real-time data collection capabilities for the Mingus article library analytics system. This service handles tracking user engagement, article performance, search behavior, and cultural relevance metrics.

## Service Initialization

```python
from backend.services.analytics_collection_service import AnalyticsCollectionService
from backend.database import get_db_session

# Initialize the service
db_session = get_db_session()
analytics_service = AnalyticsCollectionService(db_session)
```

## Core Tracking Methods

### 1. Article View Tracking

Track when users view articles and update performance metrics.

```python
# Basic article view tracking
success = analytics_service.track_article_view(
    user_id=123,
    article_id="article-uuid-here",
    reading_time_seconds=120,  # Optional: time spent reading
    device_type="desktop",     # Optional: mobile, desktop, tablet
    user_agent="Mozilla/5.0..."  # Optional: browser user agent
)

if success:
    print("Article view tracked successfully")
else:
    print("Failed to track article view")
```

**What it tracks:**
- Increments article view count
- Updates unique viewer count (if first time viewing)
- Calculates average reading time
- Updates user session engagement metrics
- Records device and browser information

### 2. Article Completion Tracking

Track when users complete reading articles.

```python
# Track article completion
success = analytics_service.track_article_completion(
    user_id=123,
    article_id="article-uuid-here",
    total_reading_time=300  # Total time spent reading in seconds
)

if success:
    print("Article completion tracked successfully")
else:
    print("Failed to track article completion")
```

**What it tracks:**
- Increments completion count for user and article
- Calculates completion rate percentage
- Updates average reading time
- Updates cultural engagement score if applicable

### 3. Article Interaction Tracking

Track user interactions like bookmarks and shares.

```python
# Track article bookmark
success = analytics_service.track_article_bookmark(
    user_id=123,
    article_id="article-uuid-here"
)

# Track article share
success = analytics_service.track_article_share(
    user_id=123,
    article_id="article-uuid-here",
    share_platform="twitter"  # Optional: platform where shared
)
```

**What it tracks:**
- Increments bookmark/share counts
- Calculates bookmark/share rates
- Updates user engagement metrics

### 4. Search Query Tracking

Track user search behavior and effectiveness.

```python
# Track search query
success = analytics_service.track_search_query(
    user_id=123,
    query="African American career advancement",
    results_count=15,
    clicked_article_id="article-uuid-here",  # Optional: if user clicked a result
    selected_phase="DO",  # Optional: BE/DO/HAVE filter used
    cultural_relevance_filter=7  # Optional: minimum cultural relevance filter
)

if success:
    print("Search query tracked successfully")
else:
    print("Failed to track search query")
```

**What it tracks:**
- Records search query and results count
- Tracks if user clicked on results
- Categorizes query type (topic, author, specific_question, general)
- Detects cultural keywords in search queries
- Calculates search success rates

### 5. Assessment Completion Tracking

Track when users complete the Be-Do-Have assessment.

```python
# Track assessment completion
success = analytics_service.track_assessment_completion(
    user_id=123,
    be_score_change=5,    # Change in BE score
    do_score_change=3,    # Change in DO score
    have_score_change=2   # Change in HAVE score
)

if success:
    print("Assessment completion tracked successfully")
else:
    print("Failed to track assessment completion")
```

**What it tracks:**
- Records assessment completion status
- Tracks score changes across all three phases
- Calculates content unlocked count based on scores
- Updates user engagement metrics

### 6. Session Management

Track user session start and end.

```python
# Session is automatically created when tracking any user activity
# To end a session explicitly:

success = analytics_service.end_user_session(
    user_id=123,
    session_id="session_123_1234567890"  # Optional: specific session ID
)

if success:
    print("Session ended successfully")
else:
    print("Failed to end session")
```

**What it tracks:**
- Session duration
- Total session time
- Session end timestamp

### 7. Cultural Relevance Metrics

Calculate and update cultural relevance engagement metrics.

```python
# Calculate cultural relevance metrics for a user
success = analytics_service.calculate_cultural_relevance_metrics(user_id=123)

if success:
    print("Cultural relevance metrics calculated successfully")
else:
    print("Failed to calculate cultural relevance metrics")
```

**What it calculates:**
- High relevance content preference (0-10 scale)
- Community content engagement level
- Cultural search terms frequency
- Diverse representation response metrics

## API Integration

### Frontend JavaScript Integration

```javascript
// Track article view
async function trackArticleView(articleId, readingTime = 0) {
    try {
        const response = await fetch('/api/analytics/track/article-view', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                article_id: articleId,
                reading_time_seconds: readingTime,
                device_type: getDeviceType(),
                user_agent: navigator.userAgent
            })
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Article view tracked successfully');
        }
    } catch (error) {
        console.error('Failed to track article view:', error);
    }
}

// Track search query
async function trackSearchQuery(query, resultsCount, clickedArticleId = null) {
    try {
        const response = await fetch('/api/analytics/track/search-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                search_query: query,
                results_count: resultsCount,
                clicked_article_id: clickedArticleId,
                selected_phase: getCurrentPhase(),
                cultural_relevance_filter: getCulturalFilter()
            })
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Search query tracked successfully');
        }
    } catch (error) {
        console.error('Failed to track search query:', error);
    }
}

// Track article completion
async function trackArticleCompletion(articleId, totalReadingTime) {
    try {
        const response = await fetch('/api/analytics/track/article-completion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                article_id: articleId,
                total_reading_time: totalReadingTime
            })
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Article completion tracked successfully');
        }
    } catch (error) {
        console.error('Failed to track article completion:', error);
    }
}

// Track assessment completion
async function trackAssessmentCompletion(beScoreChange, doScoreChange, haveScoreChange) {
    try {
        const response = await fetch('/api/analytics/track/assessment-completion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                be_score_change: beScoreChange,
                do_score_change: doScoreChange,
                have_score_change: haveScoreChange
            })
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Assessment completion tracked successfully');
        }
    } catch (error) {
        console.error('Failed to track assessment completion:', error);
    }
}

// End user session
async function endUserSession(sessionId = null) {
    try {
        const response = await fetch('/api/analytics/track/session-end', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Session ended successfully');
        }
    } catch (error) {
        console.error('Failed to end session:', error);
    }
}
```

### React Component Integration

```jsx
import React, { useEffect, useRef } from 'react';

const ArticleReader = ({ articleId, articleContent }) => {
    const startTime = useRef(Date.now());
    const readingTimer = useRef(null);
    
    useEffect(() => {
        // Track article view when component mounts
        trackArticleView(articleId);
        
        // Start reading timer
        readingTimer.current = setInterval(() => {
            const readingTime = Math.floor((Date.now() - startTime.current) / 1000);
            // Could track reading progress here
        }, 5000); // Update every 5 seconds
        
        return () => {
            // Track completion when component unmounts
            const totalReadingTime = Math.floor((Date.now() - startTime.current) / 1000);
            trackArticleCompletion(articleId, totalReadingTime);
            
            if (readingTimer.current) {
                clearInterval(readingTimer.current);
            }
        };
    }, [articleId]);
    
    const handleBookmark = () => {
        trackArticleBookmark(articleId);
    };
    
    const handleShare = (platform) => {
        trackArticleShare(articleId, platform);
    };
    
    return (
        <div>
            <h1>{articleContent.title}</h1>
            <div>{articleContent.content}</div>
            <button onClick={handleBookmark}>Bookmark</button>
            <button onClick={() => handleShare('twitter')}>Share on Twitter</button>
        </div>
    );
};
```

## Data Collection Best Practices

### 1. Privacy and Consent
- Always obtain user consent before tracking
- Respect user privacy preferences
- Anonymize data when possible
- Follow GDPR compliance guidelines

### 2. Performance Optimization
- Use batch processing for high-volume events
- Implement retry logic for failed tracking calls
- Cache frequently accessed data
- Monitor tracking performance impact

### 3. Data Quality
- Validate data before tracking
- Handle missing or invalid data gracefully
- Implement data cleaning processes
- Monitor for data anomalies

### 4. Error Handling
```python
try:
    success = analytics_service.track_article_view(
        user_id=user_id,
        article_id=article_id,
        reading_time_seconds=reading_time
    )
    
    if not success:
        logger.warning(f"Failed to track article view for user {user_id}")
        # Implement fallback or retry logic
        
except Exception as e:
    logger.error(f"Error in analytics tracking: {str(e)}")
    # Don't let analytics errors break user experience
```

## Reporting and Analytics

### Daily Reports
```python
# Generate daily report
daily_report = analytics_service.generate_daily_report()

print(f"Date: {daily_report['date']}")
print(f"Total Views: {daily_report['total_views']}")
print(f"Total Searches: {daily_report['total_searches']}")
print(f"Active Users: {daily_report['active_users']}")
```

### Custom Analytics Queries
```python
# Get user engagement for specific date range
from datetime import datetime, timedelta

start_date = datetime.utcnow() - timedelta(days=7)
end_date = datetime.utcnow()

user_engagement = db_session.query(UserEngagementMetrics).filter(
    and_(
        UserEngagementMetrics.created_at >= start_date,
        UserEngagementMetrics.created_at <= end_date
    )
).all()

# Analyze cultural relevance trends
cultural_metrics = db_session.query(CulturalRelevanceAnalytics).filter(
    CulturalRelevanceAnalytics.last_calculated >= start_date
).all()
```

## Monitoring and Maintenance

### Health Checks
- Monitor tracking success rates
- Check database performance
- Monitor API response times
- Track error rates and types

### Data Cleanup
- Archive old analytics data
- Clean up orphaned records
- Optimize database indexes
- Monitor storage usage

### Performance Monitoring
```python
# Monitor tracking performance
import time

start_time = time.time()
success = analytics_service.track_article_view(user_id, article_id)
tracking_time = time.time() - start_time

if tracking_time > 1.0:  # More than 1 second
    logger.warning(f"Slow analytics tracking: {tracking_time:.2f}s")
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database connectivity
   - Verify connection pool settings
   - Monitor database performance

2. **Data Validation Errors**
   - Validate input data before tracking
   - Check for required fields
   - Handle null/empty values

3. **Performance Issues**
   - Monitor query performance
   - Check database indexes
   - Implement caching where appropriate

4. **Memory Issues**
   - Monitor memory usage
   - Implement data pagination
   - Clean up old sessions

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('backend.services.analytics_collection_service').setLevel(logging.DEBUG)

# This will show detailed tracking information
analytics_service.track_article_view(user_id, article_id)
```

## Integration with Existing Systems

### Article Library Integration
```python
# In your article view endpoint
@app.route('/api/articles/<article_id>', methods=['GET'])
@require_auth
def get_article(article_id):
    user_id = session.get('user_id')
    
    # Get article data
    article = get_article_by_id(article_id)
    
    # Track the view
    analytics_service = AnalyticsCollectionService(get_db_session())
    analytics_service.track_article_view(
        user_id=user_id,
        article_id=article_id,
        device_type=request.headers.get('User-Agent', '').split()[0] if request.headers.get('User-Agent') else None
    )
    
    return jsonify(article)
```

### Search Integration
```python
# In your search endpoint
@app.route('/api/articles/search', methods=['POST'])
@require_auth
def search_articles():
    user_id = session.get('user_id')
    data = request.get_json()
    
    # Perform search
    results = perform_search(data['query'], data.get('filters', {}))
    
    # Track search query
    analytics_service = AnalyticsCollectionService(get_db_session())
    analytics_service.track_search_query(
        user_id=user_id,
        query=data['query'],
        results_count=len(results),
        selected_phase=data.get('phase'),
        cultural_relevance_filter=data.get('cultural_relevance_filter')
    )
    
    return jsonify(results)
```

This comprehensive guide provides everything needed to effectively use the AnalyticsCollectionService for tracking user behavior and collecting analytics data in the Mingus article library system.
