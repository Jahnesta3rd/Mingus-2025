import React from 'react';
import styles from './Tier2PurchaseReminder.module.css';

/**
 * Proceed / defer / skip actions for Tier 2 shopping day.
 */
export default function Tier2DecisionUI({
  onProceed,
  onDefer,
  onSkip,
  loading = false,
}) {
  return (
    <div className={styles.actions}>
      <button
        type="button"
        onClick={onProceed}
        className={styles.primaryButton}
        disabled={loading}
      >
        {loading ? 'Loading…' : 'Shop Tier 2 now'}
      </button>
      <button
        type="button"
        onClick={onDefer}
        className={styles.secondaryButton}
        disabled={loading}
      >
        Defer to later
      </button>
      <button
        type="button"
        onClick={onSkip}
        className={styles.tertiaryButton}
        disabled={loading}
      >
        Skip Tier 2
      </button>
      <p className={styles.helpText}>
        Shop now with current earnings, wait for more, or skip Tier 2 entirely.
      </p>
    </div>
  );
}
