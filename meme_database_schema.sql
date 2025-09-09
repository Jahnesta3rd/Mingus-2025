-- =====================================================
-- Mingus Personal Finance App - Meme Splash Page Schema
-- SQLite Database Schema for Meme Feature
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. MEMES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS memes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'faith', 
        'work_life', 
        'friendships', 
        'children', 
        'relationships', 
        'going_out'
    )),
    caption TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. USER MEME HISTORY TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_meme_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meme_id INTEGER NOT NULL,
    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE,
    -- Note: user_id references users table (assumed to exist)
    -- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    UNIQUE(user_id, meme_id) -- Prevent duplicate views from same user
);

-- =====================================================
-- 3. USER MOOD DATA TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_mood_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    meme_id INTEGER NOT NULL,
    mood_score INTEGER NOT NULL CHECK (mood_score BETWEEN 1 AND 5),
    mood_label TEXT NOT NULL CHECK (mood_label IN ('excited', 'happy', 'neutral', 'sad', 'angry')),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meme_category TEXT NOT NULL,
    spending_context TEXT DEFAULT 'before_budget_check',
    FOREIGN KEY (meme_id) REFERENCES memes(id) ON DELETE CASCADE
);

-- =====================================================
-- 4. MOOD SPENDING CORRELATION TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS mood_spending_correlation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    avg_mood_score REAL NOT NULL,
    total_spent REAL NOT NULL,
    budget_amount REAL NOT NULL,
    spending_vs_budget REAL NOT NULL, -- positive = over budget
    correlation_strength REAL, -- calculated correlation coefficient
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- =====================================================
-- 5. USER MOOD INSIGHTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS user_mood_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    insight_type TEXT NOT NULL,
    insight_data TEXT NOT NULL, -- JSON data
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- =====================================================
-- 6. INDEXES FOR PERFORMANCE
-- =====================================================

-- Indexes for memes table
CREATE INDEX IF NOT EXISTS idx_memes_category ON memes(category);
CREATE INDEX IF NOT EXISTS idx_memes_active ON memes(is_active);
CREATE INDEX IF NOT EXISTS idx_memes_category_active ON memes(category, is_active);
CREATE INDEX IF NOT EXISTS idx_memes_created_at ON memes(created_at);

-- Indexes for mood data table
CREATE INDEX IF NOT EXISTS idx_user_mood_data_user_id ON user_mood_data(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mood_data_timestamp ON user_mood_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_mood_data_mood_score ON user_mood_data(mood_score);
CREATE INDEX IF NOT EXISTS idx_user_mood_data_user_timestamp ON user_mood_data(user_id, timestamp);

-- Indexes for correlation table
CREATE INDEX IF NOT EXISTS idx_mood_spending_correlation_user_id ON mood_spending_correlation(user_id);
CREATE INDEX IF NOT EXISTS idx_mood_spending_correlation_date ON mood_spending_correlation(date);
CREATE INDEX IF NOT EXISTS idx_mood_spending_correlation_user_date ON mood_spending_correlation(user_id, date);

-- Indexes for insights table
CREATE INDEX IF NOT EXISTS idx_user_mood_insights_user_id ON user_mood_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mood_insights_type ON user_mood_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_user_mood_insights_expires ON user_mood_insights(expires_at);

-- Indexes for user_meme_history table
CREATE INDEX IF NOT EXISTS idx_user_meme_history_user_id ON user_meme_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_meme_history_meme_id ON user_meme_history(meme_id);
CREATE INDEX IF NOT EXISTS idx_user_meme_history_viewed_at ON user_meme_history(viewed_at);
CREATE INDEX IF NOT EXISTS idx_user_meme_history_user_viewed ON user_meme_history(user_id, viewed_at);

-- =====================================================
-- 4. TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =====================================================

-- Trigger to update updated_at timestamp on memes table
CREATE TRIGGER IF NOT EXISTS update_memes_timestamp 
    AFTER UPDATE ON memes
    FOR EACH ROW
BEGIN
    UPDATE memes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =====================================================
-- 5. SAMPLE DATA - 3 MEMES PER CATEGORY
-- =====================================================

-- FAITH CATEGORY
INSERT INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/faith/bible_budget.jpg', 'faith', 'When you tithe 10% but your budget is still in the red 📖💰', 'Meme showing Bible with budget spreadsheet, highlighting financial faith struggles', 1),
('https://example.com/memes/faith/prayer_credit_score.jpg', 'faith', 'Praying for a good credit score like it''s a miracle 🙏💳', 'Cartoon person praying with credit score numbers floating above', 1),
('https://example.com/memes/faith/trust_god_bills.jpg', 'faith', 'Trusting God with my finances while staring at my bills 😅💸', 'Split image showing peaceful prayer on one side, overwhelming bills on the other', 1);

-- WORK_LIFE CATEGORY
INSERT INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/work_life/paycheck_vanishes.jpg', 'work_life', 'My paycheck: *exists for 0.2 seconds* *disappears into bills* 💸👻', 'Animated gif showing paycheck appearing and immediately vanishing', 1),
('https://example.com/memes/work_life/remote_work_savings.jpg', 'work_life', 'Working from home: Save on gas, spend on snacks. Net result: Still broke 🏠🍕', 'Split screen showing gas savings vs increased food delivery costs', 1),
('https://example.com/memes/work_life/meeting_expensive.jpg', 'work_life', 'This meeting could have been an email... and saved me $50 in coffee ☕💸', 'Office worker surrounded by expensive coffee cups during a video call', 1);

-- FRIENDSHIPS CATEGORY
INSERT INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/friendships/expensive_friends.jpg', 'friendships', 'My friends: "Let''s go out!" Me: *checks bank account* "I''ll just watch from home" 🏠👀', 'Person looking longingly out window while friends party outside', 1),
('https://example.com/memes/friendships/split_bill_math.jpg', 'friendships', 'Splitting the bill: *becomes a math PhD* *still gets it wrong* 🧮😵', 'Confused person with calculator surrounded by restaurant receipts', 1),
('https://example.com/memes/friendships/gift_budget.jpg', 'friendships', 'Friend''s birthday: Budget $20, Actual spending: $87, Regret: Priceless 🎁💸', 'Shopping cart overflowing with gifts and a shocked expression', 1);

-- CHILDREN CATEGORY
INSERT INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/children/expensive_kids.jpg', 'children', 'Kids: "I want this!" Me: "Do you want to eat this month?" 🍕👶', 'Parent pointing to expensive toy while child looks confused', 1),
('https://example.com/memes/children/college_fund.jpg', 'children', 'College fund: $0.00, Emergency fund: $0.00, My sanity: Also $0.00 🎓💸', 'Empty piggy bank with graduation cap and stressed parent', 1),
('https://example.com/memes/children/back_to_school.jpg', 'children', 'Back to school shopping: *entire paycheck disappears* 📚💸', 'Shopping cart full of school supplies with shocked parent holding empty wallet', 1);

-- RELATIONSHIPS CATEGORY
INSERT INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/relationships/date_night_budget.jpg', 'relationships', 'Date night budget: $50, Actual cost: $150, Love: Still priceless 💕💸', 'Romantic dinner scene with shocked expression at the bill', 1),
('https://example.com/memes/relationships/anniversary_gift.jpg', 'relationships', 'Anniversary gift: *checks bank account* "How about a nice card?" 💳💝', 'Person holding a simple card while expensive gifts are visible in background', 1),
('https://example.com/memes/relationships/wedding_costs.jpg', 'relationships', 'Wedding planning: *bank account starts crying* 💒😭', 'Wedding planner with calculator showing astronomical costs', 1);

-- GOING_OUT CATEGORY
INSERT INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/going_out/expensive_night.jpg', 'going_out', 'Going out: *wallet starts screaming* 🎉💸', 'Person at club with wallet visibly distressed in the background', 1),
('https://example.com/memes/going_out/uber_costs.jpg', 'going_out', 'Uber home: $25, Drinks: $60, Memories: Priceless, My budget: Dead 💀🚗', 'Split image showing fun night out vs expensive ride home', 1),
('https://example.com/memes/going_out/concert_tickets.jpg', 'going_out', 'Concert tickets: $200, Parking: $30, Food: $50, Regret: Free but painful 🎵💸', 'Concert venue with person holding expensive tickets and empty wallet', 1);

-- =====================================================
-- 6. USEFUL QUERIES FOR THE APPLICATION
-- =====================================================

-- Query to get random active memes by category
-- SELECT * FROM memes WHERE category = 'faith' AND is_active = 1 ORDER BY RANDOM() LIMIT 1;

-- Query to get memes not yet viewed by a specific user
-- SELECT m.* FROM memes m 
-- LEFT JOIN user_meme_history umh ON m.id = umh.meme_id AND umh.user_id = ?
-- WHERE m.is_active = 1 AND umh.id IS NULL;

-- Query to track user engagement
-- SELECT category, COUNT(*) as view_count 
-- FROM user_meme_history umh 
-- JOIN memes m ON umh.meme_id = m.id 
-- WHERE umh.user_id = ? 
-- GROUP BY category;

-- =====================================================
-- 7. MAINTENANCE QUERIES
-- =====================================================

-- Query to deactivate old memes (example: older than 1 year)
-- UPDATE memes SET is_active = 0 WHERE created_at < datetime('now', '-1 year');

-- Query to clean up old user history (example: older than 2 years)
-- DELETE FROM user_meme_history WHERE viewed_at < datetime('now', '-2 years');

-- =====================================================
-- SCHEMA CREATION COMPLETE
-- =====================================================
