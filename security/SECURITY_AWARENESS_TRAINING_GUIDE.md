# Security Awareness and Training System Guide

## Overview

The Security Awareness and Training System provides comprehensive security education and policy management for MINGUS. This system includes security policy documentation, training modules, awareness campaigns, and compliance tracking to ensure all users understand and follow security best practices.

## Features

### 🔒 **Security Policy Management**
- **Policy Creation & Management**: Create, update, and manage security policies
- **Policy Types**: Acceptable Use, Password Policy, Data Classification, Privacy Policy, and more
- **Policy Acknowledgment**: Track user acknowledgments with timestamps and audit trails
- **Compliance Requirements**: Link policies to specific compliance frameworks (GDPR, PCI DSS, HIPAA, etc.)
- **Version Control**: Track policy versions and effective dates
- **Review Scheduling**: Automatic reminders for policy reviews

### 🎓 **Training Module System**
- **Interactive Training Modules**: Comprehensive security training with quizzes
- **Module Types**: Security Basics, Phishing Awareness, Password Security, Data Protection, etc.
- **Progress Tracking**: Monitor user progress and completion rates
- **Quiz Assessment**: Interactive quizzes with scoring and feedback
- **Certificate Generation**: Automatic certificate issuance upon completion
- **Difficulty Levels**: Beginner, Intermediate, and Advanced modules

### 📢 **Awareness Campaigns**
- **Campaign Management**: Create and manage security awareness campaigns
- **Campaign Types**: Phishing simulations, security quizzes, awareness videos
- **Target Audience**: Segment campaigns by user roles or groups
- **Success Metrics**: Track campaign effectiveness and participation
- **Scheduling**: Set campaign start and end dates

### 📊 **Reporting & Analytics**
- **Training Reports**: Comprehensive training completion reports
- **Compliance Tracking**: Monitor policy acknowledgment compliance
- **Progress Analytics**: Track individual and organizational progress
- **Dashboard Views**: Real-time dashboard with key metrics
- **Export Capabilities**: Export reports in various formats

## Installation & Setup

### Prerequisites
- Python 3.8+
- Flask framework
- SQLite database
- Required Python packages (see requirements.txt)

### Quick Start

1. **Install Dependencies**
```bash
pip install flask flask-cors dataclasses-json
```

2. **Initialize the System**
```python
from security.security_awareness_training import create_security_awareness_training_system

# Create the training system
training_system = create_security_awareness_training_system()
```

3. **Register Flask Routes**
```python
from security.routes.security_awareness_routes import security_awareness_bp

# Register the blueprint with your Flask app
app.register_blueprint(security_awareness_bp)
```

## Configuration

### Database Configuration
```python
# Default database path
db_path = "/var/lib/mingus/security_training.db"

# Custom database path
training_system = SecurityAwarenessTrainingSystem(db_path="/custom/path/training.db")
```

### Policy Configuration
```yaml
# security_awareness_config.yml
policies:
  default_policies:
    - acceptable_use
    - password_policy
    - data_classification
    - privacy_policy
  
  acknowledgment_required: true
  acknowledgment_deadline_days: 30
  
  compliance_frameworks:
    - GDPR
    - PCI DSS
    - HIPAA
    - SOX
```

### Training Configuration
```yaml
# training_config.yml
modules:
  default_modules:
    - security_basics
    - phishing_awareness
    - password_security
  
  passing_score: 80
  certificate_required: true
  retry_attempts: 3
  
  difficulty_levels:
    - beginner
    - intermediate
    - advanced
```

## Usage Examples

### Python API Usage

#### 1. Create Security Policy
```python
from security.security_awareness_training import SecurityPolicy, PolicyType
from datetime import datetime, timedelta

# Create a new security policy
policy = SecurityPolicy(
    policy_id="POL-001",
    policy_type=PolicyType.ACCEPTABLE_USE,
    title="Acceptable Use Policy",
    description="Defines acceptable use of MINGUS systems",
    content="# Acceptable Use Policy\n\n## 1. Purpose\nThis policy...",
    version="1.0",
    effective_date=datetime.utcnow(),
    review_date=datetime.utcnow() + timedelta(days=365),
    applicable_to=["all_users"],
    compliance_requirements=["GDPR", "PCI DSS"],
    created_by="security_team"
)

# Save the policy
training_system = create_security_awareness_training_system()
success = training_system.create_security_policy(policy)
```

#### 2. Create Training Module
```python
from security.security_awareness_training import TrainingModule, TrainingModuleType

# Create a training module
module = TrainingModule(
    module_id="TRAIN-001",
    module_type=TrainingModuleType.SECURITY_BASICS,
    title="Security Fundamentals",
    description="Introduction to basic security concepts",
    content="# Security Fundamentals\n\n## What is Information Security?...",
    duration_minutes=30,
    difficulty_level="beginner",
    prerequisites=[],
    learning_objectives=[
        "Understand basic security concepts",
        "Identify common security threats",
        "Learn fundamental security practices"
    ],
    quiz_questions=[
        {
            "question": "What does the 'C' in CIA triad stand for?",
            "options": ["Confidentiality", "Control", "Compliance", "Confidence"],
            "correct_answer": 0,
            "explanation": "Confidentiality ensures information is accessible only to authorized users."
        }
    ],
    passing_score=80,
    created_by="security_team"
)

# Save the module
success = training_system.create_training_module(module)
```

#### 3. Assign Training to User
```python
from datetime import datetime, timedelta

# Assign training with due date
due_date = datetime.utcnow() + timedelta(days=30)
success = training_system.assign_training_to_user(
    user_id="user123",
    module_id="TRAIN-001",
    due_date=due_date
)
```

#### 4. Acknowledge Policy
```python
# Record policy acknowledgment
success = training_system.acknowledge_policy(
    user_id="user123",
    policy_id="POL-001",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)
```

#### 5. Get User Training Status
```python
# Get comprehensive training status
status = training_system.get_user_training_status("user123")

print(f"Completion Rate: {status['completion_percentage']}%")
print(f"Completed Trainings: {status['completed_count']}")
print(f"Overdue Trainings: {status['overdue_count']}")
print(f"Compliance Status: {status['compliance_status']}")
```

#### 6. Generate Training Report
```python
# Generate comprehensive report
report = training_system.generate_training_report(
    user_id="user123",
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow()
)

print(f"Training Statistics: {report['training_statistics']}")
print(f"Policy Statistics: {report['policy_statistics']}")
print(f"Campaign Statistics: {report['campaign_statistics']}")
```

### REST API Usage

#### 1. Get All Policies
```bash
curl -X GET "http://localhost:5000/api/security-awareness/policies" \
  -H "Content-Type: application/json"
```

#### 2. Create New Policy
```bash
curl -X POST "http://localhost:5000/api/security-awareness/policies" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_type": "acceptable_use",
    "title": "New Acceptable Use Policy",
    "description": "Updated acceptable use policy",
    "content": "# New Policy Content...",
    "version": "2.0",
    "effective_date": "2024-01-01T00:00:00",
    "review_date": "2025-01-01T00:00:00",
    "applicable_to": ["all_users"],
    "compliance_requirements": ["GDPR"],
    "created_by": "admin"
  }'
```

#### 3. Acknowledge Policy
```bash
curl -X POST "http://localhost:5000/api/security-awareness/policies/POL-001/acknowledge" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123"
  }'
```

#### 4. Get Training Modules
```bash
curl -X GET "http://localhost:5000/api/security-awareness/training/modules" \
  -H "Content-Type: application/json"
```

#### 5. Assign Training
```bash
curl -X POST "http://localhost:5000/api/security-awareness/training/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "module_id": "TRAIN-001",
    "due_date": "2024-02-01T00:00:00"
  }'
```

#### 6. Get User Training Status
```bash
curl -X GET "http://localhost:5000/api/security-awareness/training/status/user123" \
  -H "Content-Type: application/json"
```

#### 7. Get Dashboard Data
```bash
curl -X GET "http://localhost:5000/api/security-awareness/dashboard?user_id=user123" \
  -H "Content-Type: application/json"
```

#### 8. Generate Training Report
```bash
curl -X GET "http://localhost:5000/api/security-awareness/reports/training?user_id=user123" \
  -H "Content-Type: application/json"
```

## Web Interface

### Policy Viewing
Access policies through the web interface:
```
http://localhost:5000/api/security-awareness/policies/{policy_id}/view
```

### Training Module Interface
Access training modules through the web interface:
```
http://localhost:5000/api/security-awareness/training/modules/{module_id}/view
```

## Database Schema

### Security Policies Table
```sql
CREATE TABLE security_policies (
    policy_id TEXT PRIMARY KEY,
    policy_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    review_date TEXT NOT NULL,
    applicable_to TEXT,
    compliance_requirements TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    requires_acknowledgment BOOLEAN DEFAULT 1,
    acknowledgment_deadline TEXT
);
```

### Training Modules Table
```sql
CREATE TABLE training_modules (
    module_id TEXT PRIMARY KEY,
    module_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    difficulty_level TEXT NOT NULL,
    prerequisites TEXT,
    learning_objectives TEXT,
    quiz_questions TEXT,
    passing_score INTEGER DEFAULT 80,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    tags TEXT
);
```

