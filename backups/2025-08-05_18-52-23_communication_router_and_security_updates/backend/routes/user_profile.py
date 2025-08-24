#!/usr/bin/env python3
"""
User Profile API Routes
Handles all user profile operations including CRUD, validation, and onboarding
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
user_profile_bp = Blueprint('user_profile', __name__, url_prefix='/api/user-profile')

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('instance/mingus.db')
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def validate_user_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user profile data"""
    errors = []
    
    # Required fields validation
    required_fields = ['first_name', 'last_name', 'zip_code']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Field-specific validation
    if data.get('first_name') and len(data['first_name'].strip()) < 2:
        errors.append("First name must be at least 2 characters")
    
    if data.get('last_name') and len(data['last_name'].strip()) < 2:
        errors.append("Last name must be at least 2 characters")
    
    if data.get('zip_code'):
        zip_code = data['zip_code'].replace('-', '')
        if not zip_code.isdigit() or len(zip_code) not in [5, 9]:
            errors.append("ZIP code must be 5 or 9 digits")
    
    if data.get('dependents') is not None:
        try:
            dependents = int(data['dependents'])
            if dependents < 0 or dependents > 20:
                errors.append("Dependents must be between 0 and 20")
        except ValueError:
            errors.append("Dependents must be a number")
    
    if data.get('monthly_income') is not None:
        try:
            income = float(data['monthly_income'])
            if income < 0:
                errors.append("Monthly income cannot be negative")
        except ValueError:
            errors.append("Monthly income must be a number")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def calculate_profile_completion_percentage(user_data: Dict[str, Any]) -> float:
    """Calculate profile completion percentage"""
    total_fields = 0
    completed_fields = 0
    
    # Define important fields for completion calculation
    important_fields = [
        'first_name', 'last_name', 'zip_code', 'dependents', 'marital_status',
        'industry', 'job_title', 'monthly_income', 'employment_status',
        'education_level', 'primary_financial_goal', 'risk_tolerance_level'
    ]
    
    for field in important_fields:
        total_fields += 1
        if user_data.get(field):
            completed_fields += 1
    
    # Add bonus for additional fields
    bonus_fields = [
        'phone_number', 'date_of_birth', 'company_name', 'company_size',
        'years_of_experience', 'current_savings_balance', 'total_debt_amount'
    ]
    
    for field in bonus_fields:
        if user_data.get(field):
            completed_fields += 0.5
    
    completion_percentage = min(100.0, (completed_fields / total_fields) * 100)
    return round(completion_percentage, 1)

