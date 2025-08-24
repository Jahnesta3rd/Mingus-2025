"""
Secure Financial Profile Routes
Provides secure endpoints for financial profile management with encryption and audit logging
"""

from flask import Blueprint, request, jsonify, g, current_app
from loguru import logger
from functools import wraps
from typing import Dict, Any, Optional
import uuid

from backend.app_factory import get_audit_service, get_db_session
from backend.models.encrypted_financial_models import (
    EncryptedFinancialProfile, EncryptedIncomeSource, EncryptedDebtAccount
)
from backend.middleware.security_middleware import (
    require_https, validate_financial_data, audit_financial_access
)

# Create blueprint
secure_financial_bp = Blueprint('secure_financial', __name__)

def require_authentication(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# FINANCIAL PROFILE ENDPOINTS
# =====================================================

@secure_financial_bp.route('/api/secure/financial-profile', methods=['GET'])
@require_https
@require_authentication
@audit_financial_access
def get_financial_profile():
    """Get user's encrypted financial profile"""
    try:
        user_id = g.user_id
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Get profile from database
        profile = db_session.query(EncryptedFinancialProfile).filter(
            EncryptedFinancialProfile.user_id == user_id
        ).first()
        
        if not profile:
            return jsonify({'error': 'Financial profile not found'}), 404
        
        # Log access
        audit_service.log_financial_profile_access(profile.id, 'READ')
        
        # Return decrypted data
        return jsonify({
            'success': True,
            'data': profile.to_dict(),
            'request_id': g.get('request_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting financial profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@secure_financial_bp.route('/api/secure/financial-profile', methods=['POST'])
@require_https
@require_authentication
@validate_financial_data
@audit_financial_access
def create_financial_profile():
    """Create new encrypted financial profile"""
    try:
        user_id = g.user_id
        data = request.get_json()
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Check if profile already exists
        existing_profile = db_session.query(EncryptedFinancialProfile).filter(
            EncryptedFinancialProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            return jsonify({'error': 'Financial profile already exists'}), 409
        
        # Create new profile with encrypted data
        profile = EncryptedFinancialProfile(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        
        # Set encrypted values
        if 'monthly_income' in data:
            profile.set_monthly_income(float(data['monthly_income']))
        
        if 'current_savings' in data:
            profile.set_current_savings(float(data['current_savings']))
        
        if 'current_debt' in data:
            profile.set_current_debt(float(data['current_debt']))
        
        if 'emergency_fund' in data:
            profile.set_emergency_fund(float(data['emergency_fund']))
        
        if 'savings_goal' in data:
            profile.set_savings_goal(float(data['savings_goal']))
        
        # Set non-sensitive fields
        profile.income_frequency = data.get('income_frequency')
        profile.primary_income_source = data.get('primary_income_source')
        profile.secondary_income_source = data.get('secondary_income_source')
        profile.risk_tolerance = data.get('risk_tolerance')
        profile.investment_experience = data.get('investment_experience')
        profile.budgeting_experience = data.get('budgeting_experience')
        
        # Save to database
        db_session.add(profile)
        db_session.commit()
        
        # Log creation
        audit_service.log_financial_profile_access(profile.id, 'CREATE')
        
        return jsonify({
            'success': True,
            'message': 'Financial profile created successfully',
            'profile_id': profile.id,
            'request_id': g.get('request_id')
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating financial profile: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@secure_financial_bp.route('/api/secure/financial-profile', methods=['PUT'])
@require_https
@require_authentication
@validate_financial_data
@audit_financial_access
def update_financial_profile():
    """Update encrypted financial profile"""
    try:
        user_id = g.user_id
        data = request.get_json()
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Get existing profile
        profile = db_session.query(EncryptedFinancialProfile).filter(
            EncryptedFinancialProfile.user_id == user_id
        ).first()
        
        if not profile:
            return jsonify({'error': 'Financial profile not found'}), 404
        
        # Track changes for audit
        changes = {}
        
        # Update encrypted fields with audit logging
        if 'monthly_income' in data:
            old_value = profile.get_monthly_income()
            new_value = float(data['monthly_income'])
            profile.set_monthly_income(new_value)
            audit_service.log_field_update(
                'encrypted_financial_profiles', 
                profile.id, 
                'monthly_income', 
                old_value, 
                new_value
            )
        
        if 'current_savings' in data:
            old_value = profile.get_current_savings()
            new_value = float(data['current_savings'])
            profile.set_current_savings(new_value)
            audit_service.log_field_update(
                'encrypted_financial_profiles', 
                profile.id, 
                'current_savings', 
                old_value, 
                new_value
            )
        
        if 'current_debt' in data:
            old_value = profile.get_current_debt()
            new_value = float(data['current_debt'])
            profile.set_current_debt(new_value)
            audit_service.log_field_update(
                'encrypted_financial_profiles', 
                profile.id, 
                'current_debt', 
                old_value, 
                new_value
            )
        
        if 'emergency_fund' in data:
            old_value = profile.get_emergency_fund()
            new_value = float(data['emergency_fund'])
            profile.set_emergency_fund(new_value)
            audit_service.log_field_update(
                'encrypted_financial_profiles', 
                profile.id, 
                'emergency_fund', 
                old_value, 
                new_value
            )
        
        if 'savings_goal' in data:
            old_value = profile.get_savings_goal()
            new_value = float(data['savings_goal'])
            profile.set_savings_goal(new_value)
            audit_service.log_field_update(
                'encrypted_financial_profiles', 
                profile.id, 
                'savings_goal', 
                old_value, 
                new_value
            )
        
        # Update non-sensitive fields
        if 'income_frequency' in data:
            profile.income_frequency = data['income_frequency']
        
        if 'primary_income_source' in data:
            profile.primary_income_source = data['primary_income_source']
        
        if 'secondary_income_source' in data:
            profile.secondary_income_source = data['secondary_income_source']
        
        if 'risk_tolerance' in data:
            profile.risk_tolerance = data['risk_tolerance']
        
        if 'investment_experience' in data:
            profile.investment_experience = data['investment_experience']
        
        if 'budgeting_experience' in data:
            profile.budgeting_experience = data['budgeting_experience']
        
        # Save changes
        db_session.commit()
        
        # Log update
        audit_service.log_financial_profile_access(profile.id, 'UPDATE')
        
        return jsonify({
            'success': True,
            'message': 'Financial profile updated successfully',
            'request_id': g.get('request_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating financial profile: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# INCOME SOURCES ENDPOINTS
# =====================================================

@secure_financial_bp.route('/api/secure/income-sources', methods=['GET'])
@require_https
@require_authentication
@audit_financial_access
def get_income_sources():
    """Get user's encrypted income sources"""
    try:
        user_id = g.user_id
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Get income sources
        sources = db_session.query(EncryptedIncomeSource).filter(
            EncryptedIncomeSource.user_id == user_id,
            EncryptedIncomeSource.is_active == True
        ).all()
        
        # Log access for each source
        for source in sources:
            audit_service.log_income_source_access(source.id, 'READ')
        
        return jsonify({
            'success': True,
            'data': [source.to_dict() for source in sources],
            'request_id': g.get('request_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting income sources: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@secure_financial_bp.route('/api/secure/income-sources', methods=['POST'])
@require_https
@require_authentication
@validate_financial_data
@audit_financial_access
def create_income_source():
    """Create new encrypted income source"""
    try:
        user_id = g.user_id
        data = request.get_json()
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Create new income source
        source = EncryptedIncomeSource(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source_name=data['source_name'],
            frequency=data['frequency']
        )
        
        # Set encrypted amount
        source.set_amount(float(data['amount']))
        
        # Set additional fields
        if 'start_date' in data:
            source.start_date = data['start_date']
        
        if 'end_date' in data:
            source.end_date = data['end_date']
        
        # Save to database
        db_session.add(source)
        db_session.commit()
        
        # Log creation
        audit_service.log_income_source_access(source.id, 'CREATE')
        
        return jsonify({
            'success': True,
            'message': 'Income source created successfully',
            'source_id': source.id,
            'request_id': g.get('request_id')
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating income source: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# DEBT ACCOUNTS ENDPOINTS
# =====================================================

@secure_financial_bp.route('/api/secure/debt-accounts', methods=['GET'])
@require_https
@require_authentication
@audit_financial_access
def get_debt_accounts():
    """Get user's encrypted debt accounts"""
    try:
        user_id = g.user_id
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Get debt accounts
        accounts = db_session.query(EncryptedDebtAccount).filter(
            EncryptedDebtAccount.user_id == user_id,
            EncryptedDebtAccount.is_active == True
        ).all()
        
        # Log access for each account
        for account in accounts:
            audit_service.log_debt_account_access(account.id, 'READ')
        
        return jsonify({
            'success': True,
            'data': [account.to_dict() for account in accounts],
            'request_id': g.get('request_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting debt accounts: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@secure_financial_bp.route('/api/secure/debt-accounts', methods=['POST'])
@require_https
@require_authentication
@validate_financial_data
@audit_financial_access
def create_debt_account():
    """Create new encrypted debt account"""
    try:
        user_id = g.user_id
        data = request.get_json()
        db_session = get_db_session()
        audit_service = get_audit_service()
        
        # Create new debt account
        account = EncryptedDebtAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_name=data['account_name'],
            account_type=data['account_type']
        )
        
        # Set encrypted values
        account.set_balance(float(data['balance']))
        
        if 'minimum_payment' in data:
            account.set_minimum_payment(float(data['minimum_payment']))
        
        # Set non-sensitive fields
        if 'interest_rate' in data:
            account.interest_rate = data['interest_rate']
        
        if 'due_date' in data:
            account.due_date = data['due_date']
        
        # Save to database
        db_session.add(account)
        db_session.commit()
        
        # Log creation
        audit_service.log_debt_account_access(account.id, 'CREATE')
        
        return jsonify({
            'success': True,
            'message': 'Debt account created successfully',
            'account_id': account.id,
            'request_id': g.get('request_id')
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating debt account: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# AUDIT ENDPOINTS
# =====================================================

@secure_financial_bp.route('/api/secure/audit-logs', methods=['GET'])
@require_https
@require_authentication
def get_audit_logs():
    """Get user's audit logs"""
    try:
        user_id = g.user_id
        audit_service = get_audit_service()
        
        # Get days parameter
        days = request.args.get('days', 30, type=int)
        
        # Get audit logs
        logs = audit_service.get_user_audit_logs(user_id, days)
        
        return jsonify({
            'success': True,
            'data': logs,
            'request_id': g.get('request_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@secure_financial_bp.route('/api/secure/audit-summary', methods=['GET'])
@require_https
@require_authentication
def get_audit_summary():
    """Get user's audit summary"""
    try:
        user_id = g.user_id
        audit_service = get_audit_service()
        
        # Get days parameter
        days = request.args.get('days', 30, type=int)
        
        # Get audit summary
        summary = audit_service.get_financial_audit_summary(user_id, days)
        
        return jsonify({
            'success': True,
            'data': summary,
            'request_id': g.get('request_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting audit summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 