#!/usr/bin/env python3
"""
Utility script to display the last HTTP request from application logs
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

def parse_log_file(log_file_path):
    """Parse the log file and extract request information"""
    requests = []
    
    if not os.path.exists(log_file_path):
        print(f"Log file not found: {log_file_path}")
        return []
    
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
    
    current_request = None
    
    for line in lines:
        # Look for REQUEST log entries
        if 'REQUEST:' in line:
            # Parse request line
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| INFO \| .*? \| REQUEST: (\w+) (.+) from (.+)', line)
            if match:
                timestamp, method, path, remote_addr = match.groups()
                current_request = {
                    'timestamp': timestamp,
                    'method': method,
                    'path': path,
                    'remote_addr': remote_addr,
                    'details': None
                }
        
        # Look for detailed request information (DEBUG level)
        elif current_request and 'Request details:' in line:
            try:
                # Extract JSON from the line
                json_start = line.find('{')
                if json_start != -1:
                    json_str = line[json_start:]
                    details = json.loads(json_str)
                    current_request['details'] = details
                    requests.append(current_request)
                    current_request = None
            except json.JSONDecodeError:
                continue
        
        # Look for RESPONSE log entries
        elif 'RESPONSE:' in line:
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| INFO \| .*? \| RESPONSE: (\d+) (\w+) (.+) - ([\d.]+)ms', line)
            if match and requests:
                timestamp, status_code, method, path, response_time = match.groups()
                # Update the last request with response info
                if requests and requests[-1]['method'] == method and requests[-1]['path'] == path:
                    requests[-1]['response'] = {
                        'timestamp': timestamp,
                        'status_code': status_code,
                        'response_time_ms': float(response_time)
                    }
    
    return requests

def display_last_request(requests, show_details=False):
    """Display the last request in a formatted way"""
    if not requests:
        print("No requests found in logs")
        return
    
    last_request = requests[-1]
    
    print("=" * 80)
    print("LAST REQUEST")
    print("=" * 80)
    print(f"Timestamp: {last_request['timestamp']}")
    print(f"Method: {last_request['method']}")
    print(f"Path: {last_request['path']}")
    print(f"Remote Address: {last_request['remote_addr']}")
    
    if 'response' in last_request:
        print(f"Response Status: {last_request['response']['status_code']}")
        print(f"Response Time: {last_request['response']['response_time_ms']}ms")
    
    if show_details and last_request.get('details'):
        print("\n" + "-" * 40)
        print("DETAILED REQUEST INFORMATION")
        print("-" * 40)
        details = last_request['details']
        
        if 'headers' in details:
            print("\nHeaders:")
            for key, value in details['headers'].items():
                if key.lower() in ['authorization', 'cookie']:
                    print(f"  {key}: [REDACTED]")
                else:
                    print(f"  {key}: {value}")
        
        if 'body' in details:
            print("\nRequest Body:")
            print(json.dumps(details['body'], indent=2))
        
        if 'form_data' in details:
            print("\nForm Data:")
            print(json.dumps(details['form_data'], indent=2))
    
    print("=" * 80)

def main():
    """Main function"""
    # Find the most recent log file
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("Logs directory not found")
        return
    
    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        print("No log files found")
        return
    
    # Use the most recent log file
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    print(f"Reading from: {latest_log}")
    
    # Parse requests
    requests = parse_log_file(latest_log)
    
    # Display last request
    import sys
    show_details = '--details' in sys.argv or '-d' in sys.argv
    display_last_request(requests, show_details)
    
    # Show recent requests count
    if len(requests) > 1:
        print(f"\nTotal requests in this log file: {len(requests)}")
        print("Use --details or -d flag to see detailed request information")

if __name__ == "__main__":
    main() 