import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import type { SpiritCheckinRow } from '../../hooks/useSpiritCheckin';
import { csrfHeaders } from '../../utils/csrfHeaders';
import { PracticeBreakdownBars, type PracticeBreakdownEntry } from './PracticeBreakdownBars';

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

const FEELING_LABELS: Record<number, string> = {
  1: 'Low',
  2: 'Neutral',
  3: 'Calm',
  4: 'Lifted',
  5: 'Renewed',
};

const PRACTICE_EMOJI: Record<string, string> = {
  prayer: '🙏',
  meditation: '🧘',
  gratitude: '📓',
  affirmation: '✨',
};

function practiceEmoji(type: string): string {
  return PRACTICE_EMOJI[type.toLowerCase()] || '✨';
}

function practiceLabel(type: string): string {
  const t = type.toLowerCase();
  if (t === 'affirmation') return 'Affirmations';
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function formatHistoryDate(iso: string): string {
  const d = new Date(iso + (iso.includes('T') ? '' : 'T12:00:00'));
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function isSameMonth(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth();
}

function buildBreakdown(checkins: SpiritCheckinRow[]): PracticeBreakdownEntry[] {
  if (!checkins.length) return [];
  const counts = new Map<string, number>();
  for (const c of checkins) {
    const k = c.practice_type.toLowerCase();
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  const total = checkins.length;
  return Array.from(counts.entries())
    .map(([type, count]) => ({
      type,
      count,
      pct: (count / total) * 100,
    }))
    .sort((a, b) => b.count - a.count);
}

type HistoryApi = {
  checkins?: SpiritCheckinRow[];
  total?: number;
};

export const HistoryView: React.FC = () => {
  const { getAccessToken, isAuthenticated } = useAuth();
  const [allCheckins, setAllCheckins] = useState<SpiritCheckinRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visible, setVisible] = useState(10);

  const fetchPage = useCallback(
    async (pageNum: number, append: boolean) => {
      const qs = new URLSearchParams({
        weeks: '8',
        per_page: '100',
        page: String(pageNum),
      });
      const res = await fetch(`/api/spirit/history?${qs}`, {
        method: 'GET',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      const data = (await res.json().catch(() => ({}))) as HistoryApi & { error?: string };
      if (!res.ok) {
        throw new Error(data.error || res.statusText || 'Failed to load history');
      }
      const rows = Array.isArray(data.checkins) ? data.checkins : [];
      const t = typeof data.total === 'number' ? data.total : rows.length;
      if (append) {
        setAllCheckins((prev) => {
          const seen = new Set(prev.map((r) => r.id));
          const next = [...prev];
          for (const r of rows) {
            if (!seen.has(r.id)) {
              seen.add(r.id);
              next.push(r);
            }
          }
          return next.sort(
            (a, b) => new Date(b.checked_in_date).getTime() - new Date(a.checked_in_date).getTime()
          );
        });
      } else {
        setAllCheckins(rows);
      }
      setTotal(t);
      setPage(pageNum);
    },
    [getAccessToken]
  );

  useEffect(() => {
    if (!isAuthenticated) {
      setAllCheckins([]);
      setTotal(0);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setVisible(10);

    void (async () => {
      try {
        await fetchPage(1, false);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load history');
          setAllCheckins([]);
          setTotal(0);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, fetchPage]);

  const breakdown = useMemo(() => buildBreakdown(allCheckins), [allCheckins]);

  const monthStats = useMemo(() => {
    const now = new Date();
    const monthStart = startOfMonth(now);
    const inMonth = allCheckins.filter((c) => {
      const d = new Date(c.checked_in_date + 'T12:00:00');
      return !Number.isNaN(d.getTime()) && d >= monthStart && isSameMonth(d, now);
    });

    if (!inMonth.length) {
      return {
        total: 0,
        avgDuration: null as number | null,
        avgFeeling: null as number | null,
        longest: null as number | null,
        bestDay: null as string | null,
        consistency: null as number | null,
      };
    }

    const durations = inMonth.map((c) => c.duration_minutes);
    const feelings = inMonth.map((c) => c.feeling_after);
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
    const avgFeeling = feelings.reduce((a, b) => a + b, 0) / feelings.length;
    const longest = Math.max(...durations);

    const weekdayCounts = new Map<number, number>();
    for (const c of inMonth) {
      const d = new Date(c.checked_in_date + 'T12:00:00');
      const wd = d.getDay();
      weekdayCounts.set(wd, (weekdayCounts.get(wd) || 0) + 1);
    }
    let bestWd = 0;
    let bestN = -1;
    weekdayCounts.forEach((n, wd) => {
      if (n > bestN) {
        bestN = n;
        bestWd = wd;
      }
    });
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const bestDay = bestN > 0 ? dayNames[bestWd] : null;

    const uniqueDays = new Set(inMonth.map((c) => c.checked_in_date)).size;
    const dayOfMonth = now.getDate();
    const consistency = dayOfMonth > 0 ? Math.round((uniqueDays / dayOfMonth) * 100) : null;

    return {
      total: inMonth.length,
      avgDuration,
      avgFeeling,
      longest,
      bestDay,
      consistency,
    };
  }, [allCheckins]);

  const canLoadMore = visible < allCheckins.length || allCheckins.length < total;

  const handleLoadMore = async () => {
    if (visible < allCheckins.length) {
      setVisible((v) => v + 10);
      return;
    }
    if (allCheckins.length >= total) return;
    setLoadingMore(true);
    try {
      await fetchPage(page + 1, true);
      setVisible((v) => v + 10);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load more');
    } finally {
      setLoadingMore(false);
    }
  };

  const rowsShown = allCheckins.slice(0, visible);

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white/80 p-6 text-center text-sm text-slate-500">
        Loading history…
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
                await fetchPage(1, false);
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
        <h2 className="font-display text-lg font-semibold text-[#0f172a]">Recent Check-Ins</h2>
        {!rowsShown.length ? (
          <p className="text-sm text-slate-500">
            No check-ins in the last eight weeks yet. Complete your daily check-in to build history here.
          </p>
        ) : (
          <>
            <ul className="max-h-[min(28rem,70vh)] space-y-0 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-sm">
              {rowsShown.map((c) => {
                const feelingLabel = FEELING_LABELS[c.feeling_after] ?? '—';
                return (
                  <li
                    key={c.id}
                    className="flex items-start justify-between gap-4 border-b border-slate-100 px-4 py-3 last:border-b-0"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-[#0f172a]">
                        {formatHistoryDate(c.checked_in_date)}{' '}
                        <span className="font-normal text-slate-600">
                          · {practiceLabel(c.practice_type)} {practiceEmoji(c.practice_type)}
                        </span>
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {c.duration_minutes} min · {feelingLabel}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="font-display text-lg font-semibold tabular-nums text-[#C4A064]">
                        {c.practice_score.toFixed(1)}
                      </p>
                      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                        Score
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
            {canLoadMore ? (
              <button
                type="button"
                onClick={() => void handleLoadMore()}
                disabled={loadingMore}
                className="w-full rounded-lg border border-slate-200 bg-white py-2.5 text-sm font-semibold text-[#0f172a] transition-colors hover:bg-slate-50 disabled:opacity-60"
              >
                {loadingMore ? 'Loading…' : 'Load more'}
              </button>
            ) : null}
          </>
        )}
      </div>

      <div className="space-y-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="font-display text-base font-semibold text-[#0f172a]">Practice mix</h3>
          <p className="mt-1 text-xs text-slate-500">Share of check-ins in the last 8 weeks</p>
          <div className="mt-4">
            <PracticeBreakdownBars breakdown={breakdown} />
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="font-display text-base font-semibold text-[#0f172a]">This Month</h3>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <StatCell
              label="Total Check-Ins"
              value={monthStats.total > 0 ? String(monthStats.total) : '—'}
            />
            <StatCell
              label="Avg Duration"
              value={
                monthStats.avgDuration != null ? `${monthStats.avgDuration.toFixed(1)} min` : '—'
              }
            />
            <StatCell
              label="Avg Feeling Score"
              value={monthStats.avgFeeling != null ? monthStats.avgFeeling.toFixed(1) : '—'}
            />
            <StatCell
              label="Longest Session"
              value={monthStats.longest != null ? `${monthStats.longest} min` : '—'}
            />
            <StatCell label="Best Practice Day" value={monthStats.bestDay ?? '—'} />
            <StatCell
              label="Consistency Rate"
              value={monthStats.consistency != null ? `${monthStats.consistency}%` : '—'}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

function StatCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-3 py-2.5">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-[#0f172a]">{value}</p>
    </div>
  );
}
