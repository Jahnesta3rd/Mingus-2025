# Meme Splash Page Feature Documentation

## Overview

The Meme Splash Page feature is a comprehensive system for displaying motivational and educational memes to users in the Mingus personal finance app. The feature includes user preference management, interaction tracking, and analytics to provide a personalized meme experience.

## Database Schema

### Tables

#### 1. `memes` - Core Meme Storage

```sql
CREATE TABLE memes (
    id VARCHAR(36) PRIMARY KEY,
    image_url VARCHAR(500) NOT NULL,
    image_file_path VARCHAR(500),
    category VARCHAR(20) NOT NULL CHECK (
        category IN ('monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith')
    ),
    caption_text TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    engagement_score REAL DEFAULT 0.0,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    tags TEXT,
    source_attribution VARCHAR(200),
    admin_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier (UUID)
- `image_url`: URL to the meme image
- `image_file_path`: Alternative local file path
- `category`: One of 7 day-of-week themed categories
- `caption_text`: The meme's caption
- `alt_text`: Accessibility description
- `is_active`: Whether the meme is available for display
- `view_count`, `like_count`, `share_count`: Engagement metrics
- `engagement_score`: Calculated engagement score
- `priority`: Display priority (1-10)
- `tags`: JSON array of tags for categorization
- `source_attribution`: Credit to original creator
- `admin_notes`: Internal notes
- `created_at`, `updated_at`: Timestamps

#### 2. `user_meme_history` - User Interaction Tracking

```sql
CREATE TABLE user_meme_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    meme_id VARCHAR(36) NOT NULL,
    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_spent_seconds INTEGER DEFAULT 0,
    interaction_type VARCHAR(20) DEFAULT 'view' CHECK (
        interaction_type IN ('view', 'like', 'share', 'skip', 'report')
    ),
    session_id VARCHAR(100),
    source_page VARCHAR(200),
    device_type VARCHAR(50),
    user_agent TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE,
    UNIQUE(user_id, meme_id, viewed_at)
);
```

**Fields:**
- `id`: Unique identifier (UUID)
- `user_id`: Reference to users table
- `meme_id`: Reference to memes table
- `viewed_at`: When the interaction occurred
- `time_spent_seconds`: How long user spent viewing
- `interaction_type`: Type of interaction (view, like, share, skip, report)
- `session_id`: User session identifier
- `source_page`: Where the meme was displayed
- `device_type`, `user_agent`, `ip_address`: Analytics data

#### 3. `user_meme_preferences` - User Control Settings

```sql
CREATE TABLE user_meme_preferences (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    memes_enabled BOOLEAN DEFAULT 1,
    preferred_categories TEXT,
    frequency_setting VARCHAR(20) DEFAULT 'daily' CHECK (
        frequency_setting IN ('daily', 'weekly', 'disabled', 'custom')
    ),
    custom_frequency_days INTEGER DEFAULT 1 CHECK (custom_frequency_days BETWEEN 1 AND 30),
    last_meme_shown_at DATETIME,
    last_meme_shown_id VARCHAR(36),
    opt_out_reason TEXT,
    opt_out_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (last_meme_shown_id) REFERENCES memes(id) ON DELETE SET NULL
);
```

**Fields:**
- `id`: Unique identifier (UUID)
- `user_id`: Reference to users table (unique)
- `memes_enabled`: Whether user wants to see memes
- `preferred_categories`: JSON array of preferred categories
- `frequency_setting`: How often to show memes
- `custom_frequency_days`: Custom frequency in days
- `last_meme_shown_at`: When last meme was shown
- `last_meme_shown_id`: Which meme was last shown
- `opt_out_reason`: Why user disabled memes
- `opt_out_date`: When user opted out

### Indexes

The schema includes comprehensive indexing for performance:

```sql
-- Memes table indexes
CREATE INDEX idx_memes_category ON memes(category);
CREATE INDEX idx_memes_active ON memes(is_active);
CREATE INDEX idx_memes_priority ON memes(priority);
CREATE INDEX idx_memes_engagement ON memes(engagement_score DESC);
CREATE INDEX idx_memes_created_at ON memes(created_at DESC);
CREATE INDEX idx_memes_category_active ON memes(category, is_active);

