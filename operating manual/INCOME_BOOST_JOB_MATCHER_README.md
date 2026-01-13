# Income-Focused Job Matching System for Mingus

## Overview

The IncomeBoostJobMatcher is a comprehensive job matching system designed specifically to prioritize salary improvement opportunities for African American professionals. The system focuses on identifying jobs that offer 15-45% salary increases while considering multiple factors including career advancement, company diversity, and work-life balance.

## Key Features

### 🎯 Salary-Focused Search
- Targets jobs offering 15-45% salary increases
- Integrates with major job boards (Indeed, LinkedIn, Glassdoor)
- Real-time salary data and market analysis

### 🏙️ MSA Targeting
- Focuses on top 10 metro areas with high opportunity:
  - Atlanta-Sandy Springs-Alpharetta, GA
  - Houston-The Woodlands-Sugar Land, TX
  - Washington-Arlington-Alexandria, DC-VA-MD-WV
  - Dallas-Fort Worth-Arlington, TX
  - New York-Newark-Jersey City, NY-NJ-PA
  - Philadelphia-Camden-Wilmington, PA-NJ-DE-MD
  - Chicago-Naperville-Elgin, IL-IN-WI
  - Charlotte-Concord-Gastonia, NC-SC
  - Miami-Fort Lauderdale-Pompano Beach, FL
  - Baltimore-Columbia-Towson, MD

### 📊 Multi-Dimensional Scoring System
- **Salary Increase Potential (40% weight)**: Primary focus on income improvement
- **Career Advancement Opportunities (25% weight)**: Growth potential and leadership roles
- **Company Diversity Metrics (20% weight)**: Inclusive workplace indicators
- **Benefits and Work-Life Balance (15% weight)**: Comprehensive benefits package

### 🎯 Field-Specific Strategies
Customized search strategies for different career fields:
- Technology
- Finance
- Healthcare
- Education
- Marketing
- Sales
- Consulting
- Engineering
- Data Science
- Product Management

### 🏢 Company Quality Assessment
- Diversity and inclusion metrics
- Growth potential analysis
- Company culture evaluation
- Leadership diversity assessment
- Employee retention rates

### 🏠 Remote Opportunity Detection
- Identifies remote-friendly positions
- Hybrid work arrangements
- Location-independent opportunities

## Architecture

### Core Components

1. **IncomeBoostJobMatcher** (`backend/utils/income_boost_job_matcher.py`)
   - Main job matching engine
   - Multi-dimensional scoring system
   - MSA targeting and remote detection

2. **JobBoardAPIManager** (`backend/utils/job_board_apis.py`)
   - API integration with major job boards
   - Real-time job data retrieval
   - Salary parsing and normalization

3. **CompanyDataAPIManager** (`backend/utils/job_board_apis.py`)
   - Company profile data aggregation
   - Diversity and growth metrics
   - Glassdoor and Crunchbase integration

4. **Job Matching API Endpoints** (`backend/api/job_matching_endpoints.py`)
   - REST API for frontend integration
   - Search, filtering, and analytics endpoints

## Installation and Setup

### Prerequisites
- Python 3.8+
- SQLite3
- Required Python packages (see requirements.txt)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export INDEED_API_KEY="your_indeed_api_key"
export LINKEDIN_API_KEY="your_linkedin_api_key"
export GLASSDOOR_API_KEY="your_glassdoor_api_key"
export CRUNCHBASE_API_KEY="your_crunchbase_api_key"

# Initialize database
python -c "from backend.utils.income_boost_job_matcher import IncomeBoostJobMatcher; IncomeBoostJobMatcher()"
```

### Database Schema

#### job_opportunities
```sql
CREATE TABLE job_opportunities (
    job_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    msa TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_median INTEGER,
    salary_increase_potential REAL,
    remote_friendly BOOLEAN,
    job_board TEXT,
    url TEXT,
    description TEXT,
    requirements TEXT,
    benefits TEXT,
    diversity_score REAL,
    growth_score REAL,
    culture_score REAL,
    overall_score REAL,
    field TEXT,
    experience_level TEXT,
    posted_date TIMESTAMP,
    application_deadline TIMESTAMP,
    company_size TEXT,
    company_industry TEXT,
    equity_offered BOOLEAN,
    bonus_potential INTEGER,
    career_advancement_score REAL,
    work_life_balance_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### company_profiles
```sql
CREATE TABLE company_profiles (
    company_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    size TEXT,
    diversity_score REAL,
    growth_score REAL,
    culture_score REAL,
    benefits_score REAL,
    leadership_diversity REAL,
    employee_retention REAL,
    glassdoor_rating REAL,
    indeed_rating REAL,
    remote_friendly BOOLEAN,
    headquarters TEXT,
    founded_year INTEGER,
    funding_stage TEXT,
    revenue TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage

### Basic Job Search

```python
from backend.utils.income_boost_job_matcher import (
    IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel
)
import asyncio

async def search_jobs():
    matcher = IncomeBoostJobMatcher()
    
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,  # 25% increase
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=["health insurance", "401k"],
        company_size_preference="mid",
        industry_preference="technology",
        equity_required=False,
        min_company_rating=3.0
    )
    
    jobs = await matcher.salary_focused_search(criteria)
    
    for job in jobs[:5]:  # Top 5 results
        print(f"{job.title} at {job.company}")
        print(f"Salary: ${job.salary_median:,} ({job.salary_increase_potential:.1%} increase)")
        print(f"Overall Score: {job.overall_score:.1f}")
        print(f"Remote: {job.remote_friendly}")
        print("---")

# Run the search
asyncio.run(search_jobs())
```

### API Usage

#### Search Jobs
```bash
curl -X POST http://localhost:5000/api/job-matching/search \
  -H "Content-Type: application/json" \
  -d '{
    "current_salary": 75000,
    "target_salary_increase": 0.25,
    "career_field": "technology",
    "experience_level": "mid",
    "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"],
    "remote_ok": true,
    "max_commute_time": 30,
    "must_have_benefits": ["health insurance", "401k"],
    "company_size_preference": "mid",
    "industry_preference": "technology",
    "equity_required": false,
    "min_company_rating": 3.0
  }'
```

#### Get Company Profile
```bash
curl -X GET http://localhost:5000/api/job-matching/company/Google
```

#### Get Field Strategies
```bash
curl -X GET http://localhost:5000/api/job-matching/field-strategies/technology
```

#### Apply MSA Targeting
```bash
curl -X POST http://localhost:5000/api/job-matching/msa-targeting \
  -H "Content-Type: application/json" \
  -d '{
    "jobs": [...],
    "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"]
  }'
```

#### Detect Remote Opportunities
```bash
curl -X POST http://localhost:5000/api/job-matching/remote-detection \
  -H "Content-Type: application/json" \
  -d '{
    "jobs": [...]
  }'
```

## Scoring System

### Salary Score (40% weight)
- 100 points: 45%+ salary increase
- 90 points: 30-45% salary increase
- 80 points: 15-30% salary increase
- 60 points: 5-15% salary increase
- 30 points: <5% salary increase

### Career Advancement Score (25% weight)
- Advancement keywords in title: +20 points
- Growth opportunities in description: +15 points
- Equity/stock options offered: +15 points
- Bonus potential: +10 points
- Base score: 50 points

### Diversity Score (20% weight)
- Company diversity metrics
- Leadership diversity
- Inclusive workplace indicators
- Employee retention rates

### Benefits Score (15% weight)
- Key benefits (health, 401k, dental, vision, PTO): +5 points each
- Work-life balance keywords: +15 points
- Remote work friendly: +10 points
- Base score: 50 points

## Field-Specific Strategies

### Technology
- **Keywords**: software engineer, developer, programmer, architect, devops
- **Salary Keywords**: competitive salary, equity, stock options, bonus
- **Growth Keywords**: senior, lead, principal, staff, director
- **Benefits Keywords**: unlimited PTO, flexible hours, remote work, learning budget

### Finance
- **Keywords**: financial analyst, investment banker, portfolio manager, risk analyst
- **Salary Keywords**: bonus, commission, profit sharing, performance bonus
- **Growth Keywords**: VP, director, managing director, partner
- **Benefits Keywords**: 401k match, health insurance, bonus structure, pension

### Healthcare
- **Keywords**: nurse, physician, pharmacist, therapist, technician
- **Salary Keywords**: shift differential, overtime, call pay, holiday pay
- **Growth Keywords**: charge nurse, supervisor, manager, director
- **Benefits Keywords**: health insurance, retirement, tuition reimbursement, CEU

## Testing

Run the comprehensive test suite:

```bash
python test_income_boost_job_matcher.py
```

The test suite includes:
- Unit tests for all core functionality
- Integration tests for API endpoints
- Mock tests for external API calls
- Database operation tests
- Scoring system validation

## Configuration

### Environment Variables
```bash
# Job Board API Keys
INDEED_API_KEY=your_indeed_api_key
LINKEDIN_API_KEY=your_linkedin_api_key
GLASSDOOR_API_KEY=your_glassdoor_api_key
CRUNCHBASE_API_KEY=your_crunchbase_api_key

# Database Configuration
JOB_MATCHING_DB_PATH=backend/job_matching.db

# API Rate Limits
INDEED_RATE_LIMIT=60
LINKEDIN_RATE_LIMIT=30
GLASSDOOR_RATE_LIMIT=20
```

### MSA Configuration
The system is pre-configured with the top 10 metro areas for African American professionals. You can modify the `target_msas` list in the `IncomeBoostJobMatcher` class to add or remove metro areas.

### Salary Multipliers
Location-based salary multipliers are configured for major metro areas. These can be adjusted in the `msa_salary_multipliers` dictionary.

## Performance Optimization

### Database Indexing
```sql
-- Create indexes for better performance
CREATE INDEX idx_job_field ON job_opportunities(field);
CREATE INDEX idx_job_score ON job_opportunities(overall_score);
CREATE INDEX idx_job_salary ON job_opportunities(salary_median);
CREATE INDEX idx_job_remote ON job_opportunities(remote_friendly);
CREATE INDEX idx_job_company ON job_opportunities(company);
CREATE INDEX idx_company_name ON company_profiles(name);
```

### Caching
- Company profiles are cached in the database
- Search results can be cached for repeated queries
- API responses are cached to reduce external calls

### Rate Limiting
- Each job board API has configurable rate limits
- Requests are queued and throttled appropriately
- Retry logic with exponential backoff

## Monitoring and Analytics

### Key Metrics
- Job search success rate
- Average salary increase achieved
- Company diversity scores
- Remote job percentage
- Search performance metrics

### Analytics Endpoint
```bash
curl -X GET http://localhost:5000/api/job-matching/analytics
```

Returns:
- Field distribution
- Average scores by field
- Top companies by job count
- Remote job percentage
- Total jobs processed

## Security Considerations

### API Key Management
- Store API keys in environment variables
- Use secure key management services in production
- Rotate keys regularly

### Data Privacy
- No personal information is stored
- Job data is anonymized
- Company data is publicly available information only

### Rate Limiting
- Implement rate limiting on API endpoints
- Monitor for abuse and suspicious activity
- Use CAPTCHA for high-volume requests

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**
   - Personalized job recommendations
   - Salary prediction models
   - Career path optimization

2. **Advanced Analytics**
   - Market trend analysis
   - Salary benchmarking
   - Company growth predictions

3. **Mobile App Integration**
   - Push notifications for new opportunities
   - Mobile-optimized search interface
   - Offline job browsing

4. **Social Features**
   - Job sharing and recommendations
   - Company reviews and ratings
   - Professional networking integration

5. **AI-Powered Matching**
   - Natural language processing for job descriptions
   - Skill gap analysis
   - Career transition recommendations

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests before making changes
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Include unit tests for new functionality

### Testing
- All new features must include tests
- Maintain test coverage above 90%
- Use mock objects for external API calls
- Test both success and error scenarios

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Core job matching functionality
- Multi-dimensional scoring system
- MSA targeting
- Remote opportunity detection
- Company quality assessment
- API integration with major job boards
- Comprehensive test suite
