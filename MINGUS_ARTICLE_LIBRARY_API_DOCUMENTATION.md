# Mingus Article Library API Documentation

## Overview

The Mingus Article Library API provides comprehensive endpoints for managing and accessing the classified article library with Be-Do-Have framework support. This API includes advanced search, personalization, access control, and user progress tracking.

## Base URL

```
http://localhost:5000/api/articles
```

## Authentication

Most endpoints require authentication. The API uses session-based authentication. Include session cookies in requests after login.

## Caching

The API implements intelligent caching for performance optimization:

- **Popular Articles**: Cached for 1 hour
- **Trending Articles**: Cached for 30 minutes  
- **Recent Articles**: Cached for 15 minutes
- **Featured Articles**: Cached for 2 hours
- **Topics & Filters**: Cached for 2 hours

Caches are automatically invalidated when content is updated.

## Input Validation

The API includes comprehensive input validation:

- **JSON Validation**: Ensures proper Content-Type and data structure
- **Assessment Scores**: Validates scores are between 0-100
- **Rating Scores**: Validates ratings are between 1-5
- **Pagination**: Validates page numbers and limits
- **Phase Parameters**: Validates phase values (BE, DO, HAVE)

## Error Handling

The API provides consistent error responses:

- **404**: Article not found
- **403**: Access denied (complete assessment required)
- **400**: Invalid input data
- **500**: Internal server error

## API Endpoints

### Article Discovery & Browsing

#### 1. List Articles
**GET** `/api/articles/`

List articles with filtering, pagination, and personalization.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `q` (string): Search query
- `phase` (string): Filter by phase (BE/DO/HAVE)
- `difficulty` (string): Filter by difficulty (Beginner/Intermediate/Advanced)
- `topics` (string): Comma-separated topics
- `cultural_relevance_min` (int): Minimum cultural relevance score
- `reading_time_max` (int): Maximum reading time in minutes

**Response:**
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": "uuid",
        "title": "Article Title",
        "content_preview": "Preview text...",
        "primary_phase": "BE",
        "difficulty_level": "Beginner",
        "demographic_relevance": 8,
        "reading_time_minutes": 5,
        "user_read": {
          "started_at": "2024-01-01T10:00:00Z",
          "completed_at": null,
          "time_spent_seconds": 120
        }
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

#### 2. Advanced Search
**POST** `/api/articles/search`

Advanced search with multiple filters and ranking.

**Request Body:**
```json
{
  "query": "financial planning",
  "filters": {
    "phase": "BE",
    "difficulty": "Beginner",
    "topics": ["budgeting", "savings"],
    "cultural_relevance_min": 7,
    "reading_time_max": 10
  },
  "page": 1,
  "per_page": 20
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "articles": [...],
    "pagination": {...}
  },
  "articles": [...],
  "query": "financial planning",
  "filters_applied": {...},
  "search_id": "uuid",
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 20,
    "total": 100,
    "has_prev": false,
    "has_next": true
  }
}
```

**Note:** The `search_id` is returned for tracking user interactions with search results.

#### 3. Get Articles by Phase
**GET** `/api/articles/phases/{phase}`

Get articles by Be-Do-Have phase (BE/DO/HAVE).

**Path Parameters:**
- `phase` (string): Phase name (BE, DO, or HAVE)

**Query Parameters:**
- `page` (int): Page number
- `per_page` (int): Items per page

#### 4. Get Recommendations
**GET** `/api/articles/recommendations`

Get personalized article recommendations using advanced multi-strategy recommendation engine.

