"""
Account Linking Service for MINGUS

This service handles the complete account linking workflow:
- Plaid Link integration for account selection
- Multi-factor authentication handling
- Institution credential verification
- Account ownership verification
- Connection success confirmation
"""

import logging
import json
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.bank_account_models import (
    BankAccount, PlaidConnection, BankingPreferences
)
from backend.models.plaid_models import PlaidInstitution
from backend.integrations.plaid_integration import PlaidIntegrationService
from backend.services.plaid_subscription_service import PlaidSubscriptionService
from backend.services.notification_service import NotificationService
from backend.services.audit_service import AuditService
from backend.services.tier_access_control_service import TierAccessControlService
from backend.utils.encryption import encrypt_data, decrypt_data
from backend.utils.validation import validate_email, validate_phone

logger = logging.getLogger(__name__)

class LinkingStatus(Enum):
    """Account linking status enumeration"""
    INITIATED = "initiated"
    LINK_TOKEN_CREATED = "link_token_created"
    ACCOUNTS_SELECTED = "accounts_selected"
    MFA_REQUIRED = "mfa_required"
    MFA_COMPLETED = "mfa_completed"
    CREDENTIALS_VERIFIED = "credentials_verified"
    OWNERSHIP_VERIFIED = "ownership_verified"
    CONNECTION_ESTABLISHED = "connection_established"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MFAType(Enum):
    """Multi-factor authentication type enumeration"""
    SMS = "sms"
    EMAIL = "email"
    PHONE = "phone"
    SECURITY_QUESTIONS = "security_questions"
    AUTHENTICATOR_APP = "authenticator_app"
    HARDWARE_TOKEN = "hardware_token"
    BIOMETRIC = "biometric"

class VerificationMethod(Enum):
    """Account ownership verification method enumeration"""
    MICRO_DEPOSITS = "micro_deposits"
    ACCOUNT_STATEMENT = "account_statement"
    BANK_VERIFICATION = "bank_verification"
    DOCUMENT_UPLOAD = "document_upload"
    PHONE_VERIFICATION = "phone_verification"
    EMAIL_VERIFICATION = "email_verification"

@dataclass
class LinkingSession:
    """Account linking session data"""
    session_id: str
    user_id: str
    status: LinkingStatus
    link_token: Optional[str] = None
    public_token: Optional[str] = None
    access_token: Optional[str] = None
    item_id: Optional[str] = None
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    selected_accounts: List[Dict[str, Any]] = None
    mfa_required: bool = False
    mfa_type: Optional[MFAType] = None
    mfa_questions: List[Dict[str, str]] = None
    verification_required: bool = False
    verification_method: Optional[VerificationMethod] = None
    created_at: datetime = None
    updated_at: datetime = None
    expires_at: datetime = None
    metadata: Dict[str, Any] = None

@dataclass
class MFASession:
    """Multi-factor authentication session data"""
    session_id: str
    linking_session_id: str
    mfa_type: MFAType
    questions: List[Dict[str, str]] = None
    attempts_remaining: int = 3
    created_at: datetime = None
    expires_at: datetime = None
    completed: bool = False

@dataclass
class VerificationSession:
    """Account ownership verification session data"""
    session_id: str
    linking_session_id: str
    verification_method: VerificationMethod
    micro_deposits: List[Dict[str, Any]] = None
    verification_code: Optional[str] = None
    attempts_remaining: int = 3
    created_at: datetime = None
    expires_at: datetime = None
    completed: bool = False

class AccountLinkingService:
    """Service for handling complete account linking workflow"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db_session = db_session
        self.config = config
        self.plaid_service = PlaidIntegrationService(db_session, config)
        self.subscription_service = PlaidSubscriptionService(db_session)
        self.notification_service = NotificationService(db_session, config)
        self.audit_service = AuditService(db_session)
        self.tier_access_service = TierAccessControlService(db_session, config)
        
        # Session storage (in production, use Redis or similar)
        self.linking_sessions: Dict[str, LinkingSession] = {}
        self.mfa_sessions: Dict[str, MFASession] = {}
        self.verification_sessions: Dict[str, VerificationSession] = {}
        
        # Configuration
        self.session_timeout = timedelta(hours=2)
        self.mfa_timeout = timedelta(minutes=15)
        self.verification_timeout = timedelta(days=7)
        self.max_mfa_attempts = 3
        self.max_verification_attempts = 3
    
    def initiate_linking(self, user_id: str, institution_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate the account linking process
        
        Args:
            user_id: User ID initiating the linking process
            institution_id: Optional specific institution ID to link
            
        Returns:
            Dictionary containing session information and link token
        """
        try:
            # Check tier-based access controls
            access_result = self.tier_access_service.check_account_linking_access(user_id, institution_id)
            
            if access_result['access'].value == 'upgrade_required':
                return {
                    'success': False,
                    'error': 'upgrade_required',
                    'message': access_result['reason'],
                    'upgrade_prompt': access_result['upgrade_prompt'],
                    'current_tier': access_result['current_tier']
                }
            
            if access_result['access'].value == 'limit_reached':
                return {
                    'success': False,
                    'error': 'limit_reached',
                    'message': access_result['reason'],
                    'upgrade_prompt': access_result['upgrade_prompt'],
                    'current_tier': access_result['current_tier'],
                    'usage': access_result['usage']
                }
            
            # Create linking session
            session_id = self._generate_session_id()
            session = LinkingSession(
                session_id=session_id,
                user_id=user_id,
                status=LinkingStatus.INITIATED,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.session_timeout,
                metadata={
                    'institution_id': institution_id,
                    'tier_info': {
                        'current_tier': access_result['current_tier'],
                        'limits': access_result['limits'],
                        'usage': access_result['usage']
                    }
                }
            )
            
            # Create Plaid link token
            link_token_result = self.plaid_service.create_link_token(
                user_id=user_id,
                institution_id=institution_id
            )
            
            if not link_token_result.success:
                return {
                    'success': False,
                    'error': 'link_token_creation_failed',
                    'message': link_token_result.error
                }
            
            session.link_token = link_token_result.link_token
            session.status = LinkingStatus.LINK_TOKEN_CREATED
            session.updated_at = datetime.utcnow()
            
            # Store session
            self.linking_sessions[session_id] = session
            
            # Audit log
            self.audit_service.log_event(
                user_id=user_id,
                event_type='account_linking_initiated',
                details={'session_id': session_id, 'institution_id': institution_id}
            )
            
            return {
                'success': True,
                'session_id': session_id,
                'link_token': link_token_result.link_token,
                'expires_at': session.expires_at.isoformat(),
                'status': session.status.value,
                'tier_info': {
                    'current_tier': access_result['current_tier'],
                    'limits': access_result['limits'],
                    'usage': access_result['usage']
                }
            }
            
        except Exception as e:
            logger.error(f"Error initiating account linking for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'initiation_failed',
                'message': 'Failed to initiate account linking process'
            }
    
    def handle_account_selection(self, session_id: str, public_token: str, 
                               account_ids: List[str]) -> Dict[str, Any]:
        """
        Handle account selection from Plaid Link
        
        Args:
            session_id: Linking session ID
            public_token: Plaid public token
            account_ids: List of selected account IDs
            
        Returns:
            Dictionary containing next steps in the linking process
        """
        try:
            session = self._get_linking_session(session_id)
            if not session:
                return {'success': False, 'error': 'invalid_session'}
            
            # Exchange public token for access token
            exchange_result = self.plaid_service.exchange_public_token(public_token)
            if not exchange_result.success:
                return {
                    'success': False,
                    'error': 'token_exchange_failed',
                    'message': exchange_result.error
                }
            
            # Get account information
            accounts_result = self.plaid_service.get_account_balances(exchange_result.access_token)
            if not accounts_result.success:
                return {
                    'success': False,
                    'error': 'accounts_fetch_failed',
                    'message': accounts_result.error
                }
            
            # Filter selected accounts
            selected_accounts = [
                account for account in accounts_result.accounts
                if account.account_id in account_ids
            ]
            
            # Check account limits before proceeding
            limit_check = self.tier_access_service.enforce_account_limits(
                session.user_id, len(selected_accounts)
            )
            
            if not limit_check['enforced']:
                return {
                    'success': False,
                    'error': 'account_limit_exceeded',
                    'message': limit_check['reason'],
                    'upgrade_prompt': limit_check.get('upgrade_prompt'),
                    'current_accounts': limit_check['current_accounts'],
                    'requested_addition': limit_check['requested_addition'],
                    'limit': limit_check['limit']
                }
            
            # Update session
            session.public_token = public_token
            session.access_token = exchange_result.access_token
            session.item_id = exchange_result.item_id
            session.selected_accounts = selected_accounts
            session.status = LinkingStatus.ACCOUNTS_SELECTED
            session.updated_at = datetime.utcnow()
            
            # Get institution information
            institution_info = self._get_institution_info(exchange_result.item_id)
            if institution_info:
                session.institution_id = institution_info.get('institution_id')
                session.institution_name = institution_info.get('name')
            
            # Check if MFA is required
            mfa_required = self._check_mfa_requirement(exchange_result.access_token)
            session.mfa_required = mfa_required
            
            if mfa_required:
                # Initialize MFA session
                mfa_session = self._create_mfa_session(session_id, exchange_result.access_token)
                session.mfa_type = mfa_session.mfa_type
                session.mfa_questions = mfa_session.questions
                session.status = LinkingStatus.MFA_REQUIRED
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'status': session.status.value,
                    'mfa_required': True,
                    'mfa_type': mfa_session.mfa_type.value,
                    'mfa_session_id': mfa_session.session_id,
                    'questions': mfa_session.questions,
                    'expires_at': mfa_session.expires_at.isoformat()
                }
            else:
                # Proceed to credential verification
                return self._proceed_to_verification(session_id)
                
        except Exception as e:
            logger.error(f"Error handling account selection for session {session_id}: {str(e)}")
            return {
                'success': False,
                'error': 'account_selection_failed',
                'message': 'Failed to process account selection'
            }
    
    def handle_mfa_challenge(self, mfa_session_id: str, answers: List[str]) -> Dict[str, Any]:
        """
        Handle multi-factor authentication challenge
        
        Args:
            mfa_session_id: MFA session ID
            answers: List of answers to MFA questions
            
        Returns:
            Dictionary containing MFA result and next steps
        """
        try:
            mfa_session = self._get_mfa_session(mfa_session_id)
            if not mfa_session:
                return {'success': False, 'error': 'invalid_mfa_session'}
            
            linking_session = self._get_linking_session(mfa_session.linking_session_id)
            if not linking_session:
                return {'success': False, 'error': 'invalid_linking_session'}
            
            # Validate MFA answers
            mfa_result = self.plaid_service.handle_mfa_challenge(
                access_token=linking_session.access_token,
                mfa_type=mfa_session.mfa_type.value,
                answers=answers
            )
            
            if not mfa_result.success:
                mfa_session.attempts_remaining -= 1
                
                if mfa_session.attempts_remaining <= 0:
                    # MFA failed, end session
                    linking_session.status = LinkingStatus.FAILED
                    linking_session.updated_at = datetime.utcnow()
                    
                    self.audit_service.log_event(
                        user_id=linking_session.user_id,
                        event_type='mfa_failed',
                        details={'session_id': linking_session.session_id, 'attempts_exceeded': True}
                    )
                    
                    return {
                        'success': False,
                        'error': 'mfa_failed',
                        'message': 'Maximum MFA attempts exceeded'
                    }
                
                return {
                    'success': False,
                    'error': 'mfa_incorrect',
                    'message': f'Incorrect answers. {mfa_session.attempts_remaining} attempts remaining.',
                    'attempts_remaining': mfa_session.attempts_remaining
                }
            
            # MFA successful
            mfa_session.completed = True
            linking_session.status = LinkingStatus.MFA_COMPLETED
            linking_session.updated_at = datetime.utcnow()
            
            # Proceed to credential verification
            return self._proceed_to_verification(linking_session.session_id)
            
        except Exception as e:
            logger.error(f"Error handling MFA challenge for session {mfa_session_id}: {str(e)}")
            return {
                'success': False,
                'error': 'mfa_processing_failed',
                'message': 'Failed to process MFA challenge'
            }
    
    def _proceed_to_verification(self, session_id: str) -> Dict[str, Any]:
        """
        Proceed to credential verification step
        
        Args:
            session_id: Linking session ID
            
        Returns:
            Dictionary containing verification requirements
        """
        try:
            session = self._get_linking_session(session_id)
            if not session:
                return {'success': False, 'error': 'invalid_session'}
            
            # Check if verification is required
            verification_required = self._check_verification_requirement(session.access_token)
            session.verification_required = verification_required
            
            if verification_required:
                # Determine verification method
                verification_method = self._determine_verification_method(session.access_token)
                session.verification_method = verification_method
                
                # Create verification session
                verification_session = self._create_verification_session(
                    session_id, verification_method, session.access_token
                )
                
                session.status = LinkingStatus.CREDENTIALS_VERIFIED
                session.updated_at = datetime.utcnow()
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'status': session.status.value,
                    'verification_required': True,
                    'verification_method': verification_method.value,
                    'verification_session_id': verification_session.session_id,
                    'micro_deposits': verification_session.micro_deposits,
                    'expires_at': verification_session.expires_at.isoformat()
                }
            else:
                # No verification required, proceed to connection establishment
                return self._establish_connection(session_id)
                
        except Exception as e:
            logger.error(f"Error proceeding to verification for session {session_id}: {str(e)}")
            return {
                'success': False,
                'error': 'verification_setup_failed',
                'message': 'Failed to setup verification process'
            }
    
    def handle_verification(self, verification_session_id: str, 
                          verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle account ownership verification
        
        Args:
            verification_session_id: Verification session ID
            verification_data: Verification data (micro-deposit amounts, etc.)
            
        Returns:
            Dictionary containing verification result and next steps
        """
        try:
            verification_session = self._get_verification_session(verification_session_id)
            if not verification_session:
                return {'success': False, 'error': 'invalid_verification_session'}
            
            linking_session = self._get_linking_session(verification_session.linking_session_id)
            if not linking_session:
                return {'success': False, 'error': 'invalid_linking_session'}
            
            # Verify based on method
            verification_result = self._verify_ownership(
                verification_session.verification_method,
                linking_session.access_token,
                verification_data
            )
            
            if not verification_result.success:
                verification_session.attempts_remaining -= 1
                
                if verification_session.attempts_remaining <= 0:
                    # Verification failed, end session
                    linking_session.status = LinkingStatus.FAILED
                    linking_session.updated_at = datetime.utcnow()
                    
                    self.audit_service.log_event(
                        user_id=linking_session.user_id,
                        event_type='verification_failed',
                        details={'session_id': linking_session.session_id, 'attempts_exceeded': True}
                    )
                    
                    return {
                        'success': False,
                        'error': 'verification_failed',
                        'message': 'Maximum verification attempts exceeded'
                    }
                
                return {
                    'success': False,
                    'error': 'verification_incorrect',
                    'message': f'Incorrect verification data. {verification_session.attempts_remaining} attempts remaining.',
                    'attempts_remaining': verification_session.attempts_remaining
                }
            
            # Verification successful
            verification_session.completed = True
            linking_session.status = LinkingStatus.OWNERSHIP_VERIFIED
            linking_session.updated_at = datetime.utcnow()
            
            # Proceed to connection establishment
            return self._establish_connection(linking_session.session_id)
            
        except Exception as e:
            logger.error(f"Error handling verification for session {verification_session_id}: {str(e)}")
            return {
                'success': False,
                'error': 'verification_processing_failed',
                'message': 'Failed to process verification'
            }
    
    def _establish_connection(self, session_id: str) -> Dict[str, Any]:
        """
        Establish the final connection and create database records
        
        Args:
            session_id: Linking session ID
            
        Returns:
            Dictionary containing connection result
        """
        try:
            session = self._get_linking_session(session_id)
            if not session:
                return {'success': False, 'error': 'invalid_session'}
            
            # Create Plaid connection record
            plaid_connection = PlaidConnection(
                user_id=session.user_id,
                access_token=encrypt_data(session.access_token),
                item_id=session.item_id,
                institution_id=session.institution_id,
                institution_name=session.institution_name,
                is_active=True,
                sync_frequency='daily'
            )
            
            self.db_session.add(plaid_connection)
            self.db_session.flush()  # Get the ID
            
            # Create bank account records
            bank_accounts = []
            for account_data in session.selected_accounts:
                bank_account = BankAccount(
                    user_id=session.user_id,
                    plaid_connection_id=plaid_connection.id,
                    account_id=account_data['account_id'],
                    name=account_data['name'],
                    mask=account_data.get('mask'),
                    type=account_data['type'],
                    subtype=account_data.get('subtype'),
                    account_type=self._classify_account_type(account_data['type'], account_data.get('subtype')),
                    status='active',
                    verification_status='verified',
                    current_balance=account_data.get('balances', {}).get('current'),
                    available_balance=account_data.get('balances', {}).get('available'),
                    credit_limit=account_data.get('balances', {}).get('limit'),
                    iso_currency_code=account_data.get('balances', {}).get('iso_currency_code', 'USD'),
                    last_sync_at=datetime.utcnow()
                )
                
                self.db_session.add(bank_account)
                bank_accounts.append(bank_account)
            
            # Create default banking preferences
            preferences = BankingPreferences(
                user_id=session.user_id,
                bank_account_id=None,  # Global preferences
                sync_frequency='daily',
                balance_alerts=True,
                email_notifications=True,
                push_notifications=True,
                notification_frequency='daily'
            )
            
            self.db_session.add(preferences)
            
            # Commit all changes
            self.db_session.commit()
            
            # Track usage for tier access control
            self.tier_access_service.track_account_linking_usage(
                session.user_id, len(bank_accounts), session.institution_id
            )
            
            # Update session status
            session.status = LinkingStatus.CONNECTION_ESTABLISHED
            session.updated_at = datetime.utcnow()
            
            # Send success notification
            self.notification_service.send_notification(
                user_id=session.user_id,
                notification_type='account_linked_successfully',
                data={
                    'institution_name': session.institution_name,
                    'account_count': len(bank_accounts),
                    'account_names': [acc.name for acc in bank_accounts]
                }
            )
            
            # Audit log
            self.audit_service.log_event(
                user_id=session.user_id,
                event_type='account_linking_completed',
                details={
                    'session_id': session_id,
                    'institution_name': session.institution_name,
                    'account_count': len(bank_accounts),
                    'connection_id': str(plaid_connection.id)
                }
            )
            
            return {
                'success': True,
                'session_id': session_id,
                'status': session.status.value,
                'connection_id': str(plaid_connection.id),
                'institution_name': session.institution_name,
                'accounts_linked': len(bank_accounts),
                'account_details': [
                    {
                        'id': str(acc.id),
                        'name': acc.name,
                        'type': acc.account_type,
                        'balance': float(acc.current_balance) if acc.current_balance else None
                    }
                    for acc in bank_accounts
                ]
            }
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error establishing connection for session {session_id}: {str(e)}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Failed to save connection to database'
            }
        except Exception as e:
            logger.error(f"Error establishing connection for session {session_id}: {str(e)}")
            return {
                'success': False,
                'error': 'connection_establishment_failed',
                'message': 'Failed to establish connection'
            }
    
    def get_linking_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current status of linking session
        
        Args:
            session_id: Linking session ID
            
        Returns:
            Dictionary containing session status and details
        """
        session = self._get_linking_session(session_id)
        if not session:
            return {'success': False, 'error': 'invalid_session'}
        
        return {
            'success': True,
            'session_id': session_id,
            'status': session.status.value,
            'institution_name': session.institution_name,
            'accounts_selected': len(session.selected_accounts) if session.selected_accounts else 0,
            'mfa_required': session.mfa_required,
            'verification_required': session.verification_required,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'expires_at': session.expires_at.isoformat()
        }
    
    def cancel_linking(self, session_id: str) -> Dict[str, Any]:
        """
        Cancel the linking process
        
        Args:
            session_id: Linking session ID
            
        Returns:
            Dictionary containing cancellation result
        """
        session = self._get_linking_session(session_id)
        if not session:
            return {'success': False, 'error': 'invalid_session'}
        
        session.status = LinkingStatus.CANCELLED
        session.updated_at = datetime.utcnow()
        
        # Audit log
        self.audit_service.log_event(
            user_id=session.user_id,
            event_type='account_linking_cancelled',
            details={'session_id': session_id}
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'status': session.status.value,
            'message': 'Account linking process cancelled'
        }
    
    # Helper methods
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return secrets.token_urlsafe(32)
    
    def _get_linking_session(self, session_id: str) -> Optional[LinkingSession]:
        """Get linking session by ID"""
        session = self.linking_sessions.get(session_id)
        if session and session.expires_at > datetime.utcnow():
            return session
        return None
    
    def _get_mfa_session(self, session_id: str) -> Optional[MFASession]:
        """Get MFA session by ID"""
        session = self.mfa_sessions.get(session_id)
        if session and session.expires_at > datetime.utcnow():
            return session
        return None
    
    def _get_verification_session(self, session_id: str) -> Optional[VerificationSession]:
        """Get verification session by ID"""
        session = self.verification_sessions.get(session_id)
        if session and session.expires_at > datetime.utcnow():
            return session
        return None
    
    def _get_institution_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get institution information for item"""
        try:
            # This would typically call Plaid's /item/get endpoint
            # For now, return mock data
            return {
                'institution_id': 'ins_123',
                'name': 'Sample Bank'
            }
        except Exception as e:
            logger.error(f"Error getting institution info for item {item_id}: {str(e)}")
            return None
    
    def _check_mfa_requirement(self, access_token: str) -> bool:
        """Check if MFA is required for the connection"""
        try:
            # This would typically check with Plaid API
            # For now, return False (no MFA required)
            return False
        except Exception as e:
            logger.error(f"Error checking MFA requirement: {str(e)}")
            return False
    
    def _create_mfa_session(self, linking_session_id: str, access_token: str) -> MFASession:
        """Create MFA session"""
        session_id = self._generate_session_id()
        mfa_session = MFASession(
            session_id=session_id,
            linking_session_id=linking_session_id,
            mfa_type=MFAType.SECURITY_QUESTIONS,
            questions=[
                {'question': 'What was your first pet\'s name?', 'field': 'pet_name'},
                {'question': 'In what city were you born?', 'field': 'birth_city'}
            ],
            attempts_remaining=self.max_mfa_attempts,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.mfa_timeout
        )
        
        self.mfa_sessions[session_id] = mfa_session
        return mfa_session
    
    def _check_verification_requirement(self, access_token: str) -> bool:
        """Check if account ownership verification is required"""
        try:
            # This would typically check with Plaid API or business rules
            # For now, return False (no verification required)
            return False
        except Exception as e:
            logger.error(f"Error checking verification requirement: {str(e)}")
            return False
    
    def _determine_verification_method(self, access_token: str) -> VerificationMethod:
        """Determine the appropriate verification method"""
        # This would typically be based on institution requirements
        # For now, return micro-deposits
        return VerificationMethod.MICRO_DEPOSITS
    
    def _create_verification_session(self, linking_session_id: str, 
                                   verification_method: VerificationMethod,
                                   access_token: str) -> VerificationSession:
        """Create verification session"""
        session_id = self._generate_session_id()
        
        if verification_method == VerificationMethod.MICRO_DEPOSITS:
            # Generate micro-deposits
            micro_deposits = [
                {'amount': 0.32, 'currency': 'USD'},
                {'amount': 0.45, 'currency': 'USD'}
            ]
        else:
            micro_deposits = None
        
        verification_session = VerificationSession(
            session_id=session_id,
            linking_session_id=linking_session_id,
            verification_method=verification_method,
            micro_deposits=micro_deposits,
            attempts_remaining=self.max_verification_attempts,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.verification_timeout
        )
        
        self.verification_sessions[session_id] = verification_session
        return verification_session
    
    def _verify_ownership(self, verification_method: VerificationMethod,
                         access_token: str, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify account ownership based on method"""
        try:
            if verification_method == VerificationMethod.MICRO_DEPOSITS:
                # Verify micro-deposit amounts
                expected_amounts = [0.32, 0.45]
                provided_amounts = verification_data.get('amounts', [])
                
                if len(provided_amounts) != len(expected_amounts):
                    return {'success': False, 'error': 'incorrect_number_of_amounts'}
                
                for expected, provided in zip(expected_amounts, provided_amounts):
                    if abs(expected - provided) > 0.01:  # Allow small rounding differences
                        return {'success': False, 'error': 'incorrect_amounts'}
                
                return {'success': True}
            
            elif verification_method == VerificationMethod.PHONE_VERIFICATION:
                # Verify phone verification code
                expected_code = verification_data.get('expected_code')
                provided_code = verification_data.get('provided_code')
                
                if expected_code != provided_code:
                    return {'success': False, 'error': 'incorrect_code'}
                
                return {'success': True}
            
            else:
                return {'success': False, 'error': 'unsupported_verification_method'}
                
        except Exception as e:
            logger.error(f"Error verifying ownership: {str(e)}")
            return {'success': False, 'error': 'verification_error'}
    
    def _classify_account_type(self, plaid_type: str, plaid_subtype: str) -> str:
        """Classify account type based on Plaid type and subtype"""
        if plaid_type == 'depository':
            if plaid_subtype == 'checking':
                return 'checking'
            elif plaid_subtype == 'savings':
                return 'savings'
            else:
                return 'savings'
        elif plaid_type == 'credit':
            return 'credit'
        elif plaid_type == 'loan':
            return 'loan'
        elif plaid_type == 'investment':
            return 'investment'
        else:
            return 'other'
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        
        # Clean up linking sessions
        expired_linking = [
            session_id for session_id, session in self.linking_sessions.items()
            if session.expires_at <= current_time
        ]
        for session_id in expired_linking:
            del self.linking_sessions[session_id]
        
        # Clean up MFA sessions
        expired_mfa = [
            session_id for session_id, session in self.mfa_sessions.items()
            if session.expires_at <= current_time
        ]
        for session_id in expired_mfa:
            del self.mfa_sessions[session_id]
        
        # Clean up verification sessions
        expired_verification = [
            session_id for session_id, session in self.verification_sessions.items()
            if session.expires_at <= current_time
        ]
        for session_id in expired_verification:
            del self.verification_sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_linking)} linking, {len(expired_mfa)} MFA, and {len(expired_verification)} verification sessions") 