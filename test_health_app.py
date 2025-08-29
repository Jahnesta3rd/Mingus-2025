#!/usr/bin/env python3
"""
Simple Flask Test App for Health-to-Finance Features
Demonstrates the unique health-to-finance connection features
"""

from flask import Flask, jsonify, request, render_template_string
from datetime import datetime, date, timedelta
import json
import random

app = Flask(__name__)

# Mock data for demonstration
mock_health_data = {
    "user_1": {
        "checkins": [
            {
                "id": 1,
                "checkin_date": "2025-08-20",
                "physical_activity_minutes": 45,
                "physical_activity_level": "moderate",
                "relationships_rating": 8,
                "relationships_notes": "Had great conversations with family",
                "mindfulness_minutes": 20,
                "mindfulness_type": "meditation",
                "stress_level": 4,
                "energy_level": 7,
                "mood_rating": 8
            },
            {
                "id": 2,
                "checkin_date": "2025-08-13",
                "physical_activity_minutes": 30,
                "physical_activity_level": "low",
                "relationships_rating": 6,
                "relationships_notes": "Some tension with coworkers",
                "mindfulness_minutes": 10,
                "mindfulness_type": "breathing",
                "stress_level": 7,
                "energy_level": 5,
                "mood_rating": 6
            }
        ],
        "spending_data": [
            {"date": "2025-08-20", "category": "entertainment", "amount": 120},
            {"date": "2025-08-13", "category": "food", "amount": 85},
            {"date": "2025-08-06", "category": "entertainment", "amount": 150},
            {"date": "2025-07-30", "category": "food", "amount": 95}
        ]
    }
}

