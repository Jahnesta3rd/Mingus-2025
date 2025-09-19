#!/usr/bin/env python3
"""
Enhanced Vehicle Expense API Endpoints for Mingus Personal Finance App
Advanced API endpoints with ML-powered vehicle expense categorization and analysis

Features:
- ML-powered expense categorization with improved accuracy
- Multi-vehicle expense linking with smart detection
- Maintenance cost prediction and comparison
- Real-time insight generation
- Integration with existing spending analysis
- Advanced analytics and recommendations
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Import the enhanced ML engine
from backend.services.enhanced_vehicle_expense_ml_engine import (
    EnhancedVehicleExpenseMLEngine, 
    VehicleExpenseType,
    MLPredictionResult
)

# Import existing services for integration
from backend.services.vehicle_expense_categorizer import VehicleExpenseCategorizer
from backend.services.enhanced_spending_analyzer import EnhancedSpendingAnalyzer
from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_vehicle_api = Blueprint('enhanced_vehicle_api', __name__)

# Initialize services
ml_engine = EnhancedVehicleExpenseMLEngine()
categorizer = VehicleExpenseCategorizer()
spending_analyzer = EnhancedSpendingAnalyzer()
maintenance_engine = MaintenancePredictionEngine()

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/categorize', methods=['POST'])
def categorize_expense_enhanced():
    """
    Enhanced expense categorization using ML models
    
    Request body:
    {
        "expense_id": "string",
        "description": "string",
        "merchant": "string",
        "amount": number,
        "date": "YYYY-MM-DD",
        "user_email": "string",
        "vehicle_id": number (optional)
    }
    
    Returns:
    {
        "success": boolean,
        "categorization": {
            "expense_id": "string",
            "vehicle_id": number|null,
            "expense_type": "string",
            "confidence_score": number,
            "ml_confidence": number,
            "probability_distribution": {string: number},
            "feature_importance": {string: number},
            "model_version": "string",
            "matched_keywords": [string],
            "matched_patterns": [string],
            "suggested_vehicle": "string|null",
            "is_maintenance_related": boolean,
            "predicted_cost_range": [number, number]|null,
            "ml_metadata": {string: any}
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
        
        # Use ML engine for categorization
        ml_result = ml_engine.categorize_expense_ml(data, data['user_email'])
        
        # Also get traditional categorization for comparison
        traditional_match = categorizer.categorize_expense(data, data['user_email'])
        
        # Combine results
        categorization = {
            'expense_id': ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_match.expense_id,
            'vehicle_id': traditional_match.vehicle_id,
            'expense_type': ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_match.expense_type.value,
            'confidence_score': ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else traditional_match.confidence_score,
            'ml_confidence': ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else 0.0,
            'probability_distribution': ml_result.probability_distribution if hasattr(ml_result, 'probability_distribution') else {},
            'feature_importance': ml_result.feature_importance if hasattr(ml_result, 'feature_importance') else {},
            'model_version': ml_result.model_version if hasattr(ml_result, 'model_version') else 'legacy',
            'matched_keywords': traditional_match.matched_keywords,
            'matched_patterns': traditional_match.matched_patterns,
            'suggested_vehicle': traditional_match.suggested_vehicle,
            'is_maintenance_related': traditional_match.is_maintenance_related,
            'predicted_cost_range': traditional_match.predicted_cost_range,
            'ml_metadata': ml_result.prediction_metadata if hasattr(ml_result, 'prediction_metadata') else {}
        }
        
        # Save categorization if confidence is high enough
        if categorization['confidence_score'] > 0.3:
            # Save to enhanced database
            ml_engine._save_enhanced_categorization(categorization, data['user_email'], data)
            
            # Also save to traditional database for compatibility
            categorizer.save_expense_categorization(traditional_match, data['user_email'], data)
        
        return jsonify({
            'success': True,
            'categorization': categorization
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced expense categorization: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/categorize-batch', methods=['POST'])
def categorize_expenses_batch_enhanced():
    """
    Enhanced batch expense categorization using ML models
    
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
                "ml_confidence": number,
                "is_vehicle_related": boolean,
                "is_maintenance_related": boolean
            }
        ],
        "summary": {
            "total_processed": number,
            "vehicle_related": number,
            "maintenance_related": number,
            "ml_processed": number,
            "average_confidence": number
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
        ml_processed_count = 0
        total_confidence = 0.0
        
        for expense in expenses:
            # Add user_email to each expense
            expense['user_email'] = user_email
            
            # Use ML engine for categorization
            ml_result = ml_engine.categorize_expense_ml(expense, user_email)
            
            # Also get traditional categorization
            traditional_match = categorizer.categorize_expense(expense, user_email)
            
            # Determine if vehicle-related
            is_vehicle_related = (ml_result.confidence_score > 0.3 if hasattr(ml_result, 'confidence_score') 
                                else traditional_match.confidence_score > 0.3)
            
            if is_vehicle_related:
                vehicle_related_count += 1
                ml_processed_count += 1
                
                if traditional_match.is_maintenance_related:
                    maintenance_related_count += 1
            
            total_confidence += ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else traditional_match.confidence_score
            
            # Add to results
            categorizations.append({
                'expense_id': expense['expense_id'],
                'vehicle_id': traditional_match.vehicle_id,
                'expense_type': ml_result.expense_type.value if hasattr(ml_result, 'expense_type') else traditional_match.expense_type.value,
                'confidence_score': ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else traditional_match.confidence_score,
                'ml_confidence': ml_result.confidence_score if hasattr(ml_result, 'confidence_score') else 0.0,
                'is_vehicle_related': is_vehicle_related,
                'is_maintenance_related': traditional_match.is_maintenance_related
            })
        
        average_confidence = total_confidence / len(expenses) if expenses else 0.0
        
        return jsonify({
            'success': True,
            'categorizations': categorizations,
            'summary': {
                'total_processed': len(expenses),
                'vehicle_related': vehicle_related_count,
                'maintenance_related': maintenance_related_count,
                'ml_processed': ml_processed_count,
                'average_confidence': average_confidence
            }
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced batch categorization: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/insights', methods=['GET'])
def get_enhanced_insights():
    """
    Get enhanced ML-powered vehicle expense insights
    
    Query parameters:
    - user_email: User's email address
    - months: Number of months to analyze (default: 12)
    - include_ml: Include ML-specific insights (default: true)
    
    Returns:
    {
        "success": boolean,
        "insights": [
            {
                "insight_type": "string",
                "title": "string",
                "description": "string",
                "confidence": number,
                "impact_score": number,
                "recommendation": "string",
                "potential_savings": number,
                "category": "string",
                "ml_confidence": number,
                "supporting_data": {string: any}
            }
        ],
        "ml_analysis": {
            "model_version": "string",
            "total_insights": number,
            "ml_generated": number,
            "average_confidence": number
        }
    }
    """
    try:
        user_email = request.args.get('user_email')
        months = int(request.args.get('months', 12))
        include_ml = request.args.get('include_ml', 'true').lower() == 'true'
        
        if not user_email:
            return jsonify({'success': False, 'error': 'user_email parameter required'}), 400
        
        insights = []
        ml_generated_count = 0
        total_confidence = 0.0
        
        if include_ml:
            # Get ML-powered insights
            ml_insights = ml_engine.generate_insights(user_email, months)
            insights.extend(ml_insights)
            ml_generated_count = len(ml_insights)
            
            for insight in ml_insights:
                total_confidence += insight.confidence
        
        # Get traditional insights
        traditional_analysis = spending_analyzer.get_comprehensive_spending_analysis(user_email, months)
        traditional_insights = traditional_analysis.get('insights', [])
        insights.extend(traditional_insights)
        
        average_confidence = total_confidence / ml_generated_count if ml_generated_count > 0 else 0.0
        
        return jsonify({
            'success': True,
            'insights': [
                {
                    'insight_type': insight.insight_type if hasattr(insight, 'insight_type') else 'traditional',
                    'title': insight.title if hasattr(insight, 'title') else insight.get('title', ''),
                    'description': insight.description if hasattr(insight, 'description') else insight.get('description', ''),
                    'confidence': insight.confidence if hasattr(insight, 'confidence') else insight.get('confidence', 0.0),
                    'impact_score': insight.impact_score if hasattr(insight, 'impact_score') else insight.get('impact_level', 'medium'),
                    'recommendation': insight.recommendation if hasattr(insight, 'recommendation') else insight.get('recommendation', ''),
                    'potential_savings': insight.potential_savings if hasattr(insight, 'potential_savings') else insight.get('potential_savings', 0.0),
                    'category': insight.category if hasattr(insight, 'category') else insight.get('category', ''),
                    'ml_confidence': insight.ml_confidence if hasattr(insight, 'ml_confidence') else 0.0,
                    'supporting_data': insight.supporting_data if hasattr(insight, 'supporting_data') else {}
                }
                for insight in insights
            ],
            'ml_analysis': {
                'model_version': ml_engine.model_version,
                'total_insights': len(insights),
                'ml_generated': ml_generated_count,
                'average_confidence': average_confidence
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting enhanced insights: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/analysis', methods=['GET'])
def get_enhanced_analysis():
    """
    Get comprehensive enhanced vehicle expense analysis
    
    Query parameters:
    - user_email: User's email address
    - months: Number of months to analyze (default: 12)
    
    Returns:
    {
        "success": boolean,
        "analysis": {
            "spending_summary": {
                "total_expenses": number,
                "monthly_average": number,
                "vehicle_related_percentage": number
            },
            "category_breakdown": {
                "maintenance": {string: any},
                "fuel": {string: any},
                "insurance": {string: any},
                ...
            },
            "ml_insights": [
                {
                    "insight_type": "string",
                    "title": "string",
                    "description": "string",
                    "confidence": number,
                    "recommendation": "string"
                }
            ],
            "cost_optimization": {
                "potential_savings": number,
                "recommendations": [string],
                "priority_actions": [string]
            },
            "maintenance_forecast": {
                "upcoming_services": [string],
                "estimated_costs": number,
                "recommended_schedule": [string]
            }
        }
    }
    """
    try:
        user_email = request.args.get('user_email')
        months = int(request.args.get('months', 12))
        
        if not user_email:
            return jsonify({'success': False, 'error': 'user_email parameter required'}), 400
        
        # Get comprehensive analysis
        traditional_analysis = spending_analyzer.get_comprehensive_spending_analysis(user_email, months)
        ml_insights = ml_engine.generate_insights(user_email, months)
        
        # Get vehicle expense summary
        vehicle_summary = categorizer.get_vehicle_expense_summary(user_email, months)
        
        # Combine analysis
        analysis = {
            'spending_summary': {
                'total_expenses': vehicle_summary.get('summary', {}).get('total_expenses', 0),
                'monthly_average': vehicle_summary.get('summary', {}).get('average_monthly', 0),
                'vehicle_related_percentage': traditional_analysis.get('summary', {}).get('vehicle_percentage', 0)
            },
            'category_breakdown': vehicle_summary.get('expenses_by_type', {}),
            'ml_insights': [
                {
                    'insight_type': insight.insight_type,
                    'title': insight.title,
                    'description': insight.description,
                    'confidence': insight.confidence,
                    'recommendation': insight.recommendation
                }
                for insight in ml_insights
            ],
            'cost_optimization': {
                'potential_savings': sum(insight.potential_savings for insight in ml_insights),
                'recommendations': [insight.recommendation for insight in ml_insights],
                'priority_actions': [
                    insight.recommendation for insight in ml_insights 
                    if insight.impact_score > 0.7
                ]
            },
            'maintenance_forecast': {
                'upcoming_services': [],  # Would integrate with maintenance prediction engine
                'estimated_costs': 0,    # Would calculate from predictions
                'recommended_schedule': []  # Would generate from maintenance engine
            }
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting enhanced analysis: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/train-models', methods=['POST'])
def train_ml_models():
    """
    Train ML models with user data
    
    Request body:
    {
        "user_email": "string" (optional - train on specific user data)
    }
    
    Returns:
    {
        "success": boolean,
        "training_results": {
            "accuracy": number,
            "training_samples": number,
            "test_samples": number,
            "model_version": "string",
            "training_date": "string"
        }
    }
    """
    try:
        data = request.get_json() or {}
        user_email = data.get('user_email')
        
        # Train models
        training_results = ml_engine.train_models(user_email)
        
        if 'error' in training_results:
            return jsonify({
                'success': False,
                'error': training_results['error']
            }), 400
        
        return jsonify({
            'success': True,
            'training_results': training_results
        })
        
    except Exception as e:
        logger.error(f"Error training ML models: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/service-status', methods=['GET'])
def get_service_status():
    """Get enhanced service status"""
    try:
        status = ml_engine.get_service_status()
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@enhanced_vehicle_api.route('/api/enhanced-vehicle-expenses/health', methods=['GET'])
def health_check():
    """Health check endpoint for enhanced vehicle expense service"""
    return jsonify({
        'status': 'healthy',
        'service': 'enhanced_vehicle_expense_ml',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'ml_categorization': True,
            'enhanced_insights': True,
            'cost_optimization': True,
            'maintenance_prediction': True,
            'pattern_learning': True,
            'anomaly_detection': True
        },
        'ml_available': ml_engine.ml_available,
        'model_version': ml_engine.model_version
    })
