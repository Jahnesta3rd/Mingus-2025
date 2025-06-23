# Mingus Application - Deployment & Scaling Infrastructure

This repository contains a comprehensive deployment and scaling infrastructure for the Mingus application with advanced job security features.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Terraform (for infrastructure)
- kubectl (for Kubernetes)
- AWS CLI (for cloud deployment)
- Python 3.11+

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd mingus-application

# Start local environment
docker-compose -f deployment/docker-compose.yml up -d

# Run health checks
./deployment/scripts/health_check.sh

# Access the application
open http://localhost:5002
```

## 📁 Infrastructure Overview

```
deployment/
├── docker-compose.yml          # Local development setup
├── Dockerfile                  # Application container
├── Dockerfile.backup          # Backup service container
├── nginx/                     # Load balancer configuration
├── monitoring/                # Prometheus & Grafana configs
├── backup/                    # Backup service scripts
├── ci-cd/                     # CI/CD pipeline configuration
├── feature-flags/             # Feature flag system
└── scripts/                   # Deployment & maintenance scripts

infrastructure/
├── terraform/                 # Infrastructure as Code
│   ├── main.tf               # Main infrastructure
│   ├── variables.tf          # Configuration variables
│   └── user_data.sh          # EC2 initialization script

data/management/
├── data_retention.py         # Data lifecycle management

maintenance/
├── health_monitor.py         # Health monitoring system
```

## 🏗️ Architecture

### Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   Route 53      │    │   Certificate   │
│   (CDN)         │    │   (DNS)         │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Auto Scaling  │    │   Load Balancer │
│   Load Balancer │    │   Group (ASG)   │    │   (ALB)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ECS/EKS       │    │   RDS           │    │   ElastiCache   │
│   (Containers)  │    │   (PostgreSQL)  │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3            │    │   CloudWatch    │    │   Prometheus    │
│   (Backups)     │    │   (Monitoring)  │    │   (Metrics)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Deployment Options

### 1. Local Development

```bash
# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker-compose.yml logs -f

# Stop services
docker-compose -f deployment/docker-compose.yml down
```

### 2. Staging Deployment

```bash
# Deploy to staging
./deployment/scripts/deploy.sh staging latest

# Run health checks
./deployment/scripts/health_check.sh

# Monitor deployment
kubectl get pods -l app=mingus-app
```

### 3. Production Deployment

```bash
# Deploy to production (requires approval)
./deployment/scripts/deploy.sh production v1.2.3

# Verify deployment
kubectl rollout status deployment/mingus-app

# Monitor application
kubectl logs -l app=mingus-app -f
```

## 🔧 Infrastructure as Code

### Terraform Deployment

```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Plan deployment
terraform plan -var-file=staging.tfvars

# Apply infrastructure
terraform apply -var-file=staging.tfvars

# Destroy infrastructure (be careful!)
terraform destroy -var-file=staging.tfvars
```

### Environment Configuration

Create environment-specific variable files:

```hcl
# staging.tfvars
environment = "staging"
instance_type = "t3.medium"
desired_capacity = 2
max_size = 5

# production.tfvars
environment = "production"
instance_type = "t3.large"
desired_capacity = 3
max_size = 10
```

## 📊 Monitoring & Observability

### Prometheus Metrics

The application exposes metrics at `/monitoring/metrics`:

- Application metrics (request count, response time, error rate)
- Business metrics (user registrations, job security scores)
- System metrics (CPU, memory, disk usage)

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin123):

- **Application Dashboard**: Request rates, error rates, response times
- **Infrastructure Dashboard**: CPU, memory, disk, network usage
- **Business Dashboard**: User metrics, feature usage, job security insights

### Health Checks

```bash
# Run comprehensive health check
./deployment/scripts/health_check.sh

# Check specific components
curl http://localhost:5002/health
curl http://localhost:5002/api/health/database
curl http://localhost:5002/api/health/redis
```

## 🔄 CI/CD Pipeline

### Pipeline Stages

1. **Code Commit**: Triggers pipeline on push
2. **Testing**: Unit, integration, and security tests
3. **Build**: Docker image creation and security scanning
4. **Deploy**: Staging deployment with smoke tests
5. **Production**: Manual approval required

### Pipeline Configuration

```yaml
# .circleci/config.yml
workflows:
  development:
    jobs:
      - test
      - security-scan
      - build
      - deploy-staging
  
  production:
    jobs:
      - test
      - security-scan
      - build
      - hold-production
      - deploy-production
