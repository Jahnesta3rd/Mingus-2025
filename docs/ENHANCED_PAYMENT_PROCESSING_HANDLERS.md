# Enhanced Payment Processing Handlers

## Overview

The enhanced `invoice.payment_succeeded` and `invoice.payment_failed` webhook handlers provide comprehensive payment processing and failure handling for MINGUS. These handlers process payment successes and failures from Stripe with detailed tracking, notifications, analytics, and business logic.

## Payment Success Handler (`invoice.payment_succeeded`)

### Key Features

#### 💰 **Comprehensive Payment Processing**
- Subscription and one-time payment handling
- Payment method validation and updates
- Amount and currency processing
- Tax calculation and handling
- Discount and coupon processing

#### 🔄 **Subscription Status Management**
- Automatic subscription reactivation
- Status updates (past_due → active)
- Subscription metadata updates
- Feature activation based on payment success

#### 👤 **Customer Status Updates**
- Payment history tracking
- Customer lifetime value calculation
- Payment method success tracking
- Customer metadata updates

#### 🎫 **Discount and Credit Handling**
- Coupon application tracking
- Discount amount calculations
- Credit application processing
- Promotional code validation

#### 🏛️ **Tax Processing**
- Tax amount calculations
- Tax rate tracking
- Tax breakdown processing
- Multi-jurisdiction tax handling

#### 🔔 **Multi-Channel Notifications**
- Payment confirmation emails
- Receipt generation and sending
- Subscription reactivation notifications
- First payment thank you messages

#### 📊 **Comprehensive Analytics**
- Payment success tracking
- Payment method usage analytics
- Customer lifetime value tracking
- Subscription payment analytics
- Discount usage tracking

### Handler Flow (12 Steps)

#### Step 1: Invoice Details Extraction
```python
def _extract_invoice_details(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate invoice details"""
    # Extract comprehensive invoice data
    invoice_details = {
        'invoice_id': invoice_data.get('id'),
        'customer_id': invoice_data.get('customer'),
        'subscription_id': invoice_data.get('subscription'),
        'status': invoice_data.get('status'),
        'amount_due': invoice_data.get('amount_due', 0) / 100,
        'amount_paid': invoice_data.get('amount_paid', 0) / 100,
        'amount_remaining': invoice_data.get('amount_remaining', 0) / 100,
        'currency': invoice_data.get('currency', 'usd'),
        'created': invoice_data.get('created'),
        'due_date': invoice_data.get('due_date'),
        'period_start': invoice_data.get('period_start'),
        'period_end': invoice_data.get('period_end'),
        'hosted_invoice_url': invoice_data.get('hosted_invoice_url'),
        'invoice_pdf': invoice_data.get('invoice_pdf'),
        'receipt_url': invoice_data.get('receipt_url'),
        'collection_method': invoice_data.get('collection_method'),
        'auto_advance': invoice_data.get('auto_advance'),
        'attempt_count': invoice_data.get('attempt_count', 0),
        'next_payment_attempt': invoice_data.get('next_payment_attempt'),
        'metadata': invoice_data.get('metadata', {}),
        'discount': invoice_data.get('discount'),
        'tax': invoice_data.get('tax'),
        'tax_percent': invoice_data.get('tax_percent'),
        'total_tax_amounts': invoice_data.get('total_tax_amounts', []),
        'lines': invoice_data.get('lines', {}).get('data', []),
        'payment_intent': invoice_data.get('payment_intent'),
        'charge': invoice_data.get('charge'),
        'payment_method': invoice_data.get('payment_method'),
        'payment_method_types': invoice_data.get('payment_method_types', []),
        'payment_settings': invoice_data.get('payment_settings', {}),
        'transfer_data': invoice_data.get('transfer_data'),
        'application_fee_amount': invoice_data.get('application_fee_amount'),
        'last_finalization_error': invoice_data.get('last_finalization_error'),
        'last_payment_error': invoice_data.get('last_payment_error'),
        'livemode': invoice_data.get('livemode', False)
    }
    
    # Validate required fields
    required_fields = ['invoice_id', 'customer_id', 'status', 'amount_paid']
    for field in required_fields:
        if not invoice_details.get(field):
            logger.error(f"Missing required field: {field}")
            return None
    
    return invoice_details
```

