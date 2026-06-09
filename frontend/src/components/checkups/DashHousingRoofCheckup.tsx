import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitHousingCheckup } from './checkupShared';
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
import {
  deriveUserTier,
  fetchWaterfallContext,
  FluencyCue,
  type WaterfallContext,
} from '../fluency';

const TENURE_OPTIONS = [
  { value: 'rent', label: 'Rent' },
  { value: 'own', label: 'Own' },
] as const;

const LEASE_OPTIONS = [
  { value: 'under_3mo', label: 'Under 3 months' },
  { value: '3_6mo', label: '3–6 months' },
  { value: '6_12mo', label: '6–12 months' },
  { value: 'over_12mo', label: 'Over 12 months' },
  { value: 'month_to_month', label: 'Month-to-month' },
] as const;

const COST_CHANGED_OPTIONS = [
  { value: 'increased', label: 'Increased' },
  { value: 'decreased', label: 'Decreased' },
  { value: 'same', label: 'About the same' },
  { value: 'not_sure', label: 'Not sure' },
] as const;

const DOWN_PAYMENT_OPTIONS = [
  { value: 'not_saving', label: 'Not saving yet' },
  { value: 'started', label: 'Started saving' },
  { value: 'on_track', label: 'On track for my goal' },
  { value: 'ready', label: 'Ready or already saved' },
] as const;

type HousingStep =
  | 'stability'
  | 'tenure'
  | 'lease'
  | 'down_payment'
  | 'cost_changed'
  | 'unexpected'
  | 'unexpected_amount';

function buildSteps(tenure: string | null, unexpectedCost: boolean | null): HousingStep[] {
  const steps: HousingStep[] = ['stability', 'tenure'];
  if (tenure === 'rent') steps.push('lease');
  if (tenure === 'own') steps.push('down_payment');
  steps.push('cost_changed', 'unexpected');
  if (unexpectedCost === true) steps.push('unexpected_amount');
  return steps;
}

/**
 * Housing & Roof check-in — 7-field set with tenure branch + unexpected-cost trigger (#170).
 */
