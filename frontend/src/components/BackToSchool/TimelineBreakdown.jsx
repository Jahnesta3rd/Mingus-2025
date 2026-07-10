import React from 'react';
import styles from './PurchasePlanView.module.css';

function parseLocalDate(dateStr) {
  const [year, month, day] = String(dateStr).split('-');
  return new Date(Number(year), Number(month) - 1, Number(day));
}

function formatDate(dateStr) {
  try {
    const date = parseLocalDate(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function calculateDaysUntil(dateStr) {
  const targetDate = parseLocalDate(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  targetDate.setHours(0, 0, 0, 0);
  return Math.ceil((targetDate - today) / (1000 * 60 * 60 * 24));
}

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

function daysLabel(daysUntil) {
  if (daysUntil > 0) return `${daysUntil} day${daysUntil === 1 ? '' : 's'} away`;
  if (daysUntil === 0) return 'Today';
  return 'Overdue';
}

function TierTimelineStep({ tier, daysUntil, budget, spent, percent, purchaseBy }) {
  const labels = { 1: 'Critical', 2: 'Important', 3: 'Nice-to-have' };
  return (
    <div className={styles.timelineStep}>
      <div className={`${styles.timelineMarker} ${styles[`tier${tier}`]}`} aria-hidden="true" />
      <div className={styles.timelineContent}>
        <p className={styles.timelineLabel}>{labels[tier]}</p>
        <p className={styles.timelineDate}>{formatDate(purchaseBy)}</p>
        <p className={styles.timelineDaysLeft}>{daysLabel(daysUntil)}</p>
        <div className={styles.budgetBar} aria-hidden="true">
          <div className={styles.budgetUsed} style={{ width: `${percent}%` }} />
        </div>
        <p className={styles.budgetText}>
          {formatMoney(spent)} of {formatMoney(budget)}
        </p>
      </div>
    </div>
  );
}

/**
 * Visual 3-week timeline with budget utilization bars.
 */
export default function TimelineBreakdown({ plan }) {
  if (!plan?.tier1 || !plan?.tier2 || !plan?.tier3) return null;

  const steps = [1, 2, 3].map((tier) => {
    const block = plan[`tier${tier}`];
    const budget = Number(block.budget) || 0;
    const spent = Number(block.totalEstimated) || 0;
    const percent = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;
    return {
      tier,
      daysUntil: calculateDaysUntil(block.purchaseBy),
      budget,
      spent,
      percent,
      purchaseBy: block.purchaseBy,
    };
  });

  return (
    <section className={styles.timeline} aria-label="Purchase timeline">
      <div className={styles.timelineTrack}>
        {steps.map((step) => (
          <TierTimelineStep key={step.tier} {...step} />
        ))}
      </div>
    </section>
  );
}
