import React, { useCallback, useMemo, useState } from 'react';
import type { LifeScoreSnapshot } from '../../hooks/useLifeCorrelation';

export interface ScoreTimelineChartProps {
  snapshots: LifeScoreSnapshot[];
}

const COLOR_BODY = '#C4A064';
const COLOR_VIBE = '#F0E8D8';
const COLOR_LEDGER = '#F59E0B';
const COLOR_SAVINGS = '#9a8f7e';

const PADDING = { top: 28, right: 12, bottom: 36, left: 44 };

function savingsScaled(s: LifeScoreSnapshot): number | null {
  const r = s.monthly_savings_rate;
  if (r == null || Number.isNaN(Number(r))) return null;
  return Math.min(100, Math.max(0, Number(r) * 100));
}

function smoothPath(xs: number[], ys: (number | null)[]): string {
  const pts: { x: number; y: number }[] = [];
  for (let i = 0; i < xs.length; i++) {
    const y = ys[i];
    if (y == null) continue;
    pts.push({ x: xs[i], y });
  }
  if (pts.length < 2) return '';
  let d = `M ${pts[0].x} ${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
  }
  return d;
}

function monthLabel(iso: string): string {
  try {
    const d = new Date(iso + (iso.includes('T') ? '' : 'T12:00:00'));
    return d.toLocaleDateString(undefined, { month: 'short' });
  } catch {
    return '';
  }
}

function formatHoverDate(iso: string): string {
  try {
    const d = new Date(iso + (iso.includes('T') ? '' : 'T12:00:00'));
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
}

const ScoreTimelineChart: React.FC<ScoreTimelineChartProps> = ({ snapshots }) => {
  const sorted = useMemo(
    () => [...snapshots].sort((a, b) => a.snapshot_date.localeCompare(b.snapshot_date)),
    [snapshots]
  );

  const w = 560;
  const h = 220;
  const innerW = w - PADDING.left - PADDING.right;
  const innerH = h - PADDING.top - PADDING.bottom;

  const xs = useMemo(() => {
    if (sorted.length <= 1) return sorted.map(() => PADDING.left + innerW / 2);
    return sorted.map((_, i) => PADDING.left + (i / (sorted.length - 1)) * innerW);
  }, [sorted, innerW]);

  const yAt = useCallback(
    (value: number | null) => {
      if (value == null) return null;
      const v = Math.min(100, Math.max(0, value));
      return PADDING.top + innerH - (v / 100) * innerH;
    },
    [innerH]
  );

  const series = useMemo(() => {
    const body = sorted.map((s) => (s.body_score != null ? Number(s.body_score) : null));
    const vibe = sorted.map((s) => (s.best_vibe_combined_score != null ? Number(s.best_vibe_combined_score) : null));
    const ledger = sorted.map((s) => (s.life_ledger_score != null ? Number(s.life_ledger_score) : null));
    const savings = sorted.map((s) => savingsScaled(s));
    return { body, vibe, ledger, savings };
  }, [sorted]);

  const paths = useMemo(
    () => ({
      body: smoothPath(xs, series.body.map((v) => (v == null ? null : yAt(v)))),
      vibe: smoothPath(xs, series.vibe.map((v) => (v == null ? null : yAt(v)))),
      ledger: smoothPath(xs, series.ledger.map((v) => (v == null ? null : yAt(v)))),
      savings: smoothPath(xs, series.savings.map((v) => (v == null ? null : yAt(v)))),
    }),
    [xs, series, yAt]
  );

  const [hover, setHover] = useState<{ index: number } | null>(null);

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (sorted.length < 3) return;
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const scaleX = w / rect.width;
    const mx = (e.clientX - rect.left) * scaleX;
    if (sorted.length === 0) return;
    let best = 0;
    let bestDist = Infinity;
    xs.forEach((x, i) => {
      const d = Math.abs(mx - x);
      if (d < bestDist) {
        bestDist = d;
        best = i;
      }
    });
    setHover({ index: best });
  };

  const onLeave = () => setHover(null);

  if (sorted.length < 3) {
    return (
      <div
        className="rounded-lg border border-[#9a8f7e]/30 bg-[#1a1512]/80 px-4 py-10 text-center"
        role="img"
        aria-label="Timeline chart placeholder"
      >
        <p className="text-[#F0E8D8] text-sm font-medium">Your patterns will appear here as you track over time</p>
        <p className="mt-2 text-xs text-[#9a8f7e]">We need at least three snapshots to draw your correlation timeline.</p>
      </div>
    );
  }

  const hi = hover?.index;
  const snap = hi != null ? sorted[hi] : null;
  const hoverSavings = snap ? savingsScaled(snap) : null;

  return (
    <div className="relative w-full">
      <div className="flex flex-wrap gap-4 mb-2 text-xs text-[#9a8f7e]">
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 rounded" style={{ background: COLOR_BODY }} />
          Body Score
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 rounded" style={{ background: COLOR_VIBE }} />
          Best Vibe Score
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 rounded" style={{ background: COLOR_LEDGER }} />
          Life Ledger Score
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 rounded" style={{ background: COLOR_SAVINGS }} />
          Savings rate × 100
        </span>
      </div>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="w-full h-auto max-h-[280px]"
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        role="img"
        aria-label="Life score timeline"
      >
        {/* Y grid */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const y = yAt(tick);
          if (y == null) return null;
          return (
            <g key={tick}>
              <line
                x1={PADDING.left}
                y1={y}
                x2={w - PADDING.right}
                y2={y}
                stroke="#9a8f7e"
                strokeOpacity={0.2}
                strokeWidth={1}
              />
              <text x={PADDING.left - 8} y={y + 4} fill="#9a8f7e" fontSize={10} textAnchor="end">
                {tick}
              </text>
            </g>
          );
        })}

        {/* X labels (sparse) */}
        {sorted.map((s, i) => {
          if (sorted.length <= 6 || i % Math.ceil(sorted.length / 6) === 0 || i === sorted.length - 1) {
            return (
              <text
                key={s.id}
                x={xs[i]}
                y={h - 10}
                fill="#9a8f7e"
                fontSize={10}
                textAnchor="middle"
              >
                {monthLabel(s.snapshot_date)}
              </text>
            );
          }
          return null;
        })}

        {paths.savings && (
          <path d={paths.savings} fill="none" stroke={COLOR_SAVINGS} strokeWidth={2} strokeLinecap="round" />
        )}
        {paths.ledger && (
          <path d={paths.ledger} fill="none" stroke={COLOR_LEDGER} strokeWidth={2} strokeLinecap="round" />
        )}
        {paths.vibe && (
          <path d={paths.vibe} fill="none" stroke={COLOR_VIBE} strokeWidth={2} strokeLinecap="round" />
        )}
        {paths.body && (
          <path d={paths.body} fill="none" stroke={COLOR_BODY} strokeWidth={2.5} strokeLinecap="round" />
        )}

        {hi != null && (
          <line
            x1={xs[hi]}
            y1={PADDING.top}
            x2={xs[hi]}
            y2={PADDING.top + innerH}
            stroke="#C4A064"
            strokeOpacity={0.35}
            strokeWidth={1}
          />
        )}

        {sorted.map((s, i) => {
          const cx = xs[i];
          const markers = [
            { v: series.body[i], c: COLOR_BODY },
            { v: series.vibe[i], c: COLOR_VIBE },
            { v: series.ledger[i], c: COLOR_LEDGER },
            { v: series.savings[i], c: COLOR_SAVINGS },
          ];
          return (
            <g key={s.id}>
              {markers.map((m, j) => {
                if (m.v == null) return null;
                const cy = yAt(m.v);
                if (cy == null) return null;
                return (
                  <circle
                    key={j}
                    cx={cx}
                    cy={cy}
                    r={hi === i ? 5 : 3}
                    fill={m.c}
                    stroke="#0d0a08"
                    strokeWidth={1}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>

      {snap && hi != null && (
        <div
          className="mt-3 rounded-md border border-[#C4A064]/40 bg-[#1a1512] px-3 py-2 text-xs text-[#F0E8D8]"
          role="status"
        >
          <p className="font-semibold text-[#C4A064] mb-1">{formatHoverDate(snap.snapshot_date)}</p>
          <ul className="space-y-0.5">
            <li>Body: {snap.body_score ?? '—'}</li>
            <li>Best vibe (combined): {snap.best_vibe_combined_score ?? '—'}</li>
            <li>Life Ledger: {snap.life_ledger_score ?? '—'}</li>
            <li>Savings × 100: {hoverSavings != null ? hoverSavings.toFixed(0) : '—'}</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ScoreTimelineChart;
