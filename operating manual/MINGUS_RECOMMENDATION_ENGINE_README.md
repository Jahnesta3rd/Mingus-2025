# Mingus Job Recommendation Engine

## Overview

The Mingus Job Recommendation Engine is a comprehensive central orchestration system that coordinates all components for seamless resume-to-recommendation workflow. It provides end-to-end processing from resume upload to final job recommendations with robust error handling, performance optimization, and analytics tracking.

## Key Features

### 🚀 Complete Workflow Orchestration
- **Resume Parsing & Analysis**: Advanced resume parsing with confidence scoring
- **Income & Market Research**: Salary benchmarking and market analysis
- **Job Searching & Filtering**: Multi-source job search with intelligent filtering
- **Three-Tier Recommendations**: Conservative, Optimal, and Stretch opportunities
- **Application Strategy Creation**: Customized application approaches
- **Results Formatting**: Professional presentation of recommendations

### ⚡ Performance Optimization
- **Result Caching**: Intelligent caching with TTL for improved performance
- **Parallel Processing**: Concurrent execution of workflow steps
- **Performance Monitoring**: Real-time metrics and performance tracking
- **Target Processing Time**: <8 seconds for complete workflow

### 🛡️ Robust Error Handling
- **Graceful Degradation**: Fallback mechanisms for component failures
- **Comprehensive Logging**: Detailed error tracking and debugging
- **Recovery Mechanisms**: Automatic retry and fallback strategies
- **Error Classification**: Severity-based error handling

### 📊 Analytics & Monitoring
- **User Behavior Tracking**: Complete analytics for user interactions
- **Performance Metrics**: System health and performance monitoring
- **Success Rate Tracking**: Recommendation accuracy and user satisfaction
- **Real-time Dashboards**: Live monitoring of system performance

## Architecture

### Core Components

```
MingusJobRecommendationEngine
├── Resume Parser (Advanced + Basic fallback)
├── Job Matcher (Income-focused search)
├── Three-Tier Selector (Risk/reward categorization)
├── Analytics Tracker (User behavior & metrics)
├── Cache Manager (Performance optimization)
└── Error Handler (Graceful degradation)
```

### Workflow Steps

1. **Resume Parsing** → Extract structured data and analyze skills
2. **Market Research** → Perform income and market analysis
3. **Job Search** → Find relevant job opportunities
4. **Recommendation Generation** → Create three-tier recommendations
5. **Strategy Creation** → Develop application strategies
6. **Results Formatting** → Format and present final results

## Installation & Setup

### Prerequisites

```bash
# Required Python packages
pip install asyncio sqlite3 flask flask-cors aiohttp
```

### Database Setup

The engine automatically initializes the required database tables:

- `workflow_sessions` - Session tracking
- `workflow_steps` - Step-by-step execution tracking
- `user_analytics` - User behavior analytics
- `performance_metrics` - System performance data
- `recommendation_cache` - Result caching

### Basic Usage

```python
from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine

# Initialize the engine
engine = MingusJobRecommendationEngine()

# Process a resume completely
result = await engine.process_resume_completely(
    resume_content="Your resume text here...",
    user_id="user123",
    location="New York",
    preferences={
        "remote_ok": True,
        "max_commute_time": 30,
        "must_have_benefits": ["health insurance", "401k"]
    }
)

# Check results
if result['success']:
    recommendations = result['recommendations']
    tier_summary = result['tier_summary']
    action_plan = result['action_plan']
else:
    print(f"Error: {result['error_message']}")
```

## API Endpoints

### Process Resume
```http
POST /api/recommendations/process-resume
Content-Type: application/json

{
    "resume_content": "Resume text content...",
    "user_id": "user123",
    "file_name": "resume.pdf",
    "location": "New York",
    "preferences": {
        "remote_ok": true,
        "max_commute_time": 30,
        "must_have_benefits": ["health insurance", "401k"],
        "company_size_preference": "mid",
        "industry_preference": "technology",
        "equity_required": false,
        "min_company_rating": 3.5
    }
}
```

### Get Processing Status
```http
GET /api/recommendations/status/{session_id}
```

### Track Analytics
```http
POST /api/recommendations/analytics
Content-Type: application/json

{
    "user_id": "user123",
    "session_id": "session456",
    "event_type": "recommendation_viewed",
    "event_data": {
        "recommendation_id": "rec123",
        "tier": "optimal",
        "action": "viewed"
    }
}
```

### Performance Metrics
```http
GET /api/recommendations/performance
```

### Health Check
```http
GET /api/recommendations/health
```

## Configuration

### Performance Targets

```python
performance_targets = {
    'total_time': 8.0,              # Maximum processing time (seconds)
    'recommendation_accuracy': 0.90, # 90%+ relevant matches
    'system_reliability': 0.995     # 99.5% uptime
}
```

### Cache Configuration

```python
cache_ttl = 3600  # 1 hour cache TTL
max_processing_time = 8.0  # 8 seconds max processing time
```

### Error Handling

```python
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

## Response Format

### Successful Response

```json
{
    "success": true,
    "session_id": "user123_abc123_20240101_120000",
    "processing_time": 6.5,
    "recommendations": {
        "conservative": [
            {
                "job": {
                    "job_id": "job123",
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "location": "New York",
                    "salary_median": 95000
                },
                "tier": "conservative",
                "success_probability": 0.85,
                "salary_increase_potential": 0.18,
                "skills_gap_analysis": [...],
                "application_strategy": {...},
                "preparation_roadmap": {...}
            }
        ],
        "optimal": [...],
        "stretch": [...]
    },
    "tier_summary": {
        "conservative": {
            "count": 3,
            "avg_salary_increase": 18.5,
            "avg_success_probability": 85.2,
            "description": "Similar roles, established companies"
        }
    },
    "application_strategies": {...},
    "insights": {...},
    "action_plan": {...},
    "next_steps": [...],
    "processing_metrics": {
        "total_time": 6.5,
        "resume_parsing_time": 1.2,
        "job_search_time": 2.1,
        "recommendation_generation_time": 2.8,
        "cache_hit_rate": 0.15
    }
}
```

### Error Response

```json
{
    "success": false,
    "error_type": "resume_parsing_failed",
    "error_message": "Resume content is too short or empty",
    "timestamp": "2024-01-01T12:00:00Z",
    "processing_metrics": {...}
}
```

## Advanced Usage

### Custom Search Criteria

```python
from backend.utils.income_boost_job_matcher import SearchCriteria, CareerField, ExperienceLevel

criteria = SearchCriteria(
    current_salary=80000,
    target_salary_increase=0.30,
    career_field=CareerField.TECHNOLOGY,
    experience_level=ExperienceLevel.SENIOR,
    preferred_msas=["New York", "San Francisco"],
    remote_ok=True,
    max_commute_time=45,
    must_have_benefits=["health insurance", "401k", "equity"],
    company_size_preference="mid",
    industry_preference="technology",
    equity_required=True,
    min_company_rating=4.0
)
```

### Analytics Tracking

```python
# Track user interactions
await engine._track_analytics(
    user_id="user123",
    session_id="session456",
    event_type="recommendation_clicked",
    event_data={
        "recommendation_id": "rec123",
        "tier": "optimal",
        "action": "view_details"
    }
)
```

### Performance Monitoring

```python
# Get current metrics
metrics = engine.metrics
print(f"Total processing time: {metrics.total_time}s")
print(f"Cache hit rate: {metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses)}")
print(f"Error count: {metrics.errors_count}")
```

## Testing

### Unit Tests

```bash
python test_mingus_recommendation_engine.py
```

### Performance Tests

```bash
# Run performance validation
python -c "
import asyncio
from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine

async def test_performance():
    engine = MingusJobRecommendationEngine()
    start_time = time.time()
    
    result = await engine.process_resume_completely(
        resume_content='Sample resume content...',
        user_id='perf_test'
    )
    
    processing_time = time.time() - start_time
    print(f'Processing time: {processing_time:.2f}s')
    print(f'Target: < 8.0s')
    print(f'Status: {\"PASS\" if processing_time < 8.0 else \"FAIL\"}')

asyncio.run(test_performance())
"
```

## Monitoring & Maintenance

### Health Checks

The engine provides comprehensive health monitoring:

- **Database Connectivity**: SQLite connection status
- **Component Availability**: All sub-components status
- **Performance Metrics**: Real-time processing statistics
- **Error Rates**: Success/failure tracking

### Cache Management

```python
# Clear cache
await engine.clear_cache()

# Get cache statistics
cache_stats = await engine.get_cache_stats()
```

### Performance Optimization

1. **Caching Strategy**: Results are cached with TTL for repeated requests
2. **Parallel Processing**: Multiple workflow steps run concurrently
3. **Database Optimization**: Indexed queries and efficient data structures
4. **Memory Management**: Efficient object lifecycle management

## Troubleshooting

### Common Issues

1. **Processing Timeout**
   - Check system resources
   - Verify database connectivity
   - Review error logs

2. **Resume Parsing Failures**
   - Ensure resume content is valid
   - Check file format compatibility
   - Review parsing confidence scores

3. **Job Search Errors**
   - Verify API connectivity
   - Check search criteria validity
   - Review rate limiting

4. **Cache Issues**
   - Clear cache if corrupted
   - Check cache TTL settings
   - Verify database permissions

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with detailed output
result = await engine.process_resume_completely(
    resume_content=content,
    user_id="debug_user",
    debug=True
)
```

## Performance Benchmarks

### Target Metrics

- **Processing Time**: < 8 seconds
- **Recommendation Accuracy**: 90%+ relevant matches
- **System Reliability**: 99.5% uptime
- **Cache Hit Rate**: > 60% for repeated requests
- **Error Rate**: < 5% for valid inputs

### Load Testing

```python
# Concurrent processing test
import asyncio

async def load_test():
    engine = MingusJobRecommendationEngine()
    
    # Test with 10 concurrent requests
    tasks = [
        engine.process_resume_completely(
            resume_content=f"Resume {i}",
            user_id=f"user_{i}"
        )
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = len([r for r in results if isinstance(r, dict) and r.get('success')])
    print(f"Success rate: {successful}/10")

asyncio.run(load_test())
```

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies
3. Run tests
4. Make changes
5. Test thoroughly
6. Submit pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add comprehensive docstrings
- Include unit tests
- Update documentation

## License

This project is part of the Mingus Personal Finance Application and follows the same licensing terms.

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information
4. Contact the development team

---

**Note**: This engine is designed to handle high-volume processing while maintaining performance targets. Monitor system resources and adjust configuration as needed for your specific use case.
