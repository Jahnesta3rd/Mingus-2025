import React, { useCallback } from 'react';
import type { StepProps } from '../StepDefinitions';

export const GOAL_INTENT_OPTIONS = [
  { value: 'home_purchase', label: 'Buy a home' },
  { value: 'car_purchase', label: 'Buy a car' },
  { value: 'apartment_move', label: 'Move to a new apartment' },
  { value: 'business', label: 'Start a business' },
  { value: 'side_income', label: 'Grow side income' },
  { value: 'debt_payoff', label: 'Pay off debt' },
  { value: 'baby', label: 'Saving for a milestone (baby, education, etc.)' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say yet' },
] as const;

const cardClass =
  'min-h-[72px] w-full rounded-xl border-2 border-[#E2E8F0] bg-white px-4 py-4 text-left text-sm font-medium text-[#1E293B] shadow-sm transition hover:border-[#5B2D8E] hover:bg-[#FAF5FF] focus:outline-none focus:ring-2 focus:ring-[#5B2D8E] focus:ring-offset-2';

export default function GoalIntentStep({ stepLabel, onSubmit, onSkip }: StepProps) {
  const handleSelect = useCallback(
    (value: string) => {
      void onSubmit({
        goal_intent: value,
        interested: value !== 'prefer_not_to_say',
      });
    },
    [onSubmit],
  );

  return (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
        {stepLabel}
      </h1>
      <p className="mt-2 text-sm text-[#64748B]">
        Optional — this helps us personalize your financial path. You can always set a goal later.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {GOAL_INTENT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className={cardClass}
            data-testid={`goal-intent-${opt.value}`}
            onClick={() => handleSelect(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={onSkip}
        className="mt-6 text-sm font-medium text-[#64748B] underline-offset-2 hover:text-[#5B2D8E] hover:underline"
      >
        Skip for now
      </button>
    </div>
  );
}
