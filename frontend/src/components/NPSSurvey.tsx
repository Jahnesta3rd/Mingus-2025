import React, { useCallback, useMemo, useState } from 'react';
import { csrfHeaders } from '../utils/csrfHeaders';

export const NPS_FEATURE_OPTIONS = [
  { value: 'wellness_finance_correlation', label: 'Wellness-Finance Correlation' },
  { value: 'vehicle_analytics', label: 'Vehicle Analytics' },
  { value: 'housing_intelligence', label: 'Housing Intelligence' },
  { value: 'financial_dashboard', label: 'Financial Dashboard' },
  { value: 'assessments', label: 'Assessments' },
  { value: 'other', label: 'Other' },
] as const;

type Phase = 'nps' | 'most' | 'least' | 'pay' | 'price' | 'comments' | 'thanks';

export interface NPSSurveyProps {
  onDismiss: () => void;
}

const NPSSurvey: React.FC<NPSSurveyProps> = ({ onDismiss }) => {
  const [phase, setPhase] = useState<Phase>('nps');
  const [score, setScore] = useState<number | null>(null);
  const [mostValuable, setMostValuable] = useState('');
  const [leastValuable, setLeastValuable] = useState('');
  const [wouldPay, setWouldPay] = useState<'yes' | 'maybe' | 'no' | ''>('');
  const [priceChoice, setPriceChoice] = useState<15 | 35 | 100 | 'other' | null>(null);
  const [otherPrice, setOtherPrice] = useState('');
  const [additionalComments, setAdditionalComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const needsPriceStep = wouldPay === 'yes' || wouldPay === 'maybe';

  const { stepIndex, totalSteps } = useMemo(() => {
    const order: Phase[] = ['nps', 'most', 'least', 'pay'];
    if (needsPriceStep) order.push('price');
    order.push('comments');
    const idx = order.indexOf(phase === 'thanks' ? 'comments' : phase);
    return { stepIndex: Math.max(0, idx), totalSteps: order.length };
  }, [phase, needsPriceStep]);

  const progressPct = totalSteps > 0 ? ((stepIndex + 1) / totalSteps) * 100 : 0;

  const goNextFromPay = useCallback(() => {
    if (wouldPay === 'yes' || wouldPay === 'maybe') setPhase('price');
    else setPhase('comments');
  }, [wouldPay]);

  const advance = () => {
    setError(null);
    if (phase === 'nps') {
      if (score === null) return;
      setPhase('most');
    } else if (phase === 'most') {
      if (!mostValuable) return;
      setPhase('least');
    } else if (phase === 'least') {
      if (!leastValuable) return;
      setPhase('pay');
    } else if (phase === 'pay') {
      if (!wouldPay) return;
      goNextFromPay();
    } else if (phase === 'price') {
      if (priceChoice === null) return;
      if (priceChoice === 'other') {
        const n = parseInt(otherPrice, 10);
        if (Number.isNaN(n) || n < 0) {
          setError('Enter a valid dollar amount.');
          return;
        }
      }
      setPhase('comments');
    }
  };

  const resolvePriceWilling = (): number | null => {
    if (!needsPriceStep) return null;
    if (priceChoice === 15 || priceChoice === 35 || priceChoice === 100) return priceChoice;
    if (priceChoice === 'other') {
      const n = parseInt(otherPrice, 10);
      return Number.isNaN(n) ? null : n;
    }
    return null;
  };

  const submit = async () => {
    if (score === null) return;
    setError(null);
    setSubmitting(true);
    const body: Record<string, unknown> = {
      score,
      most_valuable_feature: mostValuable || undefined,
      least_valuable_feature: leastValuable || undefined,
      would_pay: wouldPay || undefined,
      price_willing: resolvePriceWilling() ?? undefined,
      additional_comments: additionalComments.trim() || undefined,
    };
    try {
      const res = await fetch('/api/feedback/nps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
        credentials: 'include',
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409) {
        setSubmitting(false);
        onDismiss();
        return;
      }
      if (!res.ok) {
        setError((data as { error?: string }).error || 'Something went wrong');
        setSubmitting(false);
        return;
      }
      setPhase('thanks');
    } catch {
      setError('Network error');
    } finally {
      setSubmitting(false);
    }
  };

  if (phase === 'thanks') {
    return (
      <div
        className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="nps-thanks-title"
      >
        <div className="w-full max-w-md rounded-2xl bg-white border border-gray-200 shadow-xl p-6 text-center">
          <h2 id="nps-thanks-title" className="text-lg font-semibold text-gray-900">
            Thank you!
          </h2>
          <p className="mt-2 text-sm text-gray-600">Your feedback helps us improve Mingus.</p>
          <button
            type="button"
            className="mt-6 w-full rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700"
            onClick={onDismiss}
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="nps-modal-title"
    >
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-white border border-gray-200 shadow-xl">
        <div className="sticky top-0 z-10 border-b border-gray-100 bg-white px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <h2 id="nps-modal-title" className="text-base font-semibold text-gray-900">
              Quick feedback
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
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-violet-500 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className="p-4 space-y-4">
          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          {phase === 'nps' && (
            <div>
              <p className="text-sm text-gray-700 mb-3">
                How likely are you to recommend Mingus to a friend or colleague?
              </p>
              <div className="flex flex-wrap gap-1 justify-center">
                {Array.from({ length: 11 }, (_, i) => i).map((n) => {
                  let tone = 'bg-red-100 text-red-900 hover:bg-red-200 border-red-200';
                  if (n >= 7 && n <= 8)
                    tone = 'bg-amber-100 text-amber-900 hover:bg-amber-200 border-amber-200';
                  if (n >= 9)
                    tone = 'bg-emerald-100 text-emerald-900 hover:bg-emerald-200 border-emerald-200';
                  return (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setScore(n)}
                      className={`h-9 w-9 rounded-md border text-sm font-medium transition-colors ${
                        score === n ? 'ring-2 ring-violet-500 ring-offset-2' : ''
                      } ${tone}`}
                    >
                      {n}
                    </button>
                  );
                })}
              </div>
              <button
                type="button"
                disabled={score === null}
                onClick={advance}
                className="mt-4 w-full rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}

          {phase === 'most' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Which feature have you found most valuable so far?
              </label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={mostValuable}
                onChange={(e) => setMostValuable(e.target.value)}
              >
                <option value="">Select…</option>
                {NPS_FEATURE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={!mostValuable}
                onClick={advance}
                className="mt-4 w-full rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}

          {phase === 'least' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Which feature felt least useful or was confusing?
              </label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={leastValuable}
                onChange={(e) => setLeastValuable(e.target.value)}
              >
                <option value="">Select…</option>
                {NPS_FEATURE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={!leastValuable}
                onClick={advance}
                className="mt-4 w-full rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}

          {phase === 'pay' && (
            <div>
              <p className="text-sm text-gray-700 mb-3">After the beta, would you pay for Mingus?</p>
              <div className="flex flex-wrap gap-2">
                {(['yes', 'maybe', 'no'] as const).map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setWouldPay(v)}
                    className={`flex-1 min-w-[4rem] rounded-lg border px-3 py-2 text-sm font-medium capitalize ${
                      wouldPay === v
                        ? 'border-violet-600 bg-violet-50 text-violet-900'
                        : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
              <button
                type="button"
                disabled={!wouldPay}
                onClick={advance}
                className="mt-4 w-full rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}

          {phase === 'price' && (
            <div>
              <p className="text-sm text-gray-700 mb-3">What monthly price feels right to you?</p>
              <div className="flex flex-wrap gap-2">
                {([15, 35, 100] as const).map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => {
                      setPriceChoice(amt);
                      setOtherPrice('');
                    }}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium ${
                      priceChoice === amt
                        ? 'border-violet-600 bg-violet-50 text-violet-900'
                        : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    ${amt}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setPriceChoice('other')}
                  className={`rounded-lg border px-3 py-2 text-sm font-medium ${
                    priceChoice === 'other'
                      ? 'border-violet-600 bg-violet-50 text-violet-900'
                      : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Other
                </button>
              </div>
              {priceChoice === 'other' && (
                <input
                  type="number"
                  min={0}
                  placeholder="Amount per month ($)"
                  className="mt-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={otherPrice}
                  onChange={(e) => setOtherPrice(e.target.value)}
                />
              )}
              <button
                type="button"
                onClick={advance}
                className="mt-4 w-full rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-700"
              >
                Next
              </button>
            </div>
          )}

          {phase === 'comments' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Any other feedback for the team? <span className="font-normal text-gray-500">(optional)</span>
              </label>
              <textarea
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm min-h-[100px]"
                maxLength={500}
                placeholder="Share anything else…"
                value={additionalComments}
                onChange={(e) => setAdditionalComments(e.target.value)}
              />
              <p className="text-xs text-gray-400 mt-1">{additionalComments.length}/500</p>
              <button
                type="button"
                disabled={submitting}
                onClick={() => submit()}
                className="mt-4 w-full rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-40"
              >
                {submitting ? 'Submitting…' : 'Submit'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NPSSurvey;
