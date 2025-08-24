#!/usr/bin/env python3
"""
Validate Existing Articles Script
Validates all existing articles in the database for:
- Be-Do-Have classifications
- Cultural relevance scores
- Search vectors for full-text search
- Article access control requirements
"""

import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
        logging.FileHandler('existing_articles_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExistingArticlesValidator:
    """Validate existing articles in the database"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
        self.engine = None
        self.session = None
        self.inspector = None
        
        # Validation statistics
        self.stats = {
            'total_articles': 0,
            'validation_errors': [],
            'classification_issues': [],
            'cultural_relevance_issues': [],
            'search_vector_issues': [],
            'access_control_issues': [],
            'articles_with_issues': []
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
    
    def get_all_articles(self) -> List[Dict]:
        """Get all articles from database"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, url, title, content, content_preview, meta_description, author,
                           primary_phase, difficulty_level, confidence_score, demographic_relevance,
                           cultural_sensitivity, income_impact_potential, actionability_score,
                           professional_development_value, key_topics, learning_objectives,
                           prerequisites, cultural_relevance_keywords, target_income_range,
                           career_stage, search_vector, domain, source_quality_score,
                           is_active, is_featured, created_at, updated_at
                    FROM articles
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """))
                
                articles = []
                for row in result.fetchall():
                    article = dict(row._mapping)
                    
                    # Parse JSON fields
                    for field in ['key_topics', 'learning_objectives', 'prerequisites', 'cultural_relevance_keywords']:
                        if article.get(field):
                            try:
                                article[field] = json.loads(article[field])
                            except:
                                article[field] = []
                        else:
                            article[field] = []
                    
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            return []
    
    def validate_be_do_have_classification(self, article: Dict) -> Tuple[bool, List[str]]:
        """Validate Be-Do-Have classification accuracy"""
        issues = []
        title = (article.get('title') or '').lower()
        content = (article.get('content_preview') or '').lower()
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
        cultural_sensitivity = article.get('cultural_sensitivity', 0)
        cultural_keywords = article.get('cultural_relevance_keywords', [])
        
        # Check if cultural keywords are present
        title = (article.get('title') or '').lower()
        content = (article.get('content_preview') or '').lower()
        
        cultural_matches = sum(1 for keyword in self.cultural_keywords if keyword in title or keyword in content)
        
        # Validate cultural sensitivity score
        if cultural_sensitivity == 0:
            issues.append("Cultural sensitivity score is not populated")
        
        # Check if cultural keywords list is populated
        if cultural_matches > 0 and not cultural_keywords:
            issues.append("Cultural keywords found in content but cultural_relevance_keywords list is empty")
        
        return len(issues) == 0, issues
    
    def validate_search_vector(self, article: Dict) -> Tuple[bool, List[str]]:
        """Validate search vector generation"""
        issues = []
        
        search_vector = article.get('search_vector', '')
        
        if not search_vector:
            issues.append("Search vector is empty")
        elif len(search_vector) < 50:
            issues.append("Search vector too short - may not provide adequate search coverage")
        
        # Check for key terms
        title = (article.get('title') or '').lower()
        if title and search_vector and title not in search_vector.lower():
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
    
    def validate_all_articles(self) -> bool:
        """Validate all articles in the database"""
        logger.info("Starting validation of existing articles...")
        
        # Connect to database
        if not self.connect_database():
            return False
        
        # Get all articles
        articles = self.get_all_articles()
        self.stats['total_articles'] = len(articles)
        
        logger.info(f"Found {len(articles)} articles to validate")
        
        for article in articles:
            article_issues = []
            
            # Basic validation
            is_valid, validation_errors = self.validate_article_data(article)
            if not is_valid:
                self.stats['validation_errors'].extend(validation_errors)
                article_issues.extend(validation_errors)
            
            # Be-Do-Have classification validation
            classification_valid, classification_issues = self.validate_be_do_have_classification(article)
            if not classification_valid:
                self.stats['classification_issues'].extend(classification_issues)
                article_issues.extend(classification_issues)
            
            # Cultural relevance validation
            cultural_valid, cultural_issues = self.validate_cultural_relevance_scores(article)
            if not cultural_valid:
                self.stats['cultural_relevance_issues'].extend(cultural_issues)
                article_issues.extend(cultural_issues)
            
            # Search vector validation
            search_valid, search_issues = self.validate_search_vector(article)
            if not search_valid:
                self.stats['search_vector_issues'].extend(search_issues)
                article_issues.extend(search_issues)
            
            # Access control validation
            access_valid, access_issues = self.validate_access_control_requirements(article)
            if not access_valid:
                self.stats['access_control_issues'].extend(access_issues)
                article_issues.extend(access_issues)
            
            # Record article with issues
            if article_issues:
                self.stats['articles_with_issues'].append({
                    'title': article.get('title', 'Unknown'),
                    'id': article.get('id', 'Unknown'),
                    'issues': article_issues
                })
        
        return True
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("EXISTING ARTICLES VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now()}")
        report.append(f"Database: {self.database_url}")
        report.append("")
        
        # Summary statistics
        report.append("VALIDATION SUMMARY:")
        report.append("-" * 40)
        report.append(f"Total articles validated: {self.stats['total_articles']}")
        report.append(f"Articles with issues: {len(self.stats['articles_with_issues'])}")
        report.append(f"Total validation errors: {len(self.stats['validation_errors'])}")
        report.append(f"Total classification issues: {len(self.stats['classification_issues'])}")
        report.append(f"Total cultural relevance issues: {len(self.stats['cultural_relevance_issues'])}")
        report.append(f"Total search vector issues: {len(self.stats['search_vector_issues'])}")
        report.append(f"Total access control issues: {len(self.stats['access_control_issues'])}")
        report.append("")
        
        # Articles with issues
        if self.stats['articles_with_issues']:
            report.append("ARTICLES WITH ISSUES:")
            report.append("-" * 40)
            for article in self.stats['articles_with_issues']:
                report.append(f"• {article['title']} (ID: {article['id']})")
                for issue in article['issues']:
                    report.append(f"  - {issue}")
                report.append("")
        
        # Detailed issue breakdown
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
        
        # Database statistics
        report.append("DATABASE STATISTICS:")
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
            
            # Cultural sensitivity distribution
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
            
            # Search vector statistics
            result = conn.execute(text("""
                SELECT 
                    CASE 
                        WHEN search_vector IS NULL OR search_vector = '' THEN 'Empty'
                        WHEN LENGTH(search_vector) < 50 THEN 'Short (<50 chars)'
                        WHEN LENGTH(search_vector) < 200 THEN 'Medium (50-200 chars)'
                        ELSE 'Long (>200 chars)'
                    END as vector_status,
                    COUNT(*) as count
                FROM articles 
                GROUP BY vector_status
                ORDER BY vector_status
            """))
            report.append("\nSearch Vector Status:")
            for status, count in result.fetchall():
                report.append(f"  {status}: {count} articles")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_validation(self) -> bool:
        """Run complete validation process"""
        logger.info("Starting existing articles validation...")
        
        try:
            # Validate all articles
            if not self.validate_all_articles():
                return False
            
            # Generate and save report
            report = self.generate_validation_report()
            
            # Save report to file
            report_filename = f"existing_articles_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            
            # Print report to console
            print(report)
            
            logger.info(f"Report saved to: {report_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate existing articles in database')
    parser.add_argument('--database', help='Database URL')
    
    args = parser.parse_args()
    
    # Create validator instance
    validator = ExistingArticlesValidator(args.database)
    
    # Run validation
    success = validator.run_validation()
    
    if success:
        logger.info("Validation completed successfully!")
        return 0
    else:
        logger.error("Validation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
