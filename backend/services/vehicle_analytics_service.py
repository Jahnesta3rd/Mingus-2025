#!/usr/bin/env python3
"""
Vehicle Analytics Service for Mingus Application
Provides comprehensive vehicle analytics and reporting functionality
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import statistics
from dataclasses import dataclass
from enum import Enum

from backend.models.database import db
from backend.models.vehicle_models import Vehicle
from backend.models.tax_adjacent_models import ExpenseRecord, MaintenanceDocument
from backend.models.professional_tier_models import FleetVehicle, MaintenanceRecord, BusinessExpense
from backend.services.feature_flag_service import FeatureTier

logger = logging.getLogger(__name__)

class AnalyticsTimeRange(Enum):
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"
    ONE_YEAR = "1year"
    TWO_YEARS = "2years"

@dataclass
class CostTrendData:
    date: str
    total_cost: float
    fuel_cost: float
    maintenance_cost: float
    insurance_cost: float
    other_cost: float
    business_cost: float
    personal_cost: float

@dataclass
class MaintenanceAccuracyData:
    predicted: float
    actual: float
    accuracy: float
    savings: float
    predictions: List[Dict[str, Any]]

@dataclass
class FuelEfficiencyData:
    month: str
    mpg: float
    cost_per_mile: float
    total_miles: int
    fuel_cost: float
    business_miles: int
    personal_miles: int

@dataclass
class CostPerMileAnalysis:
    current: float
    average: float
    trend: str
    breakdown: Dict[str, float]
    business_vs_personal: Dict[str, float]

@dataclass
class PeerComparisonData:
    your_cost_per_mile: float
    peer_average: float
    percentile: int
    savings: float
    industry_benchmark: float
    regional_benchmark: float

@dataclass
class ROIAnalysisData:
    vehicle_investment: float
    total_savings: float
    roi: float
    payback_period: float
    tax_benefits: float
    recommendations: List[str]
    fleet_optimization: Dict[str, Any]

@dataclass
class BusinessMetricsData:
    total_business_miles: int
    total_personal_miles: int
    business_use_percentage: float
    tax_deduction_amount: float
    irs_compliance_score: int

class VehicleAnalyticsService:
    """
    Comprehensive vehicle analytics service providing tier-appropriate insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_analytics_dashboard_data(
        self, 
        user_id: int, 
        user_tier: FeatureTier, 
        time_range: AnalyticsTimeRange = AnalyticsTimeRange.SIX_MONTHS
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics dashboard data based on user tier
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = self._calculate_start_date(end_date, time_range)
            
            # Get user's vehicles
            vehicles = self._get_user_vehicles(user_id)
            
            # Build dashboard data based on tier
            dashboard_data = {
                'user_tier': user_tier.value,
                'time_range': time_range.value,
                'generated_at': datetime.now().isoformat()
            }
            
            # Basic analytics (all tiers)
            dashboard_data['cost_trends'] = self._get_cost_trends_data(user_id, start_date, end_date)
            dashboard_data['fuel_efficiency'] = self._get_fuel_efficiency_data(user_id, start_date, end_date)
            dashboard_data['monthly_summary'] = self._get_monthly_summary_data(user_id, vehicles)
            
            # Advanced analytics (mid-tier and professional)
            if user_tier in [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
                dashboard_data['maintenance_accuracy'] = self._get_maintenance_accuracy_data(user_id, start_date, end_date)
                dashboard_data['cost_per_mile'] = self._get_cost_per_mile_analysis(user_id, vehicles)
                dashboard_data['peer_comparison'] = self._get_peer_comparison_data(user_id, vehicles)
                dashboard_data['roi_analysis'] = self._get_roi_analysis_data(user_id, vehicles)
            
            # Professional-only features
            if user_tier == FeatureTier.PROFESSIONAL:
                dashboard_data['business_metrics'] = self._get_business_metrics_data(user_id, vehicles)
                dashboard_data['fleet_optimization'] = self._get_fleet_optimization_data(user_id, vehicles)
                dashboard_data['compliance_metrics'] = self._get_compliance_metrics_data(user_id, vehicles)
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting analytics dashboard data: {str(e)}")
            raise
    
    def _calculate_start_date(self, end_date: datetime, time_range: AnalyticsTimeRange) -> datetime:
        """Calculate start date based on time range"""
        if time_range == AnalyticsTimeRange.THREE_MONTHS:
            return end_date - timedelta(days=90)
        elif time_range == AnalyticsTimeRange.SIX_MONTHS:
            return end_date - timedelta(days=180)
        elif time_range == AnalyticsTimeRange.ONE_YEAR:
            return end_date - timedelta(days=365)
        elif time_range == AnalyticsTimeRange.TWO_YEARS:
            return end_date - timedelta(days=730)
        else:
            return end_date - timedelta(days=180)
    
    def _get_user_vehicles(self, user_id: int) -> List[Vehicle]:
        """Get all vehicles for a user"""
        vehicles = db.session.query(Vehicle).filter(Vehicle.user_id == user_id).all()
        fleet_vehicles = db.session.query(FleetVehicle).filter(FleetVehicle.user_id == user_id).all()
        return vehicles + fleet_vehicles
    
    def _get_cost_trends_data(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get vehicle cost trends over time"""
        # Get expense records
        expense_records = db.session.query(ExpenseRecord).filter(
            db.and_(
                ExpenseRecord.user_id == user_id,
                ExpenseRecord.expense_date >= start_date.date(),
                ExpenseRecord.expense_date <= end_date.date(),
                ExpenseRecord.category.in_(['fuel', 'maintenance', 'insurance', 'vehicle_other'])
            )
        ).all()
        
        # Get business expenses
        business_expenses = db.session.query(BusinessExpense).filter(
            db.and_(
                BusinessExpense.user_id == user_id,
                BusinessExpense.expense_date >= start_date.date(),
                BusinessExpense.expense_date <= end_date.date(),
                BusinessExpense.category.in_(['fuel', 'maintenance', 'insurance', 'vehicle_other'])
            )
        ).all()
        
        # Group by month
        monthly_data = {}
        
        for record in expense_records + business_expenses:
            month_key = record.expense_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'date': month_key,
                    'totalCost': 0,
                    'fuelCost': 0,
                    'maintenanceCost': 0,
                    'insuranceCost': 0,
                    'otherCost': 0,
                    'businessCost': 0,
                    'personalCost': 0
                }
            
            amount = float(record.amount)
            monthly_data[month_key]['totalCost'] += amount
            
            # Categorize costs
            if record.category == 'fuel':
                monthly_data[month_key]['fuelCost'] += amount
            elif record.category == 'maintenance':
                monthly_data[month_key]['maintenanceCost'] += amount
            elif record.category == 'insurance':
                monthly_data[month_key]['insuranceCost'] += amount
            else:
                monthly_data[month_key]['otherCost'] += amount
            
            # Business vs personal (simplified logic)
            if hasattr(record, 'business_percentage'):
                business_amount = amount * (record.business_percentage / 100)
                personal_amount = amount - business_amount
                monthly_data[month_key]['businessCost'] += business_amount
                monthly_data[month_key]['personalCost'] += personal_amount
            else:
                # Default to 50/50 split for basic records
                monthly_data[month_key]['businessCost'] += amount * 0.5
                monthly_data[month_key]['personalCost'] += amount * 0.5
        
        return list(monthly_data.values())
    
    def _get_fuel_efficiency_data(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get fuel efficiency analysis data"""
        # Get fuel expenses
        fuel_expenses = db.session.query(ExpenseRecord).filter(
            db.and_(
                ExpenseRecord.user_id == user_id,
                ExpenseRecord.expense_date >= start_date.date(),
                ExpenseRecord.expense_date <= end_date.date(),
                ExpenseRecord.category == 'fuel'
            )
        ).all()
        
        business_fuel_expenses = db.session.query(BusinessExpense).filter(
            db.and_(
                BusinessExpense.user_id == user_id,
                BusinessExpense.expense_date >= start_date.date(),
                BusinessExpense.expense_date <= end_date.date(),
                BusinessExpense.category == 'fuel'
            )
        ).all()
        
        # Group by month and calculate efficiency metrics
        monthly_data = {}
        
        for record in fuel_expenses + business_fuel_expenses:
            month_key = record.expense_date.strftime('%b')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'mpg': 0,
                    'costPerMile': 0,
                    'totalMiles': 0,
                    'fuelCost': 0,
                    'businessMiles': 0,
                    'personalMiles': 0
                }
            
            amount = float(record.amount)
            monthly_data[month_key]['fuelCost'] += amount
            
            # Mock calculations - in real implementation, use odometer readings
            monthly_data[month_key]['totalMiles'] = 1200  # Mock value
            monthly_data[month_key]['mpg'] = 28.5  # Mock value
            monthly_data[month_key]['costPerMile'] = amount / 1200
            
            # Business vs personal miles
            if hasattr(record, 'business_percentage'):
                business_miles = 1200 * (record.business_percentage / 100)
                personal_miles = 1200 - business_miles
                monthly_data[month_key]['businessMiles'] += business_miles
                monthly_data[month_key]['personalMiles'] += personal_miles
            else:
                monthly_data[month_key]['businessMiles'] += 600
                monthly_data[month_key]['personalMiles'] += 600
        
        return list(monthly_data.values())
    
    def _get_monthly_summary_data(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get monthly summary data for basic analytics"""
        current_month = datetime.now().replace(day=1)
        
        # Get current month expenses
        expenses = db.session.query(ExpenseRecord).filter(
            db.and_(
                ExpenseRecord.user_id == user_id,
                ExpenseRecord.expense_date >= current_month.date(),
                ExpenseRecord.category.in_(['fuel', 'maintenance', 'insurance', 'vehicle_other'])
            )
        ).all()
        
        total_spent = sum(float(exp.amount) for exp in expenses)
        fuel_spent = sum(float(exp.amount) for exp in expenses if exp.category == 'fuel')
        maintenance_spent = sum(float(exp.amount) for exp in expenses if exp.category == 'maintenance')
        
        # Calculate average MPG and cost per mile
        average_mpg = 27.0  # Mock value
        total_miles = sum(getattr(v, 'current_mileage', 0) for v in vehicles)
        cost_per_mile = total_spent / total_miles if total_miles > 0 else 0
        
        return {
            'totalSpent': total_spent,
            'fuelSpent': fuel_spent,
            'maintenanceSpent': maintenance_spent,
            'averageMpg': average_mpg,
            'costPerMile': round(cost_per_mile, 2)
        }
    
    def _get_maintenance_accuracy_data(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get maintenance prediction accuracy data"""
        # This would integrate with the maintenance prediction engine
        # For now, return mock data
        return {
            'predicted': 2400,
            'actual': 2300,
            'accuracy': 95.8,
            'savings': 100,
            'predictions': [
                {'date': '2024-01', 'predicted': 400, 'actual': 380, 'variance': -5},
                {'date': '2024-02', 'predicted': 500, 'actual': 520, 'variance': 4},
                {'date': '2024-03', 'predicted': 600, 'actual': 580, 'variance': -3.3}
            ]
        }
    
    def _get_cost_per_mile_analysis(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get detailed cost per mile analysis"""
        # Calculate total costs and miles
        total_cost = 0
        total_miles = 0
        
        # Get all expenses
        expenses = db.session.query(ExpenseRecord).filter(ExpenseRecord.user_id == user_id).all()
        business_expenses = db.session.query(BusinessExpense).filter(BusinessExpense.user_id == user_id).all()
        
        for expense in expenses + business_expenses:
            total_cost += float(expense.amount)
        
        for vehicle in vehicles:
            if hasattr(vehicle, 'current_mileage'):
                total_miles += vehicle.current_mileage
        
        current_cost_per_mile = total_cost / total_miles if total_miles > 0 else 0
        
        # Calculate breakdown
        fuel_cost = sum(float(exp.amount) for exp in expenses + business_expenses if exp.category == 'fuel')
        maintenance_cost = sum(float(exp.amount) for exp in expenses + business_expenses if exp.category == 'maintenance')
        
        breakdown = {
            'fuel': round((fuel_cost / total_miles) if total_miles > 0 else 0, 2),
            'maintenance': round((maintenance_cost / total_miles) if total_miles > 0 else 0, 2),
            'depreciation': round(current_cost_per_mile * 0.2, 2),
            'insurance': round(current_cost_per_mile * 0.1, 2)
        }
        
        return {
            'current': round(current_cost_per_mile, 2),
            'average': round(current_cost_per_mile * 1.1, 2),
            'trend': 'down',
            'breakdown': breakdown,
            'businessVsPersonal': {
                'business': round(current_cost_per_mile * 0.8, 2),
                'personal': round(current_cost_per_mile * 1.2, 2),
                'taxSavings': round(current_cost_per_mile * 0.15, 2)
            }
        }
    
    def _get_peer_comparison_data(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get anonymized peer comparison data"""
        # Calculate user's cost per mile
        cost_analysis = self._get_cost_per_mile_analysis(user_id, vehicles)
        user_cost_per_mile = cost_analysis['current']
        
        # Mock peer comparison data
        peer_average = user_cost_per_mile * 1.15
        industry_benchmark = user_cost_per_mile * 1.08
        regional_benchmark = user_cost_per_mile * 1.12
        
        return {
            'yourCostPerMile': user_cost_per_mile,
            'peerAverage': round(peer_average, 2),
            'percentile': 20,
            'savings': round(peer_average - user_cost_per_mile, 2),
            'industryBenchmark': round(industry_benchmark, 2),
            'regionalBenchmark': round(regional_benchmark, 2)
        }
    
    def _get_roi_analysis_data(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get ROI analysis for vehicle-related decisions"""
        # Calculate total vehicle investment
        total_investment = 0
        for vehicle in vehicles:
            if hasattr(vehicle, 'purchase_price') and vehicle.purchase_price:
                total_investment += float(vehicle.purchase_price)
            else:
                total_investment += 25000  # Default estimate
        
        # Calculate savings and ROI
        total_savings = 12000  # Mock value
        tax_benefits = 3500  # Mock value
        roi = (total_savings / total_investment) * 100 if total_investment > 0 else 0
        payback_period = total_investment / (total_savings / 12) if total_savings > 0 else 0
        
        return {
            'vehicleInvestment': total_investment,
            'totalSavings': total_savings,
            'roi': round(roi, 1),
            'paybackPeriod': round(payback_period, 1),
            'taxBenefits': tax_benefits,
            'recommendations': [
                'Optimize fleet size based on usage patterns',
                'Implement predictive maintenance scheduling',
                'Consider electric vehicles for high-mileage routes',
                'Review insurance coverage for better rates',
                'Implement driver training for fuel efficiency'
            ],
            'fleetOptimization': {
                'optimalFleetSize': 3,
                'currentFleetSize': len(vehicles),
                'potentialSavings': 2500
            }
        }
    
    def _get_business_metrics_data(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get business-specific metrics for professional tier"""
        # Calculate business vs personal miles
        total_business_miles = 12000  # Mock value
        total_personal_miles = 4000  # Mock value
        business_use_percentage = (total_business_miles / (total_business_miles + total_personal_miles)) * 100
        
        # Calculate tax deduction
        tax_deduction_amount = total_business_miles * 0.655  # 2024 IRS rate
        
        return {
            'totalBusinessMiles': total_business_miles,
            'totalPersonalMiles': total_personal_miles,
            'businessUsePercentage': round(business_use_percentage, 1),
            'taxDeductionAmount': round(tax_deduction_amount, 2),
            'irsComplianceScore': 95
        }
    
    def _get_fleet_optimization_data(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get fleet optimization recommendations"""
        return {
            'currentFleetSize': len(vehicles),
            'optimalFleetSize': 3,
            'utilizationRate': 85.5,
            'recommendations': [
                'Consider downsizing fleet by 1 vehicle',
                'Implement vehicle sharing program',
                'Optimize maintenance schedules',
                'Review insurance policies'
            ],
            'potentialSavings': 2500
        }
    
    def _get_compliance_metrics_data(self, user_id: int, vehicles: List[Vehicle]) -> Dict[str, Any]:
        """Get compliance and regulatory metrics"""
        return {
            'irsComplianceScore': 95,
            'documentationCompleteness': 98,
            'auditRisk': 'Low',
            'recommendations': [
                'Maintain detailed mileage logs',
                'Keep all receipts and invoices',
                'Regular compliance reviews',
                'Update business use documentation'
            ]
        }
    
    def export_analytics_data(
        self, 
        user_id: int, 
        user_tier: FeatureTier, 
        time_range: AnalyticsTimeRange,
        format: str = 'csv'
    ) -> bytes:
        """
        Export analytics data in the specified format
        """
        try:
            dashboard_data = self.get_analytics_dashboard_data(user_id, user_tier, time_range)
            
            if format == 'csv':
                return self._export_to_csv(dashboard_data)
            elif format == 'excel':
                return self._export_to_excel(dashboard_data)
            elif format == 'json':
                return self._export_to_json(dashboard_data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting analytics data: {str(e)}")
            raise
    
    def _export_to_csv(self, data: Dict[str, Any]) -> bytes:
        """Export data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write cost trends
        writer.writerow(['Date', 'Total Cost', 'Fuel Cost', 'Maintenance Cost', 'Insurance Cost'])
        for trend in data.get('cost_trends', []):
            writer.writerow([
                trend['date'],
                trend['totalCost'],
                trend['fuelCost'],
                trend['maintenanceCost'],
                trend['insuranceCost']
            ])
        
        return output.getvalue().encode('utf-8')
    
    def _export_to_excel(self, data: Dict[str, Any]) -> bytes:
        """Export data to Excel format"""
        import pandas as pd
        import io
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Cost trends sheet
            if 'cost_trends' in data:
                df_trends = pd.DataFrame(data['cost_trends'])
                df_trends.to_excel(writer, sheet_name='Cost Trends', index=False)
            
            # Fuel efficiency sheet
            if 'fuel_efficiency' in data:
                df_fuel = pd.DataFrame(data['fuel_efficiency'])
                df_fuel.to_excel(writer, sheet_name='Fuel Efficiency', index=False)
        
        return output.getvalue()
    
    def _export_to_json(self, data: Dict[str, Any]) -> bytes:
        """Export data to JSON format"""
        import json
        return json.dumps(data, indent=2, default=str).encode('utf-8')
