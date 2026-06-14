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

interface SimulatorDefaults {
  childcare_default: number;
  childcare_metro: string;
  childcare_is_localized: boolean;
  contribution_529: number;
  gross_monthly: number;
  income_source: 'income_streams' | 'default';
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

function ContextLabelSkeleton() {
  return <div className="mt-0.5 h-4 w-32 animate-pulse rounded bg-gray-100" />;
}

export default function ParentingImpactSimulator({
  onApplyAll,
  onViewForecast,
}: ParentingImpactSimulatorProps) {
  const [defaultsLoading, setDefaultsLoading] = useState(true);
  const [defaultsMeta, setDefaultsMeta] = useState<SimulatorDefaults | null>(null);
  const [applying, setApplying] = useState(false);
  const [amounts, setAmounts] = useState<Record<string, number>>(() =>
    Object.fromEntries(RECURRING_ITEMS.map((item) => [item.id, item.defaultValue]))
  );

  useEffect(() => {
    const token = localStorage.getItem('mingus_token');
    fetch('/api/user/checklist/simulator-defaults', {
      credentials: 'include',
      headers: {
        ...csrfHeaders(),
        Authorization: `Bearer ${token ?? ''}`,
        'Content-Type': 'application/json',
      },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: SimulatorDefaults | null) => {
        if (data) {
          setDefaultsMeta(data);
          setAmounts((prev) => ({
            ...prev,
            open_529: data.contribution_529,
            childcare_waitlist: data.childcare_default,
          }));
        }
      })
      .catch(() => {})
      .finally(() => {
        setDefaultsLoading(false);
      });
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

  const renderContextLabel = (itemId: string) => {
    if (itemId === 'open_529') {
      if (defaultsLoading) return <ContextLabelSkeleton />;
      if (defaultsMeta?.income_source === 'income_streams') {
        return (
          <p className="mt-0.5 text-xs text-gray-400">
            Based on your income (~1.5% of gross monthly)
          </p>
        );
      }
      return null;
    }

    if (itemId === 'childcare_waitlist') {
      if (defaultsLoading) return <ContextLabelSkeleton />;
      if (defaultsMeta?.childcare_is_localized) {
        return (
          <p className="mt-0.5 text-xs text-gray-400">
            Based on {defaultsMeta.childcare_metro} infant care rates
          </p>
        );
      }
      return (
        <p className="mt-0.5 text-xs text-gray-400">
          National average — add your zip for local rates
        </p>
      );
    }

    return null;
  };

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
              <div key={item.id}>
                <div className="flex items-center gap-3">
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
                {renderContextLabel(item.id)}
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
