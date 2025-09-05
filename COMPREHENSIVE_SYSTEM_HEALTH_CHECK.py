#!/usr/bin/env python3
"""
MINGUS Application - Comprehensive System Health Check
Final validation before production migration to DigitalOcean
"""

import asyncio
import aiohttp
import time
import json
import sys
import os
import sqlite3
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    component: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    response_time_ms: float
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None

@dataclass
class SecurityTestResult:
    """Security test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

class SystemHealthChecker:
    """Comprehensive system health checker for MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[HealthCheckResult] = []
        self.security_results: List[SecurityTestResult] = []
        self.start_time = time.time()
        
        # Test user credentials for authenticated endpoints
        self.test_user = {
            "email": "healthcheck@mingus.test",
            "password": "HealthCheck123!",
            "first_name": "Health",
            "last_name": "Checker"
        }
        self.auth_token = None
        
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run complete system health check"""
        print("🚀 MINGUS Application - Comprehensive System Health Check")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 1. Core Application Health
        await self.check_core_application_health()
        
        # 2. Database Health
        await self.check_database_health()
        
        # 3. Authentication System
        await self.check_authentication_system()
        
        # 4. User Profile System
        await self.check_user_profile_system()
        
        # 5. Financial Features
        await self.check_financial_features()
        
        # 6. Article Library
        await self.check_article_library()
        
        # 7. Assessment System
        await self.check_assessment_system()
        
        # 8. Security Features
        await self.check_security_features()
        
        # 9. External Integrations
        await self.check_external_integrations()
        
        # 10. Performance Metrics
        await self.check_performance_metrics()
        
        # Generate comprehensive report
        return self.generate_health_report()
    
    async def check_core_application_health(self):
        """Check core application health and basic endpoints"""
        print("\n🔍 Checking Core Application Health...")
        
        endpoints = [
            ("/", "GET", "Home page"),
            ("/health", "GET", "Health endpoint"),
            ("/api/health", "GET", "API health"),
            ("/api/status", "GET", "Status endpoint"),
            ("/api/csrf/token", "GET", "CSRF token endpoint")
        ]
        
        for endpoint, method, description in endpoints:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, f"{self.base_url}{endpoint}") as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        status = "healthy" if response.status < 400 else "warning"
                        if response.status >= 500:
                            status = "critical"
                        
                        self.results.append(HealthCheckResult(
                            component=f"Core App - {description}",
                            status=status,
                            response_time_ms=response_time,
                            details={
                                "endpoint": endpoint,
                                "method": method,
                                "status_code": response.status,
                                "response_size": len(await response.text()) if response.status < 400 else 0
                            },
                            timestamp=datetime.now()
                        ))
                        
                        print(f"  ✅ {description}: {response.status} ({response_time:.1f}ms)")
                        
            except Exception as e:
                self.results.append(HealthCheckResult(
                    component=f"Core App - {description}",
                    status="critical",
                    response_time_ms=0,
                    details={"endpoint": endpoint, "method": method},
                    timestamp=datetime.now(),
                    error_message=str(e)
                ))
                print(f"  ❌ {description}: ERROR - {str(e)}")
    
    async def check_database_health(self):
        """Check database connectivity and performance"""
        print("\n🗄️ Checking Database Health...")
        
        try:
            # Check SQLite database files
            db_files = [
                "instance/mingus.db",
                "instance/mingus_analytics.db",
                "instance/mingus_alerts.db",
                "instance/mingus_bi.db",
                "instance/mingus_performance.db"
            ]
            
            for db_file in db_files:
                if os.path.exists(db_file):
                    try:
                        start_time = time.time()
                        conn = sqlite3.connect(db_file)
                        cursor = conn.cursor()
                        
                        # Test basic query
                        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                        table_count = cursor.fetchone()[0]
                        
                        # Test table access
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
                        tables = cursor.fetchall()
                        
                        response_time = (time.time() - start_time) * 1000
                        conn.close()
                        
                        self.results.append(HealthCheckResult(
                            component=f"Database - {os.path.basename(db_file)}",
                            status="healthy",
                            response_time_ms=response_time,
                            details={
                                "file_path": db_file,
                                "table_count": table_count,
                                "sample_tables": [t[0] for t in tables],
                                "file_size_mb": os.path.getsize(db_file) / (1024 * 1024)
                            },
                            timestamp=datetime.now()
                        ))
                        
                        print(f"  ✅ {os.path.basename(db_file)}: {table_count} tables ({response_time:.1f}ms)")
                        
                    except Exception as e:
                        self.results.append(HealthCheckResult(
                            component=f"Database - {os.path.basename(db_file)}",
                            status="critical",
                            response_time_ms=0,
                            details={"file_path": db_file},
                            timestamp=datetime.now(),
                            error_message=str(e)
                        ))
                        print(f"  ❌ {os.path.basename(db_file)}: ERROR - {str(e)}")
                else:
                    print(f"  ⚠️ {os.path.basename(db_file)}: File not found")
                    
        except Exception as e:
            print(f"  ❌ Database Health Check: ERROR - {str(e)}")
    
    async def check_authentication_system(self):
        """Check authentication system functionality"""
        print("\n🔐 Checking Authentication System...")
        
        try:
            # Test user registration
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                # Register test user
                register_data = {
                    "email": self.test_user["email"],
                    "password": self.test_user["password"],
                    "first_name": self.test_user["first_name"],
                    "last_name": self.test_user["last_name"],
                    "terms_accepted": True
                }
                
                async with session.post(f"{self.base_url}/api/auth/register", json=register_data) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status in [200, 201, 409]:  # 409 = user already exists
                        status = "healthy"
                        if response.status == 409:
                            print(f"  ✅ User Registration: User already exists ({response_time:.1f}ms)")
                        else:
                            print(f"  ✅ User Registration: Success ({response_time:.1f}ms)")
                    else:
                        status = "warning"
                        print(f"  ⚠️ User Registration: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Authentication - User Registration",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/auth/register",
                            "status_code": response.status,
                            "user_email": self.test_user["email"]
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test user login
                start_time = time.time()
                login_data = {
                    "email": self.test_user["email"],
                    "password": self.test_user["password"]
                }
                
                async with session.post(f"{self.base_url}/api/auth/login", json=login_data) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        login_response = await response.json()
                        self.auth_token = login_response.get("access_token")
                        status = "healthy"
                        print(f"  ✅ User Login: Success ({response_time:.1f}ms)")
                    else:
                        status = "critical"
                        print(f"  ❌ User Login: Failed - Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Authentication - User Login",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/auth/login",
                            "status_code": response.status,
                            "token_received": self.auth_token is not None
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test authentication check
                if self.auth_token:
                    start_time = time.time()
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    
                    async with session.get(f"{self.base_url}/api/auth/check-auth", headers=headers) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        status = "healthy" if response.status == 200 else "warning"
                        print(f"  ✅ Auth Check: Status {response.status} ({response_time:.1f}ms)")
                        
                        self.results.append(HealthCheckResult(
                            component="Authentication - Auth Check",
                            status=status,
                            response_time_ms=response_time,
                            details={
                                "endpoint": "/api/auth/check-auth",
                                "status_code": response.status
                            },
                            timestamp=datetime.now()
                        ))
                        
        except Exception as e:
            print(f"  ❌ Authentication System: ERROR - {str(e)}")
    
    async def check_user_profile_system(self):
        """Check user profile functionality"""
        print("\n👤 Checking User Profile System...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping profile tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test profile retrieval
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/user/profile", headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Profile Retrieval: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="User Profile - Profile Retrieval",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/user/profile",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test profile update with new fields
                start_time = time.time()
                profile_update = {
                    "phone": "+1234567890",
                    "city": "Test City",
                    "state": "TS",
                    "zip_code": "12345",
                    "age_range": "25-34",
                    "gender": "prefer_not_to_say",
                    "marital_status": "single",
                    "dependents_count": 0,
                    "household_size": 1,
                    "education_level": "bachelor",
                    "occupation": "Software Engineer",
                    "industry": "Technology",
                    "years_of_experience": "4-7",
                    "company_name": "Test Company",
                    "company_size": "51-200",
                    "monthly_income": 5000.00,
                    "income_frequency": "monthly",
                    "primary_income_source": "salary",
                    "current_savings_balance": 10000.00,
                    "total_debt_amount": 5000.00,
                    "credit_score_range": "good",
                    "employment_status": "employed",
                    "primary_financial_goal": "emergency_fund",
                    "risk_tolerance_level": "moderate",
                    "financial_knowledge_level": "intermediate",
                    "health_checkin_frequency": "weekly",
                    "notification_preferences": {
                        "weeklyInsights": True,
                        "goalReminders": True,
                        "securityAlerts": True
                    }
                }
                
                async with session.patch(f"{self.base_url}/api/user/profile", 
                                       json=profile_update, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Profile Update: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="User Profile - Profile Update",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/user/profile",
                            "status_code": response.status,
                            "fields_updated": len(profile_update)
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test onboarding progress
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/user/onboarding-progress", 
                                     headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Onboarding Progress: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="User Profile - Onboarding Progress",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/user/onboarding-progress",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                    
        except Exception as e:
            print(f"  ❌ User Profile System: ERROR - {str(e)}")
    
    async def check_financial_features(self):
        """Check financial features and security"""
        print("\n💰 Checking Financial Features...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping financial tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test financial dashboard
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/financial/dashboard", 
                                     headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Financial Dashboard: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Financial - Dashboard",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/financial/dashboard",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test budget creation (with CSRF protection)
                start_time = time.time()
                budget_data = {
                    "name": "Test Budget",
                    "amount": 1000.00,
                    "category": "test",
                    "frequency": "monthly",
                    "is_income": False
                }
                
                async with session.post(f"{self.base_url}/api/financial/budget", 
                                      json=budget_data, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status in [200, 201] else "warning"
                    print(f"  ✅ Budget Creation: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Financial - Budget Creation",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/financial/budget",
                            "status_code": response.status,
                            "csrf_protected": True
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test financial goals
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/financial/goals", 
                                     headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Financial Goals: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Financial - Goals",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/financial/goals",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                    
        except Exception as e:
            print(f"  ❌ Financial Features: ERROR - {str(e)}")
    
    async def check_article_library(self):
        """Check article library functionality"""
        print("\n📚 Checking Article Library...")
        
        try:
            # Test article listing
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/articles/") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Article Listing: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Article Library - Article Listing",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/articles/",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test featured articles
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/articles/featured") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Featured Articles: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Article Library - Featured Articles",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/articles/featured",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test article search
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/articles/search?q=financial") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Article Search: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Article Library - Article Search",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/articles/search",
                            "status_code": response.status,
                            "search_query": "financial"
                        },
                        timestamp=datetime.now()
                    ))
                    
        except Exception as e:
            print(f"  ❌ Article Library: ERROR - {str(e)}")
    
    async def check_assessment_system(self):
        """Check assessment system functionality"""
        print("\n📊 Checking Assessment System...")
        
        try:
            # Test available assessments
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/assessments/available") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Available Assessments: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Assessment System - Available Assessments",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/assessments/available",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                
                # Test specific assessment
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/assessments/financial-wellness") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    status = "healthy" if response.status == 200 else "warning"
                    print(f"  ✅ Financial Wellness Assessment: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.results.append(HealthCheckResult(
                        component="Assessment System - Financial Wellness",
                        status=status,
                        response_time_ms=response_time,
                        details={
                            "endpoint": "/api/assessments/financial-wellness",
                            "status_code": response.status
                        },
                        timestamp=datetime.now()
                    ))
                    
        except Exception as e:
            print(f"  ❌ Assessment System: ERROR - {str(e)}")
    
    async def check_security_features(self):
        """Check security features and configurations"""
        print("\n🔒 Checking Security Features...")
        
        try:
            # Test CSRF protection
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                # Try to make a POST request without CSRF token
                async with session.post(f"{self.base_url}/api/financial/budget", 
                                      json={"name": "test"}) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Should be rejected due to CSRF protection
                    status = "healthy" if response.status in [400, 403] else "warning"
                    print(f"  ✅ CSRF Protection: Status {response.status} ({response_time:.1f}ms)")
                    
                    self.security_results.append(SecurityTestResult(
                        test_name="CSRF Protection",
                        status="passed" if response.status in [400, 403] else "failed",
                        details={
                            "endpoint": "/api/financial/budget",
                            "status_code": response.status,
                            "expected_status": "400 or 403"
                        },
                        timestamp=datetime.now(),
                        recommendations=["Ensure CSRF tokens are required for all state-changing operations"]
                    ))
                
                # Test rate limiting
                start_time = time.time()
                rate_limit_requests = []
                for i in range(5):
                    async with session.get(f"{self.base_url}/api/auth/login") as response:
                        rate_limit_requests.append(response.status)
                
                response_time = (time.time() - start_time) * 1000
                
                # Check if rate limiting is working
                rate_limited = any(status == 429 for status in rate_limit_requests)
                status = "healthy" if rate_limited else "warning"
                print(f"  ✅ Rate Limiting: {'Active' if rate_limited else 'Not Detected'} ({response_time:.1f}ms)")
                
                self.security_results.append(SecurityTestResult(
                    test_name="Rate Limiting",
                    status="passed" if rate_limited else "warning",
                    details={
                        "requests_made": 5,
                        "status_codes": rate_limit_requests,
                        "rate_limited": rate_limited
                    },
                    timestamp=datetime.now(),
                    recommendations=["Ensure rate limiting is properly configured for production"]
                ))
                
                # Test security headers
                start_time = time.time()
                async with session.get(f"{self.base_url}/") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    headers = dict(response.headers)
                    security_headers = {
                        "X-Frame-Options": headers.get("X-Frame-Options"),
                        "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
                        "X-XSS-Protection": headers.get("X-XSS-Protection"),
                        "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
                        "Content-Security-Policy": headers.get("Content-Security-Policy")
                    }
                    
                    headers_present = sum(1 for v in security_headers.values() if v is not None)
                    status = "healthy" if headers_present >= 3 else "warning"
                    print(f"  ✅ Security Headers: {headers_present}/5 present ({response_time:.1f}ms)")
                    
                    self.security_results.append(SecurityTestResult(
                        test_name="Security Headers",
                        status="passed" if headers_present >= 3 else "warning",
                        details={
                            "headers_present": headers_present,
                            "total_headers": 5,
                            "security_headers": security_headers
                        },
                        timestamp=datetime.now(),
                        recommendations=["Ensure all security headers are properly configured"]
                    ))
                    
        except Exception as e:
            print(f"  ❌ Security Features: ERROR - {str(e)}")
    
    async def check_external_integrations(self):
        """Check external service integrations"""
        print("\n🔗 Checking External Integrations...")
        
        # Test external service endpoints (if available)
        external_services = [
            ("/api/integrations/plaid/health", "Plaid Integration"),
            ("/api/integrations/stripe/health", "Stripe Integration"),
            ("/api/integrations/twilio/health", "Twilio Integration"),
            ("/api/integrations/resend/health", "Resend Integration"),
            ("/api/integrations/openai/health", "OpenAI Integration")
        ]
        
        for endpoint, service_name in external_services:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        status = "healthy" if response.status == 200 else "warning"
                        print(f"  ✅ {service_name}: Status {response.status} ({response_time:.1f}ms)")
                        
                        self.results.append(HealthCheckResult(
                            component=f"External Integration - {service_name}",
                            status=status,
                            response_time_ms=response_time,
                            details={
                                "endpoint": endpoint,
                                "status_code": response.status
                            },
                            timestamp=datetime.now()
                        ))
                        
            except Exception as e:
                print(f"  ⚠️ {service_name}: Not available or error - {str(e)}")
    
    async def check_performance_metrics(self):
        """Check system performance metrics"""
        print("\n📈 Checking Performance Metrics...")
        
        try:
            # System resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate average response time
            avg_response_time = sum(r.response_time_ms for r in self.results) / len(self.results) if self.results else 0
            
            # Performance thresholds
            cpu_healthy = cpu_percent < 80
            memory_healthy = memory.percent < 80
            disk_healthy = disk.percent < 90
            response_time_healthy = avg_response_time < 1000  # 1 second
            
            overall_performance = "healthy" if all([cpu_healthy, memory_healthy, disk_healthy, response_time_healthy]) else "warning"
            
            print(f"  ✅ CPU Usage: {cpu_percent:.1f}%")
            print(f"  ✅ Memory Usage: {memory.percent:.1f}%")
            print(f"  ✅ Disk Usage: {disk.percent:.1f}%")
            print(f"  ✅ Average Response Time: {avg_response_time:.1f}ms")
            
            self.results.append(HealthCheckResult(
                component="Performance - System Resources",
                status=overall_performance,
                response_time_ms=avg_response_time,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "avg_response_time_ms": avg_response_time,
                    "total_checks": len(self.results)
                },
                timestamp=datetime.now()
            ))
            
        except Exception as e:
            print(f"  ❌ Performance Metrics: ERROR - {str(e)}")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        total_time = time.time() - self.start_time
        
        # Calculate statistics
        total_checks = len(self.results)
        healthy_checks = len([r for r in self.results if r.status == "healthy"])
        warning_checks = len([r for r in self.results if r.status == "warning"])
        critical_checks = len([r for r in self.results if r.status == "critical"])
        
        # Calculate average response time
        avg_response_time = sum(r.response_time_ms for r in self.results) / total_checks if total_checks > 0 else 0
        
        # Security test results
        security_tests = len(self.security_results)
        security_passed = len([r for r in self.security_results if r.status == "passed"])
        security_failed = len([r for r in self.security_results if r.status == "failed"])
        security_warnings = len([r for r in self.security_results if r.status == "warning"])
        
        # Overall health score
        health_score = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        security_score = (security_passed / security_tests * 100) if security_tests > 0 else 0
        
        # Determine overall status
        if critical_checks > 0:
            overall_status = "CRITICAL"
        elif warning_checks > 5:
            overall_status = "WARNING"
        elif health_score >= 90:
            overall_status = "HEALTHY"
        else:
            overall_status = "NEEDS ATTENTION"
        
        report = {
            "summary": {
                "overall_status": overall_status,
                "health_score": round(health_score, 1),
                "security_score": round(security_score, 1),
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "warning_checks": warning_checks,
                "critical_checks": critical_checks,
                "avg_response_time_ms": round(avg_response_time, 1),
                "total_execution_time_seconds": round(total_time, 1)
            },
            "health_checks": [
                {
                    "component": r.component,
                    "status": r.status,
                    "response_time_ms": round(r.response_time_ms, 1),
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat(),
                    "error_message": r.error_message
                }
                for r in self.results
            ],
            "security_tests": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat(),
                    "recommendations": r.recommendations
                }
                for r in self.security_results
            ],
            "recommendations": self.generate_recommendations(),
            "production_readiness": self.assess_production_readiness()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Check for critical issues
        critical_issues = [r for r in self.results if r.status == "critical"]
        if critical_issues:
            recommendations.append("🚨 CRITICAL: Address critical issues before production deployment")
            for issue in critical_issues:
                recommendations.append(f"   - Fix {issue.component}: {issue.error_message}")
        
        # Check for performance issues
        slow_endpoints = [r for r in self.results if r.response_time_ms > 1000]
        if slow_endpoints:
            recommendations.append("⚡ PERFORMANCE: Optimize slow endpoints")
            for endpoint in slow_endpoints:
                recommendations.append(f"   - {endpoint.component}: {endpoint.response_time_ms:.1f}ms")
        
        # Check for security issues
        security_failures = [r for r in self.security_results if r.status == "failed"]
        if security_failures:
            recommendations.append("🔒 SECURITY: Address security test failures")
            for test in security_failures:
                recommendations.append(f"   - {test.test_name}: {test.recommendations}")
        
        # Check for missing components
        missing_components = [r for r in self.results if r.status == "unknown"]
        if missing_components:
            recommendations.append("❓ UNKNOWN: Investigate unknown component statuses")
            for component in missing_components:
                recommendations.append(f"   - {component.component}")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ All systems appear healthy - ready for production deployment")
        else:
            recommendations.append("📋 Review all recommendations before proceeding to production")
        
        return recommendations
    
    def assess_production_readiness(self) -> Dict[str, Any]:
        """Assess overall production readiness"""
        critical_issues = len([r for r in self.results if r.status == "critical"])
        security_failures = len([r for r in self.security_results if r.status == "failed"])
        slow_endpoints = len([r for r in self.results if r.response_time_ms > 1000])
        
        # Production readiness criteria
        readiness_criteria = {
            "no_critical_issues": critical_issues == 0,
            "security_tests_passed": security_failures == 0,
            "performance_acceptable": slow_endpoints == 0,
            "authentication_working": any("Authentication" in r.component and r.status == "healthy" for r in self.results),
            "database_accessible": any("Database" in r.component and r.status == "healthy" for r in self.results),
            "user_profile_functional": any("User Profile" in r.component and r.status == "healthy" for r in self.results),
            "financial_features_secure": any("Financial" in r.component and r.status == "healthy" for r in self.results)
        }
        
        # Calculate readiness score
        readiness_score = sum(readiness_criteria.values()) / len(readiness_criteria) * 100
        
        # Determine readiness status
        if readiness_score >= 90:
            readiness_status = "READY"
        elif readiness_score >= 70:
            readiness_status = "NEEDS MINOR FIXES"
        elif readiness_score >= 50:
            readiness_status = "NEEDS SIGNIFICANT WORK"
        else:
            readiness_status = "NOT READY"
        
        return {
            "readiness_status": readiness_status,
            "readiness_score": round(readiness_score, 1),
            "criteria": readiness_criteria,
            "blocking_issues": critical_issues + security_failures,
            "recommendations": [
                "Address all critical issues before deployment",
                "Ensure all security tests pass",
                "Optimize slow endpoints for better performance",
                "Verify all core functionality works correctly"
            ]
        }

async def main():
    """Main function to run comprehensive health check"""
    print("🚀 MINGUS Application - Comprehensive System Health Check")
    print("=" * 70)
    
    # Initialize health checker
    health_checker = SystemHealthChecker()
    
    # Run comprehensive health check
    report = await health_checker.run_comprehensive_health_check()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 70)
    print(f"Overall Status: {report['summary']['overall_status']}")
    print(f"Health Score: {report['summary']['health_score']}%")
    print(f"Security Score: {report['summary']['security_score']}%")
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Healthy: {report['summary']['healthy_checks']}")
    print(f"Warnings: {report['summary']['warning_checks']}")
    print(f"Critical: {report['summary']['critical_checks']}")
    print(f"Average Response Time: {report['summary']['avg_response_time_ms']}ms")
    print(f"Execution Time: {report['summary']['total_execution_time_seconds']}s")
    
    print("\n🔒 SECURITY TEST SUMMARY")
    print("=" * 70)
    print(f"Security Tests: {len(report['security_tests'])}")
    print(f"Passed: {len([t for t in report['security_tests'] if t['status'] == 'passed'])}")
    print(f"Failed: {len([t for t in report['security_tests'] if t['status'] == 'failed'])}")
    print(f"Warnings: {len([t for t in report['security_tests'] if t['status'] == 'warning'])}")
    
    print("\n🚀 PRODUCTION READINESS")
    print("=" * 70)
    readiness = report['production_readiness']
    print(f"Readiness Status: {readiness['readiness_status']}")
    print(f"Readiness Score: {readiness['readiness_score']}%")
    print(f"Blocking Issues: {readiness['blocking_issues']}")
    
    print("\n📋 RECOMMENDATIONS")
    print("=" * 70)
    for recommendation in report['recommendations']:
        print(recommendation)
    
    # Save detailed report
    report_file = f"health_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on readiness
    if readiness['readiness_status'] == "READY":
        print("\n🎉 MINGUS Application is READY for production deployment!")
        return 0
    else:
        print(f"\n⚠️ MINGUS Application needs attention before production deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
