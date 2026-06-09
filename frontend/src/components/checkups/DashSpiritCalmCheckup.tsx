import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitSpiritCalmCheckin } from './checkupShared';
import { OptionButtons, StepLabel, StepNav, StepTitle, YesNoButtons } from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';

const FINANCE_IMPACT_OPTIONS = [
  { value: 'not_at_all', label: 'Not at all' },
  { value: 'slightly', label: 'Slightly — small shifts in mood or spending' },
  { value: 'moderately', label: 'Moderately — noticed real money decisions' },
  { value: 'significantly', label: 'Significantly — major calm or anxiety about money' },
] as const;

const ANXIOUS_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'no', label: 'No' },
  { value: 'unsure', label: "I'm not sure" },
] as const;

/**
 * Spirit & Calm check-in — 3-question set (#170) → LifeLedgerProfile.
 */
export function DashSpiritCalmCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { profile, loading: profileLoading } = useLifeLedger(isAuthenticated);
  const [step, setStep] = useState(0);
  const [hadMoments, setHadMoments] = useState<boolean | null>(null);
  const [affectedFinances, setAffectedFinances] = useState<string | null>(null);
  const [financiallyAnxious, setFinanciallyAnxious] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const totalSteps = 3;

  const canAdvance = useMemo(() => {
    switch (step) {
      case 0:
        return hadMoments != null;
      case 1:
        return affectedFinances != null;
      case 2:
        return financiallyAnxious != null;
      default:
        return false;
    }
  }, [affectedFinances, financiallyAnxious, hadMoments, step]);

  const submit = useCallback(async () => {
    if (hadMoments == null || affectedFinances == null || financiallyAnxious == null) return;
    setBusy(true);
    setError(null);
    try {
      await submitSpiritCalmCheckin({
        practice_had_moments: hadMoments,
        practice_affected_finances: affectedFinances,
        spirit_financially_anxious: financiallyAnxious,
      });
      setSuccessMessage('Check-in saved');
      window.setTimeout(() => navigate(CHECKUPS_HUB_PATH, { replace: true }), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [affectedFinances, financiallyAnxious, hadMoments, navigate]);

  const next = () => {
    if (step < totalSteps - 1) {
      if (canAdvance) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const lastAt = profile?.practice_had_moments != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Spirit & Calm Check-in"
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
                Did you have moments of calm, prayer, meditation, or spiritual grounding this week?
              </StepTitle>
              <YesNoButtons value={hadMoments} onChange={setHadMoments} />
            </section>
          ) : null}

          {step === 1 ? (
            <section className="space-y-4">
              <StepTitle>Did your spiritual or calm practice affect your financial decisions?</StepTitle>
              <OptionButtons
                options={FINANCE_IMPACT_OPTIONS}
                value={affectedFinances}
                onChange={setAffectedFinances}
              />
            </section>
          ) : null}

          {step === 2 ? (
            <section className="space-y-4">
              <StepTitle>
                When you think about money right now, do you feel spiritually or emotionally anxious?
              </StepTitle>
              <OptionButtons
                options={ANXIOUS_OPTIONS}
                value={financiallyAnxious}
                onChange={setFinanciallyAnxious}
              />
            </section>
          ) : null}

          <StepNav
            step={step}
            busy={busy}
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

export default DashSpiritCalmCheckup;
