import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';
import type { SpiritCorrelationData, SpiritWeeklyApiRow } from '../../hooks/useSpiritCorrelation';
import { InsightCard } from './InsightCard';
import { SpiritScoreCard } from './SpiritScoreCard';

type SpiritTier = 'budget' | 'mid_tier' | 'professional';

function normalizeTier(tier: string | null | undefined, isBeta?: boolean): SpiritTier {
  if (isBeta) return 'professional';
  const t = (tier || 'budget').trim().toLowerCase();
  if (t === 'professional') return 'professional';
  if (t === 'mid_tier') return 'mid_tier';
  return 'budget';
}

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = {
    ...csrfHeaders(),
  };
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

function insightIcon(text: string): string {
  const s = text.toLowerCase();
  if (s.includes('sav')) return '💰';
  if (s.includes('impulse')) return '📉';
  if (s.includes('stress')) return '🧘🏾';
  if (s.includes('bill')) return '📅';
  if (s.includes('streak')) return '🌟';
  return '✨';
}

function splitInsightLine(text: string): { title: string; body: string } {
  const t = text.trim();
  if (!t) return { title: 'Insight', body: '' };
  const dot = t.indexOf('. ');
  if (dot >= 20 && dot <= 140) {
    return { title: t.slice(0, dot + 1).trim(), body: t.slice(dot + 2).trim() || t };
  }
  const colon = t.indexOf(':');
  if (colon >= 8 && colon <= 80) {
    return { title: t.slice(0, colon + 1).trim(), body: t.slice(colon + 1).trim() || t };
  }
  if (t.length > 100) {
    return { title: `${t.slice(0, 52).trim()}…`, body: t };
  }
  return { title: 'Practice insight', body: t };
}

function recIcon(key: string): string {
  const k = key.toLowerCase();
  const map: Record<string, string> = {
    sunrise: '🌅',
    cart: '🛒',
    calendar: '📅',
    users: '👥',
    heart: '❤️',
    leaf: '🌿',
  };
  return map[k] || '✨';
}

const MAX_RAW_PRACTICE = 31.5;

