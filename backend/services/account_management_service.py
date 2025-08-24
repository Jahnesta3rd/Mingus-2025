"""
Account Management Service for MINGUS

This service provides comprehensive account management features:
- Account nickname and categorization
- Primary account designation
- Account status monitoring (active/inactive/error)
- Re-authentication workflows
- Account unlinking and data cleanup
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, update
from sqlalchemy.exc import SQLAlchemyError

from backend.models.bank_account_models import BankAccount, PlaidConnection, TransactionSync, AccountBalance, BankingPreferences
from backend.models.user_models import User
from backend.services.plaid_integration import PlaidIntegrationService
from backend.services.notification_service import NotificationService
from backend.services.audit_service import AuditService
from backend.services.tier_access_control_service import TierAccessControlService
from backend.utils.encryption import encrypt_data, decrypt_data
from backend.utils.validation import validate_email, validate_phone

logger = logging.getLogger(__name__)

class AccountStatus(Enum):
    """Account status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_VERIFICATION = "pending_verification"
    MAINTENANCE = "maintenance"
    DISCONNECTED = "disconnected"
    ARCHIVED = "archived"

class AccountType(Enum):
    """Account type categorization"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    INVESTMENT = "investment"
    MORTGAGE = "mortgage"
    BUSINESS = "business"
    OTHER = "other"

class ReAuthStatus(Enum):
    """Re-authentication status"""
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AccountCustomization:
    """Account customization data"""
    nickname: str
    category: str
    color: str
    icon: str
    is_primary: bool
    is_hidden: bool
    notes: str
    tags: List[str]

@dataclass
class AccountStatusInfo:
    """Account status information"""
    status: AccountStatus
    last_sync_at: Optional[datetime]
    last_error_at: Optional[datetime]
    error_message: Optional[str]
    sync_frequency: str
    re_auth_required: bool
    re_auth_status: ReAuthStatus
    connection_health: str
    data_freshness: str

@dataclass
class ReAuthWorkflow:
    """Re-authentication workflow data"""
    workflow_id: str
    account_id: str
    user_id: str
    status: ReAuthStatus
    initiated_at: datetime
    expires_at: datetime
    link_token: Optional[str]
    error_message: Optional[str]
    attempts: int
    max_attempts: int

class AccountManagementService:
    """Service for comprehensive account management"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db_session = db_session
        self.config = config
        self.plaid_service = PlaidIntegrationService(db_session, config)
        self.notification_service = NotificationService(db_session, config)
        self.audit_service = AuditService(db_session)
        self.tier_access_service = TierAccessControlService(db_session, config)
        
        # Re-authentication workflow storage (in production, use Redis)
        self.re_auth_workflows: Dict[str, ReAuthWorkflow] = {}
        self.workflow_timeout = timedelta(hours=24)
    
    def customize_account(self, user_id: str, account_id: str, customization: AccountCustomization) -> Dict[str, Any]:
        """
        Customize account settings (nickname, category, etc.)
        
        Args:
            user_id: User ID
            account_id: Account ID to customize
            customization: Customization data
            
        Returns:
            Customization result
        """
        try:
            # Validate account ownership
            account = self.db_session.query(BankAccount).filter(
                and_(
                    BankAccount.id == account_id,
                    BankAccount.user_id == user_id,
                    BankAccount.is_active == True
                )
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found or access denied'
                }
            
            # Get or create banking preferences
            preferences = self.db_session.query(BankingPreferences).filter(
                and_(
                    BankingPreferences.account_id == account_id,
                    BankingPreferences.user_id == user_id
                )
            ).first()
            
            if not preferences:
                preferences = BankingPreferences(
                    user_id=user_id,
                    account_id=account_id,
                    created_at=datetime.utcnow()
                )
                self.db_session.add(preferences)
            
            # Update customization settings
            preferences.account_nickname = customization.nickname
            preferences.account_category = customization.category
            preferences.account_color = customization.color
            preferences.account_icon = customization.icon
            preferences.is_primary_account = customization.is_primary
            preferences.is_hidden = customization.is_hidden
            preferences.account_notes = customization.notes
            preferences.account_tags = json.dumps(customization.tags)
            preferences.updated_at = datetime.utcnow()
            
            # Handle primary account designation
            if customization.is_primary:
                # Remove primary designation from other accounts
                self.db_session.query(BankingPreferences).filter(
                    and_(
                        BankingPreferences.user_id == user_id,
                        BankingPreferences.account_id != account_id,
                        BankingPreferences.is_primary_account == True
                    )
                ).update({
                    'is_primary_account': False,
                    'updated_at': datetime.utcnow()
                })
            
            # Commit changes
            self.db_session.commit()
            
            # Audit the customization
            self.audit_service.log_event(
                user_id=user_id,
                event_type='account_customized',
                details={
                    'account_id': account_id,
                    'customization': {
                        'nickname': customization.nickname,
                        'category': customization.category,
                        'is_primary': customization.is_primary,
                        'is_hidden': customization.is_hidden
                    }
                }
            )
            
            return {
                'success': True,
                'message': 'Account customized successfully',
                'account_id': account_id,
                'customization': {
                    'nickname': customization.nickname,
                    'category': customization.category,
                    'color': customization.color,
                    'icon': customization.icon,
                    'is_primary': customization.is_primary,
                    'is_hidden': customization.is_hidden,
                    'notes': customization.notes,
                    'tags': customization.tags
                }
            }
            
        except Exception as e:
            logger.error(f"Error customizing account {account_id} for user {user_id}: {str(e)}")
            self.db_session.rollback()
            return {
                'success': False,
                'error': 'customization_failed',
                'message': 'Failed to customize account'
            }
    
    def get_account_status(self, user_id: str, account_id: str) -> Dict[str, Any]:
        """
        Get comprehensive account status information
        
        Args:
            user_id: User ID
            account_id: Account ID
            
        Returns:
            Account status information
        """
        try:
            # Get account and related data
            account = self.db_session.query(BankAccount).filter(
                and_(
                    BankAccount.id == account_id,
                    BankAccount.user_id == user_id
                )
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found'
                }
            
            # Get latest sync information
            latest_sync = self.db_session.query(TransactionSync).filter(
                TransactionSync.account_id == account_id
            ).order_by(TransactionSync.created_at.desc()).first()
            
            # Get latest balance
            latest_balance = self.db_session.query(AccountBalance).filter(
                AccountBalance.account_id == account_id
            ).order_by(AccountBalance.created_at.desc()).first()
            
            # Determine account status
            status = self._determine_account_status(account, latest_sync)
            
            # Check re-authentication requirements
            re_auth_required = self._check_re_auth_required(account)
            re_auth_status = self._get_re_auth_status(account_id)
            
            # Determine connection health
            connection_health = self._assess_connection_health(account, latest_sync)
            
            # Determine data freshness
            data_freshness = self._assess_data_freshness(latest_sync, latest_balance)
            
            # Get sync frequency
            sync_frequency = self._get_sync_frequency(account)
            
            status_info = AccountStatusInfo(
                status=status,
                last_sync_at=latest_sync.created_at if latest_sync else None,
                last_error_at=account.last_error_at,
                error_message=account.error_message,
                sync_frequency=sync_frequency,
                re_auth_required=re_auth_required,
                re_auth_status=re_auth_status,
                connection_health=connection_health,
                data_freshness=data_freshness
            )
            
            return {
                'success': True,
                'account_id': account_id,
                'status_info': {
                    'status': status_info.status.value,
                    'last_sync_at': status_info.last_sync_at.isoformat() if status_info.last_sync_at else None,
                    'last_error_at': status_info.last_error_at.isoformat() if status_info.last_error_at else None,
                    'error_message': status_info.error_message,
                    'sync_frequency': status_info.sync_frequency,
                    're_auth_required': status_info.re_auth_required,
                    're_auth_status': status_info.re_auth_status.value,
                    'connection_health': status_info.connection_health,
                    'data_freshness': status_info.data_freshness
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting account status for account {account_id}, user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'status_check_failed',
                'message': 'Failed to get account status'
            }
    
    def initiate_re_authentication(self, user_id: str, account_id: str) -> Dict[str, Any]:
        """
        Initiate re-authentication workflow for an account
        
        Args:
            user_id: User ID
            account_id: Account ID
            
        Returns:
            Re-authentication workflow result
        """
        try:
            # Validate account ownership
            account = self.db_session.query(BankAccount).filter(
                and_(
                    BankAccount.id == account_id,
                    BankAccount.user_id == user_id,
                    BankAccount.is_active == True
                )
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found or access denied'
                }
            
            # Check if re-authentication is already in progress
            existing_workflow = self._get_re_auth_workflow(account_id)
            if existing_workflow and existing_workflow.status == ReAuthStatus.IN_PROGRESS:
                return {
                    'success': False,
                    'error': 'reauth_in_progress',
                    'message': 'Re-authentication already in progress',
                    'workflow_id': existing_workflow.workflow_id
                }
            
            # Create new re-authentication workflow
            workflow_id = self._generate_workflow_id()
            expires_at = datetime.utcnow() + self.workflow_timeout
            
            # Get Plaid link token for re-authentication
            link_token_result = self.plaid_service.create_link_token(
                user_id=user_id,
                client_name="MINGUS",
                country_codes=["US"],
                language="en",
                access_token=account.plaid_access_token,
                update_mode="update"
            )
            
            if not link_token_result.success:
                return {
                    'success': False,
                    'error': 'link_token_failed',
                    'message': 'Failed to create re-authentication link'
                }
            
            # Create workflow
            workflow = ReAuthWorkflow(
                workflow_id=workflow_id,
                account_id=account_id,
                user_id=user_id,
                status=ReAuthStatus.IN_PROGRESS,
                initiated_at=datetime.utcnow(),
                expires_at=expires_at,
                link_token=link_token_result.link_token,
                error_message=None,
                attempts=0,
                max_attempts=3
            )
            
            # Store workflow
            self.re_auth_workflows[workflow_id] = workflow
            
            # Update account status
            account.status = AccountStatus.PENDING_VERIFICATION.value
            account.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db_session.commit()
            
            # Send notification
            self.notification_service.send_notification(
                user_id=user_id,
                notification_type='reauth_required',
                data={
                    'account_id': account_id,
                    'account_name': account.name,
                    'workflow_id': workflow_id
                }
            )
            
            # Audit the re-authentication initiation
            self.audit_service.log_event(
                user_id=user_id,
                event_type='reauth_initiated',
                details={
                    'account_id': account_id,
                    'workflow_id': workflow_id
                }
            )
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'link_token': link_token_result.link_token,
                'expires_at': expires_at.isoformat(),
                'message': 'Re-authentication initiated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error initiating re-authentication for account {account_id}, user {user_id}: {str(e)}")
            self.db_session.rollback()
            return {
                'success': False,
                'error': 'reauth_initiation_failed',
                'message': 'Failed to initiate re-authentication'
            }
    
    def complete_re_authentication(self, workflow_id: str, public_token: str) -> Dict[str, Any]:
        """
        Complete re-authentication workflow
        
        Args:
            workflow_id: Re-authentication workflow ID
            public_token: Plaid public token from successful re-authentication
            
        Returns:
            Completion result
        """
        try:
            # Get workflow
            workflow = self.re_auth_workflows.get(workflow_id)
            if not workflow:
                return {
                    'success': False,
                    'error': 'workflow_not_found',
                    'message': 'Re-authentication workflow not found'
                }
            
            # Check if workflow is expired
            if datetime.utcnow() > workflow.expires_at:
                return {
                    'success': False,
                    'error': 'workflow_expired',
                    'message': 'Re-authentication workflow has expired'
                }
            
            # Check if workflow is in progress
            if workflow.status != ReAuthStatus.IN_PROGRESS:
                return {
                    'success': False,
                    'error': 'invalid_workflow_status',
                    'message': 'Re-authentication workflow is not in progress'
                }
            
            # Get account
            account = self.db_session.query(BankAccount).filter(
                BankAccount.id == workflow.account_id
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found'
                }
            
            # Update access token with Plaid
            update_result = self.plaid_service.update_access_token(
                access_token=account.plaid_access_token,
                public_token=public_token
            )
            
            if not update_result.success:
                # Increment attempts
                workflow.attempts += 1
                workflow.error_message = update_result.error
                
                if workflow.attempts >= workflow.max_attempts:
                    workflow.status = ReAuthStatus.FAILED
                    account.status = AccountStatus.ERROR.value
                    account.error_message = f"Re-authentication failed after {workflow.max_attempts} attempts"
                else:
                    # Allow retry
                    return {
                        'success': False,
                        'error': 'reauth_failed',
                        'message': 'Re-authentication failed, please try again',
                        'attempts_remaining': workflow.max_attempts - workflow.attempts
                    }
            else:
                # Re-authentication successful
                workflow.status = ReAuthStatus.COMPLETED
                account.status = AccountStatus.ACTIVE.value
                account.error_message = None
                account.last_sync_at = datetime.utcnow()
                account.updated_at = datetime.utcnow()
                
                # Test the connection
                test_result = self.plaid_service.get_account_balances(account.plaid_access_token)
                if test_result.success:
                    # Update account balances
                    for balance_data in test_result.balances:
                        if balance_data.account_id == account.plaid_account_id:
                            self._update_account_balance(account.id, balance_data)
                
                # Send success notification
                self.notification_service.send_notification(
                    user_id=workflow.user_id,
                    notification_type='reauth_success',
                    data={
                        'account_id': workflow.account_id,
                        'account_name': account.name
                    }
                )
            
            # Commit changes
            self.db_session.commit()
            
            # Audit the re-authentication completion
            self.audit_service.log_event(
                user_id=workflow.user_id,
                event_type='reauth_completed',
                details={
                    'account_id': workflow.account_id,
                    'workflow_id': workflow_id,
                    'status': workflow.status.value,
                    'success': workflow.status == ReAuthStatus.COMPLETED
                }
            )
            
            return {
                'success': workflow.status == ReAuthStatus.COMPLETED,
                'workflow_id': workflow_id,
                'status': workflow.status.value,
                'message': 'Re-authentication completed successfully' if workflow.status == ReAuthStatus.COMPLETED else 'Re-authentication failed'
            }
            
        except Exception as e:
            logger.error(f"Error completing re-authentication workflow {workflow_id}: {str(e)}")
            self.db_session.rollback()
            return {
                'success': False,
                'error': 'reauth_completion_failed',
                'message': 'Failed to complete re-authentication'
            }
    
    def unlink_account(self, user_id: str, account_id: str, cleanup_data: bool = True) -> Dict[str, Any]:
        """
        Unlink account and optionally cleanup data
        
        Args:
            user_id: User ID
            account_id: Account ID to unlink
            cleanup_data: Whether to cleanup account data
            
        Returns:
            Unlink result
        """
        try:
            # Validate account ownership
            account = self.db_session.query(BankAccount).filter(
                and_(
                    BankAccount.id == account_id,
                    BankAccount.user_id == user_id,
                    BankAccount.is_active == True
                )
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found or access denied'
                }
            
            # Get account details for audit
            account_name = account.name
            institution_name = account.institution_name
            
            # Remove from Plaid (if access token exists)
            if account.plaid_access_token:
                try:
                    self.plaid_service.remove_connection(account.plaid_access_token)
                except Exception as e:
                    logger.warning(f"Failed to remove Plaid connection for account {account_id}: {str(e)}")
            
            if cleanup_data:
                # Archive account data
                account.is_active = False
                account.status = AccountStatus.ARCHIVED.value
                account.archived_at = datetime.utcnow()
                account.updated_at = datetime.utcnow()
                
                # Archive related data
                self._archive_account_data(account_id)
                
                # Remove from tier usage tracking
                self.tier_access_service.clear_usage_cache(user_id)
                
                message = 'Account unlinked and data archived successfully'
            else:
                # Just mark as disconnected
                account.status = AccountStatus.DISCONNECTED.value
                account.updated_at = datetime.utcnow()
                
                message = 'Account unlinked successfully'
            
            # Commit changes
            self.db_session.commit()
            
            # Send notification
            self.notification_service.send_notification(
                user_id=user_id,
                notification_type='account_unlinked',
                data={
                    'account_id': account_id,
                    'account_name': account_name,
                    'institution_name': institution_name,
                    'cleanup_data': cleanup_data
                }
            )
            
            # Audit the account unlinking
            self.audit_service.log_event(
                user_id=user_id,
                event_type='account_unlinked',
                details={
                    'account_id': account_id,
                    'account_name': account_name,
                    'institution_name': institution_name,
                    'cleanup_data': cleanup_data
                }
            )
            
            return {
                'success': True,
                'account_id': account_id,
                'message': message,
                'cleanup_data': cleanup_data
            }
            
        except Exception as e:
            logger.error(f"Error unlinking account {account_id} for user {user_id}: {str(e)}")
            self.db_session.rollback()
            return {
                'success': False,
                'error': 'unlink_failed',
                'message': 'Failed to unlink account'
            }
    
    def get_user_accounts(self, user_id: str, include_archived: bool = False) -> Dict[str, Any]:
        """
        Get all user accounts with customization and status information
        
        Args:
            user_id: User ID
            include_archived: Whether to include archived accounts
            
        Returns:
            User accounts with details
        """
        try:
            # Build query
            query = self.db_session.query(BankAccount).filter(BankAccount.user_id == user_id)
            
            if not include_archived:
                query = query.filter(BankAccount.is_active == True)
            
            accounts = query.all()
            
            # Get customization preferences for all accounts
            account_ids = [account.id for account in accounts]
            preferences = self.db_session.query(BankingPreferences).filter(
                BankingPreferences.account_id.in_(account_ids)
            ).all()
            
            preferences_map = {pref.account_id: pref for pref in preferences}
            
            # Build response
            account_details = []
            for account in accounts:
                # Get customization
                pref = preferences_map.get(account.id)
                customization = {
                    'nickname': pref.account_nickname if pref else account.name,
                    'category': pref.account_category if pref else 'other',
                    'color': pref.account_color if pref else '#667eea',
                    'icon': pref.account_icon if pref else '🏦',
                    'is_primary': pref.is_primary_account if pref else False,
                    'is_hidden': pref.is_hidden if pref else False,
                    'notes': pref.account_notes if pref else None,
                    'tags': json.loads(pref.account_tags) if pref and pref.account_tags else []
                }
                
                # Get status information
                status_info = self.get_account_status(user_id, account.id)
                
                account_details.append({
                    'id': account.id,
                    'name': account.name,
                    'mask': account.mask,
                    'type': account.type,
                    'subtype': account.subtype,
                    'institution_name': account.institution_name,
                    'institution_logo': account.institution_logo,
                    'status': account.status,
                    'current_balance': float(account.current_balance) if account.current_balance else 0.0,
                    'available_balance': float(account.available_balance) if account.available_balance else 0.0,
                    'currency': account.iso_currency_code,
                    'last_sync_at': account.last_sync_at.isoformat() if account.last_sync_at else None,
                    'created_at': account.created_at.isoformat(),
                    'customization': customization,
                    'status_info': status_info.get('status_info', {}) if status_info.get('success') else {}
                })
            
            return {
                'success': True,
                'accounts': account_details,
                'total_accounts': len(account_details),
                'active_accounts': len([a for a in account_details if a['status'] == 'active']),
                'primary_account': next((a for a in account_details if a['customization']['is_primary']), None)
            }
            
        except Exception as e:
            logger.error(f"Error getting user accounts for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'accounts_fetch_failed',
                'message': 'Failed to get user accounts'
            }
    
    def _determine_account_status(self, account: BankAccount, latest_sync: Optional[TransactionSync]) -> AccountStatus:
        """Determine account status based on various factors"""
        if account.status == AccountStatus.ARCHIVED.value:
            return AccountStatus.ARCHIVED
        
        if account.status == AccountStatus.DISCONNECTED.value:
            return AccountStatus.DISCONNECTED
        
        if account.error_message:
            return AccountStatus.ERROR
        
        if not latest_sync:
            return AccountStatus.INACTIVE
        
        # Check if sync is recent (within 24 hours for active accounts)
        sync_age = datetime.utcnow() - latest_sync.created_at
        if sync_age > timedelta(hours=24):
            return AccountStatus.INACTIVE
        
        return AccountStatus.ACTIVE
    
    def _check_re_auth_required(self, account: BankAccount) -> bool:
        """Check if re-authentication is required"""
        # Check for Plaid item error status
        if account.error_message and 'ITEM_LOGIN_REQUIRED' in account.error_message:
            return True
        
        # Check for stale access token (older than 90 days)
        if account.last_sync_at:
            token_age = datetime.utcnow() - account.last_sync_at
            if token_age > timedelta(days=90):
                return True
        
        return False
    
    def _get_re_auth_status(self, account_id: str) -> ReAuthStatus:
        """Get re-authentication status for account"""
        for workflow in self.re_auth_workflows.values():
            if workflow.account_id == account_id:
                return workflow.status
        return ReAuthStatus.NOT_REQUIRED
    
    def _assess_connection_health(self, account: BankAccount, latest_sync: Optional[TransactionSync]) -> str:
        """Assess connection health"""
        if not latest_sync:
            return "unknown"
        
        sync_age = datetime.utcnow() - latest_sync.created_at
        
        if sync_age <= timedelta(hours=1):
            return "excellent"
        elif sync_age <= timedelta(hours=6):
            return "good"
        elif sync_age <= timedelta(hours=24):
            return "fair"
        else:
            return "poor"
    
    def _assess_data_freshness(self, latest_sync: Optional[TransactionSync], latest_balance: Optional[AccountBalance]) -> str:
        """Assess data freshness"""
        if not latest_sync and not latest_balance:
            return "unknown"
        
        latest_data = max(
            latest_sync.created_at if latest_sync else datetime.min,
            latest_balance.created_at if latest_balance else datetime.min
        )
        
        data_age = datetime.utcnow() - latest_data
        
        if data_age <= timedelta(hours=1):
            return "real_time"
        elif data_age <= timedelta(hours=6):
            return "recent"
        elif data_age <= timedelta(hours=24):
            return "daily"
        else:
            return "stale"
    
    def _get_sync_frequency(self, account: BankAccount) -> str:
        """Get sync frequency for account"""
        # This could be determined by tier or account settings
        # For now, return a default based on account type
        if account.type == 'credit':
            return "daily"
        else:
            return "real_time"
    
    def _get_re_auth_workflow(self, account_id: str) -> Optional[ReAuthWorkflow]:
        """Get re-authentication workflow for account"""
        for workflow in self.re_auth_workflows.values():
            if workflow.account_id == account_id:
                return workflow
        return None
    
    def _generate_workflow_id(self) -> str:
        """Generate unique workflow ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _update_account_balance(self, account_id: str, balance_data: Any):
        """Update account balance"""
        try:
            balance = AccountBalance(
                account_id=account_id,
                balance_type='current',
                amount=balance_data.current,
                currency=balance_data.iso_currency_code,
                created_at=datetime.utcnow()
            )
            self.db_session.add(balance)
        except Exception as e:
            logger.error(f"Error updating account balance for account {account_id}: {str(e)}")
    
    def _archive_account_data(self, account_id: str):
        """Archive account-related data"""
        try:
            # Archive transaction syncs
            self.db_session.query(TransactionSync).filter(
                TransactionSync.account_id == account_id
            ).update({
                'is_active': False,
                'archived_at': datetime.utcnow()
            })
            
            # Archive account balances
            self.db_session.query(AccountBalance).filter(
                AccountBalance.account_id == account_id
            ).update({
                'is_active': False,
                'archived_at': datetime.utcnow()
            })
            
            # Archive banking preferences
            self.db_session.query(BankingPreferences).filter(
                BankingPreferences.account_id == account_id
            ).update({
                'is_active': False,
                'archived_at': datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error archiving account data for account {account_id}: {str(e)}")
    
    def cleanup_expired_workflows(self):
        """Clean up expired re-authentication workflows"""
        try:
            expired_workflows = []
            for workflow_id, workflow in self.re_auth_workflows.items():
                if datetime.utcnow() > workflow.expires_at:
                    expired_workflows.append(workflow_id)
            
            for workflow_id in expired_workflows:
                workflow = self.re_auth_workflows[workflow_id]
                workflow.status = ReAuthStatus.FAILED
                workflow.error_message = "Workflow expired"
                
                # Update account status
                account = self.db_session.query(BankAccount).filter(
                    BankAccount.id == workflow.account_id
                ).first()
                
                if account:
                    account.status = AccountStatus.ERROR.value
                    account.error_message = "Re-authentication workflow expired"
                    account.updated_at = datetime.utcnow()
                
                del self.re_auth_workflows[workflow_id]
            
            if expired_workflows:
                self.db_session.commit()
                logger.info(f"Cleaned up {len(expired_workflows)} expired re-authentication workflows")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired workflows: {str(e)}")
            self.db_session.rollback() 