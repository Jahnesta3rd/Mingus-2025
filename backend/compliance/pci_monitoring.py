#!/usr/bin/env python3
"""
PCI DSS Compliance Monitoring System
Comprehensive monitoring and assessment for PCI DSS compliance
"""

import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from functools import wraps

from flask import current_app, request, session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class PCIRequirement(Enum):
    """PCI DSS Requirements"""
    REQ_1_1 = "1.1"  # Install and maintain a firewall configuration
    REQ_1_2 = "1.2"  # Build firewall and router configurations
    REQ_1_3 = "1.3"  # Prohibit direct public access
    REQ_1_4 = "1.4"  # Install personal firewall software
    REQ_1_5 = "1.5"  # Document security policies
    REQ_2_1 = "2.1"  # Always change vendor-supplied defaults
    REQ_2_2 = "2.2"  # Develop configuration standards
    REQ_2_3 = "2.3"  # Encrypt all non-console access
    REQ_2_4 = "2.4"  # Maintain an inventory of systems
    REQ_3_1 = "3.1"  # Keep cardholder data storage to a minimum
    REQ_3_2 = "3.2"  # Do not store sensitive authentication data
    REQ_3_3 = "3.3"  # Mask PAN when displayed
    REQ_3_4 = "3.4"  # Render PAN unreadable anywhere stored
    REQ_3_5 = "3.5"  # Protect cryptographic keys
    REQ_3_6 = "3.6"  # Document and implement key management
    REQ_4_1 = "4.1"  # Use strong cryptography and security protocols
    REQ_4_2 = "4.2"  # Never send unprotected PANs
    REQ_5_1 = "5.1"  # Deploy anti-virus software
    REQ_5_2 = "5.2"  # Maintain anti-virus mechanisms
    REQ_5_3 = "5.3"  # Ensure anti-virus mechanisms are current
    REQ_6_1 = "6.1"  # Establish process to identify security vulnerabilities
    REQ_6_2 = "6.2"  # Ensure all systems have latest security patches
    REQ_6_3 = "6.3"  # Develop software applications securely
    REQ_6_4 = "6.4"  # Follow change control procedures
    REQ_6_5 = "6.5"  # Address common coding vulnerabilities
    REQ_6_6 = "6.6"  # For public-facing web applications
    REQ_7_1 = "7.1"  # Limit access to cardholder data
    REQ_7_2 = "7.2"  # Establish access control system
    REQ_8_1 = "8.1"  # Define and implement policies
    REQ_8_2 = "8.2"  # Identify all users
    REQ_8_3 = "8.3"  # Authenticate access to system components
    REQ_8_4 = "8.4"  # Document and communicate procedures
    REQ_8_5 = "8.5"  # Assign unique ID to each person
    REQ_8_6 = "8.6"  # Establish process for access requests
    REQ_8_7 = "8.7"  # Immediately revoke access
    REQ_8_8 = "8.8"  # Verify user identity before access
    REQ_9_1 = "9.1"  # Use appropriate facility entry controls
    REQ_9_2 = "9.2"  # Verify individual access to sensitive areas
    REQ_9_3 = "9.3"  # Ensure all visitors are authorized
    REQ_9_4 = "9.4"  # Maintain audit trail of physical access
    REQ_9_5 = "9.5"  # Physically secure all media
    REQ_9_6 = "9.6"  # Maintain strict control over storage
    REQ_9_7 = "9.7"  # Destroy media when no longer needed
    REQ_9_8 = "9.8"  # Protect devices that capture payment data
    REQ_9_9 = "9.9"  # Physically secure all payment devices
    REQ_10_1 = "10.1"  # Implement audit trails
    REQ_10_2 = "10.2"  # Automate audit trails
    REQ_10_3 = "10.3"  # Record audit trail entries
    REQ_10_4 = "10.4"  # Synchronize all critical system clocks
    REQ_10_5 = "10.5"  # Secure audit trails
    REQ_10_6 = "10.6"  # Review logs and security events
    REQ_10_7 = "10.7"  # Retain audit trail history
    REQ_11_1 = "11.1"  # Test security controls
    REQ_11_2 = "11.2"  # Run internal and external network scans
    REQ_11_3 = "11.3"  # Implement methodology for penetration testing
    REQ_11_4 = "11.4"  # Use intrusion detection/prevention
    REQ_11_5 = "11.5"  # Deploy file integrity monitoring
    REQ_12_1 = "12.1"  # Establish, publish, maintain, and disseminate
    REQ_12_2 = "12.2"  # Implement risk assessment process
    REQ_12_3 = "12.3"  # Develop usage policies
    REQ_12_4 = "12.4"  # Ensure policies clearly define responsibilities
    REQ_12_5 = "12.5"  # Assign information security responsibility
    REQ_12_6 = "12.6"  # Implement formal security awareness program
    REQ_12_7 = "12.7"  # Screen potential personnel
    REQ_12_8 = "12.8"  # Maintain and implement policies
    REQ_12_9 = "12.9"  # Additional requirements for service providers
    REQ_12_10 = "12.10"  # Implement incident response plan