function meanNonNull(nums: (number | null | undefined)[]): number | null {
  const vals = nums.filter((n): n is number => n != null && !Number.isNaN(n));
  if (!vals.length) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function deriveScoreAndChange(
  weekly: SpiritWeeklyApiRow[],
  corr: Pick<
    SpiritCorrelationData,
    'avg_practice_score_high_weeks'
  > | null
): {
  score: number;
  change: number;
} {
  if (!weekly.length) {
    const high = corr?.avg_practice_score_high_weeks;
    if (high != null && !Number.isNaN(high)) {
      const score = Math.round(Math.min(100, (high / MAX_RAW_PRACTICE) * 100));
      return { score, change: 0 };
    }
    return { score: 0, change: 0 };
  }
  const scores = weekly.map((w) => w.practice_score);
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
  const score = Math.round(Math.min(100, (avg / MAX_RAW_PRACTICE) * 100));
  if (scores.length < 2) return { score, change: 0 };
  const delta = scores[scores.length - 1] - scores[0];
  const change = Math.round(delta * 3);
  return { score, change };
}

function percentileFromScore(score: number): number {
  return Math.max(5, Math.min(45, Math.round(42 - score * 0.35)));
}

type InsightsApi = {
  insights?: string[];
  recommendations?: { icon: string; title: string; body: string }[];
};

function formatPct(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '—';
  return `${(n * 100).toFixed(1)}%`;
}

function formatMoney(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '—';
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
}

function formatBills(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '—';
  return `${n.toFixed(1)} / 10`;
}

function badgeClass(hasValue: boolean): string {
  if (!hasValue) return 'bg-slate-100 text-slate-500 border-slate-200';
  return 'bg-amber-50 text-amber-900 border-amber-200';
}

export interface InsightsViewProps {
  userTier?: string | null;
  isBeta?: boolean;
}

export const InsightsView: React.FC<InsightsViewProps> = ({ userTier, isBeta }) => {
  const tier = normalizeTier(userTier ?? null, isBeta);
  const isPro = tier === 'professional';
  const { getAccessToken, isAuthenticated } = useAuth();

  const [insightsBody, setInsightsBody] = useState<InsightsApi | null>(null);
  const [corr, setCorr] = useState<SpiritCorrelationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const res = await fetch('/api/spirit/insights', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    const data = (await res.json().catch(() => ({}))) as InsightsApi & { error?: string };
    if (!res.ok) {
      throw new Error(data.error || res.statusText || 'Failed to load insights');
    }
    setInsightsBody({
      insights: Array.isArray(data.insights) ? data.insights.map(String) : [],
      recommendations: Array.isArray(data.recommendations) ? data.recommendations : [],
    });
  }, [getAccessToken]);

  const loadCorr = useCallback(async () => {
    const res = await fetch('/api/spirit/correlation', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    const data = (await res.json().catch(() => ({}))) as SpiritCorrelationData & { error?: string };
    if (!res.ok) {
      setCorr(null);
      return;
    }
    setCorr(data);
  }, [getAccessToken]);

  useEffect(() => {
    if (!isAuthenticated) {
      setInsightsBody(null);
      setCorr(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    void (async () => {
      try {
        await load();
        if (isPro && !cancelled) {
          await loadCorr();
        } else if (!cancelled) {
          setCorr(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load');
          setInsightsBody(null);
          setCorr(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isPro, load, loadCorr]);

  const weekly = useMemo(
    () => (Array.isArray(corr?.weekly_data) ? (corr!.weekly_data as SpiritWeeklyApiRow[]) : []),
    [corr]
  );

  const { score, change } = useMemo(
    () => deriveScoreAndChange(weekly, corr),
    [weekly, corr]
  );
  const percentile = useMemo(() => percentileFromScore(score), [score]);

  const financialRows = useMemo(() => {
    if (!isPro || !weekly.length) {
      return [
        { label: 'Savings rate', value: '—', has: false },
        { label: 'On-budget days', value: '—', has: false },
        { label: 'Impulse spend (avg / wk)', value: '—', has: false },
        { label: 'Bills on-time score', value: '—', has: false },
        { label: 'Investment contributions', value: '—', has: false },
        { label: 'Financial stress index', value: '—', has: false },
      ];
    }
    const savings = meanNonNull(weekly.map((w) => w.savings_rate ?? null));
    const impulse = meanNonNull(weekly.map((w) => w.impulse_spend ?? null));
    const stress = meanNonNull(weekly.map((w) => w.stress_index ?? null));
    const bills = meanNonNull(weekly.map((w) => w.bills_ontime ?? null));
    const onBudget = corr?.avg_impulse_checkin_days;

    return [
      { label: 'Savings rate', value: formatPct(savings), has: savings != null },
      {
        label: 'On-budget days',
        value: onBudget != null && !Number.isNaN(onBudget) ? `${onBudget.toFixed(1)} avg` : '—',
        has: onBudget != null,
      },
      { label: 'Impulse spend (avg / wk)', value: formatMoney(impulse), has: impulse != null },
      { label: 'Bills on-time score', value: formatBills(bills), has: bills != null },
      { label: 'Investment contributions', value: 'Not tracked', has: false },
      {
        label: 'Financial stress index',
        value: stress != null ? stress.toFixed(1) : '—',
        has: stress != null,
      },
    ];
  }, [isPro, weekly, corr]);

  const recommendations = insightsBody?.recommendations ?? [];
  const insights = insightsBody?.insights ?? [];

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white/80 p-6 text-center text-sm text-slate-500">
        Loading insights…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-800">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => {
            setLoading(true);
            setError(null);
            void (async () => {
              try {
                await load();
                if (isPro) await loadCorr();
                else setCorr(null);
              } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load');
              } finally {
                setLoading(false);
              }
            })();
          }}
          className="mt-2 text-sm font-semibold text-red-900 underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:items-start">
      <div className="space-y-4">
        <h2 className="font-display text-lg font-semibold text-[#0f172a]">AI-Powered Insights</h2>
        {!insights.length ? (
          <p className="text-sm text-slate-500">
            Personalized insights will appear once your spirit and finance correlations have enough data.
          </p>
        ) : (
          <div className="space-y-4">
            {insights.map((line, i) => {
              const { title, body } = splitInsightLine(line);
              return (
                <InsightCard
                  key={`${i}-${line.slice(0, 24)}`}
                  icon={insightIcon(line)}
                  title={title}
                  body={body}
                />
              );
            })}
          </div>
        )}
        <SpiritScoreCard score={score} percentile={percentile} change={change} />
      </div>

      <div className="space-y-6">
        <h2 className="font-display text-lg font-semibold text-[#0f172a]">Recommendations</h2>
        {!recommendations.length ? (
          <p className="text-sm text-slate-500">No recommendations available right now.</p>
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
            {recommendations.slice(0, 4).map((rec, idx) => (
              <div
                key={`${rec.title}-${idx}`}
                className={
                  idx > 0 ? 'border-t border-slate-100 px-5 py-4' : 'px-5 py-4'
                }
              >
                <div className="text-3xl leading-none" aria-hidden>
                  {recIcon(rec.icon)}
                </div>
                <h3 className="mt-2 text-sm font-bold text-[#0f172a]">{rec.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">{rec.body}</p>
              </div>
            ))}
          </div>
        )}

        <div>
          <h2 className="font-display text-lg font-semibold text-[#0f172a]">
            Financial Variables Tracked
          </h2>
          {!isPro ? (
            <div className="mt-3 rounded-xl border border-dashed border-slate-300 bg-white/80 p-4 text-sm text-slate-600">
              <p>Upgrade to Professional to see savings, impulse, stress, and bills metrics alongside your practice.</p>
              <Link
                to="/settings/upgrade"
                className="mt-2 inline-flex text-sm font-semibold text-[#C4A064] underline-offset-2 hover:underline"
              >
                View upgrade options
              </Link>
            </div>
          ) : (
            <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <table className="w-full text-sm">
                <tbody>
                  {financialRows.map((row) => (
                    <tr key={row.label} className="border-b border-slate-100 last:border-b-0">
                      <td className="px-4 py-3 font-medium text-slate-700">{row.label}</td>
                      <td className="px-4 py-3 text-right">
                        <span
                          className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${badgeClass(row.has)}`}
                        >
                          {row.value}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
