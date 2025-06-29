"""
Onboarding routes blueprint
"""

from flask import Blueprint, request, jsonify, session, current_app, render_template, redirect, url_for
from loguru import logger
from supabase import create_client
import uuid
from datetime import datetime

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
        
        # Create user profile
        profile_data = {
            'user_id': user_id,
            'monthly_income': data.get('monthly_income'),
            'income_frequency': data.get('income_frequency'),
            'primary_income_source': data.get('primary_income_source'),
            'age_range': data.get('age_range'),
            'location_state': data.get('location_state'),
            'location_city': data.get('location_city'),
            'household_size': data.get('household_size'),
            'employment_status': data.get('employment_status'),
            'current_savings': data.get('current_savings'),
            'current_debt': data.get('current_debt'),
            'credit_score_range': data.get('credit_score_range')
        }
        
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
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    # Save to Supabase (pseudo-code, replace with your actual supabase logic)
    supabase = create_client()
    expense_row = {
        'user_id': user_id,
        'starting_balance': data.get('startingBalance'),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    for field, val in data.get('expenses', {}).items():
        if isinstance(val, dict):
            expense_row[field] = val.get('amount')
            expense_row[f"{field.replace('Expense', '')}_frequency"] = val.get('frequency')
            expense_row[f"{field.replace('Expense', '')}_due_date"] = val.get('dueDate')
        else:
            expense_row[field] = val
    # Upsert into user_expense_items
    supabase.table('user_expense_items').upsert([expense_row], on_conflict=['user_id'])
    # Update onboarding progress
    update_onboarding_progress(user_id, 4)
    return jsonify({'success': True})

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