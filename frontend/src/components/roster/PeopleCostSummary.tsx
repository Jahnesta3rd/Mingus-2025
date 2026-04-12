import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export interface PeopleCostSummaryProps {
  userEmail: string;
}

interface TrackedPersonRow {
  id: string;
  nickname: string;
  emoji: string | null;
  card_type?: string;
}

interface PeopleListApiResponse {
  people?: TrackedPersonRow[];
}

interface PersonEventsApiResponse {
  thirty_day_cost_total: number;
}

interface ChipData {
  id: string;
  nickname: string;
  emoji: string;
  monthlyApprox: number;
  isKids: boolean;
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token') ?? '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function formatUsdMo(value: number): string {
  return `${new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)}/mo`;
}

export default function PeopleCostSummary({ userEmail }: PeopleCostSummaryProps) {
  const navigate = useNavigate();
  const [chips, setChips] = useState<ChipData[] | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!userEmail) {
      setLoading(false);
      setChips([]);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/vibe-tracker/people', {
        credentials: 'include',
        headers: authHeaders(),
      });
      if (!res.ok) {
        setChips(null);
        return;
      }
      const json = (await res.json()) as PeopleListApiResponse;
      const people = json.people ?? [];
      if (people.length === 0) {
        setChips([]);
        return;
      }

      const totals = await Promise.all(
        people.map(async (p) => {
          try {
            const er = await fetch(
              `/api/vibe-tracker/people/${encodeURIComponent(p.id)}/events`,
              { credentials: 'include', headers: authHeaders() }
            );
            if (!er.ok) return { person: p, total: 0 };
            const ej = (await er.json()) as PersonEventsApiResponse;
            const t =
              typeof ej.thirty_day_cost_total === 'number' ? ej.thirty_day_cost_total : 0;
            return { person: p, total: t };
          } catch {
            return { person: p, total: 0 };
          }
        })
      );

      const mapped: ChipData[] = totals.map(({ person: p, total }) => ({
        id: p.id,
        nickname: p.nickname,
        emoji: p.emoji?.trim() || (p.card_type === 'kids' ? '👶' : '·'),
        monthlyApprox: total,
        isKids: p.card_type === 'kids',
      }));
      mapped.sort((a, b) => b.monthlyApprox - a.monthlyApprox);
      setChips(mapped);
    } catch {
      setChips(null);
    } finally {
      setLoading(false);
    }
  }, [userEmail]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm" aria-busy="true" aria-label="Loading people costs">
        <div className="mb-3 h-4 w-56 animate-pulse rounded bg-gray-200" />
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-11 w-full max-w-xs animate-pulse rounded-full bg-gray-100 sm:w-40"
            />
          ))}
        </div>
      </div>
    );
  }

  if (chips === null || chips.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-[#1E293B]">Who&apos;s in your forecast this month:</p>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {chips.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => navigate('/dashboard/roster')}
            aria-label={`Open roster: ${c.nickname}, about ${formatUsdMo(c.monthlyApprox)} in the next 30 days`}
            className={`inline-flex min-h-11 w-full max-w-full items-center gap-2 rounded-full border px-4 py-2 text-left text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 sm:w-auto sm:max-w-none ${
              c.isKids
                ? 'border-[#059669]/40 bg-[#ECFDF5] text-[#047857]'
                : 'border-[#5B2D8E]/25 bg-[#EDE9FE] text-[#5B2D8E]'
            }`}
          >
            <span className="text-lg leading-none" aria-hidden>
              {c.emoji}
            </span>
            <span className="max-w-[8rem] truncate font-medium">{c.nickname}</span>
            <span className="shrink-0 tabular-nums opacity-90">— {formatUsdMo(c.monthlyApprox)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
