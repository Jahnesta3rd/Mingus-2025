#!/usr/bin/env python3
"""
Step 4: Article Scraper for Mingus Financial Wellness App
========================================================

This script scrapes full article content from URLs belonging to approved domains,
focusing on quality content for African American professionals aged 25-35.

Features:
- Multi-method content extraction (newspaper3k, BeautifulSoup4, requests)
- Comprehensive quality filtering and cultural relevance assessment
- Respectful web scraping with rate limiting and error handling
- Progress tracking and detailed logging
- Output optimized for Step 5 AI classification

Author: Mingus Development Team
Date: 2025
"""

import os
import sys
import csv
import json
import time
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import hashlib

# Third-party imports
import pandas as pd
import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import langdetect
from textblob import TextBlob
import tqdm

# Configure paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure directories exist
for directory in [CONFIG_DIR, DATA_DIR, LOGS_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "step4_scraping.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ArticleScraper:
    """Comprehensive article scraper with quality filtering and cultural relevance assessment."""
    
    def __init__(self):
        self.approved_domains = self._load_approved_domains()
        self.raw_urls = self._load_raw_urls()
        self.filtered_urls = self._filter_urls_to_approved_domains()
        
        # Scraping configuration
        self.config = Config()
        self.config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        self.config.request_timeout = 30
        self.config.fetch_images = False
        self.config.memoize_articles = False
        
        # Rate limiting
        self.domain_delays = {}
        self.last_request_time = {}
        self.min_delay = 2  # seconds between requests per domain
        
        # Quality thresholds
        self.min_word_count = 500
        self.max_word_count = 5000
        self.min_quality_score = 0.6
        self.min_cultural_relevance = 0.3
        
        # Results storage
        self.scraped_articles = []
        self.failed_urls = []
        self.quality_stats = {
            'total_processed': 0,
            'successful_scrapes': 0,
            'quality_passed': 0,
            'cultural_relevance_passed': 0,
            'final_articles': 0
        }
        
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
    
    def _load_approved_domains(self) -> List[str]:
        """Load approved domains from config file."""
        domains_file = CONFIG_DIR / "approved_domains.txt"
        if not domains_file.exists():
            logger.error(f"Approved domains file not found: {domains_file}")
            return []
        
        with open(domains_file, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(domains)} approved domains")
        return domains
    
    def _load_raw_urls(self) -> pd.DataFrame:
        """Load raw URLs from Step 1 extraction."""
        urls_file = DATA_DIR / "raw_urls_complete.csv"
        if not urls_file.exists():
            logger.error(f"Raw URLs file not found: {urls_file}")
            return pd.DataFrame()
        
        df = pd.read_csv(urls_file)
        logger.info(f"Loaded {len(df)} raw URLs")
        return df
    
    def _filter_urls_to_approved_domains(self) -> List[str]:
        """Filter URLs to only those from approved domains."""
        if self.raw_urls.empty:
            return []
        
        filtered_urls = []
        for _, row in self.raw_urls.iterrows():
            url = row['url']
            domain = row['domain']
            
            # Check if domain is in approved list
            if domain in self.approved_domains:
                # Additional URL validation
                if self._is_valid_article_url(url):
                    filtered_urls.append(url)
        
        logger.info(f"Filtered to {len(filtered_urls)} URLs from approved domains")
        return filtered_urls
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is likely to be an article."""
        if not url or pd.isna(url):
            return False
        
        # Skip obvious non-article URLs
        skip_patterns = [
            r'\.(jpg|jpeg|png|gif|pdf|doc|docx|xls|xlsx|zip|rar)$',
            r'/(login|signup|register|subscribe)',
            r'/(cart|checkout|payment)',
            r'/(privacy|terms|contact|about)',
            r'/(admin|dashboard|manage)',
            r'/(api|ajax|json)',
            r'/(tracking|analytics|pixel)',
            r'=20$',  # Email artifacts
            r'\.\.\.$',  # Truncated URLs
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def _rate_limit_domain(self, domain: str):
        """Implement rate limiting per domain."""
        current_time = time.time()
        
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def scrape_article_newspaper3k(self, url: str) -> Optional[Dict[str, Any]]:
        """Primary scraping method using newspaper3k."""
        try:
            article = Article(url, config=self.config)
            article.download()
            article.parse()
            article.nlp()
            
            if not article.text or len(article.text.strip()) < 100:
                return None
            
            return {
                'title': article.title,
                'content': article.text,
                'summary': article.summary,
                'keywords': article.keywords,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'authors': article.authors,
                'meta_description': article.meta_description,
                'meta_keywords': article.meta_keywords,
                'meta_lang': article.meta_lang,
                'scraping_method': 'newspaper3k',
                'confidence': 0.9
            }
        except Exception as e:
            logger.debug(f"newspaper3k failed for {url}: {str(e)}")
            return None
    
    def scrape_article_beautifulsoup(self, url: str) -> Optional[Dict[str, Any]]:
        """Secondary scraping method using BeautifulSoup."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.post-content',
                '.entry-content',
                '.article-content',
                'main',
                '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text().strip() for elem in elements])
                    break
            
            # Fallback to body if no specific content area found
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text().strip()
            
            # Clean content
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', content)
            
            if not content or len(content) < 100:
                return None
            
            # Extract metadata
            meta_description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_description = meta_desc.get('content', '')
            
            # Extract publish date
            publish_date = None
            date_selectors = [
                'time[datetime]',
                '.publish-date',
                '.post-date',
                '.article-date',
                '[property="article:published_time"]'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text()
                    try:
                        publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        break
                    except:
                        continue
            
            return {
                'title': title,
                'content': content,
                'summary': content[:500] + "..." if len(content) > 500 else content,
                'keywords': [],
                'publish_date': publish_date.isoformat() if publish_date else None,
                'authors': [],
                'meta_description': meta_description,
                'meta_keywords': "",
                'meta_lang': "en",
                'scraping_method': 'beautifulsoup',
                'confidence': 0.7
            }
        except Exception as e:
            logger.debug(f"BeautifulSoup failed for {url}: {str(e)}")
            return None
    
    def scrape_article_requests(self, url: str) -> Optional[Dict[str, Any]]:
        """Tertiary scraping method using requests only."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Simple text extraction
            text = response.text
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
            
            if not text or len(text) < 100:
                return None
            
            return {
                'title': f"Article from {urlparse(url).netloc}",
                'content': text,
                'summary': text[:500] + "..." if len(text) > 500 else text,
                'keywords': [],
                'publish_date': None,
                'authors': [],
                'meta_description': "",
                'meta_keywords': "",
                'meta_lang': "en",
                'scraping_method': 'requests',
                'confidence': 0.5
            }
        except Exception as e:
            logger.debug(f"Requests failed for {url}: {str(e)}")
            return None
    
    def scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape article using multiple methods with fallback."""
        domain = self._extract_domain(url)
        self._rate_limit_domain(domain)
        
        # Try newspaper3k first
        article_data = self.scrape_article_newspaper3k(url)
        if article_data:
            return article_data
        
        # Try BeautifulSoup second
        article_data = self.scrape_article_beautifulsoup(url)
        if article_data:
            return article_data
        
        # Try requests as last resort
        article_data = self.scrape_article_requests(url)
        if article_data:
            return article_data
        
        return None
    
    def assess_content_quality(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess content quality and relevance."""
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        
        # Basic metrics
        word_count = len(word_tokenize(content))
        sentence_count = len(sent_tokenize(content))
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Language detection
        try:
            lang = langdetect.detect(content)
            is_english = lang == 'en'
        except:
            is_english = True  # Assume English if detection fails
        
        # Reading level assessment (simplified)
        if avg_sentence_length < 10:
            reading_level = "easy"
        elif avg_sentence_length < 20:
            reading_level = "medium"
        else:
            reading_level = "difficult"
        
        # Content-to-noise ratio (simplified)
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(content.lower())
        content_words = [w for w in words if w not in stop_words and len(w) > 2]
        content_ratio = len(content_words) / len(words) if words else 0
        
        # Sentiment analysis
        try:
            blob = TextBlob(content)
            sentiment = blob.sentiment.polarity
        except:
            sentiment = 0
        
        # Quality score calculation
        quality_score = 0.0
        
        # Word count factor (optimal range: 500-3000 words)
        if 500 <= word_count <= 3000:
            quality_score += 0.3
        elif 300 <= word_count <= 5000:
            quality_score += 0.2
        elif word_count > 5000:
            quality_score += 0.1
        
        # Content ratio factor
        if content_ratio > 0.6:
            quality_score += 0.2
        elif content_ratio > 0.4:
            quality_score += 0.1
        
        # Language factor
        if is_english:
            quality_score += 0.2
        
        # Reading level factor (prefer medium)
        if reading_level == "medium":
            quality_score += 0.1
        elif reading_level == "easy":
            quality_score += 0.05
        
        # Sentiment factor (prefer positive/neutral)
        if sentiment >= -0.1:
            quality_score += 0.1
        
        # Title quality factor
        if title and len(title) > 10:
            quality_score += 0.1
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
            'reading_level': reading_level,
            'content_ratio': content_ratio,
            'sentiment': sentiment,
            'is_english': is_english,
            'quality_score': min(quality_score, 1.0)
        }
    
    def assess_cultural_relevance(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess cultural relevance for African American professionals."""
        content = article_data.get('content', '').lower()
        title = article_data.get('title', '').lower()
        full_text = f"{title} {content}"
        
        # Keywords for different relevance categories
        cultural_keywords = {
            'african_american': [
                'african american', 'black', 'black professional', 'black entrepreneur',
                'black community', 'black wealth', 'black excellence', 'diversity',
                'inclusion', 'representation', 'systemic', 'racial', 'equity'
            ],
            'professional_development': [
                'career advancement', 'professional development', 'leadership',
                'executive presence', 'networking', 'mentorship', 'skill building',
                'promotion', 'salary negotiation', 'workplace', 'corporate culture'
            ],
            'financial_empowerment': [
                'financial literacy', 'wealth building', 'generational wealth',
                'financial independence', 'investment', 'savings', 'debt management',
                'student loans', 'emergency fund', 'retirement', 'homeownership'
            ],
            'income_optimization': [
                'salary', 'income', 'earnings', 'side hustle', 'passive income',
                'negotiation', 'compensation', 'bonus', 'raise', 'promotion'
            ],
            'systemic_barriers': [
                'systemic racism', 'discrimination', 'bias', 'glass ceiling',
                'pay gap', 'opportunity gap', 'access', 'barriers', 'challenges'
            ]
        }
        
        # Calculate relevance scores
        relevance_scores = {}
        total_keywords_found = 0
        
        for category, keywords in cultural_keywords.items():
            found_count = sum(1 for keyword in keywords if keyword in full_text)
            relevance_scores[category] = found_count / len(keywords) if keywords else 0
            total_keywords_found += found_count
        
        # Overall cultural relevance score
        if total_keywords_found > 0:
            cultural_relevance_score = min(total_keywords_found / 20, 1.0)  # Normalize
        else:
            cultural_relevance_score = 0.0
        
        # Determine primary focus
        primary_focus = max(relevance_scores.items(), key=lambda x: x[1])[0] if relevance_scores else 'general'
        
        return {
            'cultural_relevance_score': cultural_relevance_score,
            'primary_focus': primary_focus,
            'relevance_breakdown': relevance_scores,
            'total_keywords_found': total_keywords_found
        }
    
    def extract_article_topics(self, article_data: Dict[str, Any]) -> List[str]:
        """Extract main topics from article content."""
        content = article_data.get('content', '')
        keywords = article_data.get('keywords', [])
        
        # Use keywords if available
        if keywords:
            return keywords[:5]  # Top 5 keywords
        
        # Simple topic extraction based on frequency
        words = word_tokenize(content.lower())
        stop_words = set(stopwords.words('english'))
        
        # Filter out stop words and short words
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [word for word, freq in top_words]
    
    def process_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Process a single article through the complete pipeline."""
        try:
            # Scrape article
            article_data = self.scrape_article(url)
            if not article_data:
                self.failed_urls.append({
                    'url': url,
                    'error': 'Failed to scrape content',
                    'timestamp': datetime.now().isoformat()
                })
                return None
            
            # Add URL and domain
            article_data['url'] = url
            article_data['domain'] = self._extract_domain(url)
            
            # Assess quality
            quality_metrics = self.assess_content_quality(article_data)
            article_data.update(quality_metrics)
            
            # Check quality thresholds
            if (quality_metrics['word_count'] < self.min_word_count or 
                quality_metrics['word_count'] > self.max_word_count or
                quality_metrics['quality_score'] < self.min_quality_score):
                self.failed_urls.append({
                    'url': url,
                    'error': f"Failed quality check: word_count={quality_metrics['word_count']}, quality_score={quality_metrics['quality_score']:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
                return None
            
            # Assess cultural relevance
            cultural_metrics = self.assess_cultural_relevance(article_data)
            article_data.update(cultural_metrics)
            
            # Extract topics
            article_data['article_topics'] = self.extract_article_topics(article_data)
            
            # Calculate reading time (average 200 words per minute)
            article_data['reading_time'] = max(1, quality_metrics['word_count'] // 200)
            
            # Generate content hash for duplicate detection
            content_hash = hashlib.md5(article_data['content'].encode()).hexdigest()
            article_data['content_hash'] = content_hash
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            self.failed_urls.append({
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None
    
    def run_scraping(self, max_workers: int = 5):
        """Run the complete scraping pipeline."""
        logger.info(f"Starting article scraping for {len(self.filtered_urls)} URLs")
        
        # Process articles with progress bar
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(self.process_article, url): url for url in self.filtered_urls}
            
            # Process results with progress bar
            with tqdm.tqdm(total=len(self.filtered_urls), desc="Scraping articles") as pbar:
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    self.quality_stats['total_processed'] += 1
                    
                    try:
                        article_data = future.result()
                        if article_data:
                            self.quality_stats['successful_scrapes'] += 1
                            
                            # Check cultural relevance threshold
                            if article_data.get('cultural_relevance_score', 0) >= self.min_cultural_relevance:
                                self.quality_stats['cultural_relevance_passed'] += 1
                                self.scraped_articles.append(article_data)
                            
                            self.quality_stats['quality_passed'] += 1
                    except Exception as e:
                        logger.error(f"Error processing {url}: {str(e)}")
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Success': self.quality_stats['successful_scrapes'],
                        'Quality': self.quality_stats['quality_passed'],
                        'Cultural': self.quality_stats['cultural_relevance_passed']
                    })
        
        self.quality_stats['final_articles'] = len(self.scraped_articles)
        logger.info(f"Scraping completed. Final results: {self.quality_stats}")
    
    def save_results(self):
        """Save all results to files."""
        # Save all scraped articles
        if self.scraped_articles:
            df_all = pd.DataFrame(self.scraped_articles)
            df_all.to_csv(DATA_DIR / "scraped_articles_complete.csv", index=False)
            logger.info(f"Saved {len(df_all)} articles to scraped_articles_complete.csv")
        
        # Save high-quality articles (those that passed all filters)
        high_quality_articles = [
            article for article in self.scraped_articles
            if (article.get('quality_score', 0) >= self.min_quality_score and
                article.get('cultural_relevance_score', 0) >= self.min_cultural_relevance)
        ]
        
        if high_quality_articles:
            df_high_quality = pd.DataFrame(high_quality_articles)
            df_high_quality.to_csv(DATA_DIR / "high_quality_articles.csv", index=False)
            logger.info(f"Saved {len(df_high_quality)} high-quality articles")
        
        # Save failed URLs
        if self.failed_urls:
            df_failures = pd.DataFrame(self.failed_urls)
            df_failures.to_csv(DATA_DIR / "scraping_failures.csv", index=False)
            logger.info(f"Saved {len(df_failures)} failed URLs")
        
        # Save cultural relevance analysis
        cultural_analysis = {
            'total_articles_analyzed': len(self.scraped_articles),
            'cultural_relevance_distribution': {},
            'primary_focus_distribution': {},
            'quality_score_distribution': {},
            'domain_distribution': {}
        }
        
        if self.scraped_articles:
            # Cultural relevance distribution
            relevance_scores = [a.get('cultural_relevance_score', 0) for a in self.scraped_articles]
            cultural_analysis['cultural_relevance_distribution'] = {
                'low': len([s for s in relevance_scores if s < 0.3]),
                'medium': len([s for s in relevance_scores if 0.3 <= s < 0.7]),
                'high': len([s for s in relevance_scores if s >= 0.7])
            }
            
            # Primary focus distribution
            focus_counts = {}
            for article in self.scraped_articles:
                focus = article.get('primary_focus', 'general')
                focus_counts[focus] = focus_counts.get(focus, 0) + 1
            cultural_analysis['primary_focus_distribution'] = focus_counts
            
            # Quality score distribution
            quality_scores = [a.get('quality_score', 0) for a in self.scraped_articles]
            cultural_analysis['quality_score_distribution'] = {
                'low': len([s for s in quality_scores if s < 0.6]),
                'medium': len([s for s in quality_scores if 0.6 <= s < 0.8]),
                'high': len([s for s in quality_scores if s >= 0.8])
            }
            
            # Domain distribution
            domain_counts = {}
            for article in self.scraped_articles:
                domain = article.get('domain', 'unknown')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            cultural_analysis['domain_distribution'] = domain_counts
        
        with open(DATA_DIR / "cultural_relevance_analysis.json", 'w') as f:
            json.dump(cultural_analysis, f, indent=2)
        
        # Save content quality report
        quality_report = {
            'scraping_summary': self.quality_stats,
            'quality_thresholds': {
                'min_word_count': self.min_word_count,
                'max_word_count': self.max_word_count,
                'min_quality_score': self.min_quality_score,
                'min_cultural_relevance': self.min_cultural_relevance
            },
            'processing_timestamp': datetime.now().isoformat()
        }
        
        with open(DATA_DIR / "content_quality_report.json", 'w') as f:
            json.dump(quality_report, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report()
    
    def _generate_html_report(self):
        """Generate an HTML report of the scraping results."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Step 4 Article Scraping Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background-color: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
                .section {{ margin: 30px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Step 4: Article Scraping Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Scraping Summary</h2>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{self.quality_stats['total_processed']}</div>
                        <div class="stat-label">Total URLs Processed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.quality_stats['successful_scrapes']}</div>
                        <div class="stat-label">Successful Scrapes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.quality_stats['quality_passed']}</div>
                        <div class="stat-label">Quality Threshold Passed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.quality_stats['cultural_relevance_passed']}</div>
                        <div class="stat-label">Cultural Relevance Passed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.quality_stats['final_articles']}</div>
                        <div class="stat-label">Final Articles</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Approved Domains ({len(self.approved_domains)})</h2>
                <ul>
                    {''.join([f'<li>{domain}</li>' for domain in self.approved_domains])}
                </ul>
            </div>
            
            <div class="section">
                <h2>Sample Articles</h2>
                <table>
                    <tr>
                        <th>Domain</th>
                        <th>Title</th>
                        <th>Word Count</th>
                        <th>Quality Score</th>
                        <th>Cultural Relevance</th>
                    </tr>
                    {''.join([f'''
                    <tr>
                        <td>{article.get('domain', 'N/A')}</td>
                        <td>{article.get('title', 'N/A')[:50]}...</td>
                        <td>{article.get('word_count', 0)}</td>
                        <td>{article.get('quality_score', 0):.2f}</td>
                        <td>{article.get('cultural_relevance_score', 0):.2f}</td>
                    </tr>
                    ''' for article in self.scraped_articles[:10]])}
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(REPORTS_DIR / "scraping_summary.html", 'w') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {REPORTS_DIR / 'scraping_summary.html'}")

def main():
    """Main execution function."""
    logger.info("Starting Step 4: Article Scraper")
    
    try:
        # Initialize scraper
        scraper = ArticleScraper()
        
        if not scraper.filtered_urls:
            logger.error("No URLs to process. Check approved domains and raw URLs.")
            return
        
        # Run scraping
        scraper.run_scraping(max_workers=5)
        
        # Save results
        scraper.save_results()
        
        logger.info("Step 4 completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
