# Mingus Application - Database Production Planning Summary

**Generated:** January 2025  
**Application:** Personal Finance & Wellness Platform  
**Database:** SQLite (Development) / PostgreSQL (Production)  
**ORM:** SQLAlchemy with declarative models  

---

## 📋 Table of Contents

1. [Complete Database Schema Export](#complete-database-schema-export)
2. [Sample Data Structure (Anonymized)](#sample-data-structure-anonymized)
3. [Database Operations Analysis](#database-operations-analysis)
4. [Current Database Configuration](#current-database-configuration)
5. [Production Readiness Assessment](#production-readiness-assessment)
6. [Migration Strategy](#migration-strategy)
7. [Performance Optimization Recommendations](#performance-optimization-recommendations)

---

## 🗄️ Complete Database Schema Export

### **Database Overview**
- **Current Size:** 221KB (SQLite)
- **Tables:** 13 tables
- **Indexes:** 35 indexes
- **Views:** 2 views (suspicious_ips, user_security_summary)
- **Total Records:** 0 (empty database ready for production)

### **Complete Schema DDL**

```sql
-- Core User Tables
CREATE TABLE users (
    id INTEGER NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    full_name VARCHAR(255), 
    phone_number VARCHAR(50), 
    is_active BOOLEAN, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE user_profiles (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    monthly_income FLOAT, 
    income_frequency VARCHAR(50), 
    primary_income_source VARCHAR(100), 
    secondary_income_source VARCHAR(100), 
    primary_goal VARCHAR(100), 
    goal_amount FLOAT, 
    goal_timeline_months INTEGER, 
    age_range VARCHAR(50), 
    location_state VARCHAR(50), 
    location_city VARCHAR(100), 
    household_size INTEGER, 
    employment_status VARCHAR(50), 
    current_savings FLOAT, 
    current_debt FLOAT, 
    credit_score_range VARCHAR(50), 
    risk_tolerance VARCHAR(50), 
    investment_experience VARCHAR(50), 
    created_at DATETIME, 
    updated_at DATETIME, 
    is_complete BOOLEAN, 
    PRIMARY KEY (id), 
    UNIQUE (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Onboarding & Progress Tracking
CREATE TABLE onboarding_progress (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    current_step VARCHAR(100), 
    total_steps INTEGER, 
    completed_steps INTEGER, 
    step_status VARCHAR, 
    started_at DATETIME, 
    completed_at DATETIME, 
    last_activity DATETIME, 
    is_complete BOOLEAN, 
    completion_percentage INTEGER, 
    questionnaire_responses TEXT, 
    PRIMARY KEY (id), 
    UNIQUE (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Health & Wellness Data
CREATE TABLE user_health_checkins (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    checkin_date DATETIME NOT NULL, 
    sleep_hours FLOAT, 
    physical_activity_minutes INTEGER, 
    physical_activity_level VARCHAR(50), 
    relationships_rating INTEGER, 
    relationships_notes VARCHAR(500), 
    mindfulness_minutes INTEGER, 
    mindfulness_type VARCHAR(100), 
    stress_level INTEGER, 
    energy_level INTEGER, 
    mood_rating INTEGER, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_user_weekly_checkin UNIQUE (user_id, checkin_date), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Health-Spending Correlations
CREATE TABLE health_spending_correlations (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    analysis_period VARCHAR(50) NOT NULL, 
    analysis_start_date DATETIME NOT NULL, 
    analysis_end_date DATETIME NOT NULL, 
    health_metric VARCHAR(100) NOT NULL, 
    spending_category VARCHAR(100) NOT NULL, 
    correlation_strength FLOAT NOT NULL, 
    correlation_direction VARCHAR(20) NOT NULL, 
    sample_size INTEGER NOT NULL, 
    p_value FLOAT, 
    confidence_interval_lower FLOAT, 
    confidence_interval_upper FLOAT, 
    insight_text VARCHAR(1000), 
    recommendation_text VARCHAR(1000), 
    actionable_insight BOOLEAN, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Verification & Security
CREATE TABLE verification_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE phone_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phone_number TEXT NOT NULL,
    verification_code_hash TEXT NOT NULL,
    code_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    code_expires_at DATETIME NOT NULL,
    attempts INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    resend_count INTEGER DEFAULT 0,
    last_attempt_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    salt TEXT, 
    ip_address TEXT, 
    user_agent TEXT, 
    captcha_verified BOOLEAN DEFAULT FALSE, 
    risk_score REAL DEFAULT 0.0
);

CREATE TABLE verification_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    phone_number TEXT,
    event_type TEXT NOT NULL,
    event_details TEXT,
    risk_score REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Financial Data
CREATE TABLE financial_questionnaire_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    monthly_income FLOAT,
    monthly_expenses FLOAT,
    current_savings FLOAT,
    total_debt FLOAT,
    risk_tolerance INTEGER,
    financial_goals JSON,
    financial_health_score INTEGER,
    financial_health_level VARCHAR(50),
    recommendations JSON,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Preferences & Reminders
CREATE TABLE reminder_schedules (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    reminder_type VARCHAR(50) NOT NULL, 
    scheduled_date DATETIME NOT NULL, 
    frequency VARCHAR(20), 
    enabled BOOLEAN, 
    preferences JSON, 
    message TEXT, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE user_preferences (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    email_notifications BOOLEAN, 
    push_notifications BOOLEAN, 
    sms_notifications BOOLEAN, 
    reminder_preferences JSON, 
    preferred_communication VARCHAR(20), 
    communication_frequency VARCHAR(20), 
    share_anonymized_data BOOLEAN, 
    allow_marketing_emails BOOLEAN, 
    theme_preference VARCHAR(20), 
    language_preference VARCHAR(10), 
    onboarding_completed BOOLEAN, 
    first_checkin_scheduled BOOLEAN, 
    mobile_app_downloaded BOOLEAN, 
    custom_preferences JSON, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    PRIMARY KEY (id), 
    UNIQUE (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

-- System Tables
CREATE TABLE migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sqlite_sequence(name,seq);

-- Indexes (35 total)
CREATE INDEX idx_user_health_checkin_date_range ON user_health_checkins (user_id, checkin_date);
CREATE INDEX ix_user_health_checkins_user_id ON user_health_checkins (user_id);
CREATE INDEX idx_health_metrics ON user_health_checkins (stress_level, energy_level, mood_rating);
CREATE INDEX ix_user_health_checkins_checkin_date ON user_health_checkins (checkin_date);
CREATE INDEX idx_analysis_date_range ON health_spending_correlations (analysis_start_date, analysis_end_date);
CREATE INDEX idx_correlation_strength ON health_spending_correlations (correlation_strength);
CREATE INDEX idx_actionable_insights ON health_spending_correlations (actionable_insight, correlation_strength);
CREATE INDEX idx_user_period_metric ON health_spending_correlations (user_id, analysis_period, health_metric, spending_category);
CREATE INDEX ix_health_spending_correlations_user_id ON health_spending_correlations (user_id);
CREATE INDEX idx_verification_analytics_user_id ON verification_analytics(user_id);
CREATE INDEX idx_verification_analytics_event_type ON verification_analytics(event_type);
CREATE INDEX idx_verification_analytics_created_at ON verification_analytics(created_at);
CREATE INDEX idx_phone_verification_user_id ON phone_verification(user_id);
CREATE INDEX idx_phone_verification_phone_number ON phone_verification(phone_number);
CREATE INDEX idx_phone_verification_status ON phone_verification(status);
CREATE INDEX idx_phone_verification_created_at ON phone_verification(created_at);
CREATE INDEX idx_phone_verification_user_phone ON phone_verification(user_id, phone_number);
CREATE INDEX idx_phone_verification_resend_count ON phone_verification(resend_count);
CREATE INDEX idx_phone_verification_user_phone_resend ON phone_verification(user_id, phone_number, resend_count);
CREATE INDEX idx_verification_audit_user_id ON verification_audit_log(user_id);
CREATE INDEX idx_verification_audit_ip_address ON verification_audit_log(ip_address);
CREATE INDEX idx_verification_audit_event_type ON verification_audit_log(event_type);
CREATE INDEX idx_verification_audit_created_at ON verification_audit_log(created_at);
CREATE INDEX idx_verification_audit_risk_score ON verification_audit_log(risk_score);
CREATE INDEX idx_verification_audit_user_ip ON verification_audit_log(user_id, ip_address);
CREATE INDEX idx_phone_verification_ip_address ON phone_verification(ip_address);
CREATE INDEX idx_phone_verification_risk_score ON phone_verification(risk_score);
CREATE INDEX idx_phone_verification_captcha_verified ON phone_verification(captcha_verified);
CREATE INDEX idx_fqs_user_id ON financial_questionnaire_submissions(user_id);

-- Views
CREATE VIEW suspicious_ips AS
SELECT 
    ip_address,
    COUNT(*) as total_events,
    COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as failed_attempts,
    COUNT(CASE WHEN event_type = 'rate_limit_exceeded' THEN 1 END) as rate_limit_violations,
    AVG(risk_score) as avg_risk_score,
    MAX(created_at) as last_activity
FROM verification_audit_log 
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY ip_address
HAVING COUNT(*) > 10 OR AVG(risk_score) > 0.6
ORDER BY avg_risk_score DESC;

CREATE VIEW user_security_summary AS
SELECT 
    user_id,
    COUNT(*) as total_verifications,
    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_verifications,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT phone_number) as unique_phones,
    MAX(created_at) as last_verification,
    AVG(risk_score) as avg_risk_score
FROM phone_verification 
GROUP BY user_id;
```

---

## 📊 Sample Data Structure (Anonymized)

### **User Account Example**
```json
{
  "id": 1001,
  "email": "user@example.com",
  "password_hash": "pbkdf2:sha256:600000$...",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### **User Profile Example**
```json
{
  "id": 1001,
  "user_id": 1001,
  "monthly_income": 7500.00,
  "income_frequency": "monthly",
  "primary_income_source": "salary",
  "secondary_income_source": "freelance",
  "primary_goal": "emergency_fund",
  "goal_amount": 15000.00,
  "goal_timeline_months": 12,
  "age_range": "25-34",
  "location_state": "CA",
  "location_city": "San Francisco",
  "household_size": 2,
  "employment_status": "full_time",
  "current_savings": 5000.00,
  "current_debt": 25000.00,
  "credit_score_range": "700-749",
  "risk_tolerance": "moderate",
  "investment_experience": "beginner",
  "is_complete": true
}
```

### **Health Check-in Example**
```json
{
  "id": 5001,
  "user_id": 1001,
  "checkin_date": "2025-01-15T08:00:00Z",
  "sleep_hours": 7.5,
  "physical_activity_minutes": 45,
  "physical_activity_level": "moderate",
  "relationships_rating": 8,
  "relationships_notes": "Had dinner with family",
  "mindfulness_minutes": 15,
  "mindfulness_type": "meditation",
  "stress_level": 4,
  "energy_level": 7,
  "mood_rating": 8
}
```

### **Financial Questionnaire Example**
```json
{
  "id": 2001,
  "user_id": 1001,
  "monthly_income": 7500.00,
  "monthly_expenses": 4500.00,
  "current_savings": 5000.00,
  "total_debt": 25000.00,
  "risk_tolerance": 6,
  "financial_goals": {
    "emergency_fund": 15000,
    "retirement": 1000000,
    "vacation": 5000
  },
  "financial_health_score": 72,
  "financial_health_level": "good",
  "recommendations": {
    "priority": "build_emergency_fund",
    "monthly_savings_target": 1250,
    "debt_payoff_strategy": "avalanche_method"
  }
}
```

### **Phone Verification Example**
```json
{
  "id": 3001,
  "user_id": 1001,
  "phone_number": "+1234567890",
  "verification_code_hash": "pbkdf2:sha256:600000$...",
  "code_sent_at": "2025-01-15T10:30:00Z",
  "code_expires_at": "2025-01-15T10:35:00Z",
  "attempts": 0,
  "status": "pending",
  "resend_count": 0,
  "risk_score": 0.1,
  "captcha_verified": true
}
```

---

## 🔍 Database Operations Analysis

### **Primary Database Operations by Category**

#### **1. User Authentication & Management**
```python
# User Registration
session.add(User(email=email, password_hash=hashed_password))
session.commit()

# User Login
user = session.query(User).filter(
    User.email == email.lower(),
    User.is_active == True
).first()

# Password Verification
if check_password_hash(user.password_hash, password):
    return user_data
```

#### **2. Profile Management**
```python
# Create User Profile
profile = UserProfile(
    user_id=user_id,
    monthly_income=income,
    primary_goal=goal,
    # ... other fields
)
session.add(profile)
session.commit()

# Get User Profile
profile = session.query(UserProfile).filter_by(user_id=user_id).first()
```

#### **3. Health Data Operations**
```python
# Create Health Check-in
checkin = UserHealthCheckin(
    user_id=user_id,
    checkin_date=date,
    sleep_hours=sleep,
    stress_level=stress,
    # ... other metrics
)
session.add(checkin)
session.commit()

# Get Health History
checkins = session.query(UserHealthCheckin).filter(
    UserHealthCheckin.user_id == user_id
).order_by(UserHealthCheckin.checkin_date.desc()).all()
```

#### **4. Financial Data Operations**
```python
# Submit Financial Questionnaire
submission = FinancialQuestionnaireSubmission(
    user_id=user_id,
    monthly_income=income,
    monthly_expenses=expenses,
    financial_goals=goals_json,
    # ... other fields
)
session.add(submission)
session.commit()

# Get Financial History
submissions = session.query(FinancialQuestionnaireSubmission).filter(
    FinancialQuestionnaireSubmission.user_id == user_id
).order_by(FinancialQuestionnaireSubmission.submitted_at.desc()).all()
```

#### **5. Onboarding Progress Tracking**
```python
# Update Onboarding Progress
progress = session.query(OnboardingProgress).filter_by(user_id=user_id).first()
progress.completed_steps += 1
progress.completion_percentage = (progress.completed_steps / progress.total_steps) * 100
session.commit()
```

#### **6. Phone Verification Operations**
```python
# Create Verification Record
verification = PhoneVerification(
    user_id=user_id,
    phone_number=phone,
    verification_code_hash=hashed_code,
    code_expires_at=expiry_time
)
session.add(verification)
session.commit()

# Verify Code
verification = session.query(PhoneVerification).filter(
    PhoneVerification.user_id == user_id,
    PhoneVerification.status == 'pending'
).first()
```

#### **7. Security & Audit Operations**
```python
# Log Security Event
audit_log = VerificationAuditLog(
    user_id=user_id,
    ip_address=ip,
    event_type=event_type,
    risk_score=risk_score
)
session.add(audit_log)
session.commit()

# Get Suspicious Activity
suspicious_ips = session.execute(text("SELECT * FROM suspicious_ips")).fetchall()
```

### **Complex Operations**

#### **Financial Forecasting (Performance Critical)**
```python
# 365-day cashflow calculation
for date in date_range:  # 365 iterations
    daily_transactions = {}
    # Complex calculations for each day
    # Multiple database calls per user
    # Memory-intensive operations
```

#### **Health-Spending Correlation Analysis**
```python
# Correlation analysis between health metrics and spending
correlations = session.query(HealthSpendingCorrelation).filter(
    HealthSpendingCorrelation.user_id == user_id,
    HealthSpendingCorrelation.analysis_period == period
).all()
```

---

## ⚙️ Current Database Configuration

### **Development Configuration (`config/development.py`)**
```python
# Database Settings
DATABASE_URL = "sqlite:///instance/mingus.db"
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
CREATE_TABLES = True

# Connection Pooling (SQLite - No pooling)
# No pool_size, max_overflow settings for SQLite

# Security Settings (Development)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
WTF_CSRF_ENABLED = False
BYPASS_AUTH = True

# Logging
LOG_LEVEL = 'DEBUG'
```

### **Production Configuration (`config/production.py`)**
```python
# Database Settings
DATABASE_URL = os.environ.get('DATABASE_URL')  # Must be PostgreSQL
CREATE_TABLES = False

# Connection Pooling (PostgreSQL)
DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))

# Security Settings (Production)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
WTF_CSRF_ENABLED = True
BYPASS_AUTH = False

# Rate Limiting
RATELIMIT_ENABLED = True
RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0')

# Caching
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/1')
```

### **Base Configuration (`config/base.py`)**
```python
# Core Settings
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
DEBUG = False
TESTING = False

# Database Settings
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mingus')
DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))
CREATE_TABLES = True

# Session Settings
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_MAX_AGE = 3600
```

---

## 🚨 Production Readiness Assessment

### **Critical Security Issues**

#### **1. Hard-coded Secrets (CRITICAL)**
```python
# config/development.py - REMOVE THESE
SUPABASE_URL = "https://wiemjrvxlqkpbsukdqnb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_JWT_SECRET = "counJW9WSebZaLdlxu2e8+OBsrvgXNYcgsHravbNQrQKy6i/uyfFAL0Ne9QozcrosrXuzbudxltljMCWKpB9hg=="
```

**Action Required:** Move all secrets to environment variables

#### **2. Development Security Settings**
```python
# config/development.py - DISABLE IN PRODUCTION
BYPASS_AUTH = True  # Auth bypass enabled
WTF_CSRF_ENABLED = False  # CSRF protection disabled
SESSION_COOKIE_SECURE = False  # Non-secure cookies
```

**Action Required:** Ensure production uses secure settings

### **Database Migration Requirements**

#### **1. SQLite to PostgreSQL Migration**
- **Current:** SQLite with 221KB database
- **Target:** PostgreSQL with proper connection pooling
- **Data Volume:** 0 records (fresh migration)

#### **2. Schema Compatibility**
- **SQLite Features:** AUTOINCREMENT, BOOLEAN
- **PostgreSQL Features:** SERIAL, BOOLEAN (compatible)
- **JSON Support:** Both support JSON fields

### **Performance Considerations**

#### **1. Missing Indexes**
```sql
-- Critical missing indexes for production
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_onboarding_progress_user_id ON onboarding_progress(user_id);
CREATE INDEX idx_reminder_schedules_user_due ON reminder_schedules(user_id, scheduled_date);
CREATE INDEX idx_financial_submissions_user_date ON financial_questionnaire_submissions(user_id, submitted_at);
```

#### **2. N+1 Query Problems**
- User dashboard loading (multiple separate queries)
- Health summary queries (potential N+1)
- Verification analytics (multiple user queries)

#### **3. Memory-Intensive Operations**
- 365-day financial forecasting calculations
- Large dataset correlation analysis
- Bulk data processing operations

---

## 🔄 Migration Strategy

### **Phase 1: Environment Setup**
```bash
# 1. Set up PostgreSQL database
createdb mingus_production

# 2. Configure environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/mingus_production"
export SECRET_KEY="your-secure-secret-key"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export SUPABASE_JWT_SECRET="your-jwt-secret"
```

### **Phase 2: Schema Migration**
```python
# 1. Create migration script
from sqlalchemy import create_engine, text
from alembic import command, config

# 2. Initialize Alembic
alembic init migrations

# 3. Generate migration
alembic revision --autogenerate -m "Initial migration"

# 4. Apply migration
alembic upgrade head
```

### **Phase 3: Data Migration (if needed)**
```python
# Since database is empty, no data migration required
# For future reference:
def migrate_sqlite_to_postgres():
    # Export from SQLite
    sqlite_engine = create_engine('sqlite:///instance/mingus.db')
    
    # Import to PostgreSQL
    pg_engine = create_engine(os.environ.get('DATABASE_URL'))
    
    # Migrate each table
    for table_name in ['users', 'user_profiles', ...]:
        data = sqlite_engine.execute(f"SELECT * FROM {table_name}").fetchall()
        # Insert into PostgreSQL
```

### **Phase 4: Application Deployment**
```python
# 1. Update configuration
class ProductionConfig(Config):
    DATABASE_URL = os.environ.get('DATABASE_URL')
    CREATE_TABLES = False  # Use migrations instead
    BYPASS_AUTH = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True

# 2. Test database connection
def test_production_db():
    engine = create_engine(os.environ.get('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
```

---

## ⚡ Performance Optimization Recommendations

### **1. Database Indexes (Immediate)**
```sql
-- Add missing indexes for production
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_onboarding_progress_user_id ON onboarding_progress(user_id);
CREATE INDEX idx_reminder_schedules_user_due ON reminder_schedules(user_id, scheduled_date);
CREATE INDEX idx_financial_submissions_user_date ON financial_questionnaire_submissions(user_id, submitted_at);
CREATE INDEX idx_health_checkins_user_date ON user_health_checkins(user_id, checkin_date);
CREATE INDEX idx_verification_analytics_user_date ON verification_analytics(user_id, created_at);
```

### **2. Query Optimization (High Priority)**
```python
# Fix N+1 queries with eager loading
from sqlalchemy.orm import joinedload

# Before (N+1 problem)
users = session.query(User).all()
for user in users:
    profile = session.query(UserProfile).filter_by(user_id=user.id).first()

# After (single query with joins)
users = session.query(User).options(
    joinedload(User.profile),
    joinedload(User.onboarding_progress)
).all()
```

### **3. Connection Pooling (Production)**
```python
# PostgreSQL connection pooling
engine = create_engine(
    database_url,
    pool_size=20,  # Increased for production
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=1800,  # 30 minutes
    pool_timeout=30
)
```

### **4. Caching Strategy (Medium Priority)**
```python
# Redis caching for frequently accessed data
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('CACHE_REDIS_URL')
})

@cache.memoize(timeout=300)  # 5 minutes
def get_user_profile(user_id):
    return session.query(UserProfile).filter_by(user_id=user_id).first()
```

### **5. Background Processing (High Priority)**
```python
# Move heavy operations to background tasks
from celery import Celery

@celery.task
def calculate_financial_forecast(user_id):
    # 365-day calculation in background
    pass

@celery.task
def analyze_health_correlations(user_id):
    # Correlation analysis in background
    pass
```

### **6. Database Partitioning (Future)**
```sql
-- Partition health checkins by date for large datasets
CREATE TABLE user_health_checkins_2025_01 PARTITION OF user_health_checkins
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

---

## 📈 Scalability Projections

### **Data Growth Estimates**
- **Users:** 1,000 users = ~50MB
- **Health Check-ins:** 1,000 users × 52 weeks = 52,000 records = ~25MB
- **Financial Data:** 1,000 users × 12 months = 12,000 records = ~15MB
- **Total at 1,000 users:** ~100MB

### **Performance Benchmarks**
- **Current:** 0 users, 221KB database
- **1,000 users:** ~100MB, should perform well
- **10,000 users:** ~1GB, may need optimization
- **100,000 users:** ~10GB, requires significant optimization

### **Resource Requirements**
- **Database:** PostgreSQL 13+ with 2GB RAM minimum
- **Connection Pool:** 20-50 connections
- **Caching:** Redis with 1GB RAM
- **Background Processing:** Celery with Redis backend

---

## ✅ Production Checklist

### **Security**
- [ ] Remove hard-coded secrets from configuration
- [ ] Enable CSRF protection
- [ ] Disable auth bypass
- [ ] Enable secure cookies
- [ ] Configure rate limiting
- [ ] Set up SSL/TLS certificates

### **Database**
- [ ] Migrate to PostgreSQL
- [ ] Set up connection pooling
- [ ] Add missing indexes
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Test migration scripts

### **Performance**
- [ ] Fix N+1 queries
- [ ] Implement caching
- [ ] Set up background processing
- [ ] Optimize heavy calculations
- [ ] Configure load balancing

### **Monitoring**
- [ ] Set up database monitoring
- [ ] Configure application logging
- [ ] Set up error tracking
- [ ] Monitor performance metrics
- [ ] Set up alerting

---

## 📞 Support & Next Steps

### **Immediate Actions Required**
1. **Security:** Remove hard-coded secrets immediately
2. **Database:** Set up PostgreSQL and migrate schema
3. **Performance:** Add missing indexes and fix N+1 queries
4. **Monitoring:** Set up basic monitoring and alerting

### **Recommended Timeline**
- **Week 1:** Security fixes and PostgreSQL setup
- **Week 2:** Schema migration and testing
- **Week 3:** Performance optimization
- **Week 4:** Monitoring and production deployment

### **Contact Information**
- **Database Admin:** [Your contact info]
- **DevOps Team:** [Your contact info]
- **Security Team:** [Your contact info]

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** February 2025  
**Status:** Ready for Production Planning 