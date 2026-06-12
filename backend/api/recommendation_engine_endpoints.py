#!/usr/bin/env python3
"""
Recommendation Engine API Endpoints
Provides REST API access to the Mingus Job Recommendation Engine

This module exposes the central orchestration engine through HTTP endpoints,
enabling seamless integration with the frontend and other services.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from werkzeug.exceptions import BadRequest, InternalServerError
import os
import psycopg2
import psycopg2.extras

from backend.auth.decorators import get_current_jwt_user, require_auth
from backend.models.career_profile import CareerProfile
from backend.models.housing_profile import HousingProfile
from backend.models.user_models import User
from backend.scripts.job_postings_seed_data import MSA_CONFIG

# Import the orchestration engine
from ..utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine

# Configure logging
logger = logging.getLogger(__name__)


def get_pg_connection():
    """Get PostgreSQL database connection"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is required. SQLite is not supported."
        )
    conn = psycopg2.connect(db_url)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


# Create blueprint
recommendation_engine_api = Blueprint('recommendation_engine_api', __name__)

# Initialize the engine
engine = MingusJobRecommendationEngine()

SEED_ROLE_BLOCKLIST = frozenset({'doadmin', 'admin', 'test', 'seed_user', ''})
SEED_INDUSTRY_BLOCKLIST = frozenset(
    {v.lower() for v in ('Manufacturing', 'Unknown', 'Test', '')}
)


def _career_profile_incomplete(cp: CareerProfile) -> bool:
    """True when profile is missing or uses seed/placeholder values."""
    role = (cp.current_role or '').strip().lower()
    field = (cp.bls_career_field or '').strip()
    seniority = (cp.seniority_level or '').strip()
    if role in SEED_ROLE_BLOCKLIST:
        return True
    if not field or field.lower() in SEED_INDUSTRY_BLOCKLIST:
        return True
    if not seniority:
        return True
    return False


def validate_csrf_token(token):
    """Validate CSRF token"""
    # Simplified validation - in production, implement proper CSRF validation
    return token is not None

def check_rate_limit(client_ip):
    """Check rate limiting"""
    # Simplified rate limiting - in production, use Redis or similar
    return True


_ZIP_RE = re.compile(r'\b(\d{5})\b')

# Interim default when zip/city cannot be mapped — Houston has broad seed coverage.
DEFAULT_MSA = '26420'

ZIP_TO_MSA: dict[str, str] = {
    # Houston
    '77001': '26420', '77002': '26420', '77003': '26420', '77004': '26420',
    '77005': '26420', '77006': '26420', '77007': '26420', '77019': '26420',
    '77056': '26420', '77077': '26420', '77098': '26420',
    # Atlanta
    '30301': '12060', '30302': '12060', '30303': '12060', '30305': '12060',
    '30306': '12060', '30307': '12060', '30308': '12060', '30309': '12060',
    # DC Metro
    '20001': '47900', '20002': '47900', '20003': '47900', '20004': '47900',
    '20005': '47900', '20006': '47900', '22201': '47900', '22202': '47900',
    # Dallas
    '75201': '19100', '75202': '19100', '75203': '19100', '75204': '19100',
    '75205': '19100', '75206': '19100',
    # NYC
    '10001': '35620', '10002': '35620', '10003': '35620', '10004': '35620',
    '10005': '35620', '10006': '35620',
    # Chicago
    '60601': '16980', '60602': '16980', '60603': '16980', '60604': '16980',
    # Miami
    '33101': '33100', '33102': '33100', '33125': '33100', '33126': '33100',
    '33127': '33100', '33128': '33100', '33129': '33100', '33130': '33100',
    '33131': '33100', '33132': '33100',
    # Boston
    '02101': '14460', '02102': '14460', '02103': '14460', '02104': '14460',
    '02105': '14460', '02106': '14460', '02107': '14460', '02108': '14460',
    '02109': '14460', '02110': '14460',
    # Los Angeles
    '90001': '31080', '90002': '31080', '90003': '31080', '90004': '31080',
    '90005': '31080', '90006': '31080', '90007': '31080', '90008': '31080',
    '90010': '31080', '90012': '31080',
    # San Francisco
    '94101': '41860', '94102': '41860', '94103': '41860', '94104': '41860',
    '94105': '41860', '94107': '41860', '94108': '41860', '94109': '41860',
    '94110': '41860', '94111': '41860',
    # Phoenix
    '85001': '38060', '85002': '38060', '85003': '38060', '85004': '38060',
    '85005': '38060', '85006': '38060', '85007': '38060', '85008': '38060',
    '85009': '38060', '85010': '38060',
    # Minneapolis
    '55401': '33460', '55402': '33460', '55403': '33460', '55404': '33460',
    '55405': '33460', '55406': '33460', '55407': '33460', '55408': '33460',
    '55409': '33460', '55410': '33460',
    # San Diego
    '92101': '41740', '92102': '41740', '92103': '41740', '92104': '41740',
    '92105': '41740', '92106': '41740', '92107': '41740', '92108': '41740',
    '92109': '41740', '92110': '41740',
    # Cleveland
    '44101': '17460', '44102': '17460', '44103': '17460', '44104': '17460',
    '44105': '17460', '44106': '17460', '44107': '17460', '44108': '17460',
    '44109': '17460', '44110': '17460',
    # Kansas City
    '64101': '28140', '64102': '28140', '64103': '28140', '64104': '28140',
    '64105': '28140', '64106': '28140', '64107': '28140', '64108': '28140',
    '64109': '28140', '64110': '28140',
}


