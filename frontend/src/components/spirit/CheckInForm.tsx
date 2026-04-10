import React, { useState } from 'react';
import {
  useSpiritCheckin,
  type SubmitCheckinPayload,
  type SubmitCheckinResult,
} from '../../hooks/useSpiritCheckin';

const PLACEHOLDER_PROMPTS = [
  'Today I release financial anxiety and trust the process...',
  'I am grateful for what I have and open to abundance...',
  'I make intentional choices today that align with my goals...',
  'I release fear around money and welcome clarity...',
] as const;

export type PracticeTypeUi = 'prayer' | 'meditation' | 'gratitude' | 'affirmations';

const PRACTICE_OPTIONS: { id: PracticeTypeUi; label: string; emoji: string }[] = [
  { id: 'prayer', label: 'Prayer', emoji: '🙏' },
  { id: 'meditation', label: 'Meditation', emoji: '🧘' },
  { id: 'gratitude', label: 'Gratitude', emoji: '📓' },
  { id: 'affirmations', label: 'Affirmations', emoji: '✨' },
];

const DURATIONS = [5, 10, 15, 20, 30] as const;

const FEELINGS: { value: number; label: string; emoji: string }[] = [
  { value: 1, label: 'Low', emoji: '😔' },
  { value: 2, label: 'Neutral', emoji: '😐' },
  { value: 3, label: 'Calm', emoji: '🙂' },
  { value: 4, label: 'Lifted', emoji: '😊' },
  { value: 5, label: 'Renewed', emoji: '🌟' },
];

function toApiPracticeType(ui: PracticeTypeUi): SubmitCheckinPayload['practice_type'] {
  return ui === 'affirmations' ? 'affirmation' : ui;
}

export interface CheckInFormProps {
  onSuccess?: (result: SubmitCheckinResult) => void;
}

export const CheckInForm: React.FC<CheckInFormProps> = ({ onSuccess }) => {
  const { checkedInToday, isLoading, error, submitCheckin } = useSpiritCheckin();
  const [practiceType, setPracticeType] = useState<PracticeTypeUi | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [feelingAfter, setFeelingAfter] = useState<number | null>(null);
  const [intentionText, setIntentionText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [placeholder] = useState(
    () => PLACEHOLDER_PROMPTS[Math.floor(Math.random() * PLACEHOLDER_PROMPTS.length)]
  );

  const canSubmit = practiceType !== null && duration !== null && feelingAfter !== null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit || submitting || practiceType === null || duration === null || feelingAfter === null) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload: SubmitCheckinPayload = {
        practice_type: toApiPracticeType(practiceType),
        duration_minutes: duration,
        feeling_after: feelingAfter,
        ...(intentionText.trim() ? { intention_text: intentionText.trim() } : {}),
      };
      const result = await submitCheckin(payload);
      onSuccess?.(result);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-[#C4A064]/30 bg-white p-8 text-center text-sm text-slate-600">
        Loading check-in…
      </div>
    );
  }

  if (checkedInToday) {
    return (
      <div
        className="rounded-2xl border-2 border-[#C4A064] bg-[#FFF8EC] px-5 py-4 text-center shadow-sm"
        role="status"
      >
        <p className="font-semibold text-[#0f172a]">Already checked in today</p>
        <p className="mt-1 text-sm text-slate-600">Come back tomorrow for your next Spirit & Finance moment.</p>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => void handleSubmit(e)}
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
    >
      {(error || submitError) && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {submitError || error}
        </div>
      )}

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[#0f172a]">Practice type</h2>
        <p className="mt-1 text-xs text-slate-500">Required — choose one</p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          {PRACTICE_OPTIONS.map((opt) => {
            const active = practiceType === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => setPracticeType(opt.id)}
                className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 px-4 py-4 text-sm font-medium transition-colors ${
                  active
                    ? 'border-[#C4A064] bg-[#0f172a] text-[#FFF8EC]'
                    : 'border-transparent bg-[#FFF8EC] text-[#0f172a] hover:border-[#C4A064]/40'
                }`}
              >
                <span className="text-2xl" aria-hidden>
                  {opt.emoji}
                </span>
                {opt.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[#0f172a]">Duration</h2>
        <p className="mt-1 text-xs text-slate-500">Required</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {DURATIONS.map((m) => {
            const active = duration === m;
            const label = m === 30 ? '30 min+' : `${m} min`;
            return (
              <button
                key={m}
                type="button"
                onClick={() => setDuration(m)}
                className={`rounded-full border-2 px-4 py-2 text-sm font-medium transition-colors ${
                  active
                    ? 'border-[#C4A064] bg-[#0f172a] text-[#FFF8EC]'
                    : 'border-transparent bg-[#FFF8EC] text-[#0f172a] hover:border-[#C4A064]/40'
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[#0f172a]">How do you feel?</h2>
        <p className="mt-1 text-xs text-slate-500">Required</p>
        <div className="mt-4 flex flex-wrap justify-between gap-3 sm:justify-start sm:gap-4">
          {FEELINGS.map((f) => {
            const active = feelingAfter === f.value;
            return (
              <button
                key={f.value}
                type="button"
                onClick={() => setFeelingAfter(f.value)}
                className={`flex min-w-[4.5rem] flex-col items-center gap-1 rounded-xl border-2 px-3 py-3 text-xs font-medium transition-colors ${
                  active
                    ? 'border-[#C4A064] bg-[#0f172a] text-[#FFF8EC]'
                    : 'border-transparent bg-[#FFF8EC] text-[#0f172a] hover:border-[#C4A064]/40'
                }`}
              >
                <span className="text-2xl leading-none" aria-hidden>
                  {f.emoji}
                </span>
                {f.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[#0f172a]">Set your intention</h2>
        <p className="mt-1 text-xs text-slate-500">Optional</p>
        <textarea
          value={intentionText}
          onChange={(e) => setIntentionText(e.target.value)}
          rows={3}
          placeholder={placeholder}
          className="mt-4 w-full resize-y rounded-xl border border-slate-200 bg-[#FFF8EC] px-4 py-3 text-sm text-[#0f172a] placeholder:text-slate-400 focus:border-[#C4A064] focus:outline-none focus:ring-2 focus:ring-[#C4A064]/30"
        />
      </section>

      <button
        type="submit"
        disabled={!canSubmit || submitting}
        className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-[#C4A064] bg-[#0f172a] py-3.5 text-sm font-semibold text-[#FFF8EC] transition hover:bg-[#1e293b] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? (
          <>
            <span
              className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[#FFF8EC] border-t-transparent"
              aria-hidden
            />
            Saving…
          </>
        ) : (
          'Complete Check-In ✦'
        )}
      </button>
    </form>
  );
};

export default CheckInForm;
