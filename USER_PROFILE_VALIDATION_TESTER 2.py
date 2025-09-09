#!/usr/bin/env python3
"""
MINGUS Application - User Profile Validation Tester
Comprehensive testing of user profile functionality
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
class ProfileTestResult:
    """User profile test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

class UserProfileValidator:
    """Comprehensive user profile validation for MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[ProfileTestResult] = []
        self.auth_token = None
        self.test_user_id = None
        
    async def run_profile_validation(self) -> Dict[str, Any]:
        """Run comprehensive user profile validation"""
        print("👤 MINGUS Application - User Profile Validation")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Setup test user
        await self.setup_test_user()
        
        # 2. Test profile creation and retrieval
        await self.test_profile_creation_retrieval()
        
        # 3. Test profile field validation
        await self.test_profile_field_validation()
        
        # 4. Test profile completion calculation
        await self.test_profile_completion_calculation()
        
        # 5. Test onboarding progress tracking
        await self.test_onboarding_progress_tracking()
        
        # 6. Test profile update functionality
        await self.test_profile_update_functionality()
        
        # 7. Test profile data persistence
        await self.test_profile_data_persistence()
        
        # 8. Test profile security and authorization
        await self.test_profile_security_authorization()
        
        return self.generate_profile_report()
    
    async def setup_test_user(self):
        """Setup test user for profile testing"""
        print("\n🔧 Setting up test user...")
        
        try:
            # Register test user
            test_email = f"profiletest{int(time.time())}@mingus.test"
            test_password = "ProfileTest123!"
            
            async with aiohttp.ClientSession() as session:
                # Register user
                async with session.post(f"{self.base_url}/api/auth/register", json={
                    "email": test_email,
                    "password": test_password,
                    "first_name": "Profile",
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
                        self.test_user_id = login_response.get("user_id")
                        print(f"  ✅ Test user authenticated")
                    else:
                        print(f"  ❌ Test user authentication failed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Test user setup failed: {str(e)}")
    
    async def test_profile_creation_retrieval(self):
        """Test profile creation and retrieval functionality"""
        print("\n📝 Testing Profile Creation and Retrieval...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping profile tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test initial profile retrieval
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/user/profile", headers=headers) as response:
                    if response.status == 200:
                        profile_data = await response.json()
                        
                        self.results.append(ProfileTestResult(
                            test_name="Profile Retrieval",
                            status="passed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status,
                                "profile_fields": len(profile_data),
                                "has_required_fields": all(field in profile_data for field in ["id", "email", "first_name", "last_name"])
                            },
                            timestamp=datetime.now(),
                            recommendations=["Profile retrieval is working correctly"]
                        ))
                        print(f"  ✅ Profile retrieval successful")
                    else:
                        self.results.append(ProfileTestResult(
                            test_name="Profile Retrieval",
                            status="failed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix profile retrieval endpoint"]
                        ))
                        print(f"  ❌ Profile retrieval failed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Profile Creation/Retrieval Test: ERROR - {str(e)}")
    
    async def test_profile_field_validation(self):
        """Test profile field validation"""
        print("\n✅ Testing Profile Field Validation...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping validation tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test invalid field values
            invalid_fields = [
                {"phone": "invalid-phone"},  # Invalid phone format
                {"zip_code": "invalid-zip"},  # Invalid zip code
                {"age_range": "invalid-age"},  # Invalid age range
                {"gender": "invalid-gender"},  # Invalid gender
                {"marital_status": "invalid-status"},  # Invalid marital status
                {"monthly_income": -1000},  # Negative income
                {"dependents_count": -1},  # Negative dependents
                {"household_size": 0},  # Zero household size
            ]
            
            async with aiohttp.ClientSession() as session:
                for field_data in invalid_fields:
                    async with session.patch(f"{self.base_url}/api/user/profile", 
                                           json=field_data, headers=headers) as response:
                        if response.status in [400, 422]:
                            self.results.append(ProfileTestResult(
                                test_name="Profile Field Validation",
                                status="passed",
                                details={
                                    "field": list(field_data.keys())[0],
                                    "value": list(field_data.values())[0],
                                    "status_code": response.status
                                },
                                timestamp=datetime.now(),
                                recommendations=["Field validation is working correctly"]
                            ))
                            print(f"  ✅ Invalid field rejected: {list(field_data.keys())[0]}")
                        else:
                            self.results.append(ProfileTestResult(
                                test_name="Profile Field Validation",
                                status="failed",
                                details={
                                    "field": list(field_data.keys())[0],
                                    "value": list(field_data.values())[0],
                                    "status_code": response.status
                                },
                                timestamp=datetime.now(),
                                recommendations=["Implement proper field validation"]
                            ))
                            print(f"  ❌ Invalid field accepted: {list(field_data.keys())[0]}")
                            
        except Exception as e:
            print(f"  ❌ Profile Field Validation Test: ERROR - {str(e)}")
    
    async def test_profile_completion_calculation(self):
        """Test profile completion percentage calculation"""
        print("\n📊 Testing Profile Completion Calculation...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping completion tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test profile completion calculation
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/user/profile", headers=headers) as response:
                    if response.status == 200:
                        profile_data = await response.json()
                        
                        # Check if completion percentage is calculated
                        if "profile_completion_percentage" in profile_data:
                            completion_percentage = profile_data["profile_completion_percentage"]
                            
                            if isinstance(completion_percentage, (int, float)) and 0 <= completion_percentage <= 100:
                                self.results.append(ProfileTestResult(
                                    test_name="Profile Completion Calculation",
                                    status="passed",
                                    details={
                                        "completion_percentage": completion_percentage,
                                        "is_valid_range": True
                                    },
                                    timestamp=datetime.now(),
                                    recommendations=["Profile completion calculation is working correctly"]
                                ))
                                print(f"  ✅ Profile completion: {completion_percentage}%")
                            else:
                                self.results.append(ProfileTestResult(
                                    test_name="Profile Completion Calculation",
                                    status="failed",
                                    details={
                                        "completion_percentage": completion_percentage,
                                        "is_valid_range": False
                                    },
                                    timestamp=datetime.now(),
                                    recommendations=["Fix profile completion calculation logic"]
                                ))
                                print(f"  ❌ Invalid completion percentage: {completion_percentage}")
                        else:
                            self.results.append(ProfileTestResult(
                                test_name="Profile Completion Calculation",
                                status="failed",
                                details={
                                    "completion_percentage": "missing"
                                },
                                timestamp=datetime.now(),
                                recommendations=["Implement profile completion calculation"]
                            ))
                            print(f"  ❌ Profile completion percentage not found")
                            
        except Exception as e:
            print(f"  ❌ Profile Completion Calculation Test: ERROR - {str(e)}")
    
    async def test_onboarding_progress_tracking(self):
        """Test onboarding progress tracking"""
        print("\n🎯 Testing Onboarding Progress Tracking...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping onboarding tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test onboarding progress retrieval
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/user/onboarding-progress", 
                                     headers=headers) as response:
                    if response.status == 200:
                        progress_data = await response.json()
                        
                        # Check if progress tracking is working
                        if "current_step" in progress_data and "total_steps" in progress_data:
                            current_step = progress_data["current_step"]
                            total_steps = progress_data["total_steps"]
                            
                            if isinstance(current_step, int) and isinstance(total_steps, int) and 0 <= current_step <= total_steps:
                                self.results.append(ProfileTestResult(
                                    test_name="Onboarding Progress Tracking",
                                    status="passed",
                                    details={
                                        "current_step": current_step,
                                        "total_steps": total_steps,
                                        "progress_percentage": (current_step / total_steps * 100) if total_steps > 0 else 0
                                    },
                                    timestamp=datetime.now(),
                                    recommendations=["Onboarding progress tracking is working correctly"]
                                ))
                                print(f"  ✅ Onboarding progress: {current_step}/{total_steps}")
                            else:
                                self.results.append(ProfileTestResult(
                                    test_name="Onboarding Progress Tracking",
                                    status="failed",
                                    details={
                                        "current_step": current_step,
                                        "total_steps": total_steps,
                                        "is_valid_range": False
                                    },
                                    timestamp=datetime.now(),
                                    recommendations=["Fix onboarding progress calculation logic"]
                                ))
                                print(f"  ❌ Invalid onboarding progress: {current_step}/{total_steps}")
                        else:
                            self.results.append(ProfileTestResult(
                                test_name="Onboarding Progress Tracking",
                                status="failed",
                                details={
                                    "progress_data": progress_data
                                },
                                timestamp=datetime.now(),
                                recommendations=["Implement proper onboarding progress tracking"]
                            ))
                            print(f"  ❌ Onboarding progress data incomplete")
                    else:
                        self.results.append(ProfileTestResult(
                            test_name="Onboarding Progress Tracking",
                            status="failed",
                            details={
                                "endpoint": "/api/user/onboarding-progress",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix onboarding progress endpoint"]
                        ))
                        print(f"  ❌ Onboarding progress endpoint failed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Onboarding Progress Tracking Test: ERROR - {str(e)}")
    
    async def test_profile_update_functionality(self):
        """Test profile update functionality"""
        print("\n🔄 Testing Profile Update Functionality...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping update tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test profile update with valid data
            valid_profile_update = {
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
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(f"{self.base_url}/api/user/profile", 
                                       json=valid_profile_update, headers=headers) as response:
                    if response.status == 200:
                        updated_profile = await response.json()
                        
                        # Verify fields were updated
                        updated_fields = 0
                        for field, value in valid_profile_update.items():
                            if field in updated_profile and updated_profile[field] == value:
                                updated_fields += 1
                        
                        if updated_fields >= len(valid_profile_update) * 0.8:  # 80% of fields updated
                            self.results.append(ProfileTestResult(
                                test_name="Profile Update Functionality",
                                status="passed",
                                details={
                                    "fields_updated": updated_fields,
                                    "total_fields": len(valid_profile_update),
                                    "update_success_rate": (updated_fields / len(valid_profile_update) * 100)
                                },
                                timestamp=datetime.now(),
                                recommendations=["Profile update functionality is working correctly"]
                            ))
                            print(f"  ✅ Profile update successful: {updated_fields}/{len(valid_profile_update)} fields")
                        else:
                            self.results.append(ProfileTestResult(
                                test_name="Profile Update Functionality",
                                status="failed",
                                details={
                                    "fields_updated": updated_fields,
                                    "total_fields": len(valid_profile_update),
                                    "update_success_rate": (updated_fields / len(valid_profile_update) * 100)
                                },
                                timestamp=datetime.now(),
                                recommendations=["Fix profile update functionality"]
                            ))
                            print(f"  ❌ Profile update incomplete: {updated_fields}/{len(valid_profile_update)} fields")
                    else:
                        self.results.append(ProfileTestResult(
                            test_name="Profile Update Functionality",
                            status="failed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status
                            },
                            timestamp=datetime.now(),
                            recommendations=["Fix profile update endpoint"]
                        ))
                        print(f"  ❌ Profile update failed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Profile Update Functionality Test: ERROR - {str(e)}")
    
    async def test_profile_data_persistence(self):
        """Test profile data persistence"""
        print("\n💾 Testing Profile Data Persistence...")
        
        if not self.auth_token:
            print("  ⚠️ Skipping persistence tests - No authentication token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test data persistence by updating and then retrieving
            test_data = {
                "city": f"PersistenceTest{int(time.time())}",
                "occupation": "Data Persistence Tester"
            }
            
            async with aiohttp.ClientSession() as session:
                # Update profile
                async with session.patch(f"{self.base_url}/api/user/profile", 
                                       json=test_data, headers=headers) as response:
                    if response.status == 200:
                        # Retrieve profile to verify persistence
                        async with session.get(f"{self.base_url}/api/user/profile", 
                                             headers=headers) as response:
                            if response.status == 200:
                                profile_data = await response.json()
                                
                                # Check if data was persisted
                                data_persisted = all(
                                    field in profile_data and profile_data[field] == value
                                    for field, value in test_data.items()
                                )
                                
                                if data_persisted:
                                    self.results.append(ProfileTestResult(
                                        test_name="Profile Data Persistence",
                                        status="passed",
                                        details={
                                            "test_data": test_data,
                                            "data_persisted": True
                                        },
                                        timestamp=datetime.now(),
                                        recommendations=["Profile data persistence is working correctly"]
                                    ))
                                    print(f"  ✅ Profile data persisted successfully")
                                else:
                                    self.results.append(ProfileTestResult(
                                        test_name="Profile Data Persistence",
                                        status="failed",
                                        details={
                                            "test_data": test_data,
                                            "data_persisted": False
                                        },
                                        timestamp=datetime.now(),
                                        recommendations=["Fix profile data persistence"]
                                    ))
                                    print(f"  ❌ Profile data not persisted")
                            else:
                                print(f"  ❌ Profile retrieval failed: {response.status}")
                    else:
                        print(f"  ❌ Profile update failed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Profile Data Persistence Test: ERROR - {str(e)}")
    
    async def test_profile_security_authorization(self):
        """Test profile security and authorization"""
        print("\n🔒 Testing Profile Security and Authorization...")
        
        try:
            # Test unauthorized access to profile
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/user/profile") as response:
                    if response.status == 401:
                        self.results.append(ProfileTestResult(
                            test_name="Profile Authorization",
                            status="passed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status,
                                "unauthorized_access_blocked": True
                            },
                            timestamp=datetime.now(),
                            recommendations=["Profile authorization is working correctly"]
                        ))
                        print(f"  ✅ Unauthorized access blocked")
                    else:
                        self.results.append(ProfileTestResult(
                            test_name="Profile Authorization",
                            status="failed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status,
                                "unauthorized_access_blocked": False
                            },
                            timestamp=datetime.now(),
                            recommendations=["Implement proper profile authorization"]
                        ))
                        print(f"  ❌ Unauthorized access allowed: {response.status}")
                
                # Test profile update without authorization
                async with session.patch(f"{self.base_url}/api/user/profile", json={
                    "city": "Unauthorized Update"
                }) as response:
                    if response.status == 401:
                        self.results.append(ProfileTestResult(
                            test_name="Profile Update Authorization",
                            status="passed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status,
                                "unauthorized_update_blocked": True
                            },
                            timestamp=datetime.now(),
                            recommendations=["Profile update authorization is working correctly"]
                        ))
                        print(f"  ✅ Unauthorized update blocked")
                    else:
                        self.results.append(ProfileTestResult(
                            test_name="Profile Update Authorization",
                            status="failed",
                            details={
                                "endpoint": "/api/user/profile",
                                "status_code": response.status,
                                "unauthorized_update_blocked": False
                            },
                            timestamp=datetime.now(),
                            recommendations=["Implement proper profile update authorization"]
                        ))
                        print(f"  ❌ Unauthorized update allowed: {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Profile Security Authorization Test: ERROR - {str(e)}")
    
    def generate_profile_report(self) -> Dict[str, Any]:
        """Generate comprehensive profile validation report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        profile_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine profile status
        if failed_tests == 0 and warning_tests <= 1:
            profile_status = "FUNCTIONAL"
        elif failed_tests <= 2:
            profile_status = "NEEDS ATTENTION"
        else:
            profile_status = "BROKEN"
        
        return {
            "summary": {
                "profile_status": profile_status,
                "profile_score": round(profile_score, 1),
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
            "recommendations": self.generate_profile_recommendations(),
            "production_readiness": self.assess_profile_readiness()
        }
    
    def generate_profile_recommendations(self) -> List[str]:
        """Generate profile recommendations"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.status == "failed"]
        if failed_tests:
            recommendations.append("🚨 CRITICAL: Address failed profile tests before production")
            for test in failed_tests:
                recommendations.append(f"   - {test.test_name}: {test.recommendations[0]}")
        
        warning_tests = [r for r in self.results if r.status == "warning"]
        if warning_tests:
            recommendations.append("⚠️ WARNING: Review profile warnings")
            for test in warning_tests:
                recommendations.append(f"   - {test.test_name}: {test.recommendations[0]}")
        
        if not failed_tests and not warning_tests:
            recommendations.append("✅ All profile tests passed - ready for production")
        
        return recommendations
    
    def assess_profile_readiness(self) -> Dict[str, Any]:
        """Assess profile readiness for production"""
        failed_tests = len([r for r in self.results if r.status == "failed"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        # Profile readiness criteria
        readiness_criteria = {
            "profile_creation_working": any("Profile Creation" in r.test_name and r.status == "passed" for r in self.results),
            "field_validation_working": any("Field Validation" in r.test_name and r.status == "passed" for r in self.results),
            "completion_calculation_working": any("Completion Calculation" in r.test_name and r.status == "passed" for r in self.results),
            "onboarding_progress_working": any("Onboarding Progress" in r.test_name and r.status == "passed" for r in self.results),
            "update_functionality_working": any("Update Functionality" in r.test_name and r.status == "passed" for r in self.results),
            "data_persistence_working": any("Data Persistence" in r.test_name and r.status == "passed" for r in self.results),
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
                "Address all failed profile tests",
                "Ensure all profile fields work correctly",
                "Verify profile data persistence",
                "Test profile security and authorization"
            ]
        }

async def main():
    """Main function to run profile validation"""
    print("👤 MINGUS Application - User Profile Validation")
    print("=" * 60)
    
    # Initialize profile validator
    profile_validator = UserProfileValidator()
    
    # Run profile validation
    report = await profile_validator.run_profile_validation()
    
    # Print summary
    print("\n" + "=" * 60)
    print("👤 PROFILE VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Profile Status: {report['summary']['profile_status']}")
    print(f"Profile Score: {report['summary']['profile_score']}%")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Warnings: {report['summary']['warning_tests']}")
    
    print("\n🚀 PROFILE READINESS")
    print("=" * 60)
    readiness = report['production_readiness']
    print(f"Readiness Status: {readiness['readiness_status']}")
    print(f"Readiness Score: {readiness['readiness_score']}%")
    print(f"Blocking Issues: {readiness['blocking_issues']}")
    
    print("\n📋 PROFILE RECOMMENDATIONS")
    print("=" * 60)
    for recommendation in report['recommendations']:
        print(recommendation)
    
    # Save detailed report
    report_file = f"profile_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on profile readiness
    if readiness['readiness_status'] == "READY":
        print("\n🎉 MINGUS User Profile system is READY for production deployment!")
        return 0
    else:
        print(f"\n⚠️ MINGUS User Profile system needs attention before production deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
