#!/usr/bin/env python3
"""
Database Index Creation for Performance Optimization
Creates indexes on frequently queried columns
"""

import logging
from sqlalchemy import Index, text
from backend.models.database import db

logger = logging.getLogger(__name__)

def create_performance_indexes():
    """
    Create indexes for frequently queried columns
    
    This function should be called after database initialization
    to ensure optimal query performance.
    """
    indexes = []
    
    # User-related indexes
    try:
        indexes.append(Index('idx_user_email', text('users.email')))
        indexes.append(Index('idx_user_created_at', text('users.created_at')))
    except Exception as e:
        logger.debug(f"User indexes may not be needed: {e}")
    
    # Assessment indexes
    try:
        indexes.append(Index('idx_assessment_email', text('assessments.email')))
        indexes.append(Index('idx_assessment_type', text('assessments.assessment_type')))
        indexes.append(Index('idx_assessment_created_at', text('assessments.created_at')))
        indexes.append(Index('idx_assessment_email_type', 
                           text('assessments.email'), 
                           text('assessments.assessment_type')))
    except Exception as e:
        logger.debug(f"Assessment indexes may not be needed: {e}")
    
    # Profile indexes
    try:
        indexes.append(Index('idx_profile_email', text('user_profiles.email')))
    except Exception as e:
        logger.debug(f"Profile indexes may not be needed: {e}")
    
    # Vehicle indexes
    try:
        indexes.append(Index('idx_vehicle_user_id', text('vehicles.user_id')))
        indexes.append(Index('idx_vehicle_created_at', text('vehicles.created_at')))
    except Exception as e:
        logger.debug(f"Vehicle indexes may not be needed: {e}")
    
    # Create indexes
    created_count = 0
    for index in indexes:
        try:
            # Check if index already exists
            index.create(db.engine, checkfirst=True)
            created_count += 1
            logger.info(f"Created/verified index: {index.name}")
        except Exception as e:
            logger.warning(f"Could not create index {index.name}: {e}")
    
    logger.info(f"Created/verified {created_count} database indexes")
    return created_count


def create_custom_indexes_for_table(table_name: str, columns: list):
    """
    Create custom indexes for a specific table
    
    Args:
        table_name: Name of the table
        columns: List of column names to index
    """
    try:
        for column in columns:
            index_name = f"idx_{table_name}_{column}"
            index = Index(index_name, text(f"{table_name}.{column}"))
            index.create(db.engine, checkfirst=True)
            logger.info(f"Created index: {index_name}")
    except Exception as e:
        logger.error(f"Error creating custom indexes: {e}")
