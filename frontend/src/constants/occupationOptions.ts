export type OccupationGroup = {
  label: string;
  options: { value: string; label: string }[];
};

export const OCCUPATION_GROUPS: OccupationGroup[] = [
  {
    label: 'Technology',
    options: [
      { value: 'software_developer', label: 'Software Developer' },
      { value: 'data_analyst', label: 'Data Analyst' },
      { value: 'data_scientist', label: 'Data Scientist' },
      { value: 'qa_tester', label: 'QA Tester' },
      { value: 'it_support', label: 'IT Support' },
    ],
  },
  {
    label: 'Marketing & Creative',
    options: [
      { value: 'marketing_coordinator', label: 'Marketing Coordinator' },
      { value: 'marketing_manager', label: 'Marketing Manager' },
      { value: 'content_writer', label: 'Content Writer' },
      { value: 'social_media_manager', label: 'Social Media Manager' },
      { value: 'graphic_designer', label: 'Graphic Designer' },
    ],
  },
  {
    label: 'Operations & Admin',
    options: [
      { value: 'admin_assistant', label: 'Admin Assistant' },
      { value: 'data_entry', label: 'Data Entry' },
      { value: 'operations_coordinator', label: 'Operations Coordinator' },
    ],
  },
  {
    label: 'Management',
    options: [
      { value: 'program_manager', label: 'Program Manager' },
      { value: 'project_manager', label: 'Project Manager' },
      { value: 'operations_manager', label: 'Operations Manager' },
      { value: 'director', label: 'Director' },
      { value: 'vp_or_above', label: 'VP or Above' },
    ],
  },
  {
    label: 'Government / Public Administration',
    options: [
      { value: 'public_administrator', label: 'Public Administrator' },
      { value: 'policy_analyst', label: 'Policy Analyst' },
      { value: 'federal_program_mgr', label: 'Federal Program Manager' },
    ],
  },
  {
    label: 'Finance / Consulting / Sales',
    options: [
      { value: 'financial_analyst', label: 'Financial Analyst' },
      { value: 'consultant', label: 'Consultant' },
      { value: 'account_executive', label: 'Account Executive' },
      { value: 'sales_rep', label: 'Sales Rep' },
    ],
  },
];

// Build a flat Set of valid keys for validation
export const VALID_OCCUPATION_KEYS = new Set(
  OCCUPATION_GROUPS.flatMap((g) => g.options.map((o) => o.value))
);

if (VALID_OCCUPATION_KEYS.size !== 25) {
  throw new Error(
    `VALID_OCCUPATION_KEYS must have exactly 25 entries, got ${VALID_OCCUPATION_KEYS.size}`
  );
}
