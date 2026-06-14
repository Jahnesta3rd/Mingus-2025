export interface ChecklistItem {
  id: string;
  number: number;
  title: string;
  body: string;
  badge?: string;
  urgency: 'high' | 'medium' | 'low';
}

export const CHECKLIST_ITEMS: ChecklistItem[] = [
  {
    id: 'leave_income',
    number: 1,
    title: 'Map your leave income month by month',
    body: 'Knowing your income drops during leave is different from seeing exactly what hits your account in month 2 versus month 4. The month-by-month picture often looks very different from the high-level math.',
    urgency: 'high',
  },
  {
    id: 'health_insurance_window',
    number: 2,
    title: 'Add your baby to health insurance within 30 days',
    body: 'Miss the 30-day window after birth and you wait until open enrollment. Easy to forget in the newborn fog.',
    badge: '30-day window',
    urgency: 'high',
  },
  {
    id: 'childcare_waitlist',
    number: 3,
    title: 'Get on childcare waitlists now',
    body: 'In many cities waitlists run 6 to 12 months. Get on lists now even if you are not sure you will need them.',
    urgency: 'high',
  },
  {
    id: 'out_of_pocket_double',
    number: 4,
    title: 'Budget for your out-of-pocket max twice',
    body: 'If your baby arrives late in the year you may hit your max for the birth year, then reset on January 1 just as newborn appointments begin.',
    urgency: 'medium',
  },
  {
    id: 'w4_update',
    number: 5,
    title: 'Update your W-4 after birth',
    body: 'A new dependent changes your tax situation. Update your W-4 or you will over- or underpay through the year.',
    urgency: 'medium',
  },
  {
    id: 'life_insurance_will',
    number: 6,
    title: 'Get life insurance and a will before the baby arrives',
    body: 'Both are easier and cheaper to sort before sleep deprivation sets in.',
    urgency: 'high',
  },
  {
    id: 'open_529',
    number: 7,
    title: 'Open a 529 as soon as eligible',
    body: 'You typically cannot open a 529 until 90 days after birth. Plan accordingly — and suggest grandparents contribute to the 529 instead of buying gear.',
    badge: '90-day wait',
    urgency: 'medium',
  },
  {
    id: 'trump_account',
    number: 8,
    title: 'Sign up for a Section 530a account (Trump Accounts)',
    body: 'Capture the free $1,000 at minimum. Accounts are still launching in July 2026 — get on the list now.',
    badge: 'July 2026',
    urgency: 'medium',
  },
  {
    id: 'beneficiary_update',
    number: 9,
    title: 'Update beneficiary designations separately from your will',
    body: 'Your 401(k), IRA, and life insurance beneficiaries override whatever your will says. An outdated ex or parent listed there is a real problem.',
    urgency: 'high',
  },
  {
    id: 'baby_emergency_fund',
    number: 10,
    title: 'Create a dedicated baby emergency fund',
    body: 'Even $1,000–$2,000 in a high-yield savings account for unexpected baby costs — ER visits, specialist copays, last-minute childcare gaps — helps absorb first-year chaos without draining your main emergency fund.',
    urgency: 'medium',
  },
  {
    id: 'short_term_disability',
    number: 11,
    title: 'Enroll in short-term disability before your next pregnancy',
    body: 'Many plans cover maternity leave at 60–70% of income during open enrollment. Most people only discover this exists after they needed it.',
    urgency: 'low',
  },
  {
    id: 'year_end_deductible',
    number: 12,
    title: 'Know the year-end deductible trap',
    body: "If your baby's hospital stay bridges two calendar years, you could face up to 4x your deductible — mom and baby in year one, both again when the new year resets.",
    urgency: 'medium',
  },
];
