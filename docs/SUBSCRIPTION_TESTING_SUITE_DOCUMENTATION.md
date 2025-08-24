# MINGUS Subscription System Testing Suite Documentation

## 🎯 Overview

The MINGUS Subscription System Testing Suite provides comprehensive validation of all billing scenarios and edge cases for the MINGUS application. This testing suite ensures the reliability, security, and performance of the subscription management system.

## 📊 Test Coverage

### **Core Test Categories**

#### 1. **Subscription Creation** (`TestSubscriptionCreation`)
- ✅ Successful subscription creation with payment method
- ✅ Subscription creation with trial periods
- ✅ Yearly billing cycle setup
- ✅ Invalid pricing tier handling
- ✅ Invalid payment method handling
- ✅ Concurrent subscription creation scenarios

#### 2. **Subscription Lifecycle** (`TestSubscriptionLifecycle`)
- ✅ Subscription activation and deactivation
- ✅ Subscription cancellation (immediate and end-of-period)
- ✅ Subscription reactivation
- ✅ Subscription upgrades and downgrades
- ✅ Tier transitions with proration
- ✅ Trial period management

#### 3. **Billing Scenarios** (`TestBillingScenarios`)
- ✅ Recurring billing processing
- ✅ Usage-based billing calculations
- ✅ Tax calculation and application
- ✅ Discount and credit application
- ✅ Payment failure handling
- ✅ Proration calculations
- ✅ Multiple payment method scenarios

#### 4. **Payment Recovery** (`TestPaymentRecovery`)
- ✅ Payment failure recovery workflows
- ✅ Dunning management and escalation
- ✅ Payment method updates
- ✅ Grace period management
- ✅ Service suspension and reactivation
- ✅ Retry logic with exponential backoff

#### 5. **Webhook Handling** (`TestWebhookHandling`)
- ✅ Customer creation webhooks
- ✅ Subscription update webhooks
- ✅ Invoice payment success/failure webhooks
- ✅ Webhook signature verification
- ✅ Malformed webhook data handling
- ✅ Concurrent webhook processing

#### 6. **Feature Access Control** (`TestFeatureAccessControl`)
- ✅ Tier-based feature access validation
- ✅ Usage tracking and limits
- ✅ Budget tier restrictions
- ✅ Mid-tier feature access
- ✅ Professional tier unlimited access
- ✅ Usage limit enforcement

#### 7. **Customer Portal** (`TestCustomerPortal`)
- ✅ Portal session creation
- ✅ Subscription management options
- ✅ Billing history access
- ✅ Payment method updates
- ✅ Cancellation workflows

#### 8. **Revenue Optimization** (`TestRevenueOptimization`)
- ✅ Churn prediction algorithms
- ✅ Upsell opportunity identification
- ✅ Pricing optimization analysis
- ✅ Revenue impact calculations

#### 9. **Automated Workflows** (`TestAutomatedWorkflows`)
- ✅ Welcome workflow automation
- ✅ Payment failure workflow
- ✅ Trial ending notifications
- ✅ Customer lifecycle management

#### 10. **Edge Cases** (`TestEdgeCases`)
- ✅ Database connection failures
- ✅ Stripe API failures
- ✅ Invalid currency handling
- ✅ Negative amount validation
- ✅ Malformed data handling
- ✅ Concurrent operation scenarios

#### 11. **Performance & Load** (`TestPerformanceAndLoad`)
- ✅ Bulk subscription processing
- ✅ Concurrent webhook processing
- ✅ High-volume transaction handling
- ✅ Memory usage optimization
- ✅ Response time validation

#### 12. **Security & Compliance** (`TestSecurityAndCompliance`)
- ✅ Webhook signature verification
- ✅ Payment data encryption
- ✅ Audit logging validation
- ✅ PCI compliance checks
- ✅ Data privacy validation

## 🚀 Test Runner Usage

### **Basic Usage**

```bash
# Run all subscription tests
python tests/run_subscription_test_suite.py

# Run with coverage reporting
python tests/run_subscription_test_suite.py --coverage

# Run with performance profiling
python tests/run_subscription_test_suite.py --profile
```

### **Category-Specific Testing**

