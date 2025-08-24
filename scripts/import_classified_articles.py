#!/usr/bin/env python3
"""
Import Classified Articles Script
Imports classified articles from data files into the Mingus article library database
"""

import sys
import os
import json
import uuid
from datetime import datetime
from urllib.parse import urlparse
import sqlite3
from typing import Dict, List, Optional, Tuple

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def get_database_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'mingus.db')
    return sqlite3.connect(db_path)

def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return 'unknown'

def calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes"""
    words_per_minute = 200
    word_count = len(content.split())
    return max(1, word_count // words_per_minute)

def validate_article_data(article: Dict) -> Tuple[bool, str]:
    """Validate article data before import"""
    required_fields = ['title', 'url', 'content_preview', 'primary_phase', 'difficulty_level']
    
    for field in required_fields:
        if not article.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate phase
    valid_phases = ['BE', 'DO', 'HAVE']
    if article['primary_phase'] not in valid_phases:
        return False, f"Invalid primary_phase: {article['primary_phase']}"
    
    # Validate difficulty level
    valid_difficulties = ['Beginner', 'Intermediate', 'Advanced']
    if article['difficulty_level'] not in valid_difficulties:
        return False, f"Invalid difficulty_level: {article['difficulty_level']}"
    
    return True, "Valid"

def prepare_article_data(article: Dict) -> Dict:
    """Prepare article data for database insertion"""
    # Generate unique ID if not present
    if not article.get('article_id'):
        article['article_id'] = str(uuid.uuid4())
    
    # Extract domain from URL
    domain = extract_domain_from_url(article.get('url', ''))
    
    # Calculate reading time
    content = article.get('content_preview', '')
    reading_time = calculate_reading_time(content)
    
    # Prepare JSON fields
    key_topics = json.dumps(article.get('key_topics', []))
    learning_objectives = json.dumps(article.get('learning_objectives', []))
    prerequisites = json.dumps(article.get('prerequisites', []))
    cultural_relevance_keywords = json.dumps(article.get('cultural_relevance_keywords', []))
    
    # Set defaults for missing fields
    return {
        'id': article['article_id'],
        'url': article.get('url', ''),
        'title': article.get('title', ''),
        'content': article.get('content_preview', '')[:10000],  # Limit content length
        'content_preview': article.get('content_preview', '')[:500],
        'meta_description': article.get('meta_description', ''),
        'author': article.get('author', ''),
        'publish_date': None,  # Could be extracted from URL or content if needed
        'word_count': len(article.get('content_preview', '').split()),
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
        'domain': domain,
        'source_quality_score': 0.7,  # Default quality score
        'is_active': True,
        'is_featured': False,
        'admin_notes': f"Imported from classified data. Processing timestamp: {article.get('processing_timestamp', 'Unknown')}",
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

def insert_article(conn: sqlite3.Connection, article_data: Dict) -> bool:
    """Insert article into database"""
    try:
        cursor = conn.cursor()
        
        # Insert article
        cursor.execute("""
            INSERT OR REPLACE INTO articles (
                id, url, title, content, content_preview, meta_description, author,
                publish_date, word_count, reading_time_minutes, primary_phase,
                difficulty_level, confidence_score, demographic_relevance,
                cultural_sensitivity, income_impact_potential, actionability_score,
                professional_development_value, key_topics, learning_objectives,
                prerequisites, cultural_relevance_keywords, target_income_range,
                career_stage, recommended_reading_order, domain, source_quality_score,
                is_active, is_featured, admin_notes, created_at, updated_at
            ) VALUES (
                :id, :url, :title, :content, :content_preview, :meta_description, :author,
                :publish_date, :word_count, :reading_time_minutes, :primary_phase,
                :difficulty_level, :confidence_score, :demographic_relevance,
                :cultural_sensitivity, :income_impact_potential, :actionability_score,
                :professional_development_value, :key_topics, :learning_objectives,
                :prerequisites, :cultural_relevance_keywords, :target_income_range,
                :career_stage, :recommended_reading_order, :domain, :source_quality_score,
                :is_active, :is_featured, :admin_notes, :created_at, :updated_at
            )
        """, article_data)
        
        # Create analytics record
        analytics_id = str(uuid.uuid4())
        cursor.execute("""
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
        """, {
            'id': analytics_id,
            'article_id': article_data['id'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        return True
    except Exception as e:
        print(f"Error inserting article {article_data.get('title', 'Unknown')}: {e}")
        return False

def load_articles_from_file(file_path: str) -> List[Dict]:
    """Load articles from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return []

