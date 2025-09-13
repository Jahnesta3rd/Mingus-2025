#!/usr/bin/env python3
"""
Simple Instagram URL extraction from Mac Notes
"""

import sqlite3
import re
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import NOTES_DB_PATH

# Instagram URL patterns
INSTAGRAM_URL_PATTERNS = [
    r"https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.-]+/[0-9]+/?",
]

def extract_instagram_urls(text):
    """Extract Instagram URLs from text."""
    urls = []
    for pattern in INSTAGRAM_URL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    return urls

def get_instagram_notes(limit=None):
    """Get notes with Instagram content."""
    try:
        with sqlite3.connect(NOTES_DB_PATH, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT 
                n.Z_PK as note_id,
                COALESCE(n.ZTITLE, 'Untitled') as title,
                n.ZSNIPPET as content,
                n.ZCREATIONDATE as creation_date,
                n.ZMODIFICATIONDATE as modification_date
            FROM ZICCLOUDSYNCINGOBJECT n
            WHERE n.ZSNIPPET IS NOT NULL
            AND n.ZSNIPPET LIKE '%instagram%'
            ORDER BY n.ZMODIFICATIONDATE DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            notes = cursor.fetchall()
            
            print(f"📝 Found {len(notes)} notes with Instagram content")
            return [dict(note) for note in notes]
            
    except Exception as e:
        print(f"❌ Error retrieving notes: {e}")
        return []

def main():
    """Main extraction function."""
    print("🚀 SIMPLE INSTAGRAM URL EXTRACTION")
    print("=" * 50)
    
    # Get notes
    notes = get_instagram_notes(limit=20)
    
    if not notes:
        print("❌ No notes found")
        return 1
    
    # Extract Instagram URLs
    all_urls = []
    processed_notes = []
    
    for note in notes:
        content = note.get('content', '')
        urls = extract_instagram_urls(content)
        
        if urls:
            note_data = {
                'note_id': note['note_id'],
                'title': note['title'],
                'content': content,
                'instagram_urls': urls,
                'creation_date': note['creation_date'],
                'modification_date': note['modification_date']
            }
            processed_notes.append(note_data)
            all_urls.extend(urls)
            print(f"📱 {note['title'][:50]}... - {len(urls)} URLs")
            for url in urls:
                print(f"   • {url}")
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"   Total notes processed: {len(notes)}")
    print(f"   Notes with Instagram URLs: {len(processed_notes)}")
    print(f"   Total Instagram URLs found: {len(all_urls)}")
    print(f"   Unique URLs: {len(set(all_urls))}")
    
    # Save results
    output_dir = Path("extracted_content")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"instagram_urls_{timestamp}.json"
    
    results = {
        'extraction_info': {
            'timestamp': timestamp,
            'total_notes': len(notes),
            'notes_with_urls': len(processed_notes),
            'total_urls': len(all_urls),
            'unique_urls': len(set(all_urls))
        },
        'notes': processed_notes,
        'all_urls': list(set(all_urls))
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show unique URLs
    if all_urls:
        print(f"\n🔗 UNIQUE INSTAGRAM URLS:")
        for i, url in enumerate(set(all_urls), 1):
            print(f"   {i}. {url}")
    
    print(f"\n🎉 Extraction completed successfully!")
    return 0

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
