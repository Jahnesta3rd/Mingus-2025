# Enhanced Subscription Update and Cancellation Handlers

## Overview

The enhanced `customer.subscription.updated` and `customer.subscription.deleted` webhook handlers provide comprehensive subscription change management and cancellation processing for MINGUS. These handlers process subscription modifications and cancellations from Stripe with detailed tracking, notifications, and analytics.

## Subscription Update Handler (`customer.subscription.updated`)

### Key Features

#### 🔄 **Comprehensive Change Tracking**
- Status changes (active, trialing, past_due, canceled, etc.)
- Amount and billing cycle changes
- Pricing tier upgrades and downgrades
- Trial period modifications
- Payment method updates
- Quantity changes

#### 💰 **Pricing Tier Management**
- Automatic pricing tier detection
- Feature activation/deactivation based on tier changes
- Billing cycle determination
- Amount calculation and validation

#### 🆓 **Trial Period Handling**
- Trial start/end date changes
- Trial-specific feature setup
- Trial ending notifications
- Trial analytics tracking

#### 💳 **Billing and Payment Updates**
- Payment method configuration changes
- Collection method updates
- Billing cycle anchor management
- Billing history creation for significant changes

#### 🔔 **Multi-Channel Notifications**
- Status change notifications
- Amount change notifications
- Billing cycle change notifications
- Trial ending notifications
- Cancellation scheduled notifications

#### 📊 **Analytics and Tracking**
- Subscription update tracking
- Change type analytics
- Pricing tier change tracking
- Billing cycle change tracking
- Status change tracking
- Cancellation scheduling tracking

### Handler Flow (13 Steps)

#### Step 1: Subscription Validation
```python
def _find_and_validate_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Subscription]:
    """Find and validate subscription for updates"""
    subscription_id = subscription_data.get('id')
    if not subscription_id:
        logger.error("No subscription ID found in subscription data")
        return None
    
    subscription = self.db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if not subscription:
        logger.error(f"Subscription not found for ID: {subscription_id}")
        return None
    
    return subscription
```

#### Step 2: Data Extraction
```python
def _extract_subscription_details(self, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate subscription details"""
    items = subscription_data.get('items', {}).get('data', [])
    if not items:
        logger.error("No subscription items found")
        return None
    
    # Extract comprehensive subscription data
    subscription_details = {
        'subscription_id': subscription_data.get('id'),
        'status': subscription_data.get('status'),
        'current_period_start': subscription_data.get('current_period_start'),
        'current_period_end': subscription_data.get('current_period_end'),
        'trial_start': subscription_data.get('trial_start'),
        'trial_end': subscription_data.get('trial_end'),
        'price_id': price.get('id'),
        'price_amount': price.get('unit_amount', 0) / 100,
        'price_currency': price.get('currency', 'usd'),
        'price_interval': price.get('recurring', {}).get('interval', 'month'),
        'quantity': item.get('quantity', 1),
        # ... additional fields
    }
    
    return subscription_details
```

#### Step 3: Old Values Capture
```python
def _capture_old_subscription_values(self, subscription: Subscription) -> Dict[str, Any]:
    """Capture old subscription values for comparison"""
    return {
        'status': subscription.status,
        'amount': subscription.amount,
        'billing_cycle': subscription.billing_cycle,
        'pricing_tier_id': subscription.pricing_tier_id,
        'trial_start': subscription.trial_start,
        'trial_end': subscription.trial_end,
        'cancel_at_period_end': subscription.cancel_at_period_end,
        'canceled_at': subscription.canceled_at,
        'current_period_start': subscription.current_period_start,
        'current_period_end': subscription.current_period_end,
        'quantity': subscription.quantity,
        'collection_method': subscription.collection_method,
        'default_payment_method': subscription.default_payment_method,
        'metadata': subscription.metadata.copy() if subscription.metadata else {}
    }
```

#### Step 4: Subscription Record Update
```python
def _update_subscription_record(self, subscription: Subscription, subscription_details: Dict[str, Any], changes: List[str]) -> None:
    """Update subscription record with comprehensive changes"""
    # Update basic fields
    old_status = subscription.status
    old_amount = subscription.amount
    old_billing_cycle = subscription.billing_cycle
    old_quantity = subscription.quantity
    
    # Update status
    subscription.status = subscription_details['status']
    if old_status != subscription.status:
        changes.append(f"Status changed: {old_status} → {subscription.status}")
    
    # Update billing periods
    subscription.current_period_start = datetime.fromtimestamp(subscription_details['current_period_start'])
    subscription.current_period_end = datetime.fromtimestamp(subscription_details['current_period_end'])
    
    # Update amount and billing cycle
    price_interval = subscription_details.get('price_interval', 'month')
    new_billing_cycle = 'monthly' if price_interval == 'month' else 'yearly'
    subscription.billing_cycle = new_billing_cycle
    
    new_amount = subscription_details.get('price_amount', 0) * subscription_details.get('quantity', 1)
    subscription.amount = new_amount
    
    if old_amount != new_amount:
        changes.append(f"Amount changed: ${old_amount} → ${new_amount}")
    
    if old_billing_cycle != new_billing_cycle:
        changes.append(f"Billing cycle changed: {old_billing_cycle} → {new_billing_cycle}")
    
    # Update quantity
    new_quantity = subscription_details.get('quantity', 1)
    subscription.quantity = new_quantity
    if old_quantity != new_quantity:
        changes.append(f"Quantity changed: {old_quantity} → {new_quantity}")
    
    # Update other fields...
```

