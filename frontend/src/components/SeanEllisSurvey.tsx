import React, { useEffect, useState } from 'react';
import { csrfHeaders } from '../utils/csrfHeaders';

const OPTIONS = [
  { label: 'Very disappointed', value: 'very_disappointed' },
  { label: 'Somewhat disappointed', value: 'somewhat_disappointed' },
  { label: 'Not disappointed', value: 'not_disappointed' },
  { label: 'I no longer use it', value: 'no_longer_use' },
] as const;

export interface SeanEllisSurveyProps {
  onDismiss: () => void;
  onSubmitted: () => void;
}

const SeanEllisSurvey: React.FC<SeanEllisSurveyProps> = ({ onDismiss, onSubmitted }) => {
  const [visible, setVisible] = useState(false);
  const [phase, setPhase] = useState<'survey' | 'thanks'>('survey');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setVisible(true), 3000);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (phase !== 'thanks') return;
    const timer = window.setTimeout(() => {
      onSubmitted();
    }, 2000);
    return () => window.clearTimeout(timer);
  }, [phase, onSubmitted]);

  const submit = async (response: string) => {
    setError(null);
    setSubmitting(true);
    try {
      const token = localStorage.getItem('mingus_token');
      const res = await fetch('/api/feedback/sean-ellis', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ response }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError((data as { error?: string }).error || 'Something went wrong, try again');
        setSubmitting(false);
        return;
      }
      setPhase('thanks');
    } catch {
      setError('Something went wrong, try again');
    } finally {
      setSubmitting(false);
    }
  };

  if (!visible) return null;

  if (phase === 'thanks') {
    return (
      <div
        className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sean-ellis-thanks-title"
      >
        <div className="w-full max-w-md rounded-2xl bg-white border border-gray-200 shadow-xl p-6 text-center">
          <h2 id="sean-ellis-thanks-title" className="text-lg font-semibold text-gray-900">
            Thanks — your feedback shapes what we build next.
          </h2>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sean-ellis-modal-title"
    >
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white border border-gray-200 shadow-xl">
        <div className="sticky top-0 z-10 border-b border-gray-100 bg-white px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <h2 id="sean-ellis-modal-title" className="text-base font-semibold text-gray-900">
              Quick question
            </h2>
            <button
              type="button"
              onClick={onDismiss}
              className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
              aria-label="Close survey"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-700">
            How would you feel if you could no longer use Mingus?
          </p>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <div className="space-y-2">
            {OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                disabled={submitting}
                onClick={() => submit(opt.value)}
                className="w-full rounded-lg border border-gray-200 bg-white px-4 py-3 text-left text-sm font-medium text-gray-800 transition-colors hover:border-violet-300 hover:bg-violet-50 disabled:opacity-40"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SeanEllisSurvey;