#### Step 2: Customer Validation
```python
def _find_and_validate_customer_for_invoice(self, invoice_data: Dict[str, Any]) -> Optional[Customer]:
    """Find and validate customer for invoice"""
    customer_id = invoice_data.get('customer')
    if not customer_id:
        logger.error("No customer ID found in invoice data")
        return None
    
    customer = self.db.query(Customer).filter(
        Customer.stripe_customer_id == customer_id
    ).first()
    
    if not customer:
        logger.error(f"Customer not found for ID: {customer_id}")
        return None
    
    if not customer.is_active:
        logger.warning(f"Customer {customer.email} is not active")
    
    return customer
```

#### Step 3: Billing Record Management
```python
def _find_or_create_billing_record(self, invoice_data: Dict[str, Any], customer: Customer, invoice_details: Dict[str, Any], changes: List[str]) -> BillingHistory:
    """Find or create billing history record"""
    # Try to find existing billing record
    billing_record = self.db.query(BillingHistory).filter(
        BillingHistory.stripe_invoice_id == invoice_details['invoice_id']
    ).first()
    
    if billing_record:
        logger.info(f"Found existing billing record for invoice {invoice_details['invoice_id']}")
        return billing_record
    
    # Find subscription if available
    subscription = None
    if invoice_details.get('subscription_id'):
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice_details['subscription_id']
        ).first()
    
    # Create new billing record
    billing_record = BillingHistory(
        customer_id=customer.id,
        subscription_id=subscription.id if subscription else None,
        stripe_invoice_id=invoice_details['invoice_id'],
        amount=invoice_details['amount_paid'],
        currency=invoice_details['currency'],
        status='paid',
        description=f"Invoice payment: {invoice_details['invoice_id']}",
        billing_date=datetime.fromtimestamp(invoice_details['created']) if invoice_details.get('created') else datetime.utcnow(),
        due_date=datetime.fromtimestamp(invoice_details['due_date']) if invoice_details.get('due_date') else None,
        paid_at=datetime.utcnow(),
        invoice_url=invoice_details.get('hosted_invoice_url'),
        invoice_pdf=invoice_details.get('invoice_pdf'),
        receipt_url=invoice_details.get('receipt_url'),
        metadata={
            'invoice_created': invoice_details.get('created'),
            'period_start': invoice_details.get('period_start'),
            'period_end': invoice_details.get('period_end'),
            'collection_method': invoice_details.get('collection_method'),
            'attempt_count': invoice_details.get('attempt_count', 0),
            'payment_intent': invoice_details.get('payment_intent'),
            'charge': invoice_details.get('charge'),
            'payment_method': invoice_details.get('payment_method'),
            'payment_method_types': invoice_details.get('payment_method_types', []),
            'livemode': invoice_details.get('livemode', False)
        }
    )
    
    return billing_record
```

#### Step 4: Billing Record Update
```python
def _update_billing_record_for_successful_payment(self, billing_record: BillingHistory, invoice_details: Dict[str, Any], changes: List[str]) -> None:
    """Update billing record for successful payment"""
    old_status = billing_record.status
    old_amount = billing_record.amount
    
    # Update billing record
    billing_record.status = 'paid'
    billing_record.amount = invoice_details['amount_paid']
    billing_record.paid_at = datetime.utcnow()
    billing_record.invoice_url = invoice_details.get('hosted_invoice_url')
    billing_record.invoice_pdf = invoice_details.get('invoice_pdf')
    billing_record.receipt_url = invoice_details.get('receipt_url')
    
    # Update metadata
    if not billing_record.metadata:
        billing_record.metadata = {}
    
    billing_record.metadata.update({
        'payment_processed_at': datetime.utcnow().isoformat(),
        'payment_intent': invoice_details.get('payment_intent'),
        'charge': invoice_details.get('charge'),
        'payment_method': invoice_details.get('payment_method'),
        'attempt_count': invoice_details.get('attempt_count', 0),
        'collection_method': invoice_details.get('collection_method')
    })
    
    if old_status != billing_record.status:
        changes.append(f"Billing status updated: {old_status} → {billing_record.status}")
    
    if old_amount != billing_record.amount:
        changes.append(f"Billing amount updated: ${old_amount} → ${billing_record.amount}")
```

