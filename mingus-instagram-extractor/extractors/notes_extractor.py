"""
Notes extractor for content extraction from MINGUS folder with binary decoding.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from config import OUTPUT_DIR
from processors.binary_decoder import BinaryContentDecoder
from processors.content_categorizer import ContentCategorizer

logger = logging.getLogger(__name__)


class NotesExtractor:
    """Extracts and processes notes from the MINGUS folder with binary decoding and categorization."""
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.binary_decoder = BinaryContentDecoder()
        self.content_categorizer = ContentCategorizer()
    
    def extract_note_content(self, note: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and process content from a single note with binary decoding and categorization.
        
        Args:
            note: Note record from database
            
        Returns:
            Processed note content with binary decoding and categorization
        """
        try:
            # Convert timestamps to readable format
            creation_date = self._convert_timestamp(note.get('creation_date', 0))
            modification_date = self._convert_timestamp(note.get('modification_date', 0))
            
            # Extract basic content
            title = note.get('title', '') or 'Untitled'
            body_text = note.get('body_text', '') or ''
            binary_data = note.get('content_data')
            
            # Initialize result structure
            processed_content = {
                'note_id': note.get('note_id'),
                'title': title.strip(),
                'creation_date': creation_date,
                'modification_date': modification_date,
                'extracted_at': datetime.now().isoformat(),
                'binary_decoding': {},
                'content_analysis': {},
                'categorization': {},
                'instagram_content': {},
                'processing_stats': {}
            }
            
            # Process binary content if available
            if binary_data:
                logger.debug(f"Decoding binary content for note: {title[:50]}...")
                binary_result = self.binary_decoder.decode_binary_content(binary_data)
                processed_content['binary_decoding'] = binary_result
                
                # Use decoded content if successful
                if binary_result['success']:
                    content = binary_result['clean_text']
                    processed_content['body'] = content
                    processed_content['instagram_urls'] = binary_result['instagram_urls']
                    processed_content['all_urls'] = binary_result['all_urls']
                else:
                    content = body_text
                    processed_content['body'] = content
                    processed_content['binary_decoding_error'] = binary_result['error']
            else:
                content = body_text
                processed_content['body'] = content
                processed_content['binary_decoding'] = {'success': False, 'error': 'No binary data available'}
            
            # Analyze content characteristics
            processed_content['content_analysis'] = {
                'word_count': len(content.split()) if content else 0,
                'char_count': len(content) if content else 0,
                'has_content': bool(content.strip()),
                'is_rich_text': self._is_rich_text(content),
                'encoding_used': processed_content['binary_decoding'].get('encoding_used'),
                'confidence_score': processed_content['binary_decoding'].get('confidence_score', 0.0)
            }
            
            # Categorize content
            if content:
                logger.debug(f"Categorizing content for note: {title[:50]}...")
                categorization = self.content_categorizer.categorize_content(content, title)
                processed_content['categorization'] = categorization
                
                # Extract rich text metadata if it's Instagram-related
                if categorization.get('is_instagram_related', False):
                    rich_text_metadata = self.binary_decoder.extract_rich_text_metadata(content)
                    processed_content['instagram_content'] = rich_text_metadata
                else:
                    processed_content['instagram_content'] = {
                        'account_names': [],
                        'usernames': [],
                        'hashtags': [],
                        'mentions': [],
                        'content_type': 'not_instagram_related',
                        'description': '',
                        'search_suggestions': []
                    }
            
            # Generate processing statistics
            processed_content['processing_stats'] = {
                'binary_decoded': processed_content['binary_decoding'].get('success', False),
                'instagram_urls_found': len(processed_content.get('instagram_urls', [])),
                'total_urls_found': len(processed_content.get('all_urls', [])),
                'category_assigned': processed_content['categorization'].get('primary_category', 'uncategorized'),
                'confidence_level': processed_content['categorization'].get('confidence_level', 'very_low'),
                'rich_text_metadata_extracted': bool(processed_content['instagram_content'].get('account_names'))
            }
            
            logger.debug(f"Successfully processed note: {title[:50]}... (Category: {processed_content['categorization'].get('primary_category', 'uncategorized')})")
            return processed_content
            
        except Exception as e:
            logger.error(f"Error extracting content from note {note.get('note_id', 'unknown')}: {e}")
            return {
                'note_id': note.get('note_id'),
                'title': 'Error',
                'body': '',
                'error': str(e),
                'extracted_at': datetime.now().isoformat(),
                'binary_decoding': {'success': False, 'error': str(e)},
                'content_analysis': {'word_count': 0, 'char_count': 0, 'has_content': False},
                'categorization': {'primary_category': 'error', 'confidence_level': 'very_low'},
                'instagram_content': {},
                'processing_stats': {'binary_decoded': False, 'error': True}
            }
    
    def extract_all_notes(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract content from all notes in the MINGUS folder.
        
        Args:
            notes: List of note records from database
            
        Returns:
            List of processed note content
        """
        logger.info(f"Extracting content from {len(notes)} notes")
        
        extracted_notes = []
        for i, note in enumerate(notes, 1):
            logger.info(f"Processing note {i}/{len(notes)}")
            processed_note = self.extract_note_content(note)
            extracted_notes.append(processed_note)
        
        logger.info(f"Successfully extracted {len(extracted_notes)} notes")
        return extracted_notes
    
    def save_extracted_content(self, extracted_notes: List[Dict[str, Any]], 
                             folder_info: Dict[str, Any]) -> Path:
        """
        Save extracted content to files.
        
        Args:
            extracted_notes: List of processed notes
            folder_info: Information about the MINGUS folder
            
        Returns:
            Path to the saved content file
        """
        try:
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mingus_notes_{timestamp}.json"
            filepath = self.output_dir / filename
            
            # Prepare data for saving
            save_data = {
                'extraction_info': {
                    'folder_name': folder_info.get('title', 'MINGUS'),
                    'folder_id': folder_info.get('folder_id'),
                    'total_notes': len(extracted_notes),
                    'extraction_date': datetime.now().isoformat()
                },
                'notes': extracted_notes
            }
            
            # Save as JSON
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Extracted content saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving extracted content: {e}")
            raise
    
    def _convert_timestamp(self, timestamp: float) -> str:
        """
        Convert Core Data timestamp to readable date string.
        
        Args:
            timestamp: Core Data timestamp (seconds since 2001-01-01)
            
        Returns:
            Formatted date string
        """
        try:
            # Core Data timestamps are seconds since 2001-01-01
            # Convert to Unix timestamp by adding 978307200 seconds
            unix_timestamp = timestamp + 978307200
            dt = datetime.fromtimestamp(unix_timestamp)
            return dt.isoformat()
        except (ValueError, OSError):
            return "Unknown date"
    
    def _is_rich_text(self, content: str) -> bool:
        """
        Determine if content contains rich text formatting.
        
        Args:
            content: Text content to analyze
            
        Returns:
            True if content appears to be rich text
        """
        if not content:
            return False
        
        # Check for common rich text indicators
        rich_text_indicators = [
            '<html>', '<body>', '<p>', '<div>', '<span>',
            '<b>', '<i>', '<u>', '<strong>', '<em>',
            '&lt;', '&gt;', '&amp;', '&quot;', '&#'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in rich_text_indicators)
    
    def get_extraction_summary(self, extracted_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the extraction process.
        
        Args:
            extracted_notes: List of processed notes
            
        Returns:
            Summary statistics including binary decoding and categorization
        """
        total_notes = len(extracted_notes)
        
        # Basic content statistics
        notes_with_content = sum(1 for note in extracted_notes if note.get('content_analysis', {}).get('has_content', False))
        rich_text_notes = sum(1 for note in extracted_notes if note.get('content_analysis', {}).get('is_rich_text', False))
        total_words = sum(note.get('content_analysis', {}).get('word_count', 0) for note in extracted_notes)
        total_chars = sum(note.get('content_analysis', {}).get('char_count', 0) for note in extracted_notes)
        
        # Binary decoding statistics
        binary_decoded_notes = sum(1 for note in extracted_notes if note.get('binary_decoding', {}).get('success', False))
        encoding_stats = {}
        for note in extracted_notes:
            encoding = note.get('binary_decoding', {}).get('encoding_used')
            if encoding:
                encoding_stats[encoding] = encoding_stats.get(encoding, 0) + 1
        
        # Instagram content statistics
        instagram_notes = sum(1 for note in extracted_notes if note.get('categorization', {}).get('is_instagram_related', False))
        instagram_urls = sum(len(note.get('instagram_urls', [])) for note in extracted_notes)
        total_urls = sum(len(note.get('all_urls', [])) for note in extracted_notes)
        
        # Category statistics
        category_counts = {}
        confidence_counts = {}
        for note in extracted_notes:
            cat = note.get('categorization', {}).get('primary_category', 'uncategorized')
            confidence = note.get('categorization', {}).get('confidence_level', 'very_low')
            
            category_counts[cat] = category_counts.get(cat, 0) + 1
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        # Rich text metadata statistics
        notes_with_accounts = sum(1 for note in extracted_notes if note.get('instagram_content', {}).get('account_names'))
        notes_with_hashtags = sum(1 for note in extracted_notes if note.get('instagram_content', {}).get('hashtags'))
        notes_with_mentions = sum(1 for note in extracted_notes if note.get('instagram_content', {}).get('usernames'))
        
        return {
            'total_notes': total_notes,
            'notes_with_content': notes_with_content,
            'empty_notes': total_notes - notes_with_content,
            'rich_text_notes': rich_text_notes,
            'plain_text_notes': notes_with_content - rich_text_notes,
            'total_words': total_words,
            'total_characters': total_chars,
            'average_words_per_note': total_words / total_notes if total_notes > 0 else 0,
            'average_chars_per_note': total_chars / total_notes if total_notes > 0 else 0,
            'binary_decoding': {
                'successful_decodes': binary_decoded_notes,
                'success_rate': (binary_decoded_notes / total_notes * 100) if total_notes > 0 else 0,
                'encoding_usage': encoding_stats
            },
            'instagram_content': {
                'instagram_related_notes': instagram_notes,
                'instagram_urls_found': instagram_urls,
                'total_urls_found': total_urls,
                'notes_with_accounts': notes_with_accounts,
                'notes_with_hashtags': notes_with_hashtags,
                'notes_with_mentions': notes_with_mentions
            },
            'categorization': {
                'category_distribution': category_counts,
                'confidence_distribution': confidence_counts,
                'most_common_category': max(category_counts.items(), key=lambda x: x[1]) if category_counts else None
            }
        }