def import_articles_from_file(file_path: str, conn: sqlite3.Connection) -> Tuple[int, int, int]:
    """Import articles from a specific file"""
    print(f"Loading articles from {file_path}...")
    
    articles = load_articles_from_file(file_path)
    if not articles:
        return 0, 0, 0
    
    print(f"Found {len(articles)} articles in {file_path}")
    
    imported = 0
    skipped = 0
    failed = 0
    
    for article in articles:
        # Validate article data
        is_valid, validation_message = validate_article_data(article)
        if not is_valid:
            print(f"Skipping invalid article: {validation_message}")
            skipped += 1
            continue
        
        # Check if article already exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE url = ?", (article.get('url', ''),))
        if cursor.fetchone():
            print(f"Article already exists: {article.get('title', 'Unknown')}")
            skipped += 1
            continue
        
        # Prepare and insert article
        article_data = prepare_article_data(article)
        if insert_article(conn, article_data):
            imported += 1
            print(f"Imported: {article_data['title']}")
        else:
            failed += 1
    
    return imported, skipped, failed

def import_all_classified_articles():
    """Import all classified articles from data files"""
    print("Starting classified articles import...")
    print("=" * 60)
    
    # Data files to import from
    data_files = [
        'data/classified_articles_complete.json',
        'data/have_phase_articles.json',
        'data/do_phase_articles.json',
        'data/be_phase_articles.json',
        'data/high_confidence_classifications.json'
    ]
    
    conn = get_database_connection()
    
    total_imported = 0
    total_skipped = 0
    total_failed = 0
    
    try:
        for file_path in data_files:
            if os.path.exists(file_path):
                imported, skipped, failed = import_articles_from_file(file_path, conn)
                total_imported += imported
                total_skipped += skipped
                total_failed += failed
                
                print(f"File {file_path}: {imported} imported, {skipped} skipped, {failed} failed")
                print("-" * 40)
            else:
                print(f"File not found: {file_path}")
        
        # Commit all changes
        conn.commit()
        
        print("=" * 60)
        print("Import Summary:")
        print(f"Total imported: {total_imported}")
        print(f"Total skipped: {total_skipped}")
        print(f"Total failed: {total_failed}")
        
        # Verify import
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        print(f"Total articles in database: {total_articles}")
        
        # Show phase distribution
        cursor.execute("""
            SELECT primary_phase, COUNT(*) as count 
            FROM articles 
            GROUP BY primary_phase 
            ORDER BY primary_phase
        """)
        phase_distribution = cursor.fetchall()
        print("\nPhase Distribution:")
        for phase, count in phase_distribution:
            print(f"  {phase}: {count} articles")
        
        # Show difficulty distribution
        cursor.execute("""
            SELECT difficulty_level, COUNT(*) as count 
            FROM articles 
            GROUP BY difficulty_level 
            ORDER BY difficulty_level
        """)
        difficulty_distribution = cursor.fetchall()
        print("\nDifficulty Distribution:")
        for difficulty, count in difficulty_distribution:
            print(f"  {difficulty}: {count} articles")
        
        print("\nImport completed successfully!")
        
    except Exception as e:
        print(f"Error during import: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import classified articles into Mingus database')
    parser.add_argument('--file', help='Import from specific file only')
    parser.add_argument('--dry-run', action='store_true', help='Validate data without importing')
    
    args = parser.parse_args()
    
    if args.file:
        # Import from specific file
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            return 1
        
        conn = get_database_connection()
        imported, skipped, failed = import_articles_from_file(args.file, conn)
        conn.commit()
        conn.close()
        
        print(f"Import complete: {imported} imported, {skipped} skipped, {failed} failed")
    else:
        # Import all files
        import_all_classified_articles()
    
    return 0

if __name__ == "__main__":
    exit(main())