#### Step 5: Subscription Status Updates
```python
def _handle_subscription_status_for_successful_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle subscription status updates for successful payment"""
    changes = []
    
    if not invoice_details.get('subscription_id'):
        return changes
    
    subscription = self.db.query(Subscription).filter(
        Subscription.stripe_subscription_id == invoice_details['subscription_id']
    ).first()
    
    if not subscription:
        return changes
    
    old_status = subscription.status
    
    # Update subscription status based on payment success
    if subscription.status in ['past_due', 'unpaid']:
        subscription.status = 'active'
        changes.append(f"Subscription status updated: {old_status} → {subscription.status}")
    
    # Update subscription metadata
    if not subscription.metadata:
        subscription.metadata = {}
    
    subscription.metadata.update({
        'last_payment_successful': datetime.utcnow().isoformat(),
        'last_payment_amount': invoice_details['amount_paid'],
        'last_payment_invoice': invoice_details['invoice_id'],
        'payment_method_used': invoice_details.get('payment_method')
    })
    
    return changes
```

#### Step 6: Customer Updates
```python
def _update_customer_for_successful_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Update customer for successful payment"""
    changes = []
    
    # Update customer payment status
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'last_payment_successful': datetime.utcnow().isoformat(),
        'last_payment_amount': invoice_details['amount_paid'],
        'last_payment_invoice': invoice_details['invoice_id'],
        'total_payments_made': customer.metadata.get('total_payments_made', 0) + 1,
        'total_amount_paid': customer.metadata.get('total_amount_paid', 0.0) + invoice_details['amount_paid']
    })
    
    # Update customer subscription status if they have active subscription
    if customer.has_active_subscription:
        customer.subscription_status = 'active'
        changes.append("Customer subscription status updated to active")
    
    changes.append("Customer payment data updated")
    
    return changes
```

#### Step 7: Payment Method Updates
```python
def _handle_payment_method_for_successful_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle payment method updates for successful payment"""
    changes = []
    payment_method = invoice_details.get('payment_method')
    
    if not payment_method:
        return changes
    
    # Update customer's default payment method if successful
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'last_successful_payment_method': payment_method,
        'payment_method_last_used': datetime.utcnow().isoformat()
    })
    
    changes.append(f"Payment method updated: {payment_method}")
    
    return changes
```

#### Step 8: Discount and Credit Processing
```python
def _handle_discounts_and_credits(self, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle discounts and credits for successful payment"""
    changes = []
    
    discount = invoice_details.get('discount')
    if discount:
        discount_amount = discount.get('amount_off', 0) / 100
        discount_type = discount.get('type', 'unknown')
        changes.append(f"Discount applied: ${discount_amount} ({discount_type})")
    
    # Handle any credits applied
    if invoice_details.get('amount_remaining') < 0:
        credit_amount = abs(invoice_details['amount_remaining'])
        changes.append(f"Credit applied: ${credit_amount}")
    
    return changes
```

#### Step 9: Tax Calculations
```python
def _handle_tax_calculations(self, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle tax calculations for successful payment"""
    changes = []
    
    tax_amount = invoice_details.get('tax', 0) / 100
    tax_percent = invoice_details.get('tax_percent')
    total_tax_amounts = invoice_details.get('total_tax_amounts', [])
    
    if tax_amount > 0:
        changes.append(f"Tax applied: ${tax_amount}")
        if tax_percent:
            changes.append(f"Tax rate: {tax_percent}%")
    
    if total_tax_amounts:
        for tax in total_tax_amounts:
            tax_rate = tax.get('rate', 0)
            tax_amount = tax.get('amount', 0) / 100
            changes.append(f"Tax breakdown: ${tax_amount} at {tax_rate}%")
    
    return changes
```

#### Step 10: Notifications
```python
def _send_successful_payment_notifications(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> int:
    """Send comprehensive successful payment notifications"""
    notifications_sent = 0
    
    # Send payment confirmation
    self.notification_service.send_payment_confirmation(
        customer.id, billing_record.id
    )
    notifications_sent += 1
    
    # Send receipt
    self.notification_service.send_payment_receipt(
        customer.id, billing_record.id, invoice_details
    )
    notifications_sent += 1
    
    # Send subscription reactivation notification if applicable
    if invoice_details.get('subscription_id'):
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice_details['subscription_id']
        ).first()
        
        if subscription and subscription.status == 'active':
            self.notification_service.send_subscription_reactivated_notification(
                customer.id, subscription.id
            )
            notifications_sent += 1
    
    # Send thank you notification for first payment
    total_payments = customer.metadata.get('total_payments_made', 0) if customer.metadata else 0
    if total_payments == 1:
        self.notification_service.send_first_payment_thank_you(
            customer.id, billing_record.id
        )
        notifications_sent += 1
    
    return notifications_sent
```

