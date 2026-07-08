import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ExternalLink, Loader2, Printer } from 'lucide-react';
import {
  getPhasedIndependenceTimeline,
  type PhasedIndependenceBuyingGuide,
  type PhasedIndependenceScenario,
  type PhasedIndependenceTimelineResponse,
} from '../api/phasedIndependenceAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface PhasedIndependencePlannerProps {
  totalGap?: number;
  monthlySavings?: number;
  startupCostFull?: number;
  className?: string;
}

const LEAVE_OPTIONS = [
  { key: 'leave_3', label: '3 months' },
  { key: 'leave_6', label: '6 months' },
  { key: 'leave_12', label: '12 months' },
  { key: 'full_setup', label: '18+ months' },
] as const;

function tierBadgeClass(level: number): string {
  const classes = [
    'bg-red-100 text-red-800',
    'bg-orange-100 text-orange-800',
    'bg-blue-100 text-blue-800',
    'bg-green-100 text-green-800',
  ];
  return classes[level] ?? 'bg-gray-100 text-gray-800';
}

function ShoppingListPrint({
  guide,
  scenario,
}: {
  guide: PhasedIndependenceBuyingGuide;
  scenario: PhasedIndependenceScenario;
}) {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    const content = printRef.current;
    if (!content) return;
    const printWindow = window.open('', '_blank', 'width=800,height=900');
    if (!printWindow) return;
    printWindow.document.write(`
      <html><head><title>${guide.printable_title}</title>
      <style>
        body { font-family: system-ui, sans-serif; padding: 24px; color: #111; }
        h1 { font-size: 20px; margin-bottom: 4px; }
        h2 { font-size: 14px; margin-top: 20px; }
        ul { padding-left: 18px; }
        li { margin-bottom: 6px; }
        .meta { color: #555; font-size: 13px; margin-bottom: 16px; }
      </style></head><body>${content.innerHTML}</body></html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-semibold text-gray-900">Shopping list — {guide.title}</h3>
        <button
          type="button"
          onClick={handlePrint}
          className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
        >
          <Printer className="h-4 w-4" />
          Print
        </button>
      </div>
      <div ref={printRef}>
        <h1>{guide.printable_title}</h1>
        <p className="meta">
          Target: {scenario.label} · Housing: {scenario.housing_label} · Budget{' '}
          {formatCurrency(guide.budget_target)}
        </p>
        <p className="text-sm text-gray-600">{guide.strategy}</p>
        {guide.categories.map((category) => (
          <div key={category.name}>
            <h2>
              {category.name} ({formatCurrency(category.budget)})
            </h2>
            <ul>
              {category.items.map((row) => (
                <li key={row.item}>
                  {row.item} — {formatCurrency(row.budget)}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {guide.retailers.map((retailer) => (
          <a
            key={retailer.name}
            href={retailer.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-3 py-1 text-xs text-blue-700 hover:bg-blue-50"
            title={retailer.tip}
          >
            {retailer.name}
            <ExternalLink className="h-3 w-3" />
          </a>
        ))}
      </div>
    </div>
  );
}

export default function PhasedIndependencePlanner({
  totalGap = 765,
  monthlySavings = 600,
  startupCostFull,
  className = '',
}: PhasedIndependencePlannerProps) {
  const { getAccessToken } = useAuth();
  const [data, setData] = useState<PhasedIndependenceTimelineResponse | null>(null);
  const [selectedKey, setSelectedKey] = useState<string>('leave_6');
  const [savingsInput, setSavingsInput] = useState(monthlySavings);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getPhasedIndependenceTimeline(
        {
          totalGap,
          monthlySavings: savingsInput,
          startupCostFull,
          scenarioKey: selectedKey,
        },
        { getAccessToken },
      );
      setData(payload);
      setSelectedKey(payload.selected_scenario_key);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load independence plan');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, savingsInput, selectedKey, startupCostFull, totalGap]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedScenario = useMemo(
    () => data?.scenarios.find((row) => row.key === selectedKey) ?? data?.scenarios[0],
    [data, selectedKey],
  );

  const tierRows = useMemo(() => {
    if (!data?.tier_definitions) return [];
    return [0, 1, 2, 3]
      .map((level) => data.tier_definitions[`tier_${level}`])
      .filter((row): row is NonNullable<typeof row> => Boolean(row && 'tier' in row));
  }, [data]);

  const activeGuides = useMemo(() => {
    if (!data || !selectedScenario) return [];
    return selectedScenario.tier_levels
      .map((level) => data.buying_guides[String(level)])
      .filter(Boolean);
  }, [data, selectedScenario]);

  if (loading && !data) {
    return (
      <section
        className={`flex items-center justify-center rounded-xl border border-gray-200 bg-white p-8 ${className}`}
      >
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </section>
    );
  }

  if (error || !data || !selectedScenario) {
    return (
      <section className={`rounded-xl border border-red-200 bg-red-50 p-4 ${className}`}>
        <p className="text-sm text-red-700">{error ?? 'Unable to load phased independence plan.'}</p>
      </section>
    );
  }

  return (
    <section className={`rounded-xl border border-gray-200 bg-gray-50 p-4 sm:p-6 ${className}`}>
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Phased independence planner</h2>
        <p className="text-sm text-gray-600">
          Four tiers from emergency move-out ({formatCurrency(3500)}) to full setup with car (
          {formatCurrency(16100)}). ICC full startup reference:{' '}
          {formatCurrency(data.startup_cost_full)}.
        </p>
      </header>

      <div className="mb-5 grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Leave by</span>
          <select
            value={selectedKey}
            onChange={(e) => setSelectedKey(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          >
            {LEAVE_OPTIONS.map((opt) => (
              <option key={opt.key} value={opt.key}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Monthly savings toward move-out</span>
          <input
            type="number"
            min={0}
            step={50}
            value={savingsInput}
            onChange={(e) => setSavingsInput(Number(e.target.value) || 0)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
      </div>

      <div className="mb-5 rounded-xl border border-indigo-200 bg-indigo-50/60 p-4">
        <h3 className="font-semibold text-gray-900">{selectedScenario.label}</h3>
        <p className="mt-1 text-sm text-gray-600">{selectedScenario.housing_label}</p>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-gray-500">Startup needed</dt>
            <dd className="font-semibold">{formatCurrency(selectedScenario.cumulative_startup)}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Months to fund</dt>
            <dd className="font-semibold">
              {selectedScenario.months_to_fund ?? '—'}
              {selectedScenario.on_track ? (
                <span className="ml-1 text-green-700">on track</span>
              ) : (
                <span className="ml-1 text-amber-700">stretch</span>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Monthly gap ref.</dt>
            <dd className="font-semibold">{formatCurrency(selectedScenario.monthly_gap_reference)}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Shortfall at target</dt>
            <dd className="font-semibold">
              {formatCurrency(selectedScenario.shortfall_at_target)}
            </dd>
          </div>
        </dl>
        <div className="mt-3 flex flex-wrap gap-2">
          {selectedScenario.tier_breakdown.map((tier) => (
            <span
              key={tier.tier}
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${tierBadgeClass(tier.tier)}`}
            >
              Tier {tier.tier}: {formatCurrency(tier.cost)}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">All tier definitions</h3>
        <div className="grid gap-3 lg:grid-cols-2">
          {tierRows.map((tier) => (
            <article key={tier.tier} className="rounded-lg border border-gray-200 bg-white p-3 text-sm">
              <div className="mb-1 flex items-center justify-between">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${tierBadgeClass(tier.tier)}`}>
                  Tier {tier.tier}
                </span>
                <span className="font-semibold text-gray-900">
                  {formatCurrency(tier.cumulative_cost)} total
                </span>
              </div>
              <p className="font-medium text-gray-900">{tier.name}</p>
              <p className="mt-1 text-gray-600">{tier.description}</p>
              <p className="mt-2 text-xs text-gray-500">{tier.furniture_summary}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">Buying guides</h3>
        <div className="space-y-4">
          {activeGuides.map((guide) => (
            <ShoppingListPrint key={guide.tier} guide={guide} scenario={selectedScenario} />
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-900">Contingency planning</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {data.contingency_scenarios.map((row) => (
            <article
              key={row.key}
              className={`rounded-lg border p-3 text-sm ${
                row.still_on_track ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'
              }`}
            >
              <p className="font-medium text-gray-900">{row.label}</p>
              {row.adjusted_monthly_savings != null ? (
                <p className="text-gray-600">
                  Savings: {formatCurrency(row.adjusted_monthly_savings)}/mo
                </p>
              ) : null}
              {row.adjusted_startup != null ? (
                <p className="text-gray-600">
                  Startup: {formatCurrency(row.adjusted_startup)}
                </p>
              ) : null}
              {row.months_to_fund != null ? (
                <p className="text-gray-600">
                  Months to fund: {row.months_to_fund}
                  {row.delta_months != null && row.delta_months !== 0 ? (
                    <span className="ml-1">
                      ({row.delta_months > 0 ? '+' : ''}
                      {row.delta_months} mo)
                    </span>
                  ) : null}
                </p>
              ) : null}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
