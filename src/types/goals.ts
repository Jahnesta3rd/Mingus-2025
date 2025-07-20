export interface Goal {
  id?: string;
  type: GoalType;
  name: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: Date;
  priority: 1 | 2 | 3 | 4 | 5;
  monthlyContribution: number;
  motivationNote: string;
}

export type GoalType = 
  | 'emergency_fund' 
  | 'debt_payoff' 
  | 'home_purchase' 
  | 'vacation_fund' 
  | 'wedding_fund' 
  | 'car_purchase' 
  | 'retirement_savings' 
  | 'investment_portfolio'
  | 'side_business' 
  | 'education_fund' 
  | 'child_fund' 
  | 'important_dates';

export interface UserFinances {
  monthlyIncome: number;
  monthlyExpenses: number;
  currentSavings: number;
  debtPayments: number;
}

export interface GoalSuggestion {
  amount: number;
  reasoning: string;
}

export interface Milestone {
  percentage: number;
  amount: number;
  date: Date;
  celebration: string;
  monthsFromNow: number;
} 