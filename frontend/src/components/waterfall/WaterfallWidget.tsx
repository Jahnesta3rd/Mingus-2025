import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  deriveUserTier,
  fetchWaterfallContext,
  FluencyCue,
  type WaterfallContext,
} from '../fluency';
import './waterfallDesignTokens.css';
import {
  bucketAmount,
  computeOptimizedAllocations,
  DEFAULT_ALLOCATIONS,
  fiveYearCompoundedSurplus,
  formatUsd,
  isDownPaymentNotStarted,
  isVehicleSellTimeline,
  surplusPercent,
  type AllocationPercents,
} from './waterfallUtils';

const MIN_ANNOTATION_COMPLETENESS = 0.2;
const MIN_OPTIMIZED_COMPLETENESS = 0.3;

type BucketKey = keyof AllocationPercents;

const BUCKET_META: Record<
  BucketKey,
  { label: string; fillClass: string; sliderAccent: string }
> = {
  fixed: {
    label: 'Fixed Bills',
    fillClass: 'bg-amber-400',
    sliderAccent: 'accent-amber-500',
  },
  discretionary: {
    label: 'Discretionary',
    fillClass: 'bg-rose-400',
    sliderAccent: 'accent-rose-500',
  },
  debt: {
    label: 'Debt',
    fillClass: 'bg-violet-500',
    sliderAccent: 'accent-violet-600',
  },
  savings: {
    label: 'Savings',
    fillClass: 'bg-emerald-500',
    sliderAccent: 'accent-emerald-600',
  },
};

function PressureDot({ colorClass }: { colorClass: string }) {
  return (
    <span
      className={`mr-1 inline-block h-2 w-2 shrink-0 rounded-full ${colorClass}`}
      aria-hidden
    />
  );
}

function BucketAnnotations({
  bucket,
  ctx,
}: {
  bucket: BucketKey;
  ctx: WaterfallContext;
}) {
  const lines: { text: string; dot: string; textColor: string }[] = [];

  if (bucket === 'fixed') {
    if (ctx.fixed_bills_pressure === 'elevated') {
      lines.push({
        text: 'Unexpected housing cost this week',
        dot: 'bg-amber-500',
        textColor: 'text-amber-600',
      });
    }
    if (ctx.lease_renewal_imminent) {
      lines.push({
        text: 'Renewal window open',
        dot: 'bg-amber-500',
        textColor: 'text-amber-600',
      });
    }
  }

  if (bucket === 'discretionary') {
    if (ctx.discretionary_risk === 'high') {
      lines.push({
        text: 'Stress pattern detected this week',
        dot: 'bg-red-500',
        textColor: 'text-red-600',
      });
    } else if (ctx.discretionary_risk === 'watch') {
      lines.push({
        text: 'Possible stress spending this week',
        dot: 'bg-amber-500',
        textColor: 'text-amber-600',
      });
    }
  }

  if (bucket === 'debt' && isVehicleSellTimeline(ctx.vehicle_decision)) {
    lines.push({
      text: 'Vehicle sell timeline active',
      dot: 'bg-purple-500',
      textColor: 'text-purple-600',
    });
  }

  if (bucket === 'savings') {
    if (isDownPaymentNotStarted(ctx.down_payment_status)) {
      lines.push({
        text: 'Down payment savings not started',
        dot: 'bg-gray-400',
        textColor: 'text-gray-600',
      });
    } else if (ctx.down_payment_status === 'on_track') {
      lines.push({
        text: 'Down payment savings on track',
        dot: 'bg-green-500',
        textColor: 'text-green-600',
      });
    }
  }

  if (lines.length === 0) return null;

  return (
    <div className="mt-1 space-y-0.5">
      {lines.map((line) => (
        <p
          key={line.text}
          className={`flex items-center gap-1 text-xs ${line.textColor}`}
        >
          <PressureDot colorClass={line.dot} />
          {line.text}
        </p>
      ))}
    </div>
  );
}

