# Assessment System Migration Documentation

## Overview

Migration `016_create_assessment_system_tables.sql` adds comprehensive assessment functionality to the Mingus application's PostgreSQL schema. This migration creates a flexible, scalable assessment system that supports multiple assessment types with detailed analytics and personalized recommendations.

## Migration Files

- **`016_create_assessment_system_tables.sql`** - Main migration file
- **`016_create_assessment_system_tables_rollback.sql`** - Rollback migration file
- **`ASSESSMENT_SYSTEM_MIGRATION_README.md`** - This documentation file

## Database Schema

### 1. `assessments` Table

**Purpose**: Stores assessment templates and configurations

**Key Fields**:
- `id` (UUID) - Primary key
- `type` (assessment_type enum) - Assessment category
- `title` (VARCHAR) - Assessment title
- `questions_json` (JSONB) - Assessment questions and options
- `scoring_config` (JSONB) - Scoring logic and formulas
- `is_active` (BOOLEAN) - Whether assessment is available
- `allow_anonymous` (BOOLEAN) - Whether anonymous users can take assessment

**Assessment Types**:
- `ai_job_risk` - AI automation risk assessment
- `relationship_impact` - Relationship and money impact assessment
- `tax_impact` - Tax efficiency assessment
- `income_comparison` - Income and market position assessment

### 2. `user_assessments` Table

**Purpose**: Stores individual assessment attempts and responses

**Key Fields**:
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users table (nullable for anonymous)
- `assessment_id` (UUID) - Foreign key to assessments table
- `responses_json` (JSONB) - User's answers to questions
- `score` (INTEGER) - Calculated assessment score (0-100)
- `risk_level` (risk_level_type enum) - Risk classification
- `completed_at` (TIMESTAMP) - When assessment was completed

**Anonymous User Support**:
- `email` (VARCHAR) - For anonymous users
- `first_name` (VARCHAR) - For anonymous users
- `last_name` (VARCHAR) - For anonymous users
- `location` (VARCHAR) - Optional location data
- `job_title` (VARCHAR) - Optional job information
- `industry` (VARCHAR) - Optional industry data

### 3. `assessment_results` Table

**Purpose**: Stores detailed analysis and personalized recommendations

**Key Fields**:
- `id` (UUID) - Primary key
- `user_assessment_id` (UUID) - Foreign key to user_assessments table
- `insights_json` (JSONB) - Personalized insights
- `recommendations_json` (JSONB) - Action items and recommendations

**Assessment-Specific Fields**:

**AI Job Risk Assessment**:
- `automation_score` (INTEGER) - Automation risk score
- `augmentation_score` (INTEGER) - AI augmentation potential

**Relationship Impact Assessment**:
- `relationship_stress_score` (INTEGER) - Relationship stress level
- `financial_harmony_score` (INTEGER) - Financial harmony score

**Tax Impact Assessment**:
- `tax_efficiency_score` (INTEGER) - Tax efficiency score
- `potential_savings` (DECIMAL) - Potential tax savings
- `tax_optimization_opportunities` (JSONB) - Optimization opportunities

**Income Comparison Assessment**:
- `market_position_score` (INTEGER) - Market position score
- `salary_benchmark_data` (JSONB) - Salary benchmark information
- `negotiation_leverage_points` (JSONB) - Negotiation strategies

**General Fields**:
- `cost_projections` (JSONB) - Financial impact calculations
- `risk_factors` (JSONB) - Identified risk factors
- `mitigation_strategies` (JSONB) - Risk mitigation strategies

## Performance Indexes

The migration creates 15 performance indexes:

### Assessments Table Indexes
- `idx_assessments_type` - Assessment type queries
- `idx_assessments_active` - Active assessments only
- `idx_assessments_version` - Version-based queries
- `idx_assessments_created_at` - Creation date queries

### User Assessments Table Indexes
- `idx_user_assessments_user_id` - User-specific queries
- `idx_user_assessments_assessment_id` - Assessment-specific queries
- `idx_user_assessments_email` - Anonymous user queries
- `idx_user_assessments_completed_at` - Completion date queries
- `idx_user_assessments_risk_level` - Risk level filtering
- `idx_user_assessments_score` - Score-based queries
- `idx_user_assessments_session_id` - Session tracking
- `idx_user_assessments_started_at` - Start date queries

### Composite Indexes
- `idx_user_assessments_user_complete` - User completion status
- `idx_user_assessments_assessment_complete` - Assessment completion status
- `idx_user_assessments_email_complete` - Anonymous completion status

### Assessment Results Table Indexes
- `idx_assessment_results_user_assessment_id` - User assessment queries
- `idx_assessment_results_automation_score` - AI automation scores
- `idx_assessment_results_augmentation_score` - AI augmentation scores
- `idx_assessment_results_relationship_stress` - Relationship stress scores
- `idx_assessment_results_financial_harmony` - Financial harmony scores
- `idx_assessment_results_tax_efficiency` - Tax efficiency scores
- `idx_assessment_results_market_position` - Market position scores
- `idx_assessment_results_created_at` - Creation date queries

## Database Views

### `assessment_completion_stats`
Provides aggregated statistics for assessment completion rates, average scores, and risk level distributions.

**Key Metrics**:
- Total attempts vs completed attempts
- Completion rate percentage
- Average score per assessment
- Average time spent
- Risk level distribution counts

### `user_assessment_history`
Provides a comprehensive view of user assessment history with insights and recommendations.

**Key Data**:
- User identification (ID or email)
- Assessment type and title
- Scores and risk levels
- Completion timestamps
- Time spent
- Insights and recommendations

## Database Functions

### `calculate_assessment_score(p_responses_json JSONB, p_scoring_config JSONB)`
Calculates assessment scores based on user responses and scoring configuration.

**Features**:
- Weighted scoring system
- Formula-based calculations
- Score normalization (0-100 range)
- Configurable scoring logic

### `determine_risk_level(p_score INTEGER, p_assessment_type assessment_type)`
Determines risk levels based on assessment scores and type.

**Risk Levels**:
- `low` - Low risk/impact
- `medium` - Medium risk/impact
- `high` - High risk/impact
- `critical` - Critical risk/impact

**Assessment-Specific Logic**:
- AI Job Risk: Higher scores = higher risk
- Relationship Impact: Higher scores = higher stress
- Tax Impact: Higher scores = lower risk (better efficiency)
- Income Comparison: Higher scores = lower risk (better position)

## Default Assessment Templates

The migration includes four pre-configured assessment templates:

### 1. AI Job Risk Assessment
**Purpose**: Evaluate job vulnerability to AI automation
**Questions**: 5 questions about task automation, creativity, human interaction, industry adoption, and expertise
**Duration**: 5 minutes
**Scoring**: Weighted formula with automation risk calculation

### 2. Relationship Impact Assessment
**Purpose**: Understand relationship effects on financial decisions
**Questions**: 5 questions about relationship-based spending, financial stress, conflict avoidance, communication, and emotional spending
**Duration**: 5 minutes
**Scoring**: Relationship stress and financial harmony calculations

### 3. Tax Impact Assessment
**Purpose**: Evaluate tax efficiency and optimization opportunities
**Questions**: 5 questions about tax-advantaged accounts, tax knowledge, side income, work expenses, and tax strategy review
**Duration**: 5 minutes
**Scoring**: Tax efficiency score with potential savings calculation

### 4. Income Comparison Assessment
**Purpose**: Compare compensation to market standards
**Questions**: 5 questions about role tenure, skill growth, salary competitiveness, negotiation confidence, and market knowledge
**Duration**: 5 minutes
**Scoring**: Market position score with negotiation leverage calculation

## Data Validation

