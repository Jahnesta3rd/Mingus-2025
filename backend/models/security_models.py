"""
Security Models for MINGUS Assessment System
Models for tracking security events, validation failures, and audit logs
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class SecurityEvent(Base):
    """Model for tracking security events and potential attacks"""
    
    __tablename__ = 'security_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    field_name = Column(String(100), nullable=True)
    pattern = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=True, index=True)
    request_path = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_data = Column(JSON, nullable=True)
    severity = Column(String(20), default='medium', index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SecurityEvent(id='{self.id}', type='{self.event_type}', ip='{self.ip_address}')>"

class ValidationFailure(Base):
    """Model for tracking input validation failures"""
    
    __tablename__ = 'validation_failures'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(String(200), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    error_type = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    input_value = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ValidationFailure(id='{self.id}', endpoint='{self.endpoint}', field='{self.field_name}')>"

class AssessmentSecurityLog(Base):
    """Model for tracking assessment-specific security events"""
    
    __tablename__ = 'assessment_security_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_type = Column(String(100), nullable=False, index=True)
    assessment_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AssessmentSecurityLog(id='{self.id}', assessment='{self.assessment_type}', event='{self.event_type}')>"

class RateLimitViolation(Base):
    """Model for tracking rate limit violations"""
    
    __tablename__ = 'rate_limit_violations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(String(200), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    limit_type = Column(String(50), nullable=False, index=True)
    limit_value = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    violation_count = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<RateLimitViolation(id='{self.id}', endpoint='{self.endpoint}', ip='{self.ip_address}')>"

class SecurityMetrics(Base):
    """Model for storing security metrics and statistics"""
    
    __tablename__ = 'security_metrics'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)
    metric_value = Column(Integer, nullable=False)
    metric_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SecurityMetrics(id='{self.id}', type='{self.metric_type}', value={self.metric_value})>" 