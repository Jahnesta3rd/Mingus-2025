import { useCallback, useMemo, useState } from 'react';
import { CheckupWrapperShell } from './CheckupWrapperShell';
import ArticleRecommendationStrip from '../ArticleRecommendationStrip';
import { submitMindMoodCheckin } from './checkupShared';
import { useCheckupFluencyNavigation } from './useCheckupFluencyNavigation';
import {
  CheckupForm,
  CheckupQuestionBlock,
  EmojiMoodPicker,
  MultiSelectChips,
  OptionButtons,
  QuestionLabel,
  RangeStep,
  SubmitButton,
  YesNoButtons,
} from './dashCheckupUi';
import { useLifeLedger } from '../../hooks/useLifeLedger';
import { useAuth } from '../../hooks/useAuth';
import {
  deriveUserTier,
  FluencyCue,
} from '../fluency';

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

export function DashMindMoodCheckup() {
  const { isAuthenticated, user } = useAuth();
  const { profile, loading: profileLoading } = useLifeLedger(isAuthenticated);
  const userTier = deriveUserTier(user);
  const {
    waterfallContext,
    loadFluencyContext,
    onCueActionRoute,
    onCueDismiss,
  } = useCheckupFluencyNavigation('mood', userTier);
  const [moodRating, setMoodRating] = useState(3);
  const [stressLevel, setStressLevel] = useState(3);
  const [triggerPurchase, setTriggerPurchase] = useState<string | null>(null);
  const [avoidedFinances, setAvoidedFinances] = useState<boolean | null>(null);
  const [copingMethods, setCopingMethods] = useState<string[]>([]);
  const [spendingIntentionality, setSpendingIntentionality] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const toggleCoping = (label: string) => {
    setCopingMethods((prev) => {
      if (label === 'Nothing worked') {
        return prev.includes(label) ? [] : [label];
      }
      const without = prev.filter((x) => x !== 'Nothing worked');
      return without.includes(label)
        ? without.filter((x) => x !== label)
        : [...without, label];
    });
  };

  const canSubmit = useMemo(
    () => triggerPurchase != null && avoidedFinances != null && copingMethods.length > 0,
    [avoidedFinances, copingMethods.length, triggerPurchase]
  );

  const submit = useCallback(async () => {
    if (triggerPurchase == null || avoidedFinances == null || copingMethods.length === 0) return;
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
      void loadFluencyContext();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed');
    } finally {
      setBusy(false);
    }
  }, [avoidedFinances, copingMethods, loadFluencyContext, spendingIntentionality, triggerPurchase]);

  const lastAt = profile?.mood_stress_triggered_purchase != null ? profile.updated_at : null;

  return (
    <CheckupWrapperShell
      title="Mind & Mood Check-in"
      score={null}
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
          domain="mood"
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
              <QuestionLabel>What&apos;s your overall mood been this week?</QuestionLabel>
              <EmojiMoodPicker value={moodRating} onChange={setMoodRating} />
            </CheckupQuestionBlock>

            <RangeStep
              label="How would you rate your stress level this week?"
              min={1}
              max={5}
              value={stressLevel}
              onChange={setStressLevel}
              lowLabel="Calm"
              highLabel="Overwhelmed"
            />

            <CheckupQuestionBlock>
              <QuestionLabel>
                Think back to the last time you bought something you didn&apos;t plan to. What was
                going on for you right before?
              </QuestionLabel>
              <OptionButtons
                options={TRIGGER_OPTIONS}
                value={triggerPurchase}
                onChange={setTriggerPurchase}
              />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                Did you avoid looking at your finances at any point this week?
              </QuestionLabel>
              <YesNoButtons value={avoidedFinances} onChange={setAvoidedFinances} />
            </CheckupQuestionBlock>

            <CheckupQuestionBlock>
              <QuestionLabel>
                What helped you manage your energy or stress this week, if anything?
              </QuestionLabel>
              <MultiSelectChips
                options={COPING_OPTIONS}
                selected={copingMethods}
                onToggle={toggleCoping}
              />
            </CheckupQuestionBlock>

            <RangeStep
              label="How intentional were your spending decisions this week?"
              min={1}
              max={5}
              value={spendingIntentionality}
              onChange={setSpendingIntentionality}
              lowLabel="All reactive"
              highLabel="All intentional"
            />

            <SubmitButton busy={busy} disabled={!canSubmit} onClick={() => void submit()} />
          </CheckupForm>
        </div>
      ) : null}
    </CheckupWrapperShell>
  );
}

export default DashMindMoodCheckup;
