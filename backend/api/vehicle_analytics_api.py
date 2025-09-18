#!/usr/bin/env python3
"""
Vehicle Analytics API for Mingus Application
Provides comprehensive vehicle analytics and reporting endpoints
"""

import logging
from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
from backend.models.database import db
from backend.auth.decorators import require_auth, get_current_user_id
from backend.utils.validation import APIValidator
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from datetime import datetime, timedelta
from decimal import Decimal
import json
import csv
import io
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import func, and_, or_

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
vehicle_analytics_api = Blueprint('vehicle_analytics', __name__, url_prefix='/api/vehicle-analytics')

# Initialize services
validator = APIValidator()
feature_service = FeatureFlagService()

# ============================================================================
# VEHICLE ANALYTICS ENDPOINTS
# ============================================================================

@vehicle_analytics_api.route('/dashboard', methods=['GET'])
@require_auth
@cross_origin()
def get_vehicle_analytics_dashboard():
    """
    Get comprehensive vehicle analytics dashboard data
    """
    try:
        user_id = get_current_user_id()
        user_tier = feature_service.get_user_tier(user_id)
        
        # Get time range parameter
        time_range = request.args.get('time_range', '6months')
        
        # Calculate date range
        end_date = datetime.now()
        if time_range == '3months':
            start_date = end_date - timedelta(days=90)
        elif time_range == '6months':
            start_date = end_date - timedelta(days=180)
        elif time_range == '1year':
            start_date = end_date - timedelta(days=365)
        elif time_range == '2years':
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=180)
        
        # Get user's vehicles
        from backend.models.vehicle_models import Vehicle
        from backend.models.tax_adjacent_models import ExpenseRecord, MaintenanceDocument
        from backend.models.professional_tier_models import FleetVehicle, MaintenanceRecord, BusinessExpense
        
        vehicles = db.session.query(Vehicle).filter(Vehicle.user_id == user_id).all()
        fleet_vehicles = db.session.query(FleetVehicle).filter(FleetVehicle.user_id == user_id).all()
        
        # Get cost trends data
        cost_trends = _get_cost_trends_data(user_id, start_date, end_date)
        
        # Get maintenance prediction accuracy
        maintenance_accuracy = _get_maintenance_accuracy_data(user_id, start_date, end_date)
        
        # Get fuel efficiency data
        fuel_efficiency = _get_fuel_efficiency_data(user_id, start_date, end_date)
        
        # Get cost per mile analysis
        cost_per_mile = _get_cost_per_mile_analysis(user_id, vehicles + fleet_vehicles)
        
        # Get peer comparison (only for certain tiers)
        peer_comparison = None
        if user_tier in [FeatureTier.BUDGET_CAREER_VEHICLE, FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
            peer_comparison = _get_peer_comparison_data(user_id, cost_per_mile['current'])
        
        # Get ROI analysis (only for mid-tier and professional)
        roi_analysis = None
        if user_tier in [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
            roi_analysis = _get_roi_analysis_data(user_id, vehicles + fleet_vehicles)
        
        dashboard_data = {
            'cost_trends': cost_trends,
            'maintenance_accuracy': maintenance_accuracy,
            'fuel_efficiency': fuel_efficiency,
            'cost_per_mile': cost_per_mile,
            'peer_comparison': peer_comparison,
            'roi_analysis': roi_analysis,
            'user_tier': user_tier.value,
            'time_range': time_range
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting vehicle analytics dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load vehicle analytics data'
        }), 500

@vehicle_analytics_api.route('/cost-trends', methods=['GET'])
@require_auth
@cross_origin()
def get_cost_trends():
    """
    Get vehicle cost trends over time
    """
    try:
        user_id = get_current_user_id()
        time_range = request.args.get('time_range', '6months')
        
        # Calculate date range
        end_date = datetime.now()
        if time_range == '3months':
            start_date = end_date - timedelta(days=90)
        elif time_range == '6months':
            start_date = end_date - timedelta(days=180)
        elif time_range == '1year':
            start_date = end_date - timedelta(days=365)
        elif time_range == '2years':
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=180)
        
        cost_trends = _get_cost_trends_data(user_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': cost_trends
        })
        
    except Exception as e:
        logger.error(f"Error getting cost trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load cost trends data'
        }), 500

