#!/usr/bin/env python3
"""
MINGUS Application - Financial Features Tester
Comprehensive testing of financial features with full security enabled
"""

import asyncio
import aiohttp
import time
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class FinancialTestResult:
    """Financial feature test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

class FinancialFeaturesValidator:
    """Comprehensive financial features validation for MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[FinancialTestResult] = []
        self.auth_token = None
        self.csrf_token = None
        
    async def run_financial_validation(self) -> Dict[str, Any]:
        """Run comprehensive financial features validation"""
        print("💰 MINGUS Application - Financial Features Validation")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Setup test user and authentication
        await self.setup_test_user()
        
        # 2. Test financial dashboard
        await self.test_financial_dashboard()
        
        # 3. Test budget management
        await self.test_budget_management()
        
        # 4. Test financial goals
        await self.test_financial_goals()
        
        # 5. Test transaction management
        await self.test_transaction_management()
        
        # 6. Test financial security measures
        await self.test_financial_security()
        
        # 7. Test financial data validation
        await self.test_financial_data_validation()
        
        # 8. Test financial API authorization
        await self.test_financial_api_authorization()
        
        return self.generate_financial_report()
    
    async def setup_test_user(self):
        """Setup test user for financial testing"""
        print("\n🔧 Setting up test user for financial testing...")
        
        try:
            # Register test user
            test_email = f"financialtest{int(time.time())}@mingus.test"
            test_password = "FinancialTest123!"
            
            async with aiohttp.ClientSession() as session:
                # Register user
                async with session.post(f"{self.base_url}/api/auth/register", json={
                    "email": test_email,
                    "password": test_password,
                    "first_name": "Financial",
                    "last_name": "Tester",
                    "terms_accepted": True
                }) as response:
                    if response.status in [200, 201, 409]:  # 409 = user already exists
                        print(f"  ✅ Test user registered: {test_email}")
                    else:
                        print(f"  ⚠️ User registration status: {response.status}")
                
                # Login user
                async with session.post(f"{self.base_url}/api/auth/login", json={
                    "email": test_email,
                    "password": test_password
                }) as response:
                    if response.status == 200:
                        login_response = await response.json()
                        self.auth_token = login_response.get("access_token")
                        print(f"  ✅ Test user authenticated")
                    else:
                        print(f"  ❌ Test user authentication failed: {response.status}")
                
                # Get CSRF token
                if self.auth_token:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    async with session.get(f"{self.base_url}/api/csrf/token", headers=headers) as response:
                        if response.status == 200:
                            csrf_response = await response.json()
                            self.csrf_token = csrf_response.get("csrf_token")
                            print(f"  ✅ CSRF token obtained")
                        else:
                            print(f"  ⚠️ CSRF token not obtained: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Test user setup failed: {str(e)}")
    
    async def test_financial_dashboard(self):
        """Test financial dashboard functionality"""
        print("\n📊 Testing Financial Dashboard...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping dashboard tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test financial dashboard retrieval
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/financial/dashboard", headers=headers) as response:
                    if response.status == 200:
                        dashboard_data = await response.json()
                        
                        # Check if dashboard contains expected financial data
                        expected_fields = ["total_income", "total_expenses", "net_worth", "savings_rate"]
                        fields_present = sum(1 for field in expected_fields if field in dashboard_data)
                        
                        if fields_present >= 2:  # At least 2 financial fields present
                            self.results.append(FinancialTestResult(
                                test_name="Financial Dashboard Retrieval",
                                status="passed",
                                details={
                                    "endpoint": "/api/financial/dashboard",
                                    "status_code": response.status,
                                    "fields_present": fields_present,
                                    "total_expected_fields": len(expected_fields)
                                },
                                timestamp=datetime.now(),
                                recommendations=["Financial dashboard is working correctly"]
                            ))
                            print(f"  ✅ Financial dashboard loaded with {fields_present} financial fields")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Dashboard Retrieval",
                                status="warning",
                                details={
                                    "endpoint": "/api/financial/dashboard",
                                    "status_code": response.status,
                                    "fields_present": fields_present,
                                    "total_expected_fields": len(expected_fields)
                                },
                                timestamp=datetime.now(),
                                recommendations=["Enhance financial dashboard with more comprehensive data"]
                            ))
                            print(f"  ⚠️ Financial dashboard loaded with limited data: {fields_present} fields")
                    else:
                        self.results.append(FinancialTestResult(
                            test_name="Financial Dashboard Retrieval",
                            status="failed",
                            details={
                                "endpoint": "/api/financial/dashboard",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix financial dashboard endpoint"]
                        ))
                        print(f"  ❌ Financial dashboard failed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Financial Dashboard Test: ERROR - {str(e)}")
    
    async def test_budget_management(self):
        """Test budget management functionality"""
        print("\n💳 Testing Budget Management...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping budget tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test budget retrieval
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/financial/budget", headers=headers) as response:
                    if response.status == 200:
                        budget_data = await response.json()
                        
                        self.results.append(FinancialTestResult(
                            test_name="Budget Retrieval",
                            status="passed",
                            details={
                                "endpoint": "/api/financial/budget",
                                "status_code": response.status,
                                "budget_count": len(budget_data) if isinstance(budget_data, list) else 1
                            },
                            timestamp=datetime.now(),
                            recommendations=["Budget retrieval is working correctly"]
                        ))
                        print(f"  ✅ Budget retrieval successful")
                    else:
                        self.results.append(FinancialTestResult(
                            test_name="Budget Retrieval",
                            status="failed",
                            details={
                                "endpoint": "/api/financial/budget",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix budget retrieval endpoint"]
                        ))
                        print(f"  ❌ Budget retrieval failed: {response.status}")
                
                # Test budget creation with CSRF protection
                if self.csrf_token:
                    headers["X-CSRF-Token"] = self.csrf_token
                    
                    budget_data = {
                        "name": "Test Budget",
                        "amount": 1000.00,
                        "category": "test",
                        "frequency": "monthly",
                        "is_income": False
                    }
                    
                    async with session.post(f"{self.base_url}/api/financial/budget", 
                                          json=budget_data, headers=headers) as response:
                        if response.status in [200, 201]:
                            self.results.append(FinancialTestResult(
                                test_name="Budget Creation with CSRF",
                                status="passed",
                                details={
                                    "endpoint": "/api/financial/budget",
                                    "status_code": response.status,
                                    "csrf_protected": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Budget creation with CSRF protection is working correctly"]
                            ))
                            print(f"  ✅ Budget creation with CSRF protection successful")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Budget Creation with CSRF",
                                status="failed",
                                details={
                                    "endpoint": "/api/financial/budget",
                                    "status_code": response.status,
                                    "csrf_protected": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Fix budget creation endpoint"]
                            ))
                            print(f"  ❌ Budget creation failed: {response.status}")
                else:
                    print(f"  ⚠️ Skipping budget creation test - No CSRF token")
                    
        except Exception as e:
            print(f"  ❌ Budget Management Test: ERROR - {str(e)}")
    
    async def test_financial_goals(self):
        """Test financial goals functionality"""
        print("\n🎯 Testing Financial Goals...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping goals tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test financial goals retrieval
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/financial/goals", headers=headers) as response:
                    if response.status == 200:
                        goals_data = await response.json()
                        
                        self.results.append(FinancialTestResult(
                            test_name="Financial Goals Retrieval",
                            status="passed",
                            details={
                                "endpoint": "/api/financial/goals",
                                "status_code": response.status,
                                "goals_count": len(goals_data) if isinstance(goals_data, list) else 1
                            },
                            timestamp=datetime.now(),
                            recommendations=["Financial goals retrieval is working correctly"]
                        ))
                        print(f"  ✅ Financial goals retrieval successful")
                    else:
                        self.results.append(FinancialTestResult(
                            test_name="Financial Goals Retrieval",
                            status="failed",
                            details={
                                "endpoint": "/api/financial/goals",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix financial goals endpoint"]
                        ))
                        print(f"  ❌ Financial goals retrieval failed: {response.status}")
                
                # Test financial goals creation
                if self.csrf_token:
                    headers["X-CSRF-Token"] = self.csrf_token
                    
                    goal_data = {
                        "title": "Test Emergency Fund",
                        "target_amount": 5000.00,
                        "current_amount": 1000.00,
                        "target_date": "2025-12-31",
                        "category": "emergency_fund",
                        "priority": "high"
                    }
                    
                    async with session.post(f"{self.base_url}/api/financial/goals", 
                                          json=goal_data, headers=headers) as response:
                        if response.status in [200, 201]:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Goals Creation",
                                status="passed",
                                details={
                                    "endpoint": "/api/financial/goals",
                                    "status_code": response.status,
                                    "csrf_protected": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Financial goals creation is working correctly"]
                            ))
                            print(f"  ✅ Financial goals creation successful")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Goals Creation",
                                status="failed",
                                details={
                                    "endpoint": "/api/financial/goals",
                                    "status_code": response.status,
                                    "csrf_protected": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Fix financial goals creation endpoint"]
                            ))
                            print(f"  ❌ Financial goals creation failed: {response.status}")
                else:
                    print(f"  ⚠️ Skipping goals creation test - No CSRF token")
                    
        except Exception as e:
            print(f"  ❌ Financial Goals Test: ERROR - {str(e)}")
    
    async def test_transaction_management(self):
        """Test transaction management functionality"""
        print("\n💸 Testing Transaction Management...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping transaction tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test transaction retrieval
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/financial/transactions", headers=headers) as response:
                    if response.status == 200:
                        transactions_data = await response.json()
                        
                        self.results.append(FinancialTestResult(
                            test_name="Transaction Retrieval",
                            status="passed",
                            details={
                                "endpoint": "/api/financial/transactions",
                                "status_code": response.status,
                                "transactions_count": len(transactions_data) if isinstance(transactions_data, list) else 1
                            },
                            timestamp=datetime.now(),
                            recommendations=["Transaction retrieval is working correctly"]
                        ))
                        print(f"  ✅ Transaction retrieval successful")
                    else:
                        self.results.append(FinancialTestResult(
                            test_name="Transaction Retrieval",
                            status="failed",
                            details={
                                "endpoint": "/api/financial/transactions",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix transaction retrieval endpoint"]
                        ))
                        print(f"  ❌ Transaction retrieval failed: {response.status}")
                
                # Test transaction creation
                if self.csrf_token:
                    headers["X-CSRF-Token"] = self.csrf_token
                    
                    transaction_data = {
                        "amount": 100.00,
                        "description": "Test Transaction",
                        "category": "test",
                        "transaction_date": datetime.now().strftime("%Y-%m-%d"),
                        "transaction_type": "expense"
                    }
                    
                    async with session.post(f"{self.base_url}/api/financial/transactions", 
                                          json=transaction_data, headers=headers) as response:
                        if response.status in [200, 201]:
                            self.results.append(FinancialTestResult(
                                test_name="Transaction Creation",
                                status="passed",
                                details={
                                    "endpoint": "/api/financial/transactions",
                                    "status_code": response.status,
                                    "csrf_protected": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Transaction creation is working correctly"]
                            ))
                            print(f"  ✅ Transaction creation successful")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Transaction Creation",
                                status="failed",
                                details={
                                    "endpoint": "/api/financial/transactions",
                                    "status_code": response.status,
                                    "csrf_protected": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Fix transaction creation endpoint"]
                            ))
                            print(f"  ❌ Transaction creation failed: {response.status}")
                else:
                    print(f"  ⚠️ Skipping transaction creation test - No CSRF token")
                    
        except Exception as e:
            print(f"  ❌ Transaction Management Test: ERROR - {str(e)}")
    
    async def test_financial_security(self):
        """Test financial security measures"""
        print("\n🔒 Testing Financial Security...")
        
        try:
            # Test unauthorized access to financial endpoints
            financial_endpoints = [
                "/api/financial/dashboard",
                "/api/financial/budget",
                "/api/financial/goals",
                "/api/financial/transactions"
            ]
            
            async with aiohttp.ClientSession() as session:
                for endpoint in financial_endpoints:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 401:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Endpoint Authorization",
                                status="passed",
                                details={
                                    "endpoint": endpoint,
                                    "status_code": response.status,
                                    "unauthorized_access_blocked": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Financial endpoint authorization is working correctly"]
                            ))
                            print(f"  ✅ {endpoint}: Unauthorized access blocked")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Endpoint Authorization",
                                status="failed",
                                details={
                                    "endpoint": endpoint,
                                    "status_code": response.status,
                                    "unauthorized_access_blocked": False
                                },
                                timestamp=datetime.now(),
                                recommendations=["Implement proper financial endpoint authorization"]
                            ))
                            print(f"  ❌ {endpoint}: Unauthorized access allowed")
                
                # Test CSRF protection on financial endpoints
                if self.csrf_token:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    # Try without CSRF token
                    async with session.post(f"{self.base_url}/api/financial/budget", 
                                          json={"name": "test"}, headers=headers) as response:
                        if response.status in [400, 403]:
                            self.results.append(FinancialTestResult(
                                test_name="Financial CSRF Protection",
                                status="passed",
                                details={
                                    "endpoint": "/api/financial/budget",
                                    "status_code": response.status,
                                    "csrf_protection_active": True
                                },
                                timestamp=datetime.now(),
                                recommendations=["Financial CSRF protection is working correctly"]
                            ))
                            print(f"  ✅ Financial CSRF protection active")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Financial CSRF Protection",
                                status="failed",
                                details={
                                    "endpoint": "/api/financial/budget",
                                    "status_code": response.status,
                                    "csrf_protection_active": False
                                },
                                timestamp=datetime.now(),
                                recommendations=["Implement CSRF protection for financial endpoints"]
                            ))
                            print(f"  ❌ Financial CSRF protection not active")
                else:
                    print(f"  ⚠️ Skipping CSRF test - No CSRF token")
                    
        except Exception as e:
            print(f"  ❌ Financial Security Test: ERROR - {str(e)}")
    
    async def test_financial_data_validation(self):
        """Test financial data validation"""
        print("\n✅ Testing Financial Data Validation...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping validation tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test invalid financial data
            invalid_financial_data = [
                {"amount": -1000.00, "description": "Negative amount"},  # Negative amount
                {"amount": "invalid", "description": "Invalid amount type"},  # Invalid amount type
                {"amount": 1000.00, "description": "", "category": "test"},  # Empty description
                {"amount": 1000.00, "description": "Test", "category": ""},  # Empty category
                {"amount": 1000.00, "description": "Test", "transaction_date": "invalid-date"},  # Invalid date
            ]
            
            async with aiohttp.ClientSession() as session:
                for invalid_data in invalid_financial_data:
                    async with session.post(f"{self.base_url}/api/financial/transactions", 
                                          json=invalid_data, headers=headers) as response:
                        if response.status in [400, 422]:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Data Validation",
                                status="passed",
                                details={
                                    "invalid_data": invalid_data,
                                    "status_code": response.status
                                },
                                timestamp=datetime.now(),
                                recommendations=["Financial data validation is working correctly"]
                            ))
                            print(f"  ✅ Invalid financial data rejected: {list(invalid_data.keys())[0]}")
                        else:
                            self.results.append(FinancialTestResult(
                                test_name="Financial Data Validation",
                                status="failed",
                                details={
                                    "invalid_data": invalid_data,
                                    "status_code": response.status
                                },
                                timestamp=datetime.now(),
                                recommendations=["Implement proper financial data validation"]
                            ))
                            print(f"  ❌ Invalid financial data accepted: {list(invalid_data.keys())[0]}")
                            
        except Exception as e:
            print(f"  ❌ Financial Data Validation Test: ERROR - {str(e)}")
    
    async def test_financial_api_authorization(self):
        """Test financial API authorization"""
        print("\n🔐 Testing Financial API Authorization...")
        
        try:
            # Test different authorization scenarios
            async with aiohttp.ClientSession() as session:
                # Test without authorization header
                async with session.get(f"{self.base_url}/api/financial/dashboard") as response:
                    if response.status == 401:
                        self.results.append(FinancialTestResult(
                            test_name="Financial API Authorization - No Token",
                            status="passed",
                            details={
                                "endpoint": "/api/financial/dashboard",
                                "status_code": response.status,
                                "authorization_required": True
                            },
                            timestamp=datetime.now(),
                            recommendations=["Financial API authorization is working correctly"]
                        ))
                        print(f"  ✅ Financial API requires authorization")
                    else:
                        self.results.append(FinancialTestResult(
                            test_name="Financial API Authorization - No Token",
                            status="failed",
                            details={
                                "endpoint": "/api/financial/dashboard",
                                "status_code": response.status,
                                "authorization_required": False
                            },
                            timestamp=datetime.now(),
                            recommendations=["Implement proper financial API authorization"]
                        ))
                        print(f"  ❌ Financial API does not require authorization")
                
                # Test with invalid authorization header
                headers = {"Authorization": "Bearer invalid_token"}
                async with session.get(f"{self.base_url}/api/financial/dashboard", headers=headers) as response:
                    if response.status == 401:
                        self.results.append(FinancialTestResult(
                            test_name="Financial API Authorization - Invalid Token",
                            status="passed",
                            details={
                                "endpoint": "/api/financial/dashboard",
                                "status_code": response.status,
                                "invalid_token_rejected": True
                            },
                            timestamp=datetime.now(),
                            recommendations=["Financial API token validation is working correctly"]
                        ))
                        print(f"  ✅ Invalid token rejected")
                    else:
                        self.results.append(FinancialTestResult(
                            test_name="Financial API Authorization - Invalid Token",
                            status="failed",
                            details={
                                "endpoint": "/api/financial/dashboard",
                                "status_code": response.status,
                                "invalid_token_rejected": False
                            },
                            timestamp=datetime.now(),
                            recommendations=["Implement proper token validation"]
                        ))
                        print(f"  ❌ Invalid token accepted")
                        
        except Exception as e:
            print(f"  ❌ Financial API Authorization Test: ERROR - {str(e)}")
    
    def generate_financial_report(self) -> Dict[str, Any]:
        """Generate comprehensive financial features report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        financial_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine financial status
        if failed_tests == 0 and warning_tests <= 1:
            financial_status = "FUNCTIONAL"
        elif failed_tests <= 2:
            financial_status = "NEEDS ATTENTION"
        else:
            financial_status = "BROKEN"
        
        return {
            "summary": {
                "financial_status": financial_status,
                "financial_score": round(financial_score, 1),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat(),
                    "recommendations": r.recommendations
                }
                for r in self.results
            ],
            "recommendations": self.generate_financial_recommendations(),
            "production_readiness": self.assess_financial_readiness()
        }
    
    def generate_financial_recommendations(self) -> List[str]:
        """Generate financial recommendations"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.status == "failed"]
        if failed_tests:
            recommendations.append("🚨 CRITICAL: Address failed financial tests before production")
            for test in failed_tests:
                recommendations.append(f"   - {test.test_name}: {test.recommendations[0]}")
        
        warning_tests = [r for r in self.results if r.status == "warning"]
        if warning_tests:
            recommendations.append("⚠️ WARNING: Review financial warnings")
            for test in warning_tests:
                recommendations.append(f"   - {test.test_name}: {test.recommendations[0]}")
        
        if not failed_tests and not warning_tests:
            recommendations.append("✅ All financial tests passed - ready for production")
        
        return recommendations
    
    def assess_financial_readiness(self) -> Dict[str, Any]:
        """Assess financial readiness for production"""
        failed_tests = len([r for r in self.results if r.status == "failed"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        # Financial readiness criteria
        readiness_criteria = {
            "dashboard_working": any("Dashboard" in r.test_name and r.status == "passed" for r in self.results),
            "budget_management_working": any("Budget" in r.test_name and r.status == "passed" for r in self.results),
            "goals_working": any("Goals" in r.test_name and r.status == "passed" for r in self.results),
            "transactions_working": any("Transaction" in r.test_name and r.status == "passed" for r in self.results),
            "security_working": any("Security" in r.test_name and r.status == "passed" for r in self.results),
            "validation_working": any("Validation" in r.test_name and r.status == "passed" for r in self.results),
            "authorization_working": any("Authorization" in r.test_name and r.status == "passed" for r in self.results)
        }
        
        readiness_score = sum(readiness_criteria.values()) / len(readiness_criteria) * 100
        
        if readiness_score >= 90 and failed_tests == 0:
            readiness_status = "READY"
        elif readiness_score >= 70 and failed_tests <= 2:
            readiness_status = "NEEDS MINOR FIXES"
        else:
            readiness_status = "NOT READY"
        
        return {
            "readiness_status": readiness_status,
            "readiness_score": round(readiness_score, 1),
            "criteria": readiness_criteria,
            "blocking_issues": failed_tests,
            "recommendations": [
                "Address all failed financial tests",
                "Ensure all financial features work correctly",
                "Verify financial security measures",
                "Test financial data validation and authorization"
            ]
        }

async def main():
    """Main function to run financial validation"""
    print("💰 MINGUS Application - Financial Features Validation")
    print("=" * 60)
    
    # Initialize financial validator
    financial_validator = FinancialFeaturesValidator()
    
    # Run financial validation
    report = await financial_validator.run_financial_validation()
    
    # Print summary
    print("\n" + "=" * 60)
    print("💰 FINANCIAL VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Financial Status: {report['summary']['financial_status']}")
    print(f"Financial Score: {report['summary']['financial_score']}%")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Warnings: {report['summary']['warning_tests']}")
    
    print("\n🚀 FINANCIAL READINESS")
    print("=" * 60)
    readiness = report['production_readiness']
    print(f"Readiness Status: {readiness['readiness_status']}")
    print(f"Readiness Score: {readiness['readiness_score']}%")
    print(f"Blocking Issues: {readiness['blocking_issues']}")
    
    print("\n📋 FINANCIAL RECOMMENDATIONS")
    print("=" * 60)
    for recommendation in report['recommendations']:
        print(recommendation)
    
    # Save detailed report
    report_file = f"financial_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on financial readiness
    if readiness['readiness_status'] == "READY":
        print("\n🎉 MINGUS Financial Features are READY for production deployment!")
        return 0
    else:
        print(f"\n⚠️ MINGUS Financial Features need attention before production deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
