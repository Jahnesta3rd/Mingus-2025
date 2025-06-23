# Deployment and Scaling Infrastructure

This document provides comprehensive guidance for deploying and scaling the Mingus application with job security features.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Deployment Pipeline](#deployment-pipeline)
4. [Scaling Infrastructure](#scaling-infrastructure)
5. [Data Management](#data-management)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Security](#security)
8. [Disaster Recovery](#disaster-recovery)
9. [Operations Guide](#operations-guide)

## Overview

The Mingus application deployment infrastructure is designed for high availability, scalability, and maintainability. It includes:

- **Containerized deployment** using Docker and Docker Compose
- **Infrastructure as Code** using Terraform
- **Automated CI/CD pipeline** with testing and deployment stages
- **Auto-scaling** based on demand
- **Comprehensive monitoring** and alerting
- **Data backup and archival** procedures
- **Feature flag system** for gradual rollouts

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Auto Scaling  │    │   Monitoring    │
│   (Nginx/ALB)   │    │   Group (ASG)   │    │   Stack         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Database      │    │   Cache Layer   │
│   Instances     │    │   (PostgreSQL)  │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Job Queue     │    │   Backup        │    │   Archive       │
│   (Celery)      │    │   Service       │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Details

#### Application Layer
- **Flask Application**: Main application server
- **Gunicorn**: WSGI server for production
- **Nginx**: Reverse proxy and load balancer
- **Celery**: Background job processing

#### Data Layer
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage
- **S3**: Backup and archival storage

#### Infrastructure Layer
- **AWS ECS/EKS**: Container orchestration
- **Auto Scaling Groups**: Dynamic scaling
- **Load Balancers**: Traffic distribution
- **VPC**: Network isolation

## Deployment Pipeline

### CI/CD Pipeline Stages

1. **Code Commit**
   - Trigger pipeline on push to main/develop branches
   - Run automated tests

2. **Testing Stage**
   - Unit tests with coverage
   - Integration tests
   - Security scans (Bandit, Safety)
   - Performance tests

3. **Build Stage**
   - Build Docker images
   - Run security vulnerability scans
   - Push to container registry

4. **Deploy Stage**
   - Deploy to staging environment
   - Run smoke tests
   - Manual approval for production
   - Deploy to production

### Pipeline Configuration

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  test:
    # Run comprehensive tests
  security-scan:
    # Security vulnerability scanning
  build:
    # Build and push Docker images
  deploy-staging:
    # Deploy to staging environment
  deploy-production:
    # Deploy to production environment

workflows:
  development:
    # Automated deployment to staging
  production:
    # Manual approval required for production
```

### Feature Flags

The application uses a feature flag system for gradual rollouts:

```python
from deployment.feature_flags.feature_flags import feature_flag

@feature_flag("job_security_ml", user_id_func=get_user_id)
def predict_job_security(user_data):
    # ML-powered prediction logic
    pass
```

## Scaling Infrastructure

### Auto Scaling Configuration

#### CPU-Based Scaling
- **Scale Up**: CPU > 80% for 5 minutes
- **Scale Down**: CPU < 40% for 10 minutes
- **Min Instances**: 2 (production), 1 (staging)
- **Max Instances**: 10 (production), 5 (staging)

#### Memory-Based Scaling
- **Scale Up**: Memory > 85% for 5 minutes
- **Scale Down**: Memory < 60% for 10 minutes

#### Custom Metrics
- **Response Time**: Scale up if > 2 seconds
- **Error Rate**: Scale up if > 5%
- **Queue Length**: Scale up if > 100 jobs

### Load Balancing

#### Application Load Balancer (ALB)
- **Health Checks**: `/health` endpoint
- **Sticky Sessions**: For user sessions
- **SSL Termination**: HTTPS support
- **Rate Limiting**: Per IP and per user

#### Nginx Configuration
```nginx
upstream mingus_app {
    least_conn;
    server app1:5002 max_fails=3 fail_timeout=30s;
    server app2:5002 max_fails=3 fail_timeout=30s;
    server app3:5002 max_fails=3 fail_timeout=30s;
}
```

### Database Scaling

#### Read Replicas
- **Primary**: Write operations
- **Replicas**: Read operations
- **Auto-failover**: Automatic promotion

#### Connection Pooling
- **PgBouncer**: Connection pooling
- **Max Connections**: 100 per instance
- **Pool Size**: 20 connections per pool

## Data Management

### Backup Strategy

#### Database Backups
- **Frequency**: Daily at 2 AM
- **Retention**: 30 days (production), 7 days (staging)
- **Storage**: S3 with encryption
- **Type**: Full backup with WAL archiving

#### File Backups
- **Frequency**: Weekly on Sunday
- **Retention**: 90 days
- **Storage**: S3 Glacier for long-term

### Data Retention Policies

| Data Type | Retention Period | Archive Location |
|-----------|------------------|------------------|
| User Sessions | 30 days | S3 Standard-IA |
| Health Checkins | 90 days | S3 Standard-IA |
| Job Security Predictions | 365 days | S3 Glacier |
| Analytics Events | 180 days | S3 Standard-IA |
| Audit Logs | 7 years | S3 Glacier |
| Error Logs | 30 days | S3 Standard-IA |

### Data Archival Process

```python
# Automated archival process
def archive_old_data():
    for data_type, retention_days in retention_policies.items():
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        archive_data(data_type, cutoff_date)
```

## Monitoring & Maintenance

### Monitoring Stack

#### Prometheus
- **Metrics Collection**: Application, system, database
- **Alert Rules**: CPU, memory, disk, response time
- **Retention**: 30 days

#### Grafana
- **Dashboards**: Application, infrastructure, business metrics
- **Alerts**: Email, Slack, PagerDuty
- **Users**: Operations team

#### Application Monitoring
- **Health Checks**: `/health`, `/monitoring/metrics`
- **Performance Metrics**: Response time, throughput, error rate
- **Business Metrics**: User registrations, job security scores

### Alerting Rules

#### Critical Alerts
- Application down
- Database connectivity issues
- High error rate (>10%)
- Disk space > 90%

#### Warning Alerts
- High CPU usage (>80%)
- High memory usage (>85%)
- Slow response time (>5s)
- Backup failures

### Maintenance Tasks

#### Daily Tasks
- Health check monitoring
- Log rotation
- Performance metrics collection

#### Weekly Tasks
- Database optimization (VACUUM, ANALYZE)
- Log cleanup
- Security updates

#### Monthly Tasks
- Infrastructure updates
- Performance review
- Capacity planning

## Security

### Network Security

#### VPC Configuration
- **Private Subnets**: Application instances
- **Public Subnets**: Load balancers, bastion hosts
- **Security Groups**: Restrictive access rules
- **NACLs**: Additional network filtering

#### SSL/TLS
- **Certificates**: Let's Encrypt or AWS Certificate Manager
- **Protocols**: TLS 1.2 and 1.3
- **Ciphers**: Strong encryption suites

### Application Security

#### Authentication & Authorization
- **Session Management**: Secure session handling
- **Rate Limiting**: Prevent abuse
- **Input Validation**: SQL injection prevention
- **Output Encoding**: XSS prevention

#### Data Protection
- **Encryption at Rest**: Database and file storage
- **Encryption in Transit**: HTTPS/TLS
- **PII Handling**: Data anonymization
- **Access Controls**: Role-based access

## Disaster Recovery

### Backup Strategy

#### Database Recovery
- **Point-in-Time Recovery**: 7 days
- **Cross-Region Backup**: Disaster recovery
- **Automated Testing**: Monthly recovery tests

#### Application Recovery
- **Blue-Green Deployment**: Zero-downtime updates
- **Rollback Procedures**: Quick rollback capability
- **Health Checks**: Automated recovery validation

### Recovery Procedures

#### RTO (Recovery Time Objective)
- **Critical Systems**: 1 hour
- **Non-Critical Systems**: 4 hours

#### RPO (Recovery Point Objective)
- **Database**: 15 minutes
- **File Storage**: 1 hour

### Disaster Recovery Plan

1. **Assessment**: Evaluate impact and scope
2. **Communication**: Notify stakeholders
3. **Recovery**: Execute recovery procedures
4. **Validation**: Verify system functionality
5. **Documentation**: Record lessons learned

## Operations Guide

### Deployment Commands

#### Local Development
```bash
# Start local environment
docker-compose up -d

# Run tests
pytest tests/

# Build image
docker build -t mingus-app .
```

#### Staging Deployment
```bash
# Deploy to staging
terraform apply -var-file=staging.tfvars

# Update application
kubectl set image deployment/mingus-app mingus-app=latest

# Verify deployment
kubectl rollout status deployment/mingus-app
```

#### Production Deployment
```bash
# Deploy to production
terraform apply -var-file=production.tfvars

# Blue-green deployment
./scripts/blue-green-deploy.sh

# Monitor deployment
kubectl get pods -l app=mingus-app
```

### Monitoring Commands

#### Health Checks
```bash
# Application health
curl https://mingus.com/health

# Database health
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Redis health
redis-cli ping
```

#### Performance Monitoring
```bash
# Check CPU usage
top -p $(pgrep -f mingus-app)

# Check memory usage
free -h

# Check disk usage
df -h

# Check network connections
netstat -an | grep :5002
```

### Troubleshooting

#### Common Issues

1. **High CPU Usage**
   - Check for infinite loops
   - Review database queries
   - Scale up instances

2. **Memory Leaks**
   - Monitor memory usage
   - Restart application instances
   - Review code for memory leaks

3. **Database Connection Issues**
   - Check connection pool settings
   - Verify database availability
   - Review connection limits

4. **Slow Response Times**
   - Check database performance
   - Review caching strategy
   - Monitor external API calls

#### Debug Commands
```bash
# View application logs
docker logs mingus-app

# Check database connections
psql -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis memory
redis-cli info memory

# Check network connectivity
telnet database-host 5432
```

### Performance Optimization

#### Application Optimization
- **Caching**: Redis for frequently accessed data
- **Database Indexing**: Optimize query performance
- **Connection Pooling**: Efficient database connections
- **Async Processing**: Background job processing

#### Infrastructure Optimization
- **Auto Scaling**: Dynamic resource allocation
- **Load Balancing**: Efficient traffic distribution
- **CDN**: Static content delivery
- **Compression**: Reduce bandwidth usage

### Capacity Planning

#### Resource Requirements

| Component | CPU | Memory | Storage | Network |
|-----------|-----|--------|---------|---------|
| Application | 2 vCPU | 4GB | 20GB | 1Gbps |
| Database | 4 vCPU | 8GB | 100GB | 1Gbps |
| Redis | 1 vCPU | 2GB | 10GB | 1Gbps |
| Monitoring | 1 vCPU | 2GB | 50GB | 100Mbps |

#### Scaling Guidelines
- **CPU**: Scale when > 70% utilization
- **Memory**: Scale when > 80% utilization
- **Storage**: Scale when > 80% usage
- **Network**: Monitor bandwidth usage

### Security Best Practices

1. **Regular Updates**: Keep systems patched
2. **Access Control**: Principle of least privilege
3. **Monitoring**: Continuous security monitoring
4. **Backup Security**: Encrypt backup data
5. **Incident Response**: Have a plan ready

This infrastructure provides a robust, scalable, and maintainable foundation for the Mingus application with comprehensive monitoring, security, and disaster recovery capabilities. 