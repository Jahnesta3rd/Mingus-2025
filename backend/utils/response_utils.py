"""
Response Utilities
Standardized API response and error handling utilities
"""

from flask import jsonify
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def api_response(message: str, data: Optional[Dict[str, Any]] = None, 
                status_code: int = 200, meta: Optional[Dict[str, Any]] = None) -> tuple:
    """
    Create a standardized API response
    
    Args:
        message: Response message
        data: Response data
        status_code: HTTP status code
        meta: Additional metadata
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if meta is not None:
        response['meta'] = meta
    
    return jsonify(response), status_code

def error_response(error: str, message: Optional[str] = None, 
                  status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> tuple:
    """
    Create a standardized error response
    
    Args:
        error: Error type/name
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'success': False,
        'error': error,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message is not None:
        response['message'] = message
    
    if details is not None:
        response['details'] = details
    
    return jsonify(response), status_code

def paginated_response(data: list, page: int, per_page: int, total_count: int,
                      message: str = "Data retrieved successfully") -> tuple:
    """
    Create a paginated response
    
    Args:
        data: List of data items
        page: Current page number
        per_page: Items per page
        total_count: Total number of items
        message: Response message
        
    Returns:
        Tuple of (response, status_code)
    """
    total_pages = (total_count + per_page - 1) // per_page
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_count': total_count,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }
    
    return api_response(
        message=message,
        data={'items': data},
        meta={'pagination': pagination}
    )

def validation_error_response(errors: list, message: str = "Validation failed") -> tuple:
    """
    Create a validation error response
    
    Args:
        errors: List of validation errors
        message: Error message
        
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        error='ValidationError',
        message=message,
        status_code=400,
        details={'validation_errors': errors}
    )

def not_found_response(resource: str, resource_id: Optional[Union[str, int]] = None) -> tuple:
    """
    Create a not found response
    
    Args:
        resource: Resource type name
        resource_id: Resource identifier
        
    Returns:
        Tuple of (response, status_code)
    """
    message = f"{resource} not found"
    if resource_id is not None:
        message += f" with id: {resource_id}"
    
    return error_response(
        error='NotFoundError',
        message=message,
        status_code=404
    )

def unauthorized_response(message: str = "Authentication required") -> tuple:
    """
    Create an unauthorized response
    
    Args:
        message: Error message
        
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        error='UnauthorizedError',
        message=message,
        status_code=401
    )

def forbidden_response(message: str = "Access denied") -> tuple:
    """
    Create a forbidden response
    
    Args:
        message: Error message
        
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        error='ForbiddenError',
        message=message,
        status_code=403
    )

def rate_limit_response(retry_after: int, limit: int) -> tuple:
    """
    Create a rate limit response
    
    Args:
        retry_after: Seconds to wait before retrying
        limit: Rate limit value
        
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        error='RateLimitError',
        message=f"Rate limit exceeded. Limit: {limit} requests",
        status_code=429,
        details={'retry_after': retry_after, 'limit': limit}
    )

def server_error_response(message: str = "Internal server error", 
                         details: Optional[str] = None) -> tuple:
    """
    Create a server error response
    
    Args:
        message: Error message
        details: Additional error details
        
    Returns:
        Tuple of (response, status_code)
    """
    error_details = None
    if details:
        error_details = {'details': details}
    
    return error_response(
        error='ServerError',
        message=message,
        status_code=500,
        details=error_details
    )

def success_response(data: Optional[Dict[str, Any]] = None, 
                    message: str = "Operation completed successfully") -> tuple:
    """
    Create a success response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Tuple of (response, status_code)
    """
    return api_response(message=message, data=data, status_code=200)

def created_response(data: Optional[Dict[str, Any]] = None, 
                    message: str = "Resource created successfully") -> tuple:
    """
    Create a created response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Tuple of (response, status_code)
    """
    return api_response(message=message, data=data, status_code=201)

def updated_response(data: Optional[Dict[str, Any]] = None, 
                    message: str = "Resource updated successfully") -> tuple:
    """
    Create an updated response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Tuple of (response, status_code)
    """
    return api_response(message=message, data=data, status_code=200)

def deleted_response(message: str = "Resource deleted successfully") -> tuple:
    """
    Create a deleted response
    
    Args:
        message: Success message
        
    Returns:
        Tuple of (response, status_code)
    """
    return api_response(message=message, status_code=204)

def no_content_response() -> tuple:
    """
    Create a no content response
    
    Returns:
        Tuple of (response, status_code)
    """
    return jsonify({}), 204

def health_check_response(services: Optional[Dict[str, bool]] = None) -> tuple:
    """
    Create a health check response
    
    Args:
        services: Dictionary of service health status
        
    Returns:
        Tuple of (response, status_code)
    """
    data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if services:
        data['services'] = services
        # Check if all services are healthy
        if not all(services.values()):
            data['status'] = 'degraded'
    
    return api_response(
        message="Service is healthy",
        data=data,
        status_code=200
    )

def file_response(file_data: bytes, filename: str, content_type: str) -> tuple:
    """
    Create a file download response
    
    Args:
        file_data: File content as bytes
        filename: Name of the file
        content_type: MIME type of the file
        
    Returns:
        Tuple of (response, status_code)
    """
    from flask import Response
    
    response = Response(file_data, content_type=content_type)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Length'] = len(file_data)
    
    return response, 200

def json_file_response(data: Dict[str, Any], filename: str) -> tuple:
    """
    Create a JSON file download response
    
    Args:
        data: JSON data
        filename: Name of the file
        
    Returns:
        Tuple of (response, status_code)
    """
    import json
    
    json_data = json.dumps(data, indent=2, default=str)
    return file_response(
        file_data=json_data.encode('utf-8'),
        filename=filename,
        content_type='application/json'
    )

def csv_file_response(data: list, filename: str, headers: Optional[list] = None) -> tuple:
    """
    Create a CSV file download response
    
    Args:
        data: List of dictionaries
        filename: Name of the file
        headers: CSV headers (if None, will use dict keys)
        
    Returns:
        Tuple of (response, status_code)
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    if headers:
        writer.writerow(headers)
        for row in data:
            writer.writerow([row.get(header, '') for header in headers])
    else:
        if data:
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())
    
    csv_data = output.getvalue()
    return file_response(
        file_data=csv_data.encode('utf-8'),
        filename=filename,
        content_type='text/csv'
    ) 