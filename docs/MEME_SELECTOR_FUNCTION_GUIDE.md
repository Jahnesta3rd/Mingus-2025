# Meme Selector Function Guide

## Overview

The `select_best_meme_for_user` function is a comprehensive Python function designed for the Mingus personal finance app. It intelligently selects the best meme to show users based on their preferences, context, and engagement history.

**Target Audience:** African Americans age 25-35, connecting wellness to money decisions.

## Function Signature

```python
def select_best_meme_for_user(user_id: int, db_path: str = "instance/mingus.db") -> Optional[Dict[str, Any]]
```

## Key Features

### ✅ FIRST PRIORITY: Opt-out Respect
- **Immediate Check:** Function first checks if user has opted out of memes
- **Returns None:** If memes are disabled, function returns `None` immediately
- **Permanent Respect:** Tracks and respects permanent opt-outs

### ✅ User Preference Management
- **Category Preferences:** Respects user's preferred meme categories
- **Frequency Settings:** Honors daily, weekly, or custom frequency choices
- **Smart Defaults:** Provides sensible defaults for new users

### ✅ Contextual Intelligence
- **Day-of-Week Logic:** Considers current day for relevant content
  - **Monday:** Career & work life (`monday_career`)
  - **Tuesday:** Health & wellness (`tuesday_health`)
  - **Wednesday:** Home & transportation (`wednesday_home`)
  - **Thursday:** Relationships & family (`thursday_relationships`)
  - **Friday:** Entertainment & going out (`friday_entertainment`)
  - **Saturday:** Kids & education (`saturday_kids`)
  - **Sunday:** Faith & reflection (`sunday_faith`)

### ✅ Engagement Optimization
- **30-Day Memory:** Avoids showing memes user saw in last 30 days
- **Priority-Based Selection:** Orders by priority and engagement score
- **Fallback Logic:** Multiple fallback strategies if preferred content unavailable

### ✅ Performance & Reliability
- **Caching:** Simple in-memory cache for 5-minute TTL
- **Error Handling:** Graceful error handling without crashing
- **Analytics Logging:** Comprehensive tracking for optimization

## Database Schema

### Required Tables

