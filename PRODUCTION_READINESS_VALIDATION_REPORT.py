#!/usr/bin/env python3
"""
MINGUS Application - Production Readiness Validation Report
Master orchestrator for comprehensive production validation
"""

import asyncio
import aiohttp
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Validation result data structure"""
    validation_type: str
    status: str  # 'passed', 'failed', 'warning'
    score: float
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

class ProductionReadinessValidator:
    """Master production readiness validator for MINGUS application"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive production readiness validation"""
        print("🚀 MINGUS Application - Production Readiness Validation")
        print("=" * 70)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 1. System Health Check
        await self.run_system_health_check()
        
        # 2. Security Validation
        await self.run_security_validation()
        
        # 3. User Profile Validation
        await self.run_user_profile_validation()
        
        # 4. Financial Features Validation
        await self.run_financial_features_validation()
        
        # 5. Performance Validation
        await self.run_performance_validation()
        
        # 6. Integration Validation
        await self.run_integration_validation()
        
        # 7. Production Configuration Validation
        await self.run_production_config_validation()
        
        # Generate comprehensive report
        return self.generate_comprehensive_report()
    
    async def run_system_health_check(self):
        """Run system health check validation"""
        print("\n🔍 Running System Health Check...")
        
        try:
            # Import and run system health check
            from COMPREHENSIVE_SYSTEM_HEALTH_CHECK import SystemHealthChecker
            
            health_checker = SystemHealthChecker(self.base_url)
            health_report = await health_checker.run_comprehensive_health_check()
            
            # Extract key metrics
            health_score = health_report['summary']['health_score']
            critical_issues = health_report['summary']['critical_checks']
            warning_issues = health_report['summary']['warning_checks']
            
            # Determine status
            if critical_issues == 0 and warning_issues <= 2:
                status = "passed"
            elif critical_issues <= 1 and warning_issues <= 5:
                status = "warning"
            else:
                status = "failed"
            
            self.results.append(ValidationResult(
                validation_type="System Health Check",
                status=status,
                score=health_score,
                details={
                    "total_checks": health_report['summary']['total_checks'],
                    "healthy_checks": health_report['summary']['healthy_checks'],
                    "warning_checks": warning_issues,
                    "critical_checks": critical_issues,
                    "avg_response_time_ms": health_report['summary']['avg_response_time_ms']
                },
                timestamp=datetime.now(),
                recommendations=health_report['recommendations']
            ))
            
            print(f"  ✅ System Health Check: {health_score}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ System Health Check failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="System Health Check",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix system health check execution"]
            ))
    
    async def run_security_validation(self):
        """Run security validation"""
        print("\n🔒 Running Security Validation...")
        
        try:
            # Import and run security validation
            from SECURITY_VALIDATION_TESTER import SecurityValidator
            
            security_validator = SecurityValidator(self.base_url)
            security_report = await security_validator.run_security_validation()
            
            # Extract key metrics
            security_score = security_report['summary']['security_score']
            failed_tests = security_report['summary']['failed_tests']
            warning_tests = security_report['summary']['warning_tests']
            
            # Determine status
            if failed_tests == 0 and warning_tests <= 2:
                status = "passed"
            elif failed_tests <= 2:
                status = "warning"
            else:
                status = "failed"
            
            self.results.append(ValidationResult(
                validation_type="Security Validation",
                status=status,
                score=security_score,
                details={
                    "total_tests": security_report['summary']['total_tests'],
                    "passed_tests": security_report['summary']['passed_tests'],
                    "failed_tests": failed_tests,
                    "warning_tests": warning_tests
                },
                timestamp=datetime.now(),
                recommendations=security_report['recommendations']
            ))
            
            print(f"  ✅ Security Validation: {security_score}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ Security Validation failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="Security Validation",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix security validation execution"]
            ))
    
    async def run_user_profile_validation(self):
        """Run user profile validation"""
        print("\n👤 Running User Profile Validation...")
        
        try:
            # Import and run user profile validation
            from USER_PROFILE_VALIDATION_TESTER import UserProfileValidator
            
            profile_validator = UserProfileValidator(self.base_url)
            profile_report = await profile_validator.run_profile_validation()
            
            # Extract key metrics
            profile_score = profile_report['summary']['profile_score']
            failed_tests = profile_report['summary']['failed_tests']
            warning_tests = profile_report['summary']['warning_tests']
            
            # Determine status
            if failed_tests == 0 and warning_tests <= 1:
                status = "passed"
            elif failed_tests <= 2:
                status = "warning"
            else:
                status = "failed"
            
            self.results.append(ValidationResult(
                validation_type="User Profile Validation",
                status=status,
                score=profile_score,
                details={
                    "total_tests": profile_report['summary']['total_tests'],
                    "passed_tests": profile_report['summary']['passed_tests'],
                    "failed_tests": failed_tests,
                    "warning_tests": warning_tests
                },
                timestamp=datetime.now(),
                recommendations=profile_report['recommendations']
            ))
            
            print(f"  ✅ User Profile Validation: {profile_score}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ User Profile Validation failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="User Profile Validation",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix user profile validation execution"]
            ))
    
    async def run_financial_features_validation(self):
        """Run financial features validation"""
        print("\n💰 Running Financial Features Validation...")
        
        try:
            # Import and run financial features validation
            from FINANCIAL_FEATURES_TESTER import FinancialFeaturesValidator
            
            financial_validator = FinancialFeaturesValidator(self.base_url)
            financial_report = await financial_validator.run_financial_validation()
            
            # Extract key metrics
            financial_score = financial_report['summary']['financial_score']
            failed_tests = financial_report['summary']['failed_tests']
            warning_tests = financial_report['summary']['warning_tests']
            
            # Determine status
            if failed_tests == 0 and warning_tests <= 1:
                status = "passed"
            elif failed_tests <= 2:
                status = "warning"
            else:
                status = "failed"
            
            self.results.append(ValidationResult(
                validation_type="Financial Features Validation",
                status=status,
                score=financial_score,
                details={
                    "total_tests": financial_report['summary']['total_tests'],
                    "passed_tests": financial_report['summary']['passed_tests'],
                    "failed_tests": failed_tests,
                    "warning_tests": warning_tests
                },
                timestamp=datetime.now(),
                recommendations=financial_report['recommendations']
            ))
            
            print(f"  ✅ Financial Features Validation: {financial_score}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ Financial Features Validation failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="Financial Features Validation",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix financial features validation execution"]
            ))
    
    async def run_performance_validation(self):
        """Run performance validation"""
        print("\n📈 Running Performance Validation...")
        
        try:
            # Test key performance metrics
            performance_tests = [
                ("/", "Home page load time"),
                ("/api/health", "Health endpoint response time"),
                ("/api/auth/check-auth", "Auth check response time"),
                ("/api/user/profile", "Profile endpoint response time"),
                ("/api/financial/dashboard", "Financial dashboard response time")
            ]
            
            response_times = []
            successful_requests = 0
            
            async with aiohttp.ClientSession() as session:
                for endpoint, description in performance_tests:
                    try:
                        start_time = time.time()
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            response_time = (time.time() - start_time) * 1000
                            response_times.append(response_time)
                            
                            if response.status < 400:
                                successful_requests += 1
                                print(f"    ✅ {description}: {response_time:.1f}ms")
                            else:
                                print(f"    ⚠️ {description}: {response_time:.1f}ms (Status: {response.status})")
                    except Exception as e:
                        print(f"    ❌ {description}: ERROR - {str(e)}")
            
            # Calculate performance metrics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            success_rate = (successful_requests / len(performance_tests)) * 100
            
            # Performance thresholds
            target_response_time = 1000  # 1 second
            target_success_rate = 95  # 95%
            
            # Determine status
            if avg_response_time <= target_response_time and success_rate >= target_success_rate:
                status = "passed"
            elif avg_response_time <= target_response_time * 2 and success_rate >= target_success_rate * 0.9:
                status = "warning"
            else:
                status = "failed"
            
            performance_score = min(100, (target_response_time / avg_response_time * 100) if avg_response_time > 0 else 0)
            
            self.results.append(ValidationResult(
                validation_type="Performance Validation",
                status=status,
                score=performance_score,
                details={
                    "avg_response_time_ms": round(avg_response_time, 1),
                    "max_response_time_ms": round(max_response_time, 1),
                    "success_rate": round(success_rate, 1),
                    "target_response_time_ms": target_response_time,
                    "target_success_rate": target_success_rate
                },
                timestamp=datetime.now(),
                recommendations=self.generate_performance_recommendations(avg_response_time, success_rate)
            ))
            
            print(f"  ✅ Performance Validation: {performance_score:.1f}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ Performance Validation failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="Performance Validation",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix performance validation execution"]
            ))
    
    async def run_integration_validation(self):
        """Run integration validation"""
        print("\n🔗 Running Integration Validation...")
        
        try:
            # Test external service integrations
            integration_tests = [
                ("/api/integrations/plaid/health", "Plaid Integration"),
                ("/api/integrations/stripe/health", "Stripe Integration"),
                ("/api/integrations/twilio/health", "Twilio Integration"),
                ("/api/integrations/resend/health", "Resend Integration"),
                ("/api/integrations/openai/health", "OpenAI Integration")
            ]
            
            working_integrations = 0
            total_integrations = len(integration_tests)
            
            async with aiohttp.ClientSession() as session:
                for endpoint, service_name in integration_tests:
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            if response.status == 200:
                                working_integrations += 1
                                print(f"    ✅ {service_name}: Working")
                            else:
                                print(f"    ⚠️ {service_name}: Status {response.status}")
                    except Exception as e:
                        print(f"    ❌ {service_name}: Not available - {str(e)}")
            
            # Calculate integration score
            integration_score = (working_integrations / total_integrations) * 100
            
            # Determine status
            if integration_score >= 80:
                status = "passed"
            elif integration_score >= 60:
                status = "warning"
            else:
                status = "failed"
            
            self.results.append(ValidationResult(
                validation_type="Integration Validation",
                status=status,
                score=integration_score,
                details={
                    "working_integrations": working_integrations,
                    "total_integrations": total_integrations,
                    "integration_score": round(integration_score, 1)
                },
                timestamp=datetime.now(),
                recommendations=self.generate_integration_recommendations(working_integrations, total_integrations)
            ))
            
            print(f"  ✅ Integration Validation: {integration_score:.1f}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ Integration Validation failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="Integration Validation",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix integration validation execution"]
            ))
    
    async def run_production_config_validation(self):
        """Run production configuration validation"""
        print("\n⚙️ Running Production Configuration Validation...")
        
        try:
            # Check production configuration files
            config_files = [
                "PRODUCTION_ENVIRONMENT_VARIABLES.md",
                "PRODUCTION_DATABASE_MIGRATIONS.sql",
                "DIGITALOCEAN_PRODUCTION_DEPLOYMENT_CHECKLIST.md",
                "PRODUCTION_SECURITY_VERIFICATION.md"
            ]
            
            existing_files = 0
            for config_file in config_files:
                if os.path.exists(config_file):
                    existing_files += 1
                    print(f"    ✅ {config_file}: Found")
                else:
                    print(f"    ❌ {config_file}: Missing")
            
            # Check environment variables
            required_env_vars = [
                "SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL", "REDIS_URL",
                "STRIPE_SECRET_KEY", "RESEND_API_KEY", "TWILIO_AUTH_TOKEN"
            ]
            
            env_vars_set = 0
            for env_var in required_env_vars:
                if os.getenv(env_var):
                    env_vars_set += 1
                    print(f"    ✅ {env_var}: Set")
                else:
                    print(f"    ⚠️ {env_var}: Not set")
            
            # Calculate configuration score
            config_score = ((existing_files / len(config_files)) * 50) + ((env_vars_set / len(required_env_vars)) * 50)
            
            # Determine status
            if config_score >= 90:
                status = "passed"
            elif config_score >= 70:
                status = "warning"
            else:
                status = "failed"
            
            self.results.append(ValidationResult(
                validation_type="Production Configuration Validation",
                status=status,
                score=config_score,
                details={
                    "config_files_found": existing_files,
                    "total_config_files": len(config_files),
                    "env_vars_set": env_vars_set,
                    "total_env_vars": len(required_env_vars)
                },
                timestamp=datetime.now(),
                recommendations=self.generate_config_recommendations(existing_files, len(config_files), env_vars_set, len(required_env_vars))
            ))
            
            print(f"  ✅ Production Configuration Validation: {config_score:.1f}% (Status: {status})")
            
        except Exception as e:
            print(f"  ❌ Production Configuration Validation failed: {str(e)}")
            self.results.append(ValidationResult(
                validation_type="Production Configuration Validation",
                status="failed",
                score=0.0,
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Fix production configuration validation execution"]
            ))
    
    def generate_performance_recommendations(self, avg_response_time: float, success_rate: float) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if avg_response_time > 1000:
            recommendations.append("Optimize slow endpoints for better response times")
        
        if success_rate < 95:
            recommendations.append("Improve endpoint reliability and error handling")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable limits")
        
        return recommendations
    
    def generate_integration_recommendations(self, working_integrations: int, total_integrations: int) -> List[str]:
        """Generate integration recommendations"""
        recommendations = []
        
        if working_integrations < total_integrations:
            recommendations.append("Configure missing external service integrations")
        
        if not recommendations:
            recommendations.append("All integrations are working correctly")
        
        return recommendations
    
    def generate_config_recommendations(self, config_files: int, total_config_files: int, env_vars: int, total_env_vars: int) -> List[str]:
        """Generate configuration recommendations"""
        recommendations = []
        
        if config_files < total_config_files:
            recommendations.append("Create missing production configuration files")
        
        if env_vars < total_env_vars:
            recommendations.append("Set missing environment variables for production")
        
        if not recommendations:
            recommendations.append("Production configuration is complete")
        
        return recommendations
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report"""
        total_time = time.time() - self.start_time
        
        # Calculate overall metrics
        total_validations = len(self.results)
        passed_validations = len([r for r in self.results if r.status == "passed"])
        warning_validations = len([r for r in self.results if r.status == "warning"])
        failed_validations = len([r for r in self.results if r.status == "failed"])
        
        # Calculate overall score
        overall_score = sum(r.score for r in self.results) / total_validations if total_validations > 0 else 0
        
        # Determine overall status
        if failed_validations == 0 and warning_validations <= 2:
            overall_status = "READY FOR PRODUCTION"
        elif failed_validations <= 2:
            overall_status = "NEEDS MINOR FIXES"
        else:
            overall_status = "NOT READY FOR PRODUCTION"
        
        # Generate recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates and prioritize
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        return {
            "summary": {
                "overall_status": overall_status,
                "overall_score": round(overall_score, 1),
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "warning_validations": warning_validations,
                "failed_validations": failed_validations,
                "execution_time_seconds": round(total_time, 1)
            },
            "validation_results": [
                {
                    "validation_type": r.validation_type,
                    "status": r.status,
                    "score": round(r.score, 1),
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat(),
                    "recommendations": r.recommendations
                }
                for r in self.results
            ],
            "recommendations": unique_recommendations,
            "production_readiness": {
                "readiness_status": overall_status,
                "readiness_score": round(overall_score, 1),
                "blocking_issues": failed_validations,
                "critical_areas": [r.validation_type for r in self.results if r.status == "failed"],
                "next_steps": self.generate_next_steps()
            }
        }
    
    def generate_next_steps(self) -> List[str]:
        """Generate next steps based on validation results"""
        next_steps = []
        
        failed_validations = [r for r in self.results if r.status == "failed"]
        if failed_validations:
            next_steps.append("🚨 CRITICAL: Address all failed validations before production deployment")
            for validation in failed_validations:
                next_steps.append(f"   - Fix {validation.validation_type}")
        
        warning_validations = [r for r in self.results if r.status == "warning"]
        if warning_validations:
            next_steps.append("⚠️ WARNING: Review and address warning validations")
            for validation in warning_validations:
                next_steps.append(f"   - Review {validation.validation_type}")
        
        if not failed_validations and not warning_validations:
            next_steps.append("✅ All validations passed - proceed with production deployment")
            next_steps.append("📋 Follow the DigitalOcean deployment checklist")
            next_steps.append("🔒 Ensure all security measures are active")
            next_steps.append("📊 Monitor application performance after deployment")
        
        return next_steps

async def main():
    """Main function to run comprehensive production readiness validation"""
    print("🚀 MINGUS Application - Production Readiness Validation")
    print("=" * 70)
    
    # Initialize production readiness validator
    validator = ProductionReadinessValidator()
    
    # Run comprehensive validation
    report = await validator.run_comprehensive_validation()
    
    # Print comprehensive summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE PRODUCTION READINESS SUMMARY")
    print("=" * 70)
    print(f"Overall Status: {report['summary']['overall_status']}")
    print(f"Overall Score: {report['summary']['overall_score']}%")
    print(f"Total Validations: {report['summary']['total_validations']}")
    print(f"Passed: {report['summary']['passed_validations']}")
    print(f"Warnings: {report['summary']['warning_validations']}")
    print(f"Failed: {report['summary']['failed_validations']}")
    print(f"Execution Time: {report['summary']['execution_time_seconds']}s")
    
    print("\n📋 VALIDATION RESULTS")
    print("=" * 70)
    for result in report['validation_results']:
        status_icon = "✅" if result['status'] == "passed" else "⚠️" if result['status'] == "warning" else "❌"
        print(f"{status_icon} {result['validation_type']}: {result['score']}% ({result['status']})")
    
    print("\n🚀 PRODUCTION READINESS")
    print("=" * 70)
    readiness = report['production_readiness']
    print(f"Readiness Status: {readiness['readiness_status']}")
    print(f"Readiness Score: {readiness['readiness_score']}%")
    print(f"Blocking Issues: {readiness['blocking_issues']}")
    
    if readiness['critical_areas']:
        print(f"Critical Areas: {', '.join(readiness['critical_areas'])}")
    
    print("\n📋 NEXT STEPS")
    print("=" * 70)
    for step in readiness['next_steps']:
        print(step)
    
    print("\n📋 ALL RECOMMENDATIONS")
    print("=" * 70)
    for recommendation in report['recommendations']:
        print(recommendation)
    
    # Save comprehensive report
    report_file = f"production_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Comprehensive report saved to: {report_file}")
    
    # Return exit code based on readiness
    if readiness['readiness_status'] == "READY FOR PRODUCTION":
        print("\n🎉 MINGUS Application is READY for production deployment to DigitalOcean!")
        return 0
    else:
        print(f"\n⚠️ MINGUS Application needs attention before production deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
