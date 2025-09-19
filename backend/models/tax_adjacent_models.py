#!/usr/bin/env python3
"""
Tax-Adjacent Models for Professional Tier
Focused on expense tracking, documentation, and educational resources
"""

from datetime import datetime, date
from decimal import Decimal
from .database import db
from enum import Enum

class ExpenseCategory(Enum):
    """Expense category enumeration"""
    FUEL = "fuel"
    MAINTENANCE = "maintenance"
    INSURANCE = "insurance"
    PARKING = "parking"
    TOLLS = "tolls"
    REGISTRATION = "registration"
    REPAIRS = "repairs"
    OTHER = "other"

class TripPurpose(Enum):
    """Trip purpose enumeration"""
    BUSINESS_TRAVEL = "business_travel"
    CLIENT_MEETING = "client_meeting"
    OFFICE_COMMUTE = "office_commute"
    BUSINESS_ERRAND = "business_errand"
    PERSONAL = "personal"
    OTHER = "other"

class DocumentType(Enum):
    """Document type enumeration"""
    RECEIPT = "receipt"
    INVOICE = "invoice"
    MAINTENANCE_RECORD = "maintenance_record"
    MILEAGE_LOG = "mileage_log"
    INSURANCE_DOCUMENT = "insurance_document"
    REGISTRATION = "registration"
    OTHER = "other"

