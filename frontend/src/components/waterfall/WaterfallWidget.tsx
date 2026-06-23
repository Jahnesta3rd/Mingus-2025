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
import { WaterfallSvg } from './WaterfallSvg';
import {
  bucketAmount,
  computeOptimizedAllocations,
  DEFAULT_ALLOCATIONS,
  formatUsd,
  isDownPaymentNotStarted,
  isVehicleSellTimeline,
  surplusPercent,
  type AllocationPercents,
} from './waterfallUtils';

function hexToRgb(hex: string): string {
  const n = hex.replace('#', '');
  const r = parseInt(n.slice(0, 2), 16);
  const g = parseInt(n.slice(2, 4), 16);
  const b = parseInt(n.slice(4, 6), 16);
  return `${r}, ${g}, ${b}`;
}

function poolFiveYearLumpSum(monthlyPool: number): number {
  if (monthlyPool <= 0) return 0;
  return Math.round(monthlyPool * 12 * ((Math.pow(1.07, 5) - 1) / 0.07));
}

function poolDescription(poolPct: number, poolAmt: number): string {
  if (poolPct <= 0) {
    return 'Nothing left — your outflows exceed your income at these settings. Reduce discretionary or fixed spending to create any surplus.';
  }
  if (poolPct < 10) {
    return `${poolPct}% of income left — tight, but it's a start. Even ${formatUsd(poolAmt)} invested monthly is better than zero.`;
  }
  if (poolPct < 20) {
    return `${poolPct}% of income flowing to you — decent foundation. This is the money that can compound into savings, investments, and future security.`;
  }
  const fiveYearAmt = poolFiveYearLumpSum(poolAmt);
  return `${poolPct}% of income reaching your pool — strong position. At 7% average annual growth, ${formatUsd(poolAmt)}/month invested becomes ${formatUsd(fiveYearAmt)} in 5 years.`;
}

const POOL_USE_PILLS = [
  {
    label: '📈 Index funds',
    bg: 'rgba(91,45,142,0.08)',
    color: '#5B2D8E',
    border: 'rgba(91,45,142,0.2)',
  },
  {
    label: '🛡️ Safety net',
    bg: 'rgba(16,185,129,0.08)',
    color: '#10B981',
    border: 'rgba(16,185,129,0.2)',
  },
  {
    label: '🏠 Future goals',
    bg: 'rgba(59,130,246,0.08)',
    color: '#3B82F6',
    border: 'rgba(59,130,246,0.2)',
  },
] as const;

const MIN_ANNOTATION_COMPLETENESS = 0.2;
const MIN_OPTIMIZED_COMPLETENESS = 0.3;

const HOUSING_OVERLAY_INCOME_KEY = 'mingus_housingSecondJobIncome';
const HOUSING_OVERLAY_LABEL_KEY = 'mingus_housingSecondJobLabel';
const DEBT_OVERLAY_INCOME_KEY = 'mingus_debtSecondJobIncome';
const DEBT_OVERLAY_LABEL_KEY = 'mingus_debtSecondJobLabel';

function readStoredOverlay(
  incomeKey: string,
  labelKey: string,
): { income: number; label: string | null } {
  const raw = sessionStorage.getItem(incomeKey);
  const income = raw != null ? parseFloat(raw) : NaN;
  if (isNaN(income) || income <= 0) {
    return { income: 0, label: null };
  }
  return { income, label: sessionStorage.getItem(labelKey) };
}

export type WaterfallWidgetProps = {
  housingSecondJobIncome?: number | null;
  housingSecondJobLabel?: string | null;
  debtSecondJobIncome?: number | null;
  debtSecondJobLabel?: string | null;
};

function IncomeOverlayBadge({
  label,
  amount,
  color,
  borderColor,
  bgColor,
}: {
  label: string;
  amount: number;
  color: string;
  borderColor: string;
  bgColor: string;
}) {
  return (
    <div
      className="rounded-lg border-2 border-dashed px-3 py-2 text-sm"
      style={{ borderColor, background: bgColor, color }}
    >
      <span className="font-medium">{label}</span>
      <span className="ml-1 tabular-nums">(+{formatUsd(amount)}/mo)</span>
    </div>
  );
}

type BucketKey = keyof AllocationPercents;

const BUCKET_META: Record<
  BucketKey,
  { label: string; color: string }
> = {
  fixed: { label: 'Fixed Bills', color: '#3B82F6' },
  discretionary: { label: 'Discretionary', color: '#F97316' },
  debt: { label: 'Debt', color: '#EF4444' },
  savings: { label: 'Savings', color: '#10B981' },
};

function PressureDot({ color }: { color: string }) {
  return (
    <span
      className="mr-1 inline-block h-2 w-2 shrink-0 rounded-full"
      style={{ background: color }}
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
  const lines: { text: string; dot: string }[] = [];

  if (bucket === 'fixed') {
    if (ctx.fixed_bills_pressure === 'elevated') {
      lines.push({ text: 'Unexpected housing cost this week', dot: '#F59E0B' });
    }
    if (ctx.lease_renewal_imminent) {
      lines.push({ text: 'Renewal window open', dot: '#F59E0B' });
    }
  }

  if (bucket === 'discretionary') {
    if (ctx.discretionary_risk === 'high') {
      lines.push({ text: 'Stress pattern detected this week', dot: '#EF4444' });
    } else if (ctx.discretionary_risk === 'watch') {
      lines.push({ text: 'Possible stress spending this week', dot: '#F59E0B' });
    }
  }

  if (bucket === 'debt' && isVehicleSellTimeline(ctx.vehicle_decision)) {
    lines.push({ text: 'Vehicle sell timeline active', dot: '#5B2D8E' });
  }

  if (bucket === 'savings') {
    if (isDownPaymentNotStarted(ctx.down_payment_status)) {
      lines.push({ text: 'Down payment savings not started', dot: '#9CA3AF' });
    } else if (ctx.down_payment_status === 'on_track') {
      lines.push({ text: 'Down payment savings on track', dot: '#10B981' });
    }
  }

  if (lines.length === 0) return null;

  return (
    <div className="mt-1 space-y-0.5">
      {lines.map((line) => (
        <p
          key={line.text}
          className="flex items-center gap-1 text-[11px]"
          style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
        >
          <PressureDot color={line.dot} />
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
    <section className="space-y-2 py-3 first:pt-0 last:pb-0">
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
          <p
            className="text-sm font-semibold tabular-nums"
            style={{ color: meta.color, fontFamily: "'DM Mono', 'Courier New', monospace" }}
          >
            {displayPct}%
          </p>
          <p className="text-xs tabular-nums text-[#9CA3AF]">{formatUsd(amount)}</p>
          {delta != null && delta !== 0 ? (
            <p className="text-xs font-medium text-[var(--mingus-purple)]">
              {delta > 0 ? '+' : ''}
              {delta}% vs. now
            </p>
          ) : null}
        </div>
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
            className="waterfall-bucket-slider"
            style={
              {
                '--bucket-color': meta.color,
                background: `rgba(${hexToRgb(meta.color)}, 0.15)`,
              } as React.CSSProperties
            }
          />
        </label>
      ) : null}
    </section>
  );
}

export const WaterfallWidget: React.FC<WaterfallWidgetProps> = ({
  housingSecondJobIncome: housingIncomeProp,
  housingSecondJobLabel: housingLabelProp,
  debtSecondJobIncome: debtIncomeProp,
  debtSecondJobLabel: debtLabelProp,
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userTier = deriveUserTier(user);

  const [baseMonthlyIncome, setBaseMonthlyIncome] = useState(6000);
  const [housingOverlayIncome, setHousingOverlayIncome] = useState(0);
  const [housingOverlayLabel, setHousingOverlayLabel] = useState<string | null>(null);
  const [debtOverlayIncome, setDebtOverlayIncome] = useState(0);
  const [debtOverlayLabel, setDebtOverlayLabel] = useState<string | null>(null);
  const [allocations, setAllocations] = useState<AllocationPercents>(DEFAULT_ALLOCATIONS);
  const [waterfallCtx, setWaterfallCtx] = useState<WaterfallContext | null>(null);
  const [showOptimized, setShowOptimized] = useState(false);

  useEffect(() => {
    void fetchWaterfallContext()
      .then(setWaterfallCtx)
      .catch(() => setWaterfallCtx(null));

    const params = new URLSearchParams(window.location.search);
    const urlSecondJobIncome = params.get('secondJobIncome');
    const urlHousingIncome =
      urlSecondJobIncome != null ? parseFloat(urlSecondJobIncome) : NaN;

    const storedHousing = readStoredOverlay(HOUSING_OVERLAY_INCOME_KEY, HOUSING_OVERLAY_LABEL_KEY);
    const storedDebt = readStoredOverlay(DEBT_OVERLAY_INCOME_KEY, DEBT_OVERLAY_LABEL_KEY);

    const housingIncome =
      housingIncomeProp ??
      (!isNaN(urlHousingIncome) && urlHousingIncome > 0 ? urlHousingIncome : storedHousing.income);
    const housingLabel =
      housingLabelProp ??
      (housingIncome > 0
        ? storedHousing.label || 'Housing plan income'
        : null);

    const debtIncome = debtIncomeProp ?? storedDebt.income;
    const debtLabel =
      debtLabelProp ?? (debtIncome > 0 ? storedDebt.label || 'Debt payoff income' : null);

    if (housingIncome > 0) {
      setHousingOverlayIncome(housingIncome);
      setHousingOverlayLabel(housingLabel);
    }
    if (debtIncome > 0) {
      setDebtOverlayIncome(debtIncome);
      setDebtOverlayLabel(debtLabel);
    }
  }, [housingIncomeProp, housingLabelProp, debtIncomeProp, debtLabelProp]);

  const monthlyIncome = baseMonthlyIncome + housingOverlayIncome + debtOverlayIncome;
  const combinedOverlayIncome = housingOverlayIncome + debtOverlayIncome;

  const optimizedAllocations = useMemo(
    () => computeOptimizedAllocations(allocations, waterfallCtx),
    [allocations, waterfallCtx]
  );

  const activeAllocations = showOptimized ? optimizedAllocations : allocations;
  const surplusPct = surplusPercent(activeAllocations);
  const surplusAmount = bucketAmount(monthlyIncome, surplusPct);

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
      <header className="space-y-3">
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          className="waterfall-back-link"
        >
          ← Financial Forecast
        </button>
        <h1 className="text-[28px] font-semibold leading-tight" style={{ color: 'var(--ink)' }}>
          Your Money Waterfall
        </h1>
        <p className="text-[13px] leading-relaxed" style={{ color: 'var(--ink-mid)' }}>
          Income enters at the top. Each bucket captures its share. What flows down is yours.
        </p>
      </header>

      <section className="rounded-xl border border-[#E2E8F0] bg-white p-5 shadow-sm">
        <label className="block space-y-3">
          <div className="flex items-baseline justify-between gap-3">
            <span className="text-sm font-semibold" style={{ color: 'var(--ink-mid)' }}>
              Monthly income
            </span>
            <span
              className="text-[30px] font-semibold tabular-nums leading-none"
              style={{ color: 'var(--mingus-purple)', fontFamily: 'Fraunces, Georgia, serif' }}
            >
              {formatUsd(monthlyIncome)}
            </span>
          </div>
          {(housingOverlayIncome > 0 || debtOverlayIncome > 0) && (
            <p className="text-xs tabular-nums" style={{ color: 'var(--ink-mid)' }}>
              Base {formatUsd(baseMonthlyIncome)}
              {combinedOverlayIncome > 0 ? ` + overlays ${formatUsd(combinedOverlayIncome)}` : ''}
            </p>
          )}
          <input
            type="range"
            min={2000}
            max={20000}
            step={100}
            value={baseMonthlyIncome}
            onChange={(e) => setBaseMonthlyIncome(Number(e.target.value))}
            className="waterfall-income-slider"
          />
          <div className="flex justify-between text-xs" style={{ color: 'var(--ink-mid)' }}>
            <span>$2,000</span>
            <span>$20,000</span>
          </div>
          <div className="space-y-2 pt-1">
            {debtOverlayIncome > 0 ? (
              <IncomeOverlayBadge
                label={debtOverlayLabel ?? 'Debt payoff income'}
                amount={debtOverlayIncome}
                color="#1D4ED8"
                borderColor="#93C5FD"
                bgColor="rgba(59,130,246,0.08)"
              />
            ) : null}
            {housingOverlayIncome > 0 ? (
              <IncomeOverlayBadge
                label={housingOverlayLabel ?? 'Housing plan income'}
                amount={housingOverlayIncome}
                color="#B45309"
                borderColor="#FCD34D"
                bgColor="rgba(245,158,11,0.08)"
              />
            ) : null}
            {debtOverlayIncome > 0 && housingOverlayIncome > 0 ? (
              <p className="text-xs font-semibold tabular-nums text-[#5B2D8E]">
                Combined additional income: {formatUsd(combinedOverlayIncome)}/mo
              </p>
            ) : null}
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
                className="rounded-lg border border-[#E2E8F0] px-4 py-2 text-sm font-semibold transition hover:bg-[rgba(91,45,142,0.05)]"
                style={{ color: 'var(--mingus-purple)' }}
              >
                Back to my actual split
              </button>
            </>
          )}
        </div>
      ) : null}

      <section className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <WaterfallSvg
          monthlyIncome={monthlyIncome}
          allocations={activeAllocations}
          poolPct={surplusPct}
        />
      </section>

      <section
        className="flex gap-4"
        style={{
          background: 'rgba(91,45,142,0.05)',
          border: '1px solid rgba(91,45,142,0.2)',
          borderRadius: 12,
          padding: '20px 22px',
        }}
      >
        <span className="shrink-0 text-[32px] leading-none" aria-hidden>
          💧
        </span>
        <div className="min-w-0 flex-1">
          <h2
            className="font-semibold"
            style={{
              fontFamily: 'Fraunces, Georgia, serif',
              fontSize: 15,
              color: 'var(--ink)',
            }}
          >
            What flows to you
          </h2>
          <p
            className="mt-1 tabular-nums"
            style={{
              fontFamily: 'Fraunces, Georgia, serif',
              fontSize: 28,
              color: 'var(--mingus-purple)',
            }}
          >
            {formatUsd(surplusAmount)} / month
          </p>
          <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--ink-mid)' }}>
            {poolDescription(surplusPct, surplusAmount)}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {POOL_USE_PILLS.map((pill) => (
              <span
                key={pill.label}
                className="rounded-full px-3 py-1 text-xs font-semibold"
                style={{
                  background: pill.bg,
                  color: pill.color,
                  border: `1px solid ${pill.border}`,
                }}
              >
                {pill.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-[#E2E8F0] bg-white p-5">
        <h2 className="mb-1 text-sm font-semibold" style={{ color: 'var(--ink)' }}>
          Adjust allocations
        </h2>
        <p className="mb-4 text-xs" style={{ color: 'var(--ink-mid)' }}>
          Drag each slider to see how your waterfall reshapes in real time.
        </p>
        <div className="divide-y divide-[#E2E8F0]">
          {bucketOrder.map((key) => (
            <BucketRow
              key={key}
              bucketKey={key}
              pct={allocations[key]}
              displayPct={activeAllocations[key]}
              monthlyIncome={monthlyIncome}
              onPctChange={showOptimized ? undefined : (v) => setBucket(key, v)}
              showSlider={!showOptimized}
              delta={showOptimized ? activeAllocations[key] - allocations[key] : null}
              ctx={waterfallCtx}
              showAnnotations={showAnnotations && !showOptimized}
            />
          ))}
        </div>
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
