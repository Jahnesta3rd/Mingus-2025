# This file makes the utils directory a Python package
from .auth_decorators import require_authentication

__all__ = ['require_authentication'] 