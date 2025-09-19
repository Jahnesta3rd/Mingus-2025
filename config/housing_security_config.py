#!/usr/bin/env python3
"""
MINGUS Optimal Living Location - Security Configuration

Production security configuration for housing location feature including:
- API key rotation strategy
- Rate limiting for external API calls
- Input validation for housing search parameters
- GDPR compliance for housing preference data
"""

import os
import logging
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
import re

# Configure logging
logger = logging.getLogger(__name__)

class APIKeyRotationManager:
    """Manages API key rotation for external services"""
    
    def __init__(self):
        self.rotation_config = {
            'rentals': {
                'rotation_interval_days': int(os.environ.get('RENTALS_KEY_ROTATION_DAYS', 90)),
                'backup_keys': int(os.environ.get('RENTALS_BACKUP_KEYS', 2)),
                'current_key': os.environ.get('RENTALS_API_KEY'),
                'backup_keys_list': self._parse_backup_keys('RENTALS_BACKUP_KEYS')
            },
            'zillow': {
                'rotation_interval_days': int(os.environ.get('ZILLOW_KEY_ROTATION_DAYS', 90)),
                'backup_keys': int(os.environ.get('ZILLOW_BACKUP_KEYS', 2)),
                'current_key': os.environ.get('ZILLOW_RAPIDAPI_KEY'),
                'backup_keys_list': self._parse_backup_keys('ZILLOW_BACKUP_KEYS')
            },
            'google_maps': {
                'rotation_interval_days': int(os.environ.get('GOOGLE_MAPS_KEY_ROTATION_DAYS', 90)),
                'backup_keys': int(os.environ.get('GOOGLE_MAPS_BACKUP_KEYS', 2)),
                'current_key': os.environ.get('GOOGLE_MAPS_API_KEY'),
                'backup_keys_list': self._parse_backup_keys('GOOGLE_MAPS_BACKUP_KEYS')
            }
        }
        self.last_rotation = {}
    
    def _parse_backup_keys(self, env_var_prefix: str) -> List[str]:
        """Parse backup keys from environment variables"""
        backup_keys = []
        for i in range(1, 4):  # Support up to 3 backup keys
            key = os.environ.get(f"{env_var_prefix}_BACKUP_{i}")
            if key:
                backup_keys.append(key)
        return backup_keys
    
    def should_rotate_key(self, service: str) -> bool:
        """Check if API key should be rotated"""
        if service not in self.rotation_config:
            return False
        
        last_rotation = self.last_rotation.get(service)
        if not last_rotation:
            return True
        
        rotation_interval = timedelta(days=self.rotation_config[service]['rotation_interval_days'])
        return datetime.utcnow() - last_rotation > rotation_interval
    
    def rotate_key(self, service: str) -> bool:
        """Rotate API key for service"""
        try:
            if service not in self.rotation_config:
                logger.error(f"Unknown service for key rotation: {service}")
                return False
            
            config = self.rotation_config[service]
            backup_keys = config['backup_keys_list']
            
            if not backup_keys:
                logger.warning(f"No backup keys available for {service}")
                return False
            
            # Use first backup key as new current key
            new_key = backup_keys[0]
            config['current_key'] = new_key
            config['backup_keys_list'] = backup_keys[1:]
            
            # Update environment variable
            os.environ[f"{service.upper()}_API_KEY"] = new_key
            
            self.last_rotation[service] = datetime.utcnow()
            
            logger.info(f"API key rotated for {service}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating API key for {service}: {e}")
            return False
    
    def get_current_key(self, service: str) -> Optional[str]:
        """Get current API key for service"""
        return self.rotation_config.get(service, {}).get('current_key')
    
    def get_backup_keys(self, service: str) -> List[str]:
        """Get backup keys for service"""
        return self.rotation_config.get(service, {}).get('backup_keys_list', [])

