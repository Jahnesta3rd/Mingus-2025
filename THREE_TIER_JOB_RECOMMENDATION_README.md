# Three-Tier Job Recommendation System

A comprehensive job recommendation system that presents opportunities at different risk/reward levels for career advancement, specifically designed for African American professionals seeking salary improvements and career growth.

## Overview

The Three-Tier Job Recommendation System categorizes job opportunities into three distinct tiers based on risk/reward profiles:

- **Conservative Tier**: 15-20% salary increase, high success probability
- **Optimal Tier**: 25-30% salary increase, moderate stretch  
- **Stretch Tier**: 35%+ salary increase, aspirational goals

Each tier provides tailored application strategies, skills gap analysis, and preparation roadmaps to maximize success probability.

## Key Features

### 🎯 Three-Tier Classification
- **Conservative**: Similar roles, established companies, proven career path
- **Optimal**: Role elevation, growth companies, manageable skill gaps
- **Stretch**: Career pivots, innovation companies, significant skill development

### 📊 Comprehensive Analysis
- **Skills Gap Analysis**: Identifies required vs. current skills with learning recommendations
- **Success Probability Calculation**: Estimates likelihood of job offer based on multiple factors
- **Diversity Analysis**: Evaluates company diversity and inclusion metrics
- **Culture Fit Assessment**: Analyzes alignment with work preferences

### 🛠️ Application Support
- **Customized Strategies**: Tier-specific application approaches
- **Preparation Roadmaps**: Step-by-step preparation plans
- **Interview Preparation**: Detailed preparation tasks by interview type
- **Salary Negotiation**: Guidance and tips for each tier

### 🌍 Diversity & Inclusion Focus
- **Industry Diversity**: Ensures variety across industries within each tier
- **Company Size Variety**: Mix of startup, mid-size, and enterprise opportunities
- **Geographic Diversity**: Opportunities across different metro areas
- **Inclusive Benefits**: Analysis of diversity and inclusion benefits

## Architecture

### Core Components

#### ThreeTierJobSelector Class
Main class that orchestrates the entire recommendation system:

```python
from backend.utils.three_tier_job_selector import ThreeTierJobSelector

selector = ThreeTierJobSelector()
recommendations = await selector.generate_tiered_recommendations(criteria)
```

#### Data Models

**TieredJobRecommendation**
```python
@dataclass
class TieredJobRecommendation:
    job: JobOpportunity
    tier: JobTier
    success_probability: float
    salary_increase_potential: float
    skills_gap_analysis: List[SkillGap]
    application_strategy: ApplicationStrategy
    preparation_roadmap: PreparationRoadmap
    diversity_analysis: Dict[str, Any]
    company_culture_fit: float
    career_advancement_potential: float
```

**SkillGap Analysis**
```python
@dataclass
class SkillGap:
    skill: str
    category: SkillCategory
    current_level: float  # 0-1 scale
    required_level: float  # 0-1 scale
    gap_size: float
    priority: str  # "high", "medium", "low"
    learning_time_estimate: str
    resources: List[str]
```

## API Endpoints

### Get Tiered Recommendations
```bash
POST /api/three-tier/recommendations
```

**Request Body:**
```json
{
    "current_salary": 75000,
    "career_field": "technology",
    "experience_level": "mid",
    "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"],
    "remote_ok": true,
    "max_commute_time": 30,
    "must_have_benefits": ["health insurance", "401k"],
    "company_size_preference": "mid",
    "industry_preference": "technology",
    "equity_required": false,
    "min_company_rating": 3.5,
    "max_recommendations_per_tier": 5
}
```

**Response:**
```json
{
    "success": true,
    "recommendations": {
        "conservative": [...],
        "optimal": [...],
        "stretch": [...]
    },
    "tier_summary": {
        "conservative": {
            "count": 5,
            "avg_salary_increase": "18.5%",
            "avg_success_probability": "78.2%",
            "avg_preparation_time": "2-4 weeks",
            "industries": ["Technology", "Finance"],
            "company_sizes": ["Large Enterprise", "Fortune 500"]
        }
    },
    "total_recommendations": 15,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

### Get Specific Tier Recommendations
```bash
GET /api/three-tier/tier/{tier_name}?current_salary=75000&career_field=technology&experience_level=mid
```

### Get Tier Summary
```bash
GET /api/three-tier/tiers/summary
```

## Tier Specifications

### Conservative Tier
- **Salary Increase**: 15-20%
- **Success Probability**: 70%+
- **Company Types**: Fortune 500, Large Enterprise, Government
- **Risk Level**: Low
- **Preparation Time**: 2-4 weeks
- **Focus**: Similar roles, established companies, proven career path

### Optimal Tier
- **Salary Increase**: 25-30%
- **Success Probability**: 50%+
- **Company Types**: Growth Company, Mid-size, Scale-up
- **Risk Level**: Medium
- **Preparation Time**: 1-3 months
- **Focus**: Role elevation, growth companies, manageable skill gaps

### Stretch Tier
- **Salary Increase**: 35%+
- **Success Probability**: 30%+
- **Company Types**: Startup, Innovation, High-growth
- **Risk Level**: High
- **Preparation Time**: 3-6 months
- **Focus**: Career pivots, innovation companies, significant skill development

## Skills Gap Analysis

### Skill Categories
- **Technical**: Programming, software, technical tools
- **Soft Skills**: Communication, teamwork, problem-solving
- **Leadership**: Management, mentoring, team building
- **Financial**: Financial analysis, budgeting, accounting
- **Communication**: Writing, presentation, public speaking
- **Analytical**: Data analysis, research, metrics

### Gap Analysis Process
1. **Extract Required Skills**: Parse job description and requirements
2. **Categorize Skills**: Group skills into relevant categories
3. **Assess Current Level**: Evaluate user's current skill level (0-1 scale)
4. **Calculate Gap**: Determine difference between required and current
5. **Prioritize Gaps**: Rank by importance and impact
6. **Provide Resources**: Suggest learning materials and timelines

## Application Strategies

### Conservative Tier Strategy
- **Timeline**: 2-4 weeks
- **Focus**: Proven experience, reliability, cultural fit
- **Key Selling Points**: Track record, technical skills match, consistent performance
- **Challenges**: Internal competition, budget constraints

### Optimal Tier Strategy
- **Timeline**: 1-3 months
- **Focus**: Growth mindset, transferable skills, potential
- **Key Selling Points**: Adaptability, eagerness to learn, challenge-taking
- **Challenges**: Demonstrating readiness, addressing skill gaps

### Stretch Tier Strategy
- **Timeline**: 3-6 months
- **Focus**: Fresh perspective, passion, rapid learning
- **Key Selling Points**: Innovation, transferable skills, growth commitment
- **Challenges**: Significant skill development, demonstrating potential

## Preparation Roadmaps

### Phase Structure
Each roadmap includes multiple phases with specific tasks and timelines:

1. **Research and Preparation** (Conservative)
2. **Skill Development** (Optimal/Stretch)
3. **Portfolio Building** (Optimal/Stretch)
4. **Networking and Industry Immersion** (Stretch)
5. **Application and Interview Process** (All tiers)

### Components
- **Skill Development Plan**: Addresses identified skill gaps
- **Networking Plan**: Professional relationship building
- **Portfolio Building**: Project examples and demonstrations
- **Certification Recommendations**: Relevant professional certifications

## Database Schema

### tiered_recommendations
```sql
CREATE TABLE tiered_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    success_probability REAL,
    salary_increase_potential REAL,
    skills_gap_analysis TEXT,
    application_strategy TEXT,
    preparation_roadmap TEXT,
    diversity_analysis TEXT,
    company_culture_fit REAL,
    career_advancement_potential REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### skills_gap_analysis
```sql
CREATE TABLE skills_gap_analysis (
    gap_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    skill TEXT NOT NULL,
    category TEXT NOT NULL,
    current_level REAL,
    required_level REAL,
    gap_size REAL,
    priority TEXT,
    learning_time_estimate TEXT,
    resources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Basic Usage
```python
from backend.utils.three_tier_job_selector import ThreeTierJobSelector
from backend.utils.income_boost_job_matcher import SearchCriteria, CareerField, ExperienceLevel

# Create search criteria
criteria = SearchCriteria(
    current_salary=75000,
    target_salary_increase=0.25,
    career_field=CareerField.TECHNOLOGY,
    experience_level=ExperienceLevel.MID,
    preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA"],
    remote_ok=True
)

# Generate recommendations
selector = ThreeTierJobSelector()
recommendations = await selector.generate_tiered_recommendations(criteria)

# Access recommendations by tier
conservative_jobs = recommendations[JobTier.CONSERVATIVE]
optimal_jobs = recommendations[JobTier.OPTIMAL]
stretch_jobs = recommendations[JobTier.STRETCH]
```

### Advanced Usage
```python
# Get tier summary
summary = selector.get_tier_summary(recommendations)
print(f"Conservative tier: {summary['conservative']['count']} jobs")
print(f"Average salary increase: {summary['conservative']['avg_salary_increase']}%")

# Analyze specific job
for rec in conservative_jobs:
    print(f"Job: {rec.job.title} at {rec.job.company}")
    print(f"Success probability: {rec.success_probability:.1%}")
    print(f"Salary increase: {rec.salary_increase_potential:.1%}")
    
    # Skills gap analysis
    for gap in rec.skills_gap_analysis:
        if gap.priority == "high":
            print(f"High priority skill gap: {gap.skill}")
            print(f"Learning time: {gap.learning_time_estimate}")
            print(f"Resources: {', '.join(gap.resources[:2])}")
```

## Testing

### Run Test Suite
```bash
python test_three_tier_job_selector.py
```

### Test Coverage
- Unit tests for all core methods
- Integration tests for full workflow
- Mock tests for external dependencies
- Database initialization tests
- API endpoint tests

### Test Categories
- **Classification Tests**: Job tier classification accuracy
- **Analysis Tests**: Skills gap and success probability calculations
- **Strategy Tests**: Application strategy generation
- **Roadmap Tests**: Preparation roadmap creation
- **Diversity Tests**: Tier diversity ensuring
- **API Tests**: Endpoint functionality and error handling

## Integration

### With Existing Job Matching System
The Three-Tier Job Selector integrates seamlessly with the existing IncomeBoostJobMatcher:

```python
# Uses existing job search functionality
job_opportunities = await self.job_matcher.salary_focused_search(criteria)

# Adds tier classification and analysis
tiered_recommendations = self._classify_jobs_into_tiers(job_opportunities, criteria)
```

### With Resume Parser
Skills gap analysis can be enhanced with resume parsing:

```python
# Extract skills from resume
parsed_resume = resume_parser.parse_resume(resume_file)
current_skills = parsed_resume.get('skills', [])

# Use in skills gap analysis
skills_gaps = selector.analyze_skills_gap(job, criteria, current_skills)
```

## Performance Considerations

### Optimization Strategies
- **Async Processing**: Non-blocking job search and analysis
- **Caching**: Store frequently accessed data
- **Batch Processing**: Process multiple jobs simultaneously
- **Database Indexing**: Optimize query performance

### Scalability
- **Horizontal Scaling**: Multiple worker processes
- **Database Sharding**: Distribute data across multiple databases
- **CDN Integration**: Cache static content and responses
- **Load Balancing**: Distribute API requests

## Monitoring and Analytics

### Key Metrics
- **Recommendation Accuracy**: Success rate of tier classifications
- **User Engagement**: Time spent on each tier
- **Application Success**: Conversion from recommendation to application
- **Skills Gap Resolution**: Progress on identified skill gaps

### Logging
- **Recommendation Generation**: Track recommendation creation
- **API Usage**: Monitor endpoint usage and performance
- **Error Tracking**: Log and analyze errors
- **Performance Metrics**: Track response times and throughput

## Future Enhancements

### Planned Features
- **Machine Learning**: Improve classification accuracy with ML models
- **Real-time Updates**: Live job market data integration
- **Personalization**: User-specific recommendation tuning
- **Advanced Analytics**: Deeper insights and reporting

### Integration Opportunities
- **Learning Management Systems**: Direct integration with online courses
- **Professional Networks**: Enhanced networking recommendations
- **Salary Negotiation Tools**: Interactive negotiation guidance
- **Interview Preparation**: AI-powered interview practice

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up database: `python -c "from backend.utils.three_tier_job_selector import ThreeTierJobSelector; ThreeTierJobSelector()"`
4. Run tests: `python test_three_tier_job_selector.py`

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Include unit tests for new features

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Submit pull request with description
5. Address review feedback

## License

This project is part of the Mingus Application and follows the same licensing terms.

## Support

For questions, issues, or contributions, please contact the development team or create an issue in the repository.
