#!/usr/bin/env python3
"""
Mingus Application - Vehicle Management Models
SQLAlchemy models for vehicle management system
"""

from datetime import datetime
from decimal import Decimal
from .database import db

class Vehicle(db.Model):
    """
    Vehicle model for tracking user vehicles and their details
    """
    __tablename__ = 'vehicles'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Vehicle identification
    vin = db.Column(db.String(17), unique=True, nullable=False, index=True)
    
    # Vehicle details
    year = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(50), nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    trim = db.Column(db.String(100), nullable=True)
    
    # Usage tracking
    current_mileage = db.Column(db.Integer, nullable=False, default=0)
    monthly_miles = db.Column(db.Integer, nullable=False, default=0)
    
    # Location data for MSA mapping
    user_zipcode = db.Column(db.String(10), nullable=False, index=True)
    assigned_msa = db.Column(db.String(100), nullable=True, index=True)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    maintenance_predictions = db.relationship('MaintenancePrediction', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    commute_scenarios = db.relationship('CommuteScenario', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_vehicle_user_year', 'user_id', 'year'),
        db.Index('idx_vehicle_make_model', 'make', 'model'),
        db.Index('idx_vehicle_msa_zipcode', 'assigned_msa', 'user_zipcode'),
    )
    
    def __repr__(self):
        return f'<Vehicle {self.year} {self.make} {self.model} (VIN: {self.vin[:8]}...)>'
    
    def to_dict(self):
        """Convert vehicle to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vin': self.vin,
            'year': self.year,
            'make': self.make,
            'model': self.model,
            'trim': self.trim,
            'current_mileage': self.current_mileage,
            'monthly_miles': self.monthly_miles,
            'user_zipcode': self.user_zipcode,
            'assigned_msa': self.assigned_msa,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat()
        }


class MaintenancePrediction(db.Model):
    """
    Maintenance prediction model for tracking predicted vehicle maintenance
    """
    __tablename__ = 'maintenance_predictions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to vehicles table
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    
    # Service details
    service_type = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Prediction data
    predicted_date = db.Column(db.Date, nullable=False, index=True)
    predicted_mileage = db.Column(db.Integer, nullable=False)
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=False)
    probability = db.Column(db.Float, nullable=False, default=0.0)  # 0.0 to 1.0
    
    # Service classification
    is_routine = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_maintenance_vehicle_date', 'vehicle_id', 'predicted_date'),
        db.Index('idx_maintenance_service_type', 'service_type'),
        db.Index('idx_maintenance_routine', 'is_routine'),
        db.CheckConstraint('probability >= 0.0 AND probability <= 1.0', name='check_probability_range'),
        db.CheckConstraint('estimated_cost >= 0', name='check_positive_cost'),
    )
    
    def __repr__(self):
        return f'<MaintenancePrediction {self.service_type} for Vehicle {self.vehicle_id} on {self.predicted_date}>'
    
    def to_dict(self):
        """Convert maintenance prediction to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'service_type': self.service_type,
            'description': self.description,
            'predicted_date': self.predicted_date.isoformat() if self.predicted_date else None,
            'predicted_mileage': self.predicted_mileage,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else 0.0,
            'probability': self.probability,
            'is_routine': self.is_routine,
            'created_date': self.created_date.isoformat()
        }


class CommuteScenario(db.Model):
    """
    Commute scenario model for tracking different job location scenarios
    """
    __tablename__ = 'commute_scenarios'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to vehicles table
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    
    # Job location details
    job_location = db.Column(db.String(255), nullable=False)
    job_zipcode = db.Column(db.String(10), nullable=False, index=True)
    
    # Distance and cost calculations
    distance_miles = db.Column(db.Float, nullable=False)
    daily_cost = db.Column(db.Numeric(10, 2), nullable=False)
    monthly_cost = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Gas price and efficiency data
    gas_price_per_gallon = db.Column(db.Numeric(5, 3), nullable=False)
    vehicle_mpg = db.Column(db.Float, nullable=False)
    
    # MSA information
    from_msa = db.Column(db.String(100), nullable=True, index=True)
    to_msa = db.Column(db.String(100), nullable=True, index=True)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_commute_vehicle_zipcode', 'vehicle_id', 'job_zipcode'),
        db.Index('idx_commute_msa_route', 'from_msa', 'to_msa'),
        db.Index('idx_commute_cost', 'monthly_cost'),
        db.CheckConstraint('distance_miles >= 0', name='check_positive_distance'),
        db.CheckConstraint('daily_cost >= 0', name='check_positive_daily_cost'),
        db.CheckConstraint('monthly_cost >= 0', name='check_positive_monthly_cost'),
        db.CheckConstraint('gas_price_per_gallon >= 0', name='check_positive_gas_price'),
        db.CheckConstraint('vehicle_mpg > 0', name='check_positive_mpg'),
    )
    
    def __repr__(self):
        return f'<CommuteScenario Vehicle {self.vehicle_id} to {self.job_location} ({self.distance_miles} miles)>'
    
    def to_dict(self):
        """Convert commute scenario to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'job_location': self.job_location,
            'job_zipcode': self.job_zipcode,
            'distance_miles': self.distance_miles,
            'daily_cost': float(self.daily_cost) if self.daily_cost else 0.0,
            'monthly_cost': float(self.monthly_cost) if self.monthly_cost else 0.0,
            'gas_price_per_gallon': float(self.gas_price_per_gallon) if self.gas_price_per_gallon else 0.0,
            'vehicle_mpg': self.vehicle_mpg,
            'from_msa': self.from_msa,
            'to_msa': self.to_msa,
            'created_date': self.created_date.isoformat()
        }


class MSAGasPrice(db.Model):
    """
    MSA Gas Price model for tracking gas prices by Metropolitan Statistical Area
    Supports both specific MSAs and "National Average" fallback pricing
    """
    __tablename__ = 'msa_gas_prices'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # MSA identification (supports "National Average" as fallback)
    msa_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Price data
    current_price = db.Column(db.Numeric(5, 3), nullable=False)
    previous_price = db.Column(db.Numeric(5, 3), nullable=True)  # For price change tracking
    price_change = db.Column(db.Numeric(5, 3), nullable=True)   # Calculated price change
    
    # Data source and quality
    data_source = db.Column(db.String(50), nullable=True)  # e.g., "API", "Manual", "Fallback"
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0 data quality score
    
    # Timestamps
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_msa_name', 'msa_name'),
        db.Index('idx_last_updated', 'last_updated'),
        db.Index('idx_data_source', 'data_source'),
        db.CheckConstraint('current_price >= 0', name='check_positive_price'),
        db.CheckConstraint('previous_price >= 0 OR previous_price IS NULL', name='check_positive_previous_price'),
        db.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0 OR confidence_score IS NULL', name='check_confidence_range'),
    )
    
    def __repr__(self):
        return f'<MSAGasPrice {self.msa_name}: ${self.current_price}/gallon>'
    
    def to_dict(self):
        """Convert MSA gas price to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'msa_name': self.msa_name,
            'current_price': float(self.current_price) if self.current_price else 0.0,
            'previous_price': float(self.previous_price) if self.previous_price else None,
            'price_change': float(self.price_change) if self.price_change else None,
            'data_source': self.data_source,
            'confidence_score': self.confidence_score,
            'last_updated': self.last_updated.isoformat(),
            'created_date': self.created_date.isoformat()
        }
    
    def calculate_price_change(self):
        """Calculate price change from previous price"""
        if self.previous_price and self.current_price:
            self.price_change = self.current_price - self.previous_price
        else:
            self.price_change = None
        return self.price_change
