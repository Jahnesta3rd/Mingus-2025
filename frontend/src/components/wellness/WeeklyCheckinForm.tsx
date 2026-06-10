import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { deriveUserTier } from '../fluency';
import {
  CheckupForm,
  CheckupQuestionBlock,
  DollarInput,
  EmojiMoodPicker,
  NumericStepper,
  QuestionLabel,
  RangeStep,
  ScaleButtons,
  SkipLink,
  SubmitButton,
  YesNoButtons,
} from '../checkups/dashCheckupUi';
import '../checkups/checkupDesignTokens.css';

export interface RotatingQuestion {
  id: string;
  domain: string;
  text: string;
  anchor: boolean;
  scale_labels: Record<string, string>;
}

export interface WeeklyCheckinSubmitResponse {
  success: boolean;
  week_number: number;
  year?: number;
  stress_spend_signal: boolean;
}

export interface WeeklyCheckinFormProps {
  onSuccess?: (response: WeeklyCheckinSubmitResponse) => void;
  onCancel?: () => void;
  className?: string;
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

function parseScaleLabels(labels: Record<string, string>) {
  const min = Number(Object.keys(labels).sort()[0] ?? '1');
  const max = Number(Object.keys(labels).sort().slice(-1)[0] ?? '5');
  return { min, max, labels: Object.fromEntries(Object.entries(labels).map(([k, v]) => [Number(k), v])) as Record<number, string> };
}

function RotatingQuestionBlock({
  question,
  value,
  onChange,
}: {
  question: RotatingQuestion;
  value: number;
  onChange: (v: number) => void;
}) {
  const { min, max, labels } = parseScaleLabels(question.scale_labels);
  return (
    <CheckupQuestionBlock>
      <QuestionLabel>{question.text}</QuestionLabel>
      <ScaleButtons min={min} max={max} value={value} onChange={onChange} labels={labels} />
    </CheckupQuestionBlock>
  );
}

export const WeeklyCheckinForm: React.FC<WeeklyCheckinFormProps> = ({
  onSuccess,
  onCancel,
  className = '',
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userTier = deriveUserTier(user);
  const showB2 = userTier === 'mid_tier' || userTier === 'professional';
  const showB3 = userTier === 'professional';

  const [weekNumber, setWeekNumber] = useState<number | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [questions, setQuestions] = useState<RotatingQuestion[]>([]);
  const [questionsLoading, setQuestionsLoading] = useState(true);
  const [questionsError, setQuestionsError] = useState<string | null>(null);

  const [moodRating, setMoodRating] = useState(3);
  const [stressLevel, setStressLevel] = useState(5);
  const [activityFrequency, setActivityFrequency] = useState(0);
  const [avgSleepHours, setAvgSleepHours] = useState('7');
  const [relationshipQuality, setRelationshipQuality] = useState(3);
  const [meaningfulTime, setMeaningfulTime] = useState<boolean | null>(null);
  const [partnerSpendingUnplanned, setPartnerSpendingUnplanned] = useState<boolean | null>(null);
  const [partnerSpendingAmount, setPartnerSpendingAmount] = useState('');
  const [financialCommunication, setFinancialCommunication] = useState(3);
  const [unexpectedKidSpending, setUnexpectedKidSpending] = useState<boolean | null>(null);
  const [unexpectedKidAmount, setUnexpectedKidAmount] = useState('');
  const [practiceGrounding, setPracticeGrounding] = useState<boolean | null>(null);
  const [meditationMinutes, setMeditationMinutes] = useState(0);
  const [spiritualConnection, setSpiritualConnection] = useState<boolean | null>(null);
  const [spendingDiscipline, setSpendingDiscipline] = useState(5);
  const [spendingTrigger, setSpendingTrigger] = useState('');
  const [discretionarySpending, setDiscretionarySpending] = useState('');
  const [socialSpendingUnplanned, setSocialSpendingUnplanned] = useState<boolean | null>(null);
  const [socialSpendingAmount, setSocialSpendingAmount] = useState('');
  const [financialReflection, setFinancialReflection] = useState('');
  const [weeklyReflectionChange, setWeeklyReflectionChange] = useState('');
  const [rotatingAnswers, setRotatingAnswers] = useState<Record<string, number>>({});

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitResult, setSubmitResult] = useState<WeeklyCheckinSubmitResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setQuestionsLoading(true);
    setQuestionsError(null);
    fetch('/api/wellness/weekly-checkin/questions', { credentials: 'include', headers: authHeaders() })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.message || err.error || res.statusText);
        }
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        setWeekNumber(data.week_number ?? null);
        setYear(data.year ?? null);
        const qs: RotatingQuestion[] = data.questions ?? [];
        setQuestions(qs);
        const defaults: Record<string, number> = {};
        qs.forEach((q) => {
          defaults[q.id] = 3;
        });
        setRotatingAnswers(defaults);
      })
      .catch((e) => {
        if (!cancelled) setQuestionsError(e instanceof Error ? e.message : 'Failed to load questions');
      })
      .finally(() => {
        if (!cancelled) setQuestionsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const questionsByDomain = useMemo(() => {
    const map: Record<string, RotatingQuestion[]> = {};
    questions.forEach((q) => {
      if (!map[q.domain]) map[q.domain] = [];
      map[q.domain].push(q);
    });
    return map;
  }, [questions]);

  const setRotatingAnswer = useCallback((id: string, value: number) => {
    setRotatingAnswers((prev) => ({ ...prev, [id]: value }));
  }, []);

  const handleSubmit = useCallback(async () => {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload: Record<string, unknown> = {
        week_number: weekNumber,
        year,
        mood_rating: moodRating * 20,
        stress_level: stressLevel,
        activity_frequency: activityFrequency,
        avg_sleep_hours: avgSleepHours.trim() ? parseFloat(avgSleepHours) : null,
        relationship_temperature: relationshipQuality,
        meaningful_time_with_people: meaningfulTime,
        spending_discipline_rating: spendingDiscipline * 10,
        rotating_question_answers: Object.entries(rotatingAnswers).map(([question_id, answer]) => ({
          question_id,
          answer,
        })),
      };

      if (showB2) {
        payload.partner_spending_unplanned = partnerSpendingUnplanned;
        payload.partner_spending_amount = partnerSpendingAmount.trim()
          ? parseFloat(partnerSpendingAmount)
          : null;
        payload.financial_communication_with_partner = financialCommunication * 20;
      }
      if (showB3) {
        payload.unexpected_kid_spending = unexpectedKidSpending;
        payload.unexpected_kid_amount = unexpectedKidAmount.trim()
          ? parseFloat(unexpectedKidAmount)
          : null;
      }
      if (practiceGrounding != null) {
        payload.practice_felt_grounding = practiceGrounding;
        if (practiceGrounding) {
          payload.meditation_minutes_total = meditationMinutes;
        }
      }
      if (spiritualConnection != null) {
        payload.felt_spiritual_connection = spiritualConnection;
      }
      if (spendingDiscipline <= 5 && spendingTrigger.trim()) {
        payload.spending_trigger_description = spendingTrigger.trim();
      }
      if (discretionarySpending.trim()) {
        payload.discretionary_spending = parseFloat(discretionarySpending);
      }
      if (socialSpendingUnplanned != null) {
        payload.social_spending_unplanned = socialSpendingUnplanned;
        payload.social_spending_amount = socialSpendingAmount.trim()
          ? parseFloat(socialSpendingAmount)
          : null;
      }
      if (financialReflection.trim()) {
        payload.financial_reflection = financialReflection.trim();
      }
      if (weeklyReflectionChange.trim()) {
        payload.weekly_reflection_change = weeklyReflectionChange.trim();
      }

      const res = await fetch('/api/wellness/weekly-checkin', {
        method: 'POST',
        credentials: 'include',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.error || res.statusText);
      }
      const data: WeeklyCheckinSubmitResponse = await res.json();
      setSubmitResult(data);
      onSuccess?.(data);
      window.setTimeout(() => navigate('/dashboard'), 2000);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  }, [
    weekNumber,
    year,
    moodRating,
    stressLevel,
    activityFrequency,
    avgSleepHours,
    relationshipQuality,
    meaningfulTime,
    spendingDiscipline,
    spendingTrigger,
    discretionarySpending,
    socialSpendingUnplanned,
    socialSpendingAmount,
    financialReflection,
    weeklyReflectionChange,
    rotatingAnswers,
    showB2,
    showB3,
    partnerSpendingUnplanned,
    partnerSpendingAmount,
    financialCommunication,
    unexpectedKidSpending,
    unexpectedKidAmount,
    practiceGrounding,
    meditationMinutes,
    spiritualConnection,
    onSuccess,
    navigate,
  ]);

  if (questionsLoading) {
    return (
      <div className={`dash-checkup-root flex min-h-[40vh] items-center justify-center p-8 ${className}`}>
        <p className="flex items-center gap-2 text-sm" style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}>
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
          Loading your check-in…
        </p>
      </div>
    );
  }

  if (questionsError) {
    return (
      <div className={`dash-checkup-root p-6 ${className}`}>
        <p role="alert" className="text-sm text-red-700">
          {questionsError}
        </p>
      </div>
    );
  }

  if (submitResult) {
    return (
      <div className={`dash-checkup-root p-6 ${className}`}>
        <div
          className="rounded-2xl border bg-white p-6 shadow-sm"
          style={{ borderColor: 'var(--line)' }}
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center gap-3" style={{ color: 'var(--mingus-purple)' }}>
            <CheckCircle2 className="h-8 w-8" aria-hidden />
            <h2 className="text-xl font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
              Check-in saved
            </h2>
          </div>
          <p className="mt-2 text-sm" style={{ color: 'var(--ink-mid)' }}>
            Week {submitResult.week_number} recorded. Redirecting to dashboard…
          </p>
          {submitResult.stress_spend_signal ? (
            <p className="mt-4 text-sm">
              <Link
                to="/dashboard/waterfall"
                className="font-semibold underline-offset-2 hover:underline"
                style={{ color: 'var(--mingus-purple)' }}
              >
                See how stress may be affecting your spending →
              </Link>
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  const renderDomainQuestions = (domain: string) =>
    (questionsByDomain[domain] ?? []).map((q) => (
      <RotatingQuestionBlock
        key={q.id}
        question={q}
        value={rotatingAnswers[q.id] ?? 3}
        onChange={(v) => setRotatingAnswer(q.id, v)}
      />
    ));

  return (
    <div className={`dash-checkup-root ${className}`}>
      <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            className="mb-4 text-[13px] font-semibold underline-offset-2 hover:underline"
            style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
          >
            ← Back
          </button>
        ) : (
          <Link
            to="/dashboard/vibe-checkups"
            className="mb-4 inline-block text-[13px] font-semibold underline-offset-2 hover:underline"
            style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
          >
            ← Check-up hub
          </Link>
        )}

        <header className="mb-8 space-y-1">
          <h1 className="text-[22px] font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
            Weekly Wellness Check-in
          </h1>
          <p className="text-[13px]" style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}>
            Week {weekNumber ?? '—'} · ~5 minutes
          </p>
        </header>

        <div
          className="dash-checkup-theme max-h-[calc(100vh-8rem)] overflow-y-auto rounded-2xl border bg-white p-6 shadow-sm sm:max-h-none sm:overflow-visible sm:p-8"
          style={{ borderColor: 'var(--line)' }}
        >
          {submitError ? (
            <div role="alert" className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {submitError}
            </div>
          ) : null}

          <CheckupForm>
            {/* Section A — Self-State */}
            <section className="space-y-6">
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
                How you&apos;re doing
              </h2>
              <CheckupQuestionBlock>
                <QuestionLabel>How was your mood this week?</QuestionLabel>
                <EmojiMoodPicker value={moodRating} onChange={setMoodRating} />
              </CheckupQuestionBlock>
              <RangeStep
                label="Stress level"
                min={1}
                max={10}
                value={stressLevel}
                onChange={setStressLevel}
                lowLabel="Calm"
                highLabel="Overwhelmed"
              />
              <CheckupQuestionBlock>
                <QuestionLabel>How many times did you move intentionally this week?</QuestionLabel>
                <NumericStepper value={activityFrequency} onChange={setActivityFrequency} min={0} max={14} />
              </CheckupQuestionBlock>
              <CheckupQuestionBlock>
                <QuestionLabel>Average sleep hours per night</QuestionLabel>
                <input
                  type="number"
                  min={0}
                  max={24}
                  step={0.25}
                  value={avgSleepHours}
                  onChange={(e) => setAvgSleepHours(e.target.value)}
                  className="w-full rounded-xl border px-4 py-3 text-sm"
                  style={{ borderColor: 'var(--line)' }}
                  aria-label="Average sleep hours"
                />
              </CheckupQuestionBlock>
              {renderDomainQuestions('self_state')}
            </section>

            {/* Career domain (between A and B) */}
            {(questionsByDomain.career_purpose ?? []).length > 0 ? (
              <section className="space-y-6 border-t pt-6" style={{ borderColor: 'var(--line)' }}>
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
                  Career &amp; purpose
                </h2>
                {renderDomainQuestions('career_purpose')}
              </section>
            ) : null}

            {/* Section B — Relationships */}
            <section className="space-y-6 border-t pt-6" style={{ borderColor: 'var(--line)' }}>
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
                Your people
              </h2>
              <CheckupQuestionBlock>
                <QuestionLabel>Relationship quality this week</QuestionLabel>
                <ScaleButtons
                  min={1}
                  max={5}
                  value={relationshipQuality}
                  onChange={setRelationshipQuality}
                  labels={{ 1: 'Strained', 5: 'Thriving' }}
                />
              </CheckupQuestionBlock>
              <CheckupQuestionBlock>
                <QuestionLabel>Did you spend meaningful time with people who matter?</QuestionLabel>
                <YesNoButtons value={meaningfulTime} onChange={setMeaningfulTime} />
              </CheckupQuestionBlock>
              {showB2 ? (
                <>
                  <CheckupQuestionBlock>
                    <QuestionLabel>Did your partner spend money you hadn&apos;t planned for?</QuestionLabel>
                    <YesNoButtons value={partnerSpendingUnplanned} onChange={setPartnerSpendingUnplanned} />
                  </CheckupQuestionBlock>
                  {partnerSpendingUnplanned ? (
                    <CheckupQuestionBlock conditional>
                      <QuestionLabel>Approximate amount</QuestionLabel>
                      <DollarInput
                        value={partnerSpendingAmount}
                        onChange={setPartnerSpendingAmount}
                        placeholder="Amount in dollars"
                      />
                    </CheckupQuestionBlock>
                  ) : null}
                  <CheckupQuestionBlock>
                    <QuestionLabel>Financial communication with partner</QuestionLabel>
                    <ScaleButtons
                      min={1}
                      max={5}
                      value={financialCommunication}
                      onChange={setFinancialCommunication}
                      labels={{ 1: 'Poor', 5: 'Great' }}
                    />
                  </CheckupQuestionBlock>
                </>
              ) : null}
              {showB3 ? (
                <>
                  <CheckupQuestionBlock>
                    <QuestionLabel>Any unexpected kid-related spending this week?</QuestionLabel>
                    <YesNoButtons value={unexpectedKidSpending} onChange={setUnexpectedKidSpending} />
                  </CheckupQuestionBlock>
                  {unexpectedKidSpending ? (
                    <CheckupQuestionBlock conditional>
                      <QuestionLabel>Approximate amount</QuestionLabel>
                      <DollarInput value={unexpectedKidAmount} onChange={setUnexpectedKidAmount} />
                    </CheckupQuestionBlock>
                  ) : null}
                </>
              ) : null}
              {renderDomainQuestions('relationships')}
            </section>

            {/* Section C — Practice & Spirit */}
            <section className="space-y-6 border-t pt-6" style={{ borderColor: 'var(--line)' }}>
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
                Your practice
              </h2>
              <CheckupQuestionBlock>
                <QuestionLabel>Did you take intentional stillness this week?</QuestionLabel>
                <YesNoButtons value={practiceGrounding} onChange={setPracticeGrounding} />
              </CheckupQuestionBlock>
              {practiceGrounding ? (
                <CheckupQuestionBlock conditional>
                  <QuestionLabel>Total minutes of meditation or stillness</QuestionLabel>
                  <NumericStepper value={meditationMinutes} onChange={setMeditationMinutes} min={0} max={300} step={5} />
                </CheckupQuestionBlock>
              ) : null}
              <CheckupQuestionBlock>
                <div className="flex items-start justify-between gap-2">
                  <QuestionLabel>Did you feel connected to faith or purpose?</QuestionLabel>
                  <SkipLink onClick={() => setSpiritualConnection(null)} />
                </div>
                <YesNoButtons
                  value={spiritualConnection}
                  onChange={setSpiritualConnection}
                />
              </CheckupQuestionBlock>
            </section>

            {/* Section D — Money & Spending */}
            <section className="space-y-6 border-t pt-6" style={{ borderColor: 'var(--line)' }}>
              <h2 className="text-lg font-semibold" style={{ fontFamily: 'Fraunces, Georgia, serif', color: 'var(--ink)' }}>
                Your money this week
              </h2>
              <RangeStep
                label="Spending discipline"
                min={1}
                max={10}
                value={spendingDiscipline}
                onChange={setSpendingDiscipline}
                lowLabel="Reactive"
                highLabel="Intentional"
              />
              {spendingDiscipline <= 5 ? (
                <CheckupQuestionBlock conditional>
                  <QuestionLabel>Did anything specific trigger that spending?</QuestionLabel>
                  <textarea
                    value={spendingTrigger}
                    onChange={(e) => setSpendingTrigger(e.target.value)}
                    rows={3}
                    className="w-full rounded-xl border px-4 py-3 text-sm"
                    style={{ borderColor: 'var(--line)' }}
                    placeholder="Optional — what was going on?"
                  />
                </CheckupQuestionBlock>
              ) : null}
              <CheckupQuestionBlock>
                <QuestionLabel>Discretionary spending this week (optional)</QuestionLabel>
                <DollarInput value={discretionarySpending} onChange={setDiscretionarySpending} />
              </CheckupQuestionBlock>
              <CheckupQuestionBlock>
                <QuestionLabel>Any unplanned social spending?</QuestionLabel>
                <YesNoButtons value={socialSpendingUnplanned} onChange={setSocialSpendingUnplanned} />
              </CheckupQuestionBlock>
              {socialSpendingUnplanned ? (
                <CheckupQuestionBlock conditional>
                  <QuestionLabel>Approximate amount</QuestionLabel>
                  <DollarInput value={socialSpendingAmount} onChange={setSocialSpendingAmount} />
                </CheckupQuestionBlock>
              ) : null}
              <CheckupQuestionBlock>
                <div className="flex items-start justify-between gap-2">
                  <QuestionLabel>Anything you want to note about money this week?</QuestionLabel>
                  <SkipLink onClick={() => setFinancialReflection('')} />
                </div>
                <textarea
                  value={financialReflection}
                  onChange={(e) => setFinancialReflection(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl border px-4 py-3 text-sm"
                  style={{ borderColor: 'var(--line)' }}
                />
              </CheckupQuestionBlock>
              {renderDomainQuestions('emotional_financial')}
            </section>

            {/* Closing — Z1 */}
            <section className="space-y-3 border-t pt-6" style={{ borderColor: 'var(--line)' }}>
              <div className="flex items-start justify-between gap-2">
                <QuestionLabel>
                  If you could change one thing about how you managed your money or your energy this week, what would it be?
                </QuestionLabel>
                <SkipLink onClick={() => setWeeklyReflectionChange('')} />
              </div>
              <textarea
                value={weeklyReflectionChange}
                onChange={(e) => setWeeklyReflectionChange(e.target.value)}
                rows={4}
                className="w-full rounded-xl border px-4 py-3 text-sm"
                style={{ borderColor: 'var(--line)' }}
              />
              <p className="text-xs italic" style={{ color: 'var(--ink-mid)' }}>
                This is just for you. Writing it is the point.
              </p>
            </section>

            <SubmitButton
              busy={submitting}
              disabled={meaningfulTime == null}
              onClick={() => void handleSubmit()}
              label="Save this week's check-in"
            />
          </CheckupForm>
        </div>
      </div>
    </div>
  );
};

export default WeeklyCheckinForm;
