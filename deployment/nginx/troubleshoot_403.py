#!/usr/bin/env python3
"""
MINGUS Application - 403 Error Troubleshooting Script
Comprehensive diagnostic tool for Nginx and Flask deployment issues
"""

import os
import sys
import subprocess
import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class NginxTroubleshooter:
    """Comprehensive troubleshooting for Nginx and Flask 403 errors"""
    
    def __init__(self):
        self.issues = []
        self.recommendations = []
        self.test_results = {}
        
    def run_all_checks(self) -> Dict:
        """Run all diagnostic checks"""
        print("🔍 Starting comprehensive 403 error troubleshooting...\n")
        
        checks = [
            ("Docker Container Status", self.check_docker_containers),
            ("Nginx Configuration", self.check_nginx_config),
            ("SSL Certificate Status", self.check_ssl_certificates),
            ("File Permissions", self.check_file_permissions),
            ("Port Availability", self.check_port_availability),
            ("Network Connectivity", self.check_network_connectivity),
            ("Flask Application Status", self.check_flask_app),
            ("Security Headers", self.check_security_headers),
            ("Rate Limiting", self.check_rate_limiting),
            ("Access Logs", self.check_access_logs),
            ("Error Logs", self.check_error_logs)
        ]
        
        for check_name, check_func in checks:
            print(f"📋 Running: {check_name}")
            try:
                result = check_func()
                self.test_results[check_name] = result
                if result.get('status') == 'error':
                    self.issues.append(f"{check_name}: {result.get('message', 'Unknown error')}")
                elif result.get('status') == 'warning':
                    self.recommendations.append(f"{check_name}: {result.get('message', 'Consider optimization')}")
            except Exception as e:
                error_msg = f"Check failed: {str(e)}"
                self.test_results[check_name] = {'status': 'error', 'message': error_msg}
                self.issues.append(f"{check_name}: {error_msg}")
            print()
        
        return self.generate_report()
    
    def check_docker_containers(self) -> Dict:
        """Check Docker container status"""
        try:
            result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'status': 'error', 'message': 'Docker not accessible'}
            
            containers = result.stdout.strip().split('\n')[1:]  # Skip header
            nginx_running = False
            web_running = False
            
            for container in containers:
                if 'mingus_nginx' in container and 'Up' in container:
                    nginx_running = True
                if 'mingus_web' in container and 'Up' in container:
                    web_running = True
            
            if not nginx_running:
                return {'status': 'error', 'message': 'Nginx container not running'}
            if not web_running:
                return {'status': 'error', 'message': 'Web container not running'}
            
            return {'status': 'success', 'message': 'All containers running'}
            
        except FileNotFoundError:
            return {'status': 'error', 'message': 'Docker not installed'}
    
    def check_nginx_config(self) -> Dict:
        """Check Nginx configuration syntax"""
        try:
            # Check if nginx config is valid
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'nginx', '-t'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'error', 'message': f'Invalid Nginx config: {result.stderr}'}
            
            return {'status': 'success', 'message': 'Nginx configuration is valid'}
            
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not verify Nginx config: {str(e)}'}
    
    def check_ssl_certificates(self) -> Dict:
        """Check SSL certificate status"""
        try:
            # Check if SSL certificates exist
            cert_path = "/etc/nginx/ssl/certificate.crt"
            key_path = "/etc/nginx/ssl/private.key"
            
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'ls', '-la', cert_path], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'error', 'message': 'SSL certificate not found'}
            
            # Check certificate expiration
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'openssl', 'x509', 
                                   '-in', cert_path, '-noout', '-dates'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'warning', 'message': 'Could not verify certificate dates'}
            
            return {'status': 'success', 'message': 'SSL certificates are valid'}
            
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not verify SSL certificates: {str(e)}'}
    
    def check_file_permissions(self) -> Dict:
        """Check file permissions and ownership"""
        try:
            # Check Nginx user and permissions
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'id'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'error', 'message': 'Could not check Nginx user'}
            
            user_info = result.stdout.strip()
            if 'nginx' not in user_info:
                return {'status': 'warning', 'message': 'Nginx not running as nginx user'}
            
            # Check web root permissions
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'ls', '-la', '/var/www/mingus'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'warning', 'message': 'Could not check web root permissions'}
            
            return {'status': 'success', 'message': 'File permissions appear correct'}
            
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not check file permissions: {str(e)}'}
    
    def check_port_availability(self) -> Dict:
        """Check if required ports are available"""
        ports_to_check = [80, 443, 5002]
        available_ports = []
        unavailable_ports = []
        
        for port in ports_to_check:
            try:
                result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
                if str(port) in result.stdout:
                    unavailable_ports.append(port)
                else:
                    available_ports.append(port)
            except:
                pass
        
        if unavailable_ports:
            return {'status': 'warning', 'message': f'Ports {unavailable_ports} are in use'}
        
        return {'status': 'success', 'message': 'All required ports are available'}
    
    def check_network_connectivity(self) -> Dict:
        """Check network connectivity between containers"""
        try:
            # Test connectivity from Nginx to web container
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'ping', '-c', '1', 'web'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'error', 'message': 'Nginx cannot reach web container'}
            
            return {'status': 'success', 'message': 'Network connectivity is good'}
            
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not test network connectivity: {str(e)}'}
    
    def check_flask_app(self) -> Dict:
        """Check Flask application status"""
        try:
            # Test health endpoint
            response = requests.get('http://localhost:5002/health', timeout=5)
            if response.status_code == 200:
                return {'status': 'success', 'message': 'Flask app responding correctly'}
            else:
                return {'status': 'warning', 'message': f'Flask app returned status {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f'Flask app not accessible: {str(e)}'}
    
    def check_security_headers(self) -> Dict:
        """Check security headers configuration"""
        try:
            response = requests.get('https://localhost/', timeout=5, verify=False)
            headers = response.headers
            
            required_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            
            missing_headers = [h for h in required_headers if h not in headers]
            
            if missing_headers:
                return {'status': 'warning', 'message': f'Missing security headers: {missing_headers}'}
            
            return {'status': 'success', 'message': 'All required security headers present'}
            
        except requests.exceptions.RequestException as e:
            return {'status': 'warning', 'message': f'Could not check security headers: {str(e)}'}
    
    def check_rate_limiting(self) -> Dict:
        """Check rate limiting configuration"""
        try:
            # Test rate limiting by making multiple rapid requests
            responses = []
            for i in range(15):  # Should trigger rate limiting
                try:
                    response = requests.get('https://localhost/api/health', timeout=2, verify=False)
                    responses.append(response.status_code)
                    time.sleep(0.1)
                except:
                    pass
            
            if 429 in responses:  # Too Many Requests
                return {'status': 'success', 'message': 'Rate limiting is working'}
            else:
                return {'status': 'warning', 'message': 'Rate limiting may not be configured properly'}
                
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not test rate limiting: {str(e)}'}
    
    def check_access_logs(self) -> Dict:
        """Check Nginx access logs for patterns"""
        try:
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'tail', '-n', '50', 
                                   '/var/log/nginx/access.log'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'warning', 'message': 'Could not access Nginx logs'}
            
            logs = result.stdout
            if '403' in logs:
                return {'status': 'warning', 'message': '403 errors found in access logs'}
            
            return {'status': 'success', 'message': 'No 403 errors in recent access logs'}
            
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not check access logs: {str(e)}'}
    
    def check_error_logs(self) -> Dict:
        """Check Nginx error logs for issues"""
        try:
            result = subprocess.run(['docker', 'exec', 'mingus_nginx_prod', 'tail', '-n', '50', 
                                   '/var/log/nginx/error.log'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'status': 'warning', 'message': 'Could not access error logs'}
            
            logs = result.stdout
            if 'error' in logs.lower():
                return {'status': 'warning', 'message': 'Errors found in Nginx error logs'}
            
            return {'status': 'success', 'message': 'No errors in recent error logs'}
            
        except Exception as e:
            return {'status': 'warning', 'message': f'Could not check error logs: {str(e)}'}
    
    def generate_report(self) -> Dict:
        """Generate comprehensive troubleshooting report"""
        report = {
            'summary': {
                'total_checks': len(self.test_results),
                'success_count': len([r for r in self.test_results.values() if r.get('status') == 'success']),
                'warning_count': len([r for r in self.test_results.values() if r.get('status') == 'warning']),
                'error_count': len([r for r in self.test_results.values() if r.get('status') == 'error'])
            },
            'issues': self.issues,
            'recommendations': self.recommendations,
            'detailed_results': self.test_results
        }
        
        # Print summary
        print("📊 TROUBLESHOOTING SUMMARY")
        print("=" * 50)
        print(f"✅ Successful checks: {report['summary']['success_count']}")
        print(f"⚠️  Warnings: {report['summary']['warning_count']}")
        print(f"❌ Errors: {report['summary']['error_count']}")
        print()
        
        if self.issues:
            print("🚨 CRITICAL ISSUES FOUND:")
            for issue in self.issues:
                print(f"  • {issue}")
            print()
        
        if self.recommendations:
            print("💡 RECOMMENDATIONS:")
            for rec in self.recommendations:
                print(f"  • {rec}")
            print()
        
        return report

def main():
    """Main troubleshooting execution"""
    print("🔧 MINGUS Application - 403 Error Troubleshooter")
    print("=" * 60)
    
    troubleshooter = NginxTroubleshooter()
    report = troubleshooter.run_all_checks()
    
    # Save report to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"nginx_troubleshooting_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Detailed report saved to: {report_file}")
    
    # Provide quick fixes
    if report['summary']['error_count'] > 0:
        print("\n🚀 QUICK FIXES:")
        print("1. Restart Nginx container: docker restart mingus_nginx_prod")
        print("2. Check container logs: docker logs mingus_nginx_prod")
        print("3. Verify SSL certificates exist in deployment/nginx/ssl/")
        print("4. Ensure web container is running: docker ps | grep mingus_web")
        print("5. Check file permissions: ls -la deployment/nginx/")

if __name__ == "__main__":
    main()