type BucketRowProps = {
  bucketKey: BucketKey;
  pct: number;
  displayPct: number;
  monthlyIncome: number;
  onPctChange?: (value: number) => void;
  showSlider: boolean;
  delta?: number | null;
  ctx: WaterfallContext | null;
  showAnnotations: boolean;
};

function BucketRow({
  bucketKey,
  pct,
  displayPct,
  monthlyIncome,
  onPctChange,
  showSlider,
  delta,
  ctx,
  showAnnotations,
}: BucketRowProps) {
  const meta = BUCKET_META[bucketKey];
  const amount = bucketAmount(monthlyIncome, displayPct);

  return (
    <section className="space-y-2 rounded-xl border bg-white p-4 shadow-sm" style={{ borderColor: 'var(--line)' }}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>
            {meta.label}
          </h3>
          {showAnnotations && ctx ? (
            <BucketAnnotations bucket={bucketKey} ctx={ctx} />
          ) : null}
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold tabular-nums" style={{ color: 'var(--ink)' }}>
            {displayPct}% · {formatUsd(amount)}
          </p>
          {delta != null && delta !== 0 ? (
            <p className="text-xs font-medium text-[var(--mingus-purple)]">
              {delta > 0 ? '+' : ''}
              {delta}% vs. now
            </p>
          ) : null}
        </div>
      </div>

      <div
        className="h-3 w-full overflow-hidden rounded-full"
        style={{ background: 'var(--line)' }}
        aria-hidden
      >
        <div
          className={`h-full rounded-full transition-all duration-300 ${meta.fillClass}`}
          style={{ width: `${Math.min(100, Math.max(0, displayPct))}%` }}
        />
      </div>

      {showSlider && onPctChange ? (
        <label className="block">
          <span className="sr-only">{meta.label} allocation percent</span>
          <input
            type="range"
            min={0}
            max={60}
            step={1}
            value={pct}
            onChange={(e) => onPctChange(Number(e.target.value))}
            className={`h-2 w-full cursor-pointer ${meta.sliderAccent}`}
          />
        </label>
      ) : null}
    </section>
  );
}

export const WaterfallWidget: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userTier = deriveUserTier(user);

  const [monthlyIncome, setMonthlyIncome] = useState(6000);
  const [allocations, setAllocations] = useState<AllocationPercents>(DEFAULT_ALLOCATIONS);
  const [waterfallCtx, setWaterfallCtx] = useState<WaterfallContext | null>(null);
  const [showOptimized, setShowOptimized] = useState(false);

  useEffect(() => {
    void fetchWaterfallContext()
      .then(setWaterfallCtx)
      .catch(() => setWaterfallCtx(null));
  }, []);

  const optimizedAllocations = useMemo(
    () => computeOptimizedAllocations(allocations, waterfallCtx),
    [allocations, waterfallCtx]
  );

  const activeAllocations = showOptimized ? optimizedAllocations : allocations;
  const surplusPct = surplusPercent(activeAllocations);
  const surplusAmount = bucketAmount(monthlyIncome, surplusPct);
  const fiveYearFv = fiveYearCompoundedSurplus(surplusAmount);

  const showAnnotations =
    waterfallCtx != null && waterfallCtx.data_completeness >= MIN_ANNOTATION_COMPLETENESS;

  const showWhatIfToggle =
    waterfallCtx != null && waterfallCtx.data_completeness >= MIN_OPTIMIZED_COMPLETENESS;

  const setBucket = (key: BucketKey, value: number) => {
    setAllocations((prev) => ({ ...prev, [key]: value }));
  };

  const bucketOrder: BucketKey[] = ['fixed', 'discretionary', 'debt', 'savings'];

  return (
    <div className="waterfall-root space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold sm:text-3xl">Money waterfall</h1>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--ink-mid)' }}>
          Slide your monthly income through four buckets. What remains is your surplus — the pool
          that funds goals, cushions shocks, and compounds over time.
        </p>
      </header>

      <section
        className="rounded-xl border bg-white p-5 shadow-sm"
        style={{ borderColor: 'var(--line)' }}
      >
        <label className="block space-y-3">
          <div className="flex items-baseline justify-between gap-3">
            <span className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>
              Monthly income
            </span>
            <span className="text-lg font-bold tabular-nums" style={{ color: 'var(--mingus-purple)' }}>
              {formatUsd(monthlyIncome)}
            </span>
          </div>
          <input
            type="range"
            min={2000}
            max={20000}
            step={100}
            value={monthlyIncome}
            onChange={(e) => setMonthlyIncome(Number(e.target.value))}
            className="h-2 w-full cursor-pointer accent-[#5b2d8e]"
          />
          <div className="flex justify-between text-xs" style={{ color: 'var(--ink-mid)' }}>
            <span>$2,000</span>
            <span>$20,000</span>
          </div>
        </label>
      </section>

      {showWhatIfToggle ? (
        <div className="flex flex-wrap items-center gap-3">
          {!showOptimized ? (
            <button
              type="button"
              onClick={() => setShowOptimized(true)}
              className="rounded-lg px-4 py-2 text-sm font-semibold text-white transition hover:opacity-95"
              style={{ background: 'var(--mingus-purple)' }}
            >
              See optimized split
            </button>
          ) : (
            <>
              <p className="text-sm font-medium" style={{ color: 'var(--ink-mid)' }}>
                Based on your check-in pattern
              </p>
              <button
                type="button"
                onClick={() => setShowOptimized(false)}
                className="rounded-lg border px-4 py-2 text-sm font-semibold transition hover:bg-[var(--soft-purple)]"
                style={{ borderColor: 'var(--line)', color: 'var(--mingus-purple)' }}
              >
                Back to my actual split
              </button>
            </>
          )}
        </div>
      ) : null}

      <div className="space-y-4">
        {bucketOrder.map((key) => (
          <BucketRow
            key={key}
            bucketKey={key}
            pct={allocations[key]}
            displayPct={activeAllocations[key]}
            monthlyIncome={monthlyIncome}
            onPctChange={showOptimized ? undefined : (v) => setBucket(key, v)}
            showSlider={!showOptimized}
            delta={
              showOptimized ? activeAllocations[key] - allocations[key] : null
            }
            ctx={waterfallCtx}
            showAnnotations={showAnnotations && !showOptimized}
          />
        ))}
      </div>

      <section
        className="rounded-xl border-2 p-5"
        style={{
          borderColor: 'var(--lavender-300)',
          background: 'var(--soft-purple)',
        }}
      >
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--mingus-purple-deep)' }}>
            Surplus pool
          </h2>
          <p className="text-xl font-bold tabular-nums" style={{ color: 'var(--mingus-purple)' }}>
            {formatUsd(surplusAmount)}
            <span className="ml-2 text-sm font-medium" style={{ color: 'var(--ink-mid)' }}>
              ({surplusPct}% of income)
            </span>
          </p>
        </div>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--ink-mid)' }}>
          Income not allocated to the four buckets flows here — your flexible margin for goals,
          emergencies, and growth.
        </p>
      </section>

      <section
        className="rounded-xl border bg-white p-5 shadow-sm"
        style={{ borderColor: 'var(--line)' }}
      >
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--ink-mid)' }}>
          5-year compounding callout
        </h3>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--ink)' }}>
          If you directed this month&apos;s surplus ({formatUsd(surplusAmount)}/mo) into savings at
          roughly 7% annual growth, you&apos;d have about{' '}
          <span className="font-semibold text-[var(--mingus-purple)]">{formatUsd(fiveYearFv)}</span>{' '}
          in five years — before adding future raises or tighter spending.
        </p>
      </section>

      {waterfallCtx ? (
        <FluencyCue
          context={waterfallCtx}
          domain="mood"
          userTier={userTier}
          onActionRoute={(route) => navigate(route)}
        />
      ) : null}
    </div>
  );
};

export default WaterfallWidget;