#### Step 5: Pricing Tier Changes
```python
def _handle_pricing_tier_changes(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> List[str]:
    """Handle pricing tier changes"""
    changes = []
    price_id = subscription_details.get('price_id')
    if not price_id:
        return changes
    
    # Find new pricing tier
    new_pricing_tier = self.db.query(PricingTier).filter(
        (PricingTier.stripe_price_id_monthly == price_id) |
        (PricingTier.stripe_price_id_yearly == price_id)
    ).first()
    
    old_pricing_tier_id = subscription.pricing_tier_id
    subscription.pricing_tier_id = new_pricing_tier.id if new_pricing_tier else None
    
    if old_pricing_tier_id != subscription.pricing_tier_id:
        if new_pricing_tier:
            changes.append(f"Pricing tier changed: {new_pricing_tier.name}")
        else:
            changes.append("Pricing tier removed")
        
        # Handle feature changes based on pricing tier
        self._update_features_for_pricing_tier_change(subscription, old_pricing_tier_id, subscription.pricing_tier_id)
    
    return changes
```

#### Step 6: Trial Period Changes
```python
def _handle_trial_period_changes(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> List[str]:
    """Handle trial period changes"""
    changes = []
    old_trial_start = subscription.trial_start
    old_trial_end = subscription.trial_end
    
    # Update trial period
    if subscription_details.get('trial_start'):
        subscription.trial_start = datetime.fromtimestamp(subscription_details['trial_start'])
    if subscription_details.get('trial_end'):
        subscription.trial_end = datetime.fromtimestamp(subscription_details['trial_end'])
    
    # Check for changes
    if old_trial_start != subscription.trial_start:
        if subscription.trial_start:
            changes.append(f"Trial started: {subscription.trial_start.date()}")
        else:
            changes.append("Trial start removed")
    
    if old_trial_end != subscription.trial_end:
        if subscription.trial_end:
            changes.append(f"Trial ends: {subscription.trial_end.date()}")
        else:
            changes.append("Trial end removed")
    
    return changes
```

#### Step 7: Billing Changes
```python
def _handle_billing_changes(self, subscription: Subscription, subscription_details: Dict[str, Any]) -> List[str]:
    """Handle billing and payment method changes"""
    changes = []
    old_collection_method = subscription.collection_method
    old_default_payment_method = subscription.default_payment_method
    old_default_source = subscription.default_source
    
    # Update billing fields
    subscription.collection_method = subscription_details.get('collection_method')
    subscription.default_payment_method = subscription_details.get('default_payment_method')
    subscription.default_source = subscription_details.get('default_source')
    
    # Check for changes
    if old_collection_method != subscription.collection_method:
        changes.append(f"Collection method changed: {old_collection_method} → {subscription.collection_method}")
    
    if old_default_payment_method != subscription.default_payment_method:
        if subscription.default_payment_method:
            changes.append(f"Default payment method updated: {subscription.default_payment_method}")
        else:
            changes.append("Default payment method removed")
    
    return changes
```

#### Step 8: Customer Status Update
```python
def _update_customer_for_subscription_changes(self, subscription: Subscription, old_values: Dict[str, Any]) -> List[str]:
    """Update customer based on subscription changes"""
    changes = []
    customer = self.db.query(Customer).filter(Customer.id == subscription.customer_id).first()
    if not customer:
        return changes
    
    old_status = old_values.get('status')
    new_status = subscription.status
    
    # Update customer subscription status
    if old_status != new_status:
        customer.subscription_status = new_status
        
        # Update active subscription flag
        if new_status in ['active', 'trialing']:
            customer.has_active_subscription = True
        elif new_status in ['canceled', 'unpaid', 'past_due']:
            customer.has_active_subscription = False
        
        changes.append(f"Customer subscription status updated: {old_status} → {new_status}")
    
    # Update customer metadata
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'subscription_last_updated': datetime.utcnow().isoformat(),
        'current_subscription_status': new_status,
        'current_subscription_amount': subscription.amount,
        'current_billing_cycle': subscription.billing_cycle
    })
    
    return changes
```

