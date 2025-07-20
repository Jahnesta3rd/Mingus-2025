# Mingus Application Database Schema Documentation

**Database Type:** SQLite  
**Database File:** `instance/mingus.db`  
**Generated:** January 2025  
**Total Tables:** 13  
**Total Indexes:** 35  
**Total Views:** 2  

---

## 📋 Table of Contents

1. [Core User Tables](#core-user-tables)
2. [User Profile & Onboarding Tables](#user-profile--onboarding-tables)
3. [Health & Wellness Tables](#health--wellness-tables)
4. [Financial Tables](#financial-tables)
5. [Security & Verification Tables](#security--verification-tables)
6. [System Tables](#system-tables)
7. [Database Views](#database-views)
8. [Indexes Summary](#indexes-summary)
9. [Foreign Key Relationships](#foreign-key-relationships)

---

## 🔑 Core User Tables

### 1. `users` - Main User Accounts
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Unique user identifier |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | User's email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `full_name` | VARCHAR(255) | NULL | User's full name |
| `phone_number` | VARCHAR(50) | NULL | User's phone number |
| `is_active` | BOOLEAN | NULL | Account active status |
| `created_at` | DATETIME | NULL | Account creation timestamp |
| `updated_at` | DATETIME | NULL | Last update timestamp |

**Indexes:**
- `ix_users_email` (UNIQUE) on `email`

---

## 👤 User Profile & Onboarding Tables

### 2. `user_profiles` - Extended User Information
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Profile identifier |
| `user_id` | INTEGER | NOT NULL, UNIQUE, FK | Reference to users table |
| `monthly_income` | FLOAT | NULL | Monthly income amount |
| `income_frequency` | VARCHAR(50) | NULL | Income frequency (weekly, monthly, etc.) |
| `primary_income_source` | VARCHAR(100) | NULL | Main income source |
| `secondary_income_source` | VARCHAR(100) | NULL | Secondary income source |
| `primary_goal` | VARCHAR(100) | NULL | User's primary financial goal |
| `goal_amount` | FLOAT | NULL | Target goal amount |
| `goal_timeline_months` | INTEGER | NULL | Goal timeline in months |
| `age_range` | VARCHAR(50) | NULL | User's age range |
| `location_state` | VARCHAR(50) | NULL | State of residence |
| `location_city` | VARCHAR(100) | NULL | City of residence |
| `household_size` | INTEGER | NULL | Number of household members |
| `employment_status` | VARCHAR(50) | NULL | Employment status |
| `current_savings` | FLOAT | NULL | Current savings amount |
| `current_debt` | FLOAT | NULL | Current debt amount |
| `credit_score_range` | VARCHAR(50) | NULL | Credit score range |
| `risk_tolerance` | VARCHAR(50) | NULL | Risk tolerance level |
| `investment_experience` | VARCHAR(50) | NULL | Investment experience level |
| `created_at` | DATETIME | NULL | Profile creation timestamp |
| `updated_at` | DATETIME | NULL | Last update timestamp |
| `is_complete` | BOOLEAN | NULL | Profile completion status |

**Indexes:**
- Auto-index on `user_id` (UNIQUE constraint)

### 3. `onboarding_progress` - User Onboarding Tracking
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Progress identifier |
| `user_id` | INTEGER | NOT NULL, UNIQUE, FK | Reference to users table |
| `current_step` | VARCHAR(100) | NULL | Current onboarding step |
| `total_steps` | INTEGER | NULL | Total number of steps |
| `completed_steps` | INTEGER | NULL | Number of completed steps |
| `step_status` | VARCHAR | NULL | Current step status |
| `started_at` | DATETIME | NULL | Onboarding start timestamp |
| `completed_at` | DATETIME | NULL | Onboarding completion timestamp |
| `last_activity` | DATETIME | NULL | Last activity timestamp |
| `is_complete` | BOOLEAN | NULL | Onboarding completion status |
| `completion_percentage` | INTEGER | NULL | Completion percentage |
| `questionnaire_responses` | TEXT | NULL | JSON responses from questionnaire |

**Indexes:**
- Auto-index on `user_id` (UNIQUE constraint)

### 4. `user_preferences` - User Preferences & Settings
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Preference identifier |
| `user_id` | INTEGER | NOT NULL, UNIQUE, FK | Reference to users table |
| `email_notifications` | BOOLEAN | NULL | Email notification preference |
| `push_notifications` | BOOLEAN | NULL | Push notification preference |
| `sms_notifications` | BOOLEAN | NULL | SMS notification preference |
| `reminder_preferences` | JSON | NULL | Reminder settings |
| `preferred_communication` | VARCHAR(20) | NULL | Preferred communication method |
| `communication_frequency` | VARCHAR(20) | NULL | Communication frequency |
| `share_anonymized_data` | BOOLEAN | NULL | Data sharing consent |
| `allow_marketing_emails` | BOOLEAN | NULL | Marketing email consent |
| `theme_preference` | VARCHAR(20) | NULL | UI theme preference |
| `language_preference` | VARCHAR(10) | NULL | Language preference |
| `onboarding_completed` | BOOLEAN | NULL | Onboarding completion status |
| `first_checkin_scheduled` | BOOLEAN | NULL | First health checkin status |
| `mobile_app_downloaded` | BOOLEAN | NULL | Mobile app download status |
| `custom_preferences` | JSON | NULL | Custom user preferences |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes:**
- Auto-index on `user_id` (UNIQUE constraint)

---

## 🏥 Health & Wellness Tables

### 5. `user_health_checkins` - Health Check-in Data
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Checkin identifier |
| `user_id` | INTEGER | NOT NULL, FK | Reference to users table |
| `checkin_date` | DATETIME | NOT NULL | Checkin date |
| `sleep_hours` | FLOAT | NULL | Hours of sleep |
| `physical_activity_minutes` | INTEGER | NULL | Minutes of physical activity |
| `physical_activity_level` | VARCHAR(50) | NULL | Activity level |
| `relationships_rating` | INTEGER | NULL | Relationships satisfaction (1-10) |
| `relationships_notes` | VARCHAR(500) | NULL | Relationship notes |
| `mindfulness_minutes` | INTEGER | NULL | Mindfulness practice minutes |
| `mindfulness_type` | VARCHAR(100) | NULL | Type of mindfulness practice |
| `stress_level` | INTEGER | NULL | Stress level (1-10) |
| `energy_level` | INTEGER | NULL | Energy level (1-10) |
| `mood_rating` | INTEGER | NULL | Mood rating (1-10) |
| `created_at` | DATETIME | NULL | Creation timestamp |
| `updated_at` | DATETIME | NULL | Last update timestamp |

**Constraints:**
- `uq_user_weekly_checkin` (UNIQUE) on `(user_id, checkin_date)`

**Indexes:**
- `idx_user_health_checkin_date_range` on `(user_id, checkin_date)`
- `ix_user_health_checkins_user_id` on `user_id`
- `idx_health_metrics` on `(stress_level, energy_level, mood_rating)`
- `ix_user_health_checkins_checkin_date` on `checkin_date`
- Auto-index on `(user_id, checkin_date)` (UNIQUE constraint)

### 6. `health_spending_correlations` - Health-Spending Analysis
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Correlation identifier |
| `user_id` | INTEGER | NOT NULL, FK | Reference to users table |
| `analysis_period` | VARCHAR(50) | NOT NULL | Analysis period |
| `analysis_start_date` | DATETIME | NOT NULL | Analysis start date |
| `analysis_end_date` | DATETIME | NOT NULL | Analysis end date |
| `health_metric` | VARCHAR(100) | NOT NULL | Health metric analyzed |
| `spending_category` | VARCHAR(100) | NOT NULL | Spending category analyzed |
| `correlation_strength` | FLOAT | NOT NULL | Correlation strength (-1 to 1) |
| `correlation_direction` | VARCHAR(20) | NOT NULL | Correlation direction |
| `sample_size` | INTEGER | NOT NULL | Number of data points |
| `p_value` | FLOAT | NULL | Statistical significance |
| `confidence_interval_lower` | FLOAT | NULL | Lower confidence interval |
| `confidence_interval_upper` | FLOAT | NULL | Upper confidence interval |
| `insight_text` | VARCHAR(1000) | NULL | Generated insight text |
| `recommendation_text` | VARCHAR(1000) | NULL | Generated recommendation |
| `actionable_insight` | BOOLEAN | NULL | Whether insight is actionable |
| `created_at` | DATETIME | NULL | Creation timestamp |
| `updated_at` | DATETIME | NULL | Last update timestamp |

**Indexes:**
- `idx_analysis_date_range` on `(analysis_start_date, analysis_end_date)`
- `idx_correlation_strength` on `correlation_strength`
- `idx_actionable_insights` on `(actionable_insight, correlation_strength)`
- `idx_user_period_metric` on `(user_id, analysis_period, health_metric, spending_category)`
- `ix_health_spending_correlations_user_id` on `user_id`

---

## 💰 Financial Tables

### 7. `financial_questionnaire_submissions` - Financial Assessment Data
**Primary Key:** `id` (SERIAL)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Submission identifier |
| `user_id` | INTEGER | NOT NULL, FK | Reference to users table |
| `monthly_income` | FLOAT | NULL | Monthly income amount |
| `monthly_expenses` | FLOAT | NULL | Monthly expenses amount |
| `current_savings` | FLOAT | NULL | Current savings amount |
| `total_debt` | FLOAT | NULL | Total debt amount |
| `risk_tolerance` | INTEGER | NULL | Risk tolerance score |
| `financial_goals` | JSON | NULL | Financial goals data |
| `financial_health_score` | INTEGER | NULL | Calculated health score |
| `financial_health_level` | VARCHAR(50) | NULL | Health level category |
| `recommendations` | JSON | NULL | Generated recommendations |
| `submitted_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Submission timestamp |

**Indexes:**
- `idx_fqs_user_id` on `user_id`
- Auto-index on `id` (PRIMARY KEY)

### 8. `reminder_schedules` - User Reminders
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, NOT NULL | Reminder identifier |
| `user_id` | INTEGER | NOT NULL, FK | Reference to users table |
| `reminder_type` | VARCHAR(50) | NOT NULL | Type of reminder |
| `scheduled_date` | DATETIME | NOT NULL | Scheduled reminder date |
| `frequency` | VARCHAR(20) | NULL | Reminder frequency |
| `enabled` | BOOLEAN | NULL | Reminder enabled status |
| `preferences` | JSON | NULL | Reminder preferences |
| `message` | TEXT | NULL | Reminder message |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

---

## 🔒 Security & Verification Tables

### 9. `phone_verification` - Phone Verification System
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Verification identifier |
| `user_id` | INTEGER | NOT NULL, FK | Reference to users table |
| `phone_number` | TEXT | NOT NULL | Phone number to verify |
| `verification_code_hash` | TEXT | NOT NULL | Hashed verification code |
| `code_sent_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Code sent timestamp |
| `code_expires_at` | DATETIME | NOT NULL | Code expiration timestamp |
| `attempts` | INTEGER | DEFAULT 0 | Number of verification attempts |
| `status` | TEXT | DEFAULT 'pending' | Verification status |
| `resend_count` | INTEGER | DEFAULT 0 | Number of resend attempts |
| `last_attempt_at` | DATETIME | NULL | Last attempt timestamp |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |
| `salt` | TEXT | NULL | Salt for code hashing |
| `ip_address` | TEXT | NULL | IP address of verification attempt |
| `user_agent` | TEXT | NULL | User agent string |
| `captcha_verified` | BOOLEAN | DEFAULT FALSE | CAPTCHA verification status |
| `risk_score` | REAL | DEFAULT 0.0 | Risk assessment score |

**Indexes:**
- `idx_phone_verification_user_id` on `user_id`
- `idx_phone_verification_phone_number` on `phone_number`
- `idx_phone_verification_status` on `status`
- `idx_phone_verification_created_at` on `created_at`
- `idx_phone_verification_user_phone` on `(user_id, phone_number)`
- `idx_phone_verification_resend_count` on `resend_count`
- `idx_phone_verification_user_phone_resend` on `(user_id, phone_number, resend_count)`
- `idx_phone_verification_ip_address` on `ip_address`
- `idx_phone_verification_risk_score` on `risk_score`
- `idx_phone_verification_captcha_verified` on `captcha_verified`

### 10. `verification_analytics` - Verification Event Tracking
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Analytics identifier |
| `user_id` | INTEGER | NOT NULL, FK | Reference to users table |
| `event_type` | TEXT | NOT NULL | Type of verification event |
| `event_data` | TEXT | NULL | JSON event details |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Event timestamp |

**Indexes:**
- `idx_verification_analytics_user_id` on `user_id`
- `idx_verification_analytics_event_type` on `event_type`
- `idx_verification_analytics_created_at` on `created_at`

### 11. `verification_audit_log` - Security Audit Logging
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)  
**Foreign Key:** `user_id` → `users(id)`

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Audit log identifier |
| `user_id` | INTEGER | NULL, FK | Reference to users table |
| `ip_address` | TEXT | NOT NULL | IP address of activity |
| `user_agent` | TEXT | NULL | User agent string |
| `phone_number` | TEXT | NULL | Phone number involved |
| `event_type` | TEXT | NOT NULL | Type of security event |
| `event_details` | TEXT | NULL | JSON event details |
| `risk_score` | REAL | DEFAULT 0.0 | Risk assessment score |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Event timestamp |

**Indexes:**
- `idx_verification_audit_user_id` on `user_id`
- `idx_verification_audit_ip_address` on `ip_address`
- `idx_verification_audit_event_type` on `event_type`
- `idx_verification_audit_created_at` on `created_at`
- `idx_verification_audit_risk_score` on `risk_score`
- `idx_verification_audit_user_ip` on `(user_id, ip_address)`

---

## ⚙️ System Tables

### 12. `migrations` - Database Migration Tracking
**Primary Key:** `id` (INTEGER, AUTOINCREMENT)

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Migration identifier |
| `filename` | TEXT | UNIQUE, NOT NULL | Migration filename |
| `applied_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Application timestamp |

**Indexes:**
- Auto-index on `filename` (UNIQUE constraint)

### 13. `sqlite_sequence` - SQLite Internal Table
**System table for auto-increment management**

---

## 👁️ Database Views

### 1. `suspicious_ips` - Security Monitoring View
**Purpose:** Identifies potentially suspicious IP addresses based on verification activity

| Column | Data Type | Description |
|--------|-----------|-------------|
| `ip_address` | TEXT | IP address |
| `total_events` | INTEGER | Total events from this IP |
| `failed_attempts` | INTEGER | Number of failed verification attempts |
| `rate_limit_violations` | INTEGER | Number of rate limit violations |
| `avg_risk_score` | REAL | Average risk score |
| `last_activity` | DATETIME | Last activity timestamp |

**Filter:** Events from last 24 hours with >10 events OR avg_risk_score > 0.6

### 2. `user_security_summary` - User Security Overview
**Purpose:** Provides security summary for each user

| Column | Data Type | Description |
|--------|-----------|-------------|
| `user_id` | INTEGER | User identifier |
| `total_verifications` | INTEGER | Total verification attempts |
| `successful_verifications` | INTEGER | Successful verifications |
| `failed_verifications` | INTEGER | Failed verifications |
| `unique_ips` | INTEGER | Number of unique IP addresses |
| `unique_phones` | INTEGER | Number of unique phone numbers |
| `last_verification` | DATETIME | Last verification timestamp |
| `avg_risk_score` | REAL | Average risk score |

---

## 📊 Indexes Summary

### Performance Indexes (35 total)

**User Management:**
- `ix_users_email` (UNIQUE) - Email lookup optimization

**Health & Wellness:**
- `idx_user_health_checkin_date_range` - Date range queries
- `idx_health_metrics` - Health metric analysis
- `ix_user_health_checkins_user_id` - User health data lookup
- `ix_user_health_checkins_checkin_date` - Checkin date queries

**Financial Analysis:**
- `idx_analysis_date_range` - Date range analysis
- `idx_correlation_strength` - Correlation analysis
- `idx_actionable_insights` - Actionable insights filtering
- `idx_user_period_metric` - User-specific analysis
- `idx_fqs_user_id` - Financial questionnaire lookup

**Security & Verification:**
- `idx_phone_verification_user_id` - User verification lookup
- `idx_phone_verification_phone_number` - Phone number lookup
- `idx_phone_verification_status` - Status filtering
- `idx_phone_verification_created_at` - Time-based queries
- `idx_phone_verification_user_phone` - User-phone combination
- `idx_phone_verification_resend_count` - Resend tracking
- `idx_phone_verification_user_phone_resend` - Complex resend queries
- `idx_phone_verification_ip_address` - IP address tracking
- `idx_phone_verification_risk_score` - Risk assessment
- `idx_phone_verification_captcha_verified` - CAPTCHA status

**Audit & Analytics:**
- `idx_verification_analytics_user_id` - User analytics
- `idx_verification_analytics_event_type` - Event type filtering
- `idx_verification_analytics_created_at` - Time-based analytics
- `idx_verification_audit_user_id` - User audit lookup
- `idx_verification_audit_ip_address` - IP audit tracking
- `idx_verification_audit_event_type` - Event type audit
- `idx_verification_audit_created_at` - Time-based audit
- `idx_verification_audit_risk_score` - Risk-based audit
- `idx_verification_audit_user_ip` - User-IP combination

**Auto-generated Indexes:**
- 7 unique constraint indexes
- 1 primary key index

---

## 🔗 Foreign Key Relationships

### Primary Relationships (All referencing `users.id`)

1. **`user_profiles.user_id`** → `users.id`
   - One-to-one relationship
   - UNIQUE constraint ensures one profile per user

2. **`onboarding_progress.user_id`** → `users.id`
   - One-to-one relationship
   - UNIQUE constraint ensures one progress record per user

3. **`user_preferences.user_id`** → `users.id`
   - One-to-one relationship
   - UNIQUE constraint ensures one preference set per user

4. **`user_health_checkins.user_id`** → `users.id`
   - One-to-many relationship
   - Multiple checkins per user allowed

5. **`health_spending_correlations.user_id`** → `users.id`
   - One-to-many relationship
   - Multiple correlations per user allowed

6. **`financial_questionnaire_submissions.user_id`** → `users.id`
   - One-to-many relationship
   - Multiple submissions per user allowed

7. **`reminder_schedules.user_id`** → `users.id`
   - One-to-many relationship
   - Multiple reminders per user allowed

8. **`phone_verification.user_id`** → `users.id`
   - One-to-many relationship
   - Multiple verification attempts per user allowed

9. **`verification_analytics.user_id`** → `users.id`
   - One-to-many relationship
   - Multiple analytics events per user allowed

10. **`verification_audit_log.user_id`** → `users.id`
    - One-to-many relationship
    - Multiple audit events per user allowed

### Relationship Summary

- **Core User Table:** `users` (13 references)
- **One-to-One Relationships:** 3 tables
- **One-to-Many Relationships:** 7 tables
- **Independent Tables:** 2 tables (`migrations`, `sqlite_sequence`)

---

## 📈 Database Statistics

- **Total Tables:** 13
- **Total Indexes:** 35
- **Total Views:** 2
- **Foreign Key Relationships:** 10
- **Unique Constraints:** 7
- **Primary Keys:** 13
- **JSON Columns:** 6 (for flexible data storage)
- **Timestamp Columns:** 25+ (for audit trails)

---

## 🔧 Maintenance Notes

1. **Regular Maintenance:** Consider periodic VACUUM operations for SQLite
2. **Index Optimization:** Monitor query performance and adjust indexes as needed
3. **Data Retention:** Implement data retention policies for audit logs and analytics
4. **Backup Strategy:** Regular backups recommended for production use
5. **Migration Management:** Use the `migrations` table to track schema changes

---

*This documentation was generated from the actual database schema and reflects the current state of the Mingus Application database.* 