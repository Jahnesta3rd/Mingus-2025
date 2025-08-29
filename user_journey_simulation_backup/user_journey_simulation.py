#!/usr/bin/env python3
"""
MINGUS Application - Complete User Journey Simulation
====================================================

This script simulates a complete user journey through the MINGUS application,
testing all major user flows and functionality from discovery to monthly reporting.

User Journey Steps:
1. User discovers Mingus app
2. Signs up for Budget tier ($10)
3. Completes profile setup with income/expenses
4. Performs first weekly check-in
5. Reviews financial forecast
6. Upgrades to Mid-tier ($20)
7. Uses career recommendations
8. Receives and reviews monthly report

Author: MINGUS Development Team
Date: January 2025
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_journey_simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MingusUserJourneySimulator:
    """Simulates complete user journey through MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_data = {}
        self.test_results = {}
        
        # Test data for simulation
        self.test_user = {
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "555-123-4567"
        }
        
        self.profile_data = {
            "monthly_income": 75000,
            "income_frequency": "monthly",
            "primary_income_source": "full-time-employment",
            "employment_status": "employed",
            "industry": "technology",
            "job_title": "Software Engineer",
            "current_savings": 15000,
            "current_debt": 5000,
            "credit_score_range": "good",
            "age_range": "25-34",
            "location_state": "GA",
            "location_city": "Atlanta",
            "household_size": "2",
            "dependents": "0"
        }
        
        self.expenses_data = {
            "housing": 2000,
            "transportation": 500,
            "food": 600,
            "utilities": 300,
            "healthcare": 400,
            "entertainment": 300,
            "shopping": 200,
            "debt_payments": 300,
            "savings": 1000,
            "other": 200
        }
        
        self.health_checkin_data = {
            "physical_activity_minutes": 45,
            "physical_activity_level": "moderate",
            "relationships_rating": 8,
            "relationships_notes": "Good relationships with family and friends",
            "mindfulness_minutes": 15,
            "mindfulness_type": "meditation",
            "stress_level": 6,
            "energy_level": 7,
            "mood_rating": 8
        }

    def log_step(self, step: str, status: str, details: str = ""):
        """Log a test step with status and details"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] {step}: {status}")
        if details:
            logger.info(f"  Details: {details}")
        
        self.test_results[step] = {
            "status": status,
            "timestamp": timestamp,
            "details": details
        }

    def test_health_check(self) -> bool:
        """Test application health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_step("Health Check", "PASS", "Application is healthy")
                return True
            else:
                self.log_step("Health Check", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_step("Health Check", "FAIL", f"Connection error: {str(e)}")
            return False

    def step_1_discover_app(self) -> bool:
        """Step 1: User discovers Mingus app"""
        logger.info("\n" + "="*60)
        logger.info("STEP 1: USER DISCOVERS MINGUS APP")
        logger.info("="*60)
        
        try:
            # Test landing page
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_step("Landing Page Access", "PASS", "Landing page accessible")
            else:
                self.log_step("Landing Page Access", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test assessment landing page
            response = self.session.get(f"{self.base_url}/assessments")
            if response.status_code == 200:
                self.log_step("Assessment Landing", "PASS", "Assessment page accessible")
            else:
                self.log_step("Assessment Landing", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test available assessments
            response = self.session.get(f"{self.base_url}/api/assessments/available")
            if response.status_code == 200:
                assessments = response.json()
                self.log_step("Available Assessments", "PASS", f"Found {len(assessments.get('assessments', []))} assessments")
            else:
                self.log_step("Available Assessments", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("App Discovery", "PASS", "User successfully discovered the app")
            return True
            
        except Exception as e:
            self.log_step("App Discovery", "FAIL", f"Error: {str(e)}")
            return False

    def step_2_signup_budget_tier(self) -> bool:
        """Step 2: Signs up for Budget tier ($10)"""
        logger.info("\n" + "="*60)
        logger.info("STEP 2: SIGN UP FOR BUDGET TIER ($10)")
        logger.info("="*60)
        
        try:
            # Test signup endpoint
            signup_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"],
                "first_name": self.test_user["first_name"],
                "last_name": self.test_user["last_name"],
                "phone": self.test_user["phone"],
                "tier": "budget"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/signup", json=signup_data)
            if response.status_code in [200, 201]:
                user_data = response.json()
                self.user_data = user_data
                self.log_step("User Signup", "PASS", f"User created with ID: {user_data.get('user_id', 'N/A')}")
            else:
                self.log_step("User Signup", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test subscription creation for Budget tier
            subscription_data = {
                "tier": "budget",
                "billing_cycle": "monthly",
                "amount": 1000  # $10.00 in cents
            }
            
            response = self.session.post(f"{self.base_url}/api/subscriptions/create", json=subscription_data)
            if response.status_code in [200, 201]:
                sub_data = response.json()
                self.log_step("Budget Tier Subscription", "PASS", f"Subscription created: {sub_data.get('subscription_id', 'N/A')}")
            else:
                self.log_step("Budget Tier Subscription", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test tier access verification
            response = self.session.get(f"{self.base_url}/api/subscriptions/tier-access")
            if response.status_code == 200:
                tier_data = response.json()
                if tier_data.get('current_tier') == 'budget':
                    self.log_step("Tier Access Verification", "PASS", "Budget tier access confirmed")
                else:
                    self.log_step("Tier Access Verification", "FAIL", f"Expected budget tier, got: {tier_data.get('current_tier')}")
                    return False
            else:
                self.log_step("Tier Access Verification", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Budget Tier Signup", "PASS", "Successfully signed up for Budget tier")
            return True
            
        except Exception as e:
            self.log_step("Budget Tier Signup", "FAIL", f"Error: {str(e)}")
            return False

    def step_3_profile_setup(self) -> bool:
        """Step 3: Completes profile setup with income/expenses"""
        logger.info("\n" + "="*60)
        logger.info("STEP 3: COMPLETE PROFILE SETUP WITH INCOME/EXPENSES")
        logger.info("="*60)
        
        try:
            # Test profile creation
            response = self.session.post(f"{self.base_url}/api/onboarding/profile", json=self.profile_data)
            if response.status_code in [200, 201]:
                profile_result = response.json()
                self.log_step("Profile Creation", "PASS", f"Profile created: {profile_result.get('profile_id', 'N/A')}")
            else:
                self.log_step("Profile Creation", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test expenses setup
            response = self.session.post(f"{self.base_url}/api/onboarding/expenses", json=self.expenses_data)
            if response.status_code in [200, 201]:
                expenses_result = response.json()
                self.log_step("Expenses Setup", "PASS", f"Expenses saved: {expenses_result.get('expenses_id', 'N/A')}")
            else:
                self.log_step("Expenses Setup", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test financial questionnaire
            questionnaire_data = {
                "risk_tolerance": 7,
                "financial_knowledge": 6,
                "primary_goal": "save_money",
                "goal_amount": 50000,
                "goal_timeline_months": 24
            }
            
            response = self.session.post(f"{self.base_url}/api/onboarding/financial-questionnaire", json=questionnaire_data)
            if response.status_code in [200, 201]:
                questionnaire_result = response.json()
                self.log_step("Financial Questionnaire", "PASS", f"Questionnaire completed: {questionnaire_result.get('questionnaire_id', 'N/A')}")
            else:
                self.log_step("Financial Questionnaire", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test onboarding completion
            response = self.session.post(f"{self.base_url}/api/onboarding/complete")
            if response.status_code in [200, 201]:
                completion_result = response.json()
                self.log_step("Onboarding Completion", "PASS", f"Onboarding completed: {completion_result.get('completion_id', 'N/A')}")
            else:
                self.log_step("Onboarding Completion", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test profile retrieval
            response = self.session.get(f"{self.base_url}/api/user/profile")
            if response.status_code == 200:
                profile = response.json()
                if profile.get('monthly_income') == self.profile_data['monthly_income']:
                    self.log_step("Profile Retrieval", "PASS", "Profile data correctly saved and retrieved")
                else:
                    self.log_step("Profile Retrieval", "FAIL", "Profile data mismatch")
                    return False
            else:
                self.log_step("Profile Retrieval", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Profile Setup", "PASS", "Successfully completed profile setup with income/expenses")
            return True
            
        except Exception as e:
            self.log_step("Profile Setup", "FAIL", f"Error: {str(e)}")
            return False

    def step_4_weekly_checkin(self) -> bool:
        """Step 4: Performs first weekly check-in"""
        logger.info("\n" + "="*60)
        logger.info("STEP 4: PERFORM FIRST WEEKLY CHECK-IN")
        logger.info("="*60)
        
        try:
            # Test health check-in form access
            response = self.session.get(f"{self.base_url}/api/health/checkin")
            if response.status_code == 200:
                self.log_step("Health Check-in Form", "PASS", "Health check-in form accessible")
            else:
                self.log_step("Health Check-in Form", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test health check-in submission
            response = self.session.post(f"{self.base_url}/api/health/checkin", json=self.health_checkin_data)
            if response.status_code in [200, 201]:
                checkin_result = response.json()
                self.log_step("Health Check-in Submission", "PASS", f"Check-in submitted: {checkin_result.get('checkin_id', 'N/A')}")
            else:
                self.log_step("Health Check-in Submission", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test check-in history
            response = self.session.get(f"{self.base_url}/api/health/checkin/history")
            if response.status_code == 200:
                history = response.json()
                if len(history.get('checkins', [])) > 0:
                    self.log_step("Check-in History", "PASS", f"Found {len(history['checkins'])} check-ins in history")
                else:
                    self.log_step("Check-in History", "FAIL", "No check-ins found in history")
                    return False
            else:
                self.log_step("Check-in History", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test health status
            response = self.session.get(f"{self.base_url}/api/health/status")
            if response.status_code == 200:
                status = response.json()
                if status.get('weekly_checkin_complete'):
                    self.log_step("Health Status", "PASS", "Weekly check-in marked as complete")
                else:
                    self.log_step("Health Status", "FAIL", "Weekly check-in not marked as complete")
                    return False
            else:
                self.log_step("Health Status", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test health statistics
            response = self.session.get(f"{self.base_url}/api/health/stats")
            if response.status_code == 200:
                stats = response.json()
                self.log_step("Health Statistics", "PASS", f"Health stats generated: {stats.get('total_checkins', 0)} total check-ins")
            else:
                self.log_step("Health Statistics", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Weekly Check-in", "PASS", "Successfully completed first weekly check-in")
            return True
            
        except Exception as e:
            self.log_step("Weekly Check-in", "FAIL", f"Error: {str(e)}")
            return False

    def step_5_financial_forecast(self) -> bool:
        """Step 5: Reviews financial forecast"""
        logger.info("\n" + "="*60)
        logger.info("STEP 5: REVIEW FINANCIAL FORECAST")
        logger.info("="*60)
        
        try:
            # Test cash flow forecast generation
            forecast_data = {
                "user_id": self.user_data.get('user_id'),
                "initial_balance": 15000,
                "start_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.session.post(f"{self.base_url}/forecast", json=forecast_data)
            if response.status_code == 200:
                forecast_result = response.json()
                self.log_step("Cash Flow Forecast", "PASS", f"Forecast generated: {len(forecast_result.get('data', {}).get('daily_forecasts', []))} days")
            else:
                self.log_step("Cash Flow Forecast", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test financial analysis
            response = self.session.get(f"{self.base_url}/api/financial/analysis")
            if response.status_code == 200:
                analysis = response.json()
                self.log_step("Financial Analysis", "PASS", "Financial analysis generated")
            else:
                self.log_step("Financial Analysis", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test spending patterns
            response = self.session.get(f"{self.base_url}/api/financial/spending-patterns")
            if response.status_code == 200:
                patterns = response.json()
                self.log_step("Spending Patterns", "PASS", "Spending patterns analyzed")
            else:
                self.log_step("Spending Patterns", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test budget variance
            response = self.session.get(f"{self.base_url}/api/financial/budget-variance")
            if response.status_code == 200:
                variance = response.json()
                self.log_step("Budget Variance", "PASS", "Budget variance calculated")
            else:
                self.log_step("Budget Variance", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test financial insights (Budget tier limited)
            response = self.session.get(f"{self.base_url}/api/financial/insights")
            if response.status_code == 200:
                insights = response.json()
                self.log_step("Financial Insights", "PASS", f"Generated {len(insights.get('insights', []))} insights")
            else:
                self.log_step("Financial Insights", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Financial Forecast Review", "PASS", "Successfully reviewed financial forecast and analysis")
            return True
            
        except Exception as e:
            self.log_step("Financial Forecast Review", "FAIL", f"Error: {str(e)}")
            return False

    def step_6_upgrade_mid_tier(self) -> bool:
        """Step 6: Upgrades to Mid-tier ($20)"""
        logger.info("\n" + "="*60)
        logger.info("STEP 6: UPGRADE TO MID-TIER ($20)")
        logger.info("="*60)
        
        try:
            # Test upgrade options
            response = self.session.get(f"{self.base_url}/api/subscriptions/upgrade-options")
            if response.status_code == 200:
                options = response.json()
                mid_tier_option = next((opt for opt in options.get('options', []) if opt.get('tier') == 'mid_tier'), None)
                if mid_tier_option:
                    self.log_step("Upgrade Options", "PASS", f"Mid-tier option available: ${mid_tier_option.get('price_monthly', 0)/100}/month")
                else:
                    self.log_step("Upgrade Options", "FAIL", "Mid-tier option not found")
                    return False
            else:
                self.log_step("Upgrade Options", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test subscription upgrade
            upgrade_data = {
                "new_tier": "mid_tier",
                "billing_cycle": "monthly"
            }
            
            response = self.session.post(f"{self.base_url}/api/subscriptions/upgrade", json=upgrade_data)
            if response.status_code in [200, 201]:
                upgrade_result = response.json()
                self.log_step("Subscription Upgrade", "PASS", f"Upgraded to mid-tier: {upgrade_result.get('subscription_id', 'N/A')}")
            else:
                self.log_step("Subscription Upgrade", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test new tier access verification
            response = self.session.get(f"{self.base_url}/api/subscriptions/tier-access")
            if response.status_code == 200:
                tier_data = response.json()
                if tier_data.get('current_tier') == 'mid_tier':
                    self.log_step("Mid-Tier Access Verification", "PASS", "Mid-tier access confirmed")
                else:
                    self.log_step("Mid-Tier Access Verification", "FAIL", f"Expected mid_tier, got: {tier_data.get('current_tier')}")
                    return False
            else:
                self.log_step("Mid-Tier Access Verification", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test enhanced features access
            response = self.session.get(f"{self.base_url}/api/features/available")
            if response.status_code == 200:
                features = response.json()
                if 'career_risk_management' in features.get('available_features', []):
                    self.log_step("Enhanced Features Access", "PASS", "Career risk management feature now available")
                else:
                    self.log_step("Enhanced Features Access", "FAIL", "Career risk management feature not available")
                    return False
            else:
                self.log_step("Enhanced Features Access", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Mid-Tier Upgrade", "PASS", "Successfully upgraded to Mid-tier")
            return True
            
        except Exception as e:
            self.log_step("Mid-Tier Upgrade", "FAIL", f"Error: {str(e)}")
            return False

    def step_7_career_recommendations(self) -> bool:
        """Step 7: Uses career recommendations"""
        logger.info("\n" + "="*60)
        logger.info("STEP 7: USE CAREER RECOMMENDATIONS")
        logger.info("="*60)
        
        try:
            # Test job recommendations
            job_data = {
                "current_salary": 75000,
                "target_locations": ["Atlanta", "Houston", "Dallas"],
                "resume_text": "Experienced software engineer with 5 years in Python development..."
            }
            
            response = self.session.post(f"{self.base_url}/api/career/job-recommendations", json=job_data)
            if response.status_code == 200:
                job_result = response.json()
                recommendations = job_result.get('recommendations', [])
                self.log_step("Job Recommendations", "PASS", f"Generated {len(recommendations)} job recommendations")
            else:
                self.log_step("Job Recommendations", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test salary analysis
            response = self.session.get(f"{self.base_url}/api/career/salary-analysis")
            if response.status_code == 200:
                salary_analysis = response.json()
                self.log_step("Salary Analysis", "PASS", "Salary analysis generated")
            else:
                self.log_step("Salary Analysis", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test career advancement strategy
            strategy_data = {
                "risk_preference": "balanced",
                "timeline_months": 12
            }
            
            response = self.session.post(f"{self.base_url}/api/career/advancement-strategy", json=strategy_data)
            if response.status_code == 200:
                strategy_result = response.json()
                self.log_step("Career Strategy", "PASS", "Career advancement strategy generated")
            else:
                self.log_step("Career Strategy", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test skill gap analysis
            response = self.session.get(f"{self.base_url}/api/career/skill-gaps")
            if response.status_code == 200:
                skill_gaps = response.json()
                self.log_step("Skill Gap Analysis", "PASS", "Skill gap analysis completed")
            else:
                self.log_step("Skill Gap Analysis", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test career risk management (Mid-tier feature)
            response = self.session.get(f"{self.base_url}/api/career/risk-management")
            if response.status_code == 200:
                risk_management = response.json()
                self.log_step("Career Risk Management", "PASS", "Career risk management analysis available")
            else:
                self.log_step("Career Risk Management", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Career Recommendations", "PASS", "Successfully used career recommendations")
            return True
            
        except Exception as e:
            self.log_step("Career Recommendations", "FAIL", f"Error: {str(e)}")
            return False

    def step_8_monthly_report(self) -> bool:
        """Step 8: Receives and reviews monthly report"""
        logger.info("\n" + "="*60)
        logger.info("STEP 8: RECEIVE AND REVIEW MONTHLY REPORT")
        logger.info("="*60)
        
        try:
            # Test monthly report generation
            report_data = {
                "report_type": "monthly",
                "include_insights": True,
                "include_recommendations": True
            }
            
            response = self.session.post(f"{self.base_url}/api/reports/generate", json=report_data)
            if response.status_code in [200, 201]:
                report_result = response.json()
                self.log_step("Monthly Report Generation", "PASS", f"Report generated: {report_result.get('report_id', 'N/A')}")
            else:
                self.log_step("Monthly Report Generation", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
            
            # Test report retrieval
            report_id = report_result.get('report_id')
            response = self.session.get(f"{self.base_url}/api/reports/{report_id}")
            if response.status_code == 200:
                report = response.json()
                self.log_step("Report Retrieval", "PASS", f"Report retrieved: {report.get('report_name', 'N/A')}")
            else:
                self.log_step("Report Retrieval", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test report analytics
            response = self.session.get(f"{self.base_url}/api/reports/{report_id}/analytics")
            if response.status_code == 200:
                analytics = response.json()
                self.log_step("Report Analytics", "PASS", "Report analytics generated")
            else:
                self.log_step("Report Analytics", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test report insights
            response = self.session.get(f"{self.base_url}/api/reports/{report_id}/insights")
            if response.status_code == 200:
                insights = response.json()
                self.log_step("Report Insights", "PASS", f"Generated {len(insights.get('insights', []))} insights")
            else:
                self.log_step("Report Insights", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test report recommendations
            response = self.session.get(f"{self.base_url}/api/reports/{report_id}/recommendations")
            if response.status_code == 200:
                recommendations = response.json()
                self.log_step("Report Recommendations", "PASS", f"Generated {len(recommendations.get('recommendations', []))} recommendations")
            else:
                self.log_step("Report Recommendations", "FAIL", f"Status code: {response.status_code}")
                return False
            
            # Test report download
            response = self.session.get(f"{self.base_url}/api/reports/{report_id}/download")
            if response.status_code == 200:
                self.log_step("Report Download", "PASS", "Report download successful")
            else:
                self.log_step("Report Download", "FAIL", f"Status code: {response.status_code}")
                return False
            
            self.log_step("Monthly Report Review", "PASS", "Successfully received and reviewed monthly report")
            return True
            
        except Exception as e:
            self.log_step("Monthly Report Review", "FAIL", f"Error: {str(e)}")
            return False

    def run_complete_journey(self) -> Dict[str, Any]:
        """Run the complete user journey simulation"""
        logger.info("Starting MINGUS User Journey Simulation")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Test User: {self.test_user['email']}")
        
        # Test health check first
        if not self.test_health_check():
            return {"status": "FAILED", "reason": "Application health check failed"}
        
        # Run all steps
        steps = [
            ("Step 1: App Discovery", self.step_1_discover_app),
            ("Step 2: Budget Tier Signup", self.step_2_signup_budget_tier),
            ("Step 3: Profile Setup", self.step_3_profile_setup),
            ("Step 4: Weekly Check-in", self.step_4_weekly_checkin),
            ("Step 5: Financial Forecast", self.step_5_financial_forecast),
            ("Step 6: Mid-Tier Upgrade", self.step_6_upgrade_mid_tier),
            ("Step 7: Career Recommendations", self.step_7_career_recommendations),
            ("Step 8: Monthly Report", self.step_8_monthly_report)
        ]
        
        results = {}
        all_passed = True
        
        for step_name, step_func in steps:
            try:
                success = step_func()
                results[step_name] = "PASS" if success else "FAIL"
                if not success:
                    all_passed = False
            except Exception as e:
                logger.error(f"Error in {step_name}: {str(e)}")
                results[step_name] = "ERROR"
                all_passed = False
        
        # Generate summary
        summary = {
            "status": "PASS" if all_passed else "FAIL",
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "test_user": self.test_user["email"],
            "results": results,
            "detailed_results": self.test_results
        }
        
        # Log summary
        logger.info("\n" + "="*60)
        logger.info("SIMULATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Overall Status: {summary['status']}")
        logger.info(f"Test User: {summary['test_user']}")
        logger.info("\nStep Results:")
        for step, result in results.items():
            logger.info(f"  {step}: {result}")
        
        return summary

def main():
    """Main function to run the simulation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MINGUS User Journey Simulation")
    parser.add_argument("--url", default="http://localhost:5001", help="Base URL of the MINGUS application")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Run simulation
    simulator = MingusUserJourneySimulator(args.url)
    results = simulator.run_complete_journey()
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to: {args.output}")
    
    # Exit with appropriate code
    exit_code = 0 if results["status"] == "PASS" else 1
    exit(exit_code)

if __name__ == "__main__":
    main()