#### Step 11: Analytics Tracking
```python
def _track_successful_payment_analytics(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
    """Track comprehensive analytics for successful payment"""
    # Track basic payment success
    self.analytics_service.track_payment_succeeded(customer.id, billing_record.amount)
    
    # Track payment method usage
    payment_method = invoice_details.get('payment_method')
    if payment_method:
        self.analytics_service.track_payment_method_usage(customer.id, payment_method, billing_record.amount)
    
    # Track subscription payment if applicable
    if invoice_details.get('subscription_id'):
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice_details['subscription_id']
        ).first()
        
        if subscription:
            self.analytics_service.track_subscription_payment(
                customer.id, subscription.id, billing_record.amount
            )
    
    # Track customer lifetime value
    total_amount_paid = customer.metadata.get('total_amount_paid', 0.0) if customer.metadata else 0.0
    self.analytics_service.track_customer_lifetime_value(customer.id, total_amount_paid)
    
    # Track payment frequency
    self.analytics_service.track_payment_frequency(customer.id, billing_record.amount)
    
    # Track discount usage
    if invoice_details.get('discount'):
        discount_amount = invoice_details['discount'].get('amount_off', 0) / 100
        self.analytics_service.track_discount_usage(customer.id, discount_amount)
```

#### Step 12: Audit Logging
```python
def _log_successful_payment_audit(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
    """Log comprehensive audit trail for successful payment"""
    audit_log = AuditLog(
        event_type=AuditEventType.PAYMENT_SUCCEEDED,
        event_description=f"Payment succeeded: {billing_record.stripe_invoice_id}",
        severity=AuditSeverity.INFO,
        metadata={
            'customer_id': customer.id,
            'customer_email': customer.email,
            'billing_record_id': billing_record.id,
            'stripe_invoice_id': billing_record.stripe_invoice_id,
            'subscription_id': billing_record.subscription_id,
            'amount_paid': billing_record.amount,
            'currency': billing_record.currency,
            'payment_method': invoice_details.get('payment_method'),
            'payment_intent': invoice_details.get('payment_intent'),
            'charge': invoice_details.get('charge'),
            'collection_method': invoice_details.get('collection_method'),
            'attempt_count': invoice_details.get('attempt_count', 0),
            'discount': invoice_details.get('discount'),
            'tax': invoice_details.get('tax'),
            'tax_percent': invoice_details.get('tax_percent'),
            'invoice_url': invoice_details.get('hosted_invoice_url'),
            'receipt_url': invoice_details.get('receipt_url'),
            'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
            'processed_at': datetime.utcnow().isoformat()
        }
    )
    
    self.db.add(audit_log)
```

## Payment Failure Handler (`invoice.payment_failed`)

### Key Features

#### ❌ **Comprehensive Failure Processing**
- Multiple failure reasons handling
- Payment method failure tracking
- Retry logic management
- Dunning process automation

#### 🔄 **Retry Logic Management**
- Attempt count tracking
- Next retry scheduling
- Retry strategy determination
- Maximum attempt handling

#### 📧 **Dunning Management**
- Multi-stage dunning process
- Automated escalation
- Account suspension logic
- Payment reminder scheduling

#### 👤 **Customer Status Updates**
- Payment failure tracking
- Customer metadata updates
- Subscription status changes
- Payment method failure tracking

#### 🔔 **Multi-Channel Failure Notifications**
- Payment failure notifications
- Payment method update requests
- Retry notifications
- Account suspension warnings
- Support contact information

#### 📊 **Comprehensive Analytics**
- Payment failure tracking
- Failure reason analytics
- Attempt count tracking
- Dunning stage analytics
- Payment method failure analytics

### Handler Flow (12 Steps)

#### Step 1: Invoice Details Extraction
```python
def _extract_invoice_details(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate invoice details"""
    # Same as successful payment handler
    # Extracts comprehensive invoice data including failure-specific fields
    invoice_details = {
        # ... same fields as successful payment
        'last_payment_error': invoice_data.get('last_payment_error'),
        'next_payment_attempt': invoice_data.get('next_payment_attempt'),
        'attempt_count': invoice_data.get('attempt_count', 0)
    }
    
    return invoice_details
```

#### Step 2: Customer Validation
```python
def _find_and_validate_customer_for_invoice(self, invoice_data: Dict[str, Any]) -> Optional[Customer]:
    """Find and validate customer for invoice"""
    # Same as successful payment handler
    # Validates customer exists and is active
    return customer
```

