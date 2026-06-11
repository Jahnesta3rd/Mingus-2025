export const EMPLOYER_TYPE_OPTIONS = [
  { value: 'public_company', label: 'Publicly traded company' },
  { value: 'private_company', label: 'Private company' },
  { value: 'federal_government', label: 'Federal government' },
  { value: 'state_local_nonprofit', label: 'State/local government or nonprofit' },
  { value: 'self_employed', label: 'Self-employed / freelance' },
  { value: 'other', label: 'Other' },
] as const;

export type EmployerType = typeof EMPLOYER_TYPE_OPTIONS[number]['value'];

export function employerTypeHelperText(type: string | null | undefined): string | null {
  if (type === 'public_company') {
    return "We'll use SEC filings to track your employer's financial health.";
  }
  if (type === 'federal_government' || type === 'state_local_nonprofit') {
    return "We'll use your assessment answers for employer risk — live data isn't available for this employer type.";
  }
  return null;
}
