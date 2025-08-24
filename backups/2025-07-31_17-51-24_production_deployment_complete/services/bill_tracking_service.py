"""
Bill Tracking Service

This module provides bill tracking, due date management, and reminder functionality
for the MINGUS application.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class BillStatus(Enum):
    """Bill status"""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class BillCategory(Enum):
    """Bill categories"""
    UTILITIES = "utilities"
    RENT = "rent"
    MORTGAGE = "mortgage"
    INSURANCE = "insurance"
    SUBSCRIPTION = "subscription"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    MEDICAL = "medical"
    OTHER = "other"


@dataclass
class Bill:
    """Bill data structure"""
    id: str
    user_id: str
    name: str
    description: str
    amount: float
    due_date: date
    category: BillCategory
    status: BillStatus
    is_recurring: bool
    recurring_frequency: Optional[str]  # 'monthly', 'quarterly', 'yearly'
    created_at: datetime
    updated_at: datetime
    paid_date: Optional[date] = None
    reminder_sent: bool = False


@dataclass
class KeyDate:
    """Key date data structure"""
    id: str
    user_id: str
    title: str
    date: date
    category: str
    description: str
    is_recurring: bool
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime


class BillTrackingService:
    """Service for managing bills and key dates"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def get_user_bills(self, user_id: str) -> List[Bill]:
        """Get all bills for a user"""
        try:
            # This would query the actual bills table
            # For now, return mock data
            bills = [
                Bill(
                    id="bill_1",
                    user_id=user_id,
                    name="Electric Bill",
                    description="Monthly electricity bill",
                    amount=125.50,
                    due_date=date.today() + timedelta(days=5),
                    category=BillCategory.UTILITIES,
                    status=BillStatus.PENDING,
                    is_recurring=True,
                    recurring_frequency="monthly",
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow()
                ),
                Bill(
                    id="bill_2",
                    user_id=user_id,
                    name="Rent Payment",
                    description="Monthly rent payment",
                    amount=1200.00,
                    due_date=date.today() + timedelta(days=2),
                    category=BillCategory.RENT,
                    status=BillStatus.PENDING,
                    is_recurring=True,
                    recurring_frequency="monthly",
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow()
                ),
                Bill(
                    id="bill_3",
                    user_id=user_id,
                    name="Car Insurance",
                    description="Quarterly car insurance payment",
                    amount=450.00,
                    due_date=date.today() + timedelta(days=15),
                    category=BillCategory.INSURANCE,
                    status=BillStatus.PENDING,
                    is_recurring=True,
                    recurring_frequency="quarterly",
                    created_at=datetime.utcnow() - timedelta(days=60),
                    updated_at=datetime.utcnow()
                ),
                Bill(
                    id="bill_4",
                    user_id=user_id,
                    name="Netflix Subscription",
                    description="Monthly Netflix subscription",
                    amount=15.99,
                    due_date=date.today() - timedelta(days=1),
                    category=BillCategory.SUBSCRIPTION,
                    status=BillStatus.PAID,
                    is_recurring=True,
                    recurring_frequency="monthly",
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow(),
                    paid_date=date.today() - timedelta(days=1)
                )
            ]
            
            return bills
            
        except Exception as e:
            self.logger.error(f"Error getting bills for user {user_id}: {e}")
            return []
    
    def get_user_key_dates(self, user_id: str) -> List[KeyDate]:
        """Get all key dates for a user"""
        try:
            # This would query the actual key dates table
            # For now, return mock data
            key_dates = [
                KeyDate(
                    id="date_1",
                    user_id=user_id,
                    title="Tax Filing Deadline",
                    date=date.today() + timedelta(days=45),
                    category="tax",
                    description="Federal tax filing deadline",
                    is_recurring=True,
                    reminder_sent=False,
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow()
                ),
                KeyDate(
                    id="date_2",
                    user_id=user_id,
                    title="Car Registration Renewal",
                    date=date.today() + timedelta(days=20),
                    category="vehicle",
                    description="Annual car registration renewal",
                    is_recurring=True,
                    reminder_sent=False,
                    created_at=datetime.utcnow() - timedelta(days=60),
                    updated_at=datetime.utcnow()
                ),
                KeyDate(
                    id="date_3",
                    user_id=user_id,
                    title="Dentist Appointment",
                    date=date.today() + timedelta(days=7),
                    category="health",
                    description="Regular dental checkup",
                    is_recurring=False,
                    reminder_sent=True,
                    created_at=datetime.utcnow() - timedelta(days=14),
                    updated_at=datetime.utcnow()
                )
            ]
            
            return key_dates
            
        except Exception as e:
            self.logger.error(f"Error getting key dates for user {user_id}: {e}")
            return []
    
    def create_bill(self, user_id: str, bill_data: Dict[str, Any]) -> Optional[Bill]:
        """Create a new bill"""
        try:
            # This would create a new bill in the database
            # For now, return a mock bill
            bill = Bill(
                id=f"bill_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                name=bill_data.get('name', 'New Bill'),
                description=bill_data.get('description', ''),
                amount=float(bill_data.get('amount', 0)),
                due_date=bill_data.get('due_date', date.today()),
                category=BillCategory(bill_data.get('category', 'other')),
                status=BillStatus.PENDING,
                is_recurring=bill_data.get('is_recurring', False),
                recurring_frequency=bill_data.get('recurring_frequency'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return bill
            
        except Exception as e:
            self.logger.error(f"Error creating bill for user {user_id}: {e}")
            return None
    
    def create_key_date(self, user_id: str, date_data: Dict[str, Any]) -> Optional[KeyDate]:
        """Create a new key date"""
        try:
            # This would create a new key date in the database
            # For now, return a mock key date
            key_date = KeyDate(
                id=f"date_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                title=date_data.get('title', 'New Date'),
                date=date_data.get('date', date.today()),
                category=date_data.get('category', 'other'),
                description=date_data.get('description', ''),
                is_recurring=date_data.get('is_recurring', False),
                reminder_sent=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return key_date
            
        except Exception as e:
            self.logger.error(f"Error creating key date for user {user_id}: {e}")
            return None
    
    def mark_bill_paid(self, bill_id: str, paid_date: Optional[date] = None) -> bool:
        """Mark a bill as paid"""
        try:
            # This would update the bill status in the database
            # For now, just log the update
            self.logger.info(f"Marked bill {bill_id} as paid on {paid_date or date.today()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking bill {bill_id} as paid: {e}")
            return False
    
    def get_upcoming_bills(self, user_id: str, days: int = 30) -> List[Bill]:
        """Get bills due within the specified number of days"""
        try:
            all_bills = self.get_user_bills(user_id)
            cutoff_date = date.today() + timedelta(days=days)
            
            upcoming_bills = [
                bill for bill in all_bills
                if bill.due_date <= cutoff_date and bill.status == BillStatus.PENDING
            ]
            
            # Sort by due date
            upcoming_bills.sort(key=lambda x: x.due_date)
            
            return upcoming_bills
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming bills for user {user_id}: {e}")
            return []
    
    def get_overdue_bills(self, user_id: str) -> List[Bill]:
        """Get overdue bills"""
        try:
            all_bills = self.get_user_bills(user_id)
            
            overdue_bills = [
                bill for bill in all_bills
                if bill.due_date < date.today() and bill.status == BillStatus.PENDING
            ]
            
            # Sort by due date (most overdue first)
            overdue_bills.sort(key=lambda x: x.due_date)
            
            return overdue_bills
            
        except Exception as e:
            self.logger.error(f"Error getting overdue bills for user {user_id}: {e}")
            return []
    
    def get_bill_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of bills and key dates"""
        try:
            bills = self.get_user_bills(user_id)
            key_dates = self.get_user_key_dates(user_id)
            
            # Calculate summary statistics
            total_bills = len(bills)
            pending_bills = len([b for b in bills if b.status == BillStatus.PENDING])
            overdue_bills = len([b for b in bills if b.due_date < date.today() and b.status == BillStatus.PENDING])
            total_amount = sum(b.amount for b in bills if b.status == BillStatus.PENDING)
            
            upcoming_bills = self.get_upcoming_bills(user_id, 7)
            upcoming_amount = sum(b.amount for b in upcoming_bills)
            
            upcoming_dates = [
                d for d in key_dates
                if d.date <= date.today() + timedelta(days=30)
            ]
            
            return {
                'total_bills': total_bills,
                'pending_bills': pending_bills,
                'overdue_bills': overdue_bills,
                'total_amount': total_amount,
                'upcoming_bills_count': len(upcoming_bills),
                'upcoming_amount': upcoming_amount,
                'upcoming_dates_count': len(upcoming_dates),
                'next_bill_due': min([b.due_date for b in bills if b.status == BillStatus.PENDING]) if pending_bills > 0 else None,
                'next_key_date': min([d.date for d in key_dates]) if key_dates else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting bill summary for user {user_id}: {e}")
            return {}
    
    def send_bill_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """Send reminders for upcoming bills"""
        try:
            upcoming_bills = self.get_upcoming_bills(user_id, 7)
            reminders_sent = []
            
            for bill in upcoming_bills:
                days_until_due = (bill.due_date - date.today()).days
                
                if days_until_due <= 3 and not bill.reminder_sent:
                    reminder = {
                        'bill_id': bill.id,
                        'bill_name': bill.name,
                        'amount': bill.amount,
                        'due_date': bill.due_date,
                        'days_until_due': days_until_due,
                        'priority': 'high' if days_until_due <= 1 else 'medium'
                    }
                    reminders_sent.append(reminder)
                    
                    # Mark reminder as sent
                    bill.reminder_sent = True
            
            return reminders_sent
            
        except Exception as e:
            self.logger.error(f"Error sending bill reminders for user {user_id}: {e}")
            return []
    
    def get_bill_categories_summary(self, user_id: str) -> Dict[str, float]:
        """Get summary of bills by category"""
        try:
            bills = self.get_user_bills(user_id)
            category_totals = {}
            
            for bill in bills:
                if bill.status == BillStatus.PENDING:
                    category = bill.category.value
                    if category not in category_totals:
                        category_totals[category] = 0
                    category_totals[category] += bill.amount
            
            return category_totals
            
        except Exception as e:
            self.logger.error(f"Error getting bill categories summary for user {user_id}: {e}")
            return {} 