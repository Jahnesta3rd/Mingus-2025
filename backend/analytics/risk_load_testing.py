#!/usr/bin/env python3
"""
Risk-Based Load Testing System for Mingus Application
====================================================

Comprehensive load testing system specifically designed for risk-triggered workflows
and emergency response scenarios. Tests system performance under various risk-based
load conditions to ensure optimal career protection response times.

Features:
- High-risk user surge simulation
- Concurrent emergency unlock testing
- Risk assessment scalability validation
- Notification system capacity testing
- Performance degradation analysis
- System stability under risk load

Author: Mingus Risk Performance Team
Date: January 2025
"""

import asyncio
import aiohttp
import time
import json
import logging
import statistics
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures
from threading import Thread, Lock
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadTestScenario(Enum):
    """Load test scenario types"""
    HIGH_RISK_SURGE = "high_risk_surge"
    CONCURRENT_EMERGENCY_UNLOCKS = "concurrent_emergency_unlocks"
    RISK_ASSESSMENT_SCALABILITY = "risk_assessment_scalability"
    NOTIFICATION_CAPACITY = "notification_capacity"
    MIXED_RISK_LOAD = "mixed_risk_load"

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class LoadTestResult:
    """Load test result data structure"""
    scenario: str
    test_duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    throughput: float  # requests per second
    concurrent_users: int
    peak_cpu_usage: float
    peak_memory_usage: float
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class RiskUserProfile:
    """Risk user profile for load testing"""
    user_id: str
    risk_level: str
    industry: str
    automation_level: str
    company_size: str
    tenure: str
    performance_rating: str
    company_health: str
    recent_layoffs: str
    skills_relevance: str
    ai_tools_usage: str
    skills: List[str]