**Query Parameters:**
- `limit` (int): Number of recommendations (max: 50, default: 10)
- `explanations` (boolean): Include recommendation explanations (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": "uuid",
        "title": "Article Title",
        "primary_phase": "BE",
        "difficulty_level": "Intermediate",
        "recommendation_reason": "Recommended to strengthen your BE skills (your current score: 45) | Highly relevant to your demographic and cultural background"
      }
    ],
    "count": 10,
    "include_explanations": true
  }
}
```

**Recommendation Strategies:**
1. **Progression Recommendations**: Target user's weakest assessment phase
2. **Cultural Relevance**: High demographic and cultural sensitivity scores
3. **Similar Content**: Based on recently read article topics
4. **Featured Content**: Expert-selected content for user's level

#### 4.1. Get Recommendation Explanation
**GET** `/api/articles/recommendations/explanation/{article_id}`

Get detailed explanation for why a specific article was recommended.

**Path Parameters:**
- `article_id` (uuid): Article ID

**Response:**
```json
{
  "success": true,
  "data": {
    "article_id": "uuid",
    "explanation": "Recommended to strengthen your BE skills (your current score: 45) | Highly relevant to your demographic and cultural background"
  }
}
```

#### 5. Get Trending Articles
**GET** `/api/articles/trending`

Get trending articles based on engagement metrics.

**Query Parameters:**
- `limit` (int): Number of articles (max: 50, default: 10)

#### 6. Get Recent Articles
**GET** `/api/articles/recent`

Get recently added articles.

**Query Parameters:**
- `limit` (int): Number of articles (max: 50, default: 10)

#### 7. Get Featured Articles
**GET** `/api/articles/featured`

Get admin-featured high-value articles.

**Query Parameters:**
- `limit` (int): Number of articles (max: 50, default: 10)

### Individual Article Operations

#### 8. Get Article Details
**GET** `/api/articles/{article_id}`

Get full article details with access control validation.

**Path Parameters:**
- `article_id` (uuid): Article ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Article Title",
    "content": "Full article content...",
    "content_preview": "Preview text...",
    "primary_phase": "BE",
    "difficulty_level": "Beginner",
    "demographic_relevance": 8,
    "reading_time_minutes": 5,
    "key_topics": ["budgeting", "savings"],
    "learning_objectives": ["Understand basic budgeting"],
    "user_read": {
      "started_at": "2024-01-01T10:00:00Z",
      "completed_at": null,
      "time_spent_seconds": 120
    }
  }
}
```

#### 9. Get Related Articles
**GET** `/api/articles/{article_id}/related`

Get similar articles and next-step suggestions.

**Path Parameters:**
- `article_id` (uuid): Article ID

**Response:**
```json
{
  "success": true,
  "data": {
    "related": [
      {
        "id": "uuid",
        "title": "Related Article",
        "primary_phase": "BE"
      }
    ],
    "next_steps": [
      {
        "id": "uuid",
        "title": "Next Step Article",
        "primary_phase": "DO"
      }
    ],
    "current_phase": "BE",
    "next_phase": "DO"
  }
}
```

#### 10. Check Article Access
**GET** `/api/articles/{article_id}/access`

Check if user can access article based on assessment requirements.

**Path Parameters:**
- `article_id` (uuid): Article ID

**Response:**
```json
{
  "success": true,
  "data": {
    "can_access": true,
    "article_phase": "BE",
    "article_difficulty": "Intermediate",
    "user_scores": {
      "be_score": 75,
      "do_score": 60,
      "have_score": 45
    }
  }
}
```

#### 11. Track Article View
**POST** `/api/articles/{article_id}/view`

Track article view for analytics.

**Path Parameters:**
- `article_id` (uuid): Article ID

### User Progress & Interaction

#### 12. Update Reading Progress
**POST** `/api/articles/{article_id}/progress`

Update reading progress (start, progress %, completion).

**Path Parameters:**
- `article_id` (uuid): Article ID

**Request Body:**
```json
{
  "progress_percentage": 75.5,
  "time_spent_seconds": 300,
  "engagement_score": 0.8,
  "completed": false,
  "found_helpful": true,
  "would_recommend": true,
  "difficulty_rating": 3,
  "relevance_rating": 4
}
```

#### 13. Toggle Bookmark
**POST** `/api/articles/{article_id}/bookmark`

Toggle bookmark status.

**Path Parameters:**
- `article_id` (uuid): Article ID

**Request Body:**
```json
{
  "notes": "Important article about budgeting",
  "tags": ["budgeting", "beginner"],
  "priority": 2,
  "folder_name": "Financial Planning"
}
```

#### 14. Rate Article
**POST** `/api/articles/{article_id}/rating`

Rate article helpfulness (1-5 stars).

**Path Parameters:**
- `article_id` (uuid): Article ID

**Request Body:**
```json
{
  "overall_rating": 4,
  "helpfulness_rating": 5,
  "clarity_rating": 4,
  "actionability_rating": 3,
  "cultural_relevance_rating": 4,
  "review_text": "Great article for beginners",
  "review_title": "Excellent Introduction"
}
```

#### 15. Get Reading Progress
**GET** `/api/articles/user/reading-progress`

Get user's reading history and progress.

**Response:**
```json
{
  "success": true,
  "data": {
    "reading_history": [
      {
        "article": {
          "id": "uuid",
          "title": "Article Title"
        },
        "read_data": {
          "started_at": "2024-01-01T10:00:00Z",
          "completed_at": "2024-01-01T10:05:00Z",
          "time_spent_seconds": 300,
          "scroll_depth_percentage": 100,
          "engagement_score": 0.9
        }
      }
    ],
    "bookmarks": [...],
    "ratings": [...],
    "stats": {
      "total_articles_read": 25,
      "total_bookmarks": 8,
      "total_ratings": 15,
      "completed_articles": 20
    }
  }
}
```

