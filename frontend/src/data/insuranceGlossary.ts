export interface GlossaryTerm {
  id: string;
  term: string;
  plain_english: string;
  bottom_line: string;
  emoji: string;
}

export const INSURANCE_GLOSSARY: GlossaryTerm[] = [
  {
    id: 'monthly_premium',
    term: 'Monthly Premium',
    plain_english:
      'The fixed amount you pay every month just to have insurance — whether you use it or not. Think of it like a subscription fee for access to coverage.',
    bottom_line:
      "This comes out of your paycheck regardless of your health, so lower isn't always better if it means a higher deductible.",
    emoji: '💳',
  },
  {
    id: 'deductible',
    term: 'Deductible',
    plain_english:
      'The amount you pay out of pocket before your insurance starts sharing costs. A $2,000 deductible means you pay the first $2,000 of covered care each year.',
    bottom_line:
      'If you rarely go to the doctor, a high deductible plan can save money. If you have a planned procedure or chronic condition, a lower deductible protects your wallet.',
    emoji: '🧱',
  },
  {
    id: 'oop_max',
    term: 'Out-of-Pocket Maximum',
    plain_english:
      'The most you will ever pay for covered care in a single year. Once you hit this number, your insurance covers 100% of the rest.',
    bottom_line:
      'This is your financial exposure ceiling. If your emergency fund is less than your OOP max, one bad health event could put you in debt.',
    emoji: '🛡️',
  },
  {
    id: 'coinsurance',
    term: 'Coinsurance',
    plain_english:
      'After you meet your deductible, coinsurance is the percentage of costs you still share with your insurer. At 20% coinsurance, a $1,000 procedure costs you $200.',
    bottom_line:
      'Lower coinsurance means more predictable costs after your deductible — important if you expect significant medical care.',
    emoji: '✂️',
  },
  {
    id: 'copay',
    term: 'Copay',
    plain_english:
      'A fixed dollar amount you pay for a specific service — like $35 for a doctor visit — regardless of what the visit actually costs.',
    bottom_line:
      'Copays are predictable and usually apply before your deductible, making routine care costs easy to budget.',
    emoji: '🏥',
  },
  {
    id: 'hsa',
    term: 'HSA (Health Savings Account)',
    plain_english:
      'A tax-advantaged savings account you can use for medical expenses. Contributions reduce your taxable income, the money grows tax-free, and withdrawals for medical costs are tax-free.',
    bottom_line:
      'The triple tax benefit makes an HSA one of the most powerful savings tools available — better than a 401k for healthcare costs.',
    emoji: '💰',
  },
  {
    id: 'network',
    term: 'In-Network vs Out-of-Network',
    plain_english:
      'In-network providers have contracts with your insurer at negotiated rates. Out-of-network providers can charge full price, and your insurance may cover little or nothing.',
    bottom_line:
      'Using an out-of-network provider can cost 2-5x more for the same procedure — always verify your doctors before enrolling.',
    emoji: '🗺️',
  },
  {
    id: 'hdhp',
    term: 'HDHP (High-Deductible Health Plan)',
    plain_english:
      'A plan with a lower monthly premium but a higher deductible — typically $1,600+ for an individual. These plans qualify for HSA accounts.',
    bottom_line:
      "HDHPs make financial sense if you're healthy and can fund an HSA. They're risky without an emergency reserve to cover the deductible.",
    emoji: '⚖️',
  },
  {
    id: 'premium_after_subsidy',
    term: 'Premium After Tax Credit',
    plain_english:
      'If you buy insurance on the marketplace and your income qualifies, the government pays part of your premium directly to your insurer. You only pay the difference.',
    bottom_line:
      'Tax credits can reduce a $400/month plan to under $50/month — always check your subsidy eligibility before buying a marketplace plan.',
    emoji: '🏛️',
  },
  {
    id: 'plan_type',
    term: 'Plan Type (HMO / PPO / EPO)',
    plain_english:
      'HMOs require you to choose a primary care doctor and get referrals for specialists. PPOs let you see any doctor without referrals but cost more. EPOs are in-network only with no referrals needed.',
    bottom_line:
      'If you have specialists you see regularly, a PPO gives you flexibility. If you mostly use one doctor, an HMO saves money.',
    emoji: '🏗️',
  },
];
