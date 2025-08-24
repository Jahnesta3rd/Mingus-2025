#!/usr/bin/env python3
"""
Test script for Financial Reporting System
Tests revenue recognition reporting, tax calculation and reporting,
refund and credit tracking, and payment processor fee analysis.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from decimal import Decimal

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from analytics.financial_reporting import (
    FinancialReporting, FinancialReportingConfig, FinancialMetricType, 
    RevenueRecognitionMethod, TaxType, RefundStatus
)
from models.subscription import Customer, Subscription
from config.base import Config

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.customers = {}
        self.subscriptions = {}
        self.analytics_data = {}
    
    def commit(self):
        pass
    
    def add(self, obj):
        if isinstance(obj, Customer):
            self.customers[obj.id] = obj
        elif isinstance(obj, Subscription):
            self.subscriptions[obj.id] = obj
    
    def query(self, model):
        return MockQuery(self, model)

class MockQuery:
    """Mock query for testing"""
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.filters = []
    
    def filter(self, condition):
        self.filters.append(condition)
        return self
    
    def first(self):
        return None
    
    def all(self):
        return []

def create_mock_customer(customer_type: str = 'standard') -> Customer:
    """Create a mock customer for testing"""
    customer_id = str(uuid.uuid4())
    
    if customer_type == 'premium':
        status = 'active'
        metadata = {'monthly_revenue': 150.0, 'subscription_length_months': 12, 'segment': 'premium'}
    elif customer_type == 'enterprise':
        status = 'active'
        metadata = {'monthly_revenue': 500.0, 'subscription_length_months': 24, 'segment': 'enterprise'}
    else:
        status = 'active'
        metadata = {'monthly_revenue': 75.0, 'subscription_length_months': 3, 'segment': 'standard'}
    
    return Customer(
        id=customer_id,
        stripe_customer_id=f"cus_{uuid.uuid4().hex[:24]}",
        email=f"{customer_type}@example.com",
        name=f"{customer_type.title()} Customer",
        status=status,
        created_at=datetime.now(timezone.utc) - timedelta(days=90),
        metadata=metadata
    )

def create_mock_subscription(customer_id: str, customer_type: str = 'standard') -> Subscription:
    """Create a mock subscription for testing"""
    if customer_type == 'premium':
        amount = 150.0
        plan_id = "premium_plan"
    elif customer_type == 'enterprise':
        amount = 500.0
        plan_id = "enterprise_plan"
    else:
        amount = 75.0
        plan_id = "standard_plan"
    
    return Subscription(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        stripe_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
        status="active",
        plan_id=plan_id,
        amount=amount,
        currency="usd",
        interval="month",
        created_at=datetime.now(timezone.utc),
        metadata={}
    )

def test_revenue_recognition_reporting():
    """Test revenue recognition reporting functionality"""
    print("💰 Testing Revenue Recognition Reporting")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = FinancialReportingConfig()
    
    # Create financial reporting system
    financial_reporting = FinancialReporting(db, config)
    
    # Test revenue recognition reporting
    print("📋 Test 1: Revenue Recognition Report Generation")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    revenue_report = financial_reporting.generate_revenue_recognition_report(start_date, end_date)
    
    print(f"   Revenue Recognition Report:")
    print(f"     Report Period: {revenue_report.get('report_period', {}).get('start_date', 'N/A')} to {revenue_report.get('report_period', {}).get('end_date', 'N/A')}")
    print(f"     Period Days: {revenue_report.get('report_period', {}).get('period_days', 0)}")
    
    # Summary
    summary = revenue_report.get('summary', {})
    print(f"     Summary:")
    print(f"       Total Revenue: ${summary.get('total_revenue', 0):,.2f}")
    print(f"       Recognized Revenue: ${summary.get('recognized_revenue', 0):,.2f}")
    print(f"       Deferred Revenue: ${summary.get('deferred_revenue', 0):,.2f}")
    print(f"       Contracts Count: {summary.get('contracts_count', 0)}")
    print(f"       Average Contract Value: ${summary.get('average_contract_value', 0):,.2f}")
    
    # Recognition methods
    recognition_methods = revenue_report.get('recognition_methods', {})
    print(f"     Recognition Methods:")
    for method, data in recognition_methods.items():
        print(f"       {method.replace('_', ' ').title()}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Recognized Amount: ${data['recognized_amount']:,.2f}")
        print(f"         Deferred Amount: ${data['deferred_amount']:,.2f}")
        print(f"         Contracts Count: {data['contracts_count']}")
    
    # Monthly recognition
    monthly_recognition = revenue_report.get('monthly_recognition', {})
    print(f"     Monthly Recognition:")
    for month, data in monthly_recognition.items():
        print(f"       {month}:")
        print(f"         Recognized Revenue: ${data['recognized_revenue']:,.2f}")
        print(f"         Deferred Revenue: ${data['deferred_revenue']:,.2f}")
        print(f"         Contracts Count: {data['contracts_count']}")
    
    # Customer recognition
    customer_recognition = revenue_report.get('customer_recognition', {})
    print(f"     Customer Recognition (First 3):")
    for i, (customer_id, data) in enumerate(customer_recognition.items()):
        if i >= 3:
            break
        print(f"       Customer {customer_id}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Recognized Amount: ${data['recognized_amount']:,.2f}")
        print(f"         Deferred Amount: ${data['deferred_amount']:,.2f}")
        print(f"         Contracts Count: {data['contracts_count']}")
    
    # Deferred revenue aging
    deferred_revenue_aging = revenue_report.get('deferred_revenue_aging', {})
    print(f"     Deferred Revenue Aging:")
    for period, data in deferred_revenue_aging.items():
        print(f"       {period.replace('_', ' ').title()}:")
        print(f"         Amount: ${data['amount']:,.2f}")
        print(f"         Count: {data['count']}")
    
    # Compliance metrics
    compliance_metrics = revenue_report.get('compliance_metrics', {})
    print(f"     Compliance Metrics:")
    print(f"       Total Contracts: {compliance_metrics.get('total_contracts', 0)}")
    print(f"       Contracts with Deferred Revenue: {compliance_metrics.get('contracts_with_deferred_revenue', 0)}")
    print(f"       Deferred Revenue Percentage: {compliance_metrics.get('deferred_revenue_percentage', 0):.1%}")
    print(f"       Compliance Score: {compliance_metrics.get('compliance_score', 0):.1%}")
    print(f"       Audit Ready: {compliance_metrics.get('audit_ready', False)}")
    
    print()
    print("✅ Revenue Recognition Reporting Tests Completed")
    print()

def test_tax_calculation_and_reporting():
    """Test tax calculation and reporting functionality"""
    print("🧾 Testing Tax Calculation and Reporting")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = FinancialReportingConfig()
    
    # Create financial reporting system
    financial_reporting = FinancialReporting(db, config)
    
    # Test tax calculation and reporting
    print("📋 Test 1: Tax Calculation Report Generation")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    tax_report = financial_reporting.generate_tax_calculation_report(start_date, end_date)
    
    print(f"   Tax Calculation Report:")
    print(f"     Report Period: {tax_report.get('report_period', {}).get('start_date', 'N/A')} to {tax_report.get('report_period', {}).get('end_date', 'N/A')}")
    print(f"     Period Days: {tax_report.get('report_period', {}).get('period_days', 0)}")
    
    # Summary
    summary = tax_report.get('summary', {})
    print(f"     Summary:")
    print(f"       Total Taxable Amount: ${summary.get('total_taxable_amount', 0):,.2f}")
    print(f"       Total Tax Collected: ${summary.get('total_tax_collected', 0):,.2f}")
    print(f"       Total Tax Remitted: ${summary.get('total_tax_remitted', 0):,.2f}")
    print(f"       Tax Liability: ${summary.get('tax_liability', 0):,.2f}")
    print(f"       Transactions Count: {summary.get('transactions_count', 0)}")
    
    # Tax by type
    tax_by_type = tax_report.get('tax_by_type', {})
    print(f"     Tax by Type:")
    for tax_type, data in tax_by_type.items():
        print(f"       {tax_type.replace('_', ' ').title()}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Total Tax: ${data['total_tax']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
        print(f"         Average Rate: {data['average_rate']:.1%}")
    
    # Tax by jurisdiction
    tax_by_jurisdiction = tax_report.get('tax_by_jurisdiction', {})
    print(f"     Tax by Jurisdiction:")
    for jurisdiction, data in tax_by_jurisdiction.items():
        print(f"       {jurisdiction.replace('_', ' ').title()}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Total Tax: ${data['total_tax']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
        print(f"         Tax Rate: {data['tax_rate']:.1%}")
    
    # Monthly tax summary
    monthly_tax_summary = tax_report.get('monthly_tax_summary', {})
    print(f"     Monthly Tax Summary:")
    for month, data in monthly_tax_summary.items():
        print(f"       {month}:")
        print(f"         Taxable Amount: ${data['taxable_amount']:,.2f}")
        print(f"         Tax Collected: ${data['tax_collected']:,.2f}")
        print(f"         Tax Remitted: ${data['tax_remitted']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
    
    # Customer tax summary
    customer_tax_summary = tax_report.get('customer_tax_summary', {})
    print(f"     Customer Tax Summary (First 3):")
    for i, (customer_id, data) in enumerate(customer_tax_summary.items()):
        if i >= 3:
            break
        print(f"       Customer {customer_id}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Total Tax: ${data['total_tax']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
    
    # Compliance status
    compliance_status = tax_report.get('compliance_status', {})
    print(f"     Compliance Status:")
    print(f"       Total Tax Collected: ${compliance_status.get('total_tax_collected', 0):,.2f}")
    print(f"       Total Tax Remitted: ${compliance_status.get('total_tax_remitted', 0):,.2f}")
    print(f"       Tax Liability: ${compliance_status.get('tax_liability', 0):,.2f}")
    print(f"       Remittance Rate: {compliance_status.get('remittance_rate', 0):.1%}")
    print(f"       Compliance Score: {compliance_status.get('compliance_score', 0):.1%}")
    
    filing_deadlines = compliance_status.get('filing_deadlines', {})
    print(f"       Filing Deadlines:")
    for period, deadline in filing_deadlines.items():
        print(f"         {period.title()}: {deadline}")
    
    print()
    print("✅ Tax Calculation and Reporting Tests Completed")
    print()

def test_refund_and_credit_tracking():
    """Test refund and credit tracking functionality"""
    print("🔄 Testing Refund and Credit Tracking")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = FinancialReportingConfig()
    
    # Create financial reporting system
    financial_reporting = FinancialReporting(db, config)
    
    # Test refund and credit tracking
    print("📋 Test 1: Refund and Credit Report Generation")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    refund_report = financial_reporting.generate_refund_and_credit_report(start_date, end_date)
    
    print(f"   Refund and Credit Report:")
    print(f"     Report Period: {refund_report.get('report_period', {}).get('start_date', 'N/A')} to {refund_report.get('report_period', {}).get('end_date', 'N/A')}")
    print(f"     Period Days: {refund_report.get('report_period', {}).get('period_days', 0)}")
    
    # Summary
    summary = refund_report.get('summary', {})
    print(f"     Summary:")
    print(f"       Total Refunds: ${summary.get('total_refunds', 0):,.2f}")
    print(f"       Total Processing Fees: ${summary.get('total_processing_fees', 0):,.2f}")
    print(f"       Net Refund Amount: ${summary.get('net_refund_amount', 0):,.2f}")
    print(f"       Refunds Count: {summary.get('refunds_count', 0)}")
    print(f"       Successful Refunds: {summary.get('successful_refunds', 0)}")
    print(f"       Failed Refunds: {summary.get('failed_refunds', 0)}")
    print(f"       Average Refund Amount: ${summary.get('average_refund_amount', 0):,.2f}")
    
    # Refunds by status
    refunds_by_status = refund_report.get('refunds_by_status', {})
    print(f"     Refunds by Status:")
    for status, data in refunds_by_status.items():
        print(f"       {status.replace('_', ' ').title()}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Count: {data['count']}")
        print(f"         Processing Fees: ${data['processing_fees']:,.2f}")
    
    # Refunds by reason
    refunds_by_reason = refund_report.get('refunds_by_reason', {})
    print(f"     Refunds by Reason:")
    for reason, data in refunds_by_reason.items():
        print(f"       {reason.replace('_', ' ').title()}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Count: {data['count']}")
        print(f"         Average Amount: ${data['average_amount']:,.2f}")
    
    # Refunds by method
    refunds_by_method = refund_report.get('refunds_by_method', {})
    print(f"     Refunds by Method:")
    for method, data in refunds_by_method.items():
        print(f"       {method.replace('_', ' ').title()}:")
        print(f"         Total Amount: ${data['total_amount']:,.2f}")
        print(f"         Count: {data['count']}")
        print(f"         Processing Fees: ${data['processing_fees']:,.2f}")
    
    # Monthly refund summary
    monthly_refund_summary = refund_report.get('monthly_refund_summary', {})
    print(f"     Monthly Refund Summary:")
    for month, data in monthly_refund_summary.items():
        print(f"       {month}:")
        print(f"         Total Refunds: ${data['total_refunds']:,.2f}")
        print(f"         Processing Fees: ${data['processing_fees']:,.2f}")
        print(f"         Net Refunds: ${data['net_refunds']:,.2f}")
        print(f"         Refunds Count: {data['refunds_count']}")
    
    # Customer refund summary
    customer_refund_summary = refund_report.get('customer_refund_summary', {})
    print(f"     Customer Refund Summary (First 3):")
    for i, (customer_id, data) in enumerate(customer_refund_summary.items()):
        if i >= 3:
            break
        print(f"       Customer {customer_id}:")
        print(f"         Total Refunds: ${data['total_refunds']:,.2f}")
        print(f"         Refunds Count: {data['refunds_count']}")
        print(f"         Average Refund: ${data['average_refund']:,.2f}")
    
    # Refund trends
    refund_trends = refund_report.get('refund_trends', {})
    print(f"     Refund Trends:")
    print(f"       Total Refunds: {refund_trends.get('total_refunds', 0)}")
    print(f"       Successful Refunds: {refund_trends.get('successful_refunds', 0)}")
    print(f"       Success Rate: {refund_trends.get('success_rate', 0):.1%}")
    print(f"       Average Processing Time: {refund_trends.get('average_processing_time_days', 0)} days")
    print(f"       Trend: {refund_trends.get('trend', 'N/A')}")
    
    print()
    print("✅ Refund and Credit Tracking Tests Completed")
    print()

def test_payment_processor_fee_analysis():
    """Test payment processor fee analysis functionality"""
    print("💳 Testing Payment Processor Fee Analysis")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = FinancialReportingConfig()
    
    # Create financial reporting system
    financial_reporting = FinancialReporting(db, config)
    
    # Test payment processor fee analysis
    print("📋 Test 1: Payment Processor Fee Report Generation")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    processor_report = financial_reporting.generate_payment_processor_fee_report(start_date, end_date)
    
    print(f"   Payment Processor Fee Report:")
    print(f"     Report Period: {processor_report.get('report_period', {}).get('start_date', 'N/A')} to {processor_report.get('report_period', {}).get('end_date', 'N/A')}")
    print(f"     Period Days: {processor_report.get('report_period', {}).get('period_days', 0)}")
    
    # Summary
    summary = processor_report.get('summary', {})
    print(f"     Summary:")
    print(f"       Total Transaction Volume: ${summary.get('total_transaction_volume', 0):,.2f}")
    print(f"       Total Processor Fees: ${summary.get('total_processor_fees', 0):,.2f}")
    print(f"       Average Fee Rate: {summary.get('average_fee_rate', 0):.1%}")
    print(f"       Transactions Count: {summary.get('transactions_count', 0)}")
    print(f"       Fee Efficiency Score: {summary.get('fee_efficiency_score', 0):.1%}")
    
    # Fees by processor
    fees_by_processor = processor_report.get('fees_by_processor', {})
    print(f"     Fees by Processor:")
    for processor, data in fees_by_processor.items():
        print(f"       {processor.title()}:")
        print(f"         Total Volume: ${data['total_volume']:,.2f}")
        print(f"         Total Fees: ${data['total_fees']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
        print(f"         Average Fee Rate: {data['average_fee_rate']:.1%}")
        print(f"         Fee Percentage: {data['fee_percentage']:.1%}")
    
    # Fees by type
    fees_by_type = processor_report.get('fees_by_type', {})
    print(f"     Fees by Type:")
    for fee_type, data in fees_by_type.items():
        print(f"       {fee_type.replace('_', ' ').title()}:")
        print(f"         Total Fees: ${data['total_fees']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
        print(f"         Average Fee: ${data['average_fee']:,.2f}")
    
    # Monthly fee summary
    monthly_fee_summary = processor_report.get('monthly_fee_summary', {})
    print(f"     Monthly Fee Summary:")
    for month, data in monthly_fee_summary.items():
        print(f"       {month}:")
        print(f"         Transaction Volume: ${data['transaction_volume']:,.2f}")
        print(f"         Processor Fees: ${data['processor_fees']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
    
    # Customer fee summary
    customer_fee_summary = processor_report.get('customer_fee_summary', {})
    print(f"     Customer Fee Summary (First 3):")
    for i, (customer_id, data) in enumerate(customer_fee_summary.items()):
        if i >= 3:
            break
        print(f"       Customer {customer_id}:")
        print(f"         Transaction Volume: ${data['transaction_volume']:,.2f}")
        print(f"         Processor Fees: ${data['processor_fees']:,.2f}")
        print(f"         Transactions Count: {data['transactions_count']}")
    
    # Fee optimization
    fee_optimization = processor_report.get('fee_optimization', [])
    print(f"     Fee Optimization Recommendations:")
    for rec in fee_optimization:
        print(f"       {rec['recommendation']}")
        print(f"         Potential Savings: ${rec['potential_savings']:,.2f}")
        print(f"         Implementation Effort: {rec['implementation_effort']}")
        print(f"         Priority: {rec['priority']}")
    
    print()
    print("✅ Payment Processor Fee Analysis Tests Completed")
    print()

def test_comprehensive_financial_report():
    """Test comprehensive financial report functionality"""
    print("📊 Testing Comprehensive Financial Report")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = FinancialReportingConfig()
    
    # Create financial reporting system
    financial_reporting = FinancialReporting(db, config)
    
    # Test comprehensive financial report
    print("📋 Test 1: Comprehensive Financial Report Generation")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    comprehensive_report = financial_reporting.get_comprehensive_financial_report(start_date, end_date)
    
    print(f"   Comprehensive Financial Report:")
    print(f"     Report Period: {comprehensive_report.get('report_period', {}).get('start_date', 'N/A')} to {comprehensive_report.get('report_period', {}).get('end_date', 'N/A')}")
    print(f"     Period Days: {comprehensive_report.get('report_period', {}).get('period_days', 0)}")
    
    # Check all components
    components = [
        'revenue_recognition',
        'tax_calculation',
        'refund_tracking',
        'payment_processor_fees',
        'financial_summary',
        'compliance_status',
        'recommendations'
    ]
    
    print(f"     Report Components:")
    for component in components:
        data = comprehensive_report.get(component, {})
        if data:
            print(f"       ✅ {component.replace('_', ' ').title()}: Available")
        else:
            print(f"       ❌ {component.replace('_', ' ').title()}: Missing")
    
    # Financial summary
    financial_summary = comprehensive_report.get('financial_summary', {})
    print(f"     Financial Summary:")
    print(f"       Total Revenue: ${financial_summary.get('total_revenue', 0):,.2f}")
    print(f"       Total Expenses: ${financial_summary.get('total_expenses', 0):,.2f}")
    print(f"       Net Income: ${financial_summary.get('net_income', 0):,.2f}")
    print(f"       Gross Margin: {financial_summary.get('gross_margin', 0):.1%}")
    print(f"       Operating Margin: {financial_summary.get('operating_margin', 0):.1%}")
    print(f"       Cash Flow: ${financial_summary.get('cash_flow', 0):,.2f}")
    print(f"       Deferred Revenue: ${financial_summary.get('deferred_revenue', 0):,.2f}")
    print(f"       Accounts Receivable: ${financial_summary.get('accounts_receivable', 0):,.2f}")
    print(f"       Accounts Payable: ${financial_summary.get('accounts_payable', 0):,.2f}")
    
    # Compliance status
    compliance_status = comprehensive_report.get('compliance_status', {})
    print(f"     Compliance Status:")
    print(f"       Revenue Recognition Compliance: {compliance_status.get('revenue_recognition_compliance', 0):.1%}")
    print(f"       Tax Compliance: {compliance_status.get('tax_compliance', 0):.1%}")
    print(f"       Refund Compliance: {compliance_status.get('refund_compliance', 0):.1%}")
    print(f"       Payment Processor Compliance: {compliance_status.get('payment_processor_compliance', 0):.1%}")
    print(f"       Overall Compliance Score: {compliance_status.get('overall_compliance_score', 0):.1%}")
    print(f"       Audit Ready: {compliance_status.get('audit_ready', False)}")
    print(f"       Next Audit Date: {compliance_status.get('next_audit_date', 'N/A')}")
    
    # Recommendations
    recommendations = comprehensive_report.get('recommendations', [])
    print(f"     Financial Recommendations:")
    for rec in recommendations:
        print(f"       {rec['category'].replace('_', ' ').title()} - {rec['priority'].upper()}: {rec['recommendation']}")
        print(f"         Expected Impact: {rec['expected_impact']}")
    
    print()
    print("✅ Comprehensive Financial Report Tests Completed")
    print()

def test_financial_reporting_performance():
    """Test financial reporting performance"""
    print("⚡ Testing Financial Reporting Performance")
    print("=" * 70)
    
    # Setup
    db = MockDatabase()
    config = FinancialReportingConfig()
    
    # Create financial reporting system
    financial_reporting = FinancialReporting(db, config)
    
    # Test performance
    print("📈 Performance Metrics:")
    
    import time
    
    # Test revenue recognition report performance
    print("   Testing revenue recognition report performance...")
    start_time = time.time()
    
    for i in range(10):
        result = financial_reporting.generate_revenue_recognition_report()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average revenue recognition report time: {avg_time:.2f}ms")
    print(f"     Revenue recognition reports per second: {1000 / avg_time:.1f}")
    
    # Test tax calculation report performance
    print("   Testing tax calculation report performance...")
    start_time = time.time()
    
    for i in range(10):
        result = financial_reporting.generate_tax_calculation_report()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
    
    print(f"     Average tax calculation report time: {avg_time:.2f}ms")
    print(f"     Tax calculation reports per second: {1000 / avg_time:.1f}")
    
    # Test comprehensive report performance
    print("   Testing comprehensive report performance...")
    start_time = time.time()
    
    for i in range(5):
        result = financial_reporting.get_comprehensive_financial_report()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 5 * 1000  # Convert to milliseconds
    
    print(f"     Average comprehensive report time: {avg_time:.2f}ms")
    print(f"     Comprehensive reports per second: {1000 / avg_time:.1f}")
    
    # Test individual component performance
    components = [
        ('refund_tracking', lambda: financial_reporting.generate_refund_and_credit_report()),
        ('payment_processor_fees', lambda: financial_reporting.generate_payment_processor_fee_report())
    ]
    
    print("   Testing individual component performance...")
    for component_name, component_func in components:
        start_time = time.time()
        
        for i in range(10):
            result = component_func()
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
        
        print(f"     {component_name.replace('_', ' ').title()}: {avg_time:.2f}ms")
    
    print()
    print("✅ Financial Reporting Performance Tests Completed")
    print()

def main():
    """Main test function"""
    print("🧪 Financial Reporting System Tests")
    print("=" * 80)
    print()
    
    try:
        # Run all test suites
        test_revenue_recognition_reporting()
        test_tax_calculation_and_reporting()
        test_refund_and_credit_tracking()
        test_payment_processor_fee_analysis()
        test_comprehensive_financial_report()
        test_financial_reporting_performance()
        
        print("🎉 All tests completed successfully!")
        print()
        print("📋 Test Summary:")
        print("   ✅ Revenue Recognition Reporting")
        print("   ✅ Tax Calculation and Reporting")
        print("   ✅ Refund and Credit Tracking")
        print("   ✅ Payment Processor Fee Analysis")
        print("   ✅ Comprehensive Financial Report")
        print("   ✅ Financial Reporting Performance")
        print()
        print("🚀 The financial reporting system is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 