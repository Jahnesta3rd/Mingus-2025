#!/usr/bin/env python3
"""
Mingus Application - Professional Tier Models
SQLAlchemy models for Professional tier business vehicle management features
"""

from datetime import datetime, date
from decimal import Decimal
from .database import db
from enum import Enum

class VehicleType(Enum):
    """Vehicle type enumeration"""
    PERSONAL = "personal"
    BUSINESS = "business"
    FLEET = "fleet"

class BusinessUseType(Enum):
    """Business use type enumeration"""
    COMMUTE = "commute"
    BUSINESS_TRAVEL = "business_travel"
    CLIENT_MEETINGS = "client_meetings"
    DELIVERY = "delivery"
    SALES = "sales"
    OTHER = "other"

class TaxDeductionType(Enum):
    """Tax deduction type enumeration"""
    MILEAGE = "mileage"
    ACTUAL_EXPENSES = "actual_expenses"
    LEASE_PAYMENTS = "lease_payments"
    DEPRECIATION = "depreciation"

class FleetVehicle(db.Model):
    """
    Fleet vehicle model for Professional tier business vehicle management
    Extends basic vehicle with business-specific features
    """
    __tablename__ = 'fleet_vehicles'
    
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
    
    # Business classification
    vehicle_type = db.Column(db.Enum(VehicleType), nullable=False, default=VehicleType.PERSONAL)
    business_use_percentage = db.Column(db.Float, nullable=False, default=0.0)  # 0.0 to 100.0
    primary_business_use = db.Column(db.Enum(BusinessUseType), nullable=True)
    
    # Department/Employee assignment
    department = db.Column(db.String(100), nullable=True, index=True)
    assigned_employee = db.Column(db.String(100), nullable=True, index=True)
    cost_center = db.Column(db.String(50), nullable=True, index=True)
    
    # Usage tracking
    current_mileage = db.Column(db.Integer, nullable=False, default=0)
    monthly_miles = db.Column(db.Integer, nullable=False, default=0)
    business_miles_ytd = db.Column(db.Integer, nullable=False, default=0)
    personal_miles_ytd = db.Column(db.Integer, nullable=False, default=0)
    
    # Location data
    user_zipcode = db.Column(db.String(10), nullable=False, index=True)
    assigned_msa = db.Column(db.String(100), nullable=True, index=True)
    
    # Financial tracking
    purchase_price = db.Column(db.Numeric(12, 2), nullable=True)
    current_value = db.Column(db.Numeric(12, 2), nullable=True)
    monthly_payment = db.Column(db.Numeric(10, 2), nullable=True)
    insurance_cost_monthly = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Tax optimization
    tax_deduction_method = db.Column(db.Enum(TaxDeductionType), nullable=True)
    depreciation_basis = db.Column(db.Numeric(12, 2), nullable=True)
    accumulated_depreciation = db.Column(db.Numeric(12, 2), nullable=True, default=0)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    mileage_logs = db.relationship('MileageLog', backref='fleet_vehicle', lazy=True, cascade='all, delete-orphan')
    business_expenses = db.relationship('BusinessExpense', backref='fleet_vehicle', lazy=True, cascade='all, delete-orphan')
    maintenance_records = db.relationship('MaintenanceRecord', backref='fleet_vehicle', lazy=True, cascade='all, delete-orphan')
    tax_reports = db.relationship('TaxReport', backref='fleet_vehicle', lazy=True, cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_fleet_vehicle_user_type', 'user_id', 'vehicle_type'),
        db.Index('idx_fleet_vehicle_department', 'department'),
        db.Index('idx_fleet_vehicle_employee', 'assigned_employee'),
        db.Index('idx_fleet_vehicle_business_use', 'business_use_percentage'),
        db.CheckConstraint('business_use_percentage >= 0.0 AND business_use_percentage <= 100.0', name='check_business_use_percentage'),
        db.CheckConstraint('current_mileage >= 0', name='check_positive_mileage'),
        db.CheckConstraint('monthly_miles >= 0', name='check_positive_monthly_miles'),
    )
    
    def __repr__(self):
        return f'<FleetVehicle {self.year} {self.make} {self.model} ({self.vehicle_type.value})>'
    
    def to_dict(self):
        """Convert fleet vehicle to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vin': self.vin,
            'year': self.year,
            'make': self.make,
            'model': self.model,
            'trim': self.trim,
            'vehicle_type': self.vehicle_type.value,
            'business_use_percentage': self.business_use_percentage,
            'primary_business_use': self.primary_business_use.value if self.primary_business_use else None,
            'department': self.department,
            'assigned_employee': self.assigned_employee,
            'cost_center': self.cost_center,
            'current_mileage': self.current_mileage,
            'monthly_miles': self.monthly_miles,
            'business_miles_ytd': self.business_miles_ytd,
            'personal_miles_ytd': self.personal_miles_ytd,
            'user_zipcode': self.user_zipcode,
            'assigned_msa': self.assigned_msa,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'current_value': float(self.current_value) if self.current_value else None,
            'monthly_payment': float(self.monthly_payment) if self.monthly_payment else None,
            'insurance_cost_monthly': float(self.insurance_cost_monthly) if self.insurance_cost_monthly else None,
            'tax_deduction_method': self.tax_deduction_method.value if self.tax_deduction_method else None,
            'depreciation_basis': float(self.depreciation_basis) if self.depreciation_basis else None,
            'accumulated_depreciation': float(self.accumulated_depreciation) if self.accumulated_depreciation else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class MileageLog(db.Model):
    """
    Mileage log model for tracking business and personal miles
    Supports GPS integration and IRS-compliant reporting
    """
    __tablename__ = 'mileage_logs'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to fleet vehicles
    fleet_vehicle_id = db.Column(db.Integer, db.ForeignKey('fleet_vehicles.id'), nullable=False, index=True)
    
    # Trip details
    trip_date = db.Column(db.Date, nullable=False, index=True)
    start_location = db.Column(db.String(255), nullable=False)
    end_location = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.String(255), nullable=False)
    business_use_type = db.Column(db.Enum(BusinessUseType), nullable=True)
    
    # Distance tracking
    total_miles = db.Column(db.Float, nullable=False)
    business_miles = db.Column(db.Float, nullable=False, default=0.0)
    personal_miles = db.Column(db.Float, nullable=False, default=0.0)
    
    # GPS data (optional)
    start_latitude = db.Column(db.Float, nullable=True)
    start_longitude = db.Column(db.Float, nullable=True)
    end_latitude = db.Column(db.Float, nullable=True)
    end_longitude = db.Column(db.Float, nullable=True)
    gps_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Cost calculations
    mileage_rate = db.Column(db.Numeric(5, 3), nullable=False)  # IRS mileage rate
    business_deduction = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Receipt tracking
    receipt_attached = db.Column(db.Boolean, default=False, nullable=False)
    receipt_file_path = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_mileage_vehicle_date', 'fleet_vehicle_id', 'trip_date'),
        db.Index('idx_mileage_business_type', 'business_use_type'),
        db.Index('idx_mileage_trip_date', 'trip_date'),
        db.CheckConstraint('total_miles >= 0', name='check_positive_total_miles'),
        db.CheckConstraint('business_miles >= 0', name='check_positive_business_miles'),
        db.CheckConstraint('personal_miles >= 0', name='check_positive_personal_miles'),
        db.CheckConstraint('business_miles + personal_miles <= total_miles', name='check_miles_sum'),
    )
    
    def __repr__(self):
        return f'<MileageLog {self.trip_date}: {self.business_miles} business miles>'
    
    def to_dict(self):
        """Convert mileage log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'fleet_vehicle_id': self.fleet_vehicle_id,
            'trip_date': self.trip_date.isoformat(),
            'start_location': self.start_location,
            'end_location': self.end_location,
            'purpose': self.purpose,
            'business_use_type': self.business_use_type.value if self.business_use_type else None,
            'total_miles': self.total_miles,
            'business_miles': self.business_miles,
            'personal_miles': self.personal_miles,
            'start_latitude': self.start_latitude,
            'start_longitude': self.start_longitude,
            'end_latitude': self.end_latitude,
            'end_longitude': self.end_longitude,
            'gps_verified': self.gps_verified,
            'mileage_rate': float(self.mileage_rate) if self.mileage_rate else 0.0,
            'business_deduction': float(self.business_deduction) if self.business_deduction else 0.0,
            'receipt_attached': self.receipt_attached,
            'receipt_file_path': self.receipt_file_path,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class BusinessExpense(db.Model):
    """
    Business expense model for tracking vehicle-related business expenses
    Supports receipt management and automatic categorization
    """
    __tablename__ = 'business_expenses'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to fleet vehicles
    fleet_vehicle_id = db.Column(db.Integer, db.ForeignKey('fleet_vehicles.id'), nullable=False, index=True)
    
    # Expense details
    expense_date = db.Column(db.Date, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    subcategory = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Business classification
    is_business_expense = db.Column(db.Boolean, default=True, nullable=False)
    business_percentage = db.Column(db.Float, nullable=False, default=100.0)  # 0.0 to 100.0
    deductible_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Receipt and documentation
    receipt_attached = db.Column(db.Boolean, default=False, nullable=False)
    receipt_file_path = db.Column(db.String(500), nullable=True)
    vendor = db.Column(db.String(255), nullable=True)
    invoice_number = db.Column(db.String(100), nullable=True)
    
    # Tax reporting
    tax_year = db.Column(db.Integer, nullable=False, index=True)
    included_in_tax_report = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_expense_vehicle_date', 'fleet_vehicle_id', 'expense_date'),
        db.Index('idx_expense_category', 'category'),
        db.Index('idx_expense_tax_year', 'tax_year'),
        db.Index('idx_expense_business', 'is_business_expense'),
        db.CheckConstraint('amount >= 0', name='check_positive_amount'),
        db.CheckConstraint('business_percentage >= 0.0 AND business_percentage <= 100.0', name='check_business_percentage'),
        db.CheckConstraint('deductible_amount >= 0', name='check_positive_deductible'),
    )
    
    def __repr__(self):
        return f'<BusinessExpense {self.category}: ${self.amount} on {self.expense_date}>'
    
    def to_dict(self):
        """Convert business expense to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'fleet_vehicle_id': self.fleet_vehicle_id,
            'expense_date': self.expense_date.isoformat(),
            'category': self.category,
            'subcategory': self.subcategory,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0.0,
            'is_business_expense': self.is_business_expense,
            'business_percentage': self.business_percentage,
            'deductible_amount': float(self.deductible_amount) if self.deductible_amount else 0.0,
            'receipt_attached': self.receipt_attached,
            'receipt_file_path': self.receipt_file_path,
            'vendor': self.vendor,
            'invoice_number': self.invoice_number,
            'tax_year': self.tax_year,
            'included_in_tax_report': self.included_in_tax_report,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class MaintenanceRecord(db.Model):
    """
    Maintenance record model for tracking vehicle maintenance with business cost allocation
    """
    __tablename__ = 'maintenance_records'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to fleet vehicles
    fleet_vehicle_id = db.Column(db.Integer, db.ForeignKey('fleet_vehicles.id'), nullable=False, index=True)
    
    # Maintenance details
    service_date = db.Column(db.Date, nullable=False, index=True)
    service_type = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    odometer_reading = db.Column(db.Integer, nullable=False)
    
    # Cost tracking
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)
    labor_cost = db.Column(db.Numeric(10, 2), nullable=True)
    parts_cost = db.Column(db.Numeric(10, 2), nullable=True)
    business_percentage = db.Column(db.Float, nullable=False, default=100.0)
    business_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Service provider
    service_provider = db.Column(db.String(255), nullable=True)
    service_location = db.Column(db.String(255), nullable=True)
    warranty_covered = db.Column(db.Boolean, default=False, nullable=False)
    
    # Documentation
    invoice_attached = db.Column(db.Boolean, default=False, nullable=False)
    invoice_file_path = db.Column(db.String(500), nullable=True)
    warranty_expires = db.Column(db.Date, nullable=True)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_maintenance_vehicle_date', 'fleet_vehicle_id', 'service_date'),
        db.Index('idx_maintenance_service_type', 'service_type'),
        db.Index('idx_maintenance_provider', 'service_provider'),
        db.CheckConstraint('total_cost >= 0', name='check_positive_total_cost'),
        db.CheckConstraint('labor_cost >= 0 OR labor_cost IS NULL', name='check_positive_labor_cost'),
        db.CheckConstraint('parts_cost >= 0 OR parts_cost IS NULL', name='check_positive_parts_cost'),
        db.CheckConstraint('business_percentage >= 0.0 AND business_percentage <= 100.0', name='check_maintenance_business_percentage'),
        db.CheckConstraint('business_cost >= 0', name='check_positive_business_cost'),
    )
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.service_type}: ${self.total_cost} on {self.service_date}>'
    
    def to_dict(self):
        """Convert maintenance record to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'fleet_vehicle_id': self.fleet_vehicle_id,
            'service_date': self.service_date.isoformat(),
            'service_type': self.service_type,
            'description': self.description,
            'odometer_reading': self.odometer_reading,
            'total_cost': float(self.total_cost) if self.total_cost else 0.0,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'parts_cost': float(self.parts_cost) if self.parts_cost else None,
            'business_percentage': self.business_percentage,
            'business_cost': float(self.business_cost) if self.business_cost else 0.0,
            'service_provider': self.service_provider,
            'service_location': self.service_location,
            'warranty_covered': self.warranty_covered,
            'invoice_attached': self.invoice_attached,
            'invoice_file_path': self.invoice_file_path,
            'warranty_expires': self.warranty_expires.isoformat() if self.warranty_expires else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class TaxReport(db.Model):
    """
    Tax report model for generating CPA-ready tax reports
    """
    __tablename__ = 'tax_reports'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to fleet vehicles
    fleet_vehicle_id = db.Column(db.Integer, db.ForeignKey('fleet_vehicles.id'), nullable=False, index=True)
    
    # Report details
    tax_year = db.Column(db.Integer, nullable=False, index=True)
    report_type = db.Column(db.String(50), nullable=False)  # 'annual', 'quarterly', 'monthly'
    report_period_start = db.Column(db.Date, nullable=False)
    report_period_end = db.Column(db.Date, nullable=False)
    
    # Mileage summary
    total_business_miles = db.Column(db.Integer, nullable=False, default=0)
    total_personal_miles = db.Column(db.Integer, nullable=False, default=0)
    mileage_deduction_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    average_mileage_rate = db.Column(db.Numeric(5, 3), nullable=False, default=0.0)
    
    # Expense summary
    total_business_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    maintenance_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    fuel_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    insurance_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    depreciation_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    other_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Tax optimization
    recommended_deduction_method = db.Column(db.Enum(TaxDeductionType), nullable=True)
    potential_savings = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Report generation
    generated_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    report_file_path = db.Column(db.String(500), nullable=True)
    cpa_ready = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_tax_report_vehicle_year', 'fleet_vehicle_id', 'tax_year'),
        db.Index('idx_tax_report_type', 'report_type'),
        db.Index('idx_tax_report_period', 'report_period_start', 'report_period_end'),
        db.CheckConstraint('total_business_miles >= 0', name='check_positive_business_miles'),
        db.CheckConstraint('total_personal_miles >= 0', name='check_positive_personal_miles'),
        db.CheckConstraint('mileage_deduction_amount >= 0', name='check_positive_mileage_deduction'),
        db.CheckConstraint('total_business_expenses >= 0', name='check_positive_business_expenses'),
    )
    
    def __repr__(self):
        return f'<TaxReport {self.tax_year} {self.report_type}: ${self.mileage_deduction_amount + self.total_business_expenses}>'
    
    def to_dict(self):
        """Convert tax report to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'fleet_vehicle_id': self.fleet_vehicle_id,
            'tax_year': self.tax_year,
            'report_type': self.report_type,
            'report_period_start': self.report_period_start.isoformat(),
            'report_period_end': self.report_period_end.isoformat(),
            'total_business_miles': self.total_business_miles,
            'total_personal_miles': self.total_personal_miles,
            'mileage_deduction_amount': float(self.mileage_deduction_amount) if self.mileage_deduction_amount else 0.0,
            'average_mileage_rate': float(self.average_mileage_rate) if self.average_mileage_rate else 0.0,
            'total_business_expenses': float(self.total_business_expenses) if self.total_business_expenses else 0.0,
            'maintenance_expenses': float(self.maintenance_expenses) if self.maintenance_expenses else 0.0,
            'fuel_expenses': float(self.fuel_expenses) if self.fuel_expenses else 0.0,
            'insurance_expenses': float(self.insurance_expenses) if self.insurance_expenses else 0.0,
            'depreciation_expenses': float(self.depreciation_expenses) if self.depreciation_expenses else 0.0,
            'other_expenses': float(self.other_expenses) if self.other_expenses else 0.0,
            'recommended_deduction_method': self.recommended_deduction_method.value if self.recommended_deduction_method else None,
            'potential_savings': float(self.potential_savings) if self.potential_savings else None,
            'generated_date': self.generated_date.isoformat(),
            'report_file_path': self.report_file_path,
            'cpa_ready': self.cpa_ready,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class FleetAnalytics(db.Model):
    """
    Fleet analytics model for storing calculated metrics and KPIs
    """
    __tablename__ = 'fleet_analytics'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Analytics period
    analytics_date = db.Column(db.Date, nullable=False, index=True)
    period_type = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    
    # Fleet metrics
    total_vehicles = db.Column(db.Integer, nullable=False, default=0)
    business_vehicles = db.Column(db.Integer, nullable=False, default=0)
    personal_vehicles = db.Column(db.Integer, nullable=False, default=0)
    
    # Cost metrics
    total_monthly_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    cost_per_mile = db.Column(db.Numeric(8, 4), nullable=False, default=0.0)
    cost_per_vehicle = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Usage metrics
    total_miles = db.Column(db.Integer, nullable=False, default=0)
    business_miles = db.Column(db.Integer, nullable=False, default=0)
    personal_miles = db.Column(db.Integer, nullable=False, default=0)
    average_mpg = db.Column(db.Float, nullable=False, default=0.0)
    
    # Maintenance metrics
    maintenance_cost_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    maintenance_cost_per_mile = db.Column(db.Numeric(8, 4), nullable=False, default=0.0)
    maintenance_frequency = db.Column(db.Float, nullable=False, default=0.0)  # services per month
    
    # Tax metrics
    total_tax_deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    mileage_deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    expense_deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_fleet_analytics_user_date', 'user_id', 'analytics_date'),
        db.Index('idx_fleet_analytics_period', 'period_type'),
        db.CheckConstraint('total_vehicles >= 0', name='check_positive_total_vehicles'),
        db.CheckConstraint('business_vehicles >= 0', name='check_positive_business_vehicles'),
        db.CheckConstraint('personal_vehicles >= 0', name='check_positive_personal_vehicles'),
        db.CheckConstraint('total_monthly_cost >= 0', name='check_positive_monthly_cost'),
        db.CheckConstraint('cost_per_mile >= 0', name='check_positive_cost_per_mile'),
        db.CheckConstraint('total_miles >= 0', name='check_positive_total_miles'),
    )
    
    def __repr__(self):
        return f'<FleetAnalytics {self.analytics_date}: {self.total_vehicles} vehicles, ${self.total_monthly_cost}/month>'
    
    def to_dict(self):
        """Convert fleet analytics to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'analytics_date': self.analytics_date.isoformat(),
            'period_type': self.period_type,
            'total_vehicles': self.total_vehicles,
            'business_vehicles': self.business_vehicles,
            'personal_vehicles': self.personal_vehicles,
            'total_monthly_cost': float(self.total_monthly_cost) if self.total_monthly_cost else 0.0,
            'cost_per_mile': float(self.cost_per_mile) if self.cost_per_mile else 0.0,
            'cost_per_vehicle': float(self.cost_per_vehicle) if self.cost_per_vehicle else 0.0,
            'total_miles': self.total_miles,
            'business_miles': self.business_miles,
            'personal_miles': self.personal_miles,
            'average_mpg': self.average_mpg,
            'maintenance_cost_total': float(self.maintenance_cost_total) if self.maintenance_cost_total else 0.0,
            'maintenance_cost_per_mile': float(self.maintenance_cost_per_mile) if self.maintenance_cost_per_mile else 0.0,
            'maintenance_frequency': self.maintenance_frequency,
            'total_tax_deductions': float(self.total_tax_deductions) if self.total_tax_deductions else 0.0,
            'mileage_deductions': float(self.mileage_deductions) if self.mileage_deductions else 0.0,
            'expense_deductions': float(self.expense_deductions) if self.expense_deductions else 0.0,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }
