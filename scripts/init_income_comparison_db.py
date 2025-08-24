#!/usr/bin/env python3
"""
Database Initialization Script for Income Comparison Calculator
Creates tables, indexes, and initial data for the income comparison system
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import database components
from backend.models import Base, engine, SessionLocal
from backend.models.income_comparison import (
    SalaryBenchmark, PredictionCache, LeadEngagementScore, SalaryPrediction,
    CareerPathRecommendation, LeadCaptureEvent, GamificationBadge, UserBadge,
    EmailSequence, EmailSend, IncomeComparisonAnalytics,
    ExperienceLevel, EducationLevel, IndustryType, BadgeType, EmailSequenceType
)
from backend.services.data_persistence import (
    salary_benchmark_repo, gamification_repo, email_sequence_repo
)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False


def populate_initial_data():
    """Populate initial data for the income comparison system"""
    logger.info("Populating initial data...")
    
    # 1. Create gamification badges
    create_gamification_badges()
    
    # 2. Create email sequences
    create_email_sequences()
    
    # 3. Create sample salary benchmarks
    create_sample_benchmarks()
    
    logger.info("✅ Initial data populated successfully")


def create_gamification_badges():
    """Create initial gamification badges"""
    logger.info("Creating gamification badges...")
    
    badges_data = [
        {
            'badge_name': 'Getting Started',
            'badge_description': 'Completed your first step in the income comparison process',
            'badge_icon': '🚀',
            'badge_color': '#3B82F6',
            'unlock_criteria': {'step_completed': 1},
            'badge_type': BadgeType.PROGRESS_MAKER,
            'rarity': 'common',
            'category': 'onboarding',
            'points_value': 10
        },
        {
            'badge_name': 'Salary Insight',
            'badge_description': 'Unlocked detailed salary analysis and benchmarking',
            'badge_icon': '💰',
            'badge_color': '#10B981',
            'unlock_criteria': {'step_completed': 2},
            'badge_type': BadgeType.SALARY_INSIGHT,
            'rarity': 'common',
            'category': 'analysis',
            'points_value': 15
        },
        {
            'badge_name': 'Career Planner',
            'badge_description': 'Generated personalized career plan and recommendations',
            'badge_icon': '📈',
            'badge_color': '#8B5CF6',
            'unlock_criteria': {'step_completed': 3},
            'badge_type': BadgeType.CAREER_PLANNER,
            'rarity': 'rare',
            'category': 'planning',
            'points_value': 25
        },
        {
            'badge_name': 'Market Expert',
            'badge_description': 'Achieved top 10% salary percentile in your field',
            'badge_icon': '🏆',
            'badge_color': '#F59E0B',
            'unlock_criteria': {'percentile_rank': 90},
            'badge_type': BadgeType.MARKET_EXPERT,
            'rarity': 'epic',
            'category': 'achievement',
            'points_value': 50
        },
        {
            'badge_name': 'Goal Setter',
            'badge_description': 'Set ambitious career goals and target salary',
            'badge_icon': '🎯',
            'badge_color': '#EF4444',
            'unlock_criteria': {'target_salary_set': True},
            'badge_type': BadgeType.GOAL_SETTER,
            'rarity': 'common',
            'category': 'planning',
            'points_value': 20
        },
        {
            'badge_name': 'Skill Developer',
            'badge_description': 'Identified key skills for career advancement',
            'badge_icon': '🛠️',
            'badge_color': '#06B6D4',
            'unlock_criteria': {'skills_identified': 3},
            'badge_type': BadgeType.SKILL_DEVELOPER,
            'rarity': 'rare',
            'category': 'development',
            'points_value': 30
        },
        {
            'badge_name': 'Network Builder',
            'badge_description': 'Engaged with professional networking features',
            'badge_icon': '🤝',
            'badge_color': '#84CC16',
            'unlock_criteria': {'networking_actions': 5},
            'badge_type': BadgeType.NETWORK_BUILDER,
            'rarity': 'common',
            'category': 'networking',
            'points_value': 15
        },
        {
            'badge_name': 'Data Driven',
            'badge_description': 'Viewed comprehensive salary and market data',
            'badge_icon': '📊',
            'badge_color': '#6366F1',
            'unlock_criteria': {'data_views': 10},
            'badge_type': BadgeType.DATA_DRIVEN,
            'rarity': 'rare',
            'category': 'analysis',
            'points_value': 35
        }
    ]
    
    for badge_data in badges_data:
        existing = gamification_repo.get_by_name(badge_data['badge_name'])
        if not existing:
            gamification_repo.create(badge_data)
            logger.info(f"Created badge: {badge_data['badge_name']}")
        else:
            logger.info(f"Badge already exists: {badge_data['badge_name']}")


def create_email_sequences():
    """Create initial email sequences"""
    logger.info("Creating email sequences...")
    
    sequences_data = [
        {
            'sequence_name': 'Welcome Series',
            'sequence_description': 'Welcome new leads with personalized insights',
            'trigger_event': 'lead_captured',
            'delay_hours': 0,
            'email_template': 'welcome_email',
            'subject_line': 'Welcome to Your Salary Journey!',
            'email_content': '''Hi {{first_name}},

Welcome to your personalized salary analysis journey! 

We're excited to help you understand your earning potential and discover opportunities for career growth.

Your personalized salary report is being prepared and will be ready shortly. In the meantime, explore our interactive tools to:

• Compare your salary to peers in your industry
• Discover career advancement opportunities  
• Identify skills that boost earning potential
• Plan your path to financial goals

Stay tuned for your detailed analysis!

Best regards,
The Mingus Team''',
            'sequence_type': EmailSequenceType.WELCOME,
            'is_active': True,
            'priority': 1,
            'personalization_fields': ['first_name', 'location', 'industry']
        },
        {
            'sequence_name': 'Salary Insights',
            'sequence_description': 'Follow up with detailed salary analysis',
            'trigger_event': 'report_generated',
            'delay_hours': 24,
            'email_template': 'salary_insights',
            'subject_line': 'Your Personalized Salary Analysis is Ready',
            'email_content': '''Hi {{first_name}},

Your detailed salary analysis and market insights are ready!

Key Findings:
• Your current salary: ${{current_salary}}
• Market average: ${{market_average}}
• Your percentile: {{percentile_rank}}%
• Salary gap: ${{salary_gap}}

Career Opportunities:
• 1-year projection: ${{predicted_1yr}}
• 3-year projection: ${{predicted_3yr}}
• 5-year projection: ${{predicted_5yr}}

View your full report: {{report_link}}

Best regards,
The Mingus Team''',
            'sequence_type': EmailSequenceType.SALARY_INSIGHTS,
            'is_active': True,
            'priority': 2,
            'personalization_fields': ['first_name', 'current_salary', 'market_average', 'percentile_rank', 'salary_gap', 'predicted_1yr', 'predicted_3yr', 'predicted_5yr', 'report_link']
        },
        {
            'sequence_name': 'Career Planning',
            'sequence_description': 'Send career advancement recommendations',
            'trigger_event': 'report_generated',
            'delay_hours': 72,
            'email_template': 'career_planning',
            'subject_line': 'Your Career Advancement Roadmap',
            'email_content': '''Hi {{first_name}},

Based on your profile, here's your personalized career advancement roadmap:

Top Recommendations:
{{#each recommendations}}
• {{title}}: {{description}}
{{/each}}

Investment Analysis:
• Total investment: ${{total_investment}}
• Projected return: ${{projected_return}}
• ROI: {{roi_percentage}}%

Timeline: {{estimated_timeline}} months

Ready to take action? {{action_link}}

Best regards,
The Mingus Team''',
            'sequence_type': EmailSequenceType.CAREER_PLANNING,
            'is_active': True,
            'priority': 3,
            'personalization_fields': ['first_name', 'recommendations', 'total_investment', 'projected_return', 'roi_percentage', 'estimated_timeline', 'action_link']
        },
        {
            'sequence_name': 'Skill Development',
            'sequence_description': 'Recommend skill development opportunities',
            'trigger_event': 'skills_identified',
            'delay_hours': 168,
            'email_template': 'skill_development',
            'subject_line': 'Skills That Will Boost Your Salary',
            'email_content': '''Hi {{first_name}},

Here are the top skills that can significantly increase your earning potential:

High-Impact Skills:
{{#each skills}}
• {{name}}: +{{salary_impact}}% salary boost
{{/each}}

Development Resources:
• Online courses: {{course_links}}
• Certifications: {{certification_links}}
• Networking events: {{event_links}}

Start your skill development journey: {{skill_development_link}}

Best regards,
The Mingus Team''',
            'sequence_type': EmailSequenceType.SKILL_DEVELOPMENT,
            'is_active': True,
            'priority': 4,
            'personalization_fields': ['first_name', 'skills', 'course_links', 'certification_links', 'event_links', 'skill_development_link']
        },
        {
            'sequence_name': 'Market Updates',
            'sequence_description': 'Send market trend updates and insights',
            'trigger_event': 'lead_engaged',
            'delay_hours': 336,
            'email_template': 'market_updates',
            'subject_line': 'Latest Market Trends in Your Industry',
            'email_content': '''Hi {{first_name}},

Stay ahead with the latest salary trends and market insights:

Market Trends:
• Industry growth: {{industry_growth}}%
• Salary inflation: {{salary_inflation}}%
• Hot skills: {{hot_skills}}

Your Market Position:
• Current percentile: {{current_percentile}}%
• Market movement: {{market_movement}}
• Opportunities: {{opportunities}}

View detailed trends: {{trends_link}}

Best regards,
The Mingus Team''',
            'sequence_type': EmailSequenceType.MARKET_UPDATES,
            'is_active': True,
            'priority': 5,
            'personalization_fields': ['first_name', 'industry_growth', 'salary_inflation', 'hot_skills', 'current_percentile', 'market_movement', 'opportunities', 'trends_link']
        },
        {
            'sequence_name': 'Re-engagement',
            'sequence_description': 'Re-engage inactive leads with new features',
            'trigger_event': 'lead_inactive',
            'delay_hours': 720,
            'email_template': 're_engagement',
            'subject_line': 'New Features to Help You Succeed',
            'email_content': '''Hi {{first_name}},

We've added new features to help you maximize your earning potential:

New Features:
• Advanced career simulator
• Real-time market data
• Skill gap analysis
• Networking opportunities

Your Progress:
• Last activity: {{last_activity}}
• Achievements: {{achievements}}
• Next steps: {{next_steps}}

Reconnect with your career goals: {{reconnect_link}}

Best regards,
The Mingus Team''',
            'sequence_type': EmailSequenceType.RE_ENGAGEMENT,
            'is_active': True,
            'priority': 6,
            'personalization_fields': ['first_name', 'last_activity', 'achievements', 'next_steps', 'reconnect_link']
        }
    ]
    
    for sequence_data in sequences_data:
        existing = email_sequence_repo.get_by_name(sequence_data['sequence_name'])
        if not existing:
            email_sequence_repo.create(sequence_data)
            logger.info(f"Created email sequence: {sequence_data['sequence_name']}")
        else:
            logger.info(f"Email sequence already exists: {sequence_data['sequence_name']}")


def create_sample_benchmarks():
    """Create sample salary benchmarks for major markets and industries"""
    logger.info("Creating sample salary benchmarks...")
    
    # Sample data for major markets and industries
    benchmarks_data = [
        # Technology - Atlanta
        {
            'location': 'atlanta',
            'industry': IndustryType.TECHNOLOGY,
            'experience_level': ExperienceLevel.ENTRY,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 65000,
            'median_salary': 63000,
            'percentile_25': 55000,
            'percentile_75': 72000,
            'percentile_90': 85000,
            'sample_size': 1250,
            'data_source': 'BLS'
        },
        {
            'location': 'atlanta',
            'industry': IndustryType.TECHNOLOGY,
            'experience_level': ExperienceLevel.MID,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 85000,
            'median_salary': 82000,
            'percentile_25': 72000,
            'percentile_75': 95000,
            'percentile_90': 110000,
            'sample_size': 2100,
            'data_source': 'BLS'
        },
        {
            'location': 'atlanta',
            'industry': IndustryType.TECHNOLOGY,
            'experience_level': ExperienceLevel.SENIOR,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 120000,
            'median_salary': 115000,
            'percentile_25': 95000,
            'percentile_75': 135000,
            'percentile_90': 160000,
            'sample_size': 1800,
            'data_source': 'BLS'
        },
        
        # Technology - New York
        {
            'location': 'new-york',
            'industry': IndustryType.TECHNOLOGY,
            'experience_level': ExperienceLevel.ENTRY,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 75000,
            'median_salary': 72000,
            'percentile_25': 65000,
            'percentile_75': 82000,
            'percentile_90': 95000,
            'sample_size': 2800,
            'data_source': 'BLS'
        },
        {
            'location': 'new-york',
            'industry': IndustryType.TECHNOLOGY,
            'experience_level': ExperienceLevel.MID,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 100000,
            'median_salary': 95000,
            'percentile_25': 82000,
            'percentile_75': 115000,
            'percentile_90': 135000,
            'sample_size': 3200,
            'data_source': 'BLS'
        },
        {
            'location': 'new-york',
            'industry': IndustryType.TECHNOLOGY,
            'experience_level': ExperienceLevel.SENIOR,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 150000,
            'median_salary': 140000,
            'percentile_25': 115000,
            'percentile_75': 170000,
            'percentile_90': 200000,
            'sample_size': 2500,
            'data_source': 'BLS'
        },
        
        # Healthcare - Atlanta
        {
            'location': 'atlanta',
            'industry': IndustryType.HEALTHCARE,
            'experience_level': ExperienceLevel.ENTRY,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 55000,
            'median_salary': 53000,
            'percentile_25': 45000,
            'percentile_75': 62000,
            'percentile_90': 75000,
            'sample_size': 1800,
            'data_source': 'BLS'
        },
        {
            'location': 'atlanta',
            'industry': IndustryType.HEALTHCARE,
            'experience_level': ExperienceLevel.MID,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 75000,
            'median_salary': 72000,
            'percentile_25': 62000,
            'percentile_75': 85000,
            'percentile_90': 100000,
            'sample_size': 2400,
            'data_source': 'BLS'
        },
        {
            'location': 'atlanta',
            'industry': IndustryType.HEALTHCARE,
            'experience_level': ExperienceLevel.SENIOR,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 100000,
            'median_salary': 95000,
            'percentile_25': 80000,
            'percentile_75': 115000,
            'percentile_90': 135000,
            'sample_size': 1600,
            'data_source': 'BLS'
        },
        
        # Finance - Atlanta
        {
            'location': 'atlanta',
            'industry': IndustryType.FINANCE,
            'experience_level': ExperienceLevel.ENTRY,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 60000,
            'median_salary': 58000,
            'percentile_25': 50000,
            'percentile_75': 67000,
            'percentile_90': 80000,
            'sample_size': 1500,
            'data_source': 'BLS'
        },
        {
            'location': 'atlanta',
            'industry': IndustryType.FINANCE,
            'experience_level': ExperienceLevel.MID,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 80000,
            'median_salary': 77000,
            'percentile_25': 67000,
            'percentile_75': 90000,
            'percentile_90': 110000,
            'sample_size': 2200,
            'data_source': 'BLS'
        },
        {
            'location': 'atlanta',
            'industry': IndustryType.FINANCE,
            'experience_level': ExperienceLevel.SENIOR,
            'education_level': EducationLevel.BACHELOR,
            'mean_salary': 110000,
            'median_salary': 105000,
            'percentile_25': 90000,
            'percentile_75': 125000,
            'percentile_90': 150000,
            'sample_size': 1900,
            'data_source': 'BLS'
        }
    ]
    
    for benchmark_data in benchmarks_data:
        existing = salary_benchmark_repo.get_benchmark(
            benchmark_data['location'],
            benchmark_data['industry'],
            benchmark_data['experience_level'],
            benchmark_data['education_level']
        )
        
        if not existing:
            salary_benchmark_repo.create(benchmark_data)
            logger.info(f"Created benchmark: {benchmark_data['location']} - {benchmark_data['industry'].value} - {benchmark_data['experience_level'].value}")
        else:
            logger.info(f"Benchmark already exists: {benchmark_data['location']} - {benchmark_data['industry'].value} - {benchmark_data['experience_level'].value}")


def verify_database_setup():
    """Verify that the database setup is complete"""
    logger.info("Verifying database setup...")
    
    try:
        with SessionLocal() as session:
            # Check if tables exist
            badge_count = session.query(GamificationBadge).count()
            sequence_count = session.query(EmailSequence).count()
            benchmark_count = session.query(SalaryBenchmark).count()
            
            logger.info(f"✅ Database verification complete:")
            logger.info(f"   - Gamification badges: {badge_count}")
            logger.info(f"   - Email sequences: {sequence_count}")
            logger.info(f"   - Salary benchmarks: {benchmark_count}")
            
            return True
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False


def main():
    """Main initialization function"""
    logger.info("🚀 Starting Income Comparison Database Initialization")
    
    # Create tables
    if not create_tables():
        logger.error("Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Populate initial data
    populate_initial_data()
    
    # Verify setup
    if not verify_database_setup():
        logger.error("Database verification failed. Exiting.")
        sys.exit(1)
    
    logger.info("🎉 Income Comparison Database Initialization Complete!")


if __name__ == "__main__":
    main() 