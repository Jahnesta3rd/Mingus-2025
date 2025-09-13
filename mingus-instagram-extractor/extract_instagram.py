#!/usr/bin/env python3
"""
Comprehensive Command-Line Interface for Instagram Extraction and Download System

Main script with subcommands for:
- validate-folder: Check MINGUS folder exists and show statistics
- extract-content: Extract Instagram content from MINGUS folder
- manual-review: Export items needing manual resolution
- import-manual: Import manually resolved URLs
- download: Download Instagram content from URLs
- full-process: Complete pipeline with user prompts

Usage:
    python extract_instagram.py <subcommand> [options]

Examples:
    python extract_instagram.py validate-folder
    python extract_instagram.py extract-content --limit 10
    python extract_instagram.py manual-review export
    python extract_instagram.py import-manual results.csv
    python extract_instagram.py download --limit 5
    python extract_instagram.py full-process --interactive
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import LOG_LEVEL, LOG_FORMAT, CONTENT_CATEGORIES
from extractors.folder_validator import FolderValidator
from extractors.notes_extractor import NotesExtractor
from processors.content_analyzer import ContentAnalyzer
from manual_review.manual_review_manager import ManualReviewManager
from instagram_downloader import InstagramDownloader, ContentItem
from progress_reporter import ProgressReporter, DownloadLogger
from local_notes_processor import LocalNotesProcessor

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ColoredOutput:
    """Helper class for colored terminal output."""
    
    @staticmethod
    def success(message: str) -> str:
        return f"{Colors.GREEN}✓ {message}{Colors.END}"
    
    @staticmethod
    def error(message: str) -> str:
        return f"{Colors.RED}❌ {message}{Colors.END}"
    
    @staticmethod
    def warning(message: str) -> str:
        return f"{Colors.YELLOW}⚠️  {message}{Colors.END}"
    
    @staticmethod
    def info(message: str) -> str:
        return f"{Colors.BLUE}ℹ️  {message}{Colors.END}"
    
    @staticmethod
    def header(message: str) -> str:
        return f"{Colors.BOLD}{Colors.CYAN}{message}{Colors.END}"
    
    @staticmethod
    def highlight(message: str) -> str:
        return f"{Colors.BOLD}{message}{Colors.END}"

class ProgressBar:
    """Simple progress bar for terminal output."""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
        self.start_time = time.time()
    
    def update(self, current: int, message: str = ""):
        self.current = current
        percent = (current / self.total) * 100
        filled = int((current / self.total) * self.width)
        bar = "█" * filled + "░" * (self.width - filled)
        
        elapsed = time.time() - self.start_time
        if current > 0:
            eta = (elapsed / current) * (self.total - current)
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --"
        
        print(f"\r{Colors.CYAN}[{bar}] {percent:5.1f}% ({current}/{self.total}) {eta_str} {message}{Colors.END}", end="", flush=True)
    
    def finish(self, message: str = "Complete"):
        elapsed = time.time() - self.start_time
        print(f"\r{Colors.GREEN}[{'█' * self.width}] 100.0% ({self.total}/{self.total}) {elapsed:.1f}s {message}{Colors.END}")

class CLIInterface:
    """Main CLI interface class."""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.colors = ColoredOutput()
        
        # Initialize components
        self.folder_validator = FolderValidator()
        self.notes_extractor = NotesExtractor()
        self.content_analyzer = ContentAnalyzer()
        self.manual_review_manager = ManualReviewManager()
        self.local_notes_processor = LocalNotesProcessor()
        
        # Output directory
        self.output_dir = Path("extracted_content")
        self.output_dir.mkdir(exist_ok=True)
    
    def setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL.upper()),
            format=LOG_FORMAT,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('instagram_extractor.log')
            ]
        )
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{self.colors.header('=' * 80)}")
        print(f"{self.colors.header(title.center(80))}")
        print(f"{self.colors.header('=' * 80)}")
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"\n{self.colors.success(message)}")
    
    def print_error(self, message: str, suggestions: List[str] = None):
        """Print error message with suggestions."""
        print(f"\n{self.colors.error(message)}")
        if suggestions:
            print(f"\n{self.colors.info('Suggestions:')}")
            for suggestion in suggestions:
                print(f"   • {suggestion}")
    
    def print_warning(self, message: str):
        """Print warning message."""
        print(f"\n{self.colors.warning(message)}")
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"\n{self.colors.info(message)}")
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask user for confirmation."""
        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"{self.colors.warning(message)}{suffix}: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', '1', 'true']
    
    def get_user_input(self, prompt: str, default: str = None) -> str:
        """Get user input with optional default."""
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        else:
            return input(f"{prompt}: ").strip()
    
    def validate_folder(self, args) -> int:
        """Validate local notes and show statistics (with MINGUS folder fallback)."""
        self.print_header("VALIDATING LOCAL NOTES")
        
        try:
            # First try local notes processor (primary method)
            print(f"\n{self.colors.highlight('🔍 Checking local notes...')}")
            local_result = self.local_notes_processor.process_all_local_notes()
            
            if local_result['success']:
                # Display local notes report
                local_report = self.local_notes_processor.generate_processing_report(local_result)
                print(f"\n{local_report}")
                
                # Show detailed statistics
                print(f"\n{self.colors.highlight('📊 LOCAL NOTES STATISTICS:')}")
                print(f"   📝 Total notes processed: {local_result['total_notes']}")
                print(f"   📱 Notes with Instagram content: {local_result['notes_with_instagram']}")
                print(f"   🔗 Total Instagram URLs found: {local_result['total_instagram_urls']}")
                
                if local_result['notes_with_instagram'] > 0:
                    print(f"\n{self.colors.highlight('📱 INSTAGRAM CONTENT FOUND:')}")
                    instagram_notes = [note for note in local_result['processed_notes'] if note['has_instagram_content']]
                    for i, note in enumerate(instagram_notes[:10], 1):  # Show first 10
                        title = note['title'] or 'No title'
                        print(f"   {i}. {title[:80]}{'...' if len(title) > 80 else ''}")
                        for url in note['instagram_urls'][:3]:  # Show first 3 URLs
                            print(f"      🔗 {url}")
                    if len(instagram_notes) > 10:
                        print(f"   ... and {len(instagram_notes) - 10} more notes")
                
                self.print_success("Local notes validation completed successfully!")
                print(f"   Ready for content extraction and download.")
                return 0
            
            else:
                # Fallback to MINGUS folder validation
                print(f"\n{self.colors.warning('⚠️  Local notes processing failed, trying MINGUS folder...')}")
                print(f"   Error: {local_result['error_message']}")
                
                # Try MINGUS folder validation
                validation_result = self.folder_validator.validate_mingus_folder()
                
                # Display validation report
                validation_report = self.folder_validator.generate_validation_report(validation_result)
                print(f"\n{validation_report}")
                
                if not validation_result['valid']:
                    self.print_error(validation_result['error_message'], validation_result.get('suggestions', []))
                    return 1
                
                # Show detailed statistics
                folder_info = validation_result['folder_info']
                notes = validation_result['notes']
                
                print(f"\n{self.colors.highlight('📊 MINGUS FOLDER STATISTICS:')}")
                print(f"   📁 Folder path: {folder_info['folder_path']}")
                print(f"   📝 Total notes: {folder_info['total_notes']}")
                print(f"   📄 Notes with content: {folder_info['notes_with_content']}")
                print(f"   🎨 Rich text notes: {folder_info['rich_text_notes']}")
                print(f"   📏 Total content length: {folder_info['total_content_length']:,} characters")
                
                # Show category breakdown
                if folder_info.get('category_breakdown'):
                    print(f"\n{self.colors.highlight('🏷️  CATEGORY BREAKDOWN:')}")
                    for category, count in folder_info['category_breakdown'].items():
                        percentage = (count / folder_info['total_notes'] * 100) if folder_info['total_notes'] > 0 else 0
                        print(f"   {category}: {count} ({percentage:.1f}%)")
                
                # Show recent notes
                if folder_info.get('recent_notes'):
                    print(f"\n{self.colors.highlight('📅 RECENT NOTES:')}")
                    for note in folder_info['recent_notes'][:5]:
                        title = note.get('title', 'Untitled')[:50]
                        date = note.get('created_date', 'Unknown date')
                        print(f"   • {title}... ({date})")
                
                self.print_success("MINGUS folder validation completed successfully!")
                return 0
            
        except Exception as e:
            self.print_error(f"Validation failed: {e}")
            return 1
    
    def extract_content(self, args) -> int:
        """Extract Instagram content from local notes (with MINGUS folder fallback)."""
        self.print_header("EXTRACTING INSTAGRAM CONTENT")
        
        try:
            # First try local notes processor (primary method)
            print(f"\n{self.colors.highlight('🔍 Processing local notes...')}")
            local_result = self.local_notes_processor.process_all_local_notes()
            
            if local_result['success']:
                # Use local notes data
                notes = local_result['processed_notes']
                print(f"{self.colors.info(f'Found {len(notes)} local notes')}")
                
                # Apply limit if specified
                if args.limit:
                    notes = notes[:args.limit]
                    print(f"{self.colors.info(f'Processing first {len(notes)} notes (limit: {args.limit})')}")
                
                # Apply category filter if specified (for local notes, we'll filter by content)
                if args.category:
                    # For local notes, we'll filter by Instagram content presence
                    if args.category.lower() == 'instagram':
                        notes = [note for note in notes if note['has_instagram_content']]
                    print(f"{self.colors.info(f'Filtered to {len(notes)} notes in category: {args.category}')}")
                
                if not notes:
                    self.print_warning("No notes found matching criteria")
                    return 0
                
                # Process local notes for Instagram content
                print(f"{self.colors.info('Processing Instagram content from local notes...')}")
                
                # Filter to only notes with Instagram content
                instagram_notes = [note for note in notes if note['has_instagram_content']]
                
                # Display statistics
                print(f"\n{self.colors.highlight('📝 EXTRACTION STATISTICS:')}")
                print(f"   Total notes processed: {len(notes)}")
                print(f"   Notes with Instagram content: {len(instagram_notes)}")
                print(f"   Total Instagram URLs found: {sum(len(note['instagram_urls']) for note in instagram_notes)}")
                
                # Show Instagram URLs found
                if instagram_notes:
                    print(f"\n{self.colors.highlight('📱 INSTAGRAM CONTENT FOUND:')}")
                    for i, note in enumerate(instagram_notes[:10], 1):
                        title = note['title'] or 'No title'
                        print(f"   {i}. {title[:80]}{'...' if len(title) > 80 else ''}")
                        for url in note['instagram_urls']:
                            print(f"      🔗 {url}")
                    if len(instagram_notes) > 10:
                        print(f"   ... and {len(instagram_notes) - 10} more notes")
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.output_dir / f"local_notes_extraction_{timestamp}.json"
                
                # Prepare data for saving
                extraction_data = {
                    'extraction_timestamp': timestamp,
                    'total_notes_processed': len(notes),
                    'notes_with_instagram': len(instagram_notes),
                    'total_instagram_urls': sum(len(note['instagram_urls']) for note in instagram_notes),
                    'instagram_notes': instagram_notes
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(extraction_data, f, indent=2, ensure_ascii=False)
                
                print(f"\n{self.colors.success('✅ Local notes extraction completed!')}")
                print(f"   Results saved to: {output_file}")
                print(f"   Instagram notes: {len(instagram_notes)}")
                print(f"   Total Instagram URLs: {sum(len(note['instagram_urls']) for note in instagram_notes)}")
                
                return 0
            
            else:
                # Fallback to MINGUS folder validation
                print(f"\n{self.colors.warning('⚠️  Local notes processing failed, trying MINGUS folder...')}")
                print(f"   Error: {local_result['error_message']}")
                
                # Try MINGUS folder validation
                validation_result = self.folder_validator.validate_mingus_folder()
                if not validation_result['valid']:
                    self.print_error(validation_result['error_message'], validation_result.get('suggestions', []))
                    return 1
                
                folder_info = validation_result['folder_info']
                notes = validation_result['notes']
            
            # Apply limit if specified
            if args.limit:
                notes = notes[:args.limit]
                print(f"{self.colors.info(f'Processing first {len(notes)} notes (limit: {args.limit})')}")
            
            # Apply category filter if specified
            if args.category:
                notes = [note for note in notes if note.get('category', '').lower() == args.category.lower()]
                print(f"{self.colors.info(f'Filtered to {len(notes)} notes in category: {args.category}')}")
            
            if not notes:
                self.print_warning("No notes found matching criteria")
                return 0
            
            # Extract content from notes
            print(f"{self.colors.info('Extracting content from notes...')}")
            extracted_notes = self.notes_extractor.extract_all_notes(notes)
            
            # Generate extraction summary
            extraction_summary = self.notes_extractor.get_extraction_summary(extracted_notes)
            
            # Display extraction statistics
            print(f"\n{self.colors.highlight('📝 EXTRACTION STATISTICS:')}")
            print(f"   Total notes: {extraction_summary['total_notes']}")
            print(f"   Notes with content: {extraction_summary['notes_with_content']}")
            print(f"   Rich text notes: {extraction_summary['rich_text_notes']}")
            print(f"   Total words: {extraction_summary['total_words']:,}")
            
            # Binary decoding statistics
            binary_stats = extraction_summary['binary_decoding']
            print(f"\n{self.colors.highlight('🔧 BINARY DECODING:')}")
            print(f"   Successful decodes: {binary_stats['successful_decodes']}")
            print(f"   Success rate: {binary_stats['success_rate']:.1f}%")
            
            # Instagram content statistics
            instagram_stats = extraction_summary['instagram_content']
            print(f"\n{self.colors.highlight('📱 INSTAGRAM CONTENT:')}")
            print(f"   Instagram-related notes: {instagram_stats['instagram_related_notes']}")
            print(f"   Instagram URLs found: {instagram_stats['instagram_urls_found']}")
            print(f"   Total URLs found: {instagram_stats['total_urls_found']}")
            
            # Analyze content for Instagram links
            print(f"{self.colors.info('Analyzing content for Instagram links...')}")
            analyzed_notes = self.content_analyzer.analyze_notes(extracted_notes)
            
            # Generate Instagram summary
            instagram_summary = self.content_analyzer.get_instagram_summary(analyzed_notes)
            
            print(f"\n{self.colors.highlight('📱 INSTAGRAM ANALYSIS:')}")
            print(f"   Notes with Instagram links: {instagram_summary['notes_with_instagram']}")
            print(f"   Total Instagram URLs: {instagram_summary['total_instagram_urls']}")
            print(f"   Instagram percentage: {instagram_summary['instagram_percentage']:.1f}%")
            
            # Show unique Instagram URLs
            if instagram_summary['unique_instagram_urls']:
                print(f"\n{self.colors.highlight('🔗 INSTAGRAM URLS FOUND:')}")
                for i, url in enumerate(instagram_summary['unique_instagram_urls'][:10], 1):
                    print(f"   {i}. {url}")
                
                if len(instagram_summary['unique_instagram_urls']) > 10:
                    print(f"   ... and {len(instagram_summary['unique_instagram_urls']) - 10} more")
            
            # Save results
            print(f"{self.colors.info('Saving extracted content...')}")
            output_file = self.notes_extractor.save_extracted_content(analyzed_notes, folder_info)
            
            print(f"\n{self.colors.success(f'Results saved to: {output_file}')}")
            
            # Check if manual review is needed
            review_stats = self.manual_review_manager.csv_generator.get_review_statistics(analyzed_notes)
            notes_needing_review = review_stats['notes_needing_manual_review']
            
            if notes_needing_review > 0:
                print(f"\n{self.colors.warning(f'Manual review needed: {notes_needing_review} items')}")
                print(f"   Estimated time: {review_stats['estimated_review_time_minutes']:.0f} minutes")
                print(f"   Run: {self.colors.highlight('python extract_instagram.py manual-review export')}")
            else:
                print(f"\n{self.colors.success('No manual review needed - all Instagram content has direct URLs!')}")
            
            return 0
            
        except Exception as e:
            self.print_error(f"Extraction failed: {e}")
            return 1
    
    def manual_review(self, args) -> int:
        """Export items needing manual resolution."""
        self.print_header("MANUAL REVIEW EXPORT")
        
        try:
            # Check if extraction results exist
            extracted_files = list(self.output_dir.glob("*.json"))
            if not extracted_files:
                self.print_error("No extracted content found. Run extraction first.")
                return 1
            
            # Load the most recent extraction
            latest_file = max(extracted_files, key=lambda p: p.stat().st_mtime)
            print(f"{self.colors.info(f'Using extraction file: {latest_file}')}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                extracted_data = json.load(f)
            
            # Check if manual review is needed
            review_stats = self.manual_review_manager.csv_generator.get_review_statistics(extracted_data)
            
            if review_stats['notes_needing_manual_review'] == 0:
                print(f"\n{self.colors.success('No manual review needed - all Instagram content has direct URLs!')}")
                return 0
            
            print(f"\n{self.colors.highlight('📋 MANUAL REVIEW STATISTICS:')}")
            print(f"   Items needing review: {review_stats['notes_needing_manual_review']}")
            print(f"   Estimated time: {review_stats['estimated_review_time_minutes']:.0f} minutes")
            print(f"   Items with accounts: {review_stats['items_with_accounts']}")
            print(f"   Items with hashtags: {review_stats['items_with_hashtags']}")
            print(f"   Items with mentions: {review_stats['items_with_mentions']}")
            
            # Generate manual review CSV
            print(f"{self.colors.info('Generating manual review files...')}")
            review_result = self.manual_review_manager.generate_manual_review_csv(extracted_data)
            
            if not review_result['success']:
                self.print_error("Failed to generate manual review files")
                return 1
            
            print(f"\n{self.colors.success('Manual review files generated:')}")
            print(f"   📄 CSV file: {review_result['csv_filepath']}")
            print(f"   📋 Instructions: {review_result['instructions_file']}")
            print(f"   📖 Quick reference: {review_result['quick_reference_file']}")
            
            print(f"\n{self.colors.highlight('💡 NEXT STEPS:')}")
            print(f"   1. Open the CSV file in Excel or Google Sheets")
            print(f"   2. Read the instructions file for detailed guidance")
            print(f"   3. Use the suggested search links to find Instagram URLs")
            print(f"   4. Fill in the 'resolved_url' and 'status' columns")
            print(f"   5. Import the completed CSV: {self.colors.highlight('python extract_instagram.py import-manual <csv_file>')}")
            
            return 0
            
        except Exception as e:
            self.print_error(f"Manual review export failed: {e}")
            return 1
    
    def import_manual(self, args) -> int:
        """Import manually resolved URLs."""
        self.print_header("IMPORTING MANUAL REVIEW RESULTS")
        
        try:
            csv_filepath = Path(args.csv_file)
            
            if not csv_filepath.exists():
                self.print_error(f"CSV file not found: {csv_filepath}")
                return 1
            
            print(f"{self.colors.info(f'Importing resolved CSV: {csv_filepath}')}")
            
            # Import resolved CSV
            import_result = self.manual_review_manager.import_resolved_csv(csv_filepath)
            
            if not import_result['success']:
                self.print_error(f"Import failed: {import_result.get('error', 'Unknown error')}")
                return 1
            
            # Display import results
            print(f"\n{self.colors.success('Import completed successfully!')}")
            
            # Show statistics
            import_stats = import_result['import_result']['statistics']
            print(f"\n{self.colors.highlight('📊 IMPORT STATISTICS:')}")
            print(f"   Total items: {import_stats['total_items']}")
            print(f"   Processed items: {import_stats['processed_items']}")
            print(f"   Resolved items: {import_stats['resolved_items']}")
            print(f"   Success rate: {import_stats['success_rate']:.1f}%")
            
            # Show status distribution
            status_dist = import_stats['status_distribution']
            print(f"\n{self.colors.highlight('📈 STATUS DISTRIBUTION:')}")
            for status, count in status_dist.items():
                if count > 0:
                    percentage = (count / import_stats['total_items'] * 100) if import_stats['total_items'] > 0 else 0
                    print(f"   {status.title()}: {count} ({percentage:.1f}%)")
            
            # Show quality metrics
            quality_results = import_result['quality_results']
            print(f"\n{self.colors.highlight('🔍 QUALITY CONTROL:')}")
            print(f"   Valid URLs: {quality_results['valid_urls']}")
            print(f"   Invalid URLs: {quality_results['invalid_urls']}")
            print(f"   Quality Score: {quality_results['quality_score']:.1%}")
            
            # Show output files
            print(f"\n{self.colors.highlight('📄 OUTPUT FILES:')}")
            print(f"   Processed results: {import_result['import_result']['output_file']}")
            print(f"   Quality report: {import_result['quality_report_file']}")
            
            print(f"\n{self.colors.success('Import completed successfully!')}")
            return 0
            
        except Exception as e:
            self.print_error(f"Import failed: {e}")
            return 1
    
    def download(self, args) -> int:
        """Download Instagram content from URLs."""
        self.print_header("DOWNLOADING INSTAGRAM CONTENT")
        
        try:
            # Check if extraction results exist
            extracted_files = list(self.output_dir.glob("*.json"))
            if not extracted_files:
                self.print_error("No extracted content found. Run extraction first.")
                return 1
            
            # Load the most recent extraction
            latest_file = max(extracted_files, key=lambda p: p.stat().st_mtime)
            print(f"{self.colors.info(f'Using extraction file: {latest_file}')}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                extracted_data = json.load(f)
            
            # Convert to download format
            download_items = []
            for note in extracted_data:
                instagram_content = note.get('instagram_content', {})
                urls = instagram_content.get('instagram_urls', [])
                
                for url in urls:
                    # Determine content type
                    content_type = 'video' if any(x in url.lower() for x in ['/reel/', '/tv/']) else 'image'
                    
                    # Get category
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
                        notes=note.get('content', '')[:200],
                        original_note_id=note.get('note_id', ''),
                        content_type=content_type,
                        post_id=url.split('/')[-1].rstrip('/')
                    )
                    download_items.append(item)
            
            # Apply limit if specified
            if args.limit:
                download_items = download_items[:args.limit]
                print(f"{self.colors.info(f'Processing first {len(download_items)} items (limit: {args.limit})')}")
            
            # Apply category filter if specified
            if args.category:
                download_items = [item for item in download_items if item.category.lower() == args.category.lower()]
                print(f"{self.colors.info(f'Filtered to {len(download_items)} items in category: {args.category}')}")
            
            if not download_items:
                self.print_warning("No content items found matching criteria")
                return 0
            
            # Set output directory
            output_dir = args.output_dir or "output"
            
            # Confirm download if not dry run
            if not args.dry_run:
                print(f"\n{self.colors.highlight('📥 DOWNLOAD SUMMARY:')}")
                print(f"   Items to download: {len(download_items)}")
                print(f"   Output directory: {output_dir}")
                
                # Show category breakdown
                category_counts = {}
                for item in download_items:
                    category_counts[item.category] = category_counts.get(item.category, 0) + 1
                
                print(f"   Categories:")
                for category, count in category_counts.items():
                    print(f"     {category}: {count}")
                
                if not self.confirm_action("Proceed with download?", default=True):
                    print(f"{self.colors.info('Download cancelled')}")
                    return 0
            
            # Initialize downloader
            downloader = InstagramDownloader(output_dir)
            
            # Check tools
            print(f"{self.colors.info('Checking download tools...')}")
            tool_status = downloader.tool_checker.check_all_tools()
            
            if not any(tool_status.values()):
                self.print_error("No download tools available!")
                print(downloader.tool_checker.get_installation_guidance())
                return 1
            
            # Show available tools
            available_tools = [tool for tool, available in tool_status.items() if available]
            print(f"{self.colors.success(f'Available tools: {", ".join(available_tools)}')}")
            
            if args.dry_run:
                print(f"\n{self.colors.info('DRY RUN - No actual downloads performed')}")
                print(f"   Would download {len(download_items)} items to {output_dir}")
                return 0
            
            # Start download
            print(f"{self.colors.info('Starting download...')}")
            results = downloader.download_all_content(download_items)
            
            # Generate Mingus CSV
            csv_path = downloader.generate_mingus_csv(results)
            
            # Print summary
            stats = results['statistics']
            print(f"\n{self.colors.success('Download completed!')}")
            print(f"   ✅ Successful: {stats['successful_downloads']}")
            print(f"   ❌ Failed: {stats['failed_downloads']}")
            print(f"   ⏭️  Skipped: {stats['skipped_downloads']}")
            print(f"   📁 Total size: {stats['total_size_bytes'] / (1024*1024):.1f} MB")
            print(f"   📄 Mingus CSV: {csv_path}")
            
            return 0
            
        except Exception as e:
            self.print_error(f"Download failed: {e}")
            return 1
    
    def full_process(self, args) -> int:
        """Complete pipeline with user prompts."""
        self.print_header("COMPLETE INSTAGRAM PROCESSING PIPELINE")
        
        try:
            print(f"{self.colors.info('This will run the complete Instagram processing pipeline:')}")
            print(f"   1. Validate MINGUS folder")
            print(f"   2. Extract Instagram content")
            print(f"   3. Export manual review if needed")
            print(f"   4. Download Instagram content")
            print(f"   5. Generate Mingus-compatible output")
            
            if not self.confirm_action("Proceed with complete pipeline?", default=True):
                print(f"{self.colors.info('Pipeline cancelled')}")
                return 0
            
            # Step 1: Validate folder
            print(f"\n{self.colors.highlight('STEP 1: VALIDATING MINGUS FOLDER')}")
            if self.validate_folder(args) != 0:
                return 1
            
            # Step 2: Extract content
            print(f"\n{self.colors.highlight('STEP 2: EXTRACTING CONTENT')}")
            if self.extract_content(args) != 0:
                return 1
            
            # Step 3: Check for manual review
            print(f"\n{self.colors.highlight('STEP 3: CHECKING MANUAL REVIEW')}")
            extracted_files = list(self.output_dir.glob("*.json"))
            if extracted_files:
                latest_file = max(extracted_files, key=lambda p: p.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    extracted_data = json.load(f)
                
                review_stats = self.manual_review_manager.csv_generator.get_review_statistics(extracted_data)
                
                if review_stats['notes_needing_manual_review'] > 0:
                    print(f"\n{self.colors.warning(f'Manual review needed: {review_stats['notes_needing_manual_review']} items')}")
                    print(f"   Estimated time: {review_stats['estimated_review_time_minutes']:.0f} minutes")
                    
                    if self.confirm_action("Generate manual review files now?", default=True):
                        if self.manual_review(args) != 0:
                            return 1
                        
                        print(f"\n{self.colors.info('Please complete the manual review and run:')}")
                        print(f"   {self.colors.highlight('python extract_instagram.py import-manual <csv_file>')}")
                        print(f"   {self.colors.highlight('python extract_instagram.py download')}")
                        return 0
                    else:
                        print(f"{self.colors.info('Skipping manual review. You can run it later with:')}")
                        print(f"   {self.colors.highlight('python extract_instagram.py manual-review export')}")
            
            # Step 4: Download content
            print(f"\n{self.colors.highlight('STEP 4: DOWNLOADING CONTENT')}")
            if self.download(args) != 0:
                return 1
            
            print(f"\n{self.colors.success('🎉 COMPLETE PIPELINE FINISHED!')}")
            print(f"   📁 Output directory: {args.output_dir or 'output'}")
            print(f"   📄 Check the metadata folder for detailed reports")
            
            return 0
            
        except Exception as e:
            self.print_error(f"Full process failed: {e}")
            return 1

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Instagram Extraction and Download System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s validate-folder                    # Check MINGUS folder
  %(prog)s extract-content --limit 10         # Extract first 10 notes
  %(prog)s extract-content --category faith   # Extract only faith category
  %(prog)s manual-review export               # Export manual review CSV
  %(prog)s import-manual results.csv          # Import resolved URLs
  %(prog)s download --limit 5 --dry-run       # Preview download
  %(prog)s full-process --interactive         # Complete pipeline

For more help on a specific command:
  %(prog)s <command> --help
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate folder command
    validate_parser = subparsers.add_parser('validate-folder', help='Check MINGUS folder exists and show statistics')
    validate_parser.add_argument('--verbose', action='store_true', help='Detailed logging output')
    
    # Extract content command
    extract_parser = subparsers.add_parser('extract-content', help='Extract Instagram content from MINGUS folder')
    extract_parser.add_argument('--limit', type=int, help='Process only first N items (for testing)')
    extract_parser.add_argument('--category', choices=CONTENT_CATEGORIES, help='Filter by specific category')
    extract_parser.add_argument('--dry-run', action='store_true', help='Preview operations without execution')
    extract_parser.add_argument('--verbose', action='store_true', help='Detailed logging output')
    extract_parser.add_argument('--output-dir', help='Custom output directory')
    
    # Manual review command
    manual_parser = subparsers.add_parser('manual-review', help='Export items needing manual resolution')
    manual_parser.add_argument('action', choices=['export'], help='Action to perform')
    manual_parser.add_argument('--verbose', action='store_true', help='Detailed logging output')
    
    # Import manual command
    import_parser = subparsers.add_parser('import-manual', help='Import manually resolved URLs')
    import_parser.add_argument('csv_file', help='Path to completed CSV file')
    import_parser.add_argument('--verbose', action='store_true', help='Detailed logging output')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download Instagram content from URLs')
    download_parser.add_argument('--limit', type=int, help='Process only first N items (for testing)')
    download_parser.add_argument('--category', choices=CONTENT_CATEGORIES, help='Filter by specific category')
    download_parser.add_argument('--dry-run', action='store_true', help='Preview operations without execution')
    download_parser.add_argument('--verbose', action='store_true', help='Detailed logging output')
    download_parser.add_argument('--output-dir', help='Custom output directory')
    
    # Full process command
    full_parser = subparsers.add_parser('full-process', help='Complete pipeline with user prompts')
    full_parser.add_argument('--interactive', action='store_true', help='Interactive mode with prompts')
    full_parser.add_argument('--limit', type=int, help='Process only first N items (for testing)')
    full_parser.add_argument('--category', choices=CONTENT_CATEGORIES, help='Filter by specific category')
    full_parser.add_argument('--verbose', action='store_true', help='Detailed logging output')
    full_parser.add_argument('--output-dir', help='Custom output directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI interface
    cli = CLIInterface()
    
    # Set verbose logging if requested
    if hasattr(args, 'verbose') and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Route to appropriate command
    if args.command == 'validate-folder':
        return cli.validate_folder(args)
    elif args.command == 'extract-content':
        return cli.extract_content(args)
    elif args.command == 'manual-review':
        return cli.manual_review(args)
    elif args.command == 'import-manual':
        return cli.import_manual(args)
    elif args.command == 'download':
        return cli.download(args)
    elif args.command == 'full-process':
        return cli.full_process(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)