from flask import Blueprint, jsonify, request, g, current_app, render_template, session, redirect
from backend.services.health_correlation_service import HealthCorrelationService
from backend.models.user import User
from backend.models.user_health_checkin import UserHealthCheckin
from backend.models.health_spending_correlation import HealthSpendingCorrelation
from datetime import datetime, timedelta

health_insights_bp = Blueprint('health_insights', __name__, url_prefix='/api')

# Utility: get current user (mock for now)
def get_current_user():
    # In production, use session or token
    SessionLocal = current_app.config.get('DATABASE_SESSION')
    if SessionLocal:
        with SessionLocal() as db:
            return db.query(User).first()
    return None

# --- Mock Data for Example Responses ---
MOCK_INSIGHTS = {
    "wellness_score": 7.2,
    "week_change": 0.8,
    "spending_impact": -45,
    "insights": [
        {
            "type": "stress_spending",
            "correlation": 0.73,
            "message": "High stress weeks show 35% more impulse spending",
            "recommendation": "Try 10min meditation before shopping",
            "potential_savings": 200
        },
        {
            "type": "activity_savings",
            "correlation": -0.58,
            "message": "More activity = 18% less stress-related spending",
            "recommendation": "Aim for 30min walk 3x/week",
            "potential_savings": 120
        }
    ]
}

MOCK_TRENDS = {
    "trends": [
        {"date": "2025-06-01", "wellness_score": 6.5, "spending": 320},
        {"date": "2025-06-08", "wellness_score": 7.0, "spending": 290},
        {"date": "2025-06-15", "wellness_score": 7.2, "spending": 275}
    ]
}

MOCK_CORRELATIONS = {
    "correlations": {
        "stress_spending": 0.73,
        "activity_spending": -0.58,
        "relationship_spending": -0.41,
        "mindfulness_spending": -0.67
    },
    "details": [
        {"type": "stress_spending", "correlation": 0.73, "impact": "+35% impulse spending"},
        {"type": "activity_spending", "correlation": -0.58, "impact": "-18% stress spending"}
    ]
}

MOCK_RECOMMENDATIONS = {
    "recommendations": [
        {"area": "stress", "tip": "Try 10min meditation before shopping"},
        {"area": "activity", "tip": "Aim for 30min walk 3x/week"},
        {"area": "mindfulness", "tip": "Pause and breathe before purchases"}
    ]
}

MOCK_PREDICTIONS = {
    "predicted_spending": 250,
    "confidence": 0.82,
    "message": "If you maintain your current wellness, you could save $50 next week."
}

# --- API Endpoints ---

@health_insights_bp.route('/user/health-summary', methods=['GET'])
def health_summary():
    """API endpoint for dashboard summary data"""
    # Mock data for now - replace with real HealthCorrelationService calls
    return jsonify({
        "wellness_score": 7.2,
        "week_change": 0.8,
        "spending_impact": -45,
        "insights": [
            {
                "type": "stress_spending",
                "correlation": 0.73,
                "message": "High stress weeks show 35% more impulse spending"
            },
            {
                "type": "exercise_health",
                "correlation": -0.65,
                "message": "Active weeks reduce health spending by 20%"
            }
        ]
    })

@health_insights_bp.route('/user/health-insights', methods=['GET'])
def health_insights():
    return jsonify(MOCK_INSIGHTS)

@health_insights_bp.route('/user/wellness-score', methods=['GET'])
def wellness_score():
    return jsonify({"wellness_score": MOCK_INSIGHTS["wellness_score"], "week_change": MOCK_INSIGHTS["week_change"]})

@health_insights_bp.route('/user/health-predictions', methods=['GET'])
def health_predictions():
    return jsonify(MOCK_PREDICTIONS)

