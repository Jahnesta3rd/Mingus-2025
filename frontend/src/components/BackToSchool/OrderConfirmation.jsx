import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './CheckoutUI.module.css';

/**
 * Post-payment confirmation for a completed BTS Tier 1 order.
 */
export default function OrderConfirmation({ orderId, sessionId, tier, total }) {
  const navigate = useNavigate();
  const shortId = orderId
    ? `${String(orderId).slice(0, 8).toUpperCase()}…`
    : '—';

  return (
    <div className={styles.container}>
      <div className={styles.confirmation}>
        <p className={styles.eyebrow}>Back to school</p>
        <div className={styles.successIcon} aria-hidden="true">
          Done
        </div>
        <h1 className={styles.heading}>Order confirmed</h1>
        <div className={styles.orderDetails}>
          <p>
            <strong>Order ID:</strong> {shortId}
          </p>
          <p>
            <strong>Tier:</strong> Tier {tier}
          </p>
          <p>
            <strong>Amount:</strong> ${Number(total).toFixed(2)}
          </p>
        </div>
        <div className={styles.nextSteps}>
          <h2>What&apos;s next</h2>
          <ul>
            <li>Your Tier {tier} order is confirmed</li>
            <li>Watch for a shipping confirmation email</li>
            <li>Tier 2 shopping opens closer to school start</li>
          </ul>
        </div>
        <div className={styles.actions}>
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className={styles.primaryButton}
          >
            Back to dashboard
          </button>
          <button
            type="button"
            onClick={() => navigate(`/bts/${sessionId}/plan`)}
            className={styles.secondaryButton}
          >
            View shopping plan
          </button>
        </div>
      </div>
    </div>
  );
}
