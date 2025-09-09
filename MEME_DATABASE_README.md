# Mingus Meme Splash Page Database Schema

This document describes the SQLite database schema for the meme splash page feature in the Mingus personal finance application.

## Overview

The meme feature provides users with relatable, humorous content related to personal finance across different life categories. The database tracks meme content and user engagement to provide personalized experiences.

## Database Schema

### Tables

#### 1. `memes` Table
Stores all meme content with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique identifier (auto-increment) |
| `image_url` | TEXT NOT NULL | URL or file path to the meme image |
| `category` | TEXT NOT NULL | Category (faith, work_life, friendships, children, relationships, going_out) |
| `caption` | TEXT NOT NULL | The meme caption text |
| `alt_text` | TEXT NOT NULL | Accessibility description for screen readers |
| `is_active` | BOOLEAN | Whether the meme is currently active (default: 1) |
| `created_at` | DATETIME | Creation timestamp (auto-generated) |
| `updated_at` | DATETIME | Last update timestamp (auto-updated) |

#### 2. `user_meme_history` Table
Tracks which memes each user has viewed:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique identifier (auto-increment) |
| `user_id` | INTEGER NOT NULL | Foreign key to users table |
| `meme_id` | INTEGER NOT NULL | Foreign key to memes table |
| `viewed_at` | DATETIME | When the user viewed the meme (auto-generated) |

**Constraints:**
- Unique constraint on `(user_id, meme_id)` prevents duplicate views
- Foreign key to `memes` table with CASCADE delete

## Categories

The meme system supports six categories:

1. **faith** - Religious/spiritual financial struggles
2. **work_life** - Work-related financial challenges
3. **friendships** - Social spending and friend-related expenses
4. **children** - Parenting and child-related financial stress
5. **relationships** - Dating, marriage, and relationship expenses
6. **going_out** - Entertainment and social activities

## Performance Optimizations

### Indexes
- `idx_memes_category` - Fast category filtering
- `idx_memes_active` - Quick active meme queries
- `idx_memes_category_active` - Combined category and active status
- `idx_memes_created_at` - Time-based sorting
- `idx_user_meme_history_user_id` - User-specific history queries
- `idx_user_meme_history_meme_id` - Meme-specific analytics
- `idx_user_meme_history_viewed_at` - Time-based history analysis
- `idx_user_meme_history_user_viewed` - Combined user and time queries

### Triggers
- `update_memes_timestamp` - Automatically updates `updated_at` when memes are modified

## Usage Examples

### Get Random Meme by Category
```sql
SELECT * FROM memes 
WHERE category = 'faith' AND is_active = 1 
ORDER BY RANDOM() 
LIMIT 1;
```

### Get Unviewed Memes for User
```sql
SELECT m.* FROM memes m 
LEFT JOIN user_meme_history umh ON m.id = umh.meme_id AND umh.user_id = ?
WHERE m.is_active = 1 AND umh.id IS NULL;
```

### Record User View
```sql
INSERT OR IGNORE INTO user_meme_history (user_id, meme_id, viewed_at)
VALUES (?, ?, CURRENT_TIMESTAMP);
```

### User Engagement Analytics
```sql
SELECT m.category, COUNT(*) as view_count 
FROM user_meme_history umh 
JOIN memes m ON umh.meme_id = m.id 
WHERE umh.user_id = ? 
GROUP BY m.category;
```

## Sample Data

The schema includes 18 sample memes (3 per category) with:
- Relatable personal finance humor
- Proper accessibility alt text
- Appropriate emoji usage
- Realistic financial scenarios

## Python Integration

A `MemeDatabase` class is provided (`test_meme_database.py`) with methods for:
- `get_random_meme_by_category()` - Retrieve random memes
- `get_unviewed_memes_for_user()` - Get new content for users
- `record_meme_view()` - Track user engagement
- `get_user_engagement_stats()` - Analytics for user behavior
- `get_meme_stats()` - Overall database statistics

## Production Considerations

### Security
- Input validation for all user-provided data
- SQL injection prevention through parameterized queries
- Image URL validation and sanitization

### Performance
- Regular database maintenance and cleanup
- Consider archiving old user history data
- Monitor query performance with large datasets

### Maintenance
- Regular backup of meme content and user data
- Content moderation for new memes
- A/B testing capabilities for meme effectiveness

### Scalability
- Consider partitioning user_meme_history for large user bases
- Implement caching for frequently accessed memes
- Database connection pooling for high-traffic scenarios

## File Structure

```
├── meme_database_schema.sql    # Complete database schema
├── test_meme_database.py       # Python integration and testing
├── MEME_DATABASE_README.md     # This documentation
└── mingus_memes.db            # Generated SQLite database
```

## Getting Started

1. Run the schema file to create the database:
   ```bash
   sqlite3 mingus_memes.db < meme_database_schema.sql
   ```

2. Test the implementation:
   ```bash
   python test_meme_database.py
   ```

3. Integrate the `MemeDatabase` class into your application

## Future Enhancements

- Meme rating system
- User-generated meme submissions
- Advanced recommendation algorithms
- Meme sharing functionality
- Category-based user preferences
- Seasonal/holiday meme collections
