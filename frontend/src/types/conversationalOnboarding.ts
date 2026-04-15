export type ConvCluster = 'income' | 'expenses' | 'milestones' | 'done';

export interface ConvMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface ExtractedIncome {
  monthly_takehome: number;
  has_secondary: boolean;
  secondary_amount: number | null;
}

export interface ExtractedExpense {
  name: string;
  amount: number;
}

export interface ExtractedMilestone {
  name: string;
  date_hint: string;
  cost: number;
}

export interface ExtractedData {
  income: ExtractedIncome | null;
  expenses: ExtractedExpense[];
  milestones: ExtractedMilestone[];
}

export type ConvPhase =
  | 'chatting'
  | 'confirming'
  | 'confirmed'
  | 'committing'
  | 'complete'
  | 'hard_cap'
  | 'error';
