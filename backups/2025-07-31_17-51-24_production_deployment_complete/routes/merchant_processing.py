"""
Merchant Processing API Routes

This module provides API endpoints for merchant identification, standardization,
and recurring pattern detection for transaction processing.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from backend.banking.merchant_processor import MerchantProcessor
from backend.banking.recurring_pattern_detector import RecurringPatternDetector
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.bank_account_models import PlaidTransaction

logger = logging.getLogger(__name__)

merchant_processing_bp = Blueprint('merchant_processing', __name__, url_prefix='/api/merchant-processing')


@merchant_processing_bp.route('/merchants/process', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def process_merchants():
    """
    Process and standardize merchant names
    
    Request body:
    {
        "merchant_names": ["merchant1", "merchant2"],  # Optional
        "account_ids": ["account1", "account2"],  # Optional
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        }  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'merchant_names': {'type': 'list', 'required': False},
            'account_ids': {'type': 'list', 'required': False},
            'date_range': {'type': 'dict', 'required': False}
        })
        
        # Parse date range if provided
        date_range = None
        if data.get('date_range'):
            start_date = datetime.fromisoformat(data['date_range']['start_date'])
            end_date = datetime.fromisoformat(data['date_range']['end_date'])
            date_range = (start_date, end_date)
        
        # Initialize merchant processor
        db_session = current_app.db.session
        merchant_processor = MerchantProcessor(db_session)
        
        if data.get('merchant_names'):
            # Process specific merchant names
            merchant_names = data['merchant_names']
            results = merchant_processor.batch_process_merchants(merchant_names)
            
            processed_data = []
            for merchant_info in results:
                processed_data.append({
                    'original_name': merchant_info.original_name,
                    'standardized_name': merchant_info.standardized_name,
                    'merchant_type': merchant_info.merchant_type.value,
                    'category': merchant_info.category,
                    'confidence_score': merchant_info.confidence_score,
                    'standardization_level': merchant_info.standardization_level.value,
                    'aliases': merchant_info.aliases,
                    'website': merchant_info.website,
                    'chain_id': merchant_info.chain_id,
                    'parent_company': merchant_info.parent_company
                })
            
            return create_response(
                success=True,
                message=f"Processed {len(processed_data)} merchant names",
                data={
                    'merchants': processed_data,
                    'total_processed': len(processed_data)
                }
            )
        else:
            # Process merchants from transactions
            query = db_session.query(PlaidTransaction).filter(
                PlaidTransaction.user_id == current_user.id
            )
            
            if data.get('account_ids'):
                query = query.filter(PlaidTransaction.account_id.in_(data['account_ids']))
            
            if date_range:
                query = query.filter(
                    PlaidTransaction.date.between(date_range[0], date_range[1])
                )
            
            transactions = query.all()
            
            # Extract unique merchant names
            merchant_names = set()
            for tx in transactions:
                if tx.merchant_name:
                    merchant_names.add(tx.merchant_name)
                elif tx.name:
                    merchant_names.add(tx.name)
            
            # Process merchants
            results = merchant_processor.batch_process_merchants(list(merchant_names))
            
            processed_data = []
            for merchant_info in results:
                processed_data.append({
                    'original_name': merchant_info.original_name,
                    'standardized_name': merchant_info.standardized_name,
                    'merchant_type': merchant_info.merchant_type.value,
                    'category': merchant_info.category,
                    'confidence_score': merchant_info.confidence_score,
                    'standardization_level': merchant_info.standardization_level.value,
                    'aliases': merchant_info.aliases,
                    'website': merchant_info.website,
                    'chain_id': merchant_info.chain_id,
                    'parent_company': merchant_info.parent_company
                })
            
            return create_response(
                success=True,
                message=f"Processed {len(processed_data)} merchant names from transactions",
                data={
                    'merchants': processed_data,
                    'total_processed': len(processed_data),
                    'total_transactions': len(transactions)
                }
            )
            
    except Exception as e:
        logger.error(f"Error processing merchants: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during merchant processing",
            status_code=500
        )


