import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { ReactNode, TouchEvent } from 'react';
import { useSnapshotData } from '../hooks/useSnapshotData';
import type {
  ActionData,
  CareerData,
  CashNowData,
  FaithCardData,
  MilestonesData,
  RosterData,
  SpendingData,
  VibeCheckData,
} from '../types/snapshot';

const TOTAL_CARDS = 8;
const SWIPE_THRESHOLD_PX = 50;

export interface MingusSnapshotProps {
  /** Called when user taps a CTA on the final action panel — receives the tab name to navigate to */
  onComplete: (topCta: string) => void;
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatUsdAbs(value: number): string {
  return formatUsd(Math.abs(value));
}

function formatIntegerWithCommas(value: number): string {
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 0,
  }).format(Math.round(value));
}

type BalanceStatus = CashNowData['balance_status'];

function statusTextColor(status: BalanceStatus): string {
  switch (status) {
    case 'healthy':
      return '#059669';
    case 'warning':
      return '#D97706';
    case 'danger':
      return '#DC2626';
    default:
      return '#1E293B';
  }
}

function StatusBadge({ status }: { status: BalanceStatus }) {
  if (status === 'healthy') {
    return (
      <span
        className="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white"
        style={{ backgroundColor: '#059669' }}
      >
        ON TRACK
      </span>
    );
  }
  if (status === 'warning') {
    return (
      <span
        className="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
        style={{ backgroundColor: '#D97706', color: '#1E293B' }}
      >
        WATCH THIS
      </span>
    );
  }
  return (
    <span
      className="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white"
      style={{ backgroundColor: '#DC2626' }}
    >
      NEEDS ATTENTION
    </span>
  );
}

function VibeScoreRing({ score }: { score: number }) {
  const clamped = Math.min(100, Math.max(0, score));
  const ringColor = clamped >= 70 ? '#059669' : clamped >= 50 ? '#D97706' : '#DC2626';
  const size = 80;
  const stroke = 5;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dashOffset = c * (1 - clamped / 100);

  return (
    <div className="relative mx-auto" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        className="absolute left-0 top-0 -rotate-90"
        aria-hidden
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#E2E8F0"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={ringColor}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={dashOffset}
          style={{ willChange: 'stroke-dashoffset' }}
        />
      </svg>
      <div
        className="absolute flex items-center justify-center rounded-full text-[22px] font-bold text-white"
        style={{
          backgroundColor: ringColor,
          inset: stroke,
        }}
      >
        {Math.round(score)}
      </div>
    </div>
  );
}

function CardFrame({
  index,
  tag,
  title,
  showSwipeHint,
  swipeHintText,
  children,
}: {
  index: number;
  tag: string;
  title: string;
  showSwipeHint: boolean;
  /** When set with showSwipeHint, replaces default gray hint (purple styling). */
  swipeHintText?: string;
  children: ReactNode;
}) {
  return (
    <div
      className="box-border w-screen shrink-0 overflow-y-auto px-5 pb-[72px] pt-6"
      style={{ height: '100dvh', background: '#FAF5FF' }}
    >
      <p
        className="mb-2 text-[11px] font-medium uppercase tracking-wide"
        style={{ color: '#5B2D8E' }}
      >
        CARD {index} OF {TOTAL_CARDS} · {tag}
      </p>
      <h2 className="mb-4 text-[22px] font-bold" style={{ color: '#1E293B' }}>
        {title}
      </h2>
      {children}
      {showSwipeHint &&
        (swipeHintText ? (
          <p className="mt-10 text-center text-[12px]" style={{ color: '#5B2D8E' }}>
            {swipeHintText}
          </p>
        ) : (
          <p className="mt-10 text-center text-[12px] text-slate-500">Swipe to continue →</p>
        ))}
    </div>
  );
}

