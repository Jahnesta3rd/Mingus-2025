#!/usr/bin/env python3
"""
Fraud Detection Service for Payment Security
Comprehensive fraud detection using Stripe Radar and custom rules
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import re
import ipaddress

import stripe
from flask import request, current_app

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FraudIndicator(Enum):
    """Fraud indicator types"""
    HIGH_VALUE_PAYMENT = "high_value_payment"
    UNUSUAL_FREQUENCY = "unusual_frequency"
    LOCATION_MISMATCH = "location_mismatch"
    DEVICE_MISMATCH = "device_mismatch"
    FAILED_ATTEMPTS = "failed_attempts"
    SUSPICIOUS_IP = "suspicious_ip"
    CARD_TESTING = "card_testing"
    VELOCITY_CHECK = "velocity_check"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    STRIPE_RADAR_FLAG = "stripe_radar_flag"

@dataclass
class FraudAssessment:
    """Fraud assessment result"""
    risk_level: RiskLevel
    risk_score: float  # 0.0 to 1.0
    fraud_indicators: List[FraudIndicator]
    recommendations: List[str]
    should_block: bool
    should_review: bool
    assessment_timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class PaymentContext:
    """Payment context for fraud assessment"""
    user_id: str
    amount: float
    currency: str
    payment_method_id: str
    ip_address: str
    user_agent: str
    billing_address: Dict[str, str]
    shipping_address: Optional[Dict[str, str]]
    device_id: Optional[str]
    session_id: Optional[str]
    previous_payments: List[Dict[str, Any]]
    account_age_days: int
    total_payments_count: int
    failed_payments_count: int

class FraudDetectionService:
    """Comprehensive fraud detection service"""
    
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        # Risk thresholds
        self.risk_thresholds = {
            'high_value': float(current_app.config.get('FRAUD_HIGH_VALUE_THRESHOLD', 10000)),
            'unusual_frequency': int(current_app.config.get('FRAUD_UNUSUAL_FREQUENCY_THRESHOLD', 10)),
            'failed_attempts': int(current_app.config.get('FRAUD_FAILED_ATTEMPTS_THRESHOLD', 5)),
            'velocity_window_hours': int(current_app.config.get('FRAUD_VELOCITY_WINDOW_HOURS', 24))
        }
        
        # Risk scoring weights
        self.risk_weights = {
            'amount': 0.2,
            'frequency': 0.25,
            'location': 0.15,
            'device': 0.1,
            'behavior': 0.2,
            'stripe_radar': 0.1
        }
        
        # Initialize storage for tracking
        self.payment_history = defaultdict(deque)
        self.failed_attempts = defaultdict(int)
        self.device_history = defaultdict(set)
        self.ip_history = defaultdict(set)
        
        # Load risk rules
        self.risk_rules = self._load_risk_rules()
        
        logger.info("Fraud detection service initialized")
    
    def _load_risk_rules(self) -> Dict[str, Any]:
        """Load fraud detection risk rules"""
        return {
            'high_value_payments': {
                'enabled': True,
                'threshold': self.risk_thresholds['high_value'],
                'risk_score': 0.8
            },
            'unusual_frequency': {
                'enabled': True,
                'threshold': self.risk_thresholds['unusual_frequency'],
                'window_hours': 24,
                'risk_score': 0.7
            },
            'location_mismatch': {
                'enabled': True,
                'risk_score': 0.6
            },
            'device_mismatch': {
                'enabled': True,
                'risk_score': 0.5
            },
            'failed_attempts': {
                'enabled': True,
                'threshold': self.risk_thresholds['failed_attempts'],
                'window_hours': 24,
                'risk_score': 0.9
            },
            'suspicious_ips': {
                'enabled': True,
                'risk_score': 0.8,
                'blacklisted_ranges': [
                    '10.0.0.0/8',
                    '172.16.0.0/12',
                    '192.168.0.0/16'
                ]
            },
            'card_testing': {
                'enabled': True,
                'risk_score': 0.9,
                'test_amounts': [1.00, 0.01, 0.50, 2.00]
            },
            'velocity_check': {
                'enabled': True,
                'window_hours': self.risk_thresholds['velocity_window_hours'],
                'max_amount': 5000,
                'risk_score': 0.7
            }
        }
    
    def assess_payment_risk(self, payment_context: PaymentContext) -> FraudAssessment:
        """
        Assess payment risk using multiple detection methods
        
        Args:
            payment_context: Payment context information
            
        Returns:
            FraudAssessment with risk level and recommendations
        """
        try:
            fraud_indicators = []
            risk_scores = {}
            recommendations = []
            
            # 1. Amount-based risk assessment
            amount_risk = self._assess_amount_risk(payment_context)
            if amount_risk['risk_score'] > 0:
                fraud_indicators.append(FraudIndicator.HIGH_VALUE_PAYMENT)
                risk_scores['amount'] = amount_risk['risk_score']
                recommendations.extend(amount_risk['recommendations'])
            
            # 2. Frequency-based risk assessment
            frequency_risk = self._assess_frequency_risk(payment_context)
            if frequency_risk['risk_score'] > 0:
                fraud_indicators.append(FraudIndicator.UNUSUAL_FREQUENCY)
                risk_scores['frequency'] = frequency_risk['risk_score']
                recommendations.extend(frequency_risk['recommendations'])
            
            # 3. Location-based risk assessment
            location_risk = self._assess_location_risk(payment_context)
            if location_risk['risk_score'] > 0:
                fraud_indicators.append(FraudIndicator.LOCATION_MISMATCH)
                risk_scores['location'] = location_risk['risk_score']
                recommendations.extend(location_risk['recommendations'])
            
            # 4. Device-based risk assessment
            device_risk = self._assess_device_risk(payment_context)
            if device_risk['risk_score'] > 0:
                fraud_indicators.append(FraudIndicator.DEVICE_MISMATCH)
                risk_scores['device'] = device_risk['risk_score']
                recommendations.extend(device_risk['recommendations'])
            
            # 5. Behavioral risk assessment
            behavior_risk = self._assess_behavioral_risk(payment_context)
            if behavior_risk['risk_score'] > 0:
                fraud_indicators.append(FraudIndicator.BEHAVIORAL_ANOMALY)
                risk_scores['behavior'] = behavior_risk['risk_score']
                recommendations.extend(behavior_risk['recommendations'])
            
            # 6. Stripe Radar assessment
            stripe_risk = self._assess_stripe_radar_risk(payment_context)
            if stripe_risk['risk_score'] > 0:
                fraud_indicators.append(FraudIndicator.STRIPE_RADAR_FLAG)
                risk_scores['stripe_radar'] = stripe_risk['risk_score']
                recommendations.extend(stripe_risk['recommendations'])
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(risk_scores)
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk_score, fraud_indicators)
            
            # Determine actions
            should_block = risk_level in [RiskLevel.CRITICAL] or overall_risk_score > 0.8
            should_review = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or overall_risk_score > 0.6
            
            # Update payment history
            self._update_payment_history(payment_context)
            
            return FraudAssessment(
                risk_level=risk_level,
                risk_score=overall_risk_score,
                fraud_indicators=fraud_indicators,
                recommendations=recommendations,
                should_block=should_block,
                should_review=should_review,
                assessment_timestamp=datetime.utcnow(),
                metadata={
                    'risk_scores': risk_scores,
                    'payment_context': asdict(payment_context)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in fraud assessment: {e}")
            # Return high risk assessment on error
            return FraudAssessment(
                risk_level=RiskLevel.HIGH,
                risk_score=0.8,
                fraud_indicators=[FraudIndicator.BEHAVIORAL_ANOMALY],
                recommendations=["Fraud assessment error - manual review required"],
                should_block=False,
                should_review=True,
                assessment_timestamp=datetime.utcnow(),
                metadata={'error': str(e)}
            )
    
    def _assess_amount_risk(self, payment_context: PaymentContext) -> Dict[str, Any]:
        """Assess risk based on payment amount"""
        risk_score = 0.0
        recommendations = []
        
        # Check for high value payments
        if payment_context.amount > self.risk_rules['high_value_payments']['threshold']:
            risk_score = self.risk_rules['high_value_payments']['risk_score']
            recommendations.append(f"High value payment detected: ${payment_context.amount}")
        
        # Check for card testing amounts
        if payment_context.amount in self.risk_rules['card_testing']['test_amounts']:
            risk_score = max(risk_score, self.risk_rules['card_testing']['risk_score'])
            recommendations.append("Suspicious test amount detected")
        
        return {
            'risk_score': risk_score,
            'recommendations': recommendations
        }
    
    def _assess_frequency_risk(self, payment_context: PaymentContext) -> Dict[str, Any]:
        """Assess risk based on payment frequency"""
        risk_score = 0.0
        recommendations = []
        
        # Get recent payments for this user
        recent_payments = self._get_recent_payments(
            payment_context.user_id, 
            hours=self.risk_rules['unusual_frequency']['window_hours']
        )
        
        if len(recent_payments) >= self.risk_rules['unusual_frequency']['threshold']:
            risk_score = self.risk_rules['unusual_frequency']['risk_score']
            recommendations.append(f"Unusual payment frequency: {len(recent_payments)} payments in 24 hours")
        
        return {
            'risk_score': risk_score,
            'recommendations': recommendations
        }
    
    def _assess_location_risk(self, payment_context: PaymentContext) -> Dict[str, Any]:
        """Assess risk based on location information"""
        risk_score = 0.0
        recommendations = []
        
        # Check for location mismatch between billing and shipping
        if (payment_context.shipping_address and 
            payment_context.billing_address != payment_context.shipping_address):
            
            # Check if countries are different
            billing_country = payment_context.billing_address.get('country')
            shipping_country = payment_context.shipping_address.get('country')
            
            if billing_country != shipping_country:
                risk_score = self.risk_rules['location_mismatch']['risk_score']
                recommendations.append(f"Location mismatch: {billing_country} vs {shipping_country}")
        
        return {
            'risk_score': risk_score,
            'recommendations': recommendations
        }
    
    def _assess_device_risk(self, payment_context: PaymentContext) -> Dict[str, Any]:
        """Assess risk based on device information"""
        risk_score = 0.0
        recommendations = []
        
        if payment_context.device_id:
            # Check if this device has been used by other users
            device_users = self.device_history.get(payment_context.device_id, set())
            
            if len(device_users) > 1 and payment_context.user_id not in device_users:
                risk_score = self.risk_rules['device_mismatch']['risk_score']
                recommendations.append("Device used by multiple users")
        
        return {
            'risk_score': risk_score,
            'recommendations': recommendations
        }
    
    def _assess_behavioral_risk(self, payment_context: PaymentContext) -> Dict[str, Any]:
        """Assess risk based on behavioral patterns"""
        risk_score = 0.0
        recommendations = []
        
        # Check for failed payment attempts
        failed_attempts = self.failed_attempts.get(payment_context.user_id, 0)
        if failed_attempts >= self.risk_rules['failed_attempts']['threshold']:
            risk_score = self.risk_rules['failed_attempts']['risk_score']
            recommendations.append(f"Multiple failed payment attempts: {failed_attempts}")
        
        # Check for suspicious IP
        if self._is_suspicious_ip(payment_context.ip_address):
            risk_score = max(risk_score, self.risk_rules['suspicious_ips']['risk_score'])
            recommendations.append("Suspicious IP address detected")
        
        # Check for velocity (rapid payments)
        if self._check_velocity_risk(payment_context):
            risk_score = max(risk_score, self.risk_rules['velocity_check']['risk_score'])
            recommendations.append("Unusual payment velocity detected")
        
        return {
            'risk_score': risk_score,
            'recommendations': recommendations
        }
    
    def _assess_stripe_radar_risk(self, payment_context: PaymentContext) -> Dict[str, Any]:
        """Assess risk using Stripe Radar"""
        risk_score = 0.0
        recommendations = []
        
        try:
            # Create a test payment intent to get Radar assessment
            test_payment_intent = self.stripe.PaymentIntent.create(
                amount=int(payment_context.amount * 100),  # Convert to cents
                currency=payment_context.currency,
                payment_method=payment_context.payment_method_id,
                confirm=True,
                off_session=True,
                error_on_requires_action=True,
                metadata={
                    'user_id': payment_context.user_id,
                    'fraud_assessment': 'true'
                }
            )
            
            # Check Radar assessment
            if hasattr(test_payment_intent, 'radar') and test_payment_intent.radar:
                radar_assessment = test_payment_intent.radar
                
                if radar_assessment.get('risk_level') == 'highest':
                    risk_score = 0.9
                    recommendations.append("Stripe Radar: Highest risk level")
                elif radar_assessment.get('risk_level') == 'elevated':
                    risk_score = 0.7
                    recommendations.append("Stripe Radar: Elevated risk level")
            
            # Cancel the test payment intent
            self.stripe.PaymentIntent.cancel(test_payment_intent.id)
            
        except stripe.error.CardError as e:
            # Card was declined - this might indicate fraud
            risk_score = 0.6
            recommendations.append(f"Card declined during assessment: {str(e)}")
        except Exception as e:
            logger.error(f"Error in Stripe Radar assessment: {e}")
        
        return {
            'risk_score': risk_score,
            'recommendations': recommendations
        }
    
    def _calculate_overall_risk_score(self, risk_scores: Dict[str, float]) -> float:
        """Calculate overall risk score using weighted average"""
        if not risk_scores:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for risk_type, score in risk_scores.items():
            weight = self.risk_weights.get(risk_type, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _determine_risk_level(self, risk_score: float, fraud_indicators: List[FraudIndicator]) -> RiskLevel:
        """Determine risk level based on score and indicators"""
        if risk_score >= 0.8 or len(fraud_indicators) >= 4:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6 or len(fraud_indicators) >= 2:
            return RiskLevel.HIGH
        elif risk_score >= 0.4 or len(fraud_indicators) >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _get_recent_payments(self, user_id: str, hours: int) -> List[Dict[str, Any]]:
        """Get recent payments for a user"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_payments = []
        
        for payment in self.payment_history.get(user_id, []):
            if payment['timestamp'] >= cutoff_time:
                recent_payments.append(payment)
        
        return recent_payments
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check against blacklisted ranges
            for blacklisted_range in self.risk_rules['suspicious_ips']['blacklisted_ranges']:
                if ip in ipaddress.ip_network(blacklisted_range):
                    return True
            
            # Check for private IP addresses
            if ip.is_private:
                return True
            
            return False
            
        except ValueError:
            return True  # Invalid IP address
    
    def _check_velocity_risk(self, payment_context: PaymentContext) -> bool:
        """Check for velocity-based fraud"""
        window_hours = self.risk_rules['velocity_check']['window_hours']
        max_amount = self.risk_rules['velocity_check']['max_amount']
        
        recent_payments = self._get_recent_payments(payment_context.user_id, window_hours)
        total_amount = sum(payment['amount'] for payment in recent_payments)
        
        return total_amount > max_amount
    
    def _update_payment_history(self, payment_context: PaymentContext):
        """Update payment history for future assessments"""
        payment_record = {
            'timestamp': datetime.utcnow(),
            'amount': payment_context.amount,
            'currency': payment_context.currency,
            'ip_address': payment_context.ip_address,
            'device_id': payment_context.device_id
        }
        
        # Add to user's payment history
        self.payment_history[payment_context.user_id].append(payment_record)
        
        # Keep only recent payments (last 30 days)
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        self.payment_history[payment_context.user_id] = deque(
            [p for p in self.payment_history[payment_context.user_id] 
             if p['timestamp'] >= cutoff_time],
            maxlen=1000
        )
        
        # Update device history
        if payment_context.device_id:
            self.device_history[payment_context.device_id].add(payment_context.user_id)
        
        # Update IP history
        self.ip_history[payment_context.ip_address].add(payment_context.user_id)
    
    def record_failed_payment(self, user_id: str):
        """Record a failed payment attempt"""
        self.failed_attempts[user_id] += 1
        
        # Reset counter after 24 hours
        def reset_counter():
            time.sleep(24 * 3600)  # 24 hours
            if user_id in self.failed_attempts:
                self.failed_attempts[user_id] = max(0, self.failed_attempts[user_id] - 1)
        
        # Start background thread to reset counter
        import threading
        thread = threading.Thread(target=reset_counter)
        thread.daemon = True
        thread.start()
    
    def get_fraud_statistics(self) -> Dict[str, Any]:
        """Get fraud detection statistics"""
        return {
            'total_assessments': len(self.payment_history),
            'high_risk_payments': sum(1 for payments in self.payment_history.values() 
                                    for payment in payments if payment.get('risk_level') == 'high'),
            'blocked_payments': sum(1 for payments in self.payment_history.values() 
                                  for payment in payments if payment.get('blocked', False)),
            'suspicious_ips': len(self.ip_history),
            'multi_user_devices': sum(1 for users in self.device_history.values() if len(users) > 1),
            'failed_attempts': sum(self.failed_attempts.values())
        }

# Global fraud detection service instance
_fraud_detection_service = None

def get_fraud_detection_service() -> FraudDetectionService:
    """Get global fraud detection service instance"""
    global _fraud_detection_service
    if _fraud_detection_service is None:
        _fraud_detection_service = FraudDetectionService()
    return _fraud_detection_service
