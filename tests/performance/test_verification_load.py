"""
Load Testing for Phone Verification System
Tests high-volume scenarios and performance under stress
"""

import pytest
import time
import threading
import asyncio
import aiohttp
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

class TestVerificationLoad:
    """Load testing for verification system"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API testing"""
        return "http://localhost:5000/api"
    
    @pytest.fixture
    def test_phone_numbers(self):
        """Generate test phone numbers"""
        return [f"+1234567{i:04d}" for i in range(1000)]
    
    def test_concurrent_verification_requests(self, base_url, test_phone_numbers):
        """Test concurrent verification requests"""
        results = []
        errors = []
        start_time = time.time()
        
        def send_verification_request(phone_number):
            """Send a single verification request"""
            try:
                import requests
                response = requests.post(
                    f"{base_url}/onboarding/send-verification",
                    json={
                        "user_id": f"user_{phone_number}",
                        "phone_number": phone_number
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                return {
                    "phone": phone_number,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "phone": phone_number,
                    "error": str(e),
                    "success": False
                }
        
        # Test with 100 concurrent requests
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(send_verification_request, phone)
                for phone in test_phone_numbers[:100]
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if not result.get("success"):
                    errors.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        successful_requests = [r for r in results if r.get("success")]
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        print(f"\nLoad Test Results:")
        print(f"Total requests: {len(results)}")
        print(f"Successful requests: {len(successful_requests)}")
        print(f"Failed requests: {len(errors)}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Requests per second: {len(results) / total_time:.2f}")
        
        if response_times:
            print(f"Average response time: {statistics.mean(response_times):.3f} seconds")
            print(f"Median response time: {statistics.median(response_times):.3f} seconds")
            print(f"95th percentile: {statistics.quantiles(response_times, n=20)[18]:.3f} seconds")
        
        # Assertions
        assert len(successful_requests) > len(results) * 0.9  # 90% success rate
        if response_times:
            assert statistics.mean(response_times) < 2.0  # Average < 2 seconds
            assert statistics.quantiles(response_times, n=20)[18] < 5.0  # 95th percentile < 5 seconds
    
    @pytest.mark.asyncio
    async def test_async_verification_load(self, base_url, test_phone_numbers):
        """Test async verification requests"""
        async def send_async_request(session, phone_number):
            """Send async verification request"""
            try:
                start_time = time.time()
                async with session.post(
                    f"{base_url}/onboarding/send-verification",
                    json={
                        "user_id": f"user_{phone_number}",
                        "phone_number": phone_number
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    return {
                        "phone": phone_number,
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status == 200
                    }
            except Exception as e:
                return {
                    "phone": phone_number,
                    "error": str(e),
                    "success": False
                }
        
        # Test with 500 concurrent async requests
        connector = aiohttp.TCPConnector(limit=500, limit_per_host=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                send_async_request(session, phone)
                for phone in test_phone_numbers[:500]
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
        
        total_time = end_time - start_time
        successful_requests = [r for r in results if r.get("success")]
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        print(f"\nAsync Load Test Results:")
        print(f"Total requests: {len(results)}")
        print(f"Successful requests: {len(successful_requests)}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Requests per second: {len(results) / total_time:.2f}")
        
        if response_times:
            print(f"Average response time: {statistics.mean(response_times):.3f} seconds")
            print(f"95th percentile: {statistics.quantiles(response_times, n=20)[18]:.3f} seconds")
        
        # Assertions
        assert len(successful_requests) > len(results) * 0.85  # 85% success rate
        if response_times:
            assert statistics.mean(response_times) < 3.0  # Average < 3 seconds
    
    def test_database_connection_pool_stress(self, base_url):
        """Test database connection pool under stress"""
        # Simulate many concurrent database operations
        results = []
        
        def stress_database_operation(user_id):
            """Perform database-intensive operation"""
            try:
                import requests
                # Send multiple requests to stress database
                for i in range(10):
                    response = requests.post(
                        f"{base_url}/onboarding/send-verification",
                        json={
                            "user_id": f"{user_id}_{i}",
                            "phone_number": f"+1234567{i:04d}"
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    if response.status_code != 200:
                        return {"user_id": user_id, "success": False, "error": f"Status {response.status_code}"}
                return {"user_id": user_id, "success": True}
            except Exception as e:
                return {"user_id": user_id, "success": False, "error": str(e)}
        
        # Test with 50 concurrent users, each making 10 requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(stress_database_operation, f"user_{i}")
                for i in range(50)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        successful_operations = [r for r in results if r.get("success")]
        
        print(f"\nDatabase Stress Test Results:")
        print(f"Total operations: {len(results)}")
        print(f"Successful operations: {len(successful_operations)}")
        print(f"Success rate: {len(successful_operations) / len(results) * 100:.1f}%")
        
        # Assertions
        assert len(successful_operations) > len(results) * 0.8  # 80% success rate
    
    def test_rate_limiting_under_load(self, base_url):
        """Test rate limiting behavior under high load"""
        results = []
        
        def rapid_requests(user_id):
            """Send rapid requests to test rate limiting"""
            try:
                import requests
                phone_number = f"+1234567{user_id:04d}"
                
                # Send 10 rapid requests
                for i in range(10):
                    response = requests.post(
                        f"{base_url}/onboarding/send-verification",
                        json={
                            "user_id": f"{user_id}_{i}",
                            "phone_number": phone_number
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    
                    if response.status_code == 429:  # Rate limited
                        return {"user_id": user_id, "rate_limited": True, "request_number": i + 1}
                
                return {"user_id": user_id, "rate_limited": False, "request_number": 10}
            except Exception as e:
                return {"user_id": user_id, "error": str(e)}
        
        # Test with 20 concurrent users
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(rapid_requests, i)
                for i in range(20)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        rate_limited_requests = [r for r in results if r.get("rate_limited")]
        
        print(f"\nRate Limiting Test Results:")
        print(f"Total users: {len(results)}")
        print(f"Rate limited users: {len(rate_limited_requests)}")
        print(f"Rate limiting effectiveness: {len(rate_limited_requests) / len(results) * 100:.1f}%")
        
        # Assertions
        assert len(rate_limited_requests) > len(results) * 0.5  # At least 50% should be rate limited
    
    def test_memory_usage_under_load(self, base_url, test_phone_numbers):
        """Test memory usage under sustained load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        results = []
        
        def memory_intensive_operation(phone_number):
            """Perform memory-intensive operation"""
            try:
                import requests
                # Send request with large payload
                large_payload = {
                    "user_id": f"user_{phone_number}",
                    "phone_number": phone_number,
                    "metadata": {
                        "large_field": "x" * 1000,  # 1KB of data
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_agent": "Load Test Agent",
                        "ip_address": "192.168.1.1"
                    }
                }
                
                response = requests.post(
                    f"{base_url}/onboarding/send-verification",
                    json=large_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                return {
                    "phone": phone_number,
                    "success": response.status_code == 200,
                    "memory_used": process.memory_info().rss / 1024 / 1024
                }
            except Exception as e:
                return {"phone": phone_number, "error": str(e), "success": False}
        
        # Run 200 memory-intensive operations
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(memory_intensive_operation, phone)
                for phone in test_phone_numbers[:200]
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        successful_requests = [r for r in results if r.get("success")]
        
        print(f"\nMemory Usage Test Results:")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Successful requests: {len(successful_requests)}")
        
        # Assertions
        assert memory_increase < 100  # Memory increase should be less than 100MB
        assert len(successful_requests) > len(results) * 0.8  # 80% success rate
    
    def test_concurrent_verification_and_verification(self, base_url, test_phone_numbers):
        """Test concurrent sending and verifying codes"""
        results = []
        
        def send_and_verify(user_id):
            """Send code and immediately try to verify it"""
            try:
                import requests
                phone_number = f"+1234567{user_id:04d}"
                
                # Send verification code
                send_response = requests.post(
                    f"{base_url}/onboarding/send-verification",
                    json={
                        "user_id": f"user_{user_id}",
                        "phone_number": phone_number
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if send_response.status_code != 200:
                    return {"user_id": user_id, "success": False, "error": "Send failed"}
                
                # Try to verify with a dummy code (should fail)
                verify_response = requests.post(
                    f"{base_url}/onboarding/verify-phone",
                    json={
                        "user_id": f"user_{user_id}",
                        "phone_number": phone_number,
                        "verification_code": "000000"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                return {
                    "user_id": user_id,
                    "send_success": send_response.status_code == 200,
                    "verify_success": verify_response.status_code == 200,
                    "verify_expected_failure": verify_response.status_code == 400
                }
            except Exception as e:
                return {"user_id": user_id, "error": str(e)}
        
        # Test with 100 concurrent users
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(send_and_verify, i)
                for i in range(100)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        successful_sends = [r for r in results if r.get("send_success")]
        expected_failures = [r for r in results if r.get("verify_expected_failure")]
        
        print(f"\nConcurrent Send/Verify Test Results:")
        print(f"Total operations: {len(results)}")
        print(f"Successful sends: {len(successful_sends)}")
        print(f"Expected verification failures: {len(expected_failures)}")
        
        # Assertions
        assert len(successful_sends) > len(results) * 0.9  # 90% send success rate
        assert len(expected_failures) > len(results) * 0.8  # 80% should fail verification as expected
    
    def test_sustained_load_performance(self, base_url):
        """Test performance under sustained load"""
        import time
        
        # Run sustained load for 5 minutes
        duration = 300  # 5 minutes
        start_time = time.time()
        results = []
        
        def sustained_request():
            """Send requests continuously"""
            while time.time() - start_time < duration:
                try:
                    import requests
                    phone_number = f"+1234567{int(time.time() * 1000) % 10000:04d}"
                    
                    response = requests.post(
                        f"{base_url}/onboarding/send-verification",
                        json={
                            "user_id": f"sustained_{int(time.time())}",
                            "phone_number": phone_number
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    
                    results.append({
                        "timestamp": time.time(),
                        "success": response.status_code == 200,
                        "response_time": response.elapsed.total_seconds()
                    })
                    
                    time.sleep(0.1)  # 10 requests per second
                except Exception as e:
                    results.append({
                        "timestamp": time.time(),
                        "success": False,
                        "error": str(e)
                    })
        
        # Run sustained load in background
        thread = threading.Thread(target=sustained_request)
        thread.start()
        thread.join()
        
        # Calculate performance metrics
        successful_requests = [r for r in results if r.get("success")]
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        print(f"\nSustained Load Test Results:")
        print(f"Duration: {duration} seconds")
        print(f"Total requests: {len(results)}")
        print(f"Successful requests: {len(successful_requests)}")
        print(f"Requests per second: {len(results) / duration:.2f}")
        
        if response_times:
            print(f"Average response time: {statistics.mean(response_times):.3f} seconds")
            print(f"95th percentile: {statistics.quantiles(response_times, n=20)[18]:.3f} seconds")
        
        # Assertions
        assert len(successful_requests) > len(results) * 0.85  # 85% success rate
        if response_times:
            assert statistics.mean(response_times) < 2.0  # Average < 2 seconds
``` 