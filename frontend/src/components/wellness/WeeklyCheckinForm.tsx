import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ChevronLeft, Loader2, CheckCircle2, DollarSign, TrendingUp, Sparkles } from 'lucide-react';
import { StepIndicator } from './StepIndicator';
import { SliderInput } from './SliderInput';
import { EmojiSelector } from './EmojiSelector';
import { NumberSelector } from './NumberSelector';
import { SpendingCategory } from './SpendingCategory';
import { ToggleWithAmount } from './ToggleWithAmount';
import type { CheckinPayload, CheckinResponse, SpendingBaselines } from './types';

const STORAGE_KEY = 'mingus_weekly_checkin_draft';
const TOTAL_STEPS = 6;

const MOOD_OPTIONS = [
  { emoji: '😢', value: 2, label: 'Low (2)' },
  { emoji: '😕', value: 4, label: 'Below average (4)' },
  { emoji: '😐', value: 6, label: 'Average (6)' },
  { emoji: '🙂', value: 8, label: 'Good (8)' },
  { emoji: '😊', value: 10, label: 'Great (10)' },
];

const SOCIAL_OPTIONS = [
  { label: '0', value: 0 },
  { label: '1-2', value: 2 },
  { label: '3-5', value: 4 },
  { label: '6-10', value: 8 },
  { label: '10+', value: 12 },
];

const MEDITATION_OPTIONS = [0, 15, 30, 45, 60, 90, 120];

const INTENSITY_OPTIONS = [
  { emoji: '🚶', value: 'light', label: 'Light' },
  { emoji: '🏃', value: 'moderate', label: 'Moderate' },
  { emoji: '💪', value: 'intense', label: 'Intense' },
] as const;

const defaultPayload = (): Partial<CheckinPayload> => ({
  exercise_days: 0,
  exercise_intensity: null,
  sleep_quality: 5,
  meditation_minutes: 0,
  stress_level: 5,
  overall_mood: 6,
  relationship_satisfaction: 5,
  social_interactions: 0,
  financial_stress: 5,
  spending_control: 5,
  groceries_estimate: null,
  dining_estimate: null,
  entertainment_estimate: null,
  shopping_estimate: null,
  transport_estimate: null,
  utilities_estimate: null,
  other_estimate: null,
  had_impulse_purchases: false,
  impulse_spending: null,
  had_stress_purchases: false,
  stress_spending: null,
  celebration_spending: null,
  biggest_unnecessary_purchase: null,
  biggest_unnecessary_category: null,
  wins: null,
  challenges: null,
});

export interface WeeklyCheckinFormProps {
  onSuccess?: (response: CheckinResponse) => void;
  onCancel?: () => void;
  className?: string;
}

