#!/usr/bin/env python3
"""
Vehicle Setup API Endpoints for Mingus Application
Provides endpoints for vehicle setup, VIN lookup, and MSA mapping
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
from typing import Dict, Any, Optional
import traceback

from sqlalchemy.exc import IntegrityError

# Import existing services
from backend.auth.decorators import get_current_jwt_user, require_auth, require_csrf
from backend.models.database import db
from backend.models.vehicle_models import Vehicle
from backend.services.vin_lookup_service import VINLookupService, VINValidationError, VINAPIError
from backend.services.gas_price_service import GasPriceService
from msa_mapping_service import ZipcodeToMSAMapper
from backend.utils.validation import APIValidator

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
vehicle_setup_api = Blueprint('vehicle_setup_api', __name__)

# Initialize services
vin_service = VINLookupService()
gas_price_service = GasPriceService()
msa_mapper = ZipcodeToMSAMapper()

# ============================================================================
# VEHICLE SETUP ENDPOINTS
# ============================================================================

@vehicle_setup_api.route('/api/vehicle-setup/vin-lookup', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def lookup_vin_for_setup():
    """
    Lookup vehicle information by VIN for vehicle setup
    
    Request Body:
    {
        "vin": "string",
        "use_cache": "boolean (optional, default: true)"
    }
    
    Response:
    {
        "success": true,
        "vehicle_info": {
            "vin": "string",
            "year": "integer",
            "make": "string",
            "model": "string",
            "trim": "string",
            "engine": "string",
            "fuel_type": "string",
            "body_class": "string",
            "drive_type": "string",
            "transmission": "string",
            "doors": "integer",
            "windows": "integer",
            "series": "string",
            "plant_city": "string",
            "plant_state": "string",
            "plant_country": "string",
            "manufacturer": "string",
            "model_year": "integer",
            "vehicle_type": "string",
            "source": "string",
            "lookup_timestamp": "string",
            "error_code": "string",
            "error_text": "string"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'vin' not in data:
            return jsonify({'error': 'VIN is required'}), 400
        
        vin = data['vin'].strip().upper()
        use_cache = data.get('use_cache', True)
        
        # Validate VIN format
        if not vin_service.validate_vin(vin):
            return jsonify({'error': 'Invalid VIN format'}), 400
        
        # Lookup VIN
        vehicle_info = vin_service.lookup_vin(vin, use_cache=use_cache)
        
        # Convert to dictionary for JSON response
        response_data = {
            'vin': vehicle_info.vin,
            'year': vehicle_info.year,
            'make': vehicle_info.make,
            'model': vehicle_info.model,
            'trim': vehicle_info.trim,
            'engine': vehicle_info.engine,
            'fuel_type': vehicle_info.fuel_type,
            'body_class': vehicle_info.body_class,
            'drive_type': vehicle_info.drive_type,
            'transmission': vehicle_info.transmission,
            'doors': vehicle_info.doors,
            'windows': vehicle_info.windows,
            'series': vehicle_info.series,
            'plant_city': vehicle_info.plant_city,
            'plant_state': vehicle_info.plant_state,
            'plant_country': vehicle_info.plant_country,
            'manufacturer': vehicle_info.manufacturer,
            'model_year': vehicle_info.model_year,
            'vehicle_type': vehicle_info.vehicle_type,
            'source': vehicle_info.source,
            'lookup_timestamp': vehicle_info.lookup_timestamp.isoformat() if vehicle_info.lookup_timestamp else None,
            'error_code': vehicle_info.error_code,
            'error_text': vehicle_info.error_text
        }
        
        return jsonify({
            'success': True,
            'vehicle_info': response_data
        })
        
    except VINValidationError as e:
        logger.warning(f"VIN validation error: {e}")
        return jsonify({'error': f'Invalid VIN: {str(e)}'}), 400
        
    except VINAPIError as e:
        logger.warning(f"VIN API error: {e}")
        return jsonify({'error': 'VIN lookup service temporarily unavailable'}), 503
        
    except Exception as e:
        logger.error(f"VIN lookup error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'VIN lookup failed'}), 500

@vehicle_setup_api.route('/api/vehicle-setup/zipcode-to-msa', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def map_zipcode_to_msa():
    """
    Map ZIP code to MSA for vehicle setup
    
    Request Body:
    {
        "zipcode": "string"
    }
    
    Response:
    {
        "success": true,
        "msa_info": {
            "msa": "string",
            "distance": "float",
            "coordinates": {
                "latitude": "float",
                "longitude": "float"
            },
            "error": "string (optional)"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'zipcode' not in data:
            return jsonify({'error': 'ZIP code is required'}), 400
        
        zipcode = data['zipcode'].strip()
        
        # Validate ZIP code format
        if not zipcode or len(zipcode) != 5 or not zipcode.isdigit():
            return jsonify({'error': 'Invalid ZIP code format'}), 400
        
        # Map ZIP code to MSA
        msa_result = msa_mapper.get_msa_for_zipcode(zipcode)
        
        # Prepare response
        response_data = {
            'msa': msa_result['msa'],
            'distance': msa_result['distance'],
            'coordinates': msa_result.get('coordinates'),
            'error': msa_result.get('error')
        }
        
        return jsonify({
            'success': True,
            'msa_info': response_data
        })
        
    except Exception as e:
        logger.error(f"ZIP code to MSA mapping error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'MSA mapping failed'}), 500

@vehicle_setup_api.route('/api/vehicle-setup/submit', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def submit_vehicle_setup():
    """
    Submit completed vehicle setup data
    
    Request Body:
    {
        "vin": "string (optional)",
        "year": "integer",
        "make": "string",
        "model": "string",
        "trim": "string (optional)",
        "current_mileage": "integer",
        "monthly_miles": "integer",
        "zipcode": "string",
        "msa": "string (optional)",
        "use_vin_lookup": "boolean"
    }
    
    Response:
    {
        "success": true,
        "vehicle_id": "integer",
        "message": "string",
        "msa_info": {
            "msa": "string",
            "pricing_multiplier": "float"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        user = get_current_jwt_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db_user_id = int(user.id)
        
        # Validate required fields
        required_fields = ['year', 'make', 'model', 'current_mileage', 'monthly_miles', 'zipcode']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate and sanitize data
        sanitized_data = {}
        
        # Validate year
        try:
            year = int(data['year'])
            if year < 1900 or year > 2030:
                return jsonify({'error': 'Invalid year'}), 400
            sanitized_data['year'] = year
        except (ValueError, TypeError):
            return jsonify({'error': 'Year must be a valid integer'}), 400
        
        # Validate and sanitize string fields
        string_fields = ['make', 'model', 'trim', 'zipcode', 'msa']
        for field in string_fields:
            if field in data and data[field]:
                sanitized_value = APIValidator.sanitize_string(data[field])
                if not sanitized_value:
                    return jsonify({'error': f'Invalid {field}'}), 400
                sanitized_data[field] = sanitized_value
        
        # Validate mileage fields
        try:
            current_mileage = int(data['current_mileage'])
            monthly_miles = int(data['monthly_miles'])
            
            if current_mileage < 0 or monthly_miles < 0:
                return jsonify({'error': 'Mileage values must be non-negative'}), 400
            if current_mileage > 999999 or monthly_miles > 10000:
                return jsonify({'error': 'Mileage values are too high'}), 400
                
            sanitized_data['current_mileage'] = current_mileage
            sanitized_data['monthly_miles'] = monthly_miles
        except (ValueError, TypeError):
            return jsonify({'error': 'Mileage values must be valid integers'}), 400
        
        # Validate VIN if provided
        if 'vin' in data and data['vin']:
            vin = data['vin'].strip().upper()
            if not vin_service.validate_vin(vin):
                return jsonify({'error': 'Invalid VIN format'}), 400
            sanitized_data['vin'] = vin
        
        # Validate ZIP code format
        zipcode = sanitized_data['zipcode']
        if len(zipcode) != 5 or not zipcode.isdigit():
            return jsonify({'error': 'ZIP code must be 5 digits'}), 400
        
        # Get MSA information if not provided
        if 'msa' not in sanitized_data or not sanitized_data['msa']:
            msa_result = msa_mapper.get_msa_for_zipcode(zipcode)
            sanitized_data['msa'] = msa_result['msa']
        
        # Get pricing multiplier for the MSA
        msa_name = sanitized_data['msa']
        pricing_multiplier = msa_mapper.get_pricing_multiplier(zipcode)

        trim_val = sanitized_data.get('trim') or None
        vin_val = sanitized_data.get('vin')

        vehicle = Vehicle(
            user_id=db_user_id,
            vin=vin_val,
            year=sanitized_data['year'],
            make=sanitized_data['make'],
            model=sanitized_data['model'],
            trim=trim_val,
            current_mileage=sanitized_data['current_mileage'],
            monthly_miles=sanitized_data['monthly_miles'],
            user_zipcode=zipcode,
            assigned_msa=msa_name,
        )
        db.session.add(vehicle)
        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            logger.warning("vehicle setup insert conflict: %s", ie)
            return jsonify({'error': 'Could not save vehicle (duplicate VIN or data conflict)'}), 409

        return jsonify({
            'success': True,
            'vehicle_id': vehicle.id,
            'message': 'Vehicle setup completed successfully',
            'msa_info': {
                'msa': msa_name,
                'pricing_multiplier': pricing_multiplier
            }
        })
        
    except Exception as e:
        logger.error(f"Vehicle setup submission error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Vehicle setup failed'}), 500

@vehicle_setup_api.route('/api/vehicle-setup/popular-makes', methods=['GET'])
@cross_origin()
def get_popular_makes():
    """
    Get list of popular vehicle makes for the target demographic
    
    Response:
    {
        "success": true,
        "makes": ["string"]
    }
    """
    try:
        # Popular makes for target demographic
        popular_makes = [
            'Honda', 'Toyota', 'Nissan', 'Ford', 'Chevrolet', 'BMW', 'Mercedes-Benz', 
            'Audi', 'Lexus', 'Acura', 'Infiniti', 'Hyundai', 'Kia', 'Mazda', 'Subaru'
        ]
        
        return jsonify({
            'success': True,
            'makes': popular_makes
        })
        
    except Exception as e:
        logger.error(f"Error getting popular makes: {e}")
        return jsonify({'error': 'Failed to get popular makes'}), 500

@vehicle_setup_api.route('/api/vehicle-setup/popular-models/<make>', methods=['GET'])
@cross_origin()
def get_popular_models(make):
    """
    Get list of popular models for a specific make
    
    Response:
    {
        "success": true,
        "models": ["string"]
    }
    """
    try:
        # Popular models by make for target demographic
        popular_models = {
            'Honda': ['Civic', 'Accord', 'CR-V', 'Pilot', 'HR-V', 'Passport'],
            'Toyota': ['Camry', 'Corolla', 'RAV4', 'Highlander', 'Prius', '4Runner'],
            'Nissan': ['Altima', 'Sentra', 'Rogue', 'Murano', 'Pathfinder', 'Maxima'],
            'Ford': ['F-150', 'Explorer', 'Escape', 'Mustang', 'Edge', 'Expedition'],
            'Chevrolet': ['Silverado', 'Equinox', 'Malibu', 'Tahoe', 'Suburban', 'Camaro'],
            'BMW': ['3 Series', '5 Series', 'X3', 'X5', 'X1', '7 Series'],
            'Mercedes-Benz': ['C-Class', 'E-Class', 'GLC', 'GLE', 'A-Class', 'S-Class'],
            'Audi': ['A4', 'A6', 'Q5', 'Q7', 'A3', 'Q3'],
            'Lexus': ['ES', 'RX', 'IS', 'NX', 'GX', 'LS'],
            'Acura': ['TLX', 'RDX', 'MDX', 'ILX', 'NSX', 'RLX'],
            'Infiniti': ['Q50', 'QX60', 'QX80', 'Q60', 'QX50', 'G37'],
            'Hyundai': ['Elantra', 'Sonata', 'Tucson', 'Santa Fe', 'Palisade', 'Veloster'],
            'Kia': ['Optima', 'Sorento', 'Sportage', 'Telluride', 'Forte', 'Stinger'],
            'Mazda': ['CX-5', 'Mazda3', 'CX-9', 'Mazda6', 'CX-3', 'MX-5 Miata'],
            'Subaru': ['Outback', 'Forester', 'Impreza', 'Legacy', 'Ascent', 'WRX']
        }
        
        make_models = popular_models.get(make, [])
        
        return jsonify({
            'success': True,
            'models': make_models
        })
        
    except Exception as e:
        logger.error(f"Error getting popular models for {make}: {e}")
        return jsonify({'error': 'Failed to get popular models'}), 500

@vehicle_setup_api.route('/api/vehicle-setup/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check for vehicle setup services
    
    Response:
    {
        "success": true,
        "services": {
            "vin_lookup": "string",
            "msa_mapping": "string",
            "gas_price": "string"
        }
    }
    """
    try:
        # Check VIN service status
        vin_status = "available" if vin_service.service_status.value == "available" else "unavailable"
        
        # Check MSA mapping service
        msa_status = "available"  # MSA mapping is always available (no external dependencies)
        
        # Check gas price service
        gas_status = "available"  # Gas price service is always available
        
        return jsonify({
            'success': True,
            'services': {
                'vin_lookup': vin_status,
                'msa_mapping': msa_status,
                'gas_price': gas_status
            }
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'error': 'Health check failed'}), 500
