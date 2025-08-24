"""
Basic Expense Tracking Service

This module provides basic expense tracking functionality for Budget tier users,
including manual entry, expense summaries, budget tracking, and basic insights.
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


class TransactionType(Enum):
    """Transaction types"""
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class ManualEntry:
    """Manual entry transaction data structure"""
    id: str
    user_id: str
    amount: float
    description: str
    category: str
    date: date
    transaction_type: TransactionType
    created_at: datetime
    updated_at: datetime


@dataclass
class ExpenseSummary:
    """Expense summary data structure"""
    total_expenses: float
    total_income: float
    net_amount: float
    expense_categories: Dict[str, float]
    income_sources: Dict[str, float]
    monthly_trend: str
    top_expense_category: str
    top_income_source: str


@dataclass
class BudgetInfo:
    """Budget information data structure"""
    budget_id: str
    user_id: str
    category: str
    amount: float
    spent: float
    remaining: float
    percentage_used: float
    status: str  # 'under_budget', 'over_budget', 'on_track'


class BasicExpenseTrackingService:
    """Service for basic expense tracking and budgeting"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        
        # Mock data storage (in production, this would be database tables)
        self.manual_entries: Dict[str, List[ManualEntry]] = {}
        self.budgets: Dict[str, List[BudgetInfo]] = {}
    
    def add_manual_entry(self, user_id: str, entry_data: Dict[str, Any]) -> Optional[ManualEntry]:
        """Add a new manual entry transaction"""
        try:
            # Validate entry data
            if not self._validate_entry_data(entry_data):
                raise ValueError("Invalid entry data")
            
            # Create manual entry
            entry = ManualEntry(
                id=f"entry_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                amount=float(entry_data['amount']),
                description=entry_data['description'],
                category=entry_data['category'],
                date=entry_data['date'],
                transaction_type=TransactionType(entry_data['transaction_type']),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store entry
            if user_id not in self.manual_entries:
                self.manual_entries[user_id] = []
            self.manual_entries[user_id].append(entry)
            
            self.logger.info(f"Added manual entry for user {user_id}: {entry.description}")
            return entry
            
        except Exception as e:
            self.logger.error(f"Error adding manual entry for user {user_id}: {e}")
            return None
    
    def _validate_entry_data(self, entry_data: Dict[str, Any]) -> bool:
        """Validate manual entry data"""
        required_fields = ['amount', 'description', 'category', 'date', 'transaction_type']
        
        for field in required_fields:
            if field not in entry_data:
                return False
        
        try:
            float(entry_data['amount'])
            TransactionType(entry_data['transaction_type'])
        except (ValueError, KeyError):
            return False
        
        return True
    
    def get_recent_manual_entries(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent manual entries for a user"""
        try:
            entries = self.manual_entries.get(user_id, [])
            
            # Sort by date (most recent first)
            entries.sort(key=lambda x: x.date, reverse=True)
            
            # Convert to dictionary format
            entries_data = []
            for entry in entries[:limit]:
                entry_dict = {
                    'id': entry.id,
                    'amount': entry.amount,
                    'description': entry.description,
                    'category': entry.category,
                    'date': entry.date.isoformat(),
                    'transaction_type': entry.transaction_type.value,
                    'created_at': entry.created_at.isoformat()
                }
                entries_data.append(entry_dict)
            
            return entries_data
            
        except Exception as e:
            self.logger.error(f"Error getting recent manual entries for user {user_id}: {e}")
            return []
    
    def get_manual_entry_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for manual entries"""
        try:
            entries = self.manual_entries.get(user_id, [])
            
            if not entries:
                return {
                    'total_entries': 0,
                    'entries_this_month': 0,
                    'active_days': 0,
                    'total_expenses': 0.0,
                    'total_income': 0.0,
                    'net_amount': 0.0
                }
            
            # Calculate statistics
            total_entries = len(entries)
            
            # Entries this month
            current_month = date.today().replace(day=1)
            entries_this_month = len([e for e in entries if e.date >= current_month])
            
            # Active days (days with entries)
            active_days = len(set(e.date for e in entries))
            
            # Financial totals
            expenses = [e for e in entries if e.transaction_type == TransactionType.EXPENSE]
            income = [e for e in entries if e.transaction_type == TransactionType.INCOME]
            
            total_expenses = sum(e.amount for e in expenses)
            total_income = sum(e.amount for e in income)
            net_amount = total_income - total_expenses
            
            return {
                'total_entries': total_entries,
                'entries_this_month': entries_this_month,
                'active_days': active_days,
                'total_expenses': total_expenses,
                'total_income': total_income,
                'net_amount': net_amount
            }
            
        except Exception as e:
            self.logger.error(f"Error getting manual entry statistics for user {user_id}: {e}")
            return {}
    
    def get_expense_summary(self, user_id: str) -> Dict[str, Any]:
        """Get expense summary for a user"""
        try:
            entries = self.manual_entries.get(user_id, [])
            
            if not entries:
                return {
                    'total_expenses': 0.0,
                    'total_income': 0.0,
                    'net_amount': 0.0,
                    'expense_categories': {},
                    'income_sources': {},
                    'monthly_trend': 'stable',
                    'top_expense_category': 'None',
                    'top_income_source': 'None'
                }
            
            # Separate expenses and income
            expenses = [e for e in entries if e.transaction_type == TransactionType.EXPENSE]
            income = [e for e in entries if e.transaction_type == TransactionType.INCOME]
            
            # Calculate totals
            total_expenses = sum(e.amount for e in expenses)
            total_income = sum(e.amount for e in income)
            net_amount = total_income - total_expenses
            
            # Category breakdown
            expense_categories = {}
            for expense in expenses:
                category = expense.category
                if category not in expense_categories:
                    expense_categories[category] = 0
                expense_categories[category] += expense.amount
            
            income_sources = {}
            for inc in income:
                source = inc.description  # Use description as income source
                if source not in income_sources:
                    income_sources[source] = 0
                income_sources[source] += inc.amount
            
            # Determine trends
            monthly_trend = self._calculate_monthly_trend(entries)
            
            # Top categories
            top_expense_category = max(expense_categories.items(), key=lambda x: x[1])[0] if expense_categories else 'None'
            top_income_source = max(income_sources.items(), key=lambda x: x[1])[0] if income_sources else 'None'
            
            return {
                'total_expenses': total_expenses,
                'total_income': total_income,
                'net_amount': net_amount,
                'expense_categories': expense_categories,
                'income_sources': income_sources,
                'monthly_trend': monthly_trend,
                'top_expense_category': top_expense_category,
                'top_income_source': top_income_source
            }
            
        except Exception as e:
            self.logger.error(f"Error getting expense summary for user {user_id}: {e}")
            return {}
    
    def _calculate_monthly_trend(self, entries: List[ManualEntry]) -> str:
        """Calculate monthly spending trend"""
        try:
            if len(entries) < 2:
                return 'stable'
            
            # Get current and previous month totals
            current_month = date.today().replace(day=1)
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            
            current_month_expenses = sum(
                e.amount for e in entries 
                if e.transaction_type == TransactionType.EXPENSE and e.date >= current_month
            )
            
            previous_month_expenses = sum(
                e.amount for e in entries 
                if e.transaction_type == TransactionType.EXPENSE and e.date >= previous_month and e.date < current_month
            )
            
            if previous_month_expenses == 0:
                return 'stable'
            
            change_percentage = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100
            
            if change_percentage > 10:
                return 'increasing'
            elif change_percentage < -10:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            self.logger.error(f"Error calculating monthly trend: {e}")
            return 'stable'
    
    def get_recent_transactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for a user"""
        try:
            entries = self.manual_entries.get(user_id, [])
            
            # Sort by date (most recent first)
            entries.sort(key=lambda x: x.date, reverse=True)
            
            # Convert to transaction format
            transactions = []
            for entry in entries[:limit]:
                transaction = {
                    'id': entry.id,
                    'amount': entry.amount,
                    'description': entry.description,
                    'category': entry.category,
                    'date': entry.date.isoformat(),
                    'type': entry.transaction_type.value,
                    'formatted_amount': f"${entry.amount:.2f}" if entry.transaction_type == TransactionType.EXPENSE else f"+${entry.amount:.2f}"
                }
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting recent transactions for user {user_id}: {e}")
            return []
    
    def get_category_breakdown(self, user_id: str) -> Dict[str, Any]:
        """Get category breakdown for expenses"""
        try:
            entries = self.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type == TransactionType.EXPENSE]
            
            if not expenses:
                return {'categories': {}, 'total': 0.0}
            
            # Calculate category totals
            categories = {}
            total = 0.0
            
            for expense in expenses:
                category = expense.category
                if category not in categories:
                    categories[category] = 0
                categories[category] += expense.amount
                total += expense.amount
            
            # Calculate percentages
            category_breakdown = {}
            for category, amount in categories.items():
                percentage = (amount / total * 100) if total > 0 else 0
                category_breakdown[category] = {
                    'amount': amount,
                    'percentage': percentage
                }
            
            return {
                'categories': category_breakdown,
                'total': total
            }
            
        except Exception as e:
            self.logger.error(f"Error getting category breakdown for user {user_id}: {e}")
            return {'categories': {}, 'total': 0.0}
    
    def create_budget(self, user_id: str, budget_data: Dict[str, Any]) -> Optional[BudgetInfo]:
        """Create a new budget for a user"""
        try:
            budget = BudgetInfo(
                budget_id=f"budget_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                category=budget_data['category'],
                amount=float(budget_data['amount']),
                spent=0.0,
                remaining=float(budget_data['amount']),
                percentage_used=0.0,
                status='under_budget'
            )
            
            # Store budget
            if user_id not in self.budgets:
                self.budgets[user_id] = []
            self.budgets[user_id].append(budget)
            
            return budget
            
        except Exception as e:
            self.logger.error(f"Error creating budget for user {user_id}: {e}")
            return None
    
    def get_budget_overview(self, user_id: str) -> List[Dict[str, Any]]:
        """Get budget overview for a user"""
        try:
            budgets = self.budgets.get(user_id, [])
            
            # Update budget spending based on recent entries
            self._update_budget_spending(user_id)
            
            # Convert to dictionary format
            budget_data = []
            for budget in budgets:
                budget_dict = {
                    'budget_id': budget.budget_id,
                    'category': budget.category,
                    'amount': budget.amount,
                    'spent': budget.spent,
                    'remaining': budget.remaining,
                    'percentage_used': budget.percentage_used,
                    'status': budget.status
                }
                budget_data.append(budget_dict)
            
            return budget_data
            
        except Exception as e:
            self.logger.error(f"Error getting budget overview for user {user_id}: {e}")
            return []
    
    def _update_budget_spending(self, user_id: str):
        """Update budget spending based on recent entries"""
        try:
            budgets = self.budgets.get(user_id, [])
            entries = self.manual_entries.get(user_id, [])
            
            # Get current month expenses
            current_month = date.today().replace(day=1)
            current_month_expenses = [
                e for e in entries 
                if e.transaction_type == TransactionType.EXPENSE and e.date >= current_month
            ]
            
            # Update each budget
            for budget in budgets:
                # Calculate spending for this category
                category_spending = sum(
                    e.amount for e in current_month_expenses 
                    if e.category == budget.category
                )
                
                budget.spent = category_spending
                budget.remaining = budget.amount - category_spending
                budget.percentage_used = (category_spending / budget.amount * 100) if budget.amount > 0 else 0
                
                # Update status
                if budget.percentage_used >= 100:
                    budget.status = 'over_budget'
                elif budget.percentage_used >= 80:
                    budget.status = 'on_track'
                else:
                    budget.status = 'under_budget'
                    
        except Exception as e:
            self.logger.error(f"Error updating budget spending for user {user_id}: {e}")
    
    def get_spending_vs_budget(self, user_id: str) -> Dict[str, Any]:
        """Get spending vs budget comparison"""
        try:
            budgets = self.budgets.get(user_id, [])
            
            if not budgets:
                return {
                    'total_budget': 0.0,
                    'total_spent': 0.0,
                    'total_remaining': 0.0,
                    'overall_percentage': 0.0,
                    'budgets_over': 0,
                    'budgets_under': 0
                }
            
            total_budget = sum(b.amount for b in budgets)
            total_spent = sum(b.spent for b in budgets)
            total_remaining = total_budget - total_spent
            overall_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0
            
            budgets_over = len([b for b in budgets if b.status == 'over_budget'])
            budgets_under = len([b for b in budgets if b.status == 'under_budget'])
            
            return {
                'total_budget': total_budget,
                'total_spent': total_spent,
                'total_remaining': total_remaining,
                'overall_percentage': overall_percentage,
                'budgets_over': budgets_over,
                'budgets_under': budgets_under
            }
            
        except Exception as e:
            self.logger.error(f"Error getting spending vs budget for user {user_id}: {e}")
            return {}
    
    def get_budget_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get budget recommendations based on spending patterns"""
        try:
            entries = self.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type == TransactionType.EXPENSE]
            
            if not expenses:
                return []
            
            # Calculate average spending by category
            category_averages = {}
            for expense in expenses:
                category = expense.category
                if category not in category_averages:
                    category_averages[category] = []
                category_averages[category].append(expense.amount)
            
            recommendations = []
            
            for category, amounts in category_averages.items():
                avg_amount = sum(amounts) / len(amounts)
                recommended_budget = avg_amount * 1.1  # 10% buffer
                
                recommendation = {
                    'category': category,
                    'current_average': avg_amount,
                    'recommended_budget': recommended_budget,
                    'reasoning': f'Based on average spending of ${avg_amount:.2f} per month'
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting budget recommendations for user {user_id}: {e}")
            return []
    
    def get_basic_insights(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get basic insights for the user"""
        try:
            entries = self.manual_entries.get(user_id, [])
            
            if not entries:
                return []
            
            insights = []
            
            # Analyze spending patterns
            expense_summary = self.get_expense_summary(user_id)
            
            # Insight 1: Top spending category
            if expense_summary['top_expense_category'] != 'None':
                insights.append({
                    'id': 'top_category',
                    'title': 'Top Spending Category',
                    'description': f"Your highest spending category is {expense_summary['top_expense_category']}",
                    'category': 'spending_pattern',
                    'impact_score': 0.7,
                    'actionable': True,
                    'recommendation': f"Consider setting a budget for {expense_summary['top_expense_category']} to control spending"
                })
            
            # Insight 2: Monthly trend
            if expense_summary['monthly_trend'] == 'increasing':
                insights.append({
                    'id': 'increasing_spending',
                    'title': 'Spending Trend',
                    'description': "Your monthly spending has been increasing",
                    'category': 'trend',
                    'impact_score': 0.8,
                    'actionable': True,
                    'recommendation': 'Review your recent expenses to identify areas for cost reduction'
                })
            
            # Insight 3: Net income
            if expense_summary['net_amount'] < 0:
                insights.append({
                    'id': 'negative_net',
                    'title': 'Income vs Expenses',
                    'description': "Your expenses exceed your income this month",
                    'category': 'financial_health',
                    'impact_score': 0.9,
                    'actionable': True,
                    'recommendation': 'Focus on reducing expenses or increasing income to improve financial health'
                })
            
            # Insight 4: Category diversity
            category_count = len(expense_summary['expense_categories'])
            if category_count > 8:
                insights.append({
                    'id': 'category_diversity',
                    'title': 'Spending Diversity',
                    'description': f"You spend across {category_count} different categories",
                    'category': 'spending_pattern',
                    'impact_score': 0.5,
                    'actionable': False,
                    'recommendation': 'Consider consolidating similar expenses to simplify tracking'
                })
            
            # Insight 5: Budget status
            budget_overview = self.get_spending_vs_budget(user_id)
            if budget_overview.get('budgets_over', 0) > 0:
                insights.append({
                    'id': 'over_budget',
                    'title': 'Budget Status',
                    'description': f"You are over budget in {budget_overview['budgets_over']} category(ies)",
                    'category': 'budget',
                    'impact_score': 0.8,
                    'actionable': True,
                    'recommendation': 'Review your budget allocations and adjust spending accordingly'
                })
            
            return insights[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting basic insights for user {user_id}: {e}")
            return [] 