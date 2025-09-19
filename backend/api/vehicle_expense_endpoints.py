#!/usr/bin/env python3
"""
Vehicle Expense API Endpoints for Mingus Personal Finance App
Provides endpoints for vehicle expense categorization and analysis

Endpoints:
- POST /api/vehicle-expenses/categorize - Categorize a single expense
- POST /api/vehicle-expenses/categorize-batch - Categorize multiple expenses
- GET /api/vehicle-expenses/summary - Get vehicle expense summary
- GET /api/vehicle-expenses/analysis - Get detailed analysis
- POST /api/vehicle-expenses/compare-maintenance - Compare maintenance costs
- GET /api/vehicle-expenses/insights - Get spending insights
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Import the vehicle expense categorizer
from backend.services.vehicle_expense_categorizer import VehicleExpenseCategorizer, VehicleExpenseType

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
vehicle_expense_api = Blueprint('vehicle_expense_api', __name__)

# Initialize categorizer
categorizer = VehicleExpenseCategorizer()

@vehicle_expense_api.route('/api/vehicle-expenses/categorize', methods=['POST'])
def categorize_expense():
    """
    Categorize a single expense to determine if it's vehicle-related
    
    Request body:
    {
        "expense_id": "string",
        "description": "string",
        "merchant": "string",
        "amount": number,
        "date": "YYYY-MM-DD",
        "user_email": "string"
    }
    
    Returns:
    {
        "success": boolean,
        "categorization": {
            "expense_id": "string",
            "vehicle_id": number|null,
            "expense_type": "string",
            "confidence_score": number,
            "matched_keywords": [string],
            "matched_patterns": [string],
            "suggested_vehicle": "string|null",
            "is_maintenance_related": boolean,
            "predicted_cost_range": [number, number]|null
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['expense_id', 'description', 'amount', 'user_email']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Categorize the expense
        match = categorizer.categorize_expense(data, data['user_email'])
        
        # Save categorization if it's vehicle-related
        if match.confidence_score > 0.3:
            categorizer.save_expense_categorization(match, data['user_email'], data)
        
        # Convert to dictionary for JSON response
        categorization = {
            'expense_id': match.expense_id,
            'vehicle_id': match.vehicle_id,
            'expense_type': match.expense_type.value,
            'confidence_score': match.confidence_score,
            'matched_keywords': match.matched_keywords,
            'matched_patterns': match.matched_patterns,
            'suggested_vehicle': match.suggested_vehicle,
            'is_maintenance_related': match.is_maintenance_related,
            'predicted_cost_range': match.predicted_cost_range
        }
        
        return jsonify({
            'success': True,
            'categorization': categorization
        })
        
    except Exception as e:
        logger.error(f"Error categorizing expense: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@vehicle_expense_api.route('/api/vehicle-expenses/categorize-batch', methods=['POST'])
def categorize_expenses_batch():
    """
    Categorize multiple expenses in batch
    
    Request body:
    {
        "expenses": [
            {
                "expense_id": "string",
                "description": "string",
                "merchant": "string",
                "amount": number,
                "date": "YYYY-MM-DD"
            }
        ],
        "user_email": "string"
    }
    
    Returns:
    {
        "success": boolean,
        "categorizations": [
            {
                "expense_id": "string",
                "vehicle_id": number|null,
                "expense_type": "string",
                "confidence_score": number,
                "is_vehicle_related": boolean
            }
        ],
        "summary": {
            "total_processed": number,
            "vehicle_related": number,
            "maintenance_related": number
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'expenses' not in data or 'user_email' not in data:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        expenses = data['expenses']
        user_email = data['user_email']
        
        if not isinstance(expenses, list):
            return jsonify({'success': False, 'error': 'Expenses must be a list'}), 400
        
        categorizations = []
        vehicle_related_count = 0
        maintenance_related_count = 0
        
        for expense in expenses:
            # Add user_email to each expense
            expense['user_email'] = user_email
            
            # Categorize the expense
            match = categorizer.categorize_expense(expense, user_email)
            
            # Save categorization if it's vehicle-related
            if match.confidence_score > 0.3:
                categorizer.save_expense_categorization(match, user_email, expense)
                vehicle_related_count += 1
                
                if match.is_maintenance_related:
                    maintenance_related_count += 1
            
            # Add to results
            categorizations.append({
                'expense_id': match.expense_id,
                'vehicle_id': match.vehicle_id,
                'expense_type': match.expense_type.value,
                'confidence_score': match.confidence_score,
                'is_vehicle_related': match.confidence_score > 0.3,
                'is_maintenance_related': match.is_maintenance_related
            })
        
        return jsonify({
            'success': True,
            'categorizations': categorizations,
            'summary': {
                'total_processed': len(expenses),
                'vehicle_related': vehicle_related_count,
                'maintenance_related': maintenance_related_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error categorizing expenses batch: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@vehicle_expense_api.route('/api/vehicle-expenses/summary', methods=['GET'])
def get_vehicle_expense_summary():
    """
    Get comprehensive vehicle expense summary for user
    
    Query parameters:
    - user_email: User's email address
    - months: Number of months to analyze (default: 12)
    
    Returns:
    {
        "success": boolean,
        "summary": {
            "total_expenses": number,
            "total_count": number,
            "average_monthly": number,
            "months_analyzed": number
        },
        "expenses_by_type": {
            "maintenance": {"count": number, "total": number},
            "fuel": {"count": number, "total": number},
            ...
        },
        "expenses_by_vehicle": {
            "2020 Honda Civic": {"count": number, "total": number},
            ...
        },
        "maintenance_predictions": {
            "total_comparisons": number,
            "accuracy_breakdown": {
                "excellent": number,
                "good": number,
                "fair": number,
                "poor": number
            }
        }
    }
    """
    try:
        user_email = request.args.get('user_email')
        months = int(request.args.get('months', 12))
        
        if not user_email:
            return jsonify({'success': False, 'error': 'user_email parameter required'}), 400
        
        # Get summary from categorizer
        summary = categorizer.get_vehicle_expense_summary(user_email, months)
        
        if not summary:
            return jsonify({'success': False, 'error': 'Failed to generate summary'}), 500
        
        return jsonify({
            'success': True,
            **summary
        })
        
    except Exception as e:
        logger.error(f"Error getting vehicle expense summary: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@vehicle_expense_api.route('/api/vehicle-expenses/analysis', methods=['GET'])
def get_vehicle_expense_analysis():
    """
    Get detailed vehicle expense analysis with insights
    
    Query parameters:
    - user_email: User's email address
    - months: Number of months to analyze (default: 12)
    
    Returns:
    {
        "success": boolean,
        "analysis": {
            "spending_trends": {
                "monthly_averages": [number],
                "trend_direction": "increasing|decreasing|stable"
            },
            "cost_efficiency": {
                "maintenance_vs_predicted": number,
                "fuel_efficiency": number,
                "insurance_optimization": string
            },
            "recommendations": [string],
            "alerts": [string]
        }
    }
    """
    try:
        user_email = request.args.get('user_email')
        months = int(request.args.get('months', 12))
        
        if not user_email:
            return jsonify({'success': False, 'error': 'user_email parameter required'}), 400
        
        # Get basic summary first
        summary = categorizer.get_vehicle_expense_summary(user_email, months)
        
        if not summary:
            return jsonify({'success': False, 'error': 'Failed to generate analysis'}), 500
        
        # Generate analysis insights
        analysis = _generate_expense_analysis(summary, months)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting vehicle expense analysis: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@vehicle_expense_api.route('/api/vehicle-expenses/compare-maintenance', methods=['POST'])
def compare_maintenance_costs():
    """
    Compare actual maintenance costs to predictions
    
    Request body:
    {
        "vehicle_id": number,
        "expense_id": "string",
        "actual_cost": number,
        "service_type": "string"
    }
    
    Returns:
    {
        "success": boolean,
        "comparison": {
            "vehicle_id": number,
            "service_type": "string",
            "actual_cost": number,
            "predicted_cost": number,
            "variance_percentage": number,
            "prediction_accuracy": "excellent|good|fair|poor",
            "recommendation": "string"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        required_fields = ['vehicle_id', 'expense_id', 'actual_cost', 'service_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Compare maintenance costs
        comparison = categorizer.compare_maintenance_costs(
            data['vehicle_id'],
            data['expense_id'],
            data['actual_cost'],
            data['service_type']
        )
        
        if not comparison:
            return jsonify({'success': False, 'error': 'No prediction found for comparison'}), 404
        
        # Convert to dictionary for JSON response
        comparison_dict = {
            'vehicle_id': comparison.vehicle_id,
            'service_type': comparison.service_type,
            'actual_cost': comparison.actual_cost,
            'predicted_cost': comparison.predicted_cost,
            'variance_percentage': comparison.variance_percentage,
            'prediction_accuracy': comparison.prediction_accuracy,
            'recommendation': comparison.recommendation
        }
        
        return jsonify({
            'success': True,
            'comparison': comparison_dict
        })
        
    except Exception as e:
        logger.error(f"Error comparing maintenance costs: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@vehicle_expense_api.route('/api/vehicle-expenses/insights', methods=['GET'])
def get_vehicle_expense_insights():
    """
    Get personalized vehicle expense insights and recommendations
    
    Query parameters:
    - user_email: User's email address
    - months: Number of months to analyze (default: 12)
    
    Returns:
    {
        "success": boolean,
        "insights": {
            "spending_patterns": {
                "highest_category": "string",
                "monthly_variance": number,
                "seasonal_trends": [string]
            },
            "cost_optimization": {
                "potential_savings": number,
                "recommendations": [string],
                "maintenance_schedule": [string]
            },
            "predictive_alerts": [string],
            "budget_impact": {
                "monthly_impact": number,
                "annual_impact": number,
                "vs_budget": number
            }
        }
    }
    """
    try:
        user_email = request.args.get('user_email')
        months = int(request.args.get('months', 12))
        
        if not user_email:
            return jsonify({'success': False, 'error': 'user_email parameter required'}), 400
        
        # Get summary and generate insights
        summary = categorizer.get_vehicle_expense_summary(user_email, months)
        
        if not summary:
            return jsonify({'success': False, 'error': 'Failed to generate insights'}), 500
        
        # Generate personalized insights
        insights = _generate_personalized_insights(summary, user_email, months)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error getting vehicle expense insights: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@vehicle_expense_api.route('/api/vehicle-expenses/health', methods=['GET'])
def health_check():
    """Health check endpoint for vehicle expense categorization service"""
    return jsonify({
        'status': 'healthy',
        'service': 'vehicle_expense_categorization',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'expense_categorization': 'active',
            'vehicle_linking': 'active',
            'maintenance_comparison': 'active',
            'prediction_updates': 'active'
        }
    })

def _generate_expense_analysis(summary: Dict[str, Any], months: int) -> Dict[str, Any]:
    """Generate detailed expense analysis from summary data"""
    try:
        expenses_by_type = summary.get('expenses_by_type', {})
        total_expenses = summary.get('summary', {}).get('total_expenses', 0)
        
        # Calculate spending trends
        monthly_average = total_expenses / months if months > 0 else 0
        
        # Determine trend direction (simplified)
        trend_direction = "stable"
        if monthly_average > 0:
            # This would be more sophisticated in a real implementation
            trend_direction = "stable"
        
        # Calculate cost efficiency metrics
        maintenance_total = expenses_by_type.get('maintenance', {}).get('total', 0)
        fuel_total = expenses_by_type.get('fuel', {}).get('total', 0)
        insurance_total = expenses_by_type.get('insurance', {}).get('total', 0)
        
        # Generate recommendations
        recommendations = []
        if maintenance_total > monthly_average * 0.4:  # More than 40% of monthly average
            recommendations.append("Consider preventive maintenance to reduce unexpected repair costs")
        
        if fuel_total > monthly_average * 0.3:  # More than 30% of monthly average
            recommendations.append("Review fuel efficiency and consider carpooling or public transportation")
        
        if insurance_total > monthly_average * 0.2:  # More than 20% of monthly average
            recommendations.append("Shop around for better insurance rates")
        
        # Generate alerts
        alerts = []
        if total_expenses > monthly_average * 1.5:  # 50% above average
            alerts.append("Vehicle expenses are significantly above average this month")
        
        return {
            'spending_trends': {
                'monthly_averages': [monthly_average] * months,
                'trend_direction': trend_direction
            },
            'cost_efficiency': {
                'maintenance_vs_predicted': 0.0,  # Would calculate from actual data
                'fuel_efficiency': 0.0,  # Would calculate from actual data
                'insurance_optimization': "Consider shopping around" if insurance_total > 0 else "No insurance data"
            },
            'recommendations': recommendations,
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"Error generating expense analysis: {e}")
        return {}

def _generate_personalized_insights(summary: Dict[str, Any], user_email: str, months: int) -> Dict[str, Any]:
    """Generate personalized insights and recommendations"""
    try:
        expenses_by_type = summary.get('expenses_by_type', {})
        total_expenses = summary.get('summary', {}).get('total_expenses', 0)
        monthly_average = total_expenses / months if months > 0 else 0
        
        # Find highest spending category
        highest_category = "none"
        highest_amount = 0
        for category, data in expenses_by_type.items():
            if data.get('total', 0) > highest_amount:
                highest_amount = data.get('total', 0)
                highest_category = category
        
        # Calculate monthly variance (simplified)
        monthly_variance = 0.0  # Would calculate from actual monthly data
        
        # Generate cost optimization recommendations
        potential_savings = 0
        recommendations = []
        
        if expenses_by_type.get('maintenance', {}).get('total', 0) > monthly_average * 0.3:
            potential_savings += monthly_average * 0.1
            recommendations.append("Schedule regular maintenance to prevent costly repairs")
        
        if expenses_by_type.get('fuel', {}).get('total', 0) > monthly_average * 0.25:
            potential_savings += monthly_average * 0.05
            recommendations.append("Consider fuel-efficient driving habits or alternative transportation")
        
        if expenses_by_type.get('insurance', {}).get('total', 0) > monthly_average * 0.15:
            potential_savings += monthly_average * 0.08
            recommendations.append("Compare insurance quotes from multiple providers")
        
        # Generate maintenance schedule recommendations
        maintenance_schedule = []
        if expenses_by_type.get('maintenance', {}).get('count', 0) < 2:  # Less than 2 maintenance visits
            maintenance_schedule.append("Schedule oil change and inspection")
        
        if expenses_by_type.get('tires', {}).get('count', 0) == 0:
            maintenance_schedule.append("Check tire condition and pressure")
        
        # Generate predictive alerts
        predictive_alerts = []
        if total_expenses > monthly_average * 1.2:
            predictive_alerts.append("Vehicle expenses trending higher than usual")
        
        if expenses_by_type.get('maintenance', {}).get('count', 0) == 0 and months >= 6:
            predictive_alerts.append("No maintenance recorded in 6+ months - schedule service soon")
        
        return {
            'spending_patterns': {
                'highest_category': highest_category,
                'monthly_variance': monthly_variance,
                'seasonal_trends': []  # Would analyze seasonal patterns
            },
            'cost_optimization': {
                'potential_savings': potential_savings,
                'recommendations': recommendations,
                'maintenance_schedule': maintenance_schedule
            },
            'predictive_alerts': predictive_alerts,
            'budget_impact': {
                'monthly_impact': monthly_average,
                'annual_impact': monthly_average * 12,
                'vs_budget': 0.0  # Would compare to user's budget
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating personalized insights: {e}")
        return {}
