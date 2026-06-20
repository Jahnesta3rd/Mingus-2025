import React, { useState } from 'react';

interface CostOfSummerLoveCardProps {
  /** Called when CTA is tapped — parent expands the checklist. */
  onExploreChecklist: () => void;
  className?: string;
}

const COST_BREAKDOWN = [
  { label: 'Childcare (city average)', amount: '$14,117 / year' },
  { label: 'Healthcare premium increase', amount: '$3,200 / year' },
  { label: 'Lost income opportunity', amount: '$10,000+ / year' },
  { label: '529 gap if started at birth', amount: '$1,500 / year' },
] as const;

export default function CostOfSummerLoveCard({
  onExploreChecklist,
  className = '',
}: CostOfSummerLoveCardProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) {
    return null;
  }

  return (
    <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-900">Cost of Summer Love</h2>
        <span className="shrink-0 rounded-full bg-purple-50 px-2 py-0.5 text-xs text-purple-700">
          📊 Planning insight
        </span>
      </div>

      <p className="my-4 text-center text-5xl font-bold text-purple-700">$18,271</p>
      <p className="text-center text-sm text-gray-500">
        Average annual cost of raising a child in the US
      </p>

      <div className="my-3 border-t border-gray-100" />

      <div>
        {COST_BREAKDOWN.map((row) => (
          <div key={row.label} className="flex justify-between py-1.5 text-sm">
            <span className="text-gray-600">{row.label}</span>
            <span className="font-medium text-gray-900">{row.amount}</span>
          </div>
        ))}
      </div>

      <p className="mt-2 text-xs text-gray-400">USDA data, 2023. Excludes college costs.</p>

      <button
        type="button"
        onClick={onExploreChecklist}
        className="mt-4 w-full rounded-lg bg-purple-600 py-2.5 text-sm font-medium text-white hover:bg-purple-700"
      >
        See what to do financially if that changes →
      </button>

      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="mt-2 w-full cursor-pointer text-center text-xs text-gray-400 underline"
      >
        Not planning for kids — hide this
      </button>
    </div>
  );
}