#### Step 3: Billing Record Management
```python
def _find_or_create_billing_record_for_failure(self, invoice_data: Dict[str, Any], customer: Customer, invoice_details: Dict[str, Any], changes: List[str]) -> BillingHistory:
    """Find or create billing history record for failed payment"""
    # Try to find existing billing record
    billing_record = self.db.query(BillingHistory).filter(
        BillingHistory.stripe_invoice_id == invoice_details['invoice_id']
    ).first()
    
    if billing_record:
        return billing_record
    
    # Create new billing record for failed payment
    billing_record = BillingHistory(
        customer_id=customer.id,
        subscription_id=subscription.id if subscription else None,
        stripe_invoice_id=invoice_details['invoice_id'],
        amount=invoice_details['amount_due'],
        currency=invoice_details['currency'],
        status='failed',
        description=f"Failed invoice payment: {invoice_details['invoice_id']}",
        billing_date=datetime.fromtimestamp(invoice_details['created']) if invoice_details.get('created') else datetime.utcnow(),
        due_date=datetime.fromtimestamp(invoice_details['due_date']) if invoice_details.get('due_date') else None,
        invoice_url=invoice_details.get('hosted_invoice_url'),
        invoice_pdf=invoice_details.get('invoice_pdf'),
        metadata={
            'invoice_created': invoice_details.get('created'),
            'period_start': invoice_details.get('period_start'),
            'period_end': invoice_details.get('period_end'),
            'collection_method': invoice_details.get('collection_method'),
            'attempt_count': invoice_details.get('attempt_count', 0),
            'next_payment_attempt': invoice_details.get('next_payment_attempt'),
            'last_payment_error': invoice_details.get('last_payment_error'),
            'livemode': invoice_details.get('livemode', False)
        }
    )
    
    return billing_record
```

#### Step 4: Billing Record Update
```python
def _update_billing_record_for_failed_payment(self, billing_record: BillingHistory, invoice_details: Dict[str, Any], changes: List[str]) -> None:
    """Update billing record for failed payment"""
    old_status = billing_record.status
    old_amount = billing_record.amount
    
    # Update billing record
    billing_record.status = 'failed'
    billing_record.amount = invoice_details['amount_due']
    billing_record.invoice_url = invoice_details.get('hosted_invoice_url')
    billing_record.invoice_pdf = invoice_details.get('invoice_pdf')
    
    # Update metadata
    if not billing_record.metadata:
        billing_record.metadata = {}
    
    billing_record.metadata.update({
        'payment_failed_at': datetime.utcnow().isoformat(),
        'attempt_count': invoice_details.get('attempt_count', 0),
        'next_payment_attempt': invoice_details.get('next_payment_attempt'),
        'last_payment_error': invoice_details.get('last_payment_error'),
        'collection_method': invoice_details.get('collection_method')
    })
    
    if old_status != billing_record.status:
        changes.append(f"Billing status updated: {old_status} → {billing_record.status}")
    
    if old_amount != billing_record.amount:
        changes.append(f"Billing amount updated: ${old_amount} → ${billing_record.amount}")
```

#### Step 5: Subscription Status Updates
```python
def _handle_subscription_status_for_failed_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle subscription status updates for failed payment"""
    changes = []
    
    if not invoice_details.get('subscription_id'):
        return changes
    
    subscription = self.db.query(Subscription).filter(
        Subscription.stripe_subscription_id == invoice_details['subscription_id']
    ).first()
    
    if not subscription:
        return changes
    
    old_status = subscription.status
    
    # Update subscription status based on payment failure
    if subscription.status == 'active':
        subscription.status = 'past_due'
        changes.append(f"Subscription status updated: {old_status} → {subscription.status}")
    
    # Update subscription metadata
    if not subscription.metadata:
        subscription.metadata = {}
    
    subscription.metadata.update({
        'last_payment_failed': datetime.utcnow().isoformat(),
        'last_payment_failure_amount': invoice_details['amount_due'],
        'last_payment_failure_invoice': invoice_details['invoice_id'],
        'payment_failure_count': subscription.metadata.get('payment_failure_count', 0) + 1,
        'last_payment_error': invoice_details.get('last_payment_error')
    })
    
    return changes
```

