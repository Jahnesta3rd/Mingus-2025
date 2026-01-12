#!/usr/bin/env python3
"""
API Load Testing Script
Tests API performance under various load conditions
"""

import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import json
from datetime import datetime
import argparse
from dataclasses import dataclass, asdict
import sys

@dataclass
class RequestResult:
    """Result of a single API request"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error: str = None
    timestamp: float = None

@dataclass
class LoadTestResult:
    """Results of a load test"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    errors: List[str]

class APILoadTester:
    """API Load Testing Tool"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results: List[RequestResult] = []
        
    def make_request(
        self, 
        endpoint: str, 
        method: str = 'GET', 
        data: dict = None,
        headers: dict = None
    ) -> RequestResult:
        """Make a single API request and measure response time"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    headers=headers, 
                    timeout=30
                )
            elif method == 'PUT':
                response = self.session.put(
                    url, 
                    json=data, 
                    headers=headers, 
                    timeout=30
                )
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            success = 200 <= response.status_code < 300
            
            # Include error message for non-2xx responses
            error_msg = None
            if not success:
                try:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}'
            
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                success=success,
                error=error_msg,
                timestamp=start_time
            )
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error="Timeout",
                timestamp=start_time
            )
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error="Connection Error",
                timestamp=start_time
            )
        except Exception as e:
            response_time = time.time() - start_time
            return RequestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e),
                timestamp=start_time
            )
    
    def run_load_test(
        self,
        endpoint: str,
        method: str = 'GET',
        num_requests: int = 100,
        concurrent_users: int = 10,
        data: dict = None,
        headers: dict = None
    ) -> LoadTestResult:
        """Run load test for a specific endpoint"""
        print(f"\n{'='*70}")
        print(f"Load Testing: {method} {endpoint}")
        print(f"Total Requests: {num_requests}")
        print(f"Concurrent Users: {concurrent_users}")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        results: List[RequestResult] = []
        
        # Create tasks
        tasks = [
            (endpoint, method, data, headers) 
            for _ in range(num_requests)
        ]
        
        # Execute requests with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(self.make_request, ep, m, d, h)
                for ep, m, d, h in tasks
            ]
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1
                
                # Progress indicator
                if completed % 10 == 0:
                    print(f"Progress: {completed}/{num_requests} requests completed", end='\r')
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        # Include all response times (even failed ones) for timing analysis
        response_times = [r.response_time for r in results if r.response_time > 0]
        successful_response_times = [r.response_time for r in successful]
        
        if response_times:
            response_times_sorted = sorted(response_times)
            p95_index = int(len(response_times_sorted) * 0.95)
            p99_index = int(len(response_times_sorted) * 0.99)
            
            # Use successful response times for stats if available, otherwise use all
            stats_times = successful_response_times if successful_response_times else response_times
            
            load_result = LoadTestResult(
                endpoint=endpoint,
                method=method,
                total_requests=num_requests,
                successful_requests=len(successful),
                failed_requests=len(failed),
                avg_response_time=statistics.mean(stats_times) if stats_times else statistics.mean(response_times),
                min_response_time=min(response_times),
                max_response_time=max(response_times),
                median_response_time=statistics.median(stats_times) if stats_times else statistics.median(response_times),
                p95_response_time=response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else response_times_sorted[-1],
                p99_response_time=response_times_sorted[p99_index] if p99_index < len(response_times_sorted) else response_times_sorted[-1],
                requests_per_second=len(results) / total_time if total_time > 0 else 0,  # All requests, not just successful
                errors=[r.error for r in failed if r.error]
            )
        else:
            load_result = LoadTestResult(
                endpoint=endpoint,
                method=method,
                total_requests=num_requests,
                successful_requests=0,
                failed_requests=len(failed),
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                errors=[r.error for r in failed if r.error]
            )
        
        return load_result
    
    def print_results(self, result: LoadTestResult):
        """Print formatted test results"""
        print(f"\n{'='*70}")
        print(f"RESULTS: {result.method} {result.endpoint}")
        print(f"{'='*70}")
        print(f"Total Requests:        {result.total_requests}")
        print(f"Successful:            {result.successful_requests} ({result.successful_requests/result.total_requests*100:.1f}%)")
        print(f"Failed:                {result.failed_requests} ({result.failed_requests/result.total_requests*100:.1f}%)")
        print(f"\nResponse Times:")
        print(f"  Average:             {result.avg_response_time*1000:.2f} ms")
        print(f"  Median:              {result.median_response_time*1000:.2f} ms")
        print(f"  Min:                 {result.min_response_time*1000:.2f} ms")
        print(f"  Max:                 {result.max_response_time*1000:.2f} ms")
        print(f"  95th Percentile:     {result.p95_response_time*1000:.2f} ms")
        print(f"  99th Percentile:     {result.p99_response_time*1000:.2f} ms")
        print(f"\nThroughput:")
        print(f"  Requests/Second:     {result.requests_per_second:.2f}")
        
        if result.errors:
            print(f"\nErrors:")
            error_counts = {}
            for error in result.errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in error_counts.items():
                print(f"  {error}: {count}")
        
        print(f"{'='*70}\n")
    
    def run_comprehensive_test(
        self,
        num_requests: int = 100,
        concurrent_users: int = 10
    ):
        """Run comprehensive load test on multiple endpoints"""
        print(f"\n{'='*70}")
        print("COMPREHENSIVE API LOAD TEST")
        print(f"{'='*70}")
        print(f"Base URL: {self.base_url}")
        print(f"Test Configuration:")
        print(f"  Requests per endpoint: {num_requests}")
        print(f"  Concurrent users: {concurrent_users}")
        print(f"{'='*70}\n")
        
        # Test endpoints
        test_cases = [
            # Health and status endpoints
            {'endpoint': '/health', 'method': 'GET'},
            {'endpoint': '/api/status', 'method': 'GET'},
            
            # Assessment endpoints (with sample data)
            {
                'endpoint': '/api/assessments',
                'method': 'POST',
                'data': {
                    'email': 'test@example.com',
                    'assessmentType': 'ai-risk',
                    'answers': {'q1': 'answer1', 'q2': 'answer2'}
                },
                'headers': {'X-CSRF-Token': 'test-token'}
            },
            
            # Profile endpoints
            {'endpoint': '/api/profile', 'method': 'GET'},
            
            # Vehicle endpoints
            {'endpoint': '/api/vehicle', 'method': 'GET'},
            
            # Job matching endpoints
            {'endpoint': '/api/job-matching/search', 'method': 'GET'},
        ]
        
        all_results = []
        
        for test_case in test_cases:
            try:
                result = self.run_load_test(
                    endpoint=test_case['endpoint'],
                    method=test_case.get('method', 'GET'),
                    num_requests=num_requests,
                    concurrent_users=concurrent_users,
                    data=test_case.get('data'),
                    headers=test_case.get('headers')
                )
                all_results.append(result)
                self.print_results(result)
                
                # Small delay between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"Error testing {test_case['endpoint']}: {e}")
        
        # Summary
        self.print_summary(all_results)
        
        return all_results
    
    def print_summary(self, results: List[LoadTestResult]):
        """Print summary of all test results"""
        print(f"\n{'='*70}")
        print("LOAD TEST SUMMARY")
        print(f"{'='*70}\n")
        
        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        total_failed = sum(r.failed_requests for r in results)
        
        print(f"Overall Statistics:")
        print(f"  Total Requests:      {total_requests}")
        print(f"  Successful:          {total_successful} ({total_successful/total_requests*100:.1f}%)")
        print(f"  Failed:              {total_failed} ({total_failed/total_requests*100:.1f}%)")
        
        successful_results = [r for r in results if r.successful_requests > 0]
        if successful_results:
            avg_times = [r.avg_response_time for r in successful_results]
            print(f"\nPerformance Metrics:")
            print(f"  Average Response:   {statistics.mean(avg_times)*1000:.2f} ms")
            print(f"  Best Endpoint:      {min(successful_results, key=lambda x: x.avg_response_time).endpoint}")
            print(f"  Slowest Endpoint:   {max(successful_results, key=lambda x: x.avg_response_time).endpoint}")
            
            total_rps = sum(r.requests_per_second for r in successful_results)
            print(f"  Total Throughput:   {total_rps:.2f} requests/second")
        
        print(f"\n{'='*70}\n")
    
    def save_results(self, results: List[LoadTestResult], filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"load_test_results_{timestamp}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': [asdict(r) for r in results]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results saved to: {filename}")
        return filename

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='API Load Testing Tool')
    parser.add_argument(
        '--url',
        default='http://localhost:5001',
        help='Base URL of the API (default: http://localhost:5001)'
    )
    parser.add_argument(
        '--requests',
        type=int,
        default=100,
        help='Number of requests per endpoint (default: 100)'
    )
    parser.add_argument(
        '--concurrent',
        type=int,
        default=10,
        help='Number of concurrent users (default: 10)'
    )
    parser.add_argument(
        '--endpoint',
        help='Test specific endpoint (e.g., /api/health)'
    )
    parser.add_argument(
        '--method',
        default='GET',
        help='HTTP method (default: GET)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to JSON file'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run comprehensive test on multiple endpoints'
    )
    
    args = parser.parse_args()
    
    tester = APILoadTester(base_url=args.url)
    
    if args.full:
        # Run comprehensive test
        results = tester.run_comprehensive_test(
            num_requests=args.requests,
            concurrent_users=args.concurrent
        )
        
        if args.save:
            tester.save_results(results)
    elif args.endpoint:
        # Test single endpoint
        result = tester.run_load_test(
            endpoint=args.endpoint,
            method=args.method,
            num_requests=args.requests,
            concurrent_users=args.concurrent
        )
        tester.print_results(result)
        
        if args.save:
            tester.save_results([result])
    else:
        # Default: run comprehensive test
        results = tester.run_comprehensive_test(
            num_requests=args.requests,
            concurrent_users=args.concurrent
        )
        
        if args.save:
            tester.save_results(results)

if __name__ == '__main__':
    main()
