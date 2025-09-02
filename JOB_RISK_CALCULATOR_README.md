# AI Job Risk Calculator System

A sophisticated job risk calculation system based on the Anthropic study methodology, designed to assess automation risk and augmentation potential for various job roles.

## 🎯 Overview

This system provides comprehensive analysis of job automation risk using:
- **Fuzzy string matching** for job title recognition
- **Industry-specific modifiers** based on BLS occupation categories
- **Task-based risk assessment** mapping daily activities to automation probability
- **Experience and skill level adjustments** for personalized scoring
- **Personalized recommendations** based on risk profile and concerns

## 📊 Risk Assessment Methodology

### Risk Levels
- **High Risk (>60% automation)**: Immediate to short-term automation potential
- **Medium Risk (30-60% automation)**: Medium-term transformation potential  
- **Low Risk (<30% automation)**: Long-term stability with AI augmentation opportunities

### Scoring Factors
1. **Base Job Risk**: Pre-calculated automation/augmentation scores for 100+ job titles
2. **Industry Modifiers**: Sector-specific automation trends
3. **Task Analysis**: Daily activity automation probability mapping
4. **Experience Adjustment**: Years of experience impact on risk
5. **Skill Assessment**: Technical skills and AI usage influence
6. **Personal Concerns**: Individual AI-related worries and preferences

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mingus-application

# Install Python dependencies
pip install -r requirements-job-risk-calculator.txt

# Install fuzzywuzzy for enhanced string matching (optional)
pip install fuzzywuzzy python-Levenshtein
```

### Basic Usage

```python
from src.services.JobRiskCalculator import JobRiskCalculator

# Initialize calculator
calculator = JobRiskCalculator("v1.0")

# Sample job profile
job_profile = {
    "job_info": {
        "title": "data analyst",
        "industry": "technology", 
        "experience": 5
    },
    "daily_tasks": {
        "data_entry": True,
        "analysis": True,
        "research": True,
        "coding": False,
        "design": False,
        "management": False,
        "customer_service": False,
        "content_creation": False
    },
    "work_environment": {
        "remote_work": "full",
        "ai_usage": "extensive",
        "team_size": "large"
    },
    "skills_and_concerns": {
        "tech_skills": ["python", "sql", "excel", "tableau"],
        "ai_concerns": {
            "job_loss": True,
            "skill_gap": True,
            "privacy": False,
            "bias": False,
            "overreliance": True
        }
    },
    "contact_info": {
        "name": "John Doe",
        "email": "john@example.com",
        "location": "San Francisco"
    }
}

# Calculate risk profile
result = calculator.calculate_job_risk(job_profile)

# Display results
print(f"Automation Risk: {result.final_automation_risk:.1f}%")
print(f"Augmentation Potential: {result.final_augmentation_potential:.1f}%")
print(f"Risk Level: {result.risk_level.value}")
print(f"Timeframe: {result.timeframe.value}")
print(f"Confidence: {result.confidence:.1f}%")

# View recommendations
for rec in result.recommendations:
    print(f"- {rec['title']}: {rec['description']}")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_job_risk_calculator.py
```

The test suite includes:
- High-risk job profile testing
- Medium-risk job profile testing  
- Low-risk job profile testing
- Fuzzy string matching validation
- Recommendation generation testing
- A/B testing with different algorithm versions

## 📈 Job Title Database

The system includes 100+ job titles with pre-calculated risk scores:

### High-Risk Jobs (Examples)
- **Software Developer**: 65% automation / 35% augmentation
- **Translator**: 75% automation / 25% augmentation
- **Content Writer**: 60% automation / 35% augmentation
- **Data Entry Clerk**: 85% automation / 15% augmentation
- **Bookkeeper**: 80% automation / 20% augmentation

### Medium-Risk Jobs (Examples)
- **Marketing Manager**: 35% automation / 50% augmentation
- **Financial Analyst**: 45% automation / 45% augmentation
- **Project Manager**: 40% automation / 55% augmentation
- **Sales Representative**: 50% automation / 40% augmentation

### Low-Risk Jobs (Examples)
- **Teacher**: 15% automation / 60% augmentation
- **Therapist**: 5% automation / 45% augmentation
- **Consultant**: 20% automation / 58% augmentation
- **Nurse**: 25% automation / 55% augmentation

## 🏭 Industry Modifiers

Industry-specific automation risk multipliers:

| Industry | Modifier | Rationale |
|----------|----------|-----------|
| Manufacturing | 1.4x | High automation adoption |
| Technology | 1.2x | Rapid AI integration |
| Retail | 1.3x | Service automation |
| Healthcare | 0.8x | Human care requirements |
| Education | 0.7x | Human interaction focus |
| Government | 0.6x | Bureaucratic processes |

## 🎯 Recommendation Engine

### High-Risk Recommendations
- **Upskill in AI-Resistant Skills**: Focus on creative, strategic, and interpersonal skills
- **Career Pivot Opportunities**: Research adjacent roles less vulnerable to automation
- **AI Collaboration Mastery**: Learn to work effectively with AI tools

### Medium-Risk Recommendations
- **Strategic AI Adoption**: Integrate AI tools into workflows
- **Human Judgment Enhancement**: Focus on areas where human creativity provides value
- **Bridge Role Exploration**: Consider AI-human interface positions

### Low-Risk Recommendations
- **AI Productivity Leverage**: Use AI tools to enhance productivity
- **AI Adoption Leadership**: Position as AI adoption leader
- **Core Human Skills Enhancement**: Strengthen complementary human skills

## 🔧 Configuration

### Algorithm Versions
The system supports multiple algorithm versions for A/B testing:

```python
# Use different versions
calculator_v1 = JobRiskCalculator("v1.0")
calculator_v2 = JobRiskCalculator("v2.0")

# Compare results
result_v1 = calculator_v1.calculate_job_risk(profile)
result_v2 = calculator_v2.calculate_job_risk(profile)
```

### Custom Job Titles
Add custom job titles to the database:

```python
# Extend job titles data
calculator.job_titles_data["custom role"] = {
    "automation_risk": 45.0,
    "augmentation_potential": 50.0,
    "category": "custom",
    "description": "Custom role description"
}
```

## 📊 Analytics and Logging

### Calculation Logs
Export detailed calculation logs for analysis:

```python
log = calculator.export_calculation_log(result, job_profile)
print(json.dumps(log, indent=2))
```

### Log Output
```
{
  "timestamp": "2024-01-15T10:30:00",
  "algorithm_version": "v1.0",
  "calculation_steps": {
    "job_match": {
      "input_title": "data analyst",
      "matched_title": "data analyst",
      "base_scores": {
        "automation_risk": 50.0,
        "augmentation_potential": 40.0
      }
    },
    "modifiers": {
      "industry_modifier": 1.2,
      "experience_modifier": 0.9,
      "skill_modifier": 0.8
    },
    "final_scores": {
      "automation_risk": 43.2,
      "augmentation_potential": 38.4,
      "overall_risk": 52.4
    }
  }
}
```

## 🔍 Fuzzy String Matching

The system uses intelligent job title matching:

```python
# Test fuzzy matching
matched_title, similarity = calculator.find_best_job_match("software engineer")
print(f"Matched: {matched_title} (similarity: {similarity:.1f}%)")
```

Example matches:
- "software engineer" → "software developer" (95% similarity)
- "data entry specialist" → "data entry clerk" (90% similarity)
- "marketing coordinator" → "marketing manager" (85% similarity)

## 🚀 Performance Optimization

### Caching
Enable Redis caching for improved performance:

```python
# Configure caching (optional)
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

### Batch Processing
Process multiple profiles efficiently:

```python
profiles = [profile1, profile2, profile3, ...]
results = [calculator.calculate_job_risk(p) for p in profiles]
```

## 🔒 Security Considerations

- Input validation for all form data
- Sanitization of job titles and user inputs
- Secure logging without sensitive information
- Rate limiting for API endpoints (if implemented)

## 📝 API Integration

### REST API Example (Future Enhancement)
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class JobProfile(BaseModel):
    job_info: dict
    daily_tasks: dict
    work_environment: dict
    skills_and_concerns: dict
    contact_info: dict

@app.post("/calculate-risk")
async def calculate_risk(profile: JobProfile):
    calculator = JobRiskCalculator("v1.0")
    result = calculator.calculate_job_risk(profile.dict())
    return {
        "automation_risk": result.final_automation_risk,
        "augmentation_potential": result.final_augmentation_potential,
        "risk_level": result.risk_level.value,
        "recommendations": result.recommendations
    }
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For questions or issues:
1. Check the test suite for usage examples
2. Review the calculation logs for debugging
3. Open an issue with detailed error information

## 🔮 Future Enhancements

- **Machine Learning Integration**: ML-based risk prediction
- **Real-time Data**: Live industry automation trends
- **Geographic Factors**: Location-based risk adjustments
- **Company-Specific Analysis**: Organization-level automation assessment
- **Skill Gap Analysis**: Detailed skill development recommendations
- **Market Trend Integration**: Real-time job market data
