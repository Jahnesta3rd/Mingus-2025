"""
Advanced Resume Parsing API endpoints
Extends the existing resume parsing with advanced analytics for African American professionals
"""

import os
import sqlite3
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError

# Import the advanced parser
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.advanced_resume_parser import AdvancedResumeParser
from utils.resume_format_handler import AdvancedResumeParserWithFormats

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
advanced_resume_api = Blueprint('advanced_resume_api', __name__, url_prefix='/api')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('resume_parsing.db')
    conn.row_factory = sqlite3.Row
    return conn

def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token (simplified for demo)"""
    # In production, implement proper CSRF validation
    return token is not None and len(token) > 0

def check_rate_limit(client_ip: str) -> bool:
    """Check rate limiting (simplified for demo)"""
    # In production, implement proper rate limiting with Redis
    return True

@advanced_resume_api.route('/resume/parse-advanced', methods=['POST'])
def parse_resume_advanced():
    """
    Parse resume content with advanced analytics
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in advanced resume parsing")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        # Validate required fields
        if 'content' not in data:
            raise BadRequest("Missing required field: content")
        
        content = data['content']
        file_name = data.get('file_name', 'Unknown')
        user_id = data.get('user_id', 'anonymous')
        location = data.get('location', 'New York')
        
        # Validate content
        if not content or len(content.strip()) < 50:
            raise BadRequest("Resume content is too short or empty")
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Check if resume was already parsed
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM resume_parsing_results WHERE file_hash = ?', (file_hash,))
        existing_result = cursor.fetchone()
        
        if existing_result:
            conn.close()
            return jsonify({
                'success': True,
                'parsed_data': json.loads(existing_result['parsed_data']),
                'advanced_analytics': json.loads(existing_result.get('advanced_analytics', '{}')),
                'metadata': {
                    'file_name': existing_result['file_name'],
                    'confidence_score': existing_result['confidence_score'],
                    'processing_timestamp': existing_result['created_at'],
                    'cached': True
                },
                'message': 'Resume already parsed (cached result)'
            })
        
        # Parse resume with advanced analytics
        start_time = datetime.utcnow()
        parser = AdvancedResumeParser()
        result = parser.parse_resume_advanced(content, file_name, location)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        if not result.get('success', False):
            conn.close()
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown parsing error'),
                'parsed_data': {},
                'advanced_analytics': {}
            }), 400
        
        # Store result in database
        advanced_analytics = result.get('advanced_analytics', {})
        cursor.execute('''
            INSERT INTO resume_parsing_results 
            (user_id, file_name, file_hash, raw_content, parsed_data, extraction_errors, confidence_score, processing_time, advanced_analytics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            file_name,
            file_hash,
            content,
            json.dumps(result.get('parsed_data', {})),
            json.dumps(result.get('errors', [])),
            result.get('metadata', {}).get('confidence_score', 0.0),
            processing_time,
            json.dumps(advanced_analytics)
        ))
        
        resume_id = cursor.lastrowid
        
        # Track analytics
        cursor.execute('''
            INSERT INTO resume_analytics (resume_id, action, data)
            VALUES (?, ?, ?)
        ''', (resume_id, 'advanced_resume_parsed', json.dumps({
            'file_name': file_name,
            'content_length': len(content),
            'confidence_score': result.get('metadata', {}).get('confidence_score', 0.0),
            'processing_time': processing_time,
            'error_count': len(result.get('errors', [])),
            'warning_count': len(result.get('warnings', [])),
            'career_field': advanced_analytics.get('career_field'),
            'experience_level': advanced_analytics.get('experience_level'),
            'location': location
        })))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Advanced resume parsed successfully: {resume_id}")
        
        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'parsed_data': result.get('parsed_data', {}),
            'advanced_analytics': advanced_analytics,
            'metadata': result.get('metadata', {}),
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'message': 'Resume parsed successfully with advanced analytics'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in parse_resume_advanced: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in parse_resume_advanced: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@advanced_resume_api.route('/resume/parse-file', methods=['POST'])
def parse_resume_file():
    """
    Parse resume from uploaded file with advanced analytics
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in file resume parsing")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        
        # Check if file was uploaded
        if 'file' not in request.files:
            raise BadRequest("No file uploaded")
        
        file = request.files['file']
        if file.filename == '':
            raise BadRequest("No file selected")
        
        # Get additional parameters
        user_id = request.form.get('user_id', 'anonymous')
        location = request.form.get('location', 'New York')
        
        # Read file content
        file_bytes = file.read()
        file_name = file.filename
        
        # Parse resume with advanced analytics
        start_time = datetime.utcnow()
        parser = AdvancedResumeParserWithFormats()
        result = parser.parse_resume_from_bytes(file_bytes, file_name, location)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        if not result.get('success', False):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown parsing error'),
                'parsed_data': {},
                'advanced_analytics': {}
            }), 400
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(file_bytes).hexdigest()
        
        # Store result in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        advanced_analytics = result.get('advanced_analytics', {})
        cursor.execute('''
            INSERT INTO resume_parsing_results 
            (user_id, file_name, file_hash, raw_content, parsed_data, extraction_errors, confidence_score, processing_time, advanced_analytics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            file_name,
            file_hash,
            '',  # Raw content not stored for file uploads
            json.dumps(result.get('parsed_data', {})),
            json.dumps(result.get('errors', [])),
            result.get('metadata', {}).get('confidence_score', 0.0),
            processing_time,
            json.dumps(advanced_analytics)
        ))
        
        resume_id = cursor.lastrowid
        
        # Track analytics
        cursor.execute('''
            INSERT INTO resume_analytics (resume_id, action, data)
            VALUES (?, ?, ?)
        ''', (resume_id, 'advanced_file_resume_parsed', json.dumps({
            'file_name': file_name,
            'file_size': len(file_bytes),
            'confidence_score': result.get('metadata', {}).get('confidence_score', 0.0),
            'processing_time': processing_time,
            'error_count': len(result.get('errors', [])),
            'warning_count': len(result.get('warnings', [])),
            'career_field': advanced_analytics.get('career_field'),
            'experience_level': advanced_analytics.get('experience_level'),
            'location': location
        })))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Advanced file resume parsed successfully: {resume_id}")
        
        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'parsed_data': result.get('parsed_data', {}),
            'advanced_analytics': advanced_analytics,
            'file_info': result.get('file_info', {}),
            'metadata': result.get('metadata', {}),
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'message': 'Resume file parsed successfully with advanced analytics'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in parse_resume_file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in parse_resume_file: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@advanced_resume_api.route('/resume/analytics/<resume_id>', methods=['GET'])
def get_resume_analytics(resume_id):
    """
    Get advanced analytics for a parsed resume
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT parsed_data, advanced_analytics, confidence_score, created_at
            FROM resume_parsing_results 
            WHERE id = ?
        ''', (resume_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'error': 'Resume not found'}), 404
        
        parsed_data = json.loads(result['parsed_data'])
        advanced_analytics = json.loads(result['advanced_analytics'] or '{}')
        
        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'parsed_data': parsed_data,
            'advanced_analytics': advanced_analytics,
            'confidence_score': result['confidence_score'],
            'created_at': result['created_at']
        })
        
    except Exception as e:
        logger.error(f"Error getting resume analytics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@advanced_resume_api.route('/resume/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """
    Get summary of resume analytics across all parsed resumes
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic statistics
        cursor.execute('''
            SELECT COUNT(*) as total_resumes,
                   AVG(confidence_score) as avg_confidence,
                   COUNT(CASE WHEN advanced_analytics IS NOT NULL AND advanced_analytics != '{}' THEN 1 END) as advanced_parsed
            FROM resume_parsing_results
        ''')
        
        stats = cursor.fetchone()
        
        # Get career field distribution
        cursor.execute('''
            SELECT json_extract(advanced_analytics, '$.career_field') as career_field,
                   COUNT(*) as count
            FROM resume_parsing_results
            WHERE advanced_analytics IS NOT NULL AND advanced_analytics != '{}'
            GROUP BY career_field
            ORDER BY count DESC
        ''')
        
        career_fields = cursor.fetchall()
        
        # Get experience level distribution
        cursor.execute('''
            SELECT json_extract(advanced_analytics, '$.experience_level') as experience_level,
                   COUNT(*) as count
            FROM resume_parsing_results
            WHERE advanced_analytics IS NOT NULL AND advanced_analytics != '{}'
            GROUP BY experience_level
            ORDER BY count DESC
        ''')
        
        experience_levels = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_resumes': stats['total_resumes'],
                'average_confidence': round(stats['avg_confidence'] or 0, 2),
                'advanced_parsed': stats['advanced_parsed'],
                'career_field_distribution': [
                    {'field': row['career_field'], 'count': row['count']} 
                    for row in career_fields
                ],
                'experience_level_distribution': [
                    {'level': row['experience_level'], 'count': row['count']} 
                    for row in experience_levels
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
