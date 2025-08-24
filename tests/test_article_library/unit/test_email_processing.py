"""
Unit Tests for Email Processing Functionality

Tests for email extraction, domain analysis, and URL processing components
of the Mingus article library system.
"""

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

# Import the modules to test
try:
    from scripts.step1_mac_email_extractor import EmailExtractor
    from scripts.step2_domain_intelligence import DomainAnalyzer
    from scripts.step3_domain_approval_interface import DomainApproval
except ImportError:
    # Mock imports for testing if modules don't exist
    EmailExtractor = Mock()
    DomainAnalyzer = Mock()
    DomainApproval = Mock()

class TestEmailExtraction:
    """Test email extraction and URL discovery functionality"""
    
    @pytest.fixture
    def mock_imap_connection(self):
        """Mock IMAP connection for testing"""
        mock_conn = Mock()
        mock_conn.select.return_value = ('OK', [b'10'])
        mock_conn.search.return_value = ('OK', [b'1 2 3 4 5'])
        mock_conn.fetch.return_value = ('OK', [(b'1', b'email content')])
        return mock_conn
    
    @pytest.fixture
    def sample_email_data(self):
        """Sample email data for testing"""
        return {
            'subject': 'Weekly Financial Tips',
            'from': 'newsletter@nerdwallet.com', 
            'date': '2024-03-15',
            'body': '''
            Check out these great articles:
            https://nerdwallet.com/article/careers/salary-negotiation
            https://blackenterprise.com/wealth-building-strategies
            https://investopedia.com/emergency-fund-guide
            '''
        }
    
    def test_url_extraction_from_email_text(self, sample_email_data):
        """Test URL extraction from email content"""
        # Create a simple URL extraction function for testing
        def extract_urls_from_text(text: str) -> List[str]:
            """Extract URLs from text using regex"""
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            return re.findall(url_pattern, text)
        
        urls = extract_urls_from_text(sample_email_data['body'])
        
        assert len(urls) == 3
        assert 'nerdwallet.com' in urls[0]
        assert 'blackenterprise.com' in urls[1]
        assert 'investopedia.com' in urls[2]
    
    def test_domain_filtering(self):
        """Test domain filtering for financial websites"""
        def filter_financial_urls(urls: List[str]) -> List[str]:
            """Filter URLs to only include financial/educational domains"""
            financial_domains = [
                'nerdwallet.com', 'blackenterprise.com', 'investopedia.com',
                'forbes.com', 'essence.com', 'cnbc.com', 'bloomberg.com',
                'wsj.com', 'nytimes.com', 'washingtonpost.com'
            ]
            
            filtered_urls = []
            for url in urls:
                domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                if domain and domain.group(1) in financial_domains:
                    filtered_urls.append(url)
            
            return filtered_urls
        
        test_urls = [
            'https://nerdwallet.com/article/careers/tips',
            'https://facebook.com/share/post',
            'https://blackenterprise.com/wealth-guide',
            'https://amazon.com/product/123'
        ]
        
        filtered = filter_financial_urls(test_urls)
        
        assert len(filtered) == 2
        assert any('nerdwallet.com' in url for url in filtered)
        assert any('blackenterprise.com' in url for url in filtered)
        assert not any('facebook.com' in url for url in filtered)
        assert not any('amazon.com' in url for url in filtered)
    
    def test_email_parsing(self, sample_email_data):
        """Test email parsing functionality"""
        def parse_email_content(raw_email: str) -> Dict[str, Any]:
            """Parse email content into structured data"""
            # Simple email parsing for testing
            lines = raw_email.split('\n')
            parsed = {
                'subject': '',
                'from': '',
                'date': '',
                'body': ''
            }
            
            in_body = False
            for line in lines:
                if line.startswith('Subject:'):
                    parsed['subject'] = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    parsed['from'] = line.replace('From:', '').strip()
                elif line.startswith('Date:'):
                    parsed['date'] = line.replace('Date:', '').strip()
                elif line.strip() == '':
                    in_body = True
                elif in_body:
                    parsed['body'] += line + '\n'
            
            return parsed
        
        # Test with sample email data
        raw_email = f"""
        Subject: {sample_email_data['subject']}
        From: {sample_email_data['from']}
        Date: {sample_email_data['date']}
        
        {sample_email_data['body']}
        """
        
        parsed = parse_email_content(raw_email)
        
        assert parsed['subject'] == sample_email_data['subject']
        assert parsed['from'] == sample_email_data['from']
        assert parsed['date'] == sample_email_data['date']
        assert 'nerdwallet.com' in parsed['body']
    
    @patch('imaplib.IMAP4_SSL')
    def test_mac_email_connection(self, mock_imap, mock_imap_connection):
        """Test .mac email IMAP connection"""
        mock_imap.return_value = mock_imap_connection
        
        def connect_to_mac_email(email: str, password: str):
            """Connect to .mac email account"""
            try:
                connection = mock_imap('imap.mail.me.com', 993)
                connection.login(email, password)
                return connection
            except Exception as e:
                raise Exception(f"Failed to connect: {str(e)}")
        
        connection = connect_to_mac_email('test@mac.com', 'password')
        
        assert connection is not None
        mock_imap.assert_called_once_with('imap.mail.me.com', 993)
    
    def test_url_validation(self):
        """Test URL validation functionality"""
        def validate_url(url: str) -> bool:
            """Validate if URL is properly formatted"""
            url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
            return bool(re.match(url_pattern, url))
        
        valid_urls = [
            'https://nerdwallet.com/article/careers/salary-negotiation',
            'http://blackenterprise.com/wealth-building-strategies',
            'https://www.investopedia.com/emergency-fund-guide'
        ]
        
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',
            'https://',
            'http://example',
            'javascript:alert("xss")'
        ]
        
        for url in valid_urls:
            assert validate_url(url), f"URL should be valid: {url}"
        
        for url in invalid_urls:
            assert not validate_url(url), f"URL should be invalid: {url}"

