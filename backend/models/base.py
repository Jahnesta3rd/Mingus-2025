"""
Shared SQLAlchemy Base for all models
This ensures all models use the same metadata registry
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass

# Export the Base class
__all__ = ['Base'] 