-- User meme history indexes
CREATE INDEX idx_user_meme_history_user_id ON user_meme_history(user_id);
CREATE INDEX idx_user_meme_history_meme_id ON user_meme_history(meme_id);
CREATE INDEX idx_user_meme_history_viewed_at ON user_meme_history(viewed_at DESC);
CREATE INDEX idx_user_meme_history_user_viewed ON user_meme_history(user_id, viewed_at DESC);
CREATE INDEX idx_user_meme_history_interaction ON user_meme_history(interaction_type);

-- User meme preferences indexes
CREATE INDEX idx_user_meme_preferences_enabled ON user_meme_preferences(memes_enabled);
CREATE INDEX idx_user_meme_preferences_frequency ON user_meme_preferences(frequency_setting);
CREATE INDEX idx_user_meme_preferences_last_shown ON user_meme_preferences(last_meme_shown_at DESC);
```

### Triggers

Automatic updates via triggers:

```sql
-- Update engagement metrics
CREATE TRIGGER update_meme_view_count
    AFTER INSERT ON user_meme_history
    FOR EACH ROW
    WHEN NEW.interaction_type = 'view'
BEGIN
    UPDATE memes SET view_count = view_count + 1 WHERE id = NEW.meme_id;
END;

CREATE TRIGGER update_meme_like_count
    AFTER INSERT ON user_meme_history
    FOR EACH ROW
    WHEN NEW.interaction_type = 'like'
BEGIN
    UPDATE memes SET like_count = like_count + 1 WHERE id = NEW.meme_id;
END;

CREATE TRIGGER update_meme_share_count
    AFTER INSERT ON user_meme_history
    FOR EACH ROW
    WHEN NEW.interaction_type = 'share'
BEGIN
    UPDATE memes SET share_count = share_count + 1 WHERE id = NEW.meme_id;
