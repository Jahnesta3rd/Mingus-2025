/** Mirrors backend/services/vehicle_check_service.py VEHICLE_CHECK_QUESTIONS. */

export type VehicleCheckOption = { label: string; value: number };

export type VehicleCheckQuestion = {
  id: number;
  prompt: string;
  options: VehicleCheckOption[];
};

export const VEHICLE_CHECK_QUESTIONS: VehicleCheckQuestion[] = [
  {
    id: 1,
    prompt: "Vehicle age",
    options: [
      { label: "Under 3 years", value: 3 },
      { label: "3–7 years", value: 2 },
      { label: "7–12 years", value: 1 },
      { label: "Over 12 years", value: 0 },
    ],
  },
  {
    id: 2,
    prompt: "Mileage",
    options: [
      { label: "Under 30k miles", value: 3 },
      { label: "30k–80k", value: 2 },
      { label: "80k–150k", value: 1 },
      { label: "Over 150k", value: 0 },
    ],
  },
  {
    id: 3,
    prompt: "Maintenance history",
    options: [
      { label: "Always on schedule, documented", value: 3 },
      { label: "Mostly kept up", value: 2 },
      { label: "Behind on some items", value: 1 },
      { label: "Rarely maintained", value: 0 },
    ],
  },
  {
    id: 4,
    prompt: "Current known issues",
    options: [
      { label: "None", value: 3 },
      { label: "1 minor issue", value: 2 },
      { label: "Multiple minor or 1 major", value: 1 },
      { label: "Multiple major issues", value: 0 },
    ],
  },
  {
    id: 5,
    prompt: "Reliability in last 12 months",
    options: [
      { label: "Zero unexpected breakdowns", value: 3 },
      { label: "1 minor breakdown", value: 2 },
      { label: "2–3 breakdowns", value: 1 },
      { label: "4+ or stranded", value: 0 },
    ],
  },
  {
    id: 6,
    prompt: "Insurance situation",
    options: [
      { label: "Fully covered, comprehensive", value: 3 },
      { label: "Liability + some coverage", value: 2 },
      { label: "Minimum liability only", value: 1 },
      { label: "Uninsured or lapsed", value: 0 },
    ],
  },
  {
    id: 7,
    prompt: "Vehicle use",
    options: [
      { label: "Low mileage, mostly local", value: 3 },
      { label: "Moderate commute", value: 2 },
      { label: "High mileage commuter", value: 1 },
      { label: "Commercial or extreme use", value: 0 },
    ],
  },
  {
    id: 8,
    prompt: "Fuel efficiency",
    options: [
      { label: "Hybrid or EV", value: 3 },
      { label: "Good MPG (30+)", value: 2 },
      { label: "Average MPG (20–30)", value: 1 },
      { label: "Poor MPG (under 20)", value: 0 },
    ],
  },
  {
    id: 9,
    prompt: "Emergency fund for car",
    options: [
      { label: "3+ months car costs saved", value: 3 },
      { label: "1–2 months saved", value: 2 },
      { label: "Less than 1 month", value: 1 },
      { label: "Nothing saved", value: 0 },
    ],
  },
  {
    id: 10,
    prompt: "Plan for this vehicle",
    options: [
      { label: "Keeping 3+ more years", value: 3 },
      { label: "Keeping 1–2 more years", value: 2 },
      { label: "Replacing soon but no plan", value: 1 },
      { label: "No idea, taking it day by day", value: 0 },
    ],
  },
];