#### `memes` Table
```sql
CREATE TABLE memes (
    id TEXT PRIMARY KEY,
    image_url TEXT NOT NULL,
    image_file_path TEXT,
    category TEXT NOT NULL,
    caption_text TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    engagement_score REAL DEFAULT 0.0,
    priority INTEGER DEFAULT 5,
    tags TEXT,
    source_attribution TEXT,
    admin_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `user_meme_preferences` Table
```sql
CREATE TABLE user_meme_preferences (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    memes_enabled BOOLEAN DEFAULT 1,
    preferred_categories TEXT,  -- JSON array of categories
    frequency_setting TEXT DEFAULT 'daily',  -- 'daily', 'weekly', 'custom', 'disabled'
    custom_frequency_days INTEGER DEFAULT 1,
    last_meme_shown_at DATETIME,
    last_meme_shown_id TEXT,
    opt_out_reason TEXT,
    opt_out_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `user_meme_history` Table
```sql
CREATE TABLE user_meme_history (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    meme_id TEXT NOT NULL,
    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_spent_seconds INTEGER DEFAULT 0,
    interaction_type TEXT DEFAULT 'view',  -- 'view', 'like', 'share', 'skip', 'report'
    session_id TEXT,
    source_page TEXT,
    device_type TEXT,
    user_agent TEXT,
    ip_address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Basic Usage
```python
from backend.services.meme_selector import select_best_meme_for_user

# Get meme for user
user_id = 123
meme = select_best_meme_for_user(user_id)

if meme:
    print(f"Showing meme: {meme['caption']}")
    print(f"Category: {meme['category']}")
    print(f"Image URL: {meme['image']}")
else:
    print("No meme to show (user opted out or frequency limit)")
```

### With Custom Database Path
```python
meme = select_best_meme_for_user(123, db_path="/path/to/custom/mingus.db")
```

### Error Handling
```python
try:
    meme = select_best_meme_for_user(user_id)
    if meme:
        # Display meme to user
        display_meme(meme)
    else:
        # Show alternative content
        show_alternative_content()
except Exception as e:
    logger.error(f"Error selecting meme: {e}")
    # Fallback to default content
    show_default_content()
```

## Return Value

### Success Case
Returns a dictionary with meme information:
```python
{
    'id': 'meme-123',
    'image': 'https://example.com/memes/monday-career.jpg',
    'caption': 'Monday motivation: Building wealth one paycheck at a time 💼💪',
    'category': 'monday_career',
    'alt_text': 'A person in business attire flexing muscles with money symbols',
    'tags': ['career', 'motivation', 'wealth', 'monday']
}
```

### No Meme Case
Returns `None` when:
- User has opted out of memes
- Frequency limit not met
- No suitable memes available
- Database error occurs

## Algorithm Flow

1. **Cache Check:** Check if result is cached (5-minute TTL)
2. **Opt-out Check:** Verify user hasn't disabled memes
3. **Frequency Check:** Ensure user is due for a meme
4. **Category Selection:** Get user's preferred categories
5. **Day Context:** Consider current day of week
6. **History Filter:** Exclude recently viewed memes (30 days)
7. **Primary Query:** Try today's category + user preferences
8. **Fallback 1:** Try other preferred categories
9. **Fallback 2:** Try any available meme
10. **Update & Cache:** Update user's last shown and cache result
11. **Analytics:** Log selection data for tracking

## Analytics Events

The function logs various analytics events:

### `meme_shown`
```json
{
    "meme_id": "meme-123",
    "category": "monday_career",
    "day_of_week": 0,
    "todays_category": "monday_career",
    "used_fallback": false
}
```

### `meme_opt_out`
```json
{
    "reason": "user_disabled"
}
```

### `meme_frequency_limit`
```json
{
    "frequency_setting": "weekly",
    "last_shown": "2025-01-27T10:30:00"
}
```

### `no_memes_available`
```json
{
    "preferred_categories": ["monday_career", "tuesday_health"],
    "recently_viewed_count": 15
}
```

### `meme_selection_error`
```json
{
    "error": "Database connection failed",
    "error_type": "ConnectionError"
}
```

## Performance Considerations

### Caching
- **In-Memory Cache:** 5-minute TTL for repeated requests
- **Cache Key:** `meme_selection_{user_id}`
- **Cache Invalidation:** Automatic based on timestamp

### Database Optimization
- **Indexed Queries:** Uses existing database indexes
- **Efficient Filtering:** Filters by active status and categories
- **Connection Management:** Proper connection handling

### Memory Usage
- **Minimal Footprint:** Only caches essential data
- **Automatic Cleanup:** Old cache entries expire automatically

## Error Handling

### Database Errors
- **Connection Issues:** Logs error and returns `None`
- **Query Failures:** Graceful degradation with logging
- **Data Corruption:** Handles malformed data gracefully

### Data Validation
- **JSON Parsing:** Handles invalid JSON in preferences
- **Date Parsing:** Manages invalid date formats
- **Missing Data:** Provides sensible defaults

## Testing

### Unit Tests
```python
# Test opt-out functionality
def test_user_opted_out():
    # Setup user with memes disabled
    # Call function
    # Assert None is returned

# Test frequency limits
def test_frequency_limits():
    # Setup user with recent meme shown
    # Call function
    # Assert None is returned

# Test successful selection
def test_successful_selection():
    # Setup user with preferences
    # Call function
    # Assert meme object is returned
```

### Integration Tests
```python
# Test with real database
def test_with_real_database():
    # Setup test database
    # Insert test data
    # Call function
    # Verify results
```

## Deployment Considerations

### Production Setup
1. **Database Path:** Ensure correct database path
2. **Logging:** Configure appropriate log levels
3. **Analytics:** Integrate with analytics service
4. **Monitoring:** Set up error monitoring

### Scaling
- **Connection Pooling:** Consider for high traffic
- **Redis Cache:** Replace in-memory cache for multiple instances
- **Database Optimization:** Monitor query performance

## Security Considerations

### Data Protection
- **User Privacy:** Respects user opt-out preferences
- **Data Validation:** Validates all input data
- **SQL Injection:** Uses parameterized queries

### Access Control
- **User Isolation:** Ensures users only see their data
- **Audit Logging:** Logs all meme selections
- **Error Handling:** Doesn't expose sensitive information

## Future Enhancements

### Potential Improvements
1. **Machine Learning:** Personalized recommendations
2. **A/B Testing:** Test different selection algorithms
3. **Real-time Analytics:** Live performance monitoring
4. **Content Scheduling:** Advanced scheduling features

### Integration Opportunities
1. **Notification System:** Meme delivery via notifications
2. **Social Features:** Meme sharing and reactions
3. **Content Management:** Admin interface for meme management
4. **Performance Dashboard:** Analytics visualization

## Support and Maintenance

### Monitoring
- **Error Rates:** Track function failure rates
- **Performance Metrics:** Monitor response times
- **User Engagement:** Track meme interaction rates

### Troubleshooting
- **Common Issues:** Document frequent problems
- **Debug Mode:** Enable detailed logging
- **Fallback Strategies:** Ensure graceful degradation

---

**Note:** This function is designed to be production-ready and includes comprehensive error handling, logging, and performance optimizations. It follows best practices for database interactions and user experience design.
