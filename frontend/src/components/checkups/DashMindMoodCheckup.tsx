import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import {
  CHECKUPS_HUB_PATH,
  authJsonHeaders,
  formatRelativeLastUpdate,
  submitMindMoodCheckin,
  type MindMoodPayload,
} from './checkupShared';
import { useAuth } from '../../hooks/useAuth';

const MOOD_EMOJIS = [
  { value: 1, emoji: '😔', label: 'Very low' },
  { value: 2, emoji: '😟', label: 'Low' },
  { value: 3, emoji: '😐', label: 'Neutral' },
  { value: 4, emoji: '🙂', label: 'Good' },
  { value: 5, emoji: '😄', label: 'Great' },
] as const;

const TRIGGER_OPTIONS = [
  { value: 'yes', label: 'Yes, something was going on' },
  { value: 'no', label: "No, I don't think so" },
  { value: 'unsure', label: "I'm not sure" },
] as const;

const COPING_OPTIONS = [
  'Exercise',
  'Talking to someone',
  'Prayer or meditation',
  'Time outside',
  'Nothing worked',
  'Other',
] as const;

type WeeklyCheckinRow = {
  completed_at?: string | null;
  overall_mood?: number | null;
};

/**
 * Mind & Mood check-in — standalone question set (#170).
 * Does NOT use VibeCheckPage (legacy daily meme, stub backend).
 * Submit: POST /api/checkups/mind-mood → upserts WeeklyCheckin mood fields for current week.
 */