### User Training Records Table
```sql
CREATE TABLE user_training_records (
    record_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    status TEXT NOT NULL,
    start_date TEXT,
    completion_date TEXT,
    score INTEGER,
    attempts INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    certificate_issued BOOLEAN DEFAULT 0,
    certificate_id TEXT,
    expires_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Policy Acknowledgments Table
```sql
CREATE TABLE policy_acknowledgments (
    acknowledgment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    acknowledged_at TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    acknowledgment_text TEXT,
    created_at TEXT NOT NULL
);
```

### Awareness Campaigns Table
```sql
CREATE TABLE awareness_campaigns (
    campaign_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    campaign_type TEXT NOT NULL,
    target_audience TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    content TEXT,
    success_metrics TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1
);
```

## Security Features

### Data Protection
- **Encryption**: All sensitive data is encrypted at rest
- **Access Controls**: Role-based access to policies and training
- **Audit Logging**: Complete audit trail for all actions
- **Data Retention**: Configurable data retention policies

### Compliance Features
- **GDPR Compliance**: Data subject rights and consent management
- **PCI DSS**: Payment card industry compliance
- **HIPAA**: Health information privacy compliance
- **SOX**: Sarbanes-Oxley compliance

### Authentication & Authorization
- **User Authentication**: Secure user authentication
- **Role-Based Access**: Different access levels for different roles
- **Session Management**: Secure session handling
- **Multi-Factor Authentication**: Support for MFA

## Monitoring & Alerting

### Training Compliance Alerts
- **Overdue Training**: Alerts for overdue training assignments
- **Policy Acknowledgment**: Reminders for unacknowledged policies
- **Completion Rates**: Low completion rate alerts
- **Compliance Status**: Non-compliance alerts

### System Health Monitoring
- **Database Health**: Monitor database connectivity and performance
- **API Health**: Monitor API endpoint availability
- **User Activity**: Track user engagement and activity patterns

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
**Problem**: Unable to connect to the training database
**Solution**: 
- Verify database file permissions
- Check database path configuration
- Ensure SQLite is properly installed

#### 2. Policy Acknowledgment Failures
**Problem**: Policy acknowledgments not being recorded
**Solution**:
- Check user authentication
- Verify policy exists and is active
- Check database write permissions

#### 3. Training Module Loading Issues
**Problem**: Training modules not loading properly
**Solution**:
- Verify module content format
- Check module activation status
- Validate quiz question format

#### 4. Certificate Generation Failures
**Problem**: Certificates not being generated
**Solution**:
- Check user completion status
- Verify passing score requirements
- Check certificate template configuration

### Performance Optimization

#### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_user_training_user_id ON user_training_records(user_id);
CREATE INDEX idx_user_training_module_id ON user_training_records(module_id);
CREATE INDEX idx_policy_ack_user_id ON policy_acknowledgments(user_id);
CREATE INDEX idx_policy_ack_policy_id ON policy_acknowledgments(policy_id);
```

#### 2. Caching Strategy
```python
# Implement caching for frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_policies(user_role):
    return training_system.get_security_policies(user_role=user_role)
```

#### 3. Batch Operations
```python
# Batch policy acknowledgments for better performance
def batch_acknowledge_policies(user_id, policy_ids):
    for policy_id in policy_ids:
        training_system.acknowledge_policy(user_id, policy_id)
```

## Best Practices

### Policy Management
1. **Regular Reviews**: Schedule regular policy reviews
2. **Version Control**: Maintain clear version history
3. **User Communication**: Clearly communicate policy changes
4. **Compliance Mapping**: Map policies to compliance requirements

### Training Development
1. **Clear Objectives**: Define clear learning objectives
2. **Engaging Content**: Create interactive and engaging content
3. **Regular Updates**: Keep training content current
4. **Assessment Design**: Design effective assessments

### User Engagement
1. **Gamification**: Use gamification elements to increase engagement
2. **Progress Tracking**: Provide clear progress indicators
3. **Recognition**: Recognize and reward completion
4. **Communication**: Regular communication about training requirements

### Compliance Management
1. **Regular Audits**: Conduct regular compliance audits
2. **Documentation**: Maintain comprehensive documentation
3. **Training Records**: Keep detailed training records
4. **Incident Response**: Have clear incident response procedures

## Integration Examples

### Integration with HR System
```python
# Sync user data with HR system
def sync_hr_users():
    hr_users = hr_system.get_active_users()
    for user in hr_users:
        # Assign required training based on role
        required_modules = get_required_modules(user.role)
        for module in required_modules:
            training_system.assign_training_to_user(user.id, module.id)
```

### Integration with Learning Management System
```python
# Export training data to LMS
def export_to_lms():
    training_records = training_system.get_all_training_records()
    lms_system.import_training_data(training_records)
```

### Integration with Compliance System
```python
# Report compliance status
def report_compliance():
    compliance_data = {
        'policy_acknowledgments': training_system.get_policy_acknowledgments(),
        'training_completions': training_system.get_training_completions(),
        'compliance_scores': training_system.calculate_compliance_scores()
    }
    compliance_system.update_compliance_status(compliance_data)
```

## Support & Maintenance

### Regular Maintenance Tasks
1. **Database Maintenance**: Regular database optimization
2. **Content Updates**: Regular content review and updates
3. **Security Updates**: Regular security patches and updates
4. **Performance Monitoring**: Regular performance monitoring

### Support Resources
- **Documentation**: Comprehensive documentation and guides
- **Training Materials**: User training materials and tutorials
- **Support Team**: Dedicated support team for assistance
- **Community Forum**: User community for sharing best practices

## Conclusion

The Security Awareness and Training System provides a comprehensive solution for managing security education and policy compliance in the MINGUS application. With its robust features, flexible configuration, and extensive integration capabilities, it ensures that all users are properly trained and compliant with security policies.

For additional support or questions, please refer to the comprehensive documentation or contact the security team. 