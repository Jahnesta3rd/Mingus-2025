# Mingus Content API Documentation

## Overview
This API provides access to Instagram content extracted from your Notes app and categorized for the Mingus application.

## Endpoints

### GET /content.json
Returns all content items with metadata.

### GET /{category}.json
Returns content items for a specific category.
Available categories: uncategorized

## Content Structure
Each content item includes:
- id: Unique identifier
- title: Content title
- description: Generated description
- category: Content category
- confidence: Categorization confidence level
- keywords: Related keywords
- media_type: "image" or "video"
- file_path: Path to media file
- thumbnail_path: Path to thumbnail
- file_size: File size in bytes
- file_size_mb: File size in MB
- extracted_at: Extraction timestamp
- display_priority: Display priority (1-7)
- instagram_url: Original Instagram URL

## Usage Example
```javascript
// Fetch all content
fetch('/mingus_api/content.json')
  .then(response => response.json())
  .then(data => {
    console.log('Total items:', data.content_manifest.total_items);
    data.items.forEach(item => {
      console.log(item.title, item.category);
    });
  });

// Fetch specific category
fetch('/mingus_api/faith.json')
  .then(response => response.json())
  .then(data => {
    console.log('Faith items:', data.items);
  });
```

## Last Updated
2025-09-13T12:25:05.051896