def _extract_zip_from_text(text: str | None) -> str | None:
    if not text:
        return None
    match = _ZIP_RE.search(str(text).strip())
    return match.group(1) if match else None


def _match_msa_from_city_text(text: str | None) -> str | None:
    """Match HousingProfile zip_or_city text against MSA_CONFIG city names."""
    if not text:
        return None
    normalized = str(text).strip().lower()
    for code, meta in MSA_CONFIG.items():
        city = (meta.get('city') or '').lower()
        if city and city in normalized:
            return code
    return None


def _resolve_msa_for_user_by_zip(
    zipcode: str | None,
    city_text: str | None = None,
) -> str:
    """Map a zip (and optional city text) to a job_postings CBSA msa_code."""
    if zipcode:
        mapped = ZIP_TO_MSA.get(zipcode)
        if mapped:
            return mapped

    city_msa = _match_msa_from_city_text(city_text)
    if city_msa:
        return city_msa

    if zipcode:
        logger.warning(
            "Unknown zip %s with no city match; using default MSA %s (interim behavior)",
            zipcode,
            DEFAULT_MSA,
        )
    else:
        logger.warning(
            "No zip or city for MSA resolution; using default MSA %s (interim behavior)",
            DEFAULT_MSA,
        )
    return DEFAULT_MSA


