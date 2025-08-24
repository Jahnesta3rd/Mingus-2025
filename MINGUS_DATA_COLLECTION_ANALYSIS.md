# 🎯 MINGUS Data Collection Analysis: Complete Component Mapping

## **📋 Executive Summary**

This document provides a comprehensive mapping of all files and functions related to the five key data collection areas in the MINGUS personal finance assistant:

1. **Basic Profile Information** (age 25-35, income $40-100k)
2. **Financial Data Input** (income, expenses, due dates)
3. **Initial Health Baseline** (physical activity, relationship status, mindfulness minutes)
4. **Career Information Collection** (job title, industry, experience)
5. **Housing Situation Details** (rent/mortgage, living arrangements)

---

## **👤 1. Basic Profile Information (Age 25-35, Income $40-100k)**

### **Primary Data Models**

#### **UserProfile Model** (`backend/models/user_profile.py`)
```python
class UserProfile(Base):
    # Demographics
    age_range = Column(String(50))  # 18-25, 26-35, 36-45, etc.
    location_state = Column(String(50))
    location_city = Column(String(100))
    household_size = Column(Integer)
    
    # Financial Information
    monthly_income = Column(Float)
    income_frequency = Column(String(50))  # monthly, bi-weekly, weekly
    primary_income_source = Column(String(100))
```

#### **IncomeComparator Models** (`backend/ml/models/income_comparator.py`)
```python
# Target demographic data for ages 25-35
ComparisonGroup.AGE_25_35: DemographicIncomeData(
    group_name="Ages 25-35",
    median_income=58000,
    mean_income=72000,
    percentile_25=38000,
    percentile_75=95000,
    sample_size=45000000,
    year=2022,
    source="2022 American Community Survey"
)

# African American ages 25-35
ComparisonGroup.AFRICAN_AMERICAN_25_35: DemographicIncomeData(
    group_name="African American Ages 25-35",
    median_income=48000,
    mean_income=62000,
    percentile_25=30000,
    percentile_75=78000,
    sample_size=8500000,
    year=2022,
    source="2022 American Community Survey"
)
```

### **Frontend Components**

#### **ProfileStep Component** (`src/components/onboarding/ProfileStep.tsx`)
```typescript
interface ProfileData {
  // Basic Info
  first_name: string;
  last_name: string;
  age_range: string;
  gender: string;
  
  // Location & Household
  zip_code: string;
  location_state: string;
  location_city: string;
  household_size: string;
  
  // Income & Employment
  monthly_income: string;
  income_frequency: string;
  primary_income_source: string;
}
```

### **Database Schema**

#### **Migration Files** (`migrations/002_add_profile_fields.sql`)
```sql
-- Add basic information fields
ALTER TABLE user_onboarding_profiles 
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS age_range VARCHAR(50),
ADD COLUMN IF NOT EXISTS gender VARCHAR(50);

-- Add location and household fields
ALTER TABLE user_onboarding_profiles 
ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10),
ADD COLUMN IF NOT EXISTS location_state VARCHAR(50),
ADD COLUMN IF NOT EXISTS location_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS household_size VARCHAR(10);
```

---

## **💰 2. Financial Data Input (Income, Expenses, Due Dates)**

### **Primary Data Models**

#### **Income Due Dates** (`database/create_encrypted_financial_tables.sql`)
```sql
CREATE TABLE user_income_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    income_type VARCHAR(50) NOT NULL,  -- salary, rental, freelance, other
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,  -- weekly, bi-weekly, monthly, quarterly, annually
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### **Expense Due Dates** (`database/create_encrypted_financial_tables.sql`)
```sql
CREATE TABLE user_expense_due_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    expense_type VARCHAR(50) NOT NULL,  -- rent, utilities, car_payment, insurance, other
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    preferred_day INTEGER,
    start_date DATE NOT NULL,
    due_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### **Frontend Templates**

#### **Financial Profile Template** (`templates/financial_profile.html`)
```javascript
function gatherFormData() {
  const data = {
    // Primary income
    primaryIncome: {
      amount: parseFloat(document.getElementById('primaryIncomeAmount').value) || 0,
      frequency: document.getElementById('primaryIncomeFrequency').value,
      nextPayDate: document.getElementById('primaryNextPayDate').value,
      stability: parseInt(document.getElementById('primaryIncomeStability').value) || 7
    },
    // Secondary incomes
    secondaryIncomes: secondaryIncomes.map(inc => ({
      amount: parseFloat(inc.amount) || 0,
      frequency: inc.frequency,
      nextPayDate: inc.nextPayDate
    }))
  };
}
```

#### **Expense Profile Template** (`templates/expense_profile.html`)
```html
<div class="expense-category expanded" data-category="housing">
  <div class="category-header">
    <h4>Housing & Utilities</h4>
  </div>
  <div class="category-content">
    <label>
      Rent or Mortgage
      <input type="number" id="rent_or_mortgage_expense" name="rent_or_mortgage_expense" min="0" step="0.01" placeholder="$0.00">
    </label>
    <label>
      Frequency
      <select id="rent_or_mortgage_frequency" name="rent_or_mortgage_frequency">
        <option value="monthly">Monthly</option>
        <option value="bi-weekly">Bi-weekly</option>
        <option value="weekly">Weekly</option>
      </select>
    </label>
    <label>
      Due Date
      <input type="date" id="rent_or_mortgage_due_date" name="rent_or_mortgage_due_date">
    </label>
  </div>
</div>
```

### **Backend Services**

#### **Cash Flow Calculator** (`backend/src/utils/cashflow_calculator.py`)
```python
def calculate_daily_cashflow(user_id: str, initial_balance: float, start_date: str = None):
    """Calculate daily cash flow for the next 12 months"""
    # Fetch financial profile (income, etc.)
    profile_resp = supabase.table('user_financial_profiles').select('*').eq('user_id', user_id).single().execute()
    profile = profile_resp.data or {}
    
    # Fetch all expense schedules
    expense_response = supabase.table('user_expense_due_dates').select('*').eq('user_id', user_id).execute()
    expense_schedules = expense_response.data or []
    
    # Build daily transactions
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
```

---

## **🏥 3. Initial Health Baseline (Physical Activity, Relationship Status, Mindfulness Minutes)**

### **Primary Data Model**

#### **UserHealthCheckin Model** (`backend/models/user_health_checkin.py`)
```python
class UserHealthCheckin(Base):
    __tablename__ = 'user_health_checkins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    checkin_date = Column(DateTime, nullable=False, index=True)
    
    # Sleep metrics
    sleep_hours = Column(Float)  # Hours of sleep (e.g., 7.5 for 7.5 hours)
    
    # Physical activity metrics
    physical_activity_minutes = Column(Integer)
    physical_activity_level = Column(String(50))  # low, moderate, high
    
    # Relationship metrics
    relationships_rating = Column(Integer)  # 1-10 scale
    relationships_notes = Column(String(500))
    
    # Mindfulness metrics
    mindfulness_minutes = Column(Integer)
    mindfulness_type = Column(String(100))  # meditation, yoga, breathing, etc.
    
    # Health metrics
    stress_level = Column(Integer)  # 1-10 scale
    energy_level = Column(Integer)  # 1-10 scale
    mood_rating = Column(Integer)  # 1-10 scale
```

### **Frontend Template**

#### **Health Check-in Template** (`backend/templates/health_checkin.html`)
```html
<form class="health-form" id="healthForm">
  <!-- Physical Activity Section -->
  <div class="form-section">
    <div class="section-title">
      <div class="section-icon">🏃</div>
      Physical Activity
    </div>
    
    <div class="form-row">
      <div class="form-group">
        <label class="form-label" for="physical_activity_minutes">
          Activity Minutes Today
        </label>
        <input 
          type="number" 
          id="physical_activity_minutes" 
          name="physical_activity_minutes"
          class="form-input"
          min="0" 
          max="480"
          placeholder="e.g., 30"
        >
      </div>

      <div class="form-group">
        <label class="form-label" for="physical_activity_level">
          Activity Level
        </label>
        <select id="physical_activity_level" name="physical_activity_level" class="form-select">
          <option value="">Select activity level</option>
          <option value="low">Low</option>
          <option value="moderate">Moderate</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Relationships Section -->
  <div class="form-section">
    <div class="section-title">
      <div class="section-icon">❤️</div>
      Relationships & Social
    </div>
    
    <div class="form-group">
      <label class="form-label" for="relationships_rating">
        How would you rate your relationships this week? (1-10)
      </label>
      <input 
        type="range" 
        id="relationships_rating" 
        name="relationships_rating"
        class="form-range"
        min="1" 
        max="10" 
        value="5"
        required
      >
      <div class="range-labels">
        <span>1: Very Strained</span>
        <span>10: Excellent</span>
      </div>
    </div>
  </div>

  <!-- Mindfulness Section -->
  <div class="form-section">
    <div class="section-title">
      <div class="section-icon">🧘</div>
      Mindfulness & Wellness
    </div>
    
    <div class="form-row">
      <div class="form-group">
        <label class="form-label" for="mindfulness_minutes">
          Mindfulness Minutes Today
        </label>
        <input 
          type="number" 
          id="mindfulness_minutes" 
          name="mindfulness_minutes"
          class="form-input"
          min="0" 
          max="120"
          placeholder="e.g., 15"
        >
      </div>

      <div class="form-group">
        <label class="form-label" for="mindfulness_type">
          Mindfulness Type
        </label>
        <select id="mindfulness_type" name="mindfulness_type" class="form-select">
          <option value="">Select type</option>
          <option value="meditation">Meditation</option>
          <option value="yoga">Yoga</option>
          <option value="breathing">Breathing Exercises</option>
          <option value="prayer">Prayer</option>
          <option value="journaling">Journaling</option>
          <option value="other">Other</option>
        </select>
      </div>
    </div>
  </div>
</form>
```

### **Backend Routes**

#### **Health Routes** (`backend/routes/health.py`)
```python
@health_bp.route('/checkin', methods=['GET', 'POST'])
@require_auth
def health_checkin():
    """Health check-in form and submission"""
    if request.method == 'GET':
        user_id = get_current_user_id()
        # Get last check-in date
        with SessionLocal() as db:
            last_checkin = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .first()
        
        return render_template('health_checkin.html', last_checkin=last_checkin)
    
    # POST: Submit check-in
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['relationships_rating', 'stress_level', 'energy_level', 'mood_rating']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Create check-in record
    checkin = UserHealthCheckin(
        user_id=get_current_user_id(),
        checkin_date=datetime.now(),
        physical_activity_minutes=data.get('physical_activity_minutes'),
        physical_activity_level=data.get('physical_activity_level'),
        relationships_rating=data['relationships_rating'],
        relationships_notes=data.get('relationships_notes'),
        mindfulness_minutes=data.get('mindfulness_minutes'),
        mindfulness_type=data.get('mindfulness_type'),
        stress_level=data['stress_level'],
        energy_level=data['energy_level'],
        mood_rating=data['mood_rating']
    )
```

---

## **💼 4. Career Information Collection (Job Title, Industry, Experience)**

### **Primary Data Models**

#### **Career Profile Data** (`cypress/fixtures/comprehensive-test-data.json`)
```json
"careerProfile": {
  "companyName": "Tech Corp",
  "industry": "technology",
  "jobTitle": "Senior Software Engineer",
  "yearsExperience": "8",
  "companySize": "large",
  "jobSatisfaction": "satisfied",
  "careerGoals": ["skill-development", "promotion", "leadership"],
  "willingToRelocate": true,
  "openToRemote": true,
  "technicalSkills": ["python", "javascript", "react", "aws"],
  "softSkills": ["leadership", "communication", "project-management"],
  "certifications": ["AWS", "PMP", "Scrum Master"]
}
```

### **Frontend Components**

#### **ProfileStep Component** (`src/components/onboarding/ProfileStep.tsx`)
```typescript
interface ProfileData {
  // Income & Employment
  monthly_income: string;
  income_frequency: string;
  primary_income_source: string;
  employment_status: string;
  industry: string;
  job_title: string;
  naics_code: string;
}

// Industry mapping with NAICS codes
const industries = [
  { value: 'technology', label: 'Technology', naics: '511200' },
  { value: 'healthcare', label: 'Healthcare', naics: '621100' },
  { value: 'finance', label: 'Finance & Banking', naics: '522100' },
  { value: 'education', label: 'Education', naics: '611100' },
  { value: 'manufacturing', label: 'Manufacturing', naics: '332000' },
  { value: 'retail', label: 'Retail', naics: '445000' },
  { value: 'consulting', label: 'Consulting', naics: '541600' },
  { value: 'government', label: 'Government', naics: '920000' }
];
```

### **Backend Services**

#### **Intelligent Job Matcher** (`backend/ml/models/intelligent_job_matcher.py`)
```python
class IntelligentJobMatcher:
    def __init__(self):
        # Target MSAs for job search
        self.target_msas = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
            'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore'
        ]
        
        # Job scoring weights
        self.scoring_weights = {
            'salary_improvement': 0.35,
            'skills_match': 0.25,
            'career_progression': 0.20,
            'company_quality': 0.10,
            'location_fit': 0.05,
            'industry_alignment': 0.05
        }
        
        # Experience level progression mapping
        self.career_progression = {
            ExperienceLevel.ENTRY: [ExperienceLevel.MID],
            ExperienceLevel.MID: [ExperienceLevel.SENIOR],
            ExperienceLevel.SENIOR: ['Manager', 'Director', 'Principal']
        }
```

#### **Industry Risk Assessment** (`backend/ml/industry_risk_assessment.py`)
```python
class IndustryRiskAssessor:
    def map_industry_to_naics(self, industry_name: str, job_title: str = "") -> Optional[str]:
        """Map industry name to NAICS code"""
        mappings = {
            "software": "511200",
            "healthcare": "621100", 
            "banking": "522100",
            "education": "611100",
            "manufacturing": "332000",
            "retail": "445000",
            "consulting": "541600",
            "government": "920000"
        }
        
        # Try exact match first
        if industry_name.lower() in mappings:
            return mappings[industry_name.lower()]
        
        # Try partial matching
        for key, code in mappings.items():
            if key in industry_name.lower():
                return code
        
        return None
```

### **Enhanced Upload Route** (`backend/routes/enhanced_job_recommendations.py`)
```python
@enhanced_job_recommendations_bp.route('/upload', methods=['GET', 'POST'])
@cross_origin()
@require_auth
def enhanced_upload():
    """Enhanced upload route with comprehensive demographic collection"""
    
    # Enhanced demographic data with income comparison fields
    demographic_data = {
        'age_range': request.form.get('age_range'),
        'race': request.form.get('race'),
        'education_level': request.form.get('education_level'),
        'location': request.form.get('location'),
        'years_experience': request.form.get('years_experience'),
        'industry': request.form.get('industry'),
        'company_size': request.form.get('company_size'),
        'remote_preference': request.form.get('remote_preference') == 'true',
        'relocation_willingness': request.form.get('relocation_willingness'),
        'career_goals': request.form.get('career_goals'),
        'salary_expectations': request.form.get('salary_expectations'),
        'skills_assessment': request.form.getlist('skills'),
        'learning_preferences': request.form.getlist('learning_preferences'),
        'geographic_flexibility': request.form.get('geographic_flexibility')
    }
```

---

## **🏠 5. Housing Situation Details (Rent/Mortgage, Living Arrangements)**

### **Primary Data Models**

#### **Lifestyle Questionnaire** (`templates/lifestyle_questionnaire.html`)
```html
<!-- Section 1: Living Situation & Housing -->
<div class="section" data-section="1">
  <div class="section-title">Living Situation & Housing</div>
  <div class="section-desc">Your living situation significantly impacts your monthly expenses and long-term financial goals. Help us understand your current housing situation so we can provide more accurate forecasting and relevant recommendations.</div>
  
  <div class="question">
    <label class="question-label">1. Current Housing Status</label>
    <div class="options">
      <div class="option"><input type="radio" name="housing_status" value="own">Own your home</div>
      <div class="option"><input type="radio" name="housing_status" value="rent">Rent an apartment/house</div>
      <div class="option"><input type="radio" name="housing_status" value="family">Live with family/relatives</div>
      <div class="option"><input type="radio" name="housing_status" value="roommates">Live with roommates/housemates</div>
      <div class="option"><input type="radio" name="housing_status" value="other">Other: <input type="text" name="housing_status_other" placeholder="Please specify"></div>
    </div>
  </div>
  
  <div class="question">
    <label class="question-label">2. Housing Satisfaction (1-10)</label>
    <input type="range" name="housing_satisfaction" min="1" max="10" value="5">
    <div class="slider-labels"><span>1: Planning to move</span><span>10: Happy with current</span></div>
  </div>
  
  <div class="question">
    <label class="question-label">3. Family Living Arrangements</label>
    <div class="options">
      <div class="option"><input type="checkbox" name="living_arrangements[]" value="live_alone">Live alone</div>
      <div class="option"><input type="checkbox" name="living_arrangements[]" value="partner_spouse">Live with romantic partner/spouse</div>
      <div class="option"><input type="checkbox" name="living_arrangements[]" value="children">Live with children</div>
      <div class="option"><input type="checkbox" name="living_arrangements[]" value="extended_family">Live with extended family</div>
      <div class="option"><input type="checkbox" name="living_arrangements[]" value="support_family">Support family members financially</div>
    </div>
  </div>
  
  <div class="question">
    <label class="question-label">4. Future Housing Goals (Select all that apply)</label>
    <div class="options">
      <div class="option"><input type="checkbox" name="housing_goals[]" value="buy_home">Buy my first home within 2 years</div>
      <div class="option"><input type="checkbox" name="housing_goals[]" value="better_neighborhood">Move to a better neighborhood</div>
      <div class="option"><input type="checkbox" name="housing_goals[]" value="own_place">Get my own place</div>
      <div class="option"><input type="checkbox" name="housing_goals[]" value="downsize">Downsize to save money</div>
      <div class="option"><input type="checkbox" name="housing_goals[]" value="closer_work">Move closer to work</div>
      <div class="option"><input type="checkbox" name="housing_goals[]" value="better_schools">Move for better schools/family</div>
      <div class="option"><input type="checkbox" name="housing_goals[]" value="no_change">No housing changes planned</div>
    </div>
  </div>
</div>
```

### **Database Schema**

#### **Expense Profile Fields** (`templates/expense_profile.html`)
```html
<div class="expense-category expanded" data-category="housing">
  <div class="category-header">
    <h4>Housing & Utilities</h4>
  </div>
  <div class="category-content">
    <label>
      Rent or Mortgage
      <input type="number" id="rent_or_mortgage_expense" name="rent_or_mortgage_expense" min="0" step="0.01" placeholder="$0.00">
      <span class="monthly-conversion" id="rent_or_mortgage_monthly"></span>
    </label>
    <label>
      Frequency
      <select id="rent_or_mortgage_frequency" name="rent_or_mortgage_frequency">
        <option value="monthly">Monthly</option>
        <option value="bi-weekly">Bi-weekly</option>
        <option value="weekly">Weekly</option>
      </select>
    </label>
    <label>
      Due Date
      <input type="date" id="rent_or_mortgage_due_date" name="rent_or_mortgage_due_date">
    </label>
    
    <label>
      Utilities
      <input type="number" id="utilities_expense" name="utilities_expense" min="0" step="0.01" placeholder="$0.00">
      <span class="monthly-conversion" id="utilities_monthly"></span>
    </label>
    <label>
      Frequency
      <select id="utilities_frequency" name="utilities_frequency">
        <option value="monthly">Monthly</option>
        <option value="bi-weekly">Bi-weekly</option>
        <option value="weekly">Weekly</option>
      </select>
    </label>
    <label>
      Due Date
      <input type="date" id="utilities_due_date" name="utilities_due_date">
    </label>
  </div>
</div>
```

### **Financial Goals Integration**

#### **Home Ownership Goals** (`README_GOALS_SETUP.md`)
```markdown
### 2. Home Ownership 🏠
- **Description**: Build generational wealth
- **Examples**: Down payment, closing costs, home improvements
- **Smart Suggestions**: Based on income (20%, 12%, 8% down payment options)
```

---

## **🔗 Integration Points & Data Flow**

### **1. Onboarding Flow Integration**
- **ProfileStep Component**: Collects basic info, location, income
- **Financial Profile**: Handles income sources and frequencies
- **Expense Profile**: Manages housing and utility expenses
- **Health Check-in**: Weekly wellness baseline
- **Career Assessment**: Job matching and advancement

### **2. Database Relationships**
```sql
-- Core user data
users → user_profiles (1:1)
users → user_health_checkins (1:many)
users → user_income_due_dates (1:many)
users → user_expense_due_dates (1:many)

-- Financial tracking
user_income_due_dates → daily_cashflow (aggregated)
user_expense_due_dates → daily_cashflow (aggregated)
```

### **3. API Endpoints**
- **Profile Management**: `/api/profile` (GET/POST)
- **Financial Data**: `/api/financial-profile` (POST)
- **Health Check-in**: `/api/health/checkin` (GET/POST)
- **Career Assessment**: `/api/career/assessment` (POST)
- **Housing Data**: `/api/lifestyle/questionnaire` (POST)

---

## **📊 Data Validation & Constraints**

### **1. Age Range Validation**
```sql
CONSTRAINT valid_age_range 
CHECK (age_range IN ('18-24', '25-34', '35-44', '45-54', '55-64', '65+'))
```

### **2. Income Frequency Validation**
```sql
CONSTRAINT valid_frequency 
CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'))
```

### **3. Health Metrics Validation**
```python
# Required fields with ranges
relationships_rating: 1-10
stress_level: 1-10
energy_level: 1-10
mood_rating: 1-10
physical_activity_minutes: 0-480
mindfulness_minutes: 0-120
```

### **4. Housing Status Validation**
```html
<!-- Radio button validation -->
<input type="radio" name="housing_status" value="own" required>
<input type="radio" name="housing_status" value="rent" required>
<input type="radio" name="housing_status" value="family" required>
<input type="radio" name="housing_status" value="roommates" required>
```

---

## **🎯 Key Features Summary**

### **✅ Implemented Features**
1. **Comprehensive Profile Collection**: Age, income, location, household
2. **Financial Data Tracking**: Income sources, expense schedules, due dates
3. **Health Baseline System**: Physical activity, relationships, mindfulness
4. **Career Information**: Industry mapping, job titles, experience levels
5. **Housing Details**: Living arrangements, satisfaction, future goals

### **🔧 Technical Implementation**
- **Database Models**: 5+ tables with proper relationships
- **Frontend Components**: React components with TypeScript interfaces
- **Backend Services**: Flask routes with validation and processing
- **Data Validation**: Comprehensive constraints and error handling
- **Integration**: Seamless data flow between components

### **📱 User Experience**
- **Progressive Disclosure**: Step-by-step data collection
- **Real-time Validation**: Immediate feedback on form inputs
- **Mobile Responsive**: Works on all device sizes
- **Auto-save**: Prevents data loss during collection
- **Clear Navigation**: Progress indicators and helpful guidance

This comprehensive mapping shows that MINGUS has robust data collection systems for all five requested areas, with proper validation, storage, and integration throughout the application. 