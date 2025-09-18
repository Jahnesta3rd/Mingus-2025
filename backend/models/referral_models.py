#!/usr/bin/env python3
"""
Referral System Database Models
Handles referral tracking, unlock progress, and feature access control
"""

import sqlite3
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ReferralSystem:
    """Manages referral tracking and feature unlock system"""
    
    def __init__(self, db_path: str = 'referral_system.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize referral system database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table with referral tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    referral_count INTEGER DEFAULT 0,
                    successful_referrals INTEGER DEFAULT 0,
                    feature_unlocked BOOLEAN DEFAULT FALSE,
                    unlock_date TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Referrals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_user_id TEXT NOT NULL,
                    referred_email TEXT NOT NULL,
                    referral_code TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    validated_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (referrer_user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Feature access table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    unlocked BOOLEAN DEFAULT FALSE,
                    unlock_method TEXT,
                    unlock_date TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, feature_name)
                )
            ''')
            
            # Unlock attempts tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unlock_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    attempt_type TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Location preferences (for unlocked users)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS location_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    zipcode TEXT NOT NULL,
                    city TEXT,
                    state TEXT,
                    latitude REAL,
                    longitude REAL,
                    search_radius INTEGER DEFAULT 25,
                    commute_preference TEXT DEFAULT 'flexible',
                    remote_ok BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Resume uploads (for unlocked users)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resume_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_status TEXT DEFAULT 'pending',
                    analysis_results TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_access_user ON feature_access(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_unlock_attempts_user ON unlock_attempts(user_id)')
            
            conn.commit()
            conn.close()
            logger.info("Referral system database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing referral database: {e}")
            raise
    
    def create_user(self, user_id: str, email: str, first_name: str = None, 
                   last_name: str = None, referred_by: str = None) -> Dict:
        """Create a new user with referral code"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate unique referral code
            referral_code = self._generate_referral_code()
            
            # Check if user already exists
            cursor.execute('SELECT user_id FROM users WHERE user_id = ? OR email = ?', 
                         (user_id, email))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'error': 'User already exists'}
            
            # Create user
            cursor.execute('''
                INSERT INTO users (user_id, email, first_name, last_name, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, email, first_name, last_name, referral_code, referred_by))
            
            # If referred by someone, create referral record
            if referred_by:
                cursor.execute('''
                    INSERT INTO referrals (referrer_user_id, referred_email, referral_code)
                    VALUES (?, ?, ?)
                ''', (referred_by, email, referral_code))
                
                # Update referrer's count
                cursor.execute('''
                    UPDATE users SET referral_count = referral_count + 1
                    WHERE user_id = ?
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find the referral
            cursor.execute('''
                SELECT r.*, u.referral_code as referrer_code
                FROM referrals r
                JOIN users u ON r.referrer_user_id = u.user_id
                WHERE r.referral_code = ? AND r.referred_email = ?
            ''', (referral_code, referred_email))
            
            referral = cursor.fetchone()
            if not referral:
                conn.close()
                return {'success': False, 'error': 'Invalid referral code or email'}
            
            if referral[4] != 'pending':  # status column
                conn.close()
                return {'success': False, 'error': 'Referral already processed'}
            
            # Update referral status
            cursor.execute('''
                UPDATE referrals 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP, validated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (referral[0],))
            
            # Update referrer's successful referrals count
            cursor.execute('''
                UPDATE users 
                SET successful_referrals = successful_referrals + 1
                WHERE user_id = ?
            ''', (referral[1],))
            
            # Check if referrer should unlock features
            cursor.execute('''
                SELECT successful_referrals FROM users WHERE user_id = ?
            ''', (referral[1],))
            
            referrer_data = cursor.fetchone()
            if referrer_data and referrer_data[0] >= 3:
                self._unlock_features(referral[1], 'referral_program')
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Referral validated successfully',
                'referrer_code': referral[7]
            }
            
        except Exception as e:
            logger.error(f"Error validating referral: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_feature_access(self, user_id: str, feature_name: str = 'job_recommendations') -> Dict:
        """Check if user has access to a specific feature"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check feature access
            cursor.execute('''
                SELECT fa.unlocked, fa.unlock_date, fa.expires_at, u.successful_referrals
                FROM feature_access fa
                JOIN users u ON fa.user_id = u.user_id
                WHERE fa.user_id = ? AND fa.feature_name = ?
            ''', (user_id, feature_name))
            
            access = cursor.fetchone()
            
            if not access:
                # Check if user has enough referrals for automatic unlock
                cursor.execute('''
                    SELECT successful_referrals FROM users WHERE user_id = ?
                ''', (user_id,))
                
                user_data = cursor.fetchone()
                if user_data and user_data[0] >= 3:
                    self._unlock_features(user_id, 'referral_program')
                    conn.close()
                    return {
                        'success': True,
                        'unlocked': True,
                        'unlock_method': 'referral_program',
                        'referral_count': user_data[0]
                    }
                
                conn.close()
                return {
                    'success': True,
                    'unlocked': False,
                    'referral_count': user_data[0] if user_data else 0,
                    'referrals_needed': 3 - (user_data[0] if user_data else 0)
                }
            
            # Check if access has expired
            if access[2] and datetime.now() > datetime.fromisoformat(access[2]):
                conn.close()
                return {
                    'success': True,
                    'unlocked': False,
                    'expired': True,
                    'referral_count': access[3]
                }
            
            conn.close()
            return {
                'success': True,
                'unlocked': bool(access[0]),
                'unlock_date': access[1],
                'unlock_method': 'referral_program',
                'referral_count': access[3]
            }
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_referral_progress(self, user_id: str) -> Dict:
        """Get user's referral progress toward feature unlock"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT successful_referrals, referral_count, feature_unlocked
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return {'success': False, 'error': 'User not found'}
            
            successful_referrals = user_data[0]
            total_referrals = user_data[1]
            feature_unlocked = bool(user_data[2])
            
            # Get pending referrals
            cursor.execute('''
                SELECT referred_email, created_at, status
                FROM referrals 
                WHERE referrer_user_id = ?
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
                            'email': ref[0],
                            'created_at': ref[1],
                            'status': ref[2]
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO unlock_attempts 
                (user_id, feature_name, attempt_type, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
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
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to handle updates
            cursor.execute('''
                INSERT OR REPLACE INTO location_preferences 
                (user_id, zipcode, city, state, latitude, longitude, 
                 search_radius, commute_preference, remote_ok, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO resume_uploads 
                (user_id, filename, file_path, file_size, file_type)
                VALUES (?, ?, ?, ?, ?)
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (code,))
            if not cursor.fetchone():
                conn.close()
                return code
            conn.close()
    
    def _unlock_features(self, user_id: str, unlock_method: str):
        """Unlock features for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update user's feature unlock status
            cursor.execute('''
                UPDATE users 
                SET feature_unlocked = TRUE, unlock_date = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            # Add feature access record
            cursor.execute('''
                INSERT OR REPLACE INTO feature_access 
                (user_id, feature_name, unlocked, unlock_method, unlock_date)
                VALUES (?, 'job_recommendations', TRUE, ?, CURRENT_TIMESTAMP)
            ''', (user_id, unlock_method))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Features unlocked for user {user_id} via {unlock_method}")
            
        except Exception as e:
            logger.error(f"Error unlocking features: {e}")
            raise
