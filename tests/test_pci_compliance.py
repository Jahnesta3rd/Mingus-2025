"""
MINGUS Application - PCI Compliance Test Suite
==============================================

Comprehensive test suite for PCI DSS compliance validation, security testing,
and compliance reporting for the MINGUS personal finance application.

Test Coverage:
- PCI compliance validation
- Card data validation and sanitization
- Security test cases for payment processing
- Compliance reporting tests
- Middleware security testing
- Payment model security validation

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import pytest
import json
import hashlib
import hmac
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.payment.pci_compliance import (
    PCIComplianceValidator, CardDataValidator, CardDataTokenizer,
    PCIRequirement, ComplianceLevel, ComplianceStatus
)
from backend.payment.stripe_service import SecureStripeService
from backend.security.pci_middleware import PCIMiddleware
from backend.models.payment import (
    MINGUSCustomer, MINGUSPaymentMethod, MINGUSPaymentIntent,
    MINGUSInvoice, PaymentStatus, PaymentMethodType
)


class TestCardDataValidator:
    """Test card data validation for PCI compliance."""
    
    def test_validate_valid_visa_card(self):
        """Test validation of valid Visa card number."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("4111111111111111")
        assert is_valid is True
        assert "Valid visa card" in message
    
    def test_validate_valid_mastercard(self):
        """Test validation of valid Mastercard number."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("5555555555554444")
        assert is_valid is True
        assert "Valid mastercard" in message
    
    def test_validate_valid_amex_card(self):
        """Test validation of valid American Express card number."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("378282246310005")
        assert is_valid is True
        assert "Valid amex" in message
    
    def test_validate_invalid_card_number(self):
        """Test validation of invalid card number."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("1234567890123456")
        assert is_valid is False
        assert "Invalid card number checksum" in message
    
    def test_validate_empty_card_number(self):
        """Test validation of empty card number."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("")
        assert is_valid is False
        assert "Card number is required" in message
    
    def test_validate_card_with_spaces(self):
        """Test validation of card number with spaces."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("4111 1111 1111 1111")
        assert is_valid is True
        assert "Valid visa card" in message
    
    def test_validate_card_with_dashes(self):
        """Test validation of card number with dashes."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_card_number("4111-1111-1111-1111")
        assert is_valid is True
        assert "Valid visa card" in message
    
    def test_validate_expiry_date_valid(self):
        """Test validation of valid expiry date."""
        validator = CardDataValidator()
        next_year = datetime.now().year + 1
        is_valid, message = validator.validate_expiry_date(12, next_year)
        assert is_valid is True
        assert "Valid expiry date" in message
    
    def test_validate_expiry_date_expired(self):
        """Test validation of expired card."""
        validator = CardDataValidator()
        last_year = datetime.now().year - 1
        is_valid, message = validator.validate_expiry_date(12, last_year)
        assert is_valid is False
        assert "Card has expired" in message
    
    def test_validate_expiry_date_invalid_month(self):
        """Test validation of invalid expiry month."""
        validator = CardDataValidator()
        next_year = datetime.now().year + 1
        is_valid, message = validator.validate_expiry_date(13, next_year)
        assert is_valid is False
        assert "Invalid expiry month" in message
    
    def test_validate_cvv_valid(self):
        """Test validation of valid CVV."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_cvv("123", "visa")
        assert is_valid is True
        assert "Valid CVV" in message
    
    def test_validate_cvv_invalid_length(self):
        """Test validation of invalid CVV length."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_cvv("12", "visa")
        assert is_valid is False
        assert "Invalid CVV length" in message
    
    def test_validate_cvv_non_numeric(self):
        """Test validation of non-numeric CVV."""
        validator = CardDataValidator()
        is_valid, message = validator.validate_cvv("abc", "visa")
        assert is_valid is False
        assert "CVV must contain only digits" in message


