export type MilestoneCategory =
  // Family & Relationships
  | 'expecting'          // We're expecting 🍼  ← baby trigger
  | 'baby_born'          // Baby arrived
  | 'adoption'           // Adoption finalized
  | 'wedding_own'        // Our wedding
  | 'wedding_other'      // Attending a wedding
  | 'engagement'         // Got engaged
  | 'divorce'            // Separation / divorce
  | 'anniversary'        // Anniversary
  // Home
  | 'home_purchase'      // Buying a home
  | 'home_sale'          // Selling a home
  | 'moving'             // Moving / relocation
  | 'renovation'         // Home renovation
  | 'lease_renewal'      // Lease renewal / rent change
  // Career & Money
  | 'job_change'         // Starting a new job
  | 'job_loss'           // Job ended / layoff
  | 'promotion'          // Promotion / raise
  | 'bonus_expected'     // Bonus coming
  | 'side_hustle_launch' // Launching a side hustle
  | 'retirement'         // Retiring
  | 'return_to_work'     // Returning to work
  // Education
  | 'tuition_due'        // Tuition / school payment
  | 'graduation'         // Graduation
  | 'student_loan_start' // Student loan repayment starts
  // Travel & Events
  | 'vacation'           // Vacation
  | 'travel_other'       // Travel / trip
  // Health
  | 'medical_procedure'  // Medical procedure / surgery
  | 'insurance_enrollment' // Open enrollment
  // Vehicles
  | 'car_inspection'     // Car inspection
  | 'car_purchase'       // Buying a vehicle
  | 'car_sale'           // Selling a vehicle
  // Milestones / Other
  | 'birthday_self'      // My birthday
  | 'birthday_other'     // Someone else's birthday
  | 'debt_payoff'        // Debt payoff goal
  | 'savings_goal'       // Savings milestone
  | 'custom';            // Something else

export interface MilestoneMeta {
  category: MilestoneCategory;
  label: string;       // Display label in picker and widget
  emoji: string;       // Icon — used by SpecialDatesWidget and picker
  group: MilestoneGroup; // For grouped picker UI
  defaultCost: number | null; // Pre-fill cost field (null = leave blank)
}

export type MilestoneGroup =
  | 'Family & Relationships'
  | 'Home'
  | 'Career & Money'
  | 'Education'
  | 'Travel & Events'
  | 'Health'
  | 'Vehicles'
  | 'Milestones & Goals';

