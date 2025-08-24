"""
Bank Account Management System for MINGUS

This module provides comprehensive bank account lifecycle management:
- Account creation, linking, and verification
- Subscription tier integration and limits
- Account status monitoring and maintenance
- Data synchronization and reconciliation
- Account security and compliance
- User profile integration
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import json
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, case
from sqlalchemy.exc import SQLAlchemyError

from backend.models.plaid_models import PlaidConnection, PlaidAccount, PlaidTransaction, PlaidInstitution
from backend.models.security_models import SecurityAuditLog, UserConsent
from backend.services.plaid_integration import PlaidIntegrationService
from backend.services.plaid_reliability_service import PlaidReliabilityService
from backend.services.notification_service import NotificationService
from backend.services.enhanced_feature_access_service import EnhancedFeatureAccessService
from backend.services.plaid_subscription_service import PlaidSubscriptionService

logger = logging.getLogger(__name__)

class AccountStatus(Enum):
    """Bank account status enumeration"""
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    ARCHIVED = "archived"

class AccountType(Enum):
    """Bank account type enumeration"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    MORTGAGE = "mortgage"
    BUSINESS = "business"
    OTHER = "other"

class VerificationStatus(Enum):
    """Account verification status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class SyncFrequency(Enum):
    """Data synchronization frequency"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"

@dataclass
class AccountProfile:
    """Bank account profile information"""
    account_id: str
    user_id: str
    connection_id: str
    institution_name: str
    account_name: str
    account_type: AccountType
    account_subtype: str
    mask: str
    status: AccountStatus
    verification_status: VerificationStatus
    balance: Optional[Decimal]
    currency: str
    sync_frequency: SyncFrequency
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class AccountLimits:
    """Account limits based on subscription tier"""
    max_accounts: int
    max_connections: int
    sync_frequency: SyncFrequency
    transaction_history_months: int
    advanced_analytics: bool
    real_time_updates: bool
    export_capabilities: bool
    api_access: bool

@dataclass
class AccountMetrics:
    """Account performance and usage metrics"""
    total_transactions: int
    total_balance: Decimal
    sync_success_rate: float
    last_sync_duration: float
    error_count: int
    maintenance_count: int
    days_since_last_sync: int
    data_freshness_score: float

@dataclass
class AccountSecurityInfo:
    """Account security and compliance information"""
    encryption_level: str
    data_retention_days: int
    consent_status: str
    last_consent_update: datetime
    compliance_status: str
    audit_trail_enabled: bool
    access_logs_enabled: bool

