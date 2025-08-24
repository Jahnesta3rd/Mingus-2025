CREATE TABLE lifestyle_questionnaire_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    responses JSON,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_lqs_user_id ON lifestyle_questionnaire_submissions(user_id); 