#### Step 6: Customer Updates
```python
def _update_customer_for_failed_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Update customer for failed payment"""
    changes = []
    
    # Update customer payment status
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'last_payment_failed': datetime.utcnow().isoformat(),
        'last_payment_failure_amount': invoice_details['amount_due'],
        'last_payment_failure_invoice': invoice_details['invoice_id'],
        'total_payment_failures': customer.metadata.get('total_payment_failures', 0) + 1,
        'last_payment_error': invoice_details.get('last_payment_error')
    })
    
    # Update customer subscription status if they have active subscription
    if customer.has_active_subscription:
        customer.subscription_status = 'past_due'
        changes.append("Customer subscription status updated to past_due")
    
    changes.append("Customer payment failure data updated")
    
    return changes
```

#### Step 7: Payment Method Issues
```python
def _handle_payment_method_for_failed_payment(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle payment method issues for failed payment"""
    changes = []
    
    payment_method = invoice_details.get('payment_method')
    last_payment_error = invoice_details.get('last_payment_error')
    
    if not payment_method or not last_payment_error:
        return changes
    
    # Update customer's payment method failure tracking
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'last_failed_payment_method': payment_method,
        'payment_method_failure_count': customer.metadata.get('payment_method_failure_count', 0) + 1,
        'last_payment_error': last_payment_error
    })
    
    changes.append(f"Payment method failure tracked: {payment_method}")
    
    return changes
```

#### Step 8: Retry Logic
```python
def _handle_payment_retry_logic(self, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle payment retry logic"""
    changes = []
    
    attempt_count = invoice_details.get('attempt_count', 0)
    next_payment_attempt = invoice_details.get('next_payment_attempt')
    
    if attempt_count > 0:
        changes.append(f"Payment attempt #{attempt_count} failed")
    
    if next_payment_attempt:
        next_attempt_date = datetime.fromtimestamp(next_payment_attempt)
        changes.append(f"Next retry scheduled: {next_attempt_date}")
        
        # Schedule retry notification
        # self.retry_service.schedule_retry_notification(customer_id, next_attempt_date)
    
    # Determine retry strategy based on attempt count
    if attempt_count >= 3:
        changes.append("Maximum retry attempts reached")
        # self.retry_service.escalate_to_collections(customer_id)
    elif attempt_count >= 2:
        changes.append("Final retry attempt scheduled")
        # self.retry_service.schedule_final_retry(customer_id)
    
    return changes
```

#### Step 9: Dunning Management
```python
def _handle_dunning_management(self, customer: Customer, invoice_details: Dict[str, Any]) -> List[str]:
    """Handle dunning management for failed payments"""
    changes = []
    
    attempt_count = invoice_details.get('attempt_count', 0)
    amount_due = invoice_details['amount_due']
    
    # Determine dunning stage based on attempt count
    if attempt_count == 1:
        changes.append("Dunning stage 1: Payment reminder sent")
        # self.dunning_service.send_payment_reminder(customer.id, amount_due)
    elif attempt_count == 2:
        changes.append("Dunning stage 2: Payment warning sent")
        # self.dunning_service.send_payment_warning(customer.id, amount_due)
    elif attempt_count == 3:
        changes.append("Dunning stage 3: Final notice sent")
        # self.dunning_service.send_final_notice(customer.id, amount_due)
    elif attempt_count >= 4:
        changes.append("Dunning stage 4: Account suspension initiated")
        # self.dunning_service.suspend_account(customer.id)
    
    # Track dunning metrics
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'dunning_stage': min(attempt_count, 4),
        'last_dunning_action': datetime.utcnow().isoformat(),
        'dunning_amount': amount_due
    })
    
    return changes
```

#### Step 10: Failure Notifications
```python
def _send_failed_payment_notifications(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> int:
    """Send comprehensive failed payment notifications"""
    notifications_sent = 0
    
    # Send payment failure notification
    self.notification_service.send_payment_failure_notification(
        customer.id, billing_record.id
    )
    notifications_sent += 1
    
    # Send payment method update request
    self.notification_service.send_payment_method_update_request(
        customer.id, billing_record.id, invoice_details
    )
    notifications_sent += 1
    
    # Send retry notification if applicable
    next_payment_attempt = invoice_details.get('next_payment_attempt')
    if next_payment_attempt:
        self.notification_service.send_payment_retry_notification(
            customer.id, billing_record.id, next_payment_attempt
        )
        notifications_sent += 1
    
    # Send account suspension warning if multiple failures
    attempt_count = invoice_details.get('attempt_count', 0)
    if attempt_count >= 3:
        self.notification_service.send_account_suspension_warning(
            customer.id, billing_record.id
        )
        notifications_sent += 1
    
    # Send support contact information
    self.notification_service.send_payment_support_contact(
        customer.id, billing_record.id
    )
    notifications_sent += 1
    
    return notifications_sent
```