```

## 🚩 Feature Flags

### Using Feature Flags

```python
from deployment.feature_flags.feature_flags import feature_flag

@feature_flag("job_security_ml", user_id_func=get_user_id)
def predict_job_security(user_data):
    # ML-powered prediction logic
    pass

@feature_flag("advanced_analytics", user_id_func=get_user_id)
def show_advanced_dashboard(user_id):
    # Advanced analytics dashboard
    pass
```

### Managing Feature Flags

```python
from deployment.feature_flags.feature_flags import feature_flags

# Create a new flag
feature_flags.create_flag(FeatureFlag(
    name="new_feature",
    type=FeatureFlagType.PERCENTAGE,
    enabled=True,
    percentage=25,
    description="New feature rollout"
))

# Check if flag is enabled
if feature_flags.is_enabled("new_feature", user_id):
    # Show new feature
    pass
```

## 💾 Data Management

### Backup Strategy

- **Database**: Daily automated backups to S3
- **Files**: Weekly backups of logs and data
- **Retention**: 30 days for production, 7 days for staging

### Data Retention

```python
# Automated data archival
python data/management/data_retention.py

# Manual archival
from data.management.data_retention import DataRetentionManager
manager = DataRetentionManager()
manager.archive_old_data()
```

### Backup Commands

```bash
# Create manual backup
docker exec mingus-backup python /app/backup/backup_service.py

# Restore from backup
docker exec mingus-backup python /app/backup/backup_service.py --restore s3://bucket/backup.sql.gz
```

## 🔍 Health Monitoring

### Automated Monitoring

```bash
# Start health monitor
python maintenance/health_monitor.py

# Check monitoring status
curl http://localhost:9090/api/v1/status/targets  # Prometheus
curl http://localhost:3000/api/health            # Grafana
```

### Alert Configuration

Alerts are configured in `deployment/monitoring/alert_rules.yml`:

- **Critical**: Application down, database issues
- **Warning**: High resource usage, slow response times
- **Info**: Feature usage, business metrics

## 🔒 Security

### Security Measures

- **Network**: VPC with private subnets, security groups
- **Encryption**: TLS 1.3, database encryption, S3 encryption
- **Access**: IAM roles, least privilege principle
- **Monitoring**: Security scanning, vulnerability assessment

### Security Commands

```bash
# Run security scan
bandit -r backend/
safety check

# Check for vulnerabilities
docker run --rm -v $(pwd):/app aquasec/trivy fs /app
```

## 🚨 Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   # Check logs
   docker logs mingus-app
   
   # Check health
   curl http://localhost:5002/health
   
   # Check dependencies
   docker-compose ps
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker exec mingus-db pg_isready
   
   # Check connection
   psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **High Resource Usage**
   ```bash
   # Check system resources
   ./deployment/scripts/health_check.sh
   
   # Scale up
   kubectl scale deployment mingus-app --replicas=5
   ```

### Debug Commands

```bash
# Get detailed logs
kubectl logs -l app=mingus-app --tail=100 -f

# Check pod status
kubectl describe pod <pod-name>

# Access container shell
kubectl exec -it <pod-name> -- /bin/bash

# Check network connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup mingus-app
```

## 📈 Scaling

### Auto Scaling

The infrastructure automatically scales based on:

- **CPU Usage**: Scale up at 80%, down at 40%
- **Memory Usage**: Scale up at 85%, down at 60%
- **Response Time**: Scale up if > 2 seconds
- **Error Rate**: Scale up if > 5%

### Manual Scaling

```bash
# Scale application
kubectl scale deployment mingus-app --replicas=5

# Scale database (requires RDS modification)
aws rds modify-db-instance --db-instance-identifier mingus-db --db-instance-class db.t3.large

# Scale Redis
aws elasticache modify-replication-group --replication-group-id mingus-redis --node-type cache.t3.medium
```

## 📚 Additional Resources

### Documentation

- [Deployment Guide](docs/DEPLOYMENT_AND_SCALING.md)
- [Monitoring Guide](docs/MONITORING_AND_OPTIMIZATION.md)
- [API Documentation](docs/API_REFERENCE.md)

### Support

- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: This infrastructure is designed for production use with proper security, monitoring, and backup procedures. Always test changes in a staging environment before deploying to production. 