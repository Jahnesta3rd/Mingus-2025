import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, Loader2, Scissors } from 'lucide-react';
import {
  analyzeExpenses,
  applyExpenseAuditToIcc,
  resolveCombinedTierKey,
  type ExpenseAuditAnalyzeResponse,
  type ExpenseAuditTier,
} from '../api/expenseAuditAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface ExpenseAuditCardProps {
  iccAssessmentId?: string;
  monthlyGap?: number;
  className?: string;
}

const TIER_ORDER = ['A', 'B', 'C'] as const;

function sustainabilityClass(level: string): string {
  if (level === 'green') return 'bg-green-100 text-green-800 border-green-200';
  if (level === 'red') return 'bg-red-100 text-red-800 border-red-200';
  return 'bg-yellow-100 text-yellow-800 border-yellow-200';
}

function CategoryBars({
  spending,
}: {
  spending: Record<string, number>;
}) {
  const entries = Object.entries(spending).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div className="space-y-2">
      {entries.map(([category, amount]) => (
        <div key={category}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-gray-700">{category}</span>
            <span className="font-medium text-gray-900">{formatCurrency(amount)}/mo</span>
          </div>
          <div className="h-2 rounded-full bg-gray-100">
            <div
              className="h-2 rounded-full bg-orange-500"
              style={{ width: `${Math.max(4, (amount / max) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function TierCard({
  tierKey,
  tier,
  checked,
  onToggle,
}: {
  tierKey: string;
  tier: ExpenseAuditTier;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <article
      className={`rounded-xl border p-4 ${
        checked ? 'border-orange-400 bg-orange-50/50' : 'border-gray-200 bg-white'
      }`}
    >
      <label className="flex cursor-pointer items-start gap-3">
        <input type="checkbox" checked={checked} onChange={onToggle} className="mt-1" />
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-gray-900">Tier {tierKey}</h3>
            <span
              className={`rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${sustainabilityClass(
                tier.sustainability,
              )}`}
            >
              {tier.difficulty} · {tier.sustainability}
            </span>
          </div>
          <p className="mt-1 text-lg font-bold text-orange-600">
            −{formatCurrency(tier.monthly_savings)}/month
          </p>
          <p className="mt-1 text-sm text-gray-600">{tier.summary}</p>
          <ul className="mt-3 space-y-1 text-sm text-gray-700">
            {tier.cuts.map((cut) => (
              <li key={cut.label}>
                <span className="font-medium">{cut.label}</span> (−
                {formatCurrency(cut.monthly_savings)}/mo) — {cut.example}
              </li>
            ))}
          </ul>
        </div>
      </label>
    </article>
  );
}

export default function ExpenseAuditCard({
  iccAssessmentId,
  monthlyGap,
  className = '',
}: ExpenseAuditCardProps) {
  const { getAccessToken } = useAuth();
  const [analysis, setAnalysis] = useState<ExpenseAuditAnalyzeResponse | null>(null);
  const [selectedTiers, setSelectedTiers] = useState<Set<string>>(new Set(['A']));
  const [isLoading, setIsLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [applyResult, setApplyResult] = useState<{
    savings: number;
    newGap: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await analyzeExpenses(90, { getAccessToken });
      setAnalysis(payload);
    } catch (err) {
      setAnalysis(null);
      setError(err instanceof Error ? err.message : 'Could not analyze spending.');
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void loadAnalysis();
  }, [loadAnalysis]);

  const combinedKey = useMemo(
    () => resolveCombinedTierKey(selectedTiers),
    [selectedTiers],
  );

  const combinedSavings = analysis?.combined_savings[combinedKey] ?? 0;
  const projectedGap =
    monthlyGap != null ? Math.max(0, monthlyGap - combinedSavings) : null;

  const toggleTier = (tier: string) => {
    setSelectedTiers((prev) => {
      const next = new Set(prev);
      if (next.has(tier)) {
        next.delete(tier);
      } else {
        next.add(tier);
      }
      if (next.size === 0) {
        next.add('A');
      }
      return next;
    });
  };

  const handleApply = async () => {
    if (!iccAssessmentId || !analysis) return;
    setIsApplying(true);
    setError(null);
    try {
      const result = await applyExpenseAuditToIcc(
        {
          iccAssessmentId,
          selectedTiers: Array.from(selectedTiers),
          snapshotId: analysis.snapshot_id,
        },
        { getAccessToken },
      );
      setApplyResult({
        savings: result.total_monthly_savings,
        newGap: result.new_gap_after_cuts,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not apply cuts.');
    } finally {
      setIsApplying(false);
    }
  };

  if (isLoading) {
    return (
      <section
        className={`flex items-center justify-center rounded-2xl border border-gray-200 bg-white p-8 ${className}`}
        role="status"
      >
        <Loader2 className="h-6 w-6 animate-spin text-orange-600" aria-hidden />
        <span className="ml-2 text-sm text-gray-600">Analyzing 90 days of spending...</span>
      </section>
    );
  }

  if (error && !analysis) {
    return (
      <section
        className={`rounded-2xl border border-red-100 bg-red-50 p-6 ${className}`}
        role="alert"
      >
        <p className="text-sm text-red-700">{error}</p>
        <button
          type="button"
          onClick={() => void loadAnalysis()}
          className="mt-3 rounded-lg bg-orange-600 px-3 py-2 text-sm font-medium text-white"
        >
          Retry
        </button>
      </section>
    );
  }

  if (!analysis) return null;

  return (
    <section
      className={`rounded-2xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}
      aria-label="90-day expense audit"
    >
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-50 text-orange-600">
          <Scissors size={18} aria-hidden />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">90-day expense audit</h2>
          <p className="text-sm text-gray-600">
            Average monthly spending:{' '}
            <strong className="text-gray-900">{formatCurrency(analysis.total_monthly)}</strong>
          </p>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-800">Spending by category</h3>
        <CategoryBars spending={analysis.spending_by_category} />
      </div>

      {analysis.spending_leaks.length > 0 ? (
        <div className="mb-6 rounded-xl border border-amber-100 bg-amber-50 p-4">
          <div className="flex items-center gap-2 text-amber-900">
            <AlertCircle size={16} aria-hidden />
            <p className="text-sm font-semibold">Spending leaks detected</p>
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">
            {analysis.spending_leaks.map((leak, idx) => (
              <li key={`${leak.type}-${idx}`}>{String(leak.note)}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-800">Choose your cut tiers</h3>
        {TIER_ORDER.map((key) => (
          <TierCard
            key={key}
            tierKey={key}
            tier={analysis.tier_recommendations[key]}
            checked={selectedTiers.has(key)}
            onToggle={() => toggleTier(key)}
          />
        ))}
      </div>

      {analysis.replacement_activities.length > 0 ? (
        <div className="mt-5 rounded-xl border border-gray-100 bg-gray-50 p-4">
          <h3 className="text-sm font-semibold text-gray-800">Free replacement activities</h3>
          <ul className="mt-2 space-y-2 text-sm text-gray-700">
            {analysis.replacement_activities.map((item) => (
              <li key={item.category}>
                <span className="font-medium">{item.category}:</span> {item.ideas.join(' · ')}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-5 rounded-xl border border-orange-100 bg-orange-50 p-4">
        <p className="text-sm text-gray-800">
          Combined savings ({combinedKey}):{' '}
          <strong className="text-orange-700">{formatCurrency(combinedSavings)}/month</strong>
        </p>
        {monthlyGap != null && projectedGap != null ? (
          <p className="mt-1 text-sm text-gray-700">
            If you apply {combinedKey}: saves {formatCurrency(combinedSavings)}/month, gap becomes{' '}
            <strong>{formatCurrency(projectedGap)}/month</strong> (from{' '}
            {formatCurrency(monthlyGap)}).
          </p>
        ) : null}
        {applyResult ? (
          <p className="mt-2 text-sm font-medium text-green-800">
            Applied! New gap: {formatCurrency(applyResult.newGap)}/month (−
            {formatCurrency(applyResult.savings)} savings).
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-2">
        {iccAssessmentId ? (
          <button
            type="button"
            disabled={isApplying}
            onClick={() => void handleApply()}
            className="rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-700 disabled:opacity-60"
          >
            {isApplying ? 'Applying...' : 'Apply cuts to independence plan'}
          </button>
        ) : null}
        <Link
          to="/dashboard/waterfall"
          className="rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          View in Budget Waterfall
        </Link>
      </div>
    </section>
  );
}
