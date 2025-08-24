#!/usr/bin/env python3
"""
Mingus Financial Wellness App - Bookmark Domain Extraction & Analysis

This script extracts URLs from browser bookmarks (Chrome, Safari, Firefox),
analyzes domains using the same intelligence as Step 2, and integrates
them with the existing domain approval workflow.

Features:
- Extract bookmarks from Chrome, Safari, Firefox
- Filter for financial/career/professional development content
- Analyze domains using Step 2 intelligence logic
- Output in same format as email domains
- Integrate with existing approval interface

Author: Mingus Development Team
Date: 2025
"""

import os
import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd

# Import Step 2 analysis functions
try:
    from step2_domain_intelligence import DomainAnalyzer, analyze_domain_quality, calculate_cultural_relevance
except ImportError:
    print("Warning: Step 2 intelligence module not found. Using simplified analysis.")

# Configuration
DATA_DIR = Path("../data")
CONFIG_DIR = Path("../config")
REPORTS_DIR = Path("../reports")

# Browser bookmark paths
CHROME_BOOKMARKS = Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks"
SAFARI_BOOKMARKS = Path.home() / "Library/Safari/Bookmarks.plist"
FIREFOX_BOOKMARKS = Path.home() / "Library/Application Support/Firefox/Profiles"

# Financial/career keywords for filtering
FINANCIAL_KEYWORDS = [
    'finance', 'financial', 'money', 'investment', 'investing', 'wealth', 'budget',
    'saving', 'retirement', '401k', 'ira', 'stock', 'market', 'trading', 'portfolio',
    'credit', 'debt', 'loan', 'mortgage', 'insurance', 'tax', 'taxes', 'accounting',
    'banking', 'bank', 'credit union', 'payroll', 'salary', 'income', 'revenue',
    'profit', 'loss', 'expense', 'cash', 'cashflow', 'dividend', 'interest',
    'compound', 'inflation', 'deflation', 'recession', 'economy', 'economic'
]

CAREER_KEYWORDS = [
    'career', 'job', 'employment', 'work', 'professional', 'business', 'entrepreneur',
    'startup', 'company', 'corporate', 'office', 'workplace', 'leadership', 'management',
    'executive', 'ceo', 'cfo', 'cto', 'director', 'manager', 'supervisor', 'team',
    'resume', 'cv', 'interview', 'hiring', 'recruitment', 'hr', 'human resources',
    'salary', 'compensation', 'benefits', 'promotion', 'advancement', 'skills',
    'training', 'education', 'certification', 'degree', 'mba', 'phd', 'mentor',
    'networking', 'linkedin', 'professional development', 'workshop', 'conference',
    'industry', 'sector', 'market', 'competition', 'strategy', 'planning'
]

AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS = [
    'diversity', 'inclusion', 'equity', 'black', 'african american', 'minority',
    'representation', 'mentorship', 'networking', 'professional development',
    'career advancement', 'leadership', 'executive', 'board', 'director',
    'entrepreneur', 'business owner', 'startup', 'wealth building', 'financial literacy',
    'community', 'advocacy', 'empowerment', 'success', 'achievement', 'excellence',
    'role model', 'inspiration', 'motivation', 'perseverance', 'resilience'
]

@dataclass
class BookmarkDomain:
    domain: str
    urls: List[str]
    title: str
    description: str
    category: str
    quality_score: float
    cultural_relevance_score: float
    confidence: float
    recommendation: str
    reasoning: str
    priority: str
    sample_urls: List[str]
    url_count: int

