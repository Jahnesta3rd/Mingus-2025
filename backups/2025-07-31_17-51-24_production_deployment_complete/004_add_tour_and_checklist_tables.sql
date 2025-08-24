-- Migration: Add Tour and Checklist Tables
-- Description: Creates tables for managing app tours and personalized checklists

-- =====================================================
-- USER TOURS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS user_tours (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tour_type VARCHAR(50) NOT NULL CHECK (tour_type IN ('dashboard', 'onboarding', 'features')),
    current_step INTEGER DEFAULT 0,
    completed_steps JSONB DEFAULT '[]',
    is_completed BOOLEAN DEFAULT FALSE,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_current_step CHECK (current_step >= 0),
    CONSTRAINT unique_user_tour_type UNIQUE (user_id, tour_type)
);

-- =====================================================
-- TOUR EVENTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS tour_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tour_id UUID NOT NULL REFERENCES user_tours(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    step_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for performance
    INDEX idx_tour_events_tour_id (tour_id),
    INDEX idx_tour_events_user_id (user_id),
    INDEX idx_tour_events_timestamp (timestamp)
);

-- =====================================================
-- USER CHECKLISTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS user_checklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    items JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_items CHECK (jsonb_typeof(items) = 'array')
);

-- =====================================================
-- CHECKLIST EVENTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS checklist_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    checklist_id UUID NOT NULL REFERENCES user_checklists(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    item_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for performance
    INDEX idx_checklist_events_checklist_id (checklist_id),
    INDEX idx_checklist_events_user_id (user_id),
    INDEX idx_checklist_events_timestamp (timestamp)
);

-- =====================================================
-- ROW LEVEL SECURITY POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE user_tours ENABLE ROW LEVEL SECURITY;
ALTER TABLE tour_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE checklist_events ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- USER TOURS POLICIES
-- =====================================================

-- Users can only view their own tours
CREATE POLICY "Users can view own tours" ON user_tours
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own tours
CREATE POLICY "Users can insert own tours" ON user_tours
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own tours
CREATE POLICY "Users can update own tours" ON user_tours
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own tours
CREATE POLICY "Users can delete own tours" ON user_tours
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- TOUR EVENTS POLICIES
-- =====================================================

-- Users can only view their own tour events
CREATE POLICY "Users can view own tour events" ON tour_events
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own tour events
CREATE POLICY "Users can insert own tour events" ON tour_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- System can insert tour events for any user
CREATE POLICY "System can insert tour events" ON tour_events
    FOR INSERT WITH CHECK (true);

-- =====================================================
-- USER CHECKLISTS POLICIES
-- =====================================================

-- Users can only view their own checklists
CREATE POLICY "Users can view own checklists" ON user_checklists
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own checklists
CREATE POLICY "Users can insert own checklists" ON user_checklists
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own checklists
CREATE POLICY "Users can update own checklists" ON user_checklists
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own checklists
CREATE POLICY "Users can delete own checklists" ON user_checklists
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- CHECKLIST EVENTS POLICIES
-- =====================================================

-- Users can only view their own checklist events
CREATE POLICY "Users can view own checklist events" ON checklist_events
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own checklist events
CREATE POLICY "Users can insert own checklist events" ON checklist_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- System can insert checklist events for any user
CREATE POLICY "System can insert checklist events" ON checklist_events
    FOR INSERT WITH CHECK (true);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- User tours indexes
CREATE INDEX IF NOT EXISTS idx_user_tours_user_id ON user_tours(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tours_tour_type ON user_tours(tour_type);
CREATE INDEX IF NOT EXISTS idx_user_tours_is_completed ON user_tours(is_completed);
CREATE INDEX IF NOT EXISTS idx_user_tours_last_accessed ON user_tours(last_accessed);

-- User checklists indexes
CREATE INDEX IF NOT EXISTS idx_user_checklists_user_id ON user_checklists(user_id);
CREATE INDEX IF NOT EXISTS idx_user_checklists_updated_at ON user_checklists(updated_at);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_user_tours_updated_at 
    BEFORE UPDATE ON user_tours 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_checklists_updated_at 
    BEFORE UPDATE ON user_checklists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE user_tours IS 'Stores user tour progress and preferences';
COMMENT ON TABLE tour_events IS 'Tracks tour interaction events for analytics';
COMMENT ON TABLE user_checklists IS 'Stores personalized checklist items for users';
COMMENT ON TABLE checklist_events IS 'Tracks checklist interaction events for analytics';

COMMENT ON COLUMN user_tours.tour_type IS 'Type of tour: dashboard, onboarding, or features';
COMMENT ON COLUMN user_tours.completed_steps IS 'Array of completed step IDs';
COMMENT ON COLUMN user_tours.preferences IS 'User preferences for tour behavior';
COMMENT ON COLUMN user_checklists.items IS 'Array of checklist items with completion status'; 