#### Step 9: Feature Changes
```python
def _handle_feature_changes(self, subscription: Subscription, old_values: Dict[str, Any]) -> List[str]:
    """Handle feature changes based on subscription updates"""
    changes = []
    old_pricing_tier_id = old_values.get('pricing_tier_id')
    new_pricing_tier_id = subscription.pricing_tier_id
    
    if old_pricing_tier_id != new_pricing_tier_id:
        # Update features based on new pricing tier
        if new_pricing_tier_id:
            pricing_tier = self.db.query(PricingTier).filter(PricingTier.id == new_pricing_tier_id).first()
            if pricing_tier:
                features = pricing_tier.features or []
                changes.append(f"Features updated: {', '.join(features)}")
                # self.feature_service.update_features(subscription.customer_id, features)
        else:
            changes.append("Features removed (no pricing tier)")
    
    # Handle status-based feature changes
    old_status = old_values.get('status')
    new_status = subscription.status
    
    if old_status != new_status:
        if new_status == 'active':
            changes.append("Features activated")
        elif new_status == 'canceled':
            changes.append("Features deactivated")
        elif new_status == 'past_due':
            changes.append("Features limited (past due)")
    
    return changes
```

#### Step 10: Billing History Creation
```python
def _create_billing_history_for_changes(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> Optional[BillingHistory]:
    """Create billing history for significant changes"""
    # Only create billing history for significant changes
    significant_changes = [
        'Amount changed',
        'Billing cycle changed',
        'Pricing tier changed',
        'Status changed'
    ]
    
    has_significant_changes = any(any(sig in change for sig in significant_changes) for change in changes)
    
    if has_significant_changes:
        billing_history = BillingHistory(
            customer_id=subscription.customer_id,
            subscription_id=subscription.id,
            stripe_invoice_id=None,
            amount=subscription.amount,
            currency='usd',
            status='pending',
            description=f"Subscription updated: {', '.join(changes[:3])}",
            billing_date=datetime.utcnow(),
            due_date=subscription.current_period_end,
            metadata={
                'subscription_update': True,
                'stripe_subscription_id': subscription.stripe_subscription_id,
                'changes': changes,
                'old_amount': old_values.get('amount'),
                'new_amount': subscription.amount
            }
        )
        
        return billing_history
    
    return None
```

#### Step 11: Notifications
```python
def _send_subscription_update_notifications(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> int:
    """Send comprehensive subscription update notifications"""
    notifications_sent = 0
    
    # Send status change notification
    old_status = old_values.get('status')
    new_status = subscription.status
    
    if old_status != new_status:
        self.notification_service.send_subscription_status_update(
            subscription.customer_id, subscription.id, new_status
        )
        notifications_sent += 1
    
    # Send amount change notification
    old_amount = old_values.get('amount')
    new_amount = subscription.amount
    
    if old_amount != new_amount:
        self.notification_service.send_subscription_amount_change_notification(
            subscription.customer_id, subscription.id, old_amount, new_amount
        )
        notifications_sent += 1
    
    # Send billing cycle change notification
    old_billing_cycle = old_values.get('billing_cycle')
    new_billing_cycle = subscription.billing_cycle
    
    if old_billing_cycle != new_billing_cycle:
        self.notification_service.send_billing_cycle_change_notification(
            subscription.customer_id, subscription.id, old_billing_cycle, new_billing_cycle
        )
        notifications_sent += 1
    
    # Send trial ending notification
    if subscription.trial_end and not old_values.get('trial_end'):
        self.notification_service.send_trial_ending_notification(
            subscription.customer_id, subscription.id
        )
        notifications_sent += 1
    
    # Send cancellation scheduled notification
    if subscription.cancel_at_period_end and not old_values.get('cancel_at_period_end'):
        self.notification_service.send_cancellation_scheduled_notification(
            subscription.customer_id, subscription.id, subscription.current_period_end
        )
        notifications_sent += 1
    
    return notifications_sent
```

