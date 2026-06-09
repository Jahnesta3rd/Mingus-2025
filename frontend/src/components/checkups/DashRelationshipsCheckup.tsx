import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitRelationshipsCheckup } from './checkupShared';
import {
  OptionButtons,
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

const FRICTION_OPTIONS = [
  { value: 'none', label: 'No real friction this week' },
  { value: 'communication', label: 'Communication' },
  { value: 'money', label: 'Money or spending' },
  { value: 'time', label: 'Time or priorities' },
  { value: 'trust', label: 'Trust or boundaries' },
  { value: 'other', label: 'Something else' },
] as const;

const SPENDING_TYPE_OPTIONS = [
  { value: 'gifts', label: 'Gifts' },
  { value: 'dates', label: 'Dates or outings' },
  { value: 'travel', label: 'Travel' },
  { value: 'shared_bills', label: 'Shared bills' },
  { value: 'other', label: 'Other' },
] as const;

const DIRECTION_OPTIONS = [
  { value: 'improving', label: 'Improving' },
  { value: 'stable', label: 'Stable' },
  { value: 'uncertain', label: 'Uncertain' },
  { value: 'declining', label: 'Declining' },
] as const;

const AWARENESS_OPTIONS = [
  { value: 'very_aware', label: 'Very aware of what I spend' },
  { value: 'somewhat', label: 'Somewhat aware' },
  { value: 'rarely', label: 'Rarely think about it' },
  { value: 'unaware', label: 'Not aware until later' },
] as const;

const INTENTION_OPTIONS = [
  { value: 'invest_more', label: 'Invest more time and energy' },
  { value: 'maintain', label: 'Keep things as they are' },
  { value: 'reevaluate', label: 'Reevaluate where this is going' },
  { value: 'step_back', label: 'Step back or set boundaries' },
] as const;

type RelStep =
  | 'friction'
  | 'spending_this_week'
  | 'spending_amount'
  | 'spending_type'
  | 'direction'
  | 'cost_awareness'
  | 'future_intention';

function buildRelSteps(spendingThisWeek: boolean | null): RelStep[] {
  const steps: RelStep[] = ['friction', 'spending_this_week'];
  if (spendingThisWeek === true) {
    steps.push('spending_amount', 'spending_type');
  }
  steps.push('direction', 'cost_awareness', 'future_intention');
  return steps;
}

/**
 * Relationships check-in — 7-field set; spending trigger (#170) → LifeLedgerProfile.
 */
export function DashRelationshipsCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const [waterfallContext, setWaterfallContext] = useState<WaterfallContext | null>(null);
  const [step, setStep] = useState(0);
  const [frictionType, setFrictionType] = useState<string | null>(null);
  const [spendingThisWeek, setSpendingThisWeek] = useState<boolean | null>(null);
  const [spendingAmount, setSpendingAmount] = useState<string>('');
  const [spendingType, setSpendingType] = useState<string | null>(null);
  const [direction, setDirection] = useState<string | null>(null);
  const [costAwareness, setCostAwareness] = useState<string | null>(null);
  const [futureIntention, setFutureIntention] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const steps = useMemo(() => buildRelSteps(spendingThisWeek), [spendingThisWeek]);
  useEffect(() => {
    if (step >= steps.length) setStep(Math.max(0, steps.length - 1));
  }, [step, steps.length]);
  const current = steps[step] ?? 'friction';

  const canAdvance = useMemo(() => {
    switch (current) {
      case 'friction':
        return frictionType != null;
      case 'spending_this_week':
        return spendingThisWeek != null;
      case 'spending_amount': {
        const n = Number(spendingAmount);
        return spendingAmount.trim() !== '' && !Number.isNaN(n) && n >= 0;
      }
      case 'spending_type':
        return spendingType != null;
      case 'direction':
        return direction != null;
      case 'cost_awareness':
        return costAwareness != null;
      case 'future_intention':
        return futureIntention != null;
      default:
        return false;
    }
  }, [
    costAwareness,
    current,
    direction,
    frictionType,
    futureIntention,
    spendingAmount,
    spendingThisWeek,
    spendingType,
  ]);

  const submit = useCallback(async () => {
    if (
      frictionType == null ||
      spendingThisWeek == null ||
      direction == null ||
      costAwareness == null ||
      futureIntention == null
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await submitRelationshipsCheckup({
        relationship_friction_type: frictionType,
        relationship_spending_this_week: spendingThisWeek,
        relationship_spending_amount: spendingThisWeek ? Number(spendingAmount) : null,
        relationship_spending_type: spendingThisWeek ? spendingType : null,
        relationship_direction: direction,
        relationship_cost_awareness: costAwareness,
        relationship_future_intention: futureIntention,
      });
      setSuccessMessage('Check-in saved');
      void fetchWaterfallContext().then(setWaterfallContext).catch(() => {});
      window.setTimeout(() => navigate(CHECKUPS_HUB_PATH, { replace: true }), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [
    costAwareness,
    direction,
    frictionType,
    futureIntention,
    navigate,
    spendingAmount,
    spendingThisWeek,
    spendingType,
  ]);

  const next = () => {
    if (step < steps.length - 1) {
      if (canAdvance) setStep((s) => s + 1);
      return;
    }
    void submit();
  };

  const onSpendingThisWeekChange = (val: boolean) => {
    setSpendingThisWeek(val);
    if (!val) {
      setSpendingAmount('');
      setSpendingType(null);
    }
  };

  const lastAt =
    profile?.relationship_friction_type != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Relationships Check-in"
      lastCompletedAt={lastAt}
      loading={profileLoading}
      error={error}
      successMessage={successMessage}
    >
      {successMessage && waterfallContext ? (
        <FluencyCue
          context={waterfallContext}
          domain="relationships"
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

          {current === 'friction' ? (
            <section className="space-y-4">
              <StepTitle>
                What kind of friction showed up in your closest relationship this week, if any?
              </StepTitle>
              <OptionButtons
                options={FRICTION_OPTIONS}
                value={frictionType}
                onChange={setFrictionType}
              />
            </section>
          ) : null}

          {current === 'spending_this_week' ? (
            <section className="space-y-4">
              <StepTitle>
                Did you spend money on this relationship this week — dates, gifts, travel, or
                shared costs?
              </StepTitle>
              <YesNoButtons value={spendingThisWeek} onChange={onSpendingThisWeekChange} />
            </section>
          ) : null}

          {current === 'spending_amount' ? (
            <section className="space-y-4">
              <StepTitle>Roughly how much did you spend?</StepTitle>
              <input
                type="number"
                min={0}
                step={1}
                value={spendingAmount}
                onChange={(e) => setSpendingAmount(e.target.value)}
                placeholder="Amount in dollars"
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </section>
          ) : null}

          {current === 'spending_type' ? (
            <section className="space-y-4">
              <StepTitle>What was most of that spending for?</StepTitle>
              <OptionButtons
                options={SPENDING_TYPE_OPTIONS}
                value={spendingType}
                onChange={setSpendingType}
              />
            </section>
          ) : null}

          {current === 'direction' ? (
            <section className="space-y-4">
              <StepTitle>Overall, which way is this relationship heading?</StepTitle>
              <OptionButtons options={DIRECTION_OPTIONS} value={direction} onChange={setDirection} />
            </section>
          ) : null}

          {current === 'cost_awareness' ? (
            <section className="space-y-4">
              <StepTitle>How aware are you of what this relationship costs you financially?</StepTitle>
              <OptionButtons
                options={AWARENESS_OPTIONS}
                value={costAwareness}
                onChange={setCostAwareness}
              />
            </section>
          ) : null}

          {current === 'future_intention' ? (
            <section className="space-y-4">
              <StepTitle>What do you want to do with this relationship going forward?</StepTitle>
              <OptionButtons
                options={INTENTION_OPTIONS}
                value={futureIntention}
                onChange={setFutureIntention}
              />
            </section>
          ) : null}

          <StepNav
            step={step}
            busy={busy}
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

export default DashRelationshipsCheckup;
