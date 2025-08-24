"""
Bank Connection Flow Service for MINGUS

This module provides a comprehensive and secure bank connection user experience that:
- Drives subscription upgrades through strategic upgrade prompts
- Provides excellent onboarding for Plaid integration
- Handles tier-based access control
- Manages connection flow states and user experience
- Integrates with existing subscription and tier systems
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import SQLAlchemyError

from backend.integrations.plaid_integration import PlaidIntegrationService, PlaidProduct
from backend.services.plaid_subscription_service import PlaidSubscriptionService
from backend.services.tier_access_control_service import TierAccessControlService
from backend.services.enhanced_feature_access_service import EnhancedFeatureAccessService
from backend.models.plaid_models import PlaidConnection, PlaidAccount, PlaidInstitution
from backend.models.subscription import Subscription, PricingTier
from backend.services.analytics_service import AnalyticsService
from backend.services.notification_service import NotificationService
from backend.utils.validation import validate_user_tier
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

class ConnectionFlowState(Enum):
    """Bank connection flow states"""
    INITIALIZED = "initialized"
    TIER_CHECK = "tier_check"
    UPGRADE_PROMPT = "upgrade_prompt"
    LINK_TOKEN_CREATED = "link_token_created"
    ACCOUNT_SELECTED = "account_selected"
    MFA_REQUIRED = "mfa_required"
    VERIFICATION_REQUIRED = "verification_required"
    CONNECTION_ESTABLISHED = "connection_established"
    ERROR = "error"
    COMPLETED = "completed"

class ConnectionFlowStep(Enum):
    """Connection flow steps"""
    WELCOME = "welcome"
    TIER_UPGRADE = "tier_upgrade"
    SECURITY_INFO = "security_info"
    BANK_SELECTION = "bank_selection"
    ACCOUNT_LINKING = "account_linking"
    MFA_PROCESSING = "mfa_processing"
    VERIFICATION = "verification"
    SUCCESS = "success"

@dataclass
class ConnectionFlowSession:
    """Bank connection flow session"""
    session_id: str
    user_id: str
    current_step: ConnectionFlowStep
    current_state: ConnectionFlowState
    link_token: Optional[str] = None
    public_token: Optional[str] = None
    access_token: Optional[str] = None
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    selected_accounts: List[str] = None
    mfa_questions: List[Dict[str, Any]] = None
    verification_data: Dict[str, Any] = None
    upgrade_prompt: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    expires_at: datetime = None
    
    def __post_init__(self):
        if self.selected_accounts is None:
            self.selected_accounts = []
        if self.mfa_questions is None:
            self.mfa_questions = []
        if self.verification_data is None:
            self.verification_data = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=2)

@dataclass
class ConnectionFlowResult:
    """Result of connection flow operation"""
    success: bool
    session_id: Optional[str] = None
    next_step: Optional[ConnectionFlowStep] = None
    current_state: Optional[ConnectionFlowState] = None
    data: Optional[Dict[str, Any]] = None
    upgrade_prompt: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None

@dataclass
class UpgradePrompt:
    """Upgrade prompt configuration"""
    title: str
    message: str
    benefits: List[str]
    current_tier: str
    recommended_tier: str
    upgrade_price: float
    trial_available: bool
    trial_days: int
    features_preview: List[str]
    upgrade_url: str
    skip_url: str

class BankConnectionFlowService:
    """Comprehensive bank connection flow service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.sessions: Dict[str, ConnectionFlowSession] = {}
        self.plaid_service = None
        self.subscription_service = None
        self.tier_service = None
        self.feature_service = None
        self.analytics_service = None
        self.notification_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            from backend.integrations.plaid_integration import create_plaid_config_from_env
            from backend.services.plaid_subscription_service import PlaidSubscriptionService
            from backend.services.tier_access_control_service import TierAccessControlService
            from backend.services.enhanced_feature_access_service import EnhancedFeatureAccessService
            from backend.services.analytics_service import AnalyticsService
            from backend.services.notification_service import NotificationService
            
            # Initialize Plaid service
            plaid_config = create_plaid_config_from_env()
            self.plaid_service = PlaidIntegrationService(self.db, plaid_config)
            
            # Initialize other services
            self.feature_service = EnhancedFeatureAccessService()
            self.subscription_service = PlaidSubscriptionService(self.db, self.feature_service)
            self.tier_service = TierAccessControlService(self.db)
            self.analytics_service = AnalyticsService(self.db)
            self.notification_service = NotificationService(self.db)
            
            logger.info("Bank connection flow services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing bank connection flow services: {e}")
            raise
    
    def start_connection_flow(self, user_id: str) -> ConnectionFlowResult:
        """Start a new bank connection flow"""
        try:
            # Create session
            session_id = str(uuid.uuid4())
            session = ConnectionFlowSession(
                session_id=session_id,
                user_id=user_id,
                current_step=ConnectionFlowStep.WELCOME,
                current_state=ConnectionFlowState.INITIALIZED
            )
            
            self.sessions[session_id] = session
            
            # Track flow start
            self.analytics_service.track_event(
                user_id=user_id,
                event_type="bank_connection_flow_started",
                properties={
                    "session_id": session_id,
                    "step": session.current_step.value,
                    "state": session.current_state.value
                }
            )
            
            return ConnectionFlowResult(
                success=True,
                session_id=session_id,
                next_step=ConnectionFlowStep.WELCOME,
                current_state=ConnectionFlowState.INITIALIZED,
                data={
                    "session_id": session_id,
                    "welcome_message": self._get_welcome_message(user_id),
                    "security_info": self._get_security_info(),
                    "estimated_time": "2-3 minutes"
                }
            )
            
        except Exception as e:
            logger.error(f"Error starting connection flow for user {user_id}: {e}")
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to start connection flow"
            )
    
    def proceed_to_next_step(self, session_id: str, step_data: Dict[str, Any] = None) -> ConnectionFlowResult:
        """Proceed to the next step in the connection flow"""
        try:
            session = self._get_session(session_id)
            if not session:
                return ConnectionFlowResult(
                    success=False,
                    error_message="Invalid session"
                )
            
            # Update session data
            if step_data:
                session.verification_data.update(step_data)
            
            session.updated_at = datetime.utcnow()
            
            # Determine next step based on current step
            next_step = self._get_next_step(session)
            
            if next_step == ConnectionFlowStep.TIER_UPGRADE:
                return self._handle_tier_upgrade(session)
            elif next_step == ConnectionFlowStep.SECURITY_INFO:
                return self._handle_security_info(session)
            elif next_step == ConnectionFlowStep.BANK_SELECTION:
                return self._handle_bank_selection(session)
            elif next_step == ConnectionFlowStep.ACCOUNT_LINKING:
                return self._handle_account_linking(session)
            elif next_step == ConnectionFlowStep.MFA_PROCESSING:
                return self._handle_mfa_processing(session)
            elif next_step == ConnectionFlowStep.VERIFICATION:
                return self._handle_verification(session)
            elif next_step == ConnectionFlowStep.SUCCESS:
                return self._handle_success(session)
            else:
                return ConnectionFlowResult(
                    success=False,
                    error_message="Invalid flow step"
                )
                
        except Exception as e:
            logger.error(f"Error proceeding to next step for session {session_id}: {e}")
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to proceed to next step"
            )
    
    def handle_plaid_success(self, session_id: str, public_token: str, metadata: Dict[str, Any]) -> ConnectionFlowResult:
        """Handle Plaid Link success"""
        try:
            session = self._get_session(session_id)
            if not session:
                return ConnectionFlowResult(
                    success=False,
                    error_message="Invalid session"
                )
            
            session.public_token = public_token
            session.institution_id = metadata.get('institution', {}).get('institution_id')
            session.institution_name = metadata.get('institution', {}).get('name')
            session.selected_accounts = metadata.get('accounts', [])
            session.current_state = ConnectionFlowState.ACCOUNT_SELECTED
            session.updated_at = datetime.utcnow()
            
            # Track account selection
            self.analytics_service.track_event(
                user_id=session.user_id,
                event_type="plaid_accounts_selected",
                properties={
                    "session_id": session_id,
                    "institution_name": session.institution_name,
                    "accounts_count": len(session.selected_accounts),
                    "accounts": session.selected_accounts
                }
            )
            
            # Check if MFA is required
            if metadata.get('requires_mfa', False):
                return self._handle_mfa_required(session)
            else:
                return self._establish_connection(session)
                
        except Exception as e:
            logger.error(f"Error handling Plaid success for session {session_id}: {e}")
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to process bank connection"
            )
    
    def handle_mfa_response(self, session_id: str, mfa_answers: List[Dict[str, Any]]) -> ConnectionFlowResult:
        """Handle MFA response"""
        try:
            session = self._get_session(session_id)
            if not session:
                return ConnectionFlowResult(
                    success=False,
                    error_message="Invalid session"
                )
            
            # Process MFA answers
            session.verification_data['mfa_answers'] = mfa_answers
            session.current_state = ConnectionFlowState.MFA_REQUIRED
            session.updated_at = datetime.utcnow()
            
            # Track MFA completion
            self.analytics_service.track_event(
                user_id=session.user_id,
                event_type="mfa_completed",
                properties={
                    "session_id": session_id,
                    "questions_count": len(session.mfa_questions)
                }
            )
            
            return self._establish_connection(session)
            
        except Exception as e:
            logger.error(f"Error handling MFA response for session {session_id}: {e}")
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to process MFA response"
            )
    
    def handle_verification_response(self, session_id: str, verification_data: Dict[str, Any]) -> ConnectionFlowResult:
        """Handle verification response"""
        try:
            session = self._get_session(session_id)
            if not session:
                return ConnectionFlowResult(
                    success=False,
                    error_message="Invalid session"
                )
            
            session.verification_data.update(verification_data)
            session.current_state = ConnectionFlowState.VERIFICATION_REQUIRED
            session.updated_at = datetime.utcnow()
            
            # Track verification completion
            self.analytics_service.track_event(
                user_id=session.user_id,
                event_type="verification_completed",
                properties={
                    "session_id": session_id,
                    "verification_type": verification_data.get('type')
                }
            )
            
            return self._establish_connection(session)
            
        except Exception as e:
            logger.error(f"Error handling verification response for session {session_id}: {e}")
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to process verification"
            )
    
    def _get_session(self, session_id: str) -> Optional[ConnectionFlowSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check if session expired
        if datetime.utcnow() > session.expires_at:
            del self.sessions[session_id]
            return None
        
        return session
    
    def _get_next_step(self, session: ConnectionFlowSession) -> ConnectionFlowStep:
        """Determine the next step in the flow"""
        if session.current_step == ConnectionFlowStep.WELCOME:
            # Check tier access
            can_connect, message, upgrade_prompt = self.subscription_service.can_add_connection(session.user_id)
            if not can_connect:
                session.upgrade_prompt = upgrade_prompt._asdict() if upgrade_prompt else None
                return ConnectionFlowStep.TIER_UPGRADE
            return ConnectionFlowStep.SECURITY_INFO
        
        elif session.current_step == ConnectionFlowStep.TIER_UPGRADE:
            return ConnectionFlowStep.SECURITY_INFO
        
        elif session.current_step == ConnectionFlowStep.SECURITY_INFO:
            return ConnectionFlowStep.BANK_SELECTION
        
        elif session.current_step == ConnectionFlowStep.BANK_SELECTION:
            return ConnectionFlowStep.ACCOUNT_LINKING
        
        elif session.current_step == ConnectionFlowStep.ACCOUNT_LINKING:
            if session.current_state == ConnectionFlowState.MFA_REQUIRED:
                return ConnectionFlowStep.MFA_PROCESSING
            elif session.current_state == ConnectionFlowState.VERIFICATION_REQUIRED:
                return ConnectionFlowStep.VERIFICATION
            else:
                return ConnectionFlowStep.SUCCESS
        
        elif session.current_step == ConnectionFlowStep.MFA_PROCESSING:
            return ConnectionFlowStep.SUCCESS
        
        elif session.current_step == ConnectionFlowStep.VERIFICATION:
            return ConnectionFlowStep.SUCCESS
        
        else:
            return ConnectionFlowStep.SUCCESS
    
    def _handle_tier_upgrade(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle tier upgrade step"""
        session.current_step = ConnectionFlowStep.TIER_UPGRADE
        session.current_state = ConnectionFlowState.UPGRADE_PROMPT
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.TIER_UPGRADE,
            current_state=ConnectionFlowState.UPGRADE_PROMPT,
            upgrade_prompt=session.upgrade_prompt,
            data={
                "upgrade_benefits": self._get_upgrade_benefits(),
                "trial_info": self._get_trial_info(),
                "security_guarantee": self._get_security_guarantee()
            }
        )
    
    def _handle_security_info(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle security information step"""
        session.current_step = ConnectionFlowStep.SECURITY_INFO
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.SECURITY_INFO,
            current_state=ConnectionFlowState.TIER_CHECK,
            data={
                "security_info": self._get_security_info(),
                "privacy_policy": self._get_privacy_policy(),
                "data_usage": self._get_data_usage_info()
            }
        )
    
    def _handle_bank_selection(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle bank selection step"""
        session.current_step = ConnectionFlowStep.BANK_SELECTION
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.BANK_SELECTION,
            current_state=ConnectionFlowState.TIER_CHECK,
            data={
                "supported_banks": self._get_supported_banks(),
                "search_tips": self._get_search_tips(),
                "connection_benefits": self._get_connection_benefits()
            }
        )
    
    def _handle_account_linking(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle account linking step"""
        try:
            session.current_step = ConnectionFlowStep.ACCOUNT_LINKING
            
            # Create Plaid Link token
            link_token = self.plaid_service.create_link_token(
                session.user_id,
                [PlaidProduct.AUTH, PlaidProduct.TRANSACTIONS, PlaidProduct.IDENTITY]
            )
            
            session.link_token = link_token.link_token
            session.current_state = ConnectionFlowState.LINK_TOKEN_CREATED
            
            return ConnectionFlowResult(
                success=True,
                session_id=session.session_id,
                next_step=ConnectionFlowStep.ACCOUNT_LINKING,
                current_state=ConnectionFlowState.LINK_TOKEN_CREATED,
                data={
                    "link_token": link_token.link_token,
                    "expiration": link_token.expiration.isoformat(),
                    "plaid_config": self._get_plaid_config()
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating Link token for session {session.session_id}: {e}")
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to create bank connection"
            )
    
    def _handle_mfa_required(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle MFA required state"""
        session.current_state = ConnectionFlowState.MFA_REQUIRED
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.MFA_PROCESSING,
            current_state=ConnectionFlowState.MFA_REQUIRED,
            data={
                "mfa_required": True,
                "mfa_questions": session.mfa_questions,
                "mfa_instructions": self._get_mfa_instructions()
            }
        )
    
    def _handle_mfa_processing(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle MFA processing step"""
        session.current_step = ConnectionFlowStep.MFA_PROCESSING
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.MFA_PROCESSING,
            current_state=ConnectionFlowState.MFA_REQUIRED,
            data={
                "mfa_questions": session.mfa_questions,
                "mfa_instructions": self._get_mfa_instructions()
            }
        )
    
    def _handle_verification(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle verification step"""
        session.current_step = ConnectionFlowStep.VERIFICATION
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.VERIFICATION,
            current_state=ConnectionFlowState.VERIFICATION_REQUIRED,
            data={
                "verification_required": True,
                "verification_type": session.verification_data.get('type'),
                "verification_instructions": self._get_verification_instructions()
            }
        )
    
    def _establish_connection(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Establish the bank connection"""
        try:
            # Exchange public token for access token
            connection = self.plaid_service.exchange_public_token(
                session.public_token,
                session.user_id
            )
            
            session.access_token = connection.access_token
            session.current_state = ConnectionFlowState.CONNECTION_ESTABLISHED
            
            # Track successful connection
            self.analytics_service.track_event(
                user_id=session.user_id,
                event_type="bank_connection_established",
                properties={
                    "session_id": session.session_id,
                    "institution_name": session.institution_name,
                    "accounts_count": len(session.selected_accounts)
                }
            )
            
            # Send welcome notification
            self.notification_service.send_bank_connection_welcome(
                user_id=session.user_id,
                institution_name=session.institution_name,
                accounts_count=len(session.selected_accounts)
            )
            
            return ConnectionFlowResult(
                success=True,
                session_id=session.session_id,
                next_step=ConnectionFlowStep.SUCCESS,
                current_state=ConnectionFlowState.CONNECTION_ESTABLISHED,
                data={
                    "connection_id": str(connection.id),
                    "institution_name": session.institution_name,
                    "accounts_count": len(session.selected_accounts),
                    "success_message": self._get_success_message(session.institution_name),
                    "next_steps": self._get_next_steps()
                }
            )
            
        except Exception as e:
            logger.error(f"Error establishing connection for session {session.session_id}: {e}")
            session.current_state = ConnectionFlowState.ERROR
            session.error_message = str(e)
            
            return ConnectionFlowResult(
                success=False,
                error_message="Failed to establish bank connection"
            )
    
    def _handle_success(self, session: ConnectionFlowSession) -> ConnectionFlowResult:
        """Handle success step"""
        session.current_step = ConnectionFlowStep.SUCCESS
        session.current_state = ConnectionFlowState.COMPLETED
        
        # Clean up session
        if session.session_id in self.sessions:
            del self.sessions[session.session_id]
        
        return ConnectionFlowResult(
            success=True,
            session_id=session.session_id,
            next_step=ConnectionFlowStep.SUCCESS,
            current_state=ConnectionFlowState.COMPLETED,
            redirect_url="/dashboard/banking",
            data={
                "success": True,
                "completion_message": "Bank connection completed successfully!",
                "redirect_url": "/dashboard/banking"
            }
        )
    
    # Helper methods for content generation
    def _get_welcome_message(self, user_id: str) -> str:
        """Get personalized welcome message"""
        return "Welcome to secure bank account linking! Let's connect your accounts to unlock powerful financial insights."
    
    def _get_security_info(self) -> Dict[str, Any]:
        """Get security information"""
        return {
            "title": "Bank-Level Security",
            "description": "Your financial data is protected with bank-level encryption and security measures.",
            "features": [
                "256-bit SSL encryption",
                "Bank-level security protocols",
                "Read-only access to your accounts",
                "No access to your login credentials",
                "SOC 2 Type II certified"
            ]
        }
    
    def _get_upgrade_benefits(self) -> List[str]:
        """Get upgrade benefits"""
        return [
            "Connect unlimited bank accounts",
            "24 months of transaction history",
            "Advanced financial analytics",
            "Real-time balance updates",
            "Priority customer support",
            "Custom financial planning tools"
        ]
    
    def _get_trial_info(self) -> Dict[str, Any]:
        """Get trial information"""
        return {
            "duration": "7 days",
            "features": "All premium features included",
            "no_commitment": "Cancel anytime",
            "upgrade_anytime": "Upgrade during or after trial"
        }
    
    def _get_security_guarantee(self) -> str:
        """Get security guarantee"""
        return "Your data is protected with bank-level security. We never store your banking credentials."
    
    def _get_privacy_policy(self) -> str:
        """Get privacy policy summary"""
        return "We only access the data you authorize and never share your personal information with third parties."
    
    def _get_data_usage_info(self) -> str:
        """Get data usage information"""
        return "We use your financial data to provide personalized insights and recommendations to help you achieve your financial goals."
    
    def _get_supported_banks(self) -> List[str]:
        """Get list of supported banks"""
        return [
            "Chase", "Bank of America", "Wells Fargo", "Citibank", "US Bank",
            "Capital One", "American Express", "Discover", "Ally Bank", "Marcus by Goldman Sachs"
        ]
    
    def _get_search_tips(self) -> List[str]:
        """Get search tips"""
        return [
            "Search by bank name (e.g., 'Chase' or 'Bank of America')",
            "Try common abbreviations (e.g., 'BofA' for Bank of America)",
            "Search by your bank's website domain",
            "If you can't find your bank, contact support"
        ]
    
    def _get_connection_benefits(self) -> List[str]:
        """Get connection benefits"""
        return [
            "Automatic transaction categorization",
            "Real-time balance monitoring",
            "Spending pattern analysis",
            "Budget tracking and alerts",
            "Financial goal progress tracking"
        ]
    
    def _get_plaid_config(self) -> Dict[str, Any]:
        """Get Plaid configuration"""
        return {
            "clientName": "MINGUS",
            "products": ["auth", "transactions", "identity"],
            "countryCodes": ["US"],
            "language": "en"
        }
    
    def _get_mfa_instructions(self) -> str:
        """Get MFA instructions"""
        return "Your bank requires additional verification. Please answer the security questions below."
    
    def _get_verification_instructions(self) -> str:
        """Get verification instructions"""
        return "Please complete the verification process to secure your connection."
    
    def _get_success_message(self, institution_name: str) -> str:
        """Get success message"""
        return f"Successfully connected to {institution_name}! Your accounts are now linked and ready for analysis."
    
    def _get_next_steps(self) -> List[str]:
        """Get next steps"""
        return [
            "View your account balances",
            "Explore transaction insights",
            "Set up spending alerts",
            "Create financial goals",
            "Schedule your first financial review"
        ]
    
    def get_flow_progress(self, session_id: str) -> Dict[str, Any]:
        """Get flow progress information"""
        session = self._get_session(session_id)
        if not session:
            return {"error": "Invalid session"}
        
        steps = list(ConnectionFlowStep)
        current_index = steps.index(session.current_step)
        progress_percentage = ((current_index + 1) / len(steps)) * 100
        
        return {
            "current_step": session.current_step.value,
            "current_state": session.current_state.value,
            "progress_percentage": progress_percentage,
            "steps_completed": current_index + 1,
            "total_steps": len(steps),
            "estimated_time_remaining": "1-2 minutes"
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time > session.expires_at
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions") 