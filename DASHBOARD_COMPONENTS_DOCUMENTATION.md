# Dashboard Components Documentation

This document explains each component on the MINGUS dashboard, including their inputs, calculations, and how scores and metrics are generated.

## Table of Contents

1. [Daily Outlook](#daily-outlook)
2. [Overview](#overview)
3. [Job Recommendations](#job-recommendations)
4. [Location Intelligence](#location-intelligence)
5. [Housing Location](#housing-location)
6. [Vehicle Status](#vehicle-status)
7. [Career Analytics](#career-analytics)
8. [Quick Actions Panel](#quick-actions-panel)
9. [Risk Status Hero](#risk-status-hero)

---

## Daily Outlook

**Component:** `DailyOutlook.tsx` / `DailyOutlookCard.tsx`  
**API Endpoint:** `/api/daily-outlook`  
**Purpose:** Provides personalized daily insights, balance score, quick actions, and encouragement messages.

### Key Metrics

#### Balance Score (0-100)
The balance score is a weighted average of four category scores:

**Formula:**
```
Balance Score = (Financial Score × Financial Weight) + 
                (Wellness Score × Wellness Weight) + 
                (Relationship Score × Relationship Weight) + 
                (Career Score × Career Weight)
```

**Category Scores:**

1. **Financial Score (0-100)**
   - **Base Score:** 50
   - **Emergency Fund Contribution:**
     - +20 points if emergency fund ≥ 6 months of income
     - +10 points if emergency fund ≥ 3 months of income
   - **Debt-to-Income Ratio:**
     - +15 points if ratio < 0.2
     - +5 points if ratio < 0.4
     - -10 points if ratio ≥ 0.4
   - **Savings Rate:**
     - +15 points if savings rate > 20%
     - +5 points if savings rate > 10%
     - -5 points if savings rate ≤ 10%
   - **Formula:** `savings_rate = (monthly_income - total_expenses) / monthly_income`

2. **Wellness Score (0-100)**
   - **Base Score:** 50
   - **Mood Contribution (40% weight):**
     - Uses average mood score from last 30 days (1-5 scale)
     - `mood_contribution = (mood_score - 1) × 25` (converts 1-5 to 0-100)
     - `score += (mood_contribution - 50) × 0.4`
   - **Physical Activity:**
     - +15 points if ≥ 3 days/week
     - +5 points if ≥ 1 day/week
   - **Meditation:**
     - +10 points if ≥ 60 minutes/week
     - +5 points if ≥ 30 minutes/week
   - **Relationship Satisfaction:**
     - +10 points if ≥ 8/10
     - +5 points if ≥ 6/10

3. **Relationship Score (0-100)**
   - **Base Score:** 50
   - **Satisfaction Score:** Direct contribution from relationship satisfaction (1-10 scale)
   - **Status Impact:** Adjusted based on relationship status (single, dating, married, etc.)
   - Uses data from `user_relationship_status` table

4. **Career Score (0-100)**
   - **Base Score:** 50
   - **Risk Level Impact:**
     - Lower risk = higher career score
     - Based on current risk assessment
   - **Goal Progress:** Contribution from career goal completion
   - **Skills Development:** Based on skill gap analysis

**Dynamic Weights:**
Weights are calculated based on user priorities and recent activity:
- Default weights: Financial (0.35), Wellness (0.25), Relationship (0.20), Career (0.20)
- Weights adjust based on user behavior and priorities

### Additional Metrics

- **Trend:** Calculated by comparing current balance score to previous value
- **Change Percentage:** `((current_score - previous_score) / previous_score) × 100`
- **Streak Data:** Tracks consecutive days of engagement
- **Progress Percentage:** `(current_streak / next_milestone) × 100`

### Inputs

- User profile data (financial_info, personal_info)
- Mood tracking data (last 30 days)
- Weekly check-in data (physical activity, meditation, relationship satisfaction)
- Relationship status
- Career risk assessment
- Goal progress

---

## Overview

**Component:** Overview tab in `CareerProtectionDashboard.tsx`  
**Purpose:** Provides a high-level view of quick actions and recent activity.

### Components Included

1. **Quick Actions Panel** (see Quick Actions Panel section)
2. **Recent Activity Panel** (see Recent Activity Panel section)
3. **Housing Location Tile** (see Housing Location section)

### Metrics Displayed

- Quick action items based on risk level
- Recent user activity timeline
- Housing alerts and lease information

---

## Job Recommendations

**Component:** `RecommendationTiers.tsx`  
**API Endpoint:** `/api/recommendations/tiered`  
**Purpose:** Displays job recommendations organized into three tiers: Conservative, Optimal, and Stretch.

### Scoring System

#### Overall Score (0-100)
Weighted combination of multiple factors:

**Formula:**
```
Overall Score = (Salary Score × 0.35) + 
                (Skills Score × 0.25) + 
                (Career Score × 0.20) + 
                (Company Score × 0.10) + 
                (Location Score × 0.05) + 
                (Growth Score × 0.05)
```

#### Individual Score Components

1. **Salary Score (0-100)**
   - **Calculation:** Based on salary increase potential
   - **Formula:** `increase_ratio = job_salary_median / current_salary`
   - **Scoring:**
     - 100 points if increase_ratio ≥ 1.45 (45%+ increase)
     - 90 points if increase_ratio ≥ 1.30 (30-45% increase)
     - 80 points if increase_ratio ≥ 1.15 (15-30% increase)
     - 60 points if increase_ratio ≥ 1.05 (5-15% increase)
     - 30 points if increase_ratio < 1.05

2. **Skills Alignment Score (0-100)**
   - Compares user skills to required job skills
   - **Formula:** `match_percentage = (matching_skills / total_required_skills) × 100`
   - Considers skill categories and proficiency levels

3. **Career Progression Score (0-100)**
   - **Base Score:** 50
   - **Advancement Keywords:** +20 points for "senior", "lead", "principal", "director", "manager"
   - **Growth Opportunities:** +15 points if description mentions growth/advancement
   - **Equity Offered:** +15 points
   - **Bonus Potential:** +10 points if bonus_potential > 0

4. **Company Stability Score (0-100)**
   - Based on company size, financial health, and industry stability
   - Uses diversity_score, growth_score, and culture_score

5. **Location Compatibility Score (0-100)**
   - **Remote Match:** +20 points if job is remote and user prefers remote
   - **MSA Match:** +15 points if job MSA matches preferred MSAs
   - **Commute Distance:** Penalty for long commutes

6. **Growth Potential Score (0-100)**
   - Industry growth trends
   - Company growth trajectory
   - Role advancement potential

### Success Probability (0-1)

**Formula:**
```
Success Probability = (Average Enhanced Score × 0.4) + 
                      (Problem-Solution Alignment × 0.3) + 
                      (Skill Readiness × 0.3)
```

**Factors:**
- Experience level match: 0.9 (exact), 0.7 (upgrade), 0.4 (mismatch)
- Career field match: 0.9 (match), 0.6 (different)
- Company size preference: 0.8 (match), 0.6 (mismatch)
- Location preference: 0.9 (MSA match), 0.8 (remote match), 0.6 (mismatch)
- Company quality scores: diversity_score, growth_score, culture_score

### Salary Increase Potential

**Calculation:**
```
salary_increase_potential = ((job_salary_median - current_salary) / current_salary) × 100
```

### Skills Gap Analysis

For each required skill:
- **Gap Size:** `required_level - current_level`
- **Priority:** Based on gap size and importance to role
- **Learning Time Estimate:** Calculated from gap size and skill complexity

### Tier Classification

- **Conservative:** High success probability (>0.7), moderate salary increase (5-15%)
- **Optimal:** Balanced success probability (0.5-0.7), good salary increase (15-30%)
- **Stretch:** Lower success probability (<0.5), high salary increase (30%+)

### Inputs

- User profile (current salary, skills, experience level, location preferences)
- Job postings data (salary, requirements, company info, location)
- Resume analysis
- Market data (industry trends, salary ranges)
- User search criteria (preferred MSAs, remote preference, company size)

---

## Location Intelligence

**Component:** `LocationIntelligenceMap.tsx`  
**API Endpoint:** `/api/location/intelligence`  
**Purpose:** Visualizes job opportunities on a map with commute analysis and location-based insights.

### Metrics

#### Commute Analysis
For each job location, calculates:

1. **Driving Commute:**
   - **Time:** Calculated using Google Maps Distance Matrix API
   - **Cost:** `(distance_miles × gas_price_per_gallon × 2) / mpg × commute_days_per_month`
   - **Monthly Cost:** `daily_cost × 22` (working days)

2. **Transit Commute:**
   - **Time:** Public transit route calculation
   - **Cost:** Monthly transit pass cost
   - **Availability:** Based on transit routes near job location

3. **Walking Commute:**
   - **Time:** `distance_miles / walking_speed_mph × 60`
   - **Cost:** $0
   - **Feasibility:** Only shown if distance < 2 miles

#### Location Score
Combines multiple factors:
- Job density in area
- Average salary in MSA
- Cost of living
- Quality of life indicators
- Transportation accessibility

### Inputs

- User's current location (latitude/longitude)
- Selected search radius (miles)
- Job postings with location data
- Google Maps API for routing
- MSA (Metropolitan Statistical Area) data
- Cost of living data

---

## Housing Location

**Component:** `HousingLocationTile.tsx`  
**API Endpoints:** 
- `/api/housing/recent-searches`
- `/api/housing/scenarios`
- `/api/housing/lease-info`
- `/api/housing/alerts`

**Purpose:** Displays housing search history, scenarios, lease information, and alerts.

### Metrics

#### Lease Expiration Alerts
- **Days Until Expiry:** `lease_end_date - current_date`
- **Alert Trigger:** Shows alert if `days_until_expiry ≤ 60`
- **Urgency Levels:**
  - Critical: ≤ 30 days
  - Warning: 31-45 days
  - Notice: 46-60 days

#### Search Quota
- **Budget Tier:** 5 searches/month
- **Mid-Tier:** 10 searches/month
- **Professional:** Unlimited (-1)
- **Remaining:** `limit - searches_this_month`

#### Scenario Limits
- **Budget Tier:** 3 scenarios
- **Mid-Tier:** 10 scenarios
- **Professional:** Unlimited (-1)

### Inputs

- User's housing searches (from `HousingSearch` table)
- Saved scenarios (from `HousingScenario` table)
- Lease information (lease_end_date, monthly_rent, property_address)
- User tier (determines limits)
- Current date (for expiration calculations)

---

## Vehicle Status

**Component:** `VehicleDashboard.tsx`  
**API Endpoint:** `/api/vehicles/dashboard`  
**Purpose:** Displays vehicle information, maintenance schedules, budgets, and expenses.

### Metrics

#### Vehicle Statistics
- **Total Vehicles:** Count of user's vehicles
- **Total Mileage:** Sum of all vehicle mileages
- **Average Monthly Miles:** `total_mileage / number_of_months_owned`
- **Total Monthly Budget:** Sum of all vehicle monthly budgets
- **Upcoming Maintenance Count:** Maintenance items due in next 30 days
- **Overdue Maintenance Count:** Maintenance items past due date

#### Maintenance Predictions
- **Due Date Calculation:** `last_service_date + service_interval_days`
- **Priority Levels:**
  - High: Overdue or due within 7 days
  - Medium: Due within 30 days
  - Low: Due after 30 days

#### Budget Utilization
- **Monthly Budget:** Set budget for vehicle expenses
- **Current Spending:** Sum of expenses this month
- **Utilization:** `(current_spending / monthly_budget) × 100`
- **Status:**
  - Under budget: < 80%
  - On track: 80-100%
  - Over budget: > 100%

### Inputs

- Vehicle data (make, model, year, mileage)
- Maintenance history (service dates, types, costs)
- Monthly expenses (fuel, insurance, repairs, etc.)
- Budget settings
- Service intervals (from manufacturer recommendations)

---

## Career Analytics

**Component:** `AnalyticsDashboard.tsx`  
**API Endpoint:** `/api/analytics/dashboard`  
**Purpose:** Provides comprehensive analytics about career protection, risk trends, and success metrics.

### Metrics

#### Overview Metrics
- **Total Sessions:** Count of user sessions
- **Total Interactions:** Count of user interactions tracked
- **Average Session Duration:** `total_session_time / session_count`
- **Last Active:** Most recent activity timestamp

#### Engagement Metrics
- **Daily Active:** Boolean indicating if user was active today
- **Weekly Streak:** Consecutive weeks of activity
- **Features Used:** List of features accessed by user

#### Financial Summary
- **Budget Adherence:** Percentage of budget goals met
- **Savings Progress:** Progress toward savings goals
- **Goals On Track:** Count of goals meeting target timeline

#### Recent Activity
- Activity feed showing:
  - Assessment completions
  - Recommendation views
  - Application submissions
  - Profile updates
  - Risk level changes
  - Success milestones

### Risk Trends Analysis
- **Risk Level Distribution:** Count of assessments by risk level over time
- **Trend Analysis:** Comparison of current risk vs. historical risk
- **Top Risk Factors:** Most common risk factors identified

### Inputs

- User behavior analytics data
- Assessment results
- Recommendation interactions
- Application tracking
- Profile update history
- Risk assessment history

---

## Quick Actions Panel

**Component:** `QuickActionsPanel.tsx`  
**Purpose:** Provides quick access to key features based on user's risk level and unlocked features.

### Actions Available

1. **Job Recommendations**
   - Enabled if `hasRecommendations === true`
   - Links to `/recommendations` or `/assessment`

2. **Location Intelligence**
   - Always enabled
   - Links to `/location`

3. **Career Analytics**
   - Always enabled
   - Links to `/analytics`

4. **Update Profile**
   - Always enabled
   - Links to `/profile`

5. **Resume Builder**
   - Always enabled
   - Links to `/resume`

6. **Settings**
   - Always enabled
   - Links to `/settings`

### Risk-Based Actions

Actions adapt based on risk level:

- **Secure:** "Explore Growth", "Update Profile"
- **Watchful:** "View Strategies", "Market Analysis"
- **Action Needed:** "Protection Plan", "Emergency Prep"
- **Urgent:** "Emergency Actions", "Quick Apply"

### Inputs

- Current risk level (`secure`, `watchful`, `action_needed`, `urgent`)
- Recommendations unlocked status (`hasRecommendations`)
- User tier (for feature access)

---

## Risk Status Hero

**Component:** `RiskStatusHero.tsx`  
**API Endpoint:** `/api/risk/assess-and-track`  
**Purpose:** Displays current career risk assessment with visual indicators and primary threats.

### Risk Score (0-100)

**Calculation Method:**
Risk score is calculated from multiple risk factors:

#### Risk Factors Contributing to Score

1. **Industry Risk Factors:**
   - Industry volatility: +20 points
   - Industry downsizing: +25 points

2. **Company Risk Factors:**
   - Company financial trouble: +30 points
   - Company layoffs: +25 points
   - Company merger: +15 points

3. **Role Risk Factors:**
   - Role redundancy: +20 points
   - Role automation risk: +15 points
   - Role outsourcing risk: +20 points

4. **Personal Risk Factors:**
   - Limited skills: +15 points
   - Age discrimination risk: +10 points
   - Location risk: +10 points

**Total Score:** Sum of all applicable factors (capped at 100)

#### Risk Level Classification

- **Secure (Low Risk):** Score < 30
- **Watchful (Medium Risk):** Score 30-50
- **Action Needed (High Risk):** Score 51-70
- **Urgent (Critical Risk):** Score > 70

### Individual Risk Score Components

From `PersonalRiskPredictor`:

1. **Tenure Risk:**
   - `tenure_risk = 1 - (tenure_days / max_tenure)`
   - Max tenure = 3650 days (10 years)

2. **Performance Risk:**
   - `performance_risk = 1 - (performance_rating / 5)`
   - Based on 1-5 performance rating scale

3. **Automation Risk:**
   - Direct value from assessment (0-1)

4. **Replaceability Risk:**
   - Direct value from assessment (0-1)

5. **Company Health Risk:**
   - `company_risk = 1 - company_health`
   - Company health is 0-1 scale

**Overall Risk Score:** `mean([tenure_risk, performance_risk, automation_risk, replaceability_risk, company_risk])`

### Protective Factors

Factors that reduce risk:
- High performance (rating ≥ 4): -1 factor
- Critical role (criticality ≥ 0.8): -1 factor
- High skill demand (demand ≥ 0.7): -1 factor
- Long tenure (≥ 3 years): -1 factor

### Primary Threats

Displayed threats include:
- **Factor:** Description of the threat
- **Urgency:** Level of urgency (high, medium, low)
- **Timeline:** Expected timeframe for the threat

### Inputs

- User profile data (tenure, performance, skills)
- Company information (health, layoffs, financial status)
- Industry data (volatility, trends)
- Assessment answers (automation level, AI tool usage, etc.)
- Role information (criticality, replaceability)

---

## Recent Activity Panel

**Component:** `RecentActivityPanel.tsx`  
**API Endpoint:** `/api/user/activity/recent`  
**Purpose:** Displays a timeline of recent user activities and milestones.

### Activity Types

1. **Assessment:** Risk assessment completions
2. **Recommendation:** Job recommendation views/interactions
3. **Application:** Job application submissions
4. **Profile Update:** Profile information changes
5. **Risk Change:** Risk level changes
6. **Success:** Achievement milestones

### Timestamp Formatting

- **Just now:** < 1 hour ago
- **Xh ago:** 1-23 hours ago
- **Xd ago:** 1-6 days ago
- **Date:** > 7 days ago (formatted as date)

### Status Indicators

- **Completed/Success:** Green badge
- **Pending:** Yellow badge
- **Failed:** Red badge

### Inputs

- Activity log from database
- Timestamp of each activity
- Activity type and metadata
- Current time (for relative time calculations)

---

## Additional Notes

### Data Sources

- **User Profile:** Financial info, personal info, goals
- **Assessment Results:** AI risk, layoff risk, income comparison scores
- **Job Postings:** Salary, requirements, company data, location
- **Housing Data:** Searches, scenarios, lease information
- **Vehicle Data:** Vehicle info, maintenance, expenses
- **Analytics Data:** User behavior, engagement, success metrics

### Caching Strategy

- Balance scores are cached for performance
- Recent activity is fetched fresh on each load
- Vehicle data refreshes every 30 seconds (if auto-refresh enabled)
- Risk assessments are cached but can be refreshed

### Error Handling

All components include:
- Loading states while fetching data
- Error states with retry options
- Graceful fallbacks with default/stub data
- Null checks for optional data fields

### Performance Considerations

- Lazy loading for heavy components
- Debounced API calls where appropriate
- Cached calculations for expensive operations
- Optimistic UI updates where possible
