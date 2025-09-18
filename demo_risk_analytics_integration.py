#!/usr/bin/env python3
"""
Risk Analytics Integration Demo

This script demonstrates the complete risk-based career protection analytics system,
showing how risk assessments trigger recommendations and track outcomes.

Features Demonstrated:
- Risk assessment tracking (AI risk, layoff risk, income risk)
- Risk-triggered job recommendations
- Emergency unlock system for high-risk users
- Prediction accuracy measurement
- Career protection outcome tracking
- A/B testing for risk optimization
- Risk dashboard and reporting
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import risk analytics components
from backend.analytics.risk_analytics_integration import (
    RiskAnalyticsIntegration,
    RiskAssessmentData,
    RiskOutcomeData,
    RiskLevel,
    OutcomeType
)

class RiskAnalyticsDemo:
    """Demonstration of risk analytics integration capabilities"""
    
    def __init__(self):
        """Initialize the demo"""
        self.risk_analytics = RiskAnalyticsIntegration("demo_risk_analytics.db")
        self.demo_users = [
            "demo_user_1",  # High AI risk user
            "demo_user_2",  # High layoff risk user
            "demo_user_3",  # Low risk user
            "demo_user_4",  # Critical risk user
        ]
    
    async def run_complete_demo(self):
        """Run the complete risk analytics demonstration"""
        print("🚀 Starting Risk Analytics Integration Demo")
        print("=" * 60)
        
        # Demo 1: Risk Assessment Tracking
        await self.demo_risk_assessments()
        
        # Demo 2: Risk-Triggered Recommendations
        await self.demo_risk_recommendations()
        
        # Demo 3: Emergency Unlock System
        await self.demo_emergency_unlocks()
        
        # Demo 4: Prediction Accuracy Tracking
        await self.demo_prediction_accuracy()
        
        # Demo 5: Career Protection Outcomes
        await self.demo_career_protection_outcomes()
        
        # Demo 6: A/B Testing Framework
        await self.demo_ab_testing()
        
        # Demo 7: Risk Journey Analysis
        await self.demo_risk_journey_analysis()
        
        # Demo 8: Dashboard and Reporting
        await self.demo_dashboard_reporting()
        
        print("\n✅ Risk Analytics Integration Demo Completed Successfully!")
        print("=" * 60)
    
    async def demo_risk_assessments(self):
        """Demonstrate risk assessment tracking"""
        print("\n📊 Demo 1: Risk Assessment Tracking")
        print("-" * 40)
        
        # AI Risk Assessment
        ai_risk_data = RiskAssessmentData(
            user_id=self.demo_users[0],
            assessment_type="ai_risk",
            overall_risk=0.75,
            risk_triggers=["Manufacturing industry", "Low AI tool usage", "Outdated skills"],
            risk_breakdown={
                "industry_risk": 0.3,
                "automation_risk": 0.25,
                "skills_risk": 0.2
            },
            timeline_urgency="3_months",
            assessment_timestamp=datetime.now(),
            confidence_score=0.85,
            risk_factors={
                "industry": 0.3,
                "automation_level": 0.25,
                "ai_usage": 0.2
            }
        )
        
        result = await self.risk_analytics.track_risk_assessment_completed(
            self.demo_users[0], ai_risk_data
        )
        print(f"✓ AI Risk Assessment tracked: {result}")
        
        # Layoff Risk Assessment
        layoff_risk_data = RiskAssessmentData(
            user_id=self.demo_users[1],
            assessment_type="layoff_risk",
            overall_risk=0.65,
            risk_triggers=["Small company", "Recent layoffs", "Below expectations"],
            risk_breakdown={
                "company_size_risk": 0.2,
                "tenure_risk": 0.15,
                "performance_risk": 0.2,
                "company_health_risk": 0.1
            },
            timeline_urgency="6_months",
            assessment_timestamp=datetime.now(),
            confidence_score=0.78,
            risk_factors={
                "company_size": 0.2,
                "tenure": 0.15,
                "performance": 0.2,
                "company_health": 0.1
            }
        )
        
        result = await self.risk_analytics.track_risk_assessment_completed(
            self.demo_users[1], layoff_risk_data
        )
        print(f"✓ Layoff Risk Assessment tracked: {result}")
        
        # Low Risk Assessment
        low_risk_data = RiskAssessmentData(
            user_id=self.demo_users[2],
            assessment_type="ai_risk",
            overall_risk=0.25,
            risk_triggers=["AI-resistant skills", "High AI usage"],
            risk_breakdown={
                "industry_risk": 0.1,
                "automation_risk": 0.05,
                "skills_risk": 0.1
            },
            timeline_urgency="1_year",
            assessment_timestamp=datetime.now(),
            confidence_score=0.9,
            risk_factors={
                "industry": 0.1,
                "automation_level": 0.05,
                "ai_usage": 0.1
            }
        )
        
        result = await self.risk_analytics.track_risk_assessment_completed(
            self.demo_users[2], low_risk_data
        )
        print(f"✓ Low Risk Assessment tracked: {result}")
    
    async def demo_risk_recommendations(self):
        """Demonstrate risk-triggered recommendations"""
        print("\n🎯 Demo 2: Risk-Triggered Recommendations")
        print("-" * 40)
        
        # High AI Risk Recommendations
        ai_risk_data = RiskAssessmentData(
            user_id=self.demo_users[0],
            assessment_type="ai_risk",
            overall_risk=0.75,
            risk_triggers=["High-risk industry", "Low AI usage"],
            risk_breakdown={"industry_risk": 0.4, "automation_risk": 0.35},
            timeline_urgency="3_months",
            assessment_timestamp=datetime.now(),
            confidence_score=0.85,
            risk_factors={"industry": 0.4, "automation": 0.35}
        )
        
        ai_recommendations = {
            "jobs": [
                {
                    "job_id": "ai_safe_job_1",
                    "tier": "optimal",
                    "score": 8.5,
                    "salary_increase_potential": 15000,
                    "success_probability": 0.85,
                    "ai_resistance_score": 0.9
                },
                {
                    "job_id": "ai_safe_job_2",
                    "tier": "stretch",
                    "score": 7.2,
                    "salary_increase_potential": 25000,
                    "success_probability": 0.65,
                    "ai_resistance_score": 0.8
                }
            ],
            "success_probability": 0.75,
            "risk_mitigation_strategies": [
                "Upskill in AI-resistant areas",
                "Develop human-centric skills",
                "Build creative problem-solving abilities"
            ]
        }
        
        result = await self.risk_analytics.track_risk_recommendation_triggered(
            self.demo_users[0], ai_risk_data, ai_recommendations
        )
        print(f"✓ AI Risk Recommendations tracked: {result}")
        print(f"  - Generated {len(ai_recommendations['jobs'])} job recommendations")
        print(f"  - Success probability: {ai_recommendations['success_probability']}")
        
        # Layoff Risk Recommendations
        layoff_risk_data = RiskAssessmentData(
            user_id=self.demo_users[1],
            assessment_type="layoff_risk",
            overall_risk=0.65,
            risk_triggers=["Small company", "Recent layoffs"],
            risk_breakdown={"company_size_risk": 0.2, "layoff_risk": 0.3, "performance_risk": 0.15},
            timeline_urgency="6_months",
            assessment_timestamp=datetime.now(),
            confidence_score=0.78,
            risk_factors={"company_size": 0.2, "recent_layoffs": 0.3, "performance": 0.15}
        )
        
        layoff_recommendations = {
            "jobs": [
                {
                    "job_id": "stable_job_1",
                    "tier": "optimal",
                    "score": 8.0,
                    "salary_increase_potential": 12000,
                    "success_probability": 0.8,
                    "company_stability_score": 0.9
                },
                {
                    "job_id": "stable_job_2",
                    "tier": "safe",
                    "score": 7.5,
                    "salary_increase_potential": 8000,
                    "success_probability": 0.9,
                    "company_stability_score": 0.95
                }
            ],
            "success_probability": 0.85,
            "risk_mitigation_strategies": [
                "Target larger, more stable companies",
                "Build emergency fund",
                "Network in target industries"
            ]
        }
        
        result = await self.risk_analytics.track_risk_recommendation_triggered(
            self.demo_users[1], layoff_risk_data, layoff_recommendations
        )
        print(f"✓ Layoff Risk Recommendations tracked: {result}")
        print(f"  - Generated {len(layoff_recommendations['jobs'])} job recommendations")
        print(f"  - Success probability: {layoff_recommendations['success_probability']}")
    
    async def demo_emergency_unlocks(self):
        """Demonstrate emergency unlock system"""
        print("\n🚨 Demo 3: Emergency Unlock System")
        print("-" * 40)
        
        # Critical Risk User - Emergency Unlock
        critical_risk_data = RiskAssessmentData(
            user_id=self.demo_users[3],
            assessment_type="ai_risk",
            overall_risk=0.85,
            risk_triggers=["Critical industry risk", "No AI skills", "Outdated role"],
            risk_breakdown={"industry_risk": 0.4, "automation_risk": 0.3, "skills_risk": 0.15},
            timeline_urgency="immediate",
            assessment_timestamp=datetime.now(),
            confidence_score=0.95,
            risk_factors={"industry": 0.4, "automation": 0.3, "skills": 0.15}
        )
        
        # Track critical risk assessment
        await self.risk_analytics.track_risk_assessment_completed(
            self.demo_users[3], critical_risk_data
        )
        
        # Emergency unlock data
        emergency_unlock_data = {
            "unlock_type": "premium_features",
            "risk_score": 0.85,
            "features_unlocked": [
                "advanced_job_search",
                "priority_support",
                "salary_negotiation_tools",
                "skill_development_plan",
                "network_expansion_tools"
            ],
            "time_spent": 600,  # 10 minutes
            "unlock_reason": "Critical risk detected"
        }
        
        result = await self.risk_analytics.track_emergency_unlock_usage(
            self.demo_users[3], emergency_unlock_data
        )
        print(f"✓ Emergency Unlock tracked: {result}")
        print(f"  - Risk score: {emergency_unlock_data['risk_score']}")
        print(f"  - Features unlocked: {len(emergency_unlock_data['features_unlocked'])}")
        print(f"  - Unlock reason: {emergency_unlock_data['unlock_reason']}")
    
    async def demo_prediction_accuracy(self):
        """Demonstrate prediction accuracy tracking"""
        print("\n🎯 Demo 4: Prediction Accuracy Tracking")
        print("-" * 40)
        
        # Simulate prediction vs actual outcome for AI risk user
        predicted_risk = {
            "overall_risk": 0.75,
            "timeline_urgency": "3_months",
            "risk_factors": {"industry": 0.3, "automation": 0.25, "skills": 0.2}
        }
        
        actual_outcome = {
            "outcome_type": "proactive_switch",
            "days_from_prediction": 45,
            "risk_realized": 0.8,
            "success_factors": ["early_warning", "quick_action", "skill_development"],
            "salary_improvement": 15000,
            "career_advancement": True
        }
        
        result = await self.risk_analytics.track_risk_prediction_accuracy(
            self.demo_users[0], predicted_risk, actual_outcome
        )
        print(f"✓ Prediction Accuracy tracked: {result}")
        print(f"  - Predicted risk: {predicted_risk['overall_risk']}")
        print(f"  - Actual risk realized: {actual_outcome['risk_realized']}")
        print(f"  - Outcome: {actual_outcome['outcome_type']}")
        print(f"  - Time to outcome: {actual_outcome['days_from_prediction']} days")
        
        # Simulate prediction vs actual outcome for layoff risk user
        predicted_layoff_risk = {
            "overall_risk": 0.65,
            "timeline_urgency": "6_months",
            "risk_factors": {"company_size": 0.2, "recent_layoffs": 0.3, "performance": 0.15}
        }
        
        actual_layoff_outcome = {
            "outcome_type": "job_saved",
            "days_from_prediction": 120,
            "risk_realized": 0.3,  # Lower than predicted due to proactive action
            "success_factors": ["early_warning", "performance_improvement", "skill_upgrade"],
            "salary_improvement": 8000,
            "career_advancement": True
        }
        
        result = await self.risk_analytics.track_risk_prediction_accuracy(
            self.demo_users[1], predicted_layoff_risk, actual_layoff_outcome
        )
        print(f"✓ Layoff Prediction Accuracy tracked: {result}")
        print(f"  - Predicted risk: {predicted_layoff_risk['overall_risk']}")
        print(f"  - Actual risk realized: {actual_layoff_outcome['risk_realized']}")
        print(f"  - Outcome: {actual_layoff_outcome['outcome_type']}")
        print(f"  - Time to outcome: {actual_layoff_outcome['days_from_prediction']} days")
    
    async def demo_career_protection_outcomes(self):
        """Demonstrate career protection outcome tracking"""
        print("\n🛡️ Demo 5: Career Protection Outcomes")
        print("-" * 40)
        
        # AI Risk User - Proactive Switch Outcome
        ai_outcome_data = {
            "outcome_type": "proactive_switch",
            "risk_prediction_accuracy": 0.85,
            "time_to_outcome_days": 45,
            "salary_impact": 15000,
            "career_advancement_score": 0.8,
            "skills_improvement_score": 0.75,
            "network_expansion_score": 0.7,
            "success_factors": {
                "early_warning": 0.3,
                "quick_action": 0.25,
                "skill_development": 0.25,
                "network_help": 0.2
            },
            "job_quality_improvement": 0.8,
            "work_life_balance_improvement": 0.6
        }
        
        result = await self.risk_analytics.track_career_protection_outcomes(
            self.demo_users[0], ai_outcome_data
        )
        print(f"✓ AI Risk Career Protection tracked: {result}")
        print(f"  - Outcome: {ai_outcome_data['outcome_type']}")
        print(f"  - Salary impact: ${ai_outcome_data['salary_impact']:,}")
        print(f"  - Time to outcome: {ai_outcome_data['time_to_outcome_days']} days")
        
        # Layoff Risk User - Job Saved Outcome
        layoff_outcome_data = {
            "outcome_type": "job_saved",
            "risk_prediction_accuracy": 0.78,
            "time_to_outcome_days": 120,
            "salary_impact": 8000,
            "career_advancement_score": 0.7,
            "skills_improvement_score": 0.8,
            "network_expansion_score": 0.6,
            "success_factors": {
                "early_warning": 0.4,
                "performance_improvement": 0.3,
                "skill_upgrade": 0.2,
                "relationship_building": 0.1
            },
            "job_security_improvement": 0.9,
            "company_stability_score": 0.85
        }
        
        result = await self.risk_analytics.track_career_protection_outcomes(
            self.demo_users[1], layoff_outcome_data
        )
        print(f"✓ Layoff Risk Career Protection tracked: {result}")
        print(f"  - Outcome: {layoff_outcome_data['outcome_type']}")
        print(f"  - Salary impact: ${layoff_outcome_data['salary_impact']:,}")
        print(f"  - Time to outcome: {layoff_outcome_data['time_to_outcome_days']} days")
    
    async def demo_ab_testing(self):
        """Demonstrate A/B testing framework"""
        print("\n🧪 Demo 6: A/B Testing Framework")
        print("-" * 40)
        
        # Create risk threshold optimization test
        test_name = "Risk Threshold Optimization Test"
        threshold_variants = [0.5, 0.6, 0.7, 0.8]
        
        test_id = await self.risk_analytics.optimize_risk_trigger_thresholds(
            test_name, threshold_variants
        )
        print(f"✓ A/B Test created: {test_id}")
        print(f"  - Test name: {test_name}")
        print(f"  - Threshold variants: {threshold_variants}")
        
        # Simulate user participation in A/B test
        for i, user_id in enumerate(self.demo_users):
            risk_score = 0.5 + (i * 0.1)  # Varying risk scores
            variant = f"threshold_{threshold_variants[i % len(threshold_variants)]}"
            
            # Record user participation
            await self.risk_analytics.risk_ab_testing.record_risk_threshold_test(
                user_id, risk_score, test_id, variant
            )
            print(f"  - User {user_id} assigned to variant {variant} (risk: {risk_score:.1f})")
    
    async def demo_risk_journey_analysis(self):
        """Demonstrate risk journey analysis"""
        print("\n🛤️ Demo 7: Risk Journey Analysis")
        print("-" * 40)
        
        # Analyze risk journey for AI risk user
        journey_analysis = await self.risk_analytics.analyze_risk_to_recommendation_flow(
            self.demo_users[0], 30
        )
        
        print(f"✓ Risk Journey Analysis completed")
        print(f"  - User: {journey_analysis['user_id']}")
        print(f"  - Analysis period: {journey_analysis['analysis_period_days']} days")
        print(f"  - Flow steps: {journey_analysis['flow_steps']}")
        
        if 'flow_analysis' in journey_analysis:
            flow_analysis = journey_analysis['flow_analysis']
            print(f"  - Unique steps: {flow_analysis.get('unique_steps', 0)}")
            print(f"  - Most common step: {flow_analysis.get('most_common_step', 'N/A')}")
        
        # Measure early warning effectiveness
        effectiveness = await self.risk_analytics.measure_early_warning_effectiveness(30)
        
        if 'error' not in effectiveness:
            print(f"✓ Early Warning Effectiveness measured")
            print(f"  - Analysis period: {effectiveness['analysis_period_days']} days")
            print(f"  - Total warnings: {effectiveness['total_warnings']}")
            print(f"  - Accuracy rate: {effectiveness['accuracy_rate']:.2%}")
            print(f"  - Proactive action rate: {effectiveness['proactive_action_rate']:.2%}")
        else:
            print(f"  - Early warning data: {effectiveness['error']}")
    
    async def demo_dashboard_reporting(self):
        """Demonstrate dashboard and reporting capabilities"""
        print("\n📊 Demo 8: Dashboard and Reporting")
        print("-" * 40)
        
        # Simulate dashboard data
        dashboard_data = {
            "analysis_period_days": 30,
            "total_risk_assessments": 4,
            "high_risk_users": 2,
            "emergency_unlocks_granted": 1,
            "prediction_accuracy": 0.82,
            "career_protection_success_rate": 0.75,
            "early_warning_effectiveness": 0.78,
            "active_ab_tests": 1,
            "risk_trends": {
                "ai_risk_trend": "stable",
                "layoff_risk_trend": "decreasing",
                "income_risk_trend": "stable"
            },
            "user_segments": {
                "high_risk_high_engagement": 1,
                "high_risk_low_engagement": 1,
                "low_risk_high_engagement": 1,
                "low_risk_low_engagement": 1
            }
        }
        
        print("✓ Risk Analytics Dashboard Overview:")
        print(f"  - Total risk assessments: {dashboard_data['total_risk_assessments']}")
        print(f"  - High-risk users: {dashboard_data['high_risk_users']}")
        print(f"  - Emergency unlocks granted: {dashboard_data['emergency_unlocks_granted']}")
        print(f"  - Prediction accuracy: {dashboard_data['prediction_accuracy']:.1%}")
        print(f"  - Career protection success rate: {dashboard_data['career_protection_success_rate']:.1%}")
        print(f"  - Early warning effectiveness: {dashboard_data['early_warning_effectiveness']:.1%}")
        
        print("\n✓ Risk Trends:")
        for trend, direction in dashboard_data['risk_trends'].items():
            print(f"  - {trend.replace('_', ' ').title()}: {direction}")
        
        print("\n✓ User Segments:")
        for segment, count in dashboard_data['user_segments'].items():
            print(f"  - {segment.replace('_', ' ').title()}: {count} users")
        
        # Generate summary report
        summary_report = {
            "demo_summary": {
                "total_users": len(self.demo_users),
                "risk_assessments_tracked": 4,
                "recommendations_generated": 4,
                "emergency_unlocks": 1,
                "outcomes_tracked": 2,
                "ab_tests_created": 1
            },
            "key_insights": [
                "High-risk users receive immediate attention and emergency unlocks",
                "Risk-triggered recommendations show high success probability",
                "Early warning system enables proactive career protection",
                "A/B testing framework allows continuous optimization",
                "Prediction accuracy tracking enables model improvement"
            ],
            "recommendations": [
                "Continue monitoring high-risk users closely",
                "Expand emergency unlock features based on usage patterns",
                "Optimize risk thresholds based on A/B test results",
                "Improve prediction accuracy through model retraining",
                "Enhance early warning communication effectiveness"
            ]
        }
        
        print("\n✓ Demo Summary Report:")
        print(f"  - Total users: {summary_report['demo_summary']['total_users']}")
        print(f"  - Risk assessments tracked: {summary_report['demo_summary']['risk_assessments_tracked']}")
        print(f"  - Recommendations generated: {summary_report['demo_summary']['recommendations_generated']}")
        print(f"  - Emergency unlocks: {summary_report['demo_summary']['emergency_unlocks']}")
        print(f"  - Outcomes tracked: {summary_report['demo_summary']['outcomes_tracked']}")
        print(f"  - A/B tests created: {summary_report['demo_summary']['ab_tests_created']}")
        
        print("\n✓ Key Insights:")
        for insight in summary_report['key_insights']:
            print(f"  - {insight}")
        
        print("\n✓ Recommendations:")
        for recommendation in summary_report['recommendations']:
            print(f"  - {recommendation}")

async def main():
    """Main demo execution function"""
    demo = RiskAnalyticsDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())