class TestCardDataTokenizer:
    """Test card data tokenization for PCI compliance."""
    
    def test_tokenize_card_data(self):
        """Test tokenization of card data."""
        tokenizer = CardDataTokenizer()
        card_data = {
            'card_number': '4111111111111111',
            'card_type': 'visa',
            'exp_month': 12,
            'exp_year': 2025,
            'billing_address': {'city': 'New York'}
        }
        
        tokenized = tokenizer.tokenize_card_data(card_data)
        
        # Should not contain original card number
        assert 'card_number' not in tokenized
        
        # Should contain secure references
        assert 'card_hash' in tokenized
        assert 'card_token' in tokenized
        assert 'secure_reference' in tokenized
        
        # Should contain non-sensitive data
        assert tokenized['card_type'] == 'visa'
        assert tokenized['exp_month'] == 12
        assert tokenized['exp_year'] == 2025
        assert tokenized['billing_address'] == {'city': 'New York'}
    
    def test_tokenize_card_data_no_card_number(self):
        """Test tokenization without card number."""
        tokenizer = CardDataTokenizer()
        card_data = {
            'card_type': 'visa',
            'exp_month': 12,
            'exp_year': 2025
        }
        
        tokenized = tokenizer.tokenize_card_data(card_data)
        
        # Should not contain card-related fields
        assert 'card_hash' not in tokenized
        assert 'card_token' not in tokenized
        
        # Should contain other data
        assert tokenized['card_type'] == 'visa'
        assert tokenized['exp_month'] == 12
        assert tokenized['exp_year'] == 2025
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        tokenizer = CardDataTokenizer()
        original_data = "test_data"
        token = tokenizer._generate_secure_token(original_data)
        
        is_valid = tokenizer.verify_token(token, original_data)
        assert is_valid is True
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        tokenizer = CardDataTokenizer()
        original_data = "test_data"
        invalid_token = "invalid_token"
        
        is_valid = tokenizer.verify_token(invalid_token, original_data)
        assert is_valid is False


