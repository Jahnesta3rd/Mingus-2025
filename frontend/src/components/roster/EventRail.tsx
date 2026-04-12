import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface PersonEventRow {
  name: string;
  date: string;
  cost: number;
  emoji: string;
  days_until: number;
  after_event: number | null;
  coverage_status: 'covered' | 'tight' | 'shortfall' | null;
}

interface PersonEventsApiResponse {
  events: PersonEventRow[];
  thirty_day_cost_total: number;
}

interface EventRailProps {
  personId: string;
  nickname: string;
}

function formatUsdShort(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function coverageBadge(status: PersonEventRow['coverage_status']): string {
  if (status === 'covered') return '✅ Covered';
  if (status === 'tight') return '⚠️ Tight';
  if (status === 'shortfall') return '❌ Shortfall';
  return '';
}

function countdownLabel(days: number): string {
  if (days <= 0) return 'Today';
  if (days === 1) return '1 day';
  return `${days} days`;
}

export default function EventRail({ personId, nickname: _nickname }: EventRailProps) {
  const [data, setData] = useState<PersonEventsApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setFailed(false);
    const token = localStorage.getItem('mingus_token') ?? '';
    fetch(`/api/vibe-tracker/people/${encodeURIComponent(personId)}/events`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('events');
        return res.json() as Promise<PersonEventsApiResponse>;
      })
      .then((json) => {
        if (!cancelled) {
          setData({
            events: Array.isArray(json.events) ? json.events : [],
            thirty_day_cost_total:
              typeof json.thirty_day_cost_total === 'number' ? json.thirty_day_cost_total : 0,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [personId]);

  if (failed) {
    return null;
  }

  const total = data?.thirty_day_cost_total ?? 0;
  const rows = (data?.events ?? []).slice(0, 3);

  return (
    <div className="mt-4 border-t border-[#2a2030] pt-4" onClick={(e) => e.stopPropagation()}>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-sm font-medium uppercase tracking-wide text-[#9a8f7e]">Upcoming</span>
        <span className="text-sm tabular-nums text-[#9a8f7e]">
          {loading ? (
            <span className="inline-block h-3 w-24 animate-pulse rounded bg-[#2a2030]" />
          ) : (
            <>30-day total: {formatUsdShort(total)}</>
          )}
        </span>
      </div>

      {loading ? (
        <div className="space-y-2" aria-hidden>
          <div className="h-11 w-full animate-pulse rounded-lg bg-[#2a2030]/80" />
          <div className="h-11 w-full animate-pulse rounded-lg bg-[#2a2030]/80" />
        </div>
      ) : rows.length === 0 ? (
        <p className="text-sm text-[#9a8f7e]">No upcoming costs linked</p>
      ) : (
        <ul className="list-none space-y-2 p-0">
          {rows.map((ev) => {
            const badge = coverageBadge(ev.coverage_status);
            return (
              <li
                key={`${ev.name}-${ev.date}`}
                className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-[#F0E8D8]/95"
              >
                <span className="text-base leading-none" aria-hidden>
                  {ev.emoji}
                </span>
                <span className="min-w-0 flex-1 font-medium truncate">{ev.name}</span>
                <span className="shrink-0 tabular-nums text-[#9a8f7e]">{countdownLabel(ev.days_until)}</span>
                <span className="shrink-0 tabular-nums text-[#F0E8D8]/90">{formatUsdShort(ev.cost)}</span>
                {badge ? (
                  <span className="inline-flex min-h-9 shrink-0 items-center rounded-md border border-[#A78BFA]/40 bg-[#0d0a08] px-2 py-1 text-sm font-medium text-[#F0E8D8]">
                    {badge}
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}

      <p className="mt-3">
        <Link
          to="/dashboard/profile#important-dates"
          className="inline-flex min-h-11 items-center rounded-lg text-sm font-medium text-[#A78BFA] underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#A78BFA] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d0a08]"
        >
          Link an event →
        </Link>
      </p>
    </div>
  );
}