# Health check-in form HTML template
HEALTH_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mingus Health Check-in</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .form-content {
            padding: 40px;
        }
        .form-section {
            margin-bottom: 30px;
            padding: 25px;
            border-radius: 10px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
        }
        .section-title {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
        }
        .section-icon {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        .form-input, .form-select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-range {
            width: 100%;
            margin: 10px 0;
        }
        .range-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #666;
        }
        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            width: 100%;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        .progress-bar {
            background: #e1e5e9;
            height: 8px;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Health Check-in</h1>
            <p>Track your wellness and see how it connects to your financial health</p>
        </div>
        
        <div class="form-content">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            
            <form id="healthForm" onsubmit="submitForm(event)">
                <!-- Physical Activity Section -->
                <div class="form-section">
                    <div class="section-title">
                        <div class="section-icon">🏃</div>
                        Physical Activity
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label" for="physical_activity_minutes">
                                Activity Minutes Today
                            </label>
                            <input 
                                type="number" 
                                id="physical_activity_minutes" 
                                name="physical_activity_minutes"
                                class="form-input"
                                min="0" 
                                max="480"
                                placeholder="e.g., 30"
                                onchange="updateProgress()"
                            >
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="physical_activity_level">
                                Activity Level
                            </label>
                            <select id="physical_activity_level" name="physical_activity_level" class="form-select" onchange="updateProgress()">
                                <option value="">Select activity level</option>
                                <option value="low">Low</option>
                                <option value="moderate">Moderate</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Relationships Section -->
                <div class="form-section">
                    <div class="section-title">
                        <div class="section-icon">❤️</div>
                        Relationships & Social
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="relationships_rating">
                            How would you rate your relationships this week? (1-10)
                        </label>
                        <input 
                            type="range" 
                            id="relationships_rating" 
                            name="relationships_rating"
                            class="form-range"
                            min="1" 
                            max="10" 
                            value="5"
                            required
                            onchange="updateProgress()"
                        >
                        <div class="range-labels">
                            <span>1: Very Strained</span>
                            <span>10: Excellent</span>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="relationships_notes">
                            Notes about your relationships
                        </label>
                        <textarea 
                            id="relationships_notes" 
                            name="relationships_notes"
                            class="form-input"
                            rows="3"
                            placeholder="How are your relationships affecting your well-being?"
                            onchange="updateProgress()"
                        ></textarea>
                    </div>
                </div>

                <!-- Mindfulness Section -->
                <div class="form-section">
                    <div class="section-title">
                        <div class="section-icon">🧘‍♀️</div>
                        Mindfulness & Mental Health
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label" for="mindfulness_minutes">
                                Mindfulness Minutes Today
                            </label>
                            <input 
                                type="number" 
                                id="mindfulness_minutes" 
                                name="mindfulness_minutes"
                                class="form-input"
                                min="0" 
                                max="120"
                                placeholder="e.g., 15"
                                onchange="updateProgress()"
                            >
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="mindfulness_type">
                                Mindfulness Type
                            </label>
                            <select id="mindfulness_type" name="mindfulness_type" class="form-select" onchange="updateProgress()">
                                <option value="">Select type</option>
                                <option value="meditation">Meditation</option>
                                <option value="yoga">Yoga</option>
                                <option value="breathing">Breathing Exercises</option>
                                <option value="walking">Walking Meditation</option>
                                <option value="journaling">Journaling</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Wellness Metrics Section -->
                <div class="form-section">
                    <div class="section-title">
                        <div class="section-icon">📊</div>
                        Wellness Metrics
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label" for="stress_level">
                                Stress Level (1-10)
                            </label>
                            <input 
                                type="range" 
                                id="stress_level" 
                                name="stress_level"
                                class="form-range"
                                min="1" 
                                max="10" 
                                value="5"
                                required
                                onchange="updateProgress()"
                            >
                            <div class="range-labels">
                                <span>1: Very Low</span>
                                <span>10: Very High</span>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="energy_level">
                                Energy Level (1-10)
                            </label>
                            <input 
                                type="range" 
                                id="energy_level" 
                                name="energy_level"
                                class="form-range"
                                min="1" 
                                max="10" 
                                value="5"
                                required
                                onchange="updateProgress()"
                            >
                            <div class="range-labels">
                                <span>1: Very Low</span>
                                <span>10: Very High</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="mood_rating">
                            Mood Rating (1-10)
                        </label>
                        <input 
                            type="range" 
                            id="mood_rating" 
                            name="mood_rating"
                            class="form-range"
                            min="1" 
                            max="10" 
                            value="5"
                            required
                            onchange="updateProgress()"
                        >
                        <div class="range-labels">
                            <span>1: Very Poor</span>
                            <span>10: Excellent</span>
                        </div>
                    </div>
                </div>

                <button type="submit" class="submit-btn">
                    Submit Health Check-in
                </button>
            </form>
        </div>
    </div>

    <script>
        function updateProgress() {
            const form = document.getElementById('healthForm');
            const inputs = form.querySelectorAll('input, select, textarea');
            const filledInputs = Array.from(inputs).filter(input => {
                if (input.type === 'range') {
                    return input.value !== '5'; // Default value
                }
                return input.value.trim() !== '';
            });
            
            const progress = (filledInputs.length / inputs.length) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }

        function submitForm(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());
            
            // Convert string values to numbers where appropriate
            data.physical_activity_minutes = parseInt(data.physical_activity_minutes) || null;
            data.relationships_rating = parseInt(data.relationships_rating);
            data.mindfulness_minutes = parseInt(data.mindfulness_minutes) || null;
            data.stress_level = parseInt(data.stress_level);
            data.energy_level = parseInt(data.energy_level);
            data.mood_rating = parseInt(data.mood_rating);
            
            fetch('/api/health/checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                alert('Health check-in submitted successfully!');
                console.log('Success:', data);
            })
            .catch((error) => {
                alert('Error submitting check-in: ' + error);
                console.error('Error:', error);
            });
        }

        // Initialize progress
        updateProgress();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with health-to-finance feature overview"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mingus Health-to-Finance Features</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .feature { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
            .feature h3 { color: #333; }
            .test-link { display: inline-block; margin: 10px 5px; padding: 10px 20px; 
                        background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🧪 Health-to-Finance Connection Features Test</h1>
        
        <div class="feature">
            <h3>🏃‍♂️ 1. Weekly Check-in Form</h3>
            <p>Track physical activity, relationships, and mindfulness weekly</p>
            <a href="/api/health/demo" class="test-link">Test Demo Form</a>
            <a href="/api/health/checkin" class="test-link">Test Auth Form</a>
        </div>
        
        <div class="feature">
            <h3>💰 2. Health-Finance Correlations</h3>
            <p>Analyze connections between health data and spending patterns</p>
            <a href="/api/health/correlations" class="test-link">Test Correlations</a>
            <a href="/api/health/insights" class="test-link">Test Insights</a>
        </div>
        
        <div class="feature">
            <h3>❤️ 3. Relationship Status Impact</h3>
            <p>How relationships affect financial recommendations</p>
            <a href="/api/health/recommendations" class="test-link">Test Recommendations</a>
            <a href="/api/health/summary" class="test-link">Test Summary</a>
        </div>
        
        <div class="feature">
            <h3>🏃‍♀️ 4. Physical Activity Correlation</h3>
            <p>Correlation between physical activity and financial decisions</p>
            <a href="/api/health/patterns" class="test-link">Test Patterns</a>
            <a href="/api/health/wellness-score" class="test-link">Test Wellness Score</a>
        </div>
        
        <div class="feature">
            <h3>🧘‍♀️ 5. Mindfulness Tracking</h3>
            <p>Meditation and mindfulness integration with financial insights</p>
            <a href="/api/health/mindfulness" class="test-link">Test Mindfulness</a>
            <a href="/api/health/mindfulness/insights" class="test-link">Test Insights</a>
        </div>
        
        <div class="feature">
            <h3>📊 6. Health Check-in History</h3>
            <p>Track health check-in history and statistics</p>
            <a href="/api/health/checkin/history" class="test-link">Test History</a>
            <a href="/api/health/stats" class="test-link">Test Stats</a>
        </div>
        
        <div class="feature">
            <h3>🎯 7. Health Onboarding</h3>
            <p>Health onboarding and setup process</p>
            <a href="/api/health/onboarding" class="test-link">Test Onboarding</a>
            <a href="/api/health/onboarding/status" class="test-link">Test Status</a>
        </div>
    </body>
    </html>
    """

@app.route('/api/health/demo', methods=['GET'])
def demo_checkin_form():
    """Demo health check-in form (no authentication required)"""
    return HEALTH_FORM_HTML

@app.route('/api/health/checkin', methods=['GET'])
def checkin_form():
    """Health check-in form (would require authentication in real app)"""
    return jsonify({
        "error": "Authentication required",
        "message": "Please log in to access the health check-in form"
    }), 401

@app.route('/api/health/checkin', methods=['POST'])
def submit_health_checkin():
    """Submit health check-in data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['relationships_rating', 'stress_level', 'energy_level', 'mood_rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Simulate saving to database
        checkin_id = random.randint(1000, 9999)
        
        # Simulate health-finance correlation analysis
        correlations = analyze_health_finance_correlations(data)
        
        return jsonify({
            'success': True,
            'message': 'Health check-in submitted successfully',
            'checkin_id': checkin_id,
            'correlations': correlations,
            'insights': generate_health_insights(data)
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health/correlations', methods=['GET'])
def get_health_correlations():
    """Get health-spending correlations"""
    return jsonify({
        'correlations': [
            {
                'health_metric': 'stress_level',
                'spending_category': 'entertainment',
                'correlation_strength': 0.72,
                'correlation_direction': 'positive',
                'insight': 'Higher stress levels correlate with increased entertainment spending',
                'recommendation': 'Consider stress-reduction activities to manage impulse spending'
            },
            {
                'health_metric': 'physical_activity_minutes',
                'spending_category': 'healthcare',
                'correlation_strength': -0.65,
                'correlation_direction': 'negative',
                'insight': 'More physical activity correlates with lower healthcare spending',
                'recommendation': 'Maintain regular exercise routine for long-term health savings'
            },
            {
                'health_metric': 'relationships_rating',
                'spending_category': 'food',
                'correlation_strength': 0.58,
                'correlation_direction': 'positive',
                'insight': 'Better relationships correlate with increased food spending',
                'recommendation': 'Social dining is healthy - budget accordingly'
            }
        ]
    })

@app.route('/api/health/insights', methods=['GET'])
def get_health_insights():
    """Get health insights and analysis"""
    return jsonify({
        'insights': [
            {
                'type': 'stress_spending',
                'title': 'Stress-Induced Spending Pattern',
                'description': 'Your stress levels show a strong correlation with entertainment spending',
                'impact': 'high',
                'recommendation': 'Consider meditation or exercise when stressed instead of shopping'
            },
            {
                'type': 'activity_health',
                'title': 'Physical Activity Benefits',
                'description': 'Your physical activity correlates with better financial decisions',
                'impact': 'positive',
                'recommendation': 'Maintain your exercise routine for both health and financial benefits'
            },
            {
                'type': 'relationship_wellness',
                'title': 'Relationship Wellness Impact',
                'description': 'Your relationship satisfaction affects your overall financial well-being',
                'impact': 'medium',
                'recommendation': 'Invest time in relationships - it pays off financially too'
            }
        ]
    })

@app.route('/api/health/recommendations', methods=['GET'])
def get_health_recommendations():
    """Get relationship-based financial recommendations"""
    return jsonify({
        'recommendations': [
            {
                'category': 'relationship_investment',
                'title': 'Invest in Relationships',
                'description': 'Based on your relationship rating, consider allocating budget for social activities',
                'amount': 150,
                'frequency': 'monthly',
                'expected_return': 'improved_wellness'
            },
            {
                'category': 'stress_management',
                'title': 'Stress Management Budget',
                'description': 'Allocate funds for stress-reduction activities to prevent impulse spending',
                'amount': 100,
                'frequency': 'monthly',
                'expected_return': 'reduced_entertainment_spending'
            },
            {
                'category': 'physical_wellness',
                'title': 'Physical Activity Investment',
                'description': 'Invest in fitness activities to reduce long-term healthcare costs',
                'amount': 80,
                'frequency': 'monthly',
                'expected_return': 'lower_healthcare_costs'
            }
        ]
    })

@app.route('/api/health/summary', methods=['GET'])
def get_health_summary():
    """Get health summary including relationship metrics"""
    return jsonify({
        'summary': {
            'overall_wellness_score': 7.2,
            'stress_management': 'good',
            'physical_activity': 'moderate',
            'relationship_health': 'excellent',
            'mindfulness_practice': 'consistent',
            'financial_impact': 'positive',
            'recommendations': [
                'Continue your mindfulness practice - it correlates with better financial decisions',
                'Your relationship satisfaction is high - this supports good financial habits',
                'Consider increasing physical activity to further improve financial outcomes'
            ]
        }
    })

@app.route('/api/health/dashboard', methods=['GET'])
def get_health_dashboard():
    """Get health dashboard with relationship insights"""
    return jsonify({
        'dashboard': {
            'current_week': {
                'stress_level': 4,
                'energy_level': 7,
                'mood_rating': 8,
                'physical_activity_minutes': 45,
                'mindfulness_minutes': 20,
                'relationships_rating': 8
            },
            'trends': {
                'stress_trend': 'decreasing',
                'energy_trend': 'stable',
                'mood_trend': 'improving',
                'activity_trend': 'increasing'
            },
            'financial_correlations': {
                'entertainment_spending': 'correlated_with_stress',
                'healthcare_spending': 'inversely_correlated_with_activity',
                'food_spending': 'correlated_with_relationships'
            }
        }
    })

@app.route('/api/health/patterns', methods=['GET'])
def get_activity_patterns():
    """Get activity-based spending patterns"""
    return jsonify({
        'patterns': [
            {
                'activity_level': 'high',
                'spending_impact': 'reduced_impulse_spending',
                'healthcare_savings': 200,
                'recommendation': 'Maintain high activity levels for financial benefits'
            },
            {
                'activity_level': 'low',
                'spending_impact': 'increased_entertainment_spending',
                'healthcare_savings': -50,
                'recommendation': 'Increase physical activity to reduce stress spending'
            }
        ]
    })

@app.route('/api/health/wellness-score', methods=['GET'])
def get_wellness_score():
    """Get wellness score including physical activity"""
    return jsonify({
        'wellness_score': 7.8,
        'components': {
            'physical_activity': 8.0,
            'stress_management': 7.5,
            'relationship_health': 8.5,
            'mindfulness_practice': 7.0,
            'overall_mood': 8.0
        },
        'financial_impact': 'positive',
        'recommendations': [
            'Your wellness score is excellent and correlates with good financial habits',
            'Continue your current practices for sustained financial well-being'
        ]
    })

@app.route('/api/health/mindfulness', methods=['GET'])
def get_mindfulness_tracking():
    """Get mindfulness tracking and history"""
    return jsonify({
        'mindfulness_data': {
            'current_streak': 5,
            'total_sessions': 45,
            'average_minutes': 18,
            'preferred_type': 'meditation',
            'financial_correlation': 'reduced_impulse_spending'
        },
        'history': [
            {'date': '2025-08-20', 'minutes': 20, 'type': 'meditation'},
            {'date': '2025-08-19', 'minutes': 15, 'type': 'breathing'},
            {'date': '2025-08-18', 'minutes': 25, 'type': 'meditation'}
        ]
    })

@app.route('/api/health/mindfulness/insights', methods=['GET'])
def get_mindfulness_insights():
    """Get mindfulness-based financial insights"""
    return jsonify({
        'insights': [
            {
                'type': 'impulse_control',
                'title': 'Mindfulness Reduces Impulse Spending',
                'description': 'Your meditation practice correlates with 30% less impulse purchases',
                'financial_impact': 150,
                'recommendation': 'Continue daily meditation for financial discipline'
            },
            {
                'type': 'stress_spending',
                'title': 'Stress Management Through Mindfulness',
                'description': 'Mindfulness practice helps manage stress-related spending',
                'financial_impact': 200,
                'recommendation': 'Use breathing exercises before making purchases'
            }
        ]
    })

@app.route('/api/health/mindfulness/goals', methods=['GET'])
def get_mindfulness_goals():
    """Get mindfulness goals and progress"""
    return jsonify({
        'goals': [
            {
                'type': 'daily_meditation',
                'target_minutes': 20,
                'current_progress': 75,
                'financial_benefit': 'reduced_stress_spending'
            },
            {
                'type': 'weekly_sessions',
                'target_sessions': 7,
                'current_progress': 5,
                'financial_benefit': 'improved_decision_making'
            }
        ]
    })

@app.route('/api/health/checkin/history', methods=['GET'])
def get_checkin_history():
    """Get health check-in history"""
    return jsonify({
        'history': mock_health_data["user_1"]["checkins"],
        'summary': {
            'total_checkins': 2,
            'average_stress_level': 5.5,
            'average_energy_level': 6.0,
            'average_mood_rating': 7.0,
            'most_common_activity_level': 'moderate'
        }
    })

@app.route('/api/health/stats', methods=['GET'])
def get_health_stats():
    """Get health statistics and analytics"""
    return jsonify({
        'statistics': {
            'total_checkins': 2,
            'average_wellness_score': 7.2,
            'stress_trend': 'decreasing',
            'activity_trend': 'increasing',
            'relationship_trend': 'stable',
            'mindfulness_trend': 'improving'
        },
        'correlations': {
            'stress_spending_correlation': 0.72,
            'activity_healthcare_correlation': -0.65,
            'relationship_food_correlation': 0.58
        }
    })

@app.route('/api/health/checkin/latest', methods=['GET'])
def get_latest_checkin():
    """Get latest health check-in"""
    latest = mock_health_data["user_1"]["checkins"][0]
    return jsonify({
        'latest_checkin': latest
    })

@app.route('/api/health/onboarding', methods=['GET'])
def get_health_onboarding():
    """Get health onboarding flow"""
    return jsonify({
        'onboarding': {
            'current_step': 1,
            'total_steps': 3,
            'steps': [
                {'step': 1, 'title': 'Health Assessment', 'completed': True},
                {'step': 2, 'title': 'Goal Setting', 'completed': False},
                {'step': 3, 'title': 'First Check-in', 'completed': False}
            ]
        }
    })

@app.route('/api/health/onboarding/status', methods=['GET'])
def get_onboarding_status():
    """Get health onboarding status"""
    return jsonify({
        'status': 'in_progress',
        'progress': 33,
        'next_step': 'goal_setting'
    })

def analyze_health_finance_correlations(data):
    """Analyze health-finance correlations based on check-in data"""
    correlations = []
    
    # Stress level correlation with entertainment spending
    if data.get('stress_level', 5) > 6:
        correlations.append({
            'type': 'stress_entertainment',
            'strength': 'high',
            'description': 'High stress levels may lead to increased entertainment spending',
            'recommendation': 'Consider stress-reduction activities'
        })
    
    # Physical activity correlation with healthcare spending
    if data.get('physical_activity_minutes', 0) > 30:
        correlations.append({
            'type': 'activity_healthcare',
            'strength': 'positive',
            'description': 'Good physical activity correlates with lower healthcare costs',
            'recommendation': 'Maintain your exercise routine'
        })
    
    # Relationship rating correlation with food spending
    if data.get('relationships_rating', 5) > 7:
        correlations.append({
            'type': 'relationship_food',
            'strength': 'positive',
            'description': 'Good relationships correlate with social dining spending',
            'recommendation': 'Budget for social activities'
        })
    
    return correlations

def generate_health_insights(data):
    """Generate health insights based on check-in data"""
    insights = []
    
    # Stress management insight
    if data.get('stress_level', 5) > 6:
        insights.append({
            'category': 'stress_management',
            'message': 'Your stress level is elevated. Consider mindfulness practices.',
            'financial_impact': 'May reduce stress-related spending'
        })
    
    # Physical activity insight
    if data.get('physical_activity_minutes', 0) < 30:
        insights.append({
            'category': 'physical_activity',
            'message': 'Consider increasing physical activity for better health and financial outcomes.',
            'financial_impact': 'May reduce healthcare costs'
        })
    
    # Relationship insight
    if data.get('relationships_rating', 5) > 7:
        insights.append({
            'category': 'relationships',
            'message': 'Your relationships are strong - this supports good financial habits.',
            'financial_impact': 'Positive correlation with financial well-being'
        })
    
    return insights

if __name__ == '__main__':
    print("🧪 Starting Health-to-Finance Features Test Server")
    print("📍 Server running at: http://localhost:5002")
    print("🌐 Main page: http://localhost:5002/")
    print("🏥 Demo form: http://localhost:5002/api/health/demo")
    print("\n📋 Testing the following features:")
    print("  1. Weekly check-in form (physical activity, relationships, mindfulness)")
    print("  2. Health-finance correlations")
    print("  3. Relationship status impact on financial recommendations")
    print("  4. Physical activity correlation with financial decisions")
    print("  5. Mindfulness tracking integration")
    print("  6. Health check-in history and statistics")
    print("  7. Health onboarding process")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
