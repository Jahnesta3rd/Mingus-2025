CREATE TABLE IF NOT EXISTS financial_questionnaire_submissions (
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
CREATE INDEX IF NOT EXISTS idx_fqs_user_id ON financial_questionnaire_submissions(user_id); 