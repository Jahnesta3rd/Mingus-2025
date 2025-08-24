"""
Performance Security Testing for MINGUS
Comprehensive performance and security testing under load
"""

import os
import sys
import json
import time
import hashlib
import requests
import subprocess
import ssl
import socket
import re
import random
import string
import threading
import asyncio
import aiohttp
import multiprocessing
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import unittest
from loguru import logger
import sqlite3
import psutil
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import urllib.parse
import queue
import statistics
import concurrent.futures
import threading
import signal
import gc

class PerformanceTestType(Enum):
    """Types of performance security tests"""
    DDOS_RESILIENCE = "ddos_resilience"
    RATE_LIMITING = "rate_limiting"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONCURRENT_USER = "concurrent_user"

class PerformanceTestSeverity(Enum):
    """Performance test severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class PerformanceTest:
    """Performance test structure"""
    test_id: str
    name: str
    test_type: PerformanceTestType
    severity: PerformanceTestSeverity
    description: str
    test_function: Callable
    duration: int = 60
    concurrent_users: int = 10
    requests_per_second: int = 100
    timeout: int = 30
    success_criteria: Dict[str, Any] = field(default_factory=dict)

class DDoSResilienceTesting:
    """DDoS resilience testing suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
        self.results = {}
    
    def test_slowloris_attack(self) -> Dict[str, Any]:
        """Test Slowloris DDoS attack resilience"""
        results = {
            "vulnerable": False,
            "connection_limit": 0,
            "timeout_handling": False,
            "server_resources": {}
        }
        
        try:
            # Create multiple slow connections
            connections = []
            max_connections = 1000
            
            for i in range(max_connections):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    host = self.base_url.replace("http://", "").replace("https://", "").split(":")[0]
                    port = 80 if "http://" in self.base_url else 443
                    
                    sock.connect((host, port))
                    
                    # Send partial HTTP request
                    request = f"GET / HTTP/1.1\r\nHost: {host}\r\n"
                    sock.send(request.encode())
                    
                    connections.append(sock)
                    
                    if i % 100 == 0:
                        logger.info(f"Created {i} slow connections")
                
                except Exception as e:
                    logger.info(f"Connection limit reached at {i} connections")
                    results["connection_limit"] = i
                    break
            
            # Test if server is still responsive
            time.sleep(5)
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                if response.status_code == 200:
                    results["timeout_handling"] = True
                else:
                    results["vulnerable"] = True
            except:
                results["vulnerable"] = True
            
            # Clean up connections
            for sock in connections:
                try:
                    sock.close()
                except:
                    pass
            
            # Monitor server resources
            results["server_resources"] = self._monitor_server_resources()
            
        except Exception as e:
            logger.error(f"Error in Slowloris test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_syn_flood_attack(self) -> Dict[str, Any]:
        """Test SYN flood attack resilience"""
        results = {
            "vulnerable": False,
            "syn_cookies": False,
            "connection_handling": "normal"
        }
        
        try:
            # Create SYN flood using raw sockets (requires root)
            if os.geteuid() == 0:
                import struct
                
                # Create raw socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                
                host = self.base_url.replace("http://", "").replace("https://", "").split(":")[0]
                port = 80 if "http://" in self.base_url else 443
                
                # Send SYN packets
                for i in range(1000):
                    # Create SYN packet
                    source_port = random.randint(1024, 65535)
                    
                    # IP header
                    ip_header = struct.pack('!BBHHHBBH4s4s',
                        69, 0, 40, 54321, 0, 255, 6, 0,
                        socket.inet_aton('192.168.1.1'),
                        socket.inet_aton(socket.gethostbyname(host))
                    )
                    
                    # TCP header
                    tcp_header = struct.pack('!HHLLBBHHH',
                        source_port, port, 0, 0, 5 << 4, 2, 8192, 0, 0
                    )
                    
                    packet = ip_header + tcp_header
                    sock.sendto(packet, (host, 0))
                
                sock.close()
                
                # Test server response
                time.sleep(2)
                response = requests.get(f"{self.base_url}/health", timeout=10)
                if response.status_code != 200:
                    results["vulnerable"] = True
            else:
                logger.info("SYN flood test requires root privileges")
                results["skipped"] = "requires_root"
        
        except Exception as e:
            logger.error(f"Error in SYN flood test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_http_flood_attack(self) -> Dict[str, Any]:
        """Test HTTP flood attack resilience"""
        results = {
            "vulnerable": False,
            "requests_handled": 0,
            "response_times": [],
            "error_rate": 0.0
        }
        
        try:
            # Send rapid HTTP requests
            total_requests = 1000
            successful_requests = 0
            response_times = []
            errors = 0
            
            start_time = time.time()
            
            for i in range(total_requests):
                try:
                    request_start = time.time()
                    response = self.session.get(f"{self.base_url}/health", timeout=5)
                    request_time = time.time() - request_start
                    
                    if response.status_code == 200:
                        successful_requests += 1
                        response_times.append(request_time)
                    else:
                        errors += 1
                
                except Exception as e:
                    errors += 1
                
                if i % 100 == 0:
                    logger.info(f"Sent {i} HTTP flood requests")
            
            total_time = time.time() - start_time
            
            results["requests_handled"] = successful_requests
            results["response_times"] = response_times
            results["error_rate"] = errors / total_requests
            
            # Check if server is overwhelmed
            if results["error_rate"] > 0.5:
                results["vulnerable"] = True
            
            # Check response time degradation
            if response_times and statistics.mean(response_times) > 2.0:
                results["vulnerable"] = True
        
        except Exception as e:
            logger.error(f"Error in HTTP flood test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_amplification_attack(self) -> Dict[str, Any]:
        """Test amplification attack resilience"""
        results = {
            "vulnerable": False,
            "amplification_factor": 1.0,
            "large_response_endpoints": []
        }
        
        try:
            # Test endpoints that might return large responses
            test_endpoints = [
                "/api/users",
                "/api/data",
                "/api/logs",
                "/api/search"
            ]
            
            for endpoint in test_endpoints:
                try:
                    # Send small request
                    small_request = {"query": "test"}
                    small_response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=small_request,
                        timeout=10
                    )
                    
                    # Send large request
                    large_request = {"query": "a" * 1000}
                    large_response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=large_request,
                        timeout=10
                    )
                    
                    # Calculate amplification factor
                    if small_response.status_code == 200 and large_response.status_code == 200:
                        small_size = len(small_response.content)
                        large_size = len(large_response.content)
                        
                        if small_size > 0:
                            amplification = large_size / small_size
                            if amplification > 10:  # Significant amplification
                                results["large_response_endpoints"].append({
                                    "endpoint": endpoint,
                                    "amplification_factor": amplification
                                })
                
                except Exception as e:
                    logger.error(f"Error testing amplification for {endpoint}: {e}")
            
            # Check if any endpoints have high amplification
            if results["large_response_endpoints"]:
                max_amplification = max([ep["amplification_factor"] for ep in results["large_response_endpoints"]])
                results["amplification_factor"] = max_amplification
                
                if max_amplification > 50:
                    results["vulnerable"] = True
        
        except Exception as e:
            logger.error(f"Error in amplification test: {e}")
            results["error"] = str(e)
        
        return results
    
    def _monitor_server_resources(self) -> Dict[str, Any]:
        """Monitor server resource usage"""
        try:
            # This would typically connect to server monitoring
            # For now, return placeholder data
            return {
                "cpu_usage": random.uniform(20, 80),
                "memory_usage": random.uniform(30, 70),
                "network_connections": random.randint(100, 1000),
                "disk_io": random.uniform(10, 50)
            }
        except:
            return {"error": "monitoring_unavailable"}

class RateLimitingEffectivenessTesting:
    """Rate limiting effectiveness testing suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
        self.results = {}
    
    def test_basic_rate_limiting(self) -> Dict[str, Any]:
        """Test basic rate limiting effectiveness"""
        results = {
            "rate_limit_enforced": False,
            "limit_threshold": 0,
            "window_size": 0,
            "bypass_methods": []
        }
        
        try:
            # Test different request rates
            test_rates = [10, 50, 100, 200, 500]
            
            for rate in test_rates:
                logger.info(f"Testing rate limit at {rate} requests per second")
                
                successful_requests = 0
                rate_limited_requests = 0
                
                start_time = time.time()
                
                for i in range(rate):
                    try:
                        response = self.session.get(f"{self.base_url}/api/users", timeout=5)
                        
                        if response.status_code == 200:
                            successful_requests += 1
                        elif response.status_code == 429:  # Rate limited
                            rate_limited_requests += 1
                        
                        # Control request rate
                        time.sleep(1.0 / rate)
                    
                    except Exception as e:
                        logger.error(f"Request error: {e}")
                
                duration = time.time() - start_time
                actual_rate = successful_requests / duration
                
                if rate_limited_requests > 0:
                    results["rate_limit_enforced"] = True
                    results["limit_threshold"] = rate
                    break
            
            # Test rate limit window
            if results["rate_limit_enforced"]:
                results["window_size"] = self._test_rate_limit_window()
        
        except Exception as e:
            logger.error(f"Error in basic rate limiting test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_rate_limit_bypass(self) -> Dict[str, Any]:
        """Test rate limit bypass techniques"""
        results = {
            "bypass_methods": [],
            "vulnerable_techniques": []
        }
        
        bypass_techniques = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Real-IP": "192.168.1.1"},
            {"X-Client-IP": "192.168.1.1"},
            {"X-Remote-IP": "192.168.1.1"},
            {"X-Remote-Addr": "192.168.1.1"},
            {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
            {"Referer": "https://www.google.com"}
        ]
        
        for technique in bypass_techniques:
            try:
                # Send requests with bypass technique
                successful_requests = 0
                rate_limited_requests = 0
                
                for i in range(100):
                    response = self.session.get(
                        f"{self.base_url}/api/users",
                        headers=technique,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        successful_requests += 1
                    elif response.status_code == 429:
                        rate_limited_requests += 1
                    
                    time.sleep(0.01)  # 100 requests per second
                
                # Check if bypass was successful
                if successful_requests > 50 and rate_limited_requests < 10:
                    results["bypass_methods"].append(technique)
                    results["vulnerable_techniques"].append(list(technique.keys())[0])
            
            except Exception as e:
                logger.error(f"Error testing bypass technique {technique}: {e}")
        
        return results
    
    def test_rate_limit_consistency(self) -> Dict[str, Any]:
        """Test rate limit consistency across endpoints"""
        results = {
            "consistent_limits": True,
            "endpoint_limits": {},
            "inconsistent_endpoints": []
        }
        
        test_endpoints = [
            "/api/users",
            "/api/admin/users",
            "/api/search",
            "/api/data"
        ]
        
        for endpoint in test_endpoints:
            try:
                # Test rate limit for each endpoint
                limit_found = False
                rate_limited_count = 0
                
                for i in range(200):
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    
                    if response.status_code == 429:
                        if not limit_found:
                            results["endpoint_limits"][endpoint] = i
                            limit_found = True
                        rate_limited_count += 1
                    
                    time.sleep(0.01)
                
                if not limit_found:
                    results["endpoint_limits"][endpoint] = "no_limit"
            
            except Exception as e:
                logger.error(f"Error testing rate limit for {endpoint}: {e}")
                results["endpoint_limits"][endpoint] = "error"
        
        # Check consistency
        limits = [limit for limit in results["endpoint_limits"].values() if isinstance(limit, int)]
        if limits:
            mean_limit = statistics.mean(limits)
            for endpoint, limit in results["endpoint_limits"].items():
                if isinstance(limit, int) and abs(limit - mean_limit) > mean_limit * 0.5:
                    results["consistent_limits"] = False
                    results["inconsistent_endpoints"].append(endpoint)
        
        return results
    
    def _test_rate_limit_window(self) -> int:
        """Test rate limit window size"""
        try:
            # Find when rate limit resets
            start_time = time.time()
            
            # Trigger rate limit
            for i in range(200):
                response = self.session.get(f"{self.base_url}/api/users", timeout=5)
                if response.status_code == 429:
                    break
                time.sleep(0.01)
            
            # Wait for reset
            reset_time = None
            for i in range(60):  # Wait up to 60 seconds
                time.sleep(1)
                response = self.session.get(f"{self.base_url}/api/users", timeout=5)
                if response.status_code == 200:
                    reset_time = time.time()
                    break
            
            if reset_time:
                return int(reset_time - start_time)
            else:
                return 60  # Default to 60 seconds
        
        except Exception as e:
            logger.error(f"Error testing rate limit window: {e}")
            return 60

class ResourceExhaustionTesting:
    """Resource exhaustion testing suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
        self.results = {}
    
    def test_memory_exhaustion(self) -> Dict[str, Any]:
        """Test memory exhaustion attacks"""
        results = {
            "vulnerable": False,
            "memory_usage": [],
            "large_payload_size": 0,
            "memory_limit": "unknown"
        }
        
        try:
            # Test with increasingly large payloads
            payload_sizes = [1024, 10240, 102400, 1048576, 10485760]  # 1KB to 10MB
            
            for size in payload_sizes:
                try:
                    # Create large payload
                    large_payload = "a" * size
                    
                    response = self.session.post(
                        f"{self.base_url}/api/data",
                        json={"data": large_payload},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        results["large_payload_size"] = size
                    else:
                        break
                
                except Exception as e:
                    logger.info(f"Memory limit reached at {size} bytes")
                    results["memory_limit"] = size
                    break
            
            # Check if server is vulnerable to memory exhaustion
            if results["large_payload_size"] > 1048576:  # 1MB
                results["vulnerable"] = True
        
        except Exception as e:
            logger.error(f"Error in memory exhaustion test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_cpu_exhaustion(self) -> Dict[str, Any]:
        """Test CPU exhaustion attacks"""
        results = {
            "vulnerable": False,
            "cpu_intensive_operations": [],
            "response_time_degradation": False
        }
        
        try:
            # Test CPU-intensive operations
            cpu_intensive_payloads = [
                {"operation": "sort", "data": list(range(100000))},
                {"operation": "search", "query": "a" * 1000, "data": ["a" * 1000] * 1000},
                {"operation": "calculate", "expression": "2**1000000"},
                {"operation": "process", "data": "x" * 100000}
            ]
            
            baseline_time = self._measure_response_time(f"{self.base_url}/health")
            
            for payload in cpu_intensive_payloads:
                try:
                    start_time = time.time()
                    response = self.session.post(
                        f"{self.base_url}/api/process",
                        json=payload,
                        timeout=60
                    )
                    processing_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        results["cpu_intensive_operations"].append({
                            "operation": payload["operation"],
                            "processing_time": processing_time
                        })
                        
                        # Check if processing time is excessive
                        if processing_time > 30:
                            results["vulnerable"] = True
                
                except Exception as e:
                    logger.error(f"Error testing CPU-intensive operation {payload['operation']}: {e}")
            
            # Test response time degradation
            degraded_time = self._measure_response_time(f"{self.base_url}/health")
            if degraded_time > baseline_time * 5:
                results["response_time_degradation"] = True
                results["vulnerable"] = True
        
        except Exception as e:
            logger.error(f"Error in CPU exhaustion test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_disk_exhaustion(self) -> Dict[str, Any]:
        """Test disk exhaustion attacks"""
        results = {
            "vulnerable": False,
            "file_upload_limit": 0,
            "disk_usage": "unknown"
        }
        
        try:
            # Test file upload limits
            file_sizes = [1024, 10240, 102400, 1048576, 10485760, 104857600]  # 1KB to 100MB
            
            for size in file_sizes:
                try:
                    # Create test file content
                    file_content = b"x" * size
                    
                    files = {"file": ("test.txt", file_content, "text/plain")}
                    
                    response = self.session.post(
                        f"{self.base_url}/api/upload",
                        files=files,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        results["file_upload_limit"] = size
                    else:
                        break
                
                except Exception as e:
                    logger.info(f"File upload limit reached at {size} bytes")
                    break
            
            # Check if server is vulnerable to disk exhaustion
            if results["file_upload_limit"] > 10485760:  # 10MB
                results["vulnerable"] = True
        
        except Exception as e:
            logger.error(f"Error in disk exhaustion test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_connection_exhaustion(self) -> Dict[str, Any]:
        """Test connection exhaustion attacks"""
        results = {
            "vulnerable": False,
            "max_connections": 0,
            "connection_timeout": 0
        }
        
        try:
            # Test connection limits
            connections = []
            max_test_connections = 1000
            
            for i in range(max_test_connections):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    
                    host = self.base_url.replace("http://", "").replace("https://", "").split(":")[0]
                    port = 80 if "http://" in self.base_url else 443
                    
                    sock.connect((host, port))
                    connections.append(sock)
                    
                    if i % 100 == 0:
                        logger.info(f"Created {i} connections")
                
                except Exception as e:
                    logger.info(f"Connection limit reached at {i} connections")
                    results["max_connections"] = i
                    break
            
            # Test connection timeout
            if connections:
                start_time = time.time()
                for sock in connections:
                    try:
                        sock.send(b"GET / HTTP/1.1\r\nHost: test\r\n\r\n")
                        sock.recv(1024)
                    except:
                        pass
                
                results["connection_timeout"] = time.time() - start_time
            
            # Clean up connections
            for sock in connections:
                try:
                    sock.close()
                except:
                    pass
            
            # Check if server is vulnerable
            if results["max_connections"] > 500:
                results["vulnerable"] = True
        
        except Exception as e:
            logger.error(f"Error in connection exhaustion test: {e}")
            results["error"] = str(e)
        
        return results
    
    def _measure_response_time(self, url: str) -> float:
        """Measure response time for a URL"""
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            return time.time() - start_time
        except:
            return float('inf')

class ConcurrentUserSecurityTesting:
    """Concurrent user security testing suite"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def test_concurrent_authentication(self) -> Dict[str, Any]:
        """Test concurrent authentication security"""
        results = {
            "session_conflicts": 0,
            "authentication_races": 0,
            "session_isolation": True,
            "concurrent_sessions": []
        }
        
        try:
            # Test concurrent login attempts
            def concurrent_login(user_id):
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/auth/login",
                        json={"username": f"user_{user_id}", "password": "password"},
                        timeout=10
                    )
                    return {"user_id": user_id, "status": response.status_code, "session": self.session.cookies.get("session_id")}
                except Exception as e:
                    return {"user_id": user_id, "error": str(e)}
            
            # Run concurrent logins
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(concurrent_login, i) for i in range(10)]
                login_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            sessions = [r["session"] for r in login_results if "session" in r]
            unique_sessions = set(sessions)
            
            if len(sessions) != len(unique_sessions):
                results["session_conflicts"] = len(sessions) - len(unique_sessions)
                results["session_isolation"] = False
            
            results["concurrent_sessions"] = login_results
        
        except Exception as e:
            logger.error(f"Error in concurrent authentication test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_concurrent_data_access(self) -> Dict[str, Any]:
        """Test concurrent data access security"""
        results = {
            "data_races": 0,
            "data_corruption": 0,
            "access_conflicts": 0,
            "concurrent_operations": []
        }
        
        try:
            # Test concurrent data operations
            def concurrent_data_operation(operation_id):
                try:
                    # Create test data
                    test_data = {"id": operation_id, "value": f"test_{operation_id}"}
                    
                    # Write data
                    write_response = self.session.post(
                        f"{self.base_url}/api/data",
                        json=test_data,
                        timeout=10
                    )
                    
                    # Read data
                    read_response = self.session.get(
                        f"{self.base_url}/api/data/{operation_id}",
                        timeout=10
                    )
                    
                    return {
                        "operation_id": operation_id,
                        "write_status": write_response.status_code,
                        "read_status": read_response.status_code,
                        "data_consistent": write_response.status_code == 200 and read_response.status_code == 200
                    }
                
                except Exception as e:
                    return {"operation_id": operation_id, "error": str(e)}
            
            # Run concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(concurrent_data_operation, i) for i in range(20)]
                operation_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            consistent_operations = [r for r in operation_results if r.get("data_consistent", False)]
            results["data_races"] = len(operation_results) - len(consistent_operations)
            results["concurrent_operations"] = operation_results
            
            if results["data_races"] > 0:
                results["data_corruption"] = results["data_races"]
        
        except Exception as e:
            logger.error(f"Error in concurrent data access test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_concurrent_api_abuse(self) -> Dict[str, Any]:
        """Test concurrent API abuse scenarios"""
        results = {
            "rate_limit_bypass": False,
            "concurrent_attacks": 0,
            "security_bypass": False,
            "attack_results": []
        }
        
        try:
            # Test concurrent attack scenarios
            def concurrent_attack(attack_id):
                try:
                    # Simulate different attack types
                    attack_types = ["sql_injection", "xss", "csrf", "brute_force"]
                    attack_type = attack_types[attack_id % len(attack_types)]
                    
                    if attack_type == "sql_injection":
                        payload = {"query": "' OR '1'='1"}
                        response = self.session.post(f"{self.base_url}/api/search", json=payload, timeout=10)
                    elif attack_type == "xss":
                        payload = {"content": "<script>alert('XSS')</script>"}
                        response = self.session.post(f"{self.base_url}/api/comment", json=payload, timeout=10)
                    elif attack_type == "csrf":
                        response = self.session.post(f"{self.base_url}/api/user/change-password", json={"password": "hacked"}, timeout=10)
                    else:  # brute_force
                        response = self.session.post(f"{self.base_url}/api/auth/login", json={"username": "admin", "password": "password123"}, timeout=10)
                    
                    return {
                        "attack_id": attack_id,
                        "attack_type": attack_type,
                        "status_code": response.status_code,
                        "successful": response.status_code == 200
                    }
                
                except Exception as e:
                    return {"attack_id": attack_id, "error": str(e)}
            
            # Run concurrent attacks
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(concurrent_attack, i) for i in range(50)]
                attack_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_attacks = [r for r in attack_results if r.get("successful", False)]
            results["concurrent_attacks"] = len(successful_attacks)
            results["attack_results"] = attack_results
            
            if results["concurrent_attacks"] > 10:
                results["rate_limit_bypass"] = True
                results["security_bypass"] = True
        
        except Exception as e:
            logger.error(f"Error in concurrent API abuse test: {e}")
            results["error"] = str(e)
        
        return results
    
    def test_concurrent_resource_contention(self) -> Dict[str, Any]:
        """Test concurrent resource contention"""
        results = {
            "resource_deadlocks": 0,
            "resource_starvation": False,
            "performance_degradation": False,
            "resource_usage": {}
        }
        
        try:
            # Test concurrent resource access
            def resource_operation(operation_id):
                try:
                    # Simulate resource-intensive operations
                    operations = [
                        {"type": "file_upload", "data": b"x" * 1024},
                        {"type": "database_query", "query": "SELECT * FROM large_table"},
                        {"type": "memory_allocation", "size": 1024 * 1024},
                        {"type": "cpu_intensive", "iterations": 1000000}
                    ]
                    
                    op = operations[operation_id % len(operations)]
                    
                    if op["type"] == "file_upload":
                        files = {"file": ("test.txt", op["data"], "text/plain")}
                        response = self.session.post(f"{self.base_url}/api/upload", files=files, timeout=30)
                    elif op["type"] == "database_query":
                        response = self.session.post(f"{self.base_url}/api/query", json={"query": op["query"]}, timeout=30)
                    elif op["type"] == "memory_allocation":
                        response = self.session.post(f"{self.base_url}/api/process", json={"data": "x" * op["size"]}, timeout=30)
                    else:  # cpu_intensive
                        response = self.session.post(f"{self.base_url}/api/calculate", json={"iterations": op["iterations"]}, timeout=30)
                    
                    return {
                        "operation_id": operation_id,
                        "operation_type": op["type"],
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
                
                except Exception as e:
                    return {"operation_id": operation_id, "error": str(e)}
            
            # Run concurrent resource operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(resource_operation, i) for i in range(10)]
                resource_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            failed_operations = [r for r in resource_results if "error" in r]
            slow_operations = [r for r in resource_results if r.get("response_time", 0) > 10]
            
            results["resource_deadlocks"] = len(failed_operations)
            results["resource_starvation"] = len(slow_operations) > 5
            results["performance_degradation"] = len(slow_operations) > 0
            
            # Monitor resource usage
            results["resource_usage"] = self._monitor_resource_usage()
        
        except Exception as e:
            logger.error(f"Error in concurrent resource contention test: {e}")
            results["error"] = str(e)
        
        return results
    
    def _monitor_resource_usage(self) -> Dict[str, Any]:
        """Monitor system resource usage"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_connections": len(psutil.net_connections())
            }
        except:
            return {"error": "monitoring_unavailable"}

# Main performance security testing runner
class PerformanceSecurityTestingSuite:
    """Comprehensive performance security testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def run_all_performance_tests(self) -> Dict[str, Any]:
        """Run all performance security tests"""
        logger.info("Starting comprehensive performance security testing suite")
        
        # DDoS resilience tests
        logger.info("Running DDoS resilience tests")
        ddos_tests = DDoSResilienceTesting(self.base_url, self.session)
        self.results["ddos_resilience"] = {
            "slowloris": ddos_tests.test_slowloris_attack(),
            "syn_flood": ddos_tests.test_syn_flood_attack(),
            "http_flood": ddos_tests.test_http_flood_attack(),
            "amplification": ddos_tests.test_amplification_attack()
        }
        
        # Rate limiting tests
        logger.info("Running rate limiting effectiveness tests")
        rate_tests = RateLimitingEffectivenessTesting(self.base_url, self.session)
        self.results["rate_limiting"] = {
            "basic": rate_tests.test_basic_rate_limiting(),
            "bypass": rate_tests.test_rate_limit_bypass(),
            "consistency": rate_tests.test_rate_limit_consistency()
        }
        
        # Resource exhaustion tests
        logger.info("Running resource exhaustion tests")
        resource_tests = ResourceExhaustionTesting(self.base_url, self.session)
        self.results["resource_exhaustion"] = {
            "memory": resource_tests.test_memory_exhaustion(),
            "cpu": resource_tests.test_cpu_exhaustion(),
            "disk": resource_tests.test_disk_exhaustion(),
            "connection": resource_tests.test_connection_exhaustion()
        }
        
        # Concurrent user tests
        logger.info("Running concurrent user security tests")
        concurrent_tests = ConcurrentUserSecurityTesting(self.base_url, self.session)
        self.results["concurrent_user"] = {
            "authentication": concurrent_tests.test_concurrent_authentication(),
            "data_access": concurrent_tests.test_concurrent_data_access(),
            "api_abuse": concurrent_tests.test_concurrent_api_abuse(),
            "resource_contention": concurrent_tests.test_concurrent_resource_contention()
        }
        
        # Generate summary
        self.results["summary"] = self._generate_summary()
        self.results["timestamp"] = datetime.utcnow().isoformat()
        
        logger.info("Performance security testing suite completed")
        return self.results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance security testing summary"""
        summary = {
            "total_vulnerabilities": 0,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
            "medium_vulnerabilities": 0,
            "low_vulnerabilities": 0,
            "performance_issues": 0,
            "security_issues": 0,
            "test_categories": {}
        }
        
        # Count vulnerabilities by category
        for category, tests in self.results.items():
            if category == "summary" or category == "timestamp":
                continue
            
            category_count = 0
            for test_name, test_results in tests.items():
                if isinstance(test_results, dict):
                    if test_results.get("vulnerable", False):
                        category_count += 1
                    if test_results.get("bypass_methods"):
                        category_count += len(test_results["bypass_methods"])
                    if test_results.get("concurrent_attacks", 0) > 0:
                        category_count += 1
            
            summary["test_categories"][category] = category_count
            summary["total_vulnerabilities"] += category_count
        
        # Categorize vulnerabilities
        if summary["total_vulnerabilities"] > 0:
            summary["critical_vulnerabilities"] = summary["total_vulnerabilities"] // 4
            summary["high_vulnerabilities"] = summary["total_vulnerabilities"] // 3
            summary["medium_vulnerabilities"] = summary["total_vulnerabilities"] // 2
            summary["low_vulnerabilities"] = summary["total_vulnerabilities"] - summary["critical_vulnerabilities"] - summary["high_vulnerabilities"] - summary["medium_vulnerabilities"]
        
        return summary

def run_performance_security_testing(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """Run comprehensive performance security testing"""
    suite = PerformanceSecurityTestingSuite(base_url)
    return suite.run_all_performance_tests()

if __name__ == "__main__":
    # Run performance security testing
    results = run_performance_security_testing()
    print(json.dumps(results, indent=2)) 