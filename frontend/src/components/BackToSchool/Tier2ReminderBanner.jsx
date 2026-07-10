import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Tier2ReminderBanner.module.css';

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
 * Persistent in-app banner when Tier 2 shopping window opens (BTS8).
 */
export default function Tier2ReminderBanner({
  sessionId,
  commitment,
  tier2BaseBudget,
  tier2BudgetWithEarnings,
  dismissLoading = false,
  onDismiss,
}) {
  const navigate = useNavigate();

  const earnings = Number(commitment?.actualEarnings) || 0;
  const base =
    Number(
      tier2BaseBudget ??
        commitment?.tier2BaseBudget ??
        0,
    ) || 0;
  const total =
    tier2BudgetWithEarnings != null
      ? Number(tier2BudgetWithEarnings)
      : Number(commitment?.tier2BudgetWithEarnings) || base + earnings;

  const handleShopTier2 = () => {
    navigate(`/bts/${sessionId}/shop/2`, {
      state: {
        tier: 2,
        tierKey: 'tier2',
        budget: total,
        commitment: commitment
          ? {
              jobTitle: commitment.jobTitle,
              actualEarnings: commitment.actualEarnings,
            }
          : undefined,
      },
    });
  };

  return (
    <div className={styles.banner} role="status">
      <div className={styles.content}>
        <div className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Back to school</p>
            <h2>Tier 2 shopping is open</h2>
          </div>
          <button
            type="button"
            className={styles.dismissButton}
            onClick={onDismiss}
            disabled={dismissLoading}
            aria-label="Dismiss reminder"
          >
            Dismiss
          </button>
        </div>

        {commitment ? (
          <div className={styles.earnings}>
            <p>
              You&apos;ve earned <strong>{formatMoney(earnings)}</strong>
              {commitment.jobTitle ? ` from ${commitment.jobTitle}` : ''}.
            </p>
            <p className={styles.budget}>
              Tier 2 budget: {formatMoney(base)}
              {earnings > 0 ? ` + ${formatMoney(earnings)}` : ''} ={' '}
              <strong>{formatMoney(total)}</strong>
            </p>
          </div>
        ) : (
          <p className={styles.noBudget}>
            Your Tier 2 budget is ready
            {base > 0 ? (
              <>
                : <strong>{formatMoney(base)}</strong>
              </>
            ) : (
              '.'
            )}
          </p>
        )}

        <button
          type="button"
          className={styles.shopButton}
          onClick={handleShopTier2}
        >
          Shop Tier 2 now
        </button>
      </div>
    </div>
  );
}
