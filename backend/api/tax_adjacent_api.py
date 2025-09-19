#!/usr/bin/env python3
"""
Tax-Adjacent API Routes for Mingus Professional Tier
Focused on expense tracking, documentation, and educational resources
"""

import logging
from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.tax_adjacent_models import (
    BusinessMileageLog, ExpenseRecord, MaintenanceDocument, 
    VehicleUseTracking, EducationalContent, ExpenseReport,
    ExpenseCategory, TripPurpose, DocumentType
)
from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
from backend.utils.validation import APIValidator
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
tax_adjacent_api = Blueprint('tax_adjacent_api', __name__)

# Initialize validator
validator = APIValidator()

# ============================================================================
# EXPENSE TRACKING & CATEGORIZATION ENDPOINTS
# ============================================================================

@tax_adjacent_api.route('/api/professional/expenses', methods=['POST'])
@require_auth
@require_csrf
def create_expense_record():
    """
    Create a new expense record with business vs personal classification
    
    Request Body:
    {
        "expense_date": "date (YYYY-MM-DD)",
        "category": "fuel|maintenance|insurance|parking|tolls|registration|repairs|other",
        "subcategory": "string (optional)",
        "description": "string",
        "amount": "decimal",
        "is_business_expense": "boolean",
        "business_percentage": "float (0-100)",
        "business_purpose": "string (optional)",
        "vendor_name": "string (optional)",
        "vendor_address": "string (optional)",
        "receipt_attached": "boolean (optional, default: false)",
        "tax_year": "integer"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['expense_date', 'category', 'description', 'amount', 'tax_year']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate category
        try:
            category = ExpenseCategory(data['category'])
        except ValueError:
            return jsonify({'error': 'Invalid expense category'}), 400
        
        # Validate business percentage
        business_percentage = float(data.get('business_percentage', 100.0))
        if business_percentage < 0 or business_percentage > 100:
            return jsonify({'error': 'business_percentage must be between 0 and 100'}), 400
        
        # Create expense record
        expense = ExpenseRecord(
            user_id=user_id,
            expense_date=datetime.strptime(data['expense_date'], '%Y-%m-%d').date(),
            category=category,
            subcategory=data.get('subcategory', '').strip() if data.get('subcategory') else None,
            description=data['description'].strip(),
            amount=Decimal(str(data['amount'])),
            is_business_expense=data.get('is_business_expense', True),
            business_percentage=business_percentage,
            business_purpose=data.get('business_purpose', '').strip() if data.get('business_purpose') else None,
            vendor_name=data.get('vendor_name', '').strip() if data.get('vendor_name') else None,
            vendor_address=data.get('vendor_address', '').strip() if data.get('vendor_address') else None,
            receipt_attached=data.get('receipt_attached', False),
            tax_year=int(data['tax_year'])
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'expense': expense.to_dict(),
            'message': 'Expense record created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating expense record: {e}")
        return jsonify({'error': 'Failed to create expense record'}), 500

@tax_adjacent_api.route('/api/professional/expenses', methods=['GET'])
@require_auth
def get_expense_records():
    """
    Get expense records for the authenticated user
    
    Query Parameters:
    - category: Filter by expense category
    - tax_year: Filter by tax year
    - is_business: Filter by business vs personal (true/false)
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    - limit: Maximum number of records to return
    - offset: Number of records to skip
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        category = request.args.get('category')
        tax_year = request.args.get('tax_year', type=int)
        is_business = request.args.get('is_business')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = ExpenseRecord.query.filter_by(user_id=user_id)
        
        # Apply filters
        if category:
            try:
                category_enum = ExpenseCategory(category)
                query = query.filter_by(category=category_enum)
            except ValueError:
                return jsonify({'error': 'Invalid category filter'}), 400
        
        if tax_year:
            query = query.filter_by(tax_year=tax_year)
        
        if is_business is not None:
            is_business_bool = is_business.lower() == 'true'
            query = query.filter_by(is_business_expense=is_business_bool)
        
        if start_date:
            query = query.filter(ExpenseRecord.expense_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(ExpenseRecord.expense_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        expenses = query.order_by(ExpenseRecord.expense_date.desc()).all()
        
        # Calculate summary
        total_amount = sum(float(expense.amount) for expense in expenses)
        business_amount = sum(float(expense.amount) for expense in expenses if expense.is_business_expense)
        personal_amount = total_amount - business_amount
        
        return jsonify({
            'success': True,
            'expenses': [expense.to_dict() for expense in expenses],
            'summary': {
                'total_records': len(expenses),
                'total_amount': round(total_amount, 2),
                'business_amount': round(business_amount, 2),
                'personal_amount': round(personal_amount, 2)
            },
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': ExpenseRecord.query.filter_by(user_id=user_id).count()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting expense records: {e}")
        return jsonify({'error': 'Failed to retrieve expense records'}), 500

# ============================================================================
# MILEAGE LOGGING ENDPOINTS
# ============================================================================

@tax_adjacent_api.route('/api/professional/mileage', methods=['POST'])
@require_auth
@require_csrf
def log_business_mileage():
    """
    Log business mileage with IRS-compliant tracking
    
    Request Body:
    {
        "trip_date": "date (YYYY-MM-DD)",
        "start_location": "string",
        "end_location": "string",
        "trip_purpose": "business_travel|client_meeting|office_commute|business_errand|personal|other",
        "business_purpose": "string (optional)",
        "total_miles": "float",
        "business_miles": "float (optional, defaults to total_miles)",
        "odometer_start": "integer (optional)",
        "odometer_end": "integer (optional)",
        "start_latitude": "float (optional)",
        "start_longitude": "float (optional)",
        "end_latitude": "float (optional)",
        "end_longitude": "float (optional)",
        "business_use_percentage": "float (optional, default: 100.0)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['trip_date', 'start_location', 'end_location', 'trip_purpose', 'total_miles']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate trip purpose
        try:
            trip_purpose = TripPurpose(data['trip_purpose'])
        except ValueError:
            return jsonify({'error': 'Invalid trip purpose'}), 400
        
        # Calculate business and personal miles
        total_miles = float(data['total_miles'])
        business_miles = float(data.get('business_miles', total_miles))
        personal_miles = total_miles - business_miles
        business_use_percentage = float(data.get('business_use_percentage', 100.0))
        
        if business_miles < 0 or personal_miles < 0:
            return jsonify({'error': 'Invalid mileage values'}), 400
        
        # Create mileage log
        mileage_log = BusinessMileageLog(
            user_id=user_id,
            trip_date=datetime.strptime(data['trip_date'], '%Y-%m-%d').date(),
            start_location=data['start_location'].strip(),
            end_location=data['end_location'].strip(),
            trip_purpose=trip_purpose,
            business_purpose=data.get('business_purpose', '').strip() if data.get('business_purpose') else None,
            total_miles=total_miles,
            business_miles=business_miles,
            personal_miles=personal_miles,
            odometer_start=data.get('odometer_start'),
            odometer_end=data.get('odometer_end'),
            start_latitude=data.get('start_latitude'),
            start_longitude=data.get('start_longitude'),
            end_latitude=data.get('end_latitude'),
            end_longitude=data.get('end_longitude'),
            gps_verified=bool(data.get('start_latitude') and data.get('start_longitude')),
            business_use_percentage=business_use_percentage
        )
        
        db.session.add(mileage_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mileage_log': mileage_log.to_dict(),
            'message': 'Business mileage logged successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging business mileage: {e}")
        return jsonify({'error': 'Failed to log business mileage'}), 500

@tax_adjacent_api.route('/api/professional/mileage', methods=['GET'])
@require_auth
def get_mileage_logs():
    """
    Get mileage logs for the authenticated user
    
    Query Parameters:
    - trip_purpose: Filter by trip purpose
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    - business_only: Only return business trips (true/false)
    - limit: Maximum number of records to return
    - offset: Number of records to skip
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        trip_purpose = request.args.get('trip_purpose')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        business_only = request.args.get('business_only', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = BusinessMileageLog.query.filter_by(user_id=user_id)
        
        # Apply filters
        if trip_purpose:
            try:
                trip_purpose_enum = TripPurpose(trip_purpose)
                query = query.filter_by(trip_purpose=trip_purpose_enum)
            except ValueError:
                return jsonify({'error': 'Invalid trip purpose filter'}), 400
        
        if start_date:
            query = query.filter(BusinessMileageLog.trip_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(BusinessMileageLog.trip_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        if business_only:
            query = query.filter(BusinessMileageLog.business_miles > 0)
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        logs = query.order_by(BusinessMileageLog.trip_date.desc()).all()
        
        # Calculate summary
        total_miles = sum(log.total_miles for log in logs)
        business_miles = sum(log.business_miles for log in logs)
        personal_miles = sum(log.personal_miles for log in logs)
        
        return jsonify({
            'success': True,
            'mileage_logs': [log.to_dict() for log in logs],
            'summary': {
                'total_trips': len(logs),
                'total_miles': total_miles,
                'business_miles': business_miles,
                'personal_miles': personal_miles,
                'average_miles_per_trip': round(total_miles / len(logs), 2) if logs else 0
            },
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': BusinessMileageLog.query.filter_by(user_id=user_id).count()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting mileage logs: {e}")
        return jsonify({'error': 'Failed to retrieve mileage logs'}), 500

# ============================================================================
# MAINTENANCE DOCUMENTATION ENDPOINTS
# ============================================================================

@tax_adjacent_api.route('/api/professional/maintenance', methods=['POST'])
@require_auth
@require_csrf
def create_maintenance_document():
    """
    Create a maintenance document record
    
    Request Body:
    {
        "vehicle_year": "integer",
        "vehicle_make": "string",
        "vehicle_model": "string",
        "vehicle_vin": "string (optional)",
        "service_date": "date (YYYY-MM-DD)",
        "service_type": "string",
        "description": "string",
        "odometer_reading": "integer",
        "total_cost": "decimal",
        "labor_cost": "decimal (optional)",
        "parts_cost": "decimal (optional)",
        "service_provider": "string (optional)",
        "service_address": "string (optional)",
        "service_phone": "string (optional)",
        "warranty_info": "string (optional)",
        "warranty_expires": "date (optional, YYYY-MM-DD)",
        "business_use_percentage": "float (optional, default: 100.0)",
        "is_business_expense": "boolean (optional, default: true)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['vehicle_year', 'vehicle_make', 'vehicle_model', 'service_date', 
                          'service_type', 'description', 'odometer_reading', 'total_cost']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate business use percentage
        business_use_percentage = float(data.get('business_use_percentage', 100.0))
        if business_use_percentage < 0 or business_use_percentage > 100:
            return jsonify({'error': 'business_use_percentage must be between 0 and 100'}), 400
        
        # Create maintenance document
        maintenance = MaintenanceDocument(
            user_id=user_id,
            vehicle_year=int(data['vehicle_year']),
            vehicle_make=data['vehicle_make'].strip(),
            vehicle_model=data['vehicle_model'].strip(),
            vehicle_vin=data.get('vehicle_vin', '').strip() if data.get('vehicle_vin') else None,
            service_date=datetime.strptime(data['service_date'], '%Y-%m-%d').date(),
            service_type=data['service_type'].strip(),
            description=data['description'].strip(),
            odometer_reading=int(data['odometer_reading']),
            total_cost=Decimal(str(data['total_cost'])),
            labor_cost=Decimal(str(data['labor_cost'])) if data.get('labor_cost') else None,
            parts_cost=Decimal(str(data['parts_cost'])) if data.get('parts_cost') else None,
            service_provider=data.get('service_provider', '').strip() if data.get('service_provider') else None,
            service_address=data.get('service_address', '').strip() if data.get('service_address') else None,
            service_phone=data.get('service_phone', '').strip() if data.get('service_phone') else None,
            warranty_info=data.get('warranty_info', '').strip() if data.get('warranty_info') else None,
            warranty_expires=datetime.strptime(data['warranty_expires'], '%Y-%m-%d').date() if data.get('warranty_expires') else None,
            business_use_percentage=business_use_percentage,
            is_business_expense=data.get('is_business_expense', True)
        )
        
        db.session.add(maintenance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'maintenance': maintenance.to_dict(),
            'message': 'Maintenance document created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating maintenance document: {e}")
        return jsonify({'error': 'Failed to create maintenance document'}), 500

# ============================================================================
# EDUCATIONAL RESOURCES ENDPOINTS
# ============================================================================

@tax_adjacent_api.route('/api/professional/education', methods=['GET'])
@require_auth
def get_educational_content():
    """
    Get educational content for tax deductions
    
    Query Parameters:
    - content_type: Filter by content type (article, checklist, guide, summary)
    - category: Filter by category (tax_deductions, irs_publications, preparation)
    - difficulty: Filter by difficulty level (beginner, intermediate, advanced)
    - featured: Only return featured content (true/false)
    - limit: Maximum number of records to return
    - offset: Number of records to skip
    """
    try:
        # Get query parameters
        content_type = request.args.get('content_type')
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        featured = request.args.get('featured', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = EducationalContent.query.filter_by(is_published=True)
        
        # Apply filters
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        if category:
            query = query.filter_by(category=category)
        
        if difficulty:
            query = query.filter_by(difficulty_level=difficulty)
        
        if featured:
            query = query.filter_by(is_featured=True)
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        content = query.order_by(EducationalContent.created_date.desc()).all()
        
        return jsonify({
            'success': True,
            'content': [item.to_dict() for item in content],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': EducationalContent.query.filter_by(is_published=True).count()
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting educational content: {e}")
        return jsonify({'error': 'Failed to retrieve educational content'}), 500

@tax_adjacent_api.route('/api/professional/education/<int:content_id>', methods=['GET'])
@require_auth
def get_educational_content_item(content_id):
    """
    Get a specific educational content item
    """
    try:
        content = EducationalContent.query.filter_by(id=content_id, is_published=True).first()
        if not content:
            return jsonify({'error': 'Educational content not found'}), 404
        
        return jsonify({
            'success': True,
            'content': content.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting educational content item {content_id}: {e}")
        return jsonify({'error': 'Failed to retrieve educational content item'}), 500

# ============================================================================
# EXPENSE REPORT GENERATION ENDPOINTS
# ============================================================================

@tax_adjacent_api.route('/api/professional/reports/expense', methods=['POST'])
@require_auth
@require_csrf
def generate_expense_report():
    """
    Generate an expense report for a specific period
    
    Request Body:
    {
        "report_year": "integer",
        "report_type": "annual|quarterly|monthly",
        "report_period_start": "date (YYYY-MM-DD)",
        "report_period_end": "date (YYYY-MM-DD)"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['report_year', 'report_type', 'report_period_start', 'report_period_end']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        report_year = data['report_year']
        report_type = data['report_type']
        start_date = datetime.strptime(data['report_period_start'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['report_period_end'], '%Y-%m-%d').date()
        
        # Get expenses for the period
        expenses = ExpenseRecord.query.filter(
            ExpenseRecord.user_id == user_id,
            ExpenseRecord.expense_date >= start_date,
            ExpenseRecord.expense_date <= end_date
        ).all()
        
        # Get mileage for the period
        mileage_logs = BusinessMileageLog.query.filter(
            BusinessMileageLog.user_id == user_id,
            BusinessMileageLog.trip_date >= start_date,
            BusinessMileageLog.trip_date <= end_date
        ).all()
        
        # Calculate totals
        total_expenses = sum(float(expense.amount) for expense in expenses)
        business_expenses = sum(float(expense.amount) for expense in expenses if expense.is_business_expense)
        personal_expenses = total_expenses - business_expenses
        
        # Category breakdown
        category_totals = {}
        for expense in expenses:
            category = expense.category.value
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += float(expense.amount)
        
        # Mileage totals
        total_miles = sum(log.total_miles for log in mileage_logs)
        business_miles = sum(log.business_miles for log in mileage_logs)
        personal_miles = sum(log.personal_miles for log in mileage_logs)
        
        # Create expense report
        expense_report = ExpenseReport(
            user_id=user_id,
            report_year=report_year,
            report_type=report_type,
            report_period_start=start_date,
            report_period_end=end_date,
            total_expenses=Decimal(str(total_expenses)),
            business_expenses=Decimal(str(business_expenses)),
            personal_expenses=Decimal(str(personal_expenses)),
            fuel_expenses=Decimal(str(category_totals.get('fuel', 0))),
            maintenance_expenses=Decimal(str(category_totals.get('maintenance', 0))),
            insurance_expenses=Decimal(str(category_totals.get('insurance', 0))),
            parking_expenses=Decimal(str(category_totals.get('parking', 0))),
            toll_expenses=Decimal(str(category_totals.get('tolls', 0))),
            other_expenses=Decimal(str(category_totals.get('other', 0))),
            total_miles=total_miles,
            business_miles=business_miles,
            personal_miles=personal_miles
        )
        
        db.session.add(expense_report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'expense_report': expense_report.to_dict(),
            'message': 'Expense report generated successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating expense report: {e}")
        return jsonify({'error': 'Failed to generate expense report'}), 500

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@tax_adjacent_api.route('/api/professional/tax-adjacent/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for tax-adjacent API
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
                'tax_adjacent_api': 'active'
            },
            'message': 'Tax-adjacent API is healthy'
        })
    
    except Exception as e:
        logger.error(f"Tax-adjacent health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'message': 'Tax-adjacent API health check failed'
        }), 500
