# 🎯 MINGUS User Creation & Data Association Analysis

## **📋 Executive Summary**

This document provides a comprehensive mapping of how new users are created and linked to their data in the MINGUS personal finance assistant, covering:

1. **Account Creation & Database Schema** - User registration and core table structure
2. **Pricing Tier Association** - Budget ($10), Mid-tier ($20), Professional ($50) assignment
3. **Data Linkage** - Financial, health, and career data connections
4. **Cash Flow Forecasting Setup** - Initial forecasting configuration and data flow

---

## **👤 1. Account Creation & Database Schema**

### **Core User Creation Process**

#### **Primary User Table (`users`)**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **User Creation Flow**
1. **Registration Form** → User submits email, password, name
2. **Password Hashing** → Secure password storage with bcrypt
3. **Email Validation** → Unique email constraint enforcement
4. **Account Activation** → `is_active = TRUE` by default
5. **Timestamp Creation** → `created_at` and `updated_at` auto-set

### **Related Tables Created During Registration**

#### **User Profile (`user_profiles`)**
```sql
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    monthly_income FLOAT,
    income_frequency VARCHAR(50),
    primary_income_source VARCHAR(100),
    age_range VARCHAR(50),
    location_state VARCHAR(50),
    location_city VARCHAR(100),
    employment_status VARCHAR(50),
    current_savings FLOAT,
    current_debt FLOAT,
    risk_tolerance VARCHAR(50),
    investment_experience VARCHAR(50),
    is_complete BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **Onboarding Progress (`onboarding_progress`)**
```sql
CREATE TABLE onboarding_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    current_step VARCHAR(100),
    total_steps INTEGER,
    completed_steps INTEGER,
    step_status VARCHAR,
    completion_percentage INTEGER,
    questionnaire_responses TEXT,
    is_complete BOOLEAN DEFAULT FALSE,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
```

#### **User Preferences (`user_preferences`)**
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    reminder_preferences JSON,
    theme_preference VARCHAR(20) DEFAULT 'light',
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## **💰 2. Pricing Tier Association**

### **Pricing Tier Structure**

#### **Marketing Assessment Tiers (`MINGUS Marketing/`)**
```sql
CREATE TYPE product_tier AS ENUM (
    'Budget ($10)',
    'Mid-tier ($20)', 
    'Professional ($50)'
);

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    segment user_segment,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    product_tier product_tier,
    assessment_completed BOOLEAN DEFAULT FALSE,
    assessment_answers JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### **Assessment-Based Tier Assignment**
```javascript
// Segment mapping based on assessment scores
const SEGMENT_MAPPING = {
  'stress-free': { min: 0, max: 16, tier: 'Budget ($10)' },
  'relationship-spender': { min: 17, max: 30, tier: 'Mid-tier ($20)' },
  'emotional-manager': { min: 31, max: 45, tier: 'Mid-tier ($20)' },
  'crisis-mode': { min: 46, max: 100, tier: 'Professional ($50)' }
};

// Function to assign tier based on assessment score
function get_product_tier(segment) {
    switch(segment) {
        case 'stress-free': return 'Budget ($10)';
        case 'relationship-spender': return 'Mid-tier ($20)';
        case 'emotional-manager': return 'Mid-tier ($20)';
        case 'crisis-mode': return 'Professional ($50)';
        default: return 'Budget ($10)';
    }
}
```

#### **Production Pricing Tiers**
```sql
CREATE TABLE pricing_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier_name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    monthly_price DECIMAL(10,2) NOT NULL,
    annual_price DECIMAL(10,2) NOT NULL,
    features JSON NOT NULL,
    limits JSON,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tier definitions
INSERT INTO pricing_tiers VALUES
('essentials', 'Essentials', 10.00, 100.00, 
 '["basic_analytics", "goal_setting", "email_support", "mobile_app_access"]',
 '{"health_checkins_per_month": 4, "financial_reports_per_month": 2}'),
 
('professional', 'Professional', 29.00, 290.00,
 '["basic_analytics", "goal_setting", "email_support", "mobile_app_access", "advanced_ai_insights", "career_risk_management", "priority_support", "custom_reports", "portfolio_optimization"]',
 '{"health_checkins_per_month": 12, "financial_reports_per_month": 10}'),
 
('executive', 'Executive', 99.00, 990.00,
 '["basic_analytics", "goal_setting", "email_support", "mobile_app_access", "advanced_ai_insights", "career_risk_management", "priority_support", "custom_reports", "portfolio_optimization", "dedicated_account_manager", "custom_integrations", "advanced_security", "team_management", "api_access"]',
 '{"health_checkins_per_month": -1, "financial_reports_per_month": -1}');
```

#### **Subscription Management**
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    plan_tier VARCHAR(50) NOT NULL,
    plan_price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## **🔗 3. Data Linkage: Financial, Health & Career**

### **Financial Data Association**

#### **Income & Expense Due Dates**
```sql
CREATE TABLE user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    income_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    expense_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### **Encrypted Financial Profiles**
```sql
CREATE TABLE encrypted_financial_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Encrypted sensitive fields
    monthly_income TEXT, -- Encrypted with field-level encryption
    current_savings TEXT, -- Encrypted
    current_debt TEXT, -- Encrypted
    emergency_fund TEXT, -- Encrypted
    savings_goal TEXT, -- Encrypted
    debt_payoff_goal TEXT, -- Encrypted
    investment_goal TEXT, -- Encrypted
    
    -- Non-sensitive fields
    income_frequency VARCHAR(50),
    primary_income_source VARCHAR(100),
    secondary_income_source VARCHAR(100),
    risk_tolerance VARCHAR(50),
    investment_experience VARCHAR(50),
    budgeting_experience VARCHAR(50),
    
    is_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Health & Wellness Data Association**

#### **Health Check-ins**
```sql
CREATE TABLE user_health_checkins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    checkin_date DATE NOT NULL,
    physical_activity_minutes INTEGER,
    sleep_hours FLOAT,
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 10),
    relationships_rating INTEGER CHECK (relationships_rating BETWEEN 1 AND 10),
    mindfulness_minutes INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **Health-Spending Correlations**
```sql
CREATE TABLE health_spending_correlations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    analysis_period VARCHAR(50),
    health_metric VARCHAR(100),
    spending_category VARCHAR(100),
    correlation_strength FLOAT,
    insight_text TEXT,
    actionable_insight TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### **Career Information Association**

#### **Career Data in User Profiles**
```sql
-- Fields in user_profiles table
employment_status VARCHAR(50), -- employed, self_employed, student, etc.
primary_income_source VARCHAR(100), -- job title, industry
secondary_income_source VARCHAR(100), -- side hustle, freelance
age_range VARCHAR(50), -- 18-25, 26-35, 36-45, etc.
location_state VARCHAR(50), -- for regional income comparisons
location_city VARCHAR(100), -- for local market analysis
```

#### **Income Analysis Integration**
```python
# From backend/ml/models/income_comparator.py
class IncomeComparator:
    def __init__(self):
        self.demographic_data = {
            'age_ranges': ['25-27', '28-30', '31-33', '34-36', '37-40'],
            'education_levels': ['High School', 'Some College', 'Bachelor\'s', 'Master\'s', 'Doctorate'],
            'locations': ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City', 'Los Angeles', 'Chicago', 'Philadelphia', 'Phoenix', 'San Antonio']
        }
    
    def compare_income(self, user_data):
        """Compare user income to demographic peers"""
        age_range = user_data.get('age_range')
        education = user_data.get('education_level')
        location = user_data.get('location')
        current_income = user_data.get('monthly_income')
        
        # Generate comparison analysis
        return {
            'overall_percentile': self.calculate_percentile(current_income, age_range, education, location),
            'peer_comparisons': self.get_peer_comparisons(age_range, education, location),
            'career_opportunities': self.identify_opportunities(current_income, age_range, education, location)
        }
```

---

## **📊 4. Cash Flow Forecasting Setup**

### **Daily Cash Flow Table Structure**
```sql
CREATE TABLE daily_cashflow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    opening_balance DECIMAL(10,2) NOT NULL,
    income DECIMAL(10,2) NOT NULL DEFAULT 0,
    expenses DECIMAL(10,2) NOT NULL DEFAULT 0,
    closing_balance DECIMAL(10,2) NOT NULL,
    net_change DECIMAL(10,2) NOT NULL,
    balance_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT valid_balance_status CHECK (balance_status IN ('healthy', 'warning', 'danger')),
    CONSTRAINT unique_user_date UNIQUE (user_id, forecast_date)
);
```

### **Cash Flow Calculation Process**

#### **Initial Setup Function**
```python
# From backend/src/utils/cashflow_calculator.py
def calculate_daily_cashflow(user_id: str, initial_balance: float, start_date: str = None):
    """
    Calculate daily cash flow for the next 12 months based on financial profile, 
    actual expenses, and goals.
    """
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = current_date + timedelta(days=365)
    
    # 1. Fetch financial profile (income, etc.)
    profile_resp = supabase.table('user_financial_profiles').select('*').eq('user_id', user_id).single().execute()
    profile = profile_resp.data or {}
    
    # 2. Fetch all expense schedules
    expense_response = supabase.table('user_expense_due_dates').select('*').eq('user_id', user_id).execute()
    expense_schedules = expense_response.data or []
    
    # 3. Fetch actual expense items (recurring, variable)
    expense_items_resp = supabase.table('user_expense_items').select('*').eq('user_id', user_id).execute()
    expense_items = expense_items_resp.data or []
    
    # 4. Fetch financial goals (future expenses)
    goals_resp = supabase.table('user_financial_goals').select('*').eq('user_id', user_id).execute()
    goals = goals_resp.data or []
    
    # 5. Build daily transactions
    daily_transactions = {}
    
    # Income: add recurring income from profile
    income = profile.get('income', 0)
    income_frequency = profile.get('income_frequency', 'monthly')
    
    # Convert income to daily
    if income_frequency == 'monthly':
        daily_income = income / 30.44
    elif income_frequency == 'bi-weekly':
        daily_income = (income * 26) / 365
    elif income_frequency == 'weekly':
        daily_income = (income * 52) / 365
    else:
        daily_income = income / 30.44
    
    # Add daily income to each day
    temp_date = current_date
    while temp_date <= end_date:
        date_str = temp_date.strftime("%Y-%m-%d")
        if date_str not in daily_transactions:
            daily_transactions[date_str] = {'income': 0, 'expenses': 0}
        daily_transactions[date_str]['income'] += daily_income
        temp_date += timedelta(days=1)
    
    # Expenses: add scheduled and actual expenses
    for expense in expense_schedules:
        due_day = int(expense.get('due_date', 1))
        amount = float(expense.get('amount', 0))
        freq = expense.get('frequency', 'monthly')
        
        temp_date = current_date
        while temp_date <= end_date:
            if temp_date.day == due_day:
                date_str = temp_date.strftime("%Y-%m-%d")
                if date_str not in daily_transactions:
                    daily_transactions[date_str] = {'income': 0, 'expenses': 0}
                daily_transactions[date_str]['expenses'] += amount
            temp_date += timedelta(days=1)
    
    # 6. Calculate running balances and insert into database
    running_balance = initial_balance
    cashflow_records = []
    
    for date_str, transactions in sorted(daily_transactions.items()):
        income = transactions['income']
        expenses = transactions['expenses']
        net_change = income - expenses
        closing_balance = running_balance + net_change
        
        # Determine balance status
        if closing_balance > 0:
            balance_status = 'healthy'
        elif closing_balance > -1000:
            balance_status = 'warning'
        else:
            balance_status = 'danger'
        
        cashflow_records.append({
            'user_id': user_id,
            'forecast_date': date_str,
            'opening_balance': running_balance,
            'income': income,
            'expenses': expenses,
            'closing_balance': closing_balance,
            'net_change': net_change,
            'balance_status': balance_status
        })
        
        running_balance = closing_balance
    
    # 7. Insert all records into daily_cashflow table
    supabase.table('daily_cashflow').insert(cashflow_records).execute()
    
    return cashflow_records
```

### **Data Flow for Cash Flow Forecasting**

#### **1. User Registration → Profile Creation**
```
User Registration → users table → user_profiles table → financial data collection
```

#### **2. Income & Expense Setup**
```
user_profiles → user_income_due_dates + user_expense_due_dates → scheduled transactions
```

#### **3. Cash Flow Calculation**
```
Financial Profile + Income Schedules + Expense Schedules + Goals → calculate_daily_cashflow() → daily_cashflow table
```

#### **4. Ongoing Updates**
```
New transactions → Recalculate cash flow → Update daily_cashflow table → Dashboard display
```

---

## **🔄 5. Complete User Creation Sequence**

### **Step-by-Step Process**

#### **Phase 1: Account Creation**
1. **User submits registration form**
2. **Password hashed and stored**
3. **User record created in `users` table**
4. **Default preferences created in `user_preferences` table**
5. **Onboarding progress initialized in `onboarding_progress` table**

#### **Phase 2: Assessment & Tier Assignment**
1. **User completes financial assessment**
2. **Assessment score calculated (0-100)**
3. **User segment determined based on score**
4. **Pricing tier assigned automatically**
5. **Lead record created/updated in `leads` table**

#### **Phase 3: Profile & Data Collection**
1. **Financial profile created in `user_profiles` table**
2. **Income sources added to `user_income_due_dates`**
3. **Expenses added to `user_expense_due_dates`**
4. **Health baseline established in `user_health_checkins`**
5. **Career information stored in profile fields**

#### **Phase 4: Cash Flow Setup**
1. **Initial balance established**
2. **`calculate_daily_cashflow()` function called**
3. **12-month forecast generated**
4. **Daily cash flow records inserted into `daily_cashflow` table**
5. **Dashboard displays initial forecast**

#### **Phase 5: Subscription Activation**
1. **Payment processed for selected tier**
2. **Subscription record created in `subscriptions` table**
3. **Feature access granted based on tier**
4. **Welcome email sent**
5. **User redirected to dashboard**

---

## **📈 6. Database Relationships Summary**

### **Core Relationships**
```
users (1) ←→ (1) user_profiles
users (1) ←→ (1) user_preferences  
users (1) ←→ (1) onboarding_progress
users (1) ←→ (1) encrypted_financial_profiles
users (1) ←→ (many) user_income_due_dates
users (1) ←→ (many) user_expense_due_dates
users (1) ←→ (many) user_health_checkins
users (1) ←→ (many) daily_cashflow
users (1) ←→ (many) subscriptions
```

### **Data Integrity Constraints**
- **UNIQUE constraints** on user_id in one-to-one relationships
- **FOREIGN KEY constraints** with CASCADE DELETE for data consistency
- **CHECK constraints** for data validation (income amounts, frequency values, etc.)
- **NOT NULL constraints** on critical fields

### **Indexes for Performance**
- **Primary key indexes** on all tables
- **Foreign key indexes** on user_id columns
- **Composite indexes** for common query patterns
- **Date-based indexes** for time-series data

---

## **🎯 7. Key Benefits of This Architecture**

### **1. Scalable User Management**
- **Modular table design** allows for easy feature additions
- **One-to-one relationships** ensure data consistency
- **Flexible JSON fields** for future extensibility

### **2. Secure Financial Data**
- **Encrypted financial profiles** for sensitive data
- **Field-level encryption** for income, savings, debt amounts
- **Row-level security** policies for data access control

### **3. Flexible Pricing Model**
- **Assessment-based tier assignment** ensures appropriate pricing
- **Multiple pricing structures** (marketing vs production)
- **Subscription management** with billing cycle tracking

### **4. Comprehensive Cash Flow Forecasting**
- **Daily granularity** for precise financial planning
- **12-month projections** for long-term planning
- **Real-time updates** as financial data changes
- **Balance status tracking** for financial health monitoring

### **5. Integrated Health & Wellness**
- **Health-spending correlations** for holistic insights
- **Regular check-ins** for ongoing wellness tracking
- **Relationship impact analysis** on financial decisions

This architecture provides a robust foundation for the MINGUS personal finance assistant, ensuring secure, scalable, and comprehensive user data management with advanced financial forecasting capabilities. 