#### Step 12: Analytics Tracking
```python
def _track_subscription_update_analytics(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> None:
    """Track comprehensive analytics for subscription updates"""
    # Track subscription update
    self.analytics_service.track_subscription_updated(subscription.customer_id, subscription.id, changes)
    
    # Track specific change types
    for change in changes:
        if 'Amount changed' in change:
            old_amount = old_values.get('amount', 0)
            new_amount = subscription.amount
            self.analytics_service.track_subscription_amount_change(
                subscription.customer_id, subscription.id, old_amount, new_amount
            )
        
        if 'Billing cycle changed' in change:
            old_cycle = old_values.get('billing_cycle')
            new_cycle = subscription.billing_cycle
            self.analytics_service.track_billing_cycle_change(
                subscription.customer_id, subscription.id, old_cycle, new_cycle
            )
        
        if 'Status changed' in change:
            old_status = old_values.get('status')
            new_status = subscription.status
            self.analytics_service.track_subscription_status_change(
                subscription.customer_id, subscription.id, old_status, new_status
            )
        
        if 'Pricing tier changed' in change:
            old_tier_id = old_values.get('pricing_tier_id')
            new_tier_id = subscription.pricing_tier_id
            self.analytics_service.track_pricing_tier_change(
                subscription.customer_id, subscription.id, old_tier_id, new_tier_id
            )
    
    # Track cancellation scheduling
    if subscription.cancel_at_period_end and not old_values.get('cancel_at_period_end'):
        self.analytics_service.track_cancellation_scheduled(
            subscription.customer_id, subscription.id, subscription.current_period_end
        )
```

#### Step 13: Audit Logging
```python
def _log_subscription_update_audit(self, subscription: Subscription, old_values: Dict[str, Any], changes: List[str]) -> None:
    """Log comprehensive audit trail for subscription updates"""
    audit_log = AuditLog(
        event_type=AuditEventType.SUBSCRIPTION_UPDATED,
        event_description=f"Subscription updated: {subscription.stripe_subscription_id}",
        severity=AuditSeverity.INFO,
        metadata={
            'subscription_id': subscription.id,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'customer_id': subscription.customer_id,
            'old_values': old_values,
            'new_values': {
                'status': subscription.status,
                'amount': subscription.amount,
                'billing_cycle': subscription.billing_cycle,
                'pricing_tier_id': subscription.pricing_tier_id,
                'trial_start': subscription.trial_start.isoformat() if subscription.trial_start else None,
                'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                'quantity': subscription.quantity,
                'collection_method': subscription.collection_method
            },
            'changes': changes,
            'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
            'updated_at': datetime.utcnow().isoformat()
        }
    )
    
    self.db.add(audit_log)
```

## Subscription Cancellation Handler (`customer.subscription.deleted`)

### Key Features

#### 🚫 **Comprehensive Cancellation Processing**
- Multiple cancellation reasons (customer-requested, payment failure, fraudulent, etc.)
- Immediate vs end-of-period cancellation handling
- Cancellation source tracking
- Cancellation feedback collection

#### 📊 **Pre-Cancellation State Capture**
- Subscription lifetime metrics calculation
- Total billing cycles tracking
- Total amount paid calculation
- Feature usage history

#### 🔧 **Feature Deactivation**
- Automatic feature deactivation
- Immediate vs delayed deactivation
- Trial-specific cleanup
- Pricing tier-based feature removal

#### 👤 **Customer Status Management**
- Customer subscription status updates
- Active subscription flag management
- Customer metadata updates
- Historical data preservation

#### 🧹 **Data Retention and Cleanup**
- Reason-based retention periods
- Cleanup scheduling
- Immediate cleanup for fraud
- Data retention notifications

#### 🔔 **Multi-Channel Cancellation Notifications**
- Cancellation confirmation
- Reason-specific notifications
- Feedback request notifications
- Reactivation offers
- Data retention notifications

#### 📈 **Comprehensive Analytics**
- Cancellation reason tracking
- Churn metrics
- Lifetime value calculation
- Reactivation potential tracking
- Cancellation source analytics

### Handler Flow (11 Steps)

#### Step 1: Subscription Validation
```python
def _find_and_validate_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Subscription]:
    """Find and validate subscription for cancellation"""
    subscription_id = subscription_data.get('id')
    if not subscription_id:
        logger.error("No subscription ID found in subscription data")
        return None
    
    subscription = self.db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if not subscription:
        logger.error(f"Subscription not found for ID: {subscription_id}")
        return None
    
    return subscription
```

#### Step 2: Cancellation Details Extraction
```python
def _extract_cancellation_details(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract cancellation details from subscription data"""
    return {
        'cancellation_reason': subscription_data.get('cancellation_reason'),
        'canceled_at': subscription_data.get('canceled_at'),
        'cancel_at_period_end': subscription_data.get('cancel_at_period_end', False),
        'ended_at': subscription_data.get('ended_at'),
        'status': subscription_data.get('status'),
        'metadata': subscription_data.get('metadata', {}),
        'cancellation_source': subscription_data.get('metadata', {}).get('cancellation_source', 'unknown'),
        'cancellation_feedback': subscription_data.get('metadata', {}).get('cancellation_feedback'),
        'cancellation_date': datetime.utcnow()
    }
```

