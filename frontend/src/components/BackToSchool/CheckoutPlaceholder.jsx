import React from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

/**
 * Placeholder until BTS9 checkout orchestrator ships.
 */
export default function CheckoutPlaceholder() {
  const { sessionId } = useParams();
  const location = useLocation();
  const state = location.state || {};
  const tier = state.tier ?? state.tierKey ?? '—';
  const total = state.total;
  const budget = state.budget;

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
        Checkout
      </h1>
      <p style={{ color: 'var(--ink-mid, #5c5c7a)', lineHeight: 1.45 }}>
        Checkout orchestrator (BTS9) is next. Session <code>{sessionId}</code>
        {tier != null ? ` · tier ${tier}` : null}
        {total != null ? ` · cart $${Number(total).toFixed(2)}` : null}
        {budget != null ? ` · budget $${Number(budget).toFixed(2)}` : null}.
      </p>
      <p style={{ marginTop: '1.25rem' }}>
        <Link
          to={`/bts/${sessionId}/shop/${state.tierKey || state.tier || 1}`}
          style={{ color: 'var(--mingus-purple, #583fbc)', fontWeight: 600 }}
        >
          Back to shopping
        </Link>
      </p>
    </div>
  );
}
