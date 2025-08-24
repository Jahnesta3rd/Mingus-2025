# User Profile Fields Documentation

## Overview

This document describes the comprehensive user profile fields that have been added to the `users` table in the Mingus application database. These fields enable enhanced personalization, better financial planning, and improved user experience.

## Migration Information

- **Migration File**: `migrations/012_add_comprehensive_user_fields.sql`
- **Rollback File**: `migrations/012_add_comprehensive_user_fields_rollback.sql`
- **Applied Date**: 2025-01-27
- **Total New Fields**: 25 fields across 6 categories

## Field Categories

### 1. Personal Information

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `first_name` | VARCHAR(50) | User's first name | None |
| `last_name` | VARCHAR(50) | User's last name | None |
| `date_of_birth` | DATE | User's date of birth | None |
| `zip_code` | VARCHAR(10) | User's zip code | Format: 5 digits or 5+4 format |
| `phone_number` | VARCHAR(20) | User's phone number | International format |
| `email_verification_status` | BOOLEAN | Email verification status | Default: FALSE |

### 2. Financial Data

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `monthly_income` | DECIMAL(10,2) | Monthly income amount | None |
| `income_frequency` | ENUM | How often income is received | weekly, bi-weekly, semi-monthly, monthly, annually |
| `primary_income_source` | VARCHAR(100) | Main source of income | None |
| `current_savings_balance` | DECIMAL(10,2) | Current savings balance | None |
| `total_debt_amount` | DECIMAL(10,2) | Total outstanding debt | None |
| `credit_score_range` | ENUM | Credit score range | excellent, good, fair, poor, very_poor, unknown |
| `employment_status` | VARCHAR(50) | Current employment status | None |

### 3. Demographics

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `age_range` | ENUM | User's age range | 18-24, 25-34, 35-44, 45-54, 55-64, 65+ |
| `marital_status` | ENUM | Marital status | single, married, partnership, divorced, widowed, prefer_not_to_say |
| `dependents_count` | INT | Number of dependents | 0-20, Default: 0 |
| `household_size` | INT | Total household size | 1-20, Default: 1 |
| `education_level` | VARCHAR(100) | Highest education achieved | None |
| `occupation` | VARCHAR(100) | Current job title | None |
| `industry` | VARCHAR(100) | Industry of employment | None |
| `years_of_experience` | ENUM | Years of work experience | less_than_1, 1-3, 4-7, 8-12, 13-20, 20+ |

### 4. Goals and Preferences

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `primary_financial_goal` | VARCHAR(100) | Main financial goal | None |
| `risk_tolerance_level` | ENUM | Investment risk tolerance | conservative, moderate, aggressive, unsure |
| `financial_knowledge_level` | ENUM | Financial knowledge level | beginner, intermediate, advanced, expert |
| `preferred_contact_method` | VARCHAR(50) | Preferred contact method | None |
| `notification_preferences` | JSONB | Notification settings | JSON object |

### 5. Health and Wellness

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `health_checkin_frequency` | ENUM | Health check-in frequency | daily, weekly, monthly, on_demand, never |
| `stress_level_baseline` | INT | Baseline stress level | 1-10 scale |
| `wellness_goals` | JSONB | Wellness goals | JSON object |

### 6. Compliance and Preferences

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `gdpr_consent_status` | BOOLEAN | GDPR consent status | Default: FALSE |
| `data_sharing_preferences` | VARCHAR(100) | Data sharing preferences | None |
| `profile_completion_percentage` | DECIMAL(5,2) | Profile completion % | 0.00-100.00, Default: 0.00 |
| `onboarding_step` | INT | Current onboarding step | 1-10, Default: 1 |

## Database Functions

### Profile Completion Calculation

The migration includes an automatic function to calculate profile completion percentage:

```sql
SELECT calculate_profile_completion_percentage(user_id);
```

This function:
- Counts filled fields out of 25 total fields
- Returns a percentage (0.00-100.00)
- Is automatically triggered on user updates

