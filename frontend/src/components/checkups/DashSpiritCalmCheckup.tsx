import { useCallback, useMemo, useState } from 'react';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import ArticleRecommendationStrip from '../ArticleRecommendationStrip';
import { submitSpiritCalmCheckin } from './checkupShared';
import { useCheckupFluencyNavigation } from './useCheckupFluencyNavigation';
import { BreathingExerciseModal } from './BreathingExerciseModal';
import {
  CheckupForm,
  CheckupQuestionBlock,
  NumericStepper,
  OptionButtons,
  QuestionLabel,
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

const FINANCE_IMPACT_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'possibly', label: 'Possibly' },
  { value: 'no', label: 'No' },
  { value: 'no_practice', label: "I don't have a practice" },
] as const;

const FINANCE_IMPACT_API: Record<string, string> = {
  yes: 'significantly',
  possibly: 'slightly',
  no: 'not_at_all',
  no_practice: 'not_at_all',
};

const ANXIOUS_OPTIONS = [
  { value: 'yes', label: 'Yes' },
  { value: 'a_little', label: 'A little' },
  { value: 'no', label: 'No' },
] as const;

const ANXIOUS_API: Record<string, string> = {
  yes: 'yes',
  a_little: 'unsure',
  no: 'no',
};

export function DashSpiritCalmCheckup() {
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const {
    waterfallContext,
    loadFluencyContext,
    onCueActionRoute,
    onCueDismiss,
  } = useCheckupFluencyNavigation('spirit', userTier);
  const [hadMoments, setHadMoments] = useState<boolean | null>(null);
  const [meditationMinutes, setMeditationMinutes] = useState(0);
  const [affectedFinances, setAffectedFinances] = useState<string | null>(null);
  const [financiallyAnxious, setFinanciallyAnxious] = useState<string | null>(null);
  const [spiritualConnection, setSpiritualConnection] = useState<boolean | null>(null);
  const [showBreathing, setShowBreathing] = useState(false);
  const [pendingNavigate, setPendingNavigate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const canSubmit = useMemo(
    () => hadMoments != null && affectedFinances != null && financiallyAnxious != null,
    [affectedFinances, financiallyAnxious, hadMoments]
  );

  const finishFlow = useCallback(() => {
    setShowBreathing(false);
    setPendingNavigate(true);
    setSuccessMessage('Check-in saved');
    void loadFluencyContext();
  }, [loadFluencyContext]);

  const submit = useCallback(async () => {
    if (hadMoments == null || affectedFinances == null || financiallyAnxious == null) return;
    setBusy(true);
    setError(null);
    try {
      await submitSpiritCalmCheckin({
        practice_had_moments: hadMoments,
        practice_affected_finances: FINANCE_IMPACT_API[affectedFinances] ?? 'not_at_all',
        spirit_financially_anxious: ANXIOUS_API[financiallyAnxious] ?? 'no',
      });
      if (financiallyAnxious === 'yes' || financiallyAnxious === 'a_little') {
        setShowBreathing(true);
      } else {
        finishFlow();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [affectedFinances, financiallyAnxious, finishFlow, hadMoments]);

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
      <BreathingExerciseModal open={showBreathing} onComplete={finishFlow} />

      {successMessage ? (
        <ArticleRecommendationStrip
          heading="Free game for you"
          subheading="Based on your check-in"
          className="mt-4"
        />
      ) : null}

      {successMessage && waterfallContext && pendingNavigate ? (
        <FluencyCue
          context={waterfallContext}
          domain="spirit"
          userTier={userTier}
          onActionRoute={onCueActionRoute}
          onDismiss={onCueDismiss}
        />
      ) : null}

      {!successMessage && !showBreathing ? (
        <div
          className="dash-checkup-theme max-h-[70vh] overflow-y-auto rounded-2xl border bg-white p-6 shadow-sm sm:max-h-none sm:overflow-visible sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          <CheckupForm>
            <CheckupQuestionBlock>
              <QuestionLabel>
                Did you have any moments of stillness or intentional calm this week?
              </QuestionLabel>
              <YesNoButtons value={hadMoments} onChange={setHadMoments} />
            </CheckupQuestionBlock>

            {hadMoments === true ? (
              <CheckupQuestionBlock conditional>
                <QuestionLabel>Approximately how many minutes total this week?</QuestionLabel>
                <NumericStepper
                  min={0}
                  max={300}
                  value={meditationMinutes}
                  onChange={setMeditationMinutes}
                />
              </CheckupQuestionBlock>
            ) : null}

            <CheckupQuestionBlock>
              <QuestionLabel>
                Did your practice — or the absence of it — affect how you handled stress or money
                decisions this week?
              </QuestionLabel>
              <OptionButtons
                options={FINANCE_IMPACT_OPTIONS}
                value={affectedFinances}
                onChange={setAffectedFinances}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>Did you feel financially anxious or avoidant this week?</QuestionLabel>
              <OptionButtons
                options={ANXIOUS_OPTIONS}
                value={financiallyAnxious}
                onChange={setFinanciallyAnxious}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                Did your faith, values, or sense of purpose inform any decision you made this week?
              </QuestionLabel>
              <YesNoButtons value={spiritualConnection} onChange={setSpiritualConnection} />
              <SkipLink onClick={() => setSpiritualConnection(null)} />
            </CheckupQuestionBlock>

            <SubmitButton busy={busy} disabled={!canSubmit} onClick={() => void submit()} />
          </CheckupForm>
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashSpiritCalmCheckup;
