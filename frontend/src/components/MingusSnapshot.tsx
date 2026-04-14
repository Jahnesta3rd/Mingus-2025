import { useCallback, useRef, useState } from 'react';
import type { ReactNode, TouchEvent } from 'react';
import { useSnapshotData } from '../hooks/useSnapshotData';
import type {
  CashNowData,
  MilestonesData,
  RosterData,
  SpendingData,
  VibeCheckData,
} from '../types/snapshot';

const TOTAL_CARDS = 7;
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
  children,
}: {
  index: number;
  tag: string;
  title: string;
  showSwipeHint: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className="box-border w-screen shrink-0 overflow-y-auto bg-[#F8FAFC] px-5 pb-[72px] pt-6"
      style={{ height: '100dvh' }}
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
      {showSwipeHint && (
        <p className="mt-10 text-center text-[12px] text-slate-500">Swipe to continue →</p>
      )}
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

function MingusSnapshot({ onComplete }: MingusSnapshotProps) {
  const { data, loadStates } = useSnapshotData();
  const [index, setIndex] = useState(0);
  const touchStartXRef = useRef<number | null>(null);

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

  const vibeLoading = loadStates.vibe === 'loading';
  const cashLoading = loadStates.cash === 'loading';
  const cashMissingOrError = loadStates.cash === 'error' || (loadStates.cash === 'ready' && !data.cash);
  const spendingLoading = loadStates.spending === 'loading';
  const rosterLoading = loadStates.roster === 'loading';
  const milestonesLoading = loadStates.milestones === 'loading';

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
          <CardFrame index={1} tag="VIBE CHECK" title="Your Vibe Check" showSwipeHint>
            <VibeCardContent
              loading={vibeLoading}
              vibe={data.vibe}
              onStartCheckIn={() => onComplete('vibe-checkups')}
            />
          </CardFrame>

          <CardFrame index={2} tag="MONEY RIGHT NOW" title="Money right now" showSwipeHint>
            <CashCardContent
              loading={cashLoading}
              cash={data.cash}
              loadError={cashMissingOrError}
              onAddIncome={() => onComplete('financial-forecast')}
            />
          </CardFrame>

          <CardFrame index={3} tag="SPENDING" title="Where your money is going" showSwipeHint>
            <SpendingCardContent
              loading={spendingLoading}
              spending={data.spending}
              onAddExpenses={() => onComplete('financial-forecast')}
            />
          </CardFrame>

          <CardFrame index={4} tag="ROSTER" title="Your roster's cost" showSwipeHint>
            <RosterCardContent loading={rosterLoading} roster={data.roster} />
          </CardFrame>

          <CardFrame index={5} tag="MILESTONES" title="Milestones coming up" showSwipeHint>
            <MilestonesCardContent
              loading={milestonesLoading}
              milestones={data.milestones}
              onReviewForecast={() => onComplete('financial-forecast')}
              onAddMilestones={() => onComplete('overview')}
            />
          </CardFrame>

          {[6, 7].map((n) => (
            <div
              key={n}
              className="box-border flex w-screen shrink-0 items-center justify-center overflow-y-auto bg-[#F8FAFC] px-5 pb-[72px] pt-6 text-center text-slate-500"
              style={{ height: '100dvh' }}
            >
              <span className="text-base">Card {n} — Coming Soon</span>
            </div>
          ))}
        </div>
      </div>

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
