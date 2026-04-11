import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import LifeReadyScoreCard from './LifeReadyScoreCard';
import { useAuth } from '../hooks/useAuth';
import { useLifeLedger } from '../hooks/useLifeLedger';

interface DailyCashflowEntry {
  date: string;
  opening_balance: number;
  closing_balance: number;
  net_change: number;
  balance_status: 'healthy' | 'warning' | 'danger';
}

interface ForecastResponse {
  success: boolean;
  forecast?: {
    daily_cashflow?: DailyCashflowEntry[];
  };
}

interface RosterLatestAssessment {
  emotional_score: number;
  financial_score: number;
  annual_projection: number | null;
  completed_at: string | null;
}

interface RosterPerson {
  id: string;
  nickname: string;
  latest_assessment: RosterLatestAssessment | null;
}

interface RosterPeopleResponse {
  people: RosterPerson[];
}

function forecastAuthHeaders(): HeadersInit {
  const token =
    localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function balanceStatusLabel(status: DailyCashflowEntry['balance_status']): string {
  switch (status) {
    case 'healthy':
      return 'On track';
    case 'warning':
      return 'Watch this';
    case 'danger':
      return 'Needs attention';
    default:
      return 'On track';
  }
}

function balanceStatusBadgeClass(status: DailyCashflowEntry['balance_status']): string {
  switch (status) {
    case 'healthy':
      return 'bg-[#059669] text-white';
    case 'warning':
      return 'bg-[#D97706] text-white';
    case 'danger':
      return 'bg-[#DC2626] text-white';
    default:
      return 'bg-[#64748B] text-white';
  }
}

function thirtyDayCostFromAnnual(annual: number): number {
  return (annual * 30) / 365;
}

export default function HomeScreen() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, isAuthenticated } = useAuth();
  const { profile, loading: profileLoading, error: profileError, refetch: refetchProfile } =
    useLifeLedger(isAuthenticated);

  const [roster, setRoster] = useState<RosterPerson[]>([]);
  const [rosterLoading, setRosterLoading] = useState(true);
  const [rosterError, setRosterError] = useState(false);

  const [cashRow, setCashRow] = useState<DailyCashflowEntry | null>(null);
  const [cashLoading, setCashLoading] = useState(true);
  const [cashError, setCashError] = useState(false);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (!tab) return;
    const normalized = tab === 'vehicles' ? 'vehicle' : tab;
    if (normalized === 'vehicle' || normalized === 'housing' || normalized === 'life-ledger') {
      navigate(`/dashboard/tools?tab=${normalized}`, { replace: true });
      return;
    }
    if (tab === 'financial-forecast') {
      navigate('/dashboard/forecast', { replace: true });
    }
  }, [searchParams, navigate]);

  const fetchRoster = useCallback(async () => {
    if (!isAuthenticated) {
      setRosterLoading(false);
      return;
    }
    setRosterLoading(true);
    setRosterError(false);
    try {
      const token = localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
      const headers: HeadersInit = {};
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await fetch('/api/vibe-tracker/people', {
        credentials: 'include',
        headers,
      });
      if (!res.ok) throw new Error('roster');
      const data = (await res.json()) as RosterPeopleResponse;
      setRoster(Array.isArray(data.people) ? data.people.slice(0, 3) : []);
    } catch {
      setRoster([]);
      setRosterError(true);
    } finally {
      setRosterLoading(false);
    }
  }, [isAuthenticated]);

  const fetchCashPreview = useCallback(async () => {
    const email = user?.email?.trim();
    if (!email || !isAuthenticated) {
      setCashLoading(false);
      return;
    }
    setCashLoading(true);
    setCashError(false);
    try {
      const primaryUrl = `/api/cash-flow/enhanced-forecast/${encodeURIComponent(email)}?months=3`;
      const fallbackUrl = `/api/cash-flow/backward-compatibility/${encodeURIComponent(email)}?months=3`;
      const headers = forecastAuthHeaders();
      let res = await fetch(primaryUrl, { credentials: 'include', headers });
      if (!res.ok) {
        res = await fetch(fallbackUrl, { credentials: 'include', headers });
      }
      if (!res.ok) throw new Error('cash');
      const data: ForecastResponse = await res.json();
      const daily = data.forecast?.daily_cashflow;
      const first = daily && daily.length > 0 ? daily[0] : null;
      setCashRow(first);
    } catch {
      setCashRow(null);
      setCashError(true);
    } finally {
      setCashLoading(false);
    }
  }, [user?.email, isAuthenticated]);

  useEffect(() => {
    void fetchRoster();
  }, [fetchRoster]);

  useEffect(() => {
    void fetchCashPreview();
  }, [fetchCashPreview]);

  const goToForecastTools = () => {
    navigate('/dashboard/forecast');
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <LifeReadyScoreCard />

      <section className="rounded-2xl border border-[#A78BFA] bg-[#0D0A08] p-6 shadow-md">
        <h2 className="text-lg font-semibold text-white">Your Vibe Today</h2>
        <p className="mt-1 text-sm text-[#9A8F7E]">Based on your last Vibe Checkup</p>
        {profileLoading ? (
          <div className="mt-6 space-y-3">
            <div className="h-12 w-24 animate-pulse rounded-lg bg-white/10" />
            <div className="h-4 w-48 animate-pulse rounded bg-white/10" />
          </div>
        ) : profileError ? (
          <div className="mt-6 flex flex-col gap-3">
            <p className="text-sm text-[#9A8F7E]">Could not load your vibe score.</p>
            <button
              type="button"
              onClick={() => void refetchProfile()}
              className="inline-flex min-h-11 w-fit items-center justify-center rounded-xl border border-[#A78BFA] px-4 text-sm font-medium text-[#A78BFA] hover:bg-white/5"
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            <div className="mt-6 flex items-baseline gap-2">
              {profile?.vibe_score != null ? (
                <span className="text-4xl font-bold tabular-nums text-white">
                  {profile.vibe_score}
                </span>
              ) : (
                <span className="text-2xl font-semibold text-[#9A8F7E]">—</span>
              )}
              {profile?.vibe_score != null ? (
                <span className="text-sm text-[#9A8F7E]">/ 100</span>
              ) : null}
            </div>
            {profile?.vibe_score == null ? (
              <p className="mt-2 text-sm text-[#9A8F7E]">Complete a Vibe Checkup to see your score.</p>
            ) : null}
            <div className="mt-6">
              <Link
                to="/dashboard/vibe-checkups"
                className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#5B2D8E] px-4 text-center text-sm font-medium text-white hover:opacity-95 sm:w-auto"
              >
                Run a Checkup →
              </Link>
            </div>
          </>
        )}
      </section>

      <section className="rounded-2xl bg-white p-6 shadow-md">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold text-[#1E293B]">Your Roster</h2>
        </div>
        <p className="mt-1 text-sm text-[#64748B]">Up to three people you are tracking</p>
        {rosterLoading ? (
          <ul className="mt-4 space-y-3">
            {[0, 1, 2].map((i) => (
              <li key={i} className="h-20 animate-pulse rounded-xl bg-[#F8FAFC]" />
            ))}
          </ul>
        ) : rosterError ? null : roster.length === 0 ? (
          <p className="mt-4 text-sm text-[#64748B]">No one on your roster yet.</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {roster.map((p) => {
              const emo = p.latest_assessment?.emotional_score;
              const annual = p.latest_assessment?.annual_projection;
              const cost30 =
                typeof annual === 'number' && Number.isFinite(annual)
                  ? thirtyDayCostFromAnnual(annual)
                  : null;
              return (
                <li
                  key={p.id}
                  className="rounded-xl border border-[#E2E8F0] bg-[#FFFFFF] p-4 shadow-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-medium text-[#1E293B]">{p.nickname}</span>
                    {emo != null ? (
                      <span className="text-sm text-[#64748B]">
                        Vibe score: <span className="font-semibold text-[#1E293B]">{emo}</span>
                      </span>
                    ) : (
                      <span className="text-sm text-[#64748B]">No checkup yet</span>
                    )}
                  </div>
                  {cost30 != null ? (
                    <p className="mt-2 text-xs text-[#64748B]">
                      ~30-day cost:{' '}
                      <span className="font-medium text-[#1E293B]">{formatUsd(cost30)}</span>
                    </p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
        <div className="mt-4">
          <Link
            to="/dashboard/roster"
            className="inline-flex min-h-11 items-center text-sm font-medium text-[#6D28D9] hover:underline"
          >
            View full Roster →
          </Link>
        </div>
      </section>

      <section className="rounded-2xl bg-white p-6 shadow-md">
        <h2 className="text-lg font-semibold text-[#1E293B]">Cash Balance</h2>
        <p className="mt-1 text-sm text-[#64748B]">Snapshot from your forecast</p>
        {cashLoading ? (
          <div className="mt-6 space-y-3">
            <div className="h-10 w-40 animate-pulse rounded-lg bg-[#F8FAFC]" />
            <div className="h-8 w-28 animate-pulse rounded-full bg-[#F8FAFC]" />
          </div>
        ) : cashError || !cashRow ? (
          <p className="mt-4 text-sm text-[#64748B]">Forecast preview unavailable.</p>
        ) : (
          <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[#64748B]">
                Today&apos;s balance
              </p>
              <p className="mt-1 text-2xl font-bold tabular-nums text-[#1E293B]">
                {formatUsd(cashRow.closing_balance)}
              </p>
            </div>
            <span
              className={`inline-flex min-h-11 items-center justify-center rounded-full px-4 text-xs font-semibold uppercase ${balanceStatusBadgeClass(cashRow.balance_status)}`}
            >
              {balanceStatusLabel(cashRow.balance_status)}
            </span>
          </div>
        )}
        <div className="mt-4">
          <button
            type="button"
            onClick={goToForecastTools}
            className="inline-flex min-h-11 items-center text-sm font-medium text-[#6D28D9] hover:underline"
          >
            View Forecast →
          </button>
        </div>
      </section>
    </div>
  );
}
