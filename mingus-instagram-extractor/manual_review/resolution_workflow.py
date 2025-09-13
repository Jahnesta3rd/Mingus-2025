"""
Resolution workflow for importing completed manual review spreadsheets.
"""

import csv
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)


class ResolutionWorkflow:
    """Handles importing and processing of completed manual review spreadsheets."""
    
    def __init__(self, output_dir: Path = Path("extracted_content")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        # Instagram URL patterns for validation
        self.instagram_patterns = [
            r"https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?",
            r"https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?",
            r"https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?",
            r"https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.-]+/[0-9]+/?",
        ]
        
        # Compile patterns for validation
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.instagram_patterns]
    
    def import_resolved_csv(self, csv_filepath: Path) -> Dict[str, Any]:
        """
        Import and process a completed manual review CSV file.
        
        Args:
            csv_filepath: Path to the completed CSV file
            
        Returns:
            Dictionary with import results and statistics
        """
        logger.info(f"Importing resolved CSV: {csv_filepath}")
        
        try:
            # Read CSV file
            resolved_items = self._read_csv_file(csv_filepath)
            
            if not resolved_items:
                logger.warning("No data found in CSV file")
                return self._create_empty_import_result()
            
            # Process resolved items
            processed_items = self._process_resolved_items(resolved_items)
            
            # Generate statistics
            statistics = self._generate_import_statistics(processed_items)
            
            # Save processed results
            output_file = self._save_processed_results(processed_items, statistics)
            
            logger.info(f"Successfully imported {len(processed_items)} resolved items")
            
            return {
                'success': True,
                'total_items': len(resolved_items),
                'processed_items': len(processed_items),
                'statistics': statistics,
                'output_file': output_file,
                'processed_items': processed_items
            }
            
        except Exception as e:
            logger.error(f"Error importing resolved CSV: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_items': 0,
                'processed_items': 0,
                'statistics': {}
            }
    
    def _read_csv_file(self, csv_filepath: Path) -> List[Dict[str, str]]:
        """Read CSV file and return list of dictionaries."""
        items = []
        
        try:
            with open(csv_filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    items.append(row)
            
            logger.info(f"Read {len(items)} items from CSV file")
            return items
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def _process_resolved_items(self, resolved_items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Process resolved items and validate URLs."""
        processed_items = []
        
        for item in resolved_items:
            processed_item = self._process_single_item(item)
            processed_items.append(processed_item)
        
        return processed_items
    
    def _process_single_item(self, item: Dict[str, str]) -> Dict[str, Any]:
        """Process a single resolved item."""
        note_id = item.get('note_id', '')
        resolved_url = item.get('resolved_url', '').strip()
        status = item.get('status', 'pending').lower()
        notes = item.get('notes', '').strip()
        
        # Validate resolved URL if provided
        url_validation = self._validate_instagram_url(resolved_url) if resolved_url else {
            'is_valid': False,
            'url_type': 'none',
            'content_id': None
        }
        
        # Determine final status
        if status == 'resolved' and url_validation['is_valid']:
            final_status = 'resolved'
        elif status == 'not_found' or status == 'unresolvable':
            final_status = status
        elif resolved_url and not url_validation['is_valid']:
            final_status = 'invalid_url'
        else:
            final_status = 'pending'
        
        processed_item = {
            'note_id': note_id,
            'original_text': item.get('original_text', ''),
            'account_name': item.get('account_name', ''),
            'mentioned_users': item.get('mentioned_users', ''),
            'content_description': item.get('content_description', ''),
            'suggested_search': item.get('suggested_search', ''),
            'category': item.get('category', ''),
            'confidence': item.get('confidence', ''),
            'status': final_status,
            'resolved_url': resolved_url,
            'notes': notes,
            'url_validation': url_validation,
            'processed_at': datetime.now().isoformat()
        }
        
        return processed_item
    
    def _validate_instagram_url(self, url: str) -> Dict[str, Any]:
        """
        Validate Instagram URL and extract metadata.
        
        Args:
            url: URL to validate
            
        Returns:
            Validation result dictionary
        """
        if not url:
            return {
                'is_valid': False,
                'url_type': 'none',
                'content_id': None,
                'error': 'No URL provided'
            }
        
        # Check if URL matches Instagram patterns
        for pattern in self.compiled_patterns:
            if pattern.match(url):
                # Extract content ID and type
                content_id = self._extract_content_id(url)
                url_type = self._determine_url_type(url)
                
                return {
                    'is_valid': True,
                    'url_type': url_type,
                    'content_id': content_id,
                    'error': None
                }
        
        # Check if it's an Instagram domain but not a valid content URL
        if 'instagram.com' in url.lower():
            return {
                'is_valid': False,
                'url_type': 'profile_or_invalid',
                'content_id': None,
                'error': 'Instagram URL but not a valid content URL'
            }
        
        return {
            'is_valid': False,
            'url_type': 'not_instagram',
            'content_id': None,
            'error': 'Not an Instagram URL'
        }
    
    def _extract_content_id(self, url: str) -> Optional[str]:
        """Extract content ID from Instagram URL."""
        try:
            # Extract ID based on URL type
            if '/p/' in url:
                match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
                return match.group(1) if match else None
            elif '/reel/' in url:
                match = re.search(r'/reel/([A-Za-z0-9_-]+)', url)
                return match.group(1) if match else None
            elif '/tv/' in url:
                match = re.search(r'/tv/([A-Za-z0-9_-]+)', url)
                return match.group(1) if match else None
            elif '/stories/' in url:
                match = re.search(r'/stories/([A-Za-z0-9_.-]+)/([0-9]+)', url)
                return f"{match.group(1)}_{match.group(2)}" if match else None
        except Exception as e:
            logger.error(f"Error extracting content ID from {url}: {e}")
        
        return None
    
    def _determine_url_type(self, url: str) -> str:
        """Determine the type of Instagram content from URL."""
        if '/p/' in url:
            return 'post'
        elif '/reel/' in url:
            return 'reel'
        elif '/tv/' in url:
            return 'tv'
        elif '/stories/' in url:
            return 'story'
        else:
            return 'unknown'
    
    def _generate_import_statistics(self, processed_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics from processed items."""
        total_items = len(processed_items)
        
        # Count by status
        status_counts = {}
        for item in processed_items:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by URL type
        url_type_counts = {}
        for item in processed_items:
            url_type = item['url_validation']['url_type']
            url_type_counts[url_type] = url_type_counts.get(url_type, 0) + 1
        
        # Count resolved URLs
        resolved_urls = [item for item in processed_items if item['status'] == 'resolved']
        valid_urls = [item for item in processed_items if item['url_validation']['is_valid']]
        
        # Calculate success rate
        success_rate = (len(resolved_urls) / total_items * 100) if total_items > 0 else 0
        
        # Count by category
        category_counts = {}
        for item in processed_items:
            category = item['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_items': total_items,
            'status_distribution': status_counts,
            'url_type_distribution': url_type_counts,
            'resolved_items': len(resolved_urls),
            'valid_urls': len(valid_urls),
            'success_rate': success_rate,
            'category_distribution': category_counts,
            'import_timestamp': datetime.now().isoformat()
        }
    
    def _save_processed_results(self, processed_items: List[Dict[str, Any]], 
                              statistics: Dict[str, Any]) -> Path:
        """Save processed results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resolved_content_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Prepare data for saving
        save_data = {
            'import_info': {
                'import_timestamp': datetime.now().isoformat(),
                'total_items': len(processed_items),
                'statistics': statistics
            },
            'resolved_items': processed_items
        }
        
        # Save as JSON
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processed results saved to: {filepath}")
        return filepath
    
    def _create_empty_import_result(self) -> Dict[str, Any]:
        """Create empty import result for error cases."""
        return {
            'success': False,
            'error': 'No data found in CSV file',
            'total_items': 0,
            'processed_items': 0,
            'statistics': {}
        }
    
    def merge_with_direct_urls(self, resolved_items: List[Dict[str, Any]], 
                             direct_url_notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge resolved manual review items with notes that have direct URLs.
        
        Args:
            resolved_items: List of processed resolved items
            direct_url_notes: List of notes with direct Instagram URLs
            
        Returns:
            Combined list of all Instagram content
        """
        logger.info(f"Merging {len(resolved_items)} resolved items with {len(direct_url_notes)} direct URL notes")
        
        combined_items = []
        
        # Add resolved items
        for item in resolved_items:
            if item['status'] == 'resolved' and item['resolved_url']:
                combined_items.append({
                    'note_id': item['note_id'],
                    'url': item['resolved_url'],
                    'url_type': item['url_validation']['url_type'],
                    'content_id': item['url_validation']['content_id'],
                    'source': 'manual_review',
                    'account_name': item['account_name'],
                    'category': item['category'],
                    'confidence': item['confidence'],
                    'original_text': item['original_text']
                })
        
        # Add direct URL notes
        for note in direct_url_notes:
            instagram_urls = note.get('instagram_urls', [])
            for url in instagram_urls:
                # Extract metadata from URL
                url_validation = self._validate_instagram_url(url)
                
                combined_items.append({
                    'note_id': note.get('note_id', ''),
                    'url': url,
                    'url_type': url_validation['url_type'],
                    'content_id': url_validation['content_id'],
                    'source': 'direct_url',
                    'account_name': ', '.join(note.get('instagram_content', {}).get('account_names', [])),
                    'category': note.get('categorization', {}).get('primary_category', ''),
                    'confidence': note.get('categorization', {}).get('confidence_level', ''),
                    'original_text': note.get('body', '')
                })
        
        logger.info(f"Combined {len(combined_items)} total Instagram content items")
        return combined_items
    
    def generate_merge_report(self, combined_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a report on the merged Instagram content."""
        total_items = len(combined_items)
        
        # Count by source
        source_counts = {}
        for item in combined_items:
            source = item['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Count by URL type
        url_type_counts = {}
        for item in combined_items:
            url_type = item['url_type']
            url_type_counts[url_type] = url_type_counts.get(url_type, 0) + 1
        
        # Count by category
        category_counts = {}
        for item in combined_items:
            category = item['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_items': total_items,
            'source_distribution': source_counts,
            'url_type_distribution': url_type_counts,
            'category_distribution': category_counts,
            'merge_timestamp': datetime.now().isoformat()
        }
