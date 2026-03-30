import React, { useCallback, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

export interface FeatureRatingProps {
  featureName: string;
  label?: string;
}

const FeatureRating: React.FC<FeatureRatingProps> = ({ featureName, label }) => {
  const { user } = useAuth();
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const send = useCallback(
    async (rating: 'up' | 'down') => {
      if (busy || done) return;
      setBusy(true);
      try {
        const res = await fetch('/api/feedback/feature-rating', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
          credentials: 'include',
          body: JSON.stringify({ feature_name: featureName, rating }),
        });
        if (res.ok) setDone(true);
      } catch {
        /* ignore */
      } finally {
        setBusy(false);
      }
    },
    [busy, done, featureName]
  );

  if (user?.is_beta !== true) return null;

  if (done) {
    return (
      <p className="text-xs text-gray-500 mt-2" role="status">
        Thanks for the feedback!
      </p>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-gray-500">
      {label ? <span className="text-gray-500">{label}</span> : null}
      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled={busy}
          onClick={() => send('up')}
          className="rounded-md px-2 py-1 text-base leading-none text-gray-400 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-violet-400 disabled:opacity-50"
          aria-label="Thumbs up"
        >
          👍
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => send('down')}
          className="rounded-md px-2 py-1 text-base leading-none text-gray-400 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-violet-400 disabled:opacity-50"
          aria-label="Thumbs down"
        >
          👎
        </button>
      </div>
    </div>
  );
};

export default FeatureRating;
