import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitVehicleCheckup } from './checkupShared';
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

const SERVICE_OPTIONS = [
  { value: 'under_3mo', label: 'Within 3 months' },
  { value: '3_6mo', label: '3–6 months ago' },
  { value: '6_12mo', label: '6–12 months ago' },
  { value: 'over_12mo', label: 'Over a year ago' },
  { value: 'never', label: 'Never or not sure' },
] as const;

const INSURANCE_SHOPPED_OPTIONS = [
  { value: 'under_6mo', label: 'Within 6 months' },
  { value: '6_12mo', label: '6–12 months ago' },
  { value: '1_2yr', label: '1–2 years ago' },
  { value: 'over_2yr', label: 'Over 2 years ago' },
  { value: 'never', label: 'Never shopped' },
] as const;

const DECISION_OPTIONS = [
  { value: 'keeping_years', label: 'Keeping it for years' },
  { value: 'considering_replace', label: 'Considering replacing soon' },
  { value: 'actively_shopping', label: 'Actively shopping for another vehicle' },
  { value: 'unsure', label: 'Not sure yet' },
] as const;

type VehicleStep =
  | 'satisfaction'
  | 'maintenance_confidence'
  | 'recent_concern'
  | 'concern_description'
  | 'weekly_miles'
  | 'last_service'
  | 'insurance_known'
  | 'insurance_premium'
  | 'insurance_shopped'
  | 'decision_horizon'
  | 'reliability'
  | 'value_perception';

function buildVehicleSteps(
  recentConcern: boolean | null,
  insuranceKnown: boolean | null
): VehicleStep[] {
  const steps: VehicleStep[] = [
    'satisfaction',
    'maintenance_confidence',
    'recent_concern',
  ];
  if (recentConcern === true) steps.push('concern_description');
  steps.push('weekly_miles', 'last_service', 'insurance_known');
  if (insuranceKnown === true) {
    steps.push('insurance_premium', 'insurance_shopped');
  }
  steps.push('decision_horizon', 'reliability', 'value_perception');
  return steps;
}

/**
 * Vehicle Health check-in — 12-field set; concern trigger (#170) → LifeLedgerProfile.
 */
