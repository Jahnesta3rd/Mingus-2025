import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';

// ========================================
// TYPES
// ========================================

type SelfTrend = 'up' | 'down' | 'flat';

interface SelfCardApiResponse {
  body_score: number | null;
  body_trend: SelfTrend;
  mind_score: number | null;
  mind_trend: SelfTrend;
  sleep_avg: number | null;
  sleep_trend: SelfTrend;
  mindfulness_days_this_month: number;
  mindfulness_streak: number;
  stress_spend_monthly: number | null;
  spending_shield_savings: number | null;
  self_score: number;
}

export interface SelfCardProps {
  className?: string;
}

// ========================================
// HELPERS
// ========================================

function formatUsd0(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function aggregateSelfTrend(a: SelfTrend, b: SelfTrend, c: SelfTrend): SelfTrend {
  let up = 0;
  let down = 0;
  for (const t of [a, b, c]) {
    if (t === 'up') up += 1;
    if (t === 'down') down += 1;
  }
  if (up > down) return 'up';
  if (down > up) return 'down';
  return 'flat';
}

function clampPct(n: number | null | undefined): number {
  if (n == null || Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(100, n));
}

function sleepAvgColorClass(hours: number): string {
  if (hours >= 7) return 'text-[#059669]';
  if (hours >= 6) return 'text-[#D97706]';
  return 'text-[#DC2626]';
}

function TrendArrow({ trend, className = '' }: { trend: SelfTrend; className?: string }) {
  if (trend === 'up') {
    return (
      <span className={`tabular-nums text-[#059669] ${className}`} aria-hidden>
        ↑
      </span>
    );
  }
  if (trend === 'down') {
    return (
      <span className={`tabular-nums text-[#DC2626] ${className}`} aria-hidden>
        ↓
      </span>
    );
  }
  return (
    <span className={`tabular-nums text-[#64748B] ${className}`} aria-hidden>
      —
    </span>
  );
}

function SelfCardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-2xl border border-[#E2E8F0] border-l-4 border-l-[#5B2D8E] bg-white p-5 shadow-md ${className}`}
      aria-busy
      aria-label="Loading your self card"
    >
      <div className="mb-4 flex justify-between gap-4">
        <div className="h-8 w-28 rounded-lg bg-[#E2E8F0]" />
        <div className="h-14 w-14 shrink-0 rounded-full bg-[#EDE9FE]" />
      </div>
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="h-4 w-24 rounded bg-[#E2E8F0]" />
          <div className="h-2 w-full rounded-full bg-[#E2E8F0]" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-28 rounded bg-[#E2E8F0]" />
          <div className="h-2 w-full rounded-full bg-[#E2E8F0]" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-36 rounded bg-[#E2E8F0]" />
          <div className="h-2 w-full rounded-full bg-[#E2E8F0]" />
        </div>
      </div>
    </div>
  );
}

// ========================================
// COMPONENT
// ========================================

export default function SelfCard({ className = '' }: SelfCardProps) {
  const [data, setData] = useState<SelfCardApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const token = localStorage.getItem('mingus_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token || 'test-token',
      };
      if (token) headers.Authorization = `Bearer ${token}`;

      const res = await fetch('/api/self-card', { credentials: 'include', headers });
      if (!res.ok) {
        setData(null);
        setError(true);
        return;
      }
      const json: unknown = await res.json();
      if (!json || typeof json !== 'object') {
        setData(null);
        setError(true);
        return;
      }
      const o = json as Record<string, unknown>;
      const trend = (v: unknown): SelfTrend =>
        v === 'up' || v === 'down' || v === 'flat' ? v : 'flat';

      const parsed: SelfCardApiResponse = {
        body_score: typeof o.body_score === 'number' ? o.body_score : null,
        body_trend: trend(o.body_trend),
        mind_score: typeof o.mind_score === 'number' ? o.mind_score : null,
        mind_trend: trend(o.mind_trend),
        sleep_avg: typeof o.sleep_avg === 'number' ? o.sleep_avg : null,
        sleep_trend: trend(o.sleep_trend),
        mindfulness_days_this_month:
          typeof o.mindfulness_days_this_month === 'number'
            ? o.mindfulness_days_this_month
            : 0,
        mindfulness_streak:
          typeof o.mindfulness_streak === 'number' ? o.mindfulness_streak : 0,
        stress_spend_monthly:
          typeof o.stress_spend_monthly === 'number' ? o.stress_spend_monthly : null,
        spending_shield_savings:
          typeof o.spending_shield_savings === 'number' ? o.spending_shield_savings : null,
        self_score: typeof o.self_score === 'number' ? o.self_score : 0,
      };
      setData(parsed);
    } catch {
      setData(null);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return <SelfCardSkeleton className={className} />;
  }

  if (error || !data) {
    return (
      <div
        className={`rounded-2xl border border-[#E2E8F0] border-l-4 border-l-[#5B2D8E] bg-white p-5 shadow-md ${className}`}
      >
        <p className="text-sm text-[#64748B]">We couldn&apos;t load your self snapshot.</p>
        <button
          type="button"
          onClick={() => void load()}
          className="mt-3 inline-flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-[#6D28D9] underline decoration-[#6D28D9]/40 underline-offset-2 hover:decoration-[#6D28D9] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        >
          Retry
        </button>
      </div>
    );
  }

  const innerTrend = aggregateSelfTrend(data.body_trend, data.mind_trend, data.sleep_trend);
  const bodyPct = clampPct(data.body_score);
  const mindPct = clampPct(data.mind_score);

  return (
    <div
      className={`rounded-2xl border border-[#E2E8F0] border-l-4 border-l-[#5B2D8E] bg-white p-5 shadow-md ${className}`}
    >
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <h2 className="font-display text-xl font-bold text-[#1E293B]">
          <span aria-hidden>👤 </span>You
        </h2>
        <div className="flex flex-col items-end gap-1">
          <div
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#5B2D8E] text-lg font-bold tabular-nums text-white"
            aria-label={`Self score ${data.self_score}`}
          >
            {data.self_score}
          </div>
          <div className="flex items-center gap-1.5">
            <TrendArrow trend={innerTrend} className="text-sm" />
            <span className="text-sm font-semibold uppercase tracking-wide text-[#64748B]">
              Your inner life
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-5">
        {/* Body */}
        <div>
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className="text-sm font-semibold text-[#1E293B]">
              <span aria-hidden>💪 </span>Body
            </span>
            <span className="flex items-center gap-2">
              <span className="text-sm tabular-nums text-[#64748B]">
                {data.body_score != null ? `${data.body_score} / 100` : '— / 100'}
              </span>
              <span className="flex items-center gap-0.5" title="Body trend">
                <TrendArrow trend={data.body_trend} className="text-xs" />
                <span className="sr-only">
                  Body trend:{' '}
                  {data.body_trend === 'up'
                    ? 'improving'
                    : data.body_trend === 'down'
                      ? 'declining'
                      : 'steady'}
                </span>
              </span>
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-[#E2E8F0]">
            <div
              className="h-full rounded-full bg-[#5B2D8E] transition-[width] duration-300"
              style={{ width: `${bodyPct}%` }}
            />
          </div>
        </div>

        {/* Mind */}
        <div>
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className="text-sm font-semibold text-[#1E293B]">
              <span aria-hidden>🧠 </span>Mind
            </span>
            <span className="flex items-center gap-2">
              <span className="text-sm tabular-nums text-[#64748B]">
                {data.mind_score != null ? `${data.mind_score} / 100` : '— / 100'}
              </span>
              <span className="flex items-center gap-0.5" title="Mind trend">
                <TrendArrow trend={data.mind_trend} className="text-xs" />
                <span className="sr-only">
                  Mind trend:{' '}
                  {data.mind_trend === 'up'
                    ? 'improving'
                    : data.mind_trend === 'down'
                      ? 'declining'
                      : 'steady'}
                </span>
              </span>
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-[#E2E8F0]">
            <div
              className="h-full rounded-full bg-[#0D9488] transition-[width] duration-300"
              style={{ width: `${mindPct}%` }}
            />
          </div>
          <p className="mt-1.5 text-sm text-[#64748B]">
            {data.mindfulness_days_this_month} day
            {data.mindfulness_days_this_month === 1 ? '' : 's'} mindfulness this month ·{' '}
            {data.mindfulness_streak}-week streak
          </p>
          {data.sleep_avg != null && (
            <p className={`mt-0.5 text-sm font-medium ${sleepAvgColorClass(data.sleep_avg)}`}>
              Avg sleep: {data.sleep_avg.toFixed(1)} hrs
              {data.sleep_avg >= 7
                ? ' (well rested)'
                : data.sleep_avg >= 6
                  ? ' (a bit short)'
                  : ' (low)'}
            </p>
          )}
        </div>

        {/* Financial self */}
        <div>
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className="text-sm font-semibold text-[#1E293B]">
              <span aria-hidden>💰 </span>Financial Self
            </span>
          </div>
          {data.stress_spend_monthly != null ? (
            <div className="space-y-2">
              <p className="text-sm text-[#64748B]">
                Est. stress spend: {formatUsd0(data.stress_spend_monthly)}/mo
              </p>
              {data.spending_shield_savings != null && data.spending_shield_savings > 0 && (
                <span
                  className="inline-flex min-h-11 items-center rounded-lg bg-[#059669]/10 px-3 py-2 text-sm font-medium text-[#059669]"
                  title="Your mindfulness practice is reducing your estimated stress spending."
                >
                  🛡 Saving ~{formatUsd0(data.spending_shield_savings)}/mo
                </span>
              )}
            </div>
          ) : (
            <p className="text-sm text-[#64748B]">Complete a weekly check-in to see your score</p>
          )}
        </div>
      </div>

      <div className="mt-5 border-t border-[#E2E8F0] pt-4">
        <Link
          to="/daily-outlook"
          className="inline-flex min-h-11 items-center rounded-lg text-sm font-medium text-[#6D28D9] underline decoration-[#6D28D9]/40 underline-offset-2 hover:decoration-[#6D28D9] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        >
          Update your check-in →
        </Link>
      </div>
    </div>
  );
}