@user_profile_bp.route('/get', methods=['GET'])
@login_required
def get_user_profile():
    """Get current user's profile"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get user profile from users table
        cursor.execute('''
            SELECT id, email, first_name, last_name, date_of_birth, gender, phone_number,
                   zip_code, city, state, country, timezone, dependents, marital_status,
                   household_size, monthly_income, income_frequency, primary_income_source,
                   current_savings_balance, total_debt_amount, credit_score_range,
                   employment_status, education_level, occupation, industry,
                   years_of_experience, company_name, company_size, job_title, naics_code,
                   primary_financial_goal, risk_tolerance_level, financial_knowledge_level,
                   preferred_contact_method, notification_preferences, health_checkin_frequency,
                   stress_level_baseline, wellness_goals, gdpr_consent_status,
                   data_sharing_preferences, profile_completion_percentage, onboarding_step,
                   email_verification_status, is_active, created_at, updated_at
            FROM users WHERE email = ?
        ''', (current_user.email,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Convert to dictionary
        profile_data = dict(user)
        
        # Parse JSON fields
        for field in ['notification_preferences', 'wellness_goals']:
            if profile_data.get(field):
                try:
                    profile_data[field] = json.loads(profile_data[field])
                except json.JSONDecodeError:
                    profile_data[field] = None
        
        conn.close()
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_profile_bp.route('/update', methods=['POST'])
@login_required
def update_user_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate data
        validation = validate_user_profile_data(data)
        if not validation['valid']:
            return jsonify({
                'error': 'Validation failed',
                'errors': validation['errors']
            }), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Calculate profile completion percentage
        current_profile = cursor.execute(
            'SELECT * FROM users WHERE email = ?', (current_user.email,)
        ).fetchone()
        
        if current_profile:
            current_data = dict(current_profile)
            # Merge current data with new data
            updated_data = {**current_data, **data}
        else:
            updated_data = data
        
        completion_percentage = calculate_profile_completion_percentage(updated_data)
        
        # Prepare update fields
        update_fields = []
        update_values = []
        
        # Map frontend field names to database column names
        field_mapping = {
            'firstName': 'first_name',
            'lastName': 'last_name',
            'dateOfBirth': 'date_of_birth',
            'zipCode': 'zip_code',
            'phoneNumber': 'phone_number',
            'dependentsCount': 'dependents',
            'maritalStatus': 'marital_status',
            'householdSize': 'household_size',
            'monthlyIncome': 'monthly_income',
            'incomeFrequency': 'income_frequency',
            'primaryIncomeSource': 'primary_income_source',
            'currentSavingsBalance': 'current_savings_balance',
            'totalDebtAmount': 'total_debt_amount',
            'creditScoreRange': 'credit_score_range',
            'employmentStatus': 'employment_status',
            'educationLevel': 'education_level',
            'occupation': 'occupation',
            'industry': 'industry',
            'yearsOfExperience': 'years_of_experience',
            'companyName': 'company_name',
            'companySize': 'company_size',
            'jobTitle': 'job_title',
            'naicsCode': 'naics_code',
            'primaryFinancialGoal': 'primary_financial_goal',
            'riskToleranceLevel': 'risk_tolerance_level',
            'financialKnowledgeLevel': 'financial_knowledge_level',
            'preferredContactMethod': 'preferred_contact_method',
            'notificationPreferences': 'notification_preferences',
            'healthCheckinFrequency': 'health_checkin_frequency',
            'stressLevelBaseline': 'stress_level_baseline',
            'wellnessGoals': 'wellness_goals',
            'gdprConsentStatus': 'gdpr_consent_status',
            'dataSharingPreferences': 'data_sharing_preferences'
        }
        
        for frontend_field, db_field in field_mapping.items():
            if frontend_field in data:
                update_fields.append(f"{db_field} = ?")
                value = data[frontend_field]
                
                # Handle JSON fields
                if frontend_field in ['notificationPreferences', 'wellnessGoals']:
                    value = json.dumps(value) if value else None
                
                update_values.append(value)
        
        # Add completion percentage and timestamp
        update_fields.extend([
            'profile_completion_percentage = ?',
            'updated_at = ?'
        ])
        update_values.extend([completion_percentage, datetime.now().isoformat()])
        
        # Update user profile
        update_sql = f'''
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE email = ?
        '''
        update_values.append(current_user.email)
        
        cursor.execute(update_sql, update_values)
        
        # Also update user_profiles table if it exists
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles (
                    user_id, first_name, last_name, zip_code, dependents,
                    marital_status, industry, job_title, naics_code,
                    annual_income, employment_status, profile_completion_percentage,
                    updated_at
                ) VALUES (
                    (SELECT id FROM users WHERE email = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                current_user.email,
                data.get('firstName') or data.get('first_name'),
                data.get('lastName') or data.get('last_name'),
                data.get('zipCode') or data.get('zip_code'),
                data.get('dependentsCount') or data.get('dependents', 0),
                data.get('maritalStatus') or data.get('marital_status'),
                data.get('industry'),
                data.get('jobTitle') or data.get('job_title'),
                data.get('naicsCode') or data.get('naics_code'),
                (data.get('monthlyIncome') or 0) * 12,  # Convert to annual
                data.get('employmentStatus') or data.get('employment_status'),
                completion_percentage,
                datetime.now().isoformat()
            ))
        except Exception as e:
            logger.warning(f"Could not update user_profiles table: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile_completion_percentage': completion_percentage
        })
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_profile_bp.route('/onboarding-progress', methods=['GET'])
@login_required
def get_onboarding_progress():
    """Get user's onboarding progress"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user.email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Get onboarding progress
        cursor.execute('''
            SELECT step_name, step_order, is_completed, completed_at, step_data
            FROM onboarding_progress 
            WHERE user_id = ? 
            ORDER BY step_order
        ''', (user_id,))
        
        progress = []
        for row in cursor.fetchall():
            step_data = json.loads(row['step_data']) if row['step_data'] else {}
            progress.append({
                'step_name': row['step_name'],
                'step_order': row['step_order'],
                'is_completed': bool(row['is_completed']),
                'completed_at': row['completed_at'],
                'step_data': step_data
            })
        
        # Get current user profile completion
        cursor.execute('''
            SELECT profile_completion_percentage, onboarding_step
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user_info = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'progress': progress,
            'profile_completion_percentage': user_info['profile_completion_percentage'],
            'current_step': user_info['onboarding_step']
        })
        
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_profile_bp.route('/onboarding-progress', methods=['POST'])
@login_required
def update_onboarding_progress():
    """Update user's onboarding progress"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['step_name', 'step_order', 'is_completed']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user.email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Update or insert onboarding progress
        cursor.execute('''
            INSERT OR REPLACE INTO onboarding_progress (
                user_id, step_name, step_order, is_completed, completed_at, step_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data['step_name'],
            data['step_order'],
            data['is_completed'],
            datetime.now().isoformat() if data['is_completed'] else None,
            json.dumps(data.get('step_data', {})),
            datetime.now().isoformat()
        ))
        
        # Update user's onboarding step
        if data['is_completed']:
            cursor.execute('''
                UPDATE users 
                SET onboarding_step = ? 
                WHERE id = ?
            ''', (data['step_order'] + 1, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Onboarding progress updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating onboarding progress: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_profile_bp.route('/subscription', methods=['GET'])
@login_required
def get_user_subscription():
    """Get user's subscription information"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user.email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Get subscription information
        cursor.execute('''
            SELECT s.id, s.status, s.current_period_start, s.current_period_end,
                   s.trial_start, s.trial_end, s.cancelled_at, s.created_at,
                   sp.name as plan_name, sp.description as plan_description,
                   sp.price as plan_price, sp.billing_cycle, sp.features
            FROM subscriptions s
            JOIN subscription_plans sp ON s.plan_id = sp.id
            WHERE s.user_id = ? AND s.status = 'active'
            ORDER BY s.created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        subscription = cursor.fetchone()
        
        if subscription:
            subscription_data = dict(subscription)
            # Parse features JSON
            if subscription_data.get('features'):
                subscription_data['features'] = json.loads(subscription_data['features'])
        else:
            subscription_data = None
        
        # Get available plans
        cursor.execute('''
            SELECT id, name, description, price, billing_cycle, features
            FROM subscription_plans 
            WHERE is_active = 1
            ORDER BY price
        ''')
        
        available_plans = []
        for row in cursor.fetchall():
            plan_data = dict(row)
            if plan_data.get('features'):
                plan_data['features'] = json.loads(plan_data['features'])
            available_plans.append(plan_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'subscription': subscription_data,
            'available_plans': available_plans
        })
        
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_profile_bp.route('/feature-usage', methods=['GET'])
@login_required
def get_feature_usage():
    """Get user's feature usage statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user.email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Get current month's usage
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        cursor.execute('''
            SELECT fu.feature_name, fu.usage_count, fu.usage_month, fu.usage_year
            FROM feature_usage fu
            JOIN subscriptions s ON fu.subscription_id = s.id
            WHERE s.user_id = ? AND fu.usage_month = ? AND fu.usage_year = ?
        ''', (user_id, current_month, current_year))
        
        usage_data = {}
        for row in cursor.fetchall():
            usage_data[row['feature_name']] = {
                'count': row['usage_count'],
                'month': row['usage_month'],
                'year': row['usage_year']
            }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'usage': usage_data,
            'current_month': current_month,
            'current_year': current_year
        })
        
    except Exception as e:
        logger.error(f"Error getting feature usage: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers
@user_profile_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@user_profile_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
