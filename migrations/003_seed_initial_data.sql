-- =====================================================
-- Migration 003: Seed Initial Data
-- Populates the database with sample memes for each category
-- =====================================================

-- =====================================================
-- SAMPLE MEMES FOR EACH CATEGORY
-- =====================================================

-- FAITH CATEGORY
INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/faith/bible_budget.jpg', 'faith', 'When you tithe 10% but your budget is still in the red 📖💰', 'Meme showing Bible with budget spreadsheet, highlighting financial faith struggles', 1),
('https://example.com/memes/faith/prayer_credit_score.jpg', 'faith', 'Praying for a good credit score like it''s a miracle 🙏💳', 'Cartoon person praying with credit score numbers floating above', 1),
('https://example.com/memes/faith/trust_god_bills.jpg', 'faith', 'Trusting God with my finances while staring at my bills 😅💸', 'Split image showing peaceful prayer on one side, overwhelming bills on the other', 1);

-- WORK_LIFE CATEGORY
INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/work_life/paycheck_vanishes.jpg', 'work_life', 'My paycheck: *exists for 0.2 seconds* *disappears into bills* 💸👻', 'Animated gif showing paycheck appearing and immediately vanishing', 1),
('https://example.com/memes/work_life/remote_work_savings.jpg', 'work_life', 'Working from home: Save on gas, spend on snacks. Net result: Still broke 🏠🍕', 'Split screen showing gas savings vs increased food delivery costs', 1),
('https://example.com/memes/work_life/meeting_expensive.jpg', 'work_life', 'This meeting could have been an email... and saved me $50 in coffee ☕💸', 'Office worker surrounded by expensive coffee cups during a video call', 1);

-- FRIENDSHIPS CATEGORY
INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/friendships/expensive_friends.jpg', 'friendships', 'My friends: "Let''s go out!" Me: *checks bank account* "I''ll just watch from home" 🏠👀', 'Person looking longingly out window while friends party outside', 1),
('https://example.com/memes/friendships/split_bill_math.jpg', 'friendships', 'Splitting the bill: *becomes a math PhD* *still gets it wrong* 🧮😵', 'Confused person with calculator surrounded by restaurant receipts', 1),
('https://example.com/memes/friendships/gift_budget.jpg', 'friendships', 'Friend''s birthday: Budget $20, Actual spending: $87, Regret: Priceless 🎁💸', 'Shopping cart overflowing with gifts and a shocked expression', 1);

-- CHILDREN CATEGORY
INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/children/expensive_kids.jpg', 'children', 'Kids: "I want this!" Me: "Do you want to eat this month?" 🍕👶', 'Parent pointing to expensive toy while child looks confused', 1),
('https://example.com/memes/children/college_fund.jpg', 'children', 'College fund: $0.00, Emergency fund: $0.00, My sanity: Also $0.00 🎓💸', 'Empty piggy bank with graduation cap and stressed parent', 1),
('https://example.com/memes/children/back_to_school.jpg', 'children', 'Back to school shopping: *entire paycheck disappears* 📚💸', 'Shopping cart full of school supplies with shocked parent holding empty wallet', 1);

-- RELATIONSHIPS CATEGORY
INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/relationships/date_night_budget.jpg', 'relationships', 'Date night budget: $50, Actual cost: $150, Love: Still priceless 💕💸', 'Romantic dinner scene with shocked expression at the bill', 1),
('https://example.com/memes/relationships/anniversary_gift.jpg', 'relationships', 'Anniversary gift: *checks bank account* "How about a nice card?" 💳💝', 'Person holding a simple card while expensive gifts are visible in background', 1),
('https://example.com/memes/relationships/wedding_costs.jpg', 'relationships', 'Wedding planning: *bank account starts crying* 💒😭', 'Wedding planner with calculator showing astronomical costs', 1);

-- GOING_OUT CATEGORY
INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active) VALUES
('https://example.com/memes/going_out/expensive_night.jpg', 'going_out', 'Going out: *wallet starts screaming* 🎉💸', 'Person at club with wallet visibly distressed in the background', 1),
('https://example.com/memes/going_out/uber_costs.jpg', 'going_out', 'Uber home: $25, Drinks: $60, Memories: Priceless, My budget: Dead 💀🚗', 'Split image showing fun night out vs expensive ride home', 1),
('https://example.com/memes/going_out/concert_tickets.jpg', 'going_out', 'Concert tickets: $200, Parking: $30, Food: $50, Regret: Free but painful 🎵💸', 'Concert venue with person holding expensive tickets and empty wallet', 1);

-- =====================================================
-- SAMPLE USER DEMOGRAPHICS
-- =====================================================
INSERT OR IGNORE INTO user_demographics (user_id, age_range, gender, income_range, education_level, location_state) VALUES
(1, '25-34', 'female', '50k-75k', 'bachelors', 'CA'),
(2, '35-44', 'male', '75k-100k', 'masters', 'NY'),
(3, '18-24', 'non-binary', 'under_25k', 'some_college', 'TX'),
(4, '45-54', 'female', '100k-150k', 'bachelors', 'FL'),
(5, '25-34', 'male', '50k-75k', 'high_school', 'IL');

-- =====================================================
-- SAMPLE ANALYTICS EVENTS
-- =====================================================
INSERT OR IGNORE INTO meme_analytics_events (user_id, session_id, meme_id, event_type, time_spent_seconds, device_type, browser) VALUES
(1, 'session_001', 1, 'view', 8, 'mobile', 'Chrome'),
(1, 'session_001', 1, 'continue', 8, 'mobile', 'Chrome'),
(2, 'session_002', 2, 'view', 12, 'desktop', 'Firefox'),
(2, 'session_002', 2, 'skip', 12, 'desktop', 'Firefox'),
(3, 'session_003', 3, 'view', 5, 'mobile', 'Safari'),
(3, 'session_003', 3, 'auto_advance', 5, 'mobile', 'Safari');