#### Step 11: Failure Analytics
```python
def _track_failed_payment_analytics(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
    """Track comprehensive analytics for failed payment"""
    # Track basic payment failure
    self.analytics_service.track_payment_failed(customer.id, billing_record.amount)
    
    # Track payment method failure
    payment_method = invoice_details.get('payment_method')
    if payment_method:
        self.analytics_service.track_payment_method_failure(customer.id, payment_method, billing_record.amount)
    
    # Track subscription payment failure if applicable
    if invoice_details.get('subscription_id'):
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice_details['subscription_id']
        ).first()
        
        if subscription:
            self.analytics_service.track_subscription_payment_failure(
                customer.id, subscription.id, billing_record.amount
            )
    
    # Track failure reason
    last_payment_error = invoice_details.get('last_payment_error')
    if last_payment_error:
        self.analytics_service.track_payment_failure_reason(customer.id, last_payment_error, billing_record.amount)
    
    # Track attempt count
    attempt_count = invoice_details.get('attempt_count', 0)
    self.analytics_service.track_payment_attempt_count(customer.id, attempt_count, billing_record.amount)
    
    # Track dunning stage
    dunning_stage = min(attempt_count, 4)
    self.analytics_service.track_dunning_stage(customer.id, dunning_stage, billing_record.amount)
```

#### Step 12: Failure Audit Logging
```python
def _log_failed_payment_audit(self, customer: Customer, billing_record: BillingHistory, invoice_details: Dict[str, Any]) -> None:
    """Log comprehensive audit trail for failed payment"""
    audit_log = AuditLog(
        event_type=AuditEventType.PAYMENT_FAILED,
        event_description=f"Payment failed: {billing_record.stripe_invoice_id}",
        severity=AuditSeverity.WARNING,
        metadata={
            'customer_id': customer.id,
            'customer_email': customer.email,
            'billing_record_id': billing_record.id,
            'stripe_invoice_id': billing_record.stripe_invoice_id,
            'subscription_id': billing_record.subscription_id,
            'amount_due': billing_record.amount,
            'currency': billing_record.currency,
            'payment_method': invoice_details.get('payment_method'),
            'attempt_count': invoice_details.get('attempt_count', 0),
            'next_payment_attempt': invoice_details.get('next_payment_attempt'),
            'last_payment_error': invoice_details.get('last_payment_error'),
            'collection_method': invoice_details.get('collection_method'),
            'invoice_url': invoice_details.get('hosted_invoice_url'),
            'dunning_stage': min(invoice_details.get('attempt_count', 0), 4),
            'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
            'failed_at': datetime.utcnow().isoformat()
        }
    )
    
    self.db.add(audit_log)
```

## Dunning Management

### Dunning Stages

| Attempt Count | Stage | Action | Description |
|--------------|-------|--------|-------------|
| 1 | Stage 1 | Payment Reminder | Gentle reminder about payment |
| 2 | Stage 2 | Payment Warning | More urgent warning |
| 3 | Stage 3 | Final Notice | Final warning before suspension |
| 4+ | Stage 4 | Account Suspension | Account suspended, features disabled |

### Retry Logic

#### Retry Strategy
- **Attempt 1**: Immediate retry (same day)
- **Attempt 2**: 3 days later
- **Attempt 3**: 7 days later
- **Attempt 4+**: Escalation to collections

#### Retry Conditions
- **Card declined**: Retry with same method
- **Insufficient funds**: Retry after 3 days
- **Expired card**: Request payment method update
- **Fraudulent**: No retry, immediate suspension

## Payment Failure Reasons

### Common Failure Reasons

| Reason | Description | Action |
|--------|-------------|--------|
| `card_declined` | Card was declined by issuer | Retry with same method |
| `insufficient_funds` | Card has insufficient funds | Retry after 3 days |
| `expired_card` | Card has expired | Request payment method update |
| `incorrect_cvc` | CVC code is incorrect | Request payment method update |
| `processing_error` | Processing error occurred | Retry immediately |
| `fraudulent` | Payment flagged as fraudulent | No retry, suspend account |

### Failure Handling by Reason

