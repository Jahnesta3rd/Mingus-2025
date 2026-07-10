import React from 'react';
import styles from './PurchasePlanView.module.css';

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const [year, month, day] = String(dateStr).split('-');
    const date = new Date(Number(year), Number(month) - 1, Number(day));
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n) || value == null) return null;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

/**
 * Warning when Tier 2 depends on side-job earnings.
 */
export default function JobDependencyWarning({
  requiredEarnings,
  tier2Date,
  fallback,
}) {
  const earningsLabel = formatMoney(requiredEarnings);

  return (
    <aside className={styles.jobWarning} role="note">
      <div className={styles.warningIcon} aria-hidden="true">
        !
      </div>
      <div className={styles.warningContent}>
        <h3>Tier 2 depends on side job earnings</h3>
        <p>
          {earningsLabel ? (
            <>
              You&apos;ll need about <strong>{earningsLabel}</strong> by{' '}
              {formatDate(tier2Date)} for the full Tier 2 plan.
            </>
          ) : (
            <>
              Tier 2 is contingent on side income by {formatDate(tier2Date)}. Hit
              your earnings target before shopping that window.
            </>
          )}
        </p>
        <details>
          <summary>What if I don&apos;t hit the target?</summary>
          <p className={styles.fallbackText}>
            {fallback ||
              'You can still complete Tier 1 essentials and adjust Tier 2 as needed.'}
          </p>
        </details>
      </div>
    </aside>
  );
}
