import React, { useCallback } from 'react';
import type { StepProps } from '../StepDefinitions';

const OPTIONS = [
  { label: 'Reddit', value: 'reddit' },
  { label: 'LinkedIn', value: 'linkedin' },
  { label: 'A friend or colleague', value: 'friend' },
  { label: 'Email or newsletter', value: 'email' },
  { label: 'Instagram', value: 'instagram' },
  { label: 'Somewhere else', value: 'other' },
] as const;

const cardClass =
  'min-h-[72px] w-full rounded-xl border-2 border-[#E2E8F0] bg-white px-4 py-4 text-left text-sm font-medium text-[#1E293B] shadow-sm transition hover:border-[#5B2D8E] hover:bg-[#FAF5FF] focus:outline-none focus:ring-2 focus:ring-[#5B2D8E] focus:ring-offset-2';

export default function AcquisitionSourceStep({ stepLabel, onSubmit }: StepProps) {
  const handleSelect = useCallback(
    (value: string) => {
      void onSubmit({ acquisition_source: value });
    },
    [onSubmit]
  );

  return (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
        {stepLabel}
      </h1>
      <p className="mt-2 text-sm text-[#64748B]">
        How did you hear about Mingus? Tap one option to continue.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className={cardClass}
            data-testid={`acquisition-source-${opt.value}`}
            onClick={() => handleSelect(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
