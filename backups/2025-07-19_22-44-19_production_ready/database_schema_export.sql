CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255), 
	phone_number VARCHAR(50), 
	is_active BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE TABLE user_profiles (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	monthly_income FLOAT, 
	income_frequency VARCHAR(50), 
	primary_income_source VARCHAR(100), 
	secondary_income_source VARCHAR(100), 
	primary_goal VARCHAR(100), 
	goal_amount FLOAT, 
	goal_timeline_months INTEGER, 
	age_range VARCHAR(50), 
	location_state VARCHAR(50), 
	location_city VARCHAR(100), 
	household_size INTEGER, 
	employment_status VARCHAR(50), 
	current_savings FLOAT, 
	current_debt FLOAT, 
	credit_score_range VARCHAR(50), 
	risk_tolerance VARCHAR(50), 
	investment_experience VARCHAR(50), 
	created_at DATETIME, 
	updated_at DATETIME, 
	is_complete BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE onboarding_progress (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	current_step VARCHAR(100), 
	total_steps INTEGER, 
	completed_steps INTEGER, 
	step_status VARCHAR, 
	started_at DATETIME, 
	completed_at DATETIME, 
	last_activity DATETIME, 
	is_complete BOOLEAN, 
	completion_percentage INTEGER, questionnaire_responses TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE user_health_checkins (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	checkin_date DATETIME NOT NULL, 
	sleep_hours FLOAT, 
	physical_activity_minutes INTEGER, 
	physical_activity_level VARCHAR(50), 
	relationships_rating INTEGER, 
	relationships_notes VARCHAR(500), 
	mindfulness_minutes INTEGER, 
	mindfulness_type VARCHAR(100), 
	stress_level INTEGER, 
	energy_level INTEGER, 
	mood_rating INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_weekly_checkin UNIQUE (user_id, checkin_date), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_user_health_checkin_date_range ON user_health_checkins (user_id, checkin_date);
CREATE INDEX ix_user_health_checkins_user_id ON user_health_checkins (user_id);
CREATE INDEX idx_health_metrics ON user_health_checkins (stress_level, energy_level, mood_rating);
CREATE INDEX ix_user_health_checkins_checkin_date ON user_health_checkins (checkin_date);
CREATE TABLE health_spending_correlations (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	analysis_period VARCHAR(50) NOT NULL, 
	analysis_start_date DATETIME NOT NULL, 
	analysis_end_date DATETIME NOT NULL, 
	health_metric VARCHAR(100) NOT NULL, 
	spending_category VARCHAR(100) NOT NULL, 
	correlation_strength FLOAT NOT NULL, 
	correlation_direction VARCHAR(20) NOT NULL, 
	sample_size INTEGER NOT NULL, 
	p_value FLOAT, 
	confidence_interval_lower FLOAT, 
	confidence_interval_upper FLOAT, 
	insight_text VARCHAR(1000), 
	recommendation_text VARCHAR(1000), 
	actionable_insight BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_analysis_date_range ON health_spending_correlations (analysis_start_date, analysis_end_date);
CREATE INDEX idx_correlation_strength ON health_spending_correlations (correlation_strength);
CREATE INDEX idx_actionable_insights ON health_spending_correlations (actionable_insight, correlation_strength);
CREATE INDEX idx_user_period_metric ON health_spending_correlations (user_id, analysis_period, health_metric, spending_category);
CREATE INDEX ix_health_spending_correlations_user_id ON health_spending_correlations (user_id);
CREATE TABLE verification_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type TEXT NOT NULL, -- 'send_code', 'verify_success', 'verify_failed', 'change_phone', 'resend_request'
    event_data TEXT, -- Store detailed event data as JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_verification_analytics_user_id ON verification_analytics(user_id);
CREATE INDEX idx_verification_analytics_event_type ON verification_analytics(event_type);
CREATE INDEX idx_verification_analytics_created_at ON verification_analytics(created_at);
CREATE TABLE phone_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phone_number TEXT NOT NULL,
    verification_code_hash TEXT NOT NULL,
    code_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    code_expires_at DATETIME NOT NULL,
    attempts INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'failed', 'expired'
    resend_count INTEGER DEFAULT 0,
    last_attempt_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, salt TEXT, ip_address TEXT, user_agent TEXT, captcha_verified BOOLEAN DEFAULT FALSE, risk_score REAL DEFAULT 0.0);
CREATE INDEX idx_phone_verification_user_id ON phone_verification(user_id);
CREATE INDEX idx_phone_verification_phone_number ON phone_verification(phone_number);
CREATE INDEX idx_phone_verification_status ON phone_verification(status);
CREATE INDEX idx_phone_verification_created_at ON phone_verification(created_at);
CREATE INDEX idx_phone_verification_user_phone ON phone_verification(user_id, phone_number);
CREATE INDEX idx_phone_verification_resend_count ON phone_verification(resend_count);
CREATE INDEX idx_phone_verification_user_phone_resend ON phone_verification(user_id, phone_number, resend_count);
CREATE TABLE verification_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    phone_number TEXT,
    event_type TEXT NOT NULL, -- 'send_code', 'verify_success', 'verify_failed', 'rate_limit_exceeded', 'suspicious_activity', 'sim_swap_detected', 'captcha_failed'
    event_details TEXT, -- JSON data containing event details
    risk_score REAL DEFAULT 0.0, -- Risk score from 0.0 to 1.0
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_verification_audit_user_id ON verification_audit_log(user_id);
CREATE INDEX idx_verification_audit_ip_address ON verification_audit_log(ip_address);
CREATE INDEX idx_verification_audit_event_type ON verification_audit_log(event_type);
CREATE INDEX idx_verification_audit_created_at ON verification_audit_log(created_at);
CREATE INDEX idx_verification_audit_risk_score ON verification_audit_log(risk_score);
CREATE INDEX idx_verification_audit_user_ip ON verification_audit_log(user_id, ip_address);
CREATE INDEX idx_phone_verification_ip_address ON phone_verification(ip_address);
CREATE INDEX idx_phone_verification_risk_score ON phone_verification(risk_score);
CREATE INDEX idx_phone_verification_captcha_verified ON phone_verification(captcha_verified);
CREATE VIEW suspicious_ips AS
SELECT 
    ip_address,
    COUNT(*) as total_events,
    COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as failed_attempts,
    COUNT(CASE WHEN event_type = 'rate_limit_exceeded' THEN 1 END) as rate_limit_violations,
    AVG(risk_score) as avg_risk_score,
    MAX(created_at) as last_activity
FROM verification_audit_log 
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY ip_address
HAVING COUNT(*) > 10 OR AVG(risk_score) > 0.6
ORDER BY avg_risk_score DESC
/* suspicious_ips(ip_address,total_events,failed_attempts,rate_limit_violations,avg_risk_score,last_activity) */;
CREATE VIEW user_security_summary AS
SELECT 
    user_id,
    COUNT(*) as total_verifications,
    COUNT(CASE WHEN status = 'verified' THEN 1 END) as successful_verifications,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_verifications,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT phone_number) as unique_phones,
    MAX(created_at) as last_verification,
    AVG(risk_score) as avg_risk_score
FROM phone_verification 
GROUP BY user_id
/* user_security_summary(user_id,total_verifications,successful_verifications,failed_verifications,unique_ips,unique_phones,last_verification,avg_risk_score) */;
CREATE TABLE migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE financial_questionnaire_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    monthly_income FLOAT,
    monthly_expenses FLOAT,
    current_savings FLOAT,
    total_debt FLOAT,
    risk_tolerance INTEGER,
    financial_goals JSON,
    financial_health_score INTEGER,
    financial_health_level VARCHAR(50),
    recommendations JSON,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fqs_user_id ON financial_questionnaire_submissions(user_id);
CREATE TABLE reminder_schedules (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	reminder_type VARCHAR(50) NOT NULL, 
	scheduled_date DATETIME NOT NULL, 
	frequency VARCHAR(20), 
	enabled BOOLEAN, 
	preferences JSON, 
	message TEXT, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE user_preferences (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	email_notifications BOOLEAN, 
	push_notifications BOOLEAN, 
	sms_notifications BOOLEAN, 
	reminder_preferences JSON, 
	preferred_communication VARCHAR(20), 
	communication_frequency VARCHAR(20), 
	share_anonymized_data BOOLEAN, 
	allow_marketing_emails BOOLEAN, 
	theme_preference VARCHAR(20), 
	language_preference VARCHAR(10), 
	onboarding_completed BOOLEAN, 
	first_checkin_scheduled BOOLEAN, 
	mobile_app_downloaded BOOLEAN, 
	custom_preferences JSON, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
