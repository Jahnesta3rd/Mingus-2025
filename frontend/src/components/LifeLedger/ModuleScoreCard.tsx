import React from 'react';
import { Link } from 'react-router-dom';
import { Lock } from 'lucide-react';

export function lifeLedgerScoreColor(score: number): string {
  if (score >= 70) return '#16a34a';
  if (score >= 50) return '#ca8a04';
  return '#dc2626';
}

export interface ModuleScoreCardProps {
  module: string;
  score: number | null;
  label: string;
  icon: string;
  actionUrl: string;
  locked?: boolean;
}

const RING_STROKE_DEFAULT = 5;

export function LifeLedgerScoreRing({ score, size }: { score: number; size: number }) {
  const stroke = size >= 100 ? 8 : RING_STROKE_DEFAULT;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, score)) / 100;
  const dash = c * pct;
  const color = lifeLedgerScoreColor(score);

  return (
    <svg width={size} height={size} className="flex-shrink-0" aria-hidden>
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c}`}
        />
      </g>
      <text
        x="50%"
        y="50%"
        dominantBaseline="central"
        textAnchor="middle"
        className="text-lg font-bold tabular-nums"
        fill={color}
        style={{
          fontSize: size >= 120 ? '2rem' : size > 88 ? '1.5rem' : '1.125rem',
        }}
      >
        {score}
      </text>
    </svg>
  );
}

const ModuleScoreCard: React.FC<ModuleScoreCardProps> = ({
  module: _module,
  score,
  label,
  icon,
  actionUrl,
  locked = false,
}) => {
  const ringSize = 76;

  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50/80 p-4 flex flex-col items-center text-center min-h-[168px] justify-between">
      <div className="text-2xl leading-none" aria-hidden>
        {icon}
      </div>
      <p className="text-xs font-medium text-gray-600 mt-2 leading-tight">{label}</p>

      {locked ? (
        <div className="flex flex-col items-center gap-1 mt-3 py-2">
          <Lock className="w-7 h-7 text-gray-400" strokeWidth={2} aria-hidden />
          <Link
            to="/checkout"
            className="text-xs font-semibold text-violet-600 hover:text-violet-700 hover:underline"
          >
            Upgrade to unlock
          </Link>
        </div>
      ) : score == null ? (
        <Link
          to={actionUrl}
          className="mt-3 inline-flex items-center justify-center rounded-lg bg-violet-600 px-3 py-2 text-xs font-semibold text-white hover:bg-violet-700 transition-colors"
        >
          Complete Assessment
        </Link>
      ) : (
        <div className="mt-2 flex justify-center">
          <LifeLedgerScoreRing score={score} size={ringSize} />
        </div>
      )}
    </div>
  );
};

export default ModuleScoreCard;