#### Step 3: Pre-Cancellation State Capture
```python
def _capture_pre_cancellation_state(self, subscription: Subscription) -> Dict[str, Any]:
    """Capture subscription state before cancellation"""
    return {
        'status': subscription.status,
        'amount': subscription.amount,
        'billing_cycle': subscription.billing_cycle,
        'pricing_tier_id': subscription.pricing_tier_id,
        'trial_start': subscription.trial_start,
        'trial_end': subscription.trial_end,
        'current_period_start': subscription.current_period_start,
        'current_period_end': subscription.current_period_end,
        'quantity': subscription.quantity,
        'collection_method': subscription.collection_method,
        'default_payment_method': subscription.default_payment_method,
        'metadata': subscription.metadata.copy() if subscription.metadata else {},
        'created_at': subscription.created_at,
        'total_billing_cycles': self._calculate_total_billing_cycles(subscription),
        'total_amount_paid': self._calculate_total_amount_paid(subscription)
    }
```

#### Step 4: Subscription Cancellation Update
```python
def _update_subscription_for_cancellation(self, subscription: Subscription, cancellation_details: Dict[str, Any], changes: List[str]) -> None:
    """Update subscription for cancellation"""
    old_status = subscription.status
    
    # Update status
    subscription.status = 'canceled'
    if old_status != subscription.status:
        changes.append(f"Status changed: {old_status} → {subscription.status}")
    
    # Update cancellation timestamp
    if cancellation_details.get('canceled_at'):
        subscription.canceled_at = datetime.fromtimestamp(cancellation_details['canceled_at'])
    else:
        subscription.canceled_at = datetime.utcnow()
    
    changes.append(f"Canceled at: {subscription.canceled_at}")
    
    # Update cancellation settings
    subscription.cancel_at_period_end = cancellation_details.get('cancel_at_period_end', False)
    
    # Update metadata with cancellation information
    if not subscription.metadata:
        subscription.metadata = {}
    
    subscription.metadata.update({
        'cancellation_reason': cancellation_details.get('cancellation_reason'),
        'cancellation_source': cancellation_details.get('cancellation_source'),
        'cancellation_feedback': cancellation_details.get('cancellation_feedback'),
        'cancellation_date': cancellation_details.get('cancellation_date').isoformat(),
        'canceled_at_period_end': cancellation_details.get('cancel_at_period_end', False)
    })
```

#### Step 5: Feature Deactivation
```python
def _handle_feature_deactivation(self, subscription: Subscription, pre_cancellation_state: Dict[str, Any]) -> List[str]:
    """Handle feature deactivation for canceled subscription"""
    changes = []
    
    # Deactivate features based on pricing tier
    if subscription.pricing_tier_id:
        pricing_tier = self.db.query(PricingTier).filter(
            PricingTier.id == subscription.pricing_tier_id
        ).first()
        
        if pricing_tier:
            features = pricing_tier.features or []
            changes.append(f"Features deactivated: {', '.join(features)}")
            # self.feature_service.deactivate_features(subscription.customer_id, features)
    
    # Handle immediate vs end-of-period cancellation
    if subscription.cancel_at_period_end:
        changes.append("Features will be deactivated at period end")
    else:
        changes.append("Features immediately deactivated")
    
    # Handle trial-specific cleanup
    if pre_cancellation_state.get('trial_end'):
        changes.append("Trial period ended with cancellation")
    
    return changes
```

#### Step 6: Customer Status Update
```python
def _update_customer_for_cancellation(self, subscription: Subscription, pre_cancellation_state: Dict[str, Any]) -> List[str]:
    """Update customer for subscription cancellation"""
    changes = []
    customer = self.db.query(Customer).filter(Customer.id == subscription.customer_id).first()
    if not customer:
        return changes
    
    old_status = customer.subscription_status
    
    # Update customer subscription status
    customer.subscription_status = 'canceled'
    customer.has_active_subscription = False
    
    if old_status != customer.subscription_status:
        changes.append(f"Customer subscription status updated: {old_status} → {customer.subscription_status}")
    
    # Update customer metadata
    if not customer.metadata:
        customer.metadata = {}
    
    customer.metadata.update({
        'subscription_canceled_at': datetime.utcnow().isoformat(),
        'last_subscription_status': 'canceled',
        'last_subscription_amount': pre_cancellation_state.get('amount', 0),
        'last_billing_cycle': pre_cancellation_state.get('billing_cycle'),
        'total_billing_cycles': pre_cancellation_state.get('total_billing_cycles', 0),
        'total_amount_paid': pre_cancellation_state.get('total_amount_paid', 0.0),
        'cancellation_reason': subscription.metadata.get('cancellation_reason'),
        'cancellation_source': subscription.metadata.get('cancellation_source')
    })
    
    changes.append("Customer subscription data updated")
    
    return changes
```