END;
```

## API Endpoints

### Base URL: `/api/memes`

#### 1. Get Daily Meme
```
GET /api/memes/daily
```

**Description:** Retrieves the daily meme for the current user based on their preferences.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `session_id` (optional): User session identifier
- `source_page` (optional): Page where meme is displayed
- `device_type` (optional): Device type for analytics

**Response:**
```json
{
    "success": true,
    "message": "Daily meme retrieved successfully",
    "data": {
        "id": "meme-uuid",
        "image_url": "https://example.com/meme.jpg",
        "category": "faith",
        "caption_text": "When you finally stick to your budget...",
        "alt_text": "A person praying with dollar bills...",
        "view_count": 150,
        "like_count": 45,
        "share_count": 12,
        "engagement_score": 0.38,
        "priority": 8,
        "tags": ["faith", "budgeting", "blessings"],
        "created_at": "2025-01-27T10:00:00Z"
    }
}
```

#### 2. Get Memes by Category
```
GET /api/memes/category/{category}
```

**Description:** Retrieves memes for a specific category.

**Path Parameters:**
- `category`: One of: faith, work_life, friendships, children, relationships, going_out

**Query Parameters:**
- `limit` (optional): Number of memes to return (max 50, default 10)

**Response:**
```json
{
    "success": true,
    "message": "Memes for category \"faith\" retrieved successfully",
    "data": {
        "category": "faith",
        "memes": [...],
        "count": 3
    }
}
```

#### 3. Record User Interaction
```
POST /api/memes/{meme_id}/interact
```

**Description:** Records user interaction with a meme (like, share, skip, report).

**Path Parameters:**
- `meme_id`: UUID of the meme

**Request Body:**
```json
{
    "interaction_type": "like",
    "time_spent_seconds": 15,
    "session_id": "session-123",
    "source_page": "dashboard",
    "device_type": "mobile"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Interaction recorded successfully",
    "data": {
        "interaction_id": "interaction-uuid",
        "interaction_type": "like",
        "meme_id": "meme-uuid",
        "updated_metrics": {
            "view_count": 151,
            "like_count": 46,
            "share_count": 12,
            "engagement_score": 0.38
        }
    }
}
```

#### 4. Get User Preferences
```
GET /api/memes/preferences
```

**Description:** Retrieves user's meme preferences.

**Response:**
```json
{
    "success": true,
    "message": "User preferences retrieved successfully",
    "data": {
        "id": "pref-uuid",
        "user_id": 123,
        "memes_enabled": true,
        "preferred_categories": ["monday_career", "tuesday_health", "thursday_relationships"],
        "frequency_setting": "daily",
        "custom_frequency_days": 1,
        "last_meme_shown_at": "2025-01-27T09:00:00Z",
        "last_meme_shown_id": "meme-uuid"
    }
}
```

#### 5. Update User Preferences
```
PUT /api/memes/preferences
```

**Description:** Updates user's meme preferences.

**Request Body:**
```json
{
    "memes_enabled": true,
    "preferred_categories": ["faith", "work_life"],
    "frequency_setting": "weekly",
    "custom_frequency_days": 7
}
```

#### 6. Get User Stats
```
GET /api/memes/stats
```

**Description:** Retrieves user's meme interaction statistics.

**Response:**
```json
{
    "success": true,
    "message": "User stats retrieved successfully",
    "data": {
        "total_interactions": 45,
        "interactions_by_type": {
            "view": 30,
            "like": 12,
            "share": 3
        },
        "favorite_categories": ["monday_career", "tuesday_health", "thursday_relationships"]
    }
}
```

#### 7. Get Categories
```
GET /api/memes/categories
```

**Description:** Retrieves available meme categories.

**Response:**
```json
{
    "success": true,
    "message": "Categories retrieved successfully",
    "data": [
        {
            "id": "monday_career",
            "name": "Monday - Career & Business",
            "description": "Career news, business skills, professional development, and workplace financial wisdom"
        },
        {
            "id": "tuesday_health",
            "name": "Tuesday - Health & Wellness",
            "description": "Health spending, wellness investments, medical savings, and fitness financial planning"
        }
        // ... more categories
    ]
}
```

#### 8. Admin Endpoints

**Get Analytics (Admin Only):**
```
GET /api/memes/analytics
```

**Seed Sample Memes (Admin Only):**
```
POST /api/memes/seed
```

## Sample Data

The system includes 21 sample memes (3 per day-of-week category):

### Monday - Career & Business
1. **Monday Motivation** - "Monday motivation: Building wealth one paycheck at a time 💼💪"
2. **Side Hustle Life** - "Side hustle life: Because one income stream is never enough 🚀💰"
3. **Career Growth** - "Investing in yourself is the best investment you can make 📈🎯"

### Tuesday - Health & Wellness
1. **Health Investment** - "Your health is an investment, not an expense 🏃‍♀️💪"
2. **Medical Savings** - "Emergency fund + health savings = peace of mind 🏥💰"
3. **Wellness Budget** - "Budgeting for wellness today saves money tomorrow 🌱💚"

### Wednesday - Home & Transportation
1. **Home Investment** - "Your home is more than shelter, it's an investment 🏠📈"
2. **Transportation Smart** - "Smart transportation choices = more money in your pocket 🚗💡"
3. **Home Improvement** - "Home improvements that pay for themselves 🛠️💸"

### Thursday - Relationships & Family
1. **Money Talks** - "Couples who budget together, stay together 💕💰"
2. **Financial Goals** - "Shared financial goals make relationships stronger 🎯💪"
3. **Money Mindset** - "Finding someone who matches your money mindset is priceless 💎❤️"

### Friday - Entertainment & Fun
1. **Weekend Fun** - "Friday vibes: Having fun doesn't have to break the bank 🎉💸"
2. **Social Spending** - "Social spending: Finding the balance between fun and financial responsibility ⚖️🎊"
3. **Memories Over Money** - "Creating memories is priceless, but being smart about it is priceless too 📸💡"

### Saturday - Kids & Education
1. **College Fund** - "Building a college fund one diaper at a time 🍼🎓"
2. **Legacy Building** - "Creating generational wealth for the little ones 👶💎"
3. **Financial Education** - "Teaching kids about money: The gift that keeps on giving 📚💡"

### Sunday - Faith & Reflection
1. **Blessed Budget** - "When you finally stick to your budget and God rewards you with unexpected income 🙏💰"
2. **Trust the Process** - "Trusting God with your finances while still being responsible with your money 💪✝️"
3. **Grateful Heart** - "Grateful for what I have, working for what I want, and trusting God for what I need 🙌"

## Usage Examples

### Python Service Usage

```python
from backend.services.meme_service import MemeService
from backend.database import get_db

