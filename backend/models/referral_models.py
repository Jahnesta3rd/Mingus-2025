#!/usr/bin/env python3
"""
Referral System Database Models
Handles referral tracking, unlock progress, and feature access control
"""

import psycopg2
import psycopg2.extras
import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def get_pg_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

class ReferralSystem:
    """Manages referral tracking and feature unlock system"""
    
    def __init__(self, db_path: str = None):
        self.init_database()
    
    def init_database(self):
        """Verify PostgreSQL database connection"""
        try:
            conn = get_pg_connection()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def create_user(self, user_id: str, email: str, first_name: str = None, 
                   last_name: str = None, referred_by: str = None) -> Dict:
        """Create a new user with referral code"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            # Generate unique referral code
            referral_code = self._generate_referral_code()
            
            # Check if user already exists
            cursor.execute('SELECT user_id FROM users WHERE user_id = %s OR email = %s', 
                         (user_id, email))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'error': 'User already exists'}
            
            # Create user
            cursor.execute('''
                INSERT INTO users (user_id, email, first_name, last_name, referral_code, referred_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, email, first_name, last_name, referral_code, referred_by))
            
            # If referred by someone, create referral record
            if referred_by:
                cursor.execute('''
                    INSERT INTO referrals (referrer_user_id, referred_email, referral_code)
                    VALUES (%s, %s, %s)
                ''', (referred_by, email, referral_code))
                
                # Update referrer's count
                cursor.execute('''
                    UPDATE users SET referral_count = referral_count + 1
                    WHERE user_id = %s
                ''', (referred_by,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user_id': user_id,
                'referral_code': referral_code,
                'message': 'User created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_referral(self, referral_code: str, referred_email: str) -> Dict:
        """Validate and complete a referral"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            # Find the referral
            cursor.execute('''
                SELECT r.*, u.referral_code as referrer_code
                FROM referrals r
                JOIN users u ON r.referrer_user_id = u.user_id
                WHERE r.referral_code = %s AND r.referred_email = %s
            ''', (referral_code, referred_email))
            
            referral = cursor.fetchone()
            if not referral:
                conn.close()
                return {'success': False, 'error': 'Invalid referral code or email'}
            
            if referral['status'] != 'pending':  # status column
                conn.close()
                return {'success': False, 'error': 'Referral already processed'}
            
            # Update referral status
            cursor.execute('''
                UPDATE referrals 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP, validated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (referral['id'],))
            
            # Update referrer's successful referrals count
            cursor.execute('''
                UPDATE users 
                SET successful_referrals = successful_referrals + 1
                WHERE user_id = %s
            ''', (referral['referrer_user_id'],))
            
            # Check if referrer should unlock features
            cursor.execute('''
                SELECT successful_referrals FROM users WHERE user_id = %s
            ''', (referral['referrer_user_id'],))
            
            referrer_data = cursor.fetchone()
            if referrer_data and referrer_data['successful_referrals'] >= 3:
                self._unlock_features(referral['referrer_user_id'], 'referral_program')
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Referral validated successfully',
                'referrer_code': referral['referrer_code']
            }
            
        except Exception as e:
            logger.error(f"Error validating referral: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_feature_access(self, user_id: str, feature_name: str = 'job_recommendations') -> Dict:
        """Check if user has access to a specific feature"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            # Check feature access
            cursor.execute('''
                SELECT fa.unlocked, fa.unlock_date, fa.expires_at, u.successful_referrals
                FROM feature_access fa
                JOIN users u ON fa.user_id = u.user_id
                WHERE fa.user_id = %s AND fa.feature_name = %s
            ''', (user_id, feature_name))
            
            access = cursor.fetchone()
            
            if not access:
                # Check if user has enough referrals for automatic unlock
                cursor.execute('''
                    SELECT successful_referrals FROM users WHERE user_id = %s
                ''', (user_id,))
                
                user_data = cursor.fetchone()
                if user_data and user_data['successful_referrals'] >= 3:
                    self._unlock_features(user_id, 'referral_program')
                    conn.close()
                    return {
                        'success': True,
                        'unlocked': True,
                        'unlock_method': 'referral_program',
                        'referral_count': user_data['successful_referrals']
                    }
                
                conn.close()
                return {
                    'success': True,
                    'unlocked': False,
                    'referral_count': user_data['successful_referrals'] if user_data else 0,
                    'referrals_needed': 3 - (user_data['successful_referrals'] if user_data else 0)
                }
            
            # Check if access has expired
            if access['expires_at'] and datetime.now() > datetime.fromisoformat(access['expires_at']):
                conn.close()
                return {
                    'success': True,
                    'unlocked': False,
                    'expired': True,
                    'referral_count': access['successful_referrals']
                }
            
            conn.close()
            return {
                'success': True,
                'unlocked': bool(access['unlocked']),
                'unlock_date': access['unlock_date'],
                'unlock_method': 'referral_program',
                'referral_count': access['successful_referrals']
            }
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_referral_progress(self, user_id: str) -> Dict:
        """Get user's referral progress toward feature unlock"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT successful_referrals, referral_count, feature_unlocked
                FROM users WHERE user_id = %s
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return {'success': False, 'error': 'User not found'}
            
            successful_referrals = user_data['successful_referrals']
            total_referrals = user_data['referral_count']
            feature_unlocked = bool(user_data['feature_unlocked'])
            
            # Get pending referrals
            cursor.execute('''
                SELECT referred_email, created_at, status
                FROM referrals 
                WHERE referrer_user_id = %s
                ORDER BY created_at DESC
            ''', (user_id,))
            
            referrals = cursor.fetchall()
            
            conn.close()
            
            return {
                'success': True,
                'progress': {
                    'successful_referrals': successful_referrals,
                    'total_referrals': total_referrals,
                    'referrals_needed': max(0, 3 - successful_referrals),
                    'feature_unlocked': feature_unlocked,
                    'progress_percentage': min(100, (successful_referrals / 3) * 100),
                    'referrals': [
                        {
                            'email': ref['referred_email'],
                            'created_at': ref['created_at'],
                            'status': ref['status']
                        } for ref in referrals
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting referral progress: {e}")
            return {'success': False, 'error': str(e)}
    
    def track_unlock_attempt(self, user_id: str, feature_name: str, 
                           attempt_type: str, ip_address: str = None, 
                           user_agent: str = None) -> Dict:
        """Track user attempts to access locked features"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO unlock_attempts 
                (user_id, feature_name, attempt_type, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, feature_name, attempt_type, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Attempt tracked'}
            
        except Exception as e:
            logger.error(f"Error tracking unlock attempt: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_location_preferences(self, user_id: str, zipcode: str, 
                                city: str = None, state: str = None,
                                latitude: float = None, longitude: float = None,
                                search_radius: int = 25, commute_preference: str = 'flexible',
                                remote_ok: bool = True) -> Dict:
        """Save user location preferences (unlocked users only)"""
        try:
            # Check if user has feature access
            access_check = self.check_feature_access(user_id, 'job_recommendations')
            if not access_check['success'] or not access_check['unlocked']:
                return {'success': False, 'error': 'Feature access required'}
            
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO location_preferences 
                (user_id, zipcode, city, state, latitude, longitude, 
                 search_radius, commute_preference, remote_ok, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    zipcode = EXCLUDED.zipcode,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    search_radius = EXCLUDED.search_radius,
                    commute_preference = EXCLUDED.commute_preference,
                    remote_ok = EXCLUDED.remote_ok,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, zipcode, city, state, latitude, longitude, 
                  search_radius, commute_preference, remote_ok))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Location preferences saved'}
            
        except Exception as e:
            logger.error(f"Error saving location preferences: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_resume_upload(self, user_id: str, filename: str, file_path: str,
                          file_size: int, file_type: str) -> Dict:
        """Save resume upload record (unlocked users only)"""
        try:
            # Check if user has feature access
            access_check = self.check_feature_access(user_id, 'job_recommendations')
            if not access_check['success'] or not access_check['unlocked']:
                return {'success': False, 'error': 'Feature access required'}
            
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO resume_uploads 
                (user_id, filename, file_path, file_size, file_type)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, filename, file_path, file_size, file_type))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Resume upload recorded'}
            
        except Exception as e:
            logger.error(f"Error saving resume upload: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_referral_code(self) -> str:
        """Generate a unique referral code"""
        while True:
            code = secrets.token_urlsafe(8).upper()
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE referral_code = %s', (code,))
            if not cursor.fetchone():
                conn.close()
                return code
            conn.close()
    
    def _unlock_features(self, user_id: str, unlock_method: str):
        """Unlock features for user"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            # Update user's feature unlock status
            cursor.execute('''
                UPDATE users 
                SET feature_unlocked = TRUE, unlock_date = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (user_id,))
            
            # Add feature access record
            cursor.execute('''
                INSERT INTO feature_access 
                (user_id, feature_name, unlocked, unlock_method, unlock_date)
                VALUES (%s, 'job_recommendations', TRUE, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, feature_name) DO UPDATE SET
                    unlocked = TRUE,
                    unlock_method = EXCLUDED.unlock_method,
                    unlock_date = CURRENT_TIMESTAMP
            ''', (user_id, unlock_method))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Features unlocked for user {user_id} via {unlock_method}")
            
        except Exception as e:
            logger.error(f"Error unlocking features: {e}")
            raise
