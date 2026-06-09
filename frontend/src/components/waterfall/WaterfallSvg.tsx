import React, { useId, useMemo } from 'react';
import { bucketAmount, formatUsd, type AllocationPercents } from './waterfallUtils';

type BucketKey = keyof AllocationPercents;

const SVG_W = 640;
const CENTER_X = SVG_W / 2;
const MARGIN_TOP = 16;
const MARGIN_BOTTOM = 20;
const INCOME_BAR_H = 40;
const INCOME_BAR_W = 260;
const PIPE_W = 8;
const TAP_LEN = 68;
const BUCKET_MIN_W = 52;
const BUCKET_MAX_W = 148;
const BUCKET_MIN_H = 72;
const BUCKET_MAX_H = 96;
const INCOME_PIPE_H = 60;
const GAP_AFTER_INCOME = 20;
const GAP_BETWEEN = 32;
const POOL_H = 52;
const POOL_W = 220;

const BUCKET_COLORS: Record<BucketKey, string> = {
  fixed: '#3B82F6',
  discretionary: '#F97316',
  debt: '#EF4444',
  savings: '#10B981',
};

const BUCKET_LABELS: Record<BucketKey, string> = {
  fixed: 'Fixed Bills',
  discretionary: 'Discretionary',
  debt: 'Debt',
  savings: 'Savings',
};

const BUCKET_ORDER: BucketKey[] = ['fixed', 'discretionary', 'debt', 'savings'];

function bucketWidth(pct: number): number {
  const t = Math.min(60, Math.max(0, pct)) / 60;
  return BUCKET_MIN_W + t * (BUCKET_MAX_W - BUCKET_MIN_W);
}

function bucketHeight(pct: number): number {
  const t = Math.min(60, Math.max(0, pct)) / 60;
  return BUCKET_MIN_H + t * (BUCKET_MAX_H - BUCKET_MIN_H);
}

function fillAlpha(pct: number): number {
  return 0.1 + pct * 0.004;
}

type BucketLayout = {
  key: BucketKey;
  side: 'left' | 'right';
  pct: number;
  amount: number;
  x: number;
  y: number;
  width: number;
  height: number;
  fillAlpha: number;
  color: string;
  label: string;
  tapY: number;
};

type WaterfallSvgProps = {
  monthlyIncome: number;
  allocations: AllocationPercents;
  poolPct: number;
};