class BookmarkExtractor:
    def __init__(self):
        self.extracted_urls = []
        self.domain_analyzer = None
        self.setup_analyzer()
    
    def setup_analyzer(self):
        """Setup domain analyzer from Step 2"""
        try:
            from step2_domain_intelligence import DomainAnalyzer
            self.domain_analyzer = DomainAnalyzer()
            print("✅ Step 2 domain analyzer loaded")
        except ImportError:
            print("⚠️  Step 2 analyzer not available, using simplified analysis")
            self.domain_analyzer = None
    
    def extract_chrome_bookmarks(self) -> List[Dict[str, Any]]:
        """Extract bookmarks from Chrome"""
        bookmarks = []
        
        if not CHROME_BOOKMARKS.exists():
            print(f"❌ Chrome bookmarks not found at: {CHROME_BOOKMARKS}")
            return bookmarks
        
        try:
            with open(CHROME_BOOKMARKS, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def extract_bookmarks_recursive(obj, folder_name=""):
                if isinstance(obj, dict):
                    if obj.get('type') == 'url':
                        bookmark = {
                            'url': obj.get('url', ''),
                            'title': obj.get('name', ''),
                            'date_added': obj.get('date_added', ''),
                            'folder': folder_name,
                            'browser': 'Chrome'
                        }
                        if self.is_relevant_bookmark(bookmark):
                            bookmarks.append(bookmark)
                    elif obj.get('type') == 'folder':
                        folder_name = obj.get('name', '')
                        for child in obj.get('children', []):
                            extract_bookmarks_recursive(child, folder_name)
                    else:
                        for child in obj.get('children', []):
                            extract_bookmarks_recursive(child, folder_name)
            
            # Extract from bookmarks bar
            if 'roots' in data:
                if 'bookmark_bar' in data['roots']:
                    extract_bookmarks_recursive(data['roots']['bookmark_bar'], 'Bookmarks Bar')
                if 'other' in data['roots']:
                    extract_bookmarks_recursive(data['roots']['other'], 'Other Bookmarks')
            
            print(f"✅ Extracted {len(bookmarks)} relevant bookmarks from Chrome")
            return bookmarks
            
        except Exception as e:
            print(f"❌ Error extracting Chrome bookmarks: {e}")
            return bookmarks
    
    def extract_safari_bookmarks(self) -> List[Dict[str, Any]]:
        """Extract bookmarks from Safari"""
        bookmarks = []
        
        if not SAFARI_BOOKMARKS.exists():
            print(f"❌ Safari bookmarks not found at: {SAFARI_BOOKMARKS}")
            return bookmarks
        
        try:
            # Safari bookmarks are in plist format, but we'll use a simpler approach
            # For now, we'll provide instructions for manual export
            print("ℹ️  Safari bookmarks are in plist format. Please export to HTML format manually.")
            print("   File > Export Bookmarks > Save as bookmarks.html")
            print("   Then use the manual input option to add the exported file.")
            return bookmarks
            
        except Exception as e:
            print(f"❌ Error extracting Safari bookmarks: {e}")
            return bookmarks
    
    def extract_firefox_bookmarks(self) -> List[Dict[str, Any]]:
        """Extract bookmarks from Firefox"""
        bookmarks = []
        
        if not FIREFOX_BOOKMARKS.exists():
            print(f"❌ Firefox bookmarks not found at: {FIREFOX_BOOKMARKS}")
            return bookmarks
        
        try:
            # Find Firefox profile directories
            profiles = list(FIREFOX_BOOKMARKS.glob("*"))
            for profile in profiles:
                if profile.is_dir():
                    places_db = profile / "places.sqlite"
                    if places_db.exists():
                        print(f"ℹ️  Firefox profile found: {profile.name}")
                        print("   Please export bookmarks manually: Bookmarks > Manage Bookmarks > Export")
                        print("   Then use the manual input option to add the exported file.")
                        break
            
            return bookmarks
            
        except Exception as e:
            print(f"❌ Error extracting Firefox bookmarks: {e}")
            return bookmarks
    
    def extract_from_html_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract bookmarks from exported HTML file"""
        bookmarks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse HTML bookmarks
            root = ET.fromstring(content)
            
            # Find all anchor tags
            for link in root.findall('.//a'):
                href = link.get('href', '')
                title = link.text or ''
                add_date = link.get('add_date', '')
                
                if href and href.startswith('http'):
                    bookmark = {
                        'url': href,
                        'title': title,
                        'date_added': add_date,
                        'folder': 'Imported',
                        'browser': 'HTML Export'
                    }
                    if self.is_relevant_bookmark(bookmark):
                        bookmarks.append(bookmark)
            
            print(f"✅ Extracted {len(bookmarks)} relevant bookmarks from HTML file")
            return bookmarks
            
        except Exception as e:
            print(f"❌ Error extracting from HTML file: {e}")
            return bookmarks
    
    def is_relevant_bookmark(self, bookmark: Dict[str, Any]) -> bool:
        """Check if bookmark is relevant to financial/career content"""
        url = bookmark.get('url', '').lower()
        title = bookmark.get('title', '').lower()
        
        # Check for financial/career keywords
        all_keywords = FINANCIAL_KEYWORDS + CAREER_KEYWORDS + AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS
        
        for keyword in all_keywords:
            if keyword in url or keyword in title:
                return True
        
        # Check for common financial/career domains
        financial_domains = [
            'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com', 'cnbc.com',
            'marketwatch.com', 'yahoo.com/finance', 'finance.yahoo.com',
            'morningstar.com', 'fool.com', 'investopedia.com', 'nerdwallet.com',
            'creditkarma.com', 'mint.com', 'personalcapital.com', 'betterment.com',
            'wealthfront.com', 'robinhood.com', 'tdameritrade.com', 'fidelity.com',
            'vanguard.com', 'schwab.com', 'etrade.com', 'linkedin.com',
            'glassdoor.com', 'indeed.com', 'monster.com', 'careerbuilder.com',
            'ziprecruiter.com', 'dice.com', 'angel.co', 'crunchbase.com'
        ]
        
        for domain in financial_domains:
            if domain in url:
                return True
        
        return False
    
    def extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        except:
            return ""
    
    def group_urls_by_domain(self, bookmarks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group bookmarks by domain"""
        domains = {}
        
        for bookmark in bookmarks:
            domain = self.extract_domain_from_url(bookmark['url'])
            if domain:
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(bookmark)
        
        return domains
    
    def analyze_domain_quality(self, domain: str, urls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze domain quality using Step 2 logic"""
        if self.domain_analyzer:
            # Use Step 2 analyzer
            return self.domain_analyzer.analyze_domain(domain, urls)
        else:
            # Simplified analysis
            return self.simplified_domain_analysis(domain, urls)
    
    def simplified_domain_analysis(self, domain: str, urls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simplified domain analysis when Step 2 analyzer is not available"""
        url_count = len(urls)
        
        # Basic quality scoring
        quality_score = 0.5  # Default medium quality
        
        # Check for high-quality indicators
        high_quality_domains = [
            'bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com', 'cnbc.com',
            'marketwatch.com', 'morningstar.com', 'fool.com', 'investopedia.com',
            'linkedin.com', 'glassdoor.com', 'indeed.com'
        ]
        
        if domain in high_quality_domains:
            quality_score = 0.8
        
        # Check for low-quality indicators
        low_quality_indicators = [
            'blogspot.com', 'wordpress.com', 'tumblr.com', 'medium.com',
            'reddit.com', 'facebook.com', 'twitter.com', 'instagram.com'
        ]
        
        for indicator in low_quality_indicators:
            if indicator in domain:
                quality_score = 0.3
                break
        
        # Cultural relevance scoring
        cultural_relevance = 0.0
        
        # Check for African American professional content
        african_american_keywords = [
            'black', 'african', 'diversity', 'inclusion', 'minority',
            'representation', 'mentorship', 'empowerment'
        ]
        
        for url_data in urls:
            title = url_data.get('title', '').lower()
            for keyword in african_american_keywords:
                if keyword in title:
                    cultural_relevance += 0.2
        
        cultural_relevance = min(cultural_relevance, 1.0)
        
        # Determine recommendation
        if quality_score >= 0.7 and cultural_relevance >= 0.5:
            recommendation = "AUTO_APPROVE"
            confidence = 0.9
        elif quality_score >= 0.5:
            recommendation = "MANUAL_REVIEW"
            confidence = 0.6
        else:
            recommendation = "AUTO_REJECT"
            confidence = 0.8
        
        return {
            'quality_score': quality_score,
            'cultural_relevance_score': cultural_relevance,
            'confidence': confidence,
            'recommendation': recommendation,
            'reasoning': f"Quality: {quality_score:.1f}, Cultural: {cultural_relevance:.1f}",
            'priority': 'NORMAL'
        }
    
    def create_domain_objects(self, domains: Dict[str, List[Dict[str, Any]]]) -> List[BookmarkDomain]:
        """Create BookmarkDomain objects from grouped URLs"""
        domain_objects = []
        
        for domain, urls in domains.items():
            # Analyze domain
            analysis = self.analyze_domain_quality(domain, urls)
            
            # Extract sample URLs
            sample_urls = [url['url'] for url in urls[:5]]
            
            # Create domain object
            domain_obj = BookmarkDomain(
                domain=domain,
                urls=[url['url'] for url in urls],
                title=f"Bookmark Domain: {domain}",
                description=f"Extracted from {len(urls)} bookmarks",
                category="Bookmarks",
                quality_score=analysis['quality_score'],
                cultural_relevance_score=analysis['cultural_relevance_score'],
                confidence=analysis['confidence'],
                recommendation=analysis['recommendation'],
                reasoning=analysis['reasoning'],
                priority=analysis['priority'],
                sample_urls=sample_urls,
                url_count=len(urls)
            )
            
            domain_objects.append(domain_obj)
        
        return domain_objects
    
    def save_bookmark_domains(self, domains: List[BookmarkDomain]):
        """Save bookmark domains to JSON file"""
        domains_data = {}
        
        for domain_obj in domains:
            domains_data[domain_obj.domain] = {
                'recommendation': domain_obj.recommendation,
                'confidence': domain_obj.confidence,
                'reasoning': domain_obj.reasoning,
                'quality_score': domain_obj.quality_score,
                'cultural_relevance_score': domain_obj.cultural_relevance_score,
                'url_count': domain_obj.url_count,
                'priority': domain_obj.priority,
                'sample_urls': domain_obj.sample_urls,
                'source': 'bookmarks',
                'extraction_date': datetime.now().isoformat()
            }
        
        output_file = DATA_DIR / "bookmark_domains.json"
        with open(output_file, 'w') as f:
            json.dump(domains_data, f, indent=2)
        
        print(f"✅ Saved {len(domains)} bookmark domains to {output_file}")
    
    def merge_with_existing_domains(self, bookmark_domains: List[BookmarkDomain]):
        """Merge bookmark domains with existing domain recommendations"""
        try:
            # Load existing domains
            existing_file = DATA_DIR / "domain_recommendations.json"
            if existing_file.exists():
                with open(existing_file, 'r') as f:
                    existing_domains = json.load(f)
            else:
                existing_domains = {}
            
            # Add bookmark domains
            bookmark_data = {}
            for domain_obj in bookmark_domains:
                bookmark_data[domain_obj.domain] = {
                    'recommendation': domain_obj.recommendation,
                    'confidence': domain_obj.confidence,
                    'reasoning': domain_obj.reasoning,
                    'quality_score': domain_obj.quality_score,
                    'cultural_relevance_score': domain_obj.cultural_relevance_score,
                    'url_count': domain_obj.url_count,
                    'priority': domain_obj.priority,
                    'sample_urls': domain_obj.sample_urls,
                    'source': 'bookmarks',
                    'extraction_date': datetime.now().isoformat()
                }
            
            # Merge (bookmark domains take precedence for duplicates)
            existing_domains.update(bookmark_data)
            
            # Save merged data
            with open(existing_file, 'w') as f:
                json.dump(existing_domains, f, indent=2)
            
            print(f"✅ Merged {len(bookmark_domains)} bookmark domains with existing {len(existing_domains)} domains")
            
        except Exception as e:
            print(f"❌ Error merging domains: {e}")
    
    def generate_report(self, domains: List[BookmarkDomain]):
        """Generate extraction report"""
        report = {
            'extraction_date': datetime.now().isoformat(),
            'total_bookmark_domains': len(domains),
            'auto_approve_count': len([d for d in domains if d.recommendation == 'AUTO_APPROVE']),
            'manual_review_count': len([d for d in domains if d.recommendation == 'MANUAL_REVIEW']),
            'auto_reject_count': len([d for d in domains if d.recommendation == 'AUTO_REJECT']),
            'high_cultural_relevance_count': len([d for d in domains if d.cultural_relevance_score >= 0.7]),
            'domains': [asdict(d) for d in domains]
        }
        
        report_file = REPORTS_DIR / "bookmark_extraction_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Generated extraction report: {report_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("BOOKMARK EXTRACTION SUMMARY")
        print("="*50)
        print(f"Total Domains: {report['total_bookmark_domains']}")
        print(f"Auto-Approve: {report['auto_approve_count']}")
        print(f"Manual Review: {report['manual_review_count']}")
        print(f"Auto-Reject: {report['auto_reject_count']}")
        print(f"High Cultural Relevance: {report['high_cultural_relevance_count']}")
        print("="*50)
    
    def run_extraction(self, html_file: Optional[str] = None):
        """Run complete bookmark extraction process"""
        print("🔍 Starting bookmark extraction...")
        
        all_bookmarks = []
        
        # Extract from Chrome
        chrome_bookmarks = self.extract_chrome_bookmarks()
        all_bookmarks.extend(chrome_bookmarks)
        
        # Extract from Safari (manual export required)
        safari_bookmarks = self.extract_safari_bookmarks()
        all_bookmarks.extend(safari_bookmarks)
        
        # Extract from Firefox (manual export required)
        firefox_bookmarks = self.extract_firefox_bookmarks()
        all_bookmarks.extend(firefox_bookmarks)
        
        # Extract from HTML file if provided
        if html_file and os.path.exists(html_file):
            html_bookmarks = self.extract_from_html_file(html_file)
            all_bookmarks.extend(html_bookmarks)
        
        if not all_bookmarks:
            print("❌ No bookmarks found. Please check browser paths or provide HTML export file.")
            return
        
        print(f"📊 Found {len(all_bookmarks)} total bookmarks")
        
        # Group by domain
        domains = self.group_urls_by_domain(all_bookmarks)
        print(f"🌐 Grouped into {len(domains)} unique domains")
        
        # Create domain objects
        domain_objects = self.create_domain_objects(domains)
        
        # Save bookmark domains
        self.save_bookmark_domains(domain_objects)
        
        # Merge with existing domains
        self.merge_with_existing_domains(domain_objects)
        
        # Generate report
        self.generate_report(domain_objects)
        
        print("\n🎉 Bookmark extraction complete!")
        print("Next steps:")
        print("1. Run the domain approval interface to review new domains")
        print("2. Use bulk operations to quickly process bookmark domains")
        print("3. Export approved domains for Step 4 article scraping")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract and analyze browser bookmarks')
    parser.add_argument('--html-file', help='Path to exported bookmarks HTML file')
    parser.add_argument('--chrome-only', action='store_true', help='Extract only from Chrome')
    parser.add_argument('--no-merge', action='store_true', help='Do not merge with existing domains')
    
    args = parser.parse_args()
    
    # Create necessary directories
    DATA_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Run extraction
    extractor = BookmarkExtractor()
    extractor.run_extraction(html_file=args.html_file)

if __name__ == "__main__":
    main()