#### Step 7: Final Billing History
```python
def _create_final_billing_history(self, subscription: Subscription, cancellation_details: Dict[str, Any]) -> Optional[BillingHistory]:
    """Create final billing history record for cancellation"""
    billing_history = BillingHistory(
        customer_id=subscription.customer_id,
        subscription_id=subscription.id,
        stripe_invoice_id=None,
        amount=subscription.amount,
        currency='usd',
        status='cancelled',
        description=f"Subscription canceled: {subscription.stripe_subscription_id}",
        billing_date=datetime.utcnow(),
        due_date=subscription.current_period_end,
        metadata={
            'subscription_cancellation': True,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'cancellation_reason': cancellation_details.get('cancellation_reason'),
            'cancellation_source': cancellation_details.get('cancellation_source'),
            'canceled_at_period_end': cancellation_details.get('cancel_at_period_end', False),
            'cancellation_date': cancellation_details.get('cancellation_date').isoformat()
        }
    )
    
    return billing_history
```

#### Step 8: Data Retention and Cleanup
```python
def _handle_data_retention_and_cleanup(self, subscription: Subscription, cancellation_details: Dict[str, Any]) -> List[str]:
    """Handle data retention and cleanup for canceled subscription"""
    changes = []
    
    # Determine retention period based on cancellation reason
    retention_period = self._determine_retention_period(cancellation_details)
    
    # Set data retention flags
    if not subscription.metadata:
        subscription.metadata = {}
    
    subscription.metadata.update({
        'data_retention_until': (datetime.utcnow() + timedelta(days=retention_period)).isoformat(),
        'data_retention_period_days': retention_period,
        'data_cleanup_scheduled': True
    })
    
    changes.append(f"Data retention set for {retention_period} days")
    
    # Schedule cleanup tasks
    # self.cleanup_service.schedule_subscription_cleanup(subscription.id, retention_period)
    
    # Handle immediate cleanup for certain cancellation reasons
    if cancellation_details.get('cancellation_reason') in ['fraudulent', 'duplicate']:
        changes.append("Immediate data cleanup scheduled (fraudulent/duplicate)")
        # self.cleanup_service.immediate_cleanup(subscription.id)
    
    return changes
```

#### Step 9: Cancellation Notifications
```python
def _send_cancellation_notifications(self, subscription: Subscription, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> int:
    """Send comprehensive cancellation notifications"""
    notifications_sent = 0
    
    # Send cancellation confirmation
    self.notification_service.send_subscription_cancellation(
        subscription.customer_id, subscription.id
    )
    notifications_sent += 1
    
    # Send cancellation reason specific notification
    reason = cancellation_details.get('cancellation_reason')
    if reason == 'requested_by_customer':
        self.notification_service.send_customer_requested_cancellation_notification(
            subscription.customer_id, subscription.id, cancellation_details
        )
        notifications_sent += 1
    
    # Send feedback request if no feedback provided
    if not cancellation_details.get('cancellation_feedback'):
        self.notification_service.send_cancellation_feedback_request(
            subscription.customer_id, subscription.id
        )
        notifications_sent += 1
    
    # Send reactivation offer if appropriate
    if self._should_send_reactivation_offer(cancellation_details, pre_cancellation_state):
        self.notification_service.send_reactivation_offer(
            subscription.customer_id, subscription.id, pre_cancellation_state
        )
        notifications_sent += 1
    
    # Send data retention notification
    retention_period = self._determine_retention_period(cancellation_details)
    self.notification_service.send_data_retention_notification(
        subscription.customer_id, subscription.id, retention_period
    )
    notifications_sent += 1
    
    return notifications_sent
```

#### Step 10: Cancellation Analytics
```python
def _track_cancellation_analytics(self, subscription: Subscription, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> None:
    """Track comprehensive analytics for subscription cancellation"""
    # Track basic cancellation
    self.analytics_service.track_subscription_canceled(subscription.customer_id, subscription.id)
    
    # Track cancellation reason
    reason = cancellation_details.get('cancellation_reason', 'unknown')
    self.analytics_service.track_cancellation_reason(subscription.customer_id, subscription.id, reason)
    
    # Track cancellation source
    source = cancellation_details.get('cancellation_source', 'unknown')
    self.analytics_service.track_cancellation_source(subscription.customer_id, subscription.id, source)
    
    # Track subscription lifetime metrics
    total_cycles = pre_cancellation_state.get('total_billing_cycles', 0)
    total_amount = pre_cancellation_state.get('total_amount_paid', 0.0)
    subscription_duration = (subscription.canceled_at - subscription.created_at).days if subscription.canceled_at and subscription.created_at else 0
    
    self.analytics_service.track_subscription_lifetime_metrics(
        subscription.customer_id, subscription.id, total_cycles, total_amount, subscription_duration
    )
    
    # Track churn metrics
    self.analytics_service.track_churn_metrics(
        subscription.customer_id, subscription.id, reason, source, total_cycles, total_amount
    )
    
    # Track reactivation potential
    if self._should_send_reactivation_offer(cancellation_details, pre_cancellation_state):
        self.analytics_service.track_reactivation_potential(
            subscription.customer_id, subscription.id, reason, total_cycles, total_amount
        )
```

