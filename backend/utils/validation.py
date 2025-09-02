import re
from typing import Optional


def validate_user_tier(tier: Optional[str]) -> bool:
    if not tier:
        return False
    return tier in {"budget", "mid_tier", "professional"}


def validate_email_format(email: str) -> bool:
    """Validate email format using regex"""
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


__all__ = ["validate_user_tier", "validate_email_format"]










