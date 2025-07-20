from flask import Blueprint, request, jsonify, session
from datetime import datetime
from supabase import create_client
import uuid

financial_profile_bp = Blueprint('financial_profile', __name__)

# --- Security/Encryption stubs ---
def encrypt_data(data):
    # TODO: Implement real encryption
    return data

def decrypt_data(data):
    # TODO: Implement real decryption
    return data

def require_user(user_id=None):
    # Access control: ensure user is logged in and matches user_id if provided
    session_user = session.get('user_id')
    if not session_user or (user_id and user_id != session_user):
        return False
    return True

# --- Helper: Validate financial profile input ---
def validate_profile(data):
    errors = []
    income = data.get('income')
    expenses = data.get('expenses')
    debt = data.get('debt', 0)
    emergency_fund = data.get('emergency_fund', 0)
    if not data.get('user_id'):
        errors.append('user_id is required.')
    if not income or income <= 0:
        errors.append('Income must be greater than $0.')
    if expenses is None or expenses < 0:
        errors.append('Expenses must be $0 or greater.')
    if income and expenses and expenses > income:
        errors.append('Expenses exceed income.')
    if debt < 0:
        errors.append('Debt cannot be negative.')
    if expenses and emergency_fund < expenses * 3:
        errors.append('Emergency fund is less than 3 months of expenses.')
    # Add more as needed
    return errors

# --- POST /api/financial-profile ---
@financial_profile_bp.route('/api/financial-profile', methods=['POST'])
def save_financial_profile():
    data = request.get_json()
    errors = validate_profile(data)
    if errors:
        return jsonify({'errors': errors}), 400
    if not require_user(data.get('user_id')):
        return jsonify({'error': 'Unauthorized'}), 403
    supabase = create_client()
    encrypted = encrypt_data(data)
    # Upsert profile
    supabase.table('user_financial_profiles').upsert([encrypted], on_conflict=['user_id'])
    # Trigger cash flow forecast recalculation
    # (Assume daily_cashflow is a function you can call)
    # daily_cashflow.recalculate_for_user(data['user_id'])
    return jsonify({'success': True})

# --- GET /api/financial-profile/<user_id> ---
@financial_profile_bp.route('/api/financial-profile/<user_id>', methods=['GET'])
def get_financial_profile(user_id):
    if not require_user(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    supabase = create_client()
    row = supabase.table('user_financial_profiles').select('*').eq('user_id', user_id).single().execute().data
    if not row:
        return jsonify({'error': 'Profile not found'}), 404
    decrypted = decrypt_data(row)
    return jsonify({'profile': decrypted})

# --- POST /api/financial-profile/calculate-health-score ---
@financial_profile_bp.route('/api/financial-profile/calculate-health-score', methods=['POST'])
def calculate_health_score():
    data = request.get_json()
    income = data.get('income', 0)
    expenses = data.get('expenses', 0)
    debt = data.get('debt', 0)
    emergency_fund = data.get('emergency_fund', 0)
    savings = income - expenses
    dti = (debt / income) if income else 0
    emergency_months = (emergency_fund / expenses) if expenses else 0
    savings_rate = (savings / income) if income else 0
    # Score logic
    score = 100
    if dti > 0.4: score -= 30
    if emergency_months < 3: score -= 30
    if income < expenses: score -= 20
    if savings_rate < 0.1: score -= 10
    # Add more business rules as needed
    return jsonify({
        'score': max(0, min(100, score)),
        'debt_to_income': dti,
        'emergency_fund_months': emergency_months,
        'savings_rate': savings_rate
    })

# --- PUT /api/financial-profile/goals ---
@financial_profile_bp.route('/api/financial-profile/goals', methods=['PUT'])
def update_goals():
    data = request.get_json()
    user_id = data.get('user_id')
    if not require_user(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    goals = data.get('goals', [])
    supabase = create_client()
    now = datetime.utcnow().isoformat()
    upserted = []
    for goal in goals:
        if not goal.get('goal_name') or not goal.get('target_amount') or not goal.get('target_date'):
            continue
        if goal.get('target_amount') < 1:
            continue
        if goal.get('target_date') < datetime.utcnow().date().isoformat():
            continue
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
    if upserted:
        supabase.table('user_financial_goals').upsert(upserted, on_conflict=['id'])
    return jsonify({'success': True})

# --- DELETE /api/financial-profile/goals/<goal_id> ---
@financial_profile_bp.route('/api/financial-profile/goals/<goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    user_id = session.get('user_id')
    if not require_user(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    supabase = create_client()
    # Only delete if goal belongs to user
    goal = supabase.table('user_financial_goals').select('*').eq('id', goal_id).single().execute().data
    if not goal or goal['user_id'] != user_id:
        return jsonify({'error': 'Not found or unauthorized'}), 404
    supabase.table('user_financial_goals').delete().eq('id', goal_id).execute()
    return jsonify({'success': True}) 