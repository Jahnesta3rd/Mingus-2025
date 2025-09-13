#!/usr/bin/env python3
"""
Script for merging resolved manual review items with direct URL notes.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import LOG_LEVEL, LOG_FORMAT
from manual_review.manual_review_manager import ManualReviewManager


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('instagram_extractor.log')
        ]
    )


def load_notes_from_json(filepath: Path) -> List[Dict[str, Any]]:
    """Load notes from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if 'notes' in data:
            return data['notes']
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid JSON structure")
            
    except Exception as e:
        raise ValueError(f"Error loading JSON file {filepath}: {e}")


def main():
    """Main execution function for merging Instagram content."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Instagram content merge")
    logger.info("=" * 60)
    
    try:
        # Get file paths from command line arguments
        if len(sys.argv) < 3:
            print("Usage: python merge_instagram_content.py <resolved_json> <original_notes_json>")
            print("Example: python merge_instagram_content.py extracted_content/resolved_content_20241201_143022.json extracted_content/mingus_notes_20241201_143022.json")
            return 1
        
        resolved_json_path = Path(sys.argv[1])
        original_notes_path = Path(sys.argv[2])
        
        if not resolved_json_path.exists():
            print(f"❌ Resolved JSON file not found: {resolved_json_path}")
            return 1
        
        if not original_notes_path.exists():
            print(f"❌ Original notes JSON file not found: {original_notes_path}")
            return 1
        
        # Load resolved items
        print(f"📥 Loading resolved items from: {resolved_json_path}")
        resolved_data = json.load(open(resolved_json_path, 'r', encoding='utf-8'))
        
        # Handle different JSON structures for resolved items
        if 'resolved_items' in resolved_data:
            resolved_items = resolved_data['resolved_items']
        elif isinstance(resolved_data, list):
            resolved_items = resolved_data
        else:
            print("❌ Invalid resolved JSON structure")
            return 1
        
        # Load original notes
        print(f"📥 Loading original notes from: {original_notes_path}")
        original_notes = load_notes_from_json(original_notes_path)
        
        # Filter notes with direct Instagram URLs
        direct_url_notes = []
        for note in original_notes:
            instagram_urls = note.get('instagram_urls', [])
            if instagram_urls:
                direct_url_notes.append(note)
        
        print(f"📊 Found {len(resolved_items)} resolved items and {len(direct_url_notes)} direct URL notes")
        
        # Initialize manual review manager
        manual_review_manager = ManualReviewManager()
        
        # Merge content
        print(f"🔄 Merging Instagram content...")
        merge_result = manual_review_manager.merge_with_direct_urls(resolved_items, direct_url_notes)
        
        if not merge_result['success']:
            print(f"❌ Merge failed: {merge_result.get('error', 'Unknown error')}")
            return 1
        
        # Display merge results
        print(f"\n✅ Merge completed successfully!")
        
        # Show merge statistics
        merge_report = merge_result['merge_report']
        print(f"\n📊 Merge Statistics:")
        print(f"   Total combined items: {merge_report['total_items']}")
        
        # Show source distribution
        source_dist = merge_report['source_distribution']
        print(f"\n📈 Source Distribution:")
        for source, count in source_dist.items():
            percentage = (count / merge_report['total_items'] * 100) if merge_report['total_items'] > 0 else 0
            print(f"   {source.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Show URL type distribution
        url_type_dist = merge_report['url_type_distribution']
        print(f"\n🔗 URL Type Distribution:")
        for url_type, count in url_type_dist.items():
            percentage = (count / merge_report['total_items'] * 100) if merge_report['total_items'] > 0 else 0
            print(f"   {url_type.title()}: {count} ({percentage:.1f}%)")
        
        # Show category distribution
        category_dist = merge_report['category_distribution']
        if category_dist:
            print(f"\n🏷️  Category Distribution:")
            for category, count in category_dist.items():
                percentage = (count / merge_report['total_items'] * 100) if merge_report['total_items'] > 0 else 0
                print(f"   {category.title()}: {count} ({percentage:.1f}%)")
        
        # Show output file
        print(f"\n📄 Output File:")
        print(f"   Combined results: {merge_result['output_file']}")
        
        # Show sample of combined items
        combined_items = merge_result['combined_items']
        if combined_items:
            print(f"\n📋 Sample Combined Items (first 5):")
            for i, item in enumerate(combined_items[:5], 1):
                print(f"   {i}. {item['url']} ({item['source']}) - {item['url_type']}")
                if item.get('account_name'):
                    print(f"      Account: {item['account_name']}")
                if item.get('category'):
                    print(f"      Category: {item['category']}")
        
        # Show next steps
        print(f"\n💡 Next Steps:")
        print(f"   1. Review the combined results file")
        print(f"   2. Use the combined Instagram URLs for further processing")
        print(f"   3. Consider downloading or analyzing the content")
        print(f"   4. Export to other formats if needed")
        
        logger.info("Instagram content merge completed successfully")
        print(f"\n🎉 Merge completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Merge interrupted by user")
        print(f"\n⚠️  Merge interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print(f"   Please check the log file for more details")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
