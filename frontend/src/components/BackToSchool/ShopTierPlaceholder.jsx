import React from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

/**
 * Placeholder until BTS6 Product Picker ships.
 * Receives navigation state from PurchasePlanView.
 */
export default function ShopTierPlaceholder() {
  const { sessionId, tier } = useParams();
  const location = useLocation();
  const state = location.state || {};

  return (
    <div
      style={{
        maxWidth: '40rem',
        margin: '0 auto',
        padding: '1.5rem 1.25rem',
      }}
    >
      <p
        style={{
          margin: '0 0 0.35rem',
          fontSize: '0.75rem',
          fontWeight: 600,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color: 'var(--mingus-purple, #583fbc)',
        }}
      >
        Back to school
      </p>
      <h1
        style={{
          margin: '0 0 0.5rem',
          fontFamily: 'Fraunces, Georgia, serif',
          fontSize: '1.75rem',
          color: 'var(--ink, #1a1a2e)',
        }}
      >
        Shop Tier {tier}
      </h1>
      <p style={{ color: 'var(--ink-mid, #5c5c7a)', lineHeight: 1.45 }}>
        Product picker (BTS6) is next. Session{' '}
        <code>{sessionId}</code>
        {state.budget != null ? ` · budget $${state.budget}` : null}
        {Array.isArray(state.items) ? ` · ${state.items.length} categories` : null}.
      </p>
      <p style={{ marginTop: '1.25rem' }}>
        <Link
          to={`/bts/${sessionId}/plan`}
          style={{ color: 'var(--mingus-purple, #583fbc)', fontWeight: 600 }}
        >
          Back to plan
        </Link>
      </p>
    </div>
  );
}
