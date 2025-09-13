#!/usr/bin/env python3
"""
Extract Instagram content from all notes in Mac Notes database
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import NOTES_DB_PATH, LOG_LEVEL, LOG_FORMAT
from processors.content_analyzer import ContentAnalyzer
from extractors.notes_extractor import NotesExtractor
import logging

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('extract_all_notes.log')
        ]
    )

def get_all_notes(limit=None):
    """Get all notes from the database."""
    try:
        with sqlite3.connect(NOTES_DB_PATH, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query to get all notes with Instagram content
            query = """
            SELECT 
                n.Z_PK as note_id,
                COALESCE(n.ZTITLE, 'Untitled') as title,
                n.ZSNIPPET as body_text,
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
            
            print(f"📝 Retrieved {len(notes)} notes with Instagram content from database")
            return [dict(note) for note in notes]
            
    except Exception as e:
        print(f"❌ Error retrieving notes: {e}")
        return []

def main():
    """Main extraction function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 INSTAGRAM CONTENT EXTRACTION FROM ALL NOTES")
    print("=" * 60)
    
    # Get all notes
    notes = get_all_notes(limit=50)  # Limit to 50 for testing
    
    if not notes:
        print("❌ No notes found in database")
        return 1
    
    print(f"📊 Processing {len(notes)} notes...")
    
    # Initialize components
    notes_extractor = NotesExtractor()
    content_analyzer = ContentAnalyzer()
    
    # Extract content from notes
    print("🔍 Extracting content from notes...")
    extracted_notes = notes_extractor.extract_all_notes(notes)
    
    # Generate extraction summary
    extraction_summary = notes_extractor.get_extraction_summary(extracted_notes)
    
    # Display extraction statistics
    print(f"\n📊 EXTRACTION STATISTICS:")
    print(f"   Total notes: {extraction_summary['total_notes']}")
    print(f"   Notes with content: {extraction_summary['notes_with_content']}")
    print(f"   Rich text notes: {extraction_summary['rich_text_notes']}")
    print(f"   Total words: {extraction_summary['total_words']:,}")
    
    # Instagram content statistics
    instagram_stats = extraction_summary['instagram_content']
    print(f"\n📱 INSTAGRAM CONTENT:")
    print(f"   Instagram-related notes: {instagram_stats['instagram_related_notes']}")
    print(f"   Instagram URLs found: {instagram_stats['instagram_urls_found']}")
    print(f"   Total URLs found: {instagram_stats['total_urls_found']}")
    
    # Analyze content for Instagram links
    print("🔍 Analyzing content for Instagram links...")
    analyzed_notes = content_analyzer.analyze_notes(extracted_notes)
    
    # Generate Instagram summary
    instagram_summary = content_analyzer.get_instagram_summary(analyzed_notes)
    
    print(f"\n📱 INSTAGRAM ANALYSIS:")
    print(f"   Notes with Instagram links: {instagram_summary['notes_with_instagram']}")
    print(f"   Total Instagram URLs: {instagram_summary['total_instagram_urls']}")
    print(f"   Instagram percentage: {instagram_summary['instagram_percentage']:.1f}%")
    
    # Show unique Instagram URLs
    if instagram_summary['unique_instagram_urls']:
        print(f"\n🔗 INSTAGRAM URLS FOUND:")
        for i, url in enumerate(instagram_summary['unique_instagram_urls'][:10], 1):
            print(f"   {i}. {url}")
        
        if len(instagram_summary['unique_instagram_urls']) > 10:
            print(f"   ... and {len(instagram_summary['unique_instagram_urls']) - 10} more")
    
    # Save results
    print("💾 Saving extracted content...")
    output_dir = Path("extracted_content")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"all_notes_extraction_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analyzed_notes, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Results saved to: {output_file}")
    
    # Show sample notes with Instagram content
    instagram_notes = [note for note in analyzed_notes if note.get('instagram_content', {}).get('instagram_urls')]
    if instagram_notes:
        print(f"\n📱 SAMPLE INSTAGRAM NOTES:")
        for i, note in enumerate(instagram_notes[:3], 1):
            title = note.get('title', 'Untitled')
            urls = note.get('instagram_content', {}).get('instagram_urls', [])
            print(f"   {i}. {title[:50]}...")
            for url in urls[:2]:  # Show first 2 URLs
                print(f"      • {url}")
            if len(urls) > 2:
                print(f"      • ... and {len(urls) - 2} more URLs")
    
    print(f"\n🎉 Extraction completed successfully!")
    print(f"   Found {instagram_summary['total_instagram_urls']} Instagram URLs")
    print(f"   From {instagram_summary['notes_with_instagram']} notes")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
