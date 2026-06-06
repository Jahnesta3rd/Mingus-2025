import React, { useCallback, useState } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import { RELATIONSHIP_CHECK_QUESTIONS } from '../../../data/relationshipCheckQuestions';
import { csrfHeaders } from '../../../utils/csrfHeaders';

export interface RelationshipCheckPanelProps {
  nickname: string;
  personId: string;
  onComplete: () => void;
  onSkip: () => void;
}

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders(), 'Content-Type': 'application/json' };
  const token = getAccessToken();
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as { error?: string; message?: string };
    return j.error || j.message || text || res.statusText;
  } catch {
    return text || res.statusText || 'Request failed';
  }
}

const SKIP_WARNING =
  "Skipping means your forecast won't reflect the financial pattern of this relationship — you can complete this later from your roster.";

export default function RelationshipCheckPanel({
  nickname,
  personId,
  onComplete,
  onSkip,
}: RelationshipCheckPanelProps) {
  const { getAccessToken } = useAuth();
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [questionIndex, setQuestionIndex] = useState(0);
  const [showSummary, setShowSummary] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [skipConfirmOpen, setSkipConfirmOpen] = useState(false);

  const currentQuestion = RELATIONSHIP_CHECK_QUESTIONS[questionIndex];
  const allAnswered = RELATIONSHIP_CHECK_QUESTIONS.every((q) => answers[q.id] !== undefined);

  const selectAnswer = useCallback((questionId: string, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
    setError(null);
    if (questionIndex < RELATIONSHIP_CHECK_QUESTIONS.length - 1) {
      setQuestionIndex((i) => i + 1);
    } else {
      setShowSummary(true);
    }
  }, [questionIndex]);

  const handleContinue = async () => {
    if (!allAnswered) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch('/api/relationship-check/assessment', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({
          tracked_person_id: personId,
          answers,
        }),
      });
      if (!res.ok) {
        throw new Error(await readErrorMessage(res));
      }
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save assessment');
    } finally {
      setSubmitting(false);
    }
  };

  if (showSummary && allAnswered) {
    return (
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h2 className="font-serif text-xl font-semibold text-[#1E293B]">
          Relationship check — {nickname}
        </h2>
        <p className="mt-2 text-sm text-[#64748B]">
          You&apos;ve answered all five questions. Save your responses to continue.
        </p>
        {error ? (
          <p className="mt-4 text-sm text-red-600" role="alert">
            {error}
          </p>
        ) : null}
        <button
          type="button"
          disabled={submitting}
          onClick={() => void handleContinue()}
          className="mt-6 min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50"
        >
          {submitting ? 'Saving…' : 'Continue'}
        </button>
        <button
          type="button"
          onClick={() => setSkipConfirmOpen(true)}
          className="mt-3 min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        >
          Skip the check for {nickname}
        </button>
        {skipConfirmOpen ? (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm text-amber-900">{SKIP_WARNING}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={onSkip}
                className="min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-4 text-sm font-medium text-[#1E293B] hover:bg-[#F8FAFC]"
              >
                Skip anyway
              </button>
              <button
                type="button"
                onClick={() => setSkipConfirmOpen(false)}
                className="min-h-11 rounded-lg bg-[#5B2D8E] px-4 text-sm font-semibold text-white hover:opacity-95"
              >
                Go back
              </button>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <h2 className="font-serif text-xl font-semibold text-[#1E293B]">
        Relationship check — {nickname}
      </h2>
      <p className="mt-1 text-xs font-medium uppercase tracking-wide text-[#64748B]">
        {currentQuestion.axis === 'emotional' ? 'Emotional' : 'Financial'} · Question{' '}
        {questionIndex + 1} of {RELATIONSHIP_CHECK_QUESTIONS.length}
      </p>
      <p className="mt-4 text-base text-[#1E293B]">{currentQuestion.prompt}</p>

      <div className="mt-6 space-y-2">
        {currentQuestion.answers.map((label, idx) => (
          <button
            key={label}
            type="button"
            onClick={() => selectAnswer(currentQuestion.id, idx)}
            className={`min-h-11 w-full rounded-lg border px-4 py-3 text-left text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 ${
              answers[currentQuestion.id] === idx
                ? 'border-[#5B2D8E] bg-[#F5F3FF] font-medium text-[#1E293B]'
                : 'border-[#E2E8F0] bg-white text-[#1E293B] hover:border-[#5B2D8E]/40 hover:bg-[#F8FAFC]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {error ? (
        <p className="mt-4 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={() => setSkipConfirmOpen(true)}
        className="mt-6 min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
      >
        Skip the check for {nickname}
      </button>

      {skipConfirmOpen ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-900">{SKIP_WARNING}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onSkip}
              className="min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-4 text-sm font-medium text-[#1E293B] hover:bg-[#F8FAFC]"
            >
              Skip anyway
            </button>
            <button
              type="button"
              onClick={() => setSkipConfirmOpen(false)}
              className="min-h-11 rounded-lg bg-[#5B2D8E] px-4 text-sm font-semibold text-white hover:opacity-95"
            >
              Go back
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
