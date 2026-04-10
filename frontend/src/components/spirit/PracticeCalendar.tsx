import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

export interface CalendarDayStatus {
  date: string;
  status: 'done' | 'done-2' | 'missed' | 'future' | 'no_data' | string;
}

export interface PracticeCalendarProps {
  month: string;
  userId?: string;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as const;

function cellClass(status: string, isToday: boolean): string {
  let base = 'flex h-9 w-full items-center justify-center rounded-md text-xs font-medium sm:h-10 ';
  switch (status) {
    case 'done':
      base += 'bg-[#C4A064] text-[#0f172a] ';
      break;
    case 'done-2':
      base += 'bg-amber-300/80 text-[#0f172a] ';
      break;
    case 'missed':
      base += 'bg-[#F8E0E0] text-slate-700 ';
      break;
    case 'future':
      base += 'bg-[#F0F0F0] text-slate-500 ';
      break;
    case 'no_data':
      base += 'bg-transparent text-slate-400 ';
      break;
    default:
      base += 'bg-transparent text-slate-400 ';
  }
  if (isToday) {
    base += 'ring-2 ring-[#0f172a] ring-offset-1 ';
  }
  return base;
}

function localTodayYmd(): string {
  const t = new Date();
  const y = t.getFullYear();
  const m = String(t.getMonth() + 1).padStart(2, '0');
  const d = String(t.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export const PracticeCalendar: React.FC<PracticeCalendarProps> = ({ month }) => {
  const { getAccessToken, isAuthenticated } = useAuth();
  const [days, setDays] = useState<CalendarDayStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !month) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setErr(null);

    const headers: Record<string, string> = { ...csrfHeaders() };
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    void (async () => {
      try {
        const res = await fetch(`/api/spirit/calendar?month=${encodeURIComponent(month)}`, {
          credentials: 'include',
          headers,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error((data as { error?: string }).error || 'Failed to load calendar');
        }
        const list = (data as { days?: CalendarDayStatus[] }).days ?? [];
        if (!cancelled) setDays(list);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : 'Failed to load calendar');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [month, isAuthenticated, getAccessToken]);

  const byDate = useMemo(() => Object.fromEntries(days.map((d) => [d.date, d.status])), [days]);

  const { title, cells } = useMemo(() => {
    const parts = month.split('-');
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (!y || !m || m < 1 || m > 12) {
      return { title: month, cells: [] as { key: string; dayNum: number | null; dateStr: string | null; status: string }[] };
    }
    const first = new Date(y, m - 1, 1);
    const startWeekday = first.getDay();
    const daysInMonth = new Date(y, m, 0).getDate();
    const monthTitle = first.toLocaleString('en-US', { month: 'long', year: 'numeric' });

    const out: { key: string; dayNum: number | null; dateStr: string | null; status: string }[] = [];
    for (let i = 0; i < startWeekday; i++) {
      out.push({ key: `pad-${i}`, dayNum: null, dateStr: null, status: 'pad' });
    }
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const status = byDate[dateStr] ?? 'no_data';
      out.push({ key: dateStr, dayNum: d, dateStr, status });
    }
    return { title: monthTitle, cells: out };
  }, [month, byDate]);

  const todayStr = localTodayYmd();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <h3 className="text-center font-display text-lg font-semibold text-[#0f172a]">{title}</h3>

      {loading ? (
        <p className="mt-6 text-center text-sm text-slate-500">Loading calendar…</p>
      ) : err ? (
        <p className="mt-6 text-center text-sm text-red-600">{err}</p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-7 gap-1 text-center text-[10px] font-semibold uppercase tracking-wide text-slate-500 sm:text-xs">
            {WEEKDAYS.map((d) => (
              <div key={d} className="py-1">
                {d}
              </div>
            ))}
          </div>
          <div className="mt-1 grid grid-cols-7 gap-1">
            {cells.map((c) =>
              c.dayNum === null ? (
                <div key={c.key} className="h-9 sm:h-10" aria-hidden />
              ) : (
                <div
                  key={c.key}
                  className={cellClass(c.status, c.dateStr === todayStr)}
                  title={c.dateStr ?? undefined}
                >
                  {c.dayNum}
                </div>
              )
            )}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 border-t border-slate-100 pt-4 text-[10px] text-slate-600 sm:text-xs">
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded bg-[#C4A064]" /> Done
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded bg-amber-300/80" /> Two+
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded bg-[#F8E0E0]" /> Missed
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded bg-[#F0F0F0]" /> Future
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded border border-slate-200 bg-transparent" /> No data
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded border-2 border-[#0f172a]" /> Today
            </span>
          </div>
        </>
      )}
    </div>
  );
};

export default PracticeCalendar;
