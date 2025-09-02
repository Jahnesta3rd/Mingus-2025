"""
Rate Limiting Configuration for Financial Application
Comprehensive configuration with cultural sensitivity for African American professionals
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class RateLimitConfig:
    """Configuration for a specific rate limit type"""
    requests: int
    window: int  # seconds
    message: str
    cultural_message: str
    burst_limit: int = 0
    priority: str = "normal"  # low, normal, high, critical

@dataclass
class RateLimitSettings:
    """Comprehensive rate limiting settings"""
    
    # Authentication endpoints - protect against brute force attacks
    login: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=5,
        window=900,  # 15 minutes
        message="Too many login attempts. Please wait before trying again.",
        cultural_message="We understand the importance of secure access to your financial information. Please take a moment before your next attempt.",
        priority="critical"
    ))
    
    password_reset: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=3,
        window=3600,  # 1 hour
        message="Too many password reset attempts. Please wait before trying again.",
        cultural_message="Your security is our priority. Please wait before requesting another password reset.",
        priority="critical"
    ))
    
    register: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=5,
        window=900,  # 15 minutes
        message="Too many registration attempts. Please wait before trying again.",
        cultural_message="We appreciate your interest in joining our community. Please wait before your next registration attempt.",
        priority="high"
    ))
    
    # Financial data endpoints - protect sensitive information
    financial_api: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=100,
        window=60,  # 1 minute
        message="Too many financial data requests. Please wait before trying again.",
        cultural_message="We're processing your financial data requests. Please wait a moment before your next request.",
        priority="high"
    ))
    
    financial_hourly: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=1000,
        window=3600,  # 1 hour
        message="Hourly financial API limit exceeded. Please wait before trying again.",
        cultural_message="We've reached our hourly limit for financial data requests. Please wait before your next request.",
        priority="high"
    ))
    
    # Payment endpoints - critical security
    payment: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=10,
        window=3600,  # 1 hour
        message="Too many payment requests. Please wait before trying again.",
        cultural_message="We're processing your payment requests. Please wait before your next payment attempt.",
        priority="critical"
    ))
    
    stripe_webhook: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=200,
        window=3600,  # 1 hour
        message="Too many webhook requests. Please wait before trying again.",
        cultural_message="We're processing your webhook requests. Please wait before your next attempt.",
        priority="normal"
    ))
    
    # General API endpoints
    api_general: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=1000,
        window=3600,  # 1 hour
        message="Hourly API limit exceeded. Please wait before trying again.",
        cultural_message="We've reached our hourly API limit. Please wait before your next request.",
        priority="normal"
    ))
    
    api_per_minute: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=100,
        window=60,  # 1 minute
        message="Too many API requests. Please wait before trying again.",
        cultural_message="We're processing your requests. Please wait a moment before your next request.",
        priority="normal"
    ))
    
    # Assessment and onboarding endpoints
    assessment_submit: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=3,
        window=300,  # 5 minutes
        message="Too many assessment submissions. Please wait before trying again.",
        cultural_message="We're processing your assessment. Please wait before your next submission.",
        priority="high"
    ))
    
    assessment_view: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=20,
        window=300,  # 5 minutes
        message="Too many assessment views. Please wait before trying again.",
        cultural_message="We're loading your assessment data. Please wait before your next request.",
        priority="normal"
    ))
    
    # Career and professional development endpoints
    career_advice: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=10,
        window=3600,  # 1 hour
        message="Too many career advice requests. Please wait before trying again.",
        cultural_message="We're processing your career development requests. Please wait before your next request.",
        priority="normal"
    ))
    
    networking: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=20,
        window=3600,  # 1 hour
        message="Too many networking requests. Please wait before trying again.",
        cultural_message="We're processing your networking requests. Please wait before your next request.",
        priority="normal"
    ))
    
    # Financial planning and education
    financial_planning: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=15,
        window=3600,  # 1 hour
        message="Too many financial planning requests. Please wait before trying again.",
        cultural_message="We're processing your financial planning requests. Please wait before your next request.",
        priority="high"
    ))
    
    financial_education: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(
        requests=30,
        window=3600,  # 1 hour
        message="Too many financial education requests. Please wait before trying again.",
        cultural_message="We're processing your financial education requests. Please wait before your next request.",
        priority="normal"
    ))

class RateLimitManager:
    """Manager for rate limiting configuration and settings"""
    
    def __init__(self):
        self.settings = RateLimitSettings()
        self.admin_ips = self._load_admin_ips()
        self.whitelisted_ips = self._load_whitelisted_ips()
        self.blacklisted_ips = self._load_blacklisted_ips()
        self.environment = os.getenv('FLASK_ENV', 'development')
    
    def _load_admin_ips(self) -> List[str]:
        """Load admin IP addresses from environment"""
        admin_ips = os.getenv('ADMIN_IPS', '')
        if admin_ips:
            return [ip.strip() for ip in admin_ips.split(',') if ip.strip()]
        return []
    
    def _load_whitelisted_ips(self) -> List[str]:
        """Load whitelisted IP addresses from environment"""
        whitelisted_ips = os.getenv('WHITELISTED_IPS', '')
        if whitelisted_ips:
            return [ip.strip() for ip in whitelisted_ips.split(',') if ip.strip()]
        return []
    
    def _load_blacklisted_ips(self) -> List[str]:
        """Load blacklisted IP addresses from environment"""
        blacklisted_ips = os.getenv('BLACKLISTED_IPS', '')
        if blacklisted_ips:
            return [ip.strip() for ip in blacklisted_ips.split(',') if ip.strip()]
        return []
    
    def get_rate_limit_config(self, endpoint_type: str) -> RateLimitConfig:
        """Get rate limit configuration for endpoint type"""
        return getattr(self.settings, endpoint_type, self.settings.api_general)
    
    def get_all_configs(self) -> Dict[str, RateLimitConfig]:
        """Get all rate limit configurations"""
        configs = {}
        for attr_name in dir(self.settings):
            attr = getattr(self.settings, attr_name)
            if isinstance(attr, RateLimitConfig):
                configs[attr_name] = attr
        return configs
    
    def get_config_by_priority(self, priority: str) -> Dict[str, RateLimitConfig]:
        """Get rate limit configurations by priority level"""
        configs = self.get_all_configs()
        return {name: config for name, config in configs.items() 
                if config.priority == priority}
    
    def is_admin_ip(self, ip_address: str) -> bool:
        """Check if IP address is admin"""
        return ip_address in self.admin_ips
    
    def is_whitelisted_ip(self, ip_address: str) -> bool:
        """Check if IP address is whitelisted"""
        return ip_address in self.whitelisted_ips
    
    def is_blacklisted_ip(self, ip_address: str) -> bool:
        """Check if IP address is blacklisted"""
        return ip_address in self.blacklisted_ips
    
    def get_cultural_message(self, endpoint_type: str, use_cultural: bool = True) -> str:
        """Get culturally appropriate message for endpoint type"""
        config = self.get_rate_limit_config(endpoint_type)
        if use_cultural:
            return config.cultural_message
        return config.message
    
    def get_environment_specific_config(self, endpoint_type: str) -> RateLimitConfig:
        """Get environment-specific rate limit configuration"""
        base_config = self.get_rate_limit_config(endpoint_type)
        
        if self.environment == 'development':
            # More lenient limits in development
            return RateLimitConfig(
                requests=base_config.requests * 5,
                window=base_config.window,
                message=base_config.message,
                cultural_message=base_config.cultural_message,
                burst_limit=base_config.burst_limit,
                priority=base_config.priority
            )
        elif self.environment == 'testing':
            # Very lenient limits in testing
            return RateLimitConfig(
                requests=base_config.requests * 10,
                window=base_config.window,
                message=base_config.message,
                cultural_message=base_config.cultural_message,
                burst_limit=base_config.burst_limit,
                priority=base_config.priority
            )
        else:
            # Production limits
            return base_config

# Global rate limit manager instance
_rate_limit_manager = None

def get_rate_limit_manager() -> RateLimitManager:
    """Get global rate limit manager instance"""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
    return _rate_limit_manager

# Rate limit configuration constants
RATE_LIMIT_CONFIG = {
    'assessment': {
        'submit': {'requests': 3, 'window': 300},
        'view': {'requests': 20, 'window': 300},
        'analytics': {'requests': 10, 'window': 300}
    },
    'auth': {
        'register': {'requests': 5, 'window': 900},
        'login': {'requests': 5, 'window': 900},
        'password_reset': {'requests': 3, 'window': 3600},
        'refresh': {'requests': 20, 'window': 300}
    },
    'api': {
        'general': {'requests': 1000, 'window': 3600},
        'financial': {'requests': 100, 'window': 60},
        'analytics': {'requests': 30, 'window': 3600},
        'admin': {'requests': 200, 'window': 3600}
    },
    'payment': {
        'stripe': {'requests': 10, 'window': 3600},
        'webhook': {'requests': 200, 'window': 3600},
        'plaid': {'requests': 50, 'window': 3600}
    },
    'career': {
        'advice': {'requests': 10, 'window': 3600},
        'networking': {'requests': 20, 'window': 3600},
        'mentorship': {'requests': 5, 'window': 3600}
    },
    'financial': {
        'planning': {'requests': 15, 'window': 3600},
        'education': {'requests': 30, 'window': 3600},
        'tools': {'requests': 25, 'window': 3600}
    }
}

# Cultural sensitivity settings
CULTURAL_SETTINGS = {
    'african_american_focused': True,
    'professional_tone': True,
    'inclusive_language': True,
    'financial_literacy_emphasis': True,
    'career_development_focus': True,
    'community_support_emphasis': True
}

# Error message templates with cultural sensitivity
ERROR_MESSAGES = {
    'rate_limit_exceeded': {
        'default': 'Rate limit exceeded. Please wait before trying again.',
        'cultural': 'We appreciate your engagement with our platform. Please wait a moment before your next request to ensure the best experience for all users.',
        'financial': 'We\'re processing your financial data requests. Please wait a moment before your next request to maintain security.',
        'career': 'We\'re processing your career development requests. Please wait a moment before your next request.',
        'payment': 'We\'re processing your payment requests. Please wait before your next payment attempt to ensure security.'
    },
    'authentication_failed': {
        'default': 'Authentication failed. Please check your credentials.',
        'cultural': 'We couldn\'t verify your credentials. Please check your information and try again. Your security is our priority.',
        'professional': 'Authentication failed. Please verify your credentials and try again.'
    },
    'access_denied': {
        'default': 'Access denied. You don\'t have permission to access this resource.',
        'cultural': 'We\'re unable to grant access to this resource at this time. Please contact support if you believe this is an error.',
        'professional': 'Access denied. Insufficient permissions for this resource.'
    }
}

# Rate limit monitoring and alerting configuration
MONITORING_CONFIG = {
    'enable_alerts': True,
    'alert_threshold': 0.8,  # Alert when 80% of rate limit is reached
    'critical_threshold': 0.95,  # Critical alert when 95% is reached
    'alert_channels': ['log', 'email'],  # log, email, slack, webhook
    'cooldown_period': 300,  # 5 minutes between alerts
    'enable_metrics': True,
    'metrics_retention': 86400,  # 24 hours
    'enable_dashboard': True
}