export const WaterfallSvg: React.FC<WaterfallSvgProps> = ({
  monthlyIncome,
  allocations,
  poolPct,
}) => {
  const glowId = useId().replace(/:/g, '');
  const poolGlow = poolPct >= 15;

  const layout = useMemo(() => {
    const incomeBarY = MARGIN_TOP;
    const pipeStartY = incomeBarY + INCOME_BAR_H;
    let cursorY = pipeStartY + INCOME_PIPE_H + GAP_AFTER_INCOME;

    const buckets: BucketLayout[] = BUCKET_ORDER.map((key, index) => {
      const pct = allocations[key];
      const w = bucketWidth(pct);
      const h = bucketHeight(pct);
      const side: 'left' | 'right' = index % 2 === 0 ? 'left' : 'right';
      const bucketY = cursorY;
      const tapY = bucketY + 20;
      const x =
        side === 'left' ? CENTER_X - TAP_LEN - w : CENTER_X + TAP_LEN;

      const bucket: BucketLayout = {
        key,
        side,
        pct,
        amount: bucketAmount(monthlyIncome, pct),
        x,
        y: bucketY,
        width: w,
        height: h,
        fillAlpha: fillAlpha(pct),
        color: BUCKET_COLORS[key],
        label: BUCKET_LABELS[key],
        tapY,
      };

      cursorY += h + GAP_BETWEEN;
      return bucket;
    });

    const poolY = cursorY + 8;
    const totalHeight = poolY + POOL_H + MARGIN_BOTTOM;

    const pathPoints: { x: number; y: number }[] = [
      { x: CENTER_X, y: pipeStartY },
    ];
    for (const b of buckets) {
      pathPoints.push({ x: CENTER_X, y: b.tapY });
    }
    pathPoints.push({ x: CENTER_X, y: poolY });

    const centerPath = pathPoints
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
      .join(' ');

    return {
      incomeBarY,
      pipeStartY,
      buckets,
      poolY,
      poolAmount: bucketAmount(monthlyIncome, poolPct),
      totalHeight,
      centerPath,
    };
  }, [allocations, monthlyIncome, poolPct]);

  const incomeBarX = CENTER_X - INCOME_BAR_W / 2;
  const poolX = CENTER_X - POOL_W / 2;

  return (
    <svg
      viewBox={`0 0 ${SVG_W} ${layout.totalHeight}`}
      className="w-full mx-auto"
      role="img"
      aria-label="Income waterfall visualization"
    >
      <defs>
        <linearGradient id={`income-grad-${glowId}`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#5B2D8E" stopOpacity="0.85" />
          <stop offset="50%" stopColor="#7C3AED" stopOpacity="1" />
          <stop offset="100%" stopColor="#5B2D8E" stopOpacity="0.85" />
        </linearGradient>
        {poolGlow ? (
          <filter id={`pool-glow-${glowId}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        ) : null}
      </defs>

      {/* Income reservoir */}
      <rect
        x={incomeBarX}
        y={layout.incomeBarY}
        width={INCOME_BAR_W}
        height={INCOME_BAR_H}
        rx={8}
        fill={`url(#income-grad-${glowId})`}
      />
      <text
        x={CENTER_X}
        y={layout.incomeBarY + 16}
        textAnchor="middle"
        fill="rgba(91,45,142,0.7)"
        fontSize={10}
        fontFamily="Manrope, system-ui, sans-serif"
      >
        Monthly Income
      </text>
      <text
        x={CENTER_X}
        y={layout.incomeBarY + 32}
        textAnchor="middle"
        fill="#1A1815"
        fontSize={14}
        fontWeight={600}
        fontFamily="Fraunces, Georgia, serif"
      >
        {formatUsd(monthlyIncome)}
      </text>

      {/* Center pipe */}
      <path
        d={layout.centerPath}
        fill="none"
        stroke="#E2E8F0"
        strokeWidth={PIPE_W + 4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d={layout.centerPath}
        fill="none"
        stroke="rgba(91,45,142,0.25)"
        strokeWidth={PIPE_W}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Flow dots */}
      {[0, 0.5, 1, 1.5].map((delay) => (
        <circle key={delay} r={3.5} fill="#7C3AED" opacity={0.75}>
          <animateMotion
            dur="2.8s"
            begin={`${delay}s`}
            repeatCount="indefinite"
            path={layout.centerPath}
          />
        </circle>
      ))}

      {/* Buckets and taps */}
      {layout.buckets.map((b, index) => {
        const bucketY = b.y;
        const fillH = b.height * Math.min(1, b.pct / 60);
        const fillY = bucketY + b.height - fillH;
        const tapEndX = b.side === 'left' ? b.x + b.width : b.x;

        return (
          <g key={b.key}>
            {/* Horizontal tap */}
            <line
              x1={CENTER_X}
              y1={b.tapY}
              x2={tapEndX}
              y2={b.tapY}
              stroke={b.color}
              strokeWidth={3}
              strokeLinecap="round"
              opacity={0.55}
            />

            {/* Bucket outline */}
            <rect
              x={b.x}
              y={bucketY}
              width={b.width}
              height={b.height}
              rx={6}
              fill="#FFFFFF"
              stroke="#E2E8F0"
              strokeWidth={1.5}
            />

            {/* Bucket fill — level proportional to allocation % */}
            {b.pct > 0 ? (
              <rect
                x={b.x + 2}
                y={fillY + 1}
                width={b.width - 4}
                height={Math.max(0, fillH - 2)}
                rx={4}
                fill={b.color}
                opacity={b.fillAlpha}
              />
            ) : null}

            {/* Fill surface line */}
            {b.pct > 0 ? (
              <line
                x1={b.x + 4}
                y1={fillY}
                x2={b.x + b.width - 4}
                y2={fillY}
                stroke={b.color}
                strokeWidth={1.5}
                opacity={0.7}
              />
            ) : null}

            {/* Bucket label — drawn after rects so it sits on top of fill */}
            <text
              x={b.x + b.width / 2}
              y={bucketY + 32}
              textAnchor="middle"
              fill="#1A1815"
              fontSize={10}
              fontWeight={600}
              fontFamily="Manrope, system-ui, sans-serif"
            >
              {b.label}
            </text>
            <text
              x={b.x + b.width / 2}
              y={bucketY + b.height + 14}
              textAnchor="middle"
              fill={b.color}
              fontSize={11}
              fontWeight={500}
              fontFamily="'DM Mono', 'Courier New', monospace"
            >
              {b.pct}%
            </text>
            <text
              x={b.x + b.width / 2}
              y={bucketY + b.height + 26}
              textAnchor="middle"
              fill="#9CA3AF"
              fontSize={9}
              fontFamily="Manrope, system-ui, sans-serif"
            >
              {formatUsd(b.amount)}
            </text>
          </g>
        );
      })}

      {/* Pool glow ring */}
      {poolGlow ? (
        <rect
          x={poolX - 10}
          y={layout.poolY - 8}
          width={POOL_W + 20}
          height={POOL_H + 16}
          rx={14}
          fill="none"
          stroke="rgba(91,45,142,0.2)"
          strokeWidth={2}
          filter={`url(#pool-glow-${glowId})`}
          className="waterfall-pool-glow-ring"
        />
      ) : null}

      {/* Pool */}
      <rect
        x={poolX}
        y={layout.poolY}
        width={POOL_W}
        height={POOL_H}
        rx={10}
        fill="rgba(91,45,142,0.05)"
        stroke="rgba(91,45,142,0.2)"
        strokeWidth={1.5}
      />
      <text
        x={CENTER_X}
        y={layout.poolY + 18}
        textAnchor="middle"
        fill="rgba(91,45,142,0.7)"
        fontSize={10}
        fontFamily="Manrope, system-ui, sans-serif"
      >
        Surplus Pool
      </text>
      <text
        x={CENTER_X}
        y={layout.poolY + 36}
        textAnchor="middle"
        fill="#5B2D8E"
        fontSize={15}
        fontWeight={600}
        fontFamily="Fraunces, Georgia, serif"
      >
        {formatUsd(layout.poolAmount)}
      </text>
      <text
        x={CENTER_X}
        y={layout.poolY + 48}
        textAnchor="middle"
        fill="#9CA3AF"
        fontSize={9}
        fontFamily="'DM Mono', 'Courier New', monospace"
      >
        {poolPct}% of income
      </text>
    </svg>
  );
};

export default WaterfallSvg;