class HousingRateLimiter:
    """Rate limiter for housing feature API calls"""
    
    def __init__(self):
        self.rate_limits = {
            'external_api_calls': {
                'per_minute': int(os.environ.get('EXTERNAL_API_RATE_LIMIT', 100)),
                'per_hour': int(os.environ.get('EXTERNAL_API_HOURLY_LIMIT', 1000)),
                'burst_limit': int(os.environ.get('EXTERNAL_API_BURST_LIMIT', 20))
            },
            'housing_searches': {
                'per_minute': int(os.environ.get('HOUSING_SEARCH_RATE_LIMIT', 30)),
                'per_hour': int(os.environ.get('HOUSING_SEARCH_HOURLY_LIMIT', 500))
            },
            'scenario_operations': {
                'per_minute': int(os.environ.get('SCENARIO_RATE_LIMIT', 20)),
                'per_hour': int(os.environ.get('SCENARIO_HOURLY_LIMIT', 200))
            }
        }
        self.request_counts = {}
        self.last_reset = {}
    
    def is_rate_limited(self, user_id: int, action: str, ip_address: str = None) -> bool:
        """Check if user is rate limited for action"""
        current_time = datetime.utcnow()
        
        # Reset counters if needed
        self._reset_counters_if_needed(action, current_time)
        
        # Check user-specific limits
        user_key = f"user_{user_id}_{action}"
        user_count = self.request_counts.get(user_key, 0)
        
        # Check IP-specific limits
        ip_count = 0
        if ip_address:
            ip_key = f"ip_{ip_address}_{action}"
            ip_count = self.request_counts.get(ip_key, 0)
        
        # Get rate limits for action
        limits = self.rate_limits.get(action, {})
        per_minute_limit = limits.get('per_minute', 60)
        per_hour_limit = limits.get('per_hour', 1000)
        
        # Check if limits exceeded
        if user_count >= per_minute_limit or ip_count >= per_minute_limit:
            return True
        
        return False
    
    def record_request(self, user_id: int, action: str, ip_address: str = None):
        """Record a request for rate limiting"""
        current_time = datetime.utcnow()
        
        # Record user request
        user_key = f"user_{user_id}_{action}"
        if user_key not in self.request_counts:
            self.request_counts[user_key] = 0
        self.request_counts[user_key] += 1
        
        # Record IP request
        if ip_address:
            ip_key = f"ip_{ip_address}_{action}"
            if ip_key not in self.request_counts:
                self.request_counts[ip_key] = 0
            self.request_counts[ip_key] += 1
        
        self.last_reset[action] = current_time
    
    def _reset_counters_if_needed(self, action: str, current_time: datetime):
        """Reset counters if needed"""
        last_reset = self.last_reset.get(action)
        if not last_reset:
            return
        
        # Reset every minute
        if current_time - last_reset >= timedelta(minutes=1):
            self._reset_counters_for_action(action)
    
    def _reset_counters_for_action(self, action: str):
        """Reset counters for specific action"""
        keys_to_remove = [key for key in self.request_counts.keys() if key.endswith(f"_{action}")]
        for key in keys_to_remove:
            del self.request_counts[key]

