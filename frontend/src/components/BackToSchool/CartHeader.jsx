import React from 'react';
import styles from './ProductPickerUI.module.css';

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
 * Budget summary header for the product picker.
 */
export default function CartHeader({ tier, total, budget, remaining, byRetailer }) {
  return (
    <header className={styles.cartHeader}>
      <p className={styles.eyebrow}>Back to school</p>
      <h1 className={styles.heading}>Tier {tier} shopping</h1>
      <div className={styles.budgetSummary}>
        <div className={styles.summaryRow}>
          <span>Subtotal</span>
          <span>{formatMoney(total)}</span>
        </div>
        <div className={styles.summaryRow}>
          <span>Budget</span>
          <span>{formatMoney(budget)}</span>
        </div>
        <div className={`${styles.summaryRow} ${styles.total}`}>
          <span>Remaining</span>
          <span className={remaining >= 0 ? styles.positive : styles.negative}>
            {formatMoney(remaining)}
          </span>
        </div>
      </div>
      <p className={styles.breakdownByRetailer}>
        H&amp;M: {formatMoney(byRetailer['h&m'] || 0)}
        {' · '}
        Nordstrom: {formatMoney(byRetailer.nordstrom || 0)}
        {' · '}
        Amazon: {formatMoney(byRetailer.amazon || 0)}
      </p>
    </header>
  );
}
