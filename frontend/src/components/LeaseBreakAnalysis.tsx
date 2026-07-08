import React, { useCallback, useMemo, useState } from 'react';
import { AlertCircle, Loader2, Scale } from 'lucide-react';
import {
  analyzeLeaseBreak,
  type LeaseBreakAnalyzeResponse,
} from '../api/leaseBreakAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface LeaseBreakAnalysisProps {
  defaultMonthlyRent?: number;
  className?: string;
}

function recommendationClass(recommendation: string): string {
  if (recommendation === 'break_early') return 'border-green-300 bg-green-50 text-green-900';
  if (recommendation === 'stay_through_lease') return 'border-blue-300 bg-blue-50 text-blue-900';
  return 'border-amber-300 bg-amber-50 text-amber-900';
}

function CostBar({
  label,
  cost,
  max,
  tone,
}: {
  label: string;
  cost: number;
  max: number;
  tone: 'a' | 'b';
}) {
  const width = max > 0 ? Math.max(8, (cost / max) * 100) : 0;
  const color = tone === 'a' ? 'bg-blue-500' : 'bg-orange-500';
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="font-medium text-gray-800">{label}</span>
        <span className="font-semibold text-gray-900">{formatCurrency(cost)}</span>
      </div>
      <div className="h-4 rounded-full bg-gray-100">
        <div className={`h-4 rounded-full ${color}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function TimelineViz({ data }: { data: LeaseBreakAnalyzeResponse }) {
  const { timeline_impact: impact, months_remaining: months } = data;
  const points = useMemo(() => {
    const rows: Array<{ month: number; stay: number; break: number }> = [];
    let stayCumulative = 0;
    let breakCumulative = data.scenario_b.break_fee ?? 0;
    const monthlyStay = data.monthly_rent;
    const monthlyBreak = data.scenario_b.interim_housing_monthly ?? 500;
    for (let m = 1; m <= months; m += 1) {
      stayCumulative += monthlyStay;
      breakCumulative += monthlyBreak;
      rows.push({ month: m, stay: stayCumulative, break: breakCumulative });
    }
    return rows;
  }, [data, months]);

  const max = Math.max(...points.map((p) => Math.max(p.stay, p.break)), 1);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">Cumulative cost over remaining lease</h3>
      <div className="space-y-2">
        {points.filter((_, i) => i === 0 || i === points.length - 1 || i === Math.floor(points.length / 2)).map(
          (row) => (
            <div key={row.month} className="text-xs text-gray-600">
              <span className="font-medium text-gray-800">Month {row.month}</span>
              <div className="mt-1 grid grid-cols-2 gap-2">
                <div>
                  <span className="text-blue-700">Stay {formatCurrency(row.stay)}</span>
                  <div className="mt-0.5 h-1.5 rounded bg-gray-100">
                    <div
                      className="h-1.5 rounded bg-blue-500"
                      style={{ width: `${(row.stay / max) * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <span className="text-orange-700">Break {formatCurrency(row.break)}</span>
                  <div className="mt-0.5 h-1.5 rounded bg-gray-100">
                    <div
                      className="h-1.5 rounded bg-orange-500"
                      style={{ width: `${(row.break / max) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ),
        )}
      </div>
      <p className="mt-3 text-xs text-gray-500">
        Breaking frees ~{formatCurrency(impact.monthly_cashflow_delta_if_break)}/mo vs. current rent
        {impact.break_even_month != null ? ` · fee pays back in ~${impact.break_even_month} mo` : ''}
      </p>
    </div>
  );
}

export default function LeaseBreakAnalysis({
  defaultMonthlyRent = 1800,
  className = '',
}: LeaseBreakAnalysisProps) {
  const { getAccessToken } = useAuth();
  const [monthsRemaining, setMonthsRemaining] = useState(6);
  const [monthlyRent, setMonthlyRent] = useState(defaultMonthlyRent);
  const [breakFeePercent, setBreakFeePercent] = useState(1.5);
  const [result, setResult] = useState<LeaseBreakAnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showEmail, setShowEmail] = useState(false);
  const [showPhone, setShowPhone] = useState(false);

  const handleAnalyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await analyzeLeaseBreak(
        {
          monthsRemaining,
          monthlyRent,
          breakFeePercent,
        },
        { getAccessToken },
      );
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [breakFeePercent, getAccessToken, monthlyRent, monthsRemaining]);

  const maxCost = useMemo(() => {
    if (!result) return 1;
    return Math.max(result.scenario_a_cost, result.scenario_b_cost);
  }, [result]);

  return (
    <section className={`rounded-xl border border-gray-200 bg-gray-50 p-4 sm:p-6 ${className}`}>
      <header className="mb-4 flex items-start gap-3">
        <Scale className="mt-0.5 h-5 w-5 text-gray-700" />
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Lease break analysis</h2>
          <p className="text-sm text-gray-600">
            Compare staying through your lease vs. breaking early with interim housing.
          </p>
        </div>
      </header>

      <form
        className="mb-5 grid gap-4 sm:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void handleAnalyze();
        }}
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Months remaining</span>
          <input
            type="number"
            min={1}
            max={36}
            value={monthsRemaining}
            onChange={(e) => setMonthsRemaining(Number(e.target.value) || 1)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Monthly rent</span>
          <input
            type="number"
            min={1}
            step={50}
            value={monthlyRent}
            onChange={(e) => setMonthlyRent(Number(e.target.value) || 0)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-gray-700">Break fee (months of rent)</span>
          <input
            type="number"
            min={0}
            step={0.5}
            value={breakFeePercent}
            onChange={(e) => setBreakFeePercent(Number(e.target.value) || 0)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2"
          />
        </label>
        <div className="sm:col-span-3">
          <button
            type="submit"
            disabled={loading || monthlyRent <= 0}
            className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Compare scenarios
          </button>
        </div>
      </form>

      {error ? (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="space-y-5">
          <div
            className={`rounded-xl border p-4 ${recommendationClass(result.recommendation)}`}
          >
            <p className="font-semibold">{result.recommendation_label}</p>
            <p className="mt-1 text-sm">
              Estimated savings: <strong>{formatCurrency(result.savings)}</strong>
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-blue-200 bg-white p-4">
              <h3 className="mb-3 font-semibold text-blue-900">{result.scenario_a.label}</h3>
              <CostBar
                label="Total estimated cost"
                cost={result.scenario_a_cost}
                max={maxCost}
                tone="a"
              />
              <ul className="mt-3 space-y-1 text-sm text-gray-600">
                <li>Remaining rent: {formatCurrency(result.scenario_a.remaining_rent ?? 0)}</li>
                <li>Move-out costs: {formatCurrency(result.scenario_a.move_out_cost ?? 0)}</li>
              </ul>
            </article>
            <article className="rounded-xl border border-orange-200 bg-white p-4">
              <h3 className="mb-3 font-semibold text-orange-900">{result.scenario_b.label}</h3>
              <CostBar
                label="Total estimated cost"
                cost={result.scenario_b_cost}
                max={maxCost}
                tone="b"
              />
              <ul className="mt-3 space-y-1 text-sm text-gray-600">
                <li>Break fee: {formatCurrency(result.scenario_b.break_fee ?? 0)}</li>
                <li>
                  Interim housing ({formatCurrency(result.scenario_b.interim_housing_monthly ?? 0)}
                  /mo): {formatCurrency(result.scenario_b.interim_housing_total ?? 0)}
                </li>
                <li>Moving buffer: {formatCurrency(result.scenario_b.moving_buffer ?? 0)}</li>
              </ul>
            </article>
          </div>

          <TimelineViz data={result} />

          <div>
            <h3 className="mb-2 text-sm font-semibold text-gray-900">Landlord negotiation</h3>
            <ul className="mb-3 list-disc space-y-1 pl-5 text-sm text-gray-700">
              {result.negotiation_script.talking_points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setShowEmail((v) => !v)}
                className="text-sm font-medium text-blue-700 hover:underline"
              >
                {showEmail ? 'Hide' : 'Show'} email template
              </button>
              {showEmail ? (
                <pre className="overflow-x-auto rounded-lg border border-gray-200 bg-white p-3 text-xs text-gray-700 whitespace-pre-wrap">
                  {result.negotiation_script.email_template}
                </pre>
              ) : null}
              <button
                type="button"
                onClick={() => setShowPhone((v) => !v)}
                className="block text-sm font-medium text-blue-700 hover:underline"
              >
                {showPhone ? 'Hide' : 'Show'} phone script
              </button>
              {showPhone ? (
                <p className="rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-700">
                  {result.negotiation_script.phone_script}
                </p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
