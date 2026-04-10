export type BodyCheckOption = { label: string; value: 0 | 1 | 2 | 3 };

export type BodyCheckQuestion = {
  id: number;
  prompt: string;
  options: BodyCheckOption[];
};

/** Mirrors backend/services/body_check_service.py BODY_CHECK_QUESTIONS */
export const BODY_CHECK_QUESTIONS: BodyCheckQuestion[] = [
  {
    id: 1,
    prompt: "Sleep quality",
    options: [
      { label: "7-8 hrs solid sleep", value: 3 },
      { label: "6-7 hrs most nights", value: 2 },
      { label: "5-6 hrs, often tired", value: 1 },
      { label: "Under 5 hrs or very disrupted", value: 0 },
    ],
  },
  {
    id: 2,
    prompt: "Exercise frequency",
    options: [
      { label: "4+ times/week", value: 3 },
      { label: "2-3 times/week", value: 2 },
      { label: "Once a week or less", value: 1 },
      { label: "Rarely or never", value: 0 },
    ],
  },
  {
    id: 3,
    prompt: "Stress level",
    options: [
      { label: "Low, well-managed", value: 3 },
      { label: "Moderate, mostly handled", value: 2 },
      { label: "High, affecting daily life", value: 1 },
      { label: "Severe, overwhelming", value: 0 },
    ],
  },
  {
    id: 4,
    prompt: "Diet quality",
    options: [
      { label: "Mostly whole foods, intentional", value: 3 },
      { label: "Balanced but inconsistent", value: 2 },
      { label: "Frequent fast food / processed", value: 1 },
      { label: "Very poor, no thought given", value: 0 },
    ],
  },
  {
    id: 5,
    prompt: "Alcohol/substance use",
    options: [
      { label: "None or very rare", value: 3 },
      { label: "Social, moderate", value: 2 },
      { label: "Regular, weekly excess", value: 1 },
      { label: "Daily or problematic", value: 0 },
    ],
  },
  {
    id: 6,
    prompt: "Preventive care",
    options: [
      { label: "Annual checkups + dental + vision", value: 3 },
      { label: "Annual checkup only", value: 2 },
      { label: "Only when sick", value: 1 },
      { label: "Avoid doctors", value: 0 },
    ],
  },
  {
    id: 7,
    prompt: "Mental health care",
    options: [
      { label: "Active therapy or practice", value: 3 },
      { label: "Occasional support", value: 2 },
      { label: "Aware but not addressing", value: 1 },
      { label: "None", value: 0 },
    ],
  },
  {
    id: 8,
    prompt: "Chronic conditions",
    options: [
      { label: "None", value: 3 },
      { label: "One managed condition", value: 2 },
      { label: "Multiple managed", value: 1 },
      { label: "Unmanaged conditions", value: 0 },
    ],
  },
  {
    id: 9,
    prompt: "Energy levels at work",
    options: [
      { label: "Consistently high", value: 3 },
      { label: "Good most days", value: 2 },
      { label: "Frequently fatigued", value: 1 },
      { label: "Exhausted daily", value: 0 },
    ],
  },
  {
    id: 10,
    prompt: "Hydration",
    options: [
      { label: "8+ glasses water daily", value: 3 },
      { label: "Adequate most days", value: 2 },
      { label: "Often dehydrated", value: 1 },
      { label: "Rarely drink water", value: 0 },
    ],
  },
  {
    id: 11,
    prompt: "Screen time before bed",
    options: [
      { label: "No screens 1hr before bed", value: 3 },
      { label: "Sometimes screen-free", value: 2 },
      { label: "Usually on phone until sleep", value: 1 },
      { label: "Always on screen until sleep", value: 0 },
    ],
  },
  {
    id: 12,
    prompt: "Social connection",
    options: [
      { label: "Strong support network", value: 3 },
      { label: "Some close connections", value: 2 },
      { label: "Mostly isolated", value: 1 },
      { label: "Very isolated, lonely", value: 0 },
    ],
  },
  {
    id: 13,
    prompt: "Financial stress from health",
    options: [
      { label: "Health costs well covered", value: 3 },
      { label: "Manageable with some stress", value: 2 },
      { label: "Health bills cause significant stress", value: 1 },
      { label: "Health costs are crisis-level", value: 0 },
    ],
  },
  {
    id: 14,
    prompt: "Work-life balance",
    options: [
      { label: "Clear boundaries, protected time", value: 3 },
      { label: "Mostly balanced", value: 2 },
      { label: "Work dominates", value: 1 },
      { label: "No separation at all", value: 0 },
    ],
  },
  {
    id: 15,
    prompt: "Physical checkup recency",
    options: [
      { label: "Within the last year", value: 3 },
      { label: "1-2 years ago", value: 2 },
      { label: "3-5 years ago", value: 1 },
      { label: "Over 5 years or never", value: 0 },
    ],
  },
];