#### Step 11: Cancellation Audit Logging
```python
def _log_cancellation_audit(self, subscription: Subscription, cancellation_details: Dict[str, Any], pre_cancellation_state: Dict[str, Any]) -> None:
    """Log comprehensive audit trail for subscription cancellation"""
    audit_log = AuditLog(
        event_type=AuditEventType.SUBSCRIPTION_CANCELED,
        event_description=f"Subscription canceled: {subscription.stripe_subscription_id}",
        severity=AuditSeverity.WARNING,
        metadata={
            'subscription_id': subscription.id,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'customer_id': subscription.customer_id,
            'cancellation_details': cancellation_details,
            'pre_cancellation_state': pre_cancellation_state,
            'cancellation_reason': cancellation_details.get('cancellation_reason'),
            'cancellation_source': cancellation_details.get('cancellation_source'),
            'cancellation_feedback': cancellation_details.get('cancellation_feedback'),
            'total_billing_cycles': pre_cancellation_state.get('total_billing_cycles', 0),
            'total_amount_paid': pre_cancellation_state.get('total_amount_paid', 0.0),
            'subscription_duration_days': (subscription.canceled_at - subscription.created_at).days if subscription.canceled_at and subscription.created_at else 0,
            'canceled_at_period_end': cancellation_details.get('cancel_at_period_end', False),
            'data_retention_period_days': self._determine_retention_period(cancellation_details),
            'webhook_event_id': event.event_id if hasattr(event, 'event_id') else None,
            'canceled_at': datetime.utcnow().isoformat()
        }
    )
    
    self.db.add(audit_log)
```

## Data Retention Policies

### Retention Periods by Cancellation Reason

| Cancellation Reason | Retention Period | Rationale |
|-------------------|------------------|-----------|
| `fraudulent` | 30 days | Short retention for security |
| `duplicate` | 7 days | Very short for duplicates |
| `requested_by_customer` | 365 days | Long retention for customer requests |
| `payment_failure` | 90 days | Medium retention for payment issues |
| `expired` | 180 days | Medium retention for expired |
| `unknown` | 90 days | Default retention |

## Reactivation Offer Logic

### Conditions for Reactivation Offers

1. **Customer-requested cancellations** with 3+ billing cycles
2. **Payment failure cancellations** (all)
3. **Excluded reasons**: `fraudulent`, `duplicate`

### Reactivation Offer Types

1. **Discount offers** for returning customers
2. **Feature upgrades** to entice reactivation
3. **Extended trial periods** for re-engagement
4. **Personalized messaging** based on cancellation reason

## Error Handling

### Comprehensive Error Handling
```python
try:
    # All subscription update/cancellation logic
    # ...
except Exception as e:
    logger.error(f"Error handling subscription update/cancellation: {e}")
    self.db.rollback()  # Rollback all changes on error
    return WebhookProcessingResult(
        success=False,
        error=str(e)
    )
```

### Validation Errors
- **Subscription not found**: Returns error if subscription doesn't exist
- **Invalid subscription data**: Returns error if required fields are missing
- **Database errors**: Rolls back changes and returns error

## Performance Optimizations

### Database Operations
- Uses `db.flush()` instead of `db.commit()` for intermediate operations
- Batches database operations where possible
- Uses transactions for data consistency

### Logging and Monitoring
- Comprehensive logging at each step
- Performance timing for each operation
- Error tracking and reporting

## Testing

### Test Scenarios

#### Subscription Updates
1. **Subscription upgrade** - Tier change with amount increase
2. **Subscription downgrade** - Tier change with amount decrease
3. **Billing cycle change** - Monthly to yearly conversion
4. **Cancellation scheduled** - Cancel at period end
5. **Trial period changes** - Trial start/end modifications
6. **Payment method updates** - Default payment method changes

#### Subscription Cancellations
1. **Customer-requested cancellation** - With feedback
2. **Payment failure cancellation** - Multiple failed attempts
3. **Fraudulent cancellation** - Immediate cleanup required
4. **Duplicate cancellation** - Short retention period
5. **Expired cancellation** - Natural expiration

### Example Test Events