export function DashVehicleHealthCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const [step, setStep] = useState(0);
  const [satisfaction, setSatisfaction] = useState(3);
  const [maintenanceConfidence, setMaintenanceConfidence] = useState(3);
  const [recentConcern, setRecentConcern] = useState<boolean | null>(null);
  const [concernDescription, setConcernDescription] = useState('');
  const [weeklyMiles, setWeeklyMiles] = useState<string>('100');
  const [lastService, setLastService] = useState<string | null>(null);
  const [insuranceKnown, setInsuranceKnown] = useState<boolean | null>(null);
  const [insurancePremium, setInsurancePremium] = useState<string>('');
  const [insuranceShopped, setInsuranceShopped] = useState<string | null>(null);
  const [decisionHorizon, setDecisionHorizon] = useState<string | null>(null);
  const [reliability, setReliability] = useState(3);
  const [valuePerception, setValuePerception] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const steps = useMemo(
    () => buildVehicleSteps(recentConcern, insuranceKnown),
    [insuranceKnown, recentConcern]
  );
  useEffect(() => {
    if (step >= steps.length) setStep(Math.max(0, steps.length - 1));
  }, [step, steps.length]);
  const current = steps[step] ?? 'satisfaction';

  const canAdvance = useMemo(() => {
    switch (current) {
      case 'satisfaction':
      case 'maintenance_confidence':
      case 'reliability':
      case 'value_perception':
        return true;
      case 'recent_concern':
        return recentConcern != null;
      case 'concern_description':
        return concernDescription.trim().length > 0;
      case 'weekly_miles': {
        const n = Number(weeklyMiles);
        return weeklyMiles.trim() !== '' && !Number.isNaN(n) && n >= 0;
      }
      case 'last_service':
        return lastService != null;
      case 'insurance_known':
        return insuranceKnown != null;
      case 'insurance_premium': {
        const n = Number(insurancePremium);
        return insurancePremium.trim() !== '' && !Number.isNaN(n) && n >= 0;
      }
      case 'insurance_shopped':
        return insuranceShopped != null;
      case 'decision_horizon':
        return decisionHorizon != null;
      default:
        return false;
    }
  }, [
    concernDescription,
    current,
    decisionHorizon,
    insuranceKnown,
    insurancePremium,
    insuranceShopped,
    lastService,
    recentConcern,
    weeklyMiles,
  ]);

  const submit = useCallback(async () => {
    if (recentConcern == null || lastService == null || insuranceKnown == null || decisionHorizon == null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await submitVehicleCheckup({
        vehicle_satisfaction_rating: satisfaction,
        vehicle_maintenance_confidence: maintenanceConfidence,
        vehicle_recent_concern: recentConcern,
        vehicle_concern_description: recentConcern ? concernDescription.trim() : null,
        vehicle_weekly_miles: Number(weeklyMiles),
        vehicle_last_service_horizon: lastService,
        vehicle_insurance_known: insuranceKnown,
        vehicle_insurance_premium: insuranceKnown ? Number(insurancePremium) : null,
        vehicle_insurance_last_shopped: insuranceKnown ? insuranceShopped : null,
        vehicle_decision_horizon: decisionHorizon,
        vehicle_reliability_rating: reliability,
        vehicle_value_perception: valuePerception,
      });
      await refetch();
      setSuccessMessage(`Vehicle Health updated — ${data.vehicle_score} / 100`);
      window.setTimeout(() => navigate(CHECKUPS_HUB_PATH, { replace: true }), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [
    concernDescription,
    decisionHorizon,
    insuranceKnown,
    insurancePremium,
    insuranceShopped,
    lastService,
    maintenanceConfidence,
    navigate,
    recentConcern,
    refetch,
    reliability,
    satisfaction,
    valuePerception,
    weeklyMiles,
  ]);

  const next = () => {
    if (step < steps.length - 1) {
      if (canAdvance) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const onConcernChange = (val: boolean) => {
    setRecentConcern(val);
    if (!val) setConcernDescription('');
  };

  const onInsuranceKnownChange = (val: boolean) => {
    setInsuranceKnown(val);
    if (!val) {
      setInsurancePremium('');
      setInsuranceShopped(null);
    }
  };

  const lastAt = profile?.vehicle_score != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Vehicle Health Check-in"
      score={profile?.vehicle_score ?? null}
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
          <StepLabel step={step} total={steps.length} />

          {current === 'satisfaction' ? (
            <RangeStep
              label="How satisfied are you with your vehicle right now?"
              min={1}
              max={5}
              value={satisfaction}
              onChange={setSatisfaction}
              lowLabel="Very dissatisfied"
              highLabel="Very satisfied"
            />
          ) : null}

          {current === 'maintenance_confidence' ? (
            <RangeStep
              label="How confident are you that you can handle upcoming maintenance costs?"
              min={1}
              max={5}
              value={maintenanceConfidence}
              onChange={setMaintenanceConfidence}
              lowLabel="Not confident"
              highLabel="Very confident"
            />
          ) : null}

          {current === 'recent_concern' ? (
            <section className="space-y-4">
              <StepTitle>
                Has anything about your vehicle worried you recently — sounds, warning lights, or
                reliability?
              </StepTitle>
              <YesNoButtons value={recentConcern} onChange={onConcernChange} />
            </section>
          ) : null}

          {current === 'concern_description' ? (
            <section className="space-y-4">
              <StepTitle>What&apos;s the concern? A sentence is enough.</StepTitle>
              <textarea
                value={concernDescription}
                onChange={(e) => setConcernDescription(e.target.value)}
                rows={4}
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
                placeholder="e.g. brakes squeaking, check engine light"
              />
            </section>
          ) : null}

          {current === 'weekly_miles' ? (
            <section className="space-y-4">
              <StepTitle>About how many miles do you drive per week?</StepTitle>
              <input
                type="number"
                min={0}
                max={2000}
                value={weeklyMiles}
                onChange={(e) => setWeeklyMiles(e.target.value)}
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </section>
          ) : null}

          {current === 'last_service' ? (
            <section className="space-y-4">
              <StepTitle>When was your last oil change or major service?</StepTitle>
              <OptionButtons options={SERVICE_OPTIONS} value={lastService} onChange={setLastService} />
            </section>
          ) : null}

          {current === 'insurance_known' ? (
            <section className="space-y-4">
              <StepTitle>Do you know your current monthly auto insurance premium?</StepTitle>
              <YesNoButtons value={insuranceKnown} onChange={onInsuranceKnownChange} />
            </section>
          ) : null}

          {current === 'insurance_premium' ? (
            <section className="space-y-4">
              <StepTitle>What is your monthly auto insurance premium?</StepTitle>
              <input
                type="number"
                min={0}
                step={1}
                value={insurancePremium}
                onChange={(e) => setInsurancePremium(e.target.value)}
                placeholder="Monthly premium in dollars"
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </section>
          ) : null}

          {current === 'insurance_shopped' ? (
            <section className="space-y-4">
              <StepTitle>When did you last shop around for auto insurance?</StepTitle>
              <OptionButtons
                options={INSURANCE_SHOPPED_OPTIONS}
                value={insuranceShopped}
                onChange={setInsuranceShopped}
              />
            </section>
          ) : null}

          {current === 'decision_horizon' ? (
            <section className="space-y-4">
              <StepTitle>What are your plans for this vehicle over the next year or two?</StepTitle>
              <OptionButtons
                options={DECISION_OPTIONS}
                value={decisionHorizon}
                onChange={setDecisionHorizon}
              />
            </section>
          ) : null}

          {current === 'reliability' ? (
            <RangeStep
              label="How reliable has your vehicle been lately?"
              min={1}
              max={5}
              value={reliability}
              onChange={setReliability}
              lowLabel="Unreliable"
              highLabel="Very reliable"
            />
          ) : null}

          {current === 'value_perception' ? (
            <RangeStep
              label="How good a financial deal does this vehicle feel like for you?"
              min={1}
              max={5}
              value={valuePerception}
              onChange={setValuePerception}
              lowLabel="Poor value"
              highLabel="Great value"
            />
          ) : null}

          <StepNav
            step={step}
            busy={busy || profileLoading}
            canAdvance={canAdvance}
            onBack={() => setStep((s) => Math.max(0, s - 1))}
            onNext={next}
            isLast={step === steps.length - 1}
          />
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashVehicleHealthCheckup;
