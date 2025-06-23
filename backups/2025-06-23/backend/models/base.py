"""
Shared SQLAlchemy Base for all models
This ensures all models use the same metadata registry
"""
from sqlalchemy.ext.declarative import declarative_base

# Single shared Base for all models
Base = declarative_base() 