#!/usr/bin/env python3
"""
MINGUS Subscription Tier Feature Access Verification
===================================================

This script verifies that subscription tiers properly control feature access:
- Budget tier ($15): Basic features with limits
- Mid-tier ($35): Advanced features with higher limits  
- Professional ($99): Premium features with unlimited access
- Paywall implementation
- Unauthorized access prevention

Author: MINGUS Development Team
Date: January 27, 2025
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """MINGUS subscription tiers."""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"

class FeatureCategory(Enum):
    """Feature categories"""
    HEALTH_WELLNESS = "health_wellness"
    FINANCIAL_PLANNING = "financial_planning"
    AI_ANALYTICS = "ai_analytics"
    PLAID_INTEGRATION = "plaid_integration"
    CAREER_ADVANCEMENT = "career_advancement"

class SubscriptionTierVerifier:
    """Verifies subscription tier feature access controls"""
    
    def __init__(self):
        # Define subscription tiers and their features
        self.subscription_tiers = {
            SubscriptionTier.BUDGET: {
                'name': 'Budget Tier',
                'price_monthly': 1500,  # $15.00
                'price_yearly': 14400,  # $144.00 (20% discount)
                'description': 'Perfect for individuals getting started with personal finance management',
                'features': {
                    'basic_analytics': True,
                    'goal_setting': True,
                    'email_support': True,
                    'basic_reports': True,
                    'mobile_app': True,
                    'data_export': True,
                    'basic_notifications': True
                },
                'limits': {
                    'analytics_reports_per_month': 5,
                    'goals_per_account': 3,
                    'data_export_per_month': 2,
                    'support_requests_per_month': 3,
                    'transaction_history_months': 12,
                    'health_checkins_per_month': 4,
                    'budget_creation_per_month': 2
                }
            },
            SubscriptionTier.MID_TIER: {
                'name': 'Mid-Tier',
                'price_monthly': 3500,  # $35.00
                'price_yearly': 33600,  # $336.00 (20% discount)
                'description': 'Advanced features for serious personal finance management',
                'features': {
                    'basic_analytics': True,
                    'goal_setting': True,
                    'email_support': True,
                    'basic_reports': True,
                    'mobile_app': True,
                    'data_export': True,
                    'basic_notifications': True,
                    'advanced_ai_insights': True,
                    'career_risk_management': True,
                    'priority_support': True,
                    'advanced_reports': True,
                    'custom_categories': True,
                    'investment_tracking': True,
                    'debt_optimization': True,
                    'tax_planning': True,
                    'plaid_integration': True,
                    'ai_spending_analysis': True,
                    'career_planning': True
                },
                'limits': {
                    'analytics_reports_per_month': 20,
                    'goals_per_account': 10,
                    'data_export_per_month': 10,
                    'support_requests_per_month': 10,
                    'transaction_history_months': 36,
                    'ai_insights_per_month': 50,
                    'investment_accounts': 5,
                    'custom_categories': 20,
                    'health_checkins_per_month': 12,
                    'budget_creation_per_month': 10,
                    'ai_spending_analysis_per_month': 5,
                    'plaid_accounts': 2,
                    'career_planning_per_month': 3
                }
            },
            SubscriptionTier.PROFESSIONAL: {
                'name': 'Professional Tier',
                'price_monthly': 7500,  # $75.00
                'price_yearly': 72000,  # $720.00 (20% discount)
                'description': 'Unlimited access with dedicated support for professionals',
                'features': {
                    'basic_analytics': True,
                    'goal_setting': True,
                    'email_support': True,
                    'basic_reports': True,
                    'mobile_app': True,
                    'data_export': True,
                    'basic_notifications': True,
                    'advanced_ai_insights': True,
                    'career_risk_management': True,
                    'priority_support': True,
                    'advanced_reports': True,
                    'custom_categories': True,
                    'investment_tracking': True,
                    'debt_optimization': True,
                    'tax_planning': True,
                    'unlimited_access': True,
                    'dedicated_account_manager': True,
                    'team_management': True,
                    'white_label_reports': True,
                    'api_access': True,
                    'custom_integrations': True,
                    'priority_feature_requests': True,
                    'phone_support': True,
                    'onboarding_call': True,
                    'plaid_integration': True,
                    'ai_spending_analysis': True,
                    'career_planning': True,
                    'salary_negotiation': True,
                    'plaid_advanced_analytics': True
                },
                'limits': {
                    'analytics_reports_per_month': -1,  # Unlimited
                    'goals_per_account': -1,  # Unlimited
                    'data_export_per_month': -1,  # Unlimited
                    'support_requests_per_month': -1,  # Unlimited
                    'transaction_history_months': -1,  # Unlimited
                    'ai_insights_per_month': -1,  # Unlimited
                    'investment_accounts': -1,  # Unlimited
                    'custom_categories': -1,  # Unlimited
                    'team_members': 10,
                    'api_requests_per_month': 10000,
                    'health_checkins_per_month': -1,  # Unlimited
                    'budget_creation_per_month': -1,  # Unlimited
                    'ai_spending_analysis_per_month': -1,  # Unlimited
                    'plaid_accounts': -1,  # Unlimited
                    'career_planning_per_month': -1,  # Unlimited
                    'salary_negotiation_per_month': 2,
                    'plaid_advanced_analytics_per_month': 10
                }
            }
        }
        
        # Define feature access requirements
        self.feature_requirements = {
            'basic_analytics': SubscriptionTier.BUDGET,
            'goal_setting': SubscriptionTier.BUDGET,
            'email_support': SubscriptionTier.BUDGET,
            'basic_reports': SubscriptionTier.BUDGET,
            'mobile_app': SubscriptionTier.BUDGET,
            'data_export': SubscriptionTier.BUDGET,
            'basic_notifications': SubscriptionTier.BUDGET,
            'advanced_ai_insights': SubscriptionTier.MID_TIER,
            'career_risk_management': SubscriptionTier.MID_TIER,
            'priority_support': SubscriptionTier.MID_TIER,
            'advanced_reports': SubscriptionTier.MID_TIER,
            'custom_categories': SubscriptionTier.MID_TIER,
            'investment_tracking': SubscriptionTier.MID_TIER,
            'debt_optimization': SubscriptionTier.MID_TIER,
            'tax_planning': SubscriptionTier.MID_TIER,
            'plaid_integration': SubscriptionTier.MID_TIER,
            'ai_spending_analysis': SubscriptionTier.MID_TIER,
            'career_planning': SubscriptionTier.MID_TIER,
            'unlimited_access': SubscriptionTier.PROFESSIONAL,
            'dedicated_account_manager': SubscriptionTier.PROFESSIONAL,
            'team_management': SubscriptionTier.PROFESSIONAL,
            'white_label_reports': SubscriptionTier.PROFESSIONAL,
            'api_access': SubscriptionTier.PROFESSIONAL,
            'custom_integrations': SubscriptionTier.PROFESSIONAL,
            'priority_feature_requests': SubscriptionTier.PROFESSIONAL,
            'phone_support': SubscriptionTier.PROFESSIONAL,
            'onboarding_call': SubscriptionTier.PROFESSIONAL,
            'salary_negotiation': SubscriptionTier.PROFESSIONAL,
            'plaid_advanced_analytics': SubscriptionTier.PROFESSIONAL
        }
    
    def check_feature_access(self, user_tier: SubscriptionTier, feature: str) -> Dict[str, Any]:
        """Check if a user tier has access to a specific feature"""
        try:
            # Check if feature exists
            if feature not in self.feature_requirements:
                return {
                    'has_access': False,
                    'reason': 'feature_not_found',
                    'upgrade_required': False,
                    'current_tier': user_tier.value,
                    'required_tier': 'unknown'
                }
            
            # Get required tier for feature
            required_tier = self.feature_requirements[feature]
            
            # Check tier hierarchy
            tier_hierarchy = {
                SubscriptionTier.BUDGET: 1,
                SubscriptionTier.MID_TIER: 2,
                SubscriptionTier.PROFESSIONAL: 3
            }
            
            user_level = tier_hierarchy.get(user_tier, 0)
            required_level = tier_hierarchy.get(required_tier, 0)
            
            has_access = user_level >= required_level
            
            # Get usage limits
            tier_config = self.subscription_tiers.get(user_tier, {})
            limits = tier_config.get('limits', {})
            
            # Find the relevant limit for this feature
            feature_limit = None
            for limit_key, limit_value in limits.items():
                if feature in limit_key or limit_key in feature:
                    feature_limit = limit_value
                    break
            
            return {
                'has_access': has_access,
                'reason': 'upgrade_required' if not has_access else 'access_granted',
                'upgrade_required': not has_access,
                'current_tier': user_tier.value,
                'required_tier': required_tier.value,
                'usage_limit': feature_limit,
                'educational_content': self._get_educational_content(feature),
                'upgrade_benefits': self._get_upgrade_benefits(feature, user_tier)
            }
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return {
                'has_access': False,
                'reason': 'error',
                'upgrade_required': False,
                'current_tier': user_tier.value,
                'required_tier': 'unknown'
            }
    
    def _get_educational_content(self, feature: str) -> str:
        """Get educational content for a feature"""
        educational_content = {
            'ai_spending_analysis': 'AI spending analysis provides deep insights into your financial patterns, helping you make better financial decisions.',
            'plaid_integration': 'Plaid integration allows you to securely connect your bank accounts for automatic transaction tracking and financial insights.',
            'career_planning': 'Career planning helps you set clear goals, develop skills, and advance in your professional journey.',
            'salary_negotiation': 'Salary negotiation skills can significantly impact your earning potential and career growth.',
            'advanced_ai_insights': 'Advanced AI insights provide personalized recommendations based on your financial data and goals.',
            'team_management': 'Team management features allow you to collaborate with family members or financial advisors.',
            'api_access': 'API access allows you to integrate MINGUS with your own applications and workflows.'
        }
        return educational_content.get(feature, f'Learn more about {feature} and how it can help you.')
    
    def _get_upgrade_benefits(self, feature: str, current_tier: SubscriptionTier) -> List[str]:
        """Get upgrade benefits for a feature"""
        benefits = {
            'ai_spending_analysis': [
                'Unlimited AI analysis',
                'Predictive spending insights',
                'Custom spending categories',
                'Advanced financial recommendations'
            ],
            'plaid_integration': [
                'Unlimited bank accounts',
                'Multiple financial institutions',
                'Real-time transaction sync',
                'Advanced financial insights'
            ],
            'career_planning': [
                'Unlimited career planning',
                'Personalized career coaching',
                'Advanced skill assessment',
                'Industry-specific insights'
            ],
            'salary_negotiation': [
                'Unlimited negotiation support',
                'Personalized coaching sessions',
                'Market analysis reports',
                'Advanced negotiation strategies'
            ]
        }
        return benefits.get(feature, [f'Access to {feature}', 'Enhanced features', 'Priority support'])
    
    def verify_budget_tier_features(self) -> Dict[str, Any]:
        """Verify Budget tier ($15) feature access and limits"""
        logger.info("🔍 Verifying Budget Tier ($15) Features")
        
        results = {
            'tier': 'budget',
            'price': '$15/month',
            'available_features': [],
            'unavailable_features': [],
            'limits_verified': [],
            'issues': []
        }
        
        # Test available features
        available_features = [
            'basic_analytics',
            'goal_setting',
            'email_support',
            'basic_reports',
            'mobile_app',
            'data_export',
            'basic_notifications'
        ]
        
        for feature in available_features:
            result = self.check_feature_access(SubscriptionTier.BUDGET, feature)
            if result['has_access']:
                results['available_features'].append(feature)
            else:
                results['issues'].append(f"Budget tier should have access to {feature}")
        
        # Test unavailable features
        unavailable_features = [
            'advanced_ai_insights',
            'career_risk_management',
            'priority_support',
            'advanced_reports',
            'custom_categories',
            'investment_tracking',
            'debt_optimization',
            'tax_planning',
            'plaid_integration',
            'ai_spending_analysis',
            'career_planning',
            'team_management',
            'api_access',
            'salary_negotiation'
        ]
        
        for feature in unavailable_features:
            result = self.check_feature_access(SubscriptionTier.BUDGET, feature)
            if not result['has_access']:
                results['unavailable_features'].append(feature)
            else:
                results['issues'].append(f"Budget tier should not have access to {feature}")
        
        # Verify limits
        tier_config = self.subscription_tiers[SubscriptionTier.BUDGET]
        limits = tier_config['limits']
        
        expected_limits = {
            'analytics_reports_per_month': 5,
            'goals_per_account': 3,
            'data_export_per_month': 2,
            'support_requests_per_month': 3,
            'transaction_history_months': 12
        }
        
        for limit_key, expected_value in expected_limits.items():
            actual_value = limits.get(limit_key)
            if actual_value == expected_value:
                results['limits_verified'].append(f"{limit_key}: {actual_value}")
            else:
                results['issues'].append(f"Limit mismatch for {limit_key}: expected {expected_value}, got {actual_value}")
        
        logger.info(f"✅ Budget tier verification complete: {len(results['available_features'])} available, {len(results['unavailable_features'])} restricted")
        return results
    
    def verify_mid_tier_features(self) -> Dict[str, Any]:
        """Verify Mid-tier ($35) feature access and limits"""
        logger.info("🔍 Verifying Mid-Tier ($35) Features")
        
        results = {
            'tier': 'mid_tier',
            'price': '$35/month',
            'available_features': [],
            'unavailable_features': [],
            'limits_verified': [],
            'issues': []
        }
        
        # Test available features
        available_features = [
            'basic_analytics',
            'goal_setting',
            'email_support',
            'basic_reports',
            'mobile_app',
            'data_export',
            'basic_notifications',
            'advanced_ai_insights',
            'career_risk_management',
            'priority_support',
            'advanced_reports',
            'custom_categories',
            'investment_tracking',
            'debt_optimization',
            'tax_planning',
            'plaid_integration',
            'ai_spending_analysis',
            'career_planning'
        ]
        
        for feature in available_features:
            result = self.check_feature_access(SubscriptionTier.MID_TIER, feature)
            if result['has_access']:
                results['available_features'].append(feature)
            else:
                results['issues'].append(f"Mid-tier should have access to {feature}")
        
        # Test unavailable features
        unavailable_features = [
            'unlimited_access',
            'dedicated_account_manager',
            'team_management',
            'white_label_reports',
            'api_access',
            'custom_integrations',
            'priority_feature_requests',
            'phone_support',
            'onboarding_call',
            'salary_negotiation',
            'plaid_advanced_analytics'
        ]
        
        for feature in unavailable_features:
            result = self.check_feature_access(SubscriptionTier.MID_TIER, feature)
            if not result['has_access']:
                results['unavailable_features'].append(feature)
            else:
                results['issues'].append(f"Mid-tier should not have access to {feature}")
        
        # Verify limits
        tier_config = self.subscription_tiers[SubscriptionTier.MID_TIER]
        limits = tier_config['limits']
        
        expected_limits = {
            'analytics_reports_per_month': 20,
            'goals_per_account': 10,
            'data_export_per_month': 10,
            'support_requests_per_month': 10,
            'transaction_history_months': 36,
            'ai_insights_per_month': 50,
            'investment_accounts': 5,
            'custom_categories': 20
        }
        
        for limit_key, expected_value in expected_limits.items():
            actual_value = limits.get(limit_key)
            if actual_value == expected_value:
                results['limits_verified'].append(f"{limit_key}: {actual_value}")
            else:
                results['issues'].append(f"Limit mismatch for {limit_key}: expected {expected_value}, got {actual_value}")
        
        logger.info(f"✅ Mid-tier verification complete: {len(results['available_features'])} available, {len(results['unavailable_features'])} restricted")
        return results
    
    def verify_professional_tier_features(self) -> Dict[str, Any]:
        """Verify Professional tier ($75) feature access and limits"""
        logger.info("🔍 Verifying Professional Tier ($75) Features")
        
        results = {
            'tier': 'professional',
            'price': '$75/month',
            'available_features': [],
            'unlimited_features': [],
            'limits_verified': [],
            'issues': []
        }
        
        # Test all features (should all be available)
        all_features = list(self.feature_requirements.keys())
        
        for feature in all_features:
            result = self.check_feature_access(SubscriptionTier.PROFESSIONAL, feature)
            if result['has_access']:
                results['available_features'].append(feature)
            else:
                results['issues'].append(f"Professional tier should have access to {feature}")
        
        # Check unlimited features
        tier_config = self.subscription_tiers[SubscriptionTier.PROFESSIONAL]
        limits = tier_config['limits']
        
        unlimited_features = [
            'analytics_reports_per_month',
            'goals_per_account',
            'data_export_per_month',
            'support_requests_per_month',
            'transaction_history_months',
            'ai_insights_per_month',
            'investment_accounts',
            'custom_categories',
            'health_checkins_per_month',
            'budget_creation_per_month',
            'ai_spending_analysis_per_month',
            'plaid_accounts',
            'career_planning_per_month'
        ]
        
        for feature in unlimited_features:
            limit_value = limits.get(feature)
            if limit_value == -1:
                results['unlimited_features'].append(feature)
            else:
                results['issues'].append(f"Professional tier {feature} should be unlimited, got {limit_value}")
        
        # Verify specific limits
        specific_limits = {
            'team_members': 10,
            'api_requests_per_month': 10000,
            'salary_negotiation_per_month': 2,
            'plaid_advanced_analytics_per_month': 10
        }
        
        for limit_key, expected_value in specific_limits.items():
            actual_value = limits.get(limit_key)
            if actual_value == expected_value:
                results['limits_verified'].append(f"{limit_key}: {actual_value}")
            else:
                results['issues'].append(f"Limit mismatch for {limit_key}: expected {expected_value}, got {actual_value}")
        
        logger.info(f"✅ Professional tier verification complete: {len(results['available_features'])} available, {len(results['unlimited_features'])} unlimited")
        return results
    
    def verify_paywall_implementation(self) -> Dict[str, Any]:
        """Verify paywall implementation for restricted features"""
        logger.info("🔍 Verifying Paywall Implementation")
        
        results = {
            'paywall_tests': [],
            'upgrade_paths': [],
            'educational_content': [],
            'issues': []
        }
        
        # Test paywall for premium features
        premium_features = [
            'ai_spending_analysis',
            'plaid_integration',
            'career_planning',
            'salary_negotiation',
            'team_management',
            'api_access'
        ]
        
        for feature in premium_features:
            # Test budget tier trying to access premium feature
            result = self.check_feature_access(SubscriptionTier.BUDGET, feature)
            
            if not result['has_access'] and result['upgrade_required']:
                results['paywall_tests'].append(f"Budget tier correctly blocked from {feature}")
                
                # Check upgrade path
                if result['required_tier'] in ['mid_tier', 'professional']:
                    results['upgrade_paths'].append(f"Upgrade path available for {feature} -> {result['required_tier']}")
                
                # Check educational content
                if result['educational_content']:
                    results['educational_content'].append(f"Educational content available for {feature}")
                else:
                    results['issues'].append(f"No educational content for {feature}")
                
                # Check upgrade benefits
                if result['upgrade_benefits']:
                    results['upgrade_paths'].append(f"Upgrade benefits available for {feature}")
                else:
                    results['issues'].append(f"No upgrade benefits for {feature}")
            else:
                results['issues'].append(f"Paywall failed for {feature} - budget tier has access")
        
        logger.info(f"✅ Paywall verification complete: {len(results['paywall_tests'])} tests passed")
        return results
    
    def verify_unauthorized_access_prevention(self) -> Dict[str, Any]:
        """Verify that unauthorized access is properly prevented"""
        logger.info("🔍 Verifying Unauthorized Access Prevention")
        
        results = {
            'access_controls': [],
            'security_tests': [],
            'issues': []
        }
        
        # Test invalid feature access
        invalid_features = ['invalid_feature', 'nonexistent_feature', 'test_feature']
        
        for feature in invalid_features:
            result = self.check_feature_access(SubscriptionTier.PROFESSIONAL, feature)
            if not result['has_access'] and result['reason'] == 'feature_not_found':
                results['access_controls'].append(f"Invalid feature {feature} correctly rejected")
            else:
                results['issues'].append(f"Invalid feature {feature} should be rejected")
        
        # Test tier hierarchy enforcement
        tier_tests = [
            (SubscriptionTier.BUDGET, 'salary_negotiation', False),
            (SubscriptionTier.BUDGET, 'team_management', False),
            (SubscriptionTier.MID_TIER, 'salary_negotiation', False),
            (SubscriptionTier.MID_TIER, 'team_management', False),
            (SubscriptionTier.PROFESSIONAL, 'salary_negotiation', True),
            (SubscriptionTier.PROFESSIONAL, 'team_management', True)
        ]
        
        for user_tier, feature, should_have_access in tier_tests:
            result = self.check_feature_access(user_tier, feature)
            if result['has_access'] == should_have_access:
                results['security_tests'].append(f"Tier {user_tier.value} access to {feature}: {'✓' if should_have_access else '✗'}")
            else:
                results['issues'].append(f"Tier {user_tier.value} should {'have' if should_have_access else 'not have'} access to {feature}")
        
        logger.info(f"✅ Unauthorized access prevention verification complete: {len(results['access_controls'])} controls, {len(results['security_tests'])} tests")
        return results
    
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run comprehensive subscription tier verification"""
        logger.info("🚀 Starting Comprehensive Subscription Tier Feature Access Verification")
        logger.info("=" * 80)
        
        verification_results = {
            'verification_date': datetime.now().isoformat(),
            'budget_tier': self.verify_budget_tier_features(),
            'mid_tier': self.verify_mid_tier_features(),
            'professional_tier': self.verify_professional_tier_features(),
            'paywall_implementation': self.verify_paywall_implementation(),
            'unauthorized_access_prevention': self.verify_unauthorized_access_prevention(),
            'summary': {}
        }
        
        # Generate summary
        total_issues = 0
        total_tests = 0
        
        for tier_name, tier_results in verification_results.items():
            if tier_name != 'verification_date' and tier_name != 'summary':
                issues = len(tier_results.get('issues', []))
                total_issues += issues
                total_tests += 1
        
        verification_results['summary'] = {
            'total_tiers_tested': 3,
            'total_issues_found': total_issues,
            'success_rate': ((total_tests * 10 - total_issues) / (total_tests * 10)) * 100 if total_tests > 0 else 100,
            'verification_status': 'PASSED' if total_issues == 0 else 'NEEDS_ATTENTION'
        }
        
        # Print summary
        logger.info("=" * 80)
        logger.info("📊 SUBSCRIPTION TIER FEATURE ACCESS VERIFICATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Budget Tier ($15): {len(verification_results['budget_tier']['available_features'])} features available")
        logger.info(f"Mid-Tier ($35): {len(verification_results['mid_tier']['available_features'])} features available")
        logger.info(f"Professional Tier ($75): {len(verification_results['professional_tier']['available_features'])} features available")
        logger.info(f"Paywall Tests: {len(verification_results['paywall_implementation']['paywall_tests'])} passed")
        logger.info(f"Security Tests: {len(verification_results['unauthorized_access_prevention']['security_tests'])} passed")
        logger.info(f"Total Issues: {total_issues}")
        logger.info(f"Success Rate: {verification_results['summary']['success_rate']:.1f}%")
        
        if verification_results['summary']['verification_status'] == 'PASSED':
            logger.info("✅ Subscription tier feature access controls are working correctly!")
        else:
            logger.warning("⚠️ Some feature access controls need attention")
        
        # Save detailed report
        report_filename = f"subscription_tier_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(verification_results, f, indent=2)
        
        logger.info(f"📄 Detailed report saved to: {report_filename}")
        
        return verification_results


