#!/usr/bin/env python3
"""
Ultra-Budget Deployment Script for Income Comparison Feature
Optimized for free/low-cost hosting platforms with performance monitoring
"""

import os
import sys
import json
import shutil
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UltraBudgetDeployer:
    """Ultra-budget deployment manager for income comparison feature"""
    
    def __init__(self, platform: str = 'auto'):
        self.platform = self._detect_platform() if platform == 'auto' else platform
        self.project_root = Path(__file__).parent.parent
        self.deployment_config = self._load_deployment_config()
        
        logger.info(f"Initializing deployment for platform: {self.platform}")
    
    def _detect_platform(self) -> str:
        """Auto-detect hosting platform"""
        # Check environment variables for platform detection
        if os.environ.get('HEROKU_APP_NAME'):
            return 'heroku'
        elif os.environ.get('RAILWAY_PROJECT_ID'):
            return 'railway'
        elif os.environ.get('RENDER_SERVICE_ID'):
            return 'render'
        elif os.environ.get('VERCEL_PROJECT_ID'):
            return 'vercel'
        elif os.environ.get('FLY_APP_NAME'):
            return 'fly'
        elif os.environ.get('NETLIFY_SITE_ID'):
            return 'netlify'
        else:
            return 'generic'
    
    def _load_deployment_config(self) -> Dict:
        """Load deployment configuration"""
        config_path = self.project_root / 'deployment' / 'ultra_budget_config.json'
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default ultra-budget configuration
            return {
                'platforms': {
                    'heroku': {
                        'buildpack': 'heroku/python',
                        'requirements_file': 'requirements_ultra_budget.txt',
                        'procfile': 'Procfile_ultra_budget',
                        'environment': {
                            'FLASK_ENV': 'heroku',
                            'PYTHON_VERSION': '3.11.0'
                        }
                    },
                    'railway': {
                        'requirements_file': 'requirements_ultra_budget.txt',
                        'start_command': 'gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4',
                        'environment': {
                            'FLASK_ENV': 'railway'
                        }
                    },
                    'render': {
                        'requirements_file': 'requirements_ultra_budget.txt',
                        'start_command': 'gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4',
                        'environment': {
                            'FLASK_ENV': 'render'
                        }
                    },
                    'vercel': {
                        'requirements_file': 'requirements_ultra_budget.txt',
                        'vercel_json': 'vercel_ultra_budget.json',
                        'environment': {
                            'FLASK_ENV': 'vercel'
                        }
                    },
                    'fly': {
                        'requirements_file': 'requirements_ultra_budget.txt',
                        'fly_toml': 'fly_ultra_budget.toml',
                        'environment': {
                            'FLASK_ENV': 'fly'
                        }
                    },
                    'netlify': {
                        'requirements_file': 'requirements_ultra_budget.txt',
                        'netlify_toml': 'netlify_ultra_budget.toml',
                        'environment': {
                            'FLASK_ENV': 'netlify'
                        }
                    }
                },
                'optimizations': {
                    'minimize_dependencies': True,
                    'use_compression': True,
                    'enable_caching': True,
                    'optimize_static_files': True,
                    'minimize_memory_usage': True
                }
            }
    
    def create_ultra_budget_requirements(self) -> None:
        """Create minimal requirements file for ultra-budget deployment"""
        requirements = [
            # Core Flask
            'Flask==2.3.3',
            'Werkzeug==2.3.7',
            
            # Essential extensions
            'Flask-CORS==4.0.0',
            'Flask-Limiter==3.5.0',
            'Flask-Caching==2.1.0',
            
            # WSGI server
            'gunicorn==21.2.0',
            
            # Logging
            'loguru==0.7.2',
            
            # Performance monitoring
            'psutil==5.9.6',
            
            # Data processing (minimal)
            'numpy==1.24.3',
            
            # Security
            'cryptography==41.0.7',
            
            # Optional: Database (only if needed)
            # 'Flask-SQLAlchemy==3.0.5',
            # 'psycopg2-binary==2.9.7',
            
            # Optional: Redis (only if using Redis)
            # 'redis==5.0.1',
        ]
        
        requirements_path = self.project_root / 'requirements_ultra_budget.txt'
        with open(requirements_path, 'w') as f:
            f.write('\n'.join(requirements))
        
        logger.info(f"Created ultra-budget requirements file: {requirements_path}")
    
    def create_optimized_procfile(self) -> None:
        """Create optimized Procfile for Heroku"""
        procfile_content = """web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --max-requests 1000 --max-requests-jitter 100 --timeout 30 --keep-alive 2 --preload
"""
        
        procfile_path = self.project_root / 'Procfile_ultra_budget'
        with open(procfile_path, 'w') as f:
            f.write(procfile_content)
        
        logger.info(f"Created optimized Procfile: {procfile_path}")
    
    def create_vercel_config(self) -> None:
        """Create Vercel configuration for ultra-budget deployment"""
        vercel_config = {
            "version": 2,
            "builds": [
                {
                    "src": "app.py",
                    "use": "@vercel/python"
                }
            ],
            "routes": [
                {
                    "src": "/(.*)",
                    "dest": "app.py"
                }
            ],
            "env": {
                "FLASK_ENV": "vercel",
                "PYTHON_VERSION": "3.11"
            },
            "functions": {
                "app.py": {
                    "maxDuration": 10
                }
            }
        }
        
        vercel_path = self.project_root / 'vercel_ultra_budget.json'
        with open(vercel_path, 'w') as f:
            json.dump(vercel_config, f, indent=2)
        
        logger.info(f"Created Vercel configuration: {vercel_path}")
    
    def create_fly_config(self) -> None:
        """Create Fly.io configuration for ultra-budget deployment"""
        fly_config = """# fly.toml
app = "mingus-income-comparison"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile_ultra_budget"

[env]
  FLASK_ENV = "fly"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"

[processes]
  app = "gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 4 --max-requests 1000 --timeout 30"
"""
        
        fly_path = self.project_root / 'fly_ultra_budget.toml'
        with open(fly_path, 'w') as f:
            f.write(fly_config)
        
        logger.info(f"Created Fly.io configuration: {fly_path}")
    
    def create_optimized_dockerfile(self) -> None:
        """Create optimized Dockerfile for ultra-budget deployment"""
        dockerfile_content = """# Ultra-budget optimized Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements_ultra_budget.txt .
RUN pip install --no-cache-dir -r requirements_ultra_budget.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--max-requests", "1000", "--timeout", "30"]
"""
        
        dockerfile_path = self.project_root / 'Dockerfile_ultra_budget'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info(f"Created optimized Dockerfile: {dockerfile_path}")
    
    def optimize_static_files(self) -> None:
        """Optimize static files for production"""
        static_dir = self.project_root / 'static'
        
        if not static_dir.exists():
            logger.warning("Static directory not found, skipping optimization")
            return
        
        # Create optimized CSS
        css_files = list(static_dir.rglob('*.css'))
        for css_file in css_files:
            self._minify_css(css_file)
        
        # Create optimized JS
        js_files = list(static_dir.rglob('*.js'))
        for js_file in js_files:
            self._minify_js(js_file)
        
        logger.info("Static files optimized")
    
    def _minify_css(self, file_path: Path) -> None:
        """Minify CSS file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Simple CSS minification
            import re
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content)
            # Remove unnecessary semicolons
            content = re.sub(r';}', '}', content)
            
            # Write minified content
            minified_path = file_path.parent / f"{file_path.stem}.min{file_path.suffix}"
            with open(minified_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Minified CSS: {minified_path}")
        except Exception as e:
            logger.warning(f"Failed to minify CSS {file_path}: {e}")
    
    def _minify_js(self, file_path: Path) -> None:
        """Minify JavaScript file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Simple JS minification
            import re
            # Remove comments (basic)
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content)
            
            # Write minified content
            minified_path = file_path.parent / f"{file_path.stem}.min{file_path.suffix}"
            with open(minified_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Minified JS: {minified_path}")
        except Exception as e:
            logger.warning(f"Failed to minify JS {file_path}: {e}")
    
    def create_health_check_script(self) -> None:
        """Create health check script for monitoring"""
        health_script = """#!/usr/bin/env python3
\"\"\"
Health check script for ultra-budget deployment
\"\"\"

import requests
import sys
import time

def check_health(url: str) -> bool:
    \"\"\"Check application health\"\"\"
    try:
        start_time = time.time()
        response = requests.get(f"{url}/health", timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed - Response time: {response_time:.2f}s")
            print(f"   Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def check_performance(url: str) -> bool:
    \"\"\"Check performance metrics\"\"\"
    try:
        response = requests.get(f"{url}/metrics", timeout=10)
        if response.status_code == 200:
            data = response.json()
            analysis_time = data.get('endpoint_metrics', {}).get('income_analysis_avg_ms', 0)
            
            if analysis_time < 500:  # Target: < 500ms
                print(f"✅ Performance good - Avg analysis time: {analysis_time}ms")
                return True
            else:
                print(f"⚠️  Performance warning - Avg analysis time: {analysis_time}ms")
                return False
        else:
            print(f"❌ Performance check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Performance check error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python health_check.py <app_url>")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    
    print(f"Checking health for: {url}")
    print("-" * 50)
    
    health_ok = check_health(url)
    performance_ok = check_performance(url)
    
    if health_ok and performance_ok:
        print("\\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\\n❌ Some checks failed!")
        sys.exit(1)
"""
        
        health_path = self.project_root / 'health_check.py'
        with open(health_path, 'w') as f:
            f.write(health_script)
        
        # Make executable
        health_path.chmod(0o755)
        
        logger.info(f"Created health check script: {health_path}")
    
    def create_monitoring_script(self) -> None:
        """Create monitoring script for performance tracking"""
        monitoring_script = """#!/usr/bin/env python3
\"\"\"
Performance monitoring script for ultra-budget deployment
\"\"\"

import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List

class PerformanceMonitor:
    \"\"\"Monitor application performance\"\"\"
    
    def __init__(self, app_url: str):
        self.app_url = app_url.rstrip('/')
        self.metrics_file = 'performance_metrics.json'
        self.load_metrics()
    
    def load_metrics(self):
        \"\"\"Load existing metrics\"\"\"
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                self.metrics = json.load(f)
        else:
            self.metrics = {
                'checks': [],
                'performance_history': [],
                'errors': []
            }
    
    def save_metrics(self):
        \"\"\"Save metrics to file\"\"\"
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def check_health(self) -> Dict:
        \"\"\"Check application health\"\"\"
        try:
            start_time = time.time()
            response = requests.get(f"{self.app_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def check_performance(self) -> Dict:
        \"\"\"Check performance metrics\"\"\"
        try:
            response = requests.get(f"{self.app_url}/metrics", timeout=10)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def run_analysis_test(self) -> Dict:
        \"\"\"Run test income analysis\"\"\"
        try:
            test_data = {
                'current_salary': 65000,
                'age_range': '25-34',
                'education_level': 'bachelors',
                'location': 'atlanta'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.app_url}/income_analysis/analyze",
                json=test_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == 200,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    
    def run_monitoring_cycle(self):
        \"\"\"Run complete monitoring cycle\"\"\"
        print(f"Running monitoring cycle for: {self.app_url}")
        print("-" * 60)
        
        # Health check
        print("1. Health Check...")
        health_result = self.check_health()
        self.metrics['checks'].append(health_result)
        
        if health_result['success']:
            print(f"   ✅ Health: {health_result['response_time']:.2f}s")
        else:
            print(f"   ❌ Health: {health_result.get('error', 'Unknown error')}")
        
        # Performance check
        print("2. Performance Check...")
        perf_result = self.check_performance()
        
        if perf_result['success']:
            data = perf_result['data']
            analysis_time = data.get('endpoint_metrics', {}).get('income_analysis_avg_ms', 0)
            print(f"   ✅ Performance: {analysis_time}ms avg analysis time")
            
            # Store performance history
            self.metrics['performance_history'].append({
                'timestamp': perf_result['timestamp'],
                'avg_analysis_time_ms': analysis_time
            })
        else:
            print(f"   ❌ Performance: {perf_result.get('error', 'Unknown error')}")
        
        # Analysis test
        print("3. Analysis Test...")
        analysis_result = self.run_analysis_test()
        
        if analysis_result['success']:
            response_time = analysis_result['response_time']
            print(f"   ✅ Analysis: {response_time:.2f}s response time")
        else:
            print(f"   ❌ Analysis: {analysis_result.get('error', 'Unknown error')}")
            self.metrics['errors'].append(analysis_result)
        
        # Save metrics
        self.save_metrics()
        
        print("-" * 60)
        print("Monitoring cycle completed")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        \"\"\"Generate performance summary\"\"\"
        if not self.metrics['performance_history']:
            return
        
        recent_performance = self.metrics['performance_history'][-10:]  # Last 10 checks
        avg_times = [p['avg_analysis_time_ms'] for p in recent_performance]
        
        print("\\n📊 Performance Summary:")
        print(f"   Average analysis time: {sum(avg_times)/len(avg_times):.1f}ms")
        print(f"   Min analysis time: {min(avg_times):.1f}ms")
        print(f"   Max analysis time: {max(avg_times):.1f}ms")
        
        # Check against targets
        avg_time = sum(avg_times)/len(avg_times)
        if avg_time < 500:
            print("   🎉 Performance target met (< 500ms)")
        else:
            print(f"   ⚠️  Performance target missed (target: < 500ms, actual: {avg_time:.1f}ms)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python monitoring.py <app_url>")
        sys.exit(1)
    
    app_url = sys.argv[1]
    monitor = PerformanceMonitor(app_url)
    monitor.run_monitoring_cycle()
"""
        
        monitoring_path = self.project_root / 'monitoring.py'
        with open(monitoring_path, 'w') as f:
            f.write(monitoring_script)
        
        # Make executable
        monitoring_path.chmod(0o755)
        
        logger.info(f"Created monitoring script: {monitoring_path}")
    
    def deploy_to_platform(self) -> bool:
        """Deploy to detected platform"""
        logger.info(f"Deploying to platform: {self.platform}")
        
        try:
            if self.platform == 'heroku':
                return self._deploy_to_heroku()
            elif self.platform == 'railway':
                return self._deploy_to_railway()
            elif self.platform == 'render':
                return self._deploy_to_render()
            elif self.platform == 'vercel':
                return self._deploy_to_vercel()
            elif self.platform == 'fly':
                return self._deploy_to_fly()
            else:
                logger.warning(f"Platform {self.platform} not supported, using generic deployment")
                return self._deploy_generic()
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def _deploy_to_heroku(self) -> bool:
        """Deploy to Heroku"""
        logger.info("Deploying to Heroku...")
        
        # Check if Heroku CLI is installed
        try:
            subprocess.run(['heroku', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Heroku CLI not found. Please install it first.")
            return False
        
        # Create app if it doesn't exist
        app_name = os.environ.get('HEROKU_APP_NAME', 'mingus-income-comparison')
        
        try:
            # Set buildpack
            subprocess.run(['heroku', 'buildpacks:set', 'heroku/python', '-a', app_name], check=True)
            
            # Set environment variables
            env_vars = {
                'FLASK_ENV': 'heroku',
                'PYTHON_VERSION': '3.11.0'
            }
            
            for key, value in env_vars.items():
                subprocess.run(['heroku', 'config:set', f'{key}={value}', '-a', app_name], check=True)
            
            # Deploy
            subprocess.run(['git', 'add', '.'])
            subprocess.run(['git', 'commit', '-m', 'Ultra-budget deployment'])
            subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
            
            logger.info(f"Successfully deployed to Heroku: https://{app_name}.herokuapp.com")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Heroku deployment failed: {e}")
            return False
    
    def _deploy_to_railway(self) -> bool:
        """Deploy to Railway"""
        logger.info("Deploying to Railway...")
        
        # Railway deployment is typically done via Git push
        try:
            subprocess.run(['git', 'add', '.'])
            subprocess.run(['git', 'commit', '-m', 'Ultra-budget deployment'])
            subprocess.run(['git', 'push', 'railway', 'main'], check=True)
            
            logger.info("Successfully deployed to Railway")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Railway deployment failed: {e}")
            return False
    
    def _deploy_to_render(self) -> bool:
        """Deploy to Render"""
        logger.info("Deploying to Render...")
        
        # Render deployment is typically done via Git push
        try:
            subprocess.run(['git', 'add', '.'])
            subprocess.run(['git', 'commit', '-m', 'Ultra-budget deployment'])
            subprocess.run(['git', 'push', 'render', 'main'], check=True)
            
            logger.info("Successfully deployed to Render")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Render deployment failed: {e}")
            return False
    
    def _deploy_to_vercel(self) -> bool:
        """Deploy to Vercel"""
        logger.info("Deploying to Vercel...")
        
        # Check if Vercel CLI is installed
        try:
            subprocess.run(['vercel', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Vercel CLI not found. Please install it first.")
            return False
        
        try:
            subprocess.run(['vercel', '--prod'], check=True)
            
            logger.info("Successfully deployed to Vercel")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Vercel deployment failed: {e}")
            return False
    
    def _deploy_to_fly(self) -> bool:
        """Deploy to Fly.io"""
        logger.info("Deploying to Fly.io...")
        
        # Check if Fly CLI is installed
        try:
            subprocess.run(['fly', 'version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Fly CLI not found. Please install it first.")
            return False
        
        try:
            subprocess.run(['fly', 'deploy'], check=True)
            
            logger.info("Successfully deployed to Fly.io")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Fly.io deployment failed: {e}")
            return False
    
    def _deploy_generic(self) -> bool:
        """Generic deployment (manual instructions)"""
        logger.info("Generic deployment - manual steps required:")
        logger.info("1. Ensure all optimized files are created")
        logger.info("2. Set environment variables")
        logger.info("3. Run: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4")
        return True
    
    def run_full_deployment(self) -> bool:
        """Run complete ultra-budget deployment"""
        logger.info("Starting ultra-budget deployment...")
        
        try:
            # Create optimized files
            self.create_ultra_budget_requirements()
            self.create_optimized_procfile()
            self.create_vercel_config()
            self.create_fly_config()
            self.create_optimized_dockerfile()
            
            # Optimize static files
            self.optimize_static_files()
            
            # Create monitoring scripts
            self.create_health_check_script()
            self.create_monitoring_script()
            
            # Deploy to platform
            success = self.deploy_to_platform()
            
            if success:
                logger.info("🎉 Ultra-budget deployment completed successfully!")
                logger.info("📊 Use health_check.py and monitoring.py for performance tracking")
                return True
            else:
                logger.error("❌ Deployment failed")
                return False
                
        except Exception as e:
            logger.error(f"Deployment process failed: {e}")
            return False

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ultra-budget deployment for income comparison feature')
    parser.add_argument('--platform', default='auto', help='Target platform (auto, heroku, railway, render, vercel, fly)')
    parser.add_argument('--create-files-only', action='store_true', help='Only create optimized files, skip deployment')
    
    args = parser.parse_args()
    
    deployer = UltraBudgetDeployer(platform=args.platform)
    
    if args.create_files_only:
        logger.info("Creating optimized files only...")
        deployer.create_ultra_budget_requirements()
        deployer.create_optimized_procfile()
        deployer.create_vercel_config()
        deployer.create_fly_config()
        deployer.create_optimized_dockerfile()
        deployer.optimize_static_files()
        deployer.create_health_check_script()
        deployer.create_monitoring_script()
        logger.info("✅ Optimized files created successfully!")
    else:
        deployer.run_full_deployment()

if __name__ == "__main__":
    main() 