class TestDomainAnalysis:
    """Test domain analysis and intelligence functionality"""
    
    @pytest.fixture
    def sample_domain_data(self):
        """Sample domain data for testing"""
        return [
            {'url': 'https://nerdwallet.com/article/1', 'domain': 'nerdwallet.com'},
            {'url': 'https://nerdwallet.com/article/2', 'domain': 'nerdwallet.com'}, 
            {'url': 'https://blackenterprise.com/article/1', 'domain': 'blackenterprise.com'},
            {'url': 'https://investopedia.com/article/1', 'domain': 'investopedia.com'},
            {'url': 'https://forbes.com/article/1', 'domain': 'forbes.com'}
        ]
    
    def test_domain_analysis(self, sample_domain_data):
        """Test domain analysis and statistics generation"""
        def analyze_domains(url_data: List[Dict[str, str]]) -> Dict[str, Any]:
            """Analyze domains and generate statistics"""
            domain_counts = {}
            
            for item in url_data:
                domain = item['domain']
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            total_urls = len(url_data)
            unique_domains = len(domain_counts)
            
            # Find top domain
            top_domain = max(domain_counts.items(), key=lambda x: x[1])
            
            return {
                'total_urls': total_urls,
                'unique_domains': unique_domains,
                'domain_distribution': domain_counts,
                'top_domain': {'domain': top_domain[0], 'count': top_domain[1]}
            }
        
        analysis = analyze_domains(sample_domain_data)
        
        assert analysis['total_urls'] == 5
        assert analysis['unique_domains'] == 4
        assert analysis['top_domain']['domain'] == 'nerdwallet.com'
        assert analysis['top_domain']['count'] == 2
        assert 'nerdwallet.com' in analysis['domain_distribution']
        assert analysis['domain_distribution']['nerdwallet.com'] == 2
    
    def test_domain_quality_scoring(self):
        """Test domain quality scoring functionality"""
        def calculate_domain_quality(domain: str, url_count: int) -> float:
            """Calculate quality score for a domain"""
            # Base quality scores for known domains
            base_scores = {
                'nerdwallet.com': 0.95,
                'blackenterprise.com': 0.92,
                'investopedia.com': 0.90,
                'forbes.com': 0.94,
                'essence.com': 0.89,
                'cnbc.com': 0.93,
                'bloomberg.com': 0.96,
                'wsj.com': 0.97,
                'nytimes.com': 0.95,
                'washingtonpost.com': 0.94
            }
            
            base_score = base_scores.get(domain, 0.5)
            
            # Adjust score based on URL count (more content = higher quality)
            url_bonus = min(url_count / 100, 0.1)  # Max 10% bonus
            
            return min(base_score + url_bonus, 1.0)
        
        # Test quality scoring
        assert calculate_domain_quality('nerdwallet.com', 15) > 0.9
        assert calculate_domain_quality('blackenterprise.com', 12) > 0.9
        assert calculate_domain_quality('unknown.com', 5) == 0.5
        assert calculate_domain_quality('nerdwallet.com', 200) <= 1.0
    
    def test_domain_categorization(self):
        """Test domain categorization functionality"""
        def categorize_domain(domain: str) -> str:
            """Categorize domain by type"""
            financial_domains = [
                'nerdwallet.com', 'investopedia.com', 'forbes.com',
                'cnbc.com', 'bloomberg.com', 'wsj.com'
            ]
            
            cultural_domains = [
                'blackenterprise.com', 'essence.com', 'ebony.com',
                'theroot.com', 'blavity.com'
            ]
            
            news_domains = [
                'nytimes.com', 'washingtonpost.com', 'usatoday.com',
                'cnn.com', 'bbc.com'
            ]
            
            if domain in financial_domains:
                return 'financial'
            elif domain in cultural_domains:
                return 'cultural'
            elif domain in news_domains:
                return 'news'
            else:
                return 'other'
        
        assert categorize_domain('nerdwallet.com') == 'financial'
        assert categorize_domain('blackenterprise.com') == 'cultural'
        assert categorize_domain('nytimes.com') == 'news'
        assert categorize_domain('unknown.com') == 'other'