export const WeeklyCheckinForm: React.FC<WeeklyCheckinFormProps> = ({
  onSuccess,
  onCancel,
  className = '',
}) => {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<Partial<CheckinPayload>>(defaultPayload);
  const [startTime] = useState(() => Date.now());
  const [baselines, setBaselines] = useState<SpendingBaselines | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CheckinResponse | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ form, step, startTime }));
    } catch {
      // ignore
    }
  }, [form, step, startTime]);

  // Load draft from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.form && typeof parsed.step === 'number') {
          setForm((prev) => ({ ...defaultPayload(), ...prev, ...parsed.form }));
          setStep(Math.min(parsed.step, TOTAL_STEPS));
        }
      }
    } catch {
      // ignore
    }
  }, []);

  // Fetch baselines for spending step
  useEffect(() => {
    let cancelled = false;
    fetch('/api/wellness/spending/baselines', { credentials: 'include' })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data) setBaselines(data);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const update = useCallback(<K extends keyof CheckinPayload>(key: K, value: CheckinPayload[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  }, []);

  const canProceedStep1 = form.exercise_days != null && form.sleep_quality != null &&
    (form.exercise_days === 0 || form.exercise_intensity != null);
  const canProceedStep2 = form.meditation_minutes != null && form.stress_level != null && form.overall_mood != null;
  const canProceedStep3 = form.relationship_satisfaction != null && form.social_interactions != null;
  const canProceedStep4 = form.financial_stress != null && form.spending_control != null;
  const canProceedStep5 = true;
  const canProceedStep6 = true;

  const canProceed = [
    canProceedStep1,
    canProceedStep2,
    canProceedStep3,
    canProceedStep4,
    canProceedStep5,
    canProceedStep6,
  ][step - 1];

  const handleNext = useCallback(() => {
    if (step < TOTAL_STEPS) setStep((s) => s + 1);
  }, [step]);

  const handleBack = useCallback(() => {
    if (step > 1) setStep((s) => s - 1);
  }, [step]);

  const buildPayload = useCallback((): CheckinPayload => {
    const completionTime = Math.round((Date.now() - startTime) / 1000);
    return {
      exercise_days: form.exercise_days ?? 0,
      exercise_intensity: form.exercise_days === 0 ? null : (form.exercise_intensity ?? null),
      sleep_quality: form.sleep_quality ?? 5,
      meditation_minutes: form.meditation_minutes ?? 0,
      stress_level: form.stress_level ?? 5,
      overall_mood: form.overall_mood ?? 6,
      relationship_satisfaction: form.relationship_satisfaction ?? 5,
      social_interactions: form.social_interactions ?? 0,
      financial_stress: form.financial_stress ?? 5,
      spending_control: form.spending_control ?? 5,
      groceries_estimate: form.groceries_estimate ?? null,
      dining_estimate: form.dining_estimate ?? null,
      entertainment_estimate: form.entertainment_estimate ?? null,
      shopping_estimate: form.shopping_estimate ?? null,
      transport_estimate: form.transport_estimate ?? null,
      utilities_estimate: form.utilities_estimate ?? null,
      other_estimate: form.other_estimate ?? null,
      had_impulse_purchases: form.had_impulse_purchases ?? false,
      impulse_spending: form.had_impulse_purchases ? (form.impulse_spending ?? null) : null,
      had_stress_purchases: form.had_stress_purchases ?? false,
      stress_spending: form.had_stress_purchases ? (form.stress_spending ?? null) : null,
      celebration_spending: form.celebration_spending ?? null,
      biggest_unnecessary_purchase: form.biggest_unnecessary_purchase ?? null,
      biggest_unnecessary_category: form.biggest_unnecessary_category ?? null,
      wins: form.wins && form.wins.trim() ? form.wins.trim().slice(0, 200) : null,
      challenges: form.challenges && form.challenges.trim() ? form.challenges.trim().slice(0, 200) : null,
      completion_time_seconds: completionTime,
    };
  }, [form, startTime]);

  const handleSubmit = useCallback(async () => {
    setError(null);
    setSubmitting(true);
    try {
      const payload = buildPayload();
      const res = await fetch('/api/wellness/checkin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.error || res.statusText || 'Submit failed');
      }
      const data: CheckinResponse = await res.json();
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {
        // ignore
      }
      setResult(data);
      onSuccess?.(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  }, [buildPayload, onSuccess]);

  const triggerHaptic = useCallback(() => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(10);
    }
  }, []);

  // Confirmation screen
  if (result) {
    const scores = result.wellness_scores;
    const variableSum = [form.groceries_estimate, form.dining_estimate, form.entertainment_estimate, form.shopping_estimate, form.transport_estimate, form.utilities_estimate, form.other_estimate]
      .filter((n): n is number => n != null && !Number.isNaN(n))
      .reduce((a, b) => a + b, 0);
    const totalSpent = variableSum + (form.impulse_spending ?? 0) + (form.stress_spending ?? 0);
    return (
      <div className={`rounded-2xl bg-slate-800/80 p-6 text-slate-100 animate-fade-in-up ${className}`}>
        <div className="flex items-center gap-3 text-violet-400 mb-6">
          <CheckCircle2 className="w-10 h-10" aria-hidden />
          <h2 className="text-xl font-bold">Check-in complete!</h2>
        </div>
        <section className="space-y-4" aria-label="Wellness scores">
          <h3 className="text-lg font-semibold text-slate-200">Wellness scores</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-700/50 rounded-xl p-3">
              <span className="text-slate-400 text-sm">Physical</span>
              <p className="text-xl font-bold text-violet-400">{Math.round(scores.physical_score ?? 0)}</p>
            </div>
            <div className="bg-slate-700/50 rounded-xl p-3">
              <span className="text-slate-400 text-sm">Mental</span>
              <p className="text-xl font-bold text-violet-400">{Math.round(scores.mental_score ?? 0)}</p>
            </div>
            <div className="bg-slate-700/50 rounded-xl p-3">
              <span className="text-slate-400 text-sm">Relational</span>
              <p className="text-xl font-bold text-violet-400">{Math.round(scores.relational_score ?? 0)}</p>
            </div>
            <div className="bg-slate-700/50 rounded-xl p-3">
              <span className="text-slate-400 text-sm">Financial feeling</span>
              <p className="text-xl font-bold text-violet-400">{Math.round(scores.financial_feeling_score ?? 0)}</p>
            </div>
          </div>
          <div className="bg-violet-900/30 rounded-xl p-4 border border-violet-500/30">
            <span className="text-slate-300 text-sm">Overall wellness</span>
            <p className="text-2xl font-bold text-violet-400">{Math.round(scores.overall_wellness_score ?? 0)}</p>
          </div>
        </section>
        <section className="mt-6 space-y-2" aria-label="Spending summary">
          <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <DollarSign className="w-5 h-5" aria-hidden /> Total spending this week
          </h3>
          <p className="text-2xl font-bold text-slate-100">${totalSpent.toFixed(0)}</p>
          {baselines && baselines.weeks_of_data >= 3 && (baselines.avg_total ?? 0) > 0 && (
            <p className="text-slate-400 text-sm">
              Your average: ${Math.round(baselines.avg_total ?? 0)} — {totalSpent > (baselines.avg_total ?? 0) ? 'More' : 'Less'} than usual this week
            </p>
          )}
        </section>
        {result.streak_info && (
          <section className="mt-4 flex items-center gap-2 text-slate-300" aria-label="Streak">
            <TrendingUp className="w-5 h-5 text-violet-400" aria-hidden />
            <span>Streak: {result.streak_info.current_streak} week{result.streak_info.current_streak !== 1 ? 's' : ''}</span>
          </section>
        )}
        {result.insights && result.insights.length > 0 && (
          <section className="mt-6 space-y-2" aria-label="Insights">
            <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-violet-400" aria-hidden /> Insights
            </h3>
            <ul className="space-y-2">
              {result.insights.slice(0, 3).map((insight, i) => (
                <li key={i} className="bg-slate-700/50 rounded-xl p-3 text-sm text-slate-200">
                  <strong className="text-violet-300">{insight.title}</strong>
                  <p className="mt-1">{insight.message}</p>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    );
  }

  return (
    <div className={`rounded-2xl bg-slate-800/80 p-6 text-slate-100 ${className}`}>
      <form
        ref={formRef}
        onSubmit={(e) => { e.preventDefault(); if (step === TOTAL_STEPS) handleSubmit(); else handleNext(); }}
        className="space-y-6"
        noValidate
        aria-label="Weekly check-in form"
      >
        <StepIndicator currentStep={step} totalSteps={TOTAL_STEPS} ariaLabel={`Step ${step} of ${TOTAL_STEPS}`} />

        {error && (
          <div role="alert" className="rounded-xl bg-red-900/30 border border-red-500/50 text-red-200 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Physical */}
        {step === 1 && (
          <div className="space-y-6 animate-fade-in-up" role="group" aria-label="Physical wellness">
            <NumberSelector
              options={[0, 1, 2, 3, 4, 5, 6, 7]}
              value={form.exercise_days ?? null}
              onChange={(v) => { update('exercise_days', v); triggerHaptic(); }}
              label="How many days did you exercise this week?"
              id="exercise_days"
            />
            {form.exercise_days !== 0 && (
              <div className="space-y-3">
                <div className="text-slate-200 font-medium">How intense were your workouts?</div>
                <div className="flex flex-wrap gap-2">
                  {INTENSITY_OPTIONS.map((opt) => {
                    const isSelected = form.exercise_intensity === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => { update('exercise_intensity', opt.value); triggerHaptic(); }}
                        className={`min-h-[44px] px-4 rounded-xl text-base font-semibold flex items-center gap-2 transition-all focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900 ${isSelected ? 'bg-violet-600 text-white ring-2 ring-violet-400' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}
                        aria-pressed={isSelected}
                        aria-label={opt.label}
                      >
                        <span aria-hidden>{opt.emoji}</span> {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
            <SliderInput
              id="sleep_quality"
              label="How was your sleep quality?"
              value={form.sleep_quality ?? 5}
              onChange={(v) => update('sleep_quality', v)}
              leftEmoji="😫"
              rightEmoji="😴"
              min={1}
              max={10}
            />
          </div>
        )}

        {/* Step 2: Mental */}
        {step === 2 && (
          <div className="space-y-6 animate-fade-in-up" role="group" aria-label="Mental wellness">
            <NumberSelector
              options={MEDITATION_OPTIONS.map((n) => n === 120 ? { label: '120+', value: 120 } : n)}
              value={form.meditation_minutes ?? null}
              onChange={(v) => { update('meditation_minutes', v); triggerHaptic(); }}
              label="Minutes of meditation/prayer/mindfulness?"
              id="meditation_minutes"
            />
            <SliderInput
              id="stress_level"
              label="What was your average stress level?"
              value={form.stress_level ?? 5}
              onChange={(v) => update('stress_level', v)}
              leftEmoji="😌"
              rightEmoji="😰"
              min={1}
              max={10}
            />
            <EmojiSelector
              options={MOOD_OPTIONS}
              value={form.overall_mood ?? null}
              onChange={(v) => { update('overall_mood', v); triggerHaptic(); }}
              label="Overall mood this week?"
              id="overall_mood"
            />
          </div>
        )}

        {/* Step 3: Relationships */}
        {step === 3 && (
          <div className="space-y-6 animate-fade-in-up" role="group" aria-label="Relationships">
            <SliderInput
              id="relationship_satisfaction"
              label="How satisfied are you with your key relationships?"
              value={form.relationship_satisfaction ?? 5}
              onChange={(v) => update('relationship_satisfaction', v)}
              leftEmoji="💔"
              rightEmoji="💖"
              min={1}
              max={10}
            />
            <NumberSelector
              options={SOCIAL_OPTIONS}
              value={form.social_interactions ?? null}
              onChange={(v) => { update('social_interactions', v); triggerHaptic(); }}
              label="Meaningful social interactions this week?"
              id="social_interactions"
            />
          </div>
        )}

        {/* Step 4: Financial feelings */}
        {step === 4 && (
          <div className="space-y-6 animate-fade-in-up" role="group" aria-label="Financial feelings">
            <SliderInput
              id="financial_stress"
              label="How stressed about money were you this week?"
              value={form.financial_stress ?? 5}
              onChange={(v) => update('financial_stress', v)}
              leftEmoji="😌"
              rightEmoji="😰"
              min={1}
              max={10}
            />
            <SliderInput
              id="spending_control"
              label="How in control of spending did you feel?"
              value={form.spending_control ?? 5}
              onChange={(v) => update('spending_control', v)}
              leftEmoji="😬"
              rightEmoji="💪"
              min={1}
              max={10}
            />
          </div>
        )}

        {/* Step 5: Spending */}
        {step === 5 && (
          <div className="space-y-6 animate-fade-in-up" role="group" aria-label="Weekly spending">
            <div>
              <h3 className="text-lg font-bold text-slate-100">Let&apos;s estimate your spending this week 💸</h3>
              <p className="text-slate-400 text-sm mt-1">Rough estimates are fine! This helps us find patterns.</p>
            </div>
            <SpendingCategory id="groceries" label="Groceries" value={form.groceries_estimate ?? null} onChange={(v) => update('groceries_estimate', v)} baselineHint={baselines?.avg_groceries} placeholder="~$100" />
            <SpendingCategory id="dining" label="Dining & Takeout" value={form.dining_estimate ?? null} onChange={(v) => update('dining_estimate', v)} baselineHint={baselines?.avg_dining} placeholder="~$50" />
            <SpendingCategory id="entertainment" label="Entertainment" value={form.entertainment_estimate ?? null} onChange={(v) => update('entertainment_estimate', v)} baselineHint={baselines?.avg_entertainment} placeholder="~$30" />
            <SpendingCategory id="shopping" label="Shopping" value={form.shopping_estimate ?? null} onChange={(v) => update('shopping_estimate', v)} baselineHint={baselines?.avg_shopping} placeholder="~$50" />
            <SpendingCategory id="transport" label="Gas & Transport" value={form.transport_estimate ?? null} onChange={(v) => update('transport_estimate', v)} baselineHint={baselines?.avg_transport} placeholder="~$40" />
            <SpendingCategory id="other" label="Other" value={form.other_estimate ?? null} onChange={(v) => update('other_estimate', v)} placeholder="~$20" />
            <hr className="border-slate-600" />
            <ToggleWithAmount
              label="Any impulse purchases this week?"
              isYes={form.had_impulse_purchases ?? false}
              amount={form.impulse_spending ?? null}
              onToggle={(v) => update('had_impulse_purchases', v)}
              onAmountChange={(v) => update('impulse_spending', v)}
              id="impulse"
            />
            <ToggleWithAmount
              label="Any stress-related spending?"
              isYes={form.had_stress_purchases ?? false}
              amount={form.stress_spending ?? null}
              onToggle={(v) => update('had_stress_purchases', v)}
              onAmountChange={(v) => update('stress_spending', v)}
              id="stress"
            />
            <div className="space-y-2">
              <label htmlFor="biggest_regret" className="block text-slate-400 text-sm">Optional: Biggest purchase you regret?</label>
              <div className="flex gap-2 flex-wrap">
                <input
                  id="biggest_regret"
                  type="text"
                  inputMode="decimal"
                  placeholder="Amount"
                  value={form.biggest_unnecessary_purchase != null ? String(form.biggest_unnecessary_purchase) : ''}
                  onChange={(e) => {
                    const v = e.target.value.replace(/[^0-9.]/g, '');
                    update('biggest_unnecessary_purchase', v === '' ? null : parseFloat(v) || null);
                  }}
                  className="min-h-[44px] w-24 px-3 rounded-xl bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400 focus:border-violet-500"
                  aria-label="Amount"
                />
                <select
                  value={form.biggest_unnecessary_category ?? ''}
                  onChange={(e) => update('biggest_unnecessary_category', e.target.value || null)}
                  className="min-h-[44px] flex-1 min-w-[120px] px-3 rounded-xl bg-slate-700 border border-slate-600 text-slate-100 focus:border-violet-500"
                  aria-label="Category"
                >
                  <option value="">Category</option>
                  {['groceries', 'dining', 'entertainment', 'shopping', 'transport', 'other'].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Step 6: Reflection */}
        {step === 6 && (
          <div className="space-y-6 animate-fade-in-up" role="group" aria-label="Reflection">
            <div>
              <label htmlFor="wins" className="block text-slate-200 font-medium mb-2">One win from this week?</label>
              <textarea
                id="wins"
                maxLength={200}
                placeholder="e.g. Stuck to my budget on groceries"
                value={form.wins ?? ''}
                onChange={(e) => update('wins', e.target.value)}
                className="w-full min-h-[88px] px-4 py-3 rounded-xl bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
                aria-label="One win from this week"
              />
              <p className="text-slate-500 text-xs mt-1">{(form.wins ?? '').length}/200</p>
            </div>
            <div>
              <label htmlFor="challenges" className="block text-slate-200 font-medium mb-2">One challenge you faced?</label>
              <textarea
                id="challenges"
                maxLength={200}
                placeholder="e.g. Impulse bought takeout twice"
                value={form.challenges ?? ''}
                onChange={(e) => update('challenges', e.target.value)}
                className="w-full min-h-[88px] px-4 py-3 rounded-xl bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
                aria-label="One challenge you faced"
              />
              <p className="text-slate-500 text-xs mt-1">{(form.challenges ?? '').length}/200</p>
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-4">
          {step > 1 && (
            <button
              type="button"
              onClick={handleBack}
              className="min-h-[44px] px-4 rounded-xl font-semibold bg-slate-700 text-slate-200 hover:bg-slate-600 flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
              aria-label="Previous step"
            >
              <ChevronLeft className="w-5 h-5" aria-hidden /> Back
            </button>
          )}
          <button
            type="submit"
            disabled={step < TOTAL_STEPS ? !canProceed : submitting}
            className="min-h-[44px] flex-1 rounded-xl font-semibold bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            aria-label={step === TOTAL_STEPS ? (form.wins != null || form.challenges != null ? 'Skip and finish' : 'Finish check-in') : 'Next step'}
          >
            {submitting ? (
              <Loader2 className="w-5 h-5 animate-spin" aria-hidden /> 
            ) : step === TOTAL_STEPS ? (
              (form.wins != null && form.wins.trim()) || (form.challenges != null && form.challenges.trim()) ? 'Submit' : 'Skip & Finish'
            ) : (
              'Next'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default WeeklyCheckinForm;