class RiskLoadTester:
    """Risk-based load testing system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'http://localhost:5000')
        self.max_concurrent_users = config.get('max_concurrent_users', 1000)
        self.test_timeout = config.get('test_timeout', 300)  # 5 minutes
        self.results = []
        self.test_lock = Lock()
        
        # Performance thresholds
        self.thresholds = {
            'max_response_time': 5.0,  # 5 seconds
            'max_error_rate': 5.0,     # 5%
            'min_throughput': 10.0,    # 10 requests/second
            'max_cpu_usage': 90.0,     # 90%
            'max_memory_usage': 95.0   # 95%
        }
        
        logger.info("RiskLoadTester initialized successfully")
    
    def generate_risk_user_profiles(self, count: int) -> List[RiskUserProfile]:
        """Generate realistic risk user profiles for testing"""
        profiles = []
        
        # Risk level distribution
        risk_distribution = {
            RiskLevel.LOW.value: 0.3,
            RiskLevel.MEDIUM.value: 0.4,
            RiskLevel.HIGH.value: 0.2,
            RiskLevel.CRITICAL.value: 0.1
        }
        
        # Industry distribution
        industries = [
            'Manufacturing', 'Retail/E-commerce', 'Finance/Banking',
            'Technology', 'Healthcare', 'Education', 'Government',
            'Transportation', 'Energy', 'Construction'
        ]
        
        # Automation levels
        automation_levels = [
            'Very Little', 'Some', 'Moderate', 'A Lot', 'Almost Everything'
        ]
        
        # Company sizes
        company_sizes = [
            '1-10 employees', '11-50 employees', '51-200 employees',
            '201-1000 employees', '1000+ employees'
        ]
        
        # Tenure options
        tenures = [
            'Less than 6 months', '6 months - 1 year', '1-2 years',
            '3-5 years', '6-10 years', 'Over 10 years'
        ]
        
        # Performance ratings
        performance_ratings = [
            'Exceeds expectations', 'Meets expectations',
            'Below expectations', 'Unsure'
        ]
        
        # Company health
        company_healths = [
            'Very strong', 'Strong', 'Stable',
            'Some concerns', 'Major concerns'
        ]
        
        # Recent layoffs
        layoff_options = [
            'Yes, major layoffs', 'Yes, minor layoffs',
            'No layoffs', 'Not sure'
        ]
        
        # Skills relevance
        skills_relevance = [
            'Very relevant', 'Somewhat relevant', 'Neutral',
            'Somewhat outdated', 'Very outdated'
        ]
        
        # AI tools usage
        ai_usage = [
            'Never', 'Rarely', 'Sometimes', 'Often', 'Constantly'
        ]
        
        # Skills
        all_skills = [
            'Programming', 'Data Analysis', 'Project Management',
            'Customer Service', 'Sales', 'Marketing', 'Design',
            'Writing', 'Teaching/Training', 'Strategy',
            'Creative Writing', 'Leadership'
        ]
        
        for i in range(count):
            # Select risk level based on distribution
            risk_rand = random.random()
            cumulative = 0
            risk_level = RiskLevel.LOW.value
            for level, prob in risk_distribution.items():
                cumulative += prob
                if risk_rand <= cumulative:
                    risk_level = level
                    break
            
            # Generate profile based on risk level
            if risk_level == RiskLevel.CRITICAL.value:
                # High-risk profile
                industry = random.choice(['Manufacturing', 'Retail/E-commerce'])
                automation_level = random.choice(['A Lot', 'Almost Everything'])
                company_size = random.choice(['1-10 employees', '11-50 employees'])
                tenure = random.choice(['Less than 6 months', '6 months - 1 year'])
                performance_rating = random.choice(['Below expectations', 'Unsure'])
                company_health = random.choice(['Some concerns', 'Major concerns'])
                recent_layoffs = random.choice(['Yes, major layoffs', 'Yes, minor layoffs'])
                skills_relevance = random.choice(['Somewhat outdated', 'Very outdated'])
                ai_usage = random.choice(['Never', 'Rarely'])
                skills = random.sample(all_skills, random.randint(1, 3))
                
            elif risk_level == RiskLevel.HIGH.value:
                # Medium-high risk profile
                industry = random.choice(['Manufacturing', 'Retail/E-commerce', 'Finance/Banking'])
                automation_level = random.choice(['Moderate', 'A Lot'])
                company_size = random.choice(['11-50 employees', '51-200 employees'])
                tenure = random.choice(['6 months - 1 year', '1-2 years'])
                performance_rating = random.choice(['Meets expectations', 'Below expectations'])
                company_health = random.choice(['Stable', 'Some concerns'])
                recent_layoffs = random.choice(['Yes, minor layoffs', 'No layoffs'])
                skills_relevance = random.choice(['Somewhat relevant', 'Neutral'])
                ai_usage = random.choice(['Rarely', 'Sometimes'])
                skills = random.sample(all_skills, random.randint(2, 4))
                
            elif risk_level == RiskLevel.MEDIUM.value:
                # Medium risk profile
                industry = random.choice(industries)
                automation_level = random.choice(['Some', 'Moderate'])
                company_size = random.choice(['51-200 employees', '201-1000 employees'])
                tenure = random.choice(['1-2 years', '3-5 years'])
                performance_rating = random.choice(['Meets expectations', 'Exceeds expectations'])
                company_health = random.choice(['Strong', 'Stable'])
                recent_layoffs = random.choice(['No layoffs', 'Not sure'])
                skills_relevance = random.choice(['Very relevant', 'Somewhat relevant'])
                ai_usage = random.choice(['Sometimes', 'Often'])
                skills = random.sample(all_skills, random.randint(3, 5))
                
            else:  # LOW risk
                # Low risk profile
                industry = random.choice(['Technology', 'Healthcare', 'Education'])
                automation_level = random.choice(['Very Little', 'Some'])
                company_size = random.choice(['201-1000 employees', '1000+ employees'])
                tenure = random.choice(['3-5 years', '6-10 years', 'Over 10 years'])
                performance_rating = random.choice(['Exceeds expectations', 'Meets expectations'])
                company_health = random.choice(['Very strong', 'Strong'])
                recent_layoffs = random.choice(['No layoffs'])
                skills_relevance = random.choice(['Very relevant'])
                ai_usage = random.choice(['Often', 'Constantly'])
                skills = random.sample(all_skills, random.randint(4, 6))
            
            profile = RiskUserProfile(
                user_id=f"load_test_user_{i}",
                risk_level=risk_level,
                industry=industry,
                automation_level=automation_level,
                company_size=company_size,
                tenure=tenure,
                performance_rating=performance_rating,
                company_health=company_health,
                recent_layoffs=recent_layoffs,
                skills_relevance=skills_relevance,
                ai_tools_usage=ai_usage,
                skills=skills
            )
            profiles.append(profile)
        
        return profiles
    
    async def simulate_high_risk_user_surge(self, user_count: int = 500, 
                                          duration_minutes: int = 10) -> LoadTestResult:
        """Test system performance during mass layoff events"""
        logger.info(f"Starting high-risk user surge simulation: {user_count} users for {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Generate high-risk user profiles
        profiles = self.generate_risk_user_profiles(user_count)
        high_risk_profiles = [p for p in profiles if p.risk_level in ['high', 'critical']]
        
        # Track metrics
        response_times = []
        successful_requests = 0
        failed_requests = 0
        peak_cpu = 0
        peak_memory = 0
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(50)  # Max 50 concurrent requests
        
        async def simulate_user_session(profile: RiskUserProfile):
            """Simulate a single user session"""
            nonlocal successful_requests, failed_requests, peak_cpu, peak_memory
            
            async with semaphore:
                try:
                    # Simulate risk assessment
                    assessment_start = time.time()
                    await self._simulate_risk_assessment(profile)
                    assessment_time = time.time() - assessment_start
                    
                    # Simulate emergency unlock if high risk
                    if profile.risk_level in ['high', 'critical']:
                        unlock_start = time.time()
                        await self._simulate_emergency_unlock(profile)
                        unlock_time = time.time() - unlock_start
                        response_times.append(unlock_time)
                    else:
                        response_times.append(assessment_time)
                    
                    successful_requests += 1
                    
                    # Track system resources
                    cpu_usage = psutil.cpu_percent()
                    memory_usage = psutil.virtual_memory().percent
                    peak_cpu = max(peak_cpu, cpu_usage)
                    peak_memory = max(peak_memory, memory_usage)
                    
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Error in user session {profile.user_id}: {e}")
        
        # Run simulation
        tasks = []
        for profile in high_risk_profiles:
            task = asyncio.create_task(simulate_user_session(profile))
            tasks.append(task)
        
        # Wait for all tasks to complete or timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=duration_minutes * 60)
        except asyncio.TimeoutError:
            logger.warning("High-risk user surge simulation timed out")
        
        # Calculate results
        total_requests = successful_requests + failed_requests
        test_duration = time.time() - start_time
        
        result = LoadTestResult(
            scenario=LoadTestScenario.HIGH_RISK_SURGE.value,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=self._calculate_percentile(response_times, 95),
            p99_response_time=self._calculate_percentile(response_times, 99),
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            throughput=total_requests / test_duration if test_duration > 0 else 0,
            concurrent_users=min(50, len(high_risk_profiles)),
            peak_cpu_usage=peak_cpu,
            peak_memory_usage=peak_memory,
            timestamp=datetime.now().isoformat(),
            metadata={
                'high_risk_users': len(high_risk_profiles),
                'critical_risk_users': len([p for p in high_risk_profiles if p.risk_level == 'critical']),
                'duration_minutes': duration_minutes
            }
        )
        
        self.results.append(result)
        logger.info(f"High-risk user surge simulation completed: {successful_requests}/{total_requests} successful")
        return result
    
    async def test_concurrent_emergency_unlocks(self, concurrent_count: int = 100) -> LoadTestResult:
        """Validate system stability under emergency load"""
        logger.info(f"Testing concurrent emergency unlocks: {concurrent_count} concurrent users")
        
        start_time = time.time()
        
        # Generate critical risk profiles
        profiles = self.generate_risk_user_profiles(concurrent_count)
        critical_profiles = [p for p in profiles if p.risk_level == 'critical']
        
        # Track metrics
        response_times = []
        successful_requests = 0
        failed_requests = 0
        peak_cpu = 0
        peak_memory = 0
        
        async def simulate_emergency_unlock(profile: RiskUserProfile):
            """Simulate emergency unlock process"""
            nonlocal successful_requests, failed_requests, peak_cpu, peak_memory
            
            try:
                unlock_start = time.time()
                await self._simulate_emergency_unlock(profile)
                unlock_time = time.time() - unlock_start
                
                response_times.append(unlock_time)
                successful_requests += 1
                
                # Track system resources
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                peak_cpu = max(peak_cpu, cpu_usage)
                peak_memory = max(peak_memory, memory_usage)
                
            except Exception as e:
                failed_requests += 1
                logger.error(f"Error in emergency unlock {profile.user_id}: {e}")
        
        # Run concurrent emergency unlocks
        tasks = [asyncio.create_task(simulate_emergency_unlock(profile)) 
                for profile in critical_profiles]
        
        await asyncio.gather(*tasks)
        
        # Calculate results
        total_requests = successful_requests + failed_requests
        test_duration = time.time() - start_time
        
        result = LoadTestResult(
            scenario=LoadTestScenario.CONCURRENT_EMERGENCY_UNLOCKS.value,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=self._calculate_percentile(response_times, 95),
            p99_response_time=self._calculate_percentile(response_times, 99),
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            throughput=total_requests / test_duration if test_duration > 0 else 0,
            concurrent_users=concurrent_count,
            peak_cpu_usage=peak_cpu,
            peak_memory_usage=peak_memory,
            timestamp=datetime.now().isoformat(),
            metadata={
                'concurrent_unlocks': concurrent_count,
                'critical_risk_users': len(critical_profiles)
            }
        )
        
        self.results.append(result)
        logger.info(f"Concurrent emergency unlock test completed: {successful_requests}/{total_requests} successful")
        return result
    
    async def measure_risk_assessment_scalability(self, max_concurrent: int = 200) -> LoadTestResult:
        """Test performance with 100+ concurrent risk assessments"""
        logger.info(f"Testing risk assessment scalability: up to {max_concurrent} concurrent assessments")
        
        start_time = time.time()
        
        # Generate diverse user profiles
        profiles = self.generate_risk_user_profiles(max_concurrent)
        
        # Track metrics
        response_times = []
        successful_requests = 0
        failed_requests = 0
        peak_cpu = 0
        peak_memory = 0
        
        # Test with increasing concurrent load
        concurrent_levels = [10, 25, 50, 100, 150, max_concurrent]
        
        for concurrent_level in concurrent_levels:
            logger.info(f"Testing with {concurrent_level} concurrent assessments")
            
            # Create semaphore for this level
            semaphore = asyncio.Semaphore(concurrent_level)
            
            async def simulate_risk_assessment(profile: RiskUserProfile):
                """Simulate risk assessment"""
                nonlocal successful_requests, failed_requests, peak_cpu, peak_memory
                
                async with semaphore:
                    try:
                        assessment_start = time.time()
                        await self._simulate_risk_assessment(profile)
                        assessment_time = time.time() - assessment_start
                        
                        response_times.append(assessment_time)
                        successful_requests += 1
                        
                        # Track system resources
                        cpu_usage = psutil.cpu_percent()
                        memory_usage = psutil.virtual_memory().percent
                        peak_cpu = max(peak_cpu, cpu_usage)
                        peak_memory = max(peak_memory, memory_usage)
                        
                    except Exception as e:
                        failed_requests += 1
                        logger.error(f"Error in risk assessment {profile.user_id}: {e}")
            
            # Run assessments for this concurrent level
            tasks = [asyncio.create_task(simulate_risk_assessment(profile)) 
                    for profile in profiles[:concurrent_level]]
            
            await asyncio.gather(*tasks)
            
            # Brief pause between levels
            await asyncio.sleep(2)
        
        # Calculate results
        total_requests = successful_requests + failed_requests
        test_duration = time.time() - start_time
        
        result = LoadTestResult(
            scenario=LoadTestScenario.RISK_ASSESSMENT_SCALABILITY.value,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=self._calculate_percentile(response_times, 95),
            p99_response_time=self._calculate_percentile(response_times, 99),
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            throughput=total_requests / test_duration if test_duration > 0 else 0,
            concurrent_users=max_concurrent,
            peak_cpu_usage=peak_cpu,
            peak_memory_usage=peak_memory,
            timestamp=datetime.now().isoformat(),
            metadata={
                'max_concurrent': max_concurrent,
                'concurrent_levels_tested': concurrent_levels
            }
        )
        
        self.results.append(result)
        logger.info(f"Risk assessment scalability test completed: {successful_requests}/{total_requests} successful")
        return result
    
    async def validate_notification_system_capacity(self, notification_count: int = 1000) -> LoadTestResult:
        """Ensure alert system handles high-risk user volumes"""
        logger.info(f"Testing notification system capacity: {notification_count} notifications")
        
        start_time = time.time()
        
        # Generate notification data
        notifications = []
        for i in range(notification_count):
            risk_level = random.choice(['high', 'critical'])
            notification = {
                'user_id': f"notification_user_{i}",
                'risk_level': risk_level,
                'message': f"Risk alert for user {i}",
                'priority': 'high' if risk_level == 'critical' else 'medium',
                'timestamp': datetime.now().isoformat()
            }
            notifications.append(notification)
        
        # Track metrics
        response_times = []
        successful_requests = 0
        failed_requests = 0
        peak_cpu = 0
        peak_memory = 0
        
        # Create semaphore to limit concurrent notifications
        semaphore = asyncio.Semaphore(100)  # Max 100 concurrent notifications
        
        async def simulate_notification(notification: Dict[str, Any]):
            """Simulate notification delivery"""
            nonlocal successful_requests, failed_requests, peak_cpu, peak_memory
            
            async with semaphore:
                try:
                    notification_start = time.time()
                    await self._simulate_notification_delivery(notification)
                    notification_time = time.time() - notification_start
                    
                    response_times.append(notification_time)
                    successful_requests += 1
                    
                    # Track system resources
                    cpu_usage = psutil.cpu_percent()
                    memory_usage = psutil.virtual_memory().percent
                    peak_cpu = max(peak_cpu, cpu_usage)
                    peak_memory = max(peak_memory, memory_usage)
                    
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Error in notification {notification['user_id']}: {e}")
        
        # Run notification simulation
        tasks = [asyncio.create_task(simulate_notification(notification)) 
                for notification in notifications]
        
        await asyncio.gather(*tasks)
        
        # Calculate results
        total_requests = successful_requests + failed_requests
        test_duration = time.time() - start_time
        
        result = LoadTestResult(
            scenario=LoadTestScenario.NOTIFICATION_CAPACITY.value,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=self._calculate_percentile(response_times, 95),
            p99_response_time=self._calculate_percentile(response_times, 99),
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            throughput=total_requests / test_duration if test_duration > 0 else 0,
            concurrent_users=100,  # Max concurrent notifications
            peak_cpu_usage=peak_cpu,
            peak_memory_usage=peak_memory,
            timestamp=datetime.now().isoformat(),
            metadata={
                'notification_count': notification_count,
                'high_priority_notifications': len([n for n in notifications if n['priority'] == 'high'])
            }
        )
        
        self.results.append(result)
        logger.info(f"Notification system capacity test completed: {successful_requests}/{total_requests} successful")
        return result
    
    async def run_mixed_risk_load_test(self, total_users: int = 1000, 
                                     duration_minutes: int = 15) -> LoadTestResult:
        """Run comprehensive mixed risk load test"""
        logger.info(f"Starting mixed risk load test: {total_users} users for {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Generate mixed risk profiles
        profiles = self.generate_risk_user_profiles(total_users)
        
        # Track metrics
        response_times = []
        successful_requests = 0
        failed_requests = 0
        peak_cpu = 0
        peak_memory = 0
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(100)  # Max 100 concurrent requests
        
        async def simulate_mixed_user_session(profile: RiskUserProfile):
            """Simulate mixed user session"""
            nonlocal successful_requests, failed_requests, peak_cpu, peak_memory
            
            async with semaphore:
                try:
                    session_start = time.time()
                    
                    # Risk assessment
                    await self._simulate_risk_assessment(profile)
                    
                    # Emergency unlock if high risk
                    if profile.risk_level in ['high', 'critical']:
                        await self._simulate_emergency_unlock(profile)
                    
                    # Recommendations
                    await self._simulate_recommendation_generation(profile)
                    
                    # Notifications
                    await self._simulate_notification_delivery({
                        'user_id': profile.user_id,
                        'risk_level': profile.risk_level,
                        'message': f"Risk assessment completed for {profile.user_id}",
                        'priority': 'high' if profile.risk_level in ['high', 'critical'] else 'medium'
                    })
                    
                    session_time = time.time() - session_start
                    response_times.append(session_time)
                    successful_requests += 1
                    
                    # Track system resources
                    cpu_usage = psutil.cpu_percent()
                    memory_usage = psutil.virtual_memory().percent
                    peak_cpu = max(peak_cpu, cpu_usage)
                    peak_memory = max(peak_memory, memory_usage)
                    
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Error in mixed user session {profile.user_id}: {e}")
        
        # Run mixed load simulation
        tasks = []
        for profile in profiles:
            task = asyncio.create_task(simulate_mixed_user_session(profile))
            tasks.append(task)
        
        # Wait for all tasks to complete or timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=duration_minutes * 60)
        except asyncio.TimeoutError:
            logger.warning("Mixed risk load test timed out")
        
        # Calculate results
        total_requests = successful_requests + failed_requests
        test_duration = time.time() - start_time
        
        result = LoadTestResult(
            scenario=LoadTestScenario.MIXED_RISK_LOAD.value,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=self._calculate_percentile(response_times, 95),
            p99_response_time=self._calculate_percentile(response_times, 99),
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            throughput=total_requests / test_duration if test_duration > 0 else 0,
            concurrent_users=100,  # Max concurrent
            peak_cpu_usage=peak_cpu,
            peak_memory_usage=peak_memory,
            timestamp=datetime.now().isoformat(),
            metadata={
                'total_users': total_users,
                'duration_minutes': duration_minutes,
                'risk_distribution': {
                    'low': len([p for p in profiles if p.risk_level == 'low']),
                    'medium': len([p for p in profiles if p.risk_level == 'medium']),
                    'high': len([p for p in profiles if p.risk_level == 'high']),
                    'critical': len([p for p in profiles if p.risk_level == 'critical'])
                }
            }
        )
        
        self.results.append(result)
        logger.info(f"Mixed risk load test completed: {successful_requests}/{total_requests} successful")
        return result
    
    # Simulation helper methods
    async def _simulate_risk_assessment(self, profile: RiskUserProfile):
        """Simulate risk assessment API call"""
        # Simulate API call delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Simulate different processing times based on risk level
        if profile.risk_level == 'critical':
            await asyncio.sleep(random.uniform(0.2, 0.4))
        elif profile.risk_level == 'high':
            await asyncio.sleep(random.uniform(0.3, 0.6))
        elif profile.risk_level == 'medium':
            await asyncio.sleep(random.uniform(0.4, 0.8))
        else:  # low
            await asyncio.sleep(random.uniform(0.5, 1.0))
    
    async def _simulate_emergency_unlock(self, profile: RiskUserProfile):
        """Simulate emergency unlock process"""
        # Simulate emergency unlock delay
        await asyncio.sleep(random.uniform(0.05, 0.2))
    
    async def _simulate_recommendation_generation(self, profile: RiskUserProfile):
        """Simulate recommendation generation"""
        # Simulate recommendation generation delay
        await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def _simulate_notification_delivery(self, notification: Dict[str, Any]):
        """Simulate notification delivery"""
        # Simulate notification delivery delay
        await asyncio.sleep(random.uniform(0.01, 0.1))
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def analyze_load_test_results(self) -> Dict[str, Any]:
        """Analyze all load test results"""
        if not self.results:
            return {'error': 'No load test results available'}
        
        analysis = {
            'total_tests': len(self.results),
            'scenarios_tested': list(set(r.scenario for r in self.results)),
            'overall_performance': {
                'total_requests': sum(r.total_requests for r in self.results),
                'total_successful': sum(r.successful_requests for r in self.results),
                'total_failed': sum(r.failed_requests for r in self.results),
                'overall_error_rate': sum(r.failed_requests for r in self.results) / sum(r.total_requests for r in self.results) * 100 if sum(r.total_requests for r in self.results) > 0 else 0,
                'avg_response_time': statistics.mean([r.avg_response_time for r in self.results if r.avg_response_time > 0]),
                'max_response_time': max([r.max_response_time for r in self.results]),
                'peak_cpu_usage': max([r.peak_cpu_usage for r in self.results]),
                'peak_memory_usage': max([r.peak_memory_usage for r in self.results])
            },
            'scenario_analysis': {}
        }
        
        # Analyze each scenario
        for result in self.results:
            scenario = result.scenario
            if scenario not in analysis['scenario_analysis']:
                analysis['scenario_analysis'][scenario] = []
            analysis['scenario_analysis'][scenario].append(asdict(result))
        
        # Performance validation
        analysis['performance_validation'] = {
            'meets_response_time_target': all(r.avg_response_time <= self.thresholds['max_response_time'] for r in self.results),
            'meets_error_rate_target': all(r.error_rate <= self.thresholds['max_error_rate'] for r in self.results),
            'meets_throughput_target': all(r.throughput >= self.thresholds['min_throughput'] for r in self.results),
            'meets_cpu_target': all(r.peak_cpu_usage <= self.thresholds['max_cpu_usage'] for r in self.results),
            'meets_memory_target': all(r.peak_memory_usage <= self.thresholds['max_memory_usage'] for r in self.results)
        }
        
        return analysis
    
    def export_load_test_report(self, output_path: str):
        """Export comprehensive load test report"""
        analysis = self.analyze_load_test_results()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'load_test_analysis': analysis,
            'detailed_results': [asdict(result) for result in self.results],
            'performance_thresholds': self.thresholds,
            'recommendations': self._generate_performance_recommendations(analysis)
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Load test report exported to {output_path}")
    
    def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        validation = analysis.get('performance_validation', {})
        
        if not validation.get('meets_response_time_target', True):
            recommendations.append("Response times exceed target - consider optimizing risk assessment algorithms")
        
        if not validation.get('meets_error_rate_target', True):
            recommendations.append("Error rates exceed target - investigate and fix system stability issues")
        
        if not validation.get('meets_throughput_target', True):
            recommendations.append("Throughput below target - consider horizontal scaling or performance optimization")
        
        if not validation.get('meets_cpu_target', True):
            recommendations.append("CPU usage exceeds target - optimize resource-intensive operations")
        
        if not validation.get('meets_memory_target', True):
            recommendations.append("Memory usage exceeds target - implement memory optimization strategies")
        
        return recommendations

# Example usage and testing
async def main():
    """Example usage of RiskLoadTester"""
    config = {
        'api_base_url': 'http://localhost:5000',
        'max_concurrent_users': 1000,
        'test_timeout': 300
    }
    
    tester = RiskLoadTester(config)
    
    # Run high-risk user surge test
    print("Running high-risk user surge test...")
    surge_result = await tester.simulate_high_risk_user_surge(user_count=200, duration_minutes=5)
    print(f"Surge test completed: {surge_result.successful_requests}/{surge_result.total_requests} successful")
    print(f"Average response time: {surge_result.avg_response_time:.2f}s")
    print(f"Error rate: {surge_result.error_rate:.2f}%")
    
    # Run concurrent emergency unlock test
    print("\nRunning concurrent emergency unlock test...")
    unlock_result = await tester.test_concurrent_emergency_unlocks(concurrent_count=50)
    print(f"Emergency unlock test completed: {unlock_result.successful_requests}/{unlock_result.total_requests} successful")
    print(f"Average response time: {unlock_result.avg_response_time:.2f}s")
    
    # Analyze results
    analysis = tester.analyze_load_test_results()
    print(f"\nLoad test analysis: {analysis['overall_performance']}")
    
    # Export report
    tester.export_load_test_report('risk_load_test_report.json')

if __name__ == "__main__":
    asyncio.run(main())
