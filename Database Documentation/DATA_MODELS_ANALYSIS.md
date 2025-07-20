# Mingus Application Data Models Analysis

**Generated:** January 2025  
**Application Type:** Personal Finance & Wellness Platform  
**Database:** SQLite with 13 tables, 35 indexes, 2 views  

---

## 📋 Table of Contents

1. [User Data Structure](#user-data-structure)
2. [Financial Transaction Storage](#financial-transaction-storage)
3. [Health Tracking Data Organization](#health-tracking-data-organization)
4. [Milestone Events Storage](#milestone-events-storage)
5. [Entity Relationship Diagram](#entity-relationship-diagram)
6. [Data Flow Analysis](#data-flow-analysis)
7. [Security & Privacy Features](#security--privacy-features)

---

## 👤 1. User Data Structure

### **Core User Model (`users` table)**
```sql
users {
  id: INTEGER (Primary Key)
  email: VARCHAR(255) UNIQUE
  password_hash: VARCHAR(255)
  full_name: VARCHAR(255)
  phone_number: VARCHAR(50)
  is_active: BOOLEAN
  created_at: DATETIME
  updated_at: DATETIME
}
```

### **Extended User Profile (`user_profiles` table)**
```sql
user_profiles {
  id: INTEGER (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  
  # Financial Information
  monthly_income: FLOAT
  income_frequency: VARCHAR(50)  # weekly, bi-weekly, monthly
  primary_income_source: VARCHAR(100)
  secondary_income_source: VARCHAR(100)
  
  # Financial Goals
  primary_goal: VARCHAR(100)  # save, invest, debt_payoff
  goal_amount: FLOAT
  goal_timeline_months: INTEGER
  
  # Demographics
  age_range: VARCHAR(50)  # 18-25, 26-35, 36-45
  location_state: VARCHAR(50)
  location_city: VARCHAR(100)
  household_size: INTEGER
  employment_status: VARCHAR(50)
  
  # Financial Situation
  current_savings: FLOAT
  current_debt: FLOAT
  credit_score_range: VARCHAR(50)
  
  # Preferences
  risk_tolerance: VARCHAR(50)  # conservative, moderate, aggressive
  investment_experience: VARCHAR(50)  # beginner, intermediate, advanced
  
  # Metadata
  created_at: DATETIME
  updated_at: DATETIME
  is_complete: BOOLEAN
}
```

### **User Preferences (`user_preferences` table)**
```sql
user_preferences {
  id: INTEGER (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  
  # Notification Preferences
  email_notifications: BOOLEAN
  push_notifications: BOOLEAN
  sms_notifications: BOOLEAN
  reminder_preferences: JSON
  
  # Communication Settings
  preferred_communication: VARCHAR(20)
  communication_frequency: VARCHAR(20)
  
  # Privacy & Marketing
  share_anonymized_data: BOOLEAN
  allow_marketing_emails: BOOLEAN
  
  # UI Preferences
  theme_preference: VARCHAR(20)
  language_preference: VARCHAR(10)
  
  # Onboarding Status
  onboarding_completed: BOOLEAN
  first_checkin_scheduled: BOOLEAN
  mobile_app_downloaded: BOOLEAN
  
  # Custom Settings
  custom_preferences: JSON
}
```

**Key Features:**
- ✅ **One-to-one relationships** with users (UNIQUE constraints)
- ✅ **Comprehensive financial profiling** with goals and demographics
- ✅ **Flexible preference system** using JSON fields
- ✅ **Onboarding tracking** for user journey management

---

## 💰 2. Financial Transaction Storage

### **Current Financial Data Storage**

#### **A. Basic Financial Profile (user_profiles)**
- **Income:** `monthly_income`, `income_frequency`, `primary_income_source`
- **Savings:** `current_savings`
- **Debt:** `current_debt`
- **Goals:** `goal_amount`, `goal_timeline_months`

#### **B. Financial Questionnaire Submissions (`financial_questionnaire_submissions`)**
```sql
financial_questionnaire_submissions {
  id: SERIAL (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  
  # Financial Assessment
  monthly_income: FLOAT
  monthly_expenses: FLOAT
  current_savings: FLOAT
  total_debt: FLOAT
  risk_tolerance: INTEGER (1-10)
  
  # Goals & Analysis
  financial_goals: JSON  # Structured goal data
  financial_health_score: INTEGER
  financial_health_level: VARCHAR(50)
  recommendations: JSON  # Generated recommendations
  
  # Metadata
  submitted_at: TIMESTAMP
}
```

#### **C. Encrypted Financial Models (Planned/Backup)**
The application has **encrypted financial models** designed for sensitive data:

```python
# EncryptedFinancialProfile (from encrypted_financial_models.py)
class EncryptedFinancialProfile(Base):
    # Encrypted sensitive fields
    monthly_income: TEXT  # Encrypted
    current_savings: TEXT  # Encrypted
    current_debt: TEXT  # Encrypted
    emergency_fund: TEXT  # Encrypted
    savings_goal: TEXT  # Encrypted
    debt_payoff_goal: TEXT  # Encrypted
    investment_goal: TEXT  # Encrypted
    
    # Non-sensitive fields
    income_frequency: VARCHAR(50)
    primary_income_source: VARCHAR(100)
    risk_tolerance: VARCHAR(50)
    investment_experience: VARCHAR(50)
```

#### **D. Income Sources (Planned)**
```python
# EncryptedIncomeSource
class EncryptedIncomeSource(Base):
    source_name: VARCHAR(100)
    amount: TEXT  # Encrypted
    frequency: VARCHAR(50)
    start_date: DATETIME
    end_date: DATETIME
    is_active: BOOLEAN
```

#### **E. Due Dates & Cash Flow (Planned)**
```sql
# user_income_due_dates (from schema files)
user_income_due_dates {
  id: UUID (Primary Key)
  user_id: UUID (Foreign Key → users.id)
  income_type: VARCHAR(50)  # salary, rental, freelance, other
  amount: DECIMAL(10,2)
  frequency: VARCHAR(50)  # weekly, bi-weekly, monthly, quarterly, annually
  preferred_day: INTEGER  # 0=Monday through 6=Sunday
  start_date: DATE
  due_date: INTEGER  # Day of month for monthly payments
}

# user_expense_due_dates
user_expense_due_dates {
  id: UUID (Primary Key)
  user_id: UUID (Foreign Key → users.id)
  expense_type: VARCHAR(50)  # rent, utilities, car_payment, insurance, other
  amount: DECIMAL(10,2)
  frequency: VARCHAR(50)
  preferred_day: INTEGER
  start_date: DATE
  due_date: INTEGER
}
```

**Key Features:**
- ✅ **Multiple storage approaches** (basic, encrypted, questionnaire-based)
- ✅ **Field-level encryption** for sensitive financial data
- ✅ **Due date tracking** for recurring income/expenses
- ✅ **Cash flow analysis** capabilities
- ✅ **JSON flexibility** for complex financial data

---

## 🏥 3. Health Tracking Data Organization

### **Health Check-in System (`user_health_checkins`)**

```sql
user_health_checkins {
  id: INTEGER (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  checkin_date: DATETIME (NOT NULL)
  
  # Sleep Metrics
  sleep_hours: FLOAT  # Hours of sleep (e.g., 7.5)
  
  # Physical Activity
  physical_activity_minutes: INTEGER
  physical_activity_level: VARCHAR(50)  # low, moderate, high
  
  # Relationship Metrics
  relationships_rating: INTEGER  # 1-10 scale
  relationships_notes: VARCHAR(500)
  
  # Mindfulness Metrics
  mindfulness_minutes: INTEGER
  mindfulness_type: VARCHAR(100)  # meditation, yoga, breathing, etc.
  
  # Health Metrics
  stress_level: INTEGER  # 1-10 scale
  energy_level: INTEGER  # 1-10 scale
  mood_rating: INTEGER  # 1-10 scale
  
  # Metadata
  created_at: DATETIME
  updated_at: DATETIME
}
```

### **Health-Spending Correlations (`health_spending_correlations`)**

```sql
health_spending_correlations {
  id: INTEGER (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  
  # Analysis Metadata
  analysis_period: VARCHAR(50)  # weekly, monthly, quarterly, yearly
  analysis_start_date: DATETIME
  analysis_end_date: DATETIME
  
  # Correlation Details
  health_metric: VARCHAR(100)  # stress_level, energy_level, mood_rating
  spending_category: VARCHAR(100)  # food, entertainment, healthcare
  correlation_strength: FLOAT  # -1.0 to 1.0
  correlation_direction: VARCHAR(20)  # positive, negative, none
  
  # Statistical Analysis
  sample_size: INTEGER
  p_value: FLOAT  # Statistical significance
  confidence_interval_lower: FLOAT
  confidence_interval_upper: FLOAT
  
  # Insights
  insight_text: VARCHAR(1000)
  recommendation_text: VARCHAR(1000)
  actionable_insight: BOOLEAN
}
```

### **Health Score Calculation**
The system includes sophisticated health scoring:

```python
def calculate_health_score(self) -> float:
    """Calculate composite health score based on metrics"""
    score = 0.0
    factors = 0
    
    # Sleep quality (0-100 points)
    if 7 <= self.sleep_hours <= 9:  # Optimal range
        score += 100
    elif 6 <= self.sleep_hours <= 10:  # Acceptable range
        score += 80
    # ... more sleep logic
    
    # Physical activity (0-100 points)
    if self.physical_activity_minutes >= 150:  # Weekly minimum
        score += 100
    else:
        score += min(100, (self.physical_activity_minutes / 150) * 100)
    
    # Stress level (inverted, lower is better)
    stress_score = max(0, 10 - self.stress_level) * 10
    score += stress_score
    
    # Energy level, mood, relationships (10-100 scale each)
    score += self.energy_level * 10
    score += self.mood_rating * 10
    score += self.relationships_rating * 10
    
    # Mindfulness bonus (up to 20 points)
    if self.mindfulness_minutes > 0:
        score += min(20, self.mindfulness_minutes)
    
    return score / factors if factors > 0 else 0.0
```

**Key Features:**
- ✅ **Comprehensive health metrics** (sleep, activity, relationships, mindfulness)
- ✅ **Weekly check-in system** with unique constraints
- ✅ **Health-spending correlation analysis** with statistical significance
- ✅ **Automated health scoring** algorithm
- ✅ **Performance indexes** for efficient querying

---

## 🎯 4. Milestone Events Storage

### **A. Reminder Schedules (`reminder_schedules`)**

```sql
reminder_schedules {
  id: INTEGER (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  
  # Reminder Configuration
  reminder_type: VARCHAR(50)  # first_checkin, weekly_checkin, goal_reminder
  scheduled_date: DATETIME (NOT NULL)
  frequency: VARCHAR(20)  # daily, weekly, biweekly, monthly
  enabled: BOOLEAN
  
  # Customization
  preferences: JSON  # User preferences for this reminder
  message: TEXT  # Custom message
  
  # Metadata
  created_at: DATETIME
  updated_at: DATETIME
}
```

### **B. Important Dates System (Planned/Backup)**

```sql
important_dates {
  id: UUID (Primary Key)
  user_id: UUID (Foreign Key → users.id)
  date_type_id: UUID (Foreign Key → date_types.id)
  
  # Event Details
  event_date: DATE (NOT NULL)
  amount: DECIMAL(10,2)
  description: TEXT
  is_recurring: BOOLEAN (DEFAULT true)
  
  # Reminder Configuration
  reminder_days: INTEGER[]  # [7, 3, 1] - Days before to send reminder
  status: VARCHAR(20)  # pending, completed, cancelled
  balance_impact: VARCHAR(20)  # expense, income, neutral
  
  # Metadata
  created_at: TIMESTAMPTZ
  updated_at: TIMESTAMPTZ
}

date_types {
  id: UUID (Primary Key)
  type_code: VARCHAR(50) (UNIQUE)
  type_name: VARCHAR(100)
  max_occurrences: INTEGER
  requires_names: BOOLEAN
  description: TEXT
}

associated_people {
  id: UUID (Primary Key)
  important_date_id: UUID (Foreign Key → important_dates.id)
  full_name: VARCHAR(100)
  relationship: VARCHAR(50)
  notes: TEXT
}
```

### **C. Financial Goals & Milestones (Planned)**

```sql
user_financial_goals {
  id: UUID (Primary Key)
  user_id: UUID (Foreign Key → users.id)
  
  # Goal Details
  goal_type: TEXT  # emergency_fund, debt_payoff, home_purchase, etc.
  goal_name: TEXT (NOT NULL)
  target_amount: DECIMAL(12,2) (NOT NULL)
  current_amount: DECIMAL(12,2) (DEFAULT 0.00)
  target_date: DATE
  
  # Progress Tracking
  priority_level: INTEGER (1-5)
  monthly_contribution: DECIMAL(10,2)
  auto_contribute: BOOLEAN
  status: TEXT  # active, paused, completed, cancelled
  
  # Motivation & Milestones
  motivation_note: TEXT
  milestone_amounts: DECIMAL[]
  
  # Metadata
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
}

goal_progress_tracking {
  id: UUID (Primary Key)
  goal_id: UUID (Foreign Key → user_financial_goals.id)
  
  # Progress Details
  progress_date: DATE (NOT NULL)
  amount_contributed: DECIMAL(10,2) (NOT NULL)
  balance_after_contribution: DECIMAL(12,2) (NOT NULL)
  contribution_source: TEXT  # manual, automatic, windfall
  notes: TEXT
  
  # Metadata
  created_at: TIMESTAMP
}
```

### **D. Onboarding Progress (`onboarding_progress`)**

```sql
onboarding_progress {
  id: INTEGER (Primary Key)
  user_id: INTEGER (Foreign Key → users.id)
  
  # Progress Tracking
  current_step: VARCHAR(100)
  total_steps: INTEGER
  completed_steps: INTEGER
  step_status: VARCHAR
  completion_percentage: INTEGER
  
  # Timeline
  started_at: DATETIME
  completed_at: DATETIME
  last_activity: DATETIME
  is_complete: BOOLEAN
  
  # Data Storage
  questionnaire_responses: TEXT  # JSON responses
}
```

**Key Features:**
- ✅ **Flexible reminder system** with multiple frequencies
- ✅ **Important dates tracking** with associated people
- ✅ **Financial goal milestones** with progress tracking
- ✅ **Onboarding milestone tracking** with completion percentages
- ✅ **JSON flexibility** for complex milestone data

---

## 🔗 5. Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│      users      │    │   user_profiles     │    │ user_preferences    │
├─────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ id (PK)         │◄───┤ user_id (FK)        │    │ user_id (FK)        │
│ email           │    │ monthly_income      │    │ email_notifications │
│ password_hash   │    │ income_frequency    │    │ push_notifications  │
│ full_name       │    │ primary_goal        │    │ reminder_preferences│
│ phone_number    │    │ goal_amount         │    │ theme_preference    │
│ is_active       │    │ current_savings     │    │ onboarding_completed│
│ created_at      │    │ current_debt        │    └─────────────────────┘
│ updated_at      │    │ risk_tolerance      │
└─────────────────┘    │ is_complete         │
         │              └─────────────────────┘
         │                       │
         │              ┌─────────────────────┐
         │              │ onboarding_progress │
         │              ├─────────────────────┤
         │              │ user_id (FK)        │
         │              │ current_step        │
         │              │ completion_percentage│
         │              │ is_complete         │
         │              └─────────────────────┘
         │
         ├──────────────┐
         │              │
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│user_health_     │    │   reminder_         │    │financial_          │
│checkins         │    │   schedules         │    │questionnaire_      │
├─────────────────┤    ├─────────────────────┤    │submissions         │
│ user_id (FK)    │    │ user_id (FK)        │    ├─────────────────────┤
│ checkin_date    │    │ reminder_type       │    │ user_id (FK)        │
│ sleep_hours     │    │ scheduled_date      │    │ monthly_income      │
│ physical_       │    │ frequency           │    │ monthly_expenses    │
│ activity_minutes│    │ enabled             │    │ current_savings     │
│ stress_level    │    │ preferences         │    │ financial_goals     │
│ energy_level    │    │ message             │    │ recommendations     │
│ mood_rating     │    └─────────────────────┘    └─────────────────────┘
│ relationships_  │
│ rating          │
└─────────────────┘
         │
         │
┌─────────────────────┐
│health_spending_     │
│correlations         │
├─────────────────────┤
│ user_id (FK)        │
│ analysis_period      │
│ health_metric        │
│ spending_category    │
│ correlation_strength │
│ insight_text         │
│ actionable_insight   │
└─────────────────────┘
```

### **Relationship Summary:**

1. **Core User (`users`)** - Central entity with 10 foreign key references
2. **One-to-One Relationships:**
   - `user_profiles` → `users` (financial & demographic data)
   - `user_preferences` → `users` (settings & preferences)
   - `onboarding_progress` → `users` (onboarding tracking)

3. **One-to-Many Relationships:**
   - `user_health_checkins` → `users` (health tracking)
   - `health_spending_correlations` → `users` (analytics)
   - `financial_questionnaire_submissions` → `users` (assessments)
   - `reminder_schedules` → `users` (milestones & reminders)

4. **Data Flow Patterns:**
   - **User Creation** → Profile Setup → Onboarding → Health Tracking
   - **Financial Data** → Questionnaire → Correlations → Insights
   - **Milestones** → Reminders → Progress Tracking → Goal Achievement

---

## 🔄 6. Data Flow Analysis

### **User Journey Data Flow:**

```
1. USER REGISTRATION
   users (core account) 
   ↓
   user_preferences (default settings)
   ↓
   onboarding_progress (tracking)

2. PROFILE COMPLETION
   user_profiles (financial & demographic)
   ↓
   financial_questionnaire_submissions (assessment)
   ↓
   reminder_schedules (first check-in)

3. ONGOING ENGAGEMENT
   user_health_checkins (weekly tracking)
   ↓
   health_spending_correlations (analysis)
   ↓
   reminder_schedules (ongoing reminders)
```

### **Financial Data Flow:**

```
1. INCOME TRACKING
   user_profiles.monthly_income
   ↓
   financial_questionnaire_submissions
   ↓
   (planned) user_income_due_dates

2. EXPENSE TRACKING
   user_profiles (basic amounts)
   ↓
   financial_questionnaire_submissions
   ↓
   (planned) user_expense_due_dates

3. GOAL TRACKING
   user_profiles.primary_goal
   ↓
   (planned) user_financial_goals
   ↓
   (planned) goal_progress_tracking
```

### **Health Data Flow:**

```
1. WEEKLY CHECK-INS
   user_health_checkins (comprehensive metrics)
   ↓
   Health score calculation
   ↓
   Trend analysis

2. CORRELATION ANALYSIS
   user_health_checkins + financial data
   ↓
   health_spending_correlations
   ↓
   Actionable insights & recommendations
```

### **Milestone Data Flow:**

```
1. REMINDER SYSTEM
   reminder_schedules (scheduled events)
   ↓
   User notifications
   ↓
   Progress tracking

2. IMPORTANT DATES
   (planned) important_dates
   ↓
   Associated people tracking
   ↓
   Cash flow impact analysis
```

---

## 🔒 7. Security & Privacy Features

### **Data Protection:**

1. **Field-Level Encryption:**
   - Sensitive financial data encrypted at field level
   - Uses AES-256-GCM encryption algorithm
   - Separate encryption keys for different data types

2. **User Isolation:**
   - All data strictly isolated by `user_id`
   - Foreign key constraints ensure data integrity
   - No cross-user data access

3. **Audit Logging:**
   - `verification_audit_log` for security events
   - `verification_analytics` for user behavior tracking
   - Risk scoring for suspicious activity

4. **Privacy Controls:**
   - `share_anonymized_data` preference
   - `allow_marketing_emails` control
   - Custom privacy preferences in JSON

### **Data Validation:**

1. **Input Validation:**
   - Numeric ranges (1-10 for ratings, 0-480 for activity)
   - Email format validation
   - Date constraints (future dates only)
   - Enum constraints for categorical data

2. **Business Logic Validation:**
   - Weekly check-in limits (unique constraints)
   - Financial goal validation
   - Risk tolerance scoring
   - Health metric correlations

### **Performance Optimization:**

1. **Indexing Strategy:**
   - 35 indexes across 13 tables
   - Composite indexes for complex queries
   - Date range indexes for time-based queries
   - User-specific indexes for isolation

2. **Query Optimization:**
   - Efficient health-spending correlation analysis
   - Date range queries for reminders
   - User-specific data retrieval patterns

---

## 📊 Summary

The Mingus Application demonstrates a **sophisticated data architecture** that seamlessly integrates:

- ✅ **Comprehensive user management** with detailed profiling
- ✅ **Flexible financial tracking** with multiple storage approaches
- ✅ **Advanced health monitoring** with correlation analysis
- ✅ **Intelligent milestone tracking** with reminder systems
- ✅ **Robust security** with encryption and audit logging
- ✅ **Scalable design** with proper indexing and relationships

The system is designed to provide **personalized financial wellness insights** by correlating health data with financial behavior, creating a unique holistic approach to personal finance management. 