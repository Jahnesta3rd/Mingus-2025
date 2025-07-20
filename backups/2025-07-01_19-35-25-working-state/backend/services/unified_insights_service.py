"""
Unified Insights Service
Aggregates data from multiple services to provide comprehensive insights and recommendations
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from ..integrations.financial_planning_integration import FinancialPlanningIntegration
from ..integrations.recommendations_integration import RecommendationsIntegration
from .health_correlation_service import HealthCorrelationService

logger = logging.getLogger(__name__)

class InsightCategory(Enum):
    CAREER = "career"
    FINANCIAL = "financial"
    HEALTH = "health"
    RELATIONSHIP = "relationship"
    EMERGENCY = "emergency"

class InsightSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Insight:
    """Data class for individual insights"""
    id: str
    category: InsightCategory
    title: str
    description: str
    severity: InsightSeverity
    priority: int  # 1-10, higher is more important
    recommendations: List[str]
    actionable: bool
    estimated_impact: str  # e.g., "$500/month savings", "30% risk reduction"
    time_horizon: str  # e.g., "immediate", "1-3 months", "6+ months"
    source_service: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Recommendation:
    """Data class for actionable recommendations"""
    id: str
    insight_id: str
    title: str
    description: str
    action_type: str  # e.g., "budget_adjustment", "skill_development", "insurance_purchase"
    estimated_cost: Optional[float] = None
    estimated_savings: Optional[float] = None
    time_required: str = "varies"
    difficulty: str = "medium"  # easy, medium, hard
    priority: int = 5
    completed: bool = False

class UnifiedInsightsService:
    """
    Unified service that aggregates insights from multiple sources:
    - Financial Planning Integration
    - Recommendations Integration  
    - Health Correlation Service
    
    Provides personalized insights and actionable recommendations
    """
    
    def __init__(self):
        self.financial_planning = FinancialPlanningIntegration()
        self.recommendations = RecommendationsIntegration()
        # Create a placeholder database session for HealthCorrelationService
        from sqlalchemy.orm import Session
        from sqlalchemy import create_engine
        engine = create_engine('sqlite:///:memory:')
        placeholder_session = Session(engine)
        self.health_correlation = HealthCorrelationService(placeholder_session)
        
        # Insight priority weights
        self.category_weights = {
            InsightCategory.EMERGENCY: 10,
            InsightCategory.FINANCIAL: 8,
            InsightCategory.CAREER: 7,
            InsightCategory.HEALTH: 6,
            InsightCategory.RELATIONSHIP: 5
        }
        
        # Severity multipliers
        self.severity_multipliers = {
            InsightSeverity.CRITICAL: 2.0,
            InsightSeverity.HIGH: 1.5,
            InsightSeverity.MEDIUM: 1.0,
            InsightSeverity.LOW: 0.5
        }
    
    def get_user_insights(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get comprehensive insights for a user
        Returns aggregated insights from all services
        """
        try:
            # Get insights from each service
            financial_insights = self._get_financial_insights(user_id)
            career_insights = self._get_career_insights(user_id)
            health_insights = self._get_health_insights(user_id)
            
            # Combine and prioritize all insights
            all_insights = financial_insights + career_insights + health_insights
            prioritized_insights = self._prioritize_insights(all_insights)
            
            # Get top insights
            top_insights = prioritized_insights[:limit]
            
            # Generate summary statistics
            summary = self._generate_insights_summary(prioritized_insights)
            
            return {
                "insights": [insight.__dict__ for insight in top_insights],
                "summary": summary,
                "total_count": len(prioritized_insights),
                "categories": self._get_category_breakdown(prioritized_insights),
                "severity_distribution": self._get_severity_distribution(prioritized_insights),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user insights: {str(e)}")
            return {"error": f"Failed to get insights: {str(e)}"}
    
    def get_priority_insights(self, user_id: int, limit: int = 5) -> List[Insight]:
        """
        Get top priority insights that require immediate attention
        """
        try:
            all_insights = self.get_user_insights(user_id, limit=50)
            if "error" in all_insights:
                return []
            
            insights = [Insight(**insight) for insight in all_insights["insights"]]
            
            # Filter for high priority insights
            priority_insights = [
                insight for insight in insights 
                if insight.priority >= 7 or insight.severity in [InsightSeverity.HIGH, InsightSeverity.CRITICAL]
            ]
            
            # Sort by priority and return top results
            priority_insights.sort(key=lambda x: x.priority, reverse=True)
            return priority_insights[:limit]
            
        except Exception as e:
            logger.error(f"Error getting priority insights: {str(e)}")
            return []
    
    def get_insight_recommendations(self, user_id: int, insight_id: Optional[str] = None) -> List[Recommendation]:
        """
        Get actionable recommendations for insights
        """
        try:
            if insight_id:
                # Get recommendations for specific insight
                return self._get_recommendations_for_insight(user_id, insight_id)
            else:
                # Get all recommendations
                return self._get_all_recommendations(user_id)
                
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def get_insights_dashboard(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data including insights, recommendations, and metrics
        """
        try:
            # Get all insights
            insights_data = self.get_user_insights(user_id, limit=20)
            
            # Get priority insights
            priority_insights = self.get_priority_insights(user_id, limit=5)
            
            # Get recommendations
            recommendations = self.get_insight_recommendations(user_id)
            
            # Calculate metrics
            metrics = self._calculate_dashboard_metrics(user_id, insights_data, recommendations)
            
            return {
                "insights": insights_data,
                "priority_insights": [insight.__dict__ for insight in priority_insights],
                "recommendations": [rec.__dict__ for rec in recommendations],
                "metrics": metrics,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting insights dashboard: {str(e)}")
            return {"error": f"Failed to get dashboard: {str(e)}"}
    
    def _get_financial_insights(self, user_id: int) -> List[Insight]:
        """Get insights from financial planning integration"""
        insights = []
        
        try:
            # Get financial health score
            health_score = self.financial_planning.get_financial_health_score(user_id)
            if "error" not in health_score:
                score = health_score.get("overall_score", 0)
                
                if score < 50:
                    insights.append(Insight(
                        id=f"financial_health_{user_id}",
                        category=InsightCategory.FINANCIAL,
                        title="Financial Health Needs Attention",
                        description=f"Your financial health score is {score:.0f}/100. This indicates areas for improvement in your financial planning.",
                        severity=InsightSeverity.HIGH if score < 30 else InsightSeverity.MEDIUM,
                        priority=8,
                        recommendations=[
                            "Review your emergency fund status",
                            "Analyze your spending patterns",
                            "Consider debt consolidation options",
                            "Increase your savings rate"
                        ],
                        actionable=True,
                        estimated_impact="Potential 20-30% improvement in financial stability",
                        time_horizon="3-6 months",
                        source_service="financial_planning",
                        created_at=datetime.now()
                    ))
            
            # Get emergency fund insights
            emergency_insights = self._get_emergency_fund_insights(user_id)
            insights.extend(emergency_insights)
            
        except Exception as e:
            logger.error(f"Error getting financial insights: {str(e)}")
        
        return insights
    
    def _get_career_insights(self, user_id: int) -> List[Insight]:
        """Get insights from recommendations integration"""
        insights = []
        
        try:
            # Get job security assessment
            job_security = self.recommendations.get_job_security_assessment(user_id)
            if "error" not in job_security:
                risk_level = job_security.get("overall_risk", {}).get("risk_level", "low")
                
                if risk_level in ["high", "very_high"]:
                    insights.append(Insight(
                        id=f"job_security_{user_id}",
                        category=InsightCategory.CAREER,
                        title="Career Security Alert",
                        description=f"Your job security risk level is {risk_level}. Consider proactive measures to protect your career and finances.",
                        severity=InsightSeverity.HIGH if risk_level == "very_high" else InsightSeverity.MEDIUM,
                        priority=9 if risk_level == "very_high" else 7,
                        recommendations=[
                            "Build emergency fund to 9-12 months of expenses",
                            "Start networking and skill development",
                            "Review insurance coverage",
                            "Begin career transition planning"
                        ],
                        actionable=True,
                        estimated_impact="Reduces financial risk by 60-80%",
                        time_horizon="1-3 months",
                        source_service="recommendations",
                        created_at=datetime.now()
                    ))
            
            # Get skills development insights
            skills_insights = self._get_skills_insights(user_id)
            insights.extend(skills_insights)
            
        except Exception as e:
            logger.error(f"Error getting career insights: {str(e)}")
        
        return insights
    
    def _get_health_insights(self, user_id: int) -> List[Insight]:
        """Get insights from health correlation service"""
        insights = []
        
        try:
            # Get health-based budget recommendations
            health_recommendations = self.health_correlation.generate_health_based_budget_recommendations(user_id)
            
            if "budget_adjustments" in health_recommendations:
                for adjustment in health_recommendations["budget_adjustments"]:
                    if adjustment["priority"] == "high":
                        insights.append(Insight(
                            id=f"health_budget_{user_id}_{adjustment['type']}",
                            category=InsightCategory.HEALTH,
                            title="Health-Based Budget Adjustment",
                            description=adjustment["description"],
                            severity=InsightSeverity.MEDIUM,
                            priority=6,
                            recommendations=[
                                "Allocate budget for health activities",
                                "Track stress-spending correlations",
                                "Implement wellness routines",
                                "Monitor health-spending patterns"
                            ],
                            actionable=True,
                            estimated_impact=f"${adjustment.get('amount', 0):.0f} budget adjustment",
                            time_horizon="immediate",
                            source_service="health_correlation",
                            created_at=datetime.now()
                        ))
            
            # Get stress-spending insights
            stress_insights = self._get_stress_spending_insights(user_id)
            insights.extend(stress_insights)
            
        except Exception as e:
            logger.error(f"Error getting health insights: {str(e)}")
        
        return insights
    
    def _get_emergency_fund_insights(self, user_id: int) -> List[Insight]:
        """Get emergency fund specific insights"""
        insights = []
        
        try:
            # This would typically get real user data
            # For now, create sample insights
            insights.append(Insight(
                id=f"emergency_fund_{user_id}",
                category=InsightCategory.EMERGENCY,
                title="Emergency Fund Recommendation",
                description="Your emergency fund should cover 6-12 months of expenses based on your job security risk level.",
                severity=InsightSeverity.MEDIUM,
                priority=8,
                recommendations=[
                    "Calculate your monthly expenses",
                    "Set up automatic savings transfers",
                    "Consider high-yield savings account",
                    "Review and adjust monthly contributions"
                ],
                actionable=True,
                estimated_impact="Provides 6-12 months of financial security",
                time_horizon="3-6 months",
                source_service="financial_planning",
                created_at=datetime.now()
            ))
            
        except Exception as e:
            logger.error(f"Error getting emergency fund insights: {str(e)}")
        
        return insights
    
    def _get_skills_insights(self, user_id: int) -> List[Insight]:
        """Get skills development insights"""
        insights = []
        
        try:
            insights.append(Insight(
                id=f"skills_development_{user_id}",
                category=InsightCategory.CAREER,
                title="Skills Development Opportunity",
                description="Industry trends show growing demand for your skills. Consider upskilling to increase career security.",
                severity=InsightSeverity.LOW,
                priority=5,
                recommendations=[
                    "Identify in-demand skills in your industry",
                    "Enroll in relevant courses or certifications",
                    "Join professional development programs",
                    "Network with industry professionals"
                ],
                actionable=True,
                estimated_impact="Potential 15-25% salary increase",
                time_horizon="6+ months",
                source_service="recommendations",
                created_at=datetime.now()
            ))
            
        except Exception as e:
            logger.error(f"Error getting skills insights: {str(e)}")
        
        return insights
    
    def _get_stress_spending_insights(self, user_id: int) -> List[Insight]:
        """Get stress-spending correlation insights"""
        insights = []
        
        try:
            insights.append(Insight(
                id=f"stress_spending_{user_id}",
                category=InsightCategory.HEALTH,
                title="Stress-Spending Pattern Detected",
                description="Your spending increases by 35% during high-stress periods. Consider stress management strategies.",
                severity=InsightSeverity.MEDIUM,
                priority=6,
                recommendations=[
                    "Practice stress-reduction techniques",
                    "Set spending limits during stress periods",
                    "Create alternative stress-relief activities",
                    "Monitor stress-spending triggers"
                ],
                actionable=True,
                estimated_impact="Potential $200-400/month savings",
                time_horizon="1-3 months",
                source_service="health_correlation",
                created_at=datetime.now()
            ))
            
        except Exception as e:
            logger.error(f"Error getting stress-spending insights: {str(e)}")
        
        return insights
    
    def _prioritize_insights(self, insights: List[Insight]) -> List[Insight]:
        """Prioritize insights based on category, severity, and other factors"""
        for insight in insights:
            # Calculate priority score
            base_priority = insight.priority
            category_weight = self.category_weights.get(insight.category, 1)
            severity_multiplier = self.severity_multipliers.get(insight.severity, 1)
            
            # Adjust priority based on factors
            insight.priority = int(base_priority * category_weight * severity_multiplier)
            
            # Cap priority at 10
            insight.priority = min(insight.priority, 10)
        
        # Sort by priority (highest first)
        insights.sort(key=lambda x: x.priority, reverse=True)
        return insights
    
    def _generate_insights_summary(self, insights: List[Insight]) -> Dict[str, Any]:
        """Generate summary statistics for insights"""
        if not insights:
            return {}
        
        return {
            "total_insights": len(insights),
            "high_priority_count": len([i for i in insights if i.priority >= 7]),
            "critical_insights": len([i for i in insights if i.severity == InsightSeverity.CRITICAL]),
            "actionable_insights": len([i for i in insights if i.actionable]),
            "average_priority": sum(i.priority for i in insights) / len(insights),
            "most_common_category": max(set(i.category.value for i in insights), 
                                      key=lambda x: sum(1 for i in insights if i.category.value == x))
        }
    
    def _get_category_breakdown(self, insights: List[Insight]) -> Dict[str, int]:
        """Get breakdown of insights by category"""
        breakdown = {}
        for insight in insights:
            category = insight.category.value
            breakdown[category] = breakdown.get(category, 0) + 1
        return breakdown
    
    def _get_severity_distribution(self, insights: List[Insight]) -> Dict[str, int]:
        """Get distribution of insights by severity"""
        distribution = {}
        for insight in insights:
            severity = insight.severity.value
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def _get_recommendations_for_insight(self, user_id: int, insight_id: str) -> List[Recommendation]:
        """Get recommendations for a specific insight"""
        recommendations = []
        
        try:
            # This would typically fetch recommendations from the database
            # For now, return sample recommendations
            recommendations.append(Recommendation(
                id=f"rec_{insight_id}_1",
                insight_id=insight_id,
                title="Implement Budget Tracking",
                description="Start tracking your expenses to identify spending patterns and opportunities for savings.",
                action_type="budget_tracking",
                estimated_savings=200.0,
                time_required="30 minutes/week",
                difficulty="easy",
                priority=8
            ))
            
        except Exception as e:
            logger.error(f"Error getting recommendations for insight: {str(e)}")
        
        return recommendations
    
    def _get_all_recommendations(self, user_id: int) -> List[Recommendation]:
        """Get all recommendations for a user"""
        recommendations = []
        
        try:
            # Get insights first
            insights = self.get_user_insights(user_id, limit=10)
            if "error" not in insights:
                for insight_data in insights["insights"]:
                    insight = Insight(**insight_data)
                    if insight.actionable:
                        # Generate recommendations for each actionable insight
                        insight_recs = self._get_recommendations_for_insight(user_id, insight.id)
                        recommendations.extend(insight_recs)
            
        except Exception as e:
            logger.error(f"Error getting all recommendations: {str(e)}")
        
        return recommendations
    
    def _calculate_dashboard_metrics(self, user_id: int, insights_data: Dict[str, Any], 
                                   recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Calculate dashboard metrics"""
        try:
            total_insights = insights_data.get("total_count", 0)
            completed_recommendations = len([r for r in recommendations if r.completed])
            total_recommendations = len(recommendations)
            
            return {
                "insights_count": total_insights,
                "recommendations_completed": completed_recommendations,
                "recommendations_total": total_recommendations,
                "completion_rate": (completed_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0,
                "high_priority_insights": insights_data.get("summary", {}).get("high_priority_count", 0),
                "actionable_insights": insights_data.get("summary", {}).get("actionable_insights", 0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating dashboard metrics: {str(e)}")
            return {}

    def get_job_security_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive job security insights with empowering language
        """
        try:
            # Get job security assessment
            job_security = self.recommendations.get_job_security_assessment(user_id)
            
            if "error" in job_security:
                return {"error": "Unable to assess job security"}
            
            risk_level = job_security.get("overall_risk", {}).get("risk_level", "low")
            risk_score = job_security.get("overall_risk", {}).get("risk_score", 0.3)
            
            # Convert risk score to security score (invert and scale)
            security_score = max(0, min(100, (1 - risk_score) * 100))
            
            # Generate empowering language based on score
            if security_score >= 80:
                message = "Excellent job security! Your position is well-protected."
                tone = "positive"
            elif security_score >= 60:
                message = "Good job security. You're in a stable position with room for growth."
                tone = "positive"
            elif security_score >= 40:
                message = "Moderate job security. Consider proactive measures to strengthen your position."
                tone = "neutral"
            else:
                message = "Job security needs attention. Focus on building your emergency fund and skills."
                tone = "constructive"
            
            # Get top awareness factors
            awareness_factors = self._get_job_security_awareness_factors(job_security)
            
            # Get career optimization strategies
            optimization_strategies = self._get_career_optimization_strategies(risk_level)
            
            return {
                "security_score": round(security_score, 1),
                "risk_level": risk_level,
                "message": message,
                "tone": tone,
                "awareness_factors": awareness_factors,
                "optimization_strategies": optimization_strategies,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting job security insights: {str(e)}")
            return {"error": f"Failed to get job security insights: {str(e)}"}

    def get_emergency_fund_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Get personalized emergency fund recommendations and cash flow insights
        """
        try:
            # Get current financial situation
            current_financials = self.financial_planning._get_current_financial_situation(user_id)
            
            # Get job security assessment for emergency fund adjustment
            job_security = self.recommendations.get_job_security_assessment(user_id)
            risk_level = job_security.get("overall_risk", {}).get("risk_level", "low") if "error" not in job_security else "low"
            
            # Calculate emergency fund recommendations
            emergency_fund_multipliers = {
                'low': 3, 'medium': 6, 'high': 9, 'very_high': 12
            }
            
            recommended_months = emergency_fund_multipliers.get(risk_level, 6)
            monthly_expenses = current_financials.get('monthly_expenses', 4000)
            current_savings = current_financials.get('current_savings', 0)
            
            recommended_amount = monthly_expenses * recommended_months
            current_months = current_savings / monthly_expenses if monthly_expenses > 0 else 0
            gap = max(0, recommended_amount - current_savings)
            
            # Calculate monthly savings needed
            monthly_savings_needed = gap / 12 if gap > 0 else 0
            
            # Generate immediate recommendations
            immediate_recommendations = self._get_immediate_financial_recommendations(
                current_financials, risk_level, gap
            )
            
            # Calculate progress percentage
            progress_percentage = min(100, (current_savings / recommended_amount) * 100) if recommended_amount > 0 else 0
            
            return {
                "current_savings": current_savings,
                "recommended_amount": recommended_amount,
                "current_months": round(current_months, 1),
                "recommended_months": recommended_months,
                "gap": gap,
                "monthly_savings_needed": monthly_savings_needed,
                "progress_percentage": round(progress_percentage, 1),
                "risk_level": risk_level,
                "immediate_recommendations": immediate_recommendations,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting emergency fund insights: {str(e)}")
            return {"error": f"Failed to get emergency fund insights: {str(e)}"}

    def get_health_relationship_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Get health and relationship awareness insights
        """
        try:
            # Get health correlation data
            health_data = self.health_correlation.get_user_health_summary(user_id, days=30)
            
            # Get relationship data from questionnaire responses
            relationship_data = self._get_relationship_data(user_id)
            
            # Generate health awareness insights
            health_insights = self._generate_health_awareness_insights(health_data)
            
            # Generate relationship awareness insights
            relationship_insights = self._generate_relationship_awareness_insights(relationship_data)
            
            # Generate social support recommendations
            social_support_recommendations = self._get_social_support_recommendations(relationship_data)
            
            return {
                "health_awareness": health_insights,
                "relationship_awareness": relationship_insights,
                "social_support_recommendations": social_support_recommendations,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health relationship insights: {str(e)}")
            return {"error": f"Failed to get health relationship insights: {str(e)}"}

    def _get_job_security_awareness_factors(self, job_security_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get top awareness factors for job security"""
        factors = []
        
        # Personal factors
        personal_risk = job_security_assessment.get("personal_risk", {})
        if personal_risk.get("risk_score", 0) > 0.5:
            factors.append({
                "factor": "Personal Performance",
                "description": "Focus on exceeding expectations and building key relationships",
                "priority": "high"
            })
        
        # Company factors
        company_risk = job_security_assessment.get("company_risk", {})
        if company_risk.get("risk_score", 0) > 0.6:
            factors.append({
                "factor": "Company Stability",
                "description": "Monitor company financial health and industry trends",
                "priority": "high"
            })
        
        # Industry factors
        industry_risk = job_security_assessment.get("industry_risk", {})
        if industry_risk.get("risk_score", 0) > 0.7:
            factors.append({
                "factor": "Industry Trends",
                "description": "Stay updated on industry changes and emerging technologies",
                "priority": "medium"
            })
        
        return factors[:3]  # Return top 3 factors

    def _get_career_optimization_strategies(self, risk_level: str) -> List[Dict[str, Any]]:
        """Get career optimization strategies based on risk level"""
        strategies = {
            'low': [
                {"strategy": "Skill Development", "description": "Continue building in-demand skills", "timeline": "ongoing"},
                {"strategy": "Networking", "description": "Maintain professional relationships", "timeline": "ongoing"}
            ],
            'medium': [
                {"strategy": "Emergency Fund", "description": "Build 6+ months of expenses", "timeline": "3-6 months"},
                {"strategy": "Skill Enhancement", "description": "Focus on transferable skills", "timeline": "3-6 months"},
                {"strategy": "Market Research", "description": "Monitor job market trends", "timeline": "ongoing"}
            ],
            'high': [
                {"strategy": "Emergency Fund", "description": "Build 9+ months of expenses", "timeline": "immediate"},
                {"strategy": "Skill Diversification", "description": "Learn adjacent skills", "timeline": "1-3 months"},
                {"strategy": "Job Search Preparation", "description": "Update resume and network", "timeline": "immediate"}
            ],
            'very_high': [
                {"strategy": "Emergency Fund", "description": "Build 12+ months of expenses", "timeline": "immediate"},
                {"strategy": "Active Job Search", "description": "Begin searching for new opportunities", "timeline": "immediate"},
                {"strategy": "Skill Pivot", "description": "Consider career transition", "timeline": "1-3 months"}
            ]
        }
        
        return strategies.get(risk_level, strategies['medium'])

    def _get_immediate_financial_recommendations(self, current_financials: Dict[str, Any], 
                                               risk_level: str, gap: float) -> Dict[str, Any]:
        """Get immediate spending and saving recommendations"""
        monthly_income = current_financials.get('monthly_income', 5000)
        monthly_expenses = current_financials.get('monthly_expenses', 4000)
        current_savings_rate = current_financials.get('monthly_savings_rate', 0.1)
        
        # Spending recommendations
        spending_recommendations = []
        if monthly_expenses > monthly_income * 0.8:
            spending_recommendations.append({
                "category": "Reduce Discretionary Spending",
                "description": "Cut non-essential expenses by 15-20%",
                "potential_savings": monthly_expenses * 0.15,
                "difficulty": "medium"
            })
        
        # Saving recommendations
        saving_recommendations = []
        target_savings_rate = 0.2 if risk_level in ['low', 'medium'] else 0.3
        if current_savings_rate < target_savings_rate:
            additional_savings_needed = (target_savings_rate - current_savings_rate) * monthly_income
            saving_recommendations.append({
                "category": "Increase Savings Rate",
                "description": f"Save an additional ${additional_savings_needed:.0f}/month",
                "target_rate": target_savings_rate,
                "difficulty": "medium"
            })
        
        return {
            "spending_recommendations": spending_recommendations,
            "saving_recommendations": saving_recommendations,
            "emergency_fund_priority": "high" if gap > monthly_expenses * 3 else "medium"
        }

    def _get_relationship_data(self, user_id: int) -> Dict[str, Any]:
        """Get relationship data from questionnaire responses"""
        # This would typically fetch from database
        # For now, return mock data
        return {
            "family_satisfaction": 7,
            "romantic_satisfaction": 8,
            "friendship_satisfaction": 6,
            "social_support": 7,
            "relationship_spending_impact": True,
            "social_spending_comfort": 6
        }

    def _generate_health_awareness_insights(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health awareness insights"""
        if not health_data or "error" in health_data:
            return {"message": "Complete health check-ins to see personalized insights"}
        
        insights = []
        avg_stress = health_data.get("averages", {}).get("stress_level", 5)
        avg_mood = health_data.get("averages", {}).get("mood_rating", 5)
        
        if avg_stress > 7:
            insights.append({
                "type": "stress_management",
                "title": "High Stress Levels",
                "description": "Your stress levels are elevated. Consider stress-reduction techniques.",
                "recommendation": "Try daily meditation or exercise to reduce stress"
            })
        
        if avg_mood < 6:
            insights.append({
                "type": "mood_improvement",
                "title": "Mood Optimization",
                "description": "Your mood could be improved with lifestyle changes.",
                "recommendation": "Focus on sleep, exercise, and social connections"
            })
        
        return {
            "insights": insights,
            "overall_health_score": health_data.get("wellness_score", 7.0),
            "trend": health_data.get("trend", "stable")
        }

    def _generate_relationship_awareness_insights(self, relationship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate relationship awareness insights"""
        insights = []
        
        family_satisfaction = relationship_data.get("family_satisfaction", 5)
        friendship_satisfaction = relationship_data.get("friendship_satisfaction", 5)
        social_support = relationship_data.get("social_support", 5)
        
        if family_satisfaction < 6:
            insights.append({
                "type": "family_relationships",
                "title": "Family Connection",
                "description": "Your family relationships could be strengthened.",
                "recommendation": "Schedule regular family time and open communication"
            })
        
        if friendship_satisfaction < 6:
            insights.append({
                "type": "friendships",
                "title": "Social Connections",
                "description": "Your social network could be expanded.",
                "recommendation": "Join clubs, attend events, or reconnect with old friends"
            })
        
        if social_support < 6:
            insights.append({
                "type": "social_support",
                "title": "Support Network",
                "description": "Your support network needs strengthening.",
                "recommendation": "Build deeper connections with trusted friends and family"
            })
        
        return {
            "insights": insights,
            "overall_relationship_score": (family_satisfaction + friendship_satisfaction + social_support) / 3
        }

    def _get_social_support_recommendations(self, relationship_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get social support recommendations"""
        recommendations = []
        
        social_support = relationship_data.get("social_support", 5)
        
        if social_support < 6:
            recommendations.extend([
                {
                    "type": "immediate",
                    "title": "Reach Out to Friends",
                    "description": "Contact 2-3 close friends this week",
                    "action": "Schedule coffee or phone calls"
                },
                {
                    "type": "long_term",
                    "title": "Join Social Groups",
                    "description": "Find groups aligned with your interests",
                    "action": "Look for local clubs or online communities"
                }
            ])
        
        return recommendations
