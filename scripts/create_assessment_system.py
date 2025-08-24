#!/usr/bin/env python3
"""
Create Assessment System Script
Creates default assessment templates, scoring thresholds, access mapping, and gatekeeping logic
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
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
        logging.FileHandler('assessment_system_creation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AssessmentSystemCreator:
    """Create comprehensive assessment system with templates and gatekeeping"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
        self.engine = None
        self.session = None
        
        # Assessment configuration
        self.scoring_thresholds = {
            'Beginner': 0,      # 0-59%
            'Intermediate': 60,  # 60-79%
            'Advanced': 80       # 80-100%
        }
        
        # Default assessment templates
        self.assessment_templates = {
            'be_identity_mindset': {
                'name': 'Identity & Mindset Assessment',
                'description': 'Assess your financial identity and mindset',
                'phase': 'BE',
                'questions': [
                    {
                        'id': 'be_confidence',
                        'text': 'How confident are you in your ability to build wealth?',
                        'type': 'rating',
                        'options': [
                            {'value': 1, 'text': 'Not confident at all', 'points': 10},
                            {'value': 2, 'text': 'Somewhat confident', 'points': 20},
                            {'value': 3, 'text': 'Confident', 'points': 30},
                            {'value': 4, 'text': 'Very confident', 'points': 40},
                            {'value': 5, 'text': 'Extremely confident', 'points': 50}
                        ]
                    },
                    {
                        'id': 'be_mindset',
                        'text': 'What best describes your current money mindset?',
                        'type': 'radio',
                        'options': [
                            {'value': 'scarcity', 'text': 'Scarcity mindset - money is limited', 'points': 10},
                            {'value': 'neutral', 'text': 'Neutral - money is a tool', 'points': 30},
                            {'value': 'abundance', 'text': 'Abundance mindset - opportunities are everywhere', 'points': 50}
                        ]
                    },
                    {
                        'id': 'be_identity',
                        'text': 'How do you identify with money and wealth?',
                        'type': 'radio',
                        'options': [
                            {'value': 'struggler', 'text': 'I struggle with money', 'points': 10},
                            {'value': 'learner', 'text': 'I\'m learning about money', 'points': 30},
                            {'value': 'builder', 'text': 'I\'m building wealth', 'points': 50},
                            {'value': 'creator', 'text': 'I create wealth', 'points': 70}
                        ]
                    },
                    {
                        'id': 'be_goals',
                        'text': 'What are your primary financial goals?',
                        'type': 'checkbox',
                        'options': [
                            {'value': 'survive', 'text': 'Just survive financially', 'points': 10},
                            {'value': 'stability', 'text': 'Achieve financial stability', 'points': 20},
                            {'value': 'growth', 'text': 'Grow my wealth', 'points': 30},
                            {'value': 'freedom', 'text': 'Achieve financial freedom', 'points': 40},
                            {'value': 'legacy', 'text': 'Build generational wealth', 'points': 50}
                        ]
                    }
                ]
            },
            'do_skills_action': {
                'name': 'Skills & Action Assessment',
                'description': 'Assess your financial skills and action-taking ability',
                'phase': 'DO',
                'questions': [
                    {
                        'id': 'do_budgeting',
                        'text': 'How would you rate your budgeting skills?',
                        'type': 'rating',
                        'options': [
                            {'value': 1, 'text': 'I don\'t budget', 'points': 10},
                            {'value': 2, 'text': 'I try to budget but struggle', 'points': 20},
                            {'value': 3, 'text': 'I have a basic budget', 'points': 30},
                            {'value': 4, 'text': 'I have a detailed budget', 'points': 40},
                            {'value': 5, 'text': 'I have advanced budgeting systems', 'points': 50}
                        ]
                    },
                    {
                        'id': 'do_investing',
                        'text': 'What is your experience with investing?',
                        'type': 'radio',
                        'options': [
                            {'value': 'none', 'text': 'No experience', 'points': 10},
                            {'value': 'basic', 'text': 'Basic knowledge', 'points': 30},
                            {'value': 'moderate', 'text': 'Moderate experience', 'points': 50},
                            {'value': 'advanced', 'text': 'Advanced experience', 'points': 70}
                        ]
                    },
                    {
                        'id': 'do_actions',
                        'text': 'How often do you take action on financial opportunities?',
                        'type': 'radio',
                        'options': [
                            {'value': 'never', 'text': 'I rarely take action', 'points': 10},
                            {'value': 'sometimes', 'text': 'I take action sometimes', 'points': 30},
                            {'value': 'often', 'text': 'I take action often', 'points': 50},
                            {'value': 'always', 'text': 'I always take action', 'points': 70}
                        ]
                    },
                    {
                        'id': 'do_skills',
                        'text': 'Which financial skills do you have?',
                        'type': 'checkbox',
                        'options': [
                            {'value': 'saving', 'text': 'Saving money', 'points': 15},
                            {'value': 'budgeting', 'text': 'Budgeting', 'points': 15},
                            {'value': 'investing', 'text': 'Investing', 'points': 20},
                            {'value': 'tax_planning', 'text': 'Tax planning', 'points': 15},
                            {'value': 'estate_planning', 'text': 'Estate planning', 'points': 15},
                            {'value': 'business', 'text': 'Business ownership', 'points': 20}
                        ]
                    }
                ]
            },
            'have_results_wealth': {
                'name': 'Results & Wealth Assessment',
                'description': 'Assess your current financial results and wealth status',
                'phase': 'HAVE',
                'questions': [
                    {
                        'id': 'have_income',
                        'text': 'What is your current annual income?',
                        'type': 'radio',
                        'options': [
                            {'value': 'under_30k', 'text': 'Under $30,000', 'points': 10},
                            {'value': '30k_50k', 'text': '$30,000 - $50,000', 'points': 20},
                            {'value': '50k_80k', 'text': '$50,000 - $80,000', 'points': 30},
                            {'value': '80k_120k', 'text': '$80,000 - $120,000', 'points': 40},
                            {'value': '120k_200k', 'text': '$120,000 - $200,000', 'points': 50},
                            {'value': 'over_200k', 'text': 'Over $200,000', 'points': 70}
                        ]
                    },
                    {
                        'id': 'have_assets',
                        'text': 'What is your approximate net worth?',
                        'type': 'radio',
                        'options': [
                            {'value': 'negative', 'text': 'Negative (more debt than assets)', 'points': 10},
                            {'value': 'under_10k', 'text': 'Under $10,000', 'points': 20},
                            {'value': '10k_50k', 'text': '$10,000 - $50,000', 'points': 30},
                            {'value': '50k_100k', 'text': '$50,000 - $100,000', 'points': 40},
                            {'value': '100k_500k', 'text': '$100,000 - $500,000', 'points': 50},
                            {'value': 'over_500k', 'text': 'Over $500,000', 'points': 70}
                        ]
                    },
                    {
                        'id': 'have_investments',
                        'text': 'What types of investments do you have?',
                        'type': 'checkbox',
                        'options': [
                            {'value': 'savings', 'text': 'Savings account', 'points': 10},
                            {'value': 'retirement', 'text': 'Retirement accounts', 'points': 15},
                            {'value': 'stocks', 'text': 'Stocks/bonds', 'points': 20},
                            {'value': 'real_estate', 'text': 'Real estate', 'points': 25},
                            {'value': 'business', 'text': 'Business ownership', 'points': 30}
                        ]
                    },
                    {
                        'id': 'have_passive_income',
                        'text': 'Do you have passive income streams?',
                        'type': 'radio',
                        'options': [
                            {'value': 'none', 'text': 'No passive income', 'points': 10},
                            {'value': 'some', 'text': 'Some passive income', 'points': 30},
                            {'value': 'significant', 'text': 'Significant passive income', 'points': 50},
                            {'value': 'multiple', 'text': 'Multiple passive income streams', 'points': 70}
                        ]
                    }
                ]
            }
        }
        
        # Access control mapping
        self.access_mapping = {
            'Beginner': {
                'BE': ['Beginner'],
                'DO': ['Beginner'],
                'HAVE': ['Beginner']
            },
            'Intermediate': {
                'BE': ['Beginner', 'Intermediate'],
                'DO': ['Beginner', 'Intermediate'],
                'HAVE': ['Beginner', 'Intermediate']
            },
            'Advanced': {
                'BE': ['Beginner', 'Intermediate', 'Advanced'],
                'DO': ['Beginner', 'Intermediate', 'Advanced'],
                'HAVE': ['Beginner', 'Intermediate', 'Advanced']
            }
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
    
    def create_assessment_templates_table(self) -> bool:
        """Create assessment templates table"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS assessment_templates (
                        id VARCHAR(36) PRIMARY KEY,
                        template_key VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        phase VARCHAR(10) NOT NULL,
                        questions JSON NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assessment_templates_phase ON assessment_templates(phase)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assessment_templates_active ON assessment_templates(is_active)"))
                
                conn.commit()
                logger.info("Created assessment_templates table")
                return True
                
        except Exception as e:
            logger.error(f"Error creating assessment_templates table: {e}")
            return False
    
    def create_access_control_table(self) -> bool:
        """Create access control mapping table"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS access_control_mapping (
                        id VARCHAR(36) PRIMARY KEY,
                        user_level VARCHAR(20) NOT NULL,
                        article_phase VARCHAR(10) NOT NULL,
                        allowed_difficulties JSON NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_level, article_phase)
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_access_control_user_level ON access_control_mapping(user_level)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_access_control_phase ON access_control_mapping(article_phase)"))
                
                conn.commit()
                logger.info("Created access_control_mapping table")
                return True
                
        except Exception as e:
            logger.error(f"Error creating access_control_mapping table: {e}")
            return False
    
    def insert_default_assessment_templates(self) -> bool:
        """Insert default assessment templates"""
        try:
            with self.engine.connect() as conn:
                for template_key, template in self.assessment_templates.items():
                    conn.execute(text("""
                        INSERT OR REPLACE INTO assessment_templates (
                            id, template_key, name, description, phase, questions, is_active
                        ) VALUES (
                            :id, :template_key, :name, :description, :phase, :questions, :is_active
                        )
                    """), {
                        'id': str(uuid.uuid4()),
                        'template_key': template_key,
                        'name': template['name'],
                        'description': template['description'],
                        'phase': template['phase'],
                        'questions': json.dumps(template['questions']),
                        'is_active': True
                    })
                
                conn.commit()
                logger.info(f"Inserted {len(self.assessment_templates)} assessment templates")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting assessment templates: {e}")
            return False
    
    def insert_access_control_mapping(self) -> bool:
        """Insert access control mapping"""
        try:
            with self.engine.connect() as conn:
                for user_level, phase_mapping in self.access_mapping.items():
                    for article_phase, allowed_difficulties in phase_mapping.items():
                        conn.execute(text("""
                            INSERT OR REPLACE INTO access_control_mapping (
                                id, user_level, article_phase, allowed_difficulties
                            ) VALUES (
                                :id, :user_level, :article_phase, :allowed_difficulties
                            )
                        """), {
                            'id': str(uuid.uuid4()),
                            'user_level': user_level,
                            'article_phase': article_phase,
                            'allowed_difficulties': json.dumps(allowed_difficulties)
                        })
                
                conn.commit()
                logger.info("Inserted access control mapping")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting access control mapping: {e}")
            return False
    
    def calculate_assessment_score(self, answers: Dict[str, Any], template_key: str) -> Dict[str, Any]:
        """Calculate assessment score based on answers and template"""
        template = self.assessment_templates.get(template_key)
        if not template:
            return {'error': 'Template not found'}
        
        total_score = 0
        max_possible_score = 0
        question_scores = {}
        
        for question in template['questions']:
            question_id = question['id']
            answer = answers.get(question_id)
            
            if answer is None:
                continue
            
            question_score = 0
            question_max = 0
            
            if question['type'] == 'radio':
                # Single choice
                for option in question['options']:
                    question_max = max(question_max, option['points'])
                    if option['value'] == answer:
                        question_score = option['points']
            
            elif question['type'] == 'checkbox':
                # Multiple choice
                if isinstance(answer, list):
                    for selected_value in answer:
                        for option in question['options']:
                            if option['value'] == selected_value:
                                question_score += option['points']
                                question_max = max(question_max, option['points'])
            
            elif question['type'] == 'rating':
                # Rating scale
                if isinstance(answer, (int, float)) and 1 <= answer <= 5:
                    for option in question['options']:
                        if option['value'] == answer:
                            question_score = option['points']
                            question_max = max(question_max, option['points'])
                            break
            
            total_score += question_score
            max_possible_score += question_max
            question_scores[question_id] = question_score
        
        # Calculate percentage score
        percentage_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        # Determine level based on thresholds
        level = 'Beginner'
        if percentage_score >= self.scoring_thresholds['Advanced']:
            level = 'Advanced'
        elif percentage_score >= self.scoring_thresholds['Intermediate']:
            level = 'Intermediate'
        
        return {
            'total_score': total_score,
            'max_possible_score': max_possible_score,
            'percentage_score': round(percentage_score, 2),
            'level': level,
            'phase': template['phase'],
            'question_scores': question_scores
        }
    
    def check_article_access(self, user_level: str, article_phase: str, article_difficulty: str) -> bool:
        """Check if user has access to an article based on their level"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT allowed_difficulties 
                    FROM access_control_mapping 
                    WHERE user_level = :user_level AND article_phase = :article_phase
                """), {
                    'user_level': user_level,
                    'article_phase': article_phase
                })
                
                row = result.fetchone()
                if not row:
                    return False
                
                allowed_difficulties = json.loads(row[0])
                return article_difficulty in allowed_difficulties
                
        except Exception as e:
            logger.error(f"Error checking article access: {e}")
            return False
    
    def create_sample_user_assessments(self) -> bool:
        """Create sample user assessments for testing"""
        try:
            sample_users = [
                {
                    'user_id': 1,
                    'name': 'John Beginner',
                    'assessments': {
                        'be_identity_mindset': {
                            'be_confidence': 2,
                            'be_mindset': 'neutral',
                            'be_identity': 'learner',
                            'be_goals': ['stability', 'growth']
                        },
                        'do_skills_action': {
                            'do_budgeting': 2,
                            'do_investing': 'basic',
                            'do_actions': 'sometimes',
                            'do_skills': ['saving', 'budgeting']
                        },
                        'have_results_wealth': {
                            'have_income': '30k_50k',
                            'have_assets': 'under_10k',
                            'have_investments': ['savings'],
                            'have_passive_income': 'none'
                        }
                    }
                },
                {
                    'user_id': 2,
                    'name': 'Sarah Intermediate',
                    'assessments': {
                        'be_identity_mindset': {
                            'be_confidence': 4,
                            'be_mindset': 'abundance',
                            'be_identity': 'builder',
                            'be_goals': ['growth', 'freedom']
                        },
                        'do_skills_action': {
                            'do_budgeting': 4,
                            'do_investing': 'moderate',
                            'do_actions': 'often',
                            'do_skills': ['saving', 'budgeting', 'investing']
                        },
                        'have_results_wealth': {
                            'have_income': '80k_120k',
                            'have_assets': '50k_100k',
                            'have_investments': ['savings', 'retirement', 'stocks'],
                            'have_passive_income': 'some'
                        }
                    }
                },
                {
                    'user_id': 3,
                    'name': 'Mike Advanced',
                    'assessments': {
                        'be_identity_mindset': {
                            'be_confidence': 5,
                            'be_mindset': 'abundance',
                            'be_identity': 'creator',
                            'be_goals': ['freedom', 'legacy']
                        },
                        'do_skills_action': {
                            'do_budgeting': 5,
                            'do_investing': 'advanced',
                            'do_actions': 'always',
                            'do_skills': ['saving', 'budgeting', 'investing', 'tax_planning', 'business']
                        },
                        'have_results_wealth': {
                            'have_income': 'over_200k',
                            'have_assets': 'over_500k',
                            'have_investments': ['savings', 'retirement', 'stocks', 'real_estate', 'business'],
                            'have_passive_income': 'multiple'
                        }
                    }
                }
            ]
            
            with self.engine.connect() as conn:
                for user in sample_users:
                    # Calculate scores for each phase
                    be_score = self.calculate_assessment_score(
                        user['assessments']['be_identity_mindset'], 
                        'be_identity_mindset'
                    )
                    do_score = self.calculate_assessment_score(
                        user['assessments']['do_skills_action'], 
                        'do_skills_action'
                    )
                    have_score = self.calculate_assessment_score(
                        user['assessments']['have_results_wealth'], 
                        'have_results_wealth'
                    )
                    
                    # Insert assessment scores
                    conn.execute(text("""
                        INSERT OR REPLACE INTO user_assessment_scores (
                            id, user_id, be_score, do_score, have_score,
                            be_level, do_level, have_level, overall_readiness_level,
                            assessment_date, assessment_version, total_questions,
                            confidence_score, is_valid, created_at, updated_at
                        ) VALUES (
                            :id, :user_id, :be_score, :do_score, :have_score,
                            :be_level, :do_level, :have_level, :overall_readiness_level,
                            :assessment_date, :assessment_version, :total_questions,
                            :confidence_score, :is_valid, :created_at, :updated_at
                        )
                    """), {
                        'id': str(uuid.uuid4()),
                        'user_id': user['user_id'],
                        'be_score': be_score['total_score'],
                        'do_score': do_score['total_score'],
                        'have_score': have_score['total_score'],
                        'be_level': be_score['level'],
                        'do_level': do_score['level'],
                        'have_level': have_score['level'],
                        'overall_readiness_level': self._calculate_overall_level([be_score, do_score, have_score]),
                        'assessment_date': datetime.utcnow(),
                        'assessment_version': '1.0',
                        'total_questions': 12,
                        'confidence_score': 0.9,
                        'is_valid': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    })
                
                conn.commit()
                logger.info(f"Created {len(sample_users)} sample user assessments")
                return True
                
        except Exception as e:
            logger.error(f"Error creating sample user assessments: {e}")
            return False
    
    def _calculate_overall_level(self, phase_scores: List[Dict]) -> str:
        """Calculate overall readiness level based on phase scores"""
        avg_percentage = sum(score['percentage_score'] for score in phase_scores) / len(phase_scores)
        
        if avg_percentage >= 80:
            return 'Advanced'
        elif avg_percentage >= 60:
            return 'Intermediate'
        else:
            return 'Beginner'
    
    def test_gatekeeping_logic(self) -> Dict[str, Any]:
        """Test gatekeeping logic with sample data"""
        logger.info("Testing gatekeeping logic...")
        
        test_results = {
            'access_tests': [],
            'progressive_unlocking': [],
            'scoring_accuracy': []
        }
        
        try:
            # Test article access for different user levels
            test_articles = [
                {'phase': 'BE', 'difficulty': 'Beginner', 'title': 'Basic Mindset Article'},
                {'phase': 'BE', 'difficulty': 'Intermediate', 'title': 'Intermediate Mindset Article'},
                {'phase': 'BE', 'difficulty': 'Advanced', 'title': 'Advanced Mindset Article'},
                {'phase': 'DO', 'difficulty': 'Beginner', 'title': 'Basic Skills Article'},
                {'phase': 'DO', 'difficulty': 'Advanced', 'title': 'Advanced Skills Article'},
                {'phase': 'HAVE', 'difficulty': 'Intermediate', 'title': 'Intermediate Results Article'}
            ]
            
            user_levels = ['Beginner', 'Intermediate', 'Advanced']
            
            for user_level in user_levels:
                for article in test_articles:
                    has_access = self.check_article_access(
                        user_level, 
                        article['phase'], 
                        article['difficulty']
                    )
                    
                    test_results['access_tests'].append({
                        'user_level': user_level,
                        'article_phase': article['phase'],
                        'article_difficulty': article['difficulty'],
                        'article_title': article['title'],
                        'has_access': has_access,
                        'expected': self._get_expected_access(user_level, article['phase'], article['difficulty'])
                    })
            
            # Test progressive unlocking
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT user_id, be_level, do_level, have_level, overall_readiness_level
                    FROM user_assessment_scores
                    ORDER BY user_id
                """))
                
                for row in result.fetchall():
                    user_level = row[4]  # overall_readiness_level
                    test_results['progressive_unlocking'].append({
                        'user_id': row[0],
                        'overall_level': user_level,
                        'be_level': row[1],
                        'do_level': row[2],
                        'have_level': row[3],
                        'accessible_phases': self._get_accessible_phases(user_level)
                    })
            
            # Test scoring accuracy
            test_results['scoring_accuracy'] = self._test_scoring_accuracy()
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error testing gatekeeping logic: {e}")
            return {'error': str(e)}
    
    def _get_expected_access(self, user_level: str, article_phase: str, article_difficulty: str) -> bool:
        """Get expected access based on access mapping"""
        if user_level not in self.access_mapping:
            return False
        
        if article_phase not in self.access_mapping[user_level]:
            return False
        
        return article_difficulty in self.access_mapping[user_level][article_phase]
    
    def _get_accessible_phases(self, user_level: str) -> Dict[str, List[str]]:
        """Get accessible phases and difficulties for a user level"""
        if user_level not in self.access_mapping:
            return {}
        
        return self.access_mapping[user_level]
    
    def _test_scoring_accuracy(self) -> List[Dict]:
        """Test scoring accuracy with known inputs"""
        test_cases = [
            {
                'name': 'Perfect Beginner Score',
                'answers': {
                    'be_confidence': 1,
                    'be_mindset': 'scarcity',
                    'be_identity': 'struggler',
                    'be_goals': ['survive']
                },
                'expected_level': 'Beginner'
            },
            {
                'name': 'Perfect Intermediate Score',
                'answers': {
                    'be_confidence': 3,
                    'be_mindset': 'neutral',
                    'be_identity': 'builder',
                    'be_goals': ['stability', 'growth']
                },
                'expected_level': 'Intermediate'
            },
            {
                'name': 'Perfect Advanced Score',
                'answers': {
                    'be_confidence': 5,
                    'be_mindset': 'abundance',
                    'be_identity': 'creator',
                    'be_goals': ['freedom', 'legacy']
                },
                'expected_level': 'Advanced'
            }
        ]
        
        results = []
        for test_case in test_cases:
            score = self.calculate_assessment_score(test_case['answers'], 'be_identity_mindset')
            results.append({
                'test_name': test_case['name'],
                'expected_level': test_case['expected_level'],
                'actual_level': score['level'],
                'percentage_score': score['percentage_score'],
                'passed': score['level'] == test_case['expected_level']
            })
        
        return results
    
    def generate_system_report(self) -> str:
        """Generate comprehensive system report"""
        report = []
        report.append("=" * 80)
        report.append("ASSESSMENT SYSTEM CREATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now()}")
        report.append(f"Database: {self.database_url}")
        report.append("")
        
        # System configuration
        report.append("SYSTEM CONFIGURATION:")
        report.append("-" * 40)
        report.append(f"Scoring Thresholds:")
        for level, threshold in self.scoring_thresholds.items():
            report.append(f"  {level}: {threshold}%")
        report.append("")
        
        # Assessment templates
        report.append("ASSESSMENT TEMPLATES:")
        report.append("-" * 40)
        for template_key, template in self.assessment_templates.items():
            report.append(f"• {template['name']} ({template['phase']} phase)")
            report.append(f"  - {len(template['questions'])} questions")
            report.append(f"  - {template['description']}")
        report.append("")
        
        # Access control mapping
        report.append("ACCESS CONTROL MAPPING:")
        report.append("-" * 40)
        for user_level, phase_mapping in self.access_mapping.items():
            report.append(f"{user_level} users can access:")
            for phase, difficulties in phase_mapping.items():
                report.append(f"  {phase} phase: {', '.join(difficulties)}")
        report.append("")
        
        # Test results
        test_results = self.test_gatekeeping_logic()
        
        if 'access_tests' in test_results:
            report.append("GATEKEEPING TEST RESULTS:")
            report.append("-" * 40)
            
            # Access tests
            access_passed = sum(1 for test in test_results['access_tests'] if test['has_access'] == test['expected'])
            access_total = len(test_results['access_tests'])
            report.append(f"Access Control Tests: {access_passed}/{access_total} passed")
            
            # Progressive unlocking
            report.append(f"Progressive Unlocking Tests: {len(test_results['progressive_unlocking'])} users tested")
            
            # Scoring accuracy
            scoring_passed = sum(1 for test in test_results['scoring_accuracy'] if test['passed'])
            scoring_total = len(test_results['scoring_accuracy'])
            report.append(f"Scoring Accuracy Tests: {scoring_passed}/{scoring_total} passed")
        
        # Database verification
        report.append("")
        report.append("DATABASE VERIFICATION:")
        report.append("-" * 40)
        with self.engine.connect() as conn:
            # Assessment templates
            result = conn.execute(text("SELECT COUNT(*) FROM assessment_templates"))
            template_count = result.fetchone()[0]
            report.append(f"Assessment Templates: {template_count}")
            
            # Access control mapping
            result = conn.execute(text("SELECT COUNT(*) FROM access_control_mapping"))
            mapping_count = result.fetchone()[0]
            report.append(f"Access Control Mappings: {mapping_count}")
            
            # User assessments
            result = conn.execute(text("SELECT COUNT(*) FROM user_assessment_scores"))
            assessment_count = result.fetchone()[0]
            report.append(f"User Assessments: {assessment_count}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def create_assessment_system(self) -> bool:
        """Create complete assessment system"""
        logger.info("Creating assessment system...")
        
        # Connect to database
        if not self.connect_database():
            return False
        
        try:
            # Create tables
            if not self.create_assessment_templates_table():
                return False
            
            if not self.create_access_control_table():
                return False
            
            # Insert default data
            if not self.insert_default_assessment_templates():
                return False
            
            if not self.insert_access_control_mapping():
                return False
            
            # Create sample user assessments
            if not self.create_sample_user_assessments():
                return False
            
            # Generate and save report
            report = self.generate_system_report()
            
            # Save report to file
            report_filename = f"assessment_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            
            # Print report to console
            print(report)
            
            logger.info(f"Report saved to: {report_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating assessment system: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create assessment system with templates and gatekeeping')
    parser.add_argument('--database', help='Database URL')
    
    args = parser.parse_args()
    
    # Create assessment system
    creator = AssessmentSystemCreator(args.database)
    
    # Run creation
    success = creator.create_assessment_system()
    
    if success:
        logger.info("Assessment system created successfully!")
        return 0
    else:
        logger.error("Assessment system creation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