class BankAccountManager:
    """Comprehensive bank account management system"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.plaid_service = PlaidIntegrationService(db_session, config)
        self.reliability_service = PlaidReliabilityService(db_session, NotificationService(db_session, config), config)
        self.notification_service = NotificationService(db_session, config)
        self.feature_service = EnhancedFeatureAccessService(db_session, config)
        self.subscription_service = PlaidSubscriptionService(db_session, config)
        
    def create_account_connection(self, user_id: str, institution_id: str, 
                                public_token: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new bank account connection"""
        try:
            # Validate user subscription tier
            tier_limits = self.subscription_service.get_tier_limits(user_id)
            current_usage = self.subscription_service.get_user_usage_metrics(user_id)
            
            if not self.subscription_service.can_add_connection(user_id):
                return {
                    'success': False,
                    'error': 'Connection limit reached for your subscription tier',
                    'upgrade_required': True,
                    'current_usage': current_usage,
                    'tier_limits': tier_limits
                }
            
            # Exchange public token for access token
            token_result = self.plaid_service.exchange_public_token(public_token)
            if not token_result.success:
                return {
                    'success': False,
                    'error': f'Failed to exchange token: {token_result.error}'
                }
            
            # Get account information from Plaid
            accounts_result = self.plaid_service.get_account_balances(token_result.access_token)
            if not accounts_result.success:
                return {
                    'success': False,
                    'error': f'Failed to get accounts: {accounts_result.error}'
                }
            
            # Create Plaid connection
            connection = PlaidConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                access_token=token_result.access_token,
                item_id=token_result.item_id,
                institution_id=institution_id,
                institution_name=metadata.get('institution_name', 'Unknown Bank'),
                is_active=True,
                requires_reauth=False,
                last_sync_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.db.add(connection)
            self.db.flush()  # Get the connection ID
            
            # Create account records
            created_accounts = []
            for account_data in accounts_result.accounts:
                account = PlaidAccount(
                    id=str(uuid.uuid4()),
                    connection_id=connection.id,
                    account_id=account_data.account_id,
                    name=account_data.name,
                    mask=account_data.mask,
                    type=account_data.type,
                    subtype=account_data.subtype,
                    iso_currency_code=account_data.iso_currency_code,
                    balance=account_data.balance,
                    limit=account_data.limit,
                    is_active=True
                )
                
                self.db.add(account)
                created_accounts.append(account)
            
            # Create initial sync log
            sync_log = PlaidSyncLog(
                connection_id=connection.id,
                sync_type='initial_setup',
                status='success',
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                duration=0.1,
                records_processed=len(created_accounts),
                records_failed=0,
                error_message=None,
                retry_after=None,
                context={'setup_type': 'initial_connection'}
            )
            
            self.db.add(sync_log)
            
            # Create security audit log
            audit_log = SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='account_connection_created',
                resource_type='plaid_connection',
                resource_id=str(connection.id),
                ip_address=metadata.get('ip_address', 'unknown'),
                user_agent=metadata.get('user_agent', 'unknown'),
                success=True,
                details={
                    'institution_id': institution_id,
                    'accounts_count': len(created_accounts),
                    'metadata': metadata
                },
                risk_level='low'
            )
            
            self.db.add(audit_log)
            
            # Create user consent record
            consent = UserConsent(
                user_id=user_id,
                consent_type='bank_data_access',
                granted=True,
                granted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),
                scope='read',
                metadata={
                    'connection_id': str(connection.id),
                    'institution_id': institution_id,
                    'accounts_count': len(created_accounts)
                }
            )
            
            self.db.add(consent)
            
            self.db.commit()
            
            # Send welcome notification
            self._send_account_connection_notification(user_id, connection, created_accounts)
            
            return {
                'success': True,
                'connection_id': str(connection.id),
                'accounts_created': len(created_accounts),
                'accounts': [
                    {
                        'account_id': str(acc.id),
                        'name': acc.name,
                        'mask': acc.mask,
                        'type': acc.type,
                        'balance': float(acc.balance) if acc.balance else None,
                        'currency': acc.iso_currency_code
                    }
                    for acc in created_accounts
                ],
                'institution_name': connection.institution_name,
                'sync_status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error creating account connection: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': f'Failed to create account connection: {str(e)}'
            }
    
    def get_user_accounts(self, user_id: str, include_archived: bool = False) -> List[AccountProfile]:
        """Get all accounts for a user"""
        try:
            query = self.db.query(PlaidConnection).filter(
                PlaidConnection.user_id == user_id
            )
            
            if not include_archived:
                query = query.filter(PlaidConnection.is_active == True)
            
            connections = query.all()
            
            accounts = []
            for connection in connections:
                # Get accounts for this connection
                connection_accounts = self.db.query(PlaidAccount).filter(
                    PlaidAccount.connection_id == connection.id,
                    PlaidAccount.is_active == True
                ).all()
                
                for account in connection_accounts:
                    # Determine account status
                    status = self._determine_account_status(connection, account)
                    verification_status = self._get_verification_status(account)
                    
                    # Get sync frequency based on subscription tier
                    sync_frequency = self._get_sync_frequency(user_id)
                    
                    # Calculate next sync time
                    next_sync_at = self._calculate_next_sync_time(connection.last_sync_at, sync_frequency)
                    
                    account_profile = AccountProfile(
                        account_id=str(account.id),
                        user_id=user_id,
                        connection_id=str(connection.id),
                        institution_name=connection.institution_name,
                        account_name=account.name,
                        account_type=AccountType(account.type),
                        account_subtype=account.subtype,
                        mask=account.mask,
                        status=status,
                        verification_status=verification_status,
                        balance=account.balance,
                        currency=account.iso_currency_code,
                        sync_frequency=sync_frequency,
                        last_sync_at=connection.last_sync_at,
                        next_sync_at=next_sync_at,
                        created_at=account.created_at,
                        updated_at=account.updated_at,
                        metadata=connection.metadata
                    )
                    
                    accounts.append(account_profile)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error getting user accounts: {e}")
            return []
    
    def get_account_details(self, account_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific account"""
        try:
            # Verify account belongs to user
            account = self.db.query(PlaidAccount).join(PlaidConnection).filter(
                PlaidAccount.id == account_id,
                PlaidConnection.user_id == user_id
            ).first()
            
            if not account:
                return None
            
            connection = account.connection
            
            # Get account metrics
            metrics = self._calculate_account_metrics(account)
            
            # Get security information
            security_info = self._get_account_security_info(account, user_id)
            
            # Get recent transactions
            recent_transactions = self.db.query(PlaidTransaction).filter(
                PlaidTransaction.account_id == account.id
            ).order_by(desc(PlaidTransaction.date)).limit(10).all()
            
            # Get account limits
            limits = self.subscription_service.get_tier_limits(user_id)
            
            return {
                'account_id': str(account.id),
                'connection_id': str(connection.id),
                'institution_name': connection.institution_name,
                'account_name': account.name,
                'mask': account.mask,
                'type': account.type,
                'subtype': account.subtype,
                'balance': float(account.balance) if account.balance else None,
                'currency': account.iso_currency_code,
                'limit': float(account.limit) if account.limit else None,
                'status': self._determine_account_status(connection, account).value,
                'verification_status': self._get_verification_status(account).value,
                'last_sync_at': connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                'created_at': account.created_at.isoformat(),
                'updated_at': account.updated_at.isoformat(),
                'metrics': {
                    'total_transactions': metrics.total_transactions,
                    'total_balance': float(metrics.total_balance),
                    'sync_success_rate': metrics.sync_success_rate,
                    'last_sync_duration': metrics.last_sync_duration,
                    'error_count': metrics.error_count,
                    'days_since_last_sync': metrics.days_since_last_sync,
                    'data_freshness_score': metrics.data_freshness_score
                },
                'security': {
                    'encryption_level': security_info.encryption_level,
                    'data_retention_days': security_info.data_retention_days,
                    'consent_status': security_info.consent_status,
                    'last_consent_update': security_info.last_consent_update.isoformat(),
                    'compliance_status': security_info.compliance_status,
                    'audit_trail_enabled': security_info.audit_trail_enabled
                },
                'limits': {
                    'max_accounts': limits.max_accounts,
                    'max_connections': limits.max_connections,
                    'sync_frequency': limits.sync_frequency.value,
                    'transaction_history_months': limits.transaction_history_months,
                    'advanced_analytics': limits.advanced_analytics,
                    'real_time_updates': limits.real_time_updates
                },
                'recent_transactions': [
                    {
                        'transaction_id': str(t.id),
                        'name': t.name,
                        'amount': float(t.amount),
                        'currency': t.iso_currency_code,
                        'date': t.date.isoformat(),
                        'category': t.category,
                        'pending': t.pending
                    }
                    for t in recent_transactions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
            return None
    
    def sync_account_data(self, account_id: str, user_id: str, force_sync: bool = False) -> Dict[str, Any]:
        """Synchronize data for a specific account"""
        try:
            # Verify account belongs to user
            account = self.db.query(PlaidAccount).join(PlaidConnection).filter(
                PlaidAccount.id == account_id,
                PlaidConnection.user_id == user_id
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'Account not found'
                }
            
            connection = account.connection
            
            # Check if sync is needed
            if not force_sync and not self._should_sync_account(connection, account):
                return {
                    'success': False,
                    'error': 'Account does not need synchronization',
                    'next_sync_at': self._calculate_next_sync_time(connection.last_sync_at, self._get_sync_frequency(user_id)).isoformat()
                }
            
            # Check subscription limits
            if not self.subscription_service.can_access_transaction_history(user_id):
                return {
                    'success': False,
                    'error': 'Transaction history access not available for your subscription tier',
                    'upgrade_required': True
                }
            
            # Perform sync
            start_time = datetime.utcnow()
            
            # Get updated account information
            accounts_result = self.plaid_service.get_account_balances(connection.access_token)
            if not accounts_result.success:
                return {
                    'success': False,
                    'error': f'Failed to get account balances: {accounts_result.error}'
                }
            
            # Update account balance
            for account_data in accounts_result.accounts:
                if account_data.account_id == account.account_id:
                    account.balance = account_data.balance
                    account.updated_at = datetime.utcnow()
                    break
            
            # Get transactions if allowed
            transactions_synced = 0
            if self.subscription_service.can_access_transaction_history(user_id):
                transactions_result = self.plaid_service.get_transaction_history(
                    connection.access_token,
                    account.account_id,
                    months_back=min(24, self.subscription_service.get_tier_limits(user_id).transaction_history_months)
                )
                
                if transactions_result.success:
                    # Process new transactions
                    existing_transaction_ids = set(
                        self.db.query(PlaidTransaction.transaction_id).filter(
                            PlaidTransaction.account_id == account.id
                        ).all()
                    )
                    
                    for transaction_data in transactions_result.transactions:
                        if transaction_data.transaction_id not in existing_transaction_ids:
                            transaction = PlaidTransaction(
                                id=str(uuid.uuid4()),
                                connection_id=connection.id,
                                account_id=account.id,
                                transaction_id=transaction_data.transaction_id,
                                name=transaction_data.name,
                                amount=transaction_data.amount,
                                iso_currency_code=transaction_data.iso_currency_code,
                                date=transaction_data.date,
                                datetime=transaction_data.datetime,
                                authorized_datetime=transaction_data.authorized_datetime,
                                category=transaction_data.category,
                                category_id=transaction_data.category_id,
                                check_number=transaction_data.check_number,
                                payment_channel=transaction_data.payment_channel,
                                pending=transaction_data.pending,
                                pending_transaction_id=transaction_data.pending_transaction_id,
                                account_owner=transaction_data.account_owner,
                                transaction_type=transaction_data.transaction_type,
                                transaction_code=transaction_data.transaction_code
                            )
                            
                            self.db.add(transaction)
                            transactions_synced += 1
            
            # Update connection sync time
            connection.last_sync_at = datetime.utcnow()
            connection.updated_at = datetime.utcnow()
            
            # Create sync log
            sync_duration = (datetime.utcnow() - start_time).total_seconds()
            sync_log = PlaidSyncLog(
                connection_id=connection.id,
                sync_type='account_sync',
                status='success',
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration=sync_duration,
                records_processed=transactions_synced,
                records_failed=0,
                error_message=None,
                retry_after=None,
                context={
                    'account_id': str(account.id),
                    'transactions_synced': transactions_synced,
                    'force_sync': force_sync
                }
            )
            
            self.db.add(sync_log)
            self.db.commit()
            
            return {
                'success': True,
                'account_id': str(account.id),
                'balance_updated': True,
                'transactions_synced': transactions_synced,
                'sync_duration': sync_duration,
                'last_sync_at': connection.last_sync_at.isoformat(),
                'next_sync_at': self._calculate_next_sync_time(connection.last_sync_at, self._get_sync_frequency(user_id)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing account data: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': f'Failed to sync account data: {str(e)}'
            }
    
    def disconnect_account(self, account_id: str, user_id: str, reason: str = "user_request") -> Dict[str, Any]:
        """Disconnect a bank account"""
        try:
            # Verify account belongs to user
            account = self.db.query(PlaidAccount).join(PlaidConnection).filter(
                PlaidAccount.id == account_id,
                PlaidConnection.user_id == user_id
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'Account not found'
                }
            
            connection = account.connection
            
            # Remove from Plaid
            remove_result = self.plaid_service.remove_connection(connection.access_token)
            
            # Update account status
            account.is_active = False
            account.updated_at = datetime.utcnow()
            
            # Update connection status
            connection.is_active = False
            connection.requires_reauth = True
            connection.updated_at = datetime.utcnow()
            
            # Create audit log
            audit_log = SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='account_disconnected',
                resource_type='plaid_connection',
                resource_id=str(connection.id),
                ip_address='system',
                user_agent='system',
                success=True,
                details={
                    'account_id': str(account.id),
                    'reason': reason,
                    'plaid_removal_success': remove_result.success
                },
                risk_level='low'
            )
            
            self.db.add(audit_log)
            
            # Revoke consent
            consent = self.db.query(UserConsent).filter(
                UserConsent.user_id == user_id,
                UserConsent.consent_type == 'bank_data_access',
                UserConsent.metadata.contains({'connection_id': str(connection.id)})
            ).first()
            
            if consent:
                consent.granted = False
                consent.revoked_at = datetime.utcnow()
                consent.metadata['revocation_reason'] = reason
            
            self.db.commit()
            
            # Send notification
            self._send_account_disconnection_notification(user_id, connection, account, reason)
            
            return {
                'success': True,
                'account_id': str(account.id),
                'connection_id': str(connection.id),
                'disconnected_at': datetime.utcnow().isoformat(),
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting account: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': f'Failed to disconnect account: {str(e)}'
            }
    
    def get_account_analytics(self, account_id: str, user_id: str, 
                            analytics_type: str = "overview") -> Dict[str, Any]:
        """Get analytics for a specific account"""
        try:
            # Verify account belongs to user
            account = self.db.query(PlaidAccount).join(PlaidConnection).filter(
                PlaidAccount.id == account_id,
                PlaidConnection.user_id == user_id
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'Account not found'
                }
            
            # Check subscription tier for analytics access
            if not self.subscription_service.can_access_advanced_analytics(user_id):
                return {
                    'success': False,
                    'error': 'Advanced analytics not available for your subscription tier',
                    'upgrade_required': True
                }
            
            # Get transactions for analytics
            transactions = self.db.query(PlaidTransaction).filter(
                PlaidTransaction.account_id == account.id
            ).order_by(PlaidTransaction.date).all()
            
            if analytics_type == "overview":
                return self._generate_overview_analytics(account, transactions)
            elif analytics_type == "spending":
                return self._generate_spending_analytics(account, transactions)
            elif analytics_type == "income":
                return self._generate_income_analytics(account, transactions)
            elif analytics_type == "trends":
                return self._generate_trend_analytics(account, transactions)
            else:
                return {
                    'success': False,
                    'error': f'Unknown analytics type: {analytics_type}'
                }
            
        except Exception as e:
            logger.error(f"Error getting account analytics: {e}")
            return {
                'success': False,
                'error': f'Failed to get account analytics: {str(e)}'
            }
    
    def update_account_preferences(self, account_id: str, user_id: str, 
                                 preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update account preferences and settings"""
        try:
            # Verify account belongs to user
            account = self.db.query(PlaidAccount).join(PlaidConnection).filter(
                PlaidAccount.id == account_id,
                PlaidConnection.user_id == user_id
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'Account not found'
                }
            
            connection = account.connection
            
            # Update metadata with preferences
            if 'metadata' not in connection.metadata:
                connection.metadata = {}
            
            connection.metadata.update(preferences)
            connection.updated_at = datetime.utcnow()
            
            # Create audit log
            audit_log = SecurityAuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action='account_preferences_updated',
                resource_type='plaid_account',
                resource_id=str(account.id),
                ip_address='system',
                user_agent='system',
                success=True,
                details={
                    'preferences_updated': list(preferences.keys()),
                    'metadata': preferences
                },
                risk_level='low'
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            return {
                'success': True,
                'account_id': str(account.id),
                'preferences_updated': list(preferences.keys()),
                'updated_at': connection.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating account preferences: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': f'Failed to update account preferences: {str(e)}'
            }
    
    # Private helper methods
    
    def _determine_account_status(self, connection: PlaidConnection, account: PlaidAccount) -> AccountStatus:
        """Determine the current status of an account"""
        if not connection.is_active:
            return AccountStatus.DISCONNECTED
        
        if connection.requires_reauth:
            return AccountStatus.ERROR
        
        if connection.maintenance_until and connection.maintenance_until > datetime.utcnow():
            return AccountStatus.MAINTENANCE
        
        if connection.last_error and connection.last_error_at:
            # Check if error is recent (within last hour)
            if connection.last_error_at > datetime.utcnow() - timedelta(hours=1):
                return AccountStatus.ERROR
        
        if not account.is_active:
            return AccountStatus.SUSPENDED
        
        return AccountStatus.ACTIVE
    
    def _get_verification_status(self, account: PlaidAccount) -> VerificationStatus:
        """Get verification status for an account"""
        # In a real implementation, this would check against verification records
        # For now, return verified for active accounts
        if account.is_active:
            return VerificationStatus.VERIFIED
        else:
            return VerificationStatus.FAILED
    
    def _get_sync_frequency(self, user_id: str) -> SyncFrequency:
        """Get sync frequency based on subscription tier"""
        limits = self.subscription_service.get_tier_limits(user_id)
        
        if limits.real_time_updates:
            return SyncFrequency.REAL_TIME
        elif limits.sync_frequency == 'hourly':
            return SyncFrequency.HOURLY
        elif limits.sync_frequency == 'daily':
            return SyncFrequency.DAILY
        else:
            return SyncFrequency.WEEKLY
    
    def _calculate_next_sync_time(self, last_sync: Optional[datetime], 
                                frequency: SyncFrequency) -> Optional[datetime]:
        """Calculate next sync time based on frequency"""
        if not last_sync:
            return datetime.utcnow()
        
        if frequency == SyncFrequency.REAL_TIME:
            return datetime.utcnow()
        elif frequency == SyncFrequency.HOURLY:
            return last_sync + timedelta(hours=1)
        elif frequency == SyncFrequency.DAILY:
            return last_sync + timedelta(days=1)
        elif frequency == SyncFrequency.WEEKLY:
            return last_sync + timedelta(weeks=1)
        else:
            return None
    
    def _should_sync_account(self, connection: PlaidConnection, account: PlaidAccount) -> bool:
        """Determine if account should be synced"""
        if not connection.last_sync_at:
            return True
        
        # Check if enough time has passed since last sync
        time_since_last_sync = datetime.utcnow() - connection.last_sync_at
        
        # Sync if more than 1 hour has passed
        return time_since_last_sync > timedelta(hours=1)
    
    def _calculate_account_metrics(self, account: PlaidAccount) -> AccountMetrics:
        """Calculate account performance metrics"""
        # Get transaction count
        total_transactions = self.db.query(PlaidTransaction).filter(
            PlaidTransaction.account_id == account.id
        ).count()
        
        # Get total balance
        total_balance = account.balance or Decimal('0')
        
        # Get sync success rate
        sync_logs = self.db.query(PlaidSyncLog).filter(
            PlaidSyncLog.connection_id == account.connection_id
        ).order_by(desc(PlaidSyncLog.completed_at)).limit(10).all()
        
        if sync_logs:
            successful_syncs = len([log for log in sync_logs if log.status == 'success'])
            sync_success_rate = (successful_syncs / len(sync_logs)) * 100
            last_sync_duration = sync_logs[0].duration if sync_logs[0].status == 'success' else 0
        else:
            sync_success_rate = 0
            last_sync_duration = 0
        
        # Calculate days since last sync
        days_since_last_sync = 0
        if account.connection.last_sync_at:
            days_since_last_sync = (datetime.utcnow() - account.connection.last_sync_at).days
        
        # Calculate data freshness score (0-100)
        if days_since_last_sync == 0:
            data_freshness_score = 100
        elif days_since_last_sync <= 1:
            data_freshness_score = 90
        elif days_since_last_sync <= 7:
            data_freshness_score = 70
        elif days_since_last_sync <= 30:
            data_freshness_score = 40
        else:
            data_freshness_score = 10
        
        return AccountMetrics(
            total_transactions=total_transactions,
            total_balance=total_balance,
            sync_success_rate=sync_success_rate,
            last_sync_duration=last_sync_duration,
            error_count=len([log for log in sync_logs if log.status == 'failed']),
            maintenance_count=0,  # Would need to track maintenance events
            days_since_last_sync=days_since_last_sync,
            data_freshness_score=data_freshness_score
        )
    
    def _get_account_security_info(self, account: PlaidAccount, user_id: str) -> AccountSecurityInfo:
        """Get security information for an account"""
        # Get consent information
        consent = self.db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == 'bank_data_access',
            UserConsent.granted == True
        ).first()
        
        return AccountSecurityInfo(
            encryption_level='AES-256-GCM',
            data_retention_days=365,
            consent_status='active' if consent else 'expired',
            last_consent_update=consent.granted_at if consent else datetime.utcnow(),
            compliance_status='compliant',
            audit_trail_enabled=True,
            access_logs_enabled=True
        )
    
    def _generate_overview_analytics(self, account: PlaidAccount, transactions: List[PlaidTransaction]) -> Dict[str, Any]:
        """Generate overview analytics for an account"""
        if not transactions:
            return {
                'success': True,
                'analytics_type': 'overview',
                'data': {
                    'total_transactions': 0,
                    'total_spending': 0,
                    'total_income': 0,
                    'net_flow': 0,
                    'average_transaction': 0,
                    'top_categories': [],
                    'monthly_trends': []
                }
            }
        
        # Calculate basic metrics
        total_transactions = len(transactions)
        total_spending = sum(t.amount for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        net_flow = total_income + total_spending
        average_transaction = net_flow / total_transactions if total_transactions > 0 else 0
        
        # Get top spending categories
        category_spending = {}
        for transaction in transactions:
            if transaction.amount < 0 and transaction.category:
                category = transaction.category[0] if transaction.category else 'Other'
                category_spending[category] = category_spending.get(category, 0) + abs(transaction.amount)
        
        top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'success': True,
            'analytics_type': 'overview',
            'data': {
                'total_transactions': total_transactions,
                'total_spending': float(total_spending),
                'total_income': float(total_income),
                'net_flow': float(net_flow),
                'average_transaction': float(average_transaction),
                'top_categories': [
                    {'category': cat, 'amount': float(amount)}
                    for cat, amount in top_categories
                ],
                'monthly_trends': []  # Would calculate monthly trends
            }
        }
    
    def _generate_spending_analytics(self, account: PlaidAccount, transactions: List[PlaidTransaction]) -> Dict[str, Any]:
        """Generate spending analytics for an account"""
        spending_transactions = [t for t in transactions if t.amount < 0]
        
        if not spending_transactions:
            return {
                'success': True,
                'analytics_type': 'spending',
                'data': {
                    'total_spending': 0,
                    'spending_by_category': [],
                    'spending_by_month': [],
                    'largest_expenses': []
                }
            }
        
        # Calculate spending by category
        category_spending = {}
        for transaction in spending_transactions:
            category = transaction.category[0] if transaction.category else 'Other'
            category_spending[category] = category_spending.get(category, 0) + abs(transaction.amount)
        
        # Get largest expenses
        largest_expenses = sorted(spending_transactions, key=lambda x: abs(x.amount))[-10:]
        
        return {
            'success': True,
            'analytics_type': 'spending',
            'data': {
                'total_spending': float(sum(abs(t.amount) for t in spending_transactions)),
                'spending_by_category': [
                    {'category': cat, 'amount': float(amount)}
                    for cat, amount in category_spending.items()
                ],
                'spending_by_month': [],  # Would calculate monthly spending
                'largest_expenses': [
                    {
                        'name': t.name,
                        'amount': float(abs(t.amount)),
                        'date': t.date.isoformat(),
                        'category': t.category[0] if t.category else 'Other'
                    }
                    for t in largest_expenses
                ]
            }
        }
    
    def _generate_income_analytics(self, account: PlaidAccount, transactions: List[PlaidTransaction]) -> Dict[str, Any]:
        """Generate income analytics for an account"""
        income_transactions = [t for t in transactions if t.amount > 0]
        
        if not income_transactions:
            return {
                'success': True,
                'analytics_type': 'income',
                'data': {
                    'total_income': 0,
                    'income_sources': [],
                    'income_by_month': [],
                    'largest_income': []
                }
            }
        
        # Calculate income by source (using transaction names)
        source_income = {}
        for transaction in income_transactions:
            source = transaction.name
            source_income[source] = source_income.get(source, 0) + transaction.amount
        
        # Get largest income transactions
        largest_income = sorted(income_transactions, key=lambda x: x.amount, reverse=True)[:10]
        
        return {
            'success': True,
            'analytics_type': 'income',
            'data': {
                'total_income': float(sum(t.amount for t in income_transactions)),
                'income_sources': [
                    {'source': source, 'amount': float(amount)}
                    for source, amount in source_income.items()
                ],
                'income_by_month': [],  # Would calculate monthly income
                'largest_income': [
                    {
                        'name': t.name,
                        'amount': float(t.amount),
                        'date': t.date.isoformat()
                    }
                    for t in largest_income
                ]
            }
        }
    
    def _generate_trend_analytics(self, account: PlaidAccount, transactions: List[PlaidTransaction]) -> Dict[str, Any]:
        """Generate trend analytics for an account"""
        if not transactions:
            return {
                'success': True,
                'analytics_type': 'trends',
                'data': {
                    'spending_trends': [],
                    'income_trends': [],
                    'balance_trends': []
                }
            }
        
        # Group transactions by month
        monthly_data = {}
        for transaction in transactions:
            month_key = transaction.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'spending': 0, 'income': 0}
            
            if transaction.amount < 0:
                monthly_data[month_key]['spending'] += abs(transaction.amount)
            else:
                monthly_data[month_key]['income'] += transaction.amount
        
        # Convert to trend data
        spending_trends = [
            {'month': month, 'amount': float(data['spending'])}
            for month, data in sorted(monthly_data.items())
        ]
        
        income_trends = [
            {'month': month, 'amount': float(data['income'])}
            for month, data in sorted(monthly_data.items())
        ]
        
        return {
            'success': True,
            'analytics_type': 'trends',
            'data': {
                'spending_trends': spending_trends,
                'income_trends': income_trends,
                'balance_trends': []  # Would calculate balance trends
            }
        }
    
    def _send_account_connection_notification(self, user_id: str, connection: PlaidConnection, 
                                            accounts: List[PlaidAccount]):
        """Send notification about successful account connection"""
        try:
            notification_data = {
                'user_id': user_id,
                'notification_type': 'account_connection_success',
                'title': 'Bank Account Connected Successfully',
                'message': f'Successfully connected {len(accounts)} account(s) from {connection.institution_name}',
                'priority': 'low',
                'channels': ['in_app'],
                'action_required': False,
                'metadata': {
                    'institution_name': connection.institution_name,
                    'accounts_count': len(accounts),
                    'connection_id': str(connection.id)
                }
            }
            
            self.notification_service.send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error sending account connection notification: {e}")
    
    def _send_account_disconnection_notification(self, user_id: str, connection: PlaidConnection, 
                                               account: PlaidAccount, reason: str):
        """Send notification about account disconnection"""
        try:
            notification_data = {
                'user_id': user_id,
                'notification_type': 'account_disconnected',
                'title': 'Bank Account Disconnected',
                'message': f'Your account from {connection.institution_name} has been disconnected',
                'priority': 'medium',
                'channels': ['email', 'in_app'],
                'action_required': False,
                'metadata': {
                    'institution_name': connection.institution_name,
                    'account_name': account.name,
                    'reason': reason,
                    'connection_id': str(connection.id)
                }
            }
            
            self.notification_service.send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error sending account disconnection notification: {e}") 