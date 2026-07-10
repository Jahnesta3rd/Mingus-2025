import React from 'react';
import styles from './EarningsProgressBar.module.css';

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(n);
}

/**
 * Progress toward side-job earnings target + Tier 2 budget breakdown.
 */
export default function EarningsProgressBar({ commitment }) {
  if (!commitment) return null;

  const actual = Number(commitment.actualEarnings) || 0;
  const target = Number(commitment.targetEarnings) || 0;
  const base = Number(commitment.tier2BaseBudget) || 0;
  const total =
    Number(commitment.tier2BudgetWithEarnings) || base + actual;
  const percent = target > 0 ? (actual / target) * 100 : 0;
  const progressPercent = Math.min(Math.max(percent, 0), 100);
  const goalMet = percent >= 100;

  return (
    <div className={styles.progressSection}>
      <div className={styles.header}>
        <span className={styles.title}>{commitment.jobTitle}</span>
        <span className={goalMet ? styles.statusMet : styles.status}>
          {goalMet ? 'Goal met' : `${Math.floor(percent)}%`}
        </span>
      </div>

      <div
        className={styles.bar}
        role="progressbar"
        aria-valuenow={Math.round(progressPercent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Earnings progress"
      >
        <div
          className={styles.progress}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className={styles.labels}>
        <span>{formatMoney(actual)} earned</span>
        <span>{formatMoney(target)} target</span>
      </div>

      <div className={styles.budgetBreakdown}>
        <div className={styles.item}>
          <span>Tier 2 base</span>
          <span>{formatMoney(base)}</span>
        </div>
        <div className={styles.item}>
          <span>Job earnings</span>
          <span className={styles.earnings}>{formatMoney(actual)}</span>
        </div>
        <div className={`${styles.item} ${styles.total}`}>
          <span>Total budget</span>
          <span>{formatMoney(total)}</span>
        </div>
      </div>
    </div>
  );
}
