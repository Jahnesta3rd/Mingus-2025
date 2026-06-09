import { useCallback, useMemo, useState } from 'react';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { submitHousingCheckup } from './checkupShared';
import { RenewalPrompt } from './RenewalPrompt';
import { useCheckupFluencyNavigation } from './useCheckupFluencyNavigation';
import {
  CheckupForm,
  CheckupQuestionBlock,
  DollarInput,
  OptionButtons,
  QuestionLabel,
  ScaleButtons,
  SubmitButton,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';
import {
  deriveUserTier,
  FluencyCue,
} from '../fluency';

const TENURE_OPTIONS = [
  { value: 'renting', label: 'Renting' },
  { value: 'own', label: 'I own' },
  { value: 'other', label: 'Other' },
] as const;

const LEASE_OPTIONS = [
  { value: 'under_3mo', label: 'Within 3 months' },
  { value: '3_6mo', label: '3–6 months' },
  { value: '6_12mo', label: '6–12 months' },
  { value: 'over_12mo', label: 'More than a year away' },
  { value: 'month_to_month', label: 'Month-to-month' },
] as const;

const COST_CHANGED_OPTIONS = [
  { value: 'increased', label: 'Increased' },
  { value: 'decreased', label: 'Decreased' },
  { value: 'same', label: 'No change' },
  { value: 'na_own', label: 'N/A — I own' },
] as const;

const DOWN_PAYMENT_OPTIONS = [
  { value: 'not_saving', label: "Haven't started yet" },
  { value: 'started', label: 'Started but behind' },
  { value: 'on_track', label: 'On track' },
  { value: 'not_goal', label: 'Not a goal right now' },
] as const;

const DOWN_PAYMENT_API: Record<string, string> = {
  not_saving: 'not_saving',
  started: 'started',
  on_track: 'on_track',
  not_goal: 'not_saving',
};

export function DashHousingRoofCheckup() {
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const {
    waterfallContext,
    loadFluencyContext,
    onCueActionRoute,
    onCueDismiss,
  } = useCheckupFluencyNavigation('housing', userTier);
  const [stabilityRating, setStabilityRating] = useState(3);
  const [tenure, setTenure] = useState<string | null>(null);
  const [leaseHorizon, setLeaseHorizon] = useState<string | null>(null);
  const [costChanged, setCostChanged] = useState<string | null>(null);
  const [unexpectedCost, setUnexpectedCost] = useState<boolean | null>(null);
  const [unexpectedAmount, setUnexpectedAmount] = useState('');
  const [downPaymentStatus, setDownPaymentStatus] = useState<string | null>(null);
  const [renewalVariant, setRenewalVariant] = useState<'renewal' | 'increased' | null>(null);
  const [pendingIncreasedPrompt, setPendingIncreasedPrompt] = useState(false);
  const [submittedRoofScore, setSubmittedRoofScore] = useState<number | null>(null);
  const [pendingNavigate, setPendingNavigate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const isRenting = tenure === 'renting';
  const apiTenure = tenure === 'renting' ? 'rent' : 'own';

  const canSubmit = useMemo(() => {
    if (tenure == null || costChanged == null || unexpectedCost == null) return false;
    if (isRenting && (leaseHorizon == null || downPaymentStatus == null)) return false;
    return true;
  }, [costChanged, downPaymentStatus, isRenting, leaseHorizon, tenure, unexpectedCost]);

  const finishFlow = useCallback(
    (roofScore: number) => {
      setRenewalVariant(null);
      setPendingNavigate(true);
      setSuccessMessage(`Roof score updated — ${roofScore} / 100`);
      void loadFluencyContext();
    },
    [loadFluencyContext]
  );

  const submit = useCallback(async () => {
    if (!canSubmit || tenure == null || costChanged == null || unexpectedCost == null) return;
    setBusy(true);
    setError(null);
    try {
      const apiCostChanged = costChanged === 'na_own' ? 'same' : costChanged;
      const data = await submitHousingCheckup({
        housing_stability_rating: stabilityRating,
        housing_tenure: apiTenure,
        housing_lease_end_horizon: isRenting ? leaseHorizon : null,
        housing_cost_changed: apiCostChanged,
        housing_down_payment_status: isRenting
          ? DOWN_PAYMENT_API[downPaymentStatus ?? 'not_saving'] ?? 'not_saving'
          : 'not_saving',
        housing_unexpected_cost: unexpectedCost,
        housing_unexpected_cost_amount: unexpectedCost
          ? unexpectedAmount.trim() !== ''
            ? Number(unexpectedAmount)
            : 0
          : null,
      });
      await refetch();
      setSubmittedRoofScore(data.roof_score);

      const showRenewal = isRenting && leaseHorizon === 'under_3mo';
      const showIncreased = apiCostChanged === 'increased';
      if (showRenewal) {
        setRenewalVariant('renewal');
        if (showIncreased) setPendingIncreasedPrompt(true);
      } else if (showIncreased) {
        setRenewalVariant('increased');
      } else {
        finishFlow(data.roof_score);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [
    canSubmit,
    costChanged,
    downPaymentStatus,
    finishFlow,
    isRenting,
    leaseHorizon,
    refetch,
    stabilityRating,
    tenure,
    unexpectedAmount,
    unexpectedCost,
  ]);

  const onTenureChange = (val: string) => {
    setTenure(val);
    if (val !== 'renting') {
      setLeaseHorizon(null);
      setDownPaymentStatus(null);
    }
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
      <RenewalPrompt
        variant={renewalVariant ?? 'renewal'}
        open={renewalVariant != null}
        onDismiss={() => {
          if (pendingIncreasedPrompt && renewalVariant === 'renewal') {
            setPendingIncreasedPrompt(false);
            setRenewalVariant('increased');
            return;
          }
          finishFlow(submittedRoofScore ?? profile?.roof_score ?? 0);
        }}
      />

      {successMessage && waterfallContext && pendingNavigate ? (
        <FluencyCue
          context={waterfallContext}
          domain="housing"
          userTier={userTier}
          onActionRoute={onCueActionRoute}
          onDismiss={onCueDismiss}
        />
      ) : null}

      {!successMessage && renewalVariant == null ? (
        <div
          className="dash-checkup-theme max-h-[70vh] overflow-y-auto rounded-2xl border bg-white p-6 shadow-sm sm:max-h-none sm:overflow-visible sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <CheckupForm>
            <CheckupQuestionBlock>
              <QuestionLabel>How stable does your housing situation feel right now?</QuestionLabel>
              <ScaleButtons
                min={1}
                max={5}
                value={stabilityRating}
                onChange={setStabilityRating}
                labels={{ 1: 'Very uncertain', 3: 'Manageable', 5: 'Rock solid' }}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>What&apos;s your current housing situation?</QuestionLabel>
              <OptionButtons options={TENURE_OPTIONS} value={tenure} onChange={onTenureChange} />
            </CheckupQuestionBlock>

            {isRenting ? (
              <CheckupQuestionBlock conditional>
                <QuestionLabel>
                  When does your current lease end or come up for renewal?
                </QuestionLabel>
                <OptionButtons options={LEASE_OPTIONS} value={leaseHorizon} onChange={setLeaseHorizon} />
              </CheckupQuestionBlock>
            ) : null}

            <CheckupQuestionBlock>
              <QuestionLabel>Has your rent or housing cost changed in the last 3 months?</QuestionLabel>
              <OptionButtons options={COST_CHANGED_OPTIONS} value={costChanged} onChange={setCostChanged} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>Were there any unexpected housing costs this week?</QuestionLabel>
              <YesNoButtons value={unexpectedCost} onChange={onUnexpectedChange} />
            </CheckupQuestionBlock>

            {unexpectedCost === true ? (
              <CheckupQuestionBlock conditional>
                <QuestionLabel>Roughly how much? (optional)</QuestionLabel>
                <DollarInput
                  id="housing-unexpected-amount"
                  value={unexpectedAmount}
                  onChange={setUnexpectedAmount}
                />
              </CheckupQuestionBlock>
            ) : null}

            {isRenting ? (
              <CheckupQuestionBlock conditional>
                <QuestionLabel>Where are you on saving for a down payment?</QuestionLabel>
                <OptionButtons
                  options={DOWN_PAYMENT_OPTIONS}
                  value={downPaymentStatus}
                  onChange={setDownPaymentStatus}
                />
              </CheckupQuestionBlock>
            ) : null}

            <SubmitButton
              busy={busy || profileLoading}
              disabled={!canSubmit}
              onClick={() => void submit()}
            />
          </CheckupForm>
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashHousingRoofCheckup;
