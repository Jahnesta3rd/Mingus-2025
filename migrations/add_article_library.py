"""
Migration: Add Article Library Tables
Description: Creates all tables for the Mingus article library with Be-Do-Have framework
Date: 2025-08-23
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import os

def run_migration():
    """Execute the article library migration"""
    
    # Database connection - adjust as needed for your setup
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Create enum types for PostgreSQL (if using PostgreSQL)
        # For SQLite, we'll use TEXT columns with CHECK constraints
        
        print("Creating article library tables...")
        
        # Create articles table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS articles (
                id VARCHAR(36) PRIMARY KEY,
                url VARCHAR(500) NOT NULL UNIQUE,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                content_preview VARCHAR(500),
                meta_description TEXT,
                author VARCHAR(200),
                publish_date DATE,
                word_count INTEGER DEFAULT 0,
                reading_time_minutes INTEGER DEFAULT 0,
                primary_phase VARCHAR(10) NOT NULL CHECK (primary_phase IN ('BE', 'DO', 'HAVE')),
                difficulty_level VARCHAR(20) NOT NULL CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Advanced')),
                confidence_score REAL DEFAULT 0.0,
                demographic_relevance INTEGER DEFAULT 0,
                cultural_sensitivity INTEGER DEFAULT 0,
                income_impact_potential INTEGER DEFAULT 0,
                actionability_score INTEGER DEFAULT 0,
                professional_development_value INTEGER DEFAULT 0,
                key_topics TEXT, -- JSON stored as TEXT
                learning_objectives TEXT, -- JSON stored as TEXT
                prerequisites TEXT, -- JSON stored as TEXT
                cultural_relevance_keywords TEXT, -- JSON stored as TEXT
                target_income_range VARCHAR(50),
                career_stage VARCHAR(50),
                recommended_reading_order INTEGER DEFAULT 50,
                search_vector TEXT, -- For full-text search
                domain VARCHAR(100) NOT NULL,
                source_quality_score REAL DEFAULT 0.0,
                is_active BOOLEAN DEFAULT 1,
                is_featured BOOLEAN DEFAULT 0,
                admin_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create user_article_reads table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_article_reads (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                article_id VARCHAR(36) NOT NULL,
                started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                time_spent_seconds INTEGER DEFAULT 0,
                scroll_depth_percentage REAL DEFAULT 0.0,
                engagement_score REAL DEFAULT 0.0,
                found_helpful BOOLEAN,
                would_recommend BOOLEAN,
                difficulty_rating INTEGER,
                relevance_rating INTEGER,
                reading_session_id VARCHAR(100),
                source_page VARCHAR(200),
                device_type VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                UNIQUE(user_id, article_id)
            )
        """))
        
        # Create user_article_bookmarks table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_article_bookmarks (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                article_id VARCHAR(36) NOT NULL,
                notes TEXT,
                tags TEXT, -- JSON stored as TEXT
                priority INTEGER DEFAULT 1,
                folder_name VARCHAR(100) DEFAULT 'General',
                is_archived BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                UNIQUE(user_id, article_id)
            )
        """))
        
        # Create user_article_ratings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_article_ratings (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                article_id VARCHAR(36) NOT NULL,
                overall_rating INTEGER NOT NULL,
                helpfulness_rating INTEGER,
                clarity_rating INTEGER,
                actionability_rating INTEGER,
                cultural_relevance_rating INTEGER,
                review_text TEXT,
                review_title VARCHAR(200),
                is_approved BOOLEAN DEFAULT 1,
                is_anonymous BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                UNIQUE(user_id, article_id)
            )
        """))
        
        # Create user_article_progress table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_article_progress (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                article_id VARCHAR(36) NOT NULL,
                current_phase VARCHAR(10) NOT NULL CHECK (current_phase IN ('BE', 'DO', 'HAVE')),
                phase_progress REAL DEFAULT 0.0,
                total_progress REAL DEFAULT 0.0,
                learning_objectives_achieved TEXT, -- JSON stored as TEXT
                skills_developed TEXT, -- JSON stored as TEXT
                actions_taken TEXT, -- JSON stored as TEXT
                self_assessment_score INTEGER,
                confidence_increase REAL,
                knowledge_retention_score REAL,
                next_recommended_article_id VARCHAR(36),
                next_phase_target VARCHAR(10) CHECK (next_phase_target IN ('BE', 'DO', 'HAVE')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (next_recommended_article_id) REFERENCES articles(id) ON DELETE SET NULL,
                UNIQUE(user_id, article_id)
            )
        """))
        
        # Create article_recommendations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS article_recommendations (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                article_id VARCHAR(36) NOT NULL,
                recommendation_score REAL NOT NULL,
                recommendation_reason VARCHAR(200),
                recommendation_source VARCHAR(100),
                user_income_match REAL,
                user_career_match REAL,
                user_goals_match REAL,
                cultural_relevance_match REAL,
                is_displayed BOOLEAN DEFAULT 0,
                is_clicked BOOLEAN DEFAULT 0,
                is_read BOOLEAN DEFAULT 0,
                display_position INTEGER,
                recommended_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                displayed_at DATETIME,
                clicked_at DATETIME,
                read_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """))
        
        # Create article_analytics table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS article_analytics (
                id VARCHAR(36) PRIMARY KEY,
                article_id VARCHAR(36) NOT NULL UNIQUE,
                total_views INTEGER DEFAULT 0,
                total_reads INTEGER DEFAULT 0,
                total_bookmarks INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                completion_rate REAL DEFAULT 0.0,
                average_time_spent REAL DEFAULT 0.0,
                average_scroll_depth REAL DEFAULT 0.0,
                average_rating REAL DEFAULT 0.0,
                total_ratings INTEGER DEFAULT 0,
                helpfulness_score REAL DEFAULT 0.0,
                clarity_score REAL DEFAULT 0.0,
                actionability_score REAL DEFAULT 0.0,
                cultural_relevance_score REAL DEFAULT 0.0,
                recommendation_click_rate REAL DEFAULT 0.0,
                recommendation_read_rate REAL DEFAULT 0.0,
                demographic_breakdown TEXT, -- JSON stored as TEXT
                phase_effectiveness TEXT, -- JSON stored as TEXT
                daily_views TEXT, -- JSON stored as TEXT
                weekly_engagement TEXT, -- JSON stored as TEXT
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        """))
        
        # Create indexes for performance
        print("Creating indexes...")
        
        # Articles table indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_primary_phase ON articles(primary_phase)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_difficulty_level ON articles(difficulty_level)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_demographic_relevance ON articles(demographic_relevance)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_domain ON articles(domain)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_is_active ON articles(is_active)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_is_featured ON articles(is_featured)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_articles_publish_date ON articles(publish_date)"))
        
        # User article reads indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_reads_user_id ON user_article_reads(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_reads_article_id ON user_article_reads(article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_reads_created_at ON user_article_reads(created_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_reads_completed_at ON user_article_reads(completed_at)"))
        
        # User article bookmarks indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_bookmarks_user_id ON user_article_bookmarks(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_bookmarks_article_id ON user_article_bookmarks(article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_bookmarks_folder_name ON user_article_bookmarks(folder_name)"))
        
        # User article ratings indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_ratings_user_id ON user_article_ratings(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_ratings_article_id ON user_article_ratings(article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_ratings_overall_rating ON user_article_ratings(overall_rating)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_ratings_is_approved ON user_article_ratings(is_approved)"))
        
        # User article progress indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_progress_user_id ON user_article_progress(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_progress_article_id ON user_article_progress(article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_article_progress_current_phase ON user_article_progress(current_phase)"))
        
        # Article recommendations indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_recommendations_user_id ON article_recommendations(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_recommendations_article_id ON article_recommendations(article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_recommendations_score ON article_recommendations(recommendation_score)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_recommendations_recommended_at ON article_recommendations(recommended_at)"))
        
        # Article analytics indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_analytics_article_id ON article_analytics(article_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_analytics_total_views ON article_analytics(total_views)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_analytics_total_reads ON article_analytics(total_reads)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_article_analytics_average_rating ON article_analytics(average_rating)"))
        
        # Commit the transaction
        conn.commit()
        
        print("Article library tables created successfully!")
        
        # Load sample data from classified articles
        load_sample_articles(conn)
        
        print("Migration completed successfully!")

def load_sample_articles(conn):
    """Load sample articles from the classified data files"""
    
    print("Loading sample articles from classified data...")
    
    # Load from the complete classified articles file
    sample_file = "data/classified_articles_complete.json"
    
    if not os.path.exists(sample_file):
        print(f"Warning: Sample data file {sample_file} not found. Skipping data load.")
        return
    
    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
        
        # Load first 10 articles as sample data
        sample_articles = articles_data[:10]
        
        for article_data in sample_articles:
            # Generate a unique ID for the article
            article_id = str(uuid.uuid4())
            
            # Extract domain from URL
            url = article_data.get('url', '')
            domain = url.split('/')[2] if url and len(url.split('/')) > 2 else 'unknown'
            
            # Prepare the article data
            article_values = {
                'id': article_id,
                'url': url,
                'title': article_data.get('title', ''),
                'content': article_data.get('content_preview', '')[:1000],  # Truncate for sample
                'content_preview': article_data.get('content_preview', '')[:500],
                'primary_phase': article_data.get('primary_phase', 'DO'),
                'difficulty_level': article_data.get('difficulty_level', 'Intermediate'),
                'confidence_score': article_data.get('confidence_score', 0.0),
                'demographic_relevance': article_data.get('demographic_relevance', 5),
                'cultural_sensitivity': article_data.get('cultural_sensitivity', 5),
                'income_impact_potential': article_data.get('income_impact_potential', 5),
                'actionability_score': article_data.get('actionability_score', 5),
                'professional_development_value': article_data.get('professional_development_value', 5),
                'key_topics': json.dumps(article_data.get('key_topics', [])),
                'learning_objectives': json.dumps(article_data.get('learning_objectives', [])),
                'prerequisites': json.dumps(article_data.get('prerequisites', [])),
                'cultural_relevance_keywords': json.dumps(article_data.get('cultural_relevance_keywords', [])),
                'target_income_range': article_data.get('target_income_range', '$40K-$60K'),
                'career_stage': article_data.get('career_stage', 'Mid-career'),
                'recommended_reading_order': article_data.get('recommended_reading_order', 50),
                'domain': domain,
                'source_quality_score': 0.7,  # Default quality score
                'is_active': True,
                'is_featured': False,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert the article
            conn.execute(text("""
                INSERT OR REPLACE INTO articles (
                    id, url, title, content, content_preview, primary_phase, 
                    difficulty_level, confidence_score, demographic_relevance,
                    cultural_sensitivity, income_impact_potential, actionability_score,
                    professional_development_value, key_topics, learning_objectives,
                    prerequisites, cultural_relevance_keywords, target_income_range,
                    career_stage, recommended_reading_order, domain, source_quality_score,
                    is_active, is_featured, created_at, updated_at
                ) VALUES (
                    :id, :url, :title, :content, :content_preview, :primary_phase,
                    :difficulty_level, :confidence_score, :demographic_relevance,
                    :cultural_sensitivity, :income_impact_potential, :actionability_score,
                    :professional_development_value, :key_topics, :learning_objectives,
                    :prerequisites, :cultural_relevance_keywords, :target_income_range,
                    :career_stage, :recommended_reading_order, :domain, :source_quality_score,
                    :is_active, :is_featured, :created_at, :updated_at
                )
            """), article_values)
            
            # Create analytics record for the article
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
                'article_id': article_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        
        conn.commit()
        print(f"Loaded {len(sample_articles)} sample articles successfully!")
        
    except Exception as e:
        print(f"Error loading sample articles: {e}")
        conn.rollback()

if __name__ == "__main__":
    run_migration()
