#!/usr/bin/env python3
"""
Instagram Content Downloader

A comprehensive tool for downloading Instagram content using yt-dlp and gallery-dl.
Handles both direct URLs and manually resolved URLs with proper organization,
attribution preservation, and quality assurance.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import requests
from PIL import Image
import pandas as pd

# Optional imports for enhanced functionality
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    ffmpeg = None

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import LOG_LEVEL, LOG_FORMAT, CONTENT_CATEGORIES, MAX_VIDEO_HEIGHT
from processors.content_processor import ContentProcessor
from progress_reporter import ProgressReporter, DownloadLogger


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    resolution: Optional[str] = None
    format: Optional[str] = None
    thumbnail_path: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class ContentItem:
    """Represents an Instagram content item to download."""
    url: str
    category: str
    caption: str = ""
    alt_text: str = ""
    creator_credit: str = ""
    creator_link: str = ""
    permission_status: str = "unknown"
    notes: str = ""
    original_note_id: str = ""
    content_type: str = "unknown"  # image, video, carousel
    post_id: str = ""


class ToolChecker:
    """Checks availability of download tools and provides installation guidance."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tools = {
            'yt-dlp': {'available': False, 'version': None, 'install_cmd': 'pip install yt-dlp'},
            'gallery-dl': {'available': False, 'version': None, 'install_cmd': 'pip install gallery-dl'},
            'ffmpeg': {'available': False, 'version': None, 'install_cmd': 'brew install ffmpeg'}
        }
    
    def check_all_tools(self) -> Dict[str, bool]:
        """Check availability of all required tools."""
        self.logger.info("Checking tool availability...")
        
        for tool_name in self.tools:
            self.tools[tool_name]['available'] = self._check_tool(tool_name)
        
        return {tool: info['available'] for tool, info in self.tools.items()}
    
    def _check_tool(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        try:
            if tool_name == 'ffmpeg':
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run([tool_name, '--version'], 
                                      capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.tools[tool_name]['version'] = version_line
                self.logger.info(f"✓ {tool_name} found: {version_line}")
                return True
            else:
                self.logger.warning(f"✗ {tool_name} not found or not working")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.logger.warning(f"✗ {tool_name} not found")
            return False
    
    def get_installation_guidance(self) -> str:
        """Get installation guidance for missing tools."""
        missing_tools = [tool for tool, info in self.tools.items() if not info['available']]
        
        if not missing_tools:
            return "All required tools are available!"
        
        guidance = "Missing tools detected. Please install them:\n\n"
        for tool in missing_tools:
            guidance += f"• {tool}: {self.tools[tool]['install_cmd']}\n"
        
        guidance += "\nAfter installation, run the downloader again."
        return guidance


class InstagramDownloader:
    """Main Instagram content downloader class."""
    
    def __init__(self, output_dir: str = "output"):
        # Setup logging
        self.download_logger = DownloadLogger()
        self.logger = self.download_logger.get_logger()
        
        self.output_dir = Path(output_dir)
        self.tool_checker = ToolChecker()
        self.content_processor = ContentProcessor()
        self.progress_reporter = ProgressReporter(self.logger)
        
        # Create output directory structure
        self._create_output_structure()
        
        # Download statistics
        self.stats = {
            'total_items': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_downloads': 0,
            'total_size_bytes': 0,
            'categories': {},
            'content_types': {}
        }
        
        # Rate limiting
        self.last_download_time = 0
        self.download_delay = 2.0  # 2 seconds between downloads
    
    def _create_output_structure(self):
        """Create the output directory structure."""
        categories = CONTENT_CATEGORIES
        
        for content_type in ['images', 'videos']:
            for category in categories:
                category_dir = self.output_dir / content_type / category
                category_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory
        (self.output_dir / 'metadata').mkdir(exist_ok=True)
        
        self.logger.info(f"Created output structure in: {self.output_dir}")
    
    def load_urls_from_json(self, json_file: str) -> List[ContentItem]:
        """Load URLs from JSON file and convert to ContentItem objects."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = []
            for item_data in data:
                item = ContentItem(
                    url=item_data.get('url', ''),
                    category=item_data.get('category', 'uncategorized'),
                    caption=item_data.get('caption', ''),
                    alt_text=item_data.get('alt_text', ''),
                    creator_credit=item_data.get('creator_credit', ''),
                    creator_link=item_data.get('creator_link', ''),
                    permission_status=item_data.get('permission_status', 'unknown'),
                    notes=item_data.get('notes', ''),
                    original_note_id=item_data.get('original_note_id', ''),
                    content_type=item_data.get('content_type', 'unknown'),
                    post_id=item_data.get('post_id', '')
                )
                items.append(item)
            
            self.logger.info(f"Loaded {len(items)} content items from {json_file}")
            return items
            
        except Exception as e:
            self.logger.error(f"Error loading URLs from JSON: {e}")
            return []
    
    def _rate_limit(self):
        """Implement rate limiting for Instagram respect."""
        current_time = time.time()
        time_since_last = current_time - self.last_download_time
        
        if time_since_last < self.download_delay:
            sleep_time = self.download_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_download_time = time.time()
    
    def _generate_unique_filename(self, url: str, category: str, content_type: str, 
                                extension: str) -> str:
        """Generate a unique filename to prevent conflicts."""
        # Create hash from URL and timestamp
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean category name for filename
        clean_category = category.lower().replace(' ', '_').replace('/', '_')
        
        # Generate base filename
        base_name = f"{clean_category}_{timestamp}_{url_hash}"
        filename = f"{base_name}.{extension}"
        
        # Ensure uniqueness
        counter = 1
        original_filename = filename
        while (self.output_dir / content_type / category / filename).exists():
            name, ext = original_filename.rsplit('.', 1)
            filename = f"{name}_{counter}.{ext}"
            counter += 1
        
        return filename
    
    def _download_with_ytdlp(self, url: str, output_path: Path) -> DownloadResult:
        """Download content using yt-dlp."""
        try:
            # yt-dlp command with Instagram-specific options
            cmd = [
                'yt-dlp',
                '--no-playlist',
                '--write-info-json',
                '--write-thumbnail',
                '--format', 'best',  # Use best available format
                '--output', str(output_path / '%(title)s.%(ext)s'),
                '--sleep-interval', '2',  # Rate limiting
                '--max-sleep-interval', '5',
                url
            ]
            
            self.logger.debug(f"Running yt-dlp command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(output_path.parent)
            )
            
            if result.returncode == 0:
                # Find the downloaded file
                downloaded_files = list(output_path.parent.glob(f"{output_path.name}.*"))
                if downloaded_files:
                    main_file = downloaded_files[0]
                    
                    # Get metadata
                    metadata = self._extract_metadata_from_json(output_path.parent)
                    
                    return DownloadResult(
                        success=True,
                        file_path=str(main_file),
                        file_size=main_file.stat().st_size,
                        metadata=metadata
                    )
                else:
                    return DownloadResult(success=False, error_message="No file downloaded")
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return DownloadResult(success=False, error_message=f"yt-dlp error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            return DownloadResult(success=False, error_message="Download timeout")
        except Exception as e:
            return DownloadResult(success=False, error_message=f"yt-dlp exception: {str(e)}")
    
    def _download_with_gallerydl(self, url: str, output_path: Path) -> DownloadResult:
        """Download content using gallery-dl as fallback."""
        try:
            # gallery-dl command
            cmd = [
                'gallery-dl',
                '--directory', str(output_path.parent),
                '--filename', f"{output_path.name}.{{extension}}",
                '--sleep', '2',  # Rate limiting
                url
            ]
            
            self.logger.debug(f"Running gallery-dl command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(output_path.parent)
            )
            
            if result.returncode == 0:
                # Find the downloaded file
                downloaded_files = list(output_path.parent.glob(f"{output_path.name}.*"))
                if downloaded_files:
                    main_file = downloaded_files[0]
                    return DownloadResult(
                        success=True,
                        file_path=str(main_file),
                        file_size=main_file.stat().st_size
                    )
                else:
                    return DownloadResult(success=False, error_message="No file downloaded")
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return DownloadResult(success=False, error_message=f"gallery-dl error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            return DownloadResult(success=False, error_message="Download timeout")
        except Exception as e:
            return DownloadResult(success=False, error_message=f"gallery-dl exception: {str(e)}")
    
    def _extract_metadata_from_json(self, directory: Path) -> Dict:
        """Extract metadata from yt-dlp info JSON file."""
        try:
            json_files = list(directory.glob("*.info.json"))
            if json_files:
                with open(json_files[0], 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                return metadata
        except Exception as e:
            self.logger.warning(f"Could not extract metadata: {e}")
        return {}
    
    def _generate_thumbnail(self, video_path: str, output_path: str) -> bool:
        """Generate thumbnail for video content."""
        if not FFMPEG_AVAILABLE:
            self.logger.warning("ffmpeg not available, skipping thumbnail generation")
            return False
        return self.content_processor.generate_thumbnail(video_path, output_path)
    
    def _validate_downloaded_file(self, file_path: str) -> bool:
        """Validate that the downloaded file is valid."""
        validation_result = self.content_processor.validate_content(file_path)
        return validation_result.get('valid', False)
    
    def download_content(self, item: ContentItem) -> DownloadResult:
        """Download a single content item."""
        self.logger.info(f"Downloading: {item.url}")
        
        # Rate limiting
        self._rate_limit()
        
        # Determine content type directory
        content_type_dir = 'videos' if item.content_type == 'video' else 'images'
        category_dir = self.output_dir / content_type_dir / item.category
        
        # Generate unique filename
        extension = 'mp4' if item.content_type == 'video' else 'jpg'
        filename = self._generate_unique_filename(
            item.url, item.category, content_type_dir, extension
        )
        
        output_path = category_dir / filename
        
        # Try yt-dlp first, then gallery-dl
        result = self._download_with_ytdlp(item.url, output_path)
        
        if not result.success and self.tool_checker.tools['gallery-dl']['available']:
            self.logger.info("yt-dlp failed, trying gallery-dl...")
            result = self._download_with_gallerydl(item.url, output_path)
        
        if result.success:
            # Validate the downloaded file
            if self._validate_downloaded_file(result.file_path):
                # Generate thumbnail for videos
                if item.content_type == 'video' and result.file_path:
                    thumbnail_path = str(output_path.with_suffix('.jpg'))
                    if self._generate_thumbnail(result.file_path, thumbnail_path):
                        result.thumbnail_path = thumbnail_path
                
                self.logger.info(f"✓ Downloaded: {result.file_path}")
            else:
                result.success = False
                result.error_message = "Downloaded file validation failed"
                self.logger.error(f"✗ Validation failed: {result.file_path}")
        
        return result
    
    def download_all_content(self, items: List[ContentItem]) -> Dict[str, Any]:
        """Download all content items and return comprehensive results."""
        self.logger.info(f"Starting download of {len(items)} content items")
        self.stats['total_items'] = len(items)
        
        # Initialize progress reporting
        self.progress_reporter.start_download_session(len(items))
        
        results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'statistics': self.stats
        }
        
        for i, item in enumerate(items, 1):
            self.logger.info(f"Processing item {i}/{len(items)}: {item.category}")
            
            # Update progress
            self.progress_reporter.update_progress(
                item_name=f"{item.category} - {item.content_type}",
                category=item.category,
                content_type=item.content_type
            )
            
            # Skip if already downloaded (check for existing files)
            content_type_dir = 'videos' if item.content_type == 'video' else 'images'
            category_dir = self.output_dir / content_type_dir / item.category
            
            # Check if we already have this content
            existing_files = list(category_dir.glob("*"))
            if existing_files and self._is_duplicate_content(item, existing_files):
                self.logger.info(f"Skipping duplicate content: {item.url}")
                results['skipped'].append(item)
                self.stats['skipped_downloads'] += 1
                self.progress_reporter.mark_skipped(
                    item_name=f"{item.category} - {item.content_type}",
                    category=item.category
                )
                continue
            
            # Download the content
            result = self.download_content(item)
            
            if result.success:
                results['successful'].append({
                    'item': item,
                    'result': result
                })
                self.stats['successful_downloads'] += 1
                self.stats['total_size_bytes'] += result.file_size or 0
                
                # Update category and content type stats
                self.stats['categories'][item.category] = self.stats['categories'].get(item.category, 0) + 1
                self.stats['content_types'][item.content_type] = self.stats['content_types'].get(item.content_type, 0) + 1
                
                # Update progress with success
                self.progress_reporter.update_progress(
                    success=True,
                    file_size=result.file_size or 0,
                    category=item.category,
                    content_type=item.content_type
                )
                
                self.progress_reporter.log_success(
                    f"Downloaded {item.content_type}",
                    item_url=item.url,
                    file_size=result.file_size or 0
                )
            else:
                results['failed'].append({
                    'item': item,
                    'result': result
                })
                self.stats['failed_downloads'] += 1
                
                # Update progress with failure
                self.progress_reporter.update_progress(
                    success=False,
                    category=item.category,
                    content_type=item.content_type
                )
                
                self.progress_reporter.log_error(
                    f"Failed to download: {result.error_message}",
                    item_url=item.url,
                    category=item.category
                )
        
        # Generate final report
        self._generate_download_report(results)
        
        # Print final summary
        self.progress_reporter.print_final_summary()
        
        # Save detailed report
        self.progress_reporter.save_detailed_report(self.output_dir, results)
        
        return results
    
    def _is_duplicate_content(self, item: ContentItem, existing_files: List[Path]) -> bool:
        """Check if content is already downloaded (basic duplicate detection)."""
        # Simple duplicate detection based on URL hash
        url_hash = hashlib.md5(item.url.encode()).hexdigest()[:8]
        
        for file_path in existing_files:
            if url_hash in file_path.name:
                return True
        
        return False
    
    def _generate_download_report(self, results: Dict[str, Any]):
        """Generate a comprehensive download report."""
        report_path = self.output_dir / 'metadata' / 'download_report.json'
        
        # Prepare report data
        report_data = {
            'download_timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'successful_downloads': [
                {
                    'url': item['item'].url,
                    'category': item['item'].category,
                    'file_path': item['result'].file_path,
                    'file_size': item['result'].file_size
                }
                for item in results['successful']
            ],
            'failed_downloads': [
                {
                    'url': item['item'].url,
                    'category': item['item'].category,
                    'error': item['result'].error_message
                }
                for item in results['failed']
            ],
            'skipped_downloads': [
                {
                    'url': item.url,
                    'category': item.category,
                    'reason': 'duplicate'
                }
                for item in results['skipped']
            ]
        }
        
        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Download report saved to: {report_path}")
    
    def generate_mingus_csv(self, results: Dict[str, Any]) -> str:
        """Generate CSV compatible with Mingus database upload."""
        csv_data = []
        
        for item_data in results['successful']:
            item = item_data['item']
            result = item_data['result']
            
            # Generate alt text if not provided
            alt_text = item.alt_text or self._generate_alt_text(item, result)
            
            csv_row = {
                'filename': Path(result.file_path).name if result.file_path else '',
                'category': item.category,
                'caption': item.caption,
                'alt_text': alt_text,
                'creator_credit': item.creator_credit,
                'creator_link': item.creator_link,
                'permission_status': item.permission_status,
                'notes': item.notes,
                'file_path': result.file_path or '',
                'file_size': result.file_size or 0,
                'content_type': item.content_type,
                'download_timestamp': datetime.now().isoformat(),
                'original_url': item.url
            }
            
            csv_data.append(csv_row)
        
        # Create DataFrame and save CSV
        df = pd.DataFrame(csv_data)
        csv_path = self.output_dir / 'metadata' / 'mingus_upload.csv'
        df.to_csv(csv_path, index=False)
        
        self.logger.info(f"Mingus CSV saved to: {csv_path}")
        return str(csv_path)
    
    def _generate_alt_text(self, item: ContentItem, result: DownloadResult) -> str:
        """Generate accessibility alt text for content."""
        base_description = f"Instagram {item.content_type} from {item.category} category"
        
        if item.caption:
            # Use first 100 characters of caption as alt text
            caption_text = item.caption.replace('\n', ' ').strip()
            if len(caption_text) > 100:
                caption_text = caption_text[:97] + "..."
            return f"{base_description}: {caption_text}"
        
        return base_description


def main():
    """Main function for command-line usage."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('instagram_downloader.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Check for required arguments
    if len(sys.argv) < 2:
        print("Usage: python instagram_downloader.py <json_file> [output_dir]")
        print("  json_file: Path to JSON file containing URLs and metadata")
        print("  output_dir: Output directory (default: 'output')")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    # Initialize downloader
    downloader = InstagramDownloader(output_dir)
    
    # Check tools
    logger.info("Checking required tools...")
    tool_status = downloader.tool_checker.check_all_tools()
    
    if not tool_status.get('yt-dlp', False) and not tool_status.get('gallery-dl', False):
        logger.error("No download tools available!")
        print(downloader.tool_checker.get_installation_guidance())
        sys.exit(1)
    
    # Load content items
    logger.info(f"Loading content from: {json_file}")
    items = downloader.load_urls_from_json(json_file)
    
    if not items:
        logger.error("No content items found in JSON file")
        sys.exit(1)
    
    # Download all content
    logger.info(f"Starting download of {len(items)} items...")
    results = downloader.download_all_content(items)
    
    # Generate reports
    csv_path = downloader.generate_mingus_csv(results)
    
    # Print summary
    stats = results['statistics']
    print(f"\n🎉 Download completed!")
    print(f"   Total items: {stats['total_items']}")
    print(f"   Successful: {stats['successful_downloads']}")
    print(f"   Failed: {stats['failed_downloads']}")
    print(f"   Skipped: {stats['skipped_downloads']}")
    print(f"   Total size: {stats['total_size_bytes'] / (1024*1024):.1f} MB")
    print(f"   Mingus CSV: {csv_path}")


if __name__ == "__main__":
    main()
