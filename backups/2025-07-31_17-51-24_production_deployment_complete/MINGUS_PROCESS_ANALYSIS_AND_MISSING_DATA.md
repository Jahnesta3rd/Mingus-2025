# 🔍 MINGUS Process Analysis & Missing Data Requirements

## **📋 Executive Summary**

This document provides a comprehensive analysis of the MINGUS system's processes for connecting various data types and identifies critical missing data requirements that are needed for all calculations and processes.

---

## **🏥 1. Health Metrics to Spending Patterns Connection**

### **Implemented Processes**

#### **Health Correlation Service (`backend/services/health_correlation_service.py`)**
```python
class HealthCorrelationService:
    def analyze_health_spending_patterns(self, user_id: int, weeks: int = 12) -> Dict[str, Any]:
        """Main correlation analysis method"""
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Get health and spending data
        health_data = self._get_health_data(user_id, start_date, end_date)
        spending_data = self._get_spending_data(user_id, start_date, end_date)
        
        # Perform correlation analyses
        correlations = self._calculate_correlations(health_data, spending_data)
        patterns = self._analyze_spending_patterns(health_data, spending_data)
        insights = self._generate_insights(correlations, patterns, health_data, spending_data)
        trends = self._analyze_trends(health_data, spending_data)
        
        return {
            'correlations': correlations,
            'spending_patterns': patterns,
            'insights': insights,
            'trends': trends,
            'risk_assessment': self._assess_financial_risk(correlations, patterns),
            'recommendations': self._generate_recommendations(correlations, patterns, insights)
        }
```

#### **Correlation Analysis Methods**
```python
def correlate_stress_to_spending(self, health_data: List[Dict], spending_data: List[Dict]) -> CorrelationResult:
    """Analyze correlation between stress levels and spending behavior"""
    # Align health and spending data by date
    aligned_data = self._align_data_by_date(health_data, spending_data)
    
    # Extract stress levels and spending amounts
    stress_levels = [record['stress_level'] for record in aligned_data]
    spending_amounts = [record['spending_amount'] for record in aligned_data]
    
    # Calculate correlation using Pearson's r
    correlation, p_value = stats.pearsonr(stress_levels, spending_amounts)
    
    return CorrelationResult(
        metric="stress_spending",
        correlation_coefficient=correlation,
        p_value=p_value,
        significance="significant" if p_value < 0.05 else "not_significant",
        sample_size=len(aligned_data),
        trend_direction="positive" if correlation > 0 else "negative",
        strength=self._get_correlation_strength(abs(correlation)),
        confidence_interval=self._calculate_confidence_interval(correlation, len(aligned_data))
    )
```

#### **Database Schema (`health_spending_correlations`)**
```sql
CREATE TABLE health_spending_correlations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Analysis metadata
    analysis_period VARCHAR(50) NOT NULL,  -- weekly, monthly, quarterly, yearly
    analysis_start_date DATETIME NOT NULL,
    analysis_end_date DATETIME NOT NULL,
    
    -- Correlation details
    health_metric VARCHAR(100) NOT NULL,  -- stress_level, energy_level, mood_rating
    spending_category VARCHAR(100) NOT NULL,  -- food, entertainment, healthcare
    correlation_strength FLOAT NOT NULL,  -- -1.0 to 1.0
    correlation_direction VARCHAR(20) NOT NULL,  -- positive, negative, none
    
    -- Statistical details
    sample_size INTEGER NOT NULL,
    p_value FLOAT,  -- Statistical significance
    confidence_interval_lower FLOAT,
    confidence_interval_upper FLOAT,
    
    -- Insights and recommendations
    insight_text VARCHAR(1000),
    recommendation_text VARCHAR(1000),
    actionable_insight BOOLEAN DEFAULT FALSE
);
```

### **Health Metrics Collected**
- **Stress Level**: 1-10 scale from health check-ins
- **Energy Level**: 1-10 scale from health check-ins
- **Mood Rating**: 1-10 scale from health check-ins
- **Physical Activity**: Minutes per day
- **Sleep Hours**: Hours of sleep
- **Relationships Rating**: 1-10 scale
- **Mindfulness Minutes**: Daily practice time

### **Spending Categories Analyzed**
- **Food & Dining**: Restaurant spending, groceries
- **Entertainment**: Movies, events, hobbies
- **Healthcare**: Medical expenses, wellness
- **Shopping**: Retail purchases
- **Transportation**: Gas, rideshare, public transit

---

## **💼 2. Career Data Influencing Income Projections**

### **Implemented Processes**

#### **Intelligent Job Matching Service (`backend/services/intelligent_job_matching_service.py`)**
```python
class IntelligentJobMatchingService:
    def find_income_advancement_opportunities(self, user_id: int, resume_text: str, 
                                           current_salary: int, target_locations: List[str] = None):
        """Find job opportunities with 15-45% salary increases"""
        # Parse resume to get user profile
        resume_analysis = self.resume_parser.parse_resume(resume_text)
        
        # Calculate target salary based on income gap analysis
        target_salary = self._calculate_target_salary(current_salary, resume_analysis)
        
        # Set up search parameters
        search_params = SearchParameters(
            current_salary=current_salary,
            target_salary_min=target_salary,
            primary_field=resume_analysis.field_analysis.primary_field,
            experience_level=resume_analysis.experience_analysis.level,
            skills=list(resume_analysis.skills_analysis.technical_skills.keys()) + 
                   list(resume_analysis.skills_analysis.business_skills.keys()),
            locations=target_locations or self.target_msas
        )
        
        return self._execute_job_search(search_params)
```

#### **Resume Analysis Service (`backend/services/resume_analysis_service.py`)**
```python
class ResumeAnalysisService:
    def _calculate_salary_insights(self, analysis: ResumeAnalysis) -> Dict[str, Any]:
        """Calculate salary insights based on analysis"""
        field = analysis.field_analysis.primary_field.value
        experience_level = analysis.experience_analysis.level.value
        
        # Get salary ranges for field and experience
        if field in self.salary_ranges:
            field_ranges = self.salary_ranges[field]
            
            # Current level range
            if experience_level == 'Entry':
                salary_insights['current_market_range'] = {
                    'min': field_ranges['entry'] * 0.8,
                    'max': field_ranges['entry'] * 1.2
                }
                next_level = 'mid'
            elif experience_level == 'Mid':
                salary_insights['current_market_range'] = {
                    'min': field_ranges['mid'] * 0.8,
                    'max': field_ranges['mid'] * 1.2
                }
                next_level = 'senior'
            
            # Next level range
            salary_insights['next_level_range'] = {
                'min': field_ranges[next_level] * 0.8,
                'max': field_ranges[next_level] * 1.2
            }
```

#### **Job Security Analysis (`backend/models/job_security_analysis.py`)**
```python
class JobSecurityAnalysis(Base):
    """Main job security analysis table for historical score tracking"""
    __tablename__ = 'job_security_analysis'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Analysis metadata
    analysis_date = Column(DateTime, nullable=False, index=True)
    employer_name = Column(String(255))
    industry_sector = Column(String(100))
    location = Column(String(100))
    
    # Core scores (0-100)
    overall_score = Column(Float, nullable=False)
    user_perception_score = Column(Float, nullable=False)
    external_data_score = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)  # 0-100 confidence in analysis
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False)  # low, medium, high, very_high
    layoff_probability_6m = Column(Float)  # 0-1 probability
```

### **Career Data Collected**
- **Job Title**: Current position
- **Industry**: Company industry sector
- **Experience Level**: Entry, Mid, Senior
- **Years of Experience**: Total work experience
- **Skills**: Technical and business skills
- **Education Level**: Degree and field of study
- **Location**: Geographic location
- **Company Size**: Small, Medium, Large, Enterprise

### **Income Projection Factors**
- **Market Salary Ranges**: By field, experience, location
- **Career Progression Paths**: Next-level positions
- **Industry Growth Trends**: Sector-specific salary growth
- **Geographic Salary Adjustments**: Cost of living adjustments
- **Skill Premium Analysis**: High-demand skill bonuses

---

## **💕 3. Relationship Status Impact on Financial Planning**

### **Implemented Processes**

#### **Questionnaire Configuration (`src/data/questionnaire-prompts.ts`)**
```typescript
export const QUESTIONNAIRE_CONFIG: QuestionnaireConfig = {
  relationships: {
    title: "How do relationships affect your finances?",
    subtitle: "Understanding relationship dynamics helps with financial planning",
    emoji: "💕",
    questions: [
      {
        id: "relationship_status",
        type: "select",
        question: "What's your current relationship status?",
        options: [
          { value: "single", label: "Single" },
          { value: "dating", label: "Dating" },
          { value: "engaged", label: "Engaged" },
          { value: "married", label: "Married" },
          { value: "divorced", label: "Divorced" },
          { value: "widowed", label: "Widowed" }
        ],
        required: true
      },
      {
        id: "relationship_spending",
        type: "scale",
        question: "How much do relationships influence your spending?",
        min: 1,
        max: 5,
        labels: {1: "No Impact", 5: "Major Impact"},
        required: true
      },
      {
        id: "childcare_stress",
        type: "scale",
        question: "Rate stress level about childcare costs",
        min: 1,
        max: 5,
        labels: {1: "No Stress", 5: "Extreme Stress"},
        allowNA: true,
        required: false
      },
      {
        id: "relationship_notes",
        type: "textarea",
        question: "Briefly describe any relationship factor affecting your finances (optional)",
        placeholder: "e.g., 'Had to help family member with emergency'",
        maxLength: 200,
        required: false
      }
    ]
  }
}
```

#### **Health Check-in Relationship Tracking (`user_health_checkins`)**
```sql
CREATE TABLE user_health_checkins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    checkin_date DATETIME NOT NULL,
    
    -- Relationship Metrics
    relationships_rating INTEGER,  -- 1-10 scale
    relationships_notes VARCHAR(500),
    
    -- Other health metrics...
    stress_level INTEGER,  -- 1-10 scale
    energy_level INTEGER,  -- 1-10 scale
    mood_rating INTEGER,  -- 1-10 scale
);
```

### **Relationship Factors Analyzed**
- **Relationship Status**: Single, Dating, Engaged, Married, Divorced, Widowed
- **Relationship Spending Impact**: 1-5 scale influence on spending
- **Childcare Stress**: Stress level about childcare costs
- **Relationship Notes**: Qualitative relationship factors
- **Weekly Relationship Rating**: 1-10 scale from health check-ins

### **Financial Planning Adjustments**
- **Emergency Fund Requirements**: Higher for families with dependents
- **Insurance Needs**: Life insurance for dependents
- **Budget Categories**: Childcare, family activities, gifts
- **Savings Goals**: Education funds, family vacations
- **Risk Tolerance**: Conservative for families with dependents

---

## **📅 4. Milestone Date Calculations and Alerts**

### **Implemented Processes**

#### **Important Dates Schema (`important_dates_schema.sql`)**
```sql
CREATE TABLE important_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date_type_id UUID NOT NULL REFERENCES date_types(id),
    event_date DATE NOT NULL,
    amount DECIMAL(10,2),
    description TEXT,
    is_recurring BOOLEAN DEFAULT true,
    reminder_days INTEGER[] DEFAULT ARRAY[7, 3, 1], -- Days before to send reminder
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    balance_impact VARCHAR(20) DEFAULT 'expense' CHECK (balance_impact IN ('expense', 'income', 'neutral')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE associated_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    important_date_id UUID NOT NULL REFERENCES important_dates(id) ON DELETE CASCADE,
    full_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### **Cash Flow Analysis Service (`backend/services/cash_flow_analysis_service.py`)**
```python
class CashFlowAnalysisService:
    def analyze_user_dates(self, user_id: str, important_dates: List[Dict], 
                          starting_balance: float, forecast: List[Dict]) -> Dict[str, Any]:
        """Analyze the financial impact of important dates"""
        try:
            # Sort dates by date
            important_dates = sorted(important_dates, key=lambda d: d['date'])
            
            # Build a running balance for each date
            running_balance = starting_balance
            date_results = []
            alerts = []
            
            for imp_date in important_dates:
                d = imp_date['date']
                
                # Add all forecast events up to this date
                for event in forecast:
                    if event['date'] <= d:
                        running_balance += event.get('amount', 0)
                
                # Subtract the important date expense
                running_balance -= imp_date.get('amount', 0)
                
                # Determine coverage status
                if running_balance >= imp_date.get('amount', 0):
                    status = 'green'
                elif running_balance >= 0.5 * imp_date.get('amount', 0):
                    status = 'yellow'
                else:
                    status = 'red'
                
                # Generate alerts for problematic dates
                if status == 'red':
                    alerts.append({
                        'date': d,
                        'title': imp_date.get('title'),
                        'amount': imp_date.get('amount', 0),
                        'projected_balance': running_balance,
                        'shortfall': imp_date.get('amount', 0) - running_balance
                    })
            
            return {
                'date_results': date_results,
                'alerts': alerts,
                'summary': {
                    'total_dates': len(important_dates),
                    'green_dates': len([d for d in date_results if d['status'] == 'green']),
                    'yellow_dates': len([d for d in date_results if d['status'] == 'yellow']),
                    'red_dates': len([d for d in date_results if d['status'] == 'red'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user dates: {str(e)}")
            raise
```

#### **Date Types Available**
```sql
INSERT INTO date_types (type_code, type_name, max_occurrences, requires_names, description) VALUES 
    ('CHILD_BIRTHDAY', 'Child''s Birthday', 3, true, 'Birthday celebrations for children'),
    ('WEDDING_ANNIV', 'Wedding Anniversary', 1, true, 'Wedding anniversary celebration'),
    ('ENGAGEMENT_ANNIV', 'Engagement Anniversary', 1, true, 'Engagement anniversary celebration'),
    ('GROUP_TRIP', 'Group Trip', NULL, true, 'Planned group trips and vacations'),
    ('SPOUSE_BIRTHDAY', 'Spouse''s Birthday', 1, true, 'Birthday celebration for spouse'),
    ('PARENT_BIRTHDAY', 'Parent''s Birthday', 4, true, 'Birthday celebrations for parents'),
    ('TAX_REFUND', 'Tax Refund Date', NULL, false, 'Expected tax refund dates'),
    ('FRATERNITY_DUES', 'Fraternity/Sorority Assessment', NULL, false, 'Fraternity or sorority membership dues and assessments');
```

### **Milestone Calculation Features**
- **Recurring Date Support**: Annual birthdays, monthly payments
- **Associated People**: Track relationships and gift-giving
- **Financial Impact Analysis**: Cash flow impact calculations
- **Reminder System**: Multiple reminder intervals (7, 3, 1 days)
- **Status Tracking**: Pending, completed, cancelled
- **Balance Impact**: Expense, income, or neutral

---

## **❌ 5. Missing Data Requirements**

### **Critical Missing Data Fields**

#### **User Profile Missing Fields (`user_profiles` table)**
```sql
-- Missing basic information
ALTER TABLE user_profiles ADD COLUMN first_name VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN last_name VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN gender VARCHAR(50);

-- Missing location and household
ALTER TABLE user_profiles ADD COLUMN zip_code VARCHAR(10);
ALTER TABLE user_profiles ADD COLUMN dependents VARCHAR(50);
ALTER TABLE user_profiles ADD COLUMN relationship_status VARCHAR(50);

-- Missing employment details
ALTER TABLE user_profiles ADD COLUMN industry VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN job_title VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN naics_code VARCHAR(10);
```

#### **Missing Tables for Production**

##### **1. Subscription Management**
```sql
-- Missing: subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    plan_tier VARCHAR(50) NOT NULL, -- 'essentials', 'professional', 'executive'
    plan_price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL, -- 'monthly', 'annual'
    status VARCHAR(20) NOT NULL, -- 'active', 'cancelled', 'past_due', 'trial'
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    trial_start TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

##### **2. Feature Access Control**
```sql
-- Missing: feature_access table
CREATE TABLE feature_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    feature_name VARCHAR(100) NOT NULL, -- 'ai_insights', 'custom_reports', 'api_access'
    access_level VARCHAR(20) NOT NULL, -- 'none', 'basic', 'premium', 'unlimited'
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    granted_by VARCHAR(100), -- 'subscription', 'promotion', 'admin'
    
    CONSTRAINT valid_access_level CHECK (access_level IN ('none', 'basic', 'premium', 'unlimited'))
);
```

##### **3. User Analytics**
```sql
-- Missing: user_analytics table
CREATE TABLE user_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    
    -- Engagement metrics
    login_count INTEGER DEFAULT 0,
    session_duration_minutes INTEGER DEFAULT 0,
    features_used JSON, -- Array of feature names used
    pages_visited JSON, -- Array of page names visited
    
    -- Financial metrics
    financial_health_score INTEGER,
    savings_rate DECIMAL(5,2),
    debt_to_income_ratio DECIMAL(5,2),
    emergency_fund_coverage DECIMAL(5,2),
    
    -- Health metrics
    average_stress_level INTEGER,
    average_energy_level INTEGER,
    average_mood_rating INTEGER,
    health_checkins_completed INTEGER DEFAULT 0,
    
    -- Goal progress
    goals_created INTEGER DEFAULT 0,
    goals_completed INTEGER DEFAULT 0,
    goals_progress_percentage DECIMAL(5,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

##### **4. Billing History**
```sql
-- Missing: billing_history table
CREATE TABLE billing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    subscription_id UUID REFERENCES subscriptions(id),
    billing_date TIMESTAMPTZ NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) NOT NULL, -- 'successful', 'failed', 'pending', 'refunded'
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

##### **5. Team Management (Executive Tier)**
```sql
-- Missing: team_members table
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id), -- Team owner
    member_email VARCHAR(255) NOT NULL,
    member_name VARCHAR(255),
    role VARCHAR(50) NOT NULL, -- 'viewer', 'editor', 'admin'
    permissions JSON, -- Specific permissions
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'declined', 'removed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Missing Data for Calculations**

#### **1. Financial Data Gaps**
- **Detailed Expense Categories**: Current system only has basic expense tracking
- **Income Sources**: Multiple income streams not fully tracked
- **Investment Portfolio**: No investment tracking for portfolio optimization
- **Debt Details**: Specific debt types and interest rates not captured
- **Insurance Information**: Coverage amounts and premiums not tracked

#### **2. Health Data Gaps**
- **Medical History**: No medical condition tracking
- **Medication Costs**: Prescription and healthcare expenses
- **Mental Health Metrics**: Depression, anxiety scores
- **Sleep Quality**: Sleep efficiency, not just hours
- **Exercise Intensity**: Heart rate, workout types

#### **3. Career Data Gaps**
- **Performance Reviews**: No performance rating tracking
- **Promotion History**: Career progression timeline
- **Skill Certifications**: Professional certifications and training
- **Network Size**: Professional network metrics
- **Job Satisfaction**: Detailed job satisfaction metrics

#### **4. Relationship Data Gaps**
- **Family Size**: Number of children, dependents
- **Relationship Duration**: How long in current relationship
- **Financial Dependencies**: Who depends on user financially
- **Shared Expenses**: Joint financial obligations
- **Relationship Financial Goals**: Couple's financial objectives

#### **5. Milestone Data Gaps**
- **Recurring Payment Schedules**: Regular bill due dates
- **Seasonal Expenses**: Holiday, back-to-school costs
- **Life Event Planning**: Major life events (wedding, baby, etc.)
- **Travel Plans**: Vacation and business travel
- **Home Maintenance**: Property-related expenses

### **Missing Integration Points**

#### **1. External Data Sources**
- **Bank Account Integration**: Real-time transaction data
- **Credit Score Monitoring**: Credit bureau integration
- **Investment Account Sync**: Portfolio performance data
- **Insurance Provider Data**: Coverage and claim history
- **Healthcare Provider Data**: Medical expense tracking

#### **2. Real-time Data Updates**
- **Live Market Data**: Stock prices, economic indicators
- **Job Market Data**: Real-time salary and job availability
- **Cost of Living Updates**: Regional cost changes
- **Tax Law Changes**: Tax bracket and deduction updates
- **Interest Rate Changes**: Loan and savings rate updates

#### **3. Predictive Analytics Data**
- **Economic Forecasts**: GDP, inflation, employment predictions
- **Industry Trends**: Sector-specific growth projections
- **Geographic Migration**: Population and job movement patterns
- **Technology Adoption**: Automation and AI impact predictions
- **Demographic Shifts**: Age, income, education trends

---

## **🔧 6. Implementation Priority Matrix**

### **High Priority (Critical for Core Functionality)**
1. **User Profile Completion**: Add missing basic fields (names, zip code, dependents)
2. **Employment Details**: Industry, job title, NAICS mapping
3. **Subscription Management**: Billing and feature access control
4. **Detailed Expense Tracking**: Categorization and recurring payments
5. **Health Data Enhancement**: Additional health metrics

### **Medium Priority (Important for Advanced Features)**
1. **Team Management**: Executive tier collaboration features
2. **Analytics Dashboard**: User behavior and financial health tracking
3. **External Integrations**: Bank account and credit score connections
4. **Advanced Milestone Planning**: Life event and goal tracking
5. **Predictive Analytics**: AI-powered financial forecasting

### **Low Priority (Nice to Have)**
1. **Social Features**: Community and sharing capabilities
2. **Gamification**: Rewards and achievement systems
3. **Advanced Reporting**: Custom report generation
4. **Mobile App**: Native mobile application
5. **API Access**: Third-party integrations

---

## **📊 7. Data Quality Requirements**

### **Data Validation Rules**
```python
# Required data quality checks
VALIDATION_RULES = {
    'user_profiles': {
        'monthly_income': {'min': 0, 'max': 1000000, 'required': True},
        'age_range': {'values': ['18-25', '26-35', '36-45', '46-55', '56-65', '65+'], 'required': True},
        'zip_code': {'pattern': r'^\d{5}(-\d{4})?$', 'required': True},
        'relationship_status': {'values': ['single', 'dating', 'engaged', 'married', 'divorced', 'widowed'], 'required': False}
    },
    'health_checkins': {
        'stress_level': {'min': 1, 'max': 10, 'required': True},
        'energy_level': {'min': 1, 'max': 10, 'required': True},
        'mood_rating': {'min': 1, 'max': 10, 'required': True}
    },
    'important_dates': {
        'event_date': {'future_only': True, 'required': True},
        'amount': {'min': 0, 'max': 100000, 'required': False}
    }
}
```

### **Data Completeness Requirements**
- **User Profile**: 90% completion rate required
- **Health Check-ins**: Weekly completion expected
- **Financial Data**: Monthly updates required
- **Career Information**: Quarterly updates recommended
- **Milestone Planning**: Real-time updates as needed

### **Data Accuracy Requirements**
- **Financial Data**: Within 5% of actual values
- **Health Metrics**: Self-reported accuracy validation
- **Career Information**: Verified against resume/employment data
- **Relationship Data**: User-confirmed accuracy
- **Milestone Dates**: Calendar integration validation

This comprehensive analysis reveals that while the MINGUS system has sophisticated processes for connecting health, career, relationship, and milestone data, there are significant gaps in data collection that need to be addressed for optimal functionality and user experience. 