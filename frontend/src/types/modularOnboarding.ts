export type ModuleId =
  | 'income'
  | 'housing'
  | 'vehicle'
  | 'recurring_expenses'
  | 'roster'
  | 'career'
  | 'milestones';

export const MODULE_ORDER: ReadonlyArray<ModuleId> = [
  'income',
  'housing',
  'vehicle',
  'recurring_expenses',
  'roster',
  'career',
  'milestones',
] as const;

export type ModuleStatus =
  | 'pending'
  | 'active'
  | 'in_progress'
  | 'complete'
  | 'skipped';

export type InputMode =
  | 'text'
  | 'number'
  | 'currency'
  | 'date'
  | 'chip_select'
  | 'chip_multi'
  | 'year'
  | 'zip';

export interface ChipOption {
  value: string;
  label: string;
}

export interface InputSpec {
  mode: InputMode;
  placeholder?: string;
  min?: number;
  max?: number;
  chips?: ChipOption[];
  fieldHint?: string;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  inputHint?: InputSpec;
}

/** Vehicle year bounds — evaluated at module load; do not hardcode a calendar year literal. */
const _currentYear = new Date().getFullYear();
export const MAX_VEHICLE_YEAR = _currentYear + 1;
export const MIN_VEHICLE_YEAR = 1950;

// Expense category keys (Option C). Single source of truth for the
// frontend — must match backend CATEGORY_KEYS.
export type ExpenseCategoryId =
  | 'insurance'
  | 'debt'
  | 'subscription'
  | 'utilities'
  | 'other'
  | 'groceries'
  | 'healthcare'
  | 'childcare';

export const EXPENSE_CATEGORY_IDS: ReadonlyArray<ExpenseCategoryId> = [
  'insurance',
  'debt',
  'subscription',
  'utilities',
  'other',
  'groceries',
  'healthcare',
  'childcare',
] as const;

export interface IncomeData {
  monthly_takehome?: number;
  pay_frequency?: 'weekly' | 'biweekly' | 'semimonthly' | 'monthly';
  has_secondary?: boolean;
  secondary_amount?: number;
  bonus_cadence?: string;
}

export interface HousingData {
  housing_type?: 'rent' | 'own';
  monthly_cost?: number;
  zip_or_city?: string;
  split_share_pct?: number;
  has_buy_goal?: boolean;
  target_price?: number;
  target_timeline_months?: number;
}

export interface VehicleEntry {
  make?: string;
  model?: string;
  year?: number;
  monthly_fuel?: number;
  monthly_payment?: number;
  recent_maintenance?: boolean;
}

export interface VehicleData {
  vehicle_count: number;
  vehicles: VehicleEntry[];
}

export interface RecurringExpensesData {
  categories: Partial<Record<ExpenseCategoryId, number>>;
}

export interface RosterPerson {
  nickname?: string;
  relationship_type?: string;
  monthly_cost?: number;
}

export interface RosterData {
  relationship_status?: 'single' | 'dating' | 'partnered' | 'married' | 'other';
  people: RosterPerson[];
  monthly_social_spend?: number;
}

export interface CareerData {
  current_role?: string;
  industry?: string;
  years_experience?: number;
  satisfaction?: number;
  open_to_move?: boolean;
  target_comp?: number;
}

export interface MilestoneEvent {
  name?: string;
  date?: string; // YYYY-MM-DD
  cost?: number;
  recurring?: boolean;
}

export interface MilestonesData {
  events: MilestoneEvent[];
}

export interface ModuleData {
  income: IncomeData;
  housing: HousingData;
  vehicle: VehicleData;
  recurring_expenses: RecurringExpensesData;
  roster: RosterData;
  career: CareerData;
  milestones: MilestonesData;
}

export interface ModuleState {
  id: ModuleId;
  display_name: string;
  status: ModuleStatus;
  order: number;
}

export type OnboardingPhase =
  | 'chatting'
  | 'ready_to_commit'
  | 'committing'
  | 'module_cap'
  | 'hard_cap'
  | 'complete'
  | 'error';

export interface OnboardingState {
  modules: Record<ModuleId, ModuleState>;
  currentModule: ModuleId | null;
  data: ModuleData;
  messages: Message[];
  isTyping: boolean;
  inputHint: InputSpec | null;
  phase: OnboardingPhase;
  error: string | null;
  turnCount: number;
}

// API response shapes (matches GC1/GC2 backend contracts):
export interface MessageResponse {
  phase: 'chatting' | 'ready_to_commit' | 'module_cap' | 'hard_cap';
  assistant_message?: string;
  extracted?: Record<string, unknown>;
  module?: ModuleId;
  prompt_user_to_confirm?: boolean;
  detected_input_mode?: InputSpec;
}

export interface CommitFieldResponse {
  ok: boolean;
  changed: boolean;
  committed_at: string;
  field_path: string;
  value_stored: unknown;
  assigned_index?: number;
  note?: string;
}

export interface CommitModuleResponse {
  ok: boolean;
  module_id: ModuleId;
  next_module: ModuleId | null;
  all_done: boolean;
  committed_fields: string[];
  failed_fields: Array<{
    field_path: string;
    error: string;
    reason: string;
  }>;
  is_revisit: boolean;
}

export interface SkipModuleResponse {
  next_module: ModuleId | null;
  all_done: boolean;
}

export interface RevisitModuleResponse {
  current_module: ModuleId;
}

export interface StatusResponse {
  current_module: ModuleId | null;
  completed_modules: ModuleId[];
  skipped_modules: ModuleId[];
  turn_count: number;
  is_complete: boolean;
  data: Partial<ModuleData>;
}