@merchant_processing_bp.route('/merchants/standardize', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def standardize_merchant():
    """
    Standardize a single merchant name
    
    Request body:
    {
        "merchant_name": "merchant name to standardize",
        "transaction_data": {  # Optional
            "amount": 100.0,
            "category": "food_dining",
            "date": "2025-01-01"
        }
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'merchant_name': {'type': 'str', 'required': True},
            'transaction_data': {'type': 'dict', 'required': False}
        })
        
        # Initialize merchant processor
        db_session = current_app.db.session
        merchant_processor = MerchantProcessor(db_session)
        
        # Process merchant
        merchant_info = merchant_processor.process_merchant(
            data['merchant_name'],
            data.get('transaction_data')
        )
        
        return create_response(
            success=True,
            message="Merchant standardized successfully",
            data={
                'original_name': merchant_info.original_name,
                'standardized_name': merchant_info.standardized_name,
                'merchant_type': merchant_info.merchant_type.value,
                'category': merchant_info.category,
                'confidence_score': merchant_info.confidence_score,
                'standardization_level': merchant_info.standardization_level.value,
                'aliases': merchant_info.aliases,
                'website': merchant_info.website,
                'chain_id': merchant_info.chain_id,
                'parent_company': merchant_info.parent_company,
                'metadata': merchant_info.metadata
            }
        )
        
    except Exception as e:
        logger.error(f"Error standardizing merchant: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during merchant standardization",
            status_code=500
        )


@merchant_processing_bp.route('/merchants/statistics', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_merchant_statistics():
    """
    Get merchant processing statistics
    
    Query parameters:
    - account_ids: Filter by account IDs
    - date_range: Filter by date range
    """
    try:
        account_ids = request.args.getlist('account_ids')
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Initialize merchant processor
        db_session = current_app.db.session
        merchant_processor = MerchantProcessor(db_session)
        
        # Get statistics
        stats = merchant_processor.get_merchant_statistics(current_user.id)
        
        return create_response(
            success=True,
            message="Retrieved merchant statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error retrieving merchant statistics: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving merchant statistics",
            status_code=500
        )


@merchant_processing_bp.route('/patterns/detect', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def detect_recurring_patterns():
    """
    Detect recurring transaction patterns
    
    Request body:
    {
        "account_ids": ["account1", "account2"],  # Optional
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        },  # Optional
        "min_confidence": 0.6  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'account_ids': {'type': 'list', 'required': False},
            'date_range': {'type': 'dict', 'required': False},
            'min_confidence': {'type': 'float', 'required': False, 'default': 0.6}
        })
        
        # Parse date range if provided
        date_range = None
        if data.get('date_range'):
            start_date = datetime.fromisoformat(data['date_range']['start_date'])
            end_date = datetime.fromisoformat(data['date_range']['end_date'])
            date_range = (start_date, end_date)
        
        # Initialize pattern detector
        db_session = current_app.db.session
        pattern_detector = RecurringPatternDetector(db_session)
        
        # Detect patterns
        patterns = pattern_detector.detect_recurring_patterns(
            user_id=current_user.id,
            account_ids=data.get('account_ids'),
            date_range=date_range,
            min_confidence=data.get('min_confidence', 0.6)
        )
        
        # Save patterns to database
        if patterns:
            pattern_detector.save_patterns_to_database(patterns)
        
        # Format response
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                'pattern_id': pattern.pattern_id,
                'merchant_name': pattern.merchant_name,
                'category': pattern.category,
                'recurring_type': pattern.recurring_type.value,
                'frequency': pattern.frequency,
                'average_amount': pattern.average_amount,
                'total_amount': pattern.total_amount,
                'confidence_score': pattern.confidence_score,
                'pattern_confidence': pattern.pattern_confidence.value,
                'is_active': pattern.is_active,
                'is_subscription': pattern.is_subscription,
                'first_occurrence': pattern.first_occurrence.isoformat(),
                'last_occurrence': pattern.last_occurrence.isoformat(),
                'next_predicted': pattern.next_predicted.isoformat() if pattern.next_predicted else None,
                'day_of_week': pattern.day_of_week,
                'day_of_month': pattern.day_of_month,
                'transaction_count': len(pattern.transaction_ids)
            })
        
        return create_response(
            success=True,
            message=f"Detected {len(patterns_data)} recurring patterns",
            data={
                'patterns': patterns_data,
                'total_patterns': len(patterns_data),
                'active_patterns': len([p for p in patterns if p.is_active]),
                'subscription_patterns': len([p for p in patterns if p.is_subscription])
            }
        )
        
    except Exception as e:
        logger.error(f"Error detecting recurring patterns: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during pattern detection",
            status_code=500
        )


