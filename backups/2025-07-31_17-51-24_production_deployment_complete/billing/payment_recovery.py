"""
Payment Recovery System for MINGUS
==================================

Comprehensive payment failure and recovery system providing:
- Automatic payment recovery with intelligent retry strategies
- Dunning management with escalating communication
- Revenue optimization and retention strategies
- Payment method updates and validation
- Grace period management
- Recovery analytics and reporting
- Integration with Stripe and other payment processors

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import stripe

from ..config.base import Config
from ..models.subscription import Customer, Subscription, BillingHistory
from ..models.payment_recovery import PaymentRecoveryRecord, DunningEvent, RecoveryStrategy
from ..services.notification_service import NotificationService
from ..analytics.event_tracker import EventTracker

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"


class DunningStage(Enum):
    """Dunning stage enumeration"""
    SOFT_FAILURE = "soft_failure"
    HARD_FAILURE = "hard_failure"
    DUNNING_1 = "dunning_1"
    DUNNING_2 = "dunning_2"
    DUNNING_3 = "dunning_3"
    DUNNING_4 = "dunning_4"
    DUNNING_5 = "dunning_5"
    FINAL_NOTICE = "final_notice"
    CANCELLATION = "cancellation"
    RECOVERY = "recovery"


class RecoveryStrategy(Enum):
    """Recovery strategy enumeration"""
    AUTOMATIC_RETRY = "automatic_retry"
    PAYMENT_METHOD_UPDATE = "payment_method_update"
    GRACE_PERIOD = "grace_period"
    PARTIAL_PAYMENT = "partial_payment"
    PAYMENT_PLAN = "payment_plan"
    MANUAL_INTERVENTION = "manual_intervention"
    CANCELLATION = "cancellation"


@dataclass
class PaymentFailure:
    """Payment failure data structure"""
    failure_id: str
    customer_id: str
    subscription_id: str
    invoice_id: str
    payment_intent_id: str
    failure_reason: str
    failure_code: str
    amount: float
    currency: str
    failed_at: datetime
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


@dataclass
class RecoveryAction:
    """Recovery action data structure"""
    action_id: str
    failure_id: str
    strategy: RecoveryStrategy
    action_type: str
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    success: Optional[bool] = None
    result: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


@dataclass
class DunningSchedule:
    """Dunning schedule data structure"""
    stage: DunningStage
    delay_days: int
    notification_type: str
    retry_attempt: bool
    amount: Optional[float] = None
    payment_method_update: bool = False
    grace_period_days: Optional[int] = None


class PaymentRecoverySystem:
    """Comprehensive payment recovery system"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Initialize Stripe
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
        
        # Payment recovery configuration
        self.recovery_config = {
            'max_retry_attempts': 5,
            'retry_intervals_days': [1, 3, 7, 14, 30],  # Standard retry schedule
            'smart_retry_intervals_days': [1, 3, 7],     # Smart retry schedule for immediate retry failures
            'grace_period_days': 7,
            'partial_payment_threshold': 0.5,  # 50% of original amount
            'recovery_timeout_days': 90,
            'auto_cancellation_days': 30,
            'high_value_threshold': 100.0,  # USD
            'enterprise_customer_grace_period': 14,
            'notification_channels': ['email', 'sms', 'in_app'],
            'payment_method_update_prompts': {
                'enabled': True,
                'prompt_days': [1, 3, 7],  # Days to prompt for payment method update
                'max_prompts': 3,
                'prompt_channels': ['email', 'sms', 'in_app', 'push']
            },
            'alternative_payment_methods': {
                'enabled': True,
                'suggestions': [
                    'credit_card',
                    'debit_card', 
                    'bank_transfer',
                    'digital_wallet',
                    'crypto_payment',
                    'gift_card',
                    'installment_plan'
                ],
                'suggestion_days': [1, 3, 5, 7],  # Days to suggest alternative methods
                'max_suggestions': 5
            },
            'grace_period_access': {
                'enabled': True,
                'duration_days': 7,
                'feature_restrictions': ['premium_features', 'advanced_analytics', 'priority_support'],
                'access_level': 'limited',
                'notification_frequency': 'daily',
                'auto_suspension': True
            },
            'voluntary_update_reminders': {
                'enabled': True,
                'reminder_days': [1, 3, 5, 6],  # Days before suspension to send reminders
                'final_warning_day': 7,  # Day before suspension
                'max_reminders': 4,
                'reminder_channels': ['email', 'sms', 'in_app', 'push'],
                'escalation_levels': {
                    1: 'gentle_reminder',
                    3: 'friendly_reminder', 
                    5: 'urgent_reminder',
                    6: 'final_warning',
                    7: 'suspension_notice'
                },
                'reminder_templates': {
                    'gentle_reminder': 'Your payment method needs attention',
                    'friendly_reminder': 'Update your payment to continue service',
                    'urgent_reminder': 'Action required: Update payment method',
                    'final_warning': 'Final notice: Update payment or lose access',
                    'suspension_notice': 'Account suspended due to payment issue'
                }
            },
            'dunning_email_sequence': {
                'enabled': True,
                'stages': {
                    'dunning_1': {
                        'delay_days': 1,
                        'subject': 'Payment Issue - Action Required',
                        'template': 'dunning_1_gentle_reminder',
                        'urgency': 'low',
                        'retry_attempt': True,
                        'amount_adjustment': False,
                        'payment_method_update': False,
                        'grace_period_offer': False
                    },
                    'dunning_2': {
                        'delay_days': 3,
                        'subject': 'Payment Overdue - Update Required',
                        'template': 'dunning_2_friendly_reminder',
                        'urgency': 'medium',
                        'retry_attempt': True,
                        'amount_adjustment': True,
                        'payment_method_update': True,
                        'grace_period_offer': False
                    },
                    'dunning_3': {
                        'delay_days': 7,
                        'subject': 'Urgent: Payment Action Required',
                        'template': 'dunning_3_urgent_reminder',
                        'urgency': 'high',
                        'retry_attempt': True,
                        'amount_adjustment': True,
                        'payment_method_update': True,
                        'grace_period_offer': True
                    },
                    'dunning_4': {
                        'delay_days': 14,
                        'subject': 'Final Notice: Payment Required',
                        'template': 'dunning_4_final_warning',
                        'urgency': 'critical',
                        'retry_attempt': True,
                        'amount_adjustment': True,
                        'payment_method_update': True,
                        'grace_period_offer': True,
                        'partial_payment_offer': True
                    },
                    'dunning_5': {
                        'delay_days': 21,
                        'subject': 'Account Suspension Imminent',
                        'template': 'dunning_5_suspension_warning',
                        'urgency': 'critical',
                        'retry_attempt': False,
                        'amount_adjustment': False,
                        'payment_method_update': True,
                        'grace_period_offer': False,
                        'manual_intervention': True
                    },
                    'final_notice': {
                        'delay_days': 28,
                        'subject': 'Account Suspended - Reactivation Required',
                        'template': 'dunning_final_suspension',
                        'urgency': 'critical',
                        'retry_attempt': False,
                        'amount_adjustment': False,
                        'payment_method_update': True,
                        'grace_period_offer': False,
                        'manual_intervention': True,
                        'reactivation_required': True
                    }
                },
                'email_templates': {
                    'dunning_1_gentle_reminder': {
                        'subject': 'Payment Issue - Action Required',
                        'greeting': 'Hi {customer_name},',
                        'body': 'We noticed your recent payment of ${amount} {currency} couldn\'t be processed. This is just a friendly reminder to update your payment method to avoid any service interruption.',
                        'call_to_action': 'Update Payment Method',
                        'footer': 'If you have any questions, please don\'t hesitate to contact our support team.',
                        'urgency_level': 'low'
                    },
                    'dunning_2_friendly_reminder': {
                        'subject': 'Payment Overdue - Update Required',
                        'greeting': 'Hello {customer_name},',
                        'body': 'Your payment method needs attention. We\'d hate to see your service interrupted, so please take a moment to update your payment details. We\'re also offering a reduced payment option to help.',
                        'call_to_action': 'Update Payment Method',
                        'footer': 'Need help? Our support team is here to assist you.',
                        'urgency_level': 'medium'
                    },
                    'dunning_3_urgent_reminder': {
                        'subject': 'Urgent: Payment Action Required',
                        'greeting': 'Hi {customer_name},',
                        'body': 'Urgent action required! Your payment method needs to be updated within 7 days to prevent service suspension. We\'re offering a grace period and reduced payment options to help resolve this quickly.',
                        'call_to_action': 'Resolve Payment Issue',
                        'footer': 'Contact support immediately if you need assistance.',
                        'urgency_level': 'high'
                    },
                    'dunning_4_final_warning': {
                        'subject': 'Final Notice: Payment Required',
                        'greeting': 'Dear {customer_name},',
                        'body': 'This is your final warning. Your account will be suspended within 7 days unless you update your payment method immediately. We\'re offering partial payment options and extended grace periods to help.',
                        'call_to_action': 'Update Payment Now',
                        'footer': 'This is your last chance to avoid account suspension.',
                        'urgency_level': 'critical'
                    },
                    'dunning_5_suspension_warning': {
                        'subject': 'Account Suspension Imminent',
                        'greeting': 'Dear {customer_name},',
                        'body': 'Your account is scheduled for suspension due to payment issues. To prevent this, please contact our support team immediately to discuss payment options and account reactivation.',
                        'call_to_action': 'Contact Support',
                        'footer': 'Manual intervention required to prevent suspension.',
                        'urgency_level': 'critical'
                    },
                    'dunning_final_suspension': {
                        'subject': 'Account Suspended - Reactivation Required',
                        'greeting': 'Dear {customer_name},',
                        'body': 'Your account has been suspended due to unresolved payment issues. To reactivate your account, please contact our support team to discuss payment options and account restoration.',
                        'call_to_action': 'Reactivate Account',
                        'footer': 'Account reactivation requires manual intervention.',
                        'urgency_level': 'critical'
                    }
                },
                'retry_config': {
                    'enabled': True,
                    'max_retries_per_stage': 2,
                    'retry_delay_hours': 24,
                    'amount_reduction_percentage': 10,
                    'retry_conditions': ['insufficient_funds', 'processing_error', 'network_error']
                },
                'grace_period_config': {
                    'enabled': True,
                    'grace_period_days': 7,
                    'grace_period_offers': [3, 7, 14],
                    'grace_period_message': 'We\'re offering you a {days}-day grace period to resolve this payment issue.'
                },
                'partial_payment_config': {
                    'enabled': True,
                    'minimum_percentage': 50,
                    'partial_payment_offers': [50, 75, 90],
                    'partial_payment_message': 'We\'re offering partial payment options starting at {percentage}% of your balance.'
                },
                'sms_notifications': {
                    'enabled': True,
                    'critical_stages': ['dunning_3', 'dunning_4', 'dunning_5', 'final_notice'],
                    'sms_templates': {
                        'dunning_3_urgent': {
                            'message': 'URGENT: Your MINGUS payment of ${amount} failed. Update payment method within 7 days to avoid suspension. Reply HELP for support.',
                            'priority': 'high',
                            'retry_count': 3
                        },
                        'dunning_4_critical': {
                            'message': 'CRITICAL: Your MINGUS account will be suspended in 7 days due to payment failure. Call {support_phone} immediately to resolve.',
                            'priority': 'urgent',
                            'retry_count': 5
                        },
                        'dunning_5_suspension': {
                            'message': 'FINAL WARNING: MINGUS account suspension scheduled. Contact support immediately at {support_phone} to prevent loss of access.',
                            'priority': 'urgent',
                            'retry_count': 5
                        },
                        'final_suspension': {
                            'message': 'ALERT: Your MINGUS account has been suspended. Call {support_phone} to reactivate your account and restore access.',
                            'priority': 'urgent',
                            'retry_count': 3
                        }
                    },
                    'support_phone': '+1-800-MINGUS-1',
                    'opt_out_keywords': ['STOP', 'CANCEL', 'UNSUBSCRIBE'],
                    'help_keywords': ['HELP', 'SUPPORT', 'INFO']
                },
                'in_app_notifications': {
                    'enabled': True,
                    'notification_types': {
                        'payment_failure': {
                            'title': 'Payment Issue Detected',
                            'message': 'We couldn\'t process your recent payment of ${amount}. Please update your payment method to continue using MINGUS.',
                            'severity': 'warning',
                            'action_required': True,
                            'action_text': 'Update Payment Method',
                            'action_url': '/billing/payment-method',
                            'dismissible': False,
                            'persistent': True
                        },
                        'grace_period_active': {
                            'title': 'Grace Period Active',
                            'message': 'Your account is in a 7-day grace period. Update your payment method to avoid service interruption.',
                            'severity': 'warning',
                            'action_required': True,
                            'action_text': 'Resolve Payment Issue',
                            'action_url': '/billing/resolve-payment',
                            'dismissible': False,
                            'persistent': True
                        },
                        'suspension_warning': {
                            'title': 'Account Suspension Warning',
                            'message': 'Your account will be suspended in {days_remaining} days due to payment issues. Take action now to prevent service interruption.',
                            'severity': 'critical',
                            'action_required': True,
                            'action_text': 'Contact Support',
                            'action_url': '/support/contact',
                            'dismissible': False,
                            'persistent': True
                        },
                        'account_suspended': {
                            'title': 'Account Suspended',
                            'message': 'Your account has been suspended due to payment issues. Contact support to reactivate your account.',
                            'severity': 'critical',
                            'action_required': True,
                            'action_text': 'Reactivate Account',
                            'action_url': '/support/reactivate',
                            'dismissible': False,
                            'persistent': True
                        }
                    },
                    'billing_alerts': {
                        'enabled': True,
                        'alert_types': {
                            'payment_failed': {
                                'title': 'Payment Failed',
                                'message': 'Your payment of ${amount} {currency} failed. Please update your payment method.',
                                'icon': 'payment_error',
                                'color': 'red',
                                'sound': 'alert',
                                'vibration': True
                            },
                            'grace_period_started': {
                                'title': 'Grace Period Started',
                                'message': 'Your account is now in a grace period. Update payment method to continue.',
                                'icon': 'warning',
                                'color': 'orange',
                                'sound': 'notification',
                                'vibration': False
                            },
                            'suspension_imminent': {
                                'title': 'Suspension Imminent',
                                'message': 'Your account will be suspended in {days_remaining} days.',
                                'icon': 'critical',
                                'color': 'red',
                                'sound': 'alert',
                                'vibration': True
                            },
                            'account_suspended': {
                                'title': 'Account Suspended',
                                'message': 'Your account has been suspended due to payment issues.',
                                'icon': 'blocked',
                                'color': 'red',
                                'sound': 'alert',
                                'vibration': True
                            }
                        },
                                        'notification_frequency': {
                    'payment_failed': 'immediate',
                    'grace_period_started': 'daily',
                    'suspension_imminent': 'daily',
                    'account_suspended': 'once'
                }
            },
            'personalized_messaging': {
                'enabled': True,
                'user_segments': {
                    'high_value': {
                        'segment_criteria': {
                            'monthly_revenue': {'min': 500, 'max': None},
                            'subscription_length_months': {'min': 12, 'max': None},
                            'feature_usage': {'min': 80, 'max': 100},
                            'support_tickets': {'max': 2}
                        },
                        'messaging_tone': 'premium',
                        'priority_level': 'high',
                        'custom_offers': True,
                        'dedicated_support': True,
                        'escalation_threshold': 2
                    },
                    'mid_value': {
                        'segment_criteria': {
                            'monthly_revenue': {'min': 100, 'max': 499},
                            'subscription_length_months': {'min': 6, 'max': 11},
                            'feature_usage': {'min': 50, 'max': 79},
                            'support_tickets': {'max': 5}
                        },
                        'messaging_tone': 'professional',
                        'priority_level': 'medium',
                        'custom_offers': True,
                        'dedicated_support': False,
                        'escalation_threshold': 3
                    },
                    'standard': {
                        'segment_criteria': {
                            'monthly_revenue': {'min': 0, 'max': 99},
                            'subscription_length_months': {'min': 0, 'max': 5},
                            'feature_usage': {'min': 0, 'max': 49},
                            'support_tickets': {'max': 10}
                        },
                        'messaging_tone': 'friendly',
                        'priority_level': 'standard',
                        'custom_offers': False,
                        'dedicated_support': False,
                        'escalation_threshold': 4
                    },
                    'at_risk': {
                        'segment_criteria': {
                            'payment_failures_last_3_months': {'min': 2, 'max': None},
                            'subscription_length_months': {'min': 0, 'max': 2},
                            'feature_usage': {'min': 0, 'max': 20},
                            'support_tickets': {'min': 3, 'max': None}
                        },
                        'messaging_tone': 'supportive',
                        'priority_level': 'high',
                        'custom_offers': True,
                        'dedicated_support': True,
                        'escalation_threshold': 1
                    }
                },
                'messaging_templates': {
                    'premium': {
                        'dunning_1': {
                            'subject': 'Important: Payment Update Required for Your Premium Account',
                            'message': 'Dear {customer_name}, we noticed a payment issue with your premium MINGUS account. As a valued customer, we want to ensure uninterrupted access to your advanced features. Please update your payment method to continue enjoying premium benefits.',
                            'cta_text': 'Update Payment Method',
                            'cta_url': '/billing/premium-update',
                            'personal_touch': True
                        },
                        'dunning_3': {
                            'subject': 'Urgent: Your Premium Account Needs Attention',
                            'message': 'Dear {customer_name}, your premium MINGUS account requires immediate attention. We\'ve prepared a special retention offer to help resolve this quickly. Contact our dedicated support team for personalized assistance.',
                            'cta_text': 'Contact Dedicated Support',
                            'cta_url': '/support/premium',
                            'personal_touch': True,
                            'retention_offer': True
                        }
                    },
                    'professional': {
                        'dunning_1': {
                            'subject': 'Payment Update Required - MINGUS Account',
                            'message': 'Hi {customer_name}, we couldn\'t process your recent payment. Please update your payment method to continue using MINGUS without interruption.',
                            'cta_text': 'Update Payment Method',
                            'cta_url': '/billing/update',
                            'personal_touch': False
                        },
                        'dunning_3': {
                            'subject': 'Action Required: Payment Issue Resolution',
                            'message': 'Hi {customer_name}, your MINGUS account needs attention. We\'re offering a special discount to help resolve this payment issue quickly.',
                            'cta_text': 'Resolve Payment Issue',
                            'cta_url': '/billing/resolve',
                            'personal_touch': False,
                            'retention_offer': True
                        }
                    },
                    'friendly': {
                        'dunning_1': {
                            'subject': 'Quick Payment Update Needed',
                            'message': 'Hey {customer_name}! We had a small hiccup with your payment. No worries - just update your payment method and you\'ll be all set!',
                            'cta_text': 'Fix Payment',
                            'cta_url': '/billing/fix',
                            'personal_touch': False
                        },
                        'dunning_3': {
                            'subject': 'Let\'s Get This Sorted Out',
                            'message': 'Hey {customer_name}! We want to help you get back on track. We\'ve got a great offer to make this easy for you.',
                            'cta_text': 'Get Special Offer',
                            'cta_url': '/billing/offer',
                            'personal_touch': False,
                            'retention_offer': True
                        }
                    },
                    'supportive': {
                        'dunning_1': {
                            'subject': 'We\'re Here to Help - Payment Support',
                            'message': 'Hi {customer_name}, we noticed you might be having some trouble with payments. We\'re here to help! Let\'s work together to get this sorted.',
                            'cta_text': 'Get Help',
                            'cta_url': '/support/payment-help',
                            'personal_touch': True
                        },
                        'dunning_3': {
                            'subject': 'Special Support Offer - Let\'s Resolve This Together',
                            'message': 'Hi {customer_name}, we understand payment issues can be stressful. We\'ve prepared a special support package to help you get back on track.',
                            'cta_text': 'Get Support Package',
                            'cta_url': '/support/special-package',
                            'personal_touch': True,
                            'retention_offer': True
                        }
                    }
                }
            },
            'retention_offers': {
                'enabled': True,
                'offer_types': {
                    'discount_offers': {
                        'high_value': {
                            'dunning_1': {'discount_percent': 25, 'duration_months': 3},
                            'dunning_3': {'discount_percent': 50, 'duration_months': 6},
                            'dunning_5': {'discount_percent': 75, 'duration_months': 12}
                        },
                        'mid_value': {
                            'dunning_1': {'discount_percent': 20, 'duration_months': 2},
                            'dunning_3': {'discount_percent': 40, 'duration_months': 4},
                            'dunning_5': {'discount_percent': 60, 'duration_months': 6}
                        },
                        'standard': {
                            'dunning_1': {'discount_percent': 15, 'duration_months': 1},
                            'dunning_3': {'discount_percent': 30, 'duration_months': 2},
                            'dunning_5': {'discount_percent': 50, 'duration_months': 3}
                        },
                        'at_risk': {
                            'dunning_1': {'discount_percent': 30, 'duration_months': 3},
                            'dunning_3': {'discount_percent': 60, 'duration_months': 6},
                            'dunning_5': {'discount_percent': 80, 'duration_months': 12}
                        }
                    },
                    'payment_plans': {
                        'high_value': {
                            'dunning_3': {'installments': 3, 'interest_free': True},
                            'dunning_5': {'installments': 6, 'interest_free': True}
                        },
                        'mid_value': {
                            'dunning_3': {'installments': 2, 'interest_free': True},
                            'dunning_5': {'installments': 3, 'interest_free': True}
                        },
                        'standard': {
                            'dunning_3': {'installments': 2, 'interest_free': False},
                            'dunning_5': {'installments': 3, 'interest_free': False}
                        },
                        'at_risk': {
                            'dunning_1': {'installments': 3, 'interest_free': True},
                            'dunning_3': {'installments': 6, 'interest_free': True},
                            'dunning_5': {'installments': 12, 'interest_free': True}
                        }
                    },
                    'feature_upgrades': {
                        'high_value': {
                            'dunning_3': ['premium_support', 'advanced_analytics', 'priority_queue'],
                            'dunning_5': ['premium_support', 'advanced_analytics', 'priority_queue', 'custom_integration']
                        },
                        'mid_value': {
                            'dunning_3': ['priority_support', 'basic_analytics'],
                            'dunning_5': ['priority_support', 'basic_analytics', 'advanced_features']
                        },
                        'standard': {
                            'dunning_3': ['extended_support'],
                            'dunning_5': ['extended_support', 'basic_analytics']
                        },
                        'at_risk': {
                            'dunning_1': ['basic_support', 'tutorial_access'],
                            'dunning_3': ['priority_support', 'basic_analytics', 'training_sessions'],
                            'dunning_5': ['premium_support', 'advanced_analytics', 'custom_onboarding']
                        }
                    },
                    'grace_periods': {
                        'high_value': {
                            'dunning_1': {'days': 14, 'full_access': True},
                            'dunning_3': {'days': 21, 'full_access': True},
                            'dunning_5': {'days': 30, 'full_access': True}
                        },
                        'mid_value': {
                            'dunning_1': {'days': 10, 'full_access': True},
                            'dunning_3': {'days': 14, 'full_access': False},
                            'dunning_5': {'days': 21, 'full_access': False}
                        },
                        'standard': {
                            'dunning_1': {'days': 7, 'full_access': False},
                            'dunning_3': {'days': 10, 'full_access': False},
                            'dunning_5': {'days': 14, 'full_access': False}
                        },
                        'at_risk': {
                            'dunning_1': {'days': 21, 'full_access': True},
                            'dunning_3': {'days': 30, 'full_access': True},
                            'dunning_5': {'days': 45, 'full_access': True}
                        }
                    }
                },
                'offer_triggers': {
                    'payment_failure_count': {
                        'high_value': {'threshold': 1, 'escalation': True},
                        'mid_value': {'threshold': 2, 'escalation': True},
                        'standard': {'threshold': 3, 'escalation': False},
                        'at_risk': {'threshold': 1, 'escalation': True}
                    },
                    'subscription_age': {
                        'high_value': {'min_months': 0, 'priority': 'high'},
                        'mid_value': {'min_months': 1, 'priority': 'medium'},
                        'standard': {'min_months': 2, 'priority': 'low'},
                        'at_risk': {'min_months': 0, 'priority': 'high'}
                    },
                    'feature_usage': {
                        'high_value': {'min_percentage': 50, 'bonus_offer': True},
                        'mid_value': {'min_percentage': 30, 'bonus_offer': True},
                        'standard': {'min_percentage': 20, 'bonus_offer': False},
                        'at_risk': {'min_percentage': 10, 'bonus_offer': True}
                    }
                },
                                'offer_personalization': {
                    'customer_name': True,
                    'subscription_details': True,
                    'usage_statistics': True,
                    'previous_offers': True,
                    'support_history': True,
                    'preferred_contact_method': True
                }
            },
            'access_control': {
                'enabled': True,
                'grace_period': {
                    'enabled': True,
                    'duration_days': 7,
                    'full_access': True,
                    'features': {
                        'all_features': True,
                        'restricted_features': [],
                        'read_only_features': []
                    },
                    'notifications': {
                        'activation': True,
                        'daily_reminders': True,
                        'expiration_warning': True,
                        'expiration_warning_days': 2
                    },
                    'extensions': {
                        'enabled': True,
                        'max_extensions': 2,
                        'extension_days': 3,
                        'extension_criteria': {
                            'high_value_customer': True,
                            'active_usage': True,
                            'support_request': True
                        }
                    }
                },
                'limited_access_mode': {
                    'enabled': True,
                    'trigger_conditions': {
                        'grace_period_expired': True,
                        'multiple_payment_failures': True,
                        'manual_activation': True
                    },
                    'features': {
                        'read_only': [
                            'dashboard_view',
                            'reports_view',
                            'data_export',
                            'profile_management',
                            'support_access'
                        ],
                        'restricted': [
                            'new_analysis',
                            'data_import',
                            'api_access',
                            'team_management',
                            'billing_changes'
                        ],
                        'blocked': [
                            'premium_features',
                            'advanced_analytics',
                            'custom_integrations',
                            'priority_support'
                        ]
                    },
                    'data_access': {
                        'view_existing_data': True,
                        'export_data': True,
                        'download_reports': True,
                        'access_history': True
                    },
                    'notifications': {
                        'activation': True,
                        'feature_restrictions': True,
                        'upgrade_prompts': True
                    }
                },
                'data_export': {
                    'enabled': True,
                    'export_formats': ['csv', 'json', 'xlsx', 'pdf'],
                    'export_limits': {
                        'max_file_size_mb': 100,
                        'max_records_per_export': 10000,
                        'max_exports_per_day': 5,
                        'max_exports_total': 20
                    },
                    'export_features': {
                        'user_data': True,
                        'analytics_data': True,
                        'reports': True,
                        'settings': True,
                        'history': True
                    },
                    'export_scheduling': {
                        'scheduled_exports': True,
                        'auto_export_on_suspension': True,
                        'export_retention_days': 30
                    },
                    'notifications': {
                        'export_started': True,
                        'export_completed': True,
                        'export_failed': True,
                        'export_ready_for_download': True
                    }
                },
                'suspension': {
                    'enabled': True,
                    'trigger_conditions': {
                        'grace_period_expired': True,
                        'limited_access_expired': True,
                        'manual_suspension': True
                    },
                    'suspension_levels': {
                        'soft_suspension': {
                            'duration_days': 14,
                            'data_access': 'read_only',
                            'export_allowed': True,
                            'reactivation_self_service': True
                        },
                        'hard_suspension': {
                            'duration_days': 30,
                            'data_access': 'export_only',
                            'export_allowed': True,
                            'reactivation_self_service': False
                        },
                        'permanent_suspension': {
                            'duration_days': 90,
                            'data_access': 'none',
                            'export_allowed': False,
                            'reactivation_self_service': False
                        }
                    },
                    'data_retention': {
                        'soft_suspension_days': 30,
                        'hard_suspension_days': 60,
                        'permanent_suspension_days': 90
                    },
                    'notifications': {
                        'suspension_warning': True,
                        'suspension_activated': True,
                        'data_export_reminder': True,
                        'reactivation_instructions': True
                    }
                },
                'reactivation': {
                    'enabled': True,
                    'reactivation_methods': {
                        'self_service': {
                            'enabled': True,
                            'payment_method_update': True,
                            'automatic_retry': True,
                            'manual_payment': True
                        },
                        'support_assisted': {
                            'enabled': True,
                            'phone_support': True,
                            'email_support': True,
                            'chat_support': True
                        },
                        'admin_override': {
                            'enabled': True,
                            'temporary_access': True,
                            'payment_plan_setup': True,
                            'manual_reactivation': True
                        }
                    },
                    'reactivation_workflows': {
                        'immediate_reactivation': {
                            'conditions': ['payment_successful', 'payment_method_updated'],
                            'access_level': 'full',
                            'feature_restoration': 'immediate',
                            'notification': True
                        },
                        'gradual_reactivation': {
                            'conditions': ['partial_payment', 'payment_plan_agreed'],
                            'access_level': 'limited',
                            'feature_restoration': 'gradual',
                            'notification': True
                        },
                        'conditional_reactivation': {
                            'conditions': ['support_approval', 'admin_override'],
                            'access_level': 'conditional',
                            'feature_restoration': 'conditional',
                            'notification': True
                        }
                    },
                    'verification_requirements': {
                        'payment_verification': True,
                        'identity_verification': False,
                        'usage_verification': False,
                        'support_approval': False
                    },
                    'notifications': {
                        'reactivation_successful': True,
                        'reactivation_failed': True,
                        'access_restored': True,
                        'feature_restoration': True
                    }
                }
            },
            'analytics_and_optimization': {
                'enabled': True,
                'payment_method_analytics': {
                    'enabled': True,
                    'tracking_metrics': {
                        'failure_rates': True,
                        'recovery_rates': True,
                        'average_recovery_time': True,
                        'recovery_cost': True,
                        'customer_satisfaction': True,
                        'churn_rates': True
                    },
                    'payment_methods': {
                        'credit_card': {
                            'tracking_enabled': True,
                            'failure_categories': ['expired', 'insufficient_funds', 'declined', 'fraudulent'],
                            'recovery_strategies': ['immediate_retry', 'payment_method_update', 'grace_period']
                        },
                        'debit_card': {
                            'tracking_enabled': True,
                            'failure_categories': ['insufficient_funds', 'declined', 'daily_limit'],
                            'recovery_strategies': ['immediate_retry', 'payment_method_update', 'grace_period']
                        },
                        'bank_transfer': {
                            'tracking_enabled': True,
                            'failure_categories': ['insufficient_funds', 'account_closed', 'routing_error'],
                            'recovery_strategies': ['payment_method_update', 'grace_period', 'payment_plan']
                        },
                        'digital_wallet': {
                            'tracking_enabled': True,
                            'failure_categories': ['insufficient_funds', 'account_suspended', 'verification_required'],
                            'recovery_strategies': ['immediate_retry', 'payment_method_update', 'grace_period']
                        },
                        'crypto': {
                            'tracking_enabled': True,
                            'failure_categories': ['insufficient_funds', 'network_error', 'transaction_failed'],
                            'recovery_strategies': ['payment_method_update', 'grace_period', 'payment_plan']
                        }
                    },
                    'reporting_intervals': {
                        'real_time': True,
                        'hourly': True,
                        'daily': True,
                        'weekly': True,
                        'monthly': True
                    },
                    'alert_thresholds': {
                        'failure_rate_warning': 0.05,  # 5%
                        'failure_rate_critical': 0.10,  # 10%
                        'recovery_rate_warning': 0.70,  # 70%
                        'recovery_rate_critical': 0.50   # 50%
                    }
                },
                'recovery_rate_optimization': {
                    'enabled': True,
                    'optimization_strategies': {
                        'retry_timing': {
                            'enabled': True,
                            'test_variants': [
                                {'name': 'immediate', 'delay_minutes': 0},
                                {'name': 'delayed_1h', 'delay_minutes': 60},
                                {'name': 'delayed_4h', 'delay_minutes': 240},
                                {'name': 'delayed_24h', 'delay_minutes': 1440}
                            ]
                        },
                        'retry_amounts': {
                            'enabled': True,
                            'test_variants': [
                                {'name': 'full_amount', 'percentage': 100},
                                {'name': 'reduced_10', 'percentage': 90},
                                {'name': 'reduced_25', 'percentage': 75},
                                {'name': 'reduced_50', 'percentage': 50}
                            ]
                        },
                        'notification_timing': {
                            'enabled': True,
                            'test_variants': [
                                {'name': 'immediate', 'delay_minutes': 0},
                                {'name': 'delayed_1h', 'delay_minutes': 60},
                                {'name': 'delayed_4h', 'delay_minutes': 240},
                                {'name': 'delayed_24h', 'delay_minutes': 1440}
                            ]
                        },
                        'grace_period_duration': {
                            'enabled': True,
                            'test_variants': [
                                {'name': '3_days', 'duration_days': 3},
                                {'name': '7_days', 'duration_days': 7},
                                {'name': '10_days', 'duration_days': 10},
                                {'name': '14_days', 'duration_days': 14}
                            ]
                        },
                        'dunning_email_sequence': {
                            'enabled': True,
                            'test_variants': [
                                {'name': 'aggressive', 'frequency': 'daily', 'tone': 'urgent'},
                                {'name': 'moderate', 'frequency': 'every_3_days', 'tone': 'professional'},
                                {'name': 'gentle', 'frequency': 'weekly', 'tone': 'friendly'},
                                {'name': 'minimal', 'frequency': 'every_2_weeks', 'tone': 'informative'}
                            ]
                        },
                        'retention_offers': {
                            'enabled': True,
                            'test_variants': [
                                {'name': 'no_offer', 'discount_percent': 0},
                                {'name': 'small_discount', 'discount_percent': 10},
                                {'name': 'medium_discount', 'discount_percent': 25},
                                {'name': 'large_discount', 'discount_percent': 50}
                            ]
                        }
                    },
                    'ab_testing': {
                        'enabled': True,
                        'test_duration_days': 30,
                        'minimum_sample_size': 100,
                        'confidence_level': 0.95,
                        'traffic_allocation': {
                            'control': 0.25,
                            'variant_a': 0.25,
                            'variant_b': 0.25,
                            'variant_c': 0.25
                        },
                        'success_metrics': {
                            'primary': 'recovery_rate',
                            'secondary': ['recovery_time', 'customer_satisfaction', 'churn_rate']
                        },
                        'statistical_tests': {
                            'chi_square': True,
                            't_test': True,
                            'mann_whitney': True,
                            'bayesian_analysis': True
                        }
                    },
                    'machine_learning': {
                        'enabled': True,
                        'models': {
                            'failure_prediction': {
                                'enabled': True,
                                'features': ['payment_history', 'customer_behavior', 'payment_method', 'amount'],
                                'algorithm': 'random_forest',
                                'retraining_frequency': 'weekly'
                            },
                            'recovery_optimization': {
                                'enabled': True,
                                'features': ['failure_reason', 'customer_segment', 'payment_method', 'amount'],
                                'algorithm': 'gradient_boosting',
                                'retraining_frequency': 'weekly'
                            },
                            'churn_prediction': {
                                'enabled': True,
                                'features': ['payment_failures', 'recovery_attempts', 'customer_satisfaction', 'usage_patterns'],
                                'algorithm': 'logistic_regression',
                                'retraining_frequency': 'weekly'
                            }
                        },
                        'feature_engineering': {
                            'enabled': True,
                            'features': {
                                'payment_history': ['success_rate', 'failure_rate', 'average_amount'],
                                'customer_behavior': ['login_frequency', 'feature_usage', 'support_contacts'],
                                'payment_method': ['method_type', 'age', 'success_rate'],
                                'temporal': ['day_of_week', 'month', 'season', 'time_of_day']
                            }
                        }
                    }
                },
                'performance_monitoring': {
                    'enabled': True,
                    'key_performance_indicators': {
                        'payment_failure_rate': {
                            'enabled': True,
                            'calculation': 'failed_payments / total_payments',
                            'target': 0.05,
                            'alert_threshold': 0.10
                        },
                        'recovery_rate': {
                            'enabled': True,
                            'calculation': 'recovered_payments / failed_payments',
                            'target': 0.80,
                            'alert_threshold': 0.60
                        },
                        'average_recovery_time': {
                            'enabled': True,
                            'calculation': 'sum(recovery_times) / recovered_payments',
                            'target': 7,  # days
                            'alert_threshold': 14  # days
                        },
                        'recovery_cost': {
                            'enabled': True,
                            'calculation': 'total_recovery_cost / recovered_payments',
                            'target': 5.0,  # dollars
                            'alert_threshold': 10.0  # dollars
                        },
                        'customer_satisfaction': {
                            'enabled': True,
                            'calculation': 'satisfied_customers / total_customers',
                            'target': 0.85,
                            'alert_threshold': 0.70
                        },
                        'churn_rate': {
                            'enabled': True,
                            'calculation': 'churned_customers / total_customers',
                            'target': 0.05,
                            'alert_threshold': 0.10
                        }
                    },
                    'real_time_monitoring': {
                        'enabled': True,
                        'update_frequency_minutes': 5,
                        'dashboard_refresh_rate': 60,
                        'alert_channels': ['email', 'slack', 'webhook']
                    },
                    'historical_analysis': {
                        'enabled': True,
                        'data_retention_days': 365,
                        'trend_analysis': True,
                        'seasonal_patterns': True,
                        'anomaly_detection': True
                    }
                },
                'churn_prediction_and_prevention': {
                    'enabled': True,
                    'churn_prediction': {
                        'enabled': True,
                        'prediction_horizon_days': 30,
                        'confidence_threshold': 0.75,
                        'update_frequency_hours': 24,
                        'features': {
                            'payment_behavior': ['payment_failures', 'recovery_attempts', 'payment_method_changes'],
                            'usage_patterns': ['login_frequency', 'feature_usage', 'session_duration'],
                            'support_interactions': ['support_tickets', 'complaint_frequency', 'satisfaction_scores'],
                            'account_activity': ['last_login', 'subscription_changes', 'billing_cycles'],
                            'demographic': ['customer_age', 'plan_type', 'geographic_location']
                        },
                        'risk_levels': {
                            'low': {'probability': 0.0, 'threshold': 0.3},
                            'medium': {'probability': 0.3, 'threshold': 0.7},
                            'high': {'probability': 0.7, 'threshold': 1.0}
                        },
                        'prevention_strategies': {
                            'low_risk': ['engagement_campaigns', 'feature_highlights', 'success_stories'],
                            'medium_risk': ['personalized_offers', 'support_outreach', 'usage_optimization'],
                            'high_risk': ['retention_offers', 'account_reviews', 'escalated_support']
                        }
                    },
                    'churn_prevention_triggers': {
                        'enabled': True,
                        'triggers': {
                            'payment_failure_escalation': {
                                'enabled': True,
                                'threshold': 3,  # consecutive failures
                                'time_window_days': 30,
                                'actions': ['support_outreach', 'payment_method_update', 'grace_period_extension']
                            },
                            'usage_decline': {
                                'enabled': True,
                                'threshold': 0.5,  # 50% decline in usage
                                'time_window_days': 14,
                                'actions': ['engagement_campaign', 'feature_highlight', 'support_outreach']
                            },
                            'support_ticket_escalation': {
                                'enabled': True,
                                'threshold': 2,  # support tickets
                                'time_window_days': 30,
                                'actions': ['account_review', 'escalated_support', 'compensation_offer']
                            },
                            'satisfaction_decline': {
                                'enabled': True,
                                'threshold': 0.6,  # satisfaction score
                                'time_window_days': 7,
                                'actions': ['satisfaction_survey', 'support_outreach', 'improvement_plan']
                            },
                            'subscription_downgrade': {
                                'enabled': True,
                                'threshold': 1,  # downgrade event
                                'time_window_days': 7,
                                'actions': ['upgrade_incentive', 'feature_highlight', 'success_story']
                            }
                        },
                        'notification_channels': ['email', 'sms', 'in_app', 'support_ticket'],
                        'escalation_levels': {
                            'level_1': {'response_time_hours': 24, 'channel': 'email'},
                            'level_2': {'response_time_hours': 4, 'channel': 'sms'},
                            'level_3': {'response_time_hours': 1, 'channel': 'phone'}
                        }
                    }
                },
                'revenue_recovery_reporting': {
                    'enabled': True,
                    'revenue_tracking': {
                        'enabled': True,
                        'metrics': {
                            'recovered_revenue': {
                                'enabled': True,
                                'calculation': 'sum(recovered_payments)',
                                'time_periods': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
                            },
                            'lost_revenue': {
                                'enabled': True,
                                'calculation': 'sum(failed_payments - recovered_payments)',
                                'time_periods': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
                            },
                            'recovery_efficiency': {
                                'enabled': True,
                                'calculation': 'recovered_revenue / (recovered_revenue + lost_revenue)',
                                'time_periods': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
                            },
                            'recovery_cost_ratio': {
                                'enabled': True,
                                'calculation': 'total_recovery_cost / recovered_revenue',
                                'time_periods': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
                            },
                            'average_recovery_time': {
                                'enabled': True,
                                'calculation': 'sum(recovery_times * amounts) / sum(amounts)',
                                'time_periods': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
                            }
                        },
                        'segmentation': {
                            'by_customer_segment': True,
                            'by_payment_method': True,
                            'by_failure_reason': True,
                            'by_recovery_strategy': True,
                            'by_geographic_region': True
                        }
                    },
                    'trending_analysis': {
                        'enabled': True,
                        'trend_indicators': {
                            'revenue_recovery_trend': {
                                'enabled': True,
                                'calculation': 'slope(recovery_efficiency_over_time)',
                                'thresholds': {'improving': 0.01, 'declining': -0.01}
                            },
                            'recovery_cost_trend': {
                                'enabled': True,
                                'calculation': 'slope(recovery_cost_ratio_over_time)',
                                'thresholds': {'improving': -0.01, 'declining': 0.01}
                            },
                            'recovery_time_trend': {
                                'enabled': True,
                                'calculation': 'slope(average_recovery_time_over_time)',
                                'thresholds': {'improving': -0.5, 'declining': 0.5}
                            }
                        },
                        'seasonal_analysis': {
                            'enabled': True,
                            'patterns': ['monthly', 'quarterly', 'yearly'],
                            'anomaly_detection': True,
                            'forecasting': True
                        },
                        'predictive_analytics': {
                            'enabled': True,
                            'forecast_horizon_days': 90,
                            'confidence_intervals': [0.8, 0.9, 0.95],
                            'models': ['linear_regression', 'time_series', 'machine_learning']
                        }
                    },
                    'reporting': {
                        'enabled': True,
                        'report_types': {
                            'executive_summary': {
                                'enabled': True,
                                'frequency': 'weekly',
                                'metrics': ['recovered_revenue', 'recovery_efficiency', 'recovery_cost_ratio']
                            },
                            'operational_dashboard': {
                                'enabled': True,
                                'frequency': 'daily',
                                'metrics': ['recovered_revenue', 'lost_revenue', 'recovery_time', 'active_recoveries']
                            },
                            'trend_analysis': {
                                'enabled': True,
                                'frequency': 'monthly',
                                'metrics': ['revenue_recovery_trend', 'recovery_cost_trend', 'recovery_time_trend']
                            },
                            'segment_performance': {
                                'enabled': True,
                                'frequency': 'weekly',
                                'metrics': ['recovery_efficiency_by_segment', 'recovery_cost_by_segment']
                            }
                        },
                        'delivery_channels': ['email', 'dashboard', 'api', 'webhook'],
                        'customization': {
                            'enabled': True,
                            'custom_metrics': True,
                            'custom_time_periods': True,
                            'custom_segments': True
                        }
                    }
                },
                'customer_support_escalation': {
                    'enabled': True,
                    'escalation_triggers': {
                        'payment_failure_escalation': {
                            'enabled': True,
                            'triggers': {
                                'consecutive_failures': {
                                    'enabled': True,
                                    'threshold': 3,
                                    'time_window_days': 30,
                                    'priority': 'high',
                                    'escalation_level': 'level_2'
                                },
                                'high_value_customer_failure': {
                                    'enabled': True,
                                    'threshold': 1,
                                    'time_window_days': 7,
                                    'priority': 'critical',
                                    'escalation_level': 'level_3'
                                },
                                'payment_method_expiration': {
                                    'enabled': True,
                                    'threshold': 1,
                                    'time_window_days': 7,
                                    'priority': 'medium',
                                    'escalation_level': 'level_1'
                                },
                                'recovery_attempt_failure': {
                                    'enabled': True,
                                    'threshold': 2,
                                    'time_window_days': 14,
                                    'priority': 'high',
                                    'escalation_level': 'level_2'
                                }
                            }
                        },
                        'customer_behavior_escalation': {
                            'enabled': True,
                            'triggers': {
                                'usage_decline': {
                                    'enabled': True,
                                    'threshold': 0.7,  # 70% decline
                                    'time_window_days': 14,
                                    'priority': 'medium',
                                    'escalation_level': 'level_1'
                                },
                                'support_ticket_frequency': {
                                    'enabled': True,
                                    'threshold': 3,
                                    'time_window_days': 30,
                                    'priority': 'high',
                                    'escalation_level': 'level_2'
                                },
                                'satisfaction_score_decline': {
                                    'enabled': True,
                                    'threshold': 0.5,
                                    'time_window_days': 7,
                                    'priority': 'high',
                                    'escalation_level': 'level_2'
                                },
                                'account_inactivity': {
                                    'enabled': True,
                                    'threshold': 30,  # days
                                    'priority': 'medium',
                                    'escalation_level': 'level_1'
                                }
                            }
                        },
                        'business_impact_escalation': {
                            'enabled': True,
                            'triggers': {
                                'revenue_at_risk': {
                                    'enabled': True,
                                    'threshold': 1000,  # dollars
                                    'time_window_days': 7,
                                    'priority': 'critical',
                                    'escalation_level': 'level_3'
                                },
                                'churn_probability': {
                                    'enabled': True,
                                    'threshold': 0.8,  # 80% probability
                                    'time_window_days': 7,
                                    'priority': 'critical',
                                    'escalation_level': 'level_3'
                                },
                                'subscription_cancellation': {
                                    'enabled': True,
                                    'threshold': 1,
                                    'time_window_days': 1,
                                    'priority': 'critical',
                                    'escalation_level': 'level_3'
                                }
                            }
                        }
                    },
                    'escalation_workflows': {
                        'enabled': True,
                        'levels': {
                            'level_1': {
                                'name': 'Automated Outreach',
                                'response_time_hours': 24,
                                'actions': ['email_notification', 'in_app_notification', 'automated_support_ticket'],
                                'escalation_criteria': ['no_response_24h', 'customer_request']
                            },
                            'level_2': {
                                'name': 'Support Specialist',
                                'response_time_hours': 4,
                                'actions': ['phone_call', 'personalized_email', 'account_review'],
                                'escalation_criteria': ['no_response_4h', 'complex_issue', 'high_value_customer']
                            },
                            'level_3': {
                                'name': 'Account Manager',
                                'response_time_hours': 1,
                                'actions': ['immediate_phone_call', 'account_restoration', 'compensation_offer'],
                                'escalation_criteria': ['no_response_1h', 'critical_issue', 'vip_customer']
                            }
                        },
                        'automation': {
                            'enabled': True,
                            'auto_escalation': True,
                            'auto_de_escalation': True,
                            'escalation_timeout_hours': 48,
                            'de_escalation_criteria': ['issue_resolved', 'customer_satisfied', 'payment_recovered']
                        }
                    },
                                    'support_integration': {
                    'enabled': True,
                    'ticket_creation': {
                        'enabled': True,
                        'auto_create': True,
                        'ticket_categories': ['payment_issue', 'account_issue', 'technical_issue', 'billing_issue'],
                        'priority_mapping': {
                            'low': 'normal',
                            'medium': 'high',
                            'high': 'urgent',
                            'critical': 'critical'
                        }
                    },
                    'customer_context': {
                        'enabled': True,
                        'include_payment_history': True,
                        'include_recovery_attempts': True,
                        'include_churn_probability': True,
                        'include_customer_value': True,
                        'include_previous_interactions': True
                    },
                    'resolution_tracking': {
                        'enabled': True,
                        'track_resolution_time': True,
                        'track_customer_satisfaction': True,
                        'track_escalation_effectiveness': True,
                        'auto_close_resolved': True
                    }
                }
            },
            'compliance_and_communication': {
                'enabled': True,
                'billing_communication': {
                    'enabled': True,
                    'transparency_requirements': {
                        'enabled': True,
                        'clear_pricing': {
                            'enabled': True,
                            'show_base_price': True,
                            'show_taxes': True,
                            'show_fees': True,
                            'show_discounts': True,
                            'show_total': True,
                            'currency_display': 'USD',
                            'decimal_places': 2
                        },
                        'billing_frequency': {
                            'enabled': True,
                            'show_next_billing_date': True,
                            'show_billing_cycle': True,
                            'show_auto_renewal': True,
                            'show_cancellation_deadline': True
                        },
                        'payment_methods': {
                            'enabled': True,
                            'show_accepted_methods': True,
                            'show_payment_processing': True,
                            'show_security_info': True,
                            'show_pci_compliance': True
                        },
                        'invoice_details': {
                            'enabled': True,
                            'show_line_items': True,
                            'show_usage_charges': True,
                            'show_adjustments': True,
                            'show_payment_history': True,
                            'show_outstanding_balance': True
                        }
                    },
                    'communication_channels': {
                        'enabled': True,
                        'email_notifications': {
                            'enabled': True,
                            'invoice_emails': True,
                            'payment_reminders': True,
                            'payment_failure_notifications': True,
                            'payment_success_notifications': True,
                            'billing_updates': True
                        },
                        'in_app_notifications': {
                            'enabled': True,
                            'billing_alerts': True,
                            'payment_due_reminders': True,
                            'payment_method_expiry': True,
                            'subscription_changes': True
                        },
                        'sms_notifications': {
                            'enabled': True,
                            'critical_payment_failures': True,
                            'payment_method_expiry': True,
                            'subscription_cancellation': True
                        },
                        'dashboard_notifications': {
                            'enabled': True,
                            'billing_summary': True,
                            'payment_status': True,
                            'subscription_status': True,
                            'account_balance': True
                        }
                    },
                    'language_support': {
                        'enabled': True,
                        'supported_languages': ['en', 'es', 'fr', 'de', 'pt', 'it', 'ja', 'ko', 'zh'],
                        'default_language': 'en',
                        'auto_detect_language': True,
                        'translation_quality': 'professional'
                    },
                    'accessibility': {
                        'enabled': True,
                        'screen_reader_support': True,
                        'high_contrast_mode': True,
                        'font_size_options': True,
                        'keyboard_navigation': True,
                        'wcag_compliance': 'AA'
                    }
                },
                'subscription_terms': {
                    'enabled': True,
                    'terms_and_conditions': {
                        'enabled': True,
                        'version_control': True,
                        'acceptance_tracking': True,
                        'change_notifications': True,
                        'legal_compliance': {
                            'gdpr_compliance': True,
                            'ccpa_compliance': True,
                            'pci_compliance': True,
                            'sox_compliance': True
                        }
                    },
                    'grace_period_explanation': {
                        'enabled': True,
                        'grace_period_duration': {
                            'standard': 7,
                            'premium': 14,
                            'enterprise': 21
                        },
                        'grace_period_benefits': {
                            'enabled': True,
                            'full_service_access': True,
                            'payment_method_updates': True,
                            'support_assistance': True,
                            'no_late_fees': True
                        },
                        'grace_period_limitations': {
                            'enabled': True,
                            'feature_restrictions': True,
                            'api_rate_limits': True,
                            'support_priority': True,
                            'renewal_requirements': True
                        },
                        'grace_period_communication': {
                            'enabled': True,
                            'grace_period_start_notification': True,
                            'daily_grace_period_reminders': True,
                            'grace_period_expiry_warning': True,
                            'grace_period_extension_offers': True
                        }
                    },
                    'subscription_features': {
                        'enabled': True,
                        'feature_breakdown': {
                            'enabled': True,
                            'core_features': True,
                            'premium_features': True,
                            'enterprise_features': True,
                            'usage_limits': True,
                            'feature_availability': True
                        },
                        'usage_tracking': {
                            'enabled': True,
                            'real_time_usage': True,
                            'usage_limits': True,
                            'overage_charges': True,
                            'usage_alerts': True,
                            'usage_reports': True
                        },
                        'service_levels': {
                            'enabled': True,
                            'uptime_guarantees': True,
                            'response_time_guarantees': True,
                            'support_response_times': True,
                            'data_backup_guarantees': True
                        }
                    },
                    'cancellation_policy': {
                        'enabled': True,
                        'cancellation_terms': {
                            'enabled': True,
                            'cancellation_deadline': True,
                            'proration_policy': True,
                            'refund_policy': True,
                            'data_retention_policy': True
                        },
                        'cancellation_process': {
                            'enabled': True,
                            'self_service_cancellation': True,
                            'cancellation_confirmation': True,
                            'cancellation_reason_collection': True,
                            'retention_offers': True
                        },
                        'cancellation_communication': {
                            'enabled': True,
                            'cancellation_confirmation_email': True,
                            'cancellation_summary': True,
                            'data_export_instructions': True,
                            'reactivation_instructions': True
                        }
                    }
                },
                'customer_support_integration': {
                    'enabled': True,
                    'support_channels': {
                        'enabled': True,
                        'live_chat': {
                            'enabled': True,
                            'availability': '24/7',
                            'response_time': '2_minutes',
                            'chat_history': True,
                            'file_sharing': True,
                            'screen_sharing': True
                        },
                        'phone_support': {
                            'enabled': True,
                            'availability': 'business_hours',
                            'response_time': 'immediate',
                            'call_recording': True,
                            'call_transfer': True,
                            'callback_service': True
                        },
                        'email_support': {
                            'enabled': True,
                            'availability': '24/7',
                            'response_time': '4_hours',
                            'auto_response': True,
                            'ticket_tracking': True,
                            'escalation_rules': True
                        },
                        'knowledge_base': {
                            'enabled': True,
                            'self_service_articles': True,
                            'video_tutorials': True,
                            'faq_section': True,
                            'search_functionality': True,
                            'feedback_collection': True
                        }
                    },
                    'complex_case_handling': {
                        'enabled': True,
                        'case_classification': {
                            'enabled': True,
                            'billing_disputes': True,
                            'technical_issues': True,
                            'account_access': True,
                            'data_requests': True,
                            'compliance_issues': True
                        },
                        'escalation_procedures': {
                            'enabled': True,
                            'automatic_escalation': True,
                            'manual_escalation': True,
                            'escalation_criteria': True,
                            'escalation_tracking': True,
                            'resolution_time_tracking': True
                        },
                        'specialist_assignment': {
                            'enabled': True,
                            'billing_specialists': True,
                            'technical_specialists': True,
                            'compliance_specialists': True,
                            'account_managers': True,
                            'senior_support': True
                        },
                        'case_resolution': {
                            'enabled': True,
                            'resolution_tracking': True,
                            'customer_satisfaction': True,
                            'follow_up_surveys': True,
                            'case_analytics': True,
                            'improvement_metrics': True
                        }
                    },
                    'support_automation': {
                        'enabled': True,
                        'chatbots': {
                            'enabled': True,
                            'billing_questions': True,
                            'payment_issues': True,
                            'subscription_help': True,
                            'account_management': True,
                            'escalation_to_human': True
                        },
                        'automated_responses': {
                            'enabled': True,
                            'common_questions': True,
                            'payment_confirmations': True,
                            'subscription_updates': True,
                            'maintenance_notifications': True,
                            'outage_notifications': True
                        },
                        'self_service_tools': {
                            'enabled': True,
                            'payment_method_updates': True,
                            'billing_address_changes': True,
                            'subscription_modifications': True,
                            'invoice_downloads': True,
                            'usage_reports': True
                        }
                    }
                },
                'refund_and_cancellation': {
                    'enabled': True,
                    'refund_policy': {
                        'enabled': True,
                        'refund_eligibility': {
                            'enabled': True,
                            'money_back_guarantee': {
                                'enabled': True,
                                'duration_days': 30,
                                'conditions': ['unused_portion', 'technical_issues', 'service_quality'],
                                'exclusions': ['fraudulent_use', 'terms_violation', 'excessive_usage']
                            },
                            'prorated_refunds': {
                                'enabled': True,
                                'calculation_method': 'daily_proration',
                                'minimum_refund_amount': 1.00,
                                'processing_time_days': 5
                            },
                            'partial_refunds': {
                                'enabled': True,
                                'circumstances': ['service_outage', 'billing_error', 'customer_satisfaction'],
                                'approval_required': True,
                                'maximum_refund_percentage': 100
                            }
                        },
                        'refund_process': {
                            'enabled': True,
                            'refund_request_submission': {
                                'enabled': True,
                                'online_form': True,
                                'email_request': True,
                                'phone_request': True,
                                'support_ticket': True
                            },
                            'refund_approval': {
                                'enabled': True,
                                'automatic_approval': True,
                                'manual_review': True,
                                'approval_criteria': True,
                                'approval_timeframe': '48_hours'
                            },
                            'refund_processing': {
                                'enabled': True,
                                'payment_method_refund': True,
                                'processing_time': '3_5_business_days',
                                'refund_notification': True,
                                'refund_tracking': True
                            }
                        },
                        'refund_communication': {
                            'enabled': True,
                            'refund_confirmation': {
                                'enabled': True,
                                'email_confirmation': True,
                                'sms_notification': True,
                                'in_app_notification': True,
                                'refund_receipt': True
                            },
                            'refund_status_updates': {
                                'enabled': True,
                                'processing_status': True,
                                'completion_notification': True,
                                'delay_notifications': True,
                                'escalation_procedures': True
                            }
                        }
                    },
                    'cancellation_options': {
                        'enabled': True,
                        'cancellation_methods': {
                            'enabled': True,
                            'self_service_cancellation': {
                                'enabled': True,
                                'online_cancellation': True,
                                'cancellation_confirmation': True,
                                'immediate_cancellation': True,
                                'scheduled_cancellation': True
                            },
                            'support_assisted_cancellation': {
                                'enabled': True,
                                'phone_cancellation': True,
                                'email_cancellation': True,
                                'chat_cancellation': True,
                                'cancellation_verification': True
                            },
                            'emergency_cancellation': {
                                'enabled': True,
                                'fraud_suspicion': True,
                                'account_compromise': True,
                                'billing_dispute': True,
                                'immediate_suspension': True
                            }
                        },
                        'cancellation_effects': {
                            'enabled': True,
                            'service_access': {
                                'enabled': True,
                                'immediate_suspension': True,
                                'grace_period_access': True,
                                'data_access_retention': True,
                                'export_capabilities': True
                            },
                            'billing_effects': {
                                'enabled': True,
                                'proration_calculation': True,
                                'final_billing': True,
                                'outstanding_balance': True,
                                'refund_processing': True
                            },
                            'data_retention': {
                                'enabled': True,
                                'data_retention_period': '90_days',
                                'data_export_options': True,
                                'data_deletion_request': True,
                                'compliance_requirements': True
                            }
                        },
                        'cancellation_communication': {
                            'enabled': True,
                            'cancellation_confirmation': {
                                'enabled': True,
                                'confirmation_email': True,
                                'confirmation_sms': True,
                                'confirmation_letter': True,
                                'cancellation_summary': True
                            },
                            'post_cancellation_support': {
                                'enabled': True,
                                'reactivation_instructions': True,
                                'data_export_help': True,
                                'final_billing_explanation': True,
                                'support_contact_info': True
                            },
                            'retention_efforts': {
                                'enabled': True,
                                'retention_offers': True,
                                'win_back_campaigns': True,
                                'feedback_collection': True,
                                'improvement_suggestions': True
                            }
                        }
                    }
                }
            }
                }
            }
        }
    }
}
        }
        
        # Dunning schedule configuration
        self.dunning_schedule = {
            DunningStage.SOFT_FAILURE: DunningSchedule(
                stage=DunningStage.SOFT_FAILURE,
                delay_days=0,
                notification_type='immediate_notification',
                retry_attempt=True,
                payment_method_update=False
            ),
            DunningStage.HARD_FAILURE: DunningSchedule(
                stage=DunningStage.HARD_FAILURE,
                delay_days=1,
                notification_type='payment_failed_notification',
                retry_attempt=True,
                payment_method_update=True
            ),
            DunningStage.DUNNING_1: DunningSchedule(
                stage=DunningStage.DUNNING_1,
                delay_days=3,
                notification_type='dunning_notification_1',
                retry_attempt=True,
                payment_method_update=True
            ),
            DunningStage.DUNNING_2: DunningSchedule(
                stage=DunningStage.DUNNING_2,
                delay_days=7,
                notification_type='dunning_notification_2',
                retry_attempt=True,
                payment_method_update=True,
                grace_period_days=3
            ),
            DunningStage.DUNNING_3: DunningSchedule(
                stage=DunningStage.DUNNING_3,
                delay_days=14,
                notification_type='dunning_notification_3',
                retry_attempt=True,
                payment_method_update=True,
                grace_period_days=7
            ),
            DunningStage.DUNNING_4: DunningSchedule(
                stage=DunningStage.DUNNING_4,
                delay_days=21,
                notification_type='dunning_notification_4',
                retry_attempt=False,
                payment_method_update=True,
                grace_period_days=14
            ),
            DunningStage.DUNNING_5: DunningSchedule(
                stage=DunningStage.DUNNING_5,
                delay_days=28,
                notification_type='dunning_notification_5',
                retry_attempt=False,
                payment_method_update=True,
                grace_period_days=21
            ),
            DunningStage.FINAL_NOTICE: DunningSchedule(
                stage=DunningStage.FINAL_NOTICE,
                delay_days=30,
                notification_type='final_notice',
                retry_attempt=False,
                payment_method_update=True,
                grace_period_days=30
            ),
            DunningStage.CANCELLATION: DunningSchedule(
                stage=DunningStage.CANCELLATION,
                delay_days=35,
                notification_type='cancellation_notice',
                retry_attempt=False,
                payment_method_update=False
            )
        }
        
        # Recovery strategies by failure type
        self.recovery_strategies = {
            'card_declined': [
                RecoveryStrategy.AUTOMATIC_RETRY,
                RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                RecoveryStrategy.GRACE_PERIOD
            ],
            'insufficient_funds': [
                RecoveryStrategy.AUTOMATIC_RETRY,
                RecoveryStrategy.PARTIAL_PAYMENT,
                RecoveryStrategy.PAYMENT_PLAN
            ],
            'expired_card': [
                RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                RecoveryStrategy.GRACE_PERIOD
            ],
            'fraudulent': [
                RecoveryStrategy.MANUAL_INTERVENTION
            ],
            'processing_error': [
                RecoveryStrategy.AUTOMATIC_RETRY,
                RecoveryStrategy.MANUAL_INTERVENTION
            ],
            'unknown': [
                RecoveryStrategy.AUTOMATIC_RETRY,
                RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                RecoveryStrategy.GRACE_PERIOD
            ]
        }
        
        # Performance metrics
        self.performance_metrics = {
            'recovery_attempts': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'average_recovery_time_days': 0.0,
            'recovery_rate': 0.0,
            'revenue_recovered': 0.0
        }
    
    def handle_payment_failure(
        self,
        customer_id: str,
        subscription_id: str,
        invoice_id: str,
        payment_intent_id: str,
        failure_reason: str,
        failure_code: str,
        amount: float,
        currency: str = 'usd'
    ) -> Dict[str, Any]:
        """Handle payment failure and initiate recovery process"""
        try:
            start_time = time.time()
            
            # Create payment failure record
            failure = PaymentFailure(
                failure_id=str(uuid.uuid4()),
                customer_id=customer_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                payment_intent_id=payment_intent_id,
                failure_reason=failure_reason,
                failure_code=failure_code,
                amount=amount,
                currency=currency,
                failed_at=datetime.now(timezone.utc)
            )
            
            # Store failure record
            self._store_payment_failure(failure)
            
            # Check if this is a temporary failure requiring immediate retry
            is_temporary_failure = self._is_temporary_failure(failure_reason, failure_code)
            
            if is_temporary_failure:
                # Execute immediate retry workflow for temporary failures
                immediate_retry_result = self._execute_immediate_retry_workflow(failure)
                
                # Update customer status based on retry result
                if immediate_retry_result['success']:
                    self._update_customer_payment_status(customer_id, 'active')
                    status_message = 'Payment recovered through immediate retry'
                else:
                    self._update_customer_payment_status(customer_id, 'past_due')
                    status_message = 'Immediate retry failed, proceeding with recovery workflow'
                
                # Record performance metric
                processing_time = (time.time() - start_time) * 1000
                self._update_performance_metrics(processing_time, immediate_retry_result['success'])
                
                return {
                    'success': True,
                    'failure_id': failure.failure_id,
                    'is_temporary_failure': True,
                    'immediate_retry_attempted': True,
                    'immediate_retry_success': immediate_retry_result['success'],
                    'retry_result': immediate_retry_result,
                    'status_message': status_message,
                    'processing_time_ms': processing_time
                }
            else:
                # Standard recovery workflow for non-temporary failures
                strategy = self._determine_recovery_strategy(failure)
                recovery_plan = self._create_recovery_plan(failure, strategy)
                immediate_result = self._execute_immediate_recovery_actions(failure, recovery_plan)
                scheduled_result = self._schedule_follow_up_actions(failure, recovery_plan)
                
                # Update customer status
                self._update_customer_payment_status(customer_id, 'past_due')
                
                # Record performance metric
                processing_time = (time.time() - start_time) * 1000
                self._update_performance_metrics(processing_time, True)
                
                return {
                    'success': True,
                    'failure_id': failure.failure_id,
                    'is_temporary_failure': False,
                    'recovery_strategy': strategy.value,
                    'immediate_actions': immediate_result,
                    'scheduled_actions': scheduled_result,
                    'processing_time_ms': processing_time
                }
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_recovery_actions(self) -> Dict[str, Any]:
        """Process scheduled recovery actions"""
        try:
            start_time = time.time()
            
            # Get pending recovery actions
            pending_actions = self._get_pending_recovery_actions()
            
            processed_count = 0
            successful_count = 0
            
            for action in pending_actions:
                try:
                    # Execute recovery action
                    result = self._execute_recovery_action(action)
                    
                    if result['success']:
                        successful_count += 1
                    
                    processed_count += 1
                    
                    # Update action record
                    self._update_recovery_action(action.action_id, result)
                    
                except Exception as e:
                    logger.error(f"Error executing recovery action {action.action_id}: {e}")
                    self._update_recovery_action(action.action_id, {
                        'success': False,
                        'error': str(e)
                    })
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, successful_count > 0)
            
            return {
                'success': True,
                'processed_actions': processed_count,
                'successful_actions': successful_count,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing recovery actions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def retry_payment(
        self,
        failure_id: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retry failed payment"""
        try:
            # Get payment failure record
            failure = self._get_payment_failure(failure_id)
            if not failure:
                return {'success': False, 'error': 'Payment failure not found'}
            
            # Get customer and subscription
            customer = self._get_customer(failure.customer_id)
            subscription = self._get_subscription(failure.subscription_id)
            
            if not customer or not subscription:
                return {'success': False, 'error': 'Customer or subscription not found'}
            
            # Determine payment method
            if payment_method_id:
                payment_method = payment_method_id
            else:
                payment_method = self._get_default_payment_method(customer.stripe_customer_id)
            
            # Attempt payment retry
            try:
                payment_intent = self.stripe.PaymentIntent.create(
                    amount=int(failure.amount * 100),  # Convert to cents
                    currency=failure.currency,
                    customer=customer.stripe_customer_id,
                    payment_method=payment_method,
                    confirm=True,
                    off_session=True,
                    metadata={
                        'failure_id': failure_id,
                        'retry_count': failure.retry_count + 1,
                        'subscription_id': failure.subscription_id
                    }
                )
                
                if payment_intent.status == 'succeeded':
                    # Payment successful
                    self._handle_payment_success(failure, payment_intent)
                    return {
                        'success': True,
                        'payment_intent_id': payment_intent.id,
                        'status': 'succeeded'
                    }
                else:
                    # Payment failed again
                    self._handle_payment_retry_failure(failure, payment_intent)
                    return {
                        'success': False,
                        'payment_intent_id': payment_intent.id,
                        'status': payment_intent.status,
                        'error': payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed'
                    }
                    
            except stripe.error.CardError as e:
                # Handle card errors
                self._handle_payment_retry_failure(failure, None, str(e))
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'card_error'
                }
                
        except Exception as e:
            logger.error(f"Error retrying payment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_payment_method(
        self,
        customer_id: str,
        new_payment_method_id: str
    ) -> Dict[str, Any]:
        """Update customer's payment method"""
        try:
            # Get customer
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Update default payment method in Stripe
            self.stripe.Customer.modify(
                customer.stripe_customer_id,
                invoice_settings={
                    'default_payment_method': new_payment_method_id
                }
            )
            
            # Update subscription payment method
            subscriptions = self._get_customer_subscriptions(customer_id)
            for subscription in subscriptions:
                if subscription.stripe_subscription_id:
                    self.stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        default_payment_method=new_payment_method_id
                    )
            
            # Retry failed payments with new payment method
            failed_payments = self._get_failed_payments_for_customer(customer_id)
            retry_results = []
            
            for failure in failed_payments:
                retry_result = self.retry_payment(failure.failure_id, new_payment_method_id)
                retry_results.append(retry_result)
            
            return {
                'success': True,
                'payment_method_updated': True,
                'subscriptions_updated': len(subscriptions),
                'retry_attempts': len(retry_results),
                'successful_retries': sum(1 for r in retry_results if r['success'])
            }
            
        except Exception as e:
            logger.error(f"Error updating payment method: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def manage_grace_period(
        self,
        customer_id: str,
        grace_period_days: int
    ) -> Dict[str, Any]:
        """Manage grace period for customer"""
        try:
            # Get customer
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Calculate grace period end date
            grace_period_end = datetime.now(timezone.utc) + timedelta(days=grace_period_days)
            
            # Update customer grace period
            customer.grace_period_until = grace_period_end
            customer.payment_status = 'grace_period'
            
            # Update subscription status
            subscriptions = self._get_customer_subscriptions(customer_id)
            for subscription in subscriptions:
                subscription.status = 'grace_period'
                subscription.grace_period_until = grace_period_end
            
            self.db.commit()
            
            # Send grace period notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': customer_id,
                'user_id': str(customer.user_id) if customer.user_id else None,
                'grace_period_days': grace_period_days,
                'grace_period_end': grace_period_end.isoformat()
            }
            
            notification_result = notification_service.send_grace_period_notifications(notification_data)
            
            return {
                'success': True,
                'grace_period_days': grace_period_days,
                'grace_period_end': grace_period_end.isoformat(),
                'subscriptions_updated': len(subscriptions),
                'notification_sent': notification_result.get('notifications_sent', 0)
            }
            
        except Exception as e:
            logger.error(f"Error managing grace period: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_recovery_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get payment recovery analytics"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get recovery statistics
            total_failures = self._get_failure_count(start_date)
            successful_recoveries = self._get_successful_recovery_count(start_date)
            failed_recoveries = self._get_failed_recovery_count(start_date)
            
            # Calculate recovery rate
            recovery_rate = (successful_recoveries / total_failures * 100) if total_failures > 0 else 0
            
            # Get revenue statistics
            total_revenue_at_risk = self._get_total_revenue_at_risk(start_date)
            recovered_revenue = self._get_recovered_revenue(start_date)
            revenue_recovery_rate = (recovered_revenue / total_revenue_at_risk * 100) if total_revenue_at_risk > 0 else 0
            
            # Get failure reasons breakdown
            failure_reasons = self._get_failure_reasons_breakdown(start_date)
            
            # Get recovery strategy effectiveness
            strategy_effectiveness = self._get_strategy_effectiveness(start_date)
            
            return {
                'success': True,
                'period_days': days,
                'total_failures': total_failures,
                'successful_recoveries': successful_recoveries,
                'failed_recoveries': failed_recoveries,
                'recovery_rate': recovery_rate,
                'total_revenue_at_risk': total_revenue_at_risk,
                'recovered_revenue': recovered_revenue,
                'revenue_recovery_rate': revenue_recovery_rate,
                'failure_reasons': failure_reasons,
                'strategy_effectiveness': strategy_effectiveness
            }
            
        except Exception as e:
            logger.error(f"Error getting recovery analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    # Private methods
    
    def _store_payment_failure(self, failure: PaymentFailure):
        """Store payment failure in database"""
        try:
            # Create payment recovery record
            recovery_record = PaymentRecoveryRecord(
                id=failure.failure_id,
                customer_id=failure.customer_id,
                subscription_id=failure.subscription_id,
                invoice_id=failure.invoice_id,
                payment_intent_id=failure.payment_intent_id,
                failure_reason=failure.failure_reason,
                failure_code=failure.failure_code,
                amount=failure.amount,
                currency=failure.currency,
                failed_at=failure.failed_at,
                retry_count=failure.retry_count,
                next_retry_at=failure.next_retry_at,
                status='pending',
                metadata=failure.metadata or {}
            )
            
            self.db.add(recovery_record)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing payment failure: {e}")
            self.db.rollback()
            raise
    
    def _determine_recovery_strategy(self, failure: PaymentFailure) -> RecoveryStrategy:
        """Determine recovery strategy based on failure reason"""
        try:
            # Map failure reason to strategy
            failure_type = self._categorize_failure_reason(failure.failure_reason)
            strategies = self.recovery_strategies.get(failure_type, self.recovery_strategies['unknown'])
            
            # Get customer value to adjust strategy
            customer = self._get_customer(failure.customer_id)
            if customer and self._is_high_value_customer(customer):
                # Prioritize manual intervention for high-value customers
                if RecoveryStrategy.MANUAL_INTERVENTION in strategies:
                    return RecoveryStrategy.MANUAL_INTERVENTION
            
            # Return first strategy (most appropriate)
            return strategies[0] if strategies else RecoveryStrategy.AUTOMATIC_RETRY
            
        except Exception as e:
            logger.error(f"Error determining recovery strategy: {e}")
            return RecoveryStrategy.AUTOMATIC_RETRY
    
    def _categorize_failure_reason(self, failure_reason: str) -> str:
        """Categorize failure reason"""
        failure_reason_lower = failure_reason.lower()
        
        if 'card_declined' in failure_reason_lower or 'declined' in failure_reason_lower:
            return 'card_declined'
        elif 'insufficient_funds' in failure_reason_lower or 'funds' in failure_reason_lower:
            return 'insufficient_funds'
        elif 'expired' in failure_reason_lower:
            return 'expired_card'
        elif 'fraud' in failure_reason_lower or 'suspicious' in failure_reason_lower:
            return 'fraudulent'
        elif 'processing' in failure_reason_lower or 'error' in failure_reason_lower:
            return 'processing_error'
        else:
            return 'unknown'
    
    def _is_high_value_customer(self, customer: Customer) -> bool:
        """Check if customer is high value"""
        try:
            # Check subscription value
            subscriptions = self._get_customer_subscriptions(str(customer.id))
            total_monthly_value = sum(sub.amount for sub in subscriptions if sub.status == 'active')
            
            return total_monthly_value >= self.recovery_config['high_value_threshold']
            
        except Exception as e:
            logger.error(f"Error checking customer value: {e}")
            return False
    
    def _create_recovery_plan(self, failure: PaymentFailure, strategy: RecoveryStrategy) -> List[RecoveryAction]:
        """Create recovery plan with scheduled actions"""
        try:
            actions = []
            
            # Get dunning schedule
            dunning_stages = list(self.dunning_schedule.keys())
            
            for i, stage in enumerate(dunning_stages):
                schedule = self.dunning_schedule[stage]
                
                # Calculate action time
                action_time = failure.failed_at + timedelta(days=schedule.delay_days)
                
                # Create recovery action
                action = RecoveryAction(
                    action_id=str(uuid.uuid4()),
                    failure_id=failure.failure_id,
                    strategy=strategy,
                    action_type=schedule.notification_type,
                    scheduled_at=action_time,
                    metadata={
                        'dunning_stage': stage.value,
                        'retry_attempt': schedule.retry_attempt,
                        'payment_method_update': schedule.payment_method_update,
                        'grace_period_days': schedule.grace_period_days
                    }
                )
                
                actions.append(action)
                
                # Store action
                self._store_recovery_action(action)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error creating recovery plan: {e}")
            return []
    
    def _execute_immediate_recovery_actions(self, failure: PaymentFailure, recovery_plan: List[RecoveryAction]) -> Dict[str, Any]:
        """Execute immediate recovery actions"""
        try:
            results = []
            
            # Send immediate notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure.customer_id,
                'failure_reason': failure.failure_reason,
                'amount': failure.amount,
                'currency': failure.currency,
                'retry_count': failure.retry_count
            }
            
            notification_result = notification_service.send_payment_failure_notifications(notification_data)
            results.append({
                'action': 'immediate_notification',
                'success': notification_result['success'],
                'notifications_sent': notification_result.get('notifications_sent', 0)
            })
            
            # Attempt immediate retry if appropriate
            if failure.retry_count < self.recovery_config['max_retry_attempts']:
                retry_result = self.retry_payment(failure.failure_id)
                results.append({
                    'action': 'immediate_retry',
                    'success': retry_result['success'],
                    'payment_intent_id': retry_result.get('payment_intent_id')
                })
            
            return {
                'success': True,
                'actions_executed': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error executing immediate recovery actions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _schedule_follow_up_actions(self, failure: PaymentFailure, recovery_plan: List[RecoveryAction]) -> Dict[str, Any]:
        """Schedule follow-up recovery actions"""
        try:
            scheduled_count = 0
            
            for action in recovery_plan:
                if action.scheduled_at > datetime.now(timezone.utc):
                    # Action is in the future, schedule it
                    self._schedule_recovery_action(action)
                    scheduled_count += 1
            
            return {
                'success': True,
                'actions_scheduled': scheduled_count
            }
            
        except Exception as e:
            logger.error(f"Error scheduling follow-up actions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_pending_recovery_actions(self) -> List[RecoveryAction]:
        """Get pending recovery actions"""
        try:
            # This would query the database for pending actions
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting pending recovery actions: {e}")
            return []
    
    def _execute_recovery_action(self, action: RecoveryAction) -> Dict[str, Any]:
        """Execute a recovery action"""
        try:
            # Get failure record
            failure = self._get_payment_failure(action.failure_id)
            if not failure:
                return {'success': False, 'error': 'Payment failure not found'}
            
            # Execute action based on type
            if action.action_type.startswith('dunning_notification'):
                return self._execute_dunning_notification(action, failure)
            elif action.action_type == 'payment_method_update':
                return self._execute_payment_method_update(action, failure)
            elif action.action_type == 'grace_period':
                return self._execute_grace_period(action, failure)
            elif action.action_type == 'retry_payment':
                return self._execute_payment_retry(action, failure)
            else:
                return {'success': False, 'error': f'Unknown action type: {action.action_type}'}
                
        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_dunning_notification(self, action: RecoveryAction, failure: PaymentFailure) -> Dict[str, Any]:
        """Execute dunning notification"""
        try:
            notification_service = NotificationService(self.db, self.config)
            
            notification_data = {
                'customer_id': failure.customer_id,
                'dunning_stage': action.metadata.get('dunning_stage'),
                'failure_reason': failure.failure_reason,
                'amount': failure.amount,
                'currency': failure.currency,
                'retry_count': failure.retry_count
            }
            
            result = notification_service.send_dunning_notifications(notification_data)
            
            return {
                'success': result['success'],
                'notifications_sent': result.get('notifications_sent', 0)
            }
            
        except Exception as e:
            logger.error(f"Error executing dunning notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_payment_method_update(self, action: RecoveryAction, failure: PaymentFailure) -> Dict[str, Any]:
        """Execute payment method update"""
        try:
            # Send payment method update notification
            notification_service = NotificationService(self.db, self.config)
            
            notification_data = {
                'customer_id': failure.customer_id,
                'failure_reason': failure.failure_reason,
                'amount': failure.amount,
                'currency': failure.currency
            }
            
            result = notification_service.send_payment_method_update_notifications(notification_data)
            
            return {
                'success': result['success'],
                'notifications_sent': result.get('notifications_sent', 0)
            }
            
        except Exception as e:
            logger.error(f"Error executing payment method update: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_grace_period(self, action: RecoveryAction, failure: PaymentFailure) -> Dict[str, Any]:
        """Execute grace period action"""
        try:
            grace_period_days = action.metadata.get('grace_period_days', self.recovery_config['grace_period_days'])
            
            result = self.manage_grace_period(failure.customer_id, grace_period_days)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing grace period: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_payment_retry(self, action: RecoveryAction, failure: PaymentFailure) -> Dict[str, Any]:
        """Execute payment retry"""
        try:
            result = self.retry_payment(failure.failure_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing payment retry: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_payment_success(self, failure: PaymentFailure, payment_intent):
        """Handle successful payment recovery"""
        try:
            # Update failure record
            failure_record = self._get_payment_failure_record(failure.failure_id)
            if failure_record:
                failure_record.status = 'recovered'
                failure_record.recovered_at = datetime.now(timezone.utc)
                failure_record.payment_intent_id = payment_intent.id
                
                self.db.commit()
            
            # Update customer status
            self._update_customer_payment_status(failure.customer_id, 'active')
            
            # Send success notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure.customer_id,
                'amount': failure.amount,
                'currency': failure.currency,
                'payment_intent_id': payment_intent.id
            }
            
            notification_service.send_payment_success_notifications(notification_data)
            
            # Track analytics event
            event_tracker = EventTracker(self.db, self.config)
            analytics_data = {
                'customer_id': failure.customer_id,
                'event_type': 'payment_recovery_success',
                'amount': failure.amount,
                'currency': failure.currency,
                'failure_reason': failure.failure_reason
            }
            
            event_tracker.track_payment_recovery_success(analytics_data)
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
    
    def _handle_payment_retry_failure(self, failure: PaymentFailure, payment_intent, error_message: str = None):
        """Handle payment retry failure"""
        try:
            # Update failure record
            failure_record = self._get_payment_failure_record(failure.failure_id)
            if failure_record:
                failure_record.retry_count += 1
                failure_record.last_error = error_message
                
                # Calculate next retry time
                if failure_record.retry_count < len(self.recovery_config['retry_intervals_days']):
                    next_retry_days = self.recovery_config['retry_intervals_days'][failure_record.retry_count]
                    failure_record.next_retry_at = datetime.now(timezone.utc) + timedelta(days=next_retry_days)
                
                self.db.commit()
            
            # Track analytics event
            event_tracker = EventTracker(self.db, self.config)
            analytics_data = {
                'customer_id': failure.customer_id,
                'event_type': 'payment_retry_failure',
                'retry_count': failure_record.retry_count if failure_record else 0,
                'error_message': error_message
            }
            
            event_tracker.track_payment_retry_failure(analytics_data)
            
        except Exception as e:
            logger.error(f"Error handling payment retry failure: {e}")
    
    def _update_customer_payment_status(self, customer_id: str, status: str):
        """Update customer payment status"""
        try:
            customer = self._get_customer(customer_id)
            if customer:
                customer.payment_status = status
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error updating customer payment status: {e}")
    
    def _get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            return self.db.query(Customer).filter(Customer.id == customer_id).first()
        except Exception as e:
            logger.error(f"Error getting customer: {e}")
            return None
    
    def _get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        try:
            return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return None
    
    def _get_payment_failure(self, failure_id: str) -> Optional[PaymentFailure]:
        """Get payment failure by ID"""
        try:
            # This would query the database
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting payment failure: {e}")
            return None
    
    def _get_payment_failure_record(self, failure_id: str) -> Optional[PaymentRecoveryRecord]:
        """Get payment failure record by ID"""
        try:
            return self.db.query(PaymentRecoveryRecord).filter(PaymentRecoveryRecord.id == failure_id).first()
        except Exception as e:
            logger.error(f"Error getting payment failure record: {e}")
            return None
    
    def _get_default_payment_method(self, stripe_customer_id: str) -> Optional[str]:
        """Get default payment method for customer"""
        try:
            customer = self.stripe.Customer.retrieve(stripe_customer_id)
            return customer.invoice_settings.default_payment_method
        except Exception as e:
            logger.error(f"Error getting default payment method: {e}")
            return None
    
    def _get_customer_subscriptions(self, customer_id: str) -> List[Subscription]:
        """Get customer subscriptions"""
        try:
            return self.db.query(Subscription).filter(Subscription.customer_id == customer_id).all()
        except Exception as e:
            logger.error(f"Error getting customer subscriptions: {e}")
            return []
    
    def _get_failed_payments_for_customer(self, customer_id: str) -> List[PaymentFailure]:
        """Get failed payments for customer"""
        try:
            # This would query the database
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting failed payments: {e}")
            return []
    
    def _store_recovery_action(self, action: RecoveryAction):
        """Store recovery action in database"""
        try:
            # This would store the action in database
            pass
        except Exception as e:
            logger.error(f"Error storing recovery action: {e}")
    
    def _schedule_recovery_action(self, action: RecoveryAction):
        """Schedule recovery action"""
        try:
            # This would schedule the action (e.g., using Celery, cron, etc.)
            pass
        except Exception as e:
            logger.error(f"Error scheduling recovery action: {e}")
    
    def _update_recovery_action(self, action_id: str, result: Dict[str, Any]):
        """Update recovery action with result"""
        try:
            # This would update the action in database
            pass
        except Exception as e:
            logger.error(f"Error updating recovery action: {e}")
    
    def _get_failure_count(self, start_date: datetime) -> int:
        """Get failure count since start date"""
        try:
            return self.db.query(PaymentRecoveryRecord).filter(
                PaymentRecoveryRecord.failed_at >= start_date
            ).count()
        except Exception as e:
            logger.error(f"Error getting failure count: {e}")
            return 0
    
    def _get_successful_recovery_count(self, start_date: datetime) -> int:
        """Get successful recovery count since start date"""
        try:
            return self.db.query(PaymentRecoveryRecord).filter(
                PaymentRecoveryRecord.failed_at >= start_date,
                PaymentRecoveryRecord.status == 'recovered'
            ).count()
        except Exception as e:
            logger.error(f"Error getting successful recovery count: {e}")
            return 0
    
    def _get_failed_recovery_count(self, start_date: datetime) -> int:
        """Get failed recovery count since start date"""
        try:
            return self.db.query(PaymentRecoveryRecord).filter(
                PaymentRecoveryRecord.failed_at >= start_date,
                PaymentRecoveryRecord.status == 'cancelled'
            ).count()
        except Exception as e:
            logger.error(f"Error getting failed recovery count: {e}")
            return 0
    
    def _get_total_revenue_at_risk(self, start_date: datetime) -> float:
        """Get total revenue at risk since start date"""
        try:
            result = self.db.query(PaymentRecoveryRecord.amount).filter(
                PaymentRecoveryRecord.failed_at >= start_date,
                PaymentRecoveryRecord.status.in_(['pending', 'retrying'])
            ).all()
            
            return sum(row[0] for row in result) if result else 0.0
            
        except Exception as e:
            logger.error(f"Error getting total revenue at risk: {e}")
            return 0.0
    
    def _get_recovered_revenue(self, start_date: datetime) -> float:
        """Get recovered revenue since start date"""
        try:
            result = self.db.query(PaymentRecoveryRecord.amount).filter(
                PaymentRecoveryRecord.failed_at >= start_date,
                PaymentRecoveryRecord.status == 'recovered'
            ).all()
            
            return sum(row[0] for row in result) if result else 0.0
            
        except Exception as e:
            logger.error(f"Error getting recovered revenue: {e}")
            return 0.0
    
    def _get_failure_reasons_breakdown(self, start_date: datetime) -> Dict[str, int]:
        """Get failure reasons breakdown"""
        try:
            result = self.db.query(
                PaymentRecoveryRecord.failure_reason,
                PaymentRecoveryRecord.amount
            ).filter(
                PaymentRecoveryRecord.failed_at >= start_date
            ).all()
            
            breakdown = {}
            for reason, amount in result:
                if reason in breakdown:
                    breakdown[reason] += 1
                else:
                    breakdown[reason] = 1
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error getting failure reasons breakdown: {e}")
            return {}
    
    def _get_strategy_effectiveness(self, start_date: datetime) -> Dict[str, float]:
        """Get recovery strategy effectiveness"""
        try:
            # This would analyze strategy effectiveness
            # For now, return placeholder data
            return {
                'automatic_retry': 0.75,
                'payment_method_update': 0.60,
                'grace_period': 0.45,
                'manual_intervention': 0.85
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy effectiveness: {e}")
            return {}
    
    def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        try:
            self.performance_metrics['recovery_attempts'] += 1
            
            if success:
                self.performance_metrics['successful_recoveries'] += 1
            else:
                self.performance_metrics['failed_recoveries'] += 1
            
            # Update recovery rate
            total_attempts = self.performance_metrics['recovery_attempts']
            successful = self.performance_metrics['successful_recoveries']
            
            if total_attempts > 0:
                self.performance_metrics['recovery_rate'] = (successful / total_attempts) * 100
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _is_temporary_failure(self, failure_reason: str, failure_code: str) -> bool:
        """Check if failure is temporary and suitable for immediate retry"""
        try:
            # Define temporary failure patterns
            temporary_failure_patterns = {
                'reasons': [
                    'insufficient_funds',
                    'processing_error',
                    'temporary_error',
                    'network_error',
                    'timeout_error',
                    'rate_limit_exceeded',
                    'service_unavailable'
                ],
                'codes': [
                    'insufficient_funds',
                    'processing_error',
                    'temporary_error',
                    'network_error',
                    'timeout',
                    'rate_limit',
                    'service_unavailable',
                    'card_declined_insufficient_funds',
                    'card_declined_processing_error'
                ]
            }
            
            # Check if failure reason matches temporary patterns
            failure_reason_lower = failure_reason.lower()
            failure_code_lower = failure_code.lower()
            
            # Check reason patterns
            for pattern in temporary_failure_patterns['reasons']:
                if pattern in failure_reason_lower:
                    logger.info(f"Temporary failure detected by reason: {failure_reason}")
                    return True
            
            # Check code patterns
            for pattern in temporary_failure_patterns['codes']:
                if pattern in failure_code_lower:
                    logger.info(f"Temporary failure detected by code: {failure_code}")
                    return True
            
            # Additional checks for specific scenarios
            if self._is_insufficient_funds_scenario(failure_reason, failure_code):
                logger.info(f"Insufficient funds scenario detected: {failure_reason}")
                return True
            
            logger.info(f"Failure classified as non-temporary: {failure_reason} ({failure_code})")
            return False
            
        except Exception as e:
            logger.error(f"Error checking temporary failure: {e}")
            return False
    
    def _is_insufficient_funds_scenario(self, failure_reason: str, failure_code: str) -> bool:
        """Check if this is an insufficient funds scenario suitable for immediate retry"""
        try:
            insufficient_funds_indicators = [
                'insufficient_funds',
                'insufficient_funds_in_account',
                'account_has_insufficient_funds',
                'card_declined_insufficient_funds',
                'insufficient_funds_for_payment',
                'not_enough_funds',
                'low_balance',
                'insufficient_balance'
            ]
            
            failure_reason_lower = failure_reason.lower()
            failure_code_lower = failure_code.lower()
            
            for indicator in insufficient_funds_indicators:
                if indicator in failure_reason_lower or indicator in failure_code_lower:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking insufficient funds scenario: {e}")
            return False
    
    def _execute_immediate_retry_workflow(self, failure: PaymentFailure) -> Dict[str, Any]:
        """Execute immediate retry workflow for temporary failures"""
        try:
            logger.info(f"Executing immediate retry workflow for failure {failure.failure_id}")
            
            # Get customer and subscription information
            customer = self._get_customer(failure.customer_id)
            subscription = self._get_subscription(failure.subscription_id)
            
            if not customer or not subscription:
                return {
                    'success': False,
                    'error': 'Customer or subscription not found',
                    'retry_attempts': 0
                }
            
            # Configure immediate retry strategy
            retry_config = self._get_immediate_retry_config(failure)
            
            # Execute immediate retry attempts
            retry_results = []
            max_immediate_retries = retry_config.get('max_immediate_retries', 3)
            retry_delay_seconds = retry_config.get('retry_delay_seconds', 30)
            
            for attempt in range(max_immediate_retries):
                try:
                    logger.info(f"Immediate retry attempt {attempt + 1}/{max_immediate_retries}")
                    
                    # Wait between retries (except for first attempt)
                    if attempt > 0:
                        time.sleep(retry_delay_seconds)
                    
                    # Attempt payment retry
                    retry_result = self._attempt_immediate_payment_retry(failure, customer, attempt + 1)
                    retry_results.append(retry_result)
                    
                    # Check if retry was successful
                    if retry_result['success']:
                        logger.info(f"Immediate retry successful on attempt {attempt + 1}")
                        
                        # Handle successful payment
                        self._handle_immediate_retry_success(failure, retry_result)
                        
                        return {
                            'success': True,
                            'retry_attempts': attempt + 1,
                            'payment_intent_id': retry_result.get('payment_intent_id'),
                            'retry_results': retry_results,
                            'recovery_method': 'immediate_retry'
                        }
                    
                    # If retry failed, check if we should continue
                    if not retry_result.get('should_retry', True):
                        logger.info(f"Stopping immediate retries: {retry_result.get('reason', 'Unknown')}")
                        break
                    
                except Exception as e:
                    logger.error(f"Error during immediate retry attempt {attempt + 1}: {e}")
                    retry_results.append({
                        'success': False,
                        'error': str(e),
                        'attempt': attempt + 1
                    })
            
            # All immediate retries failed
            logger.info(f"All immediate retry attempts failed for failure {failure.failure_id}")
            
            # Update failure record with retry information
            self._update_failure_with_retry_info(failure, retry_results)
            
            return {
                'success': False,
                'retry_attempts': len(retry_results),
                'retry_results': retry_results,
                'error': 'All immediate retry attempts failed',
                'recovery_method': 'immediate_retry_failed'
            }
            
        except Exception as e:
            logger.error(f"Error executing immediate retry workflow: {e}")
            return {
                'success': False,
                'error': str(e),
                'retry_attempts': 0
            }
    
    def _get_immediate_retry_config(self, failure: PaymentFailure) -> Dict[str, Any]:
        """Get configuration for immediate retry based on failure type"""
        try:
            # Base configuration
            base_config = {
                'max_immediate_retries': 3,
                'retry_delay_seconds': 30,
                'amount_adjustment': False,
                'payment_method_rotation': False
            }
            
            # Configuration by failure type
            failure_type_configs = {
                'insufficient_funds': {
                    'max_immediate_retries': 2,
                    'retry_delay_seconds': 60,  # Longer delay for insufficient funds
                    'amount_adjustment': True,
                    'payment_method_rotation': False
                },
                'processing_error': {
                    'max_immediate_retries': 3,
                    'retry_delay_seconds': 30,
                    'amount_adjustment': False,
                    'payment_method_rotation': False
                },
                'network_error': {
                    'max_immediate_retries': 3,
                    'retry_delay_seconds': 15,
                    'amount_adjustment': False,
                    'payment_method_rotation': False
                },
                'timeout_error': {
                    'max_immediate_retries': 2,
                    'retry_delay_seconds': 45,
                    'amount_adjustment': False,
                    'payment_method_rotation': False
                }
            }
            
            # Determine failure type
            failure_type = self._categorize_failure_reason(failure.failure_reason)
            
            # Get specific configuration
            specific_config = failure_type_configs.get(failure_type, {})
            
            # Merge configurations
            config = {**base_config, **specific_config}
            
            # Adjust based on customer value
            customer = self._get_customer(failure.customer_id)
            if customer and self._is_high_value_customer(customer):
                config['max_immediate_retries'] = min(config['max_immediate_retries'] + 1, 5)
                config['retry_delay_seconds'] = max(config['retry_delay_seconds'] - 10, 10)
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting immediate retry config: {e}")
            return {
                'max_immediate_retries': 3,
                'retry_delay_seconds': 30,
                'amount_adjustment': False,
                'payment_method_rotation': False
            }
    
    def _attempt_immediate_payment_retry(
        self,
        failure: PaymentFailure,
        customer: Customer,
        attempt_number: int
    ) -> Dict[str, Any]:
        """Attempt immediate payment retry"""
        try:
            # Get payment method
            payment_method = self._get_default_payment_method(customer.stripe_customer_id)
            if not payment_method:
                return {
                    'success': False,
                    'error': 'No payment method available',
                    'should_retry': False,
                    'reason': 'no_payment_method'
                }
            
            # Determine retry amount (may be adjusted for insufficient funds)
            retry_amount = self._calculate_retry_amount(failure, attempt_number)
            
            # Create new payment intent
            try:
                payment_intent = self.stripe.PaymentIntent.create(
                    amount=int(retry_amount * 100),  # Convert to cents
                    currency=failure.currency,
                    customer=customer.stripe_customer_id,
                    payment_method=payment_method,
                    confirm=True,
                    off_session=True,
                    metadata={
                        'failure_id': failure.failure_id,
                        'retry_attempt': attempt_number,
                        'original_amount': failure.amount,
                        'retry_amount': retry_amount,
                        'subscription_id': failure.subscription_id,
                        'retry_type': 'immediate'
                    }
                )
                
                # Check payment intent status
                if payment_intent.status == 'succeeded':
                    return {
                        'success': True,
                        'payment_intent_id': payment_intent.id,
                        'amount': retry_amount,
                        'status': payment_intent.status
                    }
                else:
                    # Payment failed
                    error_message = payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed'
                    error_code = payment_intent.last_payment_error.code if payment_intent.last_payment_error else 'unknown'
                    
                    # Determine if we should retry
                    should_retry = self._should_retry_immediate(error_code, error_message, attempt_number)
                    
                    return {
                        'success': False,
                        'payment_intent_id': payment_intent.id,
                        'error': error_message,
                        'error_code': error_code,
                        'should_retry': should_retry,
                        'reason': 'payment_failed'
                    }
                    
            except stripe.error.CardError as e:
                # Handle card errors
                should_retry = self._should_retry_immediate(e.code, e.message, attempt_number)
                
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': e.code,
                    'should_retry': should_retry,
                    'reason': 'card_error'
                }
                
            except stripe.error.StripeError as e:
                # Handle other Stripe errors
                should_retry = self._should_retry_immediate('stripe_error', str(e), attempt_number)
                
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': 'stripe_error',
                    'should_retry': should_retry,
                    'reason': 'stripe_error'
                }
                
        except Exception as e:
            logger.error(f"Error attempting immediate payment retry: {e}")
            return {
                'success': False,
                'error': str(e),
                'should_retry': False,
                'reason': 'system_error'
            }
    
    def _calculate_retry_amount(self, failure: PaymentFailure, attempt_number: int) -> float:
        """Calculate retry amount (may be adjusted for insufficient funds)"""
        try:
            # For insufficient funds, try with reduced amount
            if self._is_insufficient_funds_scenario(failure.failure_reason, failure.failure_code):
                # Reduce amount by 10% for each retry attempt
                reduction_factor = 1.0 - (0.1 * attempt_number)
                adjusted_amount = failure.amount * reduction_factor
                
                # Ensure minimum amount
                min_amount = max(failure.amount * 0.5, 1.0)  # At least 50% of original or $1
                return max(adjusted_amount, min_amount)
            
            # For other temporary failures, use original amount
            return failure.amount
            
        except Exception as e:
            logger.error(f"Error calculating retry amount: {e}")
            return failure.amount
    
    def _should_retry_immediate(self, error_code: str, error_message: str, attempt_number: int) -> bool:
        """Determine if immediate retry should continue based on error"""
        try:
            # Never retry for these error types
            non_retryable_errors = [
                'card_declined',
                'expired_card',
                'incorrect_cvc',
                'fraudulent',
                'authentication_required',
                'card_not_supported'
            ]
            
            # Check if error is non-retryable
            for non_retryable in non_retryable_errors:
                if non_retryable in error_code.lower() or non_retryable in error_message.lower():
                    return False
            
            # For insufficient funds, limit retries
            if 'insufficient_funds' in error_code.lower() or 'insufficient_funds' in error_message.lower():
                return attempt_number < 2  # Only retry once for insufficient funds
            
            # For processing errors, allow more retries
            if 'processing_error' in error_code.lower() or 'processing_error' in error_message.lower():
                return attempt_number < 3
            
            # Default: allow retry for temporary errors
            return attempt_number < 3
            
        except Exception as e:
            logger.error(f"Error determining retry decision: {e}")
            return False
    
    def _handle_immediate_retry_success(self, failure: PaymentFailure, retry_result: Dict[str, Any]):
        """Handle successful immediate retry"""
        try:
            # Update failure record
            failure_record = self._get_payment_failure_record(failure.failure_id)
            if failure_record:
                failure_record.status = RecoveryStatus.RECOVERED
                failure_record.recovered_at = datetime.now(timezone.utc)
                failure_record.payment_intent_id = retry_result.get('payment_intent_id')
                failure_record.metadata = {
                    **failure_record.metadata or {},
                    'recovery_method': 'immediate_retry',
                    'retry_attempts': retry_result.get('retry_attempts', 1),
                    'retry_amount': retry_result.get('amount', failure.amount)
                }
                
                self.db.commit()
            
            # Send success notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure.customer_id,
                'amount': retry_result.get('amount', failure.amount),
                'currency': failure.currency,
                'payment_intent_id': retry_result.get('payment_intent_id'),
                'recovery_method': 'immediate_retry'
            }
            
            notification_service.send_payment_recovery_success_notifications(notification_data)
            
            # Track analytics event
            event_tracker = EventTracker(self.db, self.config)
            analytics_data = {
                'customer_id': failure.customer_id,
                'event_type': 'immediate_retry_success',
                'amount': retry_result.get('amount', failure.amount),
                'currency': failure.currency,
                'retry_attempts': retry_result.get('retry_attempts', 1),
                'failure_reason': failure.failure_reason
            }
            
            event_tracker.track_immediate_retry_success(analytics_data)
            
            logger.info(f"Immediate retry successful for failure {failure.failure_id}")
            
        except Exception as e:
            logger.error(f"Error handling immediate retry success: {e}")
    
    def _update_failure_with_retry_info(self, failure: PaymentFailure, retry_results: List[Dict[str, Any]]):
        """Update failure record with retry information"""
        try:
            failure_record = self._get_payment_failure_record(failure.failure_id)
            if failure_record:
                failure_record.retry_count = len(retry_results)
                failure_record.last_error = retry_results[-1].get('error') if retry_results else None
                failure_record.last_error_at = datetime.now(timezone.utc)
                failure_record.metadata = {
                    **failure_record.metadata or {},
                    'immediate_retry_attempts': len(retry_results),
                    'immediate_retry_results': retry_results,
                    'immediate_retry_failed': True
                }
                
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error updating failure with retry info: {e}")
    
    def schedule_smart_retry_workflow(self, failure_id: str) -> Dict[str, Any]:
        """Schedule smart retry workflow with Day 1, Day 3, Day 7 intervals"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Get customer and subscription
            customer = self._get_customer(failure_record.customer_id)
            subscription = self._get_subscription(failure_record.subscription_id)
            
            if not customer or not subscription:
                return {'success': False, 'error': 'Customer or subscription not found'}
            
            # Create smart retry schedule
            smart_retry_schedule = self._create_smart_retry_schedule(failure_record)
            
            # Schedule retry actions
            scheduled_actions = []
            for retry_day in self.recovery_config['smart_retry_intervals_days']:
                retry_date = failure_record.failed_at + timedelta(days=retry_day)
                
                # Create retry action
                retry_action = RecoveryAction(
                    action_id=str(uuid.uuid4()),
                    recovery_record_id=failure_id,
                    action_type='smart_retry',
                    strategy=RecoveryStrategy.AUTOMATIC_RETRY,
                    dunning_stage=DunningStage.DUNNING_1 if retry_day == 1 else DunningStage.DUNNING_2 if retry_day == 3 else DunningStage.DUNNING_3,
                    scheduled_at=retry_date,
                    status=ActionStatus.SCHEDULED,
                    metadata={
                        'retry_day': retry_day,
                        'retry_attempt': retry_day,
                        'smart_retry': True,
                        'original_amount': failure_record.amount,
                        'failure_reason': failure_record.failure_reason
                    }
                )
                
                # Store retry action
                self._store_recovery_action(retry_action)
                scheduled_actions.append(retry_action)
                
                # Schedule payment method update prompt if enabled
                if self.recovery_config['payment_method_update_prompts']['enabled']:
                    self._schedule_payment_method_update_prompt(failure_record, retry_day, retry_date)
            
            # Update failure record
            failure_record.metadata = {
                **failure_record.metadata or {},
                'smart_retry_scheduled': True,
                'smart_retry_days': self.recovery_config['smart_retry_intervals_days'],
                'scheduled_actions_count': len(scheduled_actions)
            }
            self.db.commit()
            
            return {
                'success': True,
                'failure_id': failure_id,
                'scheduled_actions': len(scheduled_actions),
                'retry_days': self.recovery_config['smart_retry_intervals_days'],
                'next_retry_date': (failure_record.failed_at + timedelta(days=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling smart retry workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_smart_retry_schedule(self, failure_record: PaymentRecoveryRecord) -> Dict[str, Any]:
        """Create smart retry schedule based on failure characteristics"""
        try:
            # Base schedule
            schedule = {
                'retry_days': self.recovery_config['smart_retry_intervals_days'],
                'amount_adjustment': False,
                'payment_method_update_prompts': True,
                'notification_intensity': 'medium'
            }
            
            # Adjust schedule based on failure type
            failure_type = self._categorize_failure_reason(failure_record.failure_reason)
            
            if failure_type == 'insufficient_funds':
                schedule['amount_adjustment'] = True
                schedule['notification_intensity'] = 'high'
            elif failure_type == 'expired_card':
                schedule['payment_method_update_prompts'] = True
                schedule['notification_intensity'] = 'high'
            elif failure_type == 'processing_error':
                schedule['notification_intensity'] = 'low'
            
            # Adjust based on customer value
            customer = self._get_customer(failure_record.customer_id)
            if customer and self._is_high_value_customer(customer):
                schedule['notification_intensity'] = 'high'
                schedule['payment_method_update_prompts'] = True
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating smart retry schedule: {e}")
            return {
                'retry_days': self.recovery_config['smart_retry_intervals_days'],
                'amount_adjustment': False,
                'payment_method_update_prompts': True,
                'notification_intensity': 'medium'
            }
    
    def _schedule_payment_method_update_prompt(
        self,
        failure_record: PaymentRecoveryRecord,
        retry_day: int,
        retry_date: datetime
    ):
        """Schedule payment method update prompt"""
        try:
            # Check if we should prompt for payment method update
            if retry_day not in self.recovery_config['payment_method_update_prompts']['prompt_days']:
                return
            
            # Check prompt limits
            existing_prompts = self._get_payment_method_update_prompts(failure_record.id)
            if len(existing_prompts) >= self.recovery_config['payment_method_update_prompts']['max_prompts']:
                return
            
            # Create payment method update prompt action
            prompt_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                recovery_record_id=failure_record.id,
                action_type='payment_method_update_prompt',
                strategy=RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                dunning_stage=DunningStage.DUNNING_1 if retry_day == 1 else DunningStage.DUNNING_2 if retry_day == 3 else DunningStage.DUNNING_3,
                scheduled_at=retry_date,
                status=ActionStatus.SCHEDULED,
                metadata={
                    'prompt_day': retry_day,
                    'prompt_number': len(existing_prompts) + 1,
                    'channels': self.recovery_config['payment_method_update_prompts']['prompt_channels'],
                    'failure_reason': failure_record.failure_reason
                }
            )
            
            # Store prompt action
            self._store_recovery_action(prompt_action)
            
            logger.info(f"Scheduled payment method update prompt for day {retry_day} for failure {failure_record.id}")
            
        except Exception as e:
            logger.error(f"Error scheduling payment method update prompt: {e}")
    
    def execute_smart_retry(self, failure_id: str, retry_day: int) -> Dict[str, Any]:
        """Execute smart retry for specific day"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Get customer
            customer = self._get_customer(failure_record.customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Calculate retry amount based on day
            retry_amount = self._calculate_smart_retry_amount(failure_record, retry_day)
            
            # Attempt payment retry
            retry_result = self._attempt_smart_payment_retry(failure_record, customer, retry_day, retry_amount)
            
            # Update failure record
            failure_record.retry_count += 1
            failure_record.last_error = retry_result.get('error')
            failure_record.last_error_at = datetime.now(timezone.utc)
            
            if retry_result['success']:
                failure_record.status = RecoveryStatus.RECOVERED
                failure_record.recovered_at = datetime.now(timezone.utc)
                failure_record.payment_intent_id = retry_result.get('payment_intent_id')
            
            failure_record.metadata = {
                **failure_record.metadata or {},
                'smart_retry_day': retry_day,
                'smart_retry_amount': retry_amount,
                'smart_retry_success': retry_result['success'],
                'smart_retry_result': retry_result
            }
            
            self.db.commit()
            
            # Handle success or failure
            if retry_result['success']:
                self._handle_smart_retry_success(failure_record, retry_result)
            else:
                self._handle_smart_retry_failure(failure_record, retry_result)
            
            return retry_result
            
        except Exception as e:
            logger.error(f"Error executing smart retry: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_smart_retry_amount(self, failure_record: PaymentRecoveryRecord, retry_day: int) -> float:
        """Calculate retry amount for smart retry based on day"""
        try:
            original_amount = failure_record.amount
            
            # Get smart retry schedule
            schedule = self._create_smart_retry_schedule(failure_record)
            
            # Apply amount adjustment if enabled
            if schedule.get('amount_adjustment', False):
                # Progressive amount reduction based on retry day
                if retry_day == 1:
                    # Day 1: 90% of original amount
                    return original_amount * 0.9
                elif retry_day == 3:
                    # Day 3: 80% of original amount
                    return original_amount * 0.8
                elif retry_day == 7:
                    # Day 7: 70% of original amount
                    return original_amount * 0.7
            
            # For non-adjustment scenarios, use original amount
            return original_amount
            
        except Exception as e:
            logger.error(f"Error calculating smart retry amount: {e}")
            return failure_record.amount
    
    def _attempt_smart_payment_retry(
        self,
        failure_record: PaymentRecoveryRecord,
        customer: Customer,
        retry_day: int,
        retry_amount: float
    ) -> Dict[str, Any]:
        """Attempt smart payment retry"""
        try:
            # Get payment method
            payment_method = self._get_default_payment_method(customer.stripe_customer_id)
            if not payment_method:
                return {
                    'success': False,
                    'error': 'No payment method available',
                    'should_retry': False,
                    'reason': 'no_payment_method'
                }
            
            # Create new payment intent
            try:
                payment_intent = self.stripe.PaymentIntent.create(
                    amount=int(retry_amount * 100),  # Convert to cents
                    currency=failure_record.currency,
                    customer=customer.stripe_customer_id,
                    payment_method=payment_method,
                    confirm=True,
                    off_session=True,
                    metadata={
                        'failure_id': failure_record.id,
                        'retry_day': retry_day,
                        'original_amount': failure_record.amount,
                        'retry_amount': retry_amount,
                        'subscription_id': failure_record.subscription_id,
                        'retry_type': 'smart_retry'
                    }
                )
                
                # Check payment intent status
                if payment_intent.status == 'succeeded':
                    return {
                        'success': True,
                        'payment_intent_id': payment_intent.id,
                        'amount': retry_amount,
                        'status': payment_intent.status,
                        'retry_day': retry_day
                    }
                else:
                    # Payment failed
                    error_message = payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed'
                    error_code = payment_intent.last_payment_error.code if payment_intent.last_payment_error else 'unknown'
                    
                    return {
                        'success': False,
                        'payment_intent_id': payment_intent.id,
                        'error': error_message,
                        'error_code': error_code,
                        'retry_day': retry_day
                    }
                    
            except stripe.error.CardError as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': e.code,
                    'retry_day': retry_day
                }
                
            except stripe.error.StripeError as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': 'stripe_error',
                    'retry_day': retry_day
                }
                
        except Exception as e:
            logger.error(f"Error attempting smart payment retry: {e}")
            return {
                'success': False,
                'error': str(e),
                'retry_day': retry_day
            }
    
    def _handle_smart_retry_success(self, failure_record: PaymentRecoveryRecord, retry_result: Dict[str, Any]):
        """Handle successful smart retry"""
        try:
            # Send success notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure_record.customer_id,
                'amount': retry_result.get('amount', failure_record.amount),
                'currency': failure_record.currency,
                'payment_intent_id': retry_result.get('payment_intent_id'),
                'recovery_method': 'smart_retry',
                'retry_day': retry_result.get('retry_day')
            }
            
            notification_service.send_payment_recovery_success_notifications(notification_data)
            
            # Track analytics event
            event_tracker = EventTracker(self.db, self.config)
            analytics_data = {
                'customer_id': failure_record.customer_id,
                'event_type': 'smart_retry_success',
                'amount': retry_result.get('amount', failure_record.amount),
                'currency': failure_record.currency,
                'retry_day': retry_result.get('retry_day'),
                'failure_reason': failure_record.failure_reason
            }
            
            event_tracker.track_smart_retry_success(analytics_data)
            
            # Update customer status
            self._update_customer_payment_status(failure_record.customer_id, 'active')
            
            logger.info(f"Smart retry successful for failure {failure_record.id} on day {retry_result.get('retry_day')}")
            
        except Exception as e:
            logger.error(f"Error handling smart retry success: {e}")
    
    def _handle_smart_retry_failure(self, failure_record: PaymentRecoveryRecord, retry_result: Dict[str, Any]):
        """Handle failed smart retry"""
        try:
            # Send failure notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure_record.customer_id,
                'amount': retry_result.get('amount', failure_record.amount),
                'currency': failure_record.currency,
                'retry_day': retry_result.get('retry_day'),
                'error_message': retry_result.get('error'),
                'recovery_method': 'smart_retry'
            }
            
            notification_service.send_payment_retry_failure_notifications(notification_data)
            
            # Track analytics event
            event_tracker = EventTracker(self.db, self.config)
            analytics_data = {
                'customer_id': failure_record.customer_id,
                'event_type': 'smart_retry_failure',
                'amount': retry_result.get('amount', failure_record.amount),
                'currency': failure_record.currency,
                'retry_day': retry_result.get('retry_day'),
                'error_message': retry_result.get('error'),
                'failure_reason': failure_record.failure_reason
            }
            
            event_tracker.track_smart_retry_failure(analytics_data)
            
            logger.info(f"Smart retry failed for failure {failure_record.id} on day {retry_result.get('retry_day')}")
            
        except Exception as e:
            logger.error(f"Error handling smart retry failure: {e}")
    
    def send_payment_method_update_prompt(self, failure_id: str, prompt_day: int) -> Dict[str, Any]:
        """Send payment method update prompt"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Get customer
            customer = self._get_customer(failure_record.customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Check if prompt should be sent
            if prompt_day not in self.recovery_config['payment_method_update_prompts']['prompt_days']:
                return {'success': False, 'error': f'Prompt not scheduled for day {prompt_day}'}
            
            # Get existing prompts
            existing_prompts = self._get_payment_method_update_prompts(failure_record.id)
            if len(existing_prompts) >= self.recovery_config['payment_method_update_prompts']['max_prompts']:
                return {'success': False, 'error': 'Maximum prompts reached'}
            
            # Send payment method update notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure_record.customer_id,
                'prompt_day': prompt_day,
                'prompt_number': len(existing_prompts) + 1,
                'failure_reason': failure_record.failure_reason,
                'amount': failure_record.amount,
                'currency': failure_record.currency,
                'channels': self.recovery_config['payment_method_update_prompts']['prompt_channels']
            }
            
            result = notification_service.send_payment_method_update_prompts(notification_data)
            
            # Record prompt
            self._record_payment_method_update_prompt(failure_record, prompt_day, result)
            
            return {
                'success': True,
                'prompt_sent': result.get('notifications_sent', 0),
                'channels': result.get('channels', []),
                'prompt_day': prompt_day,
                'prompt_number': len(existing_prompts) + 1
            }
            
        except Exception as e:
            logger.error(f"Error sending payment method update prompt: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_payment_method_update_prompts(self, failure_id: str) -> List[Dict[str, Any]]:
        """Get payment method update prompts for a failure"""
        try:
            # This would query the database for existing prompts
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting payment method update prompts: {e}")
            return []
    
    def _record_payment_method_update_prompt(
        self,
        failure_record: PaymentRecoveryRecord,
        prompt_day: int,
        result: Dict[str, Any]
    ):
        """Record payment method update prompt"""
        try:
            # Create prompt record
            prompt_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                recovery_record_id=failure_record.id,
                action_type='payment_method_update_prompt_sent',
                strategy=RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                scheduled_at=datetime.now(timezone.utc),
                executed_at=datetime.now(timezone.utc),
                status=ActionStatus.COMPLETED,
                success=result.get('success', False),
                metadata={
                    'prompt_day': prompt_day,
                    'notifications_sent': result.get('notifications_sent', 0),
                    'channels': result.get('channels', []),
                    'failure_reason': failure_record.failure_reason
                }
            )
            
            # Store prompt record
            self._store_recovery_action(prompt_action)
            
        except Exception as e:
            logger.error(f"Error recording payment method update prompt: {e}")
    
    def get_smart_retry_schedule(self, failure_id: str) -> Dict[str, Any]:
        """Get smart retry schedule for a failure"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Get scheduled actions
            scheduled_actions = self._get_scheduled_actions_for_failure(failure_id)
            
            # Build schedule
            schedule = {
                'failure_id': failure_id,
                'failed_at': failure_record.failed_at.isoformat(),
                'retry_days': self.recovery_config['smart_retry_intervals_days'],
                'scheduled_retries': [],
                'payment_method_prompts': [],
                'next_retry_date': None,
                'next_prompt_date': None
            }
            
            # Process scheduled actions
            for action in scheduled_actions:
                if action.action_type == 'smart_retry':
                    retry_day = action.metadata.get('retry_day')
                    schedule['scheduled_retries'].append({
                        'day': retry_day,
                        'scheduled_date': action.scheduled_at.isoformat(),
                        'status': action.status.value,
                        'amount': action.metadata.get('retry_amount', failure_record.amount)
                    })
                elif action.action_type == 'payment_method_update_prompt':
                    prompt_day = action.metadata.get('prompt_day')
                    schedule['payment_method_prompts'].append({
                        'day': prompt_day,
                        'scheduled_date': action.scheduled_at.isoformat(),
                        'status': action.status.value
                    })
            
            # Find next retry and prompt dates
            now = datetime.now(timezone.utc)
            for retry in schedule['scheduled_retries']:
                if retry['status'] == 'scheduled' and datetime.fromisoformat(retry['scheduled_date']) > now:
                    schedule['next_retry_date'] = retry['scheduled_date']
                    break
            
            for prompt in schedule['payment_method_prompts']:
                if prompt['status'] == 'scheduled' and datetime.fromisoformat(prompt['scheduled_date']) > now:
                    schedule['next_prompt_date'] = prompt['scheduled_date']
                    break
            
            return {
                'success': True,
                'schedule': schedule
            }
            
        except Exception as e:
            logger.error(f"Error getting smart retry schedule: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_scheduled_actions_for_failure(self, failure_id: str) -> List[RecoveryAction]:
        """Get scheduled actions for a failure"""
        try:
            # This would query the database for scheduled actions
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting scheduled actions: {e}")
            return []
    
    def suggest_alternative_payment_methods(self, failure_id: str, suggestion_day: int) -> Dict[str, Any]:
        """Suggest alternative payment methods to customer"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Get customer
            customer = self._get_customer(failure_record.customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Check if suggestions should be sent
            if suggestion_day not in self.recovery_config['alternative_payment_methods']['suggestion_days']:
                return {'success': False, 'error': f'Suggestion not scheduled for day {suggestion_day}'}
            
            # Get existing suggestions
            existing_suggestions = self._get_alternative_payment_suggestions(failure_record.id)
            if len(existing_suggestions) >= self.recovery_config['alternative_payment_methods']['max_suggestions']:
                return {'success': False, 'error': 'Maximum suggestions reached'}
            
            # Generate personalized suggestions
            suggestions = self._generate_payment_method_suggestions(failure_record, customer, suggestion_day)
            
            # Send suggestions notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure_record.customer_id,
                'suggestion_day': suggestion_day,
                'suggestion_number': len(existing_suggestions) + 1,
                'suggestions': suggestions,
                'failure_reason': failure_record.failure_reason,
                'amount': failure_record.amount,
                'currency': failure_record.currency,
                'channels': self.recovery_config['notification_channels']
            }
            
            result = notification_service.send_alternative_payment_suggestions(notification_data)
            
            # Record suggestion
            self._record_alternative_payment_suggestion(failure_record, suggestion_day, suggestions, result)
            
            return {
                'success': True,
                'suggestions_sent': result.get('notifications_sent', 0),
                'suggestions': suggestions,
                'suggestion_day': suggestion_day,
                'suggestion_number': len(existing_suggestions) + 1
            }
            
        except Exception as e:
            logger.error(f"Error suggesting alternative payment methods: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_payment_method_suggestions(
        self,
        failure_record: PaymentRecoveryRecord,
        customer: Customer,
        suggestion_day: int
    ) -> List[Dict[str, Any]]:
        """Generate personalized payment method suggestions"""
        try:
            suggestions = []
            available_methods = self.recovery_config['alternative_payment_methods']['suggestions']
            
            # Get current payment method
            current_method = self._get_current_payment_method(customer.stripe_customer_id)
            
            # Filter out current method
            available_methods = [method for method in available_methods if method != current_method]
            
            # Prioritize suggestions based on failure reason and customer profile
            prioritized_methods = self._prioritize_payment_methods(
                available_methods, failure_record.failure_reason, customer, suggestion_day
            )
            
            # Generate suggestion details
            for method in prioritized_methods[:3]:  # Top 3 suggestions
                suggestion = {
                    'method': method,
                    'name': self._get_payment_method_name(method),
                    'description': self._get_payment_method_description(method),
                    'benefits': self._get_payment_method_benefits(method, failure_record.failure_reason),
                    'setup_instructions': self._get_payment_method_setup_instructions(method),
                    'estimated_setup_time': self._get_payment_method_setup_time(method),
                    'success_rate': self._get_payment_method_success_rate(method),
                    'priority': prioritized_methods.index(method) + 1
                }
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating payment method suggestions: {e}")
            return []
    
    def _prioritize_payment_methods(
        self,
        available_methods: List[str],
        failure_reason: str,
        customer: Customer,
        suggestion_day: int
    ) -> List[str]:
        """Prioritize payment methods based on failure reason and customer profile"""
        try:
            # Define priority rules
            priority_rules = {
                'insufficient_funds': ['bank_transfer', 'installment_plan', 'digital_wallet'],
                'expired_card': ['credit_card', 'debit_card', 'digital_wallet'],
                'card_declined': ['bank_transfer', 'digital_wallet', 'gift_card'],
                'processing_error': ['credit_card', 'debit_card', 'bank_transfer'],
                'fraudulent': ['bank_transfer', 'crypto_payment', 'gift_card']
            }
            
            # Get priority for failure reason
            failure_priority = priority_rules.get(failure_reason, available_methods)
            
            # Adjust based on customer profile
            if self._is_high_value_customer(customer):
                # High-value customers get premium options first
                premium_methods = ['credit_card', 'bank_transfer', 'installment_plan']
                failure_priority = [m for m in premium_methods if m in failure_priority] + \
                                 [m for m in failure_priority if m not in premium_methods]
            
            # Adjust based on suggestion day
            if suggestion_day >= 5:
                # Later suggestions include more options
                alternative_methods = ['gift_card', 'crypto_payment', 'installment_plan']
                failure_priority.extend([m for m in alternative_methods if m not in failure_priority])
            
            # Filter to available methods
            prioritized = [m for m in failure_priority if m in available_methods]
            
            # Add any remaining methods
            remaining = [m for m in available_methods if m not in prioritized]
            prioritized.extend(remaining)
            
            return prioritized
            
        except Exception as e:
            logger.error(f"Error prioritizing payment methods: {e}")
            return available_methods
    
    def _get_payment_method_name(self, method: str) -> str:
        """Get display name for payment method"""
        names = {
            'credit_card': 'Credit Card',
            'debit_card': 'Debit Card',
            'bank_transfer': 'Bank Transfer',
            'digital_wallet': 'Digital Wallet',
            'crypto_payment': 'Cryptocurrency',
            'gift_card': 'Gift Card',
            'installment_plan': 'Installment Plan'
        }
        return names.get(method, method.title())
    
    def _get_payment_method_description(self, method: str) -> str:
        """Get description for payment method"""
        descriptions = {
            'credit_card': 'Secure credit card payment with fraud protection',
            'debit_card': 'Direct debit from your bank account',
            'bank_transfer': 'Direct bank transfer for secure payments',
            'digital_wallet': 'Pay with Apple Pay, Google Pay, or PayPal',
            'crypto_payment': 'Pay with Bitcoin, Ethereum, or other cryptocurrencies',
            'gift_card': 'Use a gift card or prepaid card',
            'installment_plan': 'Split your payment into manageable installments'
        }
        return descriptions.get(method, f'Pay using {method}')
    
    def _get_payment_method_benefits(self, method: str, failure_reason: str) -> List[str]:
        """Get benefits for payment method based on failure reason"""
        benefits = {
            'credit_card': ['Fraud protection', 'Rewards points', 'Easy to use'],
            'debit_card': ['No debt', 'Direct from account', 'Widely accepted'],
            'bank_transfer': ['No fees', 'Secure', 'Direct from account'],
            'digital_wallet': ['Fast checkout', 'Secure', 'Mobile-friendly'],
            'crypto_payment': ['No chargebacks', 'Global', 'Privacy-focused'],
            'gift_card': ['No bank account needed', 'Prepaid', 'Gift option'],
            'installment_plan': ['Flexible payments', 'No interest', 'Budget-friendly']
        }
        
        # Add specific benefits based on failure reason
        if failure_reason == 'insufficient_funds':
            benefits['installment_plan'].extend(['Lower monthly payments', 'Spread cost over time'])
            benefits['gift_card'].extend(['Use existing balance', 'No overdraft risk'])
        elif failure_reason == 'expired_card':
            benefits['bank_transfer'].extend(['No expiration', 'Always available'])
            benefits['digital_wallet'].extend(['Auto-updates', 'No card needed'])
        
        return benefits.get(method, ['Secure', 'Reliable', 'Fast'])
    
    def _get_payment_method_setup_instructions(self, method: str) -> str:
        """Get setup instructions for payment method"""
        instructions = {
            'credit_card': 'Enter your card details in the payment form',
            'debit_card': 'Enter your debit card information',
            'bank_transfer': 'Provide your bank account and routing numbers',
            'digital_wallet': 'Set up Apple Pay, Google Pay, or PayPal in your account',
            'crypto_payment': 'Connect your cryptocurrency wallet',
            'gift_card': 'Enter your gift card code during checkout',
            'installment_plan': 'Select installment option and provide payment details'
        }
        return instructions.get(method, 'Follow the setup instructions in your account')
    
    def _get_payment_method_setup_time(self, method: str) -> str:
        """Get estimated setup time for payment method"""
        setup_times = {
            'credit_card': '2-3 minutes',
            'debit_card': '2-3 minutes',
            'bank_transfer': '5-10 minutes',
            'digital_wallet': '1-2 minutes',
            'crypto_payment': '10-15 minutes',
            'gift_card': '1 minute',
            'installment_plan': '3-5 minutes'
        }
        return setup_times.get(method, '5 minutes')
    
    def _get_payment_method_success_rate(self, method: str) -> float:
        """Get success rate for payment method"""
        success_rates = {
            'credit_card': 0.95,
            'debit_card': 0.92,
            'bank_transfer': 0.98,
            'digital_wallet': 0.94,
            'crypto_payment': 0.85,
            'gift_card': 0.99,
            'installment_plan': 0.90
        }
        return success_rates.get(method, 0.90)
    
    def _get_current_payment_method(self, stripe_customer_id: str) -> str:
        """Get current payment method type"""
        try:
            # This would query Stripe for current payment method
            # For now, return a default
            return 'credit_card'
        except Exception as e:
            logger.error(f"Error getting current payment method: {e}")
            return 'credit_card'
    
    def _get_alternative_payment_suggestions(self, failure_id: str) -> List[Dict[str, Any]]:
        """Get alternative payment suggestions for a failure"""
        try:
            # This would query the database for existing suggestions
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting alternative payment suggestions: {e}")
            return []
    
    def _record_alternative_payment_suggestion(
        self,
        failure_record: PaymentRecoveryRecord,
        suggestion_day: int,
        suggestions: List[Dict[str, Any]],
        result: Dict[str, Any]
    ):
        """Record alternative payment suggestion"""
        try:
            # Create suggestion record
            suggestion_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                recovery_record_id=failure_record.id,
                action_type='alternative_payment_suggestion_sent',
                strategy=RecoveryStrategy.PAYMENT_METHOD_UPDATE,
                scheduled_at=datetime.now(timezone.utc),
                executed_at=datetime.now(timezone.utc),
                status=ActionStatus.COMPLETED,
                success=result.get('success', False),
                metadata={
                    'suggestion_day': suggestion_day,
                    'suggestions_sent': result.get('notifications_sent', 0),
                    'suggestions': suggestions,
                    'failure_reason': failure_record.failure_reason
                }
            )
            
            # Store suggestion record
            self._store_recovery_action(suggestion_action)
            
        except Exception as e:
            logger.error(f"Error recording alternative payment suggestion: {e}")
    
    def manage_grace_period_access(self, failure_id: str) -> Dict[str, Any]:
        """Manage grace period access for payment failure"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Get customer
            customer = self._get_customer(failure_record.customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Check if grace period is enabled
            if not self.recovery_config['grace_period_access']['enabled']:
                return {'success': False, 'error': 'Grace period access is disabled'}
            
            # Calculate grace period dates
            grace_period_start = failure_record.failed_at
            grace_period_end = grace_period_start + timedelta(
                days=self.recovery_config['grace_period_access']['duration_days']
            )
            
            # Check if grace period is active
            now = datetime.now(timezone.utc)
            if now > grace_period_end:
                # Grace period expired, suspend access
                return self._suspend_customer_access(failure_record, customer)
            
            # Activate grace period access
            grace_period_result = self._activate_grace_period_access(failure_record, customer, grace_period_end)
            
            # Schedule grace period notifications
            self._schedule_grace_period_notifications(failure_record, grace_period_end)
            
            # Schedule access suspension
            self._schedule_access_suspension(failure_record, grace_period_end)
            
            return {
                'success': True,
                'grace_period_active': True,
                'grace_period_start': grace_period_start.isoformat(),
                'grace_period_end': grace_period_end.isoformat(),
                'days_remaining': (grace_period_end - now).days,
                'access_level': self.recovery_config['grace_period_access']['access_level'],
                'feature_restrictions': self.recovery_config['grace_period_access']['feature_restrictions']
            }
            
        except Exception as e:
            logger.error(f"Error managing grace period access: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _activate_grace_period_access(
        self,
        failure_record: PaymentRecoveryRecord,
        customer: Customer,
        grace_period_end: datetime
    ) -> Dict[str, Any]:
        """Activate grace period access for customer"""
        try:
            # Update customer status to grace period
            self._update_customer_payment_status(failure_record.customer_id, 'grace_period')
            
            # Apply feature restrictions
            feature_access_service = FeatureAccessService(self.db, self.config)
            restrictions = self.recovery_config['grace_period_access']['feature_restrictions']
            
            restriction_result = feature_access_service.apply_grace_period_restrictions(
                customer_id=failure_record.customer_id,
                restrictions=restrictions,
                grace_period_end=grace_period_end
            )
            
            # Send grace period activation notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure_record.customer_id,
                'grace_period_start': failure_record.failed_at.isoformat(),
                'grace_period_end': grace_period_end.isoformat(),
                'days_remaining': (grace_period_end - datetime.now(timezone.utc)).days,
                'feature_restrictions': restrictions,
                'access_level': self.recovery_config['grace_period_access']['access_level'],
                'channels': self.recovery_config['notification_channels']
            }
            
            notification_result = notification_service.send_grace_period_activation_notifications(notification_data)
            
            # Record grace period activation
            grace_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                recovery_record_id=failure_record.id,
                action_type='grace_period_activated',
                strategy=RecoveryStrategy.GRACE_PERIOD,
                scheduled_at=datetime.now(timezone.utc),
                executed_at=datetime.now(timezone.utc),
                status=ActionStatus.COMPLETED,
                success=True,
                metadata={
                    'grace_period_start': failure_record.failed_at.isoformat(),
                    'grace_period_end': grace_period_end.isoformat(),
                    'feature_restrictions': restrictions,
                    'access_level': self.recovery_config['grace_period_access']['access_level'],
                    'notifications_sent': notification_result.get('notifications_sent', 0)
                }
            )
            
            self._store_recovery_action(grace_action)
            
            return {
                'success': True,
                'customer_status': 'grace_period',
                'feature_restrictions_applied': restriction_result.get('success', False),
                'notifications_sent': notification_result.get('notifications_sent', 0)
            }
            
        except Exception as e:
            logger.error(f"Error activating grace period access: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _suspend_customer_access(
        self,
        failure_record: PaymentRecoveryRecord,
        customer: Customer
    ) -> Dict[str, Any]:
        """Suspend customer access after grace period"""
        try:
            # Update customer status to suspended
            self._update_customer_payment_status(failure_record.customer_id, 'suspended')
            
            # Suspend all feature access
            feature_access_service = FeatureAccessService(self.db, self.config)
            suspension_result = feature_access_service.suspend_customer_access(
                customer_id=failure_record.customer_id,
                reason='grace_period_expired',
                metadata={
                    'failure_id': failure_record.id,
                    'grace_period_expired': True,
                    'suspended_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Send suspension notification
            notification_service = NotificationService(self.db, self.config)
            notification_data = {
                'customer_id': failure_record.customer_id,
                'suspension_reason': 'Grace period expired',
                'failure_amount': failure_record.amount,
                'failure_currency': failure_record.currency,
                'channels': self.recovery_config['notification_channels']
            }
            
            notification_result = notification_service.send_access_suspension_notifications(notification_data)
            
            # Record suspension
            suspension_action = RecoveryAction(
                action_id=str(uuid.uuid4()),
                recovery_record_id=failure_record.id,
                action_type='access_suspended',
                strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                scheduled_at=datetime.now(timezone.utc),
                executed_at=datetime.now(timezone.utc),
                status=ActionStatus.COMPLETED,
                success=True,
                metadata={
                    'suspension_reason': 'grace_period_expired',
                    'feature_access_suspended': suspension_result.get('success', False),
                    'notifications_sent': notification_result.get('notifications_sent', 0)
                }
            )
            
            self._store_recovery_action(suspension_action)
            
            return {
                'success': True,
                'customer_status': 'suspended',
                'suspension_reason': 'Grace period expired',
                'feature_access_suspended': suspension_result.get('success', False),
                'notifications_sent': notification_result.get('notifications_sent', 0)
            }
            
        except Exception as e:
            logger.error(f"Error suspending customer access: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _schedule_grace_period_notifications(self, failure_record: PaymentRecoveryRecord, grace_period_end: datetime):
        """Schedule grace period notifications"""
        try:
            notification_frequency = self.recovery_config['grace_period_access']['notification_frequency']
            
            if notification_frequency == 'daily':
                # Schedule daily notifications
                for day in range(1, self.recovery_config['grace_period_access']['duration_days'] + 1):
                    notification_date = failure_record.failed_at + timedelta(days=day)
                    
                    notification_action = RecoveryAction(
                        action_id=str(uuid.uuid4()),
                        recovery_record_id=failure_record.id,
                        action_type='grace_period_notification',
                        strategy=RecoveryStrategy.GRACE_PERIOD,
                        scheduled_at=notification_date,
                        status=ActionStatus.SCHEDULED,
                        metadata={
                            'notification_day': day,
                            'days_remaining': self.recovery_config['grace_period_access']['duration_days'] - day,
                            'notification_type': 'grace_period_reminder'
                        }
                    )
                    
                    self._store_recovery_action(notification_action)
            
        except Exception as e:
            logger.error(f"Error scheduling grace period notifications: {e}")
    
    def _schedule_access_suspension(self, failure_record: PaymentRecoveryRecord, grace_period_end: datetime):
        """Schedule access suspension at end of grace period"""
        try:
            if self.recovery_config['grace_period_access']['auto_suspension']:
                suspension_action = RecoveryAction(
                    action_id=str(uuid.uuid4()),
                    recovery_record_id=failure_record.id,
                    action_type='access_suspension',
                    strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                    scheduled_at=grace_period_end,
                    status=ActionStatus.SCHEDULED,
                    metadata={
                        'suspension_reason': 'grace_period_expired',
                        'grace_period_end': grace_period_end.isoformat(),
                        'auto_suspension': True
                    }
                )
                
                self._store_recovery_action(suspension_action)
                
        except Exception as e:
            logger.error(f"Error scheduling access suspension: {e}")
    
    def get_grace_period_status(self, failure_id: str) -> Dict[str, Any]:
        """Get grace period status for a failure"""
        try:
            # Get failure record
            failure_record = self._get_payment_failure_record(failure_id)
            if not failure_record:
                return {'success': False, 'error': 'Failure record not found'}
            
            # Calculate grace period dates
            grace_period_start = failure_record.failed_at
            grace_period_end = grace_period_start + timedelta(
                days=self.recovery_config['grace_period_access']['duration_days']
            )
            
            # Check current status
            now = datetime.now(timezone.utc)
            is_active = now <= grace_period_end
            days_remaining = max(0, (grace_period_end - now).days)
            
            # Get scheduled actions
            scheduled_actions = self._get_scheduled_actions_for_failure(failure_id)
            grace_period_actions = [
                action for action in scheduled_actions 
                if action.action_type in ['grace_period_notification', 'access_suspension']
            ]
            
            return {
                'success': True,
                'grace_period_active': is_active,
                'grace_period_start': grace_period_start.isoformat(),
                'grace_period_end': grace_period_end.isoformat(),
                'days_remaining': days_remaining,
                'access_level': self.recovery_config['grace_period_access']['access_level'],
                'feature_restrictions': self.recovery_config['grace_period_access']['feature_restrictions'],
                'scheduled_notifications': len([a for a in grace_period_actions if a.action_type == 'grace_period_notification']),
                'suspension_scheduled': any(a.action_type == 'access_suspension' for a in grace_period_actions)
            }
            
        except Exception as e:
            logger.error(f"Error getting grace period status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_support_ticket(self, customer_id: str, trigger_type: str, priority: str = 'normal') -> Dict[str, Any]:
        """Create support ticket for escalated customer"""
        try:
            # Get support integration configuration
            support_config = self.recovery_config['dunning_email_sequence']['analytics_and_optimization']['customer_support_escalation']['support_integration']
            
            if not support_config['enabled']:
                return {'success': False, 'error': 'Support integration disabled'}
            
            # Get customer context
            customer_context = self._get_customer_context(customer_id, support_config['customer_context'])
            
            # Determine ticket category
            ticket_category = self._determine_ticket_category(trigger_type)
            
            # Map priority
            priority_mapping = support_config['ticket_creation']['priority_mapping']
            mapped_priority = priority_mapping.get(priority, 'normal')
            
            # Create ticket
            ticket_data = {
                'customer_id': customer_id,
                'category': ticket_category,
                'priority': mapped_priority,
                'trigger_type': trigger_type,
                'customer_context': customer_context,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'open'
            }
            
            # Store ticket
            ticket_id = self._store_support_ticket(ticket_data)
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'customer_id': customer_id,
                'category': ticket_category,
                'priority': mapped_priority,
                'trigger_type': trigger_type,
                'status': 'open'
            }
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_billing_communication(self, customer_id: str, communication_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send billing communication to customer"""
        try:
            # Get billing communication configuration
            billing_config = self.recovery_config['dunning_email_sequence']['compliance_and_communication']['billing_communication']
            
            if not billing_config['enabled']:
                return {'success': False, 'error': 'Billing communication disabled'}
            
            # Get customer
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Generate communication content
            content = self._generate_billing_communication_content(communication_type, data, customer)
            
            # Send through configured channels
            sent_channels = []
            failed_channels = []
            
            # Email notifications
            if billing_config['communication_channels']['email_notifications']['enabled']:
                email_result = self._send_billing_email(customer, communication_type, content)
                if email_result['success']:
                    sent_channels.append('email')
                else:
                    failed_channels.append(('email', email_result['error']))
            
            # In-app notifications
            if billing_config['communication_channels']['in_app_notifications']['enabled']:
                in_app_result = self._send_in_app_billing_notification(customer, communication_type, content)
                if in_app_result['success']:
                    sent_channels.append('in_app')
                else:
                    failed_channels.append(('in_app', in_app_result['error']))
            
            # SMS notifications (for critical communications)
            if billing_config['communication_channels']['sms_notifications']['enabled'] and communication_type in ['payment_failure', 'subscription_cancellation']:
                sms_result = self._send_billing_sms(customer, communication_type, content)
                if sms_result['success']:
                    sent_channels.append('sms')
                else:
                    failed_channels.append(('sms', sms_result['error']))
            
            return {
                'success': len(sent_channels) > 0,
                'customer_id': customer_id,
                'communication_type': communication_type,
                'sent_channels': sent_channels,
                'failed_channels': failed_channels,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Error sending billing communication: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription_terms(self, customer_id: str, plan_type: str = None) -> Dict[str, Any]:
        """Get subscription terms and conditions for customer"""
        try:
            # Get subscription terms configuration
            terms_config = self.recovery_config['dunning_email_sequence']['compliance_and_communication']['subscription_terms']
            
            if not terms_config['enabled']:
                return {'success': False, 'error': 'Subscription terms disabled'}
            
            # Get customer and subscription
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            subscription = self._get_customer_subscription(customer_id)
            if not subscription:
                return {'success': False, 'error': 'Subscription not found'}
            
            # Determine plan type
            if not plan_type:
                plan_type = subscription.plan_id
            
            # Get terms and conditions
            terms = self._get_terms_and_conditions(plan_type, terms_config['terms_and_conditions'])
            
            # Get grace period explanation
            grace_period = self._get_grace_period_explanation(plan_type, terms_config['grace_period_explanation'])
            
            # Get subscription features
            features = self._get_subscription_features(plan_type, terms_config['subscription_features'])
            
            # Get cancellation policy
            cancellation_policy = self._get_cancellation_policy(plan_type, terms_config['cancellation_policy'])
            
            return {
                'success': True,
                'customer_id': customer_id,
                'plan_type': plan_type,
                'terms_and_conditions': terms,
                'grace_period': grace_period,
                'subscription_features': features,
                'cancellation_policy': cancellation_policy,
                'legal_compliance': terms_config['terms_and_conditions']['legal_compliance']
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription terms: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_customer_support_request(self, customer_id: str, request_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer support request"""
        try:
            # Get customer support configuration
            support_config = self.recovery_config['dunning_email_sequence']['compliance_and_communication']['customer_support_integration']
            
            if not support_config['enabled']:
                return {'success': False, 'error': 'Customer support integration disabled'}
            
            # Get customer
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Classify the request
            case_classification = self._classify_support_request(request_type, request_data, support_config['complex_case_handling']['case_classification'])
            
            # Determine appropriate support channel
            support_channel = self._determine_support_channel(request_type, case_classification, support_config['support_channels'])
            
            # Create support case
            case_data = {
                'customer_id': customer_id,
                'request_type': request_type,
                'case_classification': case_classification,
                'support_channel': support_channel,
                'request_data': request_data,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'open'
            }
            
            # Store support case
            case_id = self._store_support_case(case_data)
            
            # Assign specialist if needed
            specialist_assignment = None
            if case_classification in ['billing_disputes', 'technical_issues', 'compliance_issues']:
                specialist_assignment = self._assign_specialist(case_id, case_classification, support_config['complex_case_handling']['specialist_assignment'])
            
            # Send initial response
            initial_response = self._send_initial_support_response(customer, support_channel, case_classification)
            
            return {
                'success': True,
                'case_id': case_id,
                'customer_id': customer_id,
                'request_type': request_type,
                'case_classification': case_classification,
                'support_channel': support_channel,
                'specialist_assignment': specialist_assignment,
                'initial_response': initial_response
            }
            
        except Exception as e:
            logger.error(f"Error handling customer support request: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_refund_request(self, customer_id: str, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process refund request for customer"""
        try:
            # Get refund configuration
            refund_config = self.recovery_config['dunning_email_sequence']['compliance_and_communication']['refund_and_cancellation']['refund_policy']
            
            if not refund_config['enabled']:
                return {'success': False, 'error': 'Refund policy disabled'}
            
            # Get customer
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Check refund eligibility
            eligibility = self._check_refund_eligibility(customer, refund_data, refund_config['refund_eligibility'])
            
            if not eligibility['eligible']:
                return {
                    'success': False,
                    'error': 'Refund not eligible',
                    'reason': eligibility['reason'],
                    'policy_details': eligibility['policy_details']
                }
            
            # Calculate refund amount
            refund_amount = self._calculate_refund_amount(customer, refund_data, eligibility['refund_type'])
            
            # Process refund request
            refund_request = {
                'customer_id': customer_id,
                'refund_type': eligibility['refund_type'],
                'refund_amount': refund_amount,
                'reason': refund_data.get('reason'),
                'requested_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending_approval'
            }
            
            # Store refund request
            request_id = self._store_refund_request(refund_request)
            
            # Auto-approve if eligible for automatic approval
            if eligibility['auto_approve']:
                approval_result = self._approve_refund_request(request_id, refund_config['refund_process']['refund_approval'])
                if approval_result['success']:
                    refund_request['status'] = 'approved'
                    refund_request['approved_at'] = datetime.now(timezone.utc).isoformat()
                    
                    # Process refund
                    processing_result = self._process_refund_payment(request_id, refund_config['refund_process']['refund_processing'])
                    if processing_result['success']:
                        refund_request['status'] = 'processed'
                        refund_request['processed_at'] = datetime.now(timezone.utc).isoformat()
            
            # Send refund confirmation
            confirmation_result = self._send_refund_confirmation(customer, refund_request, refund_config['refund_communication'])
            
            return {
                'success': True,
                'request_id': request_id,
                'customer_id': customer_id,
                'refund_type': eligibility['refund_type'],
                'refund_amount': refund_amount,
                'status': refund_request['status'],
                'eligibility': eligibility,
                'confirmation_sent': confirmation_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error processing refund request: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_cancellation_request(self, customer_id: str, cancellation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process cancellation request for customer"""
        try:
            # Get cancellation configuration
            cancellation_config = self.recovery_config['dunning_email_sequence']['compliance_and_communication']['refund_and_cancellation']['cancellation_options']
            
            if not cancellation_config['enabled']:
                return {'success': False, 'error': 'Cancellation options disabled'}
            
            # Get customer and subscription
            customer = self._get_customer(customer_id)
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            subscription = self._get_customer_subscription(customer_id)
            if not subscription:
                return {'success': False, 'error': 'Subscription not found'}
            
            # Determine cancellation method
            cancellation_method = self._determine_cancellation_method(cancellation_data, cancellation_config['cancellation_methods'])
            
            # Calculate cancellation effects
            cancellation_effects = self._calculate_cancellation_effects(subscription, cancellation_data, cancellation_config['cancellation_effects'])
            
            # Process cancellation
            cancellation_request = {
                'customer_id': customer_id,
                'subscription_id': subscription.id,
                'cancellation_method': cancellation_method,
                'cancellation_reason': cancellation_data.get('reason'),
                'effective_date': cancellation_data.get('effective_date', datetime.now(timezone.utc).isoformat()),
                'cancellation_effects': cancellation_effects,
                'requested_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending'
            }
            
            # Store cancellation request
            request_id = self._store_cancellation_request(cancellation_request)
            
            # Execute cancellation
            if cancellation_method == 'immediate':
                execution_result = self._execute_immediate_cancellation(request_id, cancellation_effects)
                if execution_result['success']:
                    cancellation_request['status'] = 'cancelled'
                    cancellation_request['cancelled_at'] = datetime.now(timezone.utc).isoformat()
            else:
                # Schedule cancellation
                scheduling_result = self._schedule_cancellation(request_id, cancellation_data.get('effective_date'))
                if scheduling_result['success']:
                    cancellation_request['status'] = 'scheduled'
            
            # Send cancellation confirmation
            confirmation_result = self._send_cancellation_confirmation(customer, cancellation_request, cancellation_config['cancellation_communication'])
            
            # Offer retention if appropriate
            retention_offer = None
            if cancellation_data.get('reason') in ['pricing', 'features', 'usage']:
                retention_offer = self._generate_retention_offer(customer, cancellation_data, cancellation_config['cancellation_communication']['retention_efforts'])
            
            return {
                'success': True,
                'request_id': request_id,
                'customer_id': customer_id,
                'cancellation_method': cancellation_method,
                'effective_date': cancellation_request['effective_date'],
                'status': cancellation_request['status'],
                'cancellation_effects': cancellation_effects,
                'confirmation_sent': confirmation_result['success'],
                'retention_offer': retention_offer
            }
            
        except Exception as e:
            logger.error(f"Error processing cancellation request: {e}")
            return {
                'success': False,
                'error': str(e)
            }