#### 16. Get User Bookmarks
**GET** `/api/articles/user/bookmarks`

Get user's bookmarked articles with metadata.

#### 17. Get Reading Stats
**GET** `/api/articles/user/reading-stats`

Get user's reading statistics and achievements.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_articles_read": 25,
    "completed_articles": 20,
    "completion_rate": 80.0,
    "total_time_spent_hours": 8.5,
    "average_engagement_score": 0.75,
    "phase_breakdown": {
      "BE": 10,
      "DO": 8,
      "HAVE": 7
    },
    "difficulty_breakdown": {
      "Beginner": 15,
      "Intermediate": 8,
      "Advanced": 2
    },
    "recent_activity": {
      "articles_read_30_days": 5,
      "last_read_date": "2024-01-15T14:30:00Z"
    }
  }
}
```

### Assessment & Access Control

#### 18. Get User Assessment
**GET** `/api/articles/user/assessment`

Get current Be-Do-Have assessment scores with content access information.

**Response:**
```json
{
  "success": true,
  "data": {
    "has_assessment": true,
    "assessment": {
      "scores": {
        "be_score": 75,
        "do_score": 60,
        "have_score": 45
      },
      "levels": {
        "be_level": "Intermediate",
        "do_level": "Intermediate",
        "have_level": "Beginner"
      },
      "metadata": {
        "assessment_date": "2024-01-01T10:00:00Z",
        "assessment_version": "1.0",
        "confidence_score": 0.85,
        "is_valid": true
      }
    },
    "content_access": {
      "total_articles": 150,
      "accessible_articles": 120,
      "access_percentage": 80.0
    }
  },
  "assessment": {
    "be_score": 75,
    "do_score": 60,
    "have_score": 45,
    "overall_readiness_level": "Intermediate"
  },
  "content_access": {
    "total_articles": 150,
    "accessible_articles": 120,
    "access_percentage": 80.0
  }
}
```

#### 19. Submit Assessment
**POST** `/api/articles/user/assessment`

Submit/update assessment scores with automatic recommendation generation.

**Request Body:**
```json
{
  "be_score": 75,
  "do_score": 60,
  "have_score": 45,
  "version": "1.0",
  "confidence_score": 0.85,
  "total_questions": 30,
  "completion_time_minutes": 15
}
```

**Response:**
```json
{
  "success": true,
  "message": "Assessment updated successfully",
  "data": {
    "assessment": {
      "be_score": 75,
      "do_score": 60,
      "have_score": 45,
      "overall_readiness_level": "Intermediate"
    },
    "overall_readiness_level": "Intermediate",
    "new_recommendations": [
      {
        "id": "uuid",
        "title": "Recommended Article",
        "recommendation_reason": "Recommended to strengthen your HAVE skills (your current score: 45)"
      }
    ]
  },
  "assessment": {
    "be_score": 75,
    "do_score": 60,
    "have_score": 45,
    "overall_readiness_level": "Intermediate"
  },
  "overall_readiness_level": "Intermediate",
  "new_recommendations": [...]
}
```

#### 20. Get Unlocked Articles
**GET** `/api/articles/user/unlocked-articles`

Get articles user can access based on assessment.

#### 21. Get Locked Articles
**GET** `/api/articles/user/locked-articles`

Get articles requiring higher assessment scores.

#### 22. Get Assessment Progress
**GET** `/api/articles/user/assessment-progress`

Get progress toward unlocking advanced content.

**Response:**
```json
{
  "success": true,
  "data": {
    "has_assessment": true,
    "progress": {
      "BE": {
        "current_score": 75,
        "current_level": "Intermediate",
        "next_level": "Advanced",
        "required_score": 80,
        "progress_to_next": 75.0
      },
      "DO": {
        "current_score": 60,
        "current_level": "Intermediate",
        "next_level": "Advanced",
        "required_score": 80,
        "progress_to_next": 0.0
      },
      "HAVE": {
        "current_score": 45,
        "current_level": "Beginner",
        "next_level": "Intermediate",
        "required_score": 60,
        "progress_to_next": 75.0
      }
    }
  }
}
```

### Search & Discovery

#### 23. Get Search Suggestions
**GET** `/api/articles/autocomplete`

Get search term autocomplete suggestions.

**Query Parameters:**
- `q` (string): Search query (minimum 2 characters)

**Response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      "Financial Planning",
      "Budgeting Basics",
      "Investment Strategies"
    ]
  }
}
```