export function DashMindMoodCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [step, setStep] = useState(0);
  const [moodRating, setMoodRating] = useState<number | null>(null);
  const [stressLevel, setStressLevel] = useState(3);
  const [triggerPurchase, setTriggerPurchase] = useState<string | null>(null);
  const [avoidedFinances, setAvoidedFinances] = useState<boolean | null>(null);
  const [copingMethods, setCopingMethods] = useState<string[]>([]);
  const [spendingIntentionality, setSpendingIntentionality] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [lastCompletedAt, setLastCompletedAt] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    (async () => {
      setHistoryLoading(true);
      try {
        const res = await fetch('/api/wellness/checkin/current-week', {
          credentials: 'include',
          headers: authJsonHeaders(),
        });
        if (res.ok) {
          const row = (await res.json()) as WeeklyCheckinRow;
          if (!cancelled && row?.overall_mood != null && row.completed_at) {
            setLastCompletedAt(row.completed_at);
          }
        }
      } catch {
        /* optional */
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const toggleCoping = (label: string) => {
    setCopingMethods((prev) =>
      prev.includes(label) ? prev.filter((x) => x !== label) : [...prev, label]
    );
  };

  const canAdvance = (): boolean => {
    switch (step) {
      case 0:
        return moodRating != null;
      case 1:
        return true;
      case 2:
        return triggerPurchase != null;
      case 3:
        return avoidedFinances != null;
      case 4:
        return copingMethods.length > 0;
      case 5:
        return true;
      default:
        return false;
    }
  };

  const submit = useCallback(async () => {
    if (moodRating == null || triggerPurchase == null || avoidedFinances == null) return;
    setBusy(true);
    setError(null);
    const payload: MindMoodPayload = {
      mood_rating: moodRating,
      stress_level: stressLevel,
      mood_stress_triggered_purchase: triggerPurchase,
      mood_avoided_finances: avoidedFinances,
      mood_coping_methods: copingMethods,
      spending_intentionality_rating: spendingIntentionality,
    };
    try {
      await submitMindMoodCheckin(payload);
      setSuccessMessage('Check-in saved');
      window.setTimeout(() => {
        navigate(CHECKUPS_HUB_PATH, { replace: true });
      }, 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [
    avoidedFinances,
    copingMethods,
    moodRating,
    navigate,
    spendingIntentionality,
    stressLevel,
    triggerPurchase,
  ]);

  const next = () => {
    if (step < 5) {
      if (canAdvance()) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const relative = formatRelativeLastUpdate(lastCompletedAt);

  return (
    <CheckupWrapperShell
      title="Mind & Mood Check-in"
      score={null}
      lastCompletedAt={lastCompletedAt}
      loading={historyLoading}
      error={error}
      successMessage={successMessage}
    >
      {!successMessage ? (
        <div
          className="dash-checkup-theme space-y-6 rounded-2xl border bg-white p-6 shadow-sm sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--ink-mid)' }}>
            Question {step + 1} of 6
          </p>

          {step === 0 ? (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold">What&apos;s your overall mood been this week?</h2>
              <div className="flex flex-wrap justify-center gap-3">
                {MOOD_EMOJIS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setMoodRating(opt.value)}
                    className={`flex min-h-16 min-w-16 flex-col items-center justify-center rounded-xl border-2 px-3 py-2 text-2xl transition ${
                      moodRating === opt.value ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)]' : ''
                    }`}
                    style={{ borderColor: moodRating === opt.value ? undefined : 'var(--line)' }}
                    aria-pressed={moodRating === opt.value}
                    aria-label={opt.label}
                  >
                    {opt.emoji}
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          {step === 1 ? (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold">
                How would you rate your stress level this week?
              </h2>
              <div className="flex justify-between text-xs" style={{ color: 'var(--ink-mid)' }}>
                <span>Calm</span>
                <span>Overwhelmed</span>
              </div>
              <input
                type="range"
                min={1}
                max={5}
                step={1}
                value={stressLevel}
                onChange={(e) => setStressLevel(Number(e.target.value))}
                className="w-full accent-[var(--mingus-purple)]"
                aria-valuemin={1}
                aria-valuemax={5}
                aria-valuenow={stressLevel}
              />
              <p className="text-center text-sm font-medium">{stressLevel} / 5</p>
            </section>
          ) : null}

          {step === 2 ? (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold leading-snug">
                Think back to the last time you bought something you didn&apos;t plan to. What was going on for you
                right before — even subtle things like feeling overlooked at work, scrolling past something that made
                you feel behind, or just a quiet restless feeling you couldn&apos;t name? (That counts.)
              </h2>
              <div className="space-y-2">
                {TRIGGER_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setTriggerPurchase(opt.value)}
                    className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition ${
                      triggerPurchase === opt.value
                        ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)] font-medium'
                        : ''
                    }`}
                    style={{ borderColor: triggerPurchase === opt.value ? undefined : 'var(--line)' }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          {step === 3 ? (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold leading-snug">
                Did you avoid looking at your finances at any point this week — not opening the app, skipping a
                statement, or putting off a money decision?
              </h2>
              <div className="flex gap-3">
                {[true, false].map((val) => (
                  <button
                    key={String(val)}
                    type="button"
                    onClick={() => setAvoidedFinances(val)}
                    className={`min-h-11 flex-1 rounded-xl border px-4 py-3 text-sm font-medium transition ${
                      avoidedFinances === val
                        ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)]'
                        : ''
                    }`}
                    style={{ borderColor: avoidedFinances === val ? undefined : 'var(--line)' }}
                  >
                    {val ? 'Yes' : 'No'}
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          {step === 4 ? (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold">
                What helped you manage your energy or stress this week, if anything?
              </h2>
              <p className="text-xs" style={{ color: 'var(--ink-mid)' }}>
                Select all that apply
              </p>
              <div className="flex flex-wrap gap-2">
                {COPING_OPTIONS.map((label) => {
                  const active = copingMethods.includes(label);
                  return (
                    <button
                      key={label}
                      type="button"
                      onClick={() => toggleCoping(label)}
                      className={`rounded-full border px-4 py-2 text-sm transition ${
                        active ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)] font-medium' : ''
                      }`}
                      style={{ borderColor: active ? undefined : 'var(--line)' }}
                      aria-pressed={active}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </section>
          ) : null}

          {step === 5 ? (
            <section className="space-y-4">
              <h2 className="font-display text-lg font-semibold">
                How intentional were your spending decisions this week?
              </h2>
              <div className="flex justify-between text-xs" style={{ color: 'var(--ink-mid)' }}>
                <span>All reactive</span>
                <span>All intentional</span>
              </div>
              <input
                type="range"
                min={1}
                max={5}
                step={1}
                value={spendingIntentionality}
                onChange={(e) => setSpendingIntentionality(Number(e.target.value))}
                className="w-full accent-[var(--mingus-purple)]"
              />
              <p className="text-center text-sm font-medium">{spendingIntentionality} / 5</p>
            </section>
          ) : null}

          <div className="flex gap-3 pt-2">
            {step > 0 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                disabled={busy}
                className="min-h-11 flex-1 rounded-xl border px-4 py-3 text-sm font-medium"
                style={{ borderColor: 'var(--line)' }}
              >
                Back
              </button>
            ) : null}
            <button
              type="button"
              onClick={next}
              disabled={busy || !canAdvance()}
              className="dash-checkup-primary min-h-11 flex-1 rounded-xl px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"
              style={{ background: 'var(--mingus-purple)' }}
            >
              {busy ? 'Saving…' : step === 5 ? 'Save check-in' : 'Continue'}
            </button>
          </div>

          {relative ? (
            <p className="text-center text-xs" style={{ color: 'var(--ink-mid)' }}>
              Previous mood check-in: {relative}
            </p>
          ) : null}
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashMindMoodCheckup;
