import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import {
  CHECKUPS_HUB_PATH,
  formatRelativeLastUpdate,
  submitMindMoodCheckin,
} from './checkupShared';
import {
  MultiSelectChips,
  OptionButtons,
  RangeStep,
  StepLabel,
  StepNav,
  StepTitle,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';

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

/**
 * Mind & Mood check-in — 4-question set (#170) → LifeLedgerProfile.
 */
export function DashMindMoodCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { profile, loading: profileLoading } = useLifeLedger(isAuthenticated);
  const [step, setStep] = useState(0);
  const [triggerPurchase, setTriggerPurchase] = useState<string | null>(null);
  const [avoidedFinances, setAvoidedFinances] = useState<boolean | null>(null);
  const [copingMethods, setCopingMethods] = useState<string[]>([]);
  const [spendingIntentionality, setSpendingIntentionality] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const totalSteps = 4;

  const toggleCoping = (label: string) => {
    setCopingMethods((prev) =>
      prev.includes(label) ? prev.filter((x) => x !== label) : [...prev, label]
    );
  };

  const canAdvance = useMemo(() => {
    switch (step) {
      case 0:
        return triggerPurchase != null;
      case 1:
        return avoidedFinances != null;
      case 2:
        return copingMethods.length > 0;
      case 3:
        return true;
      default:
        return false;
    }
  }, [avoidedFinances, copingMethods.length, step, triggerPurchase]);

  const submit = useCallback(async () => {
    if (triggerPurchase == null || avoidedFinances == null) return;
    setBusy(true);
    setError(null);
    try {
      await submitMindMoodCheckin({
        mood_stress_triggered_purchase: triggerPurchase,
        mood_avoided_finances: avoidedFinances,
        mood_coping_methods: copingMethods,
        spending_intentionality_rating: spendingIntentionality,
      });
      setSuccessMessage('Check-in saved');
      window.setTimeout(() => navigate(CHECKUPS_HUB_PATH, { replace: true }), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [avoidedFinances, copingMethods, navigate, spendingIntentionality, triggerPurchase]);

  const next = () => {
    if (step < totalSteps - 1) {
      if (canAdvance) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const lastAt =
    profile?.mood_stress_triggered_purchase != null ? profile.updated_at : null;
  const relative = formatRelativeLastUpdate(lastAt);

  return (
    <CheckupWrapperShell
      title="Mind & Mood Check-in"
      score={null}
      lastCompletedAt={lastAt}
      loading={profileLoading}
      error={error}
      successMessage={successMessage}
    >
      {!successMessage ? (
        <div
          className="dash-checkup-theme space-y-6 rounded-2xl border bg-white p-6 shadow-sm sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <StepLabel step={step} total={totalSteps} />

          {step === 0 ? (
            <section className="space-y-4">
              <StepTitle>
                Think back to the last time you bought something you didn&apos;t plan to. What was
                going on for you right before — even subtle things like feeling overlooked at work,
                scrolling past something that made you feel behind, or just a quiet restless feeling
                you couldn&apos;t name? (That counts.)
              </StepTitle>
              <OptionButtons
                options={TRIGGER_OPTIONS}
                value={triggerPurchase}
                onChange={setTriggerPurchase}
              />
            </section>
          ) : null}

          {step === 1 ? (
            <section className="space-y-4">
              <StepTitle>
                Did you avoid looking at your finances at any point this week — not opening the app,
                skipping a statement, or putting off a money decision?
              </StepTitle>
              <YesNoButtons value={avoidedFinances} onChange={setAvoidedFinances} />
            </section>
          ) : null}

          {step === 2 ? (
            <section className="space-y-4">
              <StepTitle>What helped you manage your energy or stress this week, if anything?</StepTitle>
              <p className="text-xs" style={{ color: 'var(--ink-mid)' }}>
                Select all that apply
              </p>
              <MultiSelectChips
                options={COPING_OPTIONS}
                selected={copingMethods}
                onToggle={toggleCoping}
              />
            </section>
          ) : null}

          {step === 3 ? (
            <RangeStep
              label="How intentional were your spending decisions this week?"
              min={1}
              max={5}
              value={spendingIntentionality}
              onChange={setSpendingIntentionality}
              lowLabel="All reactive"
              highLabel="All intentional"
            />
          ) : null}

          <StepNav
            step={step}
            busy={busy}
            canAdvance={canAdvance}
            onBack={() => setStep((s) => s - 1)}
            onNext={next}
            isLast={step === totalSteps - 1}
          />

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
