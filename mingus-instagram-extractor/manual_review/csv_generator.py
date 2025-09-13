"""
CSV generator for manual review of Instagram content without direct URLs.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class ManualReviewCSVGenerator:
    """Generates CSV files for manual review of Instagram content."""
    
    def __init__(self, output_dir: Path = Path("extracted_content")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        # CSV column headers as specified in requirements
        self.csv_headers = [
            'note_id',
            'original_text',
            'account_name',
            'mentioned_users',
            'content_description',
            'suggested_search',
            'category',
            'confidence',
            'status',
            'resolved_url',
            'notes'
        ]
    
    def generate_manual_review_csv(self, analyzed_notes: List[Dict[str, Any]], 
                                 filename: Optional[str] = None) -> Path:
        """
        Generate CSV file for manual review of Instagram content.
        
        Args:
            analyzed_notes: List of analyzed notes from the extraction pipeline
            filename: Optional custom filename for the CSV
            
        Returns:
            Path to the generated CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manual_review_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        logger.info(f"Generating manual review CSV: {filepath}")
        
        # Filter notes that need manual review (Instagram-related but no direct URLs)
        review_items = self._filter_notes_for_review(analyzed_notes)
        
        if not review_items:
            logger.warning("No notes found that require manual review")
            return self._create_empty_csv(filepath)
        
        # Generate CSV rows
        csv_rows = []
        for item in review_items:
            row = self._create_csv_row(item)
            csv_rows.append(row)
        
        # Write CSV file
        self._write_csv_file(filepath, csv_rows)
        
        logger.info(f"Generated manual review CSV with {len(csv_rows)} items: {filepath}")
        return filepath
    
    def _filter_notes_for_review(self, analyzed_notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter notes that need manual review.
        
        Notes need manual review if they:
        - Are Instagram-related (based on categorization)
        - Don't have direct Instagram URLs
        - Have rich text content with account names, mentions, or hashtags
        """
        review_items = []
        
        for note in analyzed_notes:
            # Check if note is Instagram-related
            is_instagram_related = note.get('categorization', {}).get('is_instagram_related', False)
            if not is_instagram_related:
                continue
            
            # Check if note has direct Instagram URLs
            has_direct_urls = bool(note.get('instagram_urls', []))
            if has_direct_urls:
                continue  # Skip notes with direct URLs
            
            # Check if note has rich text metadata that could be resolved
            instagram_content = note.get('instagram_content', {})
            has_rich_metadata = any([
                instagram_content.get('account_names'),
                instagram_content.get('usernames'),
                instagram_content.get('hashtags'),
                instagram_content.get('mentions')
            ])
            
            if not has_rich_metadata:
                continue  # Skip notes without rich metadata
            
            # This note needs manual review
            review_items.append(note)
        
        return review_items
    
    def _create_csv_row(self, note: Dict[str, Any]) -> Dict[str, str]:
        """
        Create a CSV row for a note that needs manual review.
        
        Args:
            note: Note dictionary with all extracted data
            
        Returns:
            Dictionary representing a CSV row
        """
        # Extract basic information
        note_id = str(note.get('note_id', ''))
        original_text = note.get('body', '').replace('\n', ' ').replace('\r', ' ').strip()
        
        # Extract Instagram content metadata
        instagram_content = note.get('instagram_content', {})
        account_names = instagram_content.get('account_names', [])
        usernames = instagram_content.get('usernames', [])
        hashtags = instagram_content.get('hashtags', [])
        mentions = instagram_content.get('mentions', [])
        
        # Create account name (primary account or first username)
        account_name = ''
        if account_names:
            account_name = account_names[0]
        elif usernames:
            account_name = usernames[0]
        
        # Create mentioned users list
        mentioned_users = ', '.join(set(usernames + mentions))
        
        # Create content description
        content_description = self._generate_content_description(original_text, account_names, hashtags)
        
        # Generate search suggestions
        suggested_search = self._generate_search_suggestions(account_name, usernames, hashtags, original_text)
        
        # Get categorization info
        categorization = note.get('categorization', {})
        category = categorization.get('primary_category', 'uncategorized')
        confidence = categorization.get('confidence_level', 'very_low')
        
        # Create CSV row
        row = {
            'note_id': note_id,
            'original_text': original_text[:500],  # Limit length for CSV readability
            'account_name': account_name,
            'mentioned_users': mentioned_users,
            'content_description': content_description,
            'suggested_search': suggested_search,
            'category': category,
            'confidence': confidence,
            'status': 'pending',  # Default status
            'resolved_url': '',  # Empty initially
            'notes': ''  # Empty initially
        }
        
        return row
    
    def _generate_content_description(self, original_text: str, account_names: List[str], 
                                   hashtags: List[str]) -> str:
        """Generate a brief description of the content for manual review."""
        description_parts = []
        
        # Add account context
        if account_names:
            description_parts.append(f"Account: {', '.join(account_names[:3])}")
        
        # Add hashtag context
        if hashtags:
            description_parts.append(f"Hashtags: {', '.join(hashtags[:5])}")
        
        # Add text snippet (first 100 characters)
        if original_text:
            text_snippet = original_text[:100].replace('\n', ' ')
            if len(original_text) > 100:
                text_snippet += "..."
            description_parts.append(f"Text: {text_snippet}")
        
        return " | ".join(description_parts)
    
    def _generate_search_suggestions(self, account_name: str, usernames: List[str], 
                                   hashtags: List[str], original_text: str) -> str:
        """Generate search suggestions for manual resolution."""
        suggestions = []
        
        # Instagram profile searches
        if account_name:
            suggestions.append(f"https://instagram.com/{account_name}")
        
        for username in usernames[:3]:  # Limit to first 3 usernames
            if username != account_name:  # Avoid duplicates
                suggestions.append(f"https://instagram.com/{username}")
        
        # Hashtag searches
        for hashtag in hashtags[:3]:  # Limit to first 3 hashtags
            clean_hashtag = hashtag.lstrip('#')
            suggestions.append(f"https://instagram.com/explore/tags/{clean_hashtag}")
        
        # Google search alternatives
        if account_name:
            google_query = f"site:instagram.com {account_name}"
            suggestions.append(f"https://www.google.com/search?q={quote_plus(google_query)}")
        
        # Keyword-based searches
        keywords = self._extract_keywords(original_text)
        for keyword in keywords[:2]:  # Limit to first 2 keywords
            google_query = f"site:instagram.com {keyword}"
            suggestions.append(f"https://www.google.com/search?q={quote_plus(google_query)}")
        
        return " | ".join(suggestions[:5])  # Limit to 5 suggestions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text for search suggestions."""
        if not text:
            return []
        
        # Simple keyword extraction (can be enhanced)
        words = text.lower().split()
        
        # Filter out common words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        keywords = []
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) > 3 and clean_word not in stop_words:
                keywords.append(clean_word)
        
        # Return unique keywords, limited to 10
        return list(set(keywords))[:10]
    
    def _write_csv_file(self, filepath: Path, rows: List[Dict[str, str]]) -> None:
        """Write CSV file with the specified rows."""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"Successfully wrote {len(rows)} rows to {filepath}")
            
        except Exception as e:
            logger.error(f"Error writing CSV file {filepath}: {e}")
            raise
    
    def _create_empty_csv(self, filepath: Path) -> Path:
        """Create an empty CSV file with headers only."""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
            
            logger.info(f"Created empty CSV file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating empty CSV file {filepath}: {e}")
            raise
    
    def get_review_statistics(self, analyzed_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics about notes that need manual review.
        
        Args:
            analyzed_notes: List of analyzed notes
            
        Returns:
            Dictionary with review statistics
        """
        total_notes = len(analyzed_notes)
        instagram_notes = sum(1 for note in analyzed_notes 
                            if note.get('categorization', {}).get('is_instagram_related', False))
        
        notes_with_direct_urls = sum(1 for note in analyzed_notes 
                                   if note.get('instagram_urls', []))
        
        review_items = self._filter_notes_for_review(analyzed_notes)
        notes_needing_review = len(review_items)
        
        # Categorize review items by type
        review_by_category = {}
        for item in review_items:
            category = item.get('categorization', {}).get('primary_category', 'uncategorized')
            review_by_category[category] = review_by_category.get(category, 0) + 1
        
        # Count items with different types of metadata
        items_with_accounts = sum(1 for item in review_items 
                                if item.get('instagram_content', {}).get('account_names'))
        items_with_hashtags = sum(1 for item in review_items 
                                if item.get('instagram_content', {}).get('hashtags'))
        items_with_mentions = sum(1 for item in review_items 
                                if item.get('instagram_content', {}).get('usernames'))
        
        return {
            'total_notes': total_notes,
            'instagram_related_notes': instagram_notes,
            'notes_with_direct_urls': notes_with_direct_urls,
            'notes_needing_manual_review': notes_needing_review,
            'review_percentage': (notes_needing_review / total_notes * 100) if total_notes > 0 else 0,
            'review_by_category': review_by_category,
            'items_with_accounts': items_with_accounts,
            'items_with_hashtags': items_with_hashtags,
            'items_with_mentions': items_with_mentions,
            'estimated_review_time_minutes': notes_needing_review * 2.5  # 2.5 minutes per item
        }
