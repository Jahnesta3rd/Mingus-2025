// Goal types

export type GoalType =
  | 'home_purchase'
  | 'car_purchase'
  | 'apartment_move'
  | 'baby'
  | 'business'
  | 'retirement'
  | 'education'
  | 'sabbatical';

export type FeasibilityLevel = 'Low' | 'Medium' | 'High' | 'Very High';

export type DifficultyLevel = 'Low' | 'Medium' | 'High';

export type GigType = 'freelance' | 'consulting' | 'gig_work' | 'passive_income' | 'reselling';

export type LifestyleImpact = 'None' | 'Minor' | 'Moderate' | 'Significant';

export interface Goal {
  id?: string;
  type: GoalType;
  description?: string;
  parameters: Record<string, unknown>;
  timeline: number; // years
  constraints?: string[];
  createdAt?: Date | string;
}

/**
 * Canonical user profile for goal-planning UI and API payloads.
 * Note: analyzer services (`goalAnalyzer`, `profileBuilder`) typically store
 * `income` and `expenses` as **monthly** amounts. Use `AnalyzerUserProfile`
 * when interfacing directly with analysis services.
 */
export interface UserProfile {
  id: string;
  email?: string;
  /** Annual gross/take-home depending on source; see AnalyzerUserProfile for monthly. */
  income: number;
  /** Annual expenses; see AnalyzerUserProfile for monthly. */
  expenses: number;
  savings: number;
  jobTitle: string;
  industry: string;
  skills: string[];
  availableHours: number; // per week
  yearsOfExperience?: number;
  dependents?: number;
  location?: string;
}

/**
 * Profile shape used by goal analysis services (monthly income/expenses).
 */
export interface AnalyzerUserProfile {
  id?: string;
  income?: number; // monthly
  savings?: number;
  expenses?: number; // monthly
  jobTitle?: string;
  industry?: string;
  skills?: string[];
  availableHours?: number;
}

export interface GoalAnalysis {
  goalId: string;
  goalType: GoalType | string;
  goalDescription: string;

  presentState: {
    income: number;
    monthlyExpenses: number;
    savings: number;
    savingsRate: number;
    jobTitle: string;
    skills: string[];
    availableHours?: number;
  };

  futureState: {
    income: number;
    monthlyExpenses: number;
    savingsTarget: number;
    timelineYears?: number;
  };

  gaps: {
    savingsGap: number;
    incomeGap: number;
    expenseIncrease: number;
    monthlyToSave: number;
    feasible: boolean;
    feasibilityScore: number;
    totalNeeded?: number;
    monthlyExpenseIncrease?: number;
    incomeNeeded?: number;
  };

  analysis: {
    summary: string;
    keyInsight: string;
    challenges: string[];
    opportunities: string[];
  };

  summary?: string;
  dataCompleteness?: Record<string, unknown>;
}

export interface YearProjection {
  year: number;
  savings: number;
  income?: number;
  expenses?: number;
  goalAchieved: boolean;
}

/**
 * Projection row produced by recommendation path services.
 * Alias fields support existing chart/table components.
 */
export interface PathYearProjection {
  year: number;
  cumulativeSavings: number;
  goalReached: boolean;
  monthlyBoostApplied?: number;
}

export interface RecommendationPath {
  pathId: string;
  title: string;
  description: string;
  monthlyBoost: number;
  timeline: string;
  feasibility: FeasibilityLevel;
  pros: string[];
  cons: string[];
  projections: PathYearProjection[];
  isRecommended?: boolean;
  mostRealistic?: boolean;
  actionItems?: string[];
  goalReachedYear?: number | null;
}

export interface JobSuggestion {
  jobId: string;
  title: string;
  companies: CompanySuggestion[];
  expectedSalary: number;
  incomeIncrease: number;
  requiredSkills: string[];
  interviewTopics: string[];
  timeline: string;
  difficulty: DifficultyLevel;
  salaryRange?: { min: number; max: number };
  source?: string;
}

export interface CompanySuggestion {
  name: string;
  location?: string;
  hiringNow: boolean;
  avgSalary: number;
  benefits: string[];
}

export interface GigSuggestion {
  gigId: string;
  type: GigType | string;
  title: string;
  platform?: string;
  platforms?: Array<{ name: string; url: string; signupTime?: string }>;
  estimatedMonthly: { min: number; max: number } | number;
  hoursPerWeek: number;
  startupTime?: string;
  difficulty: DifficultyLevel;
  pros?: string[];
  cons?: string[];
  description?: string;
  source?: string;
}

export interface ExpenseSuggestion {
  suggestionId?: string;
  category: string;
  categoryId?: string;
  title?: string;
  currentSpending: number;
  suggestion: string;
  potentialSavings: number;
  monthlySavings?: number;
  difficulty: DifficultyLevel | 'Easy' | 'Medium' | 'Hard';
  lifestyleImpact?: LifestyleImpact;
  lifestyle_impact?: LifestyleImpact | 'None' | 'Minor' | 'Moderate';
}

export interface RecommendationsState {
  paths: RecommendationPath[];
  selectedPath: string | null;
  source: string | null;
  generatedAt: string | null;
}

export interface EnrichmentByPath<T> {
  global: { source?: string } & Record<string, unknown> | null;
  byPathId: Record<string, T>;
}

export interface GoalRecommendationsData {
  goal: Goal;
  analysis: GoalAnalysis;
  paths: RecommendationPath[];
  selectedPath?: RecommendationPath | string;
  jobSuggestions: Record<string, JobSuggestion[]>;
  gigSuggestions: Record<string, GigSuggestion[]>;
  expenseSuggestions: Record<string, ExpenseSuggestion[]>;
}

export interface GoalPlanningAnalysisResult {
  goalAnalysis: GoalAnalysis;
  recommendations: RecommendationsState;
  jobSuggestions: EnrichmentByPath<{ jobs: JobSuggestion[]; source?: string }>;
  gigSuggestions: EnrichmentByPath<{ gigs: GigSuggestion[]; source?: string }>;
  expenseSuggestions: EnrichmentByPath<{
    suggestions: ExpenseSuggestion[];
    cumulativeSavings?: number;
    gapRemaining?: number;
    source?: string;
  }>;
  partialErrors?: string[];
}

/** Converts service projection rows to chart-friendly year projections. */
export function toYearProjections(rows: PathYearProjection[]): YearProjection[] {
  return rows.map((row) => ({
    year: row.year,
    savings: row.cumulativeSavings,
    goalAchieved: row.goalReached,
  }));
}

/** Normalizes gig estimated monthly to a min/max range. */
export function normalizeGigEstimate(
  estimate: GigSuggestion['estimatedMonthly'],
): { min: number; max: number } {
  if (typeof estimate === 'number') {
    return { min: estimate, max: estimate };
  }
  return estimate;
}
