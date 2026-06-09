import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitBodyCheckup } from './checkupShared';
import {
  OptionButtons,
  RangeStep,
  StepLabel,
  StepNav,
  StepTitle,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';

const WORK_IMPACT_OPTIONS = [
  { value: 'none', label: 'No noticeable impact' },
  { value: 'minor', label: 'Minor — occasional low energy' },
  { value: 'moderate', label: 'Moderate — affecting some tasks' },
  { value: 'major', label: 'Major — missing work or commitments' },
  { value: 'severe', label: 'Severe — unable to function normally' },
] as const;

/**
 * Body Wellness check-in (#170) — 3-question set → LifeLedgerProfile.
 */
export function DashBodyWellnessCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const [step, setStep] = useState(0);
  const [energyRating, setEnergyRating] = useState(3);
  const [workImpact, setWorkImpact] = useState<string | null>(null);
  const [ongoingHealthCost, setOngoingHealthCost] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const totalSteps = 3;

  const canAdvance = useMemo(() => {
    switch (step) {
      case 0:
        return true;
      case 1:
        return workImpact != null;
      case 2:
        return ongoingHealthCost != null;
      default:
        return false;
    }
  }, [ongoingHealthCost, step, workImpact]);

  const submit = useCallback(async () => {
    if (workImpact == null || ongoingHealthCost == null) return;
    setBusy(true);
    setError(null);
    try {
      const data = await submitBodyCheckup({
        body_energy_rating: energyRating,
        body_work_impact: workImpact,
        body_ongoing_health_cost: ongoingHealthCost,
      });
      await refetch();
      setSuccessMessage(`Body score updated — ${data.body_score} / 100`);
      window.setTimeout(() => navigate(CHECKUPS_HUB_PATH, { replace: true }), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [energyRating, navigate, ongoingHealthCost, refetch, workImpact]);

  const next = () => {
    if (step < totalSteps - 1) {
      if (canAdvance) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const lastAt = profile?.body_score != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Body Wellness Check-in"
      score={profile?.body_score ?? null}
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
            <RangeStep
              label="How would you rate your physical energy this week?"
              min={1}
              max={5}
              value={energyRating}
              onChange={setEnergyRating}
              lowLabel="Exhausted"
              highLabel="Energized"
            />
          ) : null}

          {step === 1 ? (
            <section className="space-y-4">
              <StepTitle>
                How much is your physical health affecting your ability to work or handle daily
                responsibilities?
              </StepTitle>
              <OptionButtons options={WORK_IMPACT_OPTIONS} value={workImpact} onChange={setWorkImpact} />
            </section>
          ) : null}

          {step === 2 ? (
            <section className="space-y-4">
              <StepTitle>
                Are you currently dealing with ongoing health costs — prescriptions, therapy,
                copays, or similar?
              </StepTitle>
              <YesNoButtons value={ongoingHealthCost} onChange={setOngoingHealthCost} />
            </section>
          ) : null}

          <StepNav
            step={step}
            busy={busy || profileLoading}
            canAdvance={canAdvance}
            onBack={() => setStep((s) => s - 1)}
            onNext={next}
            isLast={step === totalSteps - 1}
          />
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashBodyWellnessCheckup;
