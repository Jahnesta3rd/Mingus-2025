"""
Quality control features for validating resolved URLs and content.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Set
from urllib.parse import urlparse
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class QualityController:
    """Handles quality control for resolved Instagram content."""
    
    def __init__(self):
        # Instagram URL patterns for validation
        self.instagram_patterns = [
            r"https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?",
            r"https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?",
            r"https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?",
            r"https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.-]+/[0-9]+/?",
        ]
        
        # Compile patterns for validation
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.instagram_patterns]
    
    def validate_resolved_urls(self, resolved_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate all resolved URLs and check for quality issues.
        
        Args:
            resolved_items: List of resolved items from manual review
            
        Returns:
            Dictionary with validation results and quality metrics
        """
        logger.info(f"Validating {len(resolved_items)} resolved URLs")
        
        validation_results = {
            'total_items': len(resolved_items),
            'valid_urls': 0,
            'invalid_urls': 0,
            'quality_issues': [],
            'duplicate_detection': {},
            'content_matching': {},
            'url_validation_details': []
        }
        
        # Validate each URL
        for item in resolved_items:
            url_validation = self._validate_single_url(item)
            validation_results['url_validation_details'].append(url_validation)
            
            if url_validation['is_valid']:
                validation_results['valid_urls'] += 1
            else:
                validation_results['invalid_urls'] += 1
            
            # Check for quality issues
            quality_issues = self._check_quality_issues(item, url_validation)
            validation_results['quality_issues'].extend(quality_issues)
        
        # Check for duplicates
        duplicate_results = self._detect_duplicates(resolved_items)
        validation_results['duplicate_detection'] = duplicate_results
        
        # Check content matching
        content_matching = self._check_content_matching(resolved_items)
        validation_results['content_matching'] = content_matching
        
        # Calculate quality score
        validation_results['quality_score'] = self._calculate_quality_score(validation_results)
        
        logger.info(f"Validation complete: {validation_results['valid_urls']} valid, {validation_results['invalid_urls']} invalid")
        
        return validation_results
    
    def _validate_single_url(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single resolved URL."""
        resolved_url = item.get('resolved_url', '').strip()
        original_text = item.get('original_text', '')
        account_name = item.get('account_name', '')
        
        validation = {
            'note_id': item.get('note_id', ''),
            'url': resolved_url,
            'is_valid': False,
            'url_type': 'none',
            'content_id': None,
            'validation_errors': [],
            'warnings': []
        }
        
        if not resolved_url:
            validation['validation_errors'].append('No URL provided')
            return validation
        
        # Check if URL matches Instagram patterns
        for pattern in self.compiled_patterns:
            if pattern.match(resolved_url):
                validation['is_valid'] = True
                validation['url_type'] = self._determine_url_type(resolved_url)
                validation['content_id'] = self._extract_content_id(resolved_url)
                break
        
        if not validation['is_valid']:
            if 'instagram.com' in resolved_url.lower():
                validation['validation_errors'].append('Instagram URL but not a valid content URL')
            else:
                validation['validation_errors'].append('Not an Instagram URL')
        
        # Additional quality checks
        if validation['is_valid']:
            # Check for suspicious patterns
            if self._is_suspicious_url(resolved_url):
                validation['warnings'].append('URL contains suspicious patterns')
            
            # Check if URL seems to match original content
            if not self._url_matches_content(resolved_url, original_text, account_name):
                validation['warnings'].append('URL may not match original content description')
        
        return validation
    
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
    
    def _extract_content_id(self, url: str) -> str:
        """Extract content ID from Instagram URL."""
        try:
            if '/p/' in url:
                match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
                return match.group(1) if match else ''
            elif '/reel/' in url:
                match = re.search(r'/reel/([A-Za-z0-9_-]+)', url)
                return match.group(1) if match else ''
            elif '/tv/' in url:
                match = re.search(r'/tv/([A-Za-z0-9_-]+)', url)
                return match.group(1) if match else ''
            elif '/stories/' in url:
                match = re.search(r'/stories/([A-Za-z0-9_.-]+)/([0-9]+)', url)
                return f"{match.group(1)}_{match.group(2)}" if match else ''
        except Exception as e:
            logger.error(f"Error extracting content ID from {url}: {e}")
        
        return ''
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL contains suspicious patterns."""
        suspicious_patterns = [
            r'[0-9]{10,}',  # Very long numbers
            r'[a-zA-Z]{20,}',  # Very long strings
            r'[^a-zA-Z0-9._/-]',  # Unusual characters
            r'\.(exe|zip|rar|pdf)$',  # File extensions
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _url_matches_content(self, url: str, original_text: str, account_name: str) -> bool:
        """Check if URL seems to match the original content description."""
        if not original_text or not account_name:
            return True  # Can't determine, assume it matches
        
        # Extract username from URL if possible
        url_username = self._extract_username_from_url(url)
        if not url_username:
            return True  # Can't extract username, assume it matches
        
        # Check if account name matches URL username
        account_clean = self._clean_username(account_name)
        if account_clean and account_clean.lower() != url_username.lower():
            return False
        
        return True
    
    def _extract_username_from_url(self, url: str) -> str:
        """Extract username from Instagram URL if possible."""
        try:
            # For stories URLs, extract username
            if '/stories/' in url:
                match = re.search(r'/stories/([A-Za-z0-9_.-]+)/', url)
                return match.group(1) if match else ''
            
            # For other URLs, we can't easily extract username
            # This would require additional API calls or web scraping
            return ''
        except Exception:
            return ''
    
    def _clean_username(self, username: str) -> str:
        """Clean username for comparison."""
        if not username:
            return ''
        
        # Remove @ symbol and extra whitespace
        clean = username.lstrip('@').strip()
        
        # Remove invalid characters
        clean = re.sub(r'[^a-zA-Z0-9._]', '', clean)
        
        return clean
    
    def _check_quality_issues(self, item: Dict[str, Any], url_validation: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check for quality issues in a resolved item."""
        issues = []
        
        # Check for empty or very short resolved URLs
        resolved_url = item.get('resolved_url', '')
        if not resolved_url or len(resolved_url) < 20:
            issues.append({
                'type': 'short_url',
                'severity': 'warning',
                'message': 'Resolved URL is very short or empty',
                'note_id': item.get('note_id', '')
            })
        
        # Check for missing notes when status is not resolved
        status = item.get('status', '')
        notes = item.get('notes', '')
        if status not in ['resolved', 'pending'] and not notes:
            issues.append({
                'type': 'missing_notes',
                'severity': 'warning',
                'message': f'Status is "{status}" but no notes provided',
                'note_id': item.get('note_id', '')
            })
        
        # Check for very long original text
        original_text = item.get('original_text', '')
        if len(original_text) > 1000:
            issues.append({
                'type': 'long_text',
                'severity': 'info',
                'message': 'Original text is very long (>1000 chars)',
                'note_id': item.get('note_id', '')
            })
        
        # Check for URL validation warnings
        for warning in url_validation.get('warnings', []):
            issues.append({
                'type': 'url_warning',
                'severity': 'warning',
                'message': warning,
                'note_id': item.get('note_id', '')
            })
        
        return issues
    
    def _detect_duplicates(self, resolved_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect potential duplicate entries."""
        logger.info("Detecting duplicate entries")
        
        # Group by resolved URL
        url_groups = {}
        for item in resolved_items:
            url = item.get('resolved_url', '').strip()
            if url:
                if url not in url_groups:
                    url_groups[url] = []
                url_groups[url].append(item)
        
        # Find duplicates
        duplicates = []
        for url, items in url_groups.items():
            if len(items) > 1:
                duplicates.append({
                    'url': url,
                    'count': len(items),
                    'note_ids': [item.get('note_id', '') for item in items]
                })
        
        # Group by content ID
        content_id_groups = {}
        for item in resolved_items:
            url_validation = item.get('url_validation', {})
            content_id = url_validation.get('content_id', '')
            if content_id:
                if content_id not in content_id_groups:
                    content_id_groups[content_id] = []
                content_id_groups[content_id].append(item)
        
        # Find content ID duplicates
        content_duplicates = []
        for content_id, items in content_id_groups.items():
            if len(items) > 1:
                content_duplicates.append({
                    'content_id': content_id,
                    'count': len(items),
                    'note_ids': [item.get('note_id', '') for item in items]
                })
        
        return {
            'url_duplicates': duplicates,
            'content_id_duplicates': content_duplicates,
            'total_duplicate_urls': len(duplicates),
            'total_duplicate_content_ids': len(content_duplicates)
        }
    
    def _check_content_matching(self, resolved_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check how well resolved URLs match original content descriptions."""
        logger.info("Checking content matching")
        
        matching_results = {
            'high_confidence_matches': 0,
            'medium_confidence_matches': 0,
            'low_confidence_matches': 0,
            'no_matches': 0,
            'matching_details': []
        }
        
        for item in resolved_items:
            if item.get('status') != 'resolved':
                continue
            
            resolved_url = item.get('resolved_url', '')
            original_text = item.get('original_text', '')
            account_name = item.get('account_name', '')
            
            if not resolved_url or not original_text:
                continue
            
            # Calculate matching score
            match_score = self._calculate_content_match_score(resolved_url, original_text, account_name)
            
            # Categorize match
            if match_score >= 0.8:
                category = 'high_confidence'
                matching_results['high_confidence_matches'] += 1
            elif match_score >= 0.5:
                category = 'medium_confidence'
                matching_results['medium_confidence_matches'] += 1
            elif match_score >= 0.2:
                category = 'low_confidence'
                matching_results['low_confidence_matches'] += 1
            else:
                category = 'no_match'
                matching_results['no_matches'] += 1
            
            matching_results['matching_details'].append({
                'note_id': item.get('note_id', ''),
                'url': resolved_url,
                'match_score': match_score,
                'category': category,
                'account_name': account_name
            })
        
        return matching_results
    
    def _calculate_content_match_score(self, url: str, original_text: str, account_name: str) -> float:
        """Calculate how well a URL matches the original content description."""
        score = 0.0
        
        # Check account name matching
        if account_name:
            url_username = self._extract_username_from_url(url)
            if url_username:
                account_clean = self._clean_username(account_name)
                if account_clean and account_clean.lower() == url_username.lower():
                    score += 0.5
        
        # Check for keyword matching in URL
        text_keywords = self._extract_keywords(original_text)
        url_keywords = self._extract_keywords(url)
        
        if text_keywords and url_keywords:
            common_keywords = set(text_keywords) & set(url_keywords)
            if common_keywords:
                score += min(0.3, len(common_keywords) * 0.1)
        
        # Check for content type matching
        content_type = self._detect_content_type(original_text)
        url_type = self._determine_url_type(url)
        
        if content_type and url_type:
            # This is a simplified check - in practice, you'd need more sophisticated matching
            if content_type in ['comedy', 'sketch'] and url_type in ['post', 'reel']:
                score += 0.2
        
        return min(1.0, score)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        if not text:
            return []
        
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        keywords = []
        for word in words:
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _detect_content_type(self, text: str) -> str:
        """Detect content type from text."""
        if not text:
            return ''
        
        text_lower = text.lower()
        
        content_patterns = {
            'comedy': ['funny', 'joke', 'laugh', 'comedy', 'humor'],
            'sketch': ['sketch', 'drawing', 'art', 'illustration'],
            'dance': ['dance', 'dancing', 'choreography'],
            'music': ['music', 'song', 'beat', 'melody'],
            'fashion': ['fashion', 'outfit', 'style', 'clothes'],
            'food': ['food', 'recipe', 'cooking', 'meal'],
            'travel': ['travel', 'trip', 'vacation', 'destination'],
            'fitness': ['fitness', 'workout', 'exercise', 'gym'],
            'beauty': ['beauty', 'makeup', 'skincare', 'cosmetics'],
            'lifestyle': ['lifestyle', 'daily', 'routine', 'life']
        }
        
        for content_type, patterns in content_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return content_type
        
        return ''
    
    def _calculate_quality_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall quality score for the resolved content."""
        total_items = validation_results['total_items']
        if total_items == 0:
            return 0.0
        
        valid_urls = validation_results['valid_urls']
        quality_issues = validation_results['quality_issues']
        duplicate_results = validation_results['duplicate_detection']
        
        # Base score from valid URLs
        base_score = valid_urls / total_items
        
        # Deduct points for quality issues
        issue_penalty = 0.0
        for issue in quality_issues:
            if issue['severity'] == 'warning':
                issue_penalty += 0.05
            elif issue['severity'] == 'error':
                issue_penalty += 0.1
        
        # Deduct points for duplicates
        duplicate_penalty = 0.0
        duplicate_penalty += duplicate_results['total_duplicate_urls'] * 0.02
        duplicate_penalty += duplicate_results['total_duplicate_content_ids'] * 0.02
        
        # Calculate final score
        final_score = max(0.0, base_score - issue_penalty - duplicate_penalty)
        
        return round(final_score, 3)
    
    def generate_quality_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable quality report."""
        report = []
        report.append("=" * 60)
        report.append("QUALITY CONTROL REPORT")
        report.append("=" * 60)
        
        # Summary statistics
        total_items = validation_results['total_items']
        valid_urls = validation_results['valid_urls']
        invalid_urls = validation_results['invalid_urls']
        quality_score = validation_results['quality_score']
        
        report.append(f"\nSUMMARY:")
        report.append(f"  Total items: {total_items}")
        report.append(f"  Valid URLs: {valid_urls}")
        report.append(f"  Invalid URLs: {invalid_urls}")
        report.append(f"  Quality Score: {quality_score:.1%}")
        
        # Quality issues
        quality_issues = validation_results['quality_issues']
        if quality_issues:
            report.append(f"\nQUALITY ISSUES ({len(quality_issues)} found):")
            
            # Group by severity
            by_severity = {}
            for issue in quality_issues:
                severity = issue['severity']
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            for severity in ['error', 'warning', 'info']:
                if severity in by_severity:
                    issues = by_severity[severity]
                    report.append(f"\n  {severity.upper()} ({len(issues)} issues):")
                    for issue in issues[:5]:  # Show first 5
                        report.append(f"    • {issue['message']} (Note ID: {issue['note_id']})")
                    if len(issues) > 5:
                        report.append(f"    ... and {len(issues) - 5} more")
        
        # Duplicate detection
        duplicate_results = validation_results['duplicate_detection']
        if duplicate_results['total_duplicate_urls'] > 0 or duplicate_results['total_duplicate_content_ids'] > 0:
            report.append(f"\nDUPLICATE DETECTION:")
            report.append(f"  Duplicate URLs: {duplicate_results['total_duplicate_urls']}")
            report.append(f"  Duplicate Content IDs: {duplicate_results['total_duplicate_content_ids']}")
        
        # Content matching
        content_matching = validation_results['content_matching']
        if content_matching['high_confidence_matches'] > 0 or content_matching['medium_confidence_matches'] > 0:
            report.append(f"\nCONTENT MATCHING:")
            report.append(f"  High confidence matches: {content_matching['high_confidence_matches']}")
            report.append(f"  Medium confidence matches: {content_matching['medium_confidence_matches']}")
            report.append(f"  Low confidence matches: {content_matching['low_confidence_matches']}")
            report.append(f"  No matches: {content_matching['no_matches']}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