@vehicle_analytics_api.route('/maintenance-accuracy', methods=['GET'])
@require_auth
@cross_origin()
def get_maintenance_accuracy():
    """
    Get maintenance prediction accuracy data
    """
    try:
        user_id = get_current_user_id()
        time_range = request.args.get('time_range', '6months')
        
        # Calculate date range
        end_date = datetime.now()
        if time_range == '3months':
            start_date = end_date - timedelta(days=90)
        elif time_range == '6months':
            start_date = end_date - timedelta(days=180)
        elif time_range == '1year':
            start_date = end_date - timedelta(days=365)
        elif time_range == '2years':
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=180)
        
        maintenance_accuracy = _get_maintenance_accuracy_data(user_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': maintenance_accuracy
        })
        
    except Exception as e:
        logger.error(f"Error getting maintenance accuracy: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load maintenance accuracy data'
        }), 500

@vehicle_analytics_api.route('/fuel-efficiency', methods=['GET'])
@require_auth
@cross_origin()
def get_fuel_efficiency():
    """
    Get fuel efficiency analysis data
    """
    try:
        user_id = get_current_user_id()
        time_range = request.args.get('time_range', '6months')
        
        # Calculate date range
        end_date = datetime.now()
        if time_range == '3months':
            start_date = end_date - timedelta(days=90)
        elif time_range == '6months':
            start_date = end_date - timedelta(days=180)
        elif time_range == '1year':
            start_date = end_date - timedelta(days=365)
        elif time_range == '2years':
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=180)
        
        fuel_efficiency = _get_fuel_efficiency_data(user_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': fuel_efficiency
        })
        
    except Exception as e:
        logger.error(f"Error getting fuel efficiency: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load fuel efficiency data'
        }), 500

@vehicle_analytics_api.route('/peer-comparison', methods=['GET'])
@require_auth
@cross_origin()
def get_peer_comparison():
    """
    Get anonymized peer comparison data
    """
    try:
        user_id = get_current_user_id()
        user_tier = feature_service.get_user_tier(user_id)
        
        # Check if user has access to peer comparison
        if user_tier not in [FeatureTier.BUDGET_CAREER_VEHICLE, FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
            return jsonify({
                'success': False,
                'error': 'Peer comparison is not available for your subscription tier'
            }), 403
        
        # Get user's current cost per mile
        from backend.models.vehicle_models import Vehicle
        from backend.models.professional_tier_models import FleetVehicle
        
        vehicles = db.session.query(Vehicle).filter(Vehicle.user_id == user_id).all()
        fleet_vehicles = db.session.query(FleetVehicle).filter(FleetVehicle.user_id == user_id).all()
        
        cost_per_mile_analysis = _get_cost_per_mile_analysis(user_id, vehicles + fleet_vehicles)
        peer_comparison = _get_peer_comparison_data(user_id, cost_per_mile_analysis['current'])
        
        return jsonify({
            'success': True,
            'data': peer_comparison
        })
        
    except Exception as e:
        logger.error(f"Error getting peer comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load peer comparison data'
        }), 500

@vehicle_analytics_api.route('/roi-analysis', methods=['GET'])
@require_auth
@cross_origin()
def get_roi_analysis():
    """
    Get ROI analysis for vehicle-related decisions
    """
    try:
        user_id = get_current_user_id()
        user_tier = feature_service.get_user_tier(user_id)
        
        # Check if user has access to ROI analysis
        if user_tier not in [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
            return jsonify({
                'success': False,
                'error': 'ROI analysis is not available for your subscription tier'
            }), 403
        
        # Get user's vehicles
        from backend.models.vehicle_models import Vehicle
        from backend.models.professional_tier_models import FleetVehicle
        
        vehicles = db.session.query(Vehicle).filter(Vehicle.user_id == user_id).all()
        fleet_vehicles = db.session.query(FleetVehicle).filter(FleetVehicle.user_id == user_id).all()
        
        roi_analysis = _get_roi_analysis_data(user_id, vehicles + fleet_vehicles)
        
        return jsonify({
            'success': True,
            'data': roi_analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting ROI analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load ROI analysis data'
        }), 500

@vehicle_analytics_api.route('/export', methods=['POST'])
@require_auth
@cross_origin()
def export_vehicle_analytics():
    """
    Export vehicle analytics data (Professional tier only)
    """
    try:
        user_id = get_current_user_id()
        user_tier = feature_service.get_user_tier(user_id)
        
        # Check if user has access to export functionality
        if user_tier != FeatureTier.PROFESSIONAL:
            return jsonify({
                'success': False,
                'error': 'Export functionality is only available for Professional tier users'
            }), 403
        
        data = request.get_json()
        export_format = data.get('format', 'csv')
        time_range = data.get('time_range', '6months')
        
        # Calculate date range
        end_date = datetime.now()
        if time_range == '3months':
            start_date = end_date - timedelta(days=90)
        elif time_range == '6months':
            start_date = end_date - timedelta(days=180)
        elif time_range == '1year':
            start_date = end_date - timedelta(days=365)
        elif time_range == '2years':
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=180)
        
        # Generate export data
        export_data = _generate_export_data(user_id, start_date, end_date, export_format)
        
        if export_format == 'csv':
            return send_file(
                io.BytesIO(export_data),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'vehicle_analytics_{datetime.now().strftime("%Y%m%d")}.csv'
            )
        elif export_format == 'excel':
            return send_file(
                io.BytesIO(export_data),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'vehicle_analytics_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
        elif export_format == 'pdf':
            return send_file(
                io.BytesIO(export_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'vehicle_analytics_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported export format'
            }), 400
        
    except Exception as e:
        logger.error(f"Error exporting vehicle analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export vehicle analytics data'
        }), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_cost_trends_data(user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Get vehicle cost trends data for the specified date range
    """
    from backend.models.tax_adjacent_models import ExpenseRecord
    from backend.models.professional_tier_models import BusinessExpense
    
    # Get expense records
    expense_records = db.session.query(ExpenseRecord).filter(
        and_(
            ExpenseRecord.user_id == user_id,
            ExpenseRecord.expense_date >= start_date.date(),
            ExpenseRecord.expense_date <= end_date.date(),
            ExpenseRecord.category.in_(['fuel', 'maintenance', 'insurance', 'vehicle_other'])
        )
    ).all()
    
    # Get business expenses
    business_expenses = db.session.query(BusinessExpense).filter(
        and_(
            BusinessExpense.user_id == user_id,
            BusinessExpense.expense_date >= start_date.date(),
            BusinessExpense.expense_date <= end_date.date(),
            BusinessExpense.category.in_(['fuel', 'maintenance', 'insurance', 'vehicle_other'])
        )
    ).all()
    
    # Group by month and category
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
                'otherCost': 0
            }
        
        amount = float(record.amount)
        monthly_data[month_key]['totalCost'] += amount
        
        if record.category == 'fuel':
            monthly_data[month_key]['fuelCost'] += amount
        elif record.category == 'maintenance':
            monthly_data[month_key]['maintenanceCost'] += amount
        elif record.category == 'insurance':
            monthly_data[month_key]['insuranceCost'] += amount
        else:
            monthly_data[month_key]['otherCost'] += amount
    
    return list(monthly_data.values())

def _get_maintenance_accuracy_data(user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Get maintenance prediction accuracy data
    """
    # This would integrate with the maintenance prediction engine
    # For now, return mock data
    return {
        'predicted': 1200,
        'actual': 1150,
        'accuracy': 95.8,
        'savings': 50
    }

def _get_fuel_efficiency_data(user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Get fuel efficiency analysis data
    """
    from backend.models.tax_adjacent_models import ExpenseRecord
    from backend.models.professional_tier_models import BusinessExpense
    
    # Get fuel expenses
    fuel_expenses = db.session.query(ExpenseRecord).filter(
        and_(
            ExpenseRecord.user_id == user_id,
            ExpenseRecord.expense_date >= start_date.date(),
            ExpenseRecord.expense_date <= end_date.date(),
            ExpenseRecord.category == 'fuel'
        )
    ).all()
    
    business_fuel_expenses = db.session.query(BusinessExpense).filter(
        and_(
            BusinessExpense.user_id == user_id,
            BusinessExpense.expense_date >= start_date.date(),
            BusinessExpense.expense_date <= end_date.date(),
            BusinessExpense.category == 'fuel'
        )
    ).all()
    
    # Group by month
    monthly_data = {}
    
    for record in fuel_expenses + business_fuel_expenses:
        month_key = record.expense_date.strftime('%b')
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'month': month_key,
                'mpg': 0,
                'costPerMile': 0,
                'totalMiles': 0,
                'fuelCost': 0
            }
        
        amount = float(record.amount)
        monthly_data[month_key]['fuelCost'] += amount
        
        # Mock MPG calculation - in real implementation, this would use odometer readings
        monthly_data[month_key]['mpg'] = 28.5
        monthly_data[month_key]['totalMiles'] = 1200
        monthly_data[month_key]['costPerMile'] = amount / 1200
    
    return list(monthly_data.values())

def _get_cost_per_mile_analysis(user_id: int, vehicles: List) -> Dict[str, Any]:
    """
    Get cost per mile analysis
    """
    # Calculate total costs and miles for all vehicles
    total_cost = 0
    total_miles = 0
    
    for vehicle in vehicles:
        # Get expenses for this vehicle
        from backend.models.tax_adjacent_models import ExpenseRecord
        from backend.models.professional_tier_models import BusinessExpense
        
        vehicle_expenses = db.session.query(ExpenseRecord).filter(
            ExpenseRecord.user_id == user_id
        ).all()
        
        business_vehicle_expenses = db.session.query(BusinessExpense).filter(
            BusinessExpense.user_id == user_id
        ).all()
        
        for expense in vehicle_expenses + business_vehicle_expenses:
            total_cost += float(expense.amount)
        
        # Add vehicle mileage
        if hasattr(vehicle, 'current_mileage'):
            total_miles += vehicle.current_mileage
        elif hasattr(vehicle, 'current_mileage'):
            total_miles += vehicle.current_mileage
    
    current_cost_per_mile = total_cost / total_miles if total_miles > 0 else 0
    
    return {
        'current': round(current_cost_per_mile, 2),
        'average': round(current_cost_per_mile * 1.1, 2),  # Mock average
        'trend': 'down',
        'breakdown': {
            'fuel': round(current_cost_per_mile * 0.3, 2),
            'maintenance': round(current_cost_per_mile * 0.4, 2),
            'depreciation': round(current_cost_per_mile * 0.2, 2),
            'insurance': round(current_cost_per_mile * 0.1, 2)
        }
    }

def _get_peer_comparison_data(user_id: int, user_cost_per_mile: float) -> Dict[str, Any]:
    """
    Get anonymized peer comparison data
    """
    # Mock peer comparison data - in real implementation, this would use anonymized user data
    peer_average = user_cost_per_mile * 1.15  # 15% higher than user
    savings = peer_average - user_cost_per_mile
    percentile = 25  # User is in 25th percentile (better than 75% of peers)
    
    return {
        'yourCostPerMile': user_cost_per_mile,
        'peerAverage': round(peer_average, 2),
        'percentile': percentile,
        'savings': round(savings, 2)
    }

def _get_roi_analysis_data(user_id: int, vehicles: List) -> Dict[str, Any]:
    """
    Get ROI analysis for vehicle-related decisions
    """
    # Calculate total vehicle investment
    total_investment = 0
    for vehicle in vehicles:
        if hasattr(vehicle, 'purchase_price') and vehicle.purchase_price:
            total_investment += float(vehicle.purchase_price)
        else:
            # Estimate based on vehicle age and type
            total_investment += 25000  # Mock value
    
    # Calculate total savings (from maintenance predictions, fuel efficiency, etc.)
    total_savings = 3500  # Mock value
    
    roi = (total_savings / total_investment) * 100 if total_investment > 0 else 0
    payback_period = total_investment / (total_savings / 12) if total_savings > 0 else 0
    
    return {
        'vehicleInvestment': total_investment,
        'totalSavings': total_savings,
        'roi': round(roi, 1),
        'paybackPeriod': round(payback_period, 1),
        'recommendations': [
            'Consider fuel-efficient driving techniques',
            'Regular maintenance can reduce long-term costs',
            'Compare insurance rates annually',
            'Evaluate vehicle replacement timing based on depreciation curves'
        ]
    }

def _generate_export_data(user_id: int, start_date: datetime, end_date: datetime, format: str) -> bytes:
    """
    Generate export data in the specified format
    """
    # Get all analytics data
    cost_trends = _get_cost_trends_data(user_id, start_date, end_date)
    maintenance_accuracy = _get_maintenance_accuracy_data(user_id, start_date, end_date)
    fuel_efficiency = _get_fuel_efficiency_data(user_id, start_date, end_date)
    
    if format == 'csv':
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Metric', 'Value', 'Date'])
        
        # Write cost trends
        for trend in cost_trends:
            writer.writerow(['Total Cost', trend['totalCost'], trend['date']])
            writer.writerow(['Fuel Cost', trend['fuelCost'], trend['date']])
            writer.writerow(['Maintenance Cost', trend['maintenanceCost'], trend['date']])
            writer.writerow(['Insurance Cost', trend['insuranceCost'], trend['date']])
        
        # Write maintenance accuracy
        writer.writerow(['Maintenance Predicted', maintenance_accuracy['predicted'], ''])
        writer.writerow(['Maintenance Actual', maintenance_accuracy['actual'], ''])
        writer.writerow(['Maintenance Accuracy', maintenance_accuracy['accuracy'], ''])
        
        return output.getvalue().encode('utf-8')
    
    elif format == 'excel':
        # Create Excel data using pandas
        df = pd.DataFrame(cost_trends)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Cost Trends', index=False)
        return output.getvalue()
    
    elif format == 'pdf':
        # Create PDF report - this would use a PDF library like reportlab
        # For now, return a simple text representation
        report_text = f"""
        Vehicle Analytics Report
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
        
        Cost Trends:
        {json.dumps(cost_trends, indent=2)}
        
        Maintenance Accuracy:
        {json.dumps(maintenance_accuracy, indent=2)}
        """
        return report_text.encode('utf-8')
    
    return b''