class TestPCIComplianceValidator:
    """Test PCI DSS compliance validation."""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app for testing."""
        app = Mock()
        app.config = {
            'STRIPE_SECRET_KEY': 'test_key',
            'STRIPE_WEBHOOK_SECRET': 'test_webhook_secret',
            'HTTPS_ENFORCED': True,
            'TLS_VERSION': '1.2'
        }
        return app
    
    @pytest.fixture
    def validator(self, mock_app):
        """Create PCI compliance validator instance."""
        validator = PCIComplianceValidator()
        validator.init_app(mock_app)
        return validator
    
    def test_init_app(self, mock_app):
        """Test validator initialization with Flask app."""
        validator = PCIComplianceValidator()
        validator.init_app(mock_app)
        
        assert validator.app == mock_app
        assert validator.stripe_secret == 'test_key'
        assert validator.webhook_secret == 'test_webhook_secret'
    
    def test_validate_payment_data_valid(self, validator):
        """Test validation of valid payment data."""
        payment_data = {
            'card_number': '4111111111111111',
            'exp_month': 12,
            'exp_year': 2025,
            'cvv': '123',
            'card_type': 'visa'
        }
        
        result = validator.validate_payment_data(payment_data)
        
        assert result['compliant'] is True
        assert len(result['errors']) == 0
        assert 'card_validation' in result
        assert 'pci_requirements' in result
    
    def test_validate_payment_data_invalid_card(self, validator):
        """Test validation of invalid payment data."""
        payment_data = {
            'card_number': '1234567890123456',  # Invalid checksum
            'exp_month': 12,
            'exp_year': 2025,
            'cvv': '123',
            'card_type': 'visa'
        }
        
        result = validator.validate_payment_data(payment_data)
        
        assert result['compliant'] is False
        assert len(result['errors']) > 0
        assert any("Card validation" in error for error in result['errors'])
    
    def test_check_firewall_config(self, validator):
        """Test firewall configuration check."""
        result = validator._check_firewall_config()
        
        assert 'status' in result
        assert 'score' in result
        assert 'compliant' in result
        assert 'details' in result
    
    def test_check_encryption(self, validator):
        """Test encryption check."""
        result = validator._check_encryption()
        
        assert result['compliant'] is True
        assert result['status'] == ComplianceStatus.PASS
        assert result['score'] == 1.0
    
    def test_generate_compliance_report(self, validator):
        """Test compliance report generation."""
        report = validator.generate_compliance_report()
        
        assert report.overall_score >= 0.0
        assert report.overall_score <= 1.0
        assert report.compliance_level in ComplianceLevel
        assert len(report.checks) == 12  # All PCI requirements
        assert report.generated_at is not None
        assert report.valid_until is not None
    
    def test_validate_stripe_webhook_valid(self, validator):
        """Test valid Stripe webhook signature validation."""
        payload = b'{"test": "data"}'
        timestamp = int(time.time())
        signature = validator._compute_webhook_signature(payload, timestamp)
        
        is_valid = validator.validate_stripe_webhook(payload, signature, timestamp)
        assert is_valid is True
    
    def test_validate_stripe_webhook_invalid_timestamp(self, validator):
        """Test webhook validation with old timestamp."""
        payload = b'{"test": "data"}'
        timestamp = int(time.time()) - 400  # 6+ minutes old
        signature = validator._compute_webhook_signature(payload, timestamp)
        
        is_valid = validator.validate_stripe_webhook(payload, signature, timestamp)
        assert is_valid is False


class TestSecureStripeService:
    """Test secure Stripe service with PCI compliance."""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app for testing."""
        app = Mock()
        app.config = {
            'STRIPE_SECRET_KEY': 'test_key',
            'STRIPE_WEBHOOK_SECRET': 'test_webhook_secret',
            'STRIPE_PUBLISHABLE_KEY': 'test_publishable_key',
            'ENFORCE_PCI_COMPLIANCE': True,
            'REQUIRE_3D_SECURE': True,
            'MAX_PAYMENT_RETRY_ATTEMPTS': 3
        }
        return app
    
    @pytest.fixture
    def service(self, mock_app):
        """Create secure Stripe service instance."""
        service = SecureStripeService()
        service.init_app(mock_app)
        return service
    
    def test_init_app(self, mock_app):
        """Test service initialization with Flask app."""
        service = SecureStripeService()
        service.init_app(mock_app)
        
        assert service.app == mock_app
        assert service.stripe_secret == 'test_key'
        assert service.webhook_secret == 'test_webhook_secret'
        assert service.enforce_pci_compliance is True
        assert service.require_3d_secure is True
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create, service):
        """Test successful payment intent creation."""
        mock_intent = Mock()
        mock_intent.id = 'pi_test123'
        mock_intent.amount = 1500
        mock_intent.currency = 'usd'
        mock_intent.status = 'requires_payment_method'
        mock_intent.client_secret = 'secret_test123'
        mock_intent.created = int(time.time())
        mock_intent.metadata = {}
        mock_intent.customer = None
        mock_intent.payment_method = None
        
        mock_create.return_value = mock_intent
        
        result = service.create_payment_intent(1500, 'usd')
        
        assert result.id == 'pi_test123'
        assert result.amount == 1500
        assert result.currency == 'usd'
        assert result.status.value == 'requires_payment_method'
    
    def test_create_payment_intent_invalid_amount(self, service):
        """Test payment intent creation with invalid amount."""
        with pytest.raises(Exception) as exc_info:
            service.create_payment_intent(0, 'usd')
        
        assert "Amount must be greater than 0" in str(exc_info.value)
    
    def test_create_payment_intent_invalid_currency(self, service):
        """Test payment intent creation with invalid currency."""
        with pytest.raises(Exception) as exc_info:
            service.create_payment_intent(1500, 'invalid')
        
        assert "Unsupported currency" in str(exc_info.value)
    
    def test_validate_card_data_valid(self, service):
        """Test valid card data validation."""
        payment_data = {
            'card': {
                'number': '4111111111111111',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123'
            },
            'type': 'card'
        }
        
        result = service._validate_card_data(payment_data)
        
        assert result['compliant'] is True
        assert len(result['errors']) == 0
    
    def test_validate_card_data_invalid(self, service):
        """Test invalid card data validation."""
        payment_data = {
            'card': {
                'number': '1234567890123456',  # Invalid checksum
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123'
            },
            'type': 'card'
        }
        
        result = service._validate_card_data(payment_data)
        
        assert result['compliant'] is False
        assert len(result['errors']) > 0


