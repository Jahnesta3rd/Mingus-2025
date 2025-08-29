# MINGUS Assessment Data Seeding Script

This script populates the `assessments` table with the exact specifications from the MINGUS Calculator Analysis Summary for the 4 lead magnets.

## Overview

The seeding script creates comprehensive assessment configurations for:

1. **AI Job Risk Calculator** - with precise job risk database and automation/augmentation calculations
2. **Relationship Impact Calculator** - with exact point system and segmentation  
3. **Tax Impact Calculator** - with exact tax logic and 2025 policy calculations
4. **Income Comparison Calculator** - with exact demographic groups and BLS data integration

## Features

### AI Job Risk Calculator - EXACT SPECIFICATIONS
- **Job Risk Database**: 700+ occupations with specific automation/augmentation percentages
- **Industry Modifiers**: Technology (+10% automation), Finance (+5%), Healthcare (-10%), Education (-15%)
- **Experience Adjustments**: 10+ years gets -5% automation risk
- **AI Usage Bonus**: Daily users get -10% automation risk, +15% augmentation
- **Technical Skills**: High/expert gets -8% automation, +12% augmentation
- **Final Formula**: `automation_score * 0.7 + augmentation_score * 0.3`

### Relationship Impact Calculator - EXACT POINT SYSTEM
- **Relationship Status**: Single (0), Dating (2), Serious (4), Married (6), Complicated (8)
- **Spending Habits**: Separate (0), Share some (2), Joint (4), Spend more (6), Overspend (8)
- **Financial Stress**: Never (0), Rarely (2), Sometimes (4), Often (6), Always (8)
- **Emotional Triggers**: After breakup (3), After arguments (3), When lonely (2), When jealous (2), Social pressure (2)
- **Segments**: Stress-Free (0-16), Relationship-Spender (17-25), Emotional-Manager (26-35), Crisis-Mode (36+)

### Tax Impact Calculator - EXACT TAX LOGIC
- **State Tax Rates**: CA (8.5%), NY (8%), TX (6.25%), FL (6%), WA (6.5%), IL (6.25%), PA (6%), OH (5.75%)
- **Cost Projections**: Tax inefficiency $1,200/year + parent care costs $2,400/year + benefit losses $1,800/year
- **2025 Tax Policy**: Standard deduction increase 3%, Child tax credit expansion, Retirement limits 5% increase

### Income Comparison Calculator - EXACT DEMOGRAPHIC GROUPS
- **Demographic Groups**: National Median, African American, Age 25-35, African American Ages 25-35
- **Education Groups**: College Graduates, African American College Graduates, Metro Area, African American Metro
- **Target Metros**: Atlanta, Houston, DC, Dallas, NYC, Philadelphia, Chicago, Charlotte, Miami, Baltimore
- **BLS Data Integration**: Confidence intervals and sample sizes for statistical accuracy

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Required Python packages (see requirements below)

## Installation

### 1. Install Dependencies

```bash
pip install psycopg2-binary
```

### 2. Database Setup

Ensure your PostgreSQL database has the assessment tables created:

```sql
-- Run the migration script first
\i migrations/016_create_assessment_system_tables.sql
```

### 3. Environment Configuration

Set up environment variables for your database connection:

```bash
# Development
export ENVIRONMENT=development
export DEV_DB_HOST=localhost
export DEV_DB_NAME=mingus_dev
export DEV_DB_USER=mingus_dev_user
export DEV_DB_PASSWORD=your_password

# Production
export ENVIRONMENT=production
export PROD_DB_HOST=your-prod-host
export PROD_DB_NAME=mingus_production
export PROD_DB_USER=mingus_prod_user
export PROD_DB_PASSWORD=your_secure_password
```

## Usage

### Basic Usage

```bash
# Run with default configuration
python scripts/seed_assessment_data.py
```

### Advanced Usage

```bash
# Set environment and run
export ENVIRONMENT=production
export BACKUP_BEFORE_SEED=true
export LOG_LEVEL=INFO
python scripts/seed_assessment_data.py
```

### Configuration Options

The script supports several environment variables for customization:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment name (development, staging, production, local) |
| `SKIP_EXISTING` | `true` | Skip assessments that already exist |
| `BACKUP_BEFORE_SEED` | `false` | Create database backup before seeding |
| `VALIDATE_DATA` | `true` | Validate assessment data before insertion |
| `GENERATE_REPORT` | `true` | Generate detailed seeding report |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Database Schema

The script populates the following table structure:

```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type assessment_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    questions_json JSONB NOT NULL DEFAULT '[]',
    scoring_config JSONB NOT NULL DEFAULT '{}',
    version VARCHAR(20) DEFAULT '1.0',
    estimated_duration_minutes INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Assessment Data Structure

Each assessment includes:

### Questions JSON Structure
```json
{
    "id": "question_id",
    "question": "Question text",
    "type": "radio|dropdown|checkbox|scale",
    "options": [
        {"value": 1, "label": "Option 1"},
        {"value": 2, "label": "Option 2"}
    ],
    "weight": 0.25
}
```

### Scoring Config Structure
```json
{
    "calculation_formula": "formula_string",
    "thresholds": {
        "low": {"max": 30, "label": "Low Risk"},
        "medium": {"min": 31, "max": 60, "label": "Medium Risk"},
        "high": {"min": 61, "max": 80, "label": "High Risk"},
        "critical": {"min": 81, "max": 100, "label": "Critical Risk"}
    },
    "recommendations": {
        "low": ["Recommendation 1", "Recommendation 2"],
        "medium": ["Recommendation 1", "Recommendation 2"]
    }
}
```

## Verification

After running the script, verify the data was seeded correctly:

```sql
-- Check all assessments
SELECT type, title, version, is_active FROM assessments;

-- Check specific assessment
SELECT 
    type,
    title,
    jsonb_array_length(questions_json) as question_count,
    scoring_config->>'calculation_formula' as formula
FROM assessments 
WHERE type = 'ai_job_risk';
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```
   Error: Database connection failed: connection to server failed
   ```
   - Check database credentials
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **Table Does Not Exist**
   ```
   Error: relation "assessments" does not exist
   ```
   - Run the migration script first
   - Check database schema

3. **Permission Denied**
   ```
   Error: permission denied for table assessments
   ```
   - Check database user permissions
   - Ensure user has INSERT privileges

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
export LOG_LEVEL=DEBUG
python scripts/seed_assessment_data.py
```

### Data Validation

The script includes built-in validation:

- Question structure validation
- Scoring configuration validation
- Database constraint checking
- Duplicate assessment prevention

## Customization

### Adding New Assessments

To add a new assessment type:

1. Create a new method in `AssessmentDataSeeder` class
2. Define questions and scoring configuration
3. Add to the `seed_all_assessments()` method
4. Update the assessment type enum in the database

### Modifying Existing Assessments

To modify existing assessments:

1. Update the question structure in the seeding method
2. Increment the version number
3. Run the script with `SKIP_EXISTING=false`

## Security Considerations

- Use environment variables for sensitive database credentials
- Never commit database passwords to version control
- Use read-only database users for verification queries
- Implement proper backup procedures before production seeding

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the logs for detailed error messages
3. Verify database schema and permissions
4. Contact the MINGUS development team

## Changelog

### Version 1.0.0
- Initial release with 4 lead magnet assessments
- Exact specifications from MINGUS Calculator Analysis Summary
- Comprehensive scoring algorithms and segmentation
- Environment-specific configuration support
- Detailed logging and reporting