### Automatic Updates

A trigger automatically updates the `profile_completion_percentage` field whenever a user record is updated.

## Indexes Created

The migration creates several indexes for performance optimization:

### Single Column Indexes
- `idx_users_first_name`
- `idx_users_last_name`
- `idx_users_zip_code`
- `idx_users_phone_number`
- `idx_users_email_verification`
- `idx_users_monthly_income`
- `idx_users_credit_score`
- `idx_users_age_range`
- `idx_users_marital_status`
- `idx_users_employment_status`
- `idx_users_risk_tolerance`
- `idx_users_financial_knowledge`
- `idx_users_profile_completion`
- `idx_users_onboarding_step`
- `idx_users_gdpr_consent`

### Composite Indexes
- `idx_users_name_search` (first_name, last_name)
- `idx_users_demographics` (age_range, marital_status, employment_status)
- `idx_users_financial_profile` (monthly_income, credit_score_range, risk_tolerance_level)

## Usage Examples

### Querying Users by Demographics

```sql
-- Find users in specific age range with good credit
SELECT id, first_name, last_name, monthly_income
FROM users 
WHERE age_range = '25-34' 
  AND credit_score_range = 'good'
  AND profile_completion_percentage > 50;
```

### Financial Planning Queries

```sql
-- Find users needing debt management help
SELECT id, first_name, last_name, total_debt_amount, monthly_income
FROM users 
WHERE total_debt_amount > monthly_income * 0.5
  AND risk_tolerance_level = 'conservative';
```

### Onboarding Progress Tracking

```sql
-- Find users stuck in onboarding
SELECT id, email, onboarding_step, profile_completion_percentage
FROM users 
WHERE onboarding_step < 5 
  AND profile_completion_percentage < 30
  AND created_at < NOW() - INTERVAL '7 days';
```

## Data Validation

The migration includes several constraints to ensure data quality:

- Phone number format validation
- Zip code format validation
- Dependents count range (0-20)
- Household size range (1-20)
- Profile completion percentage range (0-100)
- Onboarding step range (1-10)
- Stress level baseline range (1-10)

## Privacy and Compliance

### GDPR Considerations

- `gdpr_consent_status` tracks user consent
- `data_sharing_preferences` stores user preferences
- Sensitive fields like `date_of_birth` should be handled carefully

### Data Retention

Consider implementing data retention policies for:
- Personal identification fields
- Financial information
- Health and wellness data

## Migration Application

### Apply Migration

```bash
# Using the provided script
python scripts/apply_user_fields_migration.py

# Or manually
psql -d your_database -f migrations/012_add_comprehensive_user_fields.sql
```

### Rollback Migration

```bash
# If needed, apply rollback
psql -d your_database -f migrations/012_add_comprehensive_user_fields_rollback.sql
```

## Best Practices

### Data Entry

1. **Progressive Disclosure**: Collect fields gradually during onboarding
2. **Validation**: Use client-side and server-side validation
3. **Default Values**: Provide sensible defaults where appropriate
4. **Optional Fields**: Make non-critical fields optional

### Performance

1. **Indexing**: Use the created indexes for common queries
2. **Pagination**: Use LIMIT/OFFSET for large result sets
3. **Caching**: Cache frequently accessed user profiles

### Security

1. **Encryption**: Encrypt sensitive fields at rest
2. **Access Control**: Implement proper row-level security
3. **Audit Logging**: Log access to sensitive user data

## Future Enhancements

Consider these potential additions:

1. **Geographic Data**: City, state, country fields
2. **Employment History**: Previous jobs, career progression
3. **Financial Products**: Current accounts, investments, insurance
4. **Family Information**: Spouse details, children information
5. **Preferences**: Language, timezone, currency preferences

## Support

For questions or issues with these fields:

1. Check the migration logs in the `migration_log` table
2. Review the database constraints and indexes
3. Test queries with sample data
4. Monitor performance impact of new indexes 