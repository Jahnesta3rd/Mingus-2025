#!/usr/bin/env python3
"""
Mingus Application - Housing Location Models
SQLAlchemy models for optimal living location feature
"""

from datetime import datetime
from decimal import Decimal
from .database import db
import enum

class HousingType(enum.Enum):
    """Enum for housing types"""
    APARTMENT = "apartment"
    HOUSE = "house"
    CONDO = "condo"

class HousingSearch(db.Model):
    """
    Housing search model for tracking user housing searches and criteria
    """
    __tablename__ = 'housing_searches'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Search criteria stored as JSONB
    search_criteria = db.Column(db.JSON, nullable=False)
    
    # MSA area for the search
    msa_area = db.Column(db.String(100), nullable=False, index=True)
    
    # Lease end date for timing
    lease_end_date = db.Column(db.Date, nullable=True)
    
    # Number of results found
    results_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='housing_searches')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_housing_searches_user_msa', 'user_id', 'msa_area'),
        db.Index('idx_housing_searches_created_at', 'created_at'),
        db.Index('idx_housing_searches_lease_end', 'lease_end_date'),
    )
    
    def __repr__(self):
        return f'<HousingSearch {self.id}: {self.msa_area}>'

class HousingScenario(db.Model):
    """
    Housing scenario model for storing specific housing options and their analysis
    """
    __tablename__ = 'housing_scenarios'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Scenario name for user reference
    scenario_name = db.Column(db.String(255), nullable=False)
    
    # Housing data stored as JSONB
    housing_data = db.Column(db.JSON, nullable=False)
    
    # Commute data stored as JSONB
    commute_data = db.Column(db.JSON, nullable=False)
    
    # Financial impact analysis stored as JSONB
    financial_impact = db.Column(db.JSON, nullable=False)
    
    # Career data stored as JSONB
    career_data = db.Column(db.JSON, nullable=False)
    
    # User favorite flag
    is_favorite = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='housing_scenarios')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_housing_scenarios_user_favorite', 'user_id', 'is_favorite'),
        db.Index('idx_housing_scenarios_created_at', 'created_at'),
        db.Index('idx_housing_scenarios_name', 'scenario_name'),
    )
    
    def __repr__(self):
        return f'<HousingScenario {self.id}: {self.scenario_name}>'

class UserHousingPreferences(db.Model):
    """
    User housing preferences model for storing user's housing criteria
    """
    __tablename__ = 'user_housing_preferences'
    
    # Primary key (user_id is the primary key since it's one-to-one)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Commute preferences
    max_commute_time = db.Column(db.Integer, nullable=True)  # minutes
    
    # Housing type preference
    preferred_housing_type = db.Column(db.Enum(HousingType), nullable=True)
    
    # Bedroom preferences
    min_bedrooms = db.Column(db.Integer, nullable=True)
    max_bedrooms = db.Column(db.Integer, nullable=True)
    
    # Financial preferences
    max_rent_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # percentage of income
    
    # Location preferences
    preferred_neighborhoods = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='housing_preferences', uselist=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_housing_prefs_commute_time', 'max_commute_time'),
        db.Index('idx_housing_prefs_housing_type', 'preferred_housing_type'),
        db.Index('idx_housing_prefs_rent_percentage', 'max_rent_percentage'),
        db.CheckConstraint('max_commute_time >= 0', name='check_positive_commute_time'),
        db.CheckConstraint('min_bedrooms >= 0', name='check_positive_min_bedrooms'),
        db.CheckConstraint('max_bedrooms >= 0', name='check_positive_max_bedrooms'),
        db.CheckConstraint('min_bedrooms <= max_bedrooms', name='check_bedroom_range'),
        db.CheckConstraint('max_rent_percentage >= 0 AND max_rent_percentage <= 100', name='check_rent_percentage_range'),
    )
    
    def __repr__(self):
        return f'<UserHousingPreferences {self.user_id}>'

class CommuteRouteCache(db.Model):
    """
    Commute route cache model for storing Google Maps API results
    """
    __tablename__ = 'commute_route_cache'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Route endpoints
    origin_zip = db.Column(db.String(10), nullable=False, index=True)
    destination_zip = db.Column(db.String(10), nullable=False, index=True)
    
    # Route data
    distance_miles = db.Column(db.Numeric(8, 2), nullable=False)
    drive_time_minutes = db.Column(db.Integer, nullable=False)
    traffic_factor = db.Column(db.Numeric(3, 2), nullable=False, default=1.0)
    
    # Cache timestamp
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_commute_cache_route', 'origin_zip', 'destination_zip'),
        db.Index('idx_commute_cache_last_updated', 'last_updated'),
        db.Index('idx_commute_cache_distance', 'distance_miles'),
        db.CheckConstraint('distance_miles >= 0', name='check_positive_distance'),
        db.CheckConstraint('drive_time_minutes >= 0', name='check_positive_drive_time'),
        db.CheckConstraint('traffic_factor >= 0.1 AND traffic_factor <= 3.0', name='check_traffic_factor_range'),
    )
    
    def __repr__(self):
        return f'<CommuteRouteCache {self.origin_zip} -> {self.destination_zip}>'
