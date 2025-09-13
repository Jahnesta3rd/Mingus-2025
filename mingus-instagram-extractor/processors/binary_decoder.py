"""
Binary content decoder for handling Mac Notes ZDATA field.
"""

import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BinaryContentDecoder:
    """Decodes binary content from Mac Notes ZDATA field."""
    
    def __init__(self):
        self.encoding_methods = ['utf-8', 'utf-16', 'latin1', 'cp1252', 'iso-8859-1']
        self.instagram_url_patterns = [
            r'https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?',
            r'https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?',
            r'https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?',
            r'https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.-]+/[0-9]+/?',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.instagram_url_patterns]
    
    def decode_binary_content(self, binary_data: bytes) -> Dict[str, Any]:
        """
        Decode binary content using multiple encoding methods.
        
        Args:
            binary_data: Raw binary data from ZDATA field
            
        Returns:
            Dict containing decoded content and metadata
        """
        result = {
            'success': False,
            'content': '',
            'encoding_used': None,
            'instagram_urls': [],
            'all_urls': [],
            'clean_text': '',
            'error': None,
            'confidence_score': 0.0
        }
        
        if not binary_data:
            result['error'] = 'No binary data provided'
            return result
        
        # Try different encoding methods
        best_result = None
        best_score = 0.0
        
        for encoding in self.encoding_methods:
            try:
                decoded_content = binary_data.decode(encoding)
                score = self._calculate_confidence_score(decoded_content)
                
                if score > best_score:
                    best_score = score
                    best_result = {
                        'content': decoded_content,
                        'encoding': encoding,
                        'score': score
                    }
                    
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.debug(f"Failed to decode with {encoding}: {e}")
                continue
        
        if best_result:
            result['success'] = True
            result['content'] = best_result['content']
            result['encoding_used'] = best_result['encoding']
            result['confidence_score'] = best_result['score']
            
            # Clean and extract content
            cleaned_content = self._clean_binary_artifacts(best_result['content'])
            result['clean_text'] = cleaned_content
            
            # Extract URLs
            urls = self._extract_urls(cleaned_content)
            result['all_urls'] = urls
            result['instagram_urls'] = self._filter_instagram_urls(urls)
            
            logger.info(f"Successfully decoded content using {best_result['encoding']} (confidence: {best_result['score']:.2f})")
        else:
            result['error'] = 'Failed to decode with any encoding method'
            logger.error("Failed to decode binary content with any encoding method")
        
        return result
    
    def _calculate_confidence_score(self, content: str) -> float:
        """
        Calculate confidence score for decoded content.
        
        Args:
            content: Decoded text content
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not content:
            return 0.0
        
        score = 0.0
        
        # Check for readable characters
        readable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        total_chars = len(content)
        if total_chars > 0:
            score += (readable_chars / total_chars) * 0.4
        
        # Check for common text patterns
        if re.search(r'[a-zA-Z]{3,}', content):  # Words with 3+ letters
            score += 0.2
        
        # Check for URLs
        if re.search(r'https?://', content):
            score += 0.2
        
        # Check for Instagram patterns
        if any(pattern.search(content) for pattern in self.compiled_patterns):
            score += 0.1
        
        # Check for common punctuation
        if re.search(r'[.!?]', content):
            score += 0.05
        
        # Check for spaces (indicates word separation)
        if ' ' in content:
            score += 0.05
        
        return min(score, 1.0)
    
    def _clean_binary_artifacts(self, content: str) -> str:
        """
        Clean binary artifacts from decoded content.
        
        Args:
            content: Raw decoded content
            
        Returns:
            Cleaned content string
        """
        if not content:
            return content
        
        # Remove null bytes and control characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove common binary artifacts
        cleaned = re.sub(r'[\x80-\xFF]+', '', cleaned)
        
        # Clean up URLs that might have artifacts
        cleaned = re.sub(r'https?://[^\s\x00-\x1F\x7F]+', 
                        lambda m: self._clean_url(m.group(0)), cleaned)
        
        return cleaned.strip()
    
    def _clean_url(self, url: str) -> str:
        """
        Clean a URL by removing binary artifacts.
        
        Args:
            url: Raw URL string
            
        Returns:
            Cleaned URL string
        """
        # Remove non-printable characters from URL
        cleaned = re.sub(r'[^\x20-\x7E]', '', url)
        
        # Ensure URL ends properly
        if cleaned.endswith(('?', '&', '/')):
            return cleaned
        elif '?' in cleaned or '#' in cleaned:
            return cleaned
        else:
            return cleaned.rstrip('/')
    
    def _extract_urls(self, content: str) -> List[str]:
        """
        Extract all URLs from content.
        
        Args:
            content: Text content to search
            
        Returns:
            List of found URLs
        """
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            re.IGNORECASE
        )
        
        urls = url_pattern.findall(content)
        return [url.strip() for url in urls if url.strip()]
    
    def _filter_instagram_urls(self, urls: List[str]) -> List[str]:
        """
        Filter URLs to find Instagram links.
        
        Args:
            urls: List of all URLs found
            
        Returns:
            List of Instagram URLs
        """
        instagram_urls = []
        
        for url in urls:
            if 'instagram.com' in url.lower():
                # Validate with compiled patterns
                for pattern in self.compiled_patterns:
                    if pattern.search(url):
                        instagram_urls.append(url)
                        break
        
        return instagram_urls
    
    def extract_rich_text_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from rich text content.
        
        Args:
            content: Decoded text content
            
        Returns:
            Dict containing rich text metadata
        """
        metadata = {
            'account_names': [],
            'usernames': [],
            'hashtags': [],
            'mentions': [],
            'content_type': 'unknown',
            'description': '',
            'search_suggestions': []
        }
        
        if not content:
            return metadata
        
        # Extract account names from "[Account] on Instagram:" pattern
        account_pattern = r'\[([^\]]+)\]\s*on\s*Instagram:?'
        account_matches = re.findall(account_pattern, content, re.IGNORECASE)
        metadata['account_names'] = [match.strip() for match in account_matches]
        
        # Extract @username mentions
        username_pattern = r'@([a-zA-Z0-9_.]+)'
        username_matches = re.findall(username_pattern, content)
        metadata['usernames'] = username_matches
        
        # Extract hashtags
        hashtag_pattern = r'#([a-zA-Z0-9_]+)'
        hashtag_matches = re.findall(hashtag_pattern, content)
        metadata['hashtags'] = hashtag_matches
        
        # Extract general mentions (words that might be usernames)
        mention_pattern = r'\b([a-zA-Z][a-zA-Z0-9_.]{2,})\b'
        mention_matches = re.findall(mention_pattern, content)
        metadata['mentions'] = list(set(mention_matches) - set(metadata['usernames']))
        
        # Determine content type
        metadata['content_type'] = self._determine_content_type(content)
        
        # Extract description (first sentence or line)
        description_match = re.search(r'^([^.!?]+[.!?])', content.strip())
        if description_match:
            metadata['description'] = description_match.group(1).strip()
        else:
            # Fallback to first line
            first_line = content.split('\n')[0].strip()
            metadata['description'] = first_line[:100] + '...' if len(first_line) > 100 else first_line
        
        # Generate search suggestions
        metadata['search_suggestions'] = self._generate_search_suggestions(metadata)
        
        return metadata
    
    def _determine_content_type(self, content: str) -> str:
        """
        Determine the type of content based on patterns.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Content type string
        """
        content_lower = content.lower()
        
        if any(pattern.search(content) for pattern in self.compiled_patterns):
            return 'instagram_url'
        elif '[account] on instagram' in content_lower:
            return 'instagram_preview'
        elif '@' in content and 'instagram' in content_lower:
            return 'instagram_mention'
        elif '#' in content and 'instagram' in content_lower:
            return 'instagram_hashtag'
        elif 'instagram' in content_lower:
            return 'instagram_related'
        else:
            return 'general_content'
    
    def _generate_search_suggestions(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Generate search suggestions for manual resolution.
        
        Args:
            metadata: Rich text metadata
            
        Returns:
            List of search suggestions
        """
        suggestions = []
        
        # Add account names as search suggestions
        for account in metadata['account_names']:
            suggestions.append(f"Search for: {account}")
        
        # Add usernames as search suggestions
        for username in metadata['usernames']:
            suggestions.append(f"Check @{username}")
        
        # Add hashtag suggestions
        for hashtag in metadata['hashtags']:
            suggestions.append(f"Explore #{hashtag}")
        
        # Add general content suggestions
        if metadata['description']:
            suggestions.append(f"Content: {metadata['description'][:50]}...")
        
        return suggestions[:10]  # Limit to 10 suggestions
