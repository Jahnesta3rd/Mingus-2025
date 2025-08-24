"""
Financial Health Scoring System

This module provides comprehensive financial health scoring including user financial health
assessment based on banking data, progress tracking over time, goal achievement rates,
risk factor identification, and success metric correlations.
"""

import logging
import time
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import defaultdict, Counter
import threading
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, case, when
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
from scipy import stats

from backend.models.user_models import User
from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.models.analytics_models import AnalyticsEvent, UserBehavior
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity

logger = logging.getLogger(__name__)


class FinancialHealthMetric(Enum):
    """Financial health metrics"""
    SAVINGS_RATE = "savings_rate"
    DEBT_TO_INCOME = "debt_to_income"
    EMERGENCY_FUND = "emergency_fund"
    CREDIT_UTILIZATION = "credit_utilization"
    BUDGET_ADHERENCE = "budget_adherence"
    SPENDING_PATTERNS = "spending_patterns"
    INVESTMENT_DIVERSITY = "investment_diversity"
    INCOME_STABILITY = "income_stability"
    EXPENSE_RATIO = "expense_ratio"
    NET_WORTH_GROWTH = "net_worth_growth"


class RiskLevel(Enum):
    """Financial risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GoalStatus(Enum):
    """Goal achievement status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    ACHIEVED = "achieved"
    AT_RISK = "at_risk"
    FAILED = "failed"


@dataclass
class FinancialHealthScore:
    """Financial health score data"""
    score_id: str
    user_id: str
    overall_score: float
    score_date: datetime
    metrics: Dict[str, float]
    risk_factors: List[str]
    recommendations: List[str]
    goal_progress: Dict[str, float]
    trend_direction: str  # improving, declining, stable
    confidence_level: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialGoal:
    """Financial goal data"""
    goal_id: str
    user_id: str
    goal_type: str
    goal_name: str
    target_amount: float
    current_amount: float
    target_date: datetime
    created_date: datetime
    status: GoalStatus
    progress_percentage: float
    risk_level: RiskLevel
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskFactor:
    """Risk factor data"""
    risk_id: str
    user_id: str
    risk_type: str
    risk_name: str
    risk_level: RiskLevel
    risk_score: float
    description: str
    impact_score: float
    mitigation_strategies: List[str]
    detected_date: datetime
    resolved_date: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SuccessMetric:
    """Success metric data"""
    metric_id: str
    user_id: str
    metric_type: str
    metric_name: str
    current_value: float
    target_value: float
    correlation_strength: float
    trend_direction: str
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressTracking:
    """Progress tracking data"""
    tracking_id: str
    user_id: str
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    tracking_date: datetime
    period_type: str  # daily, weekly, monthly, quarterly
    trend_direction: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialHealthScoring:
    """Comprehensive financial health scoring system"""
    
    def __init__(self, db_session: Session, access_control_service: AccessControlService,
                 audit_service: AuditLoggingService):
        self.db = db_session
        self.access_control_service = access_control_service
        self.audit_service = audit_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize data storage
        self.health_scores = self._initialize_health_scores()
        self.financial_goals = self._initialize_financial_goals()
        self.risk_factors = self._initialize_risk_factors()
        self.success_metrics = self._initialize_success_metrics()
        self.progress_tracking = self._initialize_progress_tracking()
        
        # Scoring weights and thresholds
        self.scoring_weights = self._initialize_scoring_weights()
        self.risk_thresholds = self._initialize_risk_thresholds()
        self.goal_thresholds = self._initialize_goal_thresholds()
        
        # Start health monitoring
        self._start_health_monitoring()
    
    def _initialize_health_scores(self) -> Dict[str, FinancialHealthScore]:
        """Initialize health scores storage"""
        return {}
    
    def _initialize_financial_goals(self) -> Dict[str, FinancialGoal]:
        """Initialize financial goals storage"""
        return {}
    
    def _initialize_risk_factors(self) -> Dict[str, RiskFactor]:
        """Initialize risk factors storage"""
        return {}
    
    def _initialize_success_metrics(self) -> Dict[str, SuccessMetric]:
        """Initialize success metrics storage"""
        return {}
    
    def _initialize_progress_tracking(self) -> Dict[str, ProgressTracking]:
        """Initialize progress tracking storage"""
        return {}
    
    def _initialize_scoring_weights(self) -> Dict[FinancialHealthMetric, float]:
        """Initialize scoring weights for different metrics"""
        return {
            FinancialHealthMetric.SAVINGS_RATE: 0.20,
            FinancialHealthMetric.DEBT_TO_INCOME: 0.15,
            FinancialHealthMetric.EMERGENCY_FUND: 0.15,
            FinancialHealthMetric.CREDIT_UTILIZATION: 0.10,
            FinancialHealthMetric.BUDGET_ADHERENCE: 0.10,
            FinancialHealthMetric.SPENDING_PATTERNS: 0.10,
            FinancialHealthMetric.INVESTMENT_DIVERSITY: 0.05,
            FinancialHealthMetric.INCOME_STABILITY: 0.05,
            FinancialHealthMetric.EXPENSE_RATIO: 0.05,
            FinancialHealthMetric.NET_WORTH_GROWTH: 0.05
        }
    
    def _initialize_risk_thresholds(self) -> Dict[RiskLevel, Dict[str, float]]:
        """Initialize risk thresholds"""
        return {
            RiskLevel.LOW: {
                'savings_rate': 0.20,
                'debt_to_income': 0.30,
                'emergency_fund_months': 6.0,
                'credit_utilization': 0.30,
                'budget_adherence': 0.80
            },
            RiskLevel.MEDIUM: {
                'savings_rate': 0.10,
                'debt_to_income': 0.43,
                'emergency_fund_months': 3.0,
                'credit_utilization': 0.50,
                'budget_adherence': 0.60
            },
            RiskLevel.HIGH: {
                'savings_rate': 0.05,
                'debt_to_income': 0.50,
                'emergency_fund_months': 1.0,
                'credit_utilization': 0.70,
                'budget_adherence': 0.40
            },
            RiskLevel.CRITICAL: {
                'savings_rate': 0.00,
                'debt_to_income': 0.60,
                'emergency_fund_months': 0.0,
                'credit_utilization': 0.90,
                'budget_adherence': 0.20
            }
        }
    
    def _initialize_goal_thresholds(self) -> Dict[GoalStatus, Dict[str, float]]:
        """Initialize goal achievement thresholds"""
        return {
            GoalStatus.NOT_STARTED: {'progress': 0.0},
            GoalStatus.IN_PROGRESS: {'progress': 0.25},
            GoalStatus.ON_TRACK: {'progress': 0.75},
            GoalStatus.ACHIEVED: {'progress': 1.0},
            GoalStatus.AT_RISK: {'progress': 0.50},
            GoalStatus.FAILED: {'progress': 0.0}
        }
    
    def _start_health_monitoring(self):
        """Start financial health monitoring thread"""
        try:
            monitoring_thread = threading.Thread(target=self._monitor_financial_health, daemon=True)
            monitoring_thread.start()
            self.logger.info("Financial health monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting financial health monitoring: {e}")
    
    def _monitor_financial_health(self):
        """Monitor financial health and generate insights"""
        while True:
            try:
                # Update health scores
                self._update_health_scores()
                
                # Identify risk factors
                self._identify_risk_factors()
                
                # Update goal progress
                self._update_goal_progress()
                
                # Calculate success correlations
                self._calculate_success_correlations()
                
                # Sleep for monitoring interval
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Error in financial health monitoring: {e}")
                time.sleep(3600)  # Wait before retrying
    
    def calculate_financial_health_score(self, user_id: str, banking_data: Dict[str, Any] = None) -> str:
        """Calculate comprehensive financial health score for a user"""
        try:
            score_id = f"health_{int(time.time())}_{secrets.token_hex(4)}"
            
            # Calculate individual metrics
            metrics = {}
            risk_factors = []
            recommendations = []
            
            # Savings rate calculation
            savings_rate = self._calculate_savings_rate(user_id, banking_data)
            metrics[FinancialHealthMetric.SAVINGS_RATE.value] = savings_rate
            
            # Debt to income ratio
            debt_to_income = self._calculate_debt_to_income(user_id, banking_data)
            metrics[FinancialHealthMetric.DEBT_TO_INCOME.value] = debt_to_income
            
            # Emergency fund assessment
            emergency_fund = self._calculate_emergency_fund(user_id, banking_data)
            metrics[FinancialHealthMetric.EMERGENCY_FUND.value] = emergency_fund
            
            # Credit utilization
            credit_utilization = self._calculate_credit_utilization(user_id, banking_data)
            metrics[FinancialHealthMetric.CREDIT_UTILIZATION.value] = credit_utilization
            
            # Budget adherence
            budget_adherence = self._calculate_budget_adherence(user_id, banking_data)
            metrics[FinancialHealthMetric.BUDGET_ADHERENCE.value] = budget_adherence
            
            # Spending patterns
            spending_patterns = self._calculate_spending_patterns(user_id, banking_data)
            metrics[FinancialHealthMetric.SPENDING_PATTERNS.value] = spending_patterns
            
            # Investment diversity
            investment_diversity = self._calculate_investment_diversity(user_id, banking_data)
            metrics[FinancialHealthMetric.INVESTMENT_DIVERSITY.value] = investment_diversity
            
            # Income stability
            income_stability = self._calculate_income_stability(user_id, banking_data)
            metrics[FinancialHealthMetric.INCOME_STABILITY.value] = income_stability
            
            # Expense ratio
            expense_ratio = self._calculate_expense_ratio(user_id, banking_data)
            metrics[FinancialHealthMetric.EXPENSE_RATIO.value] = expense_ratio
            
            # Net worth growth
            net_worth_growth = self._calculate_net_worth_growth(user_id, banking_data)
            metrics[FinancialHealthMetric.NET_WORTH_GROWTH.value] = net_worth_growth
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(metrics)
            
            # Identify risk factors
            risk_factors = self._identify_user_risk_factors(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, risk_factors)
            
            # Get goal progress
            goal_progress = self._get_goal_progress(user_id)
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(user_id, overall_score)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(metrics, banking_data)
            
            # Create health score record
            health_score = FinancialHealthScore(
                score_id=score_id,
                user_id=user_id,
                overall_score=overall_score,
                score_date=datetime.utcnow(),
                metrics=metrics,
                risk_factors=risk_factors,
                recommendations=recommendations,
                goal_progress=goal_progress,
                trend_direction=trend_direction,
                confidence_level=confidence_level,
                metadata={'banking_data_used': bool(banking_data)}
            )
            
            self.health_scores[score_id] = health_score
            
            # Log health score calculation
            self.audit_service.log_event(
                event_type=AuditEventType.FINANCIAL_HEALTH_SCORE,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"Financial health score calculated for user {user_id}",
                resource_type="financial_health",
                resource_id=score_id,
                user_id=user_id,
                metadata={
                    'overall_score': overall_score,
                    'risk_factors_count': len(risk_factors),
                    'recommendations_count': len(recommendations)
                }
            )
            
            return score_id
            
        except Exception as e:
            self.logger.error(f"Error calculating financial health score: {e}")
            raise
    
    def _calculate_savings_rate(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate savings rate"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            if banking_data and 'income' in banking_data and 'expenses' in banking_data:
                income = banking_data['income']
                expenses = banking_data['expenses']
                savings = income - expenses
                return savings / income if income > 0 else 0.0
            else:
                # Default calculation based on user profile
                return 0.15  # 15% default savings rate
            
        except Exception as e:
            self.logger.error(f"Error calculating savings rate: {e}")
            return 0.0
    
    def _calculate_debt_to_income(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate debt to income ratio"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            if banking_data and 'monthly_debt' in banking_data and 'monthly_income' in banking_data:
                monthly_debt = banking_data['monthly_debt']
                monthly_income = banking_data['monthly_income']
                return monthly_debt / monthly_income if monthly_income > 0 else 0.0
            else:
                # Default calculation
                return 0.35  # 35% default debt to income ratio
            
        except Exception as e:
            self.logger.error(f"Error calculating debt to income ratio: {e}")
            return 0.0
    
    def _calculate_emergency_fund(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate emergency fund adequacy"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            if banking_data and 'emergency_savings' in banking_data and 'monthly_expenses' in banking_data:
                emergency_savings = banking_data['emergency_savings']
                monthly_expenses = banking_data['monthly_expenses']
                return emergency_savings / monthly_expenses if monthly_expenses > 0 else 0.0
            else:
                # Default calculation
                return 3.0  # 3 months default emergency fund
            
        except Exception as e:
            self.logger.error(f"Error calculating emergency fund: {e}")
            return 0.0
    
    def _calculate_credit_utilization(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate credit utilization ratio"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            if banking_data and 'credit_used' in banking_data and 'credit_limit' in banking_data:
                credit_used = banking_data['credit_used']
                credit_limit = banking_data['credit_limit']
                return credit_used / credit_limit if credit_limit > 0 else 0.0
            else:
                # Default calculation
                return 0.25  # 25% default credit utilization
            
        except Exception as e:
            self.logger.error(f"Error calculating credit utilization: {e}")
            return 0.0
    
    def _calculate_budget_adherence(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate budget adherence rate"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            if banking_data and 'budgeted_amount' in banking_data and 'actual_spending' in banking_data:
                budgeted_amount = banking_data['budgeted_amount']
                actual_spending = banking_data['actual_spending']
                return 1.0 - (actual_spending / budgeted_amount - 1.0) if budgeted_amount > 0 else 0.0
            else:
                # Default calculation
                return 0.75  # 75% default budget adherence
            
        except Exception as e:
            self.logger.error(f"Error calculating budget adherence: {e}")
            return 0.0
    
    def _calculate_spending_patterns(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate spending pattern health score"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            # This would analyze spending consistency, discretionary vs essential spending, etc.
            return 0.80  # 80% default spending pattern score
            
        except Exception as e:
            self.logger.error(f"Error calculating spending patterns: {e}")
            return 0.0
    
    def _calculate_investment_diversity(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate investment diversity score"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            # This would analyze investment portfolio diversity
            return 0.60  # 60% default investment diversity score
            
        except Exception as e:
            self.logger.error(f"Error calculating investment diversity: {e}")
            return 0.0
    
    def _calculate_income_stability(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate income stability score"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            # This would analyze income consistency over time
            return 0.85  # 85% default income stability score
            
        except Exception as e:
            self.logger.error(f"Error calculating income stability: {e}")
            return 0.0
    
    def _calculate_expense_ratio(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate expense ratio"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            if banking_data and 'total_expenses' in banking_data and 'total_income' in banking_data:
                total_expenses = banking_data['total_expenses']
                total_income = banking_data['total_income']
                return total_expenses / total_income if total_income > 0 else 0.0
            else:
                # Default calculation
                return 0.70  # 70% default expense ratio
            
        except Exception as e:
            self.logger.error(f"Error calculating expense ratio: {e}")
            return 0.0
    
    def _calculate_net_worth_growth(self, user_id: str, banking_data: Dict[str, Any] = None) -> float:
        """Calculate net worth growth rate"""
        try:
            # Mock calculation - in real implementation, would use actual banking data
            # This would analyze net worth growth over time
            return 0.05  # 5% default net worth growth rate
            
        except Exception as e:
            self.logger.error(f"Error calculating net worth growth: {e}")
            return 0.0
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall financial health score"""
        try:
            overall_score = 0.0
            
            for metric_name, value in metrics.items():
                weight = self.scoring_weights.get(FinancialHealthMetric(metric_name), 0.0)
                
                # Normalize metric value to 0-100 scale
                normalized_value = self._normalize_metric_value(metric_name, value)
                
                overall_score += weight * normalized_value
            
            return min(100.0, max(0.0, overall_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _normalize_metric_value(self, metric_name: str, value: float) -> float:
        """Normalize metric value to 0-100 scale"""
        try:
            if metric_name == FinancialHealthMetric.SAVINGS_RATE.value:
                return min(100.0, value * 100)  # Convert percentage to 0-100
            elif metric_name == FinancialHealthMetric.DEBT_TO_INCOME.value:
                return max(0.0, 100.0 - (value * 100))  # Lower is better
            elif metric_name == FinancialHealthMetric.EMERGENCY_FUND.value:
                return min(100.0, (value / 6.0) * 100)  # 6 months = 100%
            elif metric_name == FinancialHealthMetric.CREDIT_UTILIZATION.value:
                return max(0.0, 100.0 - (value * 100))  # Lower is better
            elif metric_name == FinancialHealthMetric.BUDGET_ADHERENCE.value:
                return value * 100  # Convert percentage to 0-100
            elif metric_name == FinancialHealthMetric.SPENDING_PATTERNS.value:
                return value * 100  # Convert percentage to 0-100
            elif metric_name == FinancialHealthMetric.INVESTMENT_DIVERSITY.value:
                return value * 100  # Convert percentage to 0-100
            elif metric_name == FinancialHealthMetric.INCOME_STABILITY.value:
                return value * 100  # Convert percentage to 0-100
            elif metric_name == FinancialHealthMetric.EXPENSE_RATIO.value:
                return max(0.0, 100.0 - (value * 100))  # Lower is better
            elif metric_name == FinancialHealthMetric.NET_WORTH_GROWTH.value:
                return min(100.0, max(0.0, value * 1000))  # Convert to percentage
            else:
                return value * 100  # Default normalization
            
        except Exception as e:
            self.logger.error(f"Error normalizing metric value: {e}")
            return 0.0
    
    def _identify_user_risk_factors(self, metrics: Dict[str, float]) -> List[str]:
        """Identify risk factors based on metrics"""
        try:
            risk_factors = []
            
            # Check savings rate
            if metrics.get(FinancialHealthMetric.SAVINGS_RATE.value, 0) < 0.10:
                risk_factors.append("Low savings rate")
            
            # Check debt to income ratio
            if metrics.get(FinancialHealthMetric.DEBT_TO_INCOME.value, 0) > 0.43:
                risk_factors.append("High debt to income ratio")
            
            # Check emergency fund
            if metrics.get(FinancialHealthMetric.EMERGENCY_FUND.value, 0) < 3.0:
                risk_factors.append("Insufficient emergency fund")
            
            # Check credit utilization
            if metrics.get(FinancialHealthMetric.CREDIT_UTILIZATION.value, 0) > 0.30:
                risk_factors.append("High credit utilization")
            
            # Check budget adherence
            if metrics.get(FinancialHealthMetric.BUDGET_ADHERENCE.value, 0) < 0.60:
                risk_factors.append("Poor budget adherence")
            
            return risk_factors
            
        except Exception as e:
            self.logger.error(f"Error identifying risk factors: {e}")
            return []
    
    def _generate_recommendations(self, metrics: Dict[str, float], risk_factors: List[str]) -> List[str]:
        """Generate recommendations based on metrics and risk factors"""
        try:
            recommendations = []
            
            # Generate recommendations based on risk factors
            for risk_factor in risk_factors:
                if risk_factor == "Low savings rate":
                    recommendations.append("Increase monthly savings by 5-10% of income")
                elif risk_factor == "High debt to income ratio":
                    recommendations.append("Focus on debt reduction strategies")
                elif risk_factor == "Insufficient emergency fund":
                    recommendations.append("Build emergency fund to cover 3-6 months of expenses")
                elif risk_factor == "High credit utilization":
                    recommendations.append("Reduce credit card balances to below 30% of limits")
                elif risk_factor == "Poor budget adherence":
                    recommendations.append("Review and adjust budget categories")
            
            # Generate general recommendations
            if not recommendations:
                recommendations.append("Maintain current financial habits")
                recommendations.append("Consider increasing investment contributions")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Review financial health with advisor"]
    
    def _get_goal_progress(self, user_id: str) -> Dict[str, float]:
        """Get goal progress for user"""
        try:
            user_goals = [goal for goal in self.financial_goals.values() if goal.user_id == user_id]
            
            goal_progress = {}
            for goal in user_goals:
                goal_progress[goal.goal_name] = goal.progress_percentage
            
            return goal_progress
            
        except Exception as e:
            self.logger.error(f"Error getting goal progress: {e}")
            return {}
    
    def _determine_trend_direction(self, user_id: str, current_score: float) -> str:
        """Determine trend direction based on historical scores"""
        try:
            user_scores = [score for score in self.health_scores.values() if score.user_id == user_id]
            
            if len(user_scores) < 2:
                return "stable"
            
            # Sort by date and get recent scores
            sorted_scores = sorted(user_scores, key=lambda x: x.score_date)
            recent_scores = sorted_scores[-3:]  # Last 3 scores
            
            if len(recent_scores) < 2:
                return "stable"
            
            # Calculate trend
            first_score = recent_scores[0].overall_score
            last_score = recent_scores[-1].overall_score
            
            if last_score > first_score + 5:
                return "improving"
            elif last_score < first_score - 5:
                return "declining"
            else:
                return "stable"
            
        except Exception as e:
            self.logger.error(f"Error determining trend direction: {e}")
            return "stable"
    
    def _calculate_confidence_level(self, metrics: Dict[str, float], banking_data: Dict[str, Any] = None) -> float:
        """Calculate confidence level of the health score"""
        try:
            # Base confidence on data completeness
            base_confidence = 0.8 if banking_data else 0.6
            
            # Adjust based on metric availability
            available_metrics = len([v for v in metrics.values() if v > 0])
            metric_confidence = min(1.0, available_metrics / len(FinancialHealthMetric))
            
            # Calculate final confidence
            confidence = (base_confidence + metric_confidence) / 2
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence level: {e}")
            return 0.5
    
    def create_financial_goal(self, user_id: str, goal_type: str, goal_name: str,
                            target_amount: float, target_date: datetime,
                            metadata: Dict[str, Any] = None) -> str:
        """Create a new financial goal"""
        try:
            goal_id = f"goal_{int(time.time())}_{secrets.token_hex(4)}"
            
            financial_goal = FinancialGoal(
                goal_id=goal_id,
                user_id=user_id,
                goal_type=goal_type,
                goal_name=goal_name,
                target_amount=target_amount,
                current_amount=0.0,
                target_date=target_date,
                created_date=datetime.utcnow(),
                status=GoalStatus.NOT_STARTED,
                progress_percentage=0.0,
                risk_level=RiskLevel.MEDIUM,
                metadata=metadata or {}
            )
            
            self.financial_goals[goal_id] = financial_goal
            
            # Log goal creation
            self.audit_service.log_event(
                event_type=AuditEventType.FINANCIAL_GOAL,
                event_category=LogCategory.ANALYTICS,
                severity=LogSeverity.INFO,
                description=f"Financial goal created for user {user_id}",
                resource_type="financial_goal",
                resource_id=goal_id,
                user_id=user_id,
                metadata={
                    'goal_type': goal_type,
                    'goal_name': goal_name,
                    'target_amount': target_amount
                }
            )
            
            return goal_id
            
        except Exception as e:
            self.logger.error(f"Error creating financial goal: {e}")
            raise
    
    def update_goal_progress(self, goal_id: str, current_amount: float) -> bool:
        """Update goal progress"""
        try:
            goal = self.financial_goals.get(goal_id)
            if not goal:
                return False
            
            # Update current amount and progress
            goal.current_amount = current_amount
            goal.progress_percentage = min(1.0, current_amount / goal.target_amount) if goal.target_amount > 0 else 0.0
            
            # Update status based on progress
            goal.status = self._determine_goal_status(goal.progress_percentage, goal.target_date)
            
            # Update risk level
            goal.risk_level = self._determine_goal_risk_level(goal)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress: {e}")
            return False
    
    def _determine_goal_status(self, progress_percentage: float, target_date: datetime) -> GoalStatus:
        """Determine goal status based on progress and target date"""
        try:
            current_date = datetime.utcnow()
            time_remaining = (target_date - current_date).days
            
            if progress_percentage >= 1.0:
                return GoalStatus.ACHIEVED
            elif progress_percentage >= 0.75:
                return GoalStatus.ON_TRACK
            elif progress_percentage >= 0.25:
                if time_remaining < 30:  # Less than 30 days remaining
                    return GoalStatus.AT_RISK
                else:
                    return GoalStatus.IN_PROGRESS
            else:
                if time_remaining < 0:  # Past target date
                    return GoalStatus.FAILED
                else:
                    return GoalStatus.NOT_STARTED
            
        except Exception as e:
            self.logger.error(f"Error determining goal status: {e}")
            return GoalStatus.IN_PROGRESS
    
    def _determine_goal_risk_level(self, goal: FinancialGoal) -> RiskLevel:
        """Determine goal risk level"""
        try:
            current_date = datetime.utcnow()
            time_remaining = (goal.target_date - current_date).days
            progress_needed = 1.0 - goal.progress_percentage
            
            if time_remaining <= 0:
                return RiskLevel.CRITICAL
            elif time_remaining < 30 and progress_needed > 0.5:
                return RiskLevel.HIGH
            elif time_remaining < 90 and progress_needed > 0.3:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW
            
        except Exception as e:
            self.logger.error(f"Error determining goal risk level: {e}")
            return RiskLevel.MEDIUM
    
    def identify_risk_factors(self, user_id: str) -> List[str]:
        """Identify risk factors for a user"""
        try:
            # Get latest health score
            user_scores = [score for score in self.health_scores.values() if score.user_id == user_id]
            if not user_scores:
                return []
            
            latest_score = max(user_scores, key=lambda x: x.score_date)
            return latest_score.risk_factors
            
        except Exception as e:
            self.logger.error(f"Error identifying risk factors: {e}")
            return []
    
    def track_progress(self, user_id: str, metric_name: str, current_value: float,
                      period_type: str = "monthly") -> str:
        """Track progress for a specific metric"""
        try:
            tracking_id = f"progress_{int(time.time())}_{secrets.token_hex(4)}"
            
            # Get previous value
            previous_tracking = [
                track for track in self.progress_tracking.values()
                if track.user_id == user_id and track.metric_name == metric_name
            ]
            
            previous_value = 0.0
            if previous_tracking:
                latest_tracking = max(previous_tracking, key=lambda x: x.tracking_date)
                previous_value = latest_tracking.current_value
            
            # Calculate change
            change_percentage = ((current_value - previous_value) / previous_value * 100) if previous_value > 0 else 0.0
            
            # Determine trend direction
            if change_percentage > 5:
                trend_direction = "improving"
            elif change_percentage < -5:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
            
            progress_tracking = ProgressTracking(
                tracking_id=tracking_id,
                user_id=user_id,
                metric_name=metric_name,
                current_value=current_value,
                previous_value=previous_value,
                change_percentage=change_percentage,
                tracking_date=datetime.utcnow(),
                period_type=period_type,
                trend_direction=trend_direction,
                metadata={'metric_type': 'financial_health'}
            )
            
            self.progress_tracking[tracking_id] = progress_tracking
            
            return tracking_id
            
        except Exception as e:
            self.logger.error(f"Error tracking progress: {e}")
            raise
    
    def get_financial_health_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive financial health dashboard data"""
        try:
            # Get latest health score
            user_scores = [score for score in self.health_scores.values() if score.user_id == user_id]
            latest_score = max(user_scores, key=lambda x: x.score_date) if user_scores else None
            
            # Get user goals
            user_goals = [goal for goal in self.financial_goals.values() if goal.user_id == user_id]
            
            # Get risk factors
            risk_factors = self.identify_risk_factors(user_id)
            
            # Get progress tracking
            user_progress = [track for track in self.progress_tracking.values() if track.user_id == user_id]
            
            # Calculate goal achievement rate
            total_goals = len(user_goals)
            achieved_goals = len([goal for goal in user_goals if goal.status == GoalStatus.ACHIEVED])
            goal_achievement_rate = achieved_goals / total_goals if total_goals > 0 else 0.0
            
            return {
                'current_health_score': latest_score.overall_score if latest_score else 0.0,
                'health_metrics': latest_score.metrics if latest_score else {},
                'risk_factors': risk_factors,
                'recommendations': latest_score.recommendations if latest_score else [],
                'goals': [
                    {
                        'goal_id': goal.goal_id,
                        'goal_name': goal.goal_name,
                        'goal_type': goal.goal_type,
                        'target_amount': goal.target_amount,
                        'current_amount': goal.current_amount,
                        'progress_percentage': goal.progress_percentage,
                        'status': goal.status.value,
                        'risk_level': goal.risk_level.value,
                        'target_date': goal.target_date.isoformat()
                    }
                    for goal in user_goals
                ],
                'goal_achievement_rate': goal_achievement_rate,
                'progress_tracking': [
                    {
                        'metric_name': track.metric_name,
                        'current_value': track.current_value,
                        'change_percentage': track.change_percentage,
                        'trend_direction': track.trend_direction,
                        'tracking_date': track.tracking_date.isoformat()
                    }
                    for track in user_progress[-10:]  # Last 10 progress entries
                ],
                'trend_direction': latest_score.trend_direction if latest_score else "stable",
                'confidence_level': latest_score.confidence_level if latest_score else 0.0,
                'last_updated': latest_score.score_date.isoformat() if latest_score else datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting financial health dashboard: {e}")
            return {"error": str(e)}
    
    def _update_health_scores(self):
        """Update health scores for all users"""
        try:
            # This would update health scores for all users
            # For now, we'll just log the update
            self.logger.info("Health scores update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating health scores: {e}")
    
    def _identify_risk_factors(self):
        """Identify risk factors for all users"""
        try:
            # This would identify risk factors for all users
            # For now, we'll just log the identification
            self.logger.info("Risk factor identification scheduled")
            
        except Exception as e:
            self.logger.error(f"Error identifying risk factors: {e}")
    
    def _update_goal_progress(self):
        """Update goal progress for all users"""
        try:
            # This would update goal progress for all users
            # For now, we'll just log the update
            self.logger.info("Goal progress update scheduled")
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress: {e}")
    
    def _calculate_success_correlations(self):
        """Calculate success metric correlations"""
        try:
            # This would calculate success metric correlations
            # For now, we'll just log the calculation
            self.logger.info("Success correlation calculation scheduled")
            
        except Exception as e:
            self.logger.error(f"Error calculating success correlations: {e}") 