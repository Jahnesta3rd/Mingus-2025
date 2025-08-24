"""
Billing Configuration for MINGUS
Configuration settings for billing features, email, tax services, and currency handling
"""
import os
from typing import Dict, List, Any

class BillingConfig:
    """Configuration for billing features"""
    
    # Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'billing@mingus.com')
    FROM_NAME = os.getenv('FROM_NAME', 'MINGUS Billing')
    
    # Tax Service Configuration
    TAX_SERVICE_URL = os.getenv('TAX_SERVICE_URL', '')
    TAX_SERVICE_API_KEY = os.getenv('TAX_SERVICE_API_KEY', '')
    TAX_SERVICE_TIMEOUT = int(os.getenv('TAX_SERVICE_TIMEOUT', '10'))
    
    # Currency Configuration
    DEFAULT_CURRENCY = 'USD'
    SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
    EXCHANGE_RATE_API_URL = os.getenv('EXCHANGE_RATE_API_URL', '')
    EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', '')
    
    # Invoice Configuration
    INVOICE_DUE_DAYS = int(os.getenv('INVOICE_DUE_DAYS', '7'))
    INVOICE_PREFIX = os.getenv('INVOICE_PREFIX', 'INV')
    INVOICE_NUMBER_FORMAT = os.getenv('INVOICE_NUMBER_FORMAT', '{prefix}-{customer_id:06d}-{count:04d}-{year}')
    
    # Dunning Management Configuration
    DUNNING_FIRST_REMINDER_DAYS = int(os.getenv('DUNNING_FIRST_REMINDER_DAYS', '1'))
    DUNNING_SECOND_REMINDER_DAYS = int(os.getenv('DUNNING_SECOND_REMINDER_DAYS', '3'))
    DUNNING_FINAL_WARNING_DAYS = int(os.getenv('DUNNING_FINAL_WARNING_DAYS', '7'))
    DUNNING_SUSPENSION_DAYS = int(os.getenv('DUNNING_SUSPENSION_DAYS', '14'))
    DUNNING_MAX_RETRIES = int(os.getenv('DUNNING_MAX_RETRIES', '3'))
    
    # PDF Generation Configuration
    PDF_STORAGE_PATH = os.getenv('PDF_STORAGE_PATH', 'invoices/')
    PDF_TEMPLATE_PATH = os.getenv('PDF_TEMPLATE_PATH', 'templates/invoices/')
    
    # Email Templates Configuration
    EMAIL_TEMPLATE_PATH = os.getenv('EMAIL_TEMPLATE_PATH', 'templates/emails/')
    
    # Tax Rates (fallback for simple tax calculation)
    TAX_RATES = {
        'US': {
            'CA': 0.085, 'NY': 0.08, 'TX': 0.0625, 'FL': 0.06,
            'WA': 0.065, 'IL': 0.0625, 'PA': 0.06, 'OH': 0.0575,
            'default': 0.05
        }
    }
    
    # Exchange Rates (fallback rates for development)
    FALLBACK_EXCHANGE_RATES = {
        'USD': {
            'EUR': 0.85, 'GBP': 0.73, 'CAD': 1.25, 'AUD': 1.35
        },
        'EUR': {
            'USD': 1.18, 'GBP': 0.86, 'CAD': 1.47, 'AUD': 1.59
        },
        'GBP': {
            'USD': 1.37, 'EUR': 1.16, 'CAD': 1.71, 'AUD': 1.85
        }
    }
    
    # Currency Symbols
    CURRENCY_SYMBOLS = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'CAD': 'C$', 'AUD': 'A$'
    }
    
    # Currency Names
    CURRENCY_NAMES = {
        'USD': 'US Dollar',
        'EUR': 'Euro', 
        'GBP': 'British Pound',
        'CAD': 'Canadian Dollar',
        'AUD': 'Australian Dollar'
    }
    
    @classmethod
    def get_email_config(cls) -> Dict[str, str]:
        """Get email configuration"""
        return {
            'host': cls.SMTP_HOST,
            'port': cls.SMTP_PORT,
            'username': cls.SMTP_USERNAME,
            'password': cls.SMTP_PASSWORD,
            'from_email': cls.FROM_EMAIL,
            'from_name': cls.FROM_NAME
        }
    
    @classmethod
    def get_tax_config(cls) -> Dict[str, str]:
        """Get tax service configuration"""
        return {
            'url': cls.TAX_SERVICE_URL,
            'api_key': cls.TAX_SERVICE_API_KEY,
            'timeout': cls.TAX_SERVICE_TIMEOUT
        }
    
    @classmethod
    def get_currency_config(cls) -> Dict[str, Any]:
        """Get currency configuration"""
        return {
            'default': cls.DEFAULT_CURRENCY,
            'supported': cls.SUPPORTED_CURRENCIES,
            'exchange_rate_url': cls.EXCHANGE_RATE_API_URL,
            'exchange_rate_api_key': cls.EXCHANGE_RATE_API_KEY,
            'symbols': cls.CURRENCY_SYMBOLS,
            'names': cls.CURRENCY_NAMES,
            'fallback_rates': cls.FALLBACK_EXCHANGE_RATES
        }
    
    @classmethod
    def get_dunning_config(cls) -> Dict[str, int]:
        """Get dunning management configuration"""
        return {
            'first_reminder_days': cls.DUNNING_FIRST_REMINDER_DAYS,
            'second_reminder_days': cls.DUNNING_SECOND_REMINDER_DAYS,
            'final_warning_days': cls.DUNNING_FINAL_WARNING_DAYS,
            'suspension_days': cls.DUNNING_SUSPENSION_DAYS,
            'max_retries': cls.DUNNING_MAX_RETRIES
        }
    
    @classmethod
    def get_invoice_config(cls) -> Dict[str, Any]:
        """Get invoice configuration"""
        return {
            'due_days': cls.INVOICE_DUE_DAYS,
            'prefix': cls.INVOICE_PREFIX,
            'number_format': cls.INVOICE_NUMBER_FORMAT,
            'pdf_storage_path': cls.PDF_STORAGE_PATH,
            'pdf_template_path': cls.PDF_TEMPLATE_PATH
        }
    
    @classmethod
    def get_tax_rate(cls, country: str, state: str = None) -> float:
        """Get tax rate for a location"""
        if country == 'US':
            rates = cls.TAX_RATES.get('US', {})
            return rates.get(state, rates.get('default', 0.05))
        return 0.0
    
    @classmethod
    def get_exchange_rate(cls, from_currency: str, to_currency: str) -> float:
        """Get fallback exchange rate"""
        rates = cls.FALLBACK_EXCHANGE_RATES.get(from_currency, {})
        return rates.get(to_currency, 1.0)
    
    @classmethod
    def get_currency_symbol(cls, currency: str) -> str:
        """Get currency symbol"""
        return cls.CURRENCY_SYMBOLS.get(currency, currency)
    
    @classmethod
    def get_currency_name(cls, currency: str) -> str:
        """Get currency name"""
        return cls.CURRENCY_NAMES.get(currency, currency)
    
    @classmethod
    def is_currency_supported(cls, currency: str) -> bool:
        """Check if currency is supported"""
        return currency in cls.SUPPORTED_CURRENCIES 