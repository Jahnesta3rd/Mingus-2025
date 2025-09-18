#!/usr/bin/env python3
"""
Job Matching API Endpoints
Provides REST API endpoints for the IncomeBoostJobMatcher system
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import asyncio
import sys
import os

# Add backend utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from income_boost_job_matcher import (
    IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel,
    JobOpportunity, CompanyProfile
)
from job_board_apis import JobBoardAPIManager, CompanyDataAPIManager

# Create blueprint
job_matching_api = Blueprint('job_matching_api', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@job_matching_api.route('/job-matching/search', methods=['POST'])
@cross_origin()
def search_jobs():
    """
    Search for income-focused job opportunities
    
    Request body:
    {
        "current_salary": 75000,
        "target_salary_increase": 0.25,
        "career_field": "technology",
        "experience_level": "mid",
        "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"],
        "remote_ok": true,
        "max_commute_time": 30,
        "must_have_benefits": ["health insurance", "401k"],
        "company_size_preference": "mid",
        "industry_preference": "technology",
        "equity_required": false,
        "min_company_rating": 3.5
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['current_salary', 'career_field', 'experience_level']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create search criteria
        criteria = SearchCriteria(
            current_salary=int(data['current_salary']),
            target_salary_increase=float(data.get('target_salary_increase', 0.25)),
            career_field=CareerField(data['career_field']),
            experience_level=ExperienceLevel(data['experience_level']),
            preferred_msas=data.get('preferred_msas', []),
            remote_ok=bool(data.get('remote_ok', True)),
            max_commute_time=data.get('max_commute_time'),
            must_have_benefits=data.get('must_have_benefits', []),
            company_size_preference=data.get('company_size_preference'),
            industry_preference=data.get('industry_preference'),
            equity_required=bool(data.get('equity_required', False)),
            min_company_rating=float(data.get('min_company_rating', 3.0))
        )
        
        # Perform search
        matcher = IncomeBoostJobMatcher()
        
        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        jobs = loop.run_until_complete(matcher.salary_focused_search(criteria))
        loop.close()
        
        # Convert jobs to JSON-serializable format
        job_data = []
        for job in jobs:
            job_data.append({
                'job_id': job.job_id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'msa': job.msa,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'salary_median': job.salary_median,
                'salary_increase_potential': job.salary_increase_potential,
                'remote_friendly': job.remote_friendly,
                'job_board': job.job_board.value,
                'url': job.url,
                'description': job.description,
                'requirements': job.requirements,
                'benefits': job.benefits,
                'diversity_score': job.diversity_score,
                'growth_score': job.growth_score,
                'culture_score': job.culture_score,
                'overall_score': job.overall_score,
                'field': job.field.value,
                'experience_level': job.experience_level.value,
                'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
                'company_size': job.company_size,
                'company_industry': job.company_industry,
                'equity_offered': job.equity_offered,
                'bonus_potential': job.bonus_potential,
                'career_advancement_score': job.career_advancement_score,
                'work_life_balance_score': job.work_life_balance_score
            })
        
        return jsonify({
            'success': True,
            'jobs': job_data,
            'total_count': len(job_data),
            'search_criteria': {
                'current_salary': criteria.current_salary,
                'target_salary_increase': criteria.target_salary_increase,
                'career_field': criteria.career_field.value,
                'experience_level': criteria.experience_level.value,
                'preferred_msas': criteria.preferred_msas,
                'remote_ok': criteria.remote_ok
            }
        })
        
    except Exception as e:
        logger.error(f"Error in job search: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_matching_api.route('/job-matching/company/<company_name>', methods=['GET'])
@cross_origin()
def get_company_profile(company_name):
    """
    Get company profile with diversity and growth metrics
    
    Path parameters:
    - company_name: Name of the company
    """
    try:
        matcher = IncomeBoostJobMatcher()
        profile = matcher.company_quality_assessment(company_name)
        
        return jsonify({
            'success': True,
            'company_profile': {
                'company_id': profile.company_id,
                'name': profile.name,
                'industry': profile.industry,
                'size': profile.size,
                'diversity_score': profile.diversity_score,
                'growth_score': profile.growth_score,
                'culture_score': profile.culture_score,
                'benefits_score': profile.benefits_score,
                'leadership_diversity': profile.leadership_diversity,
                'employee_retention': profile.employee_retention,
                'glassdoor_rating': profile.glassdoor_rating,
                'indeed_rating': profile.indeed_rating,
                'remote_friendly': profile.remote_friendly,
                'headquarters': profile.headquarters,
                'founded_year': profile.founded_year,
                'funding_stage': profile.funding_stage,
                'revenue': profile.revenue
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting company profile: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_matching_api.route('/job-matching/field-strategies/<field>', methods=['GET'])
@cross_origin()
def get_field_strategies(field):
    """
    Get field-specific search strategies
    
    Path parameters:
    - field: Career field (technology, finance, healthcare, etc.)
    """
    try:
        matcher = IncomeBoostJobMatcher()
        
        try:
            career_field = CareerField(field)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid career field: {field}'
            }), 400
        
        strategies = matcher.field_specific_strategies(career_field)
        
        return jsonify({
            'success': True,
            'field': field,
            'strategies': strategies
        })
        
    except Exception as e:
        logger.error(f"Error getting field strategies: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_matching_api.route('/job-matching/msa-targeting', methods=['POST'])
@cross_origin()
def apply_msa_targeting():
    """
    Apply MSA targeting to job results
    
    Request body:
    {
        "jobs": [...],  # Array of job objects
        "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"]
    }
    """
    try:
        data = request.get_json()
        
        if 'jobs' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing jobs array'
            }), 400
        
        # Convert job data back to JobOpportunity objects
        jobs = []
        for job_data in data['jobs']:
            job = JobOpportunity(
                job_id=job_data['job_id'],
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'],
                msa=job_data.get('msa', ''),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_median=job_data.get('salary_median'),
                salary_increase_potential=job_data.get('salary_increase_potential', 0.0),
                remote_friendly=job_data.get('remote_friendly', False),
                job_board=JobBoard(job_data.get('job_board', 'indeed')),
                url=job_data.get('url', ''),
                description=job_data.get('description', ''),
                requirements=job_data.get('requirements', []),
                benefits=job_data.get('benefits', []),
                diversity_score=job_data.get('diversity_score', 0.0),
                growth_score=job_data.get('growth_score', 0.0),
                culture_score=job_data.get('culture_score', 0.0),
                overall_score=job_data.get('overall_score', 0.0),
                field=CareerField(job_data.get('field', 'technology')),
                experience_level=ExperienceLevel(job_data.get('experience_level', 'mid')),
                posted_date=datetime.fromisoformat(job_data['posted_date']) if job_data.get('posted_date') else None,
                application_deadline=datetime.fromisoformat(job_data['application_deadline']) if job_data.get('application_deadline') else None,
                company_size=job_data.get('company_size'),
                company_industry=job_data.get('company_industry'),
                equity_offered=job_data.get('equity_offered', False),
                bonus_potential=job_data.get('bonus_potential'),
                career_advancement_score=job_data.get('career_advancement_score', 0.0),
                work_life_balance_score=job_data.get('work_life_balance_score', 0.0)
            )
            jobs.append(job)
        
        # Apply MSA targeting
        matcher = IncomeBoostJobMatcher()
        preferred_msas = data.get('preferred_msas', [])
        targeted_jobs = matcher.msa_targeting(jobs, preferred_msas)
        
        # Convert back to JSON-serializable format
        job_data = []
        for job in targeted_jobs:
            job_data.append({
                'job_id': job.job_id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'msa': job.msa,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'salary_median': job.salary_median,
                'salary_increase_potential': job.salary_increase_potential,
                'remote_friendly': job.remote_friendly,
                'job_board': job.job_board.value,
                'url': job.url,
                'description': job.description,
                'requirements': job.requirements,
                'benefits': job.benefits,
                'diversity_score': job.diversity_score,
                'growth_score': job.growth_score,
                'culture_score': job.culture_score,
                'overall_score': job.overall_score,
                'field': job.field.value,
                'experience_level': job.experience_level.value,
                'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
                'company_size': job.company_size,
                'company_industry': job.company_industry,
                'equity_offered': job.equity_offered,
                'bonus_potential': job.bonus_potential,
                'career_advancement_score': job.career_advancement_score,
                'work_life_balance_score': job.work_life_balance_score
            })
        
        return jsonify({
            'success': True,
            'jobs': job_data,
            'total_count': len(job_data)
        })
        
    except Exception as e:
        logger.error(f"Error applying MSA targeting: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_matching_api.route('/job-matching/remote-detection', methods=['POST'])
@cross_origin()
def detect_remote_opportunities():
    """
    Detect remote-friendly positions in job results
    
    Request body:
    {
        "jobs": [...]  # Array of job objects
    }
    """
    try:
        data = request.get_json()
        
        if 'jobs' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing jobs array'
            }), 400
        
        # Convert job data back to JobOpportunity objects
        jobs = []
        for job_data in data['jobs']:
            job = JobOpportunity(
                job_id=job_data['job_id'],
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'],
                msa=job_data.get('msa', ''),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_median=job_data.get('salary_median'),
                salary_increase_potential=job_data.get('salary_increase_potential', 0.0),
                remote_friendly=job_data.get('remote_friendly', False),
                job_board=JobBoard(job_data.get('job_board', 'indeed')),
                url=job_data.get('url', ''),
                description=job_data.get('description', ''),
                requirements=job_data.get('requirements', []),
                benefits=job_data.get('benefits', []),
                diversity_score=job_data.get('diversity_score', 0.0),
                growth_score=job_data.get('growth_score', 0.0),
                culture_score=job_data.get('culture_score', 0.0),
                overall_score=job_data.get('overall_score', 0.0),
                field=CareerField(job_data.get('field', 'technology')),
                experience_level=ExperienceLevel(job_data.get('experience_level', 'mid')),
                posted_date=datetime.fromisoformat(job_data['posted_date']) if job_data.get('posted_date') else None,
                application_deadline=datetime.fromisoformat(job_data['application_deadline']) if job_data.get('application_deadline') else None,
                company_size=job_data.get('company_size'),
                company_industry=job_data.get('company_industry'),
                equity_offered=job_data.get('equity_offered', False),
                bonus_potential=job_data.get('bonus_potential'),
                career_advancement_score=job_data.get('career_advancement_score', 0.0),
                work_life_balance_score=job_data.get('work_life_balance_score', 0.0)
            )
            jobs.append(job)
        
        # Apply remote detection
        matcher = IncomeBoostJobMatcher()
        remote_jobs = matcher.remote_opportunity_detection(jobs)
        
        # Convert back to JSON-serializable format
        job_data = []
        for job in remote_jobs:
            job_data.append({
                'job_id': job.job_id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'msa': job.msa,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'salary_median': job.salary_median,
                'salary_increase_potential': job.salary_increase_potential,
                'remote_friendly': job.remote_friendly,
                'job_board': job.job_board.value,
                'url': job.url,
                'description': job.description,
                'requirements': job.requirements,
                'benefits': job.benefits,
                'diversity_score': job.diversity_score,
                'growth_score': job.growth_score,
                'culture_score': job.culture_score,
                'overall_score': job.overall_score,
                'field': job.field.value,
                'experience_level': job.experience_level.value,
                'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
                'company_size': job.company_size,
                'company_industry': job.company_industry,
                'equity_offered': job.equity_offered,
                'bonus_potential': job.bonus_potential,
                'career_advancement_score': job.career_advancement_score,
                'work_life_balance_score': job.work_life_balance_score
            })
        
        return jsonify({
            'success': True,
            'jobs': job_data,
            'total_count': len(job_data),
            'remote_count': sum(1 for job in remote_jobs if job.remote_friendly)
        })
        
    except Exception as e:
        logger.error(f"Error detecting remote opportunities: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_matching_api.route('/job-matching/analytics', methods=['GET'])
@cross_origin()
def get_job_matching_analytics():
    """
    Get analytics and insights from job matching data
    """
    try:
        matcher = IncomeBoostJobMatcher()
        
        # Get analytics from database
        import sqlite3
        conn = sqlite3.connect(matcher.db_path)
        cursor = conn.cursor()
        
        # Get job count by field
        cursor.execute('''
            SELECT field, COUNT(*) as count 
            FROM job_opportunities 
            GROUP BY field 
            ORDER BY count DESC
        ''')
        field_counts = dict(cursor.fetchall())
        
        # Get average scores by field
        cursor.execute('''
            SELECT field, AVG(overall_score) as avg_score 
            FROM job_opportunities 
            GROUP BY field 
            ORDER BY avg_score DESC
        ''')
        field_scores = dict(cursor.fetchall())
        
        # Get top companies by job count
        cursor.execute('''
            SELECT company, COUNT(*) as count 
            FROM job_opportunities 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_companies = dict(cursor.fetchall())
        
        # Get remote job percentage
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN remote_friendly = 1 THEN 1 ELSE 0 END) as remote
            FROM job_opportunities
        ''')
        total, remote = cursor.fetchone()
        remote_percentage = (remote / total * 100) if total > 0 else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'analytics': {
                'field_distribution': field_counts,
                'field_average_scores': field_scores,
                'top_companies': top_companies,
                'remote_job_percentage': round(remote_percentage, 2),
                'total_jobs': total
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_matching_api.route('/job-matching/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for job matching service
    """
    try:
        matcher = IncomeBoostJobMatcher()
        
        # Check database connection
        import sqlite3
        conn = sqlite3.connect(matcher.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM job_opportunities')
        job_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'job_count': job_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500