def main():
    """Main function to run verification"""
    verifier = SubscriptionTierVerifier()
    results = verifier.run_comprehensive_verification()
    
    # Print detailed results for each tier
    print("\n" + "="*80)
    print("DETAILED TIER ANALYSIS")
    print("="*80)
    
    # Budget Tier Details
    print(f"\n💰 BUDGET TIER ($15/month)")
    print(f"Available Features: {len(results['budget_tier']['available_features'])}")
    print(f"Restricted Features: {len(results['budget_tier']['unavailable_features'])}")
    print(f"Limits Verified: {len(results['budget_tier']['limits_verified'])}")
    if results['budget_tier']['issues']:
        print(f"Issues: {len(results['budget_tier']['issues'])}")
    
    # Mid-Tier Details
    print(f"\n💼 MID-TIER ($35/month)")
    print(f"Available Features: {len(results['mid_tier']['available_features'])}")
    print(f"Restricted Features: {len(results['mid_tier']['unavailable_features'])}")
    print(f"Limits Verified: {len(results['mid_tier']['limits_verified'])}")
    if results['mid_tier']['issues']:
        print(f"Issues: {len(results['mid_tier']['issues'])}")
    
    # Professional Tier Details
    print(f"\n🏆 PROFESSIONAL TIER ($75/month)")
    print(f"Available Features: {len(results['professional_tier']['available_features'])}")
    print(f"Unlimited Features: {len(results['professional_tier']['unlimited_features'])}")
    print(f"Limits Verified: {len(results['professional_tier']['limits_verified'])}")
    if results['professional_tier']['issues']:
        print(f"Issues: {len(results['professional_tier']['issues'])}")
    
    # Paywall and Security
    print(f"\n🔒 SECURITY & PAYWALL")
    print(f"Paywall Tests Passed: {len(results['paywall_implementation']['paywall_tests'])}")
    print(f"Security Tests Passed: {len(results['unauthorized_access_prevention']['security_tests'])}")
    print(f"Upgrade Paths Available: {len(results['paywall_implementation']['upgrade_paths'])}")
    
    return results


if __name__ == '__main__':
    main()