class ComplianceStatus(Enum):
    """Compliance status enumeration"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    IN_PROGRESS = "in_progress"

class ComplianceSeverity(Enum):
    """Compliance severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ComplianceCheck:
    """Individual compliance check result"""
    requirement: PCIRequirement
    status: ComplianceStatus
    severity: ComplianceSeverity
    description: str
    details: Dict[str, Any]
    last_checked: datetime
    next_check: datetime
    remediation_required: bool
    remediation_notes: Optional[str] = None

@dataclass
class ComplianceAssessment:
    """Complete PCI DSS compliance assessment"""
    assessment_id: str
    assessment_date: datetime
    overall_score: float  # 0.0 to 100.0
    compliance_status: ComplianceStatus
    requirements_checked: int
    requirements_compliant: int
    requirements_non_compliant: int
    requirements_partial: int
    critical_findings: List[str]
    recommendations: List[str]
    checks: List[ComplianceCheck]
    metadata: Dict[str, Any]

class PCIDSSComplianceMonitor:
    """Comprehensive PCI DSS compliance monitoring system"""
    
    def __init__(self):
        self.database_url = current_app.config.get('DATABASE_URL')
        self.engine = None
        self.SessionLocal = None
        self.secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
        
        # Initialize database connection
        self._init_database()
        
        # Initialize compliance tables
        self._create_compliance_tables()
        
        # Load compliance requirements
        self.compliance_requirements = self._load_compliance_requirements()
        
        logger.info("PCI DSS compliance monitor initialized")
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("PCI DSS compliance database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize PCI DSS compliance database: {e}")
            raise
    
    def _create_compliance_tables(self):
        """Create compliance monitoring tables"""
        try:
            with self.engine.connect() as conn:
                # Create compliance assessments table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pci_compliance_assessments (
                        id SERIAL PRIMARY KEY,
                        assessment_id VARCHAR(255) UNIQUE NOT NULL,
                        assessment_date TIMESTAMP WITH TIME ZONE NOT NULL,
                        overall_score DECIMAL(5,2) NOT NULL,
                        compliance_status VARCHAR(50) NOT NULL,
                        requirements_checked INTEGER NOT NULL,
                        requirements_compliant INTEGER NOT NULL,
                        requirements_non_compliant INTEGER NOT NULL,
                        requirements_partial INTEGER NOT NULL,
                        critical_findings JSONB,
                        recommendations JSONB,
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                
                # Create compliance checks table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pci_compliance_checks (
                        id SERIAL PRIMARY KEY,
                        assessment_id VARCHAR(255) NOT NULL,
                        requirement VARCHAR(20) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        description TEXT NOT NULL,
                        details JSONB,
                        last_checked TIMESTAMP WITH TIME ZONE NOT NULL,
                        next_check TIMESTAMP WITH TIME ZONE NOT NULL,
                        remediation_required BOOLEAN DEFAULT FALSE,
                        remediation_notes TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        FOREIGN KEY (assessment_id) REFERENCES pci_compliance_assessments(assessment_id)
                    )
                """))
                
                # Create indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pci_assessment_date 
                    ON pci_compliance_assessments(assessment_date)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pci_requirement 
                    ON pci_compliance_checks(requirement)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pci_status 
                    ON pci_compliance_checks(status)
                """))
                
                conn.commit()
                logger.info("PCI DSS compliance tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create PCI DSS compliance tables: {e}")
            raise
    
    def _load_compliance_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Load PCI DSS compliance requirements"""
        return {
            '3.1': {
                'title': 'Keep cardholder data storage to a minimum',
                'description': 'Implement policies and procedures that keep cardholder data storage to a minimum',
                'severity': ComplianceSeverity.CRITICAL,
                'check_function': self._check_data_storage_minimization,
                'frequency_days': 30
            },
            '3.2': {
                'title': 'Do not store sensitive authentication data',
                'description': 'Do not store sensitive authentication data after authorization',
                'severity': ComplianceSeverity.CRITICAL,
                'check_function': self._check_sensitive_auth_data,
                'frequency_days': 7
            },
            '3.4': {
                'title': 'Render PAN unreadable anywhere stored',
                'description': 'Render PAN unreadable anywhere it is stored',
                'severity': ComplianceSeverity.CRITICAL,
                'check_function': self._check_pan_encryption,
                'frequency_days': 7
            },
            '4.1': {
                'title': 'Use strong cryptography and security protocols',
                'description': 'Use strong cryptography and security protocols to safeguard sensitive cardholder data',
                'severity': ComplianceSeverity.HIGH,
                'check_function': self._check_transmission_security,
                'frequency_days': 30
            },
            '7.1': {
                'title': 'Limit access to cardholder data',
                'description': 'Limit access to cardholder data to only those individuals whose job requires such access',
                'severity': ComplianceSeverity.HIGH,
                'check_function': self._check_access_controls,
                'frequency_days': 30
            },
            '8.1': {
                'title': 'Define and implement policies',
                'description': 'Define and implement policies and procedures to ensure proper user identification',
                'severity': ComplianceSeverity.HIGH,
                'check_function': self._check_user_identification,
                'frequency_days': 30
            },
            '10.1': {
                'title': 'Implement audit trails',
                'description': 'Implement audit trails to link all access to system components',
                'severity': ComplianceSeverity.HIGH,
                'check_function': self._check_audit_trails,
                'frequency_days': 7
            },
            '11.1': {
                'title': 'Test security controls',
                'description': 'Test security controls regularly',
                'severity': ComplianceSeverity.MEDIUM,
                'check_function': self._check_security_testing,
                'frequency_days': 90
            },
            '12.1': {
                'title': 'Establish security policies',
                'description': 'Establish, publish, maintain, and disseminate a security policy',
                'severity': ComplianceSeverity.MEDIUM,
                'check_function': self._check_security_policies,
                'frequency_days': 90
            }
        }
    
    def run_compliance_assessment(self) -> ComplianceAssessment:
        """Run comprehensive PCI DSS compliance assessment"""
        try:
            assessment_id = self._generate_assessment_id()
            checks = []
            
            # Run checks for each requirement
            for req_id, req_config in self.compliance_requirements.items():
                check = self._run_requirement_check(req_id, req_config)
                checks.append(check)
            
            # Calculate overall compliance score
            overall_score = self._calculate_compliance_score(checks)
            
            # Determine overall compliance status
            compliance_status = self._determine_compliance_status(overall_score, checks)
            
            # Generate findings and recommendations
            critical_findings = self._generate_critical_findings(checks)
            recommendations = self._generate_recommendations(checks)
            
            # Create assessment
            assessment = ComplianceAssessment(
                assessment_id=assessment_id,
                assessment_date=datetime.utcnow(),
                overall_score=overall_score,
                compliance_status=compliance_status,
                requirements_checked=len(checks),
                requirements_compliant=len([c for c in checks if c.status == ComplianceStatus.COMPLIANT]),
                requirements_non_compliant=len([c for c in checks if c.status == ComplianceStatus.NON_COMPLIANT]),
                requirements_partial=len([c for c in checks if c.status == ComplianceStatus.PARTIALLY_COMPLIANT]),
                critical_findings=critical_findings,
                recommendations=recommendations,
                checks=checks,
                metadata={
                    'assessment_version': '1.0',
                    'pci_dss_version': '4.0'
                }
            )
            
            # Store assessment
            self._store_compliance_assessment(assessment)
            
            logger.info(f"PCI DSS compliance assessment completed: {overall_score}% compliant")
            return assessment
            
        except Exception as e:
            logger.error(f"Error in PCI DSS compliance assessment: {e}")
            raise
    
    def _run_requirement_check(self, req_id: str, req_config: Dict[str, Any]) -> ComplianceCheck:
        """Run check for specific PCI DSS requirement"""
        try:
            check_function = req_config['check_function']
            result = check_function()
            
            return ComplianceCheck(
                requirement=PCIRequirement(req_id),
                status=result['status'],
                severity=req_config['severity'],
                description=req_config['description'],
                details=result['details'],
                last_checked=datetime.utcnow(),
                next_check=datetime.utcnow() + timedelta(days=req_config['frequency_days']),
                remediation_required=result['status'] != ComplianceStatus.COMPLIANT,
                remediation_notes=result.get('remediation_notes')
            )
            
        except Exception as e:
            logger.error(f"Error checking requirement {req_id}: {e}")
            return ComplianceCheck(
                requirement=PCIRequirement(req_id),
                status=ComplianceStatus.NON_COMPLIANT,
                severity=req_config['severity'],
                description=req_config['description'],
                details={'error': str(e)},
                last_checked=datetime.utcnow(),
                next_check=datetime.utcnow() + timedelta(days=req_config['frequency_days']),
                remediation_required=True,
                remediation_notes=f"Check failed: {str(e)}"
            )
    
    def _check_data_storage_minimization(self) -> Dict[str, Any]:
        """Check requirement 3.1: Data storage minimization"""
        try:
            # Check if any cardholder data is stored
            with self.SessionLocal() as db_session:
                # Check for full PAN storage
                result = db_session.execute(text("""
                    SELECT COUNT(*) as count FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND column_name LIKE '%card%' 
                    OR column_name LIKE '%pan%'
                    OR column_name LIKE '%credit%'
                """))
                
                card_columns = result.fetchone().count
                
                # Check for actual card data in tables
                result = db_session.execute(text("""
                    SELECT COUNT(*) as count FROM payment_audit_log 
                    WHERE metadata::text LIKE '%card_number%'
                    OR metadata::text LIKE '%pan%'
                """))
                
                card_data_count = result.fetchone().count
                
                if card_data_count > 0:
                    return {
                        'status': ComplianceStatus.NON_COMPLIANT,
                        'details': {
                            'card_columns_found': card_columns,
                            'card_data_instances': card_data_count,
                            'risk': 'Cardholder data found in database'
                        },
                        'remediation_notes': 'Remove all cardholder data from database storage'
                    }
                else:
                    return {
                        'status': ComplianceStatus.COMPLIANT,
                        'details': {
                            'card_columns_found': card_columns,
                            'card_data_instances': 0,
                            'risk': 'No cardholder data found'
                        }
                    }
                    
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Database check failed: {str(e)}'
            }
    
    def _check_sensitive_auth_data(self) -> Dict[str, Any]:
        """Check requirement 3.2: Sensitive authentication data"""
        try:
            # Check for CVV, PIN, or full track data storage
            with self.SessionLocal() as db_session:
                result = db_session.execute(text("""
                    SELECT COUNT(*) as count FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND (column_name LIKE '%cvv%' 
                    OR column_name LIKE '%cvc%' 
                    OR column_name LIKE '%pin%'
                    OR column_name LIKE '%track%')
                """))
                
                sensitive_columns = result.fetchone().count
                
                if sensitive_columns > 0:
                    return {
                        'status': ComplianceStatus.NON_COMPLIANT,
                        'details': {
                            'sensitive_columns_found': sensitive_columns,
                            'risk': 'Sensitive authentication data columns found'
                        },
                        'remediation_notes': 'Remove all sensitive authentication data columns'
                    }
                else:
                    return {
                        'status': ComplianceStatus.COMPLIANT,
                        'details': {
                            'sensitive_columns_found': 0,
                            'risk': 'No sensitive authentication data found'
                        }
                    }
                    
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Database check failed: {str(e)}'
            }
    
    def _check_pan_encryption(self) -> Dict[str, Any]:
        """Check requirement 3.4: PAN encryption"""
        try:
            # Check if any PAN data is stored unencrypted
            with self.SessionLocal() as db_session:
                result = db_session.execute(text("""
                    SELECT COUNT(*) as count FROM payment_audit_log 
                    WHERE masked_pan IS NOT NULL 
                    AND LENGTH(masked_pan) > 4
                """))
                
                full_pan_count = result.fetchone().count
                
                if full_pan_count > 0:
                    return {
                        'status': ComplianceStatus.NON_COMPLIANT,
                        'details': {
                            'full_pan_instances': full_pan_count,
                            'risk': 'Full PAN data found in database'
                        },
                        'remediation_notes': 'Ensure all PAN data is properly masked or encrypted'
                    }
                else:
                    return {
                        'status': ComplianceStatus.COMPLIANT,
                        'details': {
                            'full_pan_instances': 0,
                            'risk': 'No full PAN data found'
                        }
                    }
                    
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Database check failed: {str(e)}'
            }
    
    def _check_transmission_security(self) -> Dict[str, Any]:
        """Check requirement 4.1: Transmission security"""
        try:
            # Check HTTPS enforcement
            https_enabled = current_app.config.get('HTTPS_ENFORCED', True)
            
            # Check TLS version
            tls_version = current_app.config.get('TLS_VERSION', '1.2')
            
            if https_enabled and tls_version >= '1.2':
                return {
                    'status': ComplianceStatus.COMPLIANT,
                    'details': {
                        'https_enabled': https_enabled,
                        'tls_version': tls_version,
                        'risk': 'Secure transmission configured'
                    }
                }
            else:
                return {
                    'status': ComplianceStatus.NON_COMPLIANT,
                    'details': {
                        'https_enabled': https_enabled,
                        'tls_version': tls_version,
                        'risk': 'Insecure transmission configuration'
                    },
                    'remediation_notes': 'Enable HTTPS and use TLS 1.2 or higher'
                }
                
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Configuration check failed: {str(e)}'
            }
    
    def _check_access_controls(self) -> Dict[str, Any]:
        """Check requirement 7.1: Access controls"""
        try:
            # Check if role-based access control is implemented
            rbac_enabled = current_app.config.get('RBAC_ENABLED', True)
            
            # Check if access logging is enabled
            access_logging = current_app.config.get('ACCESS_LOGGING_ENABLED', True)
            
            if rbac_enabled and access_logging:
                return {
                    'status': ComplianceStatus.COMPLIANT,
                    'details': {
                        'rbac_enabled': rbac_enabled,
                        'access_logging': access_logging,
                        'risk': 'Access controls properly configured'
                    }
                }
            else:
                return {
                    'status': ComplianceStatus.PARTIALLY_COMPLIANT,
                    'details': {
                        'rbac_enabled': rbac_enabled,
                        'access_logging': access_logging,
                        'risk': 'Access controls partially configured'
                    },
                    'remediation_notes': 'Enable role-based access control and access logging'
                }
                
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Configuration check failed: {str(e)}'
            }
    
    def _check_user_identification(self) -> Dict[str, Any]:
        """Check requirement 8.1: User identification"""
        try:
            # Check if user authentication is required
            auth_required = current_app.config.get('AUTHENTICATION_REQUIRED', True)
            
            # Check if MFA is available
            mfa_available = current_app.config.get('MFA_AVAILABLE', True)
            
            if auth_required:
                return {
                    'status': ComplianceStatus.COMPLIANT,
                    'details': {
                        'auth_required': auth_required,
                        'mfa_available': mfa_available,
                        'risk': 'User identification properly configured'
                    }
                }
            else:
                return {
                    'status': ComplianceStatus.NON_COMPLIANT,
                    'details': {
                        'auth_required': auth_required,
                        'mfa_available': mfa_available,
                        'risk': 'User identification not properly configured'
                    },
                    'remediation_notes': 'Enable user authentication for all access'
                }
                
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Configuration check failed: {str(e)}'
            }
    
    def _check_audit_trails(self) -> Dict[str, Any]:
        """Check requirement 10.1: Audit trails"""
        try:
            # Check if audit logging is enabled
            audit_logging = current_app.config.get('AUDIT_LOGGING_ENABLED', True)
            
            # Check if payment audit logging exists
            with self.SessionLocal() as db_session:
                result = db_session.execute(text("""
                    SELECT COUNT(*) as count FROM payment_audit_log 
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """))
                
                recent_audit_events = result.fetchone().count
            
            if audit_logging and recent_audit_events > 0:
                return {
                    'status': ComplianceStatus.COMPLIANT,
                    'details': {
                        'audit_logging': audit_logging,
                        'recent_audit_events': recent_audit_events,
                        'risk': 'Audit trails properly configured'
                    }
                }
            else:
                return {
                    'status': ComplianceStatus.NON_COMPLIANT,
                    'details': {
                        'audit_logging': audit_logging,
                        'recent_audit_events': recent_audit_events,
                        'risk': 'Audit trails not properly configured'
                    },
                    'remediation_notes': 'Enable comprehensive audit logging'
                }
                
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Audit check failed: {str(e)}'
            }
    
    def _check_security_testing(self) -> Dict[str, Any]:
        """Check requirement 11.1: Security testing"""
        try:
            # Check if security testing is configured
            security_testing = current_app.config.get('SECURITY_TESTING_ENABLED', True)
            
            # Check last security test date
            last_test_date = current_app.config.get('LAST_SECURITY_TEST_DATE')
            
            if security_testing and last_test_date:
                days_since_test = (datetime.utcnow() - last_test_date).days
                
                if days_since_test <= 90:  # Quarterly testing
                    return {
                        'status': ComplianceStatus.COMPLIANT,
                        'details': {
                            'security_testing': security_testing,
                            'days_since_test': days_since_test,
                            'risk': 'Security testing up to date'
                        }
                    }
                else:
                    return {
                        'status': ComplianceStatus.PARTIALLY_COMPLIANT,
                        'details': {
                            'security_testing': security_testing,
                            'days_since_test': days_since_test,
                            'risk': 'Security testing overdue'
                        },
                        'remediation_notes': 'Schedule security testing within 90 days'
                    }
            else:
                return {
                    'status': ComplianceStatus.NON_COMPLIANT,
                    'details': {
                        'security_testing': security_testing,
                        'last_test_date': last_test_date,
                        'risk': 'Security testing not configured'
                    },
                    'remediation_notes': 'Configure and schedule security testing'
                }
                
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Security testing check failed: {str(e)}'
            }
    
    def _check_security_policies(self) -> Dict[str, Any]:
        """Check requirement 12.1: Security policies"""
        try:
            # Check if security policies exist
            security_policies = current_app.config.get('SECURITY_POLICIES_ENABLED', True)
            
            # Check if incident response plan exists
            incident_response = current_app.config.get('INCIDENT_RESPONSE_PLAN', True)
            
            if security_policies and incident_response:
                return {
                    'status': ComplianceStatus.COMPLIANT,
                    'details': {
                        'security_policies': security_policies,
                        'incident_response': incident_response,
                        'risk': 'Security policies properly configured'
                    }
                }
            else:
                return {
                    'status': ComplianceStatus.PARTIALLY_COMPLIANT,
                    'details': {
                        'security_policies': security_policies,
                        'incident_response': incident_response,
                        'risk': 'Security policies partially configured'
                    },
                    'remediation_notes': 'Develop and implement security policies and incident response plan'
                }
                
        except Exception as e:
            return {
                'status': ComplianceStatus.NON_COMPLIANT,
                'details': {'error': str(e)},
                'remediation_notes': f'Policy check failed: {str(e)}'
            }
    
    def _calculate_compliance_score(self, checks: List[ComplianceCheck]) -> float:
        """Calculate overall compliance score"""
        if not checks:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for check in checks:
            # Assign weights based on severity
            if check.severity == ComplianceSeverity.CRITICAL:
                weight = 4.0
            elif check.severity == ComplianceSeverity.HIGH:
                weight = 3.0
            elif check.severity == ComplianceSeverity.MEDIUM:
                weight = 2.0
            else:
                weight = 1.0
            
            # Calculate score for this check
            if check.status == ComplianceStatus.COMPLIANT:
                score = 100.0
            elif check.status == ComplianceStatus.PARTIALLY_COMPLIANT:
                score = 50.0
            elif check.status == ComplianceStatus.NOT_APPLICABLE:
                score = 100.0
            else:
                score = 0.0
            
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_compliance_status(self, score: float, checks: List[ComplianceCheck]) -> ComplianceStatus:
        """Determine overall compliance status"""
        if score >= 95.0 and not any(c.status == ComplianceStatus.NON_COMPLIANT for c in checks):
            return ComplianceStatus.COMPLIANT
        elif score >= 80.0:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            return ComplianceStatus.NON_COMPLIANT
    
    def _generate_critical_findings(self, checks: List[ComplianceCheck]) -> List[str]:
        """Generate critical findings from compliance checks"""
        findings = []
        
        for check in checks:
            if (check.severity == ComplianceSeverity.CRITICAL and 
                check.status == ComplianceStatus.NON_COMPLIANT):
                findings.append(f"Critical: {check.description}")
        
        return findings
    
    def _generate_recommendations(self, checks: List[ComplianceCheck]) -> List[str]:
        """Generate recommendations from compliance checks"""
        recommendations = []
        
        for check in checks:
            if check.remediation_required and check.remediation_notes:
                recommendations.append(f"{check.requirement.value}: {check.remediation_notes}")
        
        return recommendations
    
    def _generate_assessment_id(self) -> str:
        """Generate unique assessment ID"""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        random_component = hashlib.md5(f"{timestamp}{self.secret_key}".encode()).hexdigest()[:8]
        return f"pci_assessment_{timestamp}_{random_component}"
    
    def _store_compliance_assessment(self, assessment: ComplianceAssessment):
        """Store compliance assessment in database"""
        try:
            with self.SessionLocal() as db_session:
                # Store assessment
                db_session.execute(text("""
                    INSERT INTO pci_compliance_assessments (
                        assessment_id, assessment_date, overall_score, compliance_status,
                        requirements_checked, requirements_compliant, requirements_non_compliant,
                        requirements_partial, critical_findings, recommendations, metadata
                    ) VALUES (
                        :assessment_id, :assessment_date, :overall_score, :compliance_status,
                        :requirements_checked, :requirements_compliant, :requirements_non_compliant,
                        :requirements_partial, :critical_findings, :recommendations, :metadata
                    )
                """), {
                    'assessment_id': assessment.assessment_id,
                    'assessment_date': assessment.assessment_date,
                    'overall_score': assessment.overall_score,
                    'compliance_status': assessment.compliance_status.value,
                    'requirements_checked': assessment.requirements_checked,
                    'requirements_compliant': assessment.requirements_compliant,
                    'requirements_non_compliant': assessment.requirements_non_compliant,
                    'requirements_partial': assessment.requirements_partial,
                    'critical_findings': json.dumps(assessment.critical_findings),
                    'recommendations': json.dumps(assessment.recommendations),
                    'metadata': json.dumps(assessment.metadata)
                })
                
                # Store individual checks
                for check in assessment.checks:
                    db_session.execute(text("""
                        INSERT INTO pci_compliance_checks (
                            assessment_id, requirement, status, severity, description,
                            details, last_checked, next_check, remediation_required, remediation_notes
                        ) VALUES (
                            :assessment_id, :requirement, :status, :severity, :description,
                            :details, :last_checked, :next_check, :remediation_required, :remediation_notes
                        )
                    """), {
                        'assessment_id': assessment.assessment_id,
                        'requirement': check.requirement.value,
                        'status': check.status.value,
                        'severity': check.severity.value,
                        'description': check.description,
                        'details': json.dumps(check.details),
                        'last_checked': check.last_checked,
                        'next_check': check.next_check,
                        'remediation_required': check.remediation_required,
                        'remediation_notes': check.remediation_notes
                    })
                
                db_session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store compliance assessment: {e}")
            raise
    
    def get_latest_assessment(self) -> Optional[ComplianceAssessment]:
        """Get the latest compliance assessment"""
        try:
            with self.SessionLocal() as db_session:
                result = db_session.execute(text("""
                    SELECT * FROM pci_compliance_assessments 
                    ORDER BY assessment_date DESC 
                    LIMIT 1
                """))
                
                assessment_row = result.fetchone()
                if not assessment_row:
                    return None
                
                # Get checks for this assessment
                checks_result = db_session.execute(text("""
                    SELECT * FROM pci_compliance_checks 
                    WHERE assessment_id = :assessment_id
                """), {
                    'assessment_id': assessment_row.assessment_id
                })
                
                checks = []
                for check_row in checks_result:
                    checks.append(ComplianceCheck(
                        requirement=PCIRequirement(check_row.requirement),
                        status=ComplianceStatus(check_row.status),
                        severity=ComplianceSeverity(check_row.severity),
                        description=check_row.description,
                        details=json.loads(check_row.details),
                        last_checked=check_row.last_checked,
                        next_check=check_row.next_check,
                        remediation_required=check_row.remediation_required,
                        remediation_notes=check_row.remediation_notes
                    ))
                
                return ComplianceAssessment(
                    assessment_id=assessment_row.assessment_id,
                    assessment_date=assessment_row.assessment_date,
                    overall_score=float(assessment_row.overall_score),
                    compliance_status=ComplianceStatus(assessment_row.compliance_status),
                    requirements_checked=assessment_row.requirements_checked,
                    requirements_compliant=assessment_row.requirements_compliant,
                    requirements_non_compliant=assessment_row.requirements_non_compliant,
                    requirements_partial=assessment_row.requirements_partial,
                    critical_findings=json.loads(assessment_row.critical_findings),
                    recommendations=json.loads(assessment_row.recommendations),
                    checks=checks,
                    metadata=json.loads(assessment_row.metadata)
                )
                
        except Exception as e:
            logger.error(f"Failed to get latest assessment: {e}")
            return None

# Global PCI DSS compliance monitor instance
_pci_compliance_monitor = None

def get_pci_compliance_monitor() -> PCIDSSComplianceMonitor:
    """Get global PCI DSS compliance monitor instance"""
    global _pci_compliance_monitor
    if _pci_compliance_monitor is None:
        _pci_compliance_monitor = PCIDSSComplianceMonitor()
    return _pci_compliance_monitor