### Constraints
- **JSONB Validation**: Ensures proper JSON structure for all JSONB fields
- **Score Ranges**: Validates scores are within 0-100 range
- **Time Validation**: Ensures positive time values
- **User Validation**: Requires either user_id or email+first_name for anonymous users
- **Completion Logic**: Ensures completion status matches completion timestamp

### Foreign Key Relationships
- `user_assessments.user_id` → `users.id` (SET NULL on delete)
- `user_assessments.assessment_id` → `assessments.id` (CASCADE on delete)
- `assessment_results.user_assessment_id` → `user_assessments.id` (CASCADE on delete)

## Security Features

### Row-Level Security
- Anonymous user support with email validation
- Session-based tracking for security
- IP address and user agent logging
- Assessment attempt limits per user

### Data Privacy
- Optional user authentication
- Anonymous assessment support
- Secure JSONB storage for sensitive data
- Audit trail with timestamps

## Usage Examples

### Creating a New Assessment
```sql
INSERT INTO assessments (type, title, description, questions_json, scoring_config)
VALUES (
    'ai_job_risk',
    'Custom AI Risk Assessment',
    'Custom assessment for specific industry',
    '[...]'::jsonb,
    '{...}'::jsonb
);
```

### Recording User Assessment
```sql
INSERT INTO user_assessments (
    user_id, 
    assessment_id, 
    responses_json, 
    score, 
    risk_level,
    completed_at,
    is_complete
)
VALUES (
    'user-uuid',
    'assessment-uuid',
    '{"question1": "answer1"}'::jsonb,
    75,
    'medium',
    NOW(),
    true
);
```

### Querying Assessment Results
```sql
SELECT 
    ua.score,
    ua.risk_level,
    ar.insights_json,
    ar.recommendations_json
FROM user_assessments ua
LEFT JOIN assessment_results ar ON ua.id = ar.user_assessment_id
WHERE ua.user_id = 'user-uuid'
AND ua.is_complete = true;
```

## Migration Safety

### Rollback Support
The rollback migration safely removes all created objects:
- Drops views and functions
- Removes triggers
- Drops tables in correct order (respecting foreign keys)
- Removes enum types

### Data Preservation
- Uses `IF NOT EXISTS` clauses to prevent conflicts
- Uses `ON CONFLICT DO NOTHING` for template insertions
- Preserves existing data during migration

### Performance Considerations
- Uses `CONCURRENTLY` for index creation to avoid locks
- Includes comprehensive indexing strategy
- Optimized for common query patterns

## Integration with Existing System

### Compatibility
- Follows existing Mingus database patterns
- Uses UUID primary keys for consistency
- Compatible with existing user management system
- Supports both authenticated and anonymous users

### Extensibility
- JSONB fields allow flexible data storage
- Enum types can be extended for new assessment types
- Scoring formulas are configurable
- Template system supports easy customization

## Monitoring and Analytics

### Built-in Views
- Assessment completion statistics
- User assessment history
- Risk level distributions
- Performance metrics

### Key Metrics
- Completion rates by assessment type
- Average scores and time spent
- Risk level distributions
- User engagement patterns

## Future Enhancements

### Potential Extensions
- Multi-language support
- Assessment branching logic
- Real-time scoring
- Integration with external APIs
- Advanced analytics dashboards
- Assessment versioning system

### Scalability Considerations
- Partitioning for large datasets
- Caching strategies
- Read replicas for analytics
- Horizontal scaling support

## Support and Maintenance

### Regular Maintenance
- Monitor index performance
- Review assessment completion rates
- Analyze user feedback patterns
- Update assessment templates as needed

### Troubleshooting
- Check constraint violations
- Monitor JSONB field sizes
- Review foreign key relationships
- Validate scoring calculations

---

**Migration Version**: 016  
**Created**: January 2025  
**Author**: MINGUS Development Team  
**Status**: Ready for deployment