@health_insights_bp.route('/health/correlations', methods=['GET'])
def health_correlations():
    """API endpoint for correlation data"""
    return jsonify({
        "correlations": {
            "stress_spending": 0.73,
            "exercise_health_spending": -0.65,
            "mindfulness_impulse_spending": -0.58
        }
    })

@health_insights_bp.route('/health/trends', methods=['GET'])
def health_trends():
    return jsonify(MOCK_TRENDS)

@health_insights_bp.route('/health/analyze', methods=['POST'])
def analyze_health():
    # In a real implementation, trigger analysis and return status/result
    return jsonify({"status": "Analysis started", "timestamp": datetime.utcnow().isoformat()})

@health_insights_bp.route('/health/recommendations', methods=['GET'])
def health_recommendations():
    return jsonify(MOCK_RECOMMENDATIONS)

def user_completed_health_onboarding():
    """Check if the user has completed the health onboarding process."""
    user_id = session.get('user_id')
    if not user_id:
        return False
    
    # This is a placeholder. In a real implementation, you would check a flag
    # in the user's profile or a dedicated onboarding status table.
    # For now, we'll assume the onboarding service has a method for this.
    
    # Example using a mock or a future service method:
    # onboarding_status = current_app.onboarding_service.get_onboarding_status(user_id)
    # return onboarding_status.get('health_onboarding_completed', False)
    
    # For the purpose of this example, we'll check if a session flag exists.
    # In a real app, this would be more robust.
    return session.get('health_onboarding_completed', False)

@health_insights_bp.route('/dashboard', methods=['GET'])
def health_dashboard():
    """Render the health-finance dashboard"""
    if not user_completed_health_onboarding():
        return redirect('/api/health/onboarding')
    return render_template('health_dashboard.html')

# --- Health Onboarding Routes ---

@health_insights_bp.route('/onboarding', methods=['GET'])
def health_onboarding():
    """Render the health onboarding flow"""
    return render_template('health_onboarding.html')

@health_insights_bp.route('/onboarding/step/<int:step>', methods=['GET'])
def onboarding_step(step):
    """Handle individual onboarding steps"""
    if step < 1 or step > 4:
        return jsonify({'error': 'Invalid step'}), 400
    
    # In a real implementation, you'd load step-specific data
    step_data = {
        'step': step,
        'progress': (step / 4) * 100
    }
    
    return jsonify(step_data)

@health_insights_bp.route('/onboarding/checkin', methods=['POST'])
def save_onboarding_checkin():
    """Save the first health check-in from onboarding"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = [
            'relationships_rating', 'stress_level', 
            'energy_level', 'mood_rating'
        ]
        
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # In a real implementation, save to database
        # For now, return success
        return jsonify({
            'message': 'Check-in saved successfully',
            'step': 3
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@health_insights_bp.route('/onboarding/complete', methods=['POST'])
def complete_onboarding():
    """Complete the onboarding process"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'goal' not in data:
            return jsonify({'error': 'Goal selection required'}), 400
        
        # In a real implementation:
        # 1. Save user preferences and goals
        # 2. Set up reminder schedule
        # 3. Update user profile with onboarding completion
        # 4. Initialize health tracking preferences
        
        onboarding_summary = {
            'goal': data.get('goal'),
            'reminder_frequency': data.get('reminder_frequency', 'weekly'),
            'reminder_day': data.get('reminder_day', 'monday'),
            'commitment': data.get('commitment', False),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # In a real implementation, you would set a persistent flag in your database.
        # For this example, we'll set a session variable.
        session['health_onboarding_completed'] = True
        
        return jsonify({
            'message': 'Onboarding completed successfully',
            'summary': onboarding_summary,
            'redirect_url': '/api/dashboard'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@health_insights_bp.route('/onboarding/status', methods=['GET'])
def onboarding_status():
    """Check if user has completed onboarding"""
    # In a real implementation, check user's onboarding status
    return jsonify({
        'completed': False,  # Mock - would check database
        'current_step': 1,
        'can_skip': True
    }) 