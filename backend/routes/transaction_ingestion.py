"""
Transaction Ingestion API Routes

This module provides API endpoints for transaction ingestion from Plaid
with automatic categorization and tagging capabilities.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.sql import text
import json

from backend.banking.transaction_ingestion import TransactionIngestionService
from backend.integrations.plaid_integration import PlaidIntegration
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.bank_account_models import PlaidTransaction, BankAccount

logger = logging.getLogger(__name__)

transaction_ingestion_bp = Blueprint('transaction_ingestion', __name__, url_prefix='/api/transaction-ingestion')


@transaction_ingestion_bp.route('/ingest', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def ingest_transactions():
    """
    Ingest transactions from Plaid with automatic categorization and tagging
    
    Request body:
    {
        "account_ids": ["account1", "account2"],  # Optional
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        },  # Optional
        "force_refresh": false,  # Optional
        "categorization_settings": {  # Optional
            "use_plaid_categories": true,
            "use_pattern_matching": true,
            "use_amount_heuristics": true,
            "confidence_threshold": 0.5
        }
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'account_ids': {'type': 'list', 'required': False},
            'date_range': {'type': 'dict', 'required': False},
            'force_refresh': {'type': 'bool', 'required': False, 'default': False},
            'categorization_settings': {'type': 'dict', 'required': False}
        })
        
        # Parse date range if provided
        date_range = None
        if data.get('date_range'):
            start_date = datetime.fromisoformat(data['date_range']['start_date'])
            end_date = datetime.fromisoformat(data['date_range']['end_date'])
            date_range = (start_date, end_date)
        
        # Initialize services
        db_session = current_app.db.session
        plaid_integration = PlaidIntegration()
        ingestion_service = TransactionIngestionService(db_session, plaid_integration)
        
        # Ingest transactions
        result = ingestion_service.ingest_transactions(
            user_id=current_user.id,
            account_ids=data.get('account_ids'),
            date_range=date_range,
            force_refresh=data.get('force_refresh', False)
        )
        
        if result['success']:
            return create_response(
                success=True,
                message=f"Successfully ingested {result['summary']['total_new']} new transactions",
                data={
                    'summary': result['summary'],
                    'results_count': len(result['results'])
                }
            )
        else:
            return create_response(
                success=False,
                message=f"Ingestion failed: {result['error']}",
                status_code=500
            )
            
    except Exception as e:
        logger.error(f"Error ingesting transactions: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during transaction ingestion",
            status_code=500
        )


@transaction_ingestion_bp.route('/status', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_ingestion_status():
    """
    Get ingestion status for user accounts
    
    Query parameters:
    - account_ids: Filter by specific account IDs
    - include_recent: Include recent ingestion history
    """
    try:
        account_ids = request.args.getlist('account_ids')
        include_recent = request.args.get('include_recent', 'false').lower() == 'true'
        
        # Get user accounts
        query = current_app.db.session.query(BankAccount).filter(
            BankAccount.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(BankAccount.id.in_(account_ids))
        
        accounts = query.filter(BankAccount.is_active == True).all()
        
        # Get ingestion status for each account
        status_data = []
        for account in accounts:
            # Get latest transaction
            latest_transaction = current_app.db.session.query(PlaidTransaction).filter(
                PlaidTransaction.account_id == account.id
            ).order_by(PlaidTransaction.date.desc()).first()
            
            # Get transaction count
            transaction_count = current_app.db.session.query(PlaidTransaction).filter(
                PlaidTransaction.account_id == account.id
            ).count()
            
            # Get recent transactions if requested
            recent_transactions = []
            if include_recent:
                recent_transactions = current_app.db.session.query(PlaidTransaction).filter(
                    PlaidTransaction.account_id == account.id
                ).order_by(PlaidTransaction.date.desc()).limit(10).all()
                
                recent_transactions = [{
                    'id': str(tx.id),
                    'transaction_id': tx.transaction_id,
                    'amount': float(tx.amount),
                    'date': tx.date.isoformat(),
                    'category': tx.category,
                    'categorization_confidence': tx.categorization_confidence,
                    'tags': tx.tags
                } for tx in recent_transactions]
            
            status_data.append({
                'account_id': account.id,
                'account_name': account.nickname or account.name,
                'account_type': account.account_type,
                'last_transaction_date': latest_transaction.date.isoformat() if latest_transaction else None,
                'total_transactions': transaction_count,
                'last_sync': account.last_sync_at.isoformat() if account.last_sync_at else None,
                'is_active': account.is_active,
                'recent_transactions': recent_transactions if include_recent else []
            })
        
        return create_response(
            success=True,
            message=f"Retrieved ingestion status for {len(status_data)} accounts",
            data={
                'accounts': status_data,
                'total_accounts': len(status_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving ingestion status: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving ingestion status",
            status_code=500
        )


@transaction_ingestion_bp.route('/transactions', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_ingested_transactions():
    """
    Get ingested transactions with filtering and pagination
    
    Query parameters:
    - account_ids: Filter by account IDs
    - categories: Filter by categories
    - date_range: Filter by date range
    - tags: Filter by tags
    - confidence_min: Minimum categorization confidence
    - limit: Number of transactions to return
    - offset: Pagination offset
    """
    try:
        # Parse query parameters
        account_ids = request.args.getlist('account_ids')
        categories = request.args.getlist('categories')
        tags = request.args.getlist('tags')
        confidence_min = float(request.args.get('confidence_min', 0.0))
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if categories:
            query = query.filter(PlaidTransaction.category.in_(categories))
        
        if confidence_min > 0:
            query = query.filter(PlaidTransaction.categorization_confidence >= confidence_min)
        
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                PlaidTransaction.date.between(start_dt, end_dt)
            )
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        transactions = query.order_by(PlaidTransaction.date.desc()).offset(offset).limit(limit).all()
        
        # Filter by tags if specified (post-query filtering for JSON fields)
        if tags:
            filtered_transactions = []
            for tx in transactions:
                tx_tags = json.loads(tx.tags) if tx.tags else []
                if any(tag in tx_tags for tag in tags):
                    filtered_transactions.append(tx)
            transactions = filtered_transactions
        
        # Format response
        transactions_data = []
        for tx in transactions:
            transactions_data.append({
                'id': str(tx.id),
                'transaction_id': tx.transaction_id,
                'account_id': tx.account_id,
                'amount': float(tx.amount),
                'date': tx.date.isoformat(),
                'name': tx.name,  # Note: This would need decryption in production
                'merchant_name': tx.merchant_name,  # Note: This would need decryption in production
                'category': tx.category,
                'subcategory': tx.subcategory,
                'categorization_confidence': tx.categorization_confidence,
                'categorization_method': tx.categorization_method,
                'tags': json.loads(tx.tags) if tx.tags else [],
                'metadata': json.loads(tx.metadata) if tx.metadata else {},
                'created_at': tx.created_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(transactions_data)} transactions",
            data={
                'transactions': transactions_data,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving ingested transactions: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving transactions",
            status_code=500
        )


@transaction_ingestion_bp.route('/categorization/stats', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_categorization_stats():
    """
    Get categorization statistics for user transactions
    
    Query parameters:
    - account_ids: Filter by account IDs
    - date_range: Filter by date range
    """
    try:
        account_ids = request.args.getlist('account_ids')
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build base query
        query = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                PlaidTransaction.date.between(start_dt, end_dt)
            )
        
        # Get categorization statistics
        from sqlalchemy import func
        
        # Category distribution
        category_stats = current_app.db.session.query(
            PlaidTransaction.category,
            func.count(PlaidTransaction.id).label('count'),
            func.avg(PlaidTransaction.categorization_confidence).label('avg_confidence')
        ).filter(
            PlaidTransaction.user_id == current_user.id
        ).group_by(PlaidTransaction.category).all()
        
        # Method distribution
        method_stats = current_app.db.session.query(
            PlaidTransaction.categorization_method,
            func.count(PlaidTransaction.id).label('count')
        ).filter(
            PlaidTransaction.user_id == current_user.id
        ).group_by(PlaidTransaction.categorization_method).all()
        
        # Confidence distribution
        confidence_ranges = [
            (0.0, 0.3, 'low'),
            (0.3, 0.7, 'medium'),
            (0.7, 1.0, 'high')
        ]
        
        confidence_stats = []
        for min_conf, max_conf, label in confidence_ranges:
            count = current_app.db.session.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.user_id == current_user.id,
                    PlaidTransaction.categorization_confidence >= min_conf,
                    PlaidTransaction.categorization_confidence < max_conf
                )
            ).count()
            confidence_stats.append({
                'range': label,
                'min_confidence': min_conf,
                'max_confidence': max_conf,
                'count': count
            })
        
        # Total statistics
        total_transactions = query.count()
        avg_confidence = current_app.db.session.query(
            func.avg(PlaidTransaction.categorization_confidence)
        ).filter(
            PlaidTransaction.user_id == current_user.id
        ).scalar() or 0.0
        
        return create_response(
            success=True,
            message="Retrieved categorization statistics",
            data={
                'total_transactions': total_transactions,
                'average_confidence': float(avg_confidence),
                'category_distribution': [
                    {
                        'category': stat.category,
                        'count': stat.count,
                        'percentage': (stat.count / total_transactions * 100) if total_transactions > 0 else 0,
                        'average_confidence': float(stat.avg_confidence or 0.0)
                    }
                    for stat in category_stats
                ],
                'method_distribution': [
                    {
                        'method': stat.categorization_method,
                        'count': stat.count,
                        'percentage': (stat.count / total_transactions * 100) if total_transactions > 0 else 0
                    }
                    for stat in method_stats
                ],
                'confidence_distribution': confidence_stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving categorization stats: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving categorization statistics",
            status_code=500
        )


@transaction_ingestion_bp.route('/categorization/update', methods=['PUT'])
@login_required
@require_auth
@handle_api_errors
def update_transaction_categorization():
    """
    Update transaction categorization (user override)
    
    Request body:
    {
        "transaction_id": "transaction_id",
        "category": "new_category",
        "subcategory": "new_subcategory",  # Optional
        "tags": ["tag1", "tag2"],  # Optional
        "confidence": 1.0  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'transaction_id': {'type': 'str', 'required': True},
            'category': {'type': 'str', 'required': True},
            'subcategory': {'type': 'str', 'required': False},
            'tags': {'type': 'list', 'required': False},
            'confidence': {'type': 'float', 'required': False, 'default': 1.0}
        })
        
        # Find the transaction
        transaction = current_app.db.session.query(PlaidTransaction).filter(
            and_(
                PlaidTransaction.transaction_id == data['transaction_id'],
                PlaidTransaction.user_id == current_user.id
            )
        ).first()
        
        if not transaction:
            return create_response(
                success=False,
                message="Transaction not found",
                status_code=404
            )
        
        # Update categorization
        transaction.category = data['category']
        if data.get('subcategory'):
            transaction.subcategory = data['subcategory']
        
        transaction.categorization_confidence = data.get('confidence', 1.0)
        transaction.categorization_method = 'user_override'
        
        # Update tags
        if data.get('tags'):
            current_tags = json.loads(transaction.tags) if transaction.tags else []
            # Add user_override tag and new tags
            new_tags = list(set(current_tags + data['tags'] + ['user_override']))
            transaction.tags = json.dumps(new_tags)
        
        # Update metadata
        metadata = json.loads(transaction.metadata) if transaction.metadata else {}
        metadata['user_override'] = {
            'timestamp': datetime.now().isoformat(),
            'previous_category': transaction.category,
            'previous_confidence': transaction.categorization_confidence
        }
        transaction.metadata = json.dumps(metadata)
        
        current_app.db.session.commit()
        
        return create_response(
            success=True,
            message="Transaction categorization updated successfully",
            data={
                'transaction_id': transaction.transaction_id,
                'new_category': transaction.category,
                'new_confidence': transaction.categorization_confidence
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating transaction categorization: {str(e)}")
        current_app.db.session.rollback()
        return create_response(
            success=False,
            message="Internal server error updating categorization",
            status_code=500
        )


@transaction_ingestion_bp.route('/tags', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_transaction_tags():
    """
    Get all unique tags used in user transactions
    
    Query parameters:
    - account_ids: Filter by account IDs
    - date_range: Filter by date range
    """
    try:
        account_ids = request.args.getlist('account_ids')
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                PlaidTransaction.date.between(start_dt, end_dt)
            )
        
        # Get all transactions and extract tags
        transactions = query.all()
        
        # Collect all tags
        all_tags = set()
        tag_counts = {}
        
        for tx in transactions:
            if tx.tags:
                tags = json.loads(tx.tags)
                for tag in tags:
                    all_tags.add(tag)
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Format response
        tags_data = [
            {
                'tag': tag,
                'count': tag_counts[tag],
                'percentage': (tag_counts[tag] / len(transactions) * 100) if transactions else 0
            }
            for tag in sorted(all_tags)
        ]
        
        return create_response(
            success=True,
            message=f"Retrieved {len(tags_data)} unique tags",
            data={
                'tags': tags_data,
                'total_transactions': len(transactions),
                'unique_tags_count': len(tags_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving transaction tags: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving tags",
            status_code=500
        )


@transaction_ingestion_bp.route('/duplicates', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_duplicate_transactions():
    """
    Get potential duplicate transactions
    
    Query parameters:
    - account_ids: Filter by account IDs
    - date_range: Filter by date range
    - similarity_threshold: Minimum similarity threshold (0.0-1.0)
    """
    try:
        account_ids = request.args.getlist('account_ids')
        similarity_threshold = float(request.args.get('similarity_threshold', 0.8))
        
        # Parse date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = current_app.db.session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == current_user.id
        )
        
        if account_ids:
            query = query.filter(PlaidTransaction.account_id.in_(account_ids))
        
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                PlaidTransaction.date.between(start_dt, end_dt)
            )
        
        transactions = query.order_by(PlaidTransaction.date.desc()).all()
        
        # Find potential duplicates
        duplicates = []
        processed_ids = set()
        
        for i, tx1 in enumerate(transactions):
            if tx1.id in processed_ids:
                continue
                
            similar_transactions = []
            
            for tx2 in transactions[i+1:]:
                if tx2.id in processed_ids:
                    continue
                
                # Check for similarity
                similarity = calculate_transaction_similarity(tx1, tx2)
                
                if similarity >= similarity_threshold:
                    similar_transactions.append({
                        'id': str(tx2.id),
                        'transaction_id': tx2.transaction_id,
                        'amount': float(tx2.amount),
                        'date': tx2.date.isoformat(),
                        'merchant_name': tx2.merchant_name,
                        'similarity': similarity
                    })
            
            if similar_transactions:
                duplicates.append({
                    'primary_transaction': {
                        'id': str(tx1.id),
                        'transaction_id': tx1.transaction_id,
                        'amount': float(tx1.amount),
                        'date': tx1.date.isoformat(),
                        'merchant_name': tx1.merchant_name
                    },
                    'similar_transactions': similar_transactions,
                    'group_size': len(similar_transactions) + 1
                })
                
                # Mark all transactions in this group as processed
                processed_ids.add(tx1.id)
                for similar in similar_transactions:
                    processed_ids.add(similar['id'])
        
        return create_response(
            success=True,
            message=f"Found {len(duplicates)} potential duplicate groups",
            data={
                'duplicates': duplicates,
                'total_groups': len(duplicates),
                'similarity_threshold': similarity_threshold
            }
        )
        
    except Exception as e:
        logger.error(f"Error finding duplicate transactions: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error finding duplicates",
            status_code=500
        )


def calculate_transaction_similarity(tx1: PlaidTransaction, tx2: PlaidTransaction) -> float:
    """Calculate similarity between two transactions"""
    similarity_score = 0.0
    
    # Amount similarity (exact match gets high score)
    if abs(tx1.amount) == abs(tx2.amount):
        similarity_score += 0.4
    elif abs(abs(tx1.amount) - abs(tx2.amount)) < 1.0:  # Within $1
        similarity_score += 0.3
    elif abs(abs(tx1.amount) - abs(tx2.amount)) < 5.0:  # Within $5
        similarity_score += 0.2
    
    # Date similarity (same day gets high score)
    date_diff = abs((tx1.date - tx2.date).days)
    if date_diff == 0:
        similarity_score += 0.3
    elif date_diff <= 1:
        similarity_score += 0.2
    elif date_diff <= 7:
        similarity_score += 0.1
    
    # Merchant name similarity
    merchant1 = tx1.merchant_name or tx1.name or ""
    merchant2 = tx2.merchant_name or tx2.name or ""
    
    if merchant1 and merchant2:
        # Simple word-based similarity
        words1 = set(merchant1.lower().split())
        words2 = set(merchant2.lower().split())
        
        if words1 and words2:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            merchant_similarity = len(intersection) / len(union)
            similarity_score += merchant_similarity * 0.3
    
    return min(similarity_score, 1.0)


@transaction_ingestion_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for transaction ingestion service
    """
    try:
        # Check database connection
        db_session = current_app.db.session
        db_session.execute(text('SELECT 1'))
        
        # Check Plaid integration
        plaid_integration = PlaidIntegration()
        
        return create_response(
            success=True,
            message="Transaction ingestion service is healthy",
            data={
                'status': 'healthy',
                'database': 'connected',
                'plaid_integration': 'available',
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Transaction ingestion service is unhealthy",
            status_code=503,
            data={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_transaction_ingestion_routes(app):
    """Register transaction ingestion routes with the Flask app"""
    app.register_blueprint(transaction_ingestion_bp)
    logger.info("Transaction ingestion routes registered successfully") 