# Initialize service
db = get_db()
meme_service = MemeService(db)

# Get daily meme for user
memes = meme_service.get_memes_for_user(user_id=123, limit=1)
if memes:
    daily_meme = memes[0]
    print(f"Today's meme: {daily_meme.caption_text}")

# Record user interaction
meme_service.record_user_interaction(
    user_id=123,
    meme_id="meme-uuid",
    interaction_type="like",
    time_spent=15
)

# Update user preferences
meme_service.update_user_preferences(user_id=123, {
    "preferred_categories": ["faith", "work_life"],
    "frequency_setting": "weekly"
})
```

### Frontend Integration

```javascript
// Get daily meme
const getDailyMeme = async () => {
    const response = await fetch('/api/memes/daily', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    const data = await response.json();
    return data.data;
};

// Like a meme
const likeMeme = async (memeId) => {
    const response = await fetch(`/api/memes/${memeId}/interact`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            interaction_type: 'like',
            time_spent_seconds: 15
        })
    });
    return response.json();
};

// Update preferences
const updatePreferences = async (preferences) => {
    const response = await fetch('/api/memes/preferences', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(preferences)
    });
    return response.json();
};
```

## Features

### 1. Personalized Content
- User preference management
- Category-based filtering
- Frequency control (daily, weekly, custom, disabled)
- Avoid showing recently viewed memes

### 2. Engagement Tracking
- View, like, share, skip, report interactions
- Time spent viewing analytics
- Session and device tracking
- Engagement score calculation

### 3. Content Management
- Priority-based display ordering
- Active/inactive status control
- Tag-based categorization
- Source attribution tracking

### 4. Analytics & Insights
- User interaction statistics
- Meme performance metrics
- Category popularity analysis
- Daily interaction tracking

### 5. Accessibility
- Alt text for all images
- Screen reader compatibility
- Keyboard navigation support

## Best Practices

### 1. Performance
- Use indexes for frequent queries
- Implement caching for popular memes
- Batch database operations
- Optimize image delivery

### 2. User Experience
- Respect user preferences
- Provide opt-out options
- Clear feedback on interactions
- Smooth loading states

### 3. Content Quality
- Regular content updates
- Diverse category representation
- Cultural sensitivity
- Professional tone

### 4. Privacy
- Secure user data handling
- GDPR compliance
- Opt-out mechanisms
- Data retention policies

## Migration Guide

### 1. Database Setup
```bash
# Run the migration
python -m alembic upgrade head

# Seed sample data (admin only)
curl -X POST /api/memes/seed \
  -H "Authorization: Bearer <admin-token>"
```

### 2. Register Blueprint
```python
from backend.routes.memes import memes_bp

app.register_blueprint(memes_bp)
```

### 3. Update User Model
The User model has been updated to include meme relationships:
```python
# Meme splash page relationships
meme_history = relationship("UserMemeHistory", back_populates="user")
meme_preferences = relationship("UserMemePreferences", back_populates="user", uselist=False)
```

## Troubleshooting

### Common Issues

1. **No memes showing**: Check user preferences and frequency settings
2. **Performance issues**: Verify indexes are created properly
3. **Missing relationships**: Ensure User model is updated with meme relationships
4. **Permission errors**: Verify admin status for admin-only endpoints

### Debug Queries

```sql
-- Check meme counts by category
SELECT category, COUNT(*) as count 
FROM memes 
WHERE is_active = 1 
GROUP BY category;

-- Check user preferences
SELECT * FROM user_meme_preferences 
WHERE user_id = ?;

-- Check recent interactions
SELECT * FROM user_meme_history 
WHERE user_id = ? 
ORDER BY viewed_at DESC 
LIMIT 10;
```

## Future Enhancements

1. **AI-powered recommendations** based on user behavior
2. **A/B testing** for meme effectiveness
3. **Social sharing** integration
4. **Meme creation tools** for users
5. **Advanced analytics** dashboard
6. **Multi-language support**
7. **Seasonal content** scheduling
8. **Integration with financial goals**
