#!/usr/bin/env python3
"""
Simple web server to serve Mingus API data.
"""

import json
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

class MingusAPIHandler(SimpleHTTPRequestHandler):
    """Custom handler for Mingus API endpoints."""
    
    def __init__(self, *args, **kwargs):
        self.api_dir = Path("mingus_api")
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for API endpoints."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # API endpoints
        if path == "/api/content":
            self.serve_json_file("content.json")
        elif path == "/api/splash":
            self.serve_json_file("splash_screen.json")
        elif path.startswith("/api/category/"):
            category = path.split("/")[-1]
            self.serve_json_file(f"{category}.json")
        elif path == "/api/titles":
            self.serve_json_file("title_suggestions.json")
        elif path == "/api/health":
            self.send_health_response()
        else:
            # Serve static files
            super().do_GET()
    
    def serve_json_file(self, filename):
        """Serve a JSON file from the API directory."""
        file_path = self.api_dir / filename
        
        if not file_path.exists():
            self.send_error(404, f"File not found: {filename}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            json_data = json.dumps(data, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")
    
    def send_health_response(self):
        """Send health check response."""
        health_data = {
            "status": "healthy",
            "api_version": "1.0",
            "endpoints": [
                "/api/content",
                "/api/splash",
                "/api/category/{category}",
                "/api/titles",
                "/api/health"
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(health_data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8080):
    """Run the Mingus API server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MingusAPIHandler)
    
    print(f"🚀 Mingus API Server running on http://localhost:{port}")
    print(f"📡 Available endpoints:")
    print(f"   • http://localhost:{port}/api/content - All content")
    print(f"   • http://localhost:{port}/api/splash - Splash screen data")
    print(f"   • http://localhost:{port}/api/category/uncategorized - Category content")
    print(f"   • http://localhost:{port}/api/health - Health check")
    print(f"\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