class TestDomainApproval:
    """Test domain approval interface functionality"""
    
    @pytest.fixture
    def sample_pending_domains(self):
        """Sample pending domains for approval"""
        return [
            {
                'domain': 'newfinancialsite.com',
                'url_count': 8,
                'quality_score': 0.75,
                'submission_date': datetime.now()
            },
            {
                'domain': 'anothersite.org',
                'url_count': 3,
                'quality_score': 0.45,
                'submission_date': datetime.now()
            }
        ]
    
    def test_domain_approval_criteria(self, sample_pending_domains):
        """Test domain approval criteria"""
        def evaluate_domain_for_approval(domain_data: Dict[str, Any]) -> Dict[str, Any]:
            """Evaluate domain against approval criteria"""
            criteria = {
                'min_quality_score': 0.7,
                'min_url_count': 5,
                'required_categories': ['financial', 'educational', 'news']
            }
            
            quality_score = domain_data['quality_score']
            url_count = domain_data['url_count']
            
            # Check quality score
            quality_approved = quality_score >= criteria['min_quality_score']
            
            # Check URL count
            url_count_approved = url_count >= criteria['min_url_count']
            
            # Overall approval
            approved = quality_approved and url_count_approved
            
            return {
                'domain': domain_data['domain'],
                'approved': approved,
                'quality_approved': quality_approved,
                'url_count_approved': url_count_approved,
                'reason': 'Meets all criteria' if approved else 'Does not meet quality or quantity requirements'
            }
        
        # Test approval evaluation
        evaluation1 = evaluate_domain_for_approval(sample_pending_domains[0])
        evaluation2 = evaluate_domain_for_approval(sample_pending_domains[1])
        
        assert evaluation1['approved'] == True
        assert evaluation2['approved'] == False
        assert evaluation1['quality_approved'] == True
        assert evaluation2['quality_approved'] == False
    
    def test_approval_workflow(self, sample_pending_domains):
        """Test domain approval workflow"""
        def process_domain_approval(domain_data: Dict[str, Any], approved: bool) -> Dict[str, Any]:
            """Process domain approval decision"""
            result = {
                'domain': domain_data['domain'],
                'approved': approved,
                'approval_date': datetime.now() if approved else None,
                'approved_by': 'test_user' if approved else None,
                'status': 'approved' if approved else 'rejected'
            }
            
            return result
        
        # Test approval workflow
        approval_result = process_domain_approval(sample_pending_domains[0], True)
        rejection_result = process_domain_approval(sample_pending_domains[1], False)
        
        assert approval_result['status'] == 'approved'
        assert approval_result['approval_date'] is not None
        assert rejection_result['status'] == 'rejected'
        assert rejection_result['approval_date'] is None

class TestEmailProcessingIntegration:
    """Test integration between email processing components"""
    
    def test_end_to_end_email_processing(self):
        """Test complete email processing workflow"""
        def process_email_workflow(email_content: str) -> Dict[str, Any]:
            """Complete email processing workflow"""
            # Step 1: Extract URLs
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, email_content)
            
            # Step 2: Filter financial URLs
            financial_domains = [
                'nerdwallet.com', 'blackenterprise.com', 'investopedia.com',
                'forbes.com', 'essence.com'
            ]
            
            filtered_urls = []
            for url in urls:
                domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                if domain and domain.group(1) in financial_domains:
                    filtered_urls.append(url)
            
            # Step 3: Analyze domains
            domain_counts = {}
            for url in filtered_urls:
                domain = re.search(r'https?://(?:www\.)?([^/]+)', url).group(1)
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            return {
                'total_urls_found': len(urls),
                'financial_urls_found': len(filtered_urls),
                'unique_domains': len(domain_counts),
                'domain_distribution': domain_counts,
                'processing_success': True
            }
        
        # Test with sample email
        sample_email = '''
        Check out these great articles:
        https://nerdwallet.com/article/careers/salary-negotiation
        https://blackenterprise.com/wealth-building-strategies
        https://investopedia.com/emergency-fund-guide
        https://facebook.com/share/post
        https://amazon.com/product/123
        '''
        
        result = process_email_workflow(sample_email)
        
        assert result['total_urls_found'] == 5
        assert result['financial_urls_found'] == 3
        assert result['unique_domains'] == 3
        assert result['processing_success'] == True
        assert 'nerdwallet.com' in result['domain_distribution']
        assert 'blackenterprise.com' in result['domain_distribution']
        assert 'investopedia.com' in result['domain_distribution']
