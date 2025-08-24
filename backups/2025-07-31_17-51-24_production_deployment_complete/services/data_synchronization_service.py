"""
Data Synchronization Service for MINGUS

This service provides comprehensive data synchronization features:
- Real-time balance updates
- Daily transaction synchronization
- Historical data backfill (24 months)
- Duplicate transaction detection
- Data consistency validation
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from backend.models.bank_account_models import BankAccount, PlaidConnection, TransactionSync, AccountBalance
from backend.models.plaid_models import PlaidTransaction, PlaidAccount
from backend.services.plaid_integration import PlaidIntegrationService
from backend.services.notification_service import NotificationService
from backend.services.audit_service import AuditService
from backend.utils.encryption import encrypt_data, decrypt_data
from backend.utils.validation import validate_transaction_data

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """Synchronization status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class SyncType(Enum):
    """Synchronization type enumeration"""
    BALANCE = "balance"
    TRANSACTIONS = "transactions"
    HISTORICAL = "historical"
    BACKFILL = "backfill"
    VALIDATION = "validation"

class DataConsistencyLevel(Enum):
    """Data consistency level enumeration"""
    STRICT = "strict"
    NORMAL = "normal"
    RELAXED = "relaxed"

@dataclass
class SyncResult:
    """Synchronization result data"""
    success: bool
    sync_type: SyncType
    account_id: str
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    duplicates_found: int
    errors: List[str]
    duration_seconds: float
    started_at: datetime
    completed_at: datetime

@dataclass
class TransactionData:
    """Transaction data structure"""
    transaction_id: str
    account_id: str
    amount: Decimal
    currency: str
    date: datetime
    name: str
    merchant_name: Optional[str]
    category: List[str]
    pending: bool
    location: Optional[Dict]
    payment_channel: str
    transaction_type: str
    plaid_transaction_id: str
    hash: str

@dataclass
class BalanceData:
    """Balance data structure"""
    account_id: str
    current_balance: Decimal
    available_balance: Decimal
    currency: str
    date: datetime
    type: str

class DataSynchronizationService:
    """Service for comprehensive data synchronization"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db_session = db_session
        self.config = config
        self.plaid_service = PlaidIntegrationService(db_session, config)
        self.notification_service = NotificationService(db_session, config)
        self.audit_service = AuditService(db_session)
        
        # Configuration
        self.max_workers = config.get('sync_max_workers', 4)
        self.batch_size = config.get('sync_batch_size', 100)
        self.retry_attempts = config.get('sync_retry_attempts', 3)
        self.consistency_level = DataConsistencyLevel(config.get('data_consistency_level', 'normal'))
        
        # Cache for duplicate detection
        self.transaction_hashes: Set[str] = set()
        self._load_transaction_hashes()
    
    def sync_account_data(self, account_id: str, sync_type: SyncType = SyncType.TRANSACTIONS, 
                         force_sync: bool = False) -> SyncResult:
        """
        Synchronize account data based on type
        
        Args:
            account_id: Account ID to sync
            sync_type: Type of synchronization to perform
            force_sync: Force sync even if not due
            
        Returns:
            Synchronization result
        """
        start_time = datetime.utcnow()
        
        try:
            # Get account
            account = self.db_session.query(BankAccount).filter(
                BankAccount.id == account_id
            ).first()
            
            if not account:
                return SyncResult(
                    success=False,
                    sync_type=sync_type,
                    account_id=account_id,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_skipped=0,
                    duplicates_found=0,
                    errors=["Account not found"],
                    duration_seconds=0,
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            # Check if sync is needed
            if not force_sync and not self._should_sync(account, sync_type):
                return SyncResult(
                    success=True,
                    sync_type=sync_type,
                    account_id=account_id,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_skipped=0,
                    duplicates_found=0,
                    errors=[],
                    duration_seconds=0,
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            # Create sync record
            sync_record = TransactionSync(
                account_id=account_id,
                sync_type=sync_type.value,
                status=SyncStatus.IN_PROGRESS.value,
                started_at=start_time,
                created_at=datetime.utcnow()
            )
            self.db_session.add(sync_record)
            self.db_session.commit()
            
            # Perform sync based on type
            if sync_type == SyncType.BALANCE:
                result = self._sync_balances(account)
            elif sync_type == SyncType.TRANSACTIONS:
                result = self._sync_transactions(account)
            elif sync_type == SyncType.HISTORICAL:
                result = self._sync_historical_data(account)
            elif sync_type == SyncType.BACKFILL:
                result = self._backfill_historical_data(account)
            elif sync_type == SyncType.VALIDATION:
                result = self._validate_data_consistency(account)
            else:
                result = self._sync_all_data(account)
            
            # Update sync record
            sync_record.status = SyncStatus.COMPLETED.value if result.success else SyncStatus.FAILED.value
            sync_record.completed_at = datetime.utcnow()
            sync_record.records_processed = result.records_processed
            sync_record.records_created = result.records_created
            sync_record.records_updated = result.records_updated
            sync_record.records_skipped = result.records_skipped
            sync_record.duplicates_found = result.duplicates_found
            sync_record.error_message = '; '.join(result.errors) if result.errors else None
            
            # Update account last sync time
            account.last_sync_at = datetime.utcnow()
            account.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            # Send notifications if needed
            if result.success and result.records_created > 0:
                self._send_sync_notification(account, result)
            
            # Audit the sync
            self.audit_service.log_event(
                user_id=account.user_id,
                event_type='data_sync_completed',
                details={
                    'account_id': account_id,
                    'sync_type': sync_type.value,
                    'result': {
                        'success': result.success,
                        'records_processed': result.records_processed,
                        'records_created': result.records_created,
                        'duplicates_found': result.duplicates_found
                    }
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing account {account_id}: {str(e)}")
            self.db_session.rollback()
            
            return SyncResult(
                success=False,
                sync_type=sync_type,
                account_id=account_id,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_skipped=0,
                duplicates_found=0,
                errors=[str(e)],
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def sync_all_accounts(self, sync_type: SyncType = SyncType.TRANSACTIONS, 
                         user_id: Optional[str] = None) -> List[SyncResult]:
        """
        Synchronize all accounts or user accounts
        
        Args:
            sync_type: Type of synchronization to perform
            user_id: Optional user ID to sync only user's accounts
            
        Returns:
            List of synchronization results
        """
        # Get accounts to sync
        query = self.db_session.query(BankAccount).filter(BankAccount.is_active == True)
        if user_id:
            query = query.filter(BankAccount.user_id == user_id)
        
        accounts = query.all()
        
        # Sync accounts in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_account = {
                executor.submit(self.sync_account_data, account.id, sync_type): account
                for account in accounts
            }
            
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error syncing account {account.id}: {str(e)}")
                    results.append(SyncResult(
                        success=False,
                        sync_type=sync_type,
                        account_id=account.id,
                        records_processed=0,
                        records_created=0,
                        records_updated=0,
                        records_skipped=0,
                        duplicates_found=0,
                        errors=[str(e)],
                        duration_seconds=0,
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    ))
        
        return results
    
    def _sync_balances(self, account: BankAccount) -> SyncResult:
        """Sync account balances"""
        start_time = datetime.utcnow()
        records_created = 0
        errors = []
        
        try:
            # Get balances from Plaid
            balance_result = self.plaid_service.get_account_balances(account.plaid_access_token)
            
            if not balance_result.success:
                return SyncResult(
                    success=False,
                    sync_type=SyncType.BALANCE,
                    account_id=account.id,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_skipped=0,
                    duplicates_found=0,
                    errors=[balance_result.error],
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            # Process each balance
            for balance_data in balance_result.balances:
                if balance_data.account_id == account.plaid_account_id:
                    # Create balance record
                    balance = AccountBalance(
                        account_id=account.id,
                        balance_type='current',
                        amount=balance_data.current,
                        currency=balance_data.iso_currency_code,
                        created_at=datetime.utcnow()
                    )
                    self.db_session.add(balance)
                    records_created += 1
                    
                    # Update account current balance
                    account.current_balance = balance_data.current
                    account.available_balance = balance_data.available
                    account.iso_currency_code = balance_data.iso_currency_code
            
            self.db_session.commit()
            
            return SyncResult(
                success=True,
                sync_type=SyncType.BALANCE,
                account_id=account.id,
                records_processed=len(balance_result.balances),
                records_created=records_created,
                records_updated=1,  # Account balance updated
                records_skipped=0,
                duplicates_found=0,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error syncing balances for account {account.id}: {str(e)}")
            errors.append(str(e))
            return SyncResult(
                success=False,
                sync_type=SyncType.BALANCE,
                account_id=account.id,
                records_processed=0,
                records_created=records_created,
                records_updated=0,
                records_skipped=0,
                duplicates_found=0,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _sync_transactions(self, account: BankAccount) -> SyncResult:
        """Sync recent transactions"""
        start_time = datetime.utcnow()
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        duplicates_found = 0
        errors = []
        
        try:
            # Get last sync date
            last_sync = self.db_session.query(TransactionSync).filter(
                and_(
                    TransactionSync.account_id == account.id,
                    TransactionSync.sync_type == SyncType.TRANSACTIONS.value,
                    TransactionSync.status == SyncStatus.COMPLETED.value
                )
            ).order_by(TransactionSync.completed_at.desc()).first()
            
            start_date = last_sync.completed_at if last_sync else (datetime.utcnow() - timedelta(days=30))
            end_date = datetime.utcnow()
            
            # Get transactions from Plaid
            transaction_result = self.plaid_service.get_transactions(
                access_token=account.plaid_access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                account_ids=[account.plaid_account_id]
            )
            
            if not transaction_result.success:
                return SyncResult(
                    success=False,
                    sync_type=SyncType.TRANSACTIONS,
                    account_id=account.id,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_skipped=0,
                    duplicates_found=0,
                    errors=[transaction_result.error],
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
            
            # Process transactions
            for transaction_data in transaction_result.transactions:
                records_processed += 1
                
                # Generate transaction hash for duplicate detection
                transaction_hash = self._generate_transaction_hash(transaction_data)
                
                # Check for duplicates
                if transaction_hash in self.transaction_hashes:
                    duplicates_found += 1
                    records_skipped += 1
                    continue
                
                # Validate transaction data
                validation_result = validate_transaction_data(transaction_data)
                if not validation_result['valid']:
                    errors.append(f"Invalid transaction data: {validation_result['errors']}")
                    records_skipped += 1
                    continue
                
                # Create transaction record
                transaction = PlaidTransaction(
                    plaid_transaction_id=transaction_data.transaction_id,
                    account_id=account.id,
                    amount=transaction_data.amount,
                    currency=transaction_data.iso_currency_code,
                    date=transaction_data.date,
                    name=transaction_data.name,
                    merchant_name=transaction_data.merchant_name,
                    category=json.dumps(transaction_data.category),
                    pending=transaction_data.pending,
                    location=json.dumps(transaction_data.location) if transaction_data.location else None,
                    payment_channel=transaction_data.payment_channel,
                    transaction_type=transaction_data.transaction_type,
                    transaction_hash=transaction_hash,
                    created_at=datetime.utcnow()
                )
                
                self.db_session.add(transaction)
                records_created += 1
                self.transaction_hashes.add(transaction_hash)
            
            self.db_session.commit()
            
            return SyncResult(
                success=True,
                sync_type=SyncType.TRANSACTIONS,
                account_id=account.id,
                records_processed=records_processed,
                records_created=records_created,
                records_updated=records_updated,
                records_skipped=records_skipped,
                duplicates_found=duplicates_found,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error syncing transactions for account {account.id}: {str(e)}")
            errors.append(str(e))
            return SyncResult(
                success=False,
                sync_type=SyncType.TRANSACTIONS,
                account_id=account.id,
                records_processed=records_processed,
                records_created=records_created,
                records_updated=records_updated,
                records_skipped=records_skipped,
                duplicates_found=duplicates_found,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _sync_historical_data(self, account: BankAccount) -> SyncResult:
        """Sync historical data (up to 24 months)"""
        start_time = datetime.utcnow()
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        duplicates_found = 0
        errors = []
        
        try:
            # Calculate date range (24 months back)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=730)  # 24 months
            
            # Get historical transactions in batches
            current_date = start_date
            while current_date < end_date:
                batch_end_date = min(current_date + timedelta(days=30), end_date)
                
                transaction_result = self.plaid_service.get_transactions(
                    access_token=account.plaid_access_token,
                    start_date=current_date.date(),
                    end_date=batch_end_date.date(),
                    account_ids=[account.plaid_account_id]
                )
                
                if not transaction_result.success:
                    errors.append(f"Failed to get transactions for {current_date.date()}: {transaction_result.error}")
                    current_date = batch_end_date
                    continue
                
                # Process batch transactions
                for transaction_data in transaction_result.transactions:
                    records_processed += 1
                    
                    # Generate transaction hash
                    transaction_hash = self._generate_transaction_hash(transaction_data)
                    
                    # Check for duplicates
                    if transaction_hash in self.transaction_hashes:
                        duplicates_found += 1
                        records_skipped += 1
                        continue
                    
                    # Create transaction record
                    transaction = PlaidTransaction(
                        plaid_transaction_id=transaction_data.transaction_id,
                        account_id=account.id,
                        amount=transaction_data.amount,
                        currency=transaction_data.iso_currency_code,
                        date=transaction_data.date,
                        name=transaction_data.name,
                        merchant_name=transaction_data.merchant_name,
                        category=json.dumps(transaction_data.category),
                        pending=transaction_data.pending,
                        location=json.dumps(transaction_data.location) if transaction_data.location else None,
                        payment_channel=transaction_data.payment_channel,
                        transaction_type=transaction_data.transaction_type,
                        transaction_hash=transaction_hash,
                        created_at=datetime.utcnow()
                    )
                    
                    self.db_session.add(transaction)
                    records_created += 1
                    self.transaction_hashes.add(transaction_hash)
                
                current_date = batch_end_date
                
                # Commit batch
                self.db_session.commit()
            
            return SyncResult(
                success=True,
                sync_type=SyncType.HISTORICAL,
                account_id=account.id,
                records_processed=records_processed,
                records_created=records_created,
                records_updated=records_updated,
                records_skipped=records_skipped,
                duplicates_found=duplicates_found,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error syncing historical data for account {account.id}: {str(e)}")
            errors.append(str(e))
            return SyncResult(
                success=False,
                sync_type=SyncType.HISTORICAL,
                account_id=account.id,
                records_processed=records_processed,
                records_created=records_created,
                records_updated=records_updated,
                records_skipped=records_skipped,
                duplicates_found=duplicates_found,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _backfill_historical_data(self, account: BankAccount) -> SyncResult:
        """Backfill missing historical data"""
        start_time = datetime.utcnow()
        records_created = 0
        errors = []
        
        try:
            # Find gaps in transaction data
            gaps = self._find_transaction_gaps(account.id)
            
            for gap_start, gap_end in gaps:
                # Get transactions for gap period
                transaction_result = self.plaid_service.get_transactions(
                    access_token=account.plaid_access_token,
                    start_date=gap_start.date(),
                    end_date=gap_end.date(),
                    account_ids=[account.plaid_account_id]
                )
                
                if transaction_result.success:
                    for transaction_data in transaction_result.transactions:
                        transaction_hash = self._generate_transaction_hash(transaction_data)
                        
                        if transaction_hash not in self.transaction_hashes:
                            transaction = PlaidTransaction(
                                plaid_transaction_id=transaction_data.transaction_id,
                                account_id=account.id,
                                amount=transaction_data.amount,
                                currency=transaction_data.iso_currency_code,
                                date=transaction_data.date,
                                name=transaction_data.name,
                                merchant_name=transaction_data.merchant_name,
                                category=json.dumps(transaction_data.category),
                                pending=transaction_data.pending,
                                location=json.dumps(transaction_data.location) if transaction_data.location else None,
                                payment_channel=transaction_data.payment_channel,
                                transaction_type=transaction_data.transaction_type,
                                transaction_hash=transaction_hash,
                                created_at=datetime.utcnow()
                            )
                            
                            self.db_session.add(transaction)
                            records_created += 1
                            self.transaction_hashes.add(transaction_hash)
            
            self.db_session.commit()
            
            return SyncResult(
                success=True,
                sync_type=SyncType.BACKFILL,
                account_id=account.id,
                records_processed=len(gaps),
                records_created=records_created,
                records_updated=0,
                records_skipped=0,
                duplicates_found=0,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error backfilling historical data for account {account.id}: {str(e)}")
            errors.append(str(e))
            return SyncResult(
                success=False,
                sync_type=SyncType.BACKFILL,
                account_id=account.id,
                records_processed=0,
                records_created=records_created,
                records_updated=0,
                records_skipped=0,
                duplicates_found=0,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _validate_data_consistency(self, account: BankAccount) -> SyncResult:
        """Validate data consistency"""
        start_time = datetime.utcnow()
        errors = []
        issues_found = 0
        
        try:
            # Check for orphaned transactions
            orphaned_transactions = self.db_session.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.account_id == account.id,
                    ~PlaidTransaction.plaid_transaction_id.in_(
                        self.db_session.query(PlaidTransaction.plaid_transaction_id)
                        .filter(PlaidTransaction.account_id == account.id)
                        .subquery()
                    )
                )
            ).count()
            
            if orphaned_transactions > 0:
                errors.append(f"Found {orphaned_transactions} orphaned transactions")
                issues_found += orphaned_transactions
            
            # Check for duplicate transaction hashes
            duplicate_hashes = self.db_session.query(
                PlaidTransaction.transaction_hash,
                func.count(PlaidTransaction.id).label('count')
            ).filter(
                PlaidTransaction.account_id == account.id
            ).group_by(PlaidTransaction.transaction_hash).having(
                func.count(PlaidTransaction.id) > 1
            ).all()
            
            for hash_value, count in duplicate_hashes:
                errors.append(f"Found {count} duplicate transactions with hash {hash_value[:8]}...")
                issues_found += count - 1
            
            # Check for missing required fields
            invalid_transactions = self.db_session.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.account_id == account.id,
                    or_(
                        PlaidTransaction.amount.is_(None),
                        PlaidTransaction.date.is_(None),
                        PlaidTransaction.name.is_(None)
                    )
                )
            ).count()
            
            if invalid_transactions > 0:
                errors.append(f"Found {invalid_transactions} transactions with missing required fields")
                issues_found += invalid_transactions
            
            # Check balance consistency
            balance_issues = self._check_balance_consistency(account.id)
            if balance_issues:
                errors.extend(balance_issues)
                issues_found += len(balance_issues)
            
            return SyncResult(
                success=issues_found == 0,
                sync_type=SyncType.VALIDATION,
                account_id=account.id,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_skipped=0,
                duplicates_found=len(duplicate_hashes),
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error validating data consistency for account {account.id}: {str(e)}")
            errors.append(str(e))
            return SyncResult(
                success=False,
                sync_type=SyncType.VALIDATION,
                account_id=account.id,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_skipped=0,
                duplicates_found=0,
                errors=errors,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _sync_all_data(self, account: BankAccount) -> SyncResult:
        """Sync all data types"""
        results = []
        
        # Sync balances
        balance_result = self._sync_balances(account)
        results.append(balance_result)
        
        # Sync transactions
        transaction_result = self._sync_transactions(account)
        results.append(transaction_result)
        
        # Validate consistency
        validation_result = self._validate_data_consistency(account)
        results.append(validation_result)
        
        # Aggregate results
        total_records_processed = sum(r.records_processed for r in results)
        total_records_created = sum(r.records_created for r in results)
        total_records_updated = sum(r.records_updated for r in results)
        total_records_skipped = sum(r.records_skipped for r in results)
        total_duplicates_found = sum(r.duplicates_found for r in results)
        all_errors = []
        for r in results:
            all_errors.extend(r.errors)
        
        overall_success = all(r.success for r in results)
        
        return SyncResult(
            success=overall_success,
            sync_type=SyncType.TRANSACTIONS,  # Default type
            account_id=account.id,
            records_processed=total_records_processed,
            records_created=total_records_created,
            records_updated=total_records_updated,
            records_skipped=total_records_skipped,
            duplicates_found=total_duplicates_found,
            errors=all_errors,
            duration_seconds=sum(r.duration_seconds for r in results),
            started_at=min(r.started_at for r in results),
            completed_at=max(r.completed_at for r in results)
        )
    
    def _should_sync(self, account: BankAccount, sync_type: SyncType) -> bool:
        """Check if sync is needed"""
        # Get last sync
        last_sync = self.db_session.query(TransactionSync).filter(
            and_(
                TransactionSync.account_id == account.id,
                TransactionSync.sync_type == sync_type.value,
                TransactionSync.status == SyncStatus.COMPLETED.value
            )
        ).order_by(TransactionSync.completed_at.desc()).first()
        
        if not last_sync:
            return True
        
        # Check sync frequency based on type
        if sync_type == SyncType.BALANCE:
            # Balance sync every hour
            return datetime.utcnow() - last_sync.completed_at > timedelta(hours=1)
        elif sync_type == SyncType.TRANSACTIONS:
            # Transaction sync every 6 hours
            return datetime.utcnow() - last_sync.completed_at > timedelta(hours=6)
        elif sync_type == SyncType.HISTORICAL:
            # Historical sync once per day
            return datetime.utcnow() - last_sync.completed_at > timedelta(days=1)
        elif sync_type == SyncType.VALIDATION:
            # Validation once per day
            return datetime.utcnow() - last_sync.completed_at > timedelta(days=1)
        
        return True
    
    def _generate_transaction_hash(self, transaction_data: Any) -> str:
        """Generate unique hash for transaction"""
        hash_string = f"{transaction_data.transaction_id}_{transaction_data.amount}_{transaction_data.date}_{transaction_data.name}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _load_transaction_hashes(self):
        """Load existing transaction hashes into memory"""
        try:
            hashes = self.db_session.query(PlaidTransaction.transaction_hash).all()
            self.transaction_hashes = {h[0] for h in hashes if h[0]}
        except Exception as e:
            logger.error(f"Error loading transaction hashes: {str(e)}")
            self.transaction_hashes = set()
    
    def _find_transaction_gaps(self, account_id: str) -> List[Tuple[datetime, datetime]]:
        """Find gaps in transaction data"""
        gaps = []
        
        # Get transaction date range
        date_range = self.db_session.query(
            func.min(PlaidTransaction.date),
            func.max(PlaidTransaction.date)
        ).filter(PlaidTransaction.account_id == account_id).first()
        
        if not date_range[0] or not date_range[1]:
            return gaps
        
        start_date = date_range[0]
        end_date = date_range[1]
        
        # Find gaps by checking for missing dates
        current_date = start_date
        while current_date < end_date:
            # Check if transactions exist for current date
            transaction_count = self.db_session.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.account_id == account_id,
                    func.date(PlaidTransaction.date) == current_date.date()
                )
            ).count()
            
            if transaction_count == 0:
                # Found a gap, find its end
                gap_start = current_date
                gap_end = current_date
                
                while gap_end < end_date:
                    gap_end += timedelta(days=1)
                    next_day_count = self.db_session.query(PlaidTransaction).filter(
                        and_(
                            PlaidTransaction.account_id == account_id,
                            func.date(PlaidTransaction.date) == gap_end.date()
                        )
                    ).count()
                    
                    if next_day_count > 0:
                        break
                
                gaps.append((gap_start, gap_end))
                current_date = gap_end
            else:
                current_date += timedelta(days=1)
        
        return gaps
    
    def _check_balance_consistency(self, account_id: str) -> List[str]:
        """Check balance consistency"""
        issues = []
        
        # Check for negative balances without proper context
        negative_balances = self.db_session.query(AccountBalance).filter(
            and_(
                AccountBalance.account_id == account_id,
                AccountBalance.amount < 0
            )
        ).count()
        
        if negative_balances > 0:
            issues.append(f"Found {negative_balances} negative balance records")
        
        # Check for balance records without corresponding transactions
        balance_dates = self.db_session.query(func.date(AccountBalance.created_at)).filter(
            AccountBalance.account_id == account_id
        ).distinct().all()
        
        for (balance_date,) in balance_dates:
            transaction_count = self.db_session.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.account_id == account_id,
                    func.date(PlaidTransaction.date) == balance_date
                )
            ).count()
            
            if transaction_count == 0:
                issues.append(f"No transactions found for balance date {balance_date}")
        
        return issues
    
    def _send_sync_notification(self, account: BankAccount, result: SyncResult):
        """Send sync notification to user"""
        if result.records_created > 0:
            self.notification_service.send_notification(
                user_id=account.user_id,
                notification_type='data_sync_completed',
                data={
                    'account_id': account.id,
                    'account_name': account.name,
                    'sync_type': result.sync_type.value,
                    'records_created': result.records_created,
                    'records_processed': result.records_processed,
                    'duplicates_found': result.duplicates_found
                }
            ) 