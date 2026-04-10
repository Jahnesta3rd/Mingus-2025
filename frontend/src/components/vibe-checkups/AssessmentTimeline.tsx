import { useMemo, useState } from 'react';
import type { VibePersonAssessment } from '../../hooks/useVibeTracker';

const W = 720;
const H = 220;
const PAD_L = 44;
const PAD_R = 20;
const PAD_T = 16;
const PAD_B = 36;

function parseTime(iso: string | null): number {
  if (!iso) return 0;
  const t = new Date(iso).getTime();
  return Number.isNaN(t) ? 0 : t;
}

function formatShortDate(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '—';
  }
}

function formatMoney(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

export type AssessmentTimelineProps = {
  assessments: VibePersonAssessment[];
};

export function AssessmentTimeline({ assessments }: AssessmentTimelineProps) {
  const sortedAsc = useMemo(
    () =>
      [...assessments].sort(
        (a, b) => parseTime(a.completed_at) - parseTime(b.completed_at) || a.id.localeCompare(b.id)
      ),
    [assessments]
  );

  const sortedDesc = useMemo(() => [...sortedAsc].reverse(), [sortedAsc]);

  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;

  const [hovered, setHovered] = useState<number | null>(null);

  const points = useMemo(() => {
    const n = sortedAsc.length;
    if (n === 0) return { emotional: [] as { x: number; y: number }[], financial: [] as { x: number; y: number }[] };
    return {
      emotional: sortedAsc.map((a, i) => {
        const x = n === 1 ? PAD_L + innerW / 2 : PAD_L + (i / (n - 1)) * innerW;
        const y = PAD_T + innerH - (Math.max(0, Math.min(100, a.emotional_score)) / 100) * innerH;
        return { x, y };
      }),
      financial: sortedAsc.map((a, i) => {
        const x = n === 1 ? PAD_L + innerW / 2 : PAD_L + (i / (n - 1)) * innerW;
        const y = PAD_T + innerH - (Math.max(0, Math.min(100, a.financial_score)) / 100) * innerH;
        return { x, y };
      }),
    };
  }, [sortedAsc, innerW, innerH]);

  const linePath = (pts: { x: number; y: number }[]) =>
    pts.length === 0 ? '' : `M ${pts.map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' L ')}`;

  const hoverInfo =
    hovered != null && sortedAsc[hovered]
      ? sortedAsc[hovered]
      : null;

  if (sortedAsc.length === 0) {
    return (
      <div className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/80 p-6 text-center text-sm text-[#9a8f7e]">
        No assessments yet.
      </div>
    );
  }

  if (sortedAsc.length === 1) {
    const a = sortedAsc[0];
    const cx = PAD_L + innerW / 2;
    const cyE = PAD_T + innerH - (a.emotional_score / 100) * innerH;
    const cyF = PAD_T + innerH - (a.financial_score / 100) * innerH;
    return (
      <div className="space-y-4">
        <div className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/80 p-4">
          <p className="text-center text-xs font-medium uppercase tracking-wider text-[#9a8f7e]">Score trend</p>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="mt-2 w-full overflow-visible"
            role="img"
            aria-label="Single assessment data point"
          >
            <line
              x1={PAD_L}
              y1={PAD_T + innerH}
              x2={PAD_L + innerW}
              y2={PAD_T + innerH}
              stroke="#2a2030"
              strokeWidth={1}
            />
            <text x={PAD_L} y={H - 8} fill="#9a8f7e" fontSize={11}>
              {formatShortDate(a.completed_at)}
            </text>
            <circle cx={cx} cy={cyE} r={6} fill="#C4A064" stroke="#0d0a08" strokeWidth={2} />
            <circle cx={cx} cy={cyF} r={6} fill="#F0E8D8" stroke="#0d0a08" strokeWidth={2} />
          </svg>
          <p className="mt-2 text-center text-sm text-[#9a8f7e]">Take another checkup to see trends</p>
          <div className="mt-3 flex justify-center gap-6 text-xs text-[#9a8f7e]">
            <span>
              <span className="inline-block h-2 w-2 rounded-full bg-[#C4A064]" /> Emotional
            </span>
            <span>
              <span className="inline-block h-2 w-2 rounded-full bg-[#F0E8D8]" /> Financial
            </span>
          </div>
        </div>
        <AssessmentList rows={sortedDesc} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative rounded-xl border border-[#2a2030] bg-[#0d0a08]/80 p-3">
        <p className="text-center text-xs font-medium uppercase tracking-wider text-[#9a8f7e]">Score trend</p>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="mt-1 w-full overflow-visible"
          role="img"
          aria-label="Emotional and financial scores over time"
        >
          {[0, 25, 50, 75, 100].map((tick) => {
            const y = PAD_T + innerH - (tick / 100) * innerH;
            return (
              <g key={tick}>
                <line x1={PAD_L} y1={y} x2={PAD_L + innerW} y2={y} stroke="#2a2030" strokeWidth={1} strokeDasharray="4 6" />
                <text x={4} y={y + 4} fill="#9a8f7e" fontSize={10}>
                  {tick}
                </text>
              </g>
            );
          })}
          <line
            x1={PAD_L}
            y1={PAD_T + innerH}
            x2={PAD_L + innerW}
            y2={PAD_T + innerH}
            stroke="#2a2030"
            strokeWidth={1}
          />
          <path
            d={linePath(points.financial)}
            fill="none"
            stroke="#F0E8D8"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            opacity={0.85}
          />
          <path
            d={linePath(points.emotional)}
            fill="none"
            stroke="#C4A064"
            strokeWidth={2.5}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {sortedAsc.map((a, i) => {
            const xe = points.emotional[i].x;
            const ye = points.emotional[i].y;
            const yf = points.financial[i].y;
            const active = hovered === i;
            return (
              <g key={a.id}>
                <circle
                  cx={xe}
                  cy={yf}
                  r={active ? 9 : 6}
                  fill="#F0E8D8"
                  stroke="#0d0a08"
                  strokeWidth={2}
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                />
                <circle
                  cx={xe}
                  cy={ye}
                  r={active ? 9 : 6}
                  fill="#C4A064"
                  stroke="#0d0a08"
                  strokeWidth={2}
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                />
              </g>
            );
          })}
          {sortedAsc.map((a, i) => {
            const x = points.emotional[i].x;
            const label = formatShortDate(a.completed_at);
            return (
              <text
                key={`lbl-${a.id}`}
                x={x}
                y={H - 10}
                textAnchor="middle"
                fill="#9a8f7e"
                fontSize={10}
              >
                {label}
              </text>
            );
          })}
        </svg>
        {hoverInfo ? (
          <div className="pointer-events-none absolute left-1/2 top-10 z-10 w-[min(100%,280px)] -translate-x-1/2 rounded-lg border border-[#2a2030] bg-[#1a1520] px-3 py-2 text-center text-xs text-[#F0E8D8] shadow-xl">
            <div className="font-medium text-[#C4A064]">{formatShortDate(hoverInfo.completed_at)}</div>
            <div className="mt-1">
              {hoverInfo.verdict_emoji ? <span className="mr-1">{hoverInfo.verdict_emoji}</span> : null}
              {hoverInfo.verdict_label}
            </div>
            <div className="mt-1 tabular-nums text-[#9a8f7e]">
              Emotional {hoverInfo.emotional_score}% · Financial {hoverInfo.financial_score}%
            </div>
          </div>
        ) : null}
        <div className="mt-1 flex justify-center gap-6 text-[10px] text-[#9a8f7e]">
          <span>
            <span className="mr-1 inline-block h-2 w-8 rounded-full bg-[#C4A064]" /> Emotional
          </span>
          <span>
            <span className="mr-1 inline-block h-2 w-8 rounded-full bg-[#F0E8D8]" /> Financial
          </span>
        </div>
      </div>
      <AssessmentList rows={sortedDesc} />
    </div>
  );
}

function AssessmentList({ rows }: { rows: VibePersonAssessment[] }) {
  return (
    <div className="rounded-xl border border-[#2a2030] bg-[#1a1520]/60">
      <p className="border-b border-[#2a2030] px-4 py-2 text-xs font-medium uppercase tracking-wider text-[#9a8f7e]">
        Checkup history
      </p>
      <ul className="divide-y divide-[#2a2030]">
        {rows.map((a) => (
          <li key={a.id} className="px-4 py-3 text-sm">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="text-[#9a8f7e]">{formatShortDate(a.completed_at)}</span>
              <span className="tabular-nums text-[#9a8f7e]">{formatMoney(a.annual_projection)} / yr</span>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-[#F0E8D8]">
              <span>{a.verdict_emoji}</span>
              <span>{a.verdict_label}</span>
            </div>
            <div className="mt-1 text-xs tabular-nums text-[#9a8f7e]">
              Emotional {a.emotional_score}% · Financial {a.financial_score}%
            </div>
            {a.notes ? <p className="mt-2 text-xs italic text-[#9a8f7e]">&ldquo;{a.notes}&rdquo;</p> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
