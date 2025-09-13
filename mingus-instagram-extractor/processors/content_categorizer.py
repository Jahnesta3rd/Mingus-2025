"""
Content categorizer for Instagram content based on keywords and patterns.
"""

import logging
import re
from typing import Dict, Any, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class ContentCategorizer:
    """Categorizes content based on keywords and patterns."""
    
    def __init__(self):
        self.categories = {
            'faith': {
                'keywords': [
                    'sunday', 'prayer', 'church', 'blessed', 'spiritual', 'worship', 'god',
                    'jesus', 'christ', 'faith', 'bible', 'pray', 'amen', 'hallelujah',
                    'ministry', 'pastor', 'sermon', 'devotion', 'scripture', 'holy',
                    'grace', 'mercy', 'praise', 'glory', 'heaven', 'eternal'
                ],
                'patterns': [
                    r'\b(sunday|sabbath)\b',
                    r'\b(pray|prayer|praying)\b',
                    r'\b(church|chapel|cathedral)\b',
                    r'\b(blessed|blessing)\b',
                    r'\b(spiritual|spirit)\b',
                    r'\b(worship|praise)\b',
                    r'\b(god|jesus|christ)\b'
                ]
            },
            'work_life': {
                'keywords': [
                    'monday', 'work', 'job', 'career', 'professional', 'office', 'hustle',
                    'business', 'meeting', 'project', 'deadline', 'client', 'colleague',
                    'promotion', 'salary', 'interview', 'resume', 'linkedin', 'networking',
                    'entrepreneur', 'startup', 'freelance', 'remote', 'workplace'
                ],
                'patterns': [
                    r'\b(monday|workday|weekday)\b',
                    r'\b(work|working|job|career)\b',
                    r'\b(office|workplace|desk)\b',
                    r'\b(meeting|project|deadline)\b',
                    r'\b(professional|business)\b',
                    r'\b(hustle|grind|hustling)\b'
                ]
            },
            'friendships': {
                'keywords': [
                    'friends', 'squad', 'friendship', 'social', 'crew', 'besties',
                    'bff', 'buddy', 'pal', 'mate', 'hangout', 'together', 'group',
                    'party', 'fun', 'laugh', 'memory', 'bond', 'support', 'loyalty',
                    'trust', 'care', 'love', 'family', 'chosen', 'tribe'
                ],
                'patterns': [
                    r'\b(friends?|squad|crew|besties?)\b',
                    r'\b(bff|best\s+friend)\b',
                    r'\b(hangout|hanging\s+out)\b',
                    r'\b(together|group)\b',
                    r'\b(fun|laugh|memory)\b',
                    r'\b(support|loyalty|trust)\b'
                ]
            },
            'children': {
                'keywords': [
                    'kids', 'children', 'parenting', 'baby', 'family', 'school',
                    'mom', 'dad', 'parent', 'child', 'toddler', 'teen', 'teenager',
                    'education', 'homework', 'play', 'toys', 'cute', 'adorable',
                    'growing', 'milestone', 'birthday', 'celebration', 'proud'
                ],
                'patterns': [
                    r'\b(kids?|children|child)\b',
                    r'\b(parenting|parent|mom|dad)\b',
                    r'\b(baby|toddler|teen)\b',
                    r'\b(school|education|homework)\b',
                    r'\b(family|home)\b',
                    r'\b(cute|adorable|proud)\b'
                ]
            },
            'relationships': {
                'keywords': [
                    'love', 'couple', 'dating', 'partner', 'marriage', 'bae',
                    'boyfriend', 'girlfriend', 'husband', 'wife', 'spouse',
                    'romance', 'relationship', 'together', 'forever', 'soulmate',
                    'anniversary', 'wedding', 'engagement', 'proposal', 'honeymoon',
                    'valentine', 'date', 'night', 'special', 'intimate'
                ],
                'patterns': [
                    r'\b(love|lovely|loving)\b',
                    r'\b(couple|dating|relationship)\b',
                    r'\b(partner|boyfriend|girlfriend)\b',
                    r'\b(marriage|married|husband|wife)\b',
                    r'\b(romance|romantic)\b',
                    r'\b(anniversary|wedding|engagement)\b'
                ]
            },
            'going_out': {
                'keywords': [
                    'weekend', 'party', 'fun', 'social', 'event', 'celebration',
                    'night', 'out', 'club', 'bar', 'restaurant', 'dinner',
                    'drinks', 'dancing', 'music', 'concert', 'festival', 'vacation',
                    'travel', 'trip', 'adventure', 'explore', 'discover', 'experience'
                ],
                'patterns': [
                    r'\b(weekend|friday|saturday|sunday)\b',
                    r'\b(party|partying|celebration)\b',
                    r'\b(fun|enjoy|enjoying)\b',
                    r'\b(social|event|gathering)\b',
                    r'\b(night\s+out|going\s+out)\b',
                    r'\b(club|bar|restaurant)\b'
                ]
            }
        }
        
        # Compile regex patterns for efficiency
        for category, data in self.categories.items():
            data['compiled_patterns'] = [re.compile(pattern, re.IGNORECASE) for pattern in data['patterns']]
    
    def categorize_content(self, content: str, title: str = '') -> Dict[str, Any]:
        """
        Categorize content based on keywords and patterns.
        
        Args:
            content: Text content to categorize
            title: Note title (optional)
            
        Returns:
            Dict containing category assignments and confidence scores
        """
        if not content:
            return self._empty_categorization()
        
        # Combine title and content for analysis
        full_text = f"{title} {content}".lower()
        
        category_scores = {}
        matched_keywords = {}
        matched_patterns = {}
        
        # Calculate scores for each category
        for category, data in self.categories.items():
            keyword_score = self._calculate_keyword_score(full_text, data['keywords'])
            pattern_score = self._calculate_pattern_score(full_text, data['compiled_patterns'])
            
            # Combined score (weighted: 60% keywords, 40% patterns)
            total_score = (keyword_score * 0.6) + (pattern_score * 0.4)
            
            category_scores[category] = total_score
            matched_keywords[category] = self._find_matched_keywords(full_text, data['keywords'])
            matched_patterns[category] = self._find_matched_patterns(full_text, data['compiled_patterns'])
        
        # Find primary category
        primary_category = max(category_scores.items(), key=lambda x: x[1])
        
        # Find secondary categories (score > 0.3)
        secondary_categories = {
            cat: score for cat, score in category_scores.items() 
            if score > 0.3 and cat != primary_category[0]
        }
        
        # Generate confidence level
        confidence_level = self._calculate_confidence_level(primary_category[1])
        
        result = {
            'primary_category': primary_category[0] if primary_category[1] > 0.1 else 'uncategorized',
            'primary_score': primary_category[1],
            'secondary_categories': secondary_categories,
            'all_scores': category_scores,
            'matched_keywords': matched_keywords,
            'matched_patterns': matched_patterns,
            'confidence_level': confidence_level,
            'is_instagram_related': self._is_instagram_related(content),
            'content_analysis': self._analyze_content_characteristics(content)
        }
        
        logger.debug(f"Categorized content: {primary_category[0]} (score: {primary_category[1]:.3f})")
        return result
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate score based on keyword matches.
        
        Args:
            text: Text to analyze
            keywords: List of keywords to search for
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not text or not keywords:
            return 0.0
        
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword in text:
                matches += 1
        
        return min(matches / total_keywords, 1.0)
    
    def _calculate_pattern_score(self, text: str, patterns: List[re.Pattern]) -> float:
        """
        Calculate score based on regex pattern matches.
        
        Args:
            text: Text to analyze
            patterns: List of compiled regex patterns
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not text or not patterns:
            return 0.0
        
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if pattern.search(text):
                matches += 1
        
        return min(matches / total_patterns, 1.0)
    
    def _find_matched_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find which keywords matched in the text."""
        return [keyword for keyword in keywords if keyword in text]
    
    def _find_matched_patterns(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Find which patterns matched in the text."""
        matched = []
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                matched.append(match.group(0))
        return matched
    
    def _calculate_confidence_level(self, score: float) -> str:
        """Calculate confidence level based on score."""
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def _is_instagram_related(self, content: str) -> bool:
        """Check if content is Instagram-related."""
        instagram_indicators = [
            'instagram', 'insta', 'ig', 'story', 'post', 'reel', 'tv',
            '@', '#', 'follow', 'like', 'comment', 'share'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in instagram_indicators)
    
    def _analyze_content_characteristics(self, content: str) -> Dict[str, Any]:
        """Analyze general characteristics of the content."""
        return {
            'word_count': len(content.split()),
            'char_count': len(content),
            'has_hashtags': '#' in content,
            'has_mentions': '@' in content,
            'has_urls': 'http' in content.lower(),
            'has_emojis': any(ord(char) > 127 for char in content),
            'sentiment_indicators': self._extract_sentiment_indicators(content)
        }
    
    def _extract_sentiment_indicators(self, content: str) -> Dict[str, int]:
        """Extract sentiment indicators from content."""
        positive_words = ['happy', 'joy', 'love', 'amazing', 'wonderful', 'great', 'awesome', 'fantastic']
        negative_words = ['sad', 'angry', 'frustrated', 'disappointed', 'terrible', 'awful', 'hate']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        return {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': max(0, len(content.split()) - positive_count - negative_count)
        }
    
    def _empty_categorization(self) -> Dict[str, Any]:
        """Return empty categorization for empty content."""
        return {
            'primary_category': 'uncategorized',
            'primary_score': 0.0,
            'secondary_categories': {},
            'all_scores': {},
            'matched_keywords': {},
            'matched_patterns': {},
            'confidence_level': 'very_low',
            'is_instagram_related': False,
            'content_analysis': {
                'word_count': 0,
                'char_count': 0,
                'has_hashtags': False,
                'has_mentions': False,
                'has_urls': False,
                'has_emojis': False,
                'sentiment_indicators': {'positive': 0, 'negative': 0, 'neutral': 0}
            }
        }
    
    def get_category_description(self, category: str) -> str:
        """Get human-readable description for a category."""
        descriptions = {
            'faith': 'Spiritual and religious content',
            'work_life': 'Professional and career-related content',
            'friendships': 'Social connections and friendships',
            'children': 'Parenting and family content',
            'relationships': 'Romantic relationships and love',
            'going_out': 'Social events and entertainment',
            'uncategorized': 'Content that doesn\'t fit other categories'
        }
        return descriptions.get(category, 'Unknown category')
    
    def generate_category_summary(self, categorizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for multiple categorizations."""
        if not categorizations:
            return {'total_items': 0, 'category_counts': {}, 'confidence_distribution': {}}
        
        category_counts = Counter()
        confidence_counts = Counter()
        
        for cat_data in categorizations:
            primary = cat_data.get('primary_category', 'uncategorized')
            confidence = cat_data.get('confidence_level', 'very_low')
            
            category_counts[primary] += 1
            confidence_counts[confidence] += 1
        
        return {
            'total_items': len(categorizations),
            'category_counts': dict(category_counts),
            'confidence_distribution': dict(confidence_counts),
            'most_common_category': category_counts.most_common(1)[0] if category_counts else None,
            'high_confidence_items': confidence_counts.get('high', 0) + confidence_counts.get('medium', 0)
        }