class TestPCIMiddleware:
    """Test PCI compliance middleware."""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app for testing."""
        app = Mock()
        app.config = {
            'ENFORCE_PCI_COMPLIANCE': True,
            'BLOCK_PCI_VIOLATIONS': True,
            'LOG_PCI_VIOLATIONS': True,
            'REQUIRE_HTTPS': True
        }
        return app
    
    @pytest.fixture
    def middleware(self, mock_app):
        """Create PCI middleware instance."""
        middleware = PCIMiddleware()
        middleware.init_app(mock_app)
        return middleware
    
    def test_init_app(self, mock_app):
        """Test middleware initialization with Flask app."""
        middleware = PCIMiddleware()
        middleware.init_app(mock_app)
        
        assert middleware.app == mock_app
        assert middleware.enforce_compliance is True
        assert middleware.block_violations is True
        assert middleware.log_violations is True
        assert middleware.require_https is True
    
    def test_is_excluded_route(self, middleware):
        """Test route exclusion logic."""
        assert middleware._is_excluded_route('/health') is True
        assert middleware._is_excluded_route('/status') is True
        assert middleware._is_excluded_route('/api/payments') is False
    
    def test_is_pci_protected_route(self, middleware):
        """Test PCI protected route detection."""
        assert middleware._is_pci_protected_route('/api/payments') is True
        assert middleware._is_pci_protected_route('/api/subscriptions') is True
        assert middleware._is_pci_protected_route('/health') is False
    
    def test_contains_sensitive_data_true(self, middleware):
        """Test sensitive data detection."""
        request = Mock()
        request.is_json = True
        request.get_json.return_value = {'card_number': '4111111111111111'}
        request.form = {}
        request.args = {}
        request.headers = {}
        
        contains_sensitive = middleware._contains_sensitive_data(request)
        assert contains_sensitive is True
    
    def test_contains_sensitive_data_false(self, middleware):
        """Test sensitive data detection with clean data."""
        request = Mock()
        request.is_json = True
        request.get_json.return_value = {'name': 'John Doe'}
        request.form = {}
        request.args = {}
        request.headers = {}
        
        contains_sensitive = middleware._contains_sensitive_data(request)
        assert contains_sensitive is False
    
    def test_is_sensitive_key(self, middleware):
        """Test sensitive key detection."""
        assert middleware._is_sensitive_key('card_number') is True
        assert middleware._is_sensitive_key('cvv') is True
        assert middleware._is_sensitive_key('ssn') is True
        assert middleware._is_sensitive_key('name') is False
        assert middleware._is_sensitive_key('email') is False
    
    def test_add_security_headers(self, middleware):
        """Test security header addition."""
        response = Mock()
        response.headers = {}
        
        result = middleware._add_security_headers(response)
        
        assert 'X-Frame-Options' in result.headers
        assert 'X-Content-Type-Options' in result.headers
        assert 'X-XSS-Protection' in result.headers
        assert 'X-PCI-Compliance' in result.headers
    
    def test_get_compliance_report(self, middleware):
        """Test compliance report generation."""
        report = middleware.get_compliance_report()
        
        assert 'compliance_score' in report
        assert 'total_violations' in report
        assert 'critical_violations' in report
        assert 'high_violations' in report
        assert 'medium_violations' in report
        assert 'low_violations' in report
        assert 'violations_by_type' in report


class TestPaymentModels:
    """Test PCI compliant payment models."""
    
    def test_mingus_customer_no_sensitive_data(self):
        """Test that customer model doesn't store sensitive data."""
        customer = MINGUSCustomer()
        
        # Should not have card-related fields
        assert not hasattr(customer, 'card_number')
        assert not hasattr(customer, 'cvv')
        assert not hasattr(customer, 'expiry')
        
        # Should have PCI compliance fields
        assert hasattr(customer, 'pci_compliance_level')
        assert hasattr(customer, 'last_compliance_check')
        assert hasattr(customer, 'compliance_score')
    
    def test_mingus_payment_method_no_card_data(self):
        """Test that payment method model doesn't store card data."""
        payment_method = MINGUSPaymentMethod()
        
        # Should not have sensitive card fields
        assert not hasattr(payment_method, 'card_number')
        assert not hasattr(payment_method, 'cvv')
        
        # Should only have non-sensitive fields
        assert hasattr(payment_method, 'last4')
        assert hasattr(payment_method, 'exp_month')
        assert hasattr(payment_method, 'exp_year')
        assert hasattr(payment_method, 'brand')
        
        # Should have PCI compliance fields
        assert hasattr(payment_method, 'pci_compliant')
        assert hasattr(payment_method, 'last_compliance_check')
        assert hasattr(payment_method, 'compliance_notes')
    
    def test_mingus_payment_intent_no_sensitive_data(self):
        """Test that payment intent model doesn't store sensitive data."""
        payment_intent = MINGUSPaymentIntent()
        
        # Should not have card-related fields
        assert not hasattr(payment_intent, 'card_number')
        assert not hasattr(payment_intent, 'cvv')
        
        # Should have PCI compliance fields
        assert hasattr(payment_intent, 'pci_compliant')
        assert hasattr(payment_intent, 'compliance_checks_passed')
        assert hasattr(payment_intent, 'compliance_notes')
    
    def test_mingus_invoice_no_sensitive_data(self):
        """Test that invoice model doesn't store sensitive data."""
        invoice = MINGUSInvoice()
        
        # Should not have card-related fields
        assert not hasattr(invoice, 'card_number')
        assert not hasattr(invoice, 'cvv')
        
        # Should have PCI compliance fields
        assert hasattr(invoice, 'pci_compliant')
        assert hasattr(invoice, 'compliance_checks_passed')
    
    def test_payment_method_validation(self):
        """Test payment method field validation."""
        payment_method = MINGUSPaymentMethod()
        
        # Test valid expiry month
        payment_method.exp_month = 12
        assert payment_method.exp_month == 12
        
        # Test invalid expiry month
        with pytest.raises(ValueError):
            payment_method.exp_month = 13
        
        # Test valid expiry year
        current_year = datetime.now().year
        payment_method.exp_year = current_year + 1
        assert payment_method.exp_year == current_year + 1
        
        # Test invalid expiry year (too far in future)
        with pytest.raises(ValueError):
            payment_method.exp_year = current_year + 25
        
        # Test valid last4
        payment_method.last4 = "1234"
        assert payment_method.last4 == "1234"
        
        # Test invalid last4
        with pytest.raises(ValueError):
            payment_method.last4 = "123"
    
    def test_payment_intent_validation(self):
        """Test payment intent field validation."""
        payment_intent = MINGUSPaymentIntent()
        
        # Test valid amount
        payment_intent.amount = 1500
        assert payment_intent.amount == 1500
        
        # Test invalid amount
        with pytest.raises(ValueError):
            payment_intent.amount = 0
        
        # Test valid currency
        payment_intent.currency = 'usd'
        assert payment_intent.currency == 'usd'
        
        # Test invalid currency
        with pytest.raises(ValueError):
            payment_intent.currency = 'invalid'
    
    def test_invoice_validation(self):
        """Test invoice field validation."""
        invoice = MINGUSInvoice()
        
        # Test valid amounts
        invoice.subtotal = 100.0
        invoice.tax = 10.0
        invoice.discount = 5.0
        invoice.total = 105.0
        invoice.amount_paid = 50.0
        invoice.amount_remaining = 55.0
        
        assert invoice.subtotal == 100.0
        assert invoice.tax == 10.0
        assert invoice.discount == 5.0
        assert invoice.total == 105.0
        assert invoice.amount_paid == 50.0
        assert invoice.amount_remaining == 55.0
        
        # Test invalid amounts (negative)
        with pytest.raises(ValueError):
            invoice.subtotal = -10.0
        
        with pytest.raises(ValueError):
            invoice.tax = -5.0
        
        # Test valid currency
        invoice.currency = 'eur'
        assert invoice.currency == 'eur'
        
        # Test invalid currency
        with pytest.raises(ValueError):
            invoice.currency = 'invalid'


class TestComplianceReporting:
    """Test PCI compliance reporting functionality."""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app for testing."""
        app = Mock()
        app.config = {
            'ENFORCE_PCI_COMPLIANCE': True,
            'BLOCK_PCI_VIOLATIONS': True,
            'LOG_PCI_VIOLATIONS': True,
            'REQUIRE_HTTPS': True
        }
        return app
    
    def test_compliance_score_calculation(self, mock_app):
        """Test compliance score calculation."""
        middleware = PCIMiddleware()
        middleware.init_app(mock_app)
        
        # Add some test violations
        middleware._violations = []
        
        report = middleware.get_compliance_report()
        
        # With no violations, score should be 100
        assert report['compliance_score'] == 100.0
        assert report['total_violations'] == 0
    
    def test_violation_filtering(self, mock_app):
        """Test violation filtering by date and type."""
        middleware = PCIMiddleware()
        middleware.init_app(mock_app)
        
        # Test filtering
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        violations = middleware.get_violations(start_date, end_date)
        assert isinstance(violations, list)
        
        # Test filtering by severity
        high_violations = middleware.get_violations(severity=middleware.ViolationSeverity.HIGH)
        assert isinstance(high_violations, list)
        
        # Test filtering by type
        card_violations = middleware.get_violations(violation_type=middleware.ViolationType.CARD_DATA_EXPOSURE)
        assert isinstance(card_violations, list)


if __name__ == '__main__':
    pytest.main([__file__])
