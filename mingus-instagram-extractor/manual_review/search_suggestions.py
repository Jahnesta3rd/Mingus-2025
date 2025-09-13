"""
Advanced search suggestion generator for manual Instagram content resolution.
"""

import re
import logging
from typing import List, Dict, Any, Set
from urllib.parse import quote_plus
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SearchSuggestionGenerator:
    """Generates comprehensive search suggestions for manual Instagram content resolution."""
    
    def __init__(self):
        self.instagram_base_url = "https://instagram.com"
        self.google_base_url = "https://www.google.com/search"
        
        # Common Instagram content patterns
        self.content_patterns = {
            'sketch': ['sketch', 'drawing', 'art', 'illustration', 'comic'],
            'comedy': ['comedy', 'funny', 'joke', 'humor', 'laugh'],
            'dance': ['dance', 'dancing', 'choreography', 'moves'],
            'music': ['music', 'song', 'beat', 'melody', 'lyrics'],
            'fashion': ['fashion', 'outfit', 'style', 'clothes', 'dress'],
            'food': ['food', 'recipe', 'cooking', 'meal', 'restaurant'],
            'travel': ['travel', 'trip', 'vacation', 'destination', 'place'],
            'fitness': ['fitness', 'workout', 'exercise', 'gym', 'training'],
            'beauty': ['beauty', 'makeup', 'skincare', 'cosmetics', 'glam'],
            'lifestyle': ['lifestyle', 'daily', 'routine', 'life', 'living']
        }
    
    def generate_comprehensive_suggestions(self, note_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate comprehensive search suggestions for a note.
        
        Args:
            note_data: Note data with Instagram content metadata
            
        Returns:
            Dictionary with different types of search suggestions
        """
        suggestions = {
            'instagram_profiles': [],
            'instagram_hashtags': [],
            'google_searches': [],
            'time_based_searches': [],
            'keyword_searches': [],
            'alternative_searches': []
        }
        
        # Extract data from note
        instagram_content = note_data.get('instagram_content', {})
        original_text = note_data.get('body', '')
        account_names = instagram_content.get('account_names', [])
        usernames = instagram_content.get('usernames', [])
        hashtags = instagram_content.get('hashtags', [])
        mentions = instagram_content.get('mentions', [])
        
        # Generate Instagram profile searches
        suggestions['instagram_profiles'] = self._generate_instagram_profile_searches(
            account_names, usernames, mentions
        )
        
        # Generate hashtag searches
        suggestions['instagram_hashtags'] = self._generate_hashtag_searches(hashtags)
        
        # Generate Google searches
        suggestions['google_searches'] = self._generate_google_searches(
            account_names, usernames, hashtags, original_text
        )
        
        # Generate time-based searches
        suggestions['time_based_searches'] = self._generate_time_based_searches(
            account_names, usernames, hashtags, original_text
        )
        
        # Generate keyword-based searches
        suggestions['keyword_searches'] = self._generate_keyword_searches(original_text)
        
        # Generate alternative searches
        suggestions['alternative_searches'] = self._generate_alternative_searches(
            account_names, usernames, hashtags, original_text
        )
        
        return suggestions
    
    def _generate_instagram_profile_searches(self, account_names: List[str], 
                                           usernames: List[str], 
                                           mentions: List[str]) -> List[str]:
        """Generate Instagram profile search URLs."""
        profiles = []
        
        # Add account names
        for account in account_names[:5]:  # Limit to 5
            clean_account = self._clean_username(account)
            if clean_account:
                profiles.append(f"{self.instagram_base_url}/{clean_account}")
        
        # Add usernames
        for username in usernames[:5]:  # Limit to 5
            clean_username = self._clean_username(username)
            if clean_username and clean_username not in [self._clean_username(a) for a in account_names]:
                profiles.append(f"{self.instagram_base_url}/{clean_username}")
        
        # Add mentions
        for mention in mentions[:3]:  # Limit to 3
            clean_mention = self._clean_username(mention)
            if clean_mention and clean_mention not in [self._clean_username(a) for a in account_names + usernames]:
                profiles.append(f"{self.instagram_base_url}/{clean_mention}")
        
        return profiles
    
    def _generate_hashtag_searches(self, hashtags: List[str]) -> List[str]:
        """Generate Instagram hashtag search URLs."""
        hashtag_searches = []
        
        for hashtag in hashtags[:5]:  # Limit to 5
            clean_hashtag = hashtag.lstrip('#').strip()
            if clean_hashtag:
                hashtag_searches.append(f"{self.instagram_base_url}/explore/tags/{clean_hashtag}")
        
        return hashtag_searches
    
    def _generate_google_searches(self, account_names: List[str], usernames: List[str], 
                                hashtags: List[str], original_text: str) -> List[str]:
        """Generate Google search URLs."""
        google_searches = []
        
        # Account-based searches
        for account in account_names[:3]:
            clean_account = self._clean_username(account)
            if clean_account:
                query = f"site:instagram.com {clean_account}"
                google_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        # Username-based searches
        for username in usernames[:3]:
            clean_username = self._clean_username(username)
            if clean_username and clean_username not in [self._clean_username(a) for a in account_names]:
                query = f"site:instagram.com {clean_username}"
                google_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        # Hashtag-based searches
        for hashtag in hashtags[:3]:
            clean_hashtag = hashtag.lstrip('#').strip()
            if clean_hashtag:
                query = f"site:instagram.com #{clean_hashtag}"
                google_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        # Text-based searches
        keywords = self._extract_keywords(original_text)
        for keyword in keywords[:3]:
            query = f"site:instagram.com {keyword}"
            google_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        return google_searches
    
    def _generate_time_based_searches(self, account_names: List[str], usernames: List[str], 
                                    hashtags: List[str], original_text: str) -> List[str]:
        """Generate time-based search strategies."""
        time_searches = []
        
        # Get current date for time-based searches
        now = datetime.now()
        recent_dates = [
            now.strftime("%Y-%m-%d"),
            (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            (now - timedelta(days=7)).strftime("%Y-%m-%d"),
            (now - timedelta(days=30)).strftime("%Y-%m-%d")
        ]
        
        # Combine with account names for recent content
        for account in account_names[:2]:
            clean_account = self._clean_username(account)
            if clean_account:
                for date in recent_dates[:2]:  # Only recent dates
                    query = f"site:instagram.com {clean_account} {date}"
                    time_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        # Combine with hashtags for recent content
        for hashtag in hashtags[:2]:
            clean_hashtag = hashtag.lstrip('#').strip()
            if clean_hashtag:
                for date in recent_dates[:2]:  # Only recent dates
                    query = f"site:instagram.com #{clean_hashtag} {date}"
                    time_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        return time_searches
    
    def _generate_keyword_searches(self, original_text: str) -> List[str]:
        """Generate keyword-based search strategies."""
        keyword_searches = []
        
        # Extract keywords from text
        keywords = self._extract_keywords(original_text)
        
        # Generate searches for each keyword
        for keyword in keywords[:5]:  # Limit to 5 keywords
            # Instagram search
            query = f"site:instagram.com {keyword}"
            keyword_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
            
            # Broader search
            query = f"{keyword} instagram"
            keyword_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        return keyword_searches
    
    def _generate_alternative_searches(self, account_names: List[str], usernames: List[str], 
                                     hashtags: List[str], original_text: str) -> List[str]:
        """Generate alternative search strategies."""
        alternative_searches = []
        
        # Search for similar usernames
        for username in usernames[:2]:
            clean_username = self._clean_username(username)
            if clean_username:
                # Search for variations
                variations = self._generate_username_variations(clean_username)
                for variation in variations[:3]:
                    query = f"site:instagram.com {variation}"
                    alternative_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        # Search for content type patterns
        content_type = self._detect_content_type(original_text)
        if content_type:
            for pattern in self.content_patterns.get(content_type, [])[:3]:
                query = f"site:instagram.com {pattern}"
                alternative_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        # Search for related hashtags
        for hashtag in hashtags[:2]:
            clean_hashtag = hashtag.lstrip('#').strip()
            if clean_hashtag:
                # Search for similar hashtags
                query = f"#{clean_hashtag} instagram"
                alternative_searches.append(f"{self.google_base_url}?q={quote_plus(query)}")
        
        return alternative_searches
    
    def _clean_username(self, username: str) -> str:
        """Clean and validate username for Instagram URLs."""
        if not username:
            return ""
        
        # Remove @ symbol and extra whitespace
        clean = username.lstrip('@').strip()
        
        # Remove invalid characters (Instagram usernames can only contain letters, numbers, periods, underscores)
        clean = re.sub(r'[^a-zA-Z0-9._]', '', clean)
        
        # Ensure it's not empty and not too long
        if clean and len(clean) <= 30:
            return clean
        
        return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []
        
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'so', 'very',
            'just', 'now', 'then', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'than', 'too', 'up', 'down', 'out', 'off',
            'over', 'under', 'again', 'further', 'then', 'once'
        }
        
        # Filter and clean words
        keywords = []
        for word in words:
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)
        
        # Return unique keywords, limited to 10
        return list(set(keywords))[:10]
    
    def _generate_username_variations(self, username: str) -> List[str]:
        """Generate variations of a username for alternative searches."""
        variations = []
        
        # Add common variations
        variations.extend([
            username + "_official",
            username + "_real",
            username + "_official_",
            "official_" + username,
            username.replace('_', ''),
            username.replace('_', '.'),
            username.replace('.', '_')
        ])
        
        return variations
    
    def _detect_content_type(self, text: str) -> str:
        """Detect the type of content based on text analysis."""
        if not text:
            return ""
        
        text_lower = text.lower()
        
        # Check for content type patterns
        for content_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return content_type
        
        return ""
    
    def format_suggestions_for_csv(self, suggestions: Dict[str, List[str]]) -> str:
        """
        Format search suggestions for CSV output.
        
        Args:
            suggestions: Dictionary of search suggestions by type
            
        Returns:
            Formatted string for CSV cell
        """
        formatted_suggestions = []
        
        # Add Instagram profiles first (most important)
        if suggestions['instagram_profiles']:
            formatted_suggestions.extend(suggestions['instagram_profiles'][:3])
        
        # Add hashtag searches
        if suggestions['instagram_hashtags']:
            formatted_suggestions.extend(suggestions['instagram_hashtags'][:2])
        
        # Add Google searches
        if suggestions['google_searches']:
            formatted_suggestions.extend(suggestions['google_searches'][:3])
        
        # Add time-based searches
        if suggestions['time_based_searches']:
            formatted_suggestions.extend(suggestions['time_based_searches'][:2])
        
        # Add keyword searches
        if suggestions['keyword_searches']:
            formatted_suggestions.extend(suggestions['keyword_searches'][:2])
        
        # Add alternative searches
        if suggestions['alternative_searches']:
            formatted_suggestions.extend(suggestions['alternative_searches'][:2])
        
        # Join with separator and limit total length
        result = " | ".join(formatted_suggestions[:10])  # Limit to 10 suggestions
        
        return result
