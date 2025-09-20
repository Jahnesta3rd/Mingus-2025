#!/usr/bin/env python3
"""
Referral-Gated Job Recommendation API Endpoints
Provides referral-protected access to job recommendation features
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict
from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for, flash
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, Forbidden, NotFound
import asyncio

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.referral_models import ReferralSystem
from forms.referral_forms import (
    ReferralInviteForm, LocationPreferencesForm, CareerPreferencesForm,
    EnhancedResumeUploadForm, ApplicationTrackingForm, FeatureUnlockForm,
    ZipcodeValidationForm, JobRecommendationPreferencesForm
)
from backend.utils.location_utils import LocationService
from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
referral_gated_api = Blueprint('referral_gated_api', __name__)

# Initialize services
referral_system = ReferralSystem()
location_service = LocationService()
job_engine = MingusJobRecommendationEngine()

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'uploads', 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_referral_unlock(f):
    """Decorator to require referral unlock for premium features"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required',
                'redirect_to_teaser': True
            }), 401
        
        # Check feature access
        access_check = referral_system.check_feature_access(user_id, 'job_recommendations')
        if not access_check['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to check feature access',
                'redirect_to_teaser': True
            }), 500
        
        if not access_check['unlocked']:
            # Track unlock attempt
            referral_system.track_unlock_attempt(
                user_id, 'job_recommendations', 'access_attempt',
                request.remote_addr, request.headers.get('User-Agent')
            )
            
            return jsonify({
                'success': False,
                'error': 'Feature access required',
                'redirect_to_teaser': True,
                'referral_count': access_check.get('referral_count', 0),
                'referrals_needed': access_check.get('referrals_needed', 3)
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def feature_access_check(user_id: str, feature_name: str = 'job_recommendations') -> Dict:
    """Check if user has access to a feature"""
    return referral_system.check_feature_access(user_id, feature_name)

def redirect_to_teaser(user_id: str) -> Dict:
    """Generate teaser page data for locked users"""
    progress = referral_system.get_referral_progress(user_id)
    if not progress['success']:
        return {'success': False, 'error': 'Failed to get referral progress'}
    
    return {
        'success': True,
        'teaser_data': {
            'feature_name': 'Job Recommendations',
            'description': 'Get personalized job recommendations based on your resume and career goals',
            'benefits': [
                'AI-powered job matching',
                'Salary increase analysis',
                'Location-based recommendations',
                'Company culture insights',
                'Application tracking'
            ],
            'referral_progress': progress['progress'],
            'unlock_requirements': {
                'referrals_needed': 3,
                'current_referrals': progress['progress']['successful_referrals']
            }
        }
    }

# ============================================================================
# PUBLIC ACCESS ROUTES
# ============================================================================

@referral_gated_api.route('/career-preview', methods=['GET'])
@cross_origin()
def career_preview():
    """Compelling preview of job recommendation feature"""
    try:
        return jsonify({
            'success': True,
            'preview': {
                'title': 'Unlock Your Career Potential',
                'subtitle': 'Get AI-powered job recommendations that match your skills and goals',
                'features': [
                    {
                        'icon': '🎯',
                        'title': 'Smart Matching',
                        'description': 'AI analyzes your resume to find perfect job matches'
                    },
                    {
                        'icon': '💰',
                        'title': 'Salary Insights',
                        'description': 'Discover opportunities for 20-50% salary increases'
                    },
                    {
                        'icon': '📍',
                        'title': 'Location Intelligence',
                        'description': 'Find jobs in your preferred locations with commute analysis'
                    },
                    {
                        'icon': '🏢',
                        'title': 'Company Insights',
                        'description': 'Learn about company culture, benefits, and growth opportunities'
                    }
                ],
                'success_stories': [
                    {
                        'name': 'Sarah M.',
                        'role': 'Software Engineer',
                        'increase': '35%',
                        'quote': 'Found my dream job with a 35% salary increase!'
                    },
                    {
                        'name': 'Michael R.',
                        'role': 'Marketing Manager',
                        'increase': '28%',
                        'quote': 'The location recommendations saved me hours of research.'
                    }
                ],
                'cta': {
                    'primary': 'Start Referring Friends',
                    'secondary': 'Learn More'
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error in career preview: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load preview'
        }), 500

@referral_gated_api.route('/refer-friend', methods=['POST'])
@cross_origin()
def refer_friend():
    """Send referral invitations"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['user_id', 'friend_email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        friend_email = data['friend_email']
        friend_name = data.get('friend_name', '')
        personal_message = data.get('personal_message', '')
        
        # Get user's referral code
        conn = referral_system.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        referral_code = user_data[0]
        
        # Create referral record
        cursor.execute('''
            INSERT INTO referrals (referrer_user_id, referred_email, referral_code)
            VALUES (?, ?, ?)
        ''', (user_id, friend_email, referral_code))
        
        conn.commit()
        conn.close()
        
        # In production, send actual email here
        logger.info(f"Referral invitation sent: {user_id} -> {friend_email}")
        
        return jsonify({
            'success': True,
            'message': 'Referral invitation sent successfully',
            'referral_code': referral_code
        })
        
    except Exception as e:
        logger.error(f"Error sending referral: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send referral invitation'
        }), 500

@referral_gated_api.route('/referral-status/<referral_code>', methods=['GET'])
@cross_origin()
def track_referral_status(referral_code):
    """Track individual referral success"""
    try:
        import sqlite3
        conn = sqlite3.connect(referral_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.first_name, u.last_name
            FROM referrals r
            JOIN users u ON r.referrer_user_id = u.user_id
            WHERE r.referral_code = ?
        ''', (referral_code,))
        
        referral = cursor.fetchone()
        
        if not referral:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Referral code not found'
            }), 404
        
        conn.close()
        
        return jsonify({
            'success': True,
            'referral': {
                'code': referral[3],
                'referrer_name': f"{referral[7]} {referral[8]}",
                'referred_email': referral[2],
                'status': referral[4],
                'created_at': referral[5],
                'completed_at': referral[6]
            }
        })
        
    except Exception as e:
        logger.error(f"Error tracking referral status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to track referral status'
        }), 500

# ============================================================================
# REFERRAL-GATED ROUTES
# ============================================================================

@referral_gated_api.route('/career-advancement', methods=['GET'])
@cross_origin()
def career_advancement_teaser():
    """Feature teaser page with unlock requirements"""
    try:
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 401
        
        teaser_data = redirect_to_teaser(user_id)
        if not teaser_data['success']:
            return jsonify(teaser_data), 500
        
        return jsonify({
            'success': True,
            'teaser': teaser_data['teaser_data']
        })
        
    except Exception as e:
        logger.error(f"Error in career advancement teaser: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load teaser'
        }), 500

@referral_gated_api.route('/api/feature-access/job-recommendations', methods=['GET'])
@cross_origin()
def check_feature_access():
    """Check if user has unlocked feature"""
    try:
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 401
        
        access_check = feature_access_check(user_id)
        return jsonify(access_check)
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check feature access'
        }), 500

@referral_gated_api.route('/upload-resume', methods=['POST'])
@cross_origin()
@require_referral_unlock
def upload_resume():
    """Secure resume upload (REFERRAL-GATED)"""
    try:
        user_id = request.headers.get('X-User-ID')
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only PDF, DOC, and DOCX files are allowed'
            }), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'File too large. Maximum size is 10MB'
            }), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{user_id}_{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Record upload in database
        result = referral_system.save_resume_upload(
            user_id, filename, file_path, file_size, 
            filename.rsplit('.', 1)[1].lower()
        )
        
        if not result['success']:
            # Clean up file if database save failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'message': 'Resume uploaded successfully',
            'filename': filename,
            'file_size': file_size
        })
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload resume'
        }), 500

@referral_gated_api.route('/set-location-preferences', methods=['POST'])
@cross_origin()
@require_referral_unlock
def set_location_preferences():
    """Location preferences (REFERRAL-GATED)"""
    try:
        user_id = request.headers.get('X-User-ID')
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate ZIP code
        zipcode = data.get('zipcode', '').strip()
        if not zipcode:
            return jsonify({
                'success': False,
                'error': 'ZIP code is required'
            }), 400
        
        # Geocode location
        location_result = location_service.validate_and_geocode(zipcode)
        if not location_result['success']:
            return jsonify(location_result), 400
        
        location_data = location_result['location']
        
        # Save preferences
        result = referral_system.save_location_preferences(
            user_id=user_id,
            zipcode=zipcode,
            city=location_data['city'],
            state=location_data['state'],
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            search_radius=data.get('search_radius', 25),
            commute_preference=data.get('commute_preference', 'flexible'),
            remote_ok=data.get('remote_ok', True)
        )
        
        if not result['success']:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'message': 'Location preferences saved successfully',
            'location': location_data
        })
        
    except Exception as e:
        logger.error(f"Error setting location preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save location preferences'
        }), 500

@referral_gated_api.route('/process-recommendations', methods=['POST'])
@cross_origin()
@require_referral_unlock
def process_recommendations():
    """Trigger recommendation engine (REFERRAL-GATED)"""
    try:
        user_id = request.headers.get('X-User-ID')
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get user's location preferences
        import sqlite3
        conn = sqlite3.connect(referral_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT zipcode, search_radius, commute_preference, remote_ok
            FROM location_preferences WHERE user_id = ?
        ''', (user_id,))
        
        location_prefs = cursor.fetchone()
        conn.close()
        
        if not location_prefs:
            return jsonify({
                'success': False,
                'error': 'Location preferences required. Please set your location first.'
            }), 400
        
        # Prepare search criteria
        search_criteria = {
            'current_salary': data.get('current_salary', 75000),
            'target_salary_increase': data.get('target_salary_increase', 0.25),
            'career_field': data.get('career_field', 'technology'),
            'experience_level': data.get('experience_level', 'mid'),
            'zipcode': location_prefs[0],
            'search_radius': location_prefs[1],
            'remote_ok': bool(location_prefs[3]),
            'commute_preference': location_prefs[2]
        }
        
        # Process recommendations asynchronously
        session_id = f"rec_{user_id}_{int(datetime.now().timestamp())}"
        
        # In production, use a proper task queue like Celery
        # For now, process synchronously
        try:
            recommendations = job_engine.process_recommendations(search_criteria)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'recommendations': recommendations,
                'total_count': len(recommendations),
                'search_criteria': search_criteria
            })
            
        except Exception as e:
            logger.error(f"Error processing recommendations: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to process recommendations'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in process recommendations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process recommendations'
        }), 500

@referral_gated_api.route('/referral-progress', methods=['GET'])
@cross_origin()
def get_referral_progress():
    """Show user's progress toward unlock (0/3, 1/3, 2/3, 3/3)"""
    try:
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required'
            }), 401
        
        progress = referral_system.get_referral_progress(user_id)
        return jsonify(progress)
        
    except Exception as e:
        logger.error(f"Error getting referral progress: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get referral progress'
        }), 500

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@referral_gated_api.route('/validate-zipcode', methods=['POST'])
@cross_origin()
def validate_zipcode():
    """Validate ZIP code and return location data"""
    try:
        data = request.get_json()
        
        if not data or 'zipcode' not in data:
            return jsonify({
                'success': False,
                'error': 'ZIP code required'
            }), 400
        
        zipcode = data['zipcode'].strip()
        result = location_service.validate_and_geocode(zipcode)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating ZIP code: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate ZIP code'
        }), 500

@referral_gated_api.route('/location-recommendations', methods=['POST'])
@cross_origin()
@require_referral_unlock
def get_location_recommendations():
    """Get location-based job recommendations"""
    try:
        user_id = request.headers.get('X-User-ID')
        data = request.get_json()
        
        if not data or 'zipcode' not in data:
            return jsonify({
                'success': False,
                'error': 'ZIP code required'
            }), 400
        
        # Get job data (in production, this would come from your job database)
        job_locations = data.get('job_locations', [])
        
        result = location_service.get_location_recommendations(
            data['zipcode'], job_locations
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting location recommendations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get location recommendations'
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@referral_gated_api.errorhandler(403)
def feature_locked(error):
    """Handle feature access denied"""
    return jsonify({
        'success': False,
        'error': 'Feature access required',
        'redirect_to_teaser': True,
        'message': 'Complete 3 referrals to unlock this feature'
    }), 403

@referral_gated_api.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@referral_gated_api.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