```bash
# Run billing scenarios only
python tests/run_subscription_test_suite.py --category billing_scenarios

# Run security tests only
python tests/run_subscription_test_suite.py --category security

# Run performance tests only
python tests/run_subscription_test_suite.py --category performance
```

### **Specific Test Execution**

```bash
# Run a specific test
python tests/run_subscription_test_suite.py --test test_create_subscription_with_payment_success

# Run performance-focused tests
python tests/run_subscription_test_suite.py --performance

# Run security-focused tests
python tests/run_subscription_test_suite.py --security
```

### **Advanced Options**

```bash
# Save results to file
python tests/run_subscription_test_suite.py --save-results results.json

# Generate detailed report
python tests/run_subscription_test_suite.py --report

# Combine multiple options
python tests/run_subscription_test_suite.py --coverage --report --save-results results.json
```

## 🧪 Test Scenarios

### **Billing Scenarios**

#### **1. Successful Recurring Billing**
```python
def test_recurring_billing_success(self, billing_service, sample_subscription):
    """Test successful recurring billing."""
    result = billing_service.process_recurring_billing()
    
    assert 'processed' in result
    assert 'successful' in result
    assert 'failed' in result
    assert 'errors' in result
```

#### **2. Usage-Based Billing**
```python
def test_billing_with_usage_charges(self, billing_service, sample_subscription):
    """Test billing with usage-based charges."""
    # Add usage records exceeding limits
    usage_record = FeatureUsage(
        subscription_id=sample_subscription.id,
        feature_name='api_calls',
        usage_quantity=1500,  # Over the 1000 limit
        usage_date=datetime.now(timezone.utc),
        unit_price=0.01
    )
    
    result = billing_service._process_subscription_billing(sample_subscription)
    
    assert result['success'] is True
    assert result['amount'] > sample_subscription.amount  # Should include usage charges
```

#### **3. Tax Calculation**
```python
def test_billing_with_tax_calculation(self, billing_service, sample_subscription):
    """Test billing with tax calculation."""
    sample_subscription.tax_percent = 8.5
    billing_service.db.commit()
    
    result = billing_service._process_subscription_billing(sample_subscription)
    
    assert result['success'] is True
    assert result['amount'] > sample_subscription.amount  # Should include tax
```

### **Payment Recovery Scenarios**

#### **1. Payment Failure Recovery**
```python
def test_payment_failure_recovery(self, db_session, mock_config):
    """Test payment failure recovery process."""
    recovery_service = PaymentRecoveryService(db_session, mock_config)
    
    failed_payment = {
        'subscription_id': 1,
        'amount': 15.00,
        'failure_reason': 'insufficient_funds',
        'attempt_count': 1
    }
    
    result = recovery_service.process_payment_failure(failed_payment)
    
    assert 'retry_scheduled' in result
    assert 'next_attempt' in result
```

#### **2. Dunning Management**
```python
def test_dunning_management(self, db_session, mock_config):
    """Test dunning management for failed payments."""
    recovery_service = PaymentRecoveryService(db_session, mock_config)
    
    # Simulate multiple payment failures
    for attempt in range(1, 4):
        failed_payment = {
            'subscription_id': 1,
            'amount': 15.00,
            'failure_reason': 'card_declined',
            'attempt_count': attempt
        }
        
        result = recovery_service.process_payment_failure(failed_payment)
        
        if attempt == 3:
            assert result['stage'] == 'final_warning'
            assert result['action'] == 'suspend_service'
```

### **Webhook Handling Scenarios**

#### **1. Customer Creation Webhook**
```python
def test_customer_created_webhook(self, webhook_manager, db_session):
    """Test customer.created webhook handling."""
    webhook_data = {
        'id': 'evt_test123',
        'type': 'customer.created',
        'data': {
            'object': {
                'id': 'cus_test123',
                'email': 'test@example.com',
                'name': 'Test User',
                'metadata': {
                    'mingus_user_id': '1'
                }
            }
        }
    }
    
    result = webhook_manager.process_webhook(webhook_data)
    
    assert result['success'] is True
    assert result['event_type'] == 'customer.created'
```

