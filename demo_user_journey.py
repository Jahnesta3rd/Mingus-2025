#!/usr/bin/env python3
"""
MINGUS User Journey Demo
========================

This script provides a demonstration of the complete user journey simulation
with mock responses, useful for presentations and when the actual application
isn't running.

Usage:
    python demo_user_journey.py
"""

import json
import time
from datetime import datetime
from typing import Dict, Any

class MockMingusUserJourneyDemo:
    """Demo version of the user journey simulation with mock responses"""
    
    def __init__(self):
        self.user_data = {}
        self.test_results = {}
        
        # Mock test data
        self.test_user = {
            "email": f"demo_user_{int(time.time())}@example.com",
            "password": "DemoPassword123!",
            "first_name": "Demo",
            "last_name": "User",
            "phone": "555-123-4567"
        }

    def log_step(self, step: str, status: str, details: str = ""):
        """Log a demo step with status and details"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {step}: {status}")
        if details:
            print(f"  Details: {details}")
        
        self.test_results[step] = {
            "status": status,
            "timestamp": timestamp,
            "details": details
        }

    def simulate_api_call(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Simulate an API call with mock responses"""
        print(f"  📡 {method} {endpoint}")
        if data:
            print(f"  📤 Request Data: {json.dumps(data, indent=2)}")
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Return mock responses based on endpoint
        mock_responses = {
            "/health": {"status": "healthy", "timestamp": datetime.now().isoformat()},
            "/": {"page": "landing", "title": "MINGUS - AI-Powered Financial Assessment"},
            "/assessments": {"page": "assessments", "title": "Financial Assessments"},
            "/api/assessments/available": {
                "assessments": [
                    {"id": "1", "title": "Financial Health Assessment", "duration": "10 min"},
                    {"id": "2", "title": "Career Risk Assessment", "duration": "15 min"},
                    {"id": "3", "title": "Investment Readiness Assessment", "duration": "12 min"}
                ]
            },
            "/api/auth/signup": {
                "user_id": "demo_user_123",
                "email": self.test_user["email"],
                "status": "created",
                "subscription_tier": "budget"
            },
            "/api/subscriptions/create": {
                "subscription_id": "sub_demo_123",
                "tier": "budget",
                "amount": 1000,
                "status": "active"
            },
            "/api/subscriptions/tier-access": {
                "current_tier": "budget",
                "features": ["basic_analytics", "goal_setting", "email_support"],
                "limits": {"analytics_reports_per_month": 5}
            },
            "/api/onboarding/profile": {
                "profile_id": "profile_demo_123",
                "status": "created",
                "completion_percentage": 25
            },
            "/api/onboarding/expenses": {
                "expenses_id": "expenses_demo_123",
                "status": "saved",
                "completion_percentage": 50
            },
            "/api/onboarding/financial-questionnaire": {
                "questionnaire_id": "questionnaire_demo_123",
                "status": "completed",
                "completion_percentage": 75
            },
            "/api/onboarding/complete": {
                "completion_id": "completion_demo_123",
                "status": "completed",
                "completion_percentage": 100
            },
            "/api/user/profile": {
                "monthly_income": 75000,
                "income_frequency": "monthly",
                "current_savings": 15000,
                "profile_complete": True
            },
            "/api/health/checkin": {
                "checkin_id": "checkin_demo_123",
                "status": "submitted",
                "health_score": 85
            },
            "/api/health/checkin/history": {
                "checkins": [
                    {"id": "checkin_demo_123", "date": datetime.now().strftime("%Y-%m-%d"), "score": 85}
                ],
                "total_checkins": 1
            },
            "/api/health/status": {
                "weekly_checkin_complete": True,
                "streak_days": 1,
                "next_checkin_due": "2025-01-20"
            },
            "/api/health/stats": {
                "total_checkins": 1,
                "average_score": 85,
                "streak_days": 1
            },
            "/forecast": {
                "data": {
                    "daily_forecasts": [{"date": "2025-01-15", "balance": 15000}] * 30,
                    "total_days": 30
                }
            },
            "/api/financial/analysis": {
                "total_income": 75000,
                "total_expenses": 60000,
                "net_cash_flow": 15000,
                "savings_rate": 20.0
            },
            "/api/financial/spending-patterns": {
                "patterns": [
                    {"category": "housing", "amount": 2000, "percentage": 33.3},
                    {"category": "transportation", "amount": 500, "percentage": 8.3}
                ]
            },
            "/api/financial/budget-variance": {
                "overall_variance": 0.0,
                "categories": [
                    {"category": "housing", "budgeted": 2000, "actual": 2000, "variance": 0}
                ]
            },
            "/api/financial/insights": {
                "insights": [
                    {"type": "spending", "title": "Housing costs are 33% of your income", "priority": "medium"}
                ]
            },
            "/api/subscriptions/upgrade-options": {
                "options": [
                    {"tier": "mid_tier", "price_monthly": 2000, "features": ["career_risk_management"]}
                ]
            },
            "/api/subscriptions/upgrade": {
                "subscription_id": "sub_demo_456",
                "tier": "mid_tier",
                "status": "upgraded"
            },
            "/api/features/available": {
                "available_features": ["career_risk_management", "advanced_ai_insights"],
                "current_tier": "mid_tier"
            },
            "/api/career/job-recommendations": {
                "recommendations": [
                    {"title": "Senior Software Engineer", "company": "Tech Corp", "salary": 95000},
                    {"title": "Lead Developer", "company": "Innovation Inc", "salary": 105000}
                ],
                "total_opportunities": 2
            },
            "/api/career/salary-analysis": {
                "current_salary": 75000,
                "market_average": 85000,
                "percentile": 65
            },
            "/api/career/advancement-strategy": {
                "strategy": "Focus on leadership skills and advanced technologies",
                "timeline_months": 12,
                "expected_salary_increase": 20
            },
            "/api/career/skill-gaps": {
                "skill_gaps": ["leadership", "cloud_architecture"],
                "recommendations": ["Take leadership course", "Get AWS certification"]
            },
            "/api/career/risk-management": {
                "risk_score": 25,
                "risk_factors": ["industry_volatility"],
                "mitigation_strategies": ["Diversify skills", "Network actively"]
            },
            "/api/reports/generate": {
                "report_id": "report_demo_123",
                "status": "generated",
                "report_type": "monthly"
            },
            "/api/reports/report_demo_123": {
                "report_name": "January 2025 Financial Report",
                "period": "2025-01-01 to 2025-01-31",
                "status": "completed"
            },
            "/api/reports/report_demo_123/analytics": {
                "metrics": {
                    "total_income": 75000,
                    "total_expenses": 60000,
                    "savings_rate": 20.0
                }
            },
            "/api/reports/report_demo_123/insights": {
                "insights": [
                    {"type": "savings", "title": "You saved 20% of your income this month", "impact": "positive"}
                ]
            },
            "/api/reports/report_demo_123/recommendations": {
                "recommendations": [
                    {"type": "investment", "title": "Consider opening an IRA", "priority": "high"}
                ]
            },
            "/api/reports/report_demo_123/download": {
                "download_url": "/downloads/report_demo_123.pdf",
                "file_size": "2.5MB"
            }
        }
        
        # Get mock response
        response = mock_responses.get(endpoint, {"status": "success", "message": "Mock response"})
        print(f"  📥 Response: {json.dumps(response, indent=2)}")
        return response

    def step_1_discover_app(self) -> bool:
        """Step 1: User discovers Mingus app"""
        print("\n" + "="*60)
        print("STEP 1: USER DISCOVERS MINGUS APP")
        print("="*60)
        
        try:
            # Test landing page
            response = self.simulate_api_call("/")
            if response.get("page") == "landing":
                self.log_step("Landing Page Access", "PASS", "Landing page accessible")
            else:
                self.log_step("Landing Page Access", "FAIL", "Landing page not accessible")
                return False
            
            # Test assessment landing page
            response = self.simulate_api_call("/assessments")
            if response.get("page") == "assessments":
                self.log_step("Assessment Landing", "PASS", "Assessment page accessible")
            else:
                self.log_step("Assessment Landing", "FAIL", "Assessment page not accessible")
                return False
            
            # Test available assessments
            response = self.simulate_api_call("/api/assessments/available")
            assessments = response.get("assessments", [])
            if len(assessments) > 0:
                self.log_step("Available Assessments", "PASS", f"Found {len(assessments)} assessments")
            else:
                self.log_step("Available Assessments", "FAIL", "No assessments found")
                return False
            
            self.log_step("App Discovery", "PASS", "User successfully discovered the app")
            return True
            
        except Exception as e:
            self.log_step("App Discovery", "FAIL", f"Error: {str(e)}")
            return False

    def step_2_signup_budget_tier(self) -> bool:
        """Step 2: Signs up for Budget tier ($10)"""
        print("\n" + "="*60)
        print("STEP 2: SIGN UP FOR BUDGET TIER ($10)")
        print("="*60)
        
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
            
            response = self.simulate_api_call("/api/auth/signup", "POST", signup_data)
            if response.get("status") == "created":
                self.user_data = response
                self.log_step("User Signup", "PASS", f"User created with ID: {response.get('user_id', 'N/A')}")
            else:
                self.log_step("User Signup", "FAIL", "User creation failed")
                return False
            
            # Test subscription creation for Budget tier
            subscription_data = {
                "tier": "budget",
                "billing_cycle": "monthly",
                "amount": 1000  # $10.00 in cents
            }
            
            response = self.simulate_api_call("/api/subscriptions/create", "POST", subscription_data)
            if response.get("status") == "active":
                self.log_step("Budget Tier Subscription", "PASS", f"Subscription created: {response.get('subscription_id', 'N/A')}")
            else:
                self.log_step("Budget Tier Subscription", "FAIL", "Subscription creation failed")
                return False
            
            # Test tier access verification
            response = self.simulate_api_call("/api/subscriptions/tier-access")
            if response.get("current_tier") == "budget":
                self.log_step("Tier Access Verification", "PASS", "Budget tier access confirmed")
            else:
                self.log_step("Tier Access Verification", "FAIL", f"Expected budget tier, got: {response.get('current_tier')}")
                return False
            
            self.log_step("Budget Tier Signup", "PASS", "Successfully signed up for Budget tier")
            return True
            
        except Exception as e:
            self.log_step("Budget Tier Signup", "FAIL", f"Error: {str(e)}")
            return False

    def step_3_profile_setup(self) -> bool:
        """Step 3: Completes profile setup with income/expenses"""
        print("\n" + "="*60)
        print("STEP 3: COMPLETE PROFILE SETUP WITH INCOME/EXPENSES")
        print("="*60)
        
        try:
            # Test profile creation
            profile_data = {
                "monthly_income": 75000,
                "income_frequency": "monthly",
                "primary_income_source": "full-time-employment"
            }
            
            response = self.simulate_api_call("/api/onboarding/profile", "POST", profile_data)
            if response.get("status") == "created":
                self.log_step("Profile Creation", "PASS", f"Profile created: {response.get('profile_id', 'N/A')}")
            else:
                self.log_step("Profile Creation", "FAIL", "Profile creation failed")
                return False
            
            # Test expenses setup
            expenses_data = {
                "housing": 2000,
                "transportation": 500,
                "food": 600
            }
            
            response = self.simulate_api_call("/api/onboarding/expenses", "POST", expenses_data)
            if response.get("status") == "saved":
                self.log_step("Expenses Setup", "PASS", f"Expenses saved: {response.get('expenses_id', 'N/A')}")
            else:
                self.log_step("Expenses Setup", "FAIL", "Expenses setup failed")
                return False
            
            # Test financial questionnaire
            questionnaire_data = {
                "risk_tolerance": 7,
                "financial_knowledge": 6,
                "primary_goal": "save_money"
            }
            
            response = self.simulate_api_call("/api/onboarding/financial-questionnaire", "POST", questionnaire_data)
            if response.get("status") == "completed":
                self.log_step("Financial Questionnaire", "PASS", f"Questionnaire completed: {response.get('questionnaire_id', 'N/A')}")
            else:
                self.log_step("Financial Questionnaire", "FAIL", "Questionnaire completion failed")
                return False
            
            # Test onboarding completion
            response = self.simulate_api_call("/api/onboarding/complete", "POST")
            if response.get("status") == "completed":
                self.log_step("Onboarding Completion", "PASS", f"Onboarding completed: {response.get('completion_id', 'N/A')}")
            else:
                self.log_step("Onboarding Completion", "FAIL", "Onboarding completion failed")
                return False
            
            # Test profile retrieval
            response = self.simulate_api_call("/api/user/profile")
            if response.get("profile_complete"):
                self.log_step("Profile Retrieval", "PASS", "Profile data correctly saved and retrieved")
            else:
                self.log_step("Profile Retrieval", "FAIL", "Profile data not complete")
                return False
            
            self.log_step("Profile Setup", "PASS", "Successfully completed profile setup with income/expenses")
            return True
            
        except Exception as e:
            self.log_step("Profile Setup", "FAIL", f"Error: {str(e)}")
            return False

    def step_4_weekly_checkin(self) -> bool:
        """Step 4: Performs first weekly check-in"""
        print("\n" + "="*60)
        print("STEP 4: PERFORM FIRST WEEKLY CHECK-IN")
        print("="*60)
        
        try:
            # Test health check-in form access
            response = self.simulate_api_call("/api/health/checkin")
            self.log_step("Health Check-in Form", "PASS", "Health check-in form accessible")
            
            # Test health check-in submission
            checkin_data = {
                "physical_activity_minutes": 45,
                "relationships_rating": 8,
                "stress_level": 6,
                "energy_level": 7,
                "mood_rating": 8
            }
            
            response = self.simulate_api_call("/api/health/checkin", "POST", checkin_data)
            if response.get("status") == "submitted":
                self.log_step("Health Check-in Submission", "PASS", f"Check-in submitted: {response.get('checkin_id', 'N/A')}")
            else:
                self.log_step("Health Check-in Submission", "FAIL", "Check-in submission failed")
                return False
            
            # Test check-in history
            response = self.simulate_api_call("/api/health/checkin/history")
            checkins = response.get("checkins", [])
            if len(checkins) > 0:
                self.log_step("Check-in History", "PASS", f"Found {len(checkins)} check-ins in history")
            else:
                self.log_step("Check-in History", "FAIL", "No check-ins found in history")
                return False
            
            # Test health status
            response = self.simulate_api_call("/api/health/status")
            if response.get("weekly_checkin_complete"):
                self.log_step("Health Status", "PASS", "Weekly check-in marked as complete")
            else:
                self.log_step("Health Status", "FAIL", "Weekly check-in not marked as complete")
                return False
            
            # Test health statistics
            response = self.simulate_api_call("/api/health/stats")
            stats = response
            self.log_step("Health Statistics", "PASS", f"Health stats generated: {stats.get('total_checkins', 0)} total check-ins")
            
            self.log_step("Weekly Check-in", "PASS", "Successfully completed first weekly check-in")
            return True
            
        except Exception as e:
            self.log_step("Weekly Check-in", "FAIL", f"Error: {str(e)}")
            return False

    def step_5_financial_forecast(self) -> bool:
        """Step 5: Reviews financial forecast"""
        print("\n" + "="*60)
        print("STEP 5: REVIEW FINANCIAL FORECAST")
        print("="*60)
        
        try:
            # Test cash flow forecast generation
            forecast_data = {
                "user_id": self.user_data.get('user_id'),
                "initial_balance": 15000,
                "start_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = self.simulate_api_call("/forecast", "POST", forecast_data)
            forecasts = response.get("data", {}).get("daily_forecasts", [])
            if len(forecasts) > 0:
                self.log_step("Cash Flow Forecast", "PASS", f"Forecast generated: {len(forecasts)} days")
            else:
                self.log_step("Cash Flow Forecast", "FAIL", "Forecast generation failed")
                return False
            
            # Test financial analysis
            response = self.simulate_api_call("/api/financial/analysis")
            if response.get("total_income"):
                self.log_step("Financial Analysis", "PASS", "Financial analysis generated")
            else:
                self.log_step("Financial Analysis", "FAIL", "Financial analysis failed")
                return False
            
            # Test spending patterns
            response = self.simulate_api_call("/api/financial/spending-patterns")
            patterns = response.get("patterns", [])
            if len(patterns) > 0:
                self.log_step("Spending Patterns", "PASS", "Spending patterns analyzed")
            else:
                self.log_step("Spending Patterns", "FAIL", "Spending patterns analysis failed")
                return False
            
            # Test budget variance
            response = self.simulate_api_call("/api/financial/budget-variance")
            if response.get("overall_variance") is not None:
                self.log_step("Budget Variance", "PASS", "Budget variance calculated")
            else:
                self.log_step("Budget Variance", "FAIL", "Budget variance calculation failed")
                return False
            
            # Test financial insights (Budget tier limited)
            response = self.simulate_api_call("/api/financial/insights")
            insights = response.get("insights", [])
            if len(insights) > 0:
                self.log_step("Financial Insights", "PASS", f"Generated {len(insights)} insights")
            else:
                self.log_step("Financial Insights", "FAIL", "Financial insights generation failed")
                return False
            
            self.log_step("Financial Forecast Review", "PASS", "Successfully reviewed financial forecast and analysis")
            return True
            
        except Exception as e:
            self.log_step("Financial Forecast Review", "FAIL", f"Error: {str(e)}")
            return False

    def step_6_upgrade_mid_tier(self) -> bool:
        """Step 6: Upgrades to Mid-tier ($20)"""
        print("\n" + "="*60)
        print("STEP 6: UPGRADE TO MID-TIER ($20)")
        print("="*60)
        
        try:
            # Test upgrade options
            response = self.simulate_api_call("/api/subscriptions/upgrade-options")
            options = response.get("options", [])
            mid_tier_option = next((opt for opt in options if opt.get("tier") == "mid_tier"), None)
            if mid_tier_option:
                self.log_step("Upgrade Options", "PASS", f"Mid-tier option available: ${mid_tier_option.get('price_monthly', 0)/100}/month")
            else:
                self.log_step("Upgrade Options", "FAIL", "Mid-tier option not found")
                return False
            
            # Test subscription upgrade
            upgrade_data = {
                "new_tier": "mid_tier",
                "billing_cycle": "monthly"
            }
            
            response = self.simulate_api_call("/api/subscriptions/upgrade", "POST", upgrade_data)
            if response.get("status") == "upgraded":
                self.log_step("Subscription Upgrade", "PASS", f"Upgraded to mid-tier: {response.get('subscription_id', 'N/A')}")
            else:
                self.log_step("Subscription Upgrade", "FAIL", "Subscription upgrade failed")
                return False
            
            # Test new tier access verification
            response = self.simulate_api_call("/api/subscriptions/tier-access")
            if response.get("current_tier") == "mid_tier":
                self.log_step("Mid-Tier Access Verification", "PASS", "Mid-tier access confirmed")
            else:
                self.log_step("Mid-Tier Access Verification", "FAIL", f"Expected mid_tier, got: {response.get('current_tier')}")
                return False
            
            # Test enhanced features access
            response = self.simulate_api_call("/api/features/available")
            features = response.get("available_features", [])
            if "career_risk_management" in features:
                self.log_step("Enhanced Features Access", "PASS", "Career risk management feature now available")
            else:
                self.log_step("Enhanced Features Access", "FAIL", "Career risk management feature not available")
                return False
            
            self.log_step("Mid-Tier Upgrade", "PASS", "Successfully upgraded to Mid-tier")
            return True
            
        except Exception as e:
            self.log_step("Mid-Tier Upgrade", "FAIL", f"Error: {str(e)}")
            return False

    def step_7_career_recommendations(self) -> bool:
        """Step 7: Uses career recommendations"""
        print("\n" + "="*60)
        print("STEP 7: USE CAREER RECOMMENDATIONS")
        print("="*60)
        
        try:
            # Test job recommendations
            job_data = {
                "current_salary": 75000,
                "target_locations": ["Atlanta", "Houston", "Dallas"],
                "resume_text": "Experienced software engineer with 5 years in Python development..."
            }
            
            response = self.simulate_api_call("/api/career/job-recommendations", "POST", job_data)
            recommendations = response.get("recommendations", [])
            if len(recommendations) > 0:
                self.log_step("Job Recommendations", "PASS", f"Generated {len(recommendations)} job recommendations")
            else:
                self.log_step("Job Recommendations", "FAIL", "Job recommendations generation failed")
                return False
            
            # Test salary analysis
            response = self.simulate_api_call("/api/career/salary-analysis")
            if response.get("current_salary"):
                self.log_step("Salary Analysis", "PASS", "Salary analysis generated")
            else:
                self.log_step("Salary Analysis", "FAIL", "Salary analysis failed")
                return False
            
            # Test career advancement strategy
            strategy_data = {
                "risk_preference": "balanced",
                "timeline_months": 12
            }
            
            response = self.simulate_api_call("/api/career/advancement-strategy", "POST", strategy_data)
            if response.get("strategy"):
                self.log_step("Career Strategy", "PASS", "Career advancement strategy generated")
            else:
                self.log_step("Career Strategy", "FAIL", "Career strategy generation failed")
                return False
            
            # Test skill gap analysis
            response = self.simulate_api_call("/api/career/skill-gaps")
            skill_gaps = response.get("skill_gaps", [])
            if len(skill_gaps) > 0:
                self.log_step("Skill Gap Analysis", "PASS", "Skill gap analysis completed")
            else:
                self.log_step("Skill Gap Analysis", "FAIL", "Skill gap analysis failed")
                return False
            
            # Test career risk management (Mid-tier feature)
            response = self.simulate_api_call("/api/career/risk-management")
            if response.get("risk_score") is not None:
                self.log_step("Career Risk Management", "PASS", "Career risk management analysis available")
            else:
                self.log_step("Career Risk Management", "FAIL", "Career risk management failed")
                return False
            
            self.log_step("Career Recommendations", "PASS", "Successfully used career recommendations")
            return True
            
        except Exception as e:
            self.log_step("Career Recommendations", "FAIL", f"Error: {str(e)}")
            return False

    def step_8_monthly_report(self) -> bool:
        """Step 8: Receives and reviews monthly report"""
        print("\n" + "="*60)
        print("STEP 8: RECEIVE AND REVIEW MONTHLY REPORT")
        print("="*60)
        
        try:
            # Test monthly report generation
            report_data = {
                "report_type": "monthly",
                "include_insights": True,
                "include_recommendations": True
            }
            
            response = self.simulate_api_call("/api/reports/generate", "POST", report_data)
            if response.get("status") == "generated":
                report_id = response.get("report_id")
                self.log_step("Monthly Report Generation", "PASS", f"Report generated: {report_id}")
            else:
                self.log_step("Monthly Report Generation", "FAIL", "Report generation failed")
                return False
            
            # Test report retrieval
            response = self.simulate_api_call(f"/api/reports/{report_id}")
            if response.get("report_name"):
                self.log_step("Report Retrieval", "PASS", f"Report retrieved: {response.get('report_name', 'N/A')}")
            else:
                self.log_step("Report Retrieval", "FAIL", "Report retrieval failed")
                return False
            
            # Test report analytics
            response = self.simulate_api_call(f"/api/reports/{report_id}/analytics")
            if response.get("metrics"):
                self.log_step("Report Analytics", "PASS", "Report analytics generated")
            else:
                self.log_step("Report Analytics", "FAIL", "Report analytics failed")
                return False
            
            # Test report insights
            response = self.simulate_api_call(f"/api/reports/{report_id}/insights")
            insights = response.get("insights", [])
            if len(insights) > 0:
                self.log_step("Report Insights", "PASS", f"Generated {len(insights)} insights")
            else:
                self.log_step("Report Insights", "FAIL", "Report insights failed")
                return False
            
            # Test report recommendations
            response = self.simulate_api_call(f"/api/reports/{report_id}/recommendations")
            recommendations = response.get("recommendations", [])
            if len(recommendations) > 0:
                self.log_step("Report Recommendations", "PASS", f"Generated {len(recommendations)} recommendations")
            else:
                self.log_step("Report Recommendations", "FAIL", "Report recommendations failed")
                return False
            
            # Test report download
            response = self.simulate_api_call(f"/api/reports/{report_id}/download")
            if response.get("download_url"):
                self.log_step("Report Download", "PASS", "Report download successful")
            else:
                self.log_step("Report Download", "FAIL", "Report download failed")
                return False
            
            self.log_step("Monthly Report Review", "PASS", "Successfully received and reviewed monthly report")
            return True
            
        except Exception as e:
            self.log_step("Monthly Report Review", "FAIL", f"Error: {str(e)}")
            return False

    def run_complete_journey(self) -> Dict[str, Any]:
        """Run the complete user journey simulation"""
        print("Starting MINGUS User Journey Demo")
        print(f"Demo User: {self.test_user['email']}")
        print("="*60)
        
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
                print(f"Error in {step_name}: {str(e)}")
                results[step_name] = "ERROR"
                all_passed = False
        
        # Generate summary
        summary = {
            "status": "PASS" if all_passed else "FAIL",
            "timestamp": datetime.now().isoformat(),
            "demo_user": self.test_user["email"],
            "results": results,
            "detailed_results": self.test_results
        }
        
        # Print summary
        print("\n" + "="*60)
        print("DEMO SUMMARY")
        print("="*60)
        print(f"Overall Status: {summary['status']}")
        print(f"Demo User: {summary['demo_user']}")
        print("\nStep Results:")
        for step, result in results.items():
            print(f"  {step}: {result}")
        
        return summary

def main():
    """Main function to run the demo"""
    demo = MockMingusUserJourneyDemo()
    results = demo.run_complete_journey()
    
    print(f"\nDemo completed with status: {results['status']}")
    return 0 if results["status"] == "PASS" else 1

if __name__ == "__main__":
    exit(main())