function VibeCardContent({
  loading,
  vibe,
  onStartCheckIn,
}: {
  loading: boolean;
  vibe: VibeCheckData | null;
  onStartCheckIn: () => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col items-center px-2 pt-4">
        <div className="h-20 w-20 animate-pulse rounded-full bg-slate-200" />
        <div className="mt-6 h-3 w-[80%] max-w-xs animate-pulse rounded bg-slate-200" />
        <div className="mt-3 h-3 w-[60%] max-w-[240px] animate-pulse rounded bg-slate-200" />
      </div>
    );
  }

  if (!vibe) {
    return (
      <div className="flex flex-col items-center px-2 pt-8 text-center">
        <span className="text-6xl" aria-hidden>
          🔍
        </span>
        <h3 className="mt-6 text-lg font-semibold" style={{ color: '#1E293B' }}>
          No check-in yet
        </h3>
        <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-slate-600">
          Complete your first Vibe Checkup to see how your relationships and wellness connect to your
          finances.
        </p>
        <button
          type="button"
          className="mt-6 border-none bg-transparent p-0 text-base font-semibold"
          style={{ color: '#5B2D8E' }}
          onClick={onStartCheckIn}
        >
          Start a check-in →
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center px-1">
      <VibeScoreRing score={vibe.score} />
      <p className="mt-5 text-center text-base font-bold" style={{ color: '#1E293B' }}>
        {vibe.verdict}
      </p>
      <div className="mt-6 grid w-full max-w-md grid-cols-3 gap-2 text-center">
        <div>
          <p className="text-[11px] text-slate-500">Wellness</p>
          <p className="mt-1 text-base font-bold" style={{ color: '#1E293B' }}>
            {vibe.wellness_score}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500">Financial</p>
          <p className="mt-1 text-base font-bold" style={{ color: '#1E293B' }}>
            {vibe.financial_score}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500">Emotional</p>
          <p className="mt-1 text-base font-bold" style={{ color: '#1E293B' }}>
            {vibe.emotional_score}
          </p>
        </div>
      </div>
      {vibe.headline_insight ? (
        <div
          className="mt-6 w-full max-w-md rounded-xl p-3 text-[14px] leading-snug"
          style={{ backgroundColor: '#EDE9F6', color: '#5B2D8E' }}
        >
          {vibe.headline_insight}
        </div>
      ) : null}
    </div>
  );
}

function CashCardContent({
  loading,
  cash,
  loadError,
  onAddIncome,
}: {
  loading: boolean;
  cash: CashNowData | null;
  loadError: boolean;
  onAddIncome: () => void;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-[60px] animate-pulse rounded-xl bg-slate-200" />
        <div className="h-[60px] animate-pulse rounded-xl bg-slate-200" />
        <div className="h-[60px] animate-pulse rounded-xl bg-slate-200" />
      </div>
    );
  }

  if (loadError || !cash) {
    return (
      <div className="px-1 pt-4 text-center">
        <p className="text-base" style={{ color: '#1E293B' }}>
          Unable to load your balance.
        </p>
        <button
          type="button"
          className="mt-5 border-none bg-transparent p-0 text-base font-semibold"
          style={{ color: '#5B2D8E' }}
          onClick={onAddIncome}
        >
          Add income & expenses →
        </button>
      </div>
    );
  }

  const todayColor = statusTextColor(cash.balance_status);
  const forecastColor = statusTextColor(cash.worst_status_30);
  const tighterPeriod = cash.worst_status_30 !== cash.balance_status;

  return (
    <div className="space-y-3">
      <div className="mb-3 rounded-xl bg-white p-4 shadow-sm">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Today&apos;s balance</p>
        <p className="mt-2 text-[32px] font-bold leading-none" style={{ color: todayColor }}>
          {formatUsd(cash.todays_balance)}
        </p>
      </div>
      <div className="mb-3 rounded-xl bg-white p-4 shadow-sm">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">30-day forecast</p>
        <p className="mt-2 text-2xl font-bold leading-none" style={{ color: forecastColor }}>
          {formatUsd(cash.balance_30_day)}
        </p>
        <p
          className="mt-2 text-sm font-medium"
          style={{ color: cash.net_change_30 >= 0 ? '#059669' : '#DC2626' }}
        >
          {cash.net_change_30 >= 0 ? '▲' : '▼'} {formatUsdAbs(cash.net_change_30)} from today
        </p>
      </div>
      <div className="mb-3 rounded-xl bg-white p-4 shadow-sm">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Status</p>
        <div className="mt-3">
          <StatusBadge status={cash.balance_status} />
        </div>
        {tighterPeriod ? (
          <p className="mt-3 text-[12px] text-slate-500">Tighter period coming in the next 30 days</p>
        ) : null}
      </div>
    </div>
  );
}

function spendingBarColor(pct: number): string {
  if (pct >= 0.3) return '#DC2626';
  if (pct >= 0.15) return '#D97706';
  return '#5B2D8E';
}

function SpendingCardContent({
  loading,
  spending,
  onAddExpenses,
}: {
  loading: boolean;
  spending: SpendingData | null;
  onAddExpenses: () => void;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-12 animate-pulse rounded-lg bg-slate-200" />
        <div className="h-12 animate-pulse rounded-lg bg-slate-200" />
        <div className="h-12 animate-pulse rounded-lg bg-slate-200" />
      </div>
    );
  }

  if (!spending) {
    return (
      <div className="px-1 pt-4 text-center">
        <p className="text-base" style={{ color: '#1E293B' }}>
          Add your expenses to see a spending breakdown.
        </p>
        <button
          type="button"
          className="mt-5 border-none bg-transparent p-0 text-base font-semibold"
          style={{ color: '#5B2D8E' }}
          onClick={onAddExpenses}
        >
          Add expenses →
        </button>
      </div>
    );
  }

  const pctHigh = spending.top_categories.some((c) => c.pct_of_income >= 0.3);

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Monthly income</p>
        <p className="text-[15px] font-bold" style={{ color: '#059669' }}>
          {formatUsd(spending.income_monthly)}
        </p>
      </div>
      <div className="my-4 h-px w-full bg-slate-200" />
      {spending.top_categories.map((cat) => {
        const pct = cat.pct_of_income;
        const pctLabel = Math.round(pct * 100);
        const barPct = Math.min(100, Math.max(0, pct * 100));
        return (
          <div key={cat.name} className="mb-4">
            <div className="flex w-full items-baseline justify-between gap-2">
              <span className="text-[15px] font-bold" style={{ color: '#1E293B' }}>
                {cat.name}
              </span>
              <span className="text-[15px]" style={{ color: '#1E293B' }}>
                {formatUsd(cat.amount)}
              </span>
            </div>
            <div className="mt-2 w-full overflow-hidden rounded-full bg-slate-100" style={{ height: 6 }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${barPct}%`,
                  backgroundColor: spendingBarColor(pct),
                }}
              />
            </div>
            <p className="mt-1 text-right text-[11px] text-slate-500">{pctLabel}% of income</p>
          </div>
        );
      })}
      {pctHigh ? (
        <div className="mt-2 rounded-xl p-3 text-[14px] leading-snug" style={{ backgroundColor: '#FEF3C7', color: '#1E293B' }}>
          One category is taking 30%+ of your income. That&apos;s worth a closer look.
        </div>
      ) : null}
    </div>
  );
}

function RosterCardContent({
  loading,
  roster,
}: {
  loading: boolean;
  roster: RosterData | null;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-14 animate-pulse rounded-lg bg-slate-200" />
        <div className="h-14 animate-pulse rounded-lg bg-slate-200" />
      </div>
    );
  }

  const noPeople = !roster || roster.people.length === 0;

  if (noPeople) {
    return (
      <div className="flex flex-col items-center px-2 pt-6 text-center">
        <span className="text-5xl" aria-hidden>
          👥
        </span>
        <p className="mt-5 text-base font-semibold" style={{ color: '#1E293B' }}>
          No one on your roster yet.
        </p>
        <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-slate-600">
          Run a Vibe Checkup to start tracking the people in your life and their financial impact.
        </p>
      </div>
    );
  }

  const trendLine = (trend: RosterData['people'][number]['trend']) => {
    if (trend === 'rising') {
      return <span className="text-[11px]" style={{ color: '#DC2626' }}>↑ Trending up</span>;
    }
    if (trend === 'falling') {
      return <span className="text-[11px]" style={{ color: '#059669' }}>↓ Trending down</span>;
    }
    return <span className="text-[11px] text-slate-500">→ Stable</span>;
  };

  return (
    <div>
      <div className="flex flex-col gap-4 rounded-xl bg-white p-4 shadow-sm sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Annual cost</p>
          <p className="mt-1 text-[28px] font-bold leading-none" style={{ color: '#1E293B' }}>
            {formatUsd(roster.total_annual_cost)}
          </p>
        </div>
        <div className="sm:text-right">
          <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Per month</p>
          <p className="mt-1 text-[20px] font-bold leading-none" style={{ color: '#1E293B' }}>
            {formatUsd(roster.total_monthly_cost)}
          </p>
        </div>
      </div>
      {roster.has_financial_drag ? (
        <div className="mt-3 rounded-xl p-3 text-[14px] leading-snug" style={{ backgroundColor: '#FEF3C7', color: '#1E293B' }}>
          Your savings rate has dropped while roster costs increased. The Vibe Checkups financial projection was
          built for this. Worth a fresh look.
        </div>
      ) : null}
      {roster.relationship_cost_delta > 0 ? (
        <p className="mt-3 text-[12px] text-slate-500">
          ↑ ${formatIntegerWithCommas(roster.relationship_cost_delta)} more than last year across your roster
        </p>
      ) : null}
      <div className="mt-4 space-y-2">
        {roster.people.slice(0, 4).map((person, i) => (
          <div key={`${person.nickname}-${i}`} className="rounded-lg bg-white px-3 py-2 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[15px] font-medium" style={{ color: '#1E293B' }}>
                <span aria-hidden>{person.emoji}</span> {person.nickname}
              </span>
              <span className="text-[15px]" style={{ color: '#1E293B' }}>
                {formatUsd(person.estimated_annual_cost)}
              </span>
            </div>
            <div className="mt-1">{trendLine(person.trend)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function milestoneBadgeStyle(days: number): { bg: string; text: string } {
  if (days <= 7) return { bg: '#DC2626', text: '#FFFFFF' };
  if (days <= 30) return { bg: '#D97706', text: '#1E293B' };
  return { bg: '#E2E8F0', text: '#1E293B' };
}

function MilestonesCardContent({
  loading,
  milestones,
  onReviewForecast,
  onAddMilestones,
}: {
  loading: boolean;
  milestones: MilestonesData | null;
  onReviewForecast: () => void;
  onAddMilestones: () => void;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-12 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-12 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-12 animate-pulse rounded-xl bg-slate-200" />
      </div>
    );
  }

  const emptyUpcoming = !milestones || milestones.upcoming.length === 0;

  if (emptyUpcoming) {
    return (
      <div className="flex flex-col items-center px-2 pt-6 text-center">
        <span className="text-5xl" aria-hidden>
          📅
        </span>
        <p className="mt-5 text-base font-semibold" style={{ color: '#1E293B' }}>
          No upcoming milestones found.
        </p>
        <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-slate-600">
          Add important dates and their costs to see if your forecast can cover them.
        </p>
        <button
          type="button"
          className="mt-6 border-none bg-transparent p-0 text-base font-semibold"
          style={{ color: '#5B2D8E' }}
          onClick={onAddMilestones}
        >
          Add milestones →
        </button>
      </div>
    );
  }

  const allCovered =
    milestones.upcoming.length > 0 && milestones.upcoming.every((e) => e.impact === 'covered');

  const impactBlock = (impact: MilestonesData['upcoming'][number]['impact']) => {
    if (impact === 'covered') {
      return <span className="text-[13px] font-medium" style={{ color: '#059669' }}>✅ Covered</span>;
    }
    if (impact === 'tight') {
      return <span className="text-[13px] font-medium" style={{ color: '#D97706' }}>⚠️ Tight</span>;
    }
    if (impact === 'shortfall') {
      return (
        <button
          type="button"
          className="border-none bg-transparent p-0 text-right text-[13px] font-medium"
          style={{ color: '#DC2626' }}
          onClick={onReviewForecast}
        >
          ❌ Shortfall — tap to review
        </button>
      );
    }
    return null;
  };

  return (
    <div>
      {milestones.current_streak > 0 ? (
        <p className="mb-3 text-[13px] text-slate-500">
          🔥 {milestones.current_streak}-day check-in streak
        </p>
      ) : null}
      {milestones.upcoming.slice(0, 3).map((ev, i) => {
        const badge = milestoneBadgeStyle(ev.days_away);
        return (
          <div key={`${ev.date}-${i}`} className="mb-3 rounded-xl bg-white p-4 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-[15px] font-bold" style={{ color: '#1E293B' }}>
                    {ev.title}
                  </h3>
                  <span
                    className="inline-block shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold"
                    style={{ backgroundColor: badge.bg, color: badge.text }}
                  >
                    {ev.days_away} days
                  </span>
                </div>
                <p className="mt-2 text-[13px] text-slate-500">Est. cost: {formatUsd(ev.cost)}</p>
              </div>
              <div className="flex shrink-0 justify-end sm:mt-0 sm:self-start">{impactBlock(ev.impact)}</div>
            </div>
          </div>
        );
      })}
      {allCovered ? (
        <p className="mt-1 text-[13px]" style={{ color: '#059669' }}>
          ✓ Your forecast covers all upcoming milestones.
        </p>
      ) : null}
    </div>
  );
}

function formatSalaryK(n: number): string {
  const k = Math.round(n / 1000);
  return `$${k}K`;
}

function liftBadgeStyles(lift: number): { bg: string; text: string } {
  if (lift >= 15) return { bg: '#D1FAE5', text: '#059669' };
  if (lift >= 8) return { bg: '#FEF3C7', text: '#D97706' };
  return { bg: '#F1F5F9', text: '#64748B' };
}

const URGENCY_RANK: Record<ActionData['ctas'][number]['urgency'], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

function CareerNextMoveCardContent({
  loading,
  career,
  onUploadResume,
  onComplete,
}: {
  loading: boolean;
  career: CareerData | null;
  onUploadResume: () => void;
  onComplete: (topCta: string) => void;
}) {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [transitionMonths, setTransitionMonths] = useState<3 | 6 | 9>(6);
  const [impactFadeIn, setImpactFadeIn] = useState(true);
  const prevJobIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!career?.jobs?.length) {
      setSelectedJobId(null);
      return;
    }
    setSelectedJobId((prev) => {
      if (prev && career.jobs.some((j) => j.id === prev)) return prev;
      return career.jobs[0].id;
    });
  }, [career]);

  useLayoutEffect(() => {
    if (!selectedJobId) return;
    if (prevJobIdRef.current === null) {
      prevJobIdRef.current = selectedJobId;
      setImpactFadeIn(true);
      return;
    }
    if (prevJobIdRef.current === selectedJobId) return;
    prevJobIdRef.current = selectedJobId;
    setImpactFadeIn(false);
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => setImpactFadeIn(true));
    });
    return () => cancelAnimationFrame(id);
  }, [selectedJobId]);

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-14 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-14 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-14 animate-pulse rounded-xl bg-slate-200" />
      </div>
    );
  }

  const noCareer = !career || career.jobs.length === 0;

  if (noCareer) {
    return (
      <div className="flex flex-col items-center px-2 pt-6 text-center">
        <span className="text-5xl" aria-hidden>
          💼
        </span>
        <p className="mt-5 text-base font-semibold" style={{ color: '#1E293B' }}>
          No job matches found yet.
        </p>
        <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-slate-600">
          Upload your resume to get personalized career moves and their cash impact.
        </p>
        <div
          role="button"
          tabIndex={0}
          className="mt-6 cursor-pointer border-none bg-transparent p-0 text-base font-semibold"
          style={{ color: '#5B2D8E' }}
          onClick={onUploadResume}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onUploadResume();
            }
          }}
        >
          Upload resume →
        </div>
      </div>
    );
  }

  const selectedJob = career.jobs.find((j) => j.id === selectedJobId) ?? career.jobs[0];
  const totalExpectedReturn = selectedJob?.total_expected_return;
  const hasExpectedReturn =
    selectedJob != null &&
    totalExpectedReturn != null &&
    totalExpectedReturn !== 0;

  const timeOptions: Array<{ label: string; months: 3 | 6 | 9 }> = [
    { label: '3 months', months: 3 },
    { label: '6 months', months: 6 },
    { label: '9 months', months: 9 },
  ];

  return (
    <div>
      <p className="mb-3 text-[13px] text-slate-500">
        Current: {formatUsd(career.current_salary)}/yr
      </p>
      {career.jobs.map((job) => {
        const selected = job.id === selectedJobId;
        const lift = Math.round(job.income_lift_pct);
        const badge = liftBadgeStyles(job.income_lift_pct);
        return (
          <div
            key={job.id}
            role="button"
            tabIndex={0}
            className="mb-2 flex w-full cursor-pointer items-stretch gap-3 rounded-[12px] px-[14px] py-3"
            style={{
              backgroundColor: selected ? '#EDE9F6' : '#FFFFFF',
              border: selected ? '1.5px solid #5B2D8E' : '1.5px solid #E2E8F0',
            }}
            onClick={() => setSelectedJobId(job.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setSelectedJobId(job.id);
              }
            }}
          >
            <div className="min-w-0 flex-1 text-left">
              <p className="text-[14px] font-bold" style={{ color: '#1E293B' }}>
                {job.title}
              </p>
              <p className="mt-0.5 text-[12px] text-slate-500">
                {[job.company_type, job.location].filter(Boolean).join(' · ')}
              </p>
            </div>
            <div className="shrink-0 text-right">
              <span
                className="inline-block rounded-md px-2 py-0.5 text-[12px] font-semibold"
                style={{ backgroundColor: badge.bg, color: badge.text }}
              >
                +{lift}%
              </span>
              <p className="mt-1 text-[11px] text-slate-500">
                {formatSalaryK(job.salary_low)}–{formatSalaryK(job.salary_high)}
              </p>
            </div>
          </div>
        );
      })}

      <div
        className="mt-3 rounded-xl bg-white p-4 shadow-sm transition-opacity duration-200"
        style={{ opacity: impactFadeIn ? 1 : 0 }}
      >
        <p className="text-[12px] text-slate-500">If you land this in:</p>
        <div className="mt-3 flex gap-2">
          {timeOptions.map(({ label, months }) => {
            const sel = transitionMonths === months;
            return (
              <div
                key={months}
                role="button"
                tabIndex={0}
                className="flex-1 cursor-pointer rounded-lg py-2 text-center text-[14px] font-medium"
                style={
                  sel
                    ? { backgroundColor: '#5B2D8E', color: '#FFFFFF' }
                    : {
                        backgroundColor: '#FFFFFF',
                        border: '1.5px solid #E2E8F0',
                        color: '#1E293B',
                      }
                }
                onClick={() => setTransitionMonths(months)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setTransitionMonths(months);
                  }
                }}
              >
                {label}
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-[12px] text-slate-500">
          The sooner you land it, the more of this year you capture.
        </p>
        {hasExpectedReturn ? (
          <>
            <p
              className="mt-4 text-[18px] font-bold leading-[1.4]"
              style={{ color: '#059669' }}
            >
              Making this move could put an extra $
              {selectedJob.total_expected_return.toLocaleString()} in your pocket this year.
            </p>
            <p className="mt-1 text-[12px] text-slate-500">
              After taxes · {Math.round(selectedJob.job_probability * 100)}% job probability · wellness
              included
            </p>
            <button
              type="button"
              className="mt-3 cursor-pointer border-none bg-transparent p-0 text-xs font-semibold text-purple-600 hover:underline"
              onClick={() => onComplete('job-recommendations')}
            >
              Full breakdown in Job Recommendations →
            </button>
          </>
        ) : (
          <p className="mt-4 text-[13px] text-slate-500">
            Select a role above to see your expected return.
          </p>
        )}
      </div>
    </div>
  );
}

function ActionTodayCardContent({
  loading,
  action,
}: {
  loading: boolean;
  action: ActionData | null;
}) {
  if (loading) {
    return (
      <div className="space-y-3 px-1">
        <div className="mx-auto h-6 w-32 animate-pulse rounded-full bg-slate-200" />
        <div className="mx-auto h-24 max-w-[280px] animate-pulse rounded-xl bg-slate-200" />
      </div>
    );
  }

  if (!action) {
    return (
      <div className="flex flex-col items-center px-2 pt-8 text-center">
        <p className="text-base font-semibold" style={{ color: '#1E293B' }}>
          Check back tomorrow.
        </p>
        <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-slate-600">
          Your action will be ready once we have more data.
        </p>
      </div>
    );
  }

  const sourceLabel = action.action_source.replace(/-/g, '_').toUpperCase();

  return (
    <div className="flex flex-col items-center px-1 pt-2 text-center">
      <span
        className="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
        style={{ backgroundColor: '#EDE9F6', color: '#5B2D8E' }}
      >
        {sourceLabel}
      </span>
      <p
        className="mx-auto my-6 max-w-[280px] text-center text-[20px] font-bold leading-[1.5]"
        style={{ color: '#1E293B' }}
      >
        {action.action_text}
      </p>
      <p className="text-[13px] text-slate-500">
        Based on what we found across your snapshot today.
      </p>
    </div>
  );
}

function FaithDeckCard({
  loading,
  faith,
  isFavorited,
  savedAnim,
  savedLabelOpacity,
  onFavoriteTap,
}: {
  loading: boolean;
  faith: FaithCardData | null;
  isFavorited: boolean;
  savedAnim: boolean;
  savedLabelOpacity: number;
  onFavoriteTap: () => void;
}) {
  const heartPath =
    'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z';

  return (
    <div
      className="relative box-border flex w-screen shrink-0 flex-col overflow-y-auto px-5 pb-[72px] pt-6"
      style={{
        height: '100dvh',
        background: 'linear-gradient(160deg, #3b1f6e 0%, #5B2D8E 55%, #3b1f6e 100%)',
      }}
    >
      <p
        className="mb-2 text-[11px] font-medium uppercase"
        style={{ color: '#c4b5fd', letterSpacing: '0.2em' }}
      >
        CARD 1 OF {TOTAL_CARDS} · FAITH
      </p>

      <div className="flex min-h-0 flex-1 flex-col justify-center">
        {loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-8">
            <div
              className="h-3 w-[75%] max-w-sm animate-pulse rounded"
              style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            />
            <div
              className="h-3 w-[60%] max-w-xs animate-pulse rounded"
              style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            />
            <div
              className="h-3 w-[45%] max-w-[200px] animate-pulse rounded"
              style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            />
          </div>
        ) : !faith ? (
          <div className="flex flex-col items-center px-2 text-center">
            <span className="text-6xl" aria-hidden>
              🙏
            </span>
            <h3 className="mt-6 text-lg font-semibold" style={{ color: '#f5f3ff' }}>
              Start your day with the Word
            </h3>
            <p className="mt-3 max-w-sm text-[14px] leading-relaxed" style={{ color: '#ddd6fe' }}>
              We&apos;ll have a verse ready for you tomorrow.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center px-2 py-4 text-center">
            <p
              className="mb-5 text-center text-[13px] font-medium uppercase"
              style={{
                color: '#fbbf24',
                letterSpacing: '0.12em',
              }}
            >
              {faith.verse_reference}
            </p>
            <p
              className="mx-auto max-w-[300px] text-center text-[20px] leading-[1.75]"
              style={{ color: '#f5f3ff', fontStyle: 'italic' }}
            >
              {faith.verse_text}
            </p>
            <div
              className="my-5 h-px w-10"
              style={{ backgroundColor: 'rgba(251,191,36,0.4)' }}
              aria-hidden
            />
            <p
              className="mx-auto max-w-[280px] text-center text-[14px] leading-[1.6]"
              style={{ color: '#ddd6fe' }}
            >
              {faith.bridge_sentence}
            </p>
          </div>
        )}
      </div>

      {faith && !loading ? (
        <div
          className="pointer-events-auto absolute flex items-center gap-2"
          style={{ bottom: 80, right: 24 }}
        >
          {savedAnim ? (
            <span
              style={{
                color: '#fbbf24',
                fontSize: 12,
                fontWeight: 500,
                opacity: savedLabelOpacity,
                transition: 'opacity 200ms ease',
              }}
            >
              Saved
            </span>
          ) : null}
          <button
            type="button"
            className="border-none bg-transparent p-0"
            aria-label={isFavorited ? 'Verse saved' : 'Save verse to favorites'}
            onClick={onFavoriteTap}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path
                d={heartPath}
                fill={isFavorited ? '#fbbf24' : 'none'}
                stroke={isFavorited ? '#fbbf24' : 'rgba(255,255,255,0.5)'}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      ) : null}

      <p
        className="mt-10 shrink-0 text-center text-[12px]"
        style={{ color: 'rgba(196,181,253,0.8)' }}
      >
        Swipe to see your snapshot →
      </p>
    </div>
  );
}

function EndActionPanel({
  visible,
  action,
  onComplete,
}: {
  visible: boolean;
  action: ActionData | null;
  onComplete: (tab: string) => void;
}) {
  const sortedCtas = action?.ctas
    ? [...action.ctas].sort((a, b) => URGENCY_RANK[a.urgency] - URGENCY_RANK[b.urgency])
    : [];

  return (
    <div
      className="fixed bottom-0 left-0 right-0"
      style={{
        zIndex: 60,
        background: '#FFFFFF',
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
        boxShadow: '0 -4px 24px rgba(0,0,0,0.10)',
        padding: '24px 20px 40px',
        transform: visible ? 'translateY(0)' : 'translateY(100%)',
        transition: 'transform 400ms cubic-bezier(0.4, 0, 0.2, 1)',
        pointerEvents: visible ? 'auto' : 'none',
      }}
    >
      <div
        className="mx-auto mb-4 rounded-full bg-slate-300"
        style={{ width: 40, height: 4 }}
        aria-hidden
      />
      <h3 className="text-[18px] font-bold" style={{ color: '#1E293B' }}>
        Your next steps
      </h3>
      <p className="mb-4 mt-1 text-[13px] text-slate-500">Based on your snapshot</p>
      {sortedCtas.map((cta) => {
        const high = cta.urgency === 'high';
        const medium = cta.urgency === 'medium';
        return (
          <div
            key={`${cta.tab}-${cta.label}`}
            role="button"
            tabIndex={visible ? 0 : -1}
            className="mb-2 cursor-pointer rounded-xl p-4 text-[15px] font-bold"
            style={
              high
                ? { backgroundColor: '#5B2D8E', color: '#FFFFFF' }
                : medium
                  ? {
                      backgroundColor: '#FFFFFF',
                      border: '1.5px solid #5B2D8E',
                      color: '#5B2D8E',
                    }
                  : {
                      backgroundColor: '#FFFFFF',
                      border: '1.5px solid #E2E8F0',
                      color: '#64748B',
                    }
            }
            onClick={() => onComplete(cta.tab)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onComplete(cta.tab);
              }
            }}
          >
            {cta.label}
          </div>
        );
      })}
      <div
        role="button"
        tabIndex={visible ? 0 : -1}
        className="mt-3 cursor-pointer text-center text-[13px] text-slate-500"
        onClick={() => onComplete('dashboard')}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onComplete('dashboard');
          }
        }}
      >
        Skip — take me to my dashboard
      </div>
    </div>
  );
}

function MingusSnapshot({ onComplete }: MingusSnapshotProps) {
  const { data, loadStates, saveFavorite } = useSnapshotData();
  const [index, setIndex] = useState(0);
  const [endPanelVisible, setEndPanelVisible] = useState(false);
  const [savedAnim, setSavedAnim] = useState(false);
  const [savedLabelOpacity, setSavedLabelOpacity] = useState(0);
  const [isFavorited, setIsFavorited] = useState(false);
  const touchStartXRef = useRef<number | null>(null);

  useEffect(() => {
    setIsFavorited(Boolean(data.faith?.is_favorited));
  }, [data.faith]);

  useEffect(() => {
    if (!savedAnim) return;
    setSavedLabelOpacity(0);
    let rafInner = 0;
    const rafOuter = requestAnimationFrame(() => {
      rafInner = requestAnimationFrame(() => setSavedLabelOpacity(1));
    });
    const tFadeOut = window.setTimeout(() => setSavedLabelOpacity(0), 1200);
    const tClear = window.setTimeout(() => {
      setSavedAnim(false);
      setSavedLabelOpacity(0);
    }, 1500);
    return () => {
      cancelAnimationFrame(rafOuter);
      cancelAnimationFrame(rafInner);
      window.clearTimeout(tFadeOut);
      window.clearTimeout(tClear);
    };
  }, [savedAnim]);

  useEffect(() => {
    if (index !== 7) {
      setEndPanelVisible(false);
      return;
    }
    const t = window.setTimeout(() => setEndPanelVisible(true), 600);
    return () => window.clearTimeout(t);
  }, [index]);

  const onTouchStart = useCallback((e: TouchEvent) => {
    touchStartXRef.current = e.changedTouches[0]?.clientX ?? e.touches[0]?.clientX ?? null;
  }, []);

  const onTouchEnd = useCallback(
    (e: TouchEvent) => {
      const startX = touchStartXRef.current;
      touchStartXRef.current = null;
      if (startX == null) return;
      const endX = e.changedTouches[0]?.clientX;
      if (endX == null) return;
      const delta = endX - startX;
      setIndex((i) => {
        if (delta < -SWIPE_THRESHOLD_PX && i < TOTAL_CARDS - 1) return i + 1;
        if (delta > SWIPE_THRESHOLD_PX && i > 0) return i - 1;
        return i;
      });
    },
    [],
  );

  const handleFaithFavoriteTap = useCallback(() => {
    if (isFavorited || !data.faith) return;
    setIsFavorited(true);
    setSavedAnim(true);
    void saveFavorite(data.faith).then((ok) => {
      if (!ok) setIsFavorited(false);
    });
  }, [isFavorited, data.faith, saveFavorite]);

  const faithLoading = loadStates.faith === 'loading';
  const vibeLoading = loadStates.vibe === 'loading';
  const cashLoading = loadStates.cash === 'loading';
  const cashMissingOrError = loadStates.cash === 'error' || (loadStates.cash === 'ready' && !data.cash);
  const spendingLoading = loadStates.spending === 'loading';
  const rosterLoading = loadStates.roster === 'loading';
  const milestonesLoading = loadStates.milestones === 'loading';
  const careerLoading = loadStates.career === 'loading';
  const actionLoading = loadStates.action === 'loading';

  return (
    <>
      <div
        className="fixed left-0 top-0 z-50 overflow-hidden bg-[#F8FAFC]"
        style={{ width: '100vw', height: '100dvh' }}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        <div
          className="flex flex-row"
          style={{
            width: `calc(100vw * ${TOTAL_CARDS})`,
            transform: `translateX(-${index * 100}vw)`,
            transition: 'transform 350ms cubic-bezier(0.4, 0, 0.2, 1)',
            willChange: 'transform',
          }}
        >
          <FaithDeckCard
            loading={faithLoading}
            faith={data.faith}
            isFavorited={isFavorited}
            savedAnim={savedAnim}
            savedLabelOpacity={savedLabelOpacity}
            onFavoriteTap={handleFaithFavoriteTap}
          />

          <CardFrame index={2} tag="VIBE CHECK" title="Your Vibe Check" showSwipeHint>
            <VibeCardContent
              loading={vibeLoading}
              vibe={data.vibe}
              onStartCheckIn={() => onComplete('vibe-checkups')}
            />
          </CardFrame>

          <CardFrame index={3} tag="MONEY RIGHT NOW" title="Money right now" showSwipeHint>
            <CashCardContent
              loading={cashLoading}
              cash={data.cash}
              loadError={cashMissingOrError}
              onAddIncome={() => onComplete('financial-forecast')}
            />
          </CardFrame>

          <CardFrame
            index={4}
            tag="WHERE YOUR MONEY IS GOING"
            title="Where your money is going"
            showSwipeHint
          >
            <SpendingCardContent
              loading={spendingLoading}
              spending={data.spending}
              onAddExpenses={() => onComplete('financial-forecast')}
            />
          </CardFrame>

          <CardFrame index={5} tag="YOUR ROSTER'S COST" title="Your roster's cost" showSwipeHint>
            <RosterCardContent loading={rosterLoading} roster={data.roster} />
          </CardFrame>

          <CardFrame index={6} tag="MILESTONES COMING UP" title="Milestones coming up" showSwipeHint>
            <MilestonesCardContent
              loading={milestonesLoading}
              milestones={data.milestones}
              onReviewForecast={() => onComplete('financial-forecast')}
              onAddMilestones={() => onComplete('overview')}
            />
          </CardFrame>

          <CardFrame index={7} tag="YOUR NEXT MOVE" title="Your next move" showSwipeHint>
            <CareerNextMoveCardContent
              loading={careerLoading}
              career={data.career}
              onUploadResume={() => onComplete('job-recommendations')}
              onComplete={onComplete}
            />
          </CardFrame>

          <CardFrame
            index={8}
            tag="ONE THING TO DO TODAY"
            title="One thing to do today"
            showSwipeHint
            swipeHintText="Swipe to see your next steps →"
          >
            <ActionTodayCardContent loading={actionLoading} action={data.action} />
          </CardFrame>
        </div>
      </div>

      <EndActionPanel
        visible={endPanelVisible && index === 7}
        action={data.action}
        onComplete={onComplete}
      />

      <div
        className="pointer-events-none fixed bottom-6 left-0 right-0 z-[60] flex justify-center gap-2"
        aria-hidden
      >
        {Array.from({ length: TOTAL_CARDS }, (_, i) => (
          <span
            key={i}
            className="block h-2 w-2 rounded-full"
            style={{
              backgroundColor: i === index ? '#5B2D8E' : '#CBD5E1',
            }}
          />
        ))}
      </div>
    </>
  );
}

export default MingusSnapshot;