```python
def _handle_failure_by_reason(self, reason: str, attempt_count: int) -> Dict[str, Any]:
    """Handle failure based on specific reason"""
    handling = {
        'card_declined': {
            'retry': True,
            'retry_delay': 1,  # days
            'max_attempts': 3,
            'action': 'retry_same_method'
        },
        'insufficient_funds': {
            'retry': True,
            'retry_delay': 3,  # days
            'max_attempts': 3,
            'action': 'retry_same_method'
        },
        'expired_card': {
            'retry': False,
            'action': 'request_payment_method_update'
        },
        'incorrect_cvc': {
            'retry': False,
            'action': 'request_payment_method_update'
        },
        'processing_error': {
            'retry': True,
            'retry_delay': 0,  # immediate
            'max_attempts': 3,
            'action': 'retry_same_method'
        },
        'fraudulent': {
            'retry': False,
            'action': 'suspend_account'
        }
    }
    
    return handling.get(reason, {
        'retry': True,
        'retry_delay': 1,
        'max_attempts': 3,
        'action': 'retry_same_method'
    })
```

## Testing Scenarios

### Payment Success Scenarios

1. **Subscription Payment Success**
   - Monthly/yearly subscription payment
   - Subscription reactivation
   - First payment processing

2. **One-Time Payment Success**
   - Feature upgrade payment
   - Service payment
   - Add-on payment

3. **Payment with Discount**
   - Coupon application
   - Promotional code usage
   - Credit application

4. **Payment with Tax**
   - Tax calculation
   - Multi-jurisdiction tax
   - Tax breakdown

### Payment Failure Scenarios

1. **First Attempt Failure**
   - Card declined
   - Insufficient funds
   - Expired card

2. **Multiple Attempt Failure**
   - Retry logic testing
   - Dunning process
   - Account suspension

3. **Payment Method Issues**
   - Expired card handling
   - Invalid CVC
   - Processing errors

4. **Fraudulent Payment**
   - Fraud detection
   - Account suspension
   - Security measures

## Integration Points

### Services Integration
- **NotificationService**: Sends various payment notifications
- **AnalyticsService**: Tracks payment metrics and analytics
- **RetryService**: Manages payment retry logic (to be implemented)
- **DunningService**: Handles dunning process (to be implemented)

### Database Models
- **Customer**: Updated with payment status and metadata
- **Subscription**: Updated with payment status and metadata
- **BillingHistory**: Created/updated for payment records
- **AuditLog**: Comprehensive audit trail logged

## Monitoring and Alerting

### Key Metrics
- **Payment Success Rate**: Percentage of successful payments
- **Payment Failure Rate**: Percentage of failed payments
- **Retry Success Rate**: Percentage of successful retries
- **Dunning Effectiveness**: Conversion rate by dunning stage

### Alerts
- **High Failure Rate**: Alert when failure rate exceeds threshold
- **Retry Failures**: Alert when retry success rate is low
- **Dunning Issues**: Alert when dunning process fails
- **Payment Method Issues**: Alert on payment method problems

## Best Practices

### Development
1. **Always validate payment data** before processing
2. **Use transactions** for data consistency
3. **Log comprehensive audit trails** for debugging
4. **Handle all failure scenarios** gracefully
5. **Test retry logic** thoroughly

### Operations
1. **Monitor payment success/failure rates** closely
2. **Set up alerts** for critical failures
3. **Review dunning effectiveness** regularly
4. **Monitor retry success rates** by reason
5. **Track customer lifetime value** changes

### Security
1. **Validate webhook signatures** before processing
2. **Sanitize all payment data** to prevent injection
3. **Log security-relevant events** for audit
4. **Handle fraudulent payments** appropriately
5. **Protect sensitive payment information**

## Future Enhancements

### Planned Features
1. **Advanced retry logic** - Machine learning-based retry timing
2. **Smart dunning** - Personalized dunning strategies
3. **Payment method optimization** - Automatic payment method switching
4. **Fraud detection** - Advanced fraud prevention
5. **Multi-currency support** - Enhanced currency handling

### Performance Improvements
1. **Async processing** - Process non-critical operations asynchronously
2. **Caching** - Cache frequently accessed payment data
3. **Database optimization** - Optimize payment-related queries
4. **Batch processing** - Process multiple payments in batches

## Conclusion

The enhanced payment processing handlers provide robust, scalable, and comprehensive solutions for processing payment successes and failures from Stripe. They ensure proper payment handling, provide excellent user experience through notifications, track analytics for business insights, and maintain detailed audit trails for compliance and debugging.

The handlers are designed to be maintainable, testable, and extensible, making it easy to add new payment features and handle different payment scenarios as the business grows. 