#### **2. Payment Success Webhook**
```python
def test_invoice_payment_succeeded_webhook(self, webhook_manager, db_session):
    """Test invoice.payment_succeeded webhook handling."""
    webhook_data = {
        'id': 'evt_test125',
        'type': 'invoice.payment_succeeded',
        'data': {
            'object': {
                'id': 'in_test123',
                'subscription': 'sub_test123',
                'amount_paid': 1500,
                'status': 'paid',
                'customer': 'cus_test123'
            }
        }
    }
    
    result = webhook_manager.process_webhook(webhook_data)
    
    assert result['success'] is True
    assert result['event_type'] == 'invoice.payment_succeeded'
```

### **Edge Cases**

#### **1. Concurrent Operations**
```python
def test_concurrent_subscription_creation(self, payment_service, sample_customer, sample_pricing_tiers):
    """Test concurrent subscription creation."""
    import threading
    
    results = []
    errors = []
    
    def create_subscription():
        try:
            result = payment_service.create_subscription_with_payment(
                user_id=sample_customer.user_id,
                email=sample_customer.email,
                name=sample_customer.name,
                pricing_tier_id=sample_pricing_tiers[0].id,
                payment_method_id='pm_test123',
                billing_cycle='monthly'
            )
            results.append(result)
        except Exception as e:
            errors.append(str(e))
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_subscription)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Should have exactly one successful creation
    successful_results = [r for r in results if r['success']]
    assert len(successful_results) == 1
    assert len(errors) == 4  # Other attempts should fail
```

#### **2. Database Connection Failures**
```python
def test_database_connection_failure(self, db_session, mock_config):
    """Test handling of database connection failures."""
    with patch.object(db_session, 'commit') as mock_commit:
        mock_commit.side_effect = SQLAlchemyError("Database connection lost")
        
        payment_service = PaymentService(db_session, mock_config)
        
        result = payment_service.create_subscription_with_payment(
            user_id=1,
            email='test@example.com',
            name='Test User',
            pricing_tier_id=1,
            payment_method_id='pm_test123'
        )
        
        assert result['success'] is False
        assert 'Database' in result['error']
```

## 📈 Performance Testing

### **Bulk Processing Test**
```python
def test_bulk_subscription_processing(self, payment_service, db_session):
    """Test processing multiple subscriptions efficiently."""
    import time
    
    start_time = time.time()
    
    # Create 100 test subscriptions
    for i in range(100):
        payment_service.create_subscription_with_payment(
            user_id=i,
            email=f'test{i}@example.com',
            name=f'Test User {i}',
            pricing_tier_id=1,
            payment_method_id='pm_test123'
        )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Should complete within reasonable time
    assert processing_time < 30.0  # 30 seconds for 100 subscriptions
```

### **Concurrent Webhook Processing**
```python
def test_concurrent_webhook_processing(self, webhook_manager, db_session):
    """Test concurrent webhook processing."""
    import threading
    
    results = []
    
    def process_webhook(webhook_id):
        webhook_data = {
            'id': f'evt_test{webhook_id}',
            'type': 'customer.created',
            'data': {
                'object': {
                    'id': f'cus_test{webhook_id}',
                    'email': f'test{webhook_id}@example.com',
                    'name': f'Test User {webhook_id}'
                }
            }
        }
        result = webhook_manager.process_webhook(webhook_data)
        results.append(result)
    
    # Process 50 webhooks concurrently
    threads = []
    for i in range(50):
        thread = threading.Thread(target=process_webhook, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All webhooks should be processed successfully
    successful_results = [r for r in results if r['success']]
    assert len(successful_results) == 50
```

## 🔒 Security Testing

### **Webhook Signature Verification**
```python
def test_webhook_signature_verification(self, webhook_manager, db_session):
    """Test webhook signature verification."""
    webhook_data = {
        'id': 'evt_test129',
        'type': 'customer.created',
        'data': {'object': {}}
    }
    
    with patch.object(webhook_manager, '_verify_webhook_signature') as mock_verify:
        mock_verify.return_value = True
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is True
        mock_verify.assert_called_once()
```

### **Payment Data Encryption**
```python
def test_payment_data_encryption(self, db_session, mock_config):
    """Test payment data encryption."""
    payment_service = PaymentService(db_session, mock_config)
    
    sensitive_data = {
        'card_number': '4242424242424242',
        'cvv': '123',
        'expiry': '12/25'
    }
    
    encrypted_data = payment_service._encrypt_sensitive_data(sensitive_data)
    
    assert encrypted_data != sensitive_data
    assert 'card_number' not in str(encrypted_data)
    assert 'cvv' not in str(encrypted_data)
```

## 📊 Test Results and Reporting

### **Test Report Example**
```
📊 MINGUS Subscription System Test Report
==================================================
Generated: 2025-01-27 15:30:45
Execution Time: 45.23 seconds
Overall Status: ✅ PASSED

📋 Test Categories:
  • subscription_creation: Subscription creation and setup
  • subscription_lifecycle: Subscription lifecycle management
  • billing_scenarios: Billing scenarios and calculations
  • payment_recovery: Payment failure and recovery
  • webhook_handling: Webhook processing and integration
  • feature_access: Feature access control and usage tracking
  • customer_portal: Customer portal functionality
  • revenue_optimization: Revenue optimization features
  • automated_workflows: Automated workflow scenarios
  • edge_cases: Edge cases and error handling
  • performance: Performance and load testing
  • security: Security and compliance testing

⚡ Performance Metrics:
  • Total Execution Time: 45.23 seconds
  • Average Test Time: 0.90 seconds per test

💡 Recommendations:
  • All tests passed successfully!
  • The subscription system is ready for production deployment.
```

### **Coverage Report**
When running with `--coverage`, the test suite generates:
- HTML coverage report in `coverage_html/`
- Terminal coverage summary
- Missing line coverage details

### **Performance Profiling**
When running with `--profile`, the test suite generates:
- Performance profiling data
- SVG visualization of performance bottlenecks
- Detailed timing analysis

## 🛠️ Configuration

### **Environment Setup**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-profiling

# Set up test environment variables
export STRIPE_SECRET_KEY=sk_test_mock_key
export STRIPE_PUBLISHABLE_KEY=pk_test_mock_key
export STRIPE_WEBHOOK_SECRET=whsec_mock_secret
export ENVIRONMENT=test
```

### **Test Configuration**
The test suite uses mock configurations for:
- Stripe API integration
- Database connections
- External service dependencies
- Payment processing

### **Mock Services**
- **Stripe API**: Mocked with realistic responses
- **Database**: In-memory SQLite for testing
- **Email Service**: Mocked notifications
- **Analytics**: Mocked tracking and metrics

## 🔧 Customization

### **Adding New Test Categories**
1. Create a new test class in `tests/subscription_tests.py`
2. Add the category to `test_categories` in `SubscriptionTestRunner`
3. Implement test methods with appropriate fixtures

### **Extending Test Scenarios**
1. Add new test methods to existing test classes
2. Create appropriate fixtures for test data
3. Update documentation with new scenarios

### **Custom Test Data**
```python
@pytest.fixture
def custom_test_data(self):
    """Custom test data for specific scenarios."""
    return {
        'custom_pricing_tier': {
            'name': 'Custom Tier',
            'price': 25.00,
            'features': ['custom_feature_1', 'custom_feature_2']
        },
        'custom_customer': {
            'email': 'custom@example.com',
            'name': 'Custom User',
            'metadata': {'custom_field': 'custom_value'}
        }
    }
```

## 🚨 Troubleshooting

### **Common Issues**

#### **1. Import Errors**
```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **2. Database Connection Issues**
```bash
# Use in-memory database for testing
export DATABASE_URL="sqlite:///:memory:"
```

#### **3. Stripe API Errors**
```bash
# Use test keys
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."
```

#### **4. Test Timeout Issues**
```bash
# Increase timeout for slow tests
pytest --timeout=300 tests/subscription_tests.py
```

### **Debug Mode**
```bash
# Run tests with debug output
python tests/run_subscription_test_suite.py --test test_name -v -s
```

## 📚 Additional Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Stripe Testing Guide**: https://stripe.com/docs/testing
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction
- **Performance Testing**: https://pytest-profiling.readthedocs.io/

## 🤝 Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Include comprehensive docstrings
3. Add appropriate assertions
4. Update this documentation
5. Ensure tests pass in isolation
6. Add performance considerations for new tests

## 📞 Support

For issues with the test suite:
1. Check the troubleshooting section
2. Review test logs and error messages
3. Verify environment configuration
4. Consult the MINGUS development team 