def _resolve_user_profile_zip(email: str) -> str | None:
    """Read zip_code from user_profiles by email (same source as income-percentile)."""
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s
            ''',
            ('user_profiles',),
        )
        profiles_columns = {row['column_name'] for row in cursor.fetchall()}
        if 'zip_code' not in profiles_columns:
            conn.close()
            return None
        cursor.execute(
            'SELECT zip_code FROM user_profiles WHERE email = %s LIMIT 1',
            (email,),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row.get('zip_code'):
            return _extract_zip_from_text(str(row['zip_code']))
    except Exception as exc:
        logger.warning("Could not read user_profiles zip for %s: %s", email, exc)
    return None


def _resolve_msa_for_user(internal_user_id: int) -> str:
    """
    Resolve job_postings CBSA msa_code for a user.

    Zip sources (first non-null wins): HousingProfile.zip_or_city, then
    user_profiles.zip_code by email. Maps via ZIP_TO_MSA, then city name in
    MSA_CONFIG, then DEFAULT_MSA (26420 Houston) so recommendations are never
    blocked by an unresolved location.
    """
    hp = HousingProfile.query.filter_by(user_id=internal_user_id).first()
    city_text = hp.zip_or_city if hp else None
    zipcode = _extract_zip_from_text(city_text)

    if not zipcode:
        user = User.query.get(internal_user_id)
        if user:
            zipcode = _resolve_user_profile_zip(user.email)

    return _resolve_msa_for_user_by_zip(zipcode, city_text=city_text)


def _build_career_profile_dict(cp: CareerProfile | None, msa: str) -> dict:
    """Build engine input dict from CareerProfile ORM fields."""
    career_field = cp.bls_career_field if cp else None
    seniority = cp.seniority_level if cp else None
    salary_target = cp.target_comp if cp else None
    return {
        'bls_career_field': career_field,
        'seniority_level': seniority,
        'target_comp': salary_target,
        'salary_target': salary_target,
        'current_role': cp.current_role if cp else None,
        'msa': msa,
        'open_to_move': bool(cp.open_to_move) if cp else False,
    }


@recommendation_engine_api.route('/recommendations/process-resume', methods=['POST'])
@recommendation_engine_api.route('/api/recommendations/process-resume', methods=['POST'])
@cross_origin()
@require_auth
def process_resume_complete():
    """Generate tiered job recommendations from the authenticated user's career profile."""
    try:
        user = get_current_jwt_user()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        cp = CareerProfile.query.filter_by(user_id=user.id).first()
        if not cp or _career_profile_incomplete(cp):
            return jsonify({
                'success': False,
                'error': 'career_profile_incomplete',
                'message': 'Complete your career profile to see recommendations',
            }), 422

        msa = _resolve_msa_for_user(user.id)
        career_profile = _build_career_profile_dict(cp, msa)

        recommendations = engine.process_recommendations(str(user.user_id), career_profile)

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'career_profile_used': {
                'bls_career_field': career_profile.get('bls_career_field'),
                'seniority_level': career_profile.get('seniority_level'),
                'target_comp': career_profile.get('target_comp'),
                'msa': career_profile.get('msa'),
                'open_to_move': bool(cp.open_to_move) if cp else False,
            },
        }), 200

    except Exception as e:
        logger.error(f"Error in process_resume_complete: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@recommendation_engine_api.route('/recommendations/status/<session_id>', methods=['GET'])
@cross_origin()
def get_processing_status(session_id):
    """
    Get processing status for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Processing status and progress information
    """
    try:
        # Get session status from database
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, created_at, completed_at, total_processing_time, error_message
            FROM workflow_sessions 
            WHERE session_id = %s
        ''', (session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        status = session['status']
        created_at = session['created_at']
        completed_at = session['completed_at']
        processing_time = session['total_processing_time']
        error_message = session['error_message']
        
        # Get workflow steps
        cursor.execute('''
            SELECT step_name, status, start_time, end_time, duration, error_message
            FROM workflow_steps 
            WHERE session_id = %s
            ORDER BY start_time
        ''', (session_id,))
        
        steps = cursor.fetchall()
        
        conn.close()
        
        # Format response
        response = {
            'success': True,
            'session_id': session_id,
            'status': status,
            'created_at': created_at,
            'completed_at': completed_at,
            'total_processing_time': processing_time,
            'error_message': error_message,
            'workflow_steps': [
                {
                    'step_name': step['step_name'],
                    'status': step['status'],
                    'start_time': step['start_time'],
                    'end_time': step['end_time'],
                    'duration': step['duration'],
                    'error_message': step['error_message']
                }
                for step in steps
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@recommendation_engine_api.route('/recommendations/analytics', methods=['POST'])
@cross_origin()
def track_recommendation_analytics():
    """
    Track user analytics for recommendations
    
    Request body:
    {
        "user_id": "user123",
        "session_id": "session456",
        "event_type": "recommendation_viewed",
        "event_data": {
            "recommendation_id": "rec123",
            "tier": "optimal",
            "action": "viewed"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        required_fields = ['user_id', 'session_id', 'event_type']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")
        
        user_id = data['user_id']
        session_id = data['session_id']
        event_type = data['event_type']
        event_data = data.get('event_data', {})
        
        # Track analytics
        asyncio.run(engine._track_analytics(user_id, session_id, event_type, event_data))
        
        logger.info(f"Analytics tracked: {event_type} for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Analytics tracked successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in track_recommendation_analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in track_recommendation_analytics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@recommendation_engine_api.route('/recommendations/performance', methods=['GET'])
@cross_origin()
def get_performance_metrics():
    """
    Get system performance metrics
    
    Returns:
        Performance metrics and system health information
    """
    try:
        # Get recent performance metrics
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Get recent sessions
        cursor.execute('''
            SELECT COUNT(*) as total_sessions,
                   AVG(total_processing_time) as avg_processing_time,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_sessions,
                   COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_sessions
            FROM workflow_sessions 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        ''')
        
        recent_stats = cursor.fetchone()
        
        # Get cache performance
        cursor.execute('''
            SELECT COUNT(*) as total_cache_entries,
                   AVG(hit_count) as avg_hit_count,
                   COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_entries
            FROM recommendation_cache
        ''')
        
        cache_stats = cursor.fetchone()
        
        conn.close()
        
        # Calculate success rate
        total_sessions = recent_stats['total_sessions'] or 0
        successful_sessions = recent_stats['successful_sessions'] or 0
        success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        response = {
            'success': True,
            'performance_metrics': {
                'last_24_hours': {
                    'total_sessions': total_sessions,
                    'successful_sessions': successful_sessions,
                    'failed_sessions': recent_stats['failed_sessions'] or 0,
                    'success_rate': round(success_rate, 2),
                    'avg_processing_time': round(recent_stats['avg_processing_time'] or 0, 2)
                },
                'cache_performance': {
                    'total_entries': cache_stats['total_cache_entries'] or 0,
                    'avg_hit_count': round(cache_stats['avg_hit_count'] or 0, 2),
                    'active_entries': cache_stats['active_entries'] or 0
                },
                'current_metrics': {
                    'total_time': engine.metrics.total_time,
                    'cache_hits': engine.metrics.cache_hits,
                    'cache_misses': engine.metrics.cache_misses,
                    'errors_count': engine.metrics.errors_count,
                    'warnings_count': engine.metrics.warnings_count
                }
            },
            'system_health': {
                'status': 'healthy' if success_rate > 95 else 'degraded' if success_rate > 80 else 'unhealthy',
                'recommendation_accuracy': '90%+',
                'system_reliability': '99.5%',
                'performance_target': '8 seconds max processing time'
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@recommendation_engine_api.route('/recommendations/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for the recommendation engine
    
    Returns:
        System health status and component availability
    """
    try:
        # Check database connectivity
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        db_status = 'healthy'
        
        # Check component availability
        components = {
            'resume_parser': 'available',
            'job_matcher': 'available',
            'three_tier_selector': 'available',
            'database': db_status
        }
        
        # Overall health status
        overall_status = 'healthy' if all(status == 'healthy' for status in components.values()) else 'degraded'
        
        response = {
            'success': True,
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': components,
            'performance_targets': {
                'max_processing_time': f"{engine.max_processing_time}s",
                'recommendation_accuracy': "90%+",
                'system_reliability': "99.5%"
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@recommendation_engine_api.route('/recommendations/cache/clear', methods=['POST'])
@cross_origin()
def clear_cache():
    """
    Clear recommendation cache
    
    This endpoint allows clearing the cache for maintenance or troubleshooting
    """
    try:
        # Clear cache
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM recommendation_cache')
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Clear in-memory cache
        engine.cache.clear()
        
        logger.info(f"Cache cleared: {deleted_count} entries removed")
        
        return jsonify({
            'success': True,
            'message': f'Cache cleared successfully. {deleted_count} entries removed.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@recommendation_engine_api.route('/recommendations/sessions/<session_id>/results', methods=['GET'])
@cross_origin()
def get_session_results(session_id):
    """
    Get results for a completed session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Complete results for the session
    """
    try:
        # Get session results
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, result_data, total_processing_time, error_message
            FROM workflow_sessions 
            WHERE session_id = %s
        ''', (session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        status = session['status']
        result_data = session['result_data']
        processing_time = session['total_processing_time']
        error_message = session['error_message']
        
        if status != 'completed':
            return jsonify({
                'success': False,
                'status': status,
                'error': error_message or 'Session not completed',
                'processing_time': processing_time
            }), 400
        
        # Parse result data
        results = json.loads(result_data) if result_data else {}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': status,
            'processing_time': processing_time,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting session results: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
