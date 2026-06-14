import React, { useEffect, useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { csrfHeaders } from '../utils/csrfHeaders';

interface ParentingImpactSimulatorProps {
  onApplyAll?: () => void;
  onViewForecast?: () => void;
}

interface RecurringSliderItem {
  id: string;
  label: string;
  min: number;
  max: number;
  defaultValue: number;
  step: number;
}

const RECURRING_ITEMS: RecurringSliderItem[] = [
  { id: 'open_529', label: '529 contribution', min: 0, max: 500, defaultValue: 200, step: 25 },
  {
    id: 'life_insurance_will',
    label: 'Life insurance',
    min: 0,
    max: 150,
    defaultValue: 50,
    step: 10,
  },
  {
    id: 'short_term_disability',
    label: 'Short-term disability',
    min: 0,
    max: 100,
    defaultValue: 30,
    step: 5,
  },
  {
    id: 'childcare_waitlist',
    label: 'Childcare (when starts)',
    min: 0,
    max: 3000,
    defaultValue: 1800,
    step: 50,
  },
];

const ONE_TIME_TOTAL = 5500;

function formatCurrency(amount: number): string {
  return `$${amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

async function applyImpactItem(itemId: string, amount: number): Promise<void> {
  const token = localStorage.getItem('mingus_token');
  await fetch('/api/user/checklist/apply-impact', {
    method: 'POST',
    credentials: 'include',
    headers: {
      ...csrfHeaders(),
      Authorization: `Bearer ${token ?? ''}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ item_id: itemId, amount_override: amount }),
  });
}

export default function ParentingImpactSimulator({
  onApplyAll,
  onViewForecast,
}: ParentingImpactSimulatorProps) {
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [amounts, setAmounts] = useState<Record<string, number>>(() =>
    Object.fromEntries(RECURRING_ITEMS.map((item) => [item.id, item.defaultValue]))
  );

  useEffect(() => {
    setLoading(false);
  }, []);

  const monthlyTotal = useMemo(
    () => RECURRING_ITEMS.reduce((sum, item) => sum + (amounts[item.id] ?? 0), 0),
    [amounts]
  );
  const annualTotal = monthlyTotal * 12;
  const combinedFirstYear = annualTotal + ONE_TIME_TOTAL;

  const handleApplyAll = () => {
    onApplyAll?.();
    setApplying(true);
    void Promise.all(
      RECURRING_ITEMS.map((item) => applyImpactItem(item.id, amounts[item.id] ?? item.defaultValue))
    )
      .then(() => {
        onViewForecast?.();
      })
      .finally(() => {
        setApplying(false);
      });
  };

  if (loading) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm" role="status">
        <div className="mb-4 h-5 w-64 animate-pulse rounded bg-gray-100" />
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-gray-100" />
            ))}
          </div>
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-gray-100" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="font-semibold text-gray-800">Parenting Financial Impact Simulator</h2>
      <p className="text-sm text-gray-500">
        See the estimated cash impact of common new-parent moves
      </p>

      <div className="mt-6 grid gap-8 md:grid-cols-2">
        <div>
          <h3 className="text-sm font-medium text-gray-800">Monthly Impact</h3>
          <div className="mt-3 space-y-4">
            {RECURRING_ITEMS.map((item) => (
              <div key={item.id} className="flex items-center gap-3">
                <span className="w-36 shrink-0 text-sm text-gray-600">{item.label}</span>
                <input
                  type="range"
                  min={item.min}
                  max={item.max}
                  step={item.step}
                  value={amounts[item.id]}
                  onChange={(e) =>
                    setAmounts((prev) => ({
                      ...prev,
                      [item.id]: Number(e.target.value),
                    }))
                  }
                  className="min-w-0 flex-1 accent-teal-500"
                  aria-label={item.label}
                />
                <span className="w-16 shrink-0 text-right text-sm text-gray-800">
                  {formatCurrency(amounts[item.id])}/mo
                </span>
              </div>
            ))}
          </div>
          <p className="mt-4 font-semibold text-gray-800">
            Monthly total: {formatCurrency(monthlyTotal)}
          </p>
          <p className="text-sm text-gray-500">Annual total: {formatCurrency(annualTotal)}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-800">First-Year One-Time Costs</h3>
          <div className="mt-3 space-y-3">
            <div className="flex items-center justify-between text-sm text-gray-700">
              <span>Baby emergency fund</span>
              <span>{formatCurrency(1500)}</span>
            </div>
            <div className="flex items-center justify-between text-sm text-gray-700">
              <span className="flex items-center gap-1">
                Out-of-pocket max (×2)
                <span
                  className="inline-flex text-gray-400"
                  title="If birth spans two calendar years, you may face up to 4× your deductible"
                >
                  <Info className="h-4 w-4" aria-hidden="true" />
                </span>
              </span>
              <span>{formatCurrency(4000)}</span>
            </div>
          </div>
          <p className="mt-4 font-semibold text-gray-800">
            First-year total: {formatCurrency(ONE_TIME_TOTAL)}
          </p>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-teal-200 bg-teal-50 px-4 py-4">
        <p className="font-semibold text-teal-800">
          Combined first-year impact: {formatCurrency(combinedFirstYear)}
        </p>
        <p className="mt-1 text-xs text-gray-400">
          This is an estimate. Actual costs vary by location, plan, and provider.
        </p>
        <button
          type="button"
          onClick={handleApplyAll}
          disabled={applying}
          className="mt-3 rounded-full border border-amber-400 px-4 py-2 text-sm text-amber-400 disabled:opacity-60"
        >
          {applying ? 'Applying…' : 'Apply to my forecast →'}
        </button>
      </div>
    </div>
  );
}
