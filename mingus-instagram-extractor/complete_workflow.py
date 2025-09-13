#!/usr/bin/env python3
"""
Complete Instagram Content Workflow

This script provides a complete workflow for:
1. Extracting Instagram URLs from Mac Notes
2. Generating manual review CSV if needed
3. Downloading Instagram content
4. Generating Mingus-compatible output

Usage:
    python complete_workflow.py [--skip-extraction] [--skip-download] [--output-dir OUTPUT_DIR]
"""

import sys
import argparse
from pathlib import Path
import json
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from extract_instagram import main as extract_main
from instagram_downloader import InstagramDownloader, ContentItem
from manual_review.manual_review_manager import ManualReviewManager
from progress_reporter import DownloadLogger


def setup_logging():
    """Setup logging for the complete workflow."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('complete_workflow.log')
        ]
    )
    return logging.getLogger(__name__)


def extract_instagram_urls():
    """Extract Instagram URLs from Mac Notes."""
    print("\n" + "="*80)
    print("📱 STEP 1: EXTRACTING INSTAGRAM URLS FROM MAC NOTES")
    print("="*80)
    
    try:
        # Run the extraction
        exit_code = extract_main()
        if exit_code != 0:
            print("❌ Extraction failed")
            return False
        
        print("✅ Extraction completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return False


def check_manual_review_needed():
    """Check if manual review is needed."""
    print("\n" + "="*80)
    print("📋 STEP 2: CHECKING MANUAL REVIEW REQUIREMENTS")
    print("="*80)
    
    try:
        # Check if extraction results exist
        extracted_files = list(Path("extracted_content").glob("*.json"))
        if not extracted_files:
            print("❌ No extracted content found. Run extraction first.")
            return False
        
        # Load the most recent extraction
        latest_file = max(extracted_files, key=lambda p: p.stat().st_mtime)
        print(f"📄 Using extraction file: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        
        # Check if manual review is needed
        manual_review_manager = ManualReviewManager()
        review_stats = manual_review_manager.csv_generator.get_review_statistics(extracted_data)
        
        if review_stats['notes_needing_manual_review'] > 0:
            print(f"⚠️  Manual review needed: {review_stats['notes_needing_manual_review']} items")
            print(f"   Estimated time: {review_stats['estimated_review_time_minutes']:.0f} minutes")
            
            # Generate manual review files
            review_result = manual_review_manager.generate_manual_review_csv(extracted_data)
            
            if review_result['success']:
                print(f"\n📄 Manual review files generated:")
                print(f"   CSV file: {review_result['csv_filepath']}")
                print(f"   Instructions: {review_result['instructions_file']}")
                print(f"\n💡 Next steps:")
                print(f"   1. Open the CSV file and fill in resolved URLs")
                print(f"   2. Run this script again with --skip-extraction")
                print(f"   3. Or use the resolved URLs directly for downloading")
                return False
            else:
                print("❌ Failed to generate manual review files")
                return False
        else:
            print("✅ No manual review needed - all URLs are direct")
            return True
            
    except Exception as e:
        print(f"❌ Error checking manual review: {e}")
        return False


def prepare_download_data(extracted_file: Path):
    """Prepare data for downloading."""
    print("\n" + "="*80)
    print("🔄 STEP 3: PREPARING DOWNLOAD DATA")
    print("="*80)
    
    try:
        with open(extracted_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        
        # Convert to download format
        download_items = []
        
        for note in extracted_data:
            instagram_content = note.get('instagram_content', {})
            urls = instagram_content.get('instagram_urls', [])
            
            for url in urls:
                # Determine content type
                content_type = 'video' if any(x in url.lower() for x in ['/reel/', '/tv/']) else 'image'
                
                # Get category (use the note's category if available)
                category = note.get('category', 'uncategorized')
                
                # Create download item
                item = ContentItem(
                    url=url,
                    category=category,
                    caption=instagram_content.get('caption', ''),
                    alt_text=instagram_content.get('alt_text', ''),
                    creator_credit=instagram_content.get('creator_credit', ''),
                    creator_link=instagram_content.get('creator_link', ''),
                    permission_status=instagram_content.get('permission_status', 'unknown'),
                    notes=note.get('content', '')[:200],  # First 200 chars of note content
                    original_note_id=note.get('note_id', ''),
                    content_type=content_type,
                    post_id=url.split('/')[-1].rstrip('/')
                )
                download_items.append(item)
        
        print(f"✅ Prepared {len(download_items)} items for download")
        
        # Save download data
        download_file = Path("download_data.json")
        download_data = []
        for item in download_items:
            download_data.append({
                'url': item.url,
                'category': item.category,
                'caption': item.caption,
                'alt_text': item.alt_text,
                'creator_credit': item.creator_credit,
                'creator_link': item.creator_link,
                'permission_status': item.permission_status,
                'notes': item.notes,
                'original_note_id': item.original_note_id,
                'content_type': item.content_type,
                'post_id': item.post_id
            })
        
        with open(download_file, 'w', encoding='utf-8') as f:
            json.dump(download_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Download data saved to: {download_file}")
        return download_items, download_file
        
    except Exception as e:
        print(f"❌ Error preparing download data: {e}")
        return None, None


def download_content(download_items, output_dir):
    """Download Instagram content."""
    print("\n" + "="*80)
    print("⬇️  STEP 4: DOWNLOADING INSTAGRAM CONTENT")
    print("="*80)
    
    try:
        downloader = InstagramDownloader(output_dir)
        
        # Check tools
        tool_status = downloader.tool_checker.check_all_tools()
        if not any(tool_status.values()):
            print("❌ No download tools available!")
            print(downloader.tool_checker.get_installation_guidance())
            return False
        
        # Start download
        results = downloader.download_all_content(download_items)
        
        # Generate Mingus CSV
        csv_path = downloader.generate_mingus_csv(results)
        
        # Print summary
        stats = results['statistics']
        print(f"\n🎉 Download completed!")
        print(f"   ✅ Successful: {stats['successful_downloads']}")
        print(f"   ❌ Failed: {stats['failed_downloads']}")
        print(f"   ⏭️  Skipped: {stats['skipped_downloads']}")
        print(f"   📁 Total size: {stats['total_size_bytes'] / (1024*1024):.1f} MB")
        print(f"   📄 Mingus CSV: {csv_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False


def main():
    """Main workflow function."""
    parser = argparse.ArgumentParser(
        description="Complete Instagram Content Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script provides a complete workflow for extracting and downloading Instagram content:

1. Extract Instagram URLs from Mac Notes
2. Check if manual review is needed
3. Prepare download data
4. Download Instagram content
5. Generate Mingus-compatible output

Examples:
  %(prog)s                           # Run complete workflow
  %(prog)s --skip-extraction         # Skip extraction, use existing data
  %(prog)s --skip-download           # Only extract and prepare data
  %(prog)s --output-dir my_content   # Custom output directory
        """
    )
    
    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='Skip the extraction step (use existing extracted data)'
    )
    
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip the download step (only extract and prepare data)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for downloaded content (default: output)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting complete Instagram content workflow")
    
    print("🚀 INSTAGRAM CONTENT COMPLETE WORKFLOW")
    print("="*80)
    print("This workflow will:")
    print("1. Extract Instagram URLs from Mac Notes")
    print("2. Check if manual review is needed")
    print("3. Prepare download data")
    print("4. Download Instagram content")
    print("5. Generate Mingus-compatible output")
    print("="*80)
    
    # Step 1: Extract Instagram URLs
    if not args.skip_extraction:
        if not extract_instagram_urls():
            print("\n❌ Workflow failed at extraction step")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping extraction step")
    
    # Step 2: Check manual review
    if not check_manual_review_needed():
        print("\n⚠️  Manual review required. Please complete the review and run again.")
        sys.exit(0)
    
    # Step 3: Prepare download data
    extracted_files = list(Path("extracted_content").glob("*.json"))
    if not extracted_files:
        print("❌ No extracted content found. Run extraction first.")
        sys.exit(1)
    
    latest_file = max(extracted_files, key=lambda p: p.stat().st_mtime)
    download_items, download_file = prepare_download_data(latest_file)
    
    if not download_items:
        print("❌ Failed to prepare download data")
        sys.exit(1)
    
    # Step 4: Download content
    if not args.skip_download:
        if not download_content(download_items, args.output_dir):
            print("\n❌ Workflow failed at download step")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping download step")
        print(f"📄 Download data prepared: {download_file}")
        print(f"   Run: python download_instagram.py {download_file}")
    
    print("\n🎉 COMPLETE WORKFLOW FINISHED!")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"   Images: {args.output_dir}/images/")
    print(f"   Videos: {args.output_dir}/videos/")
    print(f"   Metadata: {args.output_dir}/metadata/")


if __name__ == "__main__":
    main()
