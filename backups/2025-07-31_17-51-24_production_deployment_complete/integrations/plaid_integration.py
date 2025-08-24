"""
Plaid Integration Service for MINGUS

This module provides comprehensive Plaid integration including:
- Bank account linking via Plaid Link
- Account balance retrieval
- Transaction history access (up to 24 months)
- Account identity verification
- Real-time balance updates via webhooks
"""

import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import plaid
from plaid.api import plaid_api
from plaid.model import (
    LinkTokenCreateRequest,
    LinkTokenCreateResponse,
    ItemPublicTokenExchangeRequest,
    ItemPublicTokenExchangeResponse,
    AccountsGetRequest,
    AccountsGetResponse,
    TransactionsGetRequest,
    TransactionsGetResponse,
    IdentityGetRequest,
    IdentityGetResponse,
    InstitutionsGetByIdRequest,
    InstitutionsGetByIdResponse,
    ItemGetRequest,
    ItemGetResponse,
    ItemRemoveRequest,
    ItemRemoveResponse,
    SandboxPublicTokenCreateRequest,
    SandboxPublicTokenCreateResponse
)
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from backend.models.plaid_models import (
    PlaidConnection, 
    PlaidAccount, 
    PlaidTransaction, 
    PlaidInstitution, 
    PlaidSyncLog,
    PlaidIdentity
)
from config.plaid_config import get_plaid_config, PlaidEnvironment

logger = logging.getLogger(__name__)

class PlaidProduct(Enum):
    """Plaid products"""
    AUTH = "auth"
    TRANSACTIONS = "transactions"
    IDENTITY = "identity"
    BALANCE = "balance"
    INVESTMENTS = "investments"
    LIABILITIES = "liabilities"
    ASSETS = "assets"
    PAYMENT_INITIATION = "payment_initiation"
    TRANSFER = "transfer"

@dataclass
class LinkTokenResult:
    """Result of Link token creation"""
    link_token: str
    expiration: datetime
    request_id: str

@dataclass
class AccountBalance:
    """Account balance information"""
    account_id: str
    current_balance: float
    available_balance: float
    iso_currency_code: str
    unofficial_currency_code: Optional[str] = None
    limit: Optional[float] = None
    last_updated_datetime: Optional[datetime] = None

@dataclass
class TransactionData:
    """Transaction data structure"""
    transaction_id: str
    pending_transaction_id: Optional[str]
    name: str
    amount: float
    date: str
    datetime: Optional[str]
    authorized_date: Optional[str]
    authorized_datetime: Optional[str]
    merchant_name: Optional[str]
    logo_url: Optional[str]
    website: Optional[str]
    category: List[str]
    category_id: str
    personal_finance_category: Optional[Dict[str, Any]]
    pending: bool
    payment_channel: str
    transaction_type: str
    transaction_code: Optional[str]
    location: Optional[Dict[str, Any]]
    payment_meta: Optional[Dict[str, Any]]
    iso_currency_code: str
    unofficial_currency_code: Optional[str]
    account_owner: Optional[str]
    check_number: Optional[str]

@dataclass
class IdentityData:
    """Identity data structure"""
    names: List[str]
    phone_numbers: List[Dict[str, Any]]
    emails: List[Dict[str, Any]]
    addresses: List[Dict[str, Any]]
    account_ids: List[str]