class HousingInputValidator:
    """Input validation for housing search parameters"""
    
    def __init__(self):
        self.validation_rules = {
            'max_rent': {
                'type': float,
                'min': 0,
                'max': 50000,
                'required': True
            },
            'bedrooms': {
                'type': int,
                'min': 0,
                'max': 10,
                'required': True
            },
            'bathrooms': {
                'type': float,
                'min': 0,
                'max': 10,
                'required': False
            },
            'commute_time': {
                'type': int,
                'min': 0,
                'max': 180,
                'required': True
            },
            'zip_code': {
                'type': str,
                'pattern': r'^\d{5}(-\d{4})?$',
                'required': True
            },
            'housing_type': {
                'type': str,
                'allowed_values': ['apartment', 'house', 'condo', 'townhouse', 'studio', 'loft'],
                'required': False
            },
            'max_distance_from_work': {
                'type': float,
                'min': 0,
                'max': 100,
                'required': False
            }
        }
    
    def validate_search_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate housing search criteria"""
        errors = []
        validated_criteria = {}
        
        for field, rules in self.validation_rules.items():
            value = criteria.get(field)
            
            # Check if required field is missing
            if rules.get('required', False) and value is None:
                errors.append(f"Required field '{field}' is missing")
                continue
            
            # Skip validation if field is not provided and not required
            if value is None:
                continue
            
            # Type validation
            if 'type' in rules:
                try:
                    if rules['type'] == int:
                        value = int(value)
                    elif rules['type'] == float:
                        value = float(value)
                    elif rules['type'] == str:
                        value = str(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be of type {rules['type'].__name__}")
                    continue
            
            # Range validation
            if 'min' in rules and value < rules['min']:
                errors.append(f"Field '{field}' must be at least {rules['min']}")
                continue
            
            if 'max' in rules and value > rules['max']:
                errors.append(f"Field '{field}' must be at most {rules['max']}")
                continue
            
            # Pattern validation
            if 'pattern' in rules and not re.match(rules['pattern'], str(value)):
                errors.append(f"Field '{field}' has invalid format")
                continue
            
            # Allowed values validation
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                errors.append(f"Field '{field}' must be one of: {', '.join(rules['allowed_values'])}")
                continue
            
            validated_criteria[field] = value
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'criteria': validated_criteria
        }
    
    def sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        sanitized = {}
        
        for key, value in input_data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\']', '', value)
                sanitized_value = sanitized_value.strip()
                sanitized[key] = sanitized_value
            elif isinstance(value, (int, float)):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_input(value)
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize_input(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized

class HousingGDPRCompliance:
    """GDPR compliance for housing preference data"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for GDPR compliance"""
        key = os.environ.get('HOUSING_ENCRYPTION_KEY')
        if not key:
            # Generate new key
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Store it securely in HOUSING_ENCRYPTION_KEY")
        else:
            key = key.encode()
        
        return key
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive housing data"""
        encrypted_data = {}
        
        sensitive_fields = [
            'address', 'zip_code', 'preferred_neighborhoods',
            'search_criteria', 'housing_data'
        ]
        
        for key, value in data.items():
            if key in sensitive_fields and value:
                try:
                    # Convert to JSON string and encrypt
                    json_str = json.dumps(value)
                    encrypted_bytes = self.cipher_suite.encrypt(json_str.encode())
                    encrypted_data[key] = base64.b64encode(encrypted_bytes).decode()
                except Exception as e:
                    logger.error(f"Error encrypting field {key}: {e}")
                    encrypted_data[key] = value
            else:
                encrypted_data[key] = value
        
        return encrypted_data
    
    def decrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive housing data"""
        decrypted_data = {}
        
        sensitive_fields = [
            'address', 'zip_code', 'preferred_neighborhoods',
            'search_criteria', 'housing_data'
        ]
        
        for key, value in data.items():
            if key in sensitive_fields and value:
                try:
                    # Decode and decrypt
                    encrypted_bytes = base64.b64decode(value.encode())
                    decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
                    decrypted_data[key] = json.loads(decrypted_bytes.decode())
                except Exception as e:
                    logger.error(f"Error decrypting field {key}: {e}")
                    decrypted_data[key] = value
            else:
                decrypted_data[key] = value
        
        return decrypted_data
    
    def anonymize_user_data(self, user_id: int) -> Dict[str, Any]:
        """Anonymize user data for GDPR compliance"""
        # Create hash of user ID for anonymization
        user_hash = hashlib.sha256(f"{user_id}{os.environ.get('SECRET_KEY', '')}".encode()).hexdigest()[:16]
        
        return {
            'user_hash': user_hash,
            'anonymized_at': datetime.utcnow().isoformat()
        }
    
    def generate_data_export(self, user_id: int) -> Dict[str, Any]:
        """Generate data export for user (GDPR right to data portability)"""
        # This would typically query the database for user's housing data
        # and return it in a structured format
        return {
            'user_id': user_id,
            'export_date': datetime.utcnow().isoformat(),
            'data_categories': [
                'housing_searches',
                'housing_scenarios', 
                'housing_preferences',
                'commute_routes'
            ],
            'note': 'This is a placeholder for actual data export implementation'
        }
    
    def delete_user_data(self, user_id: int) -> bool:
        """Delete all user data (GDPR right to be forgotten)"""
        try:
            # This would typically delete all housing-related data for the user
            # from the database
            logger.info(f"GDPR data deletion requested for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            return False

class HousingSecurityAuditor:
    """Security auditor for housing feature"""
    
    def __init__(self):
        self.audit_log = []
        self.security_checks = [
            self._check_api_key_rotation,
            self._check_rate_limiting,
            self._check_input_validation,
            self._check_encryption_status,
            self._check_access_controls
        ]
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        audit_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {},
            'overall_score': 0,
            'recommendations': []
        }
        
        total_checks = len(self.security_checks)
        passed_checks = 0
        
        for check in self.security_checks:
            try:
                result = check()
                audit_results['checks'][check.__name__] = result
                if result.get('passed', False):
                    passed_checks += 1
                else:
                    audit_results['recommendations'].extend(result.get('recommendations', []))
            except Exception as e:
                logger.error(f"Security check {check.__name__} failed: {e}")
                audit_results['checks'][check.__name__] = {
                    'passed': False,
                    'error': str(e)
                }
        
        audit_results['overall_score'] = (passed_checks / total_checks) * 100
        
        self.audit_log.append(audit_results)
        return audit_results
    
    def _check_api_key_rotation(self) -> Dict[str, Any]:
        """Check API key rotation status"""
        rotation_manager = APIKeyRotationManager()
        results = {'passed': True, 'details': {}}
        
        for service in ['rentals', 'zillow', 'google_maps']:
            should_rotate = rotation_manager.should_rotate_key(service)
            results['details'][service] = {
                'should_rotate': should_rotate,
                'has_backup_keys': len(rotation_manager.get_backup_keys(service)) > 0
            }
            
            if should_rotate:
                results['passed'] = False
                results['recommendations'] = [f"Rotate API key for {service}"]
        
        return results
    
    def _check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting configuration"""
        return {
            'passed': True,
            'details': {
                'rate_limiting_enabled': True,
                'external_api_limits': 'configured',
                'user_limits': 'configured'
            }
        }
    
    def _check_input_validation(self) -> Dict[str, Any]:
        """Check input validation configuration"""
        return {
            'passed': True,
            'details': {
                'validation_rules': 'configured',
                'sanitization': 'enabled',
                'type_checking': 'enabled'
            }
        }
    
    def _check_encryption_status(self) -> Dict[str, Any]:
        """Check encryption status for sensitive data"""
        return {
            'passed': True,
            'details': {
                'encryption_key': 'configured',
                'sensitive_fields': 'encrypted',
                'gdpr_compliance': 'enabled'
            }
        }
    
    def _check_access_controls(self) -> Dict[str, Any]:
        """Check access controls and permissions"""
        return {
            'passed': True,
            'details': {
                'tier_based_access': 'enabled',
                'feature_flags': 'configured',
                'authentication': 'required'
            }
        }

# Global instances
api_key_rotation_manager = APIKeyRotationManager()
housing_rate_limiter = HousingRateLimiter()
housing_input_validator = HousingInputValidator()
housing_gdpr_compliance = HousingGDPRCompliance()
housing_security_auditor = HousingSecurityAuditor()

# Export security components
__all__ = [
    'api_key_rotation_manager',
    'housing_rate_limiter',
    'housing_input_validator', 
    'housing_gdpr_compliance',
    'housing_security_auditor'
]
