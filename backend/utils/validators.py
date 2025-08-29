"""
Validation utilities for models and data
"""

from typing import Optional, Union
from decimal import Decimal


def validate_decimal_range(value: Optional[Union[float, Decimal]], min_val: float = 0.0, max_val: float = None) -> Optional[Union[float, Decimal]]:
    """
    Validate decimal value is within specified range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value (None for no upper limit)
        
    Returns:
        Validated value or None if invalid
    """
    if value is None:
        return None
    
    try:
        decimal_value = Decimal(str(value))
        if decimal_value < min_val:
            return None
        if max_val is not None and decimal_value > max_val:
            return None
        return decimal_value
    except (ValueError, TypeError):
        return None


def validate_confidence_score(value: Optional[Union[float, Decimal]]) -> Optional[Union[float, Decimal]]:
    """
    Validate confidence score is between 0 and 1
    
    Args:
        value: Confidence score to validate
        
    Returns:
        Validated confidence score or None if invalid
    """
    return validate_decimal_range(value, 0.0, 1.0)