export const MILESTONE_META: Record<MilestoneCategory, MilestoneMeta> = {
  expecting:            { category: 'expecting',           label: "We're expecting",         emoji: '🍼', group: 'Family & Relationships', defaultCost: null },
  baby_born:            { category: 'baby_born',           label: 'Baby arrived',             emoji: '👶', group: 'Family & Relationships', defaultCost: null },
  adoption:             { category: 'adoption',            label: 'Adoption finalized',       emoji: '🏠', group: 'Family & Relationships', defaultCost: null },
  wedding_own:          { category: 'wedding_own',         label: 'Our wedding',              emoji: '💍', group: 'Family & Relationships', defaultCost: 30000 },
  wedding_other:        { category: 'wedding_other',       label: 'Attending a wedding',      emoji: '💐', group: 'Family & Relationships', defaultCost: 500 },
  engagement:           { category: 'engagement',          label: 'Got engaged',              emoji: '💎', group: 'Family & Relationships', defaultCost: null },
  divorce:              { category: 'divorce',             label: 'Separation / divorce',     emoji: '📋', group: 'Family & Relationships', defaultCost: null },
  anniversary:          { category: 'anniversary',         label: 'Anniversary',              emoji: '🎉', group: 'Family & Relationships', defaultCost: 200 },
  home_purchase:        { category: 'home_purchase',       label: 'Buying a home',            emoji: '🏡', group: 'Home',                   defaultCost: null },
  home_sale:            { category: 'home_sale',           label: 'Selling a home',           emoji: '🔑', group: 'Home',                   defaultCost: null },
  moving:               { category: 'moving',              label: 'Moving / relocation',      emoji: '📦', group: 'Home',                   defaultCost: 2500 },
  renovation:           { category: 'renovation',          label: 'Home renovation',          emoji: '🔨', group: 'Home',                   defaultCost: null },
  lease_renewal:        { category: 'lease_renewal',       label: 'Lease renewal',            emoji: '📝', group: 'Home',                   defaultCost: null },
  job_change:           { category: 'job_change',          label: 'Starting a new job',       emoji: '💼', group: 'Career & Money',         defaultCost: null },
  job_loss:             { category: 'job_loss',            label: 'Job ended / layoff',       emoji: '📉', group: 'Career & Money',         defaultCost: null },
  promotion:            { category: 'promotion',           label: 'Promotion / raise',        emoji: '📈', group: 'Career & Money',         defaultCost: null },
  bonus_expected:       { category: 'bonus_expected',      label: 'Bonus coming',             emoji: '💵', group: 'Career & Money',         defaultCost: null },
  side_hustle_launch:   { category: 'side_hustle_launch',  label: 'Launching a side hustle',  emoji: '🚀', group: 'Career & Money',         defaultCost: null },
  retirement:           { category: 'retirement',          label: 'Retiring',                 emoji: '🏖️', group: 'Career & Money',        defaultCost: null },
  return_to_work:       { category: 'return_to_work',      label: 'Returning to work',        emoji: '👩‍💼', group: 'Career & Money',      defaultCost: null },
  tuition_due:          { category: 'tuition_due',         label: 'Tuition / school payment', emoji: '🎓', group: 'Education',              defaultCost: null },
  graduation:           { category: 'graduation',          label: 'Graduation',               emoji: '🎓', group: 'Education',              defaultCost: 500 },
  student_loan_start:   { category: 'student_loan_start',  label: 'Student loan repayment',   emoji: '💳', group: 'Education',              defaultCost: null },
  vacation:             { category: 'vacation',            label: 'Vacation',                 emoji: '✈️', group: 'Travel & Events',        defaultCost: 3000 },
  travel_other:         { category: 'travel_other',        label: 'Trip / travel',            emoji: '🧳', group: 'Travel & Events',        defaultCost: null },
  medical_procedure:    { category: 'medical_procedure',   label: 'Medical procedure',        emoji: '🏥', group: 'Health',                 defaultCost: null },
  insurance_enrollment: { category: 'insurance_enrollment',label: 'Open enrollment',          emoji: '📋', group: 'Health',                 defaultCost: null },
  car_inspection:       { category: 'car_inspection',      label: 'Car inspection',           emoji: '🚗', group: 'Vehicles',               defaultCost: 150 },
  car_purchase:         { category: 'car_purchase',        label: 'Buying a vehicle',         emoji: '🚙', group: 'Vehicles',               defaultCost: null },
  car_sale:             { category: 'car_sale',            label: 'Selling a vehicle',        emoji: '🔑', group: 'Vehicles',               defaultCost: null },
  birthday_self:        { category: 'birthday_self',       label: 'My birthday',              emoji: '🎂', group: 'Milestones & Goals',     defaultCost: null },
  birthday_other:       { category: 'birthday_other',      label: "Someone's birthday",      emoji: '🎁', group: 'Milestones & Goals',     defaultCost: 100 },
  debt_payoff:          { category: 'debt_payoff',         label: 'Debt payoff goal',         emoji: '✅', group: 'Milestones & Goals',     defaultCost: null },
  savings_goal:         { category: 'savings_goal',        label: 'Savings milestone',        emoji: '🏦', group: 'Milestones & Goals',     defaultCost: null },
  custom:               { category: 'custom',              label: 'Something else',           emoji: '📅', group: 'Milestones & Goals',     defaultCost: null },
};

// Groups in display order
export const MILESTONE_GROUPS: MilestoneGroup[] = [
  'Family & Relationships', 'Home', 'Career & Money', 'Education',
  'Travel & Events', 'Health', 'Vehicles', 'Milestones & Goals',
];

// All items for a given group, in order
export const getMilestonesByGroup = (group: MilestoneGroup): MilestoneMeta[] =>
  Object.values(MILESTONE_META).filter(m => m.group === group);

// The three categories that trigger the New Parent Checklist
export const BABY_CATEGORIES: MilestoneCategory[] = ['expecting', 'baby_born', 'adoption'];

// Backward compat: map legacy hard-coded field names to new categories
export const LEGACY_FIELD_TO_CATEGORY: Record<string, MilestoneCategory> = {
  vacation: 'vacation',
  car_inspection: 'car_inspection',
  sisters_wedding: 'wedding_other',
  birthday: 'birthday_self',
};
