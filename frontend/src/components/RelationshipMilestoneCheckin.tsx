import React, { useCallback, useState } from 'react';
import { AlertTriangle, Loader2, Shield } from 'lucide-react';
import {
  DV_RESOURCES,
  getQuarterlyReassessment,
  submitRelationshipCheckin,
  type FeelsSafe,
  type QuarterlyReassessmentResponse,
  type RelationshipCheckinResponse,
  type VibeTrend,
} from '../api/relationshipCheckinAPI';
import { useAuth } from '../hooks/useAuth';

export interface RelationshipMilestoneCheckinProps {
  personId: string;
  partnerName?: string;
  className?: string;
}

type ViewMode = 'survey' | 'results' | 'quarterly';

const VIBE_OPTIONS: { value: VibeTrend; label: string }[] = [
  { value: 'improving', label: 'Improving' },
  { value: 'stable', label: 'Stable' },
  { value: 'declining', label: 'Declining' },
];

const SAFETY_OPTIONS: { value: FeelsSafe; label: string }[] = [
  { value: 'yes', label: 'Yes, I feel safe' },
  { value: 'mostly', label: 'Mostly safe' },
  { value: 'sometimes', label: 'Sometimes unsafe' },
  { value: 'no', label: 'No, I do not feel safe' },
  { value: 'unsafe', label: 'I feel unsafe right now' },
];

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    emergency: 'bg-red-100 text-red-800 border-red-200',
    accelerate: 'bg-orange-100 text-orange-800 border-orange-200',
    on_track: 'bg-green-100 text-green-800 border-green-200',
    improving: 'bg-blue-100 text-blue-800 border-blue-200',
  };
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-sm font-semibold capitalize ${
        styles[status] ?? 'bg-gray-100 text-gray-800'
      }`}
    >
      {status.replace('_', ' ')}
    </span>
  );
}

function EmergencyResources({ compact = false }: { compact?: boolean }) {
  return (
    <section
      className={`rounded-xl border border-red-200 bg-red-50/60 ${
        compact ? 'p-3' : 'p-4'
      }`}
      aria-label="Emergency safety resources"
    >
      <div className="mb-2 flex items-center gap-2 text-red-800">
        <Shield size={18} aria-hidden />
        <h3 className="text-sm font-semibold">Safety resources (always available)</h3>
      </div>
      <p className="mb-3 text-xs text-red-700">
        If you are in immediate danger, call 911. This form does not track your location.
      </p>
      <ul className="space-y-2 text-sm">
        {DV_RESOURCES.map((resource) => (
          <li key={resource.name} className="rounded-lg bg-white/80 px-3 py-2">
            <p className="font-medium text-gray-900">{resource.name}</p>
            {resource.phone ? (
              <p className="text-gray-700">
                <a href={`tel:${resource.phone.replace(/\D/g, '')}`} className="underline">
                  {resource.phone}
                </a>
              </p>
            ) : null}
            {resource.url ? (
              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-orange-700 underline"
              >
                Open resource
              </a>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function RelationshipMilestoneCheckin({
  personId,
  partnerName = 'your partner',
  className = '',
}: RelationshipMilestoneCheckinProps) {
  const { getAccessToken } = useAuth();
  const [view, setView] = useState<ViewMode>('survey');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RelationshipCheckinResponse | null>(null);
  const [quarterly, setQuarterly] = useState<QuarterlyReassessmentResponse | null>(null);

  const [vibeTrend, setVibeTrend] = useState<VibeTrend>('stable');
  const [feelsSafe, setFeelsSafe] = useState<FeelsSafe>('mostly');
  const [needsToLeaveSooner, setNeedsToLeaveSooner] = useState(false);
  const [onTrackSavings, setOnTrackSavings] = useState(true);
  const [preferLeaveNow, setPreferLeaveNow] = useState(false);

  const handleSubmit = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await submitRelationshipCheckin(
        {
          personId,
          vibeTrend,
          feelsSafe,
          needsToLeaveSooner,
          onTrackSavings,
          preferLeaveNow,
        },
        { getAccessToken },
      );
      setResult(payload);
      setView('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit check-in.');
    } finally {
      setIsLoading(false);
    }
  }, [
    feelsSafe,
    getAccessToken,
    needsToLeaveSooner,
    onTrackSavings,
    personId,
    preferLeaveNow,
    vibeTrend,
  ]);

  const loadQuarterly = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await getQuarterlyReassessment(personId, { getAccessToken });
      setQuarterly(payload);
      setView('quarterly');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load quarterly report.');
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken, personId]);

  if (view === 'quarterly' && quarterly) {
    return (
      <section
        className={`rounded-2xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}
        aria-label="Quarterly reassessment"
      >
        <h2 className="text-lg font-semibold text-gray-900">Quarterly reassessment</h2>
        <p className="mt-1 text-sm text-gray-600">
          Progress with {quarterly.partner_name ?? partnerName} over the last 3 months.
        </p>

        {quarterly.vibe_scores.length > 0 ? (
          <div className="mt-4 rounded-xl border border-gray-100 bg-gray-50 p-4">
            <p className="text-sm font-medium text-gray-700">Vibe trend (emotional scores)</p>
            <p className="mt-1 font-mono text-sm text-gray-900">
              {quarterly.vibe_scores.join(' → ')}
            </p>
          </div>
        ) : null}

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-gray-100 p-4">
            <p className="text-xs uppercase text-gray-500">Original timeline</p>
            <p className="text-2xl font-bold text-gray-900">
              {quarterly.timeline.original_months ?? '—'} mo
            </p>
          </div>
          <div className="rounded-xl border border-orange-100 bg-orange-50 p-4">
            <p className="text-xs uppercase text-orange-700">Current timeline</p>
            <p className="text-2xl font-bold text-orange-800">
              {quarterly.timeline.current_months ?? '—'} mo
            </p>
          </div>
        </div>

        {quarterly.progress_notes.length > 0 ? (
          <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-gray-700">
            {quarterly.progress_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        ) : null}

        {quarterly.improvement_path?.available ? (
          <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="font-medium text-blue-900">Your vibe is improving</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-blue-800">
              {quarterly.improvement_path.options.map((opt) => (
                <li key={opt}>{opt}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-5 flex gap-2">
          <button
            type="button"
            onClick={() => setView('survey')}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700"
          >
            New monthly check-in
          </button>
        </div>

        <div className="mt-5">
          <EmergencyResources compact />
        </div>
      </section>
    );
  }

  if (view === 'results' && result) {
    return (
      <section
        className={`rounded-2xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}
        aria-label="Check-in results"
      >
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-900">Monthly readiness</h2>
          <StatusBadge status={result.status} />
        </div>

        {result.emergency_alert ? (
          <div
            className="mt-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
            role="alert"
          >
            <AlertTriangle className="mt-0.5 shrink-0" size={18} aria-hidden />
            <div>
              <p className="font-semibold">Emergency exit recommended</p>
              <p className="mt-1">
                Your safety comes first. Use the resources below and consider Tier 0 emergency
                exit planning.
              </p>
            </div>
          </div>
        ) : null}

        <div className="mt-4">
          <h3 className="text-sm font-semibold text-gray-900">Next steps</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
            {result.next_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void loadQuarterly()}
            className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white"
          >
            View quarterly report
          </button>
          <button
            type="button"
            onClick={() => setView('survey')}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700"
          >
            Retake check-in
          </button>
        </div>

        <div className="mt-5">
          <EmergencyResources />
        </div>
      </section>
    );
  }

  return (
    <section
      className={`rounded-2xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}
      aria-label="Monthly relationship milestone check-in"
    >
      <h2 className="text-lg font-semibold text-gray-900">Monthly readiness check-in</h2>
      <p className="mt-1 text-sm text-gray-600">
        Private monthly check-in about your situation with {partnerName}. Answers are stored
        securely for your planning only.
      </p>

      <div className="mt-4">
        <EmergencyResources compact />
      </div>

      <form
        className="mt-5 space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit();
        }}
      >
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-gray-800">
            1. How is your vibe trend with {partnerName}?
          </legend>
          <div className="space-y-2">
            {VIBE_OPTIONS.map((opt) => (
              <label key={opt.value} className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="vibe-trend"
                  value={opt.value}
                  checked={vibeTrend === opt.value}
                  onChange={() => setVibeTrend(opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-gray-800">
            2. Do you feel safe at home?
          </legend>
          <div className="space-y-2">
            {SAFETY_OPTIONS.map((opt) => (
              <label key={opt.value} className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="feels-safe"
                  value={opt.value}
                  checked={feelsSafe === opt.value}
                  onChange={() => setFeelsSafe(opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-gray-800">
            3. Do you need to leave sooner than planned?
          </legend>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="leave-sooner"
                checked={needsToLeaveSooner}
                onChange={() => setNeedsToLeaveSooner(true)}
              />
              Yes
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="leave-sooner"
                checked={!needsToLeaveSooner}
                onChange={() => setNeedsToLeaveSooner(false)}
              />
              No
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-gray-800">
            4. Are you on track with savings for independence?
          </legend>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="on-track"
                checked={onTrackSavings}
                onChange={() => setOnTrackSavings(true)}
              />
              Yes
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="on-track"
                checked={!onTrackSavings}
                onChange={() => setOnTrackSavings(false)}
              />
              No
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-medium text-gray-800">
            5. Would you prefer to leave now if you could?
          </legend>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="prefer-leave"
                checked={preferLeaveNow}
                onChange={() => setPreferLeaveNow(true)}
              />
              Yes
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="prefer-leave"
                checked={!preferLeaveNow}
                onChange={() => setPreferLeaveNow(false)}
              />
              No
            </label>
          </div>
        </fieldset>

        {error ? (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <button
            type="submit"
            disabled={isLoading}
            className="rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
          >
            {isLoading ? 'Submitting...' : 'Submit monthly check-in'}
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => void loadQuarterly()}
            className="rounded-lg border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700"
          >
            Quarterly report
          </button>
        </div>
      </form>

      {isLoading ? (
        <div className="mt-3 flex items-center gap-2 text-sm text-gray-500" role="status">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          Loading...
        </div>
      ) : null}
    </section>
  );
}
