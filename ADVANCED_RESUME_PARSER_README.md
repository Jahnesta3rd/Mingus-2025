# Advanced Resume Parser for Mingus Financial App

## Overview

The Advanced Resume Parser is a sophisticated resume analysis system designed specifically for African American professionals aged 25-35 earning $40k-$100k in major metro areas. It extends the existing ResumeParser with advanced analytics including career field classification, experience level detection, career trajectory analysis, skills categorization, leadership indicators, and income potential calculation.

## Target Demographic

- **Age Range**: 25-35 years old
- **Income Range**: $40k-$100k annually
- **Geographic Focus**: Major metropolitan areas
- **Demographic**: African American professionals
- **Career Focus**: Career advancement and financial growth

## Features

### Core Functionality

1. **Career Field Classification**
   - Identifies primary career field from resume content
   - Supports 13+ career categories including Technology, Finance, Healthcare, Education, Marketing, Sales, Consulting, Real Estate, Legal, Non-Profit, Government, Retail, and Manufacturing
   - Uses keyword-based analysis with confidence scoring

2. **Experience Level Detection**
   - Calculates years of experience from work history
   - Analyzes job titles for seniority indicators
   - Classifies as Entry, Mid, Senior, or Executive level
   - Considers both quantitative (years) and qualitative (title) factors

3. **Career Trajectory Analysis**
   - Tracks growth patterns and promotion frequency
   - Analyzes role advancement and industry consistency
   - Identifies leadership development over time
   - Provides insights into career progression

4. **Skills Categorization**
   - Separates skills into Technical, Soft Skills, Leadership, Financial, Communication, and Analytical categories
   - Uses comprehensive keyword matching
   - Provides detailed skill breakdown for career planning

5. **Leadership Indicators**
   - Extracts management and leadership experience
   - Analyzes responsibility keywords and team size indicators
   - Calculates leadership score based on multiple factors
   - Identifies potential for leadership roles

6. **Income Potential Calculation**
   - Estimates current market value based on experience, skills, and location
   - Applies industry and location multipliers
   - Considers leadership experience in salary calculation
   - Provides market value range and growth potential

### File Format Support

- **PDF**: Using PyPDF2 or pdfplumber
- **DOCX**: Using python-docx
- **TXT**: Native text file support
- **Error Handling**: Comprehensive error handling for all formats

## Installation

### Prerequisites

```bash
pip install -r requirements_advanced_resume_parser.txt
```

### Required Dependencies

```
Flask==2.3.3
PyPDF2==3.0.1
pdfplumber==0.9.0
python-docx==0.8.11
pandas==2.0.3
numpy==1.24.3
nltk==3.8.1
scikit-learn==1.3.0
python-dateutil==2.8.2
```

## Usage

### Basic Usage

```python
from backend.utils.advanced_resume_parser import AdvancedResumeParser

# Initialize parser
parser = AdvancedResumeParser()

# Parse resume with advanced analytics
result = parser.parse_resume_advanced(
    content=resume_content,
    file_name="resume.txt",
    location="New York"
)

# Access results
if result['success']:
    parsed_data = result['parsed_data']
    advanced_analytics = result['advanced_analytics']
    
    print(f"Career Field: {advanced_analytics['career_field']}")
    print(f"Experience Level: {advanced_analytics['experience_level']}")
    print(f"Estimated Salary: ${advanced_analytics['income_potential']['estimated_current_salary']:,.0f}")
```

### File Upload Usage

```python
from backend.utils.resume_format_handler import AdvancedResumeParserWithFormats

# Initialize parser with format support
parser = AdvancedResumeParserWithFormats()

# Parse resume from file
result = parser.parse_resume_file(
    file_path="path/to/resume.pdf",
    location="Atlanta"
)

# Parse resume from bytes
with open("resume.docx", "rb") as f:
    file_bytes = f.read()

result = parser.parse_resume_from_bytes(
    file_bytes=file_bytes,
    file_name="resume.docx",
    location="Houston"
)
```

### API Usage

#### Parse Resume Content

```bash
curl -X POST http://localhost:5000/api/resume/parse-advanced \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: your-token" \
  -d '{
    "content": "Resume content here...",
    "file_name": "resume.txt",
    "location": "New York",
    "user_id": "user123"
  }'
```

#### Parse Resume File

```bash
curl -X POST http://localhost:5000/api/resume/parse-file \
  -H "X-CSRF-Token: your-token" \
  -F "file=@resume.pdf" \
  -F "location=Atlanta" \
  -F "user_id=user123"
```

#### Get Analytics Summary

```bash
curl -X GET http://localhost:5000/api/resume/analytics/summary
```

## API Endpoints

### POST /api/resume/parse-advanced
Parse resume content with advanced analytics

**Request Body:**
```json
{
  "content": "Resume text content",
  "file_name": "resume.txt",
  "location": "New York",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "resume_id": 123,
  "parsed_data": { ... },
  "advanced_analytics": {
    "career_field": "Technology",
    "experience_level": "Mid Level",
    "career_trajectory": { ... },
    "skills_categorized": { ... },
    "leadership_indicators": { ... },
    "income_potential": { ... }
  },
  "metadata": { ... }
}
```

### POST /api/resume/parse-file
Parse uploaded resume file with advanced analytics

**Request:** Multipart form data with file upload

**Response:** Same as parse-advanced endpoint

### GET /api/resume/analytics/<resume_id>
Get advanced analytics for a specific resume

### GET /api/resume/analytics/summary
Get summary statistics across all parsed resumes

## Advanced Analytics Details

### Career Field Classification

The system analyzes resume content to identify the primary career field using keyword matching across 13+ categories:

- **Technology**: Software, development, programming, IT
- **Finance**: Banking, investment, accounting, financial analysis
- **Healthcare**: Medical, nursing, healthcare administration
- **Education**: Teaching, academic, educational technology
- **Marketing**: Digital marketing, advertising, brand management
- **Sales**: B2B sales, account management, business development
- **Consulting**: Management consulting, advisory services
- **Real Estate**: Property, brokerage, real estate development
- **Legal**: Attorney, legal counsel, compliance
- **Non-Profit**: Foundation, charity, social impact
- **Government**: Public sector, policy, administration
- **Retail**: Merchandising, store management, e-commerce
- **Manufacturing**: Production, operations, supply chain

### Experience Level Detection

Combines quantitative and qualitative analysis:

- **Entry Level**: 0-2 years experience, junior titles
- **Mid Level**: 3-5 years experience, specialist/analyst titles
- **Senior Level**: 6-9 years experience, senior/lead titles
- **Executive Level**: 10+ years experience, management titles

### Skills Categorization

Skills are automatically categorized into:

- **Technical**: Programming, software, technical tools
- **Soft Skills**: Communication, teamwork, problem-solving
- **Leadership**: Management, mentoring, team building
- **Financial**: Financial analysis, budgeting, accounting
- **Communication**: Writing, presentation, public speaking
- **Analytical**: Data analysis, research, metrics

### Income Potential Calculation

Uses multiple factors to estimate market value:

- **Base Salary**: Based on experience level
- **Industry Multiplier**: Varies by career field
- **Location Multiplier**: Cost of living adjustment
- **Experience Multiplier**: Years of experience bonus
- **Leadership Multiplier**: Management experience bonus

## Testing

### Run Test Suite

```bash
python test_advanced_resume_parser.py
```

The test suite includes sample resumes representing the target demographic with various career fields and experience levels.

### Sample Test Results

```
🎯 ADVANCED RESUME PARSER TESTING
============================================================
Target Demographic: African American professionals aged 25-35
Income Range: $40k-$100k in major metro areas
============================================================

📄 TESTING RESUME 1: Marcus Johnson - Software Engineer (Atlanta)
--------------------------------------------------
✅ Parsing successful!
📊 Basic Parsing Results:
   • Name: MARCUS JOHNSON
   • Email: marcus.johnson@email.com
   • Experience Entries: 3
   • Skills Count: 15
   • Confidence Score: 85.50

🎯 Advanced Analytics:
   • Career Field: Technology
   • Experience Level: Mid Level
   • Growth Pattern: Upward trajectory
   • Promotion Frequency: 0.75/year
   • Industry Consistency: Yes
   • Leadership Development: Yes
   • Technical Skills: 12
   • Soft Skills: 3
   • Leadership Skills: 5
   • Leadership Score: 0.65
   • Estimated Salary: $78,500
   • Market Range: $66,725 - $90,275
   • Growth Potential: 0.75
```

## Database Schema

The system uses SQLite with the following key tables:

### resume_parsing_results
- `id`: Primary key
- `user_id`: User identifier
- `file_name`: Original file name
- `file_hash`: MD5 hash for deduplication
- `raw_content`: Original resume content
- `parsed_data`: JSON of basic parsed data
- `advanced_analytics`: JSON of advanced analytics
- `confidence_score`: Parsing confidence (0-100)
- `processing_time`: Processing duration in seconds
- `created_at`: Timestamp

### resume_analytics
- `id`: Primary key
- `resume_id`: Foreign key to resume_parsing_results
- `action`: Analytics action type
- `data`: JSON of analytics data
- `created_at`: Timestamp

## Error Handling

The system includes comprehensive error handling:

- **File Format Errors**: Unsupported formats, corrupted files
- **Parsing Errors**: Invalid content, extraction failures
- **Database Errors**: Connection issues, constraint violations
- **API Errors**: Invalid requests, authentication failures

All errors are logged and returned with appropriate HTTP status codes.

## Performance Considerations

- **Caching**: Results are cached based on file hash
- **Rate Limiting**: API endpoints include rate limiting
- **Database Indexing**: Optimized queries for analytics
- **Memory Management**: Efficient text processing
- **Async Processing**: Background processing for large files

## Security Features

- **CSRF Protection**: All API endpoints require CSRF tokens
- **Input Validation**: Comprehensive input sanitization
- **File Upload Security**: Secure file handling
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: Protection against abuse

## Future Enhancements

1. **Machine Learning Integration**: Enhanced classification using ML models
2. **Natural Language Processing**: Advanced text analysis with NLP
3. **Industry-Specific Analysis**: Specialized analysis for different industries
4. **Salary Benchmarking**: Integration with salary databases
5. **Career Recommendations**: AI-powered career advice
6. **Skills Gap Analysis**: Identify missing skills for career advancement
7. **Resume Optimization**: Suggestions for resume improvement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is part of the Mingus Financial App and follows the same licensing terms.

## Support

For support or questions about the Advanced Resume Parser, please contact the development team or create an issue in the repository.
