-- user_financial_goals
CREATE TABLE IF NOT EXISTS user_financial_goals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id) NOT NULL,
    goal_type text CHECK (goal_type IN (
        'emergency_fund', 'debt_payoff', 'home_purchase', 'vacation_fund',
        'wedding_fund', 'car_purchase', 'retirement_savings', 'investment_portfolio',
        'side_business', 'education_fund', 'child_fund', 'custom'
    )),
    goal_name text NOT NULL,
    target_amount decimal(12,2) NOT NULL,
    current_amount decimal(12,2) DEFAULT 0.00,
    target_date date,
    priority_level integer CHECK (priority_level BETWEEN 1 AND 5) DEFAULT 3,
    monthly_contribution decimal(10,2) DEFAULT 0.00,
    auto_contribute boolean DEFAULT false,
    status text CHECK (status IN ('active', 'paused', 'completed', 'cancelled')) DEFAULT 'active',
    motivation_note text,
    milestone_amounts decimal[],
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- goal_progress_tracking
CREATE TABLE IF NOT EXISTS goal_progress_tracking (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id uuid REFERENCES user_financial_goals(id) NOT NULL,
    progress_date date NOT NULL,
    amount_contributed decimal(10,2) NOT NULL,
    balance_after_contribution decimal(12,2) NOT NULL,
    contribution_source text, -- 'manual', 'automatic', 'windfall'
    notes text,
    created_at timestamp DEFAULT now()
);

-- goal_health_correlations
CREATE TABLE IF NOT EXISTS goal_health_correlations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id) NOT NULL,
    goal_id uuid REFERENCES user_financial_goals(id) NOT NULL,
    week_date date NOT NULL,
    stress_level integer,
    progress_satisfaction integer CHECK (progress_satisfaction BETWEEN 1 AND 10),
    motivation_level integer CHECK (motivation_level BETWEEN 1 AND 10),
    goal_related_spending decimal(10,2) DEFAULT 0.00,
    created_at timestamp DEFAULT now()
); 