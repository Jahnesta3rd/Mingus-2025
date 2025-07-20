# Mingus Application Database Interaction Analysis

**Generated:** January 2025  
**Application Type:** Personal Finance & Wellness Platform  
**Database:** SQLite (Development) / PostgreSQL (Production)  
**ORM:** SQLAlchemy with declarative models  

---

## 📋 Table of Contents

1. [ORM & Database Library Usage](#orm--database-library-usage)
2. [Database Queries Analysis](#database-queries-analysis)
3. [User Registration & Authentication](#user-registration--authentication)
4. [Financial Calculations & Forecasting](#financial-calculations--forecasting)
5. [Hard-coded Database Connections](#hard-coded-database-connections)
6. [Security Vulnerabilities](#security-vulnerabilities)
7. [Performance Considerations](#performance-considerations)
8. [Recommendations](#recommendations)

---

## 🔧 1. ORM & Database Library Usage

### **Primary ORM: SQLAlchemy**
Your application uses **SQLAlchemy** as the primary ORM with the following setup:

```python
# Shared Base for all models
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Database engine configuration
engine = create_engine('sqlite:///instance/mingus.db', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### **Key Database Libraries:**
- **SQLAlchemy 1.4+** - Primary ORM
- **Werkzeug** - Password hashing (`generate_password_hash`, `check_password_hash`)
- **Cryptography** - Field-level encryption for financial data
- **Supabase** - External database service (backup/alternative)

### **Model Structure:**
```python
# Example User model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # ... other fields
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    onboarding_progress = relationship("OnboardingProgress", back_populates="user")
```

---

## 🔍 2. Database Queries Analysis

### **Most Common Query Patterns:**

#### **User Authentication Queries:**
```python
# Find user by email
user = session.query(User).filter(
    User.email == email.lower(),
    User.is_active == True
).first()

# Password verification
if check_password_hash(user.password_hash, password):
    return user_data
```

#### **User Profile Queries:**
```python
# Get user profile with relationships
profile = session.query(UserProfile).filter(
    UserProfile.user_id == user_id
).first()

# Create user profile
new_profile = UserProfile(
    user_id=user_id,
    monthly_income=income,
    # ... other fields
)
session.add(new_profile)
session.commit()
```

#### **Financial Data Queries:**
```python
# Get financial questionnaire submissions
submissions = session.query(FinancialQuestionnaireSubmission).filter(
    FinancialQuestionnaireSubmission.user_id == user_id
).all()

# Get health checkins
checkins = session.query(UserHealthCheckin).filter(
    UserHealthCheckin.user_id == user_id
).order_by(UserHealthCheckin.checkin_date.desc()).all()
```

#### **Complex Financial Calculations:**
```python
# Daily cashflow calculation (365 days)
def calculate_daily_cashflow(user_id: str, initial_balance: float):
    # Fetch financial profile
    profile_resp = supabase.table('user_financial_profiles').select('*').eq('user_id', user_id).single().execute()
    
    # Fetch expense schedules
    expense_response = supabase.table('user_expense_due_dates').select('*').eq('user_id', user_id).execute()
    
    # Calculate daily transactions for 365 days
    # ... complex calculation logic
```

---

## 🔐 3. User Registration & Authentication

### **Registration Flow:**
```python
# 1. Validate input data
email = user_data.get('email', '').strip().lower()
password = user_data.get('password', '')
full_name = user_data.get('full_name', '').strip()

# 2. Check if user exists
existing_user = self.get_user_by_email(email)
if existing_user:
    return None

# 3. Hash password
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# 4. Create user
new_user = User(
    email=email,
    password_hash=password_hash,
    full_name=full_name
)
session.add(new_user)
session.commit()
```

### **Authentication Flow:**
```python
# 1. Find user by email
user = session.query(User).filter(
    User.email == email.lower(),
    User.is_active == True
).first()

# 2. Verify password
if not check_password_hash(user.password_hash, password):
    return None

# 3. Return user data
return user.to_dict()
```

### **Security Features:**
- ✅ **Password Hashing:** Uses `pbkdf2:sha256` method
- ✅ **Email Validation:** Regex pattern validation
- ✅ **Password Strength:** Minimum 8 characters validation
- ✅ **Session Management:** Flask session with secure cookies
- ✅ **Account Status:** Active/inactive user tracking

---

## 💰 4. Financial Calculations & Forecasting

### **Cash Flow Analysis Service:**
```python
class CashFlowAnalysisService:
    def analyze_user_dates(self, user_id: str, important_dates: List[Dict], starting_balance: float, forecast: List[Dict]):
        # Sort dates chronologically
        important_dates = sorted(important_dates, key=lambda d: d['date'])
        
        # Calculate running balance
        running_balance = starting_balance
        for imp_date in important_dates:
            # Add forecast events up to this date
            for event in forecast:
                if event['date'] <= imp_date['date']:
                    running_balance += event.get('amount', 0)
            
            # Subtract important date expense
            running_balance -= imp_date.get('amount', 0)
            
            # Determine coverage status
            if running_balance >= imp_date.get('amount', 0):
                status = 'green'
            elif running_balance >= 0.5 * imp_date.get('amount', 0):
                status = 'yellow'
            else:
                status = 'red'
```

### **Daily Cash Flow Calculation:**
```python
def calculate_daily_cashflow(user_id: str, initial_balance: float, start_date: str = None):
    # Calculate for 365 days
    end_date = current_date + timedelta(days=365)
    
    # Convert income to daily amounts
    if income_frequency == 'monthly':
        daily_income = income / 30.44
    elif income_frequency == 'bi-weekly':
        daily_income = (income * 26) / 365
    
    # Build daily transactions dictionary
    daily_transactions = {}
    
    # Calculate running balance for each day
    running_balance = initial_balance
    for date in date_range:
        income = daily_transactions.get(date, {}).get('income', 0)
        expenses = daily_transactions.get(date, {}).get('expenses', 0)
        net_change = income - expenses
        running_balance += net_change
```

### **Financial Planning Integration:**
```python
class FinancialPlanningIntegration:
    def adjust_emergency_fund(self, user_id: int, risk_level: str):
        # Emergency fund multipliers based on job security risk
        multipliers = {
            'low': 3,      # 3 months of expenses
            'medium': 6,   # 6 months of expenses
            'high': 9,     # 9 months of expenses
            'very_high': 12 # 12 months of expenses
        }
        
        # Calculate recommended emergency fund
        monthly_expenses = self._get_monthly_expenses(user_id)
        recommended_fund = monthly_expenses * multipliers.get(risk_level, 6)
```

---

## ⚠️ 5. Hard-coded Database Connections

### **Critical Security Issues Found:**

#### **1. Hard-coded Supabase Credentials in Development Config:**
```python
# config/development.py - LINES 47-50
SUPABASE_URL = "https://wiemjrvxlqkpbsukdqnb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY3NTAxOTcsImV4cCI6MjA2MjMyNjE5N30.9AsxxhX4Nt4Qr3EZerYfpvo4doVPbxuZRMgNSgnapM8"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndpZW1qcnZ4bHFrcGJzdWtkcW5iIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc1MDE5NywiZXhwIjoyMDYyMzI2MTk3fQ.pzTybRahJYGjD_y2OrLnhpAX5xq-ylJbd7r4K5xNGCM"
SUPABASE_JWT_SECRET = "counJW9WSebZaLdlxu2e8+OBsrvgXNYcgsHravbNQrQKy6i/uyfFAL0Ne9QozcrosrXuzbudxltljMCWKpB9hg=="
```

#### **2. Hard-coded Database URLs in Backup Files:**
```python
# simple_app.py - LINE 30
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost/mingus_dev')

# examples/onboarding_service_integration.py - LINE 15
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://username:password@localhost/mingus_db')
```

#### **3. Development Secret Key:**
```python
# config/development.py - LINE 132
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
```

---

## 🚨 6. Security Vulnerabilities

### **Critical Issues:**

#### **1. Exposed API Keys & Secrets:**
- **Supabase API keys** hard-coded in development config
- **JWT secrets** exposed in source code
- **Service role keys** visible in configuration

#### **2. Weak Development Security:**
```python
# config/development.py
BYPASS_AUTH = True  # Auth bypass enabled
WTF_CSRF_ENABLED = False  # CSRF protection disabled
SESSION_COOKIE_SECURE = False  # Non-secure cookies
```

#### **3. Password Security:**
- ✅ **Good:** Using `pbkdf2:sha256` for hashing
- ⚠️ **Concern:** Password validation only requires 8 characters minimum

#### **4. Database Security:**
- ✅ **Good:** Field-level encryption for financial data
- ✅ **Good:** User data isolation with `user_id` foreign keys
- ⚠️ **Concern:** SQLite in development (no connection pooling)

---

## ⚡ 7. Performance Considerations

### **Database Performance Issues:**

#### **1. N+1 Query Problems:**
```python
# Potential N+1 issue in user profile loading
for user in users:
    profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    # This could result in many individual queries
```

#### **2. Large Dataset Operations:**
```python
# 365-day cashflow calculation loads all data into memory
daily_transactions = {}
for date in date_range:  # 365 iterations
    # Complex calculations for each day
    # Could be memory-intensive for large datasets
```

#### **3. Missing Database Indexes:**
- ✅ **Good:** Email field has unique index
- ⚠️ **Missing:** Date-based indexes for financial queries
- ⚠️ **Missing:** Composite indexes for user_id + date queries

#### **4. Connection Pooling:**
```python
# Development uses SQLite (no pooling)
engine = create_engine('sqlite:///instance/mingus.db')

# Production should use PostgreSQL with pooling
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## 📋 8. Recommendations

### **Immediate Actions Required:**

#### **1. Security Fixes:**
```python
# Move all secrets to environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production
```

#### **2. Database Optimization:**
```sql
-- Add missing indexes for performance
CREATE INDEX idx_user_health_checkins_user_date ON user_health_checkins(user_id, checkin_date);
CREATE INDEX idx_financial_submissions_user_date ON financial_questionnaire_submissions(user_id, submitted_at);
CREATE INDEX idx_reminder_schedules_user_due ON reminder_schedules(user_id, due_date);
```

#### **3. Query Optimization:**
```python
# Use eager loading to prevent N+1 queries
users = session.query(User).options(
    joinedload(User.profile),
    joinedload(User.onboarding_progress)
).all()

# Use bulk operations for large datasets
session.bulk_insert_mappings(DailyCashflow, cashflow_records)
```

#### **4. Production Database Setup:**
```python
# Use PostgreSQL in production with proper pooling
DATABASE_URL = os.environ.get('DATABASE_URL')  # Must be PostgreSQL URL
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=1800
)
```

#### **5. Security Hardening:**
```python
# Production security settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
WTF_CSRF_ENABLED = True
BYPASS_AUTH = False
```

---

## 📊 Summary

### **Strengths:**
- ✅ Well-structured SQLAlchemy models with relationships
- ✅ Proper password hashing and validation
- ✅ Field-level encryption for sensitive financial data
- ✅ Comprehensive financial calculation engine
- ✅ Good separation of concerns in services

### **Critical Issues:**
- 🚨 **Exposed API keys and secrets** in source code
- 🚨 **Weak development security** settings
- ⚠️ **Performance concerns** with large datasets
- ⚠️ **Missing database indexes** for common queries

### **Next Steps:**
1. **Immediately** move all secrets to environment variables
2. **Add missing database indexes** for performance
3. **Implement connection pooling** for production
4. **Add query optimization** to prevent N+1 problems
5. **Harden security settings** for production deployment

---

**Analysis Generated:** January 2025  
**Security Status:** 🟡 NEEDS IMMEDIATE ATTENTION  
**Performance Status:** 🟡 OPTIMIZATION NEEDED  
**Overall Health:** 🟡 GOOD WITH CRITICAL FIXES NEEDED 