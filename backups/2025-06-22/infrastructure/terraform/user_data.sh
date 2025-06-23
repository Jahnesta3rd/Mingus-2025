#!/bin/bash

# User data script for Mingus Application EC2 instances
# This script runs when the instance starts up

set -e

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Create application directory
mkdir -p /opt/mingus
cd /opt/mingus

# Create environment file
cat > .env << EOF
FLASK_ENV=production
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}/mingus_db
REDIS_URL=redis://${redis_host}:6379/0
MONITORING_ENABLED=true
ALERTING_ENABLED=true
AWS_REGION=${aws_region}
EOF

# Create docker-compose.yml for single instance
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mingus-app:
    image: ${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/mingus-app:latest
    container_name: mingus-app
    ports:
      - "5002:5002"
    env_file:
      - .env
    volumes:
      - /opt/mingus/logs:/app/logs
      - /opt/mingus/data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: mingus-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - mingus-app
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: mingus-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: mingus-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

# Create nginx configuration
mkdir -p nginx/ssl
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    upstream mingus_app {
        server mingus-app:5002;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://mingus_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://mingus_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Create monitoring configuration
mkdir -p monitoring/grafana/dashboards monitoring/grafana/datasources

cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mingus-app'
    static_configs:
      - targets: ['mingus-app:5002']
    metrics_path: '/monitoring/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s
EOF

# Create log directories
mkdir -p logs data backups

# Set permissions
chown -R ec2-user:ec2-user /opt/mingus

# Start services
cd /opt/mingus
docker-compose up -d

# Install CloudWatch agent for system metrics
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/bin/config.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/mingus/logs/*.log",
                        "log_group_name": "/aws/ec2/mingus-app",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "MingusApp",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json

# Create systemd service for CloudWatch agent
systemctl enable amazon-cloudwatch-agent

# Create health check script
cat > /opt/mingus/health_check.sh << 'EOF'
#!/bin/bash

# Health check script for Mingus application
APP_URL="http://localhost:5002/health"
NGINX_URL="http://localhost:80/health"

# Check application health
if curl -f -s $APP_URL > /dev/null; then
    echo "Application is healthy"
    exit 0
else
    echo "Application health check failed"
    exit 1
fi
EOF

chmod +x /opt/mingus/health_check.sh

# Create cron job for health checks
echo "*/5 * * * * /opt/mingus/health_check.sh >> /opt/mingus/logs/health_check.log 2>&1" | crontab -

# Log completion
echo "Mingus application setup completed at $(date)" >> /opt/mingus/logs/setup.log 