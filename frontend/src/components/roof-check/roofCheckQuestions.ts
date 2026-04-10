export type RoofCheckOption = { label: string; value: number };

export type RoofCheckQuestion = {
  id: number;
  prompt: string;
  options: RoofCheckOption[];
};

export const ROOF_CHECK_QUESTIONS: RoofCheckQuestion[] = [
  {
    id: 1,
    prompt: "Housing type",
    options: [
      { label: "Own with equity growing", value: 3 },
      { label: "Rent strategically — saving the difference", value: 2 },
      { label: "Own but underwater/flat", value: 1 },
      { label: "Rent with nothing to show", value: 0 },
    ],
  },
  {
    id: 2,
    prompt: "Rent/mortgage to income ratio",
    options: [
      { label: "Under 25%", value: 3 },
      { label: "25-30%", value: 2 },
      { label: "30-40%", value: 1 },
      { label: "Over 40%", value: 0 },
    ],
  },
  {
    id: 3,
    prompt: "Housing stability",
    options: [
      { label: "Owned or long-term stable lease", value: 3 },
      { label: "Annual lease, renews easily", value: 2 },
      { label: "Month-to-month or uncertain", value: 1 },
      { label: "At risk of displacement", value: 0 },
    ],
  },
  {
    id: 4,
    prompt: "Location vs. opportunity",
    options: [
      { label: "Close to work, low commute cost", value: 3 },
      { label: "Manageable commute", value: 2 },
      { label: "Long commute, significant cost", value: 1 },
      { label: "Location limits job opportunities", value: 0 },
    ],
  },
  {
    id: 5,
    prompt: "Building equity",
    options: [
      { label: "Yes, paying down mortgage", value: 3 },
      { label: "Renting but investing the difference", value: 2 },
      { label: "Renting, not investing difference", value: 1 },
      { label: "No equity building at all", value: 0 },
    ],
  },
  {
    id: 6,
    prompt: "Housing cost trend",
    options: [
      { label: "Locked in stable rate", value: 3 },
      { label: "Modest increases, manageable", value: 2 },
      { label: "Significant rent increases yearly", value: 1 },
      { label: "Uncontrollable, at landlord mercy", value: 0 },
    ],
  },
  {
    id: 7,
    prompt: "Emergency housing fund",
    options: [
      { label: "3+ months housing costs saved", value: 3 },
      { label: "1-2 months saved", value: 2 },
      { label: "Less than 1 month", value: 1 },
      { label: "No housing emergency fund", value: 0 },
    ],
  },
  {
    id: 8,
    prompt: "Roommate situation",
    options: [
      { label: "Strategic roommates, significantly lowers cost", value: 3 },
      { label: "Solo but within means", value: 2 },
      { label: "Solo and stretched", value: 1 },
      { label: "Paying for others or being subsidized chaotically", value: 0 },
    ],
  },
  {
    id: 9,
    prompt: "Space vs. cost",
    options: [
      { label: "Right-sized for needs and budget", value: 3 },
      { label: "Slightly over/under but manageable", value: 2 },
      { label: "Significantly over-housed, overpaying", value: 1 },
      { label: "Under-housed, poor living conditions", value: 0 },
    ],
  },
  {
    id: 10,
    prompt: "Path to ownership",
    options: [
      { label: "Actively on path — saving, building credit", value: 3 },
      { label: "Thinking about it but no concrete plan", value: 2 },
      { label: "Not a priority right now", value: 1 },
      { label: "Feels completely out of reach", value: 0 },
    ],
  },
  {
    id: 11,
    prompt: "Property tax/insurance awareness",
    options: [
      { label: "Fully understand all housing costs", value: 3 },
      { label: "Know the basics", value: 2 },
      { label: "Vague awareness", value: 1 },
      { label: "No idea what total costs are", value: 0 },
    ],
  },
  {
    id: 12,
    prompt: "Housing decision basis",
    options: [
      { label: "Strategic — aligned with financial goals", value: 3 },
      { label: "Practical — best I could find", value: 2 },
      { label: "Emotional — fell in love with it", value: 1 },
      { label: "Reactive — took what was available", value: 0 },
    ],
  },
];
