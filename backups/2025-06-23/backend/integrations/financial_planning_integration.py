"""
Financial Planning Integration with Job Security
Adjusts financial planning based on job security risk assessment
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from ..ml.job_security_predictor import JobSecurityPredictor
from ..services.cash_flow_analysis_service import CashFlowAnalysisService

logger = logging.getLogger(__name__)

class FinancialPlanningIntegration:
    """
    Integrates job security predictions with financial planning
    - Adjusts emergency fund recommendations
    - Modifies investment risk tolerance
    - Creates job loss scenario planning
    - Integrates with budgeting and savings
    """
    
    def __init__(self, job_security_predictor: JobSecurityPredictor = None):
        self.job_security_predictor = job_security_predictor or JobSecurityPredictor()
        self.cash_flow_service = CashFlowAnalysisService()
        
        # Emergency fund multipliers based on risk level
        self.emergency_fund_multipliers = {
            'low': 3,      # 3 months of expenses
            'medium': 6,   # 6 months of expenses
            'high': 9,     # 9 months of expenses
            'very_high': 12 # 12 months of expenses
        }
        
        # Investment risk adjustments
        self.risk_adjustments = {
            'low': 1.0,      # No change to risk tolerance
            'medium': 0.8,   # Reduce risk by 20%
            'high': 0.6,     # Reduce risk by 40%
            'very_high': 0.4 # Reduce risk by 60%
        }
    
    def get_job_security_adjusted_financial_plan(self, user_id: int, 
                                                user_data: Dict[str, Any],
                                                company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive financial plan adjusted for job security risk
        
        Args:
            user_id: User ID
            user_data: User financial and employment data
            company_data: Company information
            
        Returns:
            Adjusted financial plan with job security considerations
        """
        try:
            # Get job security assessment
            job_security_assessment = self._get_job_security_assessment(user_data, company_data)
            
            # Get current financial situation
            current_financials = self._get_current_financial_situation(user_id)
            
            # Calculate adjusted recommendations
            adjusted_plan = self._calculate_adjusted_plan(
                job_security_assessment, 
                current_financials, 
                user_data
            )
            
            # Generate scenario planning
            scenarios = self._generate_job_loss_scenarios(
                job_security_assessment, 
                current_financials, 
                user_data
            )
            
            # Create action plan
            action_plan = self._create_action_plan(adjusted_plan, scenarios)
            
            return {
                'job_security_assessment': job_security_assessment,
                'current_financials': current_financials,
                'adjusted_recommendations': adjusted_plan,
                'scenario_planning': scenarios,
                'action_plan': action_plan,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating financial plan: {e}")
            return {'error': f'Failed to generate financial plan: {str(e)}'}
    
    def _get_job_security_assessment(self, user_data: Dict[str, Any], 
                                   company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get job security assessment for the user"""
        try:
            # Get personal risk prediction
            personal_risk = self.job_security_predictor.personal_risk_predictor.predict(
                user_data, company_data
            )
            
            # Get company risk prediction
            company_risk = self.job_security_predictor.company_predictor.predict(company_data)
            
            # Get industry risk prediction
            industry_risk = self.job_security_predictor.industry_predictor.predict(
                company_data.get('industry', 'general')
            )
            
            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(personal_risk, company_risk, industry_risk)
            
            return {
                'personal_risk': personal_risk,
                'company_risk': company_risk,
                'industry_risk': industry_risk,
                'overall_risk': overall_risk,
                'risk_level': overall_risk['risk_level'],
                'layoff_probability_6m': overall_risk['risk_score']
            }
            
        except Exception as e:
            logger.error(f"Error getting job security assessment: {e}")
            return {
                'overall_risk': {'risk_level': 'medium', 'risk_score': 0.5},
                'layoff_probability_6m': 0.5
            }
    
    def _calculate_overall_risk(self, personal_risk: Dict[str, Any], 
                              company_risk: Dict[str, Any], 
                              industry_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk score from multiple assessments"""
        # Weight the different risk factors
        weights = {
            'personal': 0.4,
            'company': 0.4,
            'industry': 0.2
        }
        
        personal_score = personal_risk.get('risk_score', 0.5)
        company_score = company_risk.get('risk_score', 0.5)
        industry_score = industry_risk.get('risk_score', 0.5)
        
        overall_score = (
            personal_score * weights['personal'] +
            company_score * weights['company'] +
            industry_score * weights['industry']
        )
        
        # Determine risk level
        if overall_score < 0.3:
            risk_level = 'low'
        elif overall_score < 0.6:
            risk_level = 'medium'
        elif overall_score < 0.8:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        return {
            'risk_score': overall_score,
            'risk_level': risk_level,
            'confidence': min(
                personal_risk.get('confidence', 0.5),
                company_risk.get('confidence', 0.5),
                industry_risk.get('confidence', 0.5)
            )
        }
    
    def _get_current_financial_situation(self, user_id: int) -> Dict[str, Any]:
        """Get current financial situation for the user"""
        try:
            # Get cash flow analysis
            cash_flow = self.cash_flow_service.get_user_cash_flow(user_id)
            
            # Calculate current emergency fund
            monthly_expenses = cash_flow.get('monthly_expenses', 0)
            current_savings = cash_flow.get('current_savings', 0)
            
            emergency_fund_months = current_savings / monthly_expenses if monthly_expenses > 0 else 0
            
            return {
                'monthly_income': cash_flow.get('monthly_income', 0),
                'monthly_expenses': monthly_expenses,
                'current_savings': current_savings,
                'emergency_fund_months': emergency_fund_months,
                'monthly_savings_rate': cash_flow.get('monthly_savings_rate', 0),
                'debt_payments': cash_flow.get('monthly_debt_payments', 0),
                'investment_assets': cash_flow.get('investment_assets', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting financial situation: {e}")
            return {
                'monthly_income': 0,
                'monthly_expenses': 0,
                'current_savings': 0,
                'emergency_fund_months': 0,
                'monthly_savings_rate': 0,
                'debt_payments': 0,
                'investment_assets': 0
            }
    
    def _calculate_adjusted_plan(self, job_security_assessment: Dict[str, Any],
                               current_financials: Dict[str, Any],
                               user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjusted financial recommendations based on job security"""
        risk_level = job_security_assessment['overall_risk']['risk_level']
        
        # Emergency fund recommendations
        emergency_fund_multiplier = self.emergency_fund_multipliers[risk_level]
        recommended_emergency_fund = current_financials['monthly_expenses'] * emergency_fund_multiplier
        current_emergency_fund = current_financials['current_savings']
        emergency_fund_gap = max(0, recommended_emergency_fund - current_emergency_fund)
        
        # Investment risk adjustments
        risk_adjustment = self.risk_adjustments[risk_level]
        adjusted_investment_risk = user_data.get('investment_risk_tolerance', 0.5) * risk_adjustment
        
        # Savings rate recommendations
        base_savings_rate = 0.2  # 20% base recommendation
        risk_bonus = {
            'low': 0.05,
            'medium': 0.1,
            'high': 0.15,
            'very_high': 0.2
        }
        recommended_savings_rate = base_savings_rate + risk_bonus[risk_level]
        
        # Debt management recommendations
        debt_recommendations = self._get_debt_recommendations(
            current_financials, risk_level
        )
        
        # Insurance recommendations
        insurance_recommendations = self._get_insurance_recommendations(
            current_financials, risk_level, user_data
        )
        
        return {
            'emergency_fund': {
                'current_months': current_financials['emergency_fund_months'],
                'recommended_months': emergency_fund_multiplier,
                'current_amount': current_emergency_fund,
                'recommended_amount': recommended_emergency_fund,
                'gap': emergency_fund_gap,
                'monthly_savings_needed': emergency_fund_gap / 12 if emergency_fund_gap > 0 else 0
            },
            'investment_strategy': {
                'current_risk_tolerance': user_data.get('investment_risk_tolerance', 0.5),
                'adjusted_risk_tolerance': adjusted_investment_risk,
                'recommendation': self._get_investment_recommendation(adjusted_investment_risk)
            },
            'savings_rate': {
                'current_rate': current_financials['monthly_savings_rate'],
                'recommended_rate': recommended_savings_rate,
                'additional_savings_needed': (
                    (recommended_savings_rate - current_financials['monthly_savings_rate']) * 
                    current_financials['monthly_income']
                )
            },
            'debt_management': debt_recommendations,
            'insurance': insurance_recommendations
        }
    
    def _get_debt_recommendations(self, current_financials: Dict[str, Any], 
                                risk_level: str) -> Dict[str, Any]:
        """Get debt management recommendations based on risk level"""
        debt_to_income = (
            current_financials['debt_payments'] / current_financials['monthly_income']
            if current_financials['monthly_income'] > 0 else 0
        )
        
        recommendations = []
        priority = 'normal'
        
        if risk_level in ['high', 'very_high']:
            if debt_to_income > 0.3:
                recommendations.append("Prioritize debt reduction - high debt load with job security concerns")
                priority = 'high'
            elif debt_to_income > 0.2:
                recommendations.append("Consider accelerating debt payments")
                priority = 'medium'
        
        if risk_level == 'very_high':
            recommendations.append("Avoid taking on new debt")
            recommendations.append("Consider debt consolidation to reduce monthly payments")
        
        return {
            'debt_to_income_ratio': debt_to_income,
            'recommendations': recommendations,
            'priority': priority
        }
    
    def _get_insurance_recommendations(self, current_financials: Dict[str, Any],
                                     risk_level: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get insurance recommendations based on risk level"""
        recommendations = []
        
        # Disability insurance
        if not user_data.get('disability_insurance'):
            if risk_level in ['high', 'very_high']:
                recommendations.append({
                    'type': 'disability_insurance',
                    'priority': 'high',
                    'reason': 'Protect income during job transition period'
                })
        
        # Life insurance
        if not user_data.get('life_insurance'):
            if current_financials['monthly_expenses'] > 0:
                recommendations.append({
                    'type': 'life_insurance',
                    'priority': 'medium',
                    'reason': 'Protect family from financial hardship'
                })
        
        # Unemployment insurance (if available)
        if risk_level in ['high', 'very_high']:
            recommendations.append({
                'type': 'unemployment_insurance',
                'priority': 'high',
                'reason': 'Bridge income gap during job search'
            })
        
        return {
            'recommendations': recommendations,
            'total_monthly_cost': len(recommendations) * 100  # Rough estimate
        }
    
    def _get_investment_recommendation(self, adjusted_risk_tolerance: float) -> str:
        """Get investment strategy recommendation"""
        if adjusted_risk_tolerance < 0.3:
            return "Conservative portfolio: 70% bonds, 30% stocks"
        elif adjusted_risk_tolerance < 0.5:
            return "Moderate portfolio: 50% bonds, 50% stocks"
        elif adjusted_risk_tolerance < 0.7:
            return "Balanced portfolio: 30% bonds, 70% stocks"
        else:
            return "Growth portfolio: 20% bonds, 80% stocks"
    
    def _generate_job_loss_scenarios(self, job_security_assessment: Dict[str, Any],
                                   current_financials: Dict[str, Any],
                                   user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate job loss scenario planning"""
        layoff_probability = job_security_assessment['layoff_probability_6m']
        monthly_expenses = current_financials['monthly_expenses']
        current_savings = current_financials['current_savings']
        
        scenarios = {}
        
        # Scenario 1: Immediate layoff
        immediate_layoff = {
            'duration': 'Immediate',
            'severance_pay': user_data.get('severance_pay', 0),
            'unemployment_benefits': monthly_expenses * 0.6,  # 60% of expenses
            'savings_depletion_months': (
                (current_savings + user_data.get('severance_pay', 0)) / 
                (monthly_expenses * 0.4)  # 40% gap after unemployment
            ) if monthly_expenses > 0 else 0,
            'actions_needed': [
                "File for unemployment immediately",
                "Reduce non-essential expenses",
                "Contact creditors about payment plans",
                "Update resume and start job search"
            ]
        }
        scenarios['immediate_layoff'] = immediate_layoff
        
        # Scenario 2: 3-month notice
        three_month_notice = {
            'duration': '3 months notice',
            'preparation_time': '3 months',
            'additional_savings_possible': current_financials['monthly_savings_rate'] * 3,
            'actions_needed': [
                "Maximize savings during notice period",
                "Network and update professional profile",
                "Research job market and opportunities",
                "Consider additional training or certifications"
            ]
        }
        scenarios['three_month_notice'] = three_month_notice
        
        # Scenario 3: Gradual transition
        gradual_transition = {
            'duration': '6-12 months',
            'probability': layoff_probability,
            'preparation_strategy': [
                "Build emergency fund to 12 months of expenses",
                "Develop side income or freelance opportunities",
                "Network and build professional relationships",
                "Update skills and certifications"
            ]
        }
        scenarios['gradual_transition'] = gradual_transition
        
        return scenarios
    
    def _create_action_plan(self, adjusted_plan: Dict[str, Any], 
                          scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Create prioritized action plan"""
        actions = []
        
        # Emergency fund actions
        emergency_fund = adjusted_plan['emergency_fund']
        if emergency_fund['gap'] > 0:
            actions.append({
                'priority': 'high',
                'category': 'emergency_fund',
                'action': f"Save ${emergency_fund['monthly_savings_needed']:.0f}/month to reach emergency fund goal",
                'timeline': '3-6 months',
                'impact': 'high'
            })
        
        # Debt management actions
        debt_mgmt = adjusted_plan['debt_management']
        if debt_mgmt['priority'] == 'high':
            actions.append({
                'priority': 'high',
                'category': 'debt_reduction',
                'action': 'Prioritize debt reduction to improve financial flexibility',
                'timeline': 'immediate',
                'impact': 'high'
            })
        
        # Insurance actions
        insurance = adjusted_plan['insurance']
        for rec in insurance['recommendations']:
            if rec['priority'] == 'high':
                actions.append({
                    'priority': 'high',
                    'category': 'insurance',
                    'action': f"Obtain {rec['type'].replace('_', ' ').title()}",
                    'timeline': '1 month',
                    'impact': 'high'
                })
        
        # Investment adjustments
        if adjusted_plan['investment_strategy']['current_risk_tolerance'] != adjusted_plan['investment_strategy']['adjusted_risk_tolerance']:
            actions.append({
                'priority': 'medium',
                'category': 'investment',
                'action': 'Adjust investment portfolio to reduce risk',
                'timeline': '1-2 months',
                'impact': 'medium'
            })
        
        # Sort by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return {
            'actions': actions,
            'next_30_days': [a for a in actions if a['timeline'] in ['immediate', '1 month']],
            'next_90_days': [a for a in actions if a['timeline'] in ['immediate', '1 month', '3-6 months']],
            'long_term': [a for a in actions if a['timeline'] not in ['immediate', '1 month', '3-6 months']]
        }
    
    def update_user_financial_preferences(self, user_id: int, 
                                        job_security_data: Dict[str, Any]) -> bool:
        """Update user's financial preferences based on job security assessment"""
        try:
            # This would update the user's financial preferences in the database
            # For now, return success
            logger.info(f"Updated financial preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating financial preferences: {e}")
            return False
    
    def get_financial_health_score(self, user_id: int) -> Dict[str, Any]:
        """Calculate financial health score considering job security"""
        try:
            # Get current financials
            current_financials = self._get_current_financial_situation(user_id)
            
            # Calculate base financial health score
            emergency_fund_score = min(100, (current_financials['emergency_fund_months'] / 6) * 100)
            savings_rate_score = min(100, (current_financials['monthly_savings_rate'] / 0.2) * 100)
            debt_score = max(0, 100 - (current_financials['debt_payments'] / current_financials['monthly_income']) * 100)
            
            base_score = (emergency_fund_score + savings_rate_score + debt_score) / 3
            
            # Adjust for job security (would need job security data)
            # For now, return base score
            return {
                'overall_score': base_score,
                'emergency_fund_score': emergency_fund_score,
                'savings_rate_score': savings_rate_score,
                'debt_score': debt_score,
                'job_security_adjustment': 0,
                'recommendations': self._get_health_score_recommendations(base_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating financial health score: {e}")
            return {'error': f'Failed to calculate health score: {str(e)}'}
    
    def _get_health_score_recommendations(self, score: float) -> List[str]:
        """Get recommendations based on financial health score"""
        if score >= 80:
            return ["Excellent financial health! Maintain current practices."]
        elif score >= 60:
            return ["Good financial health. Consider increasing emergency fund."]
        elif score >= 40:
            return ["Moderate financial health. Focus on building emergency fund and reducing debt."]
        else:
            return [
                "Financial health needs attention. Prioritize emergency fund and debt reduction.",
                "Consider consulting with a financial advisor."
            ] 