#!/usr/bin/env python3
"""
Mingus Gas Price API Endpoints

REST API endpoints for gas price management and retrieval.
Integrates with the gas price service and MSA mapping service.

Endpoints:
- GET /api/gas-prices/zipcode/{zipcode} - Get gas price by zipcode
- GET /api/gas-prices/msa/{msa_name} - Get gas price by MSA
- GET /api/gas-prices/all - Get all gas prices
- POST /api/gas-prices/update - Trigger gas price update
- GET /api/gas-prices/status - Get service status
- GET /api/gas-prices/history/{msa_name} - Get price history
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.exceptions import BadRequest, NotFound

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.gas_price_service import GasPriceService
from tasks.gas_price_tasks import (
    update_daily_gas_prices, 
    update_specific_msa_price,
    get_gas_price_by_zipcode_task,
    health_check_gas_price_service
)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
gas_price_api = Blueprint('gas_price_api', __name__)

# Initialize gas price service
gas_service = GasPriceService()

# ============================================================================
# GAS PRICE RETRIEVAL ENDPOINTS
# ============================================================================

@gas_price_api.route('/api/gas-prices/zipcode/<zipcode>', methods=['GET'])
@cross_origin()
def get_gas_price_by_zipcode(zipcode):
    """
    Get gas price for a specific zipcode using MSA mapping.
    
    Args:
        zipcode: 5-digit US zipcode string
        
    Returns:
        JSON response with gas price information
    """
    try:
        # Validate zipcode format
        if not zipcode or not zipcode.isdigit() or len(zipcode) != 5:
            return jsonify({
                'success': False,
                'error': 'Invalid zipcode format. Must be 5 digits.',
                'zipcode': zipcode
            }), 400
        
        # Get gas price information
        result = gas_service.get_gas_price_by_zipcode(zipcode)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to retrieve gas price'),
                'zipcode': zipcode
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting gas price for zipcode {zipcode}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'zipcode': zipcode
        }), 500

@gas_price_api.route('/api/gas-prices/msa/<msa_name>', methods=['GET'])
@cross_origin()
def get_gas_price_by_msa(msa_name):
    """
    Get gas price for a specific MSA.
    
    Args:
        msa_name: Name of the MSA
        
    Returns:
        JSON response with gas price information
    """
    try:
        # Get gas price for MSA
        gas_price = gas_service._get_gas_price_for_msa(msa_name)
        
        if not gas_price:
            return jsonify({
                'success': False,
                'error': f'No gas price data found for MSA: {msa_name}',
                'msa_name': msa_name
            }), 404
        
        return jsonify({
            'success': True,
            'data': gas_price.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting gas price for MSA {msa_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'msa_name': msa_name
        }), 500

@gas_price_api.route('/api/gas-prices/all', methods=['GET'])
@cross_origin()
def get_all_gas_prices():
    """
    Get all current gas prices for all MSAs.
    
    Returns:
        JSON response with all gas prices
    """
    try:
        # Get all gas prices
        prices = gas_service.get_all_gas_prices()
        
        return jsonify({
            'success': True,
            'data': {
                'gas_prices': prices,
                'total_count': len(prices),
                'retrieved_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all gas prices: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ============================================================================
# GAS PRICE UPDATE ENDPOINTS
# ============================================================================

@gas_price_api.route('/api/gas-prices/update', methods=['POST'])
@cross_origin()
def trigger_gas_price_update():
    """
    Trigger a gas price update for all MSAs.
    
    Body:
        force_update: boolean (optional) - Force update even if recently updated
        
    Returns:
        JSON response with update results
    """
    try:
        data = request.get_json() or {}
        force_update = data.get('force_update', False)
        
        # Trigger async update task
        task = update_daily_gas_prices.delay(force_update=force_update)
        
        return jsonify({
            'success': True,
            'message': 'Gas price update task started',
            'task_id': task.id,
            'force_update': force_update,
            'started_at': datetime.utcnow().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error triggering gas price update: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start gas price update'
        }), 500

@gas_price_api.route('/api/gas-prices/msa/<msa_name>/update', methods=['POST'])
@cross_origin()
def update_msa_gas_price(msa_name):
    """
    Update gas price for a specific MSA.
    
    Args:
        msa_name: Name of the MSA to update
        
    Body:
        price: float - New gas price
        data_source: string (optional) - Source of the price data
        
    Returns:
        JSON response with update results
    """
    try:
        data = request.get_json()
        
        if not data or 'price' not in data:
            return jsonify({
                'success': False,
                'error': 'Price is required',
                'msa_name': msa_name
            }), 400
        
        price = data['price']
        data_source = data.get('data_source', 'Manual')
        
        # Validate price
        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price must be non-negative")
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid price format',
                'msa_name': msa_name
            }), 400
        
        # Trigger async update task
        task = update_specific_msa_price.delay(msa_name, price, data_source)
        
        return jsonify({
            'success': True,
            'message': f'Gas price update task started for MSA: {msa_name}',
            'task_id': task.id,
            'msa_name': msa_name,
            'new_price': price,
            'data_source': data_source,
            'started_at': datetime.utcnow().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error updating gas price for MSA {msa_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start MSA price update',
            'msa_name': msa_name
        }), 500

# ============================================================================
# STATUS AND MONITORING ENDPOINTS
# ============================================================================

@gas_price_api.route('/api/gas-prices/status', methods=['GET'])
@cross_origin()
def get_gas_price_service_status():
    """
    Get gas price service status and health information.
    
    Returns:
        JSON response with service status
    """
    try:
        # Get service status
        status = gas_service.get_service_status()
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting gas price service status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get service status'
        }), 500

@gas_price_api.route('/api/gas-prices/health-check', methods=['POST'])
@cross_origin()
def trigger_health_check():
    """
    Trigger a health check for the gas price service.
    
    Returns:
        JSON response with health check results
    """
    try:
        # Trigger async health check task
        task = health_check_gas_price_service.delay()
        
        return jsonify({
            'success': True,
            'message': 'Health check task started',
            'task_id': task.id,
            'started_at': datetime.utcnow().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error triggering health check: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start health check'
        }), 500

# ============================================================================
# PRICE HISTORY ENDPOINTS
# ============================================================================

@gas_price_api.route('/api/gas-prices/history/<msa_name>', methods=['GET'])
@cross_origin()
def get_gas_price_history(msa_name):
    """
    Get gas price history for a specific MSA.
    
    Args:
        msa_name: Name of the MSA
        
    Query Parameters:
        days: int (optional) - Number of days of history to retrieve (default: 30)
        
    Returns:
        JSON response with price history
    """
    try:
        # Get days parameter
        days = request.args.get('days', 30, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({
                'success': False,
                'error': 'Days must be between 1 and 365',
                'msa_name': msa_name
            }), 400
        
        # Get price history
        history = gas_service.get_gas_price_history(msa_name, days)
        
        if not history:
            return jsonify({
                'success': False,
                'error': f'No price history found for MSA: {msa_name}',
                'msa_name': msa_name
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'msa_name': msa_name,
                'history': history,
                'days_requested': days,
                'days_returned': len(history),
                'retrieved_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting price history for MSA {msa_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'msa_name': msa_name
        }), 500

# ============================================================================
# TASK STATUS ENDPOINTS
# ============================================================================

@gas_price_api.route('/api/gas-prices/task/<task_id>/status', methods=['GET'])
@cross_origin()
def get_task_status(task_id):
    """
    Get status of a gas price task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        JSON response with task status
    """
    try:
        from tasks.gas_price_tasks import celery_app
        
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'status': 'Task is waiting to be processed'
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'current': task_result.info.get('current', 0),
                'total': task_result.info.get('total', 1),
                'status': task_result.info.get('status', '')
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'result': task_result.result,
                'status': 'Task completed successfully'
            }
        else:  # FAILURE or other states
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'error': str(task_result.info),
                'status': 'Task failed'
            }
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get task status',
            'task_id': task_id
        }), 500

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@gas_price_api.route('/api/gas-prices/msa-list', methods=['GET'])
@cross_origin()
def get_msa_list():
    """
    Get list of supported MSAs.
    
    Returns:
        JSON response with list of MSAs
    """
    try:
        msas = gas_service.TARGET_MSAS + ['National Average']
        
        return jsonify({
            'success': True,
            'data': {
                'msas': msas,
                'total_count': len(msas),
                'target_msas': gas_service.TARGET_MSAS,
                'fallback_available': True
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting MSA list: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get MSA list'
        }), 500

@gas_price_api.route('/api/gas-prices/fallback-prices', methods=['GET'])
@cross_origin()
def get_fallback_prices():
    """
    Get fallback gas prices used when external data is unavailable.
    
    Returns:
        JSON response with fallback prices
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'fallback_prices': gas_service.FALLBACK_PRICES,
                'last_updated': datetime.utcnow().isoformat(),
                'note': 'These are fallback prices used when external data sources are unavailable'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting fallback prices: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get fallback prices'
        }), 500
