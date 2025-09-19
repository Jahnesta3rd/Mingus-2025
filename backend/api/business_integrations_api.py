#!/usr/bin/env python3
"""
Business Integrations API for Mingus Professional Tier
Integration features for QuickBooks, corporate credit cards, HR systems, and insurance management
"""

import logging
from flask import Blueprint, request, jsonify
from backend.models.database import db
from backend.models.professional_tier_models import FleetVehicle, BusinessExpense, MileageLog
from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
from backend.utils.validation import APIValidator
from datetime import datetime, date
from decimal import Decimal
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
business_integrations_api = Blueprint('business_integrations_api', __name__)

# Initialize validator
validator = APIValidator()

# ============================================================================
# QUICKBOOKS INTEGRATION ENDPOINTS
# ============================================================================

@business_integrations_api.route('/api/professional/integrations/quickbooks/connect', methods=['POST'])
@require_auth
@require_csrf
def connect_quickbooks():
    """
    Connect to QuickBooks for automatic expense categorization and sync
    
    Request Body:
    {
        "company_id": "string",
        "access_token": "string",
        "refresh_token": "string",
        "realm_id": "string"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['company_id', 'access_token', 'realm_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # In a real implementation, you would:
        # 1. Validate the QuickBooks credentials
        # 2. Store the connection securely
        # 3. Test the connection
        
        # For now, simulate successful connection
        connection_status = {
            'connected': True,
            'company_name': 'Sample Company LLC',
            'last_sync': datetime.utcnow().isoformat(),
            'sync_status': 'active'
        }
        
        return jsonify({
            'success': True,
            'connection': connection_status,
            'message': 'QuickBooks connected successfully'
        })
    
    except Exception as e:
        logger.error(f"Error connecting to QuickBooks: {e}")
        return jsonify({'error': 'Failed to connect to QuickBooks'}), 500

@business_integrations_api.route('/api/professional/integrations/quickbooks/sync', methods=['POST'])
@require_auth
@require_csrf
def sync_quickbooks_expenses():
    """
    Sync vehicle expenses from QuickBooks
    
    Request Body:
    {
        "fleet_vehicle_id": "integer",
        "sync_period_days": "integer (optional, default: 30)"
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
        
        sync_period = data.get('sync_period_days', 30)
        
        # In a real implementation, you would:
        # 1. Connect to QuickBooks API
        # 2. Fetch expense transactions
        # 3. Categorize and match to vehicles
        # 4. Create BusinessExpense records
        
        # For now, simulate synced expenses
        synced_expenses = [
            {
                'expense_date': (datetime.now() - timedelta(days=5)).date().isoformat(),
                'category': 'fuel',
                'description': 'Gas station purchase',
                'amount': 45.67,
                'vendor': 'Shell Gas Station',
                'quickbooks_id': 'QB123456'
            },
            {
                'expense_date': (datetime.now() - timedelta(days=10)).date().isoformat(),
                'category': 'maintenance',
                'description': 'Oil change and inspection',
                'amount': 89.99,
                'vendor': 'Jiffy Lube',
                'quickbooks_id': 'QB123457'
            }
        ]
        
        return jsonify({
            'success': True,
            'vehicle_id': data['fleet_vehicle_id'],
            'synced_expenses': synced_expenses,
            'sync_period_days': sync_period,
            'message': f'Synced {len(synced_expenses)} expenses from QuickBooks'
        })
    
    except Exception as e:
        logger.error(f"Error syncing QuickBooks expenses: {e}")
        return jsonify({'error': 'Failed to sync QuickBooks expenses'}), 500

# ============================================================================
# CORPORATE CREDIT CARD INTEGRATION ENDPOINTS
# ============================================================================

@business_integrations_api.route('/api/professional/integrations/credit-card/connect', methods=['POST'])
@require_auth
@require_csrf
def connect_credit_card():
    """
    Connect corporate credit card for automatic transaction categorization
    
    Request Body:
    {
        "card_provider": "string (chase|amex|capital_one|etc)",
        "account_number": "string (last 4 digits)",
        "api_credentials": {
            "client_id": "string",
            "client_secret": "string"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['card_provider', 'account_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # In a real implementation, you would:
        # 1. Validate the credit card API credentials
        # 2. Store the connection securely
        # 3. Test the connection
        
        connection_status = {
            'connected': True,
            'card_provider': data['card_provider'],
            'account_number': f"****{data['account_number'][-4:]}",
            'last_sync': datetime.utcnow().isoformat(),
            'sync_status': 'active'
        }
        
        return jsonify({
            'success': True,
            'connection': connection_status,
            'message': 'Corporate credit card connected successfully'
        })
    
    except Exception as e:
        logger.error(f"Error connecting credit card: {e}")
        return jsonify({'error': 'Failed to connect credit card'}), 500

@business_integrations_api.route('/api/professional/integrations/credit-card/categorize', methods=['POST'])
@require_auth
@require_csrf
def categorize_credit_card_transactions():
    """
    Automatically categorize credit card transactions for vehicle expenses
    
    Request Body:
    {
        "fleet_vehicle_id": "integer",
        "transactions": [
            {
                "transaction_id": "string",
                "date": "date",
                "description": "string",
                "amount": "decimal",
                "merchant": "string"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        if 'fleet_vehicle_id' not in data or 'transactions' not in data:
            return jsonify({'error': 'fleet_vehicle_id and transactions are required'}), 400
        
        # Verify vehicle ownership
        vehicle = FleetVehicle.query.filter_by(id=data['fleet_vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Fleet vehicle not found'}), 404
        
        categorized_transactions = []
        
        # Categorize each transaction
        for transaction in data['transactions']:
            # Simple categorization logic (in real implementation, use ML/AI)
            description = transaction.get('description', '').lower()
            merchant = transaction.get('merchant', '').lower()
            
            category = 'other'
            is_business = False
            
            # Fuel/gas stations
            if any(keyword in description or keyword in merchant for keyword in ['gas', 'fuel', 'shell', 'exxon', 'chevron', 'bp', 'mobil']):
                category = 'fuel'
                is_business = True
            
            # Auto parts and maintenance
            elif any(keyword in description or keyword in merchant for keyword in ['auto', 'repair', 'maintenance', 'oil', 'tire', 'brake', 'mechanic']):
                category = 'maintenance'
                is_business = True
            
            # Insurance
            elif any(keyword in description or keyword in merchant for keyword in ['insurance', 'geico', 'progressive', 'state farm']):
                category = 'insurance'
                is_business = True
            
            # Parking and tolls
            elif any(keyword in description or keyword in merchant for keyword in ['parking', 'toll', 'garage']):
                category = 'parking_tolls'
                is_business = True
            
            # Calculate business percentage based on vehicle's business use
            business_percentage = vehicle.business_use_percentage
            deductible_amount = float(transaction.get('amount', 0)) * (business_percentage / 100) if is_business else 0
            
            categorized_transactions.append({
                'transaction_id': transaction.get('transaction_id'),
                'date': transaction.get('date'),
                'description': transaction.get('description'),
                'amount': float(transaction.get('amount', 0)),
                'merchant': transaction.get('merchant'),
                'category': category,
                'is_business': is_business,
                'business_percentage': business_percentage,
                'deductible_amount': deductible_amount
            })
        
        return jsonify({
            'success': True,
            'vehicle_id': data['fleet_vehicle_id'],
            'categorized_transactions': categorized_transactions,
            'summary': {
                'total_transactions': len(categorized_transactions),
                'business_transactions': len([t for t in categorized_transactions if t['is_business']]),
                'total_deductible_amount': sum(t['deductible_amount'] for t in categorized_transactions)
            },
            'message': 'Transactions categorized successfully'
        })
    
    except Exception as e:
        logger.error(f"Error categorizing credit card transactions: {e}")
        return jsonify({'error': 'Failed to categorize transactions'}), 500

# ============================================================================
# HR SYSTEM INTEGRATION ENDPOINTS
# ============================================================================

@business_integrations_api.route('/api/professional/integrations/hr/connect', methods=['POST'])
@require_auth
@require_csrf
def connect_hr_system():
    """
    Connect to HR system for employee vehicle benefits management
    
    Request Body:
    {
        "hr_system": "string (workday|bamboo|adp|etc)",
        "company_id": "string",
        "api_credentials": {
            "client_id": "string",
            "client_secret": "string"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['hr_system', 'company_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # In a real implementation, you would:
        # 1. Validate the HR system API credentials
        # 2. Store the connection securely
        # 3. Test the connection
        
        connection_status = {
            'connected': True,
            'hr_system': data['hr_system'],
            'company_id': data['company_id'],
            'last_sync': datetime.utcnow().isoformat(),
            'sync_status': 'active'
        }
        
        return jsonify({
            'success': True,
            'connection': connection_status,
            'message': 'HR system connected successfully'
        })
    
    except Exception as e:
        logger.error(f"Error connecting HR system: {e}")
        return jsonify({'error': 'Failed to connect HR system'}), 500

@business_integrations_api.route('/api/professional/integrations/hr/employee-vehicles', methods=['GET'])
@require_auth
def get_employee_vehicles():
    """
    Get employee vehicle assignments and benefits from HR system
    
    Query Parameters:
    - department: Filter by department
    - employee_id: Filter by specific employee
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        department = request.args.get('department')
        employee_id = request.args.get('employee_id')
        
        # In a real implementation, you would:
        # 1. Connect to HR system API
        # 2. Fetch employee vehicle assignments
        # 3. Return structured data
        
        # For now, simulate employee vehicle data
        employee_vehicles = [
            {
                'employee_id': 'EMP001',
                'employee_name': 'John Smith',
                'department': 'Sales',
                'vehicle_assignment': 'Company Car',
                'vehicle_id': 1,
                'monthly_allowance': 500.00,
                'benefit_type': 'company_vehicle',
                'start_date': '2024-01-01',
                'end_date': None
            },
            {
                'employee_id': 'EMP002',
                'employee_name': 'Jane Doe',
                'department': 'Marketing',
                'vehicle_assignment': 'Mileage Reimbursement',
                'vehicle_id': None,
                'monthly_allowance': 0.00,
                'benefit_type': 'mileage_reimbursement',
                'start_date': '2024-01-01',
                'end_date': None
            }
        ]
        
        # Apply filters
        if department:
            employee_vehicles = [ev for ev in employee_vehicles if ev['department'] == department]
        
        if employee_id:
            employee_vehicles = [ev for ev in employee_vehicles if ev['employee_id'] == employee_id]
        
        return jsonify({
            'success': True,
            'employee_vehicles': employee_vehicles,
            'total_count': len(employee_vehicles),
            'message': 'Employee vehicle assignments retrieved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error getting employee vehicles: {e}")
        return jsonify({'error': 'Failed to retrieve employee vehicles'}), 500

# ============================================================================
# INSURANCE POLICY MANAGEMENT ENDPOINTS
# ============================================================================

@business_integrations_api.route('/api/professional/integrations/insurance/connect', methods=['POST'])
@require_auth
@require_csrf
def connect_insurance_provider():
    """
    Connect to insurance provider for policy management
    
    Request Body:
    {
        "insurance_provider": "string (geico|progressive|state_farm|etc)",
        "policy_number": "string",
        "api_credentials": {
            "client_id": "string",
            "client_secret": "string"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        user_id = get_current_user_id()
        
        # Validate required fields
        required_fields = ['insurance_provider', 'policy_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # In a real implementation, you would:
        # 1. Validate the insurance provider API credentials
        # 2. Store the connection securely
        # 3. Test the connection
        
        connection_status = {
            'connected': True,
            'insurance_provider': data['insurance_provider'],
            'policy_number': data['policy_number'],
            'last_sync': datetime.utcnow().isoformat(),
            'sync_status': 'active'
        }
        
        return jsonify({
            'success': True,
            'connection': connection_status,
            'message': 'Insurance provider connected successfully'
        })
    
    except Exception as e:
        logger.error(f"Error connecting insurance provider: {e}")
        return jsonify({'error': 'Failed to connect insurance provider'}), 500

@business_integrations_api.route('/api/professional/integrations/insurance/policies', methods=['GET'])
@require_auth
def get_insurance_policies():
    """
    Get insurance policies and coverage details for fleet vehicles
    
    Query Parameters:
    - fleet_vehicle_id: Filter by specific vehicle
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        fleet_vehicle_id = request.args.get('fleet_vehicle_id')
        
        # In a real implementation, you would:
        # 1. Connect to insurance provider API
        # 2. Fetch policy details
        # 3. Return structured data
        
        # For now, simulate insurance policy data
        policies = [
            {
                'policy_id': 'POL001',
                'fleet_vehicle_id': 1,
                'vehicle_info': '2022 Toyota Camry',
                'coverage_type': 'comprehensive',
                'premium_monthly': 125.50,
                'deductible': 500.00,
                'coverage_limits': {
                    'liability': 100000,
                    'collision': 50000,
                    'comprehensive': 50000
                },
                'effective_date': '2024-01-01',
                'expiration_date': '2024-12-31',
                'status': 'active'
            },
            {
                'policy_id': 'POL002',
                'fleet_vehicle_id': 2,
                'vehicle_info': '2023 Ford F-150',
                'coverage_type': 'commercial',
                'premium_monthly': 180.75,
                'deductible': 1000.00,
                'coverage_limits': {
                    'liability': 250000,
                    'collision': 75000,
                    'comprehensive': 75000
                },
                'effective_date': '2024-01-01',
                'expiration_date': '2024-12-31',
                'status': 'active'
            }
        ]
        
        # Apply filters
        if fleet_vehicle_id:
            policies = [p for p in policies if p['fleet_vehicle_id'] == int(fleet_vehicle_id)]
        
        return jsonify({
            'success': True,
            'policies': policies,
            'total_count': len(policies),
            'message': 'Insurance policies retrieved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error getting insurance policies: {e}")
        return jsonify({'error': 'Failed to retrieve insurance policies'}), 500

# ============================================================================
# INTEGRATION STATUS ENDPOINTS
# ============================================================================

@business_integrations_api.route('/api/professional/integrations/status', methods=['GET'])
@require_auth
def get_integration_status():
    """
    Get status of all business integrations
    """
    try:
        user_id = get_current_user_id()
        
        # In a real implementation, you would check actual connection statuses
        integration_status = {
            'quickbooks': {
                'connected': True,
                'last_sync': '2024-01-15T10:30:00Z',
                'sync_status': 'active',
                'expenses_synced': 45
            },
            'credit_card': {
                'connected': True,
                'last_sync': '2024-01-15T10:25:00Z',
                'sync_status': 'active',
                'transactions_categorized': 23
            },
            'hr_system': {
                'connected': True,
                'last_sync': '2024-01-15T10:20:00Z',
                'sync_status': 'active',
                'employees_synced': 12
            },
            'insurance': {
                'connected': True,
                'last_sync': '2024-01-15T10:15:00Z',
                'sync_status': 'active',
                'policies_synced': 3
            }
        }
        
        return jsonify({
            'success': True,
            'integrations': integration_status,
            'overall_status': 'healthy',
            'message': 'Integration status retrieved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        return jsonify({'error': 'Failed to retrieve integration status'}), 500

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@business_integrations_api.route('/api/professional/integrations/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for business integrations API
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
                'business_integrations_api': 'active'
            },
            'message': 'Business integrations API is healthy'
        })
    
    except Exception as e:
        logger.error(f"Business integrations health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'message': 'Business integrations API health check failed'
        }), 500
