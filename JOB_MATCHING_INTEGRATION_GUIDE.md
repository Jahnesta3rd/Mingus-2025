# Job Matching System Integration Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_job_matching.txt
```

### 2. Set Environment Variables
```bash
export INDEED_API_KEY="your_indeed_api_key"
export LINKEDIN_API_KEY="your_linkedin_api_key"
export GLASSDOOR_API_KEY="your_glassdoor_api_key"
export CRUNCHBASE_API_KEY="your_crunchbase_api_key"
```

### 3. Run the Demo
```bash
python demo_job_matching.py
```

### 4. Run Tests
```bash
python test_income_boost_job_matcher.py
```

## API Endpoints

### Search Jobs
```bash
POST /api/job-matching/search
```

### Get Company Profile
```bash
GET /api/job-matching/company/{company_name}
```

### Get Field Strategies
```bash
GET /api/job-matching/field-strategies/{field}
```

### Apply MSA Targeting
```bash
POST /api/job-matching/msa-targeting
```

### Detect Remote Opportunities
```bash
POST /api/job-matching/remote-detection
```

### Get Analytics
```bash
GET /api/job-matching/analytics
```

### Health Check
```bash
GET /api/job-matching/health
```

## Example Usage

### Python Integration
```python
from backend.utils.income_boost_job_matcher import (
    IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel
)
import asyncio

async def search_jobs():
    matcher = IncomeBoostJobMatcher()
    
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
        remote_ok=True,
        must_have_benefits=["health insurance", "401k"]
    )
    
    jobs = await matcher.salary_focused_search(criteria)
    return jobs

# Run the search
jobs = asyncio.run(search_jobs())
```

### Frontend Integration
```javascript
// Search for jobs
const searchJobs = async (criteria) => {
  const response = await fetch('/api/job-matching/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(criteria)
  });
  
  const data = await response.json();
  return data.jobs;
};

// Get company profile
const getCompanyProfile = async (companyName) => {
  const response = await fetch(`/api/job-matching/company/${companyName}`);
  const data = await response.json();
  return data.company_profile;
};
```

## Key Features

- **Salary-Focused Search**: Targets 15-45% salary increases
- **MSA Targeting**: Focuses on top 10 metro areas
- **Multi-Dimensional Scoring**: 4-factor scoring system
- **Field-Specific Strategies**: Customized by career field
- **Company Assessment**: Diversity and growth metrics
- **Remote Detection**: Identifies remote opportunities
- **API Integration**: Major job boards and company data

## Database Schema

The system uses SQLite with two main tables:
- `job_opportunities`: Stores job listings with scores
- `company_profiles`: Stores company data and metrics

## Configuration

All configuration is done through environment variables and the `IncomeBoostJobMatcher` class constructor.

## Support

For questions or issues, refer to the main README file or contact the development team.
