#!/usr/bin/env python3
"""
Professional Tier API Routes for Mingus Application
Executive-level features for $100/month Professional tier subscription

Features:
1. Fleet Management Dashboard
2. Tax Optimization Suite
3. Executive Decision Support
4. Advanced Analytics & Reporting
5. Concierge Services
6. Business Integrations
"""

import logging
from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.professional_tier_models import (
    FleetVehicle, MileageLog, BusinessExpense, MaintenanceRecord, 
    TaxReport, FleetAnalytics, VehicleType, BusinessUseType, TaxDeductionType
)
from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
from backend.utils.validation import APIValidator
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
professional_tier_api = Blueprint('professional_tier_api', __name__)

# Initialize validator
validator = APIValidator()

# ============================================================================
# FLEET MANAGEMENT DASHBOARD ENDPOINTS
# ============================================================================

@professional_tier_api.route('/api/professional/fleet', methods=['POST'])
@require_auth
@require_csrf
def create_fleet_vehicle():
    """
    Create a new fleet vehicle with business designation
    
    Request Body:
    {
        "vin": "string",
        "year": "integer",
        "make": "string",
        "model": "string",
        "trim": "string (optional)",
        "vehicle_type": "personal|business|fleet",
        "business_use_percentage": "float (0-100)",
        "primary_business_use": "commute|business_travel|client_meetings|delivery|sales|other",
        "department": "string (optional)",
        "assigned_employee": "string (optional)",
        "cost_center": "string (optional)",
        "current_mileage": "integer (optional, default: 0)",
        "monthly_miles": "integer (optional, default: 0)",
        "user_zipcode": "string",
        "purchase_price": "decimal (optional)",
        "monthly_payment": "decimal (optional)",
        "insurance_cost_monthly": "decimal (optional)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['year', 'make', 'model', 'vehicle_type', 'business_use_percentage', 'user_zipcode']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate vehicle type
        try:
            vehicle_type = VehicleType(data['vehicle_type'])
        except ValueError:
            return jsonify({'error': 'Invalid vehicle_type. Must be personal, business, or fleet'}), 400
        
        # Validate business use percentage
        business_use_percentage = float(data['business_use_percentage'])
        if business_use_percentage < 0 or business_use_percentage > 100:
            return jsonify({'error': 'business_use_percentage must be between 0 and 100'}), 400
        
        # Validate primary business use if provided
        primary_business_use = None
        if data.get('primary_business_use'):
            try:
                primary_business_use = BusinessUseType(data['primary_business_use'])
            except ValueError:
                return jsonify({'error': 'Invalid primary_business_use'}), 400
        
        # Create fleet vehicle
        fleet_vehicle = FleetVehicle(
            user_id=user_id,
            vin=data.get('vin', '').strip().upper(),
            year=int(data['year']),
            make=data['make'].strip(),
            model=data['model'].strip(),
            trim=data.get('trim', '').strip() if data.get('trim') else None,
            vehicle_type=vehicle_type,
            business_use_percentage=business_use_percentage,
            primary_business_use=primary_business_use,
            department=data.get('department', '').strip() if data.get('department') else None,
            assigned_employee=data.get('assigned_employee', '').strip() if data.get('assigned_employee') else None,
            cost_center=data.get('cost_center', '').strip() if data.get('cost_center') else None,
            current_mileage=int(data.get('current_mileage', 0)),
            monthly_miles=int(data.get('monthly_miles', 0)),
            user_zipcode=data['user_zipcode'].strip(),
            purchase_price=Decimal(str(data['purchase_price'])) if data.get('purchase_price') else None,
            monthly_payment=Decimal(str(data['monthly_payment'])) if data.get('monthly_payment') else None,
            insurance_cost_monthly=Decimal(str(data['insurance_cost_monthly'])) if data.get('insurance_cost_monthly') else None
        )
        
        db.session.add(fleet_vehicle)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'fleet_vehicle': fleet_vehicle.to_dict(),
            'message': 'Fleet vehicle created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating fleet vehicle: {e}")
        return jsonify({'error': 'Failed to create fleet vehicle'}), 500

@professional_tier_api.route('/api/professional/fleet', methods=['GET'])
@require_auth
def get_fleet_vehicles():
    """
    Get all fleet vehicles for the authenticated user
    
    Query Parameters:
    - vehicle_type: Filter by vehicle type (personal|business|fleet)
    - department: Filter by department
    - limit: Maximum number of vehicles to return
    - offset: Number of vehicles to skip
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        vehicle_type = request.args.get('vehicle_type')
        department = request.args.get('department')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = FleetVehicle.query.filter_by(user_id=user_id)
        
        # Apply filters
        if vehicle_type:
            try:
                vehicle_type_enum = VehicleType(vehicle_type)
                query = query.filter_by(vehicle_type=vehicle_type_enum)
            except ValueError:
                return jsonify({'error': 'Invalid vehicle_type filter'}), 400
        
        if department:
            query = query.filter_by(department=department)
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        vehicles = query.all()
        
        # Calculate fleet summary
        total_vehicles = FleetVehicle.query.filter_by(user_id=user_id).count()
        business_vehicles = FleetVehicle.query.filter_by(user_id=user_id, vehicle_type=VehicleType.BUSINESS).count()
        personal_vehicles = FleetVehicle.query.filter_by(user_id=user_id, vehicle_type=VehicleType.PERSONAL).count()
        fleet_vehicles = FleetVehicle.query.filter_by(user_id=user_id, vehicle_type=VehicleType.FLEET).count()
        
        return jsonify({
            'success': True,
            'vehicles': [vehicle.to_dict() for vehicle in vehicles],
            'summary': {
                'total_vehicles': total_vehicles,
                'business_vehicles': business_vehicles,
                'personal_vehicles': personal_vehicles,
                'fleet_vehicles': fleet_vehicles
            },
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': total_vehicles
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting fleet vehicles: {e}")
        return jsonify({'error': 'Failed to retrieve fleet vehicles'}), 500

@professional_tier_api.route('/api/professional/fleet/<int:vehicle_id>', methods=['GET'])
@require_auth
def get_fleet_vehicle(vehicle_id):
    """
    Get a specific fleet vehicle by ID
    """
    try:
        user_id = get_current_user_id()
        
        vehicle = FleetVehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        return jsonify({
            'success': True,
            'vehicle': vehicle.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting fleet vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to retrieve fleet vehicle'}), 500

# ============================================================================
# MILEAGE TRACKING ENDPOINTS
# ============================================================================

@professional_tier_api.route('/api/professional/mileage', methods=['POST'])
@require_auth
@require_csrf
def log_mileage():
    """
    Log mileage for a fleet vehicle with GPS integration support
    
    Request Body:
    {
        "fleet_vehicle_id": "integer",
        "trip_date": "date (YYYY-MM-DD)",
        "start_location": "string",
        "end_location": "string",
        "purpose": "string",
        "business_use_type": "commute|business_travel|client_meetings|delivery|sales|other (optional)",
        "total_miles": "float",
        "business_miles": "float (optional, defaults to total_miles)",
        "start_latitude": "float (optional)",
        "start_longitude": "float (optional)",
        "end_latitude": "float (optional)",
        "end_longitude": "float (optional)",
        "receipt_attached": "boolean (optional, default: false)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['fleet_vehicle_id', 'trip_date', 'start_location', 'end_location', 'purpose', 'total_miles']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify vehicle ownership
        vehicle = FleetVehicle.query.filter_by(id=data['fleet_vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        # Validate business use type if provided
        business_use_type = None
        if data.get('business_use_type'):
            try:
                business_use_type = BusinessUseType(data['business_use_type'])
            except ValueError:
                return jsonify({'error': 'Invalid business_use_type'}), 400
        
        # Calculate business and personal miles
        total_miles = float(data['total_miles'])
        business_miles = float(data.get('business_miles', total_miles))
        personal_miles = total_miles - business_miles
        
        if business_miles < 0 or personal_miles < 0:
            return jsonify({'error': 'Invalid mileage values'}), 400
        
        # Get current IRS mileage rate (this would typically come from a service)
        current_mileage_rate = Decimal('0.655')  # 2024 rate, should be dynamic
        
        # Calculate business deduction
        business_deduction = Decimal(str(business_miles)) * current_mileage_rate
        
        # Create mileage log
        mileage_log = MileageLog(
            fleet_vehicle_id=data['fleet_vehicle_id'],
            trip_date=datetime.strptime(data['trip_date'], '%Y-%m-%d').date(),
            start_location=data['start_location'].strip(),
            end_location=data['end_location'].strip(),
            purpose=data['purpose'].strip(),
            business_use_type=business_use_type,
            total_miles=total_miles,
            business_miles=business_miles,
            personal_miles=personal_miles,
            start_latitude=data.get('start_latitude'),
            start_longitude=data.get('start_longitude'),
            end_latitude=data.get('end_latitude'),
            end_longitude=data.get('end_longitude'),
            gps_verified=bool(data.get('start_latitude') and data.get('start_longitude')),
            mileage_rate=current_mileage_rate,
            business_deduction=business_deduction,
            receipt_attached=data.get('receipt_attached', False)
        )
        
        db.session.add(mileage_log)
        
        # Update vehicle mileage totals
        vehicle.business_miles_ytd += int(business_miles)
        vehicle.personal_miles_ytd += int(personal_miles)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mileage_log': mileage_log.to_dict(),
            'message': 'Mileage logged successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging mileage: {e}")
        return jsonify({'error': 'Failed to log mileage'}), 500

@professional_tier_api.route('/api/professional/mileage/<int:vehicle_id>', methods=['GET'])
@require_auth
def get_mileage_logs(vehicle_id):
    """
    Get mileage logs for a specific fleet vehicle
    
    Query Parameters:
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    - business_only: Only return business miles (boolean)
    - limit: Maximum number of records to return
    - offset: Number of records to skip
    """
    try:
        user_id = get_current_user_id()
        
        # Verify vehicle ownership
        vehicle = FleetVehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        business_only = request.args.get('business_only', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = MileageLog.query.filter_by(fleet_vehicle_id=vehicle_id)
        
        # Apply filters
        if start_date:
            query = query.filter(MileageLog.trip_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(MileageLog.trip_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        if business_only:
            query = query.filter(MileageLog.business_miles > 0)
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        logs = query.order_by(MileageLog.trip_date.desc()).all()
        
        # Calculate summary
        total_miles = sum(log.total_miles for log in logs)
        business_miles = sum(log.business_miles for log in logs)
        personal_miles = sum(log.personal_miles for log in logs)
        total_deduction = sum(float(log.business_deduction) for log in logs)
        
        return jsonify({
            'success': True,
            'vehicle_id': vehicle_id,
            'mileage_logs': [log.to_dict() for log in logs],
            'summary': {
                'total_trips': len(logs),
                'total_miles': total_miles,
                'business_miles': business_miles,
                'personal_miles': personal_miles,
                'total_deduction': round(total_deduction, 2),
                'average_miles_per_trip': round(total_miles / len(logs), 2) if logs else 0
            },
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': MileageLog.query.filter_by(fleet_vehicle_id=vehicle_id).count()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting mileage logs for vehicle {vehicle_id}: {e}")
        return jsonify({'error': 'Failed to retrieve mileage logs'}), 500

# ============================================================================
# TAX OPTIMIZATION ENDPOINTS
# ============================================================================

@professional_tier_api.route('/api/professional/tax/calculator', methods=['POST'])
@require_auth
@require_csrf
def calculate_tax_deductions():
    """
    Calculate optimal tax deductions for business vehicles
    
    Request Body:
    {
        "fleet_vehicle_id": "integer",
        "tax_year": "integer",
        "deduction_method": "mileage|actual_expenses (optional, will calculate optimal)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        if 'fleet_vehicle_id' not in data:
            return jsonify({'error': 'fleet_vehicle_id is required'}), 400
        
        # Verify vehicle ownership
        vehicle = FleetVehicle.query.filter_by(id=data['fleet_vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        tax_year = data.get('tax_year', datetime.now().year)
        deduction_method = data.get('deduction_method')
        
        # Get mileage data for the tax year
        start_date = date(tax_year, 1, 1)
        end_date = date(tax_year, 12, 31)
        
        mileage_logs = MileageLog.query.filter(
            MileageLog.fleet_vehicle_id == data['fleet_vehicle_id'],
            MileageLog.trip_date >= start_date,
            MileageLog.trip_date <= end_date
        ).all()
        
        # Get expense data for the tax year
        expenses = BusinessExpense.query.filter(
            BusinessExpense.fleet_vehicle_id == data['fleet_vehicle_id'],
            BusinessExpense.tax_year == tax_year
        ).all()
        
        # Calculate mileage deduction
        total_business_miles = sum(log.business_miles for log in mileage_logs)
        mileage_rate = Decimal('0.655')  # 2024 rate
        mileage_deduction = Decimal(str(total_business_miles)) * mileage_rate
        
        # Calculate actual expenses deduction
        total_actual_expenses = sum(expense.deductible_amount for expense in expenses)
        
        # Determine optimal method if not specified
        if not deduction_method:
            deduction_method = 'mileage' if mileage_deduction > total_actual_expenses else 'actual_expenses'
        
        # Calculate final deduction
        if deduction_method == 'mileage':
            final_deduction = mileage_deduction
            actual_expenses_available = total_actual_expenses
        else:
            final_deduction = total_actual_expenses
            actual_expenses_available = total_actual_expenses
        
        # Calculate potential savings (assuming 25% tax bracket)
        tax_rate = Decimal('0.25')
        potential_savings = final_deduction * tax_rate
        
        return jsonify({
            'success': True,
            'vehicle_id': data['fleet_vehicle_id'],
            'tax_year': tax_year,
            'deduction_calculation': {
                'mileage_method': {
                    'total_business_miles': total_business_miles,
                    'mileage_rate': float(mileage_rate),
                    'deduction_amount': float(mileage_deduction)
                },
                'actual_expenses_method': {
                    'total_expenses': float(total_actual_expenses),
                    'deduction_amount': float(total_actual_expenses)
                },
                'recommended_method': deduction_method,
                'final_deduction': float(final_deduction),
                'potential_tax_savings': float(potential_savings)
            },
            'summary': {
                'total_trips': len(mileage_logs),
                'total_expenses': len(expenses),
                'business_use_percentage': vehicle.business_use_percentage
            }
        })
    
    except Exception as e:
        logger.error(f"Error calculating tax deductions: {e}")
        return jsonify({'error': 'Failed to calculate tax deductions'}), 500

@professional_tier_api.route('/api/professional/tax/report', methods=['POST'])
@require_auth
@require_csrf
def generate_tax_report():
    """
    Generate CPA-ready tax report for business vehicles
    
    Request Body:
    {
        "fleet_vehicle_id": "integer",
        "tax_year": "integer",
        "report_type": "annual|quarterly|monthly",
        "include_receipts": "boolean (optional, default: true)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['fleet_vehicle_id', 'tax_year', 'report_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify vehicle ownership
        vehicle = FleetVehicle.query.filter_by(id=data['fleet_vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        tax_year = data['tax_year']
        report_type = data['report_type']
        include_receipts = data.get('include_receipts', True)
        
        # Calculate report period
        if report_type == 'annual':
            start_date = date(tax_year, 1, 1)
            end_date = date(tax_year, 12, 31)
        elif report_type == 'quarterly':
            quarter = data.get('quarter', 1)
            quarter_starts = [1, 4, 7, 10]
            start_date = date(tax_year, quarter_starts[quarter-1], 1)
            end_date = date(tax_year, quarter_starts[quarter-1] + 2, 31)
        else:  # monthly
            month = data.get('month', 1)
            start_date = date(tax_year, month, 1)
            end_date = date(tax_year, month, 28)  # Simplified
        
        # Get mileage data
        mileage_logs = MileageLog.query.filter(
            MileageLog.fleet_vehicle_id == data['fleet_vehicle_id'],
            MileageLog.trip_date >= start_date,
            MileageLog.trip_date <= end_date
        ).all()
        
        # Get expense data
        expenses = BusinessExpense.query.filter(
            BusinessExpense.fleet_vehicle_id == data['fleet_vehicle_id'],
            BusinessExpense.tax_year == tax_year,
            BusinessExpense.expense_date >= start_date,
            BusinessExpense.expense_date <= end_date
        ).all()
        
        # Calculate totals
        total_business_miles = sum(log.business_miles for log in mileage_logs)
        total_personal_miles = sum(log.personal_miles for log in mileage_logs)
        mileage_deduction = sum(float(log.business_deduction) for log in mileage_logs)
        
        # Categorize expenses
        maintenance_expenses = sum(exp.amount for exp in expenses if exp.category == 'maintenance')
        fuel_expenses = sum(exp.amount for exp in expenses if exp.category == 'fuel')
        insurance_expenses = sum(exp.amount for exp in expenses if exp.category == 'insurance')
        other_expenses = sum(exp.amount for exp in expenses if exp.category not in ['maintenance', 'fuel', 'insurance'])
        
        total_business_expenses = sum(exp.deductible_amount for exp in expenses)
        
        # Create tax report
        tax_report = TaxReport(
            fleet_vehicle_id=data['fleet_vehicle_id'],
            tax_year=tax_year,
            report_type=report_type,
            report_period_start=start_date,
            report_period_end=end_date,
            total_business_miles=total_business_miles,
            total_personal_miles=total_personal_miles,
            mileage_deduction_amount=Decimal(str(mileage_deduction)),
            average_mileage_rate=Decimal('0.655'),
            total_business_expenses=total_business_expenses,
            maintenance_expenses=maintenance_expenses,
            fuel_expenses=fuel_expenses,
            insurance_expenses=insurance_expenses,
            other_expenses=other_expenses,
            recommended_deduction_method=TaxDeductionType.MILEAGE if mileage_deduction > total_business_expenses else TaxDeductionType.ACTUAL_EXPENSES,
            potential_savings=Decimal(str((mileage_deduction + total_business_expenses) * 0.25)),
            cpa_ready=True
        )
        
        db.session.add(tax_report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'tax_report': tax_report.to_dict(),
            'message': 'Tax report generated successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating tax report: {e}")
        return jsonify({'error': 'Failed to generate tax report'}), 500

# ============================================================================
# FLEET ANALYTICS ENDPOINTS
# ============================================================================

@professional_tier_api.route('/api/professional/analytics/fleet', methods=['GET'])
@require_auth
def get_fleet_analytics():
    """
    Get comprehensive fleet analytics and KPIs
    
    Query Parameters:
    - period: daily|weekly|monthly|quarterly|yearly (default: monthly)
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        period = request.args.get('period', 'monthly')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get fleet vehicles
        vehicles = FleetVehicle.query.filter_by(user_id=user_id).all()
        
        if not vehicles:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_vehicles': 0,
                    'business_vehicles': 0,
                    'personal_vehicles': 0,
                    'total_monthly_cost': 0,
                    'cost_per_mile': 0,
                    'total_miles': 0,
                    'business_miles': 0,
                    'personal_miles': 0,
                    'maintenance_cost_total': 0,
                    'total_tax_deductions': 0
                },
                'message': 'No fleet vehicles found'
            })
        
        # Calculate analytics
        total_vehicles = len(vehicles)
        business_vehicles = len([v for v in vehicles if v.vehicle_type == VehicleType.BUSINESS])
        personal_vehicles = len([v for v in vehicles if v.vehicle_type == VehicleType.PERSONAL])
        
        # Calculate costs
        total_monthly_cost = sum(
            (v.monthly_payment or 0) + (v.insurance_cost_monthly or 0) 
            for v in vehicles
        )
        
        # Calculate miles
        total_miles = sum(v.monthly_miles for v in vehicles)
        business_miles = sum(v.business_miles_ytd for v in vehicles)
        personal_miles = sum(v.personal_miles_ytd for v in vehicles)
        
        # Calculate cost per mile
        cost_per_mile = total_monthly_cost / total_miles if total_miles > 0 else 0
        
        # Get maintenance costs (simplified - would need actual maintenance records)
        maintenance_cost_total = 0  # Would calculate from MaintenanceRecord
        
        # Get tax deductions (simplified)
        total_tax_deductions = 0  # Would calculate from TaxReport
        
        analytics = {
            'total_vehicles': total_vehicles,
            'business_vehicles': business_vehicles,
            'personal_vehicles': personal_vehicles,
            'fleet_vehicles': len([v for v in vehicles if v.vehicle_type == VehicleType.FLEET]),
            'total_monthly_cost': float(total_monthly_cost),
            'cost_per_mile': float(cost_per_mile),
            'cost_per_vehicle': float(total_monthly_cost / total_vehicles) if total_vehicles > 0 else 0,
            'total_miles': total_miles,
            'business_miles': business_miles,
            'personal_miles': personal_miles,
            'average_mpg': 25.0,  # Would calculate from actual data
            'maintenance_cost_total': maintenance_cost_total,
            'maintenance_cost_per_mile': maintenance_cost_total / total_miles if total_miles > 0 else 0,
            'maintenance_frequency': 0,  # Would calculate from actual data
            'total_tax_deductions': total_tax_deductions,
            'mileage_deductions': 0,  # Would calculate from actual data
            'expense_deductions': 0   # Would calculate from actual data
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period': period,
            'generated_at': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting fleet analytics: {e}")
        return jsonify({'error': 'Failed to retrieve fleet analytics'}), 500

# ============================================================================
# EXECUTIVE DECISION SUPPORT ENDPOINTS
# ============================================================================

@professional_tier_api.route('/api/professional/roi-analysis', methods=['POST'])
@require_auth
@require_csrf
def calculate_vehicle_roi():
    """
    Calculate ROI analysis for vehicle replacement decisions
    
    Request Body:
    {
        "fleet_vehicle_id": "integer",
        "replacement_vehicle": {
            "year": "integer",
            "make": "string",
            "model": "string",
            "purchase_price": "decimal",
            "monthly_payment": "decimal",
            "insurance_cost_monthly": "decimal",
            "expected_mpg": "float"
        },
        "analysis_period_years": "integer (optional, default: 5)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        if 'fleet_vehicle_id' not in data or 'replacement_vehicle' not in data:
            return jsonify({'error': 'fleet_vehicle_id and replacement_vehicle are required'}), 400
        
        # Verify vehicle ownership
        current_vehicle = FleetVehicle.query.filter_by(id=data['fleet_vehicle_id'], user_id=user_id).first()
        if not current_vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        replacement = data['replacement_vehicle']
        analysis_period = data.get('analysis_period_years', 5)
        
        # Calculate current vehicle costs
        current_monthly_cost = (current_vehicle.monthly_payment or 0) + (current_vehicle.insurance_cost_monthly or 0)
        current_annual_cost = current_monthly_cost * 12
        current_total_cost = current_annual_cost * analysis_period
        
        # Calculate replacement vehicle costs
        replacement_monthly_cost = (replacement.get('monthly_payment', 0) or 0) + (replacement.get('insurance_cost_monthly', 0) or 0)
        replacement_annual_cost = replacement_monthly_cost * 12
        replacement_total_cost = replacement_annual_cost * analysis_period
        
        # Calculate fuel savings (simplified)
        current_mpg = 25.0  # Would get from vehicle data
        replacement_mpg = replacement.get('expected_mpg', 30.0)
        monthly_miles = current_vehicle.monthly_miles
        gas_price = 3.50  # Would get from gas price service
        
        current_fuel_cost = (monthly_miles / current_mpg) * gas_price * 12
        replacement_fuel_cost = (monthly_miles / replacement_mpg) * gas_price * 12
        annual_fuel_savings = current_fuel_cost - replacement_fuel_cost
        total_fuel_savings = annual_fuel_savings * analysis_period
        
        # Calculate maintenance savings (simplified)
        current_maintenance_cost = 2000  # Would calculate from actual data
        replacement_maintenance_cost = 1500  # Would calculate based on vehicle age/type
        annual_maintenance_savings = current_maintenance_cost - replacement_maintenance_cost
        total_maintenance_savings = annual_maintenance_savings * analysis_period
        
        # Calculate total savings
        total_savings = total_fuel_savings + total_maintenance_savings
        net_cost = replacement_total_cost - current_total_cost - total_savings
        
        # Calculate ROI
        roi_percentage = (total_savings / replacement_total_cost) * 100 if replacement_total_cost > 0 else 0
        
        # Calculate payback period
        monthly_savings = (annual_fuel_savings + annual_maintenance_savings) / 12
        payback_months = (replacement.get('purchase_price', 0) / monthly_savings) if monthly_savings > 0 else float('inf')
        
        return jsonify({
            'success': True,
            'roi_analysis': {
                'current_vehicle': {
                    'monthly_cost': float(current_monthly_cost),
                    'annual_cost': float(current_annual_cost),
                    'total_cost_over_period': float(current_total_cost)
                },
                'replacement_vehicle': {
                    'monthly_cost': float(replacement_monthly_cost),
                    'annual_cost': float(replacement_annual_cost),
                    'total_cost_over_period': float(replacement_total_cost)
                },
                'savings': {
                    'annual_fuel_savings': float(annual_fuel_savings),
                    'total_fuel_savings': float(total_fuel_savings),
                    'annual_maintenance_savings': float(annual_maintenance_savings),
                    'total_maintenance_savings': float(total_maintenance_savings),
                    'total_savings': float(total_savings)
                },
                'financial_impact': {
                    'net_cost': float(net_cost),
                    'roi_percentage': float(roi_percentage),
                    'payback_months': float(payback_months),
                    'recommendation': 'replace' if roi_percentage > 10 else 'keep_current'
                }
            },
            'analysis_period_years': analysis_period
        })
    
    except Exception as e:
        logger.error(f"Error calculating vehicle ROI: {e}")
        return jsonify({'error': 'Failed to calculate vehicle ROI'}), 500

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@professional_tier_api.route('/api/professional/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Professional tier API
    """
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'healthy',
                'professional_tier_api': 'active'
            },
            'message': 'Professional tier API is healthy'
        })
    
    except Exception as e:
        logger.error(f"Professional tier health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'message': 'Professional tier API health check failed'
        }), 500