#### Subscription Upgrade Event
```json
{
  "id": "evt_subscription_1234567890",
  "object": "event",
  "type": "customer.subscription.updated",
  "created": 1640995200,
  "livemode": false,
  "api_version": "2020-08-27",
  "data": {
    "object": {
      "id": "sub_upgrade_001",
      "object": "subscription",
      "customer": "cus_update_001",
      "status": "active",
      "current_period_start": 1640995200,
      "current_period_end": 1643587200,
      "cancel_at_period_end": false,
      "collection_method": "charge_automatically",
      "items": {
        "data": [{
          "id": "si_upgrade_001",
          "object": "subscription_item",
          "quantity": 1,
          "price": {
            "id": "price_pro_monthly",
            "object": "price",
            "unit_amount": 2500,
            "currency": "usd",
            "recurring": {
              "interval": "month",
              "interval_count": 1
            }
          }
        }]
      },
      "metadata": {
        "source": "webhook_test",
        "test_type": "subscription_upgrade",
        "upgrade_reason": "customer_requested"
      }
    }
  }
}
```

#### Customer-Requested Cancellation Event
```json
{
  "id": "evt_subscription_1234567890",
  "object": "event",
  "type": "customer.subscription.deleted",
  "created": 1640995200,
  "livemode": false,
  "api_version": "2020-08-27",
  "data": {
    "object": {
      "id": "sub_customer_cancel_001",
      "object": "subscription",
      "customer": "cus_cancel_001",
      "status": "canceled",
      "canceled_at": 1640995200,
      "cancel_at_period_end": false,
      "ended_at": 1640995200,
      "current_period_start": 1640995200,
      "current_period_end": 1643587200,
      "collection_method": "charge_automatically",
      "items": {
        "data": [{
          "id": "si_customer_cancel_001",
          "object": "subscription_item",
          "quantity": 1,
          "price": {
            "id": "price_pro_monthly",
            "object": "price",
            "unit_amount": 2500,
            "currency": "usd",
            "recurring": {
              "interval": "month",
              "interval_count": 1
            }
          }
        }]
      },
      "metadata": {
        "source": "webhook_test",
        "test_type": "customer_requested_cancellation",
        "cancellation_reason": "requested_by_customer",
        "cancellation_source": "customer_portal",
        "cancellation_feedback": "Switching to competitor"
      }
    }
  }
}
```

## Integration Points

### Services Integration
- **NotificationService**: Sends various update and cancellation notifications
- **AnalyticsService**: Tracks comprehensive metrics and analytics
- **FeatureService**: Manages feature activation/deactivation (to be implemented)
- **CleanupService**: Handles data retention and cleanup (to be implemented)

### Database Models
- **Customer**: Updated with subscription status and metadata
- **Subscription**: Updated with comprehensive changes or marked as canceled
- **PricingTier**: Referenced for feature management
- **BillingHistory**: Created for significant changes and cancellations
- **AuditLog**: Comprehensive audit trail logged

## Monitoring and Alerting

### Key Metrics
- **Success Rate**: Percentage of successful updates/cancellations
- **Processing Time**: Time to complete operations
- **Error Rate**: Percentage of failed operations
- **Notification Delivery**: Success rate of notification sending

### Alerts
- **High Error Rate**: Alert when error rates exceed threshold
- **Slow Processing**: Alert when processing time exceeds 5 seconds
- **Notification Failures**: Alert when notification delivery fails
- **Database Errors**: Alert on database connection or constraint issues

## Best Practices

### Development
1. **Always validate input data** before processing
2. **Use transactions** for data consistency
3. **Log comprehensive audit trails** for debugging
4. **Handle errors gracefully** with proper rollback
5. **Test all scenarios** including error cases

### Operations
1. **Monitor processing times** and success rates
2. **Set up alerts** for critical failures
3. **Review audit logs** regularly
4. **Monitor database performance** during high volume
5. **Test webhook processing** in staging environment

### Security
1. **Validate webhook signatures** before processing
2. **Sanitize all input data** to prevent injection attacks
3. **Log security-relevant events** for audit purposes
4. **Use parameterized queries** to prevent SQL injection
5. **Implement rate limiting** to prevent abuse

## Future Enhancements

### Planned Features
1. **Multi-currency support** - Handle different currencies
2. **Advanced feature management** - Dynamic feature activation
3. **Subscription reactivation** - Handle reactivation requests
4. **Promotional codes** - Apply discounts and coupons
5. **Tax calculation** - Automatic tax handling

### Performance Improvements
1. **Async processing** - Process non-critical operations asynchronously
2. **Caching** - Cache frequently accessed data
3. **Database optimization** - Optimize queries and indexes
4. **Batch processing** - Process multiple subscriptions in batches

## Conclusion

The enhanced subscription update and cancellation handlers provide robust, scalable, and comprehensive solutions for processing subscription changes and cancellations from Stripe. They ensure data integrity, provide excellent user experience through notifications, track analytics for business insights, and maintain detailed audit trails for compliance and debugging.

The handlers are designed to be maintainable, testable, and extensible, making it easy to add new features and handle different subscription scenarios as the business grows. 