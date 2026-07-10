import React from 'react';
import styles from './BTSDateSetup.module.css';

const STATUS_CLASS = {
  healthy: styles.statusHealthy,
  warning: styles.statusWarning,
  danger: styles.statusDanger,
};

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

function formatDisplayDate(iso) {
  if (!iso) return '—';
  const d = new Date(`${iso}T12:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Visual 3-week BTS cash plan: today → tier1 → tier2 → school start.
 *
 * @param {{
 *   timeline?: Array<{
 *     key: string,
 *     label: string,
 *     date: string,
 *     forecastedBalance: number,
 *     status: string,
 *     daysFromToday?: number,
 *   }>,
 *   loading?: boolean,
 * }} props
 */
export default function CashForecastTimeline({ timeline = [], loading = false }) {
  if (loading) {
    return (
      <section className={styles.timeline} aria-busy="true">
        <h3 className={styles.timelineTitle}>Your 3-week cash plan</h3>
        <p className={styles.muted}>Loading forecast…</p>
      </section>
    );
  }

  if (!timeline.length) {
    return null;
  }

  return (
    <section className={styles.timeline} aria-label="Cash forecast timeline">
      <h3 className={styles.timelineTitle}>Your 3-week cash plan</h3>
      <p className={styles.timelineSub}>
        Forecasted balances on each purchase window before school starts.
      </p>

      <ol className={styles.timelineTrack}>
        {timeline.map((point, index) => {
          const statusClass = STATUS_CLASS[point.status] || styles.statusWarning;
          return (
            <li key={point.key || point.date} className={styles.timelineItem}>
              {index > 0 ? <span className={styles.timelineConnector} aria-hidden="true" /> : null}
              <div className={`${styles.timelineCard} ${statusClass}`}>
                <span className={styles.timelineLabel}>{point.label}</span>
                <span className={styles.timelineDate}>{formatDisplayDate(point.date)}</span>
                <span className={styles.timelineBalance}>
                  {formatMoney(point.forecastedBalance)}
                </span>
                <span className={styles.timelineStatus}>{point.status}</span>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