class PlaidIntegrationService:
    """Comprehensive Plaid integration service"""
    
    def __init__(self, db_session: Session, config=None):
        self.db = db_session
        self.config = config or get_plaid_config()
        self._setup_plaid_client()
        
    def _setup_plaid_client(self):
        """Set up Plaid API client"""
        try:
            # Configure Plaid client
            plaid_config = plaid.Configuration(
                host=self._get_plaid_host(),
                api_key={
                    'clientId': self.config.client_id,
                    'secret': self.config.secret,
                }
            )
            
            self.api_client = plaid.ApiClient(plaid_config)
            self.link_token_api = plaid_api.PlaidApi(self.api_client)
            self.accounts_api = plaid_api.PlaidApi(self.api_client)
            self.transactions_api = plaid_api.PlaidApi(self.api_client)
            self.identity_api = plaid_api.PlaidApi(self.api_client)
            self.institutions_api = plaid_api.PlaidApi(self.api_client)
            self.item_api = plaid_api.PlaidApi(self.api_client)
            
            logger.info(f"Plaid client initialized for environment: {self.config.environment.value}")
            
        except Exception as e:
            logger.error(f"Error setting up Plaid client: {e}")
            raise
    
    def _get_plaid_host(self):
        """Get Plaid host based on environment"""
        if self.config.environment == PlaidEnvironment.SANDBOX:
            return plaid.Environment.Sandbox
        elif self.config.environment == PlaidEnvironment.PRODUCTION:
            return plaid.Environment.Production
        else:
            return plaid.Environment.Development
    
    # ============================================================================
    # BANK ACCOUNT LINKING VIA PLAID LINK
    # ============================================================================
    
    def create_link_token(self, user_id: str, products: List[PlaidProduct] = None) -> LinkTokenResult:
        """Create a Plaid Link token for bank account linking"""
        try:
            if products is None:
                products = [PlaidProduct.AUTH, PlaidProduct.TRANSACTIONS, PlaidProduct.IDENTITY]
            
            # Convert products to strings
            product_strings = [product.value for product in products]
            
            # Create Link token request
            request = LinkTokenCreateRequest(
                user=plaid.model.LinkTokenCreateRequestUser(
                    client_user_id=user_id
                ),
                client_name="MINGUS",
                products=product_strings,
                country_codes=self.config.country_codes,
                language=self.config.language,
                redirect_uri=self.config.redirect_uri,
                update_mode=self.config.update_mode,
                webhook=self.config.webhook.webhook_url
            )
            
            # Create Link token
            response: LinkTokenCreateResponse = self.link_token_api.link_token_create(request)
            
            logger.info(f"Link token created for user {user_id}")
            
            return LinkTokenResult(
                link_token=response.link_token,
                expiration=response.expiration,
                request_id=response.request_id
            )
            
        except Exception as e:
            logger.error(f"Error creating Link token: {e}")
            raise
    
    def exchange_public_token(self, public_token: str, user_id: str) -> PlaidConnection:
        """Exchange public token for access token and create connection"""
        try:
            # Exchange public token for access token
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response: ItemPublicTokenExchangeResponse = self.item_api.item_public_token_exchange(request)
            
            access_token = response.access_token
            item_id = response.item_id
            
            # Get item information
            item_request = ItemGetRequest(access_token=access_token)
            item_response: ItemGetResponse = self.item_api.item_get(item_request)
            
            # Get institution information
            institution_request = InstitutionsGetByIdRequest(
                institution_id=item_response.item.institution_id,
                country_codes=self.config.country_codes
            )
            institution_response: InstitutionsGetByIdResponse = self.institutions_api.institutions_get_by_id(institution_request)
            
            # Create or update connection
            connection = self.db.query(PlaidConnection).filter(
                PlaidConnection.item_id == item_id
            ).first()
            
            if connection:
                # Update existing connection
                connection.access_token = self._encrypt_access_token(access_token)
                connection.institution_name = institution_response.institution.name
                connection.is_active = True
                connection.error_code = None
                connection.error_message = None
                connection.updated_at = datetime.utcnow()
            else:
                # Create new connection
                connection = PlaidConnection(
                    user_id=user_id,
                    item_id=item_id,
                    access_token=self._encrypt_access_token(access_token),
                    institution_id=item_response.item.institution_id,
                    institution_name=institution_response.institution.name,
                    products=item_response.item.available_products,
                    webhook_url=self.config.webhook.webhook_url,
                    is_active=True
                )
                self.db.add(connection)
            
            self.db.commit()
            
            # Sync accounts and initial data
            self._sync_accounts(connection)
            self._sync_identity(connection)
            
            logger.info(f"Public token exchanged successfully for user {user_id}")
            return connection
            
        except Exception as e:
            logger.error(f"Error exchanging public token: {e}")
            self.db.rollback()
            raise
    
    def _encrypt_access_token(self, access_token: str) -> str:
        """Encrypt access token for storage"""
        # In production, use proper encryption
        if self.config.access_token_encryption_key:
            # Implement encryption here
            return access_token  # Placeholder
        return access_token
    
    def _decrypt_access_token(self, encrypted_token: str) -> str:
        """Decrypt access token for API calls"""
        # In production, use proper decryption
        if self.config.access_token_encryption_key:
            # Implement decryption here
            return encrypted_token  # Placeholder
        return encrypted_token
    
    # ============================================================================
    # ACCOUNT BALANCE RETRIEVAL
    # ============================================================================
    
    def get_account_balances(self, connection: PlaidConnection) -> List[AccountBalance]:
        """Get account balances for a connection"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Get accounts with balances
            request = AccountsGetRequest(access_token=access_token)
            response: AccountsGetResponse = self.accounts_api.accounts_get(request)
            
            balances = []
            for account in response.accounts:
                balance = AccountBalance(
                    account_id=account.account_id,
                    current_balance=account.balances.current,
                    available_balance=account.balances.available,
                    iso_currency_code=account.balances.iso_currency_code,
                    unofficial_currency_code=account.balances.unofficial_currency_code,
                    limit=account.balances.limit,
                    last_updated_datetime=account.balances.last_updated_datetime
                )
                balances.append(balance)
                
                # Update database
                self._update_account_balance(connection, account)
            
            logger.info(f"Retrieved balances for {len(balances)} accounts")
            return balances
            
        except Exception as e:
            logger.error(f"Error getting account balances: {e}")
            raise
    
    def _update_account_balance(self, connection: PlaidConnection, account_data):
        """Update account balance in database"""
        try:
            account = self.db.query(PlaidAccount).filter(
                PlaidAccount.plaid_account_id == account_data.account_id,
                PlaidAccount.connection_id == connection.id
            ).first()
            
            if account:
                account.current_balance = account_data.balances.current
                account.available_balance = account_data.balances.available
                account.iso_currency_code = account_data.balances.iso_currency_code
                account.unofficial_currency_code = account_data.balances.unofficial_currency_code
                account.limit = account_data.balances.limit
                account.last_balance_update = datetime.utcnow()
                account.updated_at = datetime.utcnow()
            else:
                # Create new account record
                account = PlaidAccount(
                    connection_id=connection.id,
                    user_id=connection.user_id,
                    plaid_account_id=account_data.account_id,
                    name=account_data.name,
                    mask=account_data.mask,
                    official_name=account_data.official_name,
                    type=account_data.type,
                    subtype=account_data.subtype,
                    current_balance=account_data.balances.current,
                    available_balance=account_data.balances.available,
                    iso_currency_code=account_data.balances.iso_currency_code,
                    unofficial_currency_code=account_data.balances.unofficial_currency_code,
                    limit=account_data.balances.limit,
                    is_active=True
                )
                self.db.add(account)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
            self.db.rollback()
    
    # ============================================================================
    # TRANSACTION HISTORY ACCESS (UP TO 24 MONTHS)
    # ============================================================================
    
    def get_transaction_history(self, connection: PlaidConnection, 
                               start_date: str = None, 
                               end_date: str = None,
                               account_ids: List[str] = None) -> List[TransactionData]:
        """Get transaction history (up to 24 months)"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Set default date range (24 months)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get transactions
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=plaid.model.TransactionsGetRequestOptions(
                    account_ids=account_ids,
                    include_personal_finance_category=True
                )
            )
            
            response: TransactionsGetResponse = self.transactions_api.transactions_get(request)
            
            transactions = []
            for transaction in response.transactions:
                transaction_data = TransactionData(
                    transaction_id=transaction.transaction_id,
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
                    check_number=transaction.check_number
                )
                transactions.append(transaction_data)
                
                # Store transaction in database
                self._store_transaction(connection, transaction_data)
            
            logger.info(f"Retrieved {len(transactions)} transactions for date range {start_date} to {end_date}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            raise
    
    def sync_transactions(self, connection: PlaidConnection, cursor: str = None) -> Tuple[List[TransactionData], str, bool]:
        """Sync transactions using cursor-based pagination"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Get transactions with cursor
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                options=plaid.model.TransactionsGetRequestOptions(
                    include_personal_finance_category=True
                )
            )
            
            if cursor:
                request.options.cursor = cursor
            
            response: TransactionsGetResponse = self.transactions_api.transactions_get(request)
            
            transactions = []
            for transaction in response.transactions:
                transaction_data = TransactionData(
                    transaction_id=transaction.transaction_id,
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
                    check_number=transaction.check_number
                )
                transactions.append(transaction_data)
                
                # Store transaction in database
                self._store_transaction(connection, transaction_data)
            
            return transactions, response.next_cursor, response.has_more
            
        except Exception as e:
            logger.error(f"Error syncing transactions: {e}")
            raise
    
    def _store_transaction(self, connection: PlaidConnection, transaction_data: TransactionData):
        """Store transaction in database"""
        try:
            # Check if transaction already exists
            existing = self.db.query(PlaidTransaction).filter(
                PlaidTransaction.plaid_transaction_id == transaction_data.transaction_id
            ).first()
            
            if existing:
                return  # Transaction already exists
            
            # Get account for this transaction
            account = self.db.query(PlaidAccount).filter(
                PlaidAccount.plaid_account_id == transaction_data.account_id
            ).first()
            
            if not account:
                logger.warning(f"Account not found for transaction {transaction_data.transaction_id}")
                return
            
            # Create transaction record
            transaction = PlaidTransaction(
                connection_id=connection.id,
                account_id=account.id,
                user_id=connection.user_id,
                plaid_transaction_id=transaction_data.transaction_id,
                pending_transaction_id=transaction_data.pending_transaction_id,
                name=transaction_data.name,
                amount=transaction_data.amount,
                date=transaction_data.date,
                datetime=transaction_data.datetime,
                authorized_date=transaction_data.authorized_date,
                authorized_datetime=transaction_data.authorized_datetime,
                merchant_name=transaction_data.merchant_name,
                logo_url=transaction_data.logo_url,
                website=transaction_data.website,
                category=transaction_data.category,
                category_id=transaction_data.category_id,
                personal_finance_category=transaction_data.personal_finance_category,
                pending=transaction_data.pending,
                payment_channel=transaction_data.payment_channel,
                transaction_type=transaction_data.transaction_type,
                transaction_code=transaction_data.transaction_code,
                location=transaction_data.location,
                payment_meta=transaction_data.payment_meta,
                iso_currency_code=transaction_data.iso_currency_code,
                unofficial_currency_code=transaction_data.unofficial_currency_code,
                account_owner=transaction_data.account_owner,
                check_number=transaction_data.check_number,
                is_active=True
            )
            
            self.db.add(transaction)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing transaction: {e}")
            self.db.rollback()
    
    # ============================================================================
    # ACCOUNT IDENTITY VERIFICATION
    # ============================================================================
    
    def get_account_identity(self, connection: PlaidConnection) -> IdentityData:
        """Get account identity information"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Get identity information
            request = IdentityGetRequest(access_token=access_token)
            response: IdentityGetResponse = self.identity_api.identity_get(request)
            
            identity_data = IdentityData(
                names=response.accounts[0].owners[0].names,
                phone_numbers=response.accounts[0].owners[0].phone_numbers,
                emails=response.accounts[0].owners[0].emails,
                addresses=response.accounts[0].owners[0].addresses,
                account_ids=[account.account_id for account in response.accounts]
            )
            
            # Store identity in database
            self._store_identity(connection, identity_data)
            
            logger.info(f"Retrieved identity for {len(identity_data.account_ids)} accounts")
            return identity_data
            
        except Exception as e:
            logger.error(f"Error getting account identity: {e}")
            raise
    
    def _store_identity(self, connection: PlaidConnection, identity_data: IdentityData):
        """Store identity information in database"""
        try:
            # Check if identity already exists
            existing = self.db.query(PlaidIdentity).filter(
                PlaidIdentity.connection_id == connection.id
            ).first()
            
            if existing:
                # Update existing identity
                existing.names = identity_data.names
                existing.phone_numbers = identity_data.phone_numbers
                existing.emails = identity_data.emails
                existing.addresses = identity_data.addresses
                existing.account_ids = identity_data.account_ids
                existing.updated_at = datetime.utcnow()
            else:
                # Create new identity record
                identity = PlaidIdentity(
                    connection_id=connection.id,
                    user_id=connection.user_id,
                    names=identity_data.names,
                    phone_numbers=identity_data.phone_numbers,
                    emails=identity_data.emails,
                    addresses=identity_data.addresses,
                    account_ids=identity_data.account_ids,
                    is_active=True
                )
                self.db.add(identity)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing identity: {e}")
            self.db.rollback()
    
    # ============================================================================
    # REAL-TIME BALANCE UPDATES VIA WEBHOOKS
    # ============================================================================
    
    def _sync_accounts(self, connection: PlaidConnection):
        """Sync accounts for a connection"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Get accounts
            request = AccountsGetRequest(access_token=access_token)
            response: AccountsGetResponse = self.accounts_api.accounts_get(request)
            
            for account_data in response.accounts:
                # Check if account already exists
                existing = self.db.query(PlaidAccount).filter(
                    PlaidAccount.plaid_account_id == account_data.account_id,
                    PlaidAccount.connection_id == connection.id
                ).first()
                
                if existing:
                    # Update existing account
                    existing.name = account_data.name
                    existing.mask = account_data.mask
                    existing.official_name = account_data.official_name
                    existing.type = account_data.type
                    existing.subtype = account_data.subtype
                    existing.current_balance = account_data.balances.current
                    existing.available_balance = account_data.balances.available
                    existing.iso_currency_code = account_data.balances.iso_currency_code
                    existing.unofficial_currency_code = account_data.balances.unofficial_currency_code
                    existing.limit = account_data.balances.limit
                    existing.is_active = True
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new account
                    account = PlaidAccount(
                        connection_id=connection.id,
                        user_id=connection.user_id,
                        plaid_account_id=account_data.account_id,
                        name=account_data.name,
                        mask=account_data.mask,
                        official_name=account_data.official_name,
                        type=account_data.type,
                        subtype=account_data.subtype,
                        current_balance=account_data.balances.current,
                        available_balance=account_data.balances.available,
                        iso_currency_code=account_data.balances.iso_currency_code,
                        unofficial_currency_code=account_data.balances.unofficial_currency_code,
                        limit=account_data.balances.limit,
                        is_active=True
                    )
                    self.db.add(account)
            
            self.db.commit()
            logger.info(f"Synced {len(response.accounts)} accounts for connection {connection.id}")
            
        except Exception as e:
            logger.error(f"Error syncing accounts: {e}")
            self.db.rollback()
    
    def _sync_identity(self, connection: PlaidConnection):
        """Sync identity for a connection"""
        try:
            identity_data = self.get_account_identity(connection)
            logger.info(f"Synced identity for connection {connection.id}")
        except Exception as e:
            logger.error(f"Error syncing identity: {e}")
    
    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================
    
    def remove_connection(self, connection: PlaidConnection) -> bool:
        """Remove a Plaid connection"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Remove item from Plaid
            request = ItemRemoveRequest(access_token=access_token)
            response: ItemRemoveResponse = self.item_api.item_remove(request)
            
            if response.removed:
                # Mark connection as inactive
                connection.is_active = False
                connection.updated_at = datetime.utcnow()
                
                # Mark accounts as inactive
                accounts = self.db.query(PlaidAccount).filter(
                    PlaidAccount.connection_id == connection.id
                ).all()
                
                for account in accounts:
                    account.is_active = False
                    account.updated_at = datetime.utcnow()
                
                self.db.commit()
                logger.info(f"Removed connection {connection.id}")
                return True
            else:
                logger.error(f"Failed to remove connection {connection.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing connection: {e}")
            self.db.rollback()
            return False
    
    def get_connection_status(self, connection: PlaidConnection) -> Dict[str, Any]:
        """Get connection status and health"""
        try:
            access_token = self._decrypt_access_token(connection.access_token)
            
            # Get item information
            request = ItemGetRequest(access_token=access_token)
            response: ItemGetResponse = self.item_api.item_get(request)
            
            # Get accounts
            accounts_request = AccountsGetRequest(access_token=access_token)
            accounts_response: AccountsGetResponse = self.accounts_api.accounts_get(accounts_request)
            
            status = {
                'connection_id': str(connection.id),
                'item_id': connection.item_id,
                'institution_name': connection.institution_name,
                'is_active': connection.is_active,
                'error_code': connection.error_code,
                'error_message': connection.error_message,
                'last_sync_at': connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                'accounts_count': len(accounts_response.accounts),
                'products': response.item.available_products,
                'webhook_url': connection.webhook_url,
                'created_at': connection.created_at.isoformat(),
                'updated_at': connection.updated_at.isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                'connection_id': str(connection.id),
                'error': str(e),
                'is_active': False
            }
    
    # ============================================================================
    # SANDBOX UTILITIES (FOR TESTING)
    # ============================================================================
    
    def create_sandbox_public_token(self, institution_id: str, 
                                   initial_products: List[str] = None) -> str:
        """Create a sandbox public token for testing"""
        try:
            if self.config.environment != PlaidEnvironment.SANDBOX:
                raise ValueError("Sandbox tokens can only be created in sandbox environment")
            
            if initial_products is None:
                initial_products = ["auth", "transactions", "identity"]
            
            request = SandboxPublicTokenCreateRequest(
                institution_id=institution_id,
                initial_products=initial_products
            )
            
            response: SandboxPublicTokenCreateResponse = self.item_api.sandbox_public_token_create(request)
            
            logger.info(f"Created sandbox public token for institution {institution_id}")
            return response.public_token
            
        except Exception as e:
            logger.error(f"Error creating sandbox public token: {e}")
            raise

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_plaid_config_from_env() -> Any:
    """Create Plaid configuration from environment variables"""
    return get_plaid_config()

def validate_plaid_config(config) -> bool:
    """Validate Plaid configuration"""
    try:
        if not config.client_id or not config.secret:
            return False
        if not config.webhook.webhook_url:
            return False
        return True
    except Exception:
        return False 