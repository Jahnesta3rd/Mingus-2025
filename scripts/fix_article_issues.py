#!/usr/bin/env python3
"""
Fix Article Issues Script
Fixes identified issues with existing articles:
- Generate missing search vectors
- Fix classification issues
- Update cultural relevance scores
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
        logging.FileHandler('fix_article_issues.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArticleIssueFixer:
    """Fix issues with existing articles"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
        self.engine = None
        self.session = None
        
        # Fix statistics
        self.stats = {
            'total_articles': 0,
            'search_vectors_fixed': 0,
            'classifications_fixed': 0,
            'cultural_scores_updated': 0,
            'articles_updated': 0
        }
        
        # Be-Do-Have keywords for classification
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
            
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
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
    
    def determine_correct_phase(self, article: Dict) -> str:
        """Determine the correct Be-Do-Have phase based on content"""
        title = (article.get('title') or '').lower()
        content = (article.get('content_preview') or '').lower()
        
        # Count keyword matches for each phase
        be_matches = sum(1 for keyword in self.be_keywords if keyword in title or keyword in content)
        do_matches = sum(1 for keyword in self.do_keywords if keyword in title or keyword in content)
        have_matches = sum(1 for keyword in self.have_keywords if keyword in title or keyword in content)
        
        # Return the phase with the most matches
        if have_matches >= max(be_matches, do_matches):
            return 'HAVE'
        elif do_matches >= be_matches:
            return 'DO'
        else:
            return 'BE'
    
    def calculate_cultural_relevance(self, article: Dict) -> int:
        """Calculate cultural relevance score based on content"""
        title = (article.get('title') or '').lower()
        content = (article.get('content_preview') or '').lower()
        
        # Count cultural keyword matches
        cultural_matches = sum(1 for keyword in self.cultural_keywords if keyword in title or keyword in content)
        
        # Calculate score based on matches
        if cultural_matches >= 3:
            return 8
        elif cultural_matches >= 2:
            return 6
        elif cultural_matches >= 1:
            return 4
        else:
            return 3  # Default score for general content
    
    def get_articles_needing_fixes(self) -> List[Dict]:
        """Get articles that need fixes"""
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
    
    def fix_article_issues(self, article: Dict) -> bool:
        """Fix issues for a single article"""
        try:
            article_id = article.get('id')
            title = article.get('title', '')
            
            logger.info(f"Fixing issues for article: {title}")
            
            updates = {}
            
            # Fix search vector
            if not article.get('search_vector'):
                search_vector = self.generate_search_vector(article)
                if search_vector:
                    updates['search_vector'] = search_vector
                    self.stats['search_vectors_fixed'] += 1
                    logger.info(f"  - Generated search vector ({len(search_vector)} chars)")
            
            # Fix classification if needed
            current_phase = article.get('primary_phase')
            correct_phase = self.determine_correct_phase(article)
            
            if current_phase != correct_phase:
                updates['primary_phase'] = correct_phase
                self.stats['classifications_fixed'] += 1
                logger.info(f"  - Fixed classification: {current_phase} -> {correct_phase}")
            
            # Update cultural sensitivity score
            current_cultural_score = article.get('cultural_sensitivity', 0)
            calculated_cultural_score = self.calculate_cultural_relevance(article)
            
            if abs(current_cultural_score - calculated_cultural_score) > 1:
                updates['cultural_sensitivity'] = calculated_cultural_score
                self.stats['cultural_scores_updated'] += 1
                logger.info(f"  - Updated cultural sensitivity: {current_cultural_score} -> {calculated_cultural_score}")
            
            # Apply updates if any
            if updates:
                with self.engine.connect() as conn:
                    # Build update query
                    set_clauses = []
                    params = {'id': article_id}
                    
                    for field, value in updates.items():
                        set_clauses.append(f"{field} = :{field}")
                        params[field] = value
                    
                    update_query = f"""
                        UPDATE articles 
                        SET {', '.join(set_clauses)}, updated_at = :updated_at
                        WHERE id = :id
                    """
                    params['updated_at'] = datetime.utcnow()
                    
                    conn.execute(text(update_query), params)
                    conn.commit()
                    
                    self.stats['articles_updated'] += 1
                    logger.info(f"  - Applied {len(updates)} updates")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fixing article {title}: {e}")
            return False
    
    def fix_all_article_issues(self) -> bool:
        """Fix issues for all articles"""
        logger.info("Starting to fix article issues...")
        
        # Connect to database
        if not self.connect_database():
            return False
        
        try:
            # Get articles needing fixes
            articles = self.get_articles_needing_fixes()
            self.stats['total_articles'] = len(articles)
            
            logger.info(f"Found {len(articles)} articles to check for fixes")
            
            # Fix issues for each article
            for article in articles:
                self.fix_article_issues(article)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during article fixes: {e}")
            return False
    
    def generate_fix_report(self) -> str:
        """Generate report of fixes applied"""
        report = []
        report.append("=" * 80)
        report.append("ARTICLE ISSUES FIX REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now()}")
        report.append(f"Database: {self.database_url}")
        report.append("")
        
        # Fix statistics
        report.append("FIX STATISTICS:")
        report.append("-" * 40)
        report.append(f"Total articles processed: {self.stats['total_articles']}")
        report.append(f"Articles updated: {self.stats['articles_updated']}")
        report.append(f"Search vectors fixed: {self.stats['search_vectors_fixed']}")
        report.append(f"Classifications fixed: {self.stats['classifications_fixed']}")
        report.append(f"Cultural scores updated: {self.stats['cultural_scores_updated']}")
        report.append("")
        
        # Database verification
        report.append("DATABASE VERIFICATION:")
        report.append("-" * 40)
        with self.engine.connect() as conn:
            # Total articles
            result = conn.execute(text("SELECT COUNT(*) FROM articles"))
            total_articles = result.fetchone()[0]
            report.append(f"Total articles in database: {total_articles}")
            
            # Search vector status
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
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_fixes(self) -> bool:
        """Run complete fix process"""
        logger.info("Starting article issue fixes...")
        
        try:
            # Fix all article issues
            if not self.fix_all_article_issues():
                return False
            
            # Generate and save report
            report = self.generate_fix_report()
            
            # Save report to file
            report_filename = f"article_fixes_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            
            # Print report to console
            print(report)
            
            logger.info(f"Report saved to: {report_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during fixes: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix issues with existing articles')
    parser.add_argument('--database', help='Database URL')
    
    args = parser.parse_args()
    
    # Create fixer instance
    fixer = ArticleIssueFixer(args.database)
    
    # Run fixes
    success = fixer.run_fixes()
    
    if success:
        logger.info("Article fixes completed successfully!")
        return 0
    else:
        logger.error("Article fixes failed!")
        return 1


if __name__ == "__main__":
    exit(main())
