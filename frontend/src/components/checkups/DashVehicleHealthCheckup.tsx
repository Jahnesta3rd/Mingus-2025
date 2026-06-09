import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import { CHECKUPS_HUB_PATH, submitVehicleCheckup } from './checkupShared';
import {
  CheckupForm,
  CheckupQuestionBlock,
  DollarInput,
  OptionButtons,
  QuestionLabel,
  ScaleButtons,
  SubmitButton,
  TextInput,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';

const SERVICE_OPTIONS = [
  { value: 'under_3mo', label: 'Within 1 month' },
  { value: '3_6mo', label: '1–3 months ago' },
  { value: '6_12mo', label: '3–6 months ago' },
  { value: 'over_12mo', label: 'More than 6 months ago' },
  { value: 'never', label: 'Not sure' },
] as const;

const INSURANCE_SHOPPED_OPTIONS = [
  { value: 'never', label: 'Never' },
  { value: 'over_2yr', label: '2+ years' },
  { value: '1_2yr', label: '1–2 years' },
  { value: '6_12mo', label: 'Within 1 year' },
  { value: 'under_6mo', label: 'Within 6 months' },
] as const;

const DECISION_OPTIONS = [
  { value: 'keeping', label: "I'm keeping it" },
  { value: 'unsure', label: 'Not sure yet' },
  { value: 'selling', label: 'Planning to sell or replace' },
] as const;

const DECISION_API: Record<string, string> = {
  keeping: 'keeping_years',
  unsure: 'unsure',
  selling: 'considering_replace',
};

const SUCCESS_BY_DECISION: Record<string, string> = {
  keeping: "We're tracking your maintenance calendar and cost profile.",
  unsure: "We'll show you the numbers on keeping vs. selling when you're ready.",
  selling: "We'll flag the best window to sell based on your depreciation curve.",
};

export function DashVehicleHealthCheckup() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const [satisfaction, setSatisfaction] = useState(3);
  const [maintenanceConfidence, setMaintenanceConfidence] = useState(3);
  const [recentConcern, setRecentConcern] = useState<boolean | null>(null);
  const [concernDescription, setConcernDescription] = useState('');
  const [weeklyMiles, setWeeklyMiles] = useState('100');
  const [lastService, setLastService] = useState<string | null>(null);
  const [insuranceKnown, setInsuranceKnown] = useState<boolean | null>(null);
  const [insurancePremium, setInsurancePremium] = useState('');
  const [insuranceShopped, setInsuranceShopped] = useState<string | null>(null);
  const [decisionHorizon, setDecisionHorizon] = useState<string | null>(null);
  const [reliability, setReliability] = useState(3);
  const [valuePerception, setValuePerception] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    const miles = Number(weeklyMiles);
    return (
      recentConcern != null &&
      lastService != null &&
      insuranceKnown != null &&
      insuranceShopped != null &&
      decisionHorizon != null &&
      weeklyMiles.trim() !== '' &&
      !Number.isNaN(miles) &&
      miles >= 0 &&
      miles <= 1000
    );
  }, [decisionHorizon, insuranceKnown, insuranceShopped, lastService, recentConcern, weeklyMiles]);

  const submit = useCallback(async () => {
    if (
      recentConcern == null ||
      lastService == null ||
      insuranceKnown == null ||
      insuranceShopped == null ||
      decisionHorizon == null
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await submitVehicleCheckup({
        vehicle_satisfaction_rating: satisfaction,
        vehicle_maintenance_confidence: maintenanceConfidence,
        vehicle_recent_concern: recentConcern,
        vehicle_concern_description: recentConcern
          ? concernDescription.trim() || 'Unspecified'
          : null,
        vehicle_weekly_miles: Number(weeklyMiles),
        vehicle_last_service_horizon: lastService,
        vehicle_insurance_known: insuranceKnown,
        vehicle_insurance_premium: insuranceKnown
          ? insurancePremium.trim() !== ''
            ? Number(insurancePremium)
            : 0
          : null,
        vehicle_insurance_last_shopped: insuranceKnown ? insuranceShopped : null,
        vehicle_decision_horizon: DECISION_API[decisionHorizon] ?? 'unsure',
        vehicle_reliability_rating: reliability,
        vehicle_value_perception: valuePerception,
      });
      await refetch();
      const banner =
        SUCCESS_BY_DECISION[decisionHorizon] ??
        `Vehicle Health updated — ${data.vehicle_score} / 100`;
      setSuccessMessage(banner);
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

  const onConcernChange = (val: boolean) => {
    setRecentConcern(val);
    if (!val) setConcernDescription('');
  };

  const onInsuranceKnownChange = (val: boolean) => {
    setInsuranceKnown(val);
    if (!val) setInsurancePremium('');
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
          className="dash-checkup-theme max-h-[70vh] overflow-y-auto rounded-2xl border bg-white p-6 shadow-sm sm:max-h-none sm:overflow-visible sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <CheckupForm>
            <CheckupQuestionBlock>
              <QuestionLabel>Overall, how satisfied are you with your vehicle?</QuestionLabel>
              <ScaleButtons min={1} max={5} value={satisfaction} onChange={setSatisfaction} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                How confident are you that your vehicle has no deferred maintenance needs?
              </QuestionLabel>
              <ScaleButtons
                min={1}
                max={5}
                value={maintenanceConfidence}
                onChange={setMaintenanceConfidence}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>Have you had any unexpected vehicle concerns this week?</QuestionLabel>
              <YesNoButtons value={recentConcern} onChange={onConcernChange} />
            </CheckupQuestionBlock>

            {recentConcern === true ? (
              <CheckupQuestionBlock conditional>
                <QuestionLabel>Briefly, what happened? (optional)</QuestionLabel>
                <TextInput
                  value={concernDescription}
                  onChange={setConcernDescription}
                  placeholder="Optional description"
                />
              </CheckupQuestionBlock>
            ) : null}

            <CheckupQuestionBlock>
              <QuestionLabel>How many miles do you typically drive in a week?</QuestionLabel>
              <input
                type="number"
                min={0}
                max={1000}
                value={weeklyMiles}
                onChange={(e) => setWeeklyMiles(e.target.value)}
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>When did you last have your vehicle serviced?</QuestionLabel>
              <OptionButtons options={SERVICE_OPTIONS} value={lastService} onChange={setLastService} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                Do you know what you&apos;re paying for vehicle insurance per month?
              </QuestionLabel>
              <YesNoButtons value={insuranceKnown} onChange={onInsuranceKnownChange} />
            </CheckupQuestionBlock>

            {insuranceKnown === true ? (
              <CheckupQuestionBlock conditional>
                <QuestionLabel>What&apos;s your monthly premium? (optional)</QuestionLabel>
                <DollarInput value={insurancePremium} onChange={setInsurancePremium} />
              </CheckupQuestionBlock>
            ) : null}

            <CheckupQuestionBlock>
              <QuestionLabel>How long ago did you last compare insurance rates?</QuestionLabel>
              <OptionButtons
                options={INSURANCE_SHOPPED_OPTIONS}
                value={insuranceShopped}
                onChange={setInsuranceShopped}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>What&apos;s your plan for this vehicle?</QuestionLabel>
              <OptionButtons
                options={DECISION_OPTIONS}
                value={decisionHorizon}
                onChange={setDecisionHorizon}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>How reliable has your vehicle been recently?</QuestionLabel>
              <ScaleButtons min={1} max={5} value={reliability} onChange={setReliability} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>Does your vehicle feel worth what you&apos;re paying for it?</QuestionLabel>
              <ScaleButtons min={1} max={5} value={valuePerception} onChange={setValuePerception} />
            </CheckupQuestionBlock>

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

export default DashVehicleHealthCheckup;