@merchant_processing_bp.route('/patterns', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_recurring_patterns():
    """
    Get detected recurring patterns
    
    Query parameters:
    - account_ids: Filter by account IDs
    - pattern_types: Filter by pattern types
    - categories: Filter by categories
    - is_active: Filter by active status
    - is_subscription: Filter by subscription status
    - limit: Number of patterns to return
    - offset: Pagination offset
    """
    try:
        from backend.models.analytics import SpendingPattern
        
        # Parse query parameters
        account_ids = request.args.getlist('account_ids')
        pattern_types = request.args.getlist('pattern_types')
        categories = request.args.getlist('categories')
        is_active = request.args.get('is_active')
        is_subscription = request.args.get('is_subscription')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = current_app.db.session.query(SpendingPattern).filter(
            SpendingPattern.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(SpendingPattern.account_id.in_(account_ids))
        
        if pattern_types:
            query = query.filter(SpendingPattern.pattern_type.in_(pattern_types))
        
        if categories:
            query = query.filter(SpendingPattern.category_name.in_(categories))
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(SpendingPattern.is_active == is_active_bool)
        
        if is_subscription is not None:
            is_subscription_bool = is_subscription.lower() == 'true'
            query = query.filter(SpendingPattern.is_recurring == is_subscription_bool)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        patterns = query.order_by(SpendingPattern.confidence_score.desc()).offset(offset).limit(limit).all()
        
        # Format response
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                'pattern_id': str(pattern.id),
                'merchant_name': pattern.merchant_name,
                'category': pattern.category_name,
                'recurring_type': pattern.pattern_type,
                'frequency': pattern.frequency,
                'average_amount': pattern.average_amount,
                'total_amount': pattern.total_amount,
                'confidence_score': pattern.confidence_score,
                'reliability_score': pattern.reliability_score,
                'is_active': pattern.is_active,
                'is_recurring': pattern.is_recurring,
                'first_occurrence': pattern.first_occurrence.isoformat() if pattern.first_occurrence else None,
                'last_occurrence': pattern.last_occurrence.isoformat() if pattern.last_occurrence else None,
                'next_predicted': pattern.next_predicted.isoformat() if pattern.next_predicted else None,
                'created_at': pattern.created_at.isoformat() if pattern.created_at else None,
                'updated_at': pattern.updated_at.isoformat() if pattern.updated_at else None
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(patterns_data)} patterns",
            data={
                'patterns': patterns_data,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recurring patterns: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving patterns",
            status_code=500
        )


@merchant_processing_bp.route('/patterns/statistics', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_pattern_statistics():
    """
    Get pattern detection statistics
    
    Query parameters:
    - account_ids: Filter by account IDs
    """
    try:
        account_ids = request.args.getlist('account_ids')
        
        # Initialize pattern detector
        db_session = current_app.db.session
        pattern_detector = RecurringPatternDetector(db_session)
        
        # Get statistics
        stats = pattern_detector.get_pattern_statistics(current_user.id)
        
        return create_response(
            success=True,
            message="Retrieved pattern statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error retrieving pattern statistics: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving pattern statistics",
            status_code=500
        )


@merchant_processing_bp.route('/patterns/<pattern_id>', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_pattern_details(pattern_id: str):
    """
    Get detailed information about a specific pattern
    
    Path parameters:
    - pattern_id: ID of the pattern to retrieve
    """
    try:
        from backend.models.analytics import SpendingPattern
        
        # Get pattern
        pattern = current_app.db.session.query(SpendingPattern).filter(
            and_(
                SpendingPattern.id == pattern_id,
                SpendingPattern.user_id == current_user.id
            )
        ).first()
        
        if not pattern:
            return create_response(
                success=False,
                message="Pattern not found",
                status_code=404
            )
        
        # Get related transactions
        transactions = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        ).order_by(PlaidTransaction.date.desc()).limit(20).all()
        
        transactions_data = []
        for tx in transactions:
            transactions_data.append({
                'id': str(tx.id),
                'transaction_id': tx.transaction_id,
                'amount': float(tx.amount),
                'date': tx.date.isoformat(),
                'merchant_name': tx.merchant_name,
                'category': tx.category,
                'categorization_confidence': tx.categorization_confidence
            })
        
        return create_response(
            success=True,
            message="Retrieved pattern details",
            data={
                'pattern': {
                    'pattern_id': str(pattern.id),
                    'merchant_name': pattern.merchant_name,
                    'category': pattern.category_name,
                    'recurring_type': pattern.pattern_type,
                    'frequency': pattern.frequency,
                    'average_amount': pattern.average_amount,
                    'total_amount': pattern.total_amount,
                    'confidence_score': pattern.confidence_score,
                    'reliability_score': pattern.reliability_score,
                    'is_active': pattern.is_active,
                    'is_recurring': pattern.is_recurring,
                    'first_occurrence': pattern.first_occurrence.isoformat() if pattern.first_occurrence else None,
                    'last_occurrence': pattern.last_occurrence.isoformat() if pattern.last_occurrence else None,
                    'next_predicted': pattern.next_predicted.isoformat() if pattern.next_predicted else None,
                    'created_at': pattern.created_at.isoformat() if pattern.created_at else None,
                    'updated_at': pattern.updated_at.isoformat() if pattern.updated_at else None
                },
                'recent_transactions': transactions_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving pattern details: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving pattern details",
            status_code=500
        )


@merchant_processing_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for merchant processing service
    """
    try:
        # Check database connection
        db_session = current_app.db.session
        db_session.execute(text('SELECT 1'))
        
        return create_response(
            success=True,
            message="Merchant processing service is healthy",
            data={
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Merchant processing service is unhealthy",
            status_code=503,
            data={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_merchant_processing_routes(app):
    """Register merchant processing routes with the Flask app"""
    app.register_blueprint(merchant_processing_bp)
    logger.info("Merchant processing routes registered successfully") 