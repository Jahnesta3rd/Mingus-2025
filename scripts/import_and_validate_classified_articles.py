#!/usr/bin/env python3
"""
Import and Validate Classified Articles Script
Imports classified articles from Step 5 and validates all requirements:
- Be-Do-Have classifications
- Cultural relevance scores
- Search vectors for full-text search
- Article access control requirements
"""

import sys
import os
import json
import uuid
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple, Set
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('article_import_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArticleImportValidator:
    """Comprehensive article import and validation system"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
        self.engine = None
        self.session = None
        self.inspector = None
        
        # Validation statistics
        self.stats = {
            'total_articles': 0,
            'imported': 0,
            'skipped': 0,
            'failed': 0,
            'validation_errors': [],
            'classification_issues': [],
            'cultural_relevance_issues': [],
            'search_vector_issues': [],
            'access_control_issues': []
        }
        
        # Be-Do-Have validation rules
        self.be_keywords = {
            'mindset', 'identity', 'beliefs', 'confidence', 'self-worth', 'attitude',
            'perspective', 'philosophy', 'mental', 'psychological', 'emotional',
            'self-awareness', 'personal development', 'growth mindset', 'abundance mindset'
        }
        
        self.do_keywords = {
            'action', 'strategy', 'technique', 'method', 'process', 'steps',
            'implementation', 'execution', 'planning', 'tactics', 'skills',
            'tools', 'resources', 'practices', 'habits', 'routines', 'systems'
        }
        
        self.have_keywords = {
            'results', 'outcomes', 'wealth', 'assets', 'investments', 'returns',
            'income', 'revenue', 'profits', 'gains', 'success', 'achievement',
            'accomplishment', 'attainment', 'possession', 'ownership', 'acquisition'
        }
        
        # Cultural relevance keywords
        self.cultural_keywords = {
            'african american', 'black', 'minority', 'diversity', 'inclusion',
            'equity', 'representation', 'cultural', 'heritage', 'community',
            'systemic', 'barriers', 'opportunities', 'empowerment', 'advocacy'
        }
    
    def connect_database(self) -> bool:
        """Connect to database"""
        try:
            logger.info(f"Connecting to database: {self.database_url}")
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.session = sessionmaker(bind=self.engine)()
            self.inspector = inspect(self.engine)
            
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def validate_be_do_have_classification(self, article: Dict) -> Tuple[bool, List[str]]:
        """Validate Be-Do-Have classification accuracy"""
        issues = []
        title = article.get('title', '').lower()
        content = article.get('content_preview', '').lower()
        primary_phase = article.get('primary_phase', '')
        
        # Check if classification matches content
        if primary_phase == 'BE':
            # Should contain BE keywords
            be_matches = sum(1 for keyword in self.be_keywords if keyword in title or keyword in content)
            do_matches = sum(1 for keyword in self.do_keywords if keyword in title or keyword in content)
            have_matches = sum(1 for keyword in self.have_keywords if keyword in title or keyword in content)
            
            if be_matches < max(do_matches, have_matches):
                issues.append(f"BE classification may be incorrect - found {do_matches} DO keywords and {have_matches} HAVE keywords vs {be_matches} BE keywords")
        
        elif primary_phase == 'DO':
            # Should contain DO keywords
            be_matches = sum(1 for keyword in self.be_keywords if keyword in title or keyword in content)
            do_matches = sum(1 for keyword in self.do_keywords if keyword in title or keyword in content)
            have_matches = sum(1 for keyword in self.have_keywords if keyword in title or keyword in content)
            
            if do_matches < max(be_matches, have_matches):
                issues.append(f"DO classification may be incorrect - found {be_matches} BE keywords and {have_matches} HAVE keywords vs {do_matches} DO keywords")
        
        elif primary_phase == 'HAVE':
            # Should contain HAVE keywords
            be_matches = sum(1 for keyword in self.be_keywords if keyword in title or keyword in content)
            do_matches = sum(1 for keyword in self.do_keywords if keyword in title or keyword in content)
            have_matches = sum(1 for keyword in self.have_keywords if keyword in title or keyword in content)
            
            if have_matches < max(be_matches, do_matches):
                issues.append(f"HAVE classification may be incorrect - found {be_matches} BE keywords and {do_matches} DO keywords vs {have_matches} HAVE keywords")
        
        # Check confidence score
        confidence = article.get('confidence_score', 0.0)
        if confidence < 0.7:
            issues.append(f"Low confidence score ({confidence}) for classification")
        
        return len(issues) == 0, issues
    
    def validate_cultural_relevance_scores(self, article: Dict) -> Tuple[bool, List[str]]:
        """Validate cultural relevance scores are properly populated"""
        issues = []
        
        # Check if cultural relevance score exists
        cultural_relevance = article.get('cultural_relevance', 0)
        cultural_sensitivity = article.get('cultural_sensitivity', 0)
        cultural_keywords = article.get('cultural_relevance_keywords', [])
        
        # Check if cultural keywords are present
        title = article.get('title', '').lower()
        content = article.get('content_preview', '').lower()
        
        cultural_matches = sum(1 for keyword in self.cultural_keywords if keyword in title or keyword in content)
        
        # Validate cultural relevance score
        if cultural_matches > 0 and cultural_relevance < 5:
            issues.append(f"Cultural keywords found but low relevance score ({cultural_relevance})")
        
        if cultural_relevance > 7 and cultural_matches == 0:
            issues.append(f"High cultural relevance score ({cultural_relevance}) but no cultural keywords found")
        
        # Check if cultural keywords list is populated
        if cultural_matches > 0 and not cultural_keywords:
            issues.append("Cultural keywords found in content but cultural_relevance_keywords list is empty")
        
        # Validate cultural sensitivity score
        if cultural_sensitivity == 0:
            issues.append("Cultural sensitivity score is not populated")
        
        return len(issues) == 0, issues
    
    def generate_search_vector(self, article: Dict) -> str:
        """Generate search vector for full-text search"""
        title = article.get('title', '')
        content_preview = article.get('content_preview', '')
        meta_description = article.get('meta_description', '')
        key_topics = ' '.join(article.get('key_topics', []))
        
        # Combine all searchable content
        search_content = f"{title} {content_preview} {meta_description} {key_topics}"
        
        # Clean and normalize
        search_content = re.sub(r'[^\w\s]', ' ', search_content.lower())
        search_content = re.sub(r'\s+', ' ', search_content).strip()
        
        return search_content
    
    def validate_search_vector(self, article: Dict) -> Tuple[bool, List[str]]:
        """Validate search vector generation"""
        issues = []
        
        search_vector = self.generate_search_vector(article)
        
        if len(search_vector) < 50:
            issues.append("Search vector too short - may not provide adequate search coverage")
        
        if not search_vector:
            issues.append("Search vector is empty")
        
        # Check for key terms
        title = article.get('title', '').lower()
        if title and title not in search_vector:
            issues.append("Title not properly included in search vector")
        
        return len(issues) == 0, issues
    
    def validate_access_control_requirements(self, article: Dict) -> Tuple[bool, List[str]]:
        """Validate article access control requirements"""
        issues = []
        
        # Check difficulty level
        difficulty_level = article.get('difficulty_level', '')
        valid_difficulties = ['Beginner', 'Intermediate', 'Advanced']
        
        if difficulty_level not in valid_difficulties:
            issues.append(f"Invalid difficulty level: {difficulty_level}")
        
        # Check if article has required fields for access control
        required_fields = ['primary_phase', 'difficulty_level', 'demographic_relevance']
        for field in required_fields:
            if not article.get(field):
                issues.append(f"Missing required field for access control: {field}")
        
        # Validate demographic relevance score
        demographic_relevance = article.get('demographic_relevance', 0)
        if not isinstance(demographic_relevance, (int, float)) or demographic_relevance < 0 or demographic_relevance > 10:
            issues.append(f"Invalid demographic relevance score: {demographic_relevance}")
        
        # Check actionability score for DO phase articles
        if article.get('primary_phase') == 'DO':
            actionability_score = article.get('actionability_score', 0)
            if actionability_score < 5:
                issues.append(f"Low actionability score ({actionability_score}) for DO phase article")
        
        return len(issues) == 0, issues
    
    def validate_article_data(self, article: Dict) -> Tuple[bool, List[str]]:
        """Comprehensive article data validation"""
        issues = []
        
        # Basic validation
        required_fields = ['title', 'url', 'content_preview', 'primary_phase', 'difficulty_level']
        for field in required_fields:
            if not article.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Validate phase
        valid_phases = ['BE', 'DO', 'HAVE']
        if article.get('primary_phase') not in valid_phases:
            issues.append(f"Invalid primary_phase: {article.get('primary_phase')}")
        
        # Validate difficulty level
        valid_difficulties = ['Beginner', 'Intermediate', 'Advanced']
        if article.get('difficulty_level') not in valid_difficulties:
            issues.append(f"Invalid difficulty_level: {article.get('difficulty_level')}")
        
        # Validate scores are within range
        score_fields = ['demographic_relevance', 'cultural_sensitivity', 'income_impact_potential', 
                       'actionability_score', 'professional_development_value']
        for field in score_fields:
            score = article.get(field, 0)
            if not isinstance(score, (int, float)) or score < 0 or score > 10:
                issues.append(f"Invalid {field} score: {score}")
        
        return len(issues) == 0, issues
    
    def prepare_article_data(self, article: Dict) -> Dict:
        """Prepare article data for database insertion"""
        # Generate unique ID if not present
        if not article.get('article_id'):
            article['article_id'] = str(uuid.uuid4())
        
        # Extract domain from URL
        url = article.get('url', '')
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
        except:
            domain = 'unknown'
        
        # Calculate reading time
        content = article.get('content_preview', '')
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # 200 words per minute
        
        # Generate search vector
        search_vector = self.generate_search_vector(article)
        
        # Prepare JSON fields
        key_topics = json.dumps(article.get('key_topics', []))
        learning_objectives = json.dumps(article.get('learning_objectives', []))
        prerequisites = json.dumps(article.get('prerequisites', []))
        cultural_relevance_keywords = json.dumps(article.get('cultural_relevance_keywords', []))
        
        return {
            'id': article['article_id'],
            'url': url,
            'title': article.get('title', ''),
            'content': content[:10000],  # Limit content length
            'content_preview': content[:500],
            'meta_description': article.get('meta_description', ''),
            'author': article.get('author', ''),
            'publish_date': None,
            'word_count': word_count,
            'reading_time_minutes': reading_time,
            'primary_phase': article.get('primary_phase', 'DO'),
            'difficulty_level': article.get('difficulty_level', 'Intermediate'),
            'confidence_score': article.get('confidence_score', 0.0),
            'demographic_relevance': article.get('demographic_relevance', 5),
            'cultural_sensitivity': article.get('cultural_sensitivity', 5),
            'income_impact_potential': article.get('income_impact_potential', 5),
            'actionability_score': article.get('actionability_score', 5),
            'professional_development_value': article.get('professional_development_value', 5),
            'key_topics': key_topics,
            'learning_objectives': learning_objectives,
            'prerequisites': prerequisites,
            'cultural_relevance_keywords': cultural_relevance_keywords,
            'target_income_range': article.get('target_income_range', '$40K-$60K'),
            'career_stage': article.get('career_stage', 'Mid-career'),
            'recommended_reading_order': article.get('recommended_reading_order', 50),
            'search_vector': search_vector,
            'domain': domain,
            'source_quality_score': article.get('source_quality_score', 0.7),
            'is_active': True,
            'is_featured': False,
            'admin_notes': f"Imported from classified data. Processing timestamp: {article.get('processing_timestamp', 'Unknown')}",
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    def insert_article(self, article_data: Dict) -> bool:
        """Insert article into database"""
        try:
            with self.engine.connect() as conn:
                # Insert article
                conn.execute(text("""
                    INSERT OR REPLACE INTO articles (
                        id, url, title, content, content_preview, meta_description, author,
                        publish_date, word_count, reading_time_minutes, primary_phase,
                        difficulty_level, confidence_score, demographic_relevance,
                        cultural_sensitivity, income_impact_potential, actionability_score,
                        professional_development_value, key_topics, learning_objectives,
                        prerequisites, cultural_relevance_keywords, target_income_range,
                        career_stage, recommended_reading_order, search_vector, domain, 
                        source_quality_score, is_active, is_featured, admin_notes, 
                        created_at, updated_at
                    ) VALUES (
                        :id, :url, :title, :content, :content_preview, :meta_description, :author,
                        :publish_date, :word_count, :reading_time_minutes, :primary_phase,
                        :difficulty_level, :confidence_score, :demographic_relevance,
                        :cultural_sensitivity, :income_impact_potential, :actionability_score,
                        :professional_development_value, :key_topics, :learning_objectives,
                        :prerequisites, :cultural_relevance_keywords, :target_income_range,
                        :career_stage, :recommended_reading_order, :search_vector, :domain,
                        :source_quality_score, :is_active, :is_featured, :admin_notes,
                        :created_at, :updated_at
                    )
                """), article_data)
                
                # Create analytics record
                analytics_id = str(uuid.uuid4())
                conn.execute(text("""
                    INSERT OR REPLACE INTO article_analytics (
                        id, article_id, total_views, total_reads, total_bookmarks,
                        total_shares, completion_rate, average_time_spent,
                        average_scroll_depth, average_rating, total_ratings,
                        helpfulness_score, clarity_score, actionability_score,
                        cultural_relevance_score, recommendation_click_rate,
                        recommendation_read_rate, created_at, updated_at
                    ) VALUES (
                        :id, :article_id, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0,
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, :created_at, :updated_at
                    )
                """), {
                    'id': analytics_id,
                    'article_id': article_data['id'],
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting article {article_data.get('title', 'Unknown')}: {e}")
            return False
    
    def load_articles_from_file(self, file_path: str) -> List[Dict]:
        """Load articles from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return []
    
    def validate_and_import_articles(self, file_path: str) -> Tuple[int, int, int]:
        """Validate and import articles from file"""
        logger.info(f"Loading articles from {file_path}...")
        
        articles = self.load_articles_from_file(file_path)
        if not articles:
            return 0, 0, 0
        
        logger.info(f"Found {len(articles)} articles in {file_path}")
        self.stats['total_articles'] += len(articles)
        
        imported = 0
        skipped = 0
        failed = 0
        
        for article in articles:
            # Comprehensive validation
            is_valid, validation_errors = self.validate_article_data(article)
            if not is_valid:
                self.stats['validation_errors'].extend(validation_errors)
                logger.warning(f"Skipping invalid article: {validation_errors}")
                skipped += 1
                continue
            
            # Be-Do-Have classification validation
            classification_valid, classification_issues = self.validate_be_do_have_classification(article)
            if not classification_valid:
                self.stats['classification_issues'].extend(classification_issues)
                logger.warning(f"Classification issues for {article.get('title', 'Unknown')}: {classification_issues}")
            
            # Cultural relevance validation
            cultural_valid, cultural_issues = self.validate_cultural_relevance_scores(article)
            if not cultural_valid:
                self.stats['cultural_relevance_issues'].extend(cultural_issues)
                logger.warning(f"Cultural relevance issues for {article.get('title', 'Unknown')}: {cultural_issues}")
            
            # Search vector validation
            search_valid, search_issues = self.validate_search_vector(article)
            if not search_valid:
                self.stats['search_vector_issues'].extend(search_issues)
                logger.warning(f"Search vector issues for {article.get('title', 'Unknown')}: {search_issues}")
            
            # Access control validation
            access_valid, access_issues = self.validate_access_control_requirements(article)
            if not access_valid:
                self.stats['access_control_issues'].extend(access_issues)
                logger.warning(f"Access control issues for {article.get('title', 'Unknown')}: {access_issues}")
            
            # Check if article already exists
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id FROM articles WHERE url = :url"), 
                                    {'url': article.get('url', '')})
                if result.fetchone():
                    logger.info(f"Article already exists: {article.get('title', 'Unknown')}")
                    skipped += 1
                    continue
            
            # Prepare and insert article
            article_data = self.prepare_article_data(article)
            if self.insert_article(article_data):
                imported += 1
                logger.info(f"Imported: {article_data['title']}")
            else:
                failed += 1
        
        return imported, skipped, failed
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("CLASSIFIED ARTICLES IMPORT AND VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now()}")
        report.append(f"Database: {self.database_url}")
        report.append("")
        
        # Import statistics
        report.append("IMPORT STATISTICS:")
        report.append("-" * 40)
        report.append(f"Total articles processed: {self.stats['total_articles']}")
        report.append(f"Successfully imported: {self.stats['imported']}")
        report.append(f"Skipped (duplicates/invalid): {self.stats['skipped']}")
        report.append(f"Failed to import: {self.stats['failed']}")
        report.append("")
        
        # Validation issues
        if self.stats['validation_errors']:
            report.append("VALIDATION ERRORS:")
            report.append("-" * 40)
            for error in self.stats['validation_errors'][:10]:  # Show first 10
                report.append(f"• {error}")
            if len(self.stats['validation_errors']) > 10:
                report.append(f"... and {len(self.stats['validation_errors']) - 10} more")
            report.append("")
        
        if self.stats['classification_issues']:
            report.append("BE-DO-HAVE CLASSIFICATION ISSUES:")
            report.append("-" * 40)
            for issue in self.stats['classification_issues'][:10]:
                report.append(f"• {issue}")
            if len(self.stats['classification_issues']) > 10:
                report.append(f"... and {len(self.stats['classification_issues']) - 10} more")
            report.append("")
        
        if self.stats['cultural_relevance_issues']:
            report.append("CULTURAL RELEVANCE ISSUES:")
            report.append("-" * 40)
            for issue in self.stats['cultural_relevance_issues'][:10]:
                report.append(f"• {issue}")
            if len(self.stats['cultural_relevance_issues']) > 10:
                report.append(f"... and {len(self.stats['cultural_relevance_issues']) - 10} more")
            report.append("")
        
        if self.stats['search_vector_issues']:
            report.append("SEARCH VECTOR ISSUES:")
            report.append("-" * 40)
            for issue in self.stats['search_vector_issues'][:10]:
                report.append(f"• {issue}")
            if len(self.stats['search_vector_issues']) > 10:
                report.append(f"... and {len(self.stats['search_vector_issues']) - 10} more")
            report.append("")
        
        if self.stats['access_control_issues']:
            report.append("ACCESS CONTROL ISSUES:")
            report.append("-" * 40)
            for issue in self.stats['access_control_issues'][:10]:
                report.append(f"• {issue}")
            if len(self.stats['access_control_issues']) > 10:
                report.append(f"... and {len(self.stats['access_control_issues']) - 10} more")
            report.append("")
        
        # Database verification
        report.append("DATABASE VERIFICATION:")
        report.append("-" * 40)
        with self.engine.connect() as conn:
            # Total articles
            result = conn.execute(text("SELECT COUNT(*) FROM articles"))
            total_articles = result.fetchone()[0]
            report.append(f"Total articles in database: {total_articles}")
            
            # Phase distribution
            result = conn.execute(text("""
                SELECT primary_phase, COUNT(*) as count 
                FROM articles 
                GROUP BY primary_phase 
                ORDER BY primary_phase
            """))
            report.append("\nPhase Distribution:")
            for phase, count in result.fetchall():
                report.append(f"  {phase}: {count} articles")
            
            # Difficulty distribution
            result = conn.execute(text("""
                SELECT difficulty_level, COUNT(*) as count 
                FROM articles 
                GROUP BY difficulty_level 
                ORDER BY difficulty_level
            """))
            report.append("\nDifficulty Distribution:")
            for difficulty, count in result.fetchall():
                report.append(f"  {difficulty}: {count} articles")
            
            # Cultural relevance distribution
            result = conn.execute(text("""
                SELECT 
                    CASE 
                        WHEN cultural_sensitivity >= 7 THEN 'High (7-10)'
                        WHEN cultural_sensitivity >= 4 THEN 'Medium (4-6)'
                        ELSE 'Low (1-3)'
                    END as sensitivity_level,
                    COUNT(*) as count
                FROM articles 
                GROUP BY sensitivity_level
                ORDER BY sensitivity_level
            """))
            report.append("\nCultural Sensitivity Distribution:")
            for level, count in result.fetchall():
                report.append(f"  {level}: {count} articles")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_import_and_validation(self, file_path: str = None) -> bool:
        """Run complete import and validation process"""
        logger.info("Starting classified articles import and validation...")
        
        # Connect to database
        if not self.connect_database():
            return False
        
        try:
            if file_path:
                # Import from specific file
                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path}")
                    return False
                
                imported, skipped, failed = self.validate_and_import_articles(file_path)
                self.stats['imported'] += imported
                self.stats['skipped'] += skipped
                self.stats['failed'] += failed
            else:
                # Import from all available files
                data_files = [
                    'data/classified_articles_complete.json',
                    'data/have_phase_articles.json',
                    'data/do_phase_articles.json',
                    'data/be_phase_articles.json',
                    'data/high_confidence_classifications.json'
                ]
                
                for file_path in data_files:
                    if os.path.exists(file_path):
                        imported, skipped, failed = self.validate_and_import_articles(file_path)
                        self.stats['imported'] += imported
                        self.stats['skipped'] += skipped
                        self.stats['failed'] += failed
                    else:
                        logger.info(f"File not found: {file_path}")
            
            # Generate and save report
            report = self.generate_validation_report()
            
            # Save report to file
            report_filename = f"article_import_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            
            # Print report to console
            print(report)
            
            logger.info(f"Report saved to: {report_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during import and validation: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import and validate classified articles')
    parser.add_argument('--file', help='Import from specific file only')
    parser.add_argument('--database', help='Database URL')
    
    args = parser.parse_args()
    
    # Create validator instance
    validator = ArticleImportValidator(args.database)
    
    # Run import and validation
    success = validator.run_import_and_validation(args.file)
    
    if success:
        logger.info("Import and validation completed successfully!")
        return 0
    else:
        logger.error("Import and validation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
