import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Tier2DecisionUI from './Tier2DecisionUI';
import styles from './Tier2PurchaseReminder.module.css';

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
 * Shown when Tier 2 purchase date has arrived and a job commitment exists.
 */
export default function Tier2PurchaseReminder({
  sessionId,
  tier2Status,
  onDecision,
}) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  if (!tier2Status || tier2Status.status === 'no_commitment') return null;
  if (!tier2Status.dateReached) return null;

  const {
    jobTitle,
    targetEarnings,
    actualEarnings,
    progressPercent,
    tier2BaseBudget,
    tier2BudgetWithEarnings,
    earningsGoalMet,
  } = tier2Status;

  const handleProceed = async () => {
    setLoading(true);
    try {
      await onDecision?.('proceed');
      navigate(`/bts/${sessionId}/shop/2`, {
        state: {
          tier: 2,
          tierKey: 'tier2',
          budget: tier2BudgetWithEarnings,
          commitment: { jobTitle, actualEarnings },
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDefer = async () => {
    setLoading(true);
    try {
      await onDecision?.('defer');
      setMessage('Tier 2 deferred. Come back when you are ready to shop.');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    setLoading(true);
    try {
      await onDecision?.('skip');
      setMessage('Tier 2 skipped. You can still shop Tier 3 later if budget allows.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <p className={styles.eyebrow}>Tier 2 ready</p>
        <h2>Time to shop Tier 2</h2>

        <div className={styles.earnings}>
          <div className={styles.stat}>
            <span className={styles.label}>Side job</span>
            <span className={styles.value}>{jobTitle}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.label}>Earnings progress</span>
            <span className={styles.value}>
              {formatMoney(actualEarnings)} / {formatMoney(targetEarnings)}
            </span>
          </div>
          <div
            className={styles.progressBar}
            role="progressbar"
            aria-valuenow={Math.round(Number(progressPercent) || 0)}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={styles.progress}
              style={{
                width: `${Math.min(Number(progressPercent) || 0, 100)}%`,
              }}
            />
          </div>
        </div>

        <div className={styles.budget}>
          <h3>Your Tier 2 budget</h3>
          <div className={styles.breakdown}>
            <div className={styles.row}>
              <span>Base budget</span>
              <span>{formatMoney(tier2BaseBudget)}</span>
            </div>
            <div className={styles.row}>
              <span>Job earnings</span>
              <span className={styles.earningsValue}>
                + {formatMoney(actualEarnings)}
              </span>
            </div>
            <div className={`${styles.row} ${styles.total}`}>
              <span>Total available</span>
              <span>{formatMoney(tier2BudgetWithEarnings)}</span>
            </div>
          </div>
        </div>

        {earningsGoalMet ? (
          <p className={styles.success}>
            You met your earnings goal. Budget is now{' '}
            {formatMoney(tier2BudgetWithEarnings)}.
          </p>
        ) : (
          <p className={styles.partial}>
            You earned {formatMoney(actualEarnings)} toward your goal. You can
            still shop with this amount.
          </p>
        )}

        {message ? <p className={styles.message}>{message}</p> : null}

        {!message ? (
          <Tier2DecisionUI
            onProceed={handleProceed}
            onDefer={handleDefer}
            onSkip={handleSkip}
            loading={loading}
          />
        ) : null}
      </div>
    </div>
  );
}
