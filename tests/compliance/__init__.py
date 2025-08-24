"""
Compliance Testing Module for MINGUS Application
Tests PCI DSS, GDPR, SOX, GLBA, and audit trail compliance
"""

__version__ = "1.0.0"
__author__ = "MINGUS Development Team"

from .test_comprehensive_compliance import ComprehensiveComplianceTests, ComplianceTestResult

__all__ = [
    'ComprehensiveComplianceTests',
    'ComplianceTestResult'
] 