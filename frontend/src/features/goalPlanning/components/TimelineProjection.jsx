import React, { useCallback, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceDot,
} from 'recharts';
import {
  buildTimelineProjectionData,
  formatAxisCurrency,
  getPathKey,
} from '../utils/timelineProjectionUtils.js';
import {
  formatCurrency,
  feasibilityClassName,
} from '../utils/recommendationDisplayUtils.js';
import styles from './TimelineProjection.module.css';

/**
 * @param {object} props
 * @param {object} [props.goal]
 * @param {object[]} [props.paths]
 * @param {object | null | undefined} [props.analysis]
 * @param {number} [props.currentSavings]
 * @param {string} [props.selectedPathId]
 * @param {string | object} [props.selectedPath] - Alias: path id or path object
 * @param {(pathId: string) => void} [props.onSelectPath]
 */
export default function TimelineProjection({
  goal,
  paths = [],
  analysis,
  currentSavings,
  selectedPathId,
  selectedPath,
  onSelectPath,
}) {
  const resolvedSelectedPathId = useMemo(() => {
    if (selectedPathId) {
      return selectedPathId;
    }
    if (typeof selectedPath === 'string') {
      return selectedPath;
    }
    if (selectedPath && typeof selectedPath === 'object') {
      return getPathKey(selectedPath);
    }
    return null;
  }, [selectedPath, selectedPathId]);

  const [hiddenPathIds, setHiddenPathIds] = useState(() => new Set());

  const { chartData, goalThreshold, timelineYears, pathMeta } = useMemo(
    () => buildTimelineProjectionData({
      goal,
      paths,
      analysis,
      currentSavings,
    }),
    [analysis, currentSavings, goal, paths],
  );

  const visiblePathMeta = useMemo(
    () => pathMeta.filter((meta) => !hiddenPathIds.has(meta.pathId)),
    [hiddenPathIds, pathMeta],
  );

  const togglePathVisibility = useCallback((pathId) => {
    setHiddenPathIds((prev) => {
      const next = new Set(prev);
      if (next.has(pathId)) {
        next.delete(pathId);
      } else {
        next.add(pathId);
      }
      return next;
    });
  }, []);

  const handleLegendClick = useCallback((pathId) => {
    togglePathVisibility(pathId);
    onSelectPath?.(pathId);
  }, [onSelectPath, togglePathVisibility]);

  const milestoneYears = useMemo(() => {
    const years = [];
    for (let year = 1; year <= Math.min(3, timelineYears); year += 1) {
      years.push(year);
    }
    return years;
  }, [timelineYears]);

  if (!paths.length || !chartData.length) {
    return (
      <section className={styles.timelineProjection} aria-label="Timeline projection">
        <div className={styles.emptyState}>
          Projection data will appear once recommendation paths are available.
        </div>
      </section>
    );
  }

  return (
    <section className={styles.timelineProjection} aria-label="Timeline projection">
      <header className={styles.header}>
        <div>
          <h4>Savings timeline</h4>
          <p>
            Compare how each path accumulates savings over {timelineYears} years.
            Goal target: {formatCurrency(goalThreshold)}.
          </p>
        </div>
      </header>

      <div className={styles.chartWrap} data-testid="timeline-chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 12, right: 16, left: 8, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#ececf4" />
            {milestoneYears.map((year) => (
              <ReferenceLine
                key={`milestone-${year}`}
                x={year}
                stroke="#f0f0f5"
                strokeDasharray="2 4"
              />
            ))}
            <XAxis
              dataKey="year"
              type="number"
              domain={[0, timelineYears]}
              ticks={Array.from({ length: timelineYears + 1 }, (_, index) => index)}
              tickFormatter={(value) => `${value}`}
              label={{ value: 'Years', position: 'insideBottomRight', offset: -4 }}
            />
            <YAxis
              tickFormatter={formatAxisCurrency}
              width={56}
              label={{ value: 'Savings ($)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip content={<ProjectionTooltip pathMeta={pathMeta} goalThreshold={goalThreshold} />} />

            <Line
              dataKey="goalThreshold"
              stroke="#999"
              strokeDasharray="5 5"
              dot={false}
              isAnimationActive={false}
              name="Goal amount"
              strokeWidth={2}
            />

            <Line
              dataKey="currentSavings"
              stroke="#ccc"
              strokeWidth={1}
              dot={false}
              isAnimationActive={false}
              name="Starting savings"
            />

            {visiblePathMeta.map((meta) => {
              const isSelected = resolvedSelectedPathId === meta.pathId;
              return (
                <Line
                  key={meta.pathId}
                  dataKey={meta.pathId}
                  stroke={meta.color}
                  strokeWidth={isSelected ? 3 : 2}
                  dot={{ r: isSelected ? 5 : 4 }}
                  activeDot={{ r: 6 }}
                  name={meta.title}
                  connectNulls
                />
              );
            })}

            {visiblePathMeta.map((meta) => {
              if (!meta.goalReachedYear) {
                return null;
              }
              const reachedRow = chartData.find((row) => row.year === meta.goalReachedYear);
              const yValue = reachedRow?.[meta.pathId];
              if (typeof yValue !== 'number') {
                return null;
              }
              return (
                <ReferenceDot
                  key={`goal-hit-${meta.pathId}`}
                  x={meta.goalReachedYear}
                  y={yValue}
                  r={6}
                  fill={meta.color}
                  stroke="#fff"
                  strokeWidth={2}
                  ifOverflow="extendDomain"
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className={styles.legend} role="list" aria-label="Path legend">
        {pathMeta.map((meta) => {
          const isHidden = hiddenPathIds.has(meta.pathId);
          const isSelected = resolvedSelectedPathId === meta.pathId;
          return (
            <button
              key={meta.pathId}
              type="button"
              role="listitem"
              aria-label={`${meta.title}${meta.mostRealistic ? ' (recommended)' : ''}`}
              className={`${styles.legendItem}${isHidden ? ` ${styles.legendItemHidden}` : ''}${isSelected ? ` ${styles.legendItemSelected}` : ''}`}
              onClick={() => handleLegendClick(meta.pathId)}
              aria-pressed={isSelected}
            >
              <span className={styles.colorSwatch} style={{ backgroundColor: meta.color }} aria-hidden />
              {meta.title}
              {meta.mostRealistic && ' ⭐'}
            </button>
          );
        })}
      </div>

      <div className={styles.metricsGrid}>
        {pathMeta.map((meta) => {
          const isSelected = resolvedSelectedPathId === meta.pathId;
          const feasibilityClass = styles[feasibilityClassName(meta.feasibility)] ?? styles.feasibilityMedium;
          return (
            <div
              key={`metric-${meta.pathId}`}
              className={`${styles.metricCard}${isSelected ? ` ${styles.metricCardSelected}` : ''}`}
            >
              <button type="button" onClick={() => onSelectPath?.(meta.pathId)}>
                <div className={styles.metricTitleRow}>
                  <span className={styles.colorSwatch} style={{ backgroundColor: meta.color }} aria-hidden />
                  <span className={styles.metricTitle}>{meta.title}</span>
                  {meta.mostRealistic && (
                    <span className={styles.recommendedBadge}>Recommended</span>
                  )}
                </div>
                <span className={`${styles.feasibilityBadge} ${feasibilityClass}`}>
                  {meta.feasibility} feasibility
                </span>
                <p className={styles.metricDetail}>
                  Monthly boost: {formatCurrency(meta.monthlyBoost)}/mo
                </p>
                <p className={styles.metricDetail}>
                  {timelineYears}-year savings: {formatCurrency(meta.totalSavings)}
                </p>
                <p className={styles.metricDetail}>
                  Goal reached: {meta.goalReachedYear ? `Year ${meta.goalReachedYear}` : 'Not within timeline'}
                </p>
                <p className={styles.metricDetail}>
                  Progress: {meta.progressPercent}%
                </p>
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/**
 * @param {object} props
 * @param {boolean} [props.active]
 * @param {Array<Record<string, unknown>>} [props.payload]
 * @param {string | number} [props.label]
 * @param {Array<Record<string, unknown>>} props.pathMeta
 * @param {number} props.goalThreshold
 */
function ProjectionTooltip({
  active,
  payload,
  label,
  pathMeta,
  goalThreshold,
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const year = Number(label ?? payload[0]?.payload?.year ?? 0);
  const pathRows = payload.filter(
    (entry) => entry.dataKey
      && entry.dataKey !== 'goalThreshold'
      && entry.dataKey !== 'currentSavings',
  );

  return (
    <div className={styles.tooltip}>
      <p className={styles.tooltipTitle}>Year {year}</p>
      {pathRows.map((entry) => {
        const meta = pathMeta.find((item) => item.pathId === entry.dataKey);
        const amount = Number(entry.value ?? 0);
        const progress = goalThreshold > 0
          ? Math.min(100, Math.round((amount / goalThreshold) * 100))
          : 0;
        return (
          <p key={String(entry.dataKey)} className={styles.tooltipRow}>
            <strong>{meta?.title ?? entry.name}:</strong>{' '}
            {formatCurrency(amount)} ({progress}% of goal)
            {meta?.monthlyBoost ? ` · +${formatCurrency(meta.monthlyBoost)}/mo` : ''}
          </p>
        );
      })}
      <p className={styles.tooltipRow}>
        Goal: {formatCurrency(goalThreshold)}
      </p>
    </div>
  );
}
