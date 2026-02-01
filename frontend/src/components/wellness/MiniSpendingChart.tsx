import React from 'react';

export interface MiniSpendingChartProps {
  /** Values for recent weeks (oldest first), e.g. [80, 95, 70, 90, 100, 85] */
  data: number[];
  /** Max value for scale (default: max of data) */
  max?: number;
  /** Width of chart in pixels */
  width?: number;
  /** Height of chart in pixels */
  height?: number;
  /** Bar color when at or above average */
  color?: string;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Tiny sparkline: simple bar or line of recent weeks' values.
 * Used as mini bar chart per category.
 */
export const MiniSpendingChart: React.FC<MiniSpendingChartProps> = ({
  data,
  max: maxProp,
  width = 48,
  height = 20,
  color = 'rgb(139, 92, 246)',
  className = '',
  ariaLabel,
}) => {
  if (!data.length) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-700/50 rounded ${className}`}
        style={{ width, height }}
        role="img"
        aria-label={ariaLabel ?? 'No history'}
      >
        <span className="text-slate-500 text-xs">—</span>
      </div>
    );
  }

  const max = maxProp ?? Math.max(...data, 1);
  const scale = max > 0 ? height / max : 0;
  const barWidth = Math.max(2, (width - (data.length - 1) * 2) / data.length);

  return (
    <div
      className={`flex items-end gap-0.5 ${className}`}
      style={{ width, height }}
      role="img"
      aria-label={ariaLabel ?? `Last ${data.length} weeks: ${data.map((v) => `$${v}`).join(', ')}`}
    >
      {data.map((value, i) => (
        <div
          key={i}
          className="rounded-sm min-w-[2px] transition-opacity hover:opacity-90"
          style={{
            width: barWidth,
            height: Math.max(2, value * scale),
            backgroundColor: color,
          }}
          aria-hidden
        />
      ))}
    </div>
  );
};

export default MiniSpendingChart;
