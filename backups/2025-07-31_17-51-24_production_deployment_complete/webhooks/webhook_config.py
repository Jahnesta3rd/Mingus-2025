"""
Webhook Configuration for MINGUS Stripe Integration
Manages webhook settings, event mappings, and security configurations
"""
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class WebhookEnvironment(Enum):
    """Webhook environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    url: str
    events: List[str]
    description: str
    enabled: bool = True
    retry_attempts: int = 3
    timeout: int = 30

@dataclass
class WebhookSecurity:
    """Webhook security configuration"""
    signature_verification: bool = True
    ip_whitelist: Optional[List[str]] = None
    rate_limiting: bool = True
    max_requests_per_minute: int = 100
    request_timeout: int = 30

class WebhookConfig:
    """Comprehensive webhook configuration management"""
    
    def __init__(self, environment: WebhookEnvironment = WebhookEnvironment.DEVELOPMENT):
        self.environment = environment
        self.endpoints = self._get_default_endpoints()
        self.security = self._get_security_config()
        self.event_mappings = self._get_event_mappings()
        self.retry_config = self._get_retry_config()
    
    def _get_default_endpoints(self) -> Dict[str, WebhookEndpoint]:
        """Get default webhook endpoints"""
        base_url = os.getenv('BASE_URL', 'https://mingus.com')
        
        return {
            'stripe_main': WebhookEndpoint(
                url=f"{base_url}/api/payment/webhooks/stripe",
                events=[
                    'customer.created',
                    'customer.updated',
                    'customer.deleted',
                    'customer.subscription.created',
                    'customer.subscription.updated',
                    'customer.subscription.deleted',
                    'customer.subscription.trial_will_end',
                    'invoice.created',
                    'invoice.finalized',
                    'invoice.payment_succeeded',
                    'invoice.payment_failed',
                    'invoice.upcoming',
                    'payment_intent.succeeded',
                    'payment_intent.payment_failed',
                    'payment_method.attached',
                    'payment_method.detached',
                    'payment_method.updated',
                    'charge.succeeded',
                    'charge.failed',
                    'charge.refunded',
                    'charge.dispute.created'
                ],
                description="Main Stripe webhook endpoint for all subscription events",
                enabled=True,
                retry_attempts=3,
                timeout=30
            ),
            'stripe_portal': WebhookEndpoint(
                url=f"{base_url}/api/payment/portal/webhook",
                events=[
                    'customer.updated',
                    'customer.subscription.updated',
                    'customer.subscription.deleted',
                    'invoice.payment_succeeded',
                    'invoice.payment_failed',
                    'payment_method.attached',
                    'payment_method.detached'
                ],
                description="Stripe Customer Portal webhook endpoint",
                enabled=True,
                retry_attempts=3,
                timeout=30
            ),
            'stripe_test': WebhookEndpoint(
                url=f"{base_url}/api/payment/webhooks/stripe/test",
                events=[
                    'customer.created',
                    'customer.subscription.created',
                    'invoice.payment_succeeded'
                ],
                description="Test webhook endpoint for development",
                enabled=self.environment == WebhookEnvironment.DEVELOPMENT,
                retry_attempts=1,
                timeout=10
            )
        }
    
    def _get_security_config(self) -> WebhookSecurity:
        """Get security configuration based on environment"""
        if self.environment == WebhookEnvironment.PRODUCTION:
            return WebhookSecurity(
                signature_verification=True,
                ip_whitelist=[
                    '3.18.12.63',
                    '3.130.192.231',
                    '13.235.14.237',
                    '13.235.122.149',
                    '18.211.135.69',
                    '18.211.135.97',
                    '18.211.135.98',
                    '18.211.135.99',
                    '18.211.135.100',
                    '18.211.135.101',
                    '18.211.135.102',
                    '18.211.135.103',
                    '18.211.135.104',
                    '18.211.135.105',
                    '18.211.135.106',
                    '18.211.135.107',
                    '18.211.135.108',
                    '18.211.135.109',
                    '18.211.135.110',
                    '18.211.135.111',
                    '18.211.135.112',
                    '18.211.135.113',
                    '18.211.135.114',
                    '18.211.135.115',
                    '18.211.135.116',
                    '18.211.135.117',
                    '18.211.135.118',
                    '18.211.135.119',
                    '18.211.135.120',
                    '18.211.135.121',
                    '18.211.135.122',
                    '18.211.135.123',
                    '18.211.135.124',
                    '18.211.135.125',
                    '18.211.135.126',
                    '18.211.135.127',
                    '18.211.135.128',
                    '18.211.135.129',
                    '18.211.135.130',
                    '18.211.135.131',
                    '18.211.135.132',
                    '18.211.135.133',
                    '18.211.135.134',
                    '18.211.135.135',
                    '18.211.135.136',
                    '18.211.135.137',
                    '18.211.135.138',
                    '18.211.135.139',
                    '18.211.135.140',
                    '18.211.135.141',
                    '18.211.135.142',
                    '18.211.135.143',
                    '18.211.135.144',
                    '18.211.135.145',
                    '18.211.135.146',
                    '18.211.135.147',
                    '18.211.135.148',
                    '18.211.135.149',
                    '18.211.135.150',
                    '18.211.135.151',
                    '18.211.135.152',
                    '18.211.135.153',
                    '18.211.135.154',
                    '18.211.135.155',
                    '18.211.135.156',
                    '18.211.135.157',
                    '18.211.135.158',
                    '18.211.135.159',
                    '18.211.135.160',
                    '18.211.135.161',
                    '18.211.135.162',
                    '18.211.135.163',
                    '18.211.135.164',
                    '18.211.135.165',
                    '18.211.135.166',
                    '18.211.135.167',
                    '18.211.135.168',
                    '18.211.135.169',
                    '18.211.135.170',
                    '18.211.135.171',
                    '18.211.135.172',
                    '18.211.135.173',
                    '18.211.135.174',
                    '18.211.135.175',
                    '18.211.135.176',
                    '18.211.135.177',
                    '18.211.135.178',
                    '18.211.135.179',
                    '18.211.135.180',
                    '18.211.135.181',
                    '18.211.135.182',
                    '18.211.135.183',
                    '18.211.135.184',
                    '18.211.135.185',
                    '18.211.135.186',
                    '18.211.135.187',
                    '18.211.135.188',
                    '18.211.135.189',
                    '18.211.135.190',
                    '18.211.135.191',
                    '18.211.135.192',
                    '18.211.135.193',
                    '18.211.135.194',
                    '18.211.135.195',
                    '18.211.135.196',
                    '18.211.135.197',
                    '18.211.135.198',
                    '18.211.135.199',
                    '18.211.135.200',
                    '18.211.135.201',
                    '18.211.135.202',
                    '18.211.135.203',
                    '18.211.135.204',
                    '18.211.135.205',
                    '18.211.135.206',
                    '18.211.135.207',
                    '18.211.135.208',
                    '18.211.135.209',
                    '18.211.135.210',
                    '18.211.135.211',
                    '18.211.135.212',
                    '18.211.135.213',
                    '18.211.135.214',
                    '18.211.135.215',
                    '18.211.135.216',
                    '18.211.135.217',
                    '18.211.135.218',
                    '18.211.135.219',
                    '18.211.135.220',
                    '18.211.135.221',
                    '18.211.135.222',
                    '18.211.135.223',
                    '18.211.135.224',
                    '18.211.135.225',
                    '18.211.135.226',
                    '18.211.135.227',
                    '18.211.135.228',
                    '18.211.135.229',
                    '18.211.135.230',
                    '18.211.135.231',
                    '18.211.135.232',
                    '18.211.135.233',
                    '18.211.135.234',
                    '18.211.135.235',
                    '18.211.135.236',
                    '18.211.135.237',
                    '18.211.135.238',
                    '18.211.135.239',
                    '18.211.135.240',
                    '18.211.135.241',
                    '18.211.135.242',
                    '18.211.135.243',
                    '18.211.135.244',
                    '18.211.135.245',
                    '18.211.135.246',
                    '18.211.135.247',
                    '18.211.135.248',
                    '18.211.135.249',
                    '18.211.135.250',
                    '18.211.135.251',
                    '18.211.135.252',
                    '18.211.135.253',
                    '18.211.135.254',
                    '18.211.135.255'
                ],
                rate_limiting=True,
                max_requests_per_minute=100,
                request_timeout=30
            )
        elif self.environment == WebhookEnvironment.STAGING:
            return WebhookSecurity(
                signature_verification=True,
                ip_whitelist=None,  # Allow all IPs in staging
                rate_limiting=True,
                max_requests_per_minute=50,
                request_timeout=30
            )
        else:  # Development
            return WebhookSecurity(
                signature_verification=False,  # Disable in development
                ip_whitelist=None,
                rate_limiting=False,
                max_requests_per_minute=1000,
                request_timeout=60
            )
    
    def _get_event_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get event type mappings and configurations"""
        return {
            'customer.created': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['welcome_email'],
                'analytics': ['customer_created']
            },
            'customer.updated': {
                'priority': 'medium',
                'retry_attempts': 2,
                'timeout': 20,
                'notifications': [],
                'analytics': ['customer_updated']
            },
            'customer.deleted': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['goodbye_email'],
                'analytics': ['customer_deleted']
            },
            'customer.subscription.created': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['subscription_confirmation'],
                'analytics': ['subscription_created']
            },
            'customer.subscription.updated': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['subscription_update'],
                'analytics': ['subscription_updated']
            },
            'customer.subscription.deleted': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['subscription_cancellation'],
                'analytics': ['subscription_canceled']
            },
            'customer.subscription.trial_will_end': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['trial_ending'],
                'analytics': ['trial_ending']
            },
            'invoice.payment_succeeded': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['payment_confirmation'],
                'analytics': ['payment_succeeded']
            },
            'invoice.payment_failed': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['payment_failure'],
                'analytics': ['payment_failed']
            },
            'invoice.created': {
                'priority': 'low',
                'retry_attempts': 1,
                'timeout': 10,
                'notifications': [],
                'analytics': ['invoice_created']
            },
            'invoice.finalized': {
                'priority': 'low',
                'retry_attempts': 1,
                'timeout': 10,
                'notifications': [],
                'analytics': ['invoice_finalized']
            },
            'invoice.upcoming': {
                'priority': 'medium',
                'retry_attempts': 2,
                'timeout': 20,
                'notifications': ['invoice_upcoming'],
                'analytics': ['invoice_upcoming']
            },
            'payment_intent.succeeded': {
                'priority': 'medium',
                'retry_attempts': 2,
                'timeout': 20,
                'notifications': [],
                'analytics': ['payment_intent_succeeded']
            },
            'payment_intent.payment_failed': {
                'priority': 'medium',
                'retry_attempts': 2,
                'timeout': 20,
                'notifications': [],
                'analytics': ['payment_intent_failed']
            },
            'payment_method.attached': {
                'priority': 'low',
                'retry_attempts': 1,
                'timeout': 10,
                'notifications': [],
                'analytics': ['payment_method_attached']
            },
            'payment_method.detached': {
                'priority': 'low',
                'retry_attempts': 1,
                'timeout': 10,
                'notifications': [],
                'analytics': ['payment_method_detached']
            },
            'payment_method.updated': {
                'priority': 'low',
                'retry_attempts': 1,
                'timeout': 10,
                'notifications': [],
                'analytics': ['payment_method_updated']
            },
            'charge.succeeded': {
                'priority': 'low',
                'retry_attempts': 1,
                'timeout': 10,
                'notifications': [],
                'analytics': ['charge_succeeded']
            },
            'charge.failed': {
                'priority': 'medium',
                'retry_attempts': 2,
                'timeout': 20,
                'notifications': [],
                'analytics': ['charge_failed']
            },
            'charge.refunded': {
                'priority': 'medium',
                'retry_attempts': 2,
                'timeout': 20,
                'notifications': ['refund_confirmation'],
                'analytics': ['charge_refunded']
            },
            'charge.dispute.created': {
                'priority': 'high',
                'retry_attempts': 3,
                'timeout': 30,
                'notifications': ['dispute_notification'],
                'analytics': ['dispute_created']
            }
        }
    
    def _get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration"""
        return {
            'exponential_backoff': True,
            'base_delay': 1,  # seconds
            'max_delay': 60,  # seconds
            'jitter': True,
            'max_retries': 3,
            'retry_on_exceptions': [
                'ConnectionError',
                'TimeoutError',
                'DatabaseError',
                'StripeError'
            ]
        }
    
    def get_endpoint(self, endpoint_name: str) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by name"""
        return self.endpoints.get(endpoint_name)
    
    def get_event_config(self, event_type: str) -> Optional[Dict[str, Any]]:
        """Get event configuration by type"""
        return self.event_mappings.get(event_type)
    
    def is_event_supported(self, event_type: str) -> bool:
        """Check if event type is supported"""
        return event_type in self.event_mappings
    
    def get_supported_events(self) -> List[str]:
        """Get list of supported event types"""
        return list(self.event_mappings.keys())
    
    def get_high_priority_events(self) -> List[str]:
        """Get list of high priority event types"""
        return [
            event_type for event_type, config in self.event_mappings.items()
            if config.get('priority') == 'high'
        ]
    
    def get_events_with_notifications(self) -> List[str]:
        """Get list of event types that trigger notifications"""
        return [
            event_type for event_type, config in self.event_mappings.items()
            if config.get('notifications')
        ]
    
    def get_events_with_analytics(self) -> List[str]:
        """Get list of event types that trigger analytics"""
        return [
            event_type for event_type, config in self.event_mappings.items()
            if config.get('analytics')
        ]
    
    def validate_ip_address(self, ip_address: str) -> bool:
        """Validate IP address against whitelist"""
        if not self.security.ip_whitelist:
            return True  # No whitelist configured
        
        return ip_address in self.security.ip_whitelist
    
    def get_webhook_secret(self) -> Optional[str]:
        """Get webhook secret for current environment"""
        if self.environment == WebhookEnvironment.PRODUCTION:
            return os.getenv('STRIPE_WEBHOOK_SECRET_PROD')
        elif self.environment == WebhookEnvironment.STAGING:
            return os.getenv('STRIPE_WEBHOOK_SECRET_STAGING')
        else:
            return os.getenv('STRIPE_WEBHOOK_SECRET_DEV')
    
    def get_stripe_api_key(self) -> str:
        """Get Stripe API key for current environment"""
        if self.environment == WebhookEnvironment.PRODUCTION:
            return os.getenv('STRIPE_SECRET_KEY_PROD', '')
        elif self.environment == WebhookEnvironment.STAGING:
            return os.getenv('STRIPE_SECRET_KEY_STAGING', '')
        else:
            return os.getenv('STRIPE_SECRET_KEY_DEV', '')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'environment': self.environment.value,
            'endpoints': {
                name: {
                    'url': endpoint.url,
                    'events': endpoint.events,
                    'description': endpoint.description,
                    'enabled': endpoint.enabled,
                    'retry_attempts': endpoint.retry_attempts,
                    'timeout': endpoint.timeout
                }
                for name, endpoint in self.endpoints.items()
            },
            'security': {
                'signature_verification': self.security.signature_verification,
                'ip_whitelist': self.security.ip_whitelist,
                'rate_limiting': self.security.rate_limiting,
                'max_requests_per_minute': self.security.max_requests_per_minute,
                'request_timeout': self.security.request_timeout
            },
            'event_mappings': self.event_mappings,
            'retry_config': self.retry_config
        } 