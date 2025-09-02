# MINGUS Security Integration Tests

This directory contains comprehensive integration tests for the MINGUS application's security systems, including PCI compliance, encryption, and audit logging.

## Test Files

### 1. `test_security_integration.py`
**End-to-end security workflow tests covering:**
- PCI + Encryption + Audit integration
- Complete payment flow with full security stack
- Performance impact measurement and benchmarking
- Security system failover and recovery testing
- Concurrent security operations testing
- Performance regression detection

**Key Test Classes:**
- `TestSecuritySystemIntegration`: Tests complete security workflows
- `TestSecurityPerformanceBenchmarks`: Performance benchmarking

### 2. `test_compliance_workflow.py`
**Complete compliance scenario testing covering:**
- Financial transaction audit trail validation
- Encryption key rotation during active use
- Compliance report generation testing
- Multi-standard compliance workflows (PCI DSS, SOC2, ISO27001, etc.)
- Compliance performance benchmarking

**Key Test Classes:**
- `TestComplianceWorkflowScenarios`: Tests compliance workflows
- `TestCompliancePerformanceBenchmarks`: Compliance performance testing

## Prerequisites

1. **Install testing dependencies:**
   ```bash
   pip install -r requirements-testing.txt
   ```

2. **Ensure security systems are available:**
   - Encryption service (`security.encryption`)
   - Audit system (`security.audit`)
   - PCI compliance validator (`security.pci_compliance`)

3. **Set up test environment:**
   - Test database configuration
   - Mock services and fixtures
   - Performance monitoring tools

## Running the Tests

### Run All Integration Tests
```bash
# From the project root
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=security --cov-report=html -v

# With performance profiling
pytest tests/integration/ --benchmark-only -v
```

### Run Specific Test Files
```bash
# Security integration tests only
pytest tests/integration/test_security_integration.py -v

# Compliance workflow tests only
pytest tests/integration/test_compliance_workflow.py -v
```

### Run Specific Test Classes
```bash
# Security system integration tests
pytest tests/integration/test_security_integration.py::TestSecuritySystemIntegration -v

# Compliance workflow tests
pytest tests/integration/test_compliance_workflow.py::TestComplianceWorkflowScenarios -v

# Performance benchmarks
pytest tests/integration/test_security_integration.py::TestSecurityPerformanceBenchmarks -v
```

### Run Specific Test Methods
```bash
# Test end-to-end payment security workflow
pytest tests/integration/test_security_integration.py::TestSecuritySystemIntegration::test_end_to_end_payment_security_workflow -v

# Test PCI compliance scenario
pytest tests/integration/test_compliance_workflow.py::TestComplianceWorkflowScenarios::test_complete_pci_compliance_scenario -v
```

## Test Categories

### Security Integration Tests
- **End-to-End Workflows**: Complete security workflows from data input to audit logging
- **Concurrent Operations**: Security systems under concurrent load
- **Failover & Recovery**: System resilience and recovery mechanisms
- **Performance Impact**: Measurement of security overhead
- **Data Integrity**: Validation of data through security pipeline

### Compliance Workflow Tests
- **PCI DSS Compliance**: Payment card industry compliance workflows
- **Multi-Standard Compliance**: SOC2, ISO27001, GLBA, CCPA workflows
- **Audit Trail Validation**: Complete financial transaction audit trails
- **Key Rotation**: Encryption key rotation during active operations
- **Report Generation**: Compliance report generation and validation

### Performance Benchmarks
- **Throughput Testing**: Operations per second under various loads
- **Latency Testing**: Response time measurements (P50, P95, P99)
- **Memory Efficiency**: Memory usage per operation
- **Scalability Testing**: Performance with increasing data volumes
- **Regression Detection**: Performance consistency over time

## Test Data and Fixtures

### Mock Data
- User sessions and authentication
- Payment card data (test numbers only)
- Financial transactions
- Compliance audit data
- Encryption keys and certificates

### Test Databases
- Temporary SQLite databases for testing
- Sample compliance audit records
- Financial transaction data
- Audit event logs

### Performance Metrics
- Processing times for each security operation
- Memory usage tracking
- Error rates and success counts
- Throughput measurements
- Latency percentiles

## Expected Results

### Performance Targets
- **PCI Validation**: < 100ms per operation
- **Data Encryption**: < 50ms per operation
- **Audit Logging**: < 20ms per operation
- **Total Workflow**: < 200ms for complete payment flow
- **Memory Usage**: < 100MB for typical operations

### Compliance Scores
- **PCI DSS**: ≥ 95% compliance
- **SOC2**: ≥ 90% compliance
- **ISO27001**: ≥ 85% compliance
- **Overall**: ≥ 85% compliance across all standards

### Security Validation
- All sensitive data properly encrypted
- Complete audit trails maintained
- PCI compliance maintained throughout workflows
- Key rotation successful without data loss
- Failover mechanisms functional

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure security modules are in Python path
2. **Database Errors**: Check test database setup and permissions
3. **Performance Failures**: Verify system resources and test environment
4. **Mock Failures**: Check mock service configurations

### Debug Mode
```bash
# Run with debug output
pytest tests/integration/ -v -s --tb=long

# Run specific test with debugger
pytest tests/integration/test_security_integration.py::TestSecuritySystemIntegration::test_end_to_end_payment_security_workflow -v -s --pdb
```

### Performance Analysis
```bash
# Generate performance report
pytest tests/integration/ --benchmark-only --benchmark-autosave

# View saved benchmarks
pytest-benchmark compare
```

## Continuous Integration

### CI/CD Integration
These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Security Integration Tests
  run: |
    pip install -r tests/integration/requirements-testing.txt
    pytest tests/integration/ --junitxml=test-results.xml --cov=security --cov-report=xml
```

### Test Reports
- JUnit XML reports for CI integration
- Coverage reports for code quality
- Performance benchmark reports
- Compliance validation reports

## Security Considerations

### Test Data
- **No Real Data**: All tests use synthetic/mock data
- **Test Cards Only**: Payment tests use test card numbers
- **Isolated Environment**: Tests run in isolated test environment
- **No Production Access**: Tests never access production systems

### Test Isolation
- Temporary databases for each test run
- Mock external services
- Isolated encryption keys
- Clean test environment between runs

## Contributing

### Adding New Tests
1. Follow existing test structure and naming conventions
2. Include performance metrics and assertions
3. Add appropriate test documentation
4. Ensure test isolation and cleanup
5. Include both positive and negative test cases

### Test Standards
- **Coverage**: Aim for >90% code coverage
- **Performance**: Include performance assertions
- **Documentation**: Clear test descriptions and expected results
- **Maintainability**: Clean, readable test code
- **Reliability**: Tests should be deterministic and repeatable

## Support

For questions or issues with these tests:
- Check the test output and error messages
- Review the test configuration and dependencies
- Ensure all security systems are properly configured
- Contact the MINGUS development team
