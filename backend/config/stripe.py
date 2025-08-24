from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class StripeWebhookConfig:
    webhook_secret: str = ""
    supported_events: Optional[list] = None

    def is_supported_event(self, event_type: str) -> bool:
        if not self.supported_events:
            return True
        return event_type in self.supported_events


@dataclass
class StripeConfig:
    api_key: str = "test_api_key"
    publishable_key: str = "test_publishable_key"
    webhook_secret: str = ""
    environment: str = "test"
    enable_debug: bool = False
    log_level: str = "warning"
    price_ids: Dict[str, Dict[str, str]] = None
    webhook: StripeWebhookConfig = field(default_factory=StripeWebhookConfig)

    def get_price_id(self, tier: str, billing_cycle: str) -> Optional[str]:
        if not self.price_ids:
            return None
        return self.price_ids.get(tier, {}).get(billing_cycle)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'environment': self.environment,
            'debug': self.enable_debug,
        }

    @property
    def missing_configuration(self) -> list:
        missing = []
        if not self.api_key:
            missing.append('api_key')
        return missing

    def validate_configuration(self) -> Dict[str, Any]:
        missing = self.missing_configuration
        return {'is_configured': len(missing) == 0, 'missing_configuration': missing}


class StripeErrorHandler:
    def __init__(self):
        import logging
        self.logger = logging.getLogger('stripe')

    def log_error(self, error: Exception, context: Dict[str, Any]):
        self.logger.warning(f"Stripe error: {error} | context={context}")

    def log_payment_event(self, event: str, data: Dict[str, Any]):
        self.logger.info(f"Stripe payment event: {event}")

    def log_subscription_event(self, event: str, data: Dict[str, Any]):
        self.logger.info(f"Stripe subscription event: {event}")


def get_stripe_config() -> StripeConfig:
    # Minimal defaults for tests; real keys come from env in production
    return StripeConfig(
        price_ids={
            'budget': {'monthly': 'price_budget_monthly', 'yearly': 'price_budget_yearly'},
            'mid_tier': {'monthly': 'price_mid_monthly', 'yearly': 'price_mid_yearly'},
            'professional': {'monthly': 'price_pro_monthly', 'yearly': 'price_pro_yearly'},
        },
        webhook=StripeWebhookConfig(webhook_secret="", supported_events=[]),
    )


def get_stripe_error_handler() -> StripeErrorHandler:
    return StripeErrorHandler()


def get_stripe_webhook_config() -> StripeWebhookConfig:
    return StripeWebhookConfig()


