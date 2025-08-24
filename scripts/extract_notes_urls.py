#!/usr/bin/env python3
"""
Mingus Financial Wellness App - Apple Notes URL Extraction & Analysis

This script extracts URLs from Apple Notes on macOS, analyzes domains using the same
intelligence as Step 2, and integrates them with the existing domain approval workflow.

Features:
- Extract URLs from Apple Notes database (SQLite)
- Parse both plain text and rich text note content
- Filter for financial/career/professional development content
- Analyze domains using Step 2 intelligence logic
- Output in same format as email/bookmark domains
- Integrate with existing approval interface
- Handle encrypted/locked notes gracefully
- Cross-reference with already approved domains

Apple Notes Database Access:
- Primary: ~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
- Fallback: ~/Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV7.storedata

Author: Mingus Development Team
Date: 2025
"""

import os
import sys
import sqlite3
import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
import logging
from collections import defaultdict, Counter
import hashlib
import base64
import zlib
from urllib.parse import urlparse, parse_qs, urlencode

# Import Step 2 analysis functions
try:
    from step2_domain_intelligence import DomainIntelligenceAnalyzer
except ImportError:
    print("Warning: Step 2 intelligence module not found. Using simplified analysis.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/notes_extraction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("../data")
CONFIG_DIR = Path("../config")
REPORTS_DIR = Path("../reports")

# Apple Notes database paths
NOTES_DB_PATHS = [
    Path.home() / "Library/Group Containers/group.com.apple.notes/NoteStore.sqlite",
    Path.home() / "Library/Containers/com.apple.Notes/Data/Library/Notes/NotesV7.storedata"
]

# Financial/career keywords for filtering
FINANCIAL_KEYWORDS = [
    'finance', 'financial', 'money', 'investment', 'investing', 'wealth', 'budget',
    'saving', 'retirement', '401k', 'ira', 'stock', 'market', 'trading', 'portfolio',
    'credit', 'debt', 'loan', 'mortgage', 'insurance', 'tax', 'taxes', 'accounting',
    'banking', 'bank', 'credit union', 'payroll', 'salary', 'income', 'revenue',
    'profit', 'loss', 'expense', 'cash', 'cashflow', 'dividend', 'interest',
    'compound', 'inflation', 'deflation', 'recession', 'economy', 'economic',
    'dollar', 'cent', 'buck', 'money', 'cash', 'fund', 'capital', 'asset',
    'liability', 'equity', 'balance', 'statement', 'report', 'quarterly',
    'annual', 'fiscal', 'year', 'month', 'week', 'daily', 'hourly', 'rate',
    'investing'  # Additional keyword
]

CAREER_KEYWORDS = [
    'career', 'job', 'employment', 'work', 'professional', 'business', 'entrepreneur',
    'startup', 'company', 'corporate', 'office', 'workplace', 'leadership', 'management',
    'executive', 'ceo', 'cfo', 'cto', 'director', 'manager', 'supervisor', 'team',
    'resume', 'cv', 'interview', 'hiring', 'recruitment', 'hr', 'human resources',
    'salary', 'compensation', 'benefits', 'promotion', 'advancement', 'skills',
    'training', 'education', 'certification', 'degree', 'mba', 'phd', 'mentor',
    'networking', 'linkedin', 'professional development', 'workshop', 'conference',
    'industry', 'sector', 'market', 'competition', 'strategy', 'planning',
    'position', 'role', 'title', 'department', 'division', 'branch', 'location',
    'remote', 'hybrid', 'onsite', 'full-time', 'part-time', 'contract', 'freelance',
    'consultant', 'advisor', 'specialist', 'analyst', 'coordinator', 'assistant',
    'career', 'work', 'skills'  # Additional keywords
]

AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS = [
    'diversity', 'inclusion', 'equity', 'black', 'african american', 'minority',
    'representation', 'mentorship', 'networking', 'professional development',
    'career advancement', 'leadership', 'executive', 'board', 'director',
    'entrepreneur', 'business owner', 'startup', 'wealth building', 'financial literacy',
    'community', 'advocacy', 'empowerment', 'success', 'achievement', 'excellence',
    'role model', 'inspiration', 'motivation', 'perseverance', 'resilience',
    'culture', 'heritage', 'identity', 'pride', 'excellence', 'trailblazer',
    'pioneer', 'innovator', 'leader', 'visionary', 'strategist', 'advisor'
]

# Additional lifestyle and personal development keywords
LIFESTYLE_KEYWORDS = [
    'relationships', 'kids', 'family', 'faith', 'health', 'reflection', 'news',
    'personal development', 'wellness', 'mindfulness', 'balance', 'growth',
    'happiness', 'fulfillment', 'purpose', 'meaning', 'values', 'priorities',
    'goals', 'aspirations', 'dreams', 'vision', 'legacy', 'impact', 'contribution',
    'service', 'giving', 'philanthropy', 'volunteer', 'community service',
    'spirituality', 'religion', 'meditation', 'prayer', 'gratitude', 'appreciation',
    'relationships', 'marriage', 'parenting', 'children', 'family', 'home',
    'lifestyle', 'wellbeing', 'fitness', 'nutrition', 'mental health', 'self-care'
]

@dataclass
class ExtractedNoteURL:
    """Data structure for extracted URL from Apple Notes"""
    url: str
    original_url: str
    note_title: str
    note_date: str
    note_id: str
    surrounding_text: str
    domain: str
    extraction_confidence: float
    note_quality_score: float
    context_keywords: List[str]

@dataclass
class NotesDomainAnalysis:
    """Data structure for domain analysis from notes"""
    domain: str
    url_count: int
    note_count: int
    avg_note_quality_score: float
    category_suggestion: str
    confidence: float
    recommendation: str
    reasoning: str
    priority: str
    sample_urls: List[str]
    note_titles: List[str]

class AppleNotesExtractor:
    """Main class for extracting URLs from Apple Notes"""
    
    def __init__(self):
        self.extracted_urls = []
        self.domain_analyzer = None
        self.notes_db_path = None
        self.setup_analyzer()
        self.find_notes_database()
        
        # URL extraction patterns
        self.url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.url_patterns]
        
        # Domain categories for automatic classification
        self.domain_categories = {
            'financial': ['bank', 'credit', 'loan', 'mortgage', 'investment', 'trading', 'finance', 'wealth', 'money'],
            'news_media': ['news', 'times', 'post', 'journal', 'tribune', 'herald', 'press', 'media', 'reuters', 'bloomberg'],
            'educational': ['.edu', 'university', 'college', 'school', 'academy', 'institute', 'course', 'learning'],
            'career': ['linkedin', 'indeed', 'glassdoor', 'monster', 'career', 'job', 'employment', 'professional'],
            'social_media': ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'snapchat'],
            'ecommerce': ['amazon', 'ebay', 'shop', 'store', 'buy', 'purchase', 'retail', 'marketplace'],
            'government': ['.gov', 'government', 'federal', 'state', 'city', 'official'],
            'blog_platform': ['wordpress', 'blogger', 'medium', 'substack', 'ghost', 'blog'],
        }
    
    def setup_analyzer(self):
        """Setup domain analyzer from Step 2"""
        try:
            self.domain_analyzer = DomainIntelligenceAnalyzer()
            logger.info("Step 2 domain analyzer loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load Step 2 analyzer: {e}")
            self.domain_analyzer = None
    
    def find_notes_database(self):
        """Find the Apple Notes database file"""
        for db_path in NOTES_DB_PATHS:
            if db_path.exists():
                self.notes_db_path = db_path
                logger.info(f"Found Notes database: {db_path}")
                return
        
        logger.error("Could not find Apple Notes database")
        raise FileNotFoundError("Apple Notes database not found")
    
    def clean_url(self, url: str) -> str:
        """Clean URL by removing tracking parameters and normalizing"""
        try:
            # Add protocol if missing
            if url.startswith('www.'):
                url = 'https://' + url
            
            # Parse URL
            parsed = urlparse(url)
            
            # Remove tracking parameters
            query_params = parse_qs(parsed.query)
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'campaign', 'medium',
                'term', 'content', 'click_id', 'session_id', 'user_id', 'tracking',
                'analytics', 'pixel', 'beacon', 'monitor', 'log', 'stats'
            ]
            
            cleaned_params = {}
            for key, value in query_params.items():
                if key.lower() not in [p.lower() for p in tracking_params]:
                    cleaned_params[key] = value
            
            # Rebuild URL
            cleaned_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
            cleaned_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if cleaned_query:
                cleaned_url += f"?{cleaned_query}"
            if parsed.fragment:
                cleaned_url += f"#{parsed.fragment}"
            
            return cleaned_url
        except Exception as e:
            logger.warning(f"Error cleaning URL {url}: {e}")
            return url
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            if url.startswith('www.'):
                url = 'https://' + url
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception as e:
            logger.warning(f"Error extracting domain from {url}: {e}")
            return url
    
    def calculate_note_quality_score(self, note_title: str, note_content: str) -> float:
        """Calculate quality score for a note based on keywords and content"""
        score = 0.0
        title_lower = note_title.lower()
        content_lower = note_content.lower()
        
        # Check for financial keywords
        for keyword in FINANCIAL_KEYWORDS:
            if keyword in title_lower:
                score += 0.3
            if keyword in content_lower:
                score += 0.1
        
        # Check for career keywords
        for keyword in CAREER_KEYWORDS:
            if keyword in title_lower:
                score += 0.3
            if keyword in content_lower:
                score += 0.1
        
        # Check for African American professional keywords
        for keyword in AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS:
            if keyword in title_lower:
                score += 0.4
            if keyword in content_lower:
                score += 0.15
        
        # Check for lifestyle and personal development keywords
        for keyword in LIFESTYLE_KEYWORDS:
            if keyword in title_lower:
                score += 0.25
            if keyword in content_lower:
                score += 0.08
        
        # Bonus for longer, more detailed notes
        if len(note_content) > 500:
            score += 0.2
        elif len(note_content) > 200:
            score += 0.1
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    def get_context_keywords(self, note_title: str, surrounding_text: str) -> List[str]:
        """Extract relevant keywords from note context"""
        keywords = []
        text_to_analyze = f"{note_title} {surrounding_text}".lower()
        
        # Check for financial keywords
        for keyword in FINANCIAL_KEYWORDS:
            if keyword in text_to_analyze:
                keywords.append(keyword)
        
        # Check for career keywords
        for keyword in CAREER_KEYWORDS:
            if keyword in text_to_analyze:
                keywords.append(keyword)
        
        # Check for African American professional keywords
        for keyword in AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS:
            if keyword in text_to_analyze:
                keywords.append(keyword)
        
        # Check for lifestyle and personal development keywords
        for keyword in LIFESTYLE_KEYWORDS:
            if keyword in text_to_analyze:
                keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def parse_rich_text_content(self, content_data: bytes) -> str:
        """Parse rich text content from Apple Notes database"""
        try:
            # Try to decompress if it's zlib compressed
            try:
                decompressed = zlib.decompress(content_data)
                content_data = decompressed
            except:
                pass  # Not compressed
            
            # Try to decode as UTF-8
            try:
                content = content_data.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        content = content_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    content = content_data.decode('utf-8', errors='ignore')
            
            # Remove HTML tags if present
            content = re.sub(r'<[^>]+>', '', content)
            
            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
        except Exception as e:
            logger.warning(f"Error parsing rich text content: {e}")
            return ""
    
    def extract_urls_from_notes(self) -> List[ExtractedNoteURL]:
        """Extract URLs from Apple Notes database"""
        extracted_urls = []
        
        try:
            # Connect to Notes database
            conn = sqlite3.connect(self.notes_db_path)
            conn.row_factory = sqlite3.Row
            
            # Query to get notes with content
            query = """
            SELECT 
                ZICCLOUDSYNCINGOBJECT.Z_PK as note_id,
                ZICCLOUDSYNCINGOBJECT.ZTITLE1 as title,
                ZICCLOUDSYNCINGOBJECT.ZCREATIONDATE1 as creation_date,
                ZICCLOUDSYNCINGOBJECT.ZMODIFICATIONDATE1 as modification_date,
                ZNOTEBODY.ZDATA as content_data,
                ZNOTEBODY.ZLENGTH as content_length
            FROM ZICCLOUDSYNCINGOBJECT
            LEFT JOIN ZNOTEBODY ON ZICCLOUDSYNCINGOBJECT.Z_PK = ZNOTEBODY.ZNOTE
            WHERE ZICCLOUDSYNCINGOBJECT.Z_ENT = 1  -- Note entities
            AND (ZICCLOUDSYNCINGOBJECT.ZTITLE1 IS NOT NULL 
                 OR ZNOTEBODY.ZDATA IS NOT NULL)
            """
            
            cursor = conn.execute(query)
            notes = cursor.fetchall()
            
            logger.info(f"Found {len(notes)} notes to process")
            
            for note in notes:
                try:
                    note_id = note['note_id']
                    note_title = note['title'] or "Untitled Note"
                    creation_date = note['creation_date']
                    modification_date = note['modification_date']
                    content_data = note['content_data']
                    
                    # Convert Apple timestamp to readable date
                    if creation_date:
                        creation_date = datetime.fromtimestamp(creation_date + 978307200).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        creation_date = "Unknown"
                    
                    # Parse note content
                    note_content = ""
                    if content_data:
                        note_content = self.parse_rich_text_content(content_data)
                    
                    # Calculate note quality score
                    note_quality_score = self.calculate_note_quality_score(note_title, note_content)
                    
                    # Extract URLs from title and content
                    all_text = f"{note_title} {note_content}"
                    
                    for pattern in self.compiled_patterns:
                        matches = pattern.findall(all_text)
                        
                        for match in matches:
                            try:
                                # Clean URL
                                cleaned_url = self.clean_url(match)
                                domain = self.extract_domain(cleaned_url)
                                
                                # Get surrounding text context
                                surrounding_text = self.get_surrounding_text(all_text, match, 100)
                                
                                # Get context keywords
                                context_keywords = self.get_context_keywords(note_title, surrounding_text)
                                
                                # Calculate extraction confidence
                                extraction_confidence = 0.8  # Base confidence
                                if note_quality_score > 0.5:
                                    extraction_confidence += 0.2
                                if context_keywords:
                                    extraction_confidence += 0.1
                                
                                extracted_url = ExtractedNoteURL(
                                    url=cleaned_url,
                                    original_url=match,
                                    note_title=note_title,
                                    note_date=creation_date,
                                    note_id=str(note_id),
                                    surrounding_text=surrounding_text,
                                    domain=domain,
                                    extraction_confidence=min(extraction_confidence, 1.0),
                                    note_quality_score=note_quality_score,
                                    context_keywords=context_keywords
                                )
                                
                                extracted_urls.append(extracted_url)
                                
                            except Exception as e:
                                logger.warning(f"Error processing URL {match} from note {note_id}: {e}")
                                continue
                
                except Exception as e:
                    logger.warning(f"Error processing note {note.get('note_id', 'unknown')}: {e}")
                    continue
            
            conn.close()
            logger.info(f"Successfully extracted {len(extracted_urls)} URLs from {len(notes)} notes")
            
        except Exception as e:
            logger.error(f"Error accessing Notes database: {e}")
            raise
        
        return extracted_urls
    
    def get_surrounding_text(self, text: str, url: str, context_length: int = 100) -> str:
        """Get text surrounding a URL for context"""
        try:
            url_index = text.find(url)
            if url_index == -1:
                return ""
            
            start = max(0, url_index - context_length)
            end = min(len(text), url_index + len(url) + context_length)
            
            surrounding = text[start:end]
            
            # Clean up the surrounding text
            surrounding = re.sub(r'\s+', ' ', surrounding).strip()
            
            return surrounding
        except Exception as e:
            logger.warning(f"Error getting surrounding text: {e}")
            return ""
    
    def analyze_domains(self, extracted_urls: List[ExtractedNoteURL]) -> Dict[str, NotesDomainAnalysis]:
        """Analyze domains using Step 2 intelligence"""
        domain_stats = defaultdict(lambda: {
            'urls': [],
            'note_count': 0,
            'note_titles': set(),
            'quality_scores': [],
            'context_keywords': set()
        })
        
        # Group URLs by domain
        for url_data in extracted_urls:
            domain = url_data.domain
            domain_stats[domain]['urls'].append(url_data.url)
            domain_stats[domain]['note_count'] += 1
            domain_stats[domain]['note_titles'].add(url_data.note_title)
            domain_stats[domain]['quality_scores'].append(url_data.note_quality_score)
            domain_stats[domain]['context_keywords'].update(url_data.context_keywords)
        
        # Analyze each domain
        domain_analyses = {}
        
        for domain, stats in domain_stats.items():
            try:
                # Calculate domain statistics
                url_count = len(stats['urls'])
                note_count = stats['note_count']
                avg_quality_score = sum(stats['quality_scores']) / len(stats['quality_scores'])
                
                # Use Step 2 analyzer if available
                if self.domain_analyzer:
                    # This would integrate with Step 2 analysis
                    # For now, use simplified analysis
                    category_suggestion = self.categorize_domain(domain)
                    confidence = min(avg_quality_score + 0.3, 1.0)
                else:
                    category_suggestion = self.categorize_domain(domain)
                    confidence = min(avg_quality_score + 0.3, 1.0)
                
                # Determine recommendation
                recommendation, reasoning = self.get_domain_recommendation(
                    domain, url_count, avg_quality_score
                )
                
                # Determine priority
                priority = self.get_domain_priority(domain, url_count, avg_quality_score)
                
                domain_analysis = NotesDomainAnalysis(
                    domain=domain,
                    url_count=url_count,
                    note_count=note_count,
                    avg_note_quality_score=avg_quality_score,
                    category_suggestion=category_suggestion,
                    confidence=confidence,
                    recommendation=recommendation,
                    reasoning=reasoning,
                    priority=priority,
                    sample_urls=stats['urls'][:5],  # First 5 URLs
                    note_titles=list(stats['note_titles'])[:5]  # First 5 note titles
                )
                
                domain_analyses[domain] = domain_analysis
                
            except Exception as e:
                logger.warning(f"Error analyzing domain {domain}: {e}")
                continue
        
        return domain_analyses
    
    def categorize_domain(self, domain: str) -> str:
        """Categorize domain based on keywords"""
        domain_lower = domain.lower()
        
        for category, keywords in self.domain_categories.items():
            for keyword in keywords:
                if keyword in domain_lower:
                    return category
        
        return "general"
    

    
    def get_domain_recommendation(self, domain: str, url_count: int, 
                                quality_score: float) -> Tuple[str, str]:
        """Get domain recommendation based on analysis"""
        # High quality content
        if quality_score > 0.7:
            return "AUTO_APPROVE", "High-quality financial/career/lifestyle content"
        
        # Medium quality
        if quality_score > 0.5:
            return "MANUAL_REVIEW", "Medium quality content requiring review"
        
        # Low quality
        return "AUTO_REJECT", "Low quality content"
    
    def get_domain_priority(self, domain: str, url_count: int, quality_score: float) -> str:
        """Get domain priority level"""
        if quality_score > 0.8 and url_count > 5:
            return "HIGH"
        elif quality_score > 0.6 and url_count > 3:
            return "MEDIUM"
        else:
            return "NORMAL"
    
    def save_results(self, extracted_urls: List[ExtractedNoteURL], 
                    domain_analyses: Dict[str, NotesDomainAnalysis]):
        """Save extraction results to files"""
        try:
            # Save complete URLs data
            urls_data = []
            for url_data in extracted_urls:
                urls_data.append({
                    'url': url_data.url,
                    'note_title': url_data.note_title,
                    'note_date': url_data.note_date,
                    'surrounding_text': url_data.surrounding_text,
                    'domain': url_data.domain,
                    'extraction_confidence': url_data.extraction_confidence,
                    'note_quality_score': url_data.note_quality_score,
                    'context_keywords': ','.join(url_data.context_keywords)
                })
            
            urls_df = pd.DataFrame(urls_data)
            urls_df.to_csv(DATA_DIR / "notes_urls_complete.csv", index=False)
            
            # Save domain analysis
            domain_data = []
            for domain, analysis in domain_analyses.items():
                domain_data.append({
                    'domain': analysis.domain,
                    'url_count': analysis.url_count,
                    'note_count': analysis.note_count,
                    'avg_note_quality_score': analysis.avg_note_quality_score,
                    'category_suggestion': analysis.category_suggestion,
                    'confidence': analysis.confidence,
                    'recommendation': analysis.recommendation,
                    'reasoning': analysis.reasoning,
                    'priority': analysis.priority,
                    'sample_urls': ';'.join(analysis.sample_urls),
                    'note_titles': ';'.join(analysis.note_titles)
                })
            
            domain_df = pd.DataFrame(domain_data)
            domain_df.to_csv(DATA_DIR / "notes_domain_analysis.csv", index=False)
            
            # Save domain recommendations in JSON format
            recommendations = {}
            for domain, analysis in domain_analyses.items():
                recommendations[domain] = {
                    'recommendation': analysis.recommendation,
                    'confidence': analysis.confidence,
                    'reasoning': analysis.reasoning,
                    'quality_score': analysis.avg_note_quality_score,
                    'url_count': analysis.url_count,
                    'priority': analysis.priority,
                    'source': 'notes'
                }
            
            with open(DATA_DIR / "notes_recommendations.json", 'w') as f:
                json.dump(recommendations, f, indent=2)
            
            # Save processing summary
            summary = {
                'extraction_date': datetime.now().isoformat(),
                'total_urls_extracted': len(extracted_urls),
                'unique_domains': len(domain_analyses),
                'total_notes_processed': len(set(url.note_id for url in extracted_urls)),
                'avg_quality_score': sum(url.note_quality_score for url in extracted_urls) / len(extracted_urls) if extracted_urls else 0,
                'recommendations': {
                    'auto_approve': len([d for d in domain_analyses.values() if d.recommendation == 'AUTO_APPROVE']),
                    'manual_review': len([d for d in domain_analyses.values() if d.recommendation == 'MANUAL_REVIEW']),
                    'auto_reject': len([d for d in domain_analyses.values() if d.recommendation == 'AUTO_REJECT'])
                }
            }
            
            with open(DATA_DIR / "notes_processing_summary.json", 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Results saved to {DATA_DIR}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
    
    def run_extraction(self):
        """Main extraction process"""
        logger.info("Starting Apple Notes URL extraction...")
        
        try:
            # Extract URLs from notes
            extracted_urls = self.extract_urls_from_notes()
            
            if not extracted_urls:
                logger.warning("No URLs found in Apple Notes")
                return
            
            # Analyze domains
            domain_analyses = self.analyze_domains(extracted_urls)
            
            # Save results
            self.save_results(extracted_urls, domain_analyses)
            
            # Print summary
            print(f"\n=== Apple Notes Extraction Summary ===")
            print(f"Total URLs extracted: {len(extracted_urls)}")
            print(f"Unique domains found: {len(domain_analyses)}")
            print(f"Notes processed: {len(set(url.note_id for url in extracted_urls))}")
            
            auto_approve = len([d for d in domain_analyses.values() if d.recommendation == 'AUTO_APPROVE'])
            manual_review = len([d for d in domain_analyses.values() if d.recommendation == 'MANUAL_REVIEW'])
            auto_reject = len([d for d in domain_analyses.values() if d.recommendation == 'AUTO_REJECT'])
            
            print(f"Auto-approve domains: {auto_approve}")
            print(f"Manual review domains: {manual_review}")
            print(f"Auto-reject domains: {auto_reject}")
            
            logger.info("Apple Notes extraction completed successfully")
            
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            raise

def main():
    """Main function"""
    try:
        extractor = AppleNotesExtractor()
        extractor.run_extraction()
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
