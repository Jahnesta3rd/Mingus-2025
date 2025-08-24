# Import Classified Articles Script

## Overview

The `scripts/import_classified_articles.py` script imports classified articles from data files into the Mingus article library database. This script handles data validation, duplicate detection, and proper database insertion with analytics record creation.

## Features

### 🔍 **Data Validation**
- Validates required fields (title, url, content_preview, primary_phase, difficulty_level)
- Validates phase values (BE, DO, HAVE)
- Validates difficulty levels (Beginner, Intermediate, Advanced)
- Provides detailed error messages for invalid data

### 🔄 **Duplicate Detection**
- Checks for existing articles by URL
- Skips duplicates to prevent data conflicts
- Reports skipped articles with reasons

### 📊 **Data Processing**
- Extracts domain from URLs
- Calculates reading time based on content length
- Converts JSON arrays to database-compatible format
- Sets appropriate defaults for missing fields
- Generates unique UUIDs for articles

### 📈 **Analytics Integration**
- Creates analytics records for each imported article
- Initializes all metrics to zero for new articles
- Links analytics records to articles via foreign key

### 🛡️ **Error Handling**
- Comprehensive error handling with rollback capability
- Detailed logging of import progress
- Graceful handling of missing or corrupted files

## Usage

### Basic Import (All Files)
```bash
python scripts/import_classified_articles.py
```

### Import from Specific File
```bash
python scripts/import_classified_articles.py --file data/classified_articles_complete.json
```

### Help
```bash
python scripts/import_classified_articles.py --help
```

## Data Sources

The script imports from the following data files:

1. **`data/classified_articles_complete.json`** - Complete classified articles dataset
2. **`data/have_phase_articles.json`** - Articles classified as HAVE phase
3. **`data/do_phase_articles.json`** - Articles classified as DO phase
4. **`data/be_phase_articles.json`** - Articles classified as BE phase
5. **`data/high_confidence_classifications.json`** - High-confidence AI classifications

## Data Structure

### Input Format
Articles should be in JSON format with the following structure:

```json
{
  "article_id": "",
  "title": "Article Title",
  "author": "Author Name",
  "url": "https://example.com/article",
  "content_preview": "Article content preview...",
  "primary_phase": "HAVE",
  "difficulty_level": "Advanced",
  "confidence_score": 0.8,
  "demographic_relevance": 7,
  "cultural_sensitivity": 5,
  "income_impact_potential": 6,
  "key_topics": ["Topic 1", "Topic 2"],
  "learning_objectives": ["Objective 1", "Objective 2"],
  "prerequisites": ["Prerequisite 1"],
  "cultural_relevance_keywords": ["Keyword 1", "Keyword 2"],
  "target_income_range": "$80K-$100K",
  "career_stage": "Mid-career",
  "actionability_score": 4,
  "professional_development_value": 7,
  "recommended_reading_order": 50
}
```

### Database Mapping

| Input Field | Database Field | Processing |
|-------------|----------------|------------|
| `article_id` | `id` | Generate UUID if empty |
| `title` | `title` | Direct mapping |
| `url` | `url` | Direct mapping |
| `content_preview` | `content_preview` | Truncate to 500 chars |
| `content_preview` | `content` | Truncate to 10,000 chars |
| `primary_phase` | `primary_phase` | Validate against BE/DO/HAVE |
| `difficulty_level` | `difficulty_level` | Validate against Beginner/Intermediate/Advanced |
| `key_topics` | `key_topics` | Convert to JSON string |
| `learning_objectives` | `learning_objectives` | Convert to JSON string |
| `prerequisites` | `prerequisites` | Convert to JSON string |
| `cultural_relevance_keywords` | `cultural_relevance_keywords` | Convert to JSON string |
| `url` | `domain` | Extract domain from URL |

## Output

### Import Summary
The script provides a comprehensive summary including:

- **Total imported**: Number of successfully imported articles
- **Total skipped**: Number of articles skipped (duplicates, invalid)
- **Total failed**: Number of articles that failed to import
- **Total articles in database**: Current article count
- **Phase distribution**: Breakdown by Be-Do-Have phase
- **Difficulty distribution**: Breakdown by difficulty level

### Example Output
```
Starting classified articles import...
============================================================
Loading articles from data/classified_articles_complete.json...
Found 2 articles in data/classified_articles_complete.json
Article already exists: The Minimum Income Necessary To Afford A Five Million Dollar House
Article already exists: The Minimum Income Necessary To Afford A Five Million Dollar House
File data/classified_articles_complete.json: 0 imported, 2 skipped, 0 failed
----------------------------------------
============================================================
Import Summary:
Total imported: 0
Total skipped: 6
Total failed: 0
Total articles in database: 2

Phase Distribution:
  HAVE: 2 articles

Difficulty Distribution:
  Advanced: 2 articles

Import completed successfully!
```

## Error Handling

### Validation Errors
- Missing required fields
- Invalid phase values
- Invalid difficulty levels
- Malformed URLs

### Database Errors
- Connection failures
- Constraint violations
- Transaction rollbacks

### File Errors
- Missing files
- Corrupted JSON
- Encoding issues

## Performance Considerations

### Batch Processing
- Processes articles one by one for detailed error reporting
- Uses database transactions for data consistency
- Commits changes after each file is processed

### Memory Usage
- Loads JSON files into memory
- Processes articles sequentially
- Releases memory after each file

### Database Optimization
- Uses prepared statements
- Implements proper indexing
- Handles large content fields efficiently

## Integration with Migration

The import script works seamlessly with the database migration:

1. **Migration creates tables** - `migrations/add_article_library.py`
2. **Import populates data** - `scripts/import_classified_articles.py`
3. **Models provide access** - `backend/models/articles.py`

## Future Enhancements

### Planned Features
- **Bulk import mode** for large datasets
- **Incremental updates** for existing articles
- **Content deduplication** beyond URL matching
- **Import scheduling** for automated updates
- **Progress tracking** for large imports

### Performance Improvements
- **Batch inserts** for better performance
- **Parallel processing** for multiple files
- **Memory optimization** for large datasets
- **Database connection pooling**

## Troubleshooting

### Common Issues

1. **"File not found" errors**
   - Check file paths in data directory
   - Verify file permissions

2. **"Article already exists" messages**
   - Normal behavior for duplicate detection
   - Use `--file` option to import specific files

3. **Database connection errors**
   - Verify database exists at `instance/mingus.db`
   - Check database permissions

4. **JSON parsing errors**
   - Validate JSON file format
   - Check for encoding issues

### Debug Mode
Add debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Conclusion

The import script provides a robust, feature-rich solution for importing classified articles into the Mingus article library. It ensures data integrity, handles duplicates gracefully, and provides comprehensive reporting for import operations.

The script is ready for production use and can handle both small and large datasets efficiently.
