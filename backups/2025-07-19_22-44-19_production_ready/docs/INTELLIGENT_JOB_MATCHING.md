# Intelligent Job Matching System

## Overview

The Intelligent Job Matching System is the core of Mingus's targeted job recommendations, specifically designed to find opportunities that offer 15-45% salary increases while matching users' field expertise and location preferences. Unlike generic job matching, this system prioritizes income advancement and career growth.

## Key Features

### 1. Income-Focused Job Search
- **Minimum 15% Salary Increase**: All jobs must offer at least 15% salary improvement
- **Target 25%+ Increases**: Prioritizes opportunities offering 25%+ salary increases
- **Salary Range Validation**: Normalizes and validates salary data across different sources
- **Income Gap Analysis**: Calculates potential salary improvements and purchasing power

### 2. Multi-Dimensional Job Scoring
- **Salary Improvement (35%)**: Primary weight for income advancement
- **Skills Match (25%)**: Alignment between required and possessed skills
- **Career Progression (20%)**: Logical next step vs lateral move assessment
- **Company Quality (10%)**: Based on company size, funding, and Glassdoor data
- **Location Fit (5%)**: Commute time, remote options, relocation requirements
- **Industry Alignment (5%)**: Industry trends and company expansion indicators

### 3. Field-Specific Search Strategies
- **Primary Field Optimization**: Uses field-specific keywords (e.g., "Data Analyst Python")
- **Skills-Based Secondary Searches**: Expands opportunities using transferable skills
- **Experience Level Targeting**: Matches job requirements with user experience level
- **Industry Crossover Identification**: Identifies career pivots with income growth potential

### 4. MSA-Targeted Search
- **Target Markets**: Atlanta, Houston, DC, Dallas, NYC, Philadelphia, Chicago, Charlotte, Miami, Baltimore
- **Location Flexibility**: Includes remote opportunities with local companies
- **Cost of Living Adjustments**: Accounts for regional salary differences
- **Commute Optimization**: Considers travel time and relocation requirements

### 5. Company Quality Assessment
- **Fortune 500 Companies**: Highest compensation reliability
- **Growth Companies**: High potential for rapid advancement
- **Startups**: Risk/reward balance assessment
- **Glassdoor Integration**: Company ratings and employee satisfaction
- **Funding Stage Analysis**: Company stability and growth potential

### 6. Remote Work Opportunity Identification
- **Geographic Expansion**: Expands income potential beyond local markets
- **Remote-First Companies**: Identifies companies with established remote policies
- **Hybrid Opportunities**: Flexible work arrangements
- **Cost Savings**: Accounts for reduced commuting and relocation costs

## Architecture

### Core Components

#### 1. IntelligentJobMatcher Class
```python
class IntelligentJobMatcher:
    def __init__(self):
        self.resume_parser = AdvancedResumeParser()
        self.job_security_predictor = JobSecurityPredictor()
        self.target_msas = [...]
        self.scoring_weights = {...}
        self.company_tier_scores = {...}
```

#### 2. JobPosting Data Structure
```python
@dataclass
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    salary_range: Optional[SalaryRange]
    requirements: List[str]
    skills: List[str]
    experience_level: str
    field: str
    remote_work: bool
    company_tier: CompanyTier
    glassdoor_rating: Optional[float]
```

#### 3. JobScore Results
```python
@dataclass
class JobScore:
    job: JobPosting
    overall_score: float
    salary_improvement_score: float
    skills_alignment_score: float
    career_progression_score: float
    company_stability_score: float
    location_compatibility_score: float
    growth_potential_score: float
    score_breakdown: Dict[str, float]
    recommendations: List[str]
    risk_factors: List[str]
```

#### 4. SearchParameters Configuration
```python
@dataclass
class SearchParameters:
    current_salary: int
    target_salary_min: int
    primary_field: FieldType
    experience_level: ExperienceLevel
    skills: List[str]
    locations: List[str]
    remote_preference: bool
    min_salary_increase: float
    max_search_radius: int
    company_tier_preference: List[CompanyTier]
```

### Service Integration

#### IntelligentJobMatchingService
```python
class IntelligentJobMatchingService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.job_matcher = IntelligentJobMatcher()
```

## API Endpoints

### 1. Find Income Advancement Opportunities
```http
POST /api/job-matching/find-opportunities
```

**Request Body:**
```json
{
    "resume_text": "Optional resume text",
    "target_locations": ["Atlanta", "Houston", "DC"],
    "min_salary_increase": 0.15
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "job_opportunities": {
            "job_recommendations": [...],
            "search_statistics": {...}
        },
        "income_analysis": {
            "current_salary": 75000,
            "average_target_salary": 95000,
            "average_salary_increase": 0.27,
            "opportunity_categories": {...}
        },
        "demographic_analysis": {
            "expected_salary_for_field": 85000,
            "salary_percentile": 65.5,
            "field_comparison": {...}
        },
        "insights": [...]
    }
}
```

### 2. Get Job Recommendations
```http
GET /api/job-matching/recommendations?type=income_advancement
```

**Query Parameters:**
- `type`: `income_advancement`, `career_growth`, `skill_development`

### 3. Analyze Salary Potential
```http
GET /api/job-matching/salary-potential?locations=Atlanta,Houston
```

### 4. Income Gap Analysis
```http
POST /api/job-matching/income-gap-analysis
```

**Request Body:**
```json
{
    "current_salary": 75000,
    "target_salary": 95000,
    "field": "Data Analysis",
    "experience_level": "Mid"
}
```

### 5. Market Comparison
```http
GET /api/job-matching/market-comparison?field=Data Analysis&experience_level=Mid&location=Atlanta
```

### 6. Generate Search Strategy
```http
POST /api/job-matching/search-strategy
```

## Search Algorithms

### 1. Income-Based Search Parameter Calculation

```python
def _calculate_target_salary(self, current_salary: int, resume_analysis: Any) -> int:
    base_multiplier = 1.25  # 25% increase as baseline
    
    # Adjust based on field
    field_multiplier = self.field_salary_multipliers.get(
        resume_analysis.field_analysis.primary_field, 1.0
    )
    
    # Adjust based on experience level
    experience_multiplier = {
        ExperienceLevel.ENTRY: 1.15,
        ExperienceLevel.MID: 1.25,
        ExperienceLevel.SENIOR: 1.35
    }.get(resume_analysis.experience_analysis.level, 1.25)
    
    # Adjust based on leadership potential
    leadership_bonus = 1.0 + (resume_analysis.leadership_potential * 0.1)
    
    target_salary = int(current_salary * base_multiplier * field_multiplier * 
                       experience_multiplier * leadership_bonus)
    
    # Ensure minimum 15% increase
    min_target = int(current_salary * 1.15)
    return max(target_salary, min_target)
```

### 2. Comprehensive Job Scoring System

```python
def _score_jobs(self, jobs: List[JobPosting], search_params: SearchParameters, 
               resume_analysis: Any) -> List[JobScore]:
    for job in jobs:
        # Calculate individual scores
        salary_score = self._calculate_salary_improvement_score(job, search_params)
        skills_score = self._calculate_skills_alignment_score(job, search_params)
        career_score = self._calculate_career_progression_score(job, search_params, resume_analysis)
        company_score = self._calculate_company_stability_score(job)
        location_score = self._calculate_location_compatibility_score(job, search_params)
        growth_score = self._calculate_growth_potential_score(job, resume_analysis)
        
        # Calculate weighted overall score
        overall_score = (
            salary_score * self.scoring_weights['salary_improvement'] +
            skills_score * self.scoring_weights['skills_match'] +
            career_score * self.scoring_weights['career_progression'] +
            company_score * self.scoring_weights['company_quality'] +
            location_score * self.scoring_weights['location_fit'] +
            growth_score * self.scoring_weights['industry_alignment']
        )
```

### 3. Multi-Source Job Aggregation

```python
def _search_jobs(self, search_params: SearchParameters) -> List[JobPosting]:
    all_jobs = []
    
    # Generate search queries
    search_queries = self._generate_search_queries(search_params)
    
    # Search across multiple sources in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {}
        
        for source_name, source_config in self.job_sources.items():
            if source_config['enabled']:
                for query in search_queries:
                    future = executor.submit(
                        self._search_single_source, 
                        source_name, 
                        query, 
                        search_params
                    )
                    future_to_source[future] = source_name
        
        # Collect results
        for future in as_completed(future_to_source):
            jobs = future.result()
            all_jobs.extend(jobs)
    
    # Remove duplicates
    unique_jobs = self._deduplicate_jobs(all_jobs)
    return unique_jobs
```

### 4. Salary Range Validation and Normalization

```python
@dataclass
class SalaryRange:
    min_salary: int
    max_salary: int
    currency: str = "USD"
    confidence: float = 0.8
    
    def __post_init__(self):
        if self.min_salary > self.max_salary:
            self.min_salary, self.max_salary = self.max_salary, self.min_salary
    
    @property
    def midpoint(self) -> int:
        return (self.min_salary + self.max_salary) // 2
    
    @property
    def range_width(self) -> int:
        return self.max_salary - self.min_salary
```

### 5. Company Tier Classification

```python
class CompanyTier(str, Enum):
    FORTUNE_500 = "fortune_500"
    GROWTH_COMPANY = "growth_company"
    STARTUP = "startup"
    ESTABLISHED = "established"
    UNKNOWN = "unknown"

company_tier_scores = {
    CompanyTier.FORTUNE_500: 0.9,
    CompanyTier.GROWTH_COMPANY: 0.8,
    CompanyTier.ESTABLISHED: 0.7,
    CompanyTier.STARTUP: 0.6,
    CompanyTier.UNKNOWN: 0.5
}
```

## Search Strategy Features

### 1. Primary Field Keyword Optimization

```python
def _get_field_specific_queries(self, field: FieldType) -> List[str]:
    field_queries = {
        FieldType.DATA_ANALYSIS: [
            "Data Analyst", "Business Intelligence Analyst", "Data Scientist",
            "Analytics Manager", "Data Engineer", "Business Analyst"
        ],
        FieldType.SOFTWARE_DEVELOPMENT: [
            "Software Engineer", "Software Developer", "Full Stack Developer",
            "Backend Developer", "Frontend Developer", "DevOps Engineer"
        ]
        # ... other fields
    }
    return field_queries.get(field, [field.value])
```

### 2. Skills-Based Secondary Searches

```python
def _generate_search_queries(self, search_params: SearchParameters) -> List[str]:
    queries = []
    
    # Primary field queries
    field_queries = self._get_field_specific_queries(search_params.primary_field)
    
    # Skills-based queries
    for skill in search_params.skills[:5]:  # Top 5 skills
        queries.append(f"{skill} {search_params.primary_field.value}")
    
    # Remote work queries
    if search_params.remote_preference:
        queries.extend([f"{q} remote" for q in queries[:3]])
    
    return queries[:10]  # Limit to top 10 queries
```

### 3. Location Flexibility

```python
def _calculate_location_compatibility_score(self, job: JobPosting, 
                                          search_params: SearchParameters) -> float:
    job_location = job.location.lower()
    preferred_locations = [loc.lower() for loc in search_params.locations]
    
    if any(pref_loc in job_location for pref_loc in preferred_locations):
        return 1.0
    elif job.remote_work and search_params.remote_preference:
        return 0.9
    else:
        return 0.3
```

### 4. Salary Filtering with Buffer Zones

```python
def _filter_by_salary_threshold(self, scored_jobs: List[JobScore], 
                              search_params: SearchParameters) -> List[JobScore]:
    filtered_jobs = []
    
    for job_score in scored_jobs:
        if job_score.job.salary_range:
            salary_increase = (job_score.job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
            
            if salary_increase >= search_params.min_salary_increase:
                filtered_jobs.append(job_score)
        else:
            # Include jobs with unknown salary but high overall score
            if job_score.overall_score >= 0.7:
                filtered_jobs.append(job_score)
    
    return filtered_jobs
```

## Job Scoring Components

### 1. Salary Improvement Score

```python
def _calculate_salary_improvement_score(self, job: JobPosting, 
                                      search_params: SearchParameters) -> float:
    if not job.salary_range:
        return 0.5
    
    salary_increase = (job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
    
    if salary_increase >= 0.45:  # 45%+ increase
        return 1.0
    elif salary_increase >= 0.35:  # 35%+ increase
        return 0.9
    elif salary_increase >= 0.25:  # 25%+ increase
        return 0.8
    elif salary_increase >= 0.15:  # 15%+ increase
        return 0.7
    else:
        return 0.3
```

### 2. Skills Alignment Score

```python
def _calculate_skills_alignment_score(self, job: JobPosting, 
                                    search_params: SearchParameters) -> float:
    if not job.requirements:
        return 0.5
    
    job_requirements = set(req.lower() for req in job.requirements)
    user_skills = set(skill.lower() for skill in search_params.skills)
    
    matches = job_requirements.intersection(user_skills)
    match_percentage = len(matches) / len(job_requirements)
    
    if match_percentage >= 0.8:
        return 1.0
    elif match_percentage >= 0.6:
        return 0.8
    elif match_percentage >= 0.4:
        return 0.6
    else:
        return 0.2
```

### 3. Career Progression Score

```python
def _calculate_career_progression_score(self, job: JobPosting, 
                                      search_params: SearchParameters,
                                      resume_analysis: Any) -> float:
    current_level = search_params.experience_level
    job_title = job.title.lower()
    
    if current_level == ExperienceLevel.ENTRY:
        if any(word in job_title for word in ['senior', 'lead', 'manager']):
            return 1.0
        elif any(word in job_title for word in ['specialist', 'analyst']):
            return 0.8
    elif current_level == ExperienceLevel.MID:
        if any(word in job_title for word in ['manager', 'director']):
            return 1.0
        elif any(word in job_title for word in ['senior', 'lead']):
            return 0.8
    
    return 0.5
```

### 4. Company Stability Score

```python
def _calculate_company_stability_score(self, job: JobPosting) -> float:
    base_score = self.company_tier_scores.get(job.company_tier, 0.5)
    
    # Adjust based on Glassdoor rating
    if job.glassdoor_rating:
        rating_bonus = (job.glassdoor_rating - 3.0) * 0.1
        base_score = min(1.0, base_score + rating_bonus)
    
    # Adjust based on company size
    if '1000+' in job.company_size or 'fortune' in job.company_size.lower():
        base_score = min(1.0, base_score + 0.1)
    
    return base_score
```

## Integration with Mingus

### 1. Resume Analysis Integration

```python
def find_income_advancement_opportunities(self, user_id: int, resume_text: str, 
                                        current_salary: int, target_locations: List[str] = None):
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
```

### 2. Job Security Integration

```python
# Integrate with existing job security predictions
job_security_data = self.job_security_predictor.predict(company_data, user_data)

# Factor job security into scoring
if job_security_data.get('overall_risk', 0) > 0.7:
    company_score *= 0.8  # Reduce score for high-risk companies
```

### 3. Financial Planning Integration

```python
# Use job recommendations for income forecasting
for job in job_recommendations:
    salary_increase = (job.salary_range.midpoint - current_salary) / current_salary
    
    # Update financial projections
    financial_planning.update_income_projection(
        user_id=user_id,
        new_salary=job.salary_range.midpoint,
        timeline='3-6 months',
        confidence=job.overall_score
    )
```

## Performance Optimization

### 1. Parallel Job Search

```python
def _search_jobs(self, search_params: SearchParameters) -> List[JobPosting]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {}
        
        for source_name, source_config in self.job_sources.items():
            if source_config['enabled']:
                for query in search_queries:
                    future = executor.submit(
                        self._search_single_source, 
                        source_name, 
                        query, 
                        search_params
                    )
                    future_to_source[future] = source_name
```

### 2. Caching Strategy

```python
# Cache search results
self.search_cache = {}
self.cache_ttl = 3600  # 1 hour

def _get_cached_search_results(self, cache_key: str) -> Optional[List[JobPosting]]:
    if cache_key in self.search_cache:
        timestamp, results = self.search_cache[cache_key]
        if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
            return results
    return None
```

### 3. Batch Processing

```python
def _process_jobs_in_batches(self, jobs: List[JobPosting], batch_size: int = 100):
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        yield batch
```

## Error Handling and Logging

### 1. Comprehensive Error Management

```python
def find_income_advancement_jobs(self, user_id: int, resume_text: str, 
                               current_salary: int, target_locations: List[str] = None):
    try:
        logger.info(f"Starting income advancement job search for user {user_id}")
        
        # Validate inputs
        if not resume_text or not current_salary:
            raise ValueError("Resume text and current salary are required")
        
        # Process job search
        result = self._process_job_search(user_id, resume_text, current_salary, target_locations)
        
        logger.info(f"Job search completed for user {user_id}: {len(result['job_recommendations'])} opportunities")
        return result
        
    except Exception as e:
        logger.error(f"Error in job search for user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise
```

### 2. Search Effectiveness Monitoring

```python
def _log_search_effectiveness(self, search_params: SearchParameters, 
                            results: Dict[str, Any]):
    logger.info(f"Search effectiveness metrics:")
    logger.info(f"  - Total jobs found: {len(results.get('job_recommendations', []))}")
    logger.info(f"  - Average salary increase: {results.get('search_statistics', {}).get('avg_salary_increase', 0)*100:.1f}%")
    logger.info(f"  - Jobs meeting threshold: {len([j for j in results.get('job_recommendations', []) if j.get('salary_improvement_score', 0) >= 0.7])}")
```

## Testing

### 1. Unit Tests

```python
def test_salary_improvement_score_calculation(self, matcher, sample_job_posting):
    search_params = SearchParameters(
        current_salary=75000,
        target_salary_min=90000,
        primary_field=FieldType.DATA_ANALYSIS,
        experience_level=ExperienceLevel.SENIOR,
        skills=["python", "sql"],
        locations=["Atlanta"]
    )
    
    score = matcher._calculate_salary_improvement_score(sample_job_posting, search_params)
    
    assert 0 <= score <= 1
    assert score > 0  # Should have some score since salary is higher
```

### 2. Integration Tests

```python
def test_complete_job_search_flow(self, matcher, sample_resume_text):
    with patch.object(matcher, '_search_jobs') as mock_search:
        mock_search.return_value = [sample_job_posting]
        
        result = matcher.find_income_advancement_jobs(
            user_id=1,
            resume_text=sample_resume_text,
            current_salary=75000,
            target_locations=["Atlanta", "Houston"]
        )
        
        assert 'job_opportunities' in result
        assert 'income_analysis' in result
        assert 'demographic_analysis' in result
```

## Future Enhancements

### 1. Machine Learning Integration
- **Custom Scoring Models**: Train field-specific scoring models
- **Salary Prediction**: ML-based salary range prediction
- **Job Success Prediction**: Predict application success probability

### 2. Real-Time Data Integration
- **Live Job Feeds**: Real-time job posting aggregation
- **Market Data**: Live salary and demand data
- **Company Intelligence**: Real-time company performance data

### 3. Advanced Analytics
- **Trend Analysis**: Industry and salary trend analysis
- **Predictive Modeling**: Career trajectory prediction
- **Market Intelligence**: Competitive intelligence and insights

### 4. Enhanced Personalization
- **Learning Preferences**: Adapt to user behavior and preferences
- **Career Goals**: Align with specific career objectives
- **Risk Tolerance**: Factor in user's risk tolerance for career moves

## Conclusion

The Intelligent Job Matching System provides a sophisticated, income-focused approach to job recommendations that goes far beyond traditional job matching. By prioritizing salary advancement, leveraging field expertise analysis, and incorporating comprehensive scoring algorithms, the system delivers highly targeted opportunities that align with users' income advancement goals.

The integration with Mingus's existing resume analysis and job security infrastructure creates a comprehensive career advancement platform that helps users make informed decisions about their professional growth and financial future. 