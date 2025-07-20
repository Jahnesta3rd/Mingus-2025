from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_UP
from flask import jsonify
import numpy as np
from backend.db import get_db

# --- Calculation Functions ---
def calculate_monthly_contribution_needed(target_amount, current_amount, target_date):
    today = date.today()
    if not target_date or target_date <= today:
        return None
    months = (target_date.year - today.year) * 12 + (target_date.month - today.month)
    if months <= 0:
        return None
    needed = Decimal(target_amount) - Decimal(current_amount)
    if needed <= 0:
        return Decimal('0.00')
    return (needed / months).quantize(Decimal('0.01'), rounding=ROUND_UP)

def analyze_goal_feasibility(user_income, user_expenses, goal_amount, timeframe_months):
    available = Decimal(user_income) - Decimal(user_expenses)
    if available <= 0:
        return {'feasible': False, 'reason': 'No available income'}
    monthly_needed = Decimal(goal_amount) / Decimal(timeframe_months)
    feasible = monthly_needed <= available * Decimal('0.3')
    return {
        'feasible': feasible,
        'monthly_needed': monthly_needed.quantize(Decimal('0.01')),
        'max_affordable': (available * Decimal('0.3')).quantize(Decimal('0.01')),
        'reason': None if feasible else 'Goal requires more than 30% of available income'
    }

def suggest_goal_adjustments(user_data, goal_data):
    available = Decimal(user_data['income']) - Decimal(user_data['expenses'])
    months = (goal_data['target_date'].year - date.today().year) * 12 + (goal_data['target_date'].month - date.today().month)
    if months <= 0:
        return {'suggestion': 'Extend your timeline'}
    monthly_needed = (Decimal(goal_data['target_amount']) - Decimal(goal_data['current_amount'])) / months
    max_affordable = available * Decimal('0.3')
    if monthly_needed > max_affordable:
        new_months = int((Decimal(goal_data['target_amount']) - Decimal(goal_data['current_amount'])) / max_affordable) + 1
        new_date = date.today() + relativedelta(months=new_months)
        return {
            'suggestion': 'Extend your timeline or reduce your goal amount',
            'recommended_target_date': new_date,
            'recommended_amount': (max_affordable * months + Decimal(goal_data['current_amount'])).quantize(Decimal('0.01'))
        }
    return {'suggestion': 'Goal is achievable'}

def calculate_goal_stress_impact(goal_progress, user_stress_levels):
    if not goal_progress or not user_stress_levels:
        return None
    progress_dict = {d: p for d, p in goal_progress}
    stress_dict = {d: s for d, s in user_stress_levels}
    common_dates = set(progress_dict.keys()) & set(stress_dict.keys())
    if not common_dates:
        return None
    progress_vals = [progress_dict[d] for d in common_dates]
    stress_vals = [stress_dict[d] for d in common_dates]
    if len(progress_vals) < 2:
        return None
    corr = np.corrcoef(progress_vals, stress_vals)[0, 1]
    return {'correlation': float(corr)}

# --- Service Functions ---
def setup_goals_service():
    # Implement onboarding GET/POST logic
    pass

def get_goals_dashboard(user):
    db = get_db()
    goals = db.fetch_all('SELECT * FROM user_financial_goals WHERE user_id = %s', (user.id,))
    # Optionally join with progress, cashflow, health, etc.
    return jsonify({'goals': [dict(g) for g in goals]})

def add_goal_service(user, data):
    db = get_db()
    # Validate and insert new goal
    # ...
    return jsonify({'status': 'success'})

def update_goal_service(user, goal_id, data):
    db = get_db()
    # Validate and update goal
    # ...
    return jsonify({'status': 'success'})

def record_contribution_service(user, goal_id, data):
    db = get_db()
    # Validate and insert contribution
    # ...
    return jsonify({'status': 'success'})

def analyze_goal_progress_service(user):
    db = get_db()
    # Fetch goals, progress, health checkins, correlate
    # ...
    return jsonify({'analysis': 'not_implemented'}) 