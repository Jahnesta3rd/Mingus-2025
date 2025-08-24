"""
Plaid Webhook Handler for MINGUS

This module handles Plaid webhook events for real-time updates including:
- Transaction updates and removals
- Account balance changes
- Item login requirements and errors
- Account updates and availability changes
"""

import json
import logging
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from flask import request, jsonify, current_app
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.models.plaid_models import (
    PlaidConnection, 
    PlaidAccount, 
    PlaidTransaction, 
    PlaidSyncLog
)
from config.plaid_config import get_plaid_config, PlaidEnvironment

logger = logging.getLogger(__name__)

class PlaidWebhookEvent(Enum):
    """Plaid webhook event types"""
    TRANSACTIONS_INITIAL_UPDATE = "TRANSACTIONS_INITIAL_UPDATE"
    TRANSACTIONS_HISTORICAL_UPDATE = "TRANSACTIONS_HISTORICAL_UPDATE"
    TRANSACTIONS_DEFAULT_UPDATE = "TRANSACTIONS_DEFAULT_UPDATE"
    TRANSACTIONS_REMOVED = "TRANSACTIONS_REMOVED"
    ITEM_LOGIN_REQUIRED = "ITEM_LOGIN_REQUIRED"
    ITEM_ERROR = "ITEM_ERROR"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    ACCOUNT_AVAILABLE_BALANCE_UPDATED = "ACCOUNT_AVAILABLE_BALANCE_UPDATED"

@dataclass
class WebhookEvent:
    """Webhook event data structure"""
    webhook_type: str
    webhook_code: str
    item_id: str
    environment: str
    timestamp: datetime
    error: Optional[Dict[str, Any]] = None
    new_transactions: int = 0
    removed_transactions: List[str] = None
    account_ids: List[str] = None
    account_id: Optional[str] = None
    available_balance: Optional[float] = None
    current_balance: Optional[float] = None
    iso_currency_code: Optional[str] = None
    
    def __post_init__(self):
        if self.removed_transactions is None:
            self.removed_transactions = []
        if self.account_ids is None:
            self.account_ids = []

class PlaidWebhookHandler:
    """Handles Plaid webhook events"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = get_plaid_config()
        
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        try:
            if not self.config.webhook.webhook_secret:
                logger.warning("No webhook secret configured, skipping signature verification")
                return True
            
            expected_signature = hmac.new(
                self.config.webhook.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"v0={expected_signature}", signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def parse_webhook_event(self, data: Dict[str, Any]) -> WebhookEvent:
        """Parse webhook event data"""
        try:
            event = WebhookEvent(
                webhook_type=data.get('webhook_type', ''),
                webhook_code=data.get('webhook_code', ''),
                item_id=data.get('item_id', ''),
                environment=data.get('environment', ''),
                timestamp=datetime.fromtimestamp(data.get('timestamp', 0), tz=timezone.utc),
                error=data.get('error'),
                new_transactions=data.get('new_transactions', 0),
                removed_transactions=data.get('removed_transactions', []),
                account_ids=data.get('account_ids', []),
                account_id=data.get('account_id'),
                available_balance=data.get('available_balance'),
                current_balance=data.get('current_balance'),
                iso_currency_code=data.get('iso_currency_code')
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            raise
    
    def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle webhook event based on type"""
        try:
            logger.info(f"Processing webhook event: {event.webhook_code} for item {event.item_id}")
            
            # Get connection for this item
            connection = self.db.query(PlaidConnection).filter(
                PlaidConnection.item_id == event.item_id,
                PlaidConnection.is_active == True
            ).first()
            
            if not connection:
                logger.error(f"No active connection found for item {event.item_id}")
                return {'error': 'Connection not found'}
            
            # Handle different webhook types
            if event.webhook_code in [
                PlaidWebhookEvent.TRANSACTIONS_INITIAL_UPDATE.value,
                PlaidWebhookEvent.TRANSACTIONS_HISTORICAL_UPDATE.value,
                PlaidWebhookEvent.TRANSACTIONS_DEFAULT_UPDATE.value
            ]:
                return self._handle_transaction_update(connection, event)
            
            elif event.webhook_code == PlaidWebhookEvent.TRANSACTIONS_REMOVED.value:
                return self._handle_transaction_removal(connection, event)
            
            elif event.webhook_code == PlaidWebhookEvent.ITEM_LOGIN_REQUIRED.value:
                return self._handle_item_login_required(connection, event)
            
            elif event.webhook_code == PlaidWebhookEvent.ITEM_ERROR.value:
                return self._handle_item_error(connection, event)
            
            elif event.webhook_code == PlaidWebhookEvent.ACCOUNT_UPDATED.value:
                return self._handle_account_update(connection, event)
            
            elif event.webhook_code == PlaidWebhookEvent.ACCOUNT_AVAILABLE_BALANCE_UPDATED.value:
                return self._handle_balance_update(connection, event)
            
            else:
                logger.warning(f"Unhandled webhook code: {event.webhook_code}")
                return {'status': 'ignored', 'reason': 'Unhandled webhook code'}
                
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")
            return {'error': str(e)}
    
    def _handle_transaction_update(self, connection: PlaidConnection, event: WebhookEvent) -> Dict[str, Any]:
        """Handle transaction update events"""
        try:
            # Create sync log entry
            sync_log = PlaidSyncLog(
                connection_id=connection.id,
                user_id=connection.user_id,
                sync_type='transactions',
                status='in_progress',
                started_at=datetime.utcnow(),
                metadata={
                    'webhook_code': event.webhook_code,
                    'new_transactions': event.new_transactions,
                    'account_ids': event.account_ids
                }
            )
            self.db.add(sync_log)
            self.db.flush()
            
            # Import Plaid service for transaction sync
            from backend.integrations.plaid_integration import PlaidIntegrationService
            plaid_service = PlaidIntegrationService(self.db, self.config)
            
            # Sync new transactions
            cursor = None  # In production, retrieve from sync_log.metadata
            transactions, next_cursor, has_more = plaid_service.sync_transactions(
                connection.access_token, cursor
            )
            
            # Process synced transactions
            synced_count = 0
            for transaction in transactions:
                # Check if transaction already exists
                existing = self.db.query(PlaidTransaction).filter(
                    PlaidTransaction.plaid_transaction_id == transaction.transaction_id
                ).first()
                
                if not existing:
                    # Get account for this transaction
                    account = self.db.query(PlaidAccount).filter(
                        PlaidAccount.plaid_account_id == transaction.account_id
                    ).first()
                    
                    if account:
                        # Create new transaction record
                        plaid_transaction = PlaidTransaction(
                            connection_id=connection.id,
                            account_id=account.id,
                            user_id=connection.user_id,
                            plaid_transaction_id=transaction.transaction_id,
                            pending_transaction_id=transaction.pending_transaction_id,
                            name=transaction.name,
                            amount=transaction.amount,
                            date=transaction.date,
                            datetime=transaction.datetime,
                            authorized_date=transaction.authorized_date,
                            authorized_datetime=transaction.authorized_datetime,
                            merchant_name=transaction.merchant_name,
                            logo_url=transaction.logo_url,
                            website=transaction.website,
                            category=transaction.category,
                            category_id=transaction.category_id,
                            personal_finance_category=transaction.personal_finance_category,
                            pending=transaction.pending,
                            payment_channel=transaction.payment_channel,
                            transaction_type=transaction.transaction_type,
                            transaction_code=transaction.transaction_code,
                            location=transaction.location,
                            payment_meta=transaction.payment_meta,
                            iso_currency_code=transaction.iso_currency_code,
                            unofficial_currency_code=transaction.unofficial_currency_code,
                            account_owner=transaction.account_owner,
                            check_number=transaction.check_number,
                            is_active=True
                        )
                        self.db.add(plaid_transaction)
                        synced_count += 1
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.completed_at = datetime.utcnow()
            sync_log.items_processed = len(transactions)
            sync_log.items_added = synced_count
            sync_log.metadata.update({
                'next_cursor': next_cursor,
                'has_more': has_more,
                'synced_count': synced_count
            })
            sync_log.calculate_duration()
            
            # Update connection last sync time
            connection.last_sync_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Successfully synced {synced_count} new transactions for item {event.item_id}")
            
            return {
                'status': 'success',
                'synced_transactions': synced_count,
                'total_transactions': len(transactions)
            }
            
        except Exception as e:
            logger.error(f"Error handling transaction update: {e}")
            if 'sync_log' in locals():
                sync_log.status = 'error'
                sync_log.completed_at = datetime.utcnow()
                sync_log.error_message = str(e)
                sync_log.calculate_duration()
                self.db.commit()
            
            return {'error': str(e)}
    
    def _handle_transaction_removal(self, connection: PlaidConnection, event: WebhookEvent) -> Dict[str, Any]:
        """Handle transaction removal events"""
        try:
            removed_count = 0
            
            for transaction_id in event.removed_transactions:
                # Find and mark transaction as inactive
                transaction = self.db.query(PlaidTransaction).filter(
                    PlaidTransaction.plaid_transaction_id == transaction_id,
                    PlaidTransaction.connection_id == connection.id
                ).first()
                
                if transaction:
                    transaction.is_active = False
                    removed_count += 1
            
            self.db.commit()
            
            logger.info(f"Marked {removed_count} transactions as removed for item {event.item_id}")
            
            return {
                'status': 'success',
                'removed_transactions': removed_count
            }
            
        except Exception as e:
            logger.error(f"Error handling transaction removal: {e}")
            return {'error': str(e)}
    
    def _handle_item_login_required(self, connection: PlaidConnection, event: WebhookEvent) -> Dict[str, Any]:
        """Handle item login required events"""
        try:
            # Update connection status
            connection.error_code = 'ITEM_LOGIN_REQUIRED'
            connection.error_message = 'User needs to re-authenticate with their bank'
            connection.is_active = False  # Temporarily disable
            
            self.db.commit()
            
            logger.warning(f"Item {event.item_id} requires re-authentication")
            
            # TODO: Send notification to user about re-authentication requirement
            
            return {
                'status': 'success',
                'action': 'connection_disabled',
                'reason': 'login_required'
            }
            
        except Exception as e:
            logger.error(f"Error handling item login required: {e}")
            return {'error': str(e)}
    
    def _handle_item_error(self, connection: PlaidConnection, event: WebhookEvent) -> Dict[str, Any]:
        """Handle item error events"""
        try:
            error_info = event.error or {}
            
            # Update connection with error information
            connection.error_code = error_info.get('error_code', 'UNKNOWN_ERROR')
            connection.error_message = error_info.get('error_message', 'Unknown error occurred')
            
            self.db.commit()
            
            logger.error(f"Item {event.item_id} error: {connection.error_code} - {connection.error_message}")
            
            # TODO: Send notification to user about connection error
            
            return {
                'status': 'success',
                'action': 'error_logged',
                'error_code': connection.error_code
            }
            
        except Exception as e:
            logger.error(f"Error handling item error: {e}")
            return {'error': str(e)}
    
    def _handle_account_update(self, connection: PlaidConnection, event: WebhookEvent) -> Dict[str, Any]:
        """Handle account update events"""
        try:
            updated_accounts = 0
            
            for account_id in event.account_ids:
                # Find and update account information
                account = self.db.query(PlaidAccount).filter(
                    PlaidAccount.plaid_account_id == account_id,
                    PlaidAccount.connection_id == connection.id
                ).first()
                
                if account:
                    # TODO: Fetch updated account information from Plaid API
                    # For now, just mark as updated
                    account.updated_at = datetime.utcnow()
                    updated_accounts += 1
            
            self.db.commit()
            
            logger.info(f"Updated {updated_accounts} accounts for item {event.item_id}")
            
            return {
                'status': 'success',
                'updated_accounts': updated_accounts
            }
            
        except Exception as e:
            logger.error(f"Error handling account update: {e}")
            return {'error': str(e)}
    
    def _handle_balance_update(self, connection: PlaidConnection, event: WebhookEvent) -> Dict[str, Any]:
        """Handle balance update events"""
        try:
            if not event.account_id:
                return {'error': 'No account ID provided'}
            
            # Find and update account balance
            account = self.db.query(PlaidAccount).filter(
                PlaidAccount.plaid_account_id == event.account_id,
                PlaidAccount.connection_id == connection.id
            ).first()
            
            if account:
                if event.current_balance is not None:
                    account.current_balance = event.current_balance
                
                if event.available_balance is not None:
                    account.available_balance = event.available_balance
                
                if event.iso_currency_code:
                    account.iso_currency_code = event.iso_currency_code
                
                account.last_balance_update = datetime.utcnow()
                account.updated_at = datetime.utcnow()
                
                self.db.commit()
                
                logger.info(f"Updated balance for account {event.account_id}: current={event.current_balance}, available={event.available_balance}")
                
                return {
                    'status': 'success',
                    'account_id': event.account_id,
                    'current_balance': event.current_balance,
                    'available_balance': event.available_balance
                }
            else:
                logger.warning(f"Account {event.account_id} not found for balance update")
                return {'error': 'Account not found'}
                
        except Exception as e:
            logger.error(f"Error handling balance update: {e}")
            return {'error': str(e)}

def handle_plaid_webhook():
    """Flask route handler for Plaid webhooks"""
    try:
        # Get webhook signature for verification
        signature = request.headers.get('Plaid-Verification')
        
        # Get request payload
        payload = request.get_data()
        data = request.get_json()
        
        if not data:
            logger.error("No webhook data received")
            return jsonify({'error': 'No data received'}), 400
        
        # Initialize webhook handler
        db_session = current_app.db.session
        handler = PlaidWebhookHandler(db_session)
        
        # Verify webhook signature (in production)
        if current_app.config.get('ENV') == 'production':
            if not handler.verify_webhook_signature(payload, signature):
                logger.error("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse webhook event
        event = handler.parse_webhook_event(data)
        
        # Handle webhook event
        result = handler.handle_webhook(event)
        
        if 'error' in result:
            logger.error(f"Webhook handling failed: {result['error']}")
            return jsonify(result), 500
        else:
            logger.info(f"Webhook handled successfully: {result}")
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def register_plaid_webhook_routes(app):
    """Register Plaid webhook routes with Flask app"""
    app.add_url_rule(
        '/api/plaid/webhook',
        'plaid_webhook',
        handle_plaid_webhook,
        methods=['POST']
    )
    
    logger.info("Plaid webhook routes registered") 