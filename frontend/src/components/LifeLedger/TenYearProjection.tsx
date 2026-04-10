import React, { useMemo } from 'react';
import type { LifeLedgerProfile } from '../../hooks/useLifeLedger';
import { lifeLedgerScoreColor } from './ModuleScoreCard';

export interface TenYearProjectionProps {
  profile: LifeLedgerProfile;
}

function barColorForModule(
  profile: LifeLedgerProfile,
  module: 'vibe' | 'body' | 'roof' | 'vehicle'
): string {
  const score =
    module === 'vibe'
      ? profile.vibe_score
      : module === 'body'
        ? profile.body_score
        : module === 'roof'
          ? profile.roof_score
          : profile.vehicle_score;
  if (score == null) return '#9ca3af';
  return lifeLedgerScoreColor(score);
}

const TenYearProjection: React.FC<TenYearProjectionProps> = ({ profile }) => {
  const rows = useMemo(() => {
    const relationship = (profile.vibe_annual_projection ?? 0) * 10;
    const health = (profile.body_health_cost_projection ?? 0) * 10;
    const housing = (profile.roof_housing_wealth_gap ?? 0) * 10;
    const vehicle = (profile.vehicle_annual_maintenance ?? 0) * 10;
    return [
      {
        key: 'relationship',
        label: 'Relationship Cost',
        short: 'Relationship',
        value: relationship,
        module: 'vibe' as const,
      },
      { key: 'health', label: 'Health Cost', short: 'Health', value: health, module: 'body' as const },
      {
        key: 'housing',
        label: 'Housing Wealth Gap',
        short: 'Housing',
        value: housing,
        module: 'roof' as const,
      },
      { key: 'vehicle', label: 'Vehicle Cost', short: 'Vehicle', value: vehicle, module: 'vehicle' as const },
    ];
  }, [profile]);

  const total = rows.reduce((s, r) => s + r.value, 0);
  const maxVal = Math.max(...rows.map((r) => r.value), 1);
  const chartW = 320;
  const chartH = 160;
  const barW = 56;
  const gap = 16;
  const totalBarsW = 4 * barW + 3 * gap;
  const startX = (chartW - totalBarsW) / 2;
  const baselineY = chartH - 28;
  const maxBarH = chartH - 48;

  return (
    <div className="mt-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">Your 10-Year Life Cost Projection</h3>
      <p className="text-sm text-gray-600 mt-1 mb-6">
        What optimizing each area could save you over a decade.
      </p>

      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-4">
        <p className="text-sm text-gray-700">
          <span className="font-medium text-gray-900">Total 10-year estimate: </span>
          <span className="text-2xl font-bold text-gray-900 tabular-nums">
            ${total.toLocaleString()}
          </span>
        </p>
      </div>

      <svg
        viewBox={`0 0 ${chartW} ${chartH}`}
        className="w-full max-w-md mx-auto block"
        role="img"
        aria-label="Ten-year cost projection by life area"
      >
        {rows.map((row, i) => {
          const h = maxBarH * (row.value / maxVal);
          const x = startX + i * (barW + gap);
          const y = baselineY - h;
          const fill = barColorForModule(profile, row.module);
          return (
            <g key={row.key}>
              <rect x={x} y={y} width={barW} height={h} rx={4} fill={fill} />
              <text
                x={x + barW / 2}
                y={chartH - 8}
                textAnchor="middle"
                fill="#4b5563"
                style={{ fontSize: '11px' }}
              >
                {row.short}
              </text>
            </g>
          );
        })}
      </svg>

      <ul className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-gray-600">
        {rows.map((row) => (
          <li key={row.key} className="flex justify-between gap-2 border-t border-gray-100 pt-2">
            <span>{row.label}</span>
            <span className="font-medium text-gray-900 tabular-nums">${row.value.toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TenYearProjection;
