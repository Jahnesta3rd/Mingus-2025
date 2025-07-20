"""
Financial Questionnaire Routes
Handles simplified financial assessment for users who choose "Keep It Brief"
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app
from loguru import logger
import json
from datetime import datetime
from typing import Dict, Any
from backend.models.financial_questionnaire_submission import FinancialQuestionnaireSubmission
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Message
from sqlalchemy import func

financial_questionnaire_bp = Blueprint('financial_questionnaire', __name__)

# Initialize rate limiter (add to app factory in production)
limiter = Limiter(key_func=get_remote_address)

@financial_questionnaire_bp.route('/questionnaire', methods=['GET'])
def show_questionnaire():
    """Display the financial questionnaire form"""
    try:
        return render_template('financial_questionnaire.html')
    except Exception as e:
        logger.error(f"Error rendering financial questionnaire: {str(e)}")
        return jsonify({'error': 'Failed to load questionnaire'}), 500

@financial_questionnaire_bp.route('/questionnaire', methods=['POST'])
@limiter.limit('5 per minute')
def submit_questionnaire():
    """Process financial questionnaire submission"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['monthly_income', 'monthly_expenses', 'current_savings', 'total_debt', 'risk_tolerance']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Calculate financial health metrics
        financial_health = calculate_financial_health(data)
        
        # Store persistent record
        session_db = current_app.config['DATABASE_SESSION']()
        try:
            submission = FinancialQuestionnaireSubmission(
                user_id=user_id,
                monthly_income=data['monthly_income'],
                monthly_expenses=data['monthly_expenses'],
                current_savings=data['current_savings'],
                total_debt=data['total_debt'],
                risk_tolerance=data['risk_tolerance'],
                financial_goals=data.get('financial_goals', []),
                financial_health_score=financial_health['score'],
                financial_health_level=financial_health['level'],
                recommendations=financial_health['recommendations'],
                submitted_at=datetime.utcnow()
            )
            session_db.add(submission)
            session_db.commit()
        except Exception as e:
            session_db.rollback()
            logger.error(f"Failed to save questionnaire submission: {e}")
        finally:
            session_db.close()
        
        # Store in session for results page
        session['questionnaire_results'] = financial_health
        
        # Email results to user
        try:
            user_email = session.get('user_email')
            if user_email and hasattr(current_app, 'mail'):
                msg = Message(
                    subject="Your Mingus Financial Health Results",
                    recipients=[user_email],
                    body=f"Your score: {financial_health['score']}\nLevel: {financial_health['level']}\nRecommendations: {financial_health['recommendations']}"
                )
                current_app.mail.send(msg)
        except Exception as e:
            logger.warning(f"Failed to send email: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Questionnaire submitted successfully',
            'financial_health': financial_health
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting questionnaire: {str(e)}")
        return jsonify({'error': 'Failed to submit questionnaire'}), 500

@financial_questionnaire_bp.route('/questionnaire/results', methods=['GET'])
def show_results():
    """Display financial questionnaire results"""
    try:
        results = session.get('questionnaire_results')
        if not results:
            return jsonify({'error': 'No results found'}), 404
        
        return render_template('financial_questionnaire_results.html', results=results)
    except Exception as e:
        logger.error(f"Error rendering questionnaire results: {str(e)}")
        return jsonify({'error': 'Failed to load results'}), 500

@financial_questionnaire_bp.route('/questionnaire/history', methods=['GET'])
def questionnaire_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    session_db = current_app.config['DATABASE_SESSION']()
    try:
        submissions = session_db.query(FinancialQuestionnaireSubmission).filter_by(user_id=user_id).order_by(FinancialQuestionnaireSubmission.submitted_at.desc()).all()
        return jsonify([s.to_dict() for s in submissions])
    finally:
        session_db.close()

@financial_questionnaire_bp.route('/admin/analytics', methods=['GET'])
def admin_analytics():
    # Example: count brief vs deep, average score, most common goals
    session_db = current_app.config['DATABASE_SESSION']()
    try:
        total = session_db.query(FinancialQuestionnaireSubmission).count()
        avg_score = session_db.query(func.avg(FinancialQuestionnaireSubmission.financial_health_score)).scalar()
        # ... more analytics ...
        return jsonify({'total': total, 'avg_score': avg_score})
    finally:
        session_db.close()

def calculate_financial_health(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate financial health score and generate recommendations
    
    Args:
        data: Questionnaire response data
        
    Returns:
        Dictionary containing score, level, and recommendations
    """
    monthly_income = float(data['monthly_income'])
    monthly_expenses = float(data['monthly_expenses'])
    current_savings = float(data['current_savings'])
    total_debt = float(data['total_debt'])
    risk_tolerance = int(data['risk_tolerance'])
    financial_goals = data.get('financial_goals', [])
    
    # Calculate key ratios
    debt_to_income = total_debt / monthly_income if monthly_income > 0 else 0
    savings_to_expenses = current_savings / monthly_expenses if monthly_expenses > 0 else 0
    monthly_savings_rate = (monthly_income - monthly_expenses) / monthly_income if monthly_income > 0 else 0
    
    # Calculate financial health score (0-100)
    score = 0
    
    # Savings rate (0-25 points)
    if monthly_savings_rate >= 0.2:
        score += 25
    elif monthly_savings_rate >= 0.1:
        score += 20
    elif monthly_savings_rate >= 0.05:
        score += 15
    elif monthly_savings_rate >= 0:
        score += 10
    
    # Emergency fund (0-25 points)
    if savings_to_expenses >= 6:
        score += 25
    elif savings_to_expenses >= 3:
        score += 20
    elif savings_to_expenses >= 1:
        score += 15
    elif savings_to_expenses >= 0.5:
        score += 10
    
    # Debt management (0-25 points)
    if debt_to_income <= 0.2:
        score += 25
    elif debt_to_income <= 0.3:
        score += 20
    elif debt_to_income <= 0.4:
        score += 15
    elif debt_to_income <= 0.5:
        score += 10
    
    # Income stability (0-25 points)
    if monthly_income >= 8000:
        score += 25
    elif monthly_income >= 6000:
        score += 22
    elif monthly_income >= 5000:
        score += 18
    elif monthly_income >= 3500:
        score += 15
    elif monthly_income >= 2500:
        score += 10
    elif monthly_income >= 1500:
        score += 5
    
    # Determine health level
    if score >= 80:
        level = "Excellent"
        color = "#10b981"
    elif score >= 60:
        level = "Good"
        color = "#3b82f6"
    elif score >= 40:
        level = "Fair"
        color = "#f59e0b"
    else:
        level = "Needs Improvement"
        color = "#ef4444"
    
    # Generate recommendations
    recommendations = generate_recommendations(
        score, level, monthly_income, monthly_expenses, 
        current_savings, total_debt, debt_to_income, 
        savings_to_expenses, monthly_savings_rate, 
        risk_tolerance, financial_goals
    )
    
    return {
        'score': score,
        'level': level,
        'color': color,
        'recommendations': recommendations,
        'metrics': {
            'debt_to_income_ratio': round(debt_to_income, 2),
            'savings_to_expenses_ratio': round(savings_to_expenses, 2),
            'monthly_savings_rate': round(monthly_savings_rate * 100, 1),
            'monthly_disposable_income': monthly_income - monthly_expenses
        }
    }

def generate_recommendations(score: int, level: str, monthly_income: float, 
                           monthly_expenses: float, current_savings: float, 
                           total_debt: float, debt_to_income: float, 
                           savings_to_expenses: float, monthly_savings_rate: float,
                           risk_tolerance: int, financial_goals: list) -> list:
    """
    Generate personalized financial recommendations
    
    Args:
        score: Financial health score
        level: Financial health level
        monthly_income: Monthly income
        monthly_expenses: Monthly expenses
        current_savings: Current savings
        total_debt: Total debt
        debt_to_income: Debt-to-income ratio
        savings_to_expenses: Savings-to-expenses ratio
        monthly_savings_rate: Monthly savings rate
        risk_tolerance: Risk tolerance (1-5)
        financial_goals: List of financial goals
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Emergency fund recommendations
    if savings_to_expenses < 3:
        target_emergency = monthly_expenses * 3
        recommendations.append({
            'category': 'Emergency Fund',
            'priority': 'high',
            'title': 'Build Your Emergency Fund',
            'description': f'You should aim to save ${target_emergency:,.0f} for emergencies (3 months of expenses).',
            'action': f'Save ${(target_emergency - current_savings) / 12:,.0f} per month to reach this goal in 12 months.'
        })
    
    # Debt management recommendations
    if debt_to_income > 0.3:
        recommendations.append({
            'category': 'Debt Management',
            'priority': 'high',
            'title': 'Reduce Your Debt',
            'description': f'Your debt-to-income ratio is {debt_to_income:.1%}, which is above the recommended 30%.',
            'action': 'Focus on paying off high-interest debt first, starting with credit cards.'
        })
    
    # Savings rate recommendations
    if monthly_savings_rate < 0.1:
        recommendations.append({
            'category': 'Savings',
            'priority': 'medium',
            'title': 'Increase Your Savings Rate',
            'description': f'You\'re currently saving {monthly_savings_rate:.1%} of your income.',
            'action': 'Aim to save at least 10% of your income. Consider the 50/30/20 rule: 50% needs, 30% wants, 20% savings.'
        })
    
    # Investment recommendations
    if savings_to_expenses >= 3 and monthly_savings_rate >= 0.1:
        if risk_tolerance >= 3:
            recommendations.append({
                'category': 'Investing',
                'priority': 'medium',
                'title': 'Start Investing',
                'description': 'You have a solid financial foundation and moderate risk tolerance.',
                'action': 'Consider opening a retirement account (401k/IRA) or starting with index funds.'
            })
        else:
            recommendations.append({
                'category': 'Investing',
                'priority': 'low',
                'title': 'Consider Conservative Investments',
                'description': 'You have a conservative risk tolerance but good savings habits.',
                'action': 'Look into high-yield savings accounts, CDs, or conservative bond funds.'
            })
    
    # Goal-specific recommendations
    if 'emergency_fund' in financial_goals and savings_to_expenses < 6:
        recommendations.append({
            'category': 'Goals',
            'priority': 'high',
            'title': 'Emergency Fund Goal',
            'description': 'You want to build an emergency fund but aren\'t quite there yet.',
            'action': 'Set up automatic transfers to a dedicated savings account.'
        })
    
    if 'debt_payoff' in financial_goals and total_debt > 0:
        recommendations.append({
            'category': 'Goals',
            'priority': 'high',
            'title': 'Debt Payoff Strategy',
            'description': 'You want to pay off debt. Consider the debt snowball or avalanche method.',
            'action': 'List all debts by interest rate and focus on the highest-rate debt first.'
        })
    
    if 'investment' in financial_goals and risk_tolerance >= 3:
        recommendations.append({
            'category': 'Goals',
            'priority': 'medium',
            'title': 'Investment Strategy',
            'description': 'You want to start investing and have moderate risk tolerance.',
            'action': 'Consider a robo-advisor or target-date fund to get started easily.'
        })
    
    # Income optimization
    if monthly_income < 4000:
        recommendations.append({
            'category': 'Income',
            'priority': 'medium',
            'title': 'Increase Your Income',
            'description': 'Your income is below the median household income.',
            'action': 'Consider asking for a raise, looking for higher-paying opportunities, or developing new skills.'
        })
    
    return recommendations 