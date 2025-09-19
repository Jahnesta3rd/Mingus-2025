#!/usr/bin/env python3
"""
Enhanced Spending Analyzer for Mingus Personal Finance App
Integrates vehicle expenses with existing spending analysis

Features:
- Combines traditional expenses with vehicle-specific expenses
- Provides comprehensive spending insights
- Integrates with existing profile system
- Generates personalized recommendations
- Tracks spending patterns and trends
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import math

# Import the vehicle expense categorizer
from backend.services.vehicle_expense_categorizer import VehicleExpenseCategorizer

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SpendingCategory:
    """Data class for spending category analysis"""
    name: str
    total_amount: float
    count: int
    average_amount: float
    percentage_of_total: float
    monthly_average: float
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    is_vehicle_related: bool
    subcategories: List[Dict[str, Any]]

@dataclass
class SpendingInsight:
    """Data class for spending insights"""
    insight_type: str
    title: str
    description: str
    impact_level: str  # 'high', 'medium', 'low'
    recommendation: str
    potential_savings: float
    category: str

@dataclass
class MonthlySpendingBreakdown:
    """Data class for monthly spending breakdown"""
    month: str
    total_spending: float
    vehicle_spending: float
    traditional_spending: float
    categories: Dict[str, float]
    vehicle_categories: Dict[str, float]

class EnhancedSpendingAnalyzer:
    """
    Enhanced spending analyzer that integrates vehicle expenses with traditional spending analysis
    
    This analyzer provides comprehensive insights by combining:
    - Traditional expense categories from user profiles
    - Vehicle-specific expense categories
    - Maintenance prediction comparisons
    - Spending pattern analysis
    - Personalized recommendations
    """
    
    def __init__(self, profile_db_path: str = "user_profiles.db", 
                 vehicle_db_path: str = "backend/mingus_vehicles.db"):
        """Initialize the enhanced spending analyzer"""
        self.profile_db_path = profile_db_path
        self.vehicle_db_path = vehicle_db_path
        self.vehicle_categorizer = VehicleExpenseCategorizer(vehicle_db_path, profile_db_path)
        
        # Traditional expense categories from the profile system
        self.traditional_categories = {
            'rent': 'Housing',
            'carPayment': 'Car Payment',
            'insurance': 'Insurance',
            'groceries': 'Groceries',
            'utilities': 'Utilities',
            'studentLoanPayment': 'Student Loan Payment',
            'creditCardMinimum': 'Credit Card Payment'
        }
        
        # Vehicle expense categories
        self.vehicle_categories = {
            'maintenance': 'Vehicle Maintenance',
            'fuel': 'Fuel',
            'parking': 'Parking',
            'registration': 'Registration',
            'repairs': 'Vehicle Repairs',
            'tires': 'Tires',
            'towing': 'Towing',
            'emergency': 'Vehicle Emergency'
        }
    
    def get_comprehensive_spending_analysis(self, user_email: str, months: int = 12) -> Dict[str, Any]:
        """
        Get comprehensive spending analysis including vehicle expenses
        
        Args:
            user_email: User's email address
            months: Number of months to analyze
            
        Returns:
            Dictionary with comprehensive spending analysis
        """
        try:
            # Get traditional spending data from profile
            traditional_spending = self._get_traditional_spending(user_email)
            
            # Get vehicle spending data
            vehicle_spending = self.vehicle_categorizer.get_vehicle_expense_summary(user_email, months)
            
            # Combine and analyze data
            combined_analysis = self._combine_spending_data(traditional_spending, vehicle_spending, months)
            
            # Generate insights
            insights = self._generate_spending_insights(combined_analysis, user_email)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(combined_analysis, user_email)
            
            return {
                'summary': combined_analysis['summary'],
                'categories': combined_analysis['categories'],
                'monthly_breakdown': combined_analysis['monthly_breakdown'],
                'insights': insights,
                'recommendations': recommendations,
                'vehicle_analysis': vehicle_spending,
                'traditional_analysis': traditional_spending
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive spending analysis: {e}")
            return {}
    
    def _get_traditional_spending(self, user_email: str) -> Dict[str, Any]:
        """Get traditional spending data from user profile"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT monthly_expenses, financial_info
                FROM user_profiles 
                WHERE email = ?
            ''', (user_email,))
            
            profile = cursor.fetchone()
            conn.close()
            
            if not profile:
                return {}
            
            monthly_expenses = json.loads(profile['monthly_expenses'] or '{}')
            financial_info = json.loads(profile['financial_info'] or '{}')
            
            # Calculate total monthly expenses
            total_monthly = sum(monthly_expenses.values())
            
            # Calculate annual expenses
            annual_expenses = {}
            for category, amount in monthly_expenses.items():
                annual_expenses[category] = amount * 12
            
            return {
                'monthly_expenses': monthly_expenses,
                'annual_expenses': annual_expenses,
                'total_monthly': total_monthly,
                'total_annual': total_monthly * 12,
                'monthly_income': financial_info.get('monthlyTakehome', 0),
                'annual_income': financial_info.get('annualIncome', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting traditional spending: {e}")
            return {}
    
    def _combine_spending_data(self, traditional: Dict[str, Any], vehicle: Dict[str, Any], 
                              months: int) -> Dict[str, Any]:
        """Combine traditional and vehicle spending data"""
        try:
            # Get traditional monthly expenses
            traditional_monthly = traditional.get('monthly_expenses', {})
            traditional_total = traditional.get('total_monthly', 0)
            
            # Get vehicle expenses
            vehicle_summary = vehicle.get('summary', {})
            vehicle_total = vehicle_summary.get('total_expenses', 0)
            vehicle_monthly = vehicle_total / months if months > 0 else 0
            
            # Calculate combined totals
            combined_monthly = traditional_total + vehicle_monthly
            combined_annual = combined_monthly * 12
            
            # Create combined categories
            combined_categories = {}
            
            # Add traditional categories
            for key, label in self.traditional_categories.items():
                amount = traditional_monthly.get(key, 0)
                if amount > 0:
                    combined_categories[label] = {
                        'amount': amount,
                        'type': 'traditional',
                        'percentage': (amount / combined_monthly * 100) if combined_monthly > 0 else 0
                    }
            
            # Add vehicle categories
            vehicle_by_type = vehicle.get('expenses_by_type', {})
            for key, label in self.vehicle_categories.items():
                if key in vehicle_by_type:
                    data = vehicle_by_type[key]
                    amount = data.get('total', 0) / months if months > 0 else 0
                    if amount > 0:
                        combined_categories[label] = {
                            'amount': amount,
                            'type': 'vehicle',
                            'percentage': (amount / combined_monthly * 100) if combined_monthly > 0 else 0
                        }
            
            # Generate monthly breakdown (simplified)
            monthly_breakdown = []
            for i in range(months):
                month_date = datetime.now() - timedelta(days=30 * i)
                month_key = month_date.strftime('%Y-%m')
                
                # This would be more sophisticated in a real implementation
                monthly_breakdown.append({
                    'month': month_key,
                    'traditional_spending': traditional_total,
                    'vehicle_spending': vehicle_monthly,
                    'total_spending': combined_monthly
                })
            
            return {
                'summary': {
                    'total_monthly': combined_monthly,
                    'total_annual': combined_annual,
                    'traditional_monthly': traditional_total,
                    'vehicle_monthly': vehicle_monthly,
                    'vehicle_percentage': (vehicle_monthly / combined_monthly * 100) if combined_monthly > 0 else 0
                },
                'categories': combined_categories,
                'monthly_breakdown': monthly_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error combining spending data: {e}")
            return {}
    
    def _generate_spending_insights(self, analysis: Dict[str, Any], user_email: str) -> List[SpendingInsight]:
        """Generate spending insights from combined analysis"""
        try:
            insights = []
            summary = analysis.get('summary', {})
            categories = analysis.get('categories', {})
            
            total_monthly = summary.get('total_monthly', 0)
            vehicle_monthly = summary.get('vehicle_monthly', 0)
            vehicle_percentage = summary.get('vehicle_percentage', 0)
            
            # Insight 1: Vehicle spending percentage
            if vehicle_percentage > 25:
                insights.append(SpendingInsight(
                    insight_type='vehicle_spending',
                    title='High Vehicle Spending',
                    description=f'Vehicle expenses represent {vehicle_percentage:.1f}% of your total monthly spending',
                    impact_level='high' if vehicle_percentage > 40 else 'medium',
                    recommendation='Consider ways to reduce vehicle costs through maintenance planning and fuel efficiency',
                    potential_savings=vehicle_monthly * 0.15,
                    category='vehicle'
                ))
            
            # Insight 2: Maintenance vs other vehicle costs
            maintenance_amount = categories.get('Vehicle Maintenance', {}).get('amount', 0)
            fuel_amount = categories.get('Fuel', {}).get('amount', 0)
            
            if maintenance_amount > 0 and fuel_amount > 0:
                maintenance_ratio = maintenance_amount / fuel_amount
                if maintenance_ratio > 2:
                    insights.append(SpendingInsight(
                        insight_type='maintenance_ratio',
                        title='High Maintenance Costs',
                        description=f'Maintenance costs are {maintenance_ratio:.1f}x higher than fuel costs',
                        impact_level='high',
                        recommendation='Consider preventive maintenance to reduce unexpected repair costs',
                        potential_savings=maintenance_amount * 0.2,
                        category='maintenance'
                    ))
            
            # Insight 3: Insurance optimization
            insurance_amount = categories.get('Insurance', {}).get('amount', 0)
            if insurance_amount > 0 and insurance_amount > total_monthly * 0.15:
                insights.append(SpendingInsight(
                    insight_type='insurance_optimization',
                    title='Insurance Cost Optimization',
                    description=f'Insurance represents {insurance_amount/total_monthly*100:.1f}% of monthly spending',
                    impact_level='medium',
                    recommendation='Shop around for better insurance rates or consider adjusting coverage',
                    potential_savings=insurance_amount * 0.1,
                    category='insurance'
                ))
            
            # Insight 4: Fuel efficiency
            if fuel_amount > 0 and fuel_amount > total_monthly * 0.2:
                insights.append(SpendingInsight(
                    insight_type='fuel_efficiency',
                    title='High Fuel Costs',
                    description=f'Fuel costs represent {fuel_amount/total_monthly*100:.1f}% of monthly spending',
                    impact_level='medium',
                    recommendation='Consider fuel-efficient driving habits or alternative transportation',
                    potential_savings=fuel_amount * 0.1,
                    category='fuel'
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating spending insights: {e}")
            return []
    
    def _generate_recommendations(self, analysis: Dict[str, Any], user_email: str) -> List[Dict[str, Any]]:
        """Generate personalized recommendations based on spending analysis"""
        try:
            recommendations = []
            summary = analysis.get('summary', {})
            categories = analysis.get('categories', {})
            
            total_monthly = summary.get('total_monthly', 0)
            vehicle_monthly = summary.get('vehicle_monthly', 0)
            
            # Recommendation 1: Vehicle maintenance planning
            maintenance_amount = categories.get('Vehicle Maintenance', {}).get('amount', 0)
            if maintenance_amount > 0:
                recommendations.append({
                    'category': 'maintenance',
                    'priority': 'high',
                    'title': 'Implement Preventive Maintenance Schedule',
                    'description': 'Schedule regular maintenance to prevent costly repairs',
                    'potential_savings': maintenance_amount * 0.2,
                    'action_items': [
                        'Set up maintenance reminders',
                        'Track service history',
                        'Compare repair costs across providers'
                    ]
                })
            
            # Recommendation 2: Fuel cost optimization
            fuel_amount = categories.get('Fuel', {}).get('amount', 0)
            if fuel_amount > 0:
                recommendations.append({
                    'category': 'fuel',
                    'priority': 'medium',
                    'title': 'Optimize Fuel Costs',
                    'description': 'Reduce fuel expenses through efficient driving and planning',
                    'potential_savings': fuel_amount * 0.15,
                    'action_items': [
                        'Use fuel price comparison apps',
                        'Plan efficient routes',
                        'Consider carpooling or public transportation'
                    ]
                })
            
            # Recommendation 3: Insurance shopping
            insurance_amount = categories.get('Insurance', {}).get('amount', 0)
            if insurance_amount > 0:
                recommendations.append({
                    'category': 'insurance',
                    'priority': 'medium',
                    'title': 'Review Insurance Coverage',
                    'description': 'Compare insurance rates and optimize coverage',
                    'potential_savings': insurance_amount * 0.1,
                    'action_items': [
                        'Get quotes from multiple providers',
                        'Review coverage levels',
                        'Consider bundling policies'
                    ]
                })
            
            # Recommendation 4: Overall vehicle cost management
            if vehicle_monthly > total_monthly * 0.3:  # More than 30% of spending
                recommendations.append({
                    'category': 'overall',
                    'priority': 'high',
                    'title': 'Comprehensive Vehicle Cost Management',
                    'description': 'Implement a comprehensive approach to managing vehicle costs',
                    'potential_savings': vehicle_monthly * 0.1,
                    'action_items': [
                        'Create a vehicle expense budget',
                        'Track all vehicle-related expenses',
                        'Set up alerts for unusual spending',
                        'Regularly review and optimize costs'
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def get_spending_trends(self, user_email: str, months: int = 12) -> Dict[str, Any]:
        """
        Analyze spending trends over time
        
        Args:
            user_email: User's email address
            months: Number of months to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            # This would be more sophisticated in a real implementation
            # For now, return a simplified trend analysis
            
            traditional = self._get_traditional_spending(user_email)
            vehicle = self.vehicle_categorizer.get_vehicle_expense_summary(user_email, months)
            
            traditional_monthly = traditional.get('total_monthly', 0)
            vehicle_monthly = vehicle.get('summary', {}).get('average_monthly', 0)
            
            return {
                'traditional_trend': {
                    'direction': 'stable',  # Would calculate from actual data
                    'monthly_average': traditional_monthly,
                    'variance': 0.0
                },
                'vehicle_trend': {
                    'direction': 'stable',  # Would calculate from actual data
                    'monthly_average': vehicle_monthly,
                    'variance': 0.0
                },
                'combined_trend': {
                    'direction': 'stable',
                    'monthly_average': traditional_monthly + vehicle_monthly,
                    'variance': 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending trends: {e}")
            return {}
    
    def get_budget_impact_analysis(self, user_email: str) -> Dict[str, Any]:
        """
        Analyze the impact of vehicle expenses on overall budget
        
        Args:
            user_email: User's email address
            
        Returns:
            Dictionary with budget impact analysis
        """
        try:
            traditional = self._get_traditional_spending(user_email)
            vehicle = self.vehicle_categorizer.get_vehicle_expense_summary(user_email, 12)
            
            monthly_income = traditional.get('monthly_income', 0)
            traditional_monthly = traditional.get('total_monthly', 0)
            vehicle_monthly = vehicle.get('summary', {}).get('average_monthly', 0)
            
            total_monthly = traditional_monthly + vehicle_monthly
            
            # Calculate budget percentages
            traditional_percentage = (traditional_monthly / monthly_income * 100) if monthly_income > 0 else 0
            vehicle_percentage = (vehicle_monthly / monthly_income * 100) if monthly_income > 0 else 0
            total_percentage = (total_monthly / monthly_income * 100) if monthly_income > 0 else 0
            
            # Calculate disposable income
            disposable_income = monthly_income - total_monthly
            
            return {
                'monthly_income': monthly_income,
                'total_expenses': total_monthly,
                'disposable_income': disposable_income,
                'expense_breakdown': {
                    'traditional': {
                        'amount': traditional_monthly,
                        'percentage_of_income': traditional_percentage
                    },
                    'vehicle': {
                        'amount': vehicle_monthly,
                        'percentage_of_income': vehicle_percentage
                    }
                },
                'budget_health': {
                    'total_percentage': total_percentage,
                    'status': 'healthy' if total_percentage < 80 else 'needs_attention',
                    'recommendation': self._get_budget_recommendation(total_percentage)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing budget impact: {e}")
            return {}
    
    def _get_budget_recommendation(self, total_percentage: float) -> str:
        """Get budget recommendation based on expense percentage"""
        if total_percentage < 50:
            return "Excellent budget management! You have significant disposable income."
        elif total_percentage < 70:
            return "Good budget management. Consider increasing savings or investments."
        elif total_percentage < 80:
            return "Budget is tight. Look for ways to reduce expenses or increase income."
        else:
            return "Budget needs immediate attention. Consider significant expense reduction or income increase."
