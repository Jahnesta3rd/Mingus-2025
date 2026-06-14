import { useCallback, useMemo, useState } from 'react';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import ArticleRecommendationStrip from '../ArticleRecommendationStrip';
import { submitBodyCheckup } from './checkupShared';
import { useCheckupFluencyNavigation } from './useCheckupFluencyNavigation';
import {
  CheckupForm,
  CheckupQuestionBlock,
  NumericStepper,
  OptionButtons,
  QuestionLabel,
  ScaleButtons,
  SkipLink,
  SubmitButton,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';
import {
  deriveUserTier,
  FluencyCue,
} from '../fluency';

const WORK_IMPACT_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'somewhat', label: 'Somewhat' },
  { value: 'no', label: 'No' },
] as const;

const WORK_IMPACT_API: Record<string, string> = {
  yes: 'moderate',
  somewhat: 'minor',
  no: 'none',
};

export function DashBodyWellnessCheckup() {
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading, refetch } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const {
    waterfallContext,
    loadFluencyContext,
    onCueActionRoute,
    onCueDismiss,
  } = useCheckupFluencyNavigation('body', userTier);
  const [physicalRating, setPhysicalRating] = useState(3);
  const [activityFrequency, setActivityFrequency] = useState(0);
  const [avgSleepHours, setAvgSleepHours] = useState('7');
  const [energyRating, setEnergyRating] = useState(3);
  const [ongoingHealthCost, setOngoingHealthCost] = useState<boolean | null>(null);
  const [workImpact, setWorkImpact] = useState<string | null>(null);
  const [deferredPrompt, setDeferredPrompt] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const canSubmit = useMemo(
    () => ongoingHealthCost != null && workImpact != null,
    [ongoingHealthCost, workImpact]
  );

  const submit = useCallback(async () => {
    if (workImpact == null || ongoingHealthCost == null) return;
    setBusy(true);
    setError(null);
    try {
      const data = await submitBodyCheckup({
        body_energy_rating: energyRating,
        body_work_impact: WORK_IMPACT_API[workImpact] ?? 'none',
        body_ongoing_health_cost: ongoingHealthCost,
      });
      await refetch();
      setSuccessMessage(`Body score updated — ${data.body_score} / 100`);
      void loadFluencyContext();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [energyRating, loadFluencyContext, ongoingHealthCost, refetch, workImpact]);

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
      {successMessage ? (
        <ArticleRecommendationStrip
          heading="Free game for you"
          subheading="Based on your check-in"
          className="mt-4"
        />
      ) : null}

      {successMessage && waterfallContext ? (
        <FluencyCue
          context={waterfallContext}
          domain="body"
          userTier={userTier}
          onActionRoute={onCueActionRoute}
          onDismiss={onCueDismiss}
        />
      ) : null}

      {!successMessage ? (
        <div
          className="dash-checkup-theme max-h-[70vh] overflow-y-auto rounded-2xl border bg-white p-6 shadow-sm sm:max-h-none sm:overflow-visible sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <CheckupForm>
            <CheckupQuestionBlock>
              <QuestionLabel>How good did you feel physically this week, overall?</QuestionLabel>
              <ScaleButtons
                min={1}
                max={5}
                value={physicalRating}
                onChange={setPhysicalRating}
                labels={{ 1: 'Rough', 5: 'Great' }}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>How many times did you move intentionally this week?</QuestionLabel>
              <NumericStepper
                min={0}
                max={14}
                value={activityFrequency}
                onChange={setActivityFrequency}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>How many hours of sleep did you average per night?</QuestionLabel>
              <input
                type="number"
                min={0}
                max={12}
                step={0.5}
                value={avgSleepHours}
                onChange={(e) => setAvgSleepHours(e.target.value)}
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                How would you rate your energy level throughout the day this week?
              </QuestionLabel>
              <ScaleButtons
                min={1}
                max={5}
                value={energyRating}
                onChange={setEnergyRating}
                labels={{ 1: 'Depleted', 3: 'Steady', 5: 'Energized' }}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                Did managing your physical health cost you money this week — gym, medication,
                supplements, appointments?
              </QuestionLabel>
              <YesNoButtons value={ongoingHealthCost} onChange={setOngoingHealthCost} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                Did your physical state affect your performance or output at work this week?
              </QuestionLabel>
              <OptionButtons options={WORK_IMPACT_OPTIONS} value={workImpact} onChange={setWorkImpact} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                Is there anything about your body you&apos;ve been meaning to address but keep
                putting off?
              </QuestionLabel>
              <YesNoButtons value={deferredPrompt} onChange={setDeferredPrompt} />
              <SkipLink onClick={() => setDeferredPrompt(null)} />
            </CheckupQuestionBlock>

            <SubmitButton busy={busy || profileLoading} disabled={!canSubmit} onClick={() => void submit()} />
          </CheckupForm>
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashBodyWellnessCheckup;
