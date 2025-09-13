#!/usr/bin/env python3
"""
Generate API-ready content data for Mingus application integration.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from enhanced_local_notes_processor import EnhancedLocalNotesProcessor

class MingusContentGenerator:
    """Generates API-ready content data for Mingus application."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.api_dir = Path("mingus_api")
        self.api_dir.mkdir(exist_ok=True)
        
    def scan_downloaded_content(self) -> Dict[str, Any]:
        """Scan the output directory for downloaded content."""
        content_items = []
        categories = ['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out', 'uncategorized']
        
        for category in categories:
            # Scan videos
            video_dir = self.output_dir / "videos" / category
            if video_dir.exists():
                for file_path in video_dir.glob("*"):
                    if file_path.is_file() and not file_path.name.endswith('.json'):
                        content_item = self._create_content_item(file_path, category, "video")
                        if content_item:
                            content_items.append(content_item)
            
            # Scan images
            image_dir = self.output_dir / "images" / category
            if image_dir.exists():
                for file_path in image_dir.glob("*"):
                    if file_path.is_file() and not file_path.name.endswith('.json'):
                        content_item = self._create_content_item(file_path, category, "image")
                        if content_item:
                            content_items.append(content_item)
        
        return content_items
    
    def _create_content_item(self, file_path: Path, category: str, media_type: str) -> Dict[str, Any]:
        """Create a content item from a file path."""
        try:
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Extract title from filename
            title = file_path.stem
            if title.startswith("Video by "):
                title = title.replace("Video by ", "")
            elif title.startswith("Post by "):
                title = title.replace("Post by ", "")
            
            # Generate thumbnail path
            thumbnail_path = self._generate_thumbnail_path(file_path)
            
            # Determine display priority based on category
            priority_map = {
                'faith': 1,
                'work_life': 2,
                'friendships': 3,
                'children': 4,
                'relationships': 5,
                'going_out': 6,
                'uncategorized': 7
            }
            
            return {
                "id": f"content_{hash(str(file_path)) % 1000:03d}",
                "title": title,
                "description": self._generate_description(title, category),
                "category": category,
                "confidence": "high",  # Since these were successfully downloaded
                "keywords": self._get_category_keywords(category),
                "media_type": media_type,
                "file_path": str(file_path),
                "thumbnail_path": thumbnail_path,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "extracted_at": modified_time.isoformat(),
                "display_priority": priority_map.get(category, 7),
                "instagram_url": self._extract_instagram_url(file_path)
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def _generate_thumbnail_path(self, file_path: Path) -> str:
        """Generate thumbnail path for the file."""
        # For now, use the original file as thumbnail
        # In production, you'd generate actual thumbnails
        return str(file_path)
    
    def _generate_description(self, title: str, category: str) -> str:
        """Generate a description based on title and category."""
        descriptions = {
            'faith': f"Inspirational content: {title}",
            'work_life': f"Professional content: {title}",
            'friendships': f"Social content: {title}",
            'children': f"Family content: {title}",
            'relationships': f"Relationship content: {title}",
            'going_out': f"Adventure content: {title}",
            'uncategorized': f"Content: {title}"
        }
        return descriptions.get(category, f"Content: {title}")
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """Get keywords for a category."""
        keyword_map = {
            'faith': ['inspiration', 'spiritual', 'motivation'],
            'work_life': ['professional', 'career', 'business'],
            'friendships': ['social', 'community', 'friends'],
            'children': ['family', 'kids', 'parenting'],
            'relationships': ['love', 'romance', 'partnership'],
            'going_out': ['adventure', 'travel', 'exploration'],
            'uncategorized': ['content', 'media', 'social']
        }
        return keyword_map.get(category, ['content'])
    
    def _extract_instagram_url(self, file_path: Path) -> str:
        """Extract Instagram URL from metadata if available."""
        # Look for corresponding .info.json file
        info_file = file_path.with_suffix(file_path.suffix + '.info.json')
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('webpage_url', '')
            except:
                pass
        return ''
    
    def generate_content_manifest(self, content_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate the content manifest."""
        # Count items by category
        category_counts = {}
        for item in content_items:
            category = item['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "content_manifest": {
                "last_updated": datetime.now().isoformat(),
                "total_items": len(content_items),
                "categories": category_counts,
                "api_version": "1.0",
                "generated_by": "mingus-instagram-extractor"
            },
            "items": content_items
        }
    
    def generate_api_endpoints(self, manifest: Dict[str, Any]) -> None:
        """Generate API endpoint files."""
        # Main content endpoint
        with open(self.api_dir / "content.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Category-specific endpoints
        categories = manifest["content_manifest"]["categories"].keys()
        for category in categories:
            category_items = [item for item in manifest["items"] if item["category"] == category]
            category_manifest = {
                "category": category,
                "total_items": len(category_items),
                "items": category_items
            }
            
            with open(self.api_dir / f"{category}.json", "w") as f:
                json.dump(category_manifest, f, indent=2)
        
        # Generate API documentation
        self._generate_api_docs(manifest)
    
    def _generate_api_docs(self, manifest: Dict[str, Any]) -> None:
        """Generate API documentation."""
        docs = f"""# Mingus Content API Documentation

## Overview
This API provides access to Instagram content extracted from your Notes app and categorized for the Mingus application.

## Endpoints

### GET /content.json
Returns all content items with metadata.

### GET /{{category}}.json
Returns content items for a specific category.
Available categories: {', '.join(manifest["content_manifest"]["categories"].keys())}

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
  .then(data => {{
    console.log('Total items:', data.content_manifest.total_items);
    data.items.forEach(item => {{
      console.log(item.title, item.category);
    }});
  }});

// Fetch specific category
fetch('/mingus_api/faith.json')
  .then(response => response.json())
  .then(data => {{
    console.log('Faith items:', data.items);
  }});
```

## Last Updated
{manifest["content_manifest"]["last_updated"]}
"""
        
        with open(self.api_dir / "README.md", "w") as f:
            f.write(docs)
    
    def generate_splash_screen_data(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data specifically for splash screen display."""
        # Sort items by display priority and confidence
        sorted_items = sorted(
            manifest["items"],
            key=lambda x: (x["display_priority"], x["confidence"] == "high")
        )
        
        # Select top items for splash screen
        splash_items = sorted_items[:10]  # Top 10 items
        
        return {
            "splash_screen": {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "total_available": len(manifest["items"]),
                "display_items": len(splash_items),
                "items": splash_items
            }
        }
    
    def run(self) -> None:
        """Run the complete content generation process."""
        print("🔍 Scanning downloaded content...")
        content_items = self.scan_downloaded_content()
        
        if not content_items:
            print("❌ No content found in output directory")
            return
        
        print(f"✅ Found {len(content_items)} content items")
        
        print("📊 Generating content manifest...")
        manifest = self.generate_content_manifest(content_items)
        
        print("🌐 Generating API endpoints...")
        self.generate_api_endpoints(manifest)
        
        print("📱 Generating splash screen data...")
        splash_data = self.generate_splash_screen_data(manifest)
        
        with open(self.api_dir / "splash_screen.json", "w") as f:
            json.dump(splash_data, f, indent=2)
        
        print(f"✅ API data generated in: {self.api_dir.absolute()}")
        print(f"   📄 Main content: content.json")
        print(f"   📄 Splash screen: splash_screen.json")
        print(f"   📄 Category files: {', '.join(manifest['content_manifest']['categories'].keys())}.json")
        print(f"   📄 Documentation: README.md")

if __name__ == "__main__":
    generator = MingusContentGenerator()
    generator.run()