#### 24. Get Available Topics
**GET** `/api/articles/topics`

Get available topics and categories.

**Response:**
```json
{
  "success": true,
  "data": {
    "topics": ["budgeting", "savings", "investing"],
    "phases": ["BE", "DO", "HAVE"],
    "difficulty_levels": ["Beginner", "Intermediate", "Advanced"],
    "income_ranges": ["$40K-$60K", "$60K-$80K"],
    "career_stages": ["Early career", "Mid-career"]
  }
}
```

#### 25. Get Available Filters
**GET** `/api/articles/filters`

Get available filter options.

### Analytics & Tracking

#### 26. Get Popular Articles
**GET** `/api/articles/popular`

Get most read articles in user's demographic.

**Query Parameters:**
- `limit` (int): Number of articles (max: 50, default: 10)

#### 27. Track Article Share
**POST** `/api/articles/{article_id}/share`

Track social sharing.

**Path Parameters:**
- `article_id` (uuid): Article ID

**Request Body:**
```json
{
  "platform": "twitter"
}
```

#### 27.1. Track Search Click
**POST** `/api/articles/search/click`

Track when user clicks on a search result for analytics.

**Request Body:**
```json
{
  "search_id": "uuid",
  "article_id": "uuid",
  "position": 3
}
```

**Response:**
```json
{
  "success": true,
  "message": "Search click tracked successfully"
}
```

#### 28. Get Article Stats
**GET** `/api/articles/stats`

Get article engagement statistics (admin).

**Response:**
```json
{
  "success": true,
  "data": {
    "overall": {
      "total_articles": 150,
      "total_views": 5000,
      "total_reads": 3000,
      "total_bookmarks": 800,
      "average_completion_rate": 60.0
    },
    "top_performing": [
      {
        "id": "uuid",
        "title": "Top Article",
        "analytics": {
          "total_views": 500,
          "total_reads": 400,
          "average_rating": 4.5,
          "completion_rate": 80.0
        }
      }
    ]
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (access denied)
- `404`: Not Found
- `500`: Internal Server Error

## Access Control Rules

The API implements assessment-based access control:

### Beginner Content
- **Access**: All users
- **Requirements**: None

### Intermediate Content
- **Access**: Users with Intermediate level (60+ score) in the article's phase
- **Requirements**: Assessment score ≥ 60 in BE, DO, or HAVE phase

### Advanced Content
- **Access**: Users with Advanced level (80+ score) in the article's phase
- **Requirements**: Assessment score ≥ 80 in BE, DO, or HAVE phase

## Rate Limiting

- **Public endpoints**: 100 requests per minute per IP
- **Authenticated endpoints**: 1000 requests per minute per user
- **Search endpoints**: 50 requests per minute per user

## Testing

Use the provided test script to verify API functionality:

```bash
python test_article_api.py
```

## Integration Examples

### JavaScript/Fetch Example

```javascript
// Get trending articles
const response = await fetch('/api/articles/trending?limit=5');
const data = await response.json();

// Search articles
const searchResponse = await fetch('/api/articles/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'financial planning',
    filters: {
      phase: 'BE',
      difficulty: 'Beginner'
    }
  })
});
const searchData = await searchResponse.json();
```

### Python/Requests Example

```python
import requests

# Get recommendations
response = requests.get('/api/articles/recommendations?limit=10')
recommendations = response.json()

# Update reading progress
progress_data = {
    'progress_percentage': 75.5,
    'time_spent_seconds': 300,
    'completed': False
}
response = requests.post(f'/api/articles/{article_id}/progress', 
                        json=progress_data)
```

## Database Schema

The API uses the following key models:

- **Article**: Core article content and metadata
- **UserArticleRead**: User reading history and engagement
- **UserArticleBookmark**: User bookmarks and notes
- **UserArticleRating**: User ratings and reviews
- **UserAssessmentScores**: Be-Do-Have assessment scores
- **ArticleAnalytics**: Aggregate engagement metrics
- **ArticleRecommendation**: Personalized recommendations

## Performance Considerations

- Full-text search uses PostgreSQL's `tsvector` for optimal performance
- Pagination is implemented on all list endpoints
- User-specific data is cached where appropriate
- Analytics are updated asynchronously to avoid blocking user interactions

## Security Features

- Session-based authentication
- Assessment-based access control
- Input validation and sanitization
- Rate limiting to prevent abuse
- SQL injection protection via SQLAlchemy ORM
- XSS protection via proper content encoding
