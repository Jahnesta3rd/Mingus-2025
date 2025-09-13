#!/usr/bin/env python3
"""
Simple command-line interface for Instagram content downloader.

This script provides an easy-to-use interface for downloading Instagram content
with proper error handling and user guidance.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from instagram_downloader import InstagramDownloader, ContentItem
from progress_reporter import DownloadLogger


def check_tools():
    """Check if required tools are available."""
    print("🔧 Checking required tools...")
    
    downloader = InstagramDownloader()
    tool_status = downloader.tool_checker.check_all_tools()
    
    print("\nTool Status:")
    for tool, available in tool_status.items():
        status = "✅ Available" if available else "❌ Not found"
        print(f"  {tool}: {status}")
    
    if not any(tool_status.values()):
        print("\n❌ No download tools available!")
        print(downloader.tool_checker.get_installation_guidance())
        return False
    
    if not tool_status.get('yt-dlp', False):
        print("\n⚠️  yt-dlp not found - will use gallery-dl as fallback")
    
    return True


def create_sample_json():
    """Create a sample JSON file for testing."""
    sample_file = Path("sample_urls.json")
    
    if sample_file.exists():
        print(f"Sample file already exists: {sample_file}")
        return str(sample_file)
    
    # Copy from existing sample
    import shutil
    shutil.copy("sample_urls.json", "my_urls.json")
    
    print(f"Created sample file: my_urls.json")
    print("Edit this file with your Instagram URLs and run the downloader again.")
    return "my_urls.json"


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Instagram Content Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check-tools                    # Check if tools are installed
  %(prog)s --create-sample                  # Create sample JSON file
  %(prog)s sample_urls.json                 # Download from JSON file
  %(prog)s sample_urls.json --output my_content  # Custom output directory
        """
    )
    
    parser.add_argument(
        'json_file',
        nargs='?',
        help='JSON file containing Instagram URLs and metadata'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '--check-tools',
        action='store_true',
        help='Check if required tools are installed'
    )
    
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create a sample JSON file for testing'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.check_tools:
        success = check_tools()
        sys.exit(0 if success else 1)
    
    if args.create_sample:
        sample_file = create_sample_json()
        print(f"\nNext steps:")
        print(f"1. Edit {sample_file} with your Instagram URLs")
        print(f"2. Run: python {sys.argv[0]} {sample_file}")
        sys.exit(0)
    
    # Validate arguments
    if not args.json_file:
        parser.error("JSON file is required. Use --help for usage information.")
    
    json_file = Path(args.json_file)
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        print("Use --create-sample to create a sample file.")
        sys.exit(1)
    
    # Check tools before starting
    if not check_tools():
        print("\nPlease install the required tools and try again.")
        sys.exit(1)
    
    # Initialize downloader
    print(f"\n🚀 Starting Instagram content downloader...")
    print(f"   Input file: {json_file}")
    print(f"   Output directory: {args.output}")
    
    try:
        downloader = InstagramDownloader(args.output)
        
        # Load content items
        print(f"\n📂 Loading content from {json_file}...")
        items = downloader.load_urls_from_json(str(json_file))
        
        if not items:
            print("❌ No content items found in JSON file")
            sys.exit(1)
        
        print(f"   Found {len(items)} content items")
        
        # Show category breakdown
        categories = {}
        content_types = {}
        for item in items:
            categories[item.category] = categories.get(item.category, 0) + 1
            content_types[item.content_type] = content_types.get(item.content_type, 0) + 1
        
        print(f"\n📊 Content breakdown:")
        print(f"   Categories: {', '.join([f'{cat} ({count})' for cat, count in categories.items()])}")
        print(f"   Content types: {', '.join([f'{type} ({count})' for type, count in content_types.items()])}")
        
        # Start download
        print(f"\n⬇️  Starting downloads...")
        results = downloader.download_all_content(items)
        
        # Generate Mingus CSV
        print(f"\n📄 Generating Mingus CSV...")
        csv_path = downloader.generate_mingus_csv(results)
        
        # Final summary
        stats = results['statistics']
        print(f"\n🎉 Download completed!")
        print(f"   ✅ Successful: {stats['successful_downloads']}")
        print(f"   ❌ Failed: {stats['failed_downloads']}")
        print(f"   ⏭️  Skipped: {stats['skipped_downloads']}")
        print(f"   📁 Total size: {stats['total_size_bytes'] / (1024*1024):.1f} MB")
        print(f"   📄 Mingus CSV: {csv_path}")
        
        if stats['failed_downloads'] > 0:
            print(f"\n⚠️  {stats['failed_downloads']} downloads failed. Check the log for details.")
        
        print(f"\n📁 Output directory: {args.output}")
        print(f"   Images: {args.output}/images/")
        print(f"   Videos: {args.output}/videos/")
        print(f"   Metadata: {args.output}/metadata/")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Check the log file for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
