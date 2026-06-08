import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import CardJobHome from './CardJobHome';
import {
  Brain,
  Car,
  ClipboardList,
  Heart,
  Home,
  Sparkles,
  Sun,
  Users,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

type StreakPayload = {
  last_checkin_date: string | null;
  total_checkins?: number;
};

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
  const h: Record<string, string> = {};
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

/** Parse API date or datetime strings; returns null if invalid. */
function parseApiDate(iso: string | null | undefined): Date | null {
  if (!iso || typeof iso !== 'string') return null;
  const normalized = iso.length === 10 ? `${iso}T12:00:00Z` : iso;
  const d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Human-readable relative time for a past calendar event.
 * Returns null when the date is missing or in the future (data not meaningful).
 */
function formatRelativeLastUpdate(iso: string | null | undefined): string | null {
  const then = parseApiDate(iso);
  if (!then) return null;
  const now = new Date();
  const diffMs = now.getTime() - then.getTime();
  if (diffMs < 0) return null;
  const dayMs = 86400000;
  const days = Math.floor(diffMs / dayMs);
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 14) return `${days} days ago`;
  if (days < 60) return `${Math.round(days / 7)} weeks ago`;
  if (days < 365) return `${Math.round(days / 30)} months ago`;
  return `${Math.round(days / 365)} years ago`;
}

const CHECKUP_ITEMS = [
  {
    id: 'body',
    title: 'Body wellness',
    description: 'Short check-in on physical habits and health risk signals that feed your Life Ledger.',
    to: '/dashboard/checkups/body',
    Icon: Heart,
    timestampKey: null as const,
  },
  {
    id: 'mind',
    title: 'Mind & mood (Vibe Check)',
    description: 'Quick pulse on how you are showing up mentally — used with your forecast context.',
    to: '/dashboard/checkups/mind-mood',
    Icon: Brain,
    timestampKey: null as const,
  },
  {
    id: 'spirit',
    title: 'Spirit & calm',
    description: 'Daily spirit practice check-in and financial calm on the Spirit & Finance page.',
    to: '/dashboard/checkups/spirit-calm',
    Icon: Sparkles,
    timestampKey: 'spirit' as const,
  },
  {
    id: 'housing',
    title: 'Housing & roof',
    description: 'Housing stability and roof-line costs that shape your home wealth picture.',
    to: '/dashboard/checkups/housing-roof',
    Icon: Home,
    timestampKey: null as const,
  },
  {
    id: 'vehicle',
    title: 'Vehicle health',
    description: 'Ten questions on your vehicle and surprise costs — feeds Vehicle Health in your ledger.',
    to: '/dashboard/checkups/vehicle', // #170-vehicle: resolved
    Icon: Car,
    timestampKey: null as const,
  },
  {
    id: 'relationships',
    title: 'Relationships (Vibe Checkups)',
    description: 'Deeper relationship checkup: emotional and financial signals for someone you are seeing.',
    to: '/dashboard/checkups/relationships',
    Icon: Users,
    timestampKey: null as const,
  },
  {
    id: 'daily-outlook',
    title: 'Daily Outlook',
    description: 'Light daily check-in: balance read, quick actions, and streak on your Tools tab.',
    to: '/dashboard/tools?tab=daily-outlook',
    Icon: Sun,
    timestampKey: null as const,
  },
  {
    id: 'weekly-wellness',
    title: 'Weekly wellness check-in',
    description: 'Holistic week snapshot (body, mind, money feelings) that powers wellness–finance insights on Tools.',
    to: '/dashboard/tools?tab=wellness',
    Icon: ClipboardList,
    timestampKey: 'weekly' as const,
  },
] as const;

export function CheckupsHub() {
  const { isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const fromToday = searchParams.get('from') === 'today';
  const cardParam = searchParams.get('card') ?? '1';

  const handleBack = () => {
    navigate('/dashboard/tools?from=today&card=' + cardParam, { replace: true });
  };
  const [weeklyStreak, setWeeklyStreak] = useState<StreakPayload | null>(null);
  const [spiritStreak, setSpiritStreak] = useState<StreakPayload | null>(null);
  const [timestampsLoading, setTimestampsLoading] = useState(true);

  const loadTimestamps = useCallback(async () => {
    if (!isAuthenticated) {
      setWeeklyStreak(null);
      setSpiritStreak(null);
      setTimestampsLoading(false);
      return;
    }
    setTimestampsLoading(true);
    const headers = authHeaders();
    try {
      const [wRes, sRes] = await Promise.all([
        fetch('/api/wellness/streak', { credentials: 'include', headers }),
        fetch('/api/spirit/streak', { credentials: 'include', headers }),
      ]);
      if (wRes.ok) {
        const j = (await wRes.json()) as StreakPayload;
        setWeeklyStreak(j);
      } else {
        setWeeklyStreak(null);
      }
      if (sRes.ok) {
        const j = (await sRes.json()) as StreakPayload;
        setSpiritStreak(j);
      } else {
        setSpiritStreak(null);
      }
    } catch {
      setWeeklyStreak(null);
      setSpiritStreak(null);
    } finally {
      setTimestampsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    void loadTimestamps();
  }, [loadTimestamps]);

  const lastByKey = useMemo(() => {
    return {
      weekly: weeklyStreak?.last_checkin_date ?? null,
      spirit: spiritStreak?.last_checkin_date ?? null,
    } as const;
  }, [weeklyStreak, spiritStreak]);

  const hubContent = (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-[#1E293B] sm:text-3xl">Your check-up hub</h1>
        <p className="max-w-2xl text-sm text-[#64748B] sm:text-base">
          Update each area to keep your forecast and insights current. Pick any card — each opens its own
          check-in; there is no multi-step flow here.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CHECKUP_ITEMS.map((item) => {
          const Icon = item.Icon;
          const tsKey = item.timestampKey;
          const rawDate = tsKey ? lastByKey[tsKey] : null;
          const relative =
            !timestampsLoading && tsKey && rawDate ? formatRelativeLastUpdate(rawDate) : null;
          const hasCompleted = Boolean(relative);
          const cta = hasCompleted ? 'Update' : 'Start';

          if (!isAuthenticated) return null;

          return (
            <Link
              key={item.id}
              to={item.to}
              className="group flex min-h-[44px] flex-col rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm transition hover:border-[#C4B5FD] hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#F5F3FF] text-[#5B2D8E]">
                  <Icon className="h-5 w-5" aria-hidden />
                </span>
                <div className="min-w-0 flex-1 space-y-1">
                  <h2 className="text-base font-semibold text-[#1E293B]">{item.title}</h2>
                  <p className="text-sm leading-relaxed text-[#64748B]">{item.description}</p>
                  {relative ? (
                    <p className="text-xs text-[#64748B]">
                      Last updated: <span className="font-medium text-[#475569]">{relative}</span>
                    </p>
                  ) : null}
                </div>
              </div>
              <span className="mt-4 inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#5B2D8E] px-4 text-sm font-semibold text-white group-hover:bg-[#4a2673] sm:w-auto sm:self-start">
                {cta}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );

  if (fromToday) {
    return (
      <CardJobHome cardId="vibe-roster" onBack={handleBack}>
        {hubContent}
      </CardJobHome>
    );
  }

  return hubContent;
}

export default CheckupsHub;
