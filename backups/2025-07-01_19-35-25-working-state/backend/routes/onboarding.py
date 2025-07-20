"""
Onboarding routes blueprint
"""

from flask import Blueprint, request, jsonify, session, current_app, render_template, redirect, url_for
from loguru import logger
from supabase import create_client
import uuid
from datetime import datetime
from backend.utils.field_mapping import (
    validate_expense_data, 
    normalize_expense_data, 
    calculate_monthly_totals,
    to_monthly_amount
)
from sqlalchemy import text

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/start', methods=['POST'])
def start_onboarding():
    """Start onboarding process for a user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Create onboarding record
        onboarding_record = current_app.onboarding_service.create_onboarding_record({
            'user_id': user_id,
            'current_step': 'welcome'
        })
        
        if onboarding_record:
            return jsonify({
                'success': True,
                'message': 'Onboarding started successfully',
                'onboarding_record': onboarding_record
            }), 201
        else:
            return jsonify({'error': 'Failed to start onboarding'}), 500
            
    except Exception as e:
        logger.error(f"Start onboarding error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/profile', methods=['POST'])
def create_profile():
    """Create user profile during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create user profile with all new fields
        profile_data = {
            'user_id': user_id,
            # Basic Info
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'age_range': data.get('age_range'),
            'gender': data.get('gender'),
            
            # Location & Household
            'zip_code': data.get('zip_code'),
            'location_state': data.get('location_state'),
            'location_city': data.get('location_city'),
            'household_size': data.get('household_size'),
            'dependents': data.get('dependents'),
            'relationship_status': data.get('relationship_status'),
            
            # Income & Employment
            'monthly_income': data.get('monthly_income'),
            'income_frequency': data.get('income_frequency'),
            'primary_income_source': data.get('primary_income_source'),
            'employment_status': data.get('employment_status'),
            'industry': data.get('industry'),
            'job_title': data.get('job_title'),
            'naics_code': data.get('naics_code'),
            
            # Financial Status
            'current_savings': data.get('current_savings'),
            'current_debt': data.get('current_debt'),
            'credit_score_range': data.get('credit_score_range')
        }
        
        # Validate required fields
        required_fields = [
            'first_name', 'last_name', 'age_range', 'zip_code', 
            'location_state', 'location_city', 'household_size', 
            'relationship_status', 'employment_status', 'industry', 
            'job_title', 'monthly_income', 'primary_income_source',
            'current_savings', 'current_debt', 'credit_score_range'
        ]
        
        missing_fields = [field for field in required_fields if not profile_data.get(field)]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Validate zip code format
        import re
        zip_pattern = re.compile(r'^\d{5}(-\d{4})?$')
        if not zip_pattern.match(profile_data['zip_code']):
            return jsonify({
                'error': 'Invalid zip code format. Please use format: 12345 or 12345-6789'
            }), 400
        
        profile = current_app.onboarding_service.create_user_profile(profile_data)
        
        if profile:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='profile',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'message': 'Profile created successfully',
                'profile': profile
            }), 201
        else:
            return jsonify({'error': 'Failed to create profile'}), 500
            
    except Exception as e:
        logger.error(f"Create profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/goals', methods=['POST'])
def set_goals():
    """Set financial goals during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update profile with goals
        goals_data = {
            'primary_goal': data.get('primary_goal'),
            'goal_amount': data.get('goal_amount'),
            'goal_timeline_months': data.get('goal_timeline_months')
        }
        
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, goals_data)
        
        if updated_profile:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='goals',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'message': 'Goals set successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile with goals'}), 500
            
    except Exception as e:
        logger.error(f"Set goals error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/preferences', methods=['POST'])
def set_preferences():
    """Set user preferences during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update profile with preferences
        preferences_data = {
            'risk_tolerance': data.get('risk_tolerance'),
            'investment_experience': data.get('investment_experience')
        }
        
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, preferences_data)
        
        if updated_profile:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='preferences',
                is_completed=True,
                responses=data
            )
            
            return jsonify({
                'success': True,
                'message': 'Preferences set successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile with preferences'}), 500
            
    except Exception as e:
        logger.error(f"Set preferences error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/expenses', methods=['POST'])
def set_expenses():
    """Set expense categories during onboarding"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        expense_categories = data.get('expense_categories', {})
        
        # Update profile with expense categories
        updated_profile = current_app.onboarding_service.update_user_profile(user_id, {
            'expense_categories': expense_categories
        })
        
        if updated_profile:
            return jsonify({
                'success': True,
                'message': 'Expense categories updated successfully',
                'profile': updated_profile
            }), 200
        else:
            return jsonify({'error': 'Failed to update expense categories'}), 500
            
    except Exception as e:
        logger.error(f"Set expenses error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/complete', methods=['POST'])
def complete_onboarding():
    """Complete onboarding process"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        
        # Mark profile as complete
        current_app.onboarding_service.update_user_profile(user_id, {'is_complete': True})
        
        # Update onboarding progress to complete
        current_app.onboarding_service.update_onboarding_progress(
            user_id=user_id,
            step_name='complete',
            is_completed=True,
            responses=data
        )
        
        return jsonify({
            'success': True,
            'message': 'Onboarding completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Complete onboarding error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/progress', methods=['GET'])
def get_onboarding_progress():
    """Get onboarding progress for current user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        profile = current_app.onboarding_service.get_user_profile(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'progress': progress,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Get onboarding progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/progress/<user_id>', methods=['GET'])
def get_user_onboarding_progress(user_id):
    """Get onboarding progress for a specific user (admin only)"""
    try:
        # Check if current user is admin or the same user
        current_user_id = session.get('user_id')
        
        if not current_user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # For now, allow users to see their own progress
        # In production, you might want to add admin checks
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        progress = current_app.onboarding_service.get_onboarding_progress(user_id)
        profile = current_app.onboarding_service.get_user_profile(user_id)
        
        if progress:
            return jsonify({
                'success': True,
                'progress': progress,
                'profile': profile
            }), 200
        else:
            return jsonify({'error': 'Onboarding progress not found'}), 404
            
    except Exception as e:
        logger.error(f"Get user onboarding progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/step/<step_name>', methods=['POST'])
def update_step(step_name):
    """Update a specific onboarding step"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        
        # Update onboarding progress for the step
        updated_progress = current_app.onboarding_service.update_onboarding_progress(
            user_id=user_id,
            step_name=step_name,
            is_completed=data.get('completed', True),
            responses=data.get('responses', {})
        )
        
        if updated_progress:
            return jsonify({
                'success': True,
                'message': f'Step {step_name} updated successfully',
                'progress': updated_progress
            }), 200
        else:
            return jsonify({'error': 'Failed to update step'}), 500
            
    except Exception as e:
        logger.error(f"Update step error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/onboarding/financial-profile', methods=['GET'])
def financial_profile():
    """Render the financial profile onboarding step (Step 3)"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('onboarding.login'))
    # Check onboarding progress
    progress = get_onboarding_progress(user_id)
    if progress.get('financial_profile_completed'):
        return redirect(url_for('onboarding.next_step'))
    # Render the template with progress info
    return render_template('financial_profile.html', step=3, total_steps=8, progress=progress)

@onboarding_bp.route('/api/financial-profile', methods=['POST'])
def save_financial_profile():
    """Save financial profile data from onboarding step 3"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    # Save to Supabase (pseudo-code, replace with your actual Supabase logic)
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    # Upsert incomes
    for inc in data.get('incomes', []):
        supabase.table('user_income_due_dates').upsert({
            'user_id': user_id,
            'income_type': inc.get('income_type'),
            'amount': inc.get('amount'),
            'frequency': inc.get('frequency'),
            'start_date': inc.get('start_date'),
            'stability': inc.get('stability')
        }, on_conflict=['user_id', 'income_type', 'start_date']).execute()
    # Update onboarding profile summary
    supabase.table('user_onboarding_profiles').upsert({
        'user_id': user_id,
        'monthly_income': data.get('total_monthly_income')
    }, on_conflict=['user_id']).execute()
    # Mark onboarding progress
    update_onboarding_progress(user_id, step_name='financial_profile', is_completed=True, responses=data)
    return jsonify({'success': True})

@onboarding_bp.route('/onboarding/expense-profile', methods=['GET'])
def expense_profile():
    """Render the expense profile onboarding step (Step 4)"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('onboarding.login'))
    # Check onboarding progress
    progress = get_onboarding_progress(user_id)
    if progress < 3:
        return redirect(url_for('onboarding.financial_profile'))
    # Mark this as step 4 of 8
    return render_template('expense_profile.html', step=4, total_steps=8, progress=progress)

@onboarding_bp.route('/api/expense-profile', methods=['POST'])
def save_expense_profile():
    """Save expense profile data from onboarding step 4"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Validate expense data structure
        is_valid, errors = validate_expense_data(data)
        if not is_valid:
            return jsonify({'error': 'Invalid expense data', 'details': errors}), 400
        
        # Normalize the data
        normalized_data = normalize_expense_data(data)
        
        # Calculate monthly amounts for all expenses
        expenses = normalized_data.get('expenses', {})
        for field, value in expenses.items():
            if isinstance(value, dict) and 'amount' in value and 'frequency' in value:
                monthly_amount = to_monthly_amount(value['amount'], value['frequency'])
                value['monthly'] = monthly_amount
        
        # Calculate category totals
        totals = calculate_monthly_totals(normalized_data)
        
        # Save to Supabase with snake_case field names
        supabase = create_client()
        expense_row = {
            'user_id': user_id,
            'starting_balance': normalized_data.get('starting_balance', 0),
            'total_monthly_expenses': totals['total'],
            'essential_expenses_total': totals['essential'],
            'living_expenses_total': totals['living'],
            'debt_expenses_total': totals['debt'],
            'discretionary_expenses_total': totals['discretionary'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Process expense fields - already in snake_case format from frontend
        for field, val in expenses.items():
            if isinstance(val, dict):
                # Handle expense amount fields
                expense_row[field] = val.get('amount', 0)
                # Handle frequency and due date fields
                if field.endswith('_expense'):
                    base_field = field.replace('_expense', '')
                    expense_row[f"{base_field}_frequency"] = val.get('frequency', 'monthly')
                    expense_row[f"{base_field}_due_date"] = val.get('due_date', '')
                    expense_row[f"{base_field}_monthly"] = val.get('monthly', 0)
            else:
                # Handle text fields (like credit card names, loan names)
                expense_row[field] = val
        
        # Upsert into user_expense_items
        result = supabase.table('user_expense_items').upsert([expense_row], on_conflict=['user_id']).execute()
        
        if result.data:
            # Update onboarding progress
            update_onboarding_progress(user_id, step_name='expense_profile', is_completed=True, responses=normalized_data)
            return jsonify({
                'success': True,
                'message': 'Expense profile saved successfully',
                'data': result.data[0] if result.data else None,
                'totals': totals
            })
        else:
            return jsonify({'error': 'Failed to save expense profile'}), 500
            
    except Exception as e:
        logger.error(f"Save expense profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/onboarding/financial-goals', methods=['GET'])
def financial_goals():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('onboarding.login'))
    progress = get_onboarding_progress(user_id)
    if progress < 4:
        return redirect(url_for('onboarding.expense_profile'))
    # Fetch existing goals from Supabase
    supabase = create_client()
    goals = supabase.table('user_financial_goals').select('*').eq('user_id', user_id).execute().data or []
    return render_template('financial_goals.html', step=5, total_steps=8, progress=progress, goals=goals)

@onboarding_bp.route('/api/financial-goals', methods=['GET'])
def get_financial_goals():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    supabase = create_client()
    goals = supabase.table('user_financial_goals').select('*').eq('user_id', user_id).execute().data or []
    return jsonify({'goals': goals})

@onboarding_bp.route('/api/financial-goals', methods=['POST'])
def save_financial_goals():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data or 'goals' not in data:
        return jsonify({'error': 'No goals provided'}), 400
    supabase = create_client()
    now = datetime.utcnow().isoformat()
    upserted = []
    for goal in data['goals']:
        goal_row = {
            'user_id': user_id,
            'goal_name': goal.get('goal_name'),
            'goal_category': goal.get('goal_category'),
            'target_amount': goal.get('target_amount'),
            'target_date': goal.get('target_date'),
            'current_progress': goal.get('current_progress'),
            'priority': goal.get('priority'),
            'created_at': goal.get('created_at', now),
            'updated_at': now,
            'id': goal.get('id') or str(uuid.uuid4())
        }
        upserted.append(goal_row)
    supabase.table('user_financial_goals').upsert(upserted, on_conflict=['id'])
    update_onboarding_progress(user_id, 5)
    return jsonify({'success': True})

# Helper: Get onboarding progress (pseudo-code)
def get_onboarding_progress(user_id):
    # Replace with your actual logic
    return {
        'registration_completed': True,
        'financial_profile_completed': False,
        # ... other steps ...
    }

# Helper: Update onboarding progress (pseudo-code)
def update_onboarding_progress(user_id, step_name, is_completed, responses):
    # Replace with your actual logic
    pass

# Update main onboarding router to include this step
@onboarding_bp.route('/onboarding/next', methods=['GET'])
def next_step():
    user_id = session.get('user_id')
    progress = get_onboarding_progress(user_id)
    if not progress.get('financial_profile_completed'):
        return redirect(url_for('onboarding.financial_profile'))
    # ... logic for next step ...
    return redirect(url_for('onboarding.dashboard'))

# Conditional access: Redirect incomplete users from dashboard
@onboarding_bp.route('/dashboard', methods=['GET'])
def dashboard():
    user_id = session.get('user_id')
    progress = get_onboarding_progress(user_id)
    if not progress.get('financial_profile_completed'):
        return redirect(url_for('onboarding.financial_profile'))
    # ... render dashboard ...
    return render_template('dashboard.html')

# Update onboarding flow navigation logic
@onboarding_bp.route('/onboarding/next-step', methods=['GET'])
def onboarding_next_step():
    user_id = session.get('user_id')
    progress = get_onboarding_progress(user_id)
    if progress == 4:
        return redirect(url_for('onboarding.financial_goals'))
    # ... existing logic for other steps ...
    return redirect(url_for('dashboard'))

@onboarding_bp.route('/choice', methods=['GET'])
def show_onboarding_choice():
    """Display the onboarding choice page (brief vs detailed setup)"""
    try:
        return render_template('onboarding_choice.html')
    except Exception as e:
        logger.error(f"Error rendering onboarding choice: {str(e)}")
        return jsonify({'error': 'Failed to load onboarding choice'}), 500

@onboarding_bp.route('/progress/steps', methods=['GET'])
def get_onboarding_step_status():
    """Get onboarding step status JSON for current user (for React tracker)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        step_status = current_app.onboarding_service.get_onboarding_step_status(user_id)
        if step_status is not None:
            return jsonify({'success': True, 'step_status': step_status}), 200
        else:
            return jsonify({'error': 'Step status not found'}), 404
    except Exception as e:
        logger.error(f"Get onboarding step status error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Phone Verification Endpoints

@onboarding_bp.route('/send-verification', methods=['POST'])
def send_verification():
    """Send verification code to phone number"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data or 'phone_number' not in data:
            return jsonify({'error': 'Phone number is required'}), 400
        
        phone_number = data['phone_number']
        
        # Get verification service from app context
        verification_service = getattr(current_app, 'verification_service', None)
        if not verification_service:
            return jsonify({'error': 'Verification service not available'}), 500
        
        # Send verification code
        result = verification_service.send_verification_code(user_id, phone_number)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result.get('message', 'Verification code sent successfully'),
                'expires_at': result.get('expires_at'),
                'resend_count': result.get('resend_count', 1),
                'next_resend_delay': result.get('next_resend_delay'),
                'alternative_contact_message': result.get('alternative_contact_message'),
                'can_change_phone': result.get('can_change_phone', False)
            }), 200
        else:
            response_data = {
                'success': False,
                'error': result['error']
            }
            
            # Add additional context for smart resend
            if 'cooldown_remaining' in result:
                response_data['cooldown_remaining'] = result['cooldown_remaining']
                response_data['resend_count'] = result.get('resend_count', 0)
            
            if result.get('suggest_alternative'):
                response_data['suggest_alternative'] = True
                
            return jsonify(response_data), 400
            
    except Exception as e:
        logger.error(f"Send verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/verify-phone', methods=['POST'])
def verify_phone():
    """Verify phone number with verification code"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        phone_number = data.get('phone_number')
        verification_code = data.get('verification_code')
        
        if not phone_number or not verification_code:
            return jsonify({'error': 'Phone number and verification code are required'}), 400
        
        # Get verification service from app context
        verification_service = getattr(current_app, 'verification_service', None)
        if not verification_service:
            return jsonify({'error': 'Verification service not available'}), 500
        
        # Verify the code
        result = verification_service.verify_code(user_id, phone_number, verification_code)
        
        if result['success']:
            # Update onboarding progress
            current_app.onboarding_service.update_onboarding_progress(
                user_id=user_id,
                step_name='verification',
                is_completed=True,
                responses={'phone_number': phone_number, 'verified_at': datetime.utcnow().isoformat()}
            )
            
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            response_data = {
                'success': False,
                'error': result['error']
            }
            
            if 'remaining_attempts' in result:
                response_data['remaining_attempts'] = result['remaining_attempts']
            
            if result.get('suggest_alternative'):
                response_data['suggest_alternative'] = True
                
            return jsonify(response_data), 400
            
    except Exception as e:
        logger.error(f"Verify phone error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification code to phone number"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data or 'phone_number' not in data:
            return jsonify({'error': 'Phone number is required'}), 400
        
        phone_number = data['phone_number']
        
        # Get verification service from app context
        verification_service = getattr(current_app, 'verification_service', None)
        if not verification_service:
            return jsonify({'error': 'Verification service not available'}), 500
        
        # Resend verification code
        result = verification_service.resend_verification_code(user_id, phone_number)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result.get('message', 'Verification code resent successfully'),
                'expires_at': result.get('expires_at'),
                'resend_count': result.get('resend_count', 1),
                'next_resend_delay': result.get('next_resend_delay'),
                'alternative_contact_message': result.get('alternative_contact_message'),
                'can_change_phone': result.get('can_change_phone', False)
            }), 200
        else:
            response_data = {
                'success': False,
                'error': result['error']
            }
            
            # Add additional context for smart resend
            if 'cooldown_remaining' in result:
                response_data['cooldown_remaining'] = result['cooldown_remaining']
                response_data['resend_count'] = result.get('resend_count', 0)
            
            if result.get('suggest_alternative'):
                response_data['suggest_alternative'] = True
                
            return jsonify(response_data), 400
            
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/verification-status', methods=['GET'])
def get_verification_status():
    """Get current verification status and attempt history"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        phone_number = request.args.get('phone_number')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Get verification service from app context
        verification_service = getattr(current_app, 'verification_service', None)
        if not verification_service:
            return jsonify({'error': 'Verification service not available'}), 500
        
        # Get verification status
        result = verification_service.get_verification_status(user_id, phone_number)
        
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Get verification status error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/change-phone', methods=['POST'])
def change_phone_number():
    """Change phone number for verification"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        old_phone = data.get('old_phone_number')
        new_phone = data.get('new_phone_number')
        
        if not old_phone or not new_phone:
            return jsonify({'error': 'Both old and new phone numbers are required'}), 400
        
        # Get verification service from app context
        verification_service = getattr(current_app, 'verification_service', None)
        if not verification_service:
            return jsonify({'error': 'Verification service not available'}), 500
        
        # Change phone number
        result = verification_service.change_phone_number(user_id, old_phone, new_phone)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'new_phone': result.get('new_phone')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Change phone number error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/verification-analytics', methods=['GET'])
def get_verification_analytics():
    """Get verification analytics for the current user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get verification service from app context
        verification_service = getattr(current_app, 'verification_service', None)
        if not verification_service:
            return jsonify({'error': 'Verification service not available'}), 500
        
        # Get analytics data from database
        query = text("""
            SELECT event_type, event_data, created_at
            FROM verification_analytics 
            WHERE user_id = :user_id
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        
        result = current_app.config['DATABASE_SESSION'].execute(query, {'user_id': user_id})
        analytics_data = []
        
        for row in result:
            analytics_data.append({
                'event_type': row.event_type,
                'event_data': row.event_data,
                'created_at': row.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'analytics': analytics_data
        }), 200
            
    except Exception as e:
        logger.error(f"Get verification analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/api/job-security-score', methods=['POST'])
def get_job_security_score():
    """Run job security ML models using onboarding data and return score/recommendations"""
    try:
        data = request.get_json()
        industry = data.get('industry')
        job_title = data.get('job_title')
        employer = data.get('employer')
        location = data.get('location')

        # Import ML assessors (assume these are available in backend.ml)
        from backend.ml.industry_risk_assessment import IndustryRiskAssessor
        from backend.ml.job_security_predictor import JobSecurityPredictor

        # Map to NAICS code
        assessor = IndustryRiskAssessor()
        naics_code = assessor.map_industry_to_naics(industry, job_title)
        industry_profile = assessor.get_industry_risk_profile(naics_code) if naics_code else None

        # Prepare company/user data
        company_data = {'industry': industry, 'employer': employer, 'location': location}
        user_data = {'job_title': job_title, 'industry': industry}

        # Run job security prediction (simulate for now)
        predictor = JobSecurityPredictor()
        job_security = predictor.predict(user_data, company_data)

        return jsonify({
            'naics_code': naics_code,
            'industry_risk': industry_profile.risk_level.value if industry_profile else None,
            'job_security_score': job_security.get('overall_risk'),
            'risk_level': job_security.get('risk_level'),
            'layoff_probability_6m': job_security.get('layoff_probability_6m'),
            'recommendations': industry_profile.recommendations if industry_profile else []
        }), 200
    except Exception as e:
        logger.error(f"Job security score error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/api/financial-overview', methods=['GET'])
def get_financial_overview():
    """Return unified financial overview for dashboard card"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        # Import or use existing services/models
        from backend.analytics.business_intelligence import UserFinancialProfile
        from backend.utils.field_mapping import to_monthly_amount

        # Fetch user profile (assume one-to-one)
        profile = UserFinancialProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'error': 'Financial profile not found'}), 404

        # Gather metrics
        monthly_income = float(profile.monthly_income or 0)
        monthly_expenses = float((profile.monthly_fixed_expenses or 0) + (profile.monthly_variable_expenses or 0))
        current_savings = float(profile.current_savings or 0)
        current_debt = float(profile.current_debt or 0)

        # Emergency fund status
        emergency_fund_months = profile.emergency_fund_coverage() if hasattr(profile, 'emergency_fund_coverage') else (current_savings / monthly_expenses if monthly_expenses > 0 else 0)

        # Financial health score (assume method exists or set to 0)
        financial_health_score = getattr(profile, 'financial_health_score', None)
        if financial_health_score is None and hasattr(profile, 'calculate_financial_health_score'):
            financial_health_score = profile.calculate_financial_health_score()
        if financial_health_score is None:
            # Fallback: simple score based on emergency fund, debt-to-income, etc.
            dti = (current_debt / monthly_income) if monthly_income > 0 else 1
            ef_score = min(emergency_fund_months / 6, 1)  # 6+ months = full score
            financial_health_score = round((0.5 * ef_score + 0.5 * (1 - dti)) * 100)

        return jsonify({
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'current_savings': current_savings,
            'current_debt': current_debt,
            'emergency_fund_months': round(emergency_fund_months, 2),
            'financial_health_score': financial_health_score
        }), 200
    except Exception as e:
        logger.error(f"Financial overview error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_bp.route('/api/insights', methods=['GET'])
def get_insights():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    # TODO: Aggregate real insights from financial, job security, and goals models
    insights = [
        {"title": "Increase Emergency Fund", "description": "Aim for at least 6 months of expenses in your emergency fund."},
        {"title": "Reduce Debt", "description": "Focus on paying off high-interest credit cards first."},
        {"title": "Review Your Budget", "description": "Track your spending to find areas for savings."}
    ]
    return jsonify({"insights": insights}), 200 