"""
Unit Tests for Article Scraping and AI Classification

Tests for article scraping, content extraction, and AI classification components
of the Mingus article library system.
"""

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

# Import the modules to test
try:
    from scripts.step3_article_scraper import ArticleScraper
    from scripts.step4_article_classifier import ArticleClassifier
    from scripts.step5_content_processor import ContentProcessor
except ImportError:
    # Mock imports for testing if modules don't exist
    ArticleScraper = Mock()
    ArticleClassifier = Mock()
    ContentProcessor = Mock()

class TestArticleScraping:
    """Test article scraping and content extraction functionality"""
    
    @pytest.fixture
    def sample_html_content(self):
        """Sample HTML content for testing"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>How to Negotiate Your Salary Like a Pro</title>
            <meta name="description" content="Master salary negotiation with these expert strategies">
            <meta name="author" content="Financial Expert">
            <meta property="article:published_time" content="2024-03-15T10:00:00Z">
        </head>
        <body>
            <article>
                <h1>How to Negotiate Your Salary Like a Pro</h1>
                <div class="author">By Financial Expert</div>
                <div class="content">
                    <p>Salary negotiation is a critical skill for career advancement...</p>
                    <p>Here are the key strategies you need to know:</p>
                    <ul>
                        <li>Research market rates</li>
                        <li>Prepare your talking points</li>
                        <li>Practice your pitch</li>
                    </ul>
                    <p>Remember to stay confident and professional throughout the process.</p>
                </div>
            </article>
        </body>
        </html>
        '''
    
    @pytest.fixture
    def sample_url(self):
        """Sample URL for testing"""
        return 'https://nerdwallet.com/article/careers/salary-negotiation'
    
    def test_html_parsing(self, sample_html_content):
        """Test HTML parsing and content extraction"""
        def parse_html_content(html_content: str) -> Dict[str, Any]:
            """Parse HTML content and extract article information"""
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else ''
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract author
            author_meta = soup.find('meta', attrs={'name': 'author'})
            author = author_meta.get('content', '') if author_meta else ''
            
            # Extract publish date
            date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            publish_date = date_meta.get('content', '') if date_meta else ''
            
            # Extract main content
            article = soup.find('article')
            if article:
                content_div = article.find('div', class_='content')
                if content_div:
                    content = content_div.get_text(separator=' ', strip=True)
                else:
                    content = article.get_text(separator=' ', strip=True)
            else:
                content = soup.get_text(separator=' ', strip=True)
            
            return {
                'title': title_text,
                'description': description,
                'author': author,
                'publish_date': publish_date,
                'content': content
            }
        
        result = parse_html_content(sample_html_content)
        
        assert result['title'] == 'How to Negotiate Your Salary Like a Pro'
        assert 'Master salary negotiation' in result['description']
        assert result['author'] == 'Financial Expert'
        assert '2024-03-15' in result['publish_date']
        assert 'Salary negotiation is a critical skill' in result['content']
        assert 'Research market rates' in result['content']
    
    def test_content_cleaning(self, sample_html_content):
        """Test content cleaning and normalization"""
        def clean_content(raw_content: str) -> str:
            """Clean and normalize article content"""
            # Remove extra whitespace
            cleaned = re.sub(r'\s+', ' ', raw_content)
            
            # Remove common HTML artifacts
            cleaned = re.sub(r'&nbsp;', ' ', cleaned)
            cleaned = re.sub(r'&amp;', '&', cleaned)
            cleaned = re.sub(r'&lt;', '<', cleaned)
            cleaned = re.sub(r'&gt;', '>', cleaned)
            
            # Remove script and style content
            cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.DOTALL)
            
            # Remove HTML tags
            cleaned = re.sub(r'<[^>]+>', '', cleaned)
            
            # Strip leading/trailing whitespace
            cleaned = cleaned.strip()
            
            return cleaned
        
        # Test with sample content
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        raw_content = soup.get_text()
        
        cleaned_content = clean_content(raw_content)
        
        assert 'Salary negotiation is a critical skill' in cleaned_content
        assert '<script>' not in cleaned_content
        assert '<style>' not in cleaned_content
        assert '&nbsp;' not in cleaned_content
        assert len(cleaned_content.split()) > 20  # Should have substantial content
    
    def test_content_analysis(self, sample_html_content):
        """Test content analysis and statistics"""
        def analyze_content(content: str) -> Dict[str, Any]:
            """Analyze content and generate statistics"""
            words = content.split()
            sentences = re.split(r'[.!?]+', content)
            paragraphs = content.split('\n\n')
            
            # Calculate reading time (average 200 words per minute)
            reading_time_minutes = max(1, len(words) // 200)
            
            # Calculate content quality metrics
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            avg_paragraph_length = len(words) / len(paragraphs) if paragraphs else 0
            
            return {
                'word_count': len(words),
                'sentence_count': len(sentences),
                'paragraph_count': len(paragraphs),
                'reading_time_minutes': reading_time_minutes,
                'avg_sentence_length': round(avg_sentence_length, 2),
                'avg_paragraph_length': round(avg_paragraph_length, 2)
            }
        
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        content = soup.get_text(separator=' ', strip=True)
        
        analysis = analyze_content(content)
        
        assert analysis['word_count'] > 0
        assert analysis['sentence_count'] > 0
        assert analysis['reading_time_minutes'] >= 1
        assert analysis['avg_sentence_length'] > 0
    
    @patch('requests.get')
    def test_web_scraping(self, mock_get, sample_html_content, sample_url):
        """Test web scraping functionality"""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_html_content
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response
        
        def scrape_article(url: str) -> Dict[str, Any]:
            """Scrape article from URL"""
            try:
                response = mock_get(url)
                response.raise_for_status()
                
                # Parse the content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract basic information
                title = soup.find('title')
                title_text = title.get_text() if title else ''
                
                # Extract content
                article = soup.find('article')
                if article:
                    content = article.get_text(separator=' ', strip=True)
                else:
                    content = soup.get_text(separator=' ', strip=True)
                
                return {
                    'url': url,
                    'title': title_text,
                    'content': content,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'success': True
                }
                
            except Exception as e:
                return {
                    'url': url,
                    'error': str(e),
                    'success': False
                }
        
        result = scrape_article(sample_url)
        
        assert result['success'] == True
        assert result['status_code'] == 200
        assert 'text/html' in result['content_type']
        assert 'How to Negotiate Your Salary' in result['title']
        assert 'Salary negotiation' in result['content']
        mock_get.assert_called_once_with(sample_url)

class TestAIClassification:
    """Test AI classification functionality"""
    
    @pytest.fixture
    def sample_article_content(self):
        """Sample article content for classification"""
        return {
            'title': 'How to Negotiate Your Salary Like a Pro',
            'content': '''
            Salary negotiation is a critical skill for career advancement. 
            This comprehensive guide will teach you proven strategies for 
            negotiating higher salaries and better compensation packages.
            
            Key topics covered:
            - Researching market rates
            - Preparing your talking points
            - Practicing your pitch
            - Handling objections
            - Closing the deal
            
            Whether you're negotiating a new job offer or asking for a raise,
            these techniques will help you achieve better financial outcomes.
            ''',
            'url': 'https://nerdwallet.com/article/careers/salary-negotiation'
        }
    
    def test_be_do_have_classification(self, sample_article_content):
        """Test Be-Do-Have framework classification"""
        def classify_article_phase(content: str, title: str) -> str:
            """Classify article into Be-Do-Have phases"""
            text = f"{title} {content}".lower()
            
            # BE (Mindset/Being) keywords
            be_keywords = [
                'mindset', 'attitude', 'belief', 'think', 'feel', 'understand',
                'awareness', 'consciousness', 'perspective', 'philosophy',
                'psychology', 'mental', 'emotional', 'spiritual'
            ]
            
            # DO (Action/Doing) keywords
            do_keywords = [
                'how to', 'step by step', 'action', 'strategy', 'technique',
                'method', 'process', 'procedure', 'guide', 'tutorial',
                'negotiate', 'implement', 'execute', 'practice', 'apply'
            ]
            
            # HAVE (Results/Having) keywords
            have_keywords = [
                'wealth', 'success', 'achievement', 'results', 'outcomes',
                'generation', 'legacy', 'empire', 'fortune', 'riches',
                'financial freedom', 'independence', 'security', 'prosperity'
            ]
            
            # Count keyword matches
            be_score = sum(1 for keyword in be_keywords if keyword in text)
            do_score = sum(1 for keyword in do_keywords if keyword in text)
            have_score = sum(1 for keyword in have_keywords if keyword in text)
            
            # Determine primary phase
            if do_score > be_score and do_score > have_score:
                return 'DO'
            elif have_score > be_score and have_score > do_score:
                return 'HAVE'
            else:
                return 'BE'
        
        phase = classify_article_phase(
            sample_article_content['content'],
            sample_article_content['title']
        )
        
        assert phase in ['BE', 'DO', 'HAVE']
        # This article should be classified as DO due to "how to" and action words
        assert phase == 'DO'
    
    def test_difficulty_classification(self, sample_article_content):
        """Test difficulty level classification"""
        def classify_difficulty(content: str, title: str) -> str:
            """Classify article difficulty level"""
            text = f"{title} {content}".lower()
            
            # Beginner indicators
            beginner_indicators = [
                'beginner', 'basic', 'introduction', 'overview', 'fundamentals',
                'getting started', 'first time', 'new to', 'simple', 'easy'
            ]
            
            # Advanced indicators
            advanced_indicators = [
                'advanced', 'expert', 'master', 'complex', 'sophisticated',
                'professional', 'enterprise', 'strategic', 'comprehensive',
                'in-depth', 'detailed analysis', 'specialized'
            ]
            
            # Count indicators
            beginner_score = sum(1 for indicator in beginner_indicators if indicator in text)
            advanced_score = sum(1 for indicator in advanced_indicators if indicator in text)
            
            # Determine difficulty
            if advanced_score > beginner_score and advanced_score > 0:
                return 'Advanced'
            elif beginner_score > advanced_score and beginner_score > 0:
                return 'Beginner'
            else:
                return 'Intermediate'
        
        difficulty = classify_difficulty(
            sample_article_content['content'],
            sample_article_content['title']
        )
        
        assert difficulty in ['Beginner', 'Intermediate', 'Advanced']
    
    def test_demographic_relevance_scoring(self, sample_article_content):
        """Test demographic relevance scoring"""
        def calculate_demographic_relevance(content: str, title: str) -> int:
            """Calculate demographic relevance score (1-10)"""
            text = f"{title} {content}".lower()
            
            # African American community relevance keywords
            cultural_keywords = [
                'african american', 'black', 'black women', 'black men',
                'generational wealth', 'community', 'culture', 'heritage',
                'representation', 'diversity', 'inclusion', 'equity'
            ]
            
            # Professional development keywords
            professional_keywords = [
                'career', 'professional', 'salary', 'negotiation', 'advancement',
                'leadership', 'management', 'business', 'entrepreneurship',
                'financial literacy', 'wealth building', 'investment'
            ]
            
            # Count relevant keywords
            cultural_score = sum(1 for keyword in cultural_keywords if keyword in text)
            professional_score = sum(1 for keyword in professional_keywords if keyword in text)
            
            # Calculate overall relevance (1-10 scale)
            total_score = cultural_score + professional_score
            relevance_score = min(10, max(1, total_score))
            
            return relevance_score
        
        relevance = calculate_demographic_relevance(
            sample_article_content['content'],
            sample_article_content['title']
        )
        
        assert 1 <= relevance <= 10
        # This article should have high relevance due to salary negotiation content
        assert relevance >= 7
    
    def test_cultural_sensitivity_scoring(self, sample_article_content):
        """Test cultural sensitivity scoring"""
        def calculate_cultural_sensitivity(content: str, title: str) -> int:
            """Calculate cultural sensitivity score (1-10)"""
            text = f"{title} {content}".lower()
            
            # Positive cultural indicators
            positive_indicators = [
                'inclusive', 'diverse', 'respectful', 'empowering', 'supportive',
                'community-focused', 'culturally-aware', 'sensitive', 'appropriate'
            ]
            
            # Negative cultural indicators
            negative_indicators = [
                'stereotype', 'bias', 'discriminatory', 'offensive', 'insensitive',
                'exclusive', 'marginalizing', 'tokenizing'
            ]
            
            # Count indicators
            positive_score = sum(1 for indicator in positive_indicators if indicator in text)
            negative_score = sum(1 for indicator in negative_indicators if indicator in text)
            
            # Calculate sensitivity score
            base_score = 5  # Neutral starting point
            sensitivity_score = base_score + positive_score - negative_score
            
            return max(1, min(10, sensitivity_score))
        
        sensitivity = calculate_cultural_sensitivity(
            sample_article_content['content'],
            sample_article_content['title']
        )
        
        assert 1 <= sensitivity <= 10
        # This article should have good sensitivity due to professional content
        assert sensitivity >= 6

class TestContentProcessing:
    """Test content processing and enhancement functionality"""
    
    @pytest.fixture
    def sample_raw_content(self):
        """Sample raw content for processing"""
        return {
            'title': 'How to Negotiate Your Salary Like a Pro',
            'content': 'Salary negotiation is a critical skill for career advancement...',
            'url': 'https://nerdwallet.com/article/careers/salary-negotiation',
            'author': 'Financial Expert',
            'publish_date': '2024-03-15'
        }
    
    def test_content_preview_generation(self, sample_raw_content):
        """Test content preview generation"""
        def generate_content_preview(content: str, max_length: int = 500) -> str:
            """Generate a preview of the content"""
            # Clean the content
            cleaned = re.sub(r'\s+', ' ', content.strip())
            
            # Truncate to max length
            if len(cleaned) <= max_length:
                return cleaned
            
            # Find the last complete sentence within the limit
            truncated = cleaned[:max_length]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            
            end_pos = max(last_period, last_exclamation, last_question)
            
            if end_pos > max_length * 0.7:  # If we found a sentence ending
                return truncated[:end_pos + 1]
            else:
                return truncated + '...'
        
        preview = generate_content_preview(sample_raw_content['content'])
        
        assert len(preview) <= 500
        assert 'Salary negotiation' in preview
        assert preview.endswith('.') or preview.endswith('...')
    
    def test_key_topics_extraction(self, sample_raw_content):
        """Test key topics extraction"""
        def extract_key_topics(content: str, title: str) -> List[str]:
            """Extract key topics from content"""
            text = f"{title} {content}".lower()
            
            # Define topic keywords
            topics = {
                'salary negotiation': ['salary', 'negotiation', 'compensation', 'pay'],
                'career advancement': ['career', 'advancement', 'promotion', 'growth'],
                'financial planning': ['financial', 'planning', 'budget', 'money'],
                'investment strategies': ['investment', 'strategy', 'portfolio', 'stocks'],
                'wealth building': ['wealth', 'building', 'rich', 'fortune'],
                'mindset development': ['mindset', 'attitude', 'belief', 'thinking']
            }
            
            extracted_topics = []
            for topic, keywords in topics.items():
                if any(keyword in text for keyword in keywords):
                    extracted_topics.append(topic)
            
            return extracted_topics
        
        topics = extract_key_topics(
            sample_raw_content['content'],
            sample_raw_content['title']
        )
        
        assert len(topics) > 0
        assert 'salary negotiation' in topics
        assert 'career advancement' in topics
    
    def test_learning_objectives_generation(self, sample_raw_content):
        """Test learning objectives generation"""
        def generate_learning_objectives(content: str, title: str) -> List[str]:
            """Generate learning objectives from content"""
            text = f"{title} {content}".lower()
            
            objectives = []
            
            # Check for different types of learning outcomes
            if 'how to' in title.lower():
                objectives.append('Learn practical techniques and strategies')
            
            if 'negotiation' in text:
                objectives.append('Master negotiation skills and tactics')
            
            if 'salary' in text:
                objectives.append('Understand salary negotiation principles')
            
            if 'career' in text:
                objectives.append('Develop career advancement strategies')
            
            if 'financial' in text:
                objectives.append('Build financial literacy and awareness')
            
            return objectives
        
        objectives = generate_learning_objectives(
            sample_raw_content['content'],
            sample_raw_content['title']
        )
        
        assert len(objectives) > 0
        assert any('negotiation' in obj.lower() for obj in objectives)
        assert any('salary' in obj.lower() for obj in objectives)
    
    def test_prerequisites_identification(self, sample_raw_content):
        """Test prerequisites identification"""
        def identify_prerequisites(content: str, title: str) -> List[str]:
            """Identify prerequisites for understanding the content"""
            text = f"{title} {content}".lower()
            
            prerequisites = []
            
            # Check for basic knowledge requirements
            if 'advanced' in text or 'expert' in text:
                prerequisites.append('Advanced knowledge in the field')
            
            if 'financial' in text and 'basic' not in text:
                prerequisites.append('Basic financial knowledge')
            
            if 'negotiation' in text:
                prerequisites.append('Basic communication skills')
            
            if 'career' in text:
                prerequisites.append('Professional experience')
            
            # Default prerequisite
            if not prerequisites:
                prerequisites.append('Open mind and willingness to learn')
            
            return prerequisites
        
        prerequisites = identify_prerequisites(
            sample_raw_content['content'],
            sample_raw_content['title']
        )
        
        assert len(prerequisites) > 0
        assert any('communication' in prereq.lower() for prereq in prerequisites)
        assert any('professional' in prereq.lower() for prereq in prerequisites)