export function DashHousingRoofCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const [waterfallContext, setWaterfallContext] = useState<WaterfallContext | null>(null);
  const [step, setStep] = useState(0);
  const [stabilityRating, setStabilityRating] = useState(3);
  const [tenure, setTenure] = useState<string | null>(null);
  const [leaseHorizon, setLeaseHorizon] = useState<string | null>(null);
  const [downPaymentStatus, setDownPaymentStatus] = useState<string | null>(null);
  const [costChanged, setCostChanged] = useState<string | null>(null);
  const [unexpectedCost, setUnexpectedCost] = useState<boolean | null>(null);
  const [unexpectedAmount, setUnexpectedAmount] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const steps = useMemo(
    () => buildSteps(tenure, unexpectedCost),
    [tenure, unexpectedCost]
  );
  useEffect(() => {
    if (step >= steps.length) setStep(Math.max(0, steps.length - 1));
  }, [step, steps.length]);
  const current = steps[step] ?? 'stability';

  const canAdvance = useMemo(() => {
    switch (current) {
      case 'stability':
        return true;
      case 'tenure':
        return tenure != null;
      case 'lease':
        return leaseHorizon != null;
      case 'down_payment':
        return downPaymentStatus != null;
      case 'cost_changed':
        return costChanged != null;
      case 'unexpected':
        return unexpectedCost != null;
      case 'unexpected_amount': {
        const n = Number(unexpectedAmount);
        return unexpectedAmount.trim() !== '' && !Number.isNaN(n) && n >= 0;
      }
      default:
        return false;
    }
  }, [costChanged, current, downPaymentStatus, leaseHorizon, tenure, unexpectedAmount, unexpectedCost]);

  const submit = useCallback(async () => {
    if (tenure == null || costChanged == null || unexpectedCost == null) return;
    setBusy(true);
    setError(null);
    try {
      const data = await submitHousingCheckup({
        housing_stability_rating: stabilityRating,
        housing_tenure: tenure,
        housing_lease_end_horizon: tenure === 'rent' ? leaseHorizon : null,
        housing_cost_changed: costChanged,
        housing_down_payment_status: tenure === 'own' ? downPaymentStatus : null,
        housing_unexpected_cost: unexpectedCost,
        housing_unexpected_cost_amount: unexpectedCost
          ? Number(unexpectedAmount)
          : null,
      });
      await refetch();
      setSuccessMessage(`Roof score updated — ${data.roof_score} / 100`);
      void fetchWaterfallContext().then(setWaterfallContext).catch(() => {});
      window.setTimeout(() => navigate(CHECKUPS_HUB_PATH, { replace: true }), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [
    costChanged,
    downPaymentStatus,
    leaseHorizon,
    navigate,
    refetch,
    stabilityRating,
    tenure,
    unexpectedAmount,
    unexpectedCost,
  ]);

  const next = () => {
    if (step < steps.length - 1) {
      if (canAdvance) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const onUnexpectedChange = (val: boolean) => {
    setUnexpectedCost(val);
    if (!val) setUnexpectedAmount('');
  };

  const lastAt = profile?.roof_score != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Housing & Roof Check-in"
      score={profile?.roof_score ?? null}
      lastCompletedAt={lastAt}
      loading={profileLoading}
      error={error}
      successMessage={successMessage}
    >
      {successMessage && waterfallContext ? (
        <FluencyCue
          context={waterfallContext}
          domain="housing"
          userTier={userTier}
          onActionRoute={(route) => navigate(route, { replace: true })}
        />
      ) : null}

      {!successMessage ? (
        <div
          className="dash-checkup-theme space-y-6 rounded-2xl border bg-white p-6 shadow-sm sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <StepLabel step={step} total={steps.length} />

          {current === 'stability' ? (
            <RangeStep
              label="How stable does your housing situation feel right now?"
              min={1}
              max={5}
              value={stabilityRating}
              onChange={setStabilityRating}
              lowLabel="Very unstable"
              highLabel="Very stable"
            />
          ) : null}

          {current === 'tenure' ? (
            <section className="space-y-4">
              <StepTitle>Do you rent or own your home?</StepTitle>
              <OptionButtons options={TENURE_OPTIONS} value={tenure} onChange={setTenure} />
            </section>
          ) : null}

          {current === 'lease' ? (
            <section className="space-y-4">
              <StepTitle>When does your lease end or come up for renewal?</StepTitle>
              <OptionButtons options={LEASE_OPTIONS} value={leaseHorizon} onChange={setLeaseHorizon} />
            </section>
          ) : null}

          {current === 'down_payment' ? (
            <section className="space-y-4">
              <StepTitle>Where are you with saving for maintenance or your next housing move?</StepTitle>
              <OptionButtons
                options={DOWN_PAYMENT_OPTIONS}
                value={downPaymentStatus}
                onChange={setDownPaymentStatus}
              />
            </section>
          ) : null}

          {current === 'cost_changed' ? (
            <section className="space-y-4">
              <StepTitle>How have your housing costs changed recently?</StepTitle>
              <OptionButtons options={COST_CHANGED_OPTIONS} value={costChanged} onChange={setCostChanged} />
            </section>
          ) : null}

          {current === 'unexpected' ? (
            <section className="space-y-4">
              <StepTitle>
                Did you face any unexpected housing costs this month — repairs, fees, or
                emergencies?
              </StepTitle>
              <YesNoButtons value={unexpectedCost} onChange={onUnexpectedChange} />
            </section>
          ) : null}

          {current === 'unexpected_amount' ? (
            <section className="space-y-4">
              <StepTitle>Roughly how much was that unexpected housing cost?</StepTitle>
              <label htmlFor="housing-unexpected-amount" className="sr-only">
                Unexpected housing cost amount
              </label>
              <input
                id="housing-unexpected-amount"
                type="number"
                min={0}
                step={1}
                value={unexpectedAmount}
                onChange={(e) => setUnexpectedAmount(e.target.value)}
                placeholder="Amount in dollars"
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </section>
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

export default DashHousingRoofCheckup;
