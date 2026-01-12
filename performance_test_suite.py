#!/usr/bin/env python3
"""
Performance Test Suite
Tests API performance with caching enabled/disabled
Compares performance metrics
"""

import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import statistics
import json
from datetime import datetime

class PerformanceTestSuite:
    """Comprehensive performance testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def test_endpoint_performance(
        self,
        endpoint: str,
        method: str = 'GET',
        num_requests: int = 50,
        concurrent: int = 5,
        data: dict = None,
        headers: dict = None
    ) -> Dict:
        """Test performance of a single endpoint"""
        results = []
        start_time = time.time()
        
        def make_request():
            url = f"{self.base_url}{endpoint}"
            req_start = time.time()
            try:
                if method == 'GET':
                    response = self.session.get(url, headers=headers, timeout=30)
                elif method == 'POST':
                    response = self.session.post(url, json=data, headers=headers, timeout=30)
                else:
                    response = self.session.request(method, url, json=data, headers=headers, timeout=30)
                
                response_time = time.time() - req_start
                return {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': 200 <= response.status_code < 300,
                    'size': len(response.content)
                }
            except Exception as e:
                return {
                    'status_code': 0,
                    'response_time': time.time() - req_start,
                    'success': False,
                    'error': str(e),
                    'size': 0
                }
        
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())
        
        total_time = time.time() - start_time
        successful = [r for r in results if r['success']]
        
        if successful:
            response_times = [r['response_time'] for r in successful]
            return {
                'endpoint': endpoint,
                'method': method,
                'total_requests': num_requests,
                'successful': len(successful),
                'failed': num_requests - len(successful),
                'total_time': total_time,
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)],
                'requests_per_second': len(successful) / total_time,
                'avg_response_size': statistics.mean([r['size'] for r in successful])
            }
        else:
            return {
                'endpoint': endpoint,
                'method': method,
                'total_requests': num_requests,
                'successful': 0,
                'failed': num_requests,
                'error': 'All requests failed'
            }
    
    def test_with_cache_warming(self, endpoint: str, warmup_requests: int = 10):
        """Test endpoint performance with cache warming"""
        print(f"\nTesting {endpoint} with cache warming...")
        
        # Warm up cache
        print(f"  Warming cache ({warmup_requests} requests)...")
        for _ in range(warmup_requests):
            try:
                self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            except:
                pass
        
        time.sleep(0.5)  # Brief pause
        
        # Test with warm cache
        print(f"  Testing with warm cache...")
        warm_result = self.test_endpoint_performance(endpoint, num_requests=50, concurrent=10)
        
        return warm_result
    
    def compare_cached_vs_uncached(self, endpoint: str):
        """Compare performance with and without cache"""
        print(f"\n{'='*70}")
        print(f"Cache Performance Comparison: {endpoint}")
        print(f"{'='*70}")
        
        # Clear cache first (if endpoint exists)
        try:
            self.session.post(f"{self.base_url}/api/recommendations/cache/clear", timeout=5)
        except:
            pass
        
        # Test without cache (cold)
        print("\n1. Testing WITHOUT cache (cold)...")
        cold_result = self.test_endpoint_performance(endpoint, num_requests=50, concurrent=10)
        
        time.sleep(1)
        
        # Warm cache
        print("\n2. Warming cache...")
        for _ in range(10):
            try:
                self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            except:
                pass
        
        time.sleep(0.5)
        
        # Test with cache (warm)
        print("\n3. Testing WITH cache (warm)...")
        warm_result = self.test_endpoint_performance(endpoint, num_requests=50, concurrent=10)
        
        # Compare results
        print(f"\n{'='*70}")
        print("COMPARISON RESULTS")
        print(f"{'='*70}")
        print(f"\nWithout Cache (Cold):")
        print(f"  Avg Response Time: {cold_result.get('avg_response_time', 0)*1000:.2f} ms")
        print(f"  Requests/Second:  {cold_result.get('requests_per_second', 0):.2f}")
        
        print(f"\nWith Cache (Warm):")
        print(f"  Avg Response Time: {warm_result.get('avg_response_time', 0)*1000:.2f} ms")
        print(f"  Requests/Second:  {warm_result.get('requests_per_second', 0):.2f}")
        
        if cold_result.get('avg_response_time') and warm_result.get('avg_response_time'):
            improvement = ((cold_result['avg_response_time'] - warm_result['avg_response_time']) / cold_result['avg_response_time']) * 100
            print(f"\nPerformance Improvement: {improvement:.1f}% faster with cache")
        
        print(f"{'='*70}\n")
        
        return {
            'cold': cold_result,
            'warm': warm_result
        }
    
    def run_full_performance_suite(self):
        """Run full performance test suite"""
        print(f"\n{'='*70}")
        print("FULL PERFORMANCE TEST SUITE")
        print(f"{'='*70}")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        # Test endpoints
        endpoints = [
            '/health',
            '/api/status',
            '/api/vehicle',
        ]
        
        all_results = []
        
        for endpoint in endpoints:
            try:
                result = self.test_endpoint_performance(endpoint, num_requests=100, concurrent=10)
                all_results.append(result)
                
                print(f"\n{endpoint}:")
                print(f"  Avg Response: {result.get('avg_response_time', 0)*1000:.2f} ms")
                print(f"  Throughput:   {result.get('requests_per_second', 0):.2f} req/s")
                print(f"  Success Rate: {result.get('successful', 0)}/{result.get('total_requests', 0)}")
                
            except Exception as e:
                print(f"Error testing {endpoint}: {e}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"performance_test_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'results': all_results
            }, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        return all_results

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Test Suite')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL')
    parser.add_argument('--endpoint', help='Test specific endpoint')
    parser.add_argument('--compare-cache', action='store_true', help='Compare cached vs uncached')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    
    args = parser.parse_args()
    
    suite = PerformanceTestSuite(base_url=args.url)
    
    if args.compare_cache and args.endpoint:
        suite.compare_cached_vs_uncached(args.endpoint)
    elif args.full:
        suite.run_full_performance_suite()
    elif args.endpoint:
        result = suite.test_endpoint_performance(args.endpoint, num_requests=100, concurrent=10)
        print(json.dumps(result, indent=2))
    else:
        print("Use --full for full suite or --endpoint <url> --compare-cache for cache comparison")