class BusinessMileageLog(db.Model):
    """
    Business mileage log model for IRS-compliant mileage tracking
    """
    __tablename__ = 'business_mileage_logs'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Trip details
    trip_date = db.Column(db.Date, nullable=False, index=True)
    start_location = db.Column(db.String(255), nullable=False)
    end_location = db.Column(db.String(255), nullable=False)
    trip_purpose = db.Column(db.Enum(TripPurpose), nullable=False)
    business_purpose = db.Column(db.Text, nullable=True)
    
    # Distance tracking
    total_miles = db.Column(db.Float, nullable=False)
    business_miles = db.Column(db.Float, nullable=False, default=0.0)
    personal_miles = db.Column(db.Float, nullable=False, default=0.0)
    
    # IRS compliance fields
    odometer_start = db.Column(db.Integer, nullable=True)
    odometer_end = db.Column(db.Integer, nullable=True)
    is_irs_compliant = db.Column(db.Boolean, default=True, nullable=False)
    
    # GPS data (optional)
    start_latitude = db.Column(db.Float, nullable=True)
    start_longitude = db.Column(db.Float, nullable=True)
    end_latitude = db.Column(db.Float, nullable=True)
    end_longitude = db.Column(db.Float, nullable=True)
    gps_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Business use percentage
    business_use_percentage = db.Column(db.Float, nullable=False, default=100.0)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_mileage_user_date', 'user_id', 'trip_date'),
        db.Index('idx_mileage_purpose', 'trip_purpose'),
        db.Index('idx_mileage_irs_compliant', 'is_irs_compliant'),
        db.CheckConstraint('total_miles >= 0', name='check_positive_total_miles'),
        db.CheckConstraint('business_miles >= 0', name='check_positive_business_miles'),
        db.CheckConstraint('personal_miles >= 0', name='check_positive_personal_miles'),
        db.CheckConstraint('business_use_percentage >= 0.0 AND business_use_percentage <= 100.0', name='check_business_use_percentage'),
    )
    
    def __repr__(self):
        return f'<BusinessMileageLog {self.trip_date}: {self.business_miles} business miles>'
    
    def to_dict(self):
        """Convert mileage log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'trip_date': self.trip_date.isoformat(),
            'start_location': self.start_location,
            'end_location': self.end_location,
            'trip_purpose': self.trip_purpose.value,
            'business_purpose': self.business_purpose,
            'total_miles': self.total_miles,
            'business_miles': self.business_miles,
            'personal_miles': self.personal_miles,
            'odometer_start': self.odometer_start,
            'odometer_end': self.odometer_end,
            'is_irs_compliant': self.is_irs_compliant,
            'start_latitude': self.start_latitude,
            'start_longitude': self.start_longitude,
            'end_latitude': self.end_latitude,
            'end_longitude': self.end_longitude,
            'gps_verified': self.gps_verified,
            'business_use_percentage': self.business_use_percentage,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class ExpenseRecord(db.Model):
    """
    Expense record model for business vs personal expense tracking
    """
    __tablename__ = 'expense_records'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Expense details
    expense_date = db.Column(db.Date, nullable=False, index=True)
    category = db.Column(db.Enum(ExpenseCategory), nullable=False, index=True)
    subcategory = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Business classification
    is_business_expense = db.Column(db.Boolean, default=True, nullable=False)
    business_percentage = db.Column(db.Float, nullable=False, default=100.0)
    business_purpose = db.Column(db.Text, nullable=True)
    
    # Vendor information
    vendor_name = db.Column(db.String(255), nullable=True)
    vendor_address = db.Column(db.Text, nullable=True)
    
    # Receipt tracking
    receipt_attached = db.Column(db.Boolean, default=False, nullable=False)
    receipt_file_path = db.Column(db.String(500), nullable=True)
    receipt_upload_date = db.Column(db.DateTime, nullable=True)
    
    # Tax year
    tax_year = db.Column(db.Integer, nullable=False, index=True)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_expense_user_date', 'user_id', 'expense_date'),
        db.Index('idx_expense_category', 'category'),
        db.Index('idx_expense_tax_year', 'tax_year'),
        db.Index('idx_expense_business', 'is_business_expense'),
        db.CheckConstraint('amount >= 0', name='check_positive_amount'),
        db.CheckConstraint('business_percentage >= 0.0 AND business_percentage <= 100.0', name='check_business_percentage'),
    )
    
    def __repr__(self):
        return f'<ExpenseRecord {self.category.value}: ${self.amount} on {self.expense_date}>'
    
    def to_dict(self):
        """Convert expense record to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expense_date': self.expense_date.isoformat(),
            'category': self.category.value,
            'subcategory': self.subcategory,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0.0,
            'is_business_expense': self.is_business_expense,
            'business_percentage': self.business_percentage,
            'business_purpose': self.business_purpose,
            'vendor_name': self.vendor_name,
            'vendor_address': self.vendor_address,
            'receipt_attached': self.receipt_attached,
            'receipt_file_path': self.receipt_file_path,
            'receipt_upload_date': self.receipt_upload_date.isoformat() if self.receipt_upload_date else None,
            'tax_year': self.tax_year,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class MaintenanceDocument(db.Model):
    """
    Maintenance record model for vehicle maintenance documentation
    """
    __tablename__ = 'maintenance_documents'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Vehicle information
    vehicle_year = db.Column(db.Integer, nullable=False)
    vehicle_make = db.Column(db.String(50), nullable=False)
    vehicle_model = db.Column(db.String(100), nullable=False)
    vehicle_vin = db.Column(db.String(17), nullable=True)
    
    # Maintenance details
    service_date = db.Column(db.Date, nullable=False, index=True)
    service_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    odometer_reading = db.Column(db.Integer, nullable=False)
    
    # Cost information
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)
    labor_cost = db.Column(db.Numeric(10, 2), nullable=True)
    parts_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Service provider
    service_provider = db.Column(db.String(255), nullable=True)
    service_address = db.Column(db.Text, nullable=True)
    service_phone = db.Column(db.String(20), nullable=True)
    
    # Documentation
    invoice_attached = db.Column(db.Boolean, default=False, nullable=False)
    invoice_file_path = db.Column(db.String(500), nullable=True)
    warranty_info = db.Column(db.Text, nullable=True)
    warranty_expires = db.Column(db.Date, nullable=True)
    
    # Business use
    business_use_percentage = db.Column(db.Float, nullable=False, default=100.0)
    is_business_expense = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_maintenance_user_date', 'user_id', 'service_date'),
        db.Index('idx_maintenance_vehicle', 'vehicle_year', 'vehicle_make', 'vehicle_model'),
        db.Index('idx_maintenance_service_type', 'service_type'),
        db.CheckConstraint('total_cost >= 0', name='check_positive_total_cost'),
        db.CheckConstraint('labor_cost >= 0 OR labor_cost IS NULL', name='check_positive_labor_cost'),
        db.CheckConstraint('parts_cost >= 0 OR parts_cost IS NULL', name='check_positive_parts_cost'),
        db.CheckConstraint('business_use_percentage >= 0.0 AND business_use_percentage <= 100.0', name='check_maintenance_business_percentage'),
    )
    
    def __repr__(self):
        return f'<MaintenanceDocument {self.service_type}: ${self.total_cost} on {self.service_date}>'
    
    def to_dict(self):
        """Convert maintenance document to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_year': self.vehicle_year,
            'vehicle_make': self.vehicle_make,
            'vehicle_model': self.vehicle_model,
            'vehicle_vin': self.vehicle_vin,
            'service_date': self.service_date.isoformat(),
            'service_type': self.service_type,
            'description': self.description,
            'odometer_reading': self.odometer_reading,
            'total_cost': float(self.total_cost) if self.total_cost else 0.0,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'parts_cost': float(self.parts_cost) if self.parts_cost else None,
            'service_provider': self.service_provider,
            'service_address': self.service_address,
            'service_phone': self.service_phone,
            'invoice_attached': self.invoice_attached,
            'invoice_file_path': self.invoice_file_path,
            'warranty_info': self.warranty_info,
            'warranty_expires': self.warranty_expires.isoformat() if self.warranty_expires else None,
            'business_use_percentage': self.business_use_percentage,
            'is_business_expense': self.is_business_expense,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class VehicleUseTracking(db.Model):
    """
    Vehicle use tracking model for business use percentage tracking
    """
    __tablename__ = 'vehicle_use_tracking'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Vehicle information
    vehicle_year = db.Column(db.Integer, nullable=False)
    vehicle_make = db.Column(db.String(50), nullable=False)
    vehicle_model = db.Column(db.String(100), nullable=False)
    vehicle_vin = db.Column(db.String(17), nullable=True)
    
    # Tracking period
    tracking_year = db.Column(db.Integer, nullable=False, index=True)
    tracking_month = db.Column(db.Integer, nullable=False)
    
    # Mileage tracking
    total_miles = db.Column(db.Integer, nullable=False, default=0)
    business_miles = db.Column(db.Integer, nullable=False, default=0)
    personal_miles = db.Column(db.Integer, nullable=False, default=0)
    business_use_percentage = db.Column(db.Float, nullable=False, default=0.0)
    
    # Trip counts
    business_trips = db.Column(db.Integer, nullable=False, default=0)
    personal_trips = db.Column(db.Integer, nullable=False, default=0)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_use_tracking_user_year', 'user_id', 'tracking_year'),
        db.Index('idx_use_tracking_vehicle', 'vehicle_year', 'vehicle_make', 'vehicle_model'),
        db.Index('idx_use_tracking_month', 'tracking_year', 'tracking_month'),
        db.CheckConstraint('total_miles >= 0', name='check_positive_total_miles'),
        db.CheckConstraint('business_miles >= 0', name='check_positive_business_miles'),
        db.CheckConstraint('personal_miles >= 0', name='check_positive_personal_miles'),
        db.CheckConstraint('business_use_percentage >= 0.0 AND business_use_percentage <= 100.0', name='check_use_percentage'),
        db.CheckConstraint('tracking_month >= 1 AND tracking_month <= 12', name='check_valid_month'),
    )
    
    def __repr__(self):
        return f'<VehicleUseTracking {self.vehicle_year} {self.vehicle_make} {self.vehicle_model}: {self.business_use_percentage}% business use'
    
    def to_dict(self):
        """Convert vehicle use tracking to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_year': self.vehicle_year,
            'vehicle_make': self.vehicle_make,
            'vehicle_model': self.vehicle_model,
            'vehicle_vin': self.vehicle_vin,
            'tracking_year': self.tracking_year,
            'tracking_month': self.tracking_month,
            'total_miles': self.total_miles,
            'business_miles': self.business_miles,
            'personal_miles': self.personal_miles,
            'business_use_percentage': self.business_use_percentage,
            'business_trips': self.business_trips,
            'personal_trips': self.personal_trips,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class EducationalContent(db.Model):
    """
    Educational content model for tax deduction resources
    """
    __tablename__ = 'educational_content'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Content details
    title = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False, index=True)  # article, checklist, guide, summary
    category = db.Column(db.String(100), nullable=False, index=True)  # tax_deductions, irs_publications, preparation
    description = db.Column(db.Text, nullable=True)
    content_body = db.Column(db.Text, nullable=False)
    
    # IRS compliance
    is_irs_publication = db.Column(db.Boolean, default=False, nullable=False)
    irs_publication_number = db.Column(db.String(50), nullable=True)
    irs_publication_date = db.Column(db.Date, nullable=True)
    
    # Content metadata
    reading_time_minutes = db.Column(db.Integer, nullable=True)
    difficulty_level = db.Column(db.String(20), nullable=True)  # beginner, intermediate, advanced
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags
    
    # Status
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_content_type', 'content_type'),
        db.Index('idx_content_category', 'category'),
        db.Index('idx_content_published', 'is_published'),
        db.Index('idx_content_featured', 'is_featured'),
        db.CheckConstraint('reading_time_minutes >= 0 OR reading_time_minutes IS NULL', name='check_positive_reading_time'),
    )
    
    def __repr__(self):
        return f'<EducationalContent {self.title} ({self.content_type})>'
    
    def to_dict(self):
        """Convert educational content to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content_type': self.content_type,
            'category': self.category,
            'description': self.description,
            'content_body': self.content_body,
            'is_irs_publication': self.is_irs_publication,
            'irs_publication_number': self.irs_publication_number,
            'irs_publication_date': self.irs_publication_date.isoformat() if self.irs_publication_date else None,
            'reading_time_minutes': self.reading_time_minutes,
            'difficulty_level': self.difficulty_level,
            'tags': self.tags,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class ExpenseReport(db.Model):
    """
    Expense report model for generating annual expense summaries
    """
    __tablename__ = 'expense_reports'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Report details
    report_year = db.Column(db.Integer, nullable=False, index=True)
    report_type = db.Column(db.String(50), nullable=False)  # annual, quarterly, monthly
    report_period_start = db.Column(db.Date, nullable=False)
    report_period_end = db.Column(db.Date, nullable=False)
    
    # Expense summary
    total_expenses = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    business_expenses = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    personal_expenses = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    
    # Category breakdown
    fuel_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    maintenance_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    insurance_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    parking_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    toll_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    other_expenses = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    
    # Mileage summary
    total_miles = db.Column(db.Integer, nullable=False, default=0)
    business_miles = db.Column(db.Integer, nullable=False, default=0)
    personal_miles = db.Column(db.Integer, nullable=False, default=0)
    
    # Report generation
    generated_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    report_file_path = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_report_user_year', 'user_id', 'report_year'),
        db.Index('idx_report_type', 'report_type'),
        db.Index('idx_report_period', 'report_period_start', 'report_period_end'),
        db.CheckConstraint('total_expenses >= 0', name='check_positive_total_expenses'),
        db.CheckConstraint('business_expenses >= 0', name='check_positive_business_expenses'),
        db.CheckConstraint('personal_expenses >= 0', name='check_positive_personal_expenses'),
    )
    
    def __repr__(self):
        return f'<ExpenseReport {self.report_year} {self.report_type}: ${self.total_expenses}>'
    
    def to_dict(self):
        """Convert expense report to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_year': self.report_year,
            'report_type': self.report_type,
            'report_period_start': self.report_period_start.isoformat(),
            'report_period_end': self.report_period_end.isoformat(),
            'total_expenses': float(self.total_expenses) if self.total_expenses else 0.0,
            'business_expenses': float(self.business_expenses) if self.business_expenses else 0.0,
            'personal_expenses': float(self.personal_expenses) if self.personal_expenses else 0.0,
            'fuel_expenses': float(self.fuel_expenses) if self.fuel_expenses else 0.0,
            'maintenance_expenses': float(self.maintenance_expenses) if self.maintenance_expenses else 0.0,
            'insurance_expenses': float(self.insurance_expenses) if self.insurance_expenses else 0.0,
            'parking_expenses': float(self.parking_expenses) if self.parking_expenses else 0.0,
            'toll_expenses': float(self.toll_expenses) if self.toll_expenses else 0.0,
            'other_expenses': float(self.other_expenses) if self.other_expenses else 0.0,
            'total_miles': self.total_miles,
            'business_miles': self.business_miles,
            'personal_miles': self.personal_miles,
            'generated_date': self.generated_date.isoformat(),
            'report_file_path': self.report_file_path,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }
