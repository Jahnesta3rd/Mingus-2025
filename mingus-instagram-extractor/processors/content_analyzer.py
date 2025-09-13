"""
Content analyzer for URL vs rich text detection in Instagram content.
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
from config import INSTAGRAM_URL_PATTERNS

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes content to detect URLs, Instagram links, and rich text formatting."""
    
    def __init__(self):
        self.instagram_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in INSTAGRAM_URL_PATTERNS]
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            re.IGNORECASE
        )
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to detect URLs, Instagram links, and formatting.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Analysis results dictionary
        """
        if not content:
            return self._empty_analysis()
        
        analysis = {
            'has_urls': False,
            'urls': [],
            'instagram_urls': [],
            'instagram_posts': [],
            'instagram_reels': [],
            'instagram_tv': [],
            'instagram_stories': [],
            'is_rich_text': False,
            'has_formatting': False,
            'word_count': len(content.split()),
            'char_count': len(content),
            'line_count': len(content.splitlines())
        }
        
        # Detect URLs
        urls = self._extract_urls(content)
        if urls:
            analysis['has_urls'] = True
            analysis['urls'] = urls
            
            # Categorize Instagram URLs
            instagram_urls = self._categorize_instagram_urls(urls)
            analysis.update(instagram_urls)
        
        # Detect rich text formatting
        analysis['is_rich_text'] = self._is_rich_text(content)
        analysis['has_formatting'] = self._has_formatting(content)
        
        return analysis
    
    def analyze_notes(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze a list of notes for content patterns (enhanced for new data structure).
        
        Args:
            notes: List of note dictionaries with binary decoding and categorization
            
        Returns:
            List of notes with additional analysis results
        """
        logger.info(f"Analyzing content in {len(notes)} notes")
        
        analyzed_notes = []
        for note in notes:
            content = note.get('body', '')
            analysis = self.analyze_content(content)
            
            # Add analysis to note (preserve existing structure)
            note_with_analysis = note.copy()
            note_with_analysis['url_analysis'] = analysis
            
            # Add Instagram URL metadata if found
            if analysis.get('instagram_urls'):
                note_with_analysis['instagram_url_metadata'] = []
                for url in analysis['instagram_urls']:
                    metadata = self.extract_instagram_metadata(url)
                    note_with_analysis['instagram_url_metadata'].append(metadata)
            
            analyzed_notes.append(note_with_analysis)
        
        logger.info(f"Completed analysis of {len(analyzed_notes)} notes")
        return analyzed_notes
    
    def get_instagram_summary(self, analyzed_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of Instagram content found in notes.
        
        Args:
            analyzed_notes: List of analyzed notes with binary decoding and categorization
            
        Returns:
            Instagram content summary
        """
        total_notes = len(analyzed_notes)
        notes_with_instagram = 0
        total_instagram_urls = 0
        instagram_by_type = {
            'posts': 0,
            'reels': 0,
            'tv': 0,
            'stories': 0
        }
        
        all_instagram_urls = []
        rich_text_metadata = {
            'account_names': [],
            'usernames': [],
            'hashtags': [],
            'mentions': []
        }
        
        for note in analyzed_notes:
            # Check for Instagram URLs from binary decoding
            instagram_urls = note.get('instagram_urls', [])
            if instagram_urls:
                notes_with_instagram += 1
                total_instagram_urls += len(instagram_urls)
                all_instagram_urls.extend(instagram_urls)
                
                # Count by type
                for url in instagram_urls:
                    if '/p/' in url:
                        instagram_by_type['posts'] += 1
                    elif '/reel/' in url:
                        instagram_by_type['reels'] += 1
                    elif '/tv/' in url:
                        instagram_by_type['tv'] += 1
                    elif '/stories/' in url:
                        instagram_by_type['stories'] += 1
            
            # Check for Instagram-related content from categorization
            if note.get('categorization', {}).get('is_instagram_related', False):
                if not instagram_urls:  # Don't double count
                    notes_with_instagram += 1
                
                # Collect rich text metadata
                instagram_content = note.get('instagram_content', {})
                rich_text_metadata['account_names'].extend(instagram_content.get('account_names', []))
                rich_text_metadata['usernames'].extend(instagram_content.get('usernames', []))
                rich_text_metadata['hashtags'].extend(instagram_content.get('hashtags', []))
                rich_text_metadata['mentions'].extend(instagram_content.get('mentions', []))
        
        # Remove duplicates and count unique items
        unique_accounts = list(set(rich_text_metadata['account_names']))
        unique_usernames = list(set(rich_text_metadata['usernames']))
        unique_hashtags = list(set(rich_text_metadata['hashtags']))
        unique_mentions = list(set(rich_text_metadata['mentions']))
        
        return {
            'total_notes': total_notes,
            'notes_with_instagram': notes_with_instagram,
            'total_instagram_urls': total_instagram_urls,
            'instagram_by_type': instagram_by_type,
            'all_instagram_urls': all_instagram_urls,
            'unique_instagram_urls': list(set(all_instagram_urls)),
            'instagram_percentage': (notes_with_instagram / total_notes * 100) if total_notes > 0 else 0,
            'rich_text_metadata': {
                'unique_accounts': unique_accounts,
                'unique_usernames': unique_usernames,
                'unique_hashtags': unique_hashtags,
                'unique_mentions': unique_mentions,
                'total_accounts': len(unique_accounts),
                'total_usernames': len(unique_usernames),
                'total_hashtags': len(unique_hashtags),
                'total_mentions': len(unique_mentions)
            }
        }
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extract all URLs from content."""
        urls = self.url_pattern.findall(content)
        return [url.strip() for url in urls if url.strip()]
    
    def _categorize_instagram_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Categorize URLs into Instagram content types."""
        result = {
            'instagram_urls': [],
            'instagram_posts': [],
            'instagram_reels': [],
            'instagram_tv': [],
            'instagram_stories': []
        }
        
        for url in urls:
            if 'instagram.com' in url.lower():
                result['instagram_urls'].append(url)
                
                # Categorize by Instagram content type
                if '/p/' in url:
                    result['instagram_posts'].append(url)
                elif '/reel/' in url:
                    result['instagram_reels'].append(url)
                elif '/tv/' in url:
                    result['instagram_tv'].append(url)
                elif '/stories/' in url:
                    result['instagram_stories'].append(url)
        
        return result
    
    def _is_rich_text(self, content: str) -> bool:
        """Check if content contains rich text HTML formatting."""
        if not content:
            return False
        
        html_tags = [
            '<html>', '<body>', '<p>', '<div>', '<span>',
            '<b>', '<i>', '<u>', '<strong>', '<em>',
            '<h1>', '<h2>', '<h3>', '<h4>', '<h5>', '<h6>',
            '<ul>', '<ol>', '<li>', '<br>', '<hr>'
        ]
        
        content_lower = content.lower()
        return any(tag in content_lower for tag in html_tags)
    
    def _has_formatting(self, content: str) -> bool:
        """Check if content has any formatting indicators."""
        if not content:
            return False
        
        formatting_indicators = [
            '\n', '\t', '  ',  # Whitespace formatting
            '*', '_', '~',     # Markdown-style formatting
            '&lt;', '&gt;',    # HTML entities
            '&amp;', '&quot;', '&#'
        ]
        
        return any(indicator in content for indicator in formatting_indicators)
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis for empty content."""
        return {
            'has_urls': False,
            'urls': [],
            'instagram_urls': [],
            'instagram_posts': [],
            'instagram_reels': [],
            'instagram_tv': [],
            'instagram_stories': [],
            'is_rich_text': False,
            'has_formatting': False,
            'word_count': 0,
            'char_count': 0,
            'line_count': 0
        }
    
    def extract_instagram_metadata(self, instagram_url: str) -> Dict[str, Any]:
        """
        Extract metadata from Instagram URL.
        
        Args:
            instagram_url: Instagram URL to analyze
            
        Returns:
            Metadata dictionary
        """
        try:
            parsed = urlparse(instagram_url)
            
            metadata = {
                'url': instagram_url,
                'domain': parsed.netloc,
                'path': parsed.path,
                'query': parsed.query,
                'content_type': 'unknown',
                'content_id': None
            }
            
            # Determine content type and extract ID
            if '/p/' in instagram_url:
                metadata['content_type'] = 'post'
                match = re.search(r'/p/([A-Za-z0-9_-]+)', instagram_url)
                if match:
                    metadata['content_id'] = match.group(1)
            elif '/reel/' in instagram_url:
                metadata['content_type'] = 'reel'
                match = re.search(r'/reel/([A-Za-z0-9_-]+)', instagram_url)
                if match:
                    metadata['content_id'] = match.group(1)
            elif '/tv/' in instagram_url:
                metadata['content_type'] = 'tv'
                match = re.search(r'/tv/([A-Za-z0-9_-]+)', instagram_url)
                if match:
                    metadata['content_id'] = match.group(1)
            elif '/stories/' in instagram_url:
                metadata['content_type'] = 'story'
                match = re.search(r'/stories/([A-Za-z0-9_.-]+)/([0-9]+)', instagram_url)
                if match:
                    metadata['content_id'] = f"{match.group(1)}_{match.group(2)}"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from URL {instagram_url}: {e}")
            return {
                'url': instagram_url,
                'error': str(e)
            }
