import { useCallback, useEffect, useRef, useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { csrfHeaders } from '../../utils/csrfHeaders';
import ConnectionTrendBadge from './ConnectionTrendBadge';

export interface ConnectionTrendAssessmentModalProps {
  personId: string;
  nickname: string;
  onComplete: () => void;
  onClose: () => void;
}

interface ConnectionTrendQuestion {
  id: string;
  key: string;
  text: string;
  answers: string[];
}

interface ConnectionTrendQuestionsResponse {
  questions: ConnectionTrendQuestion[];
}

interface ConnectionTrendPatternInsight {
  insight_message: string | null;
  financial_note: string | null;
}

interface ConnectionTrendAssessmentPayload {
  id: string;
  assessed_at: string | null;
  fade_tier: string;
  pattern_type: string | null;
  pattern_insight: ConnectionTrendPatternInsight | null;
}

interface ConnectionTrendAssessResponse {
  assessment: ConnectionTrendAssessmentPayload;
}

function authJsonHeaders(): Record<string, string> {
  const token = localStorage.getItem('mingus_token') ?? '';
  return {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

type Phase = 'loading' | 'quiz' | 'submitting' | 'result' | 'error';

export default function ConnectionTrendAssessmentModal({
  personId,
  nickname,
  onComplete,
  onClose,
}: ConnectionTrendAssessmentModalProps) {
  const [phase, setPhase] = useState<Phase>('loading');
  const [questions, setQuestions] = useState<ConnectionTrendQuestion[]>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [result, setResult] = useState<ConnectionTrendAssessmentPayload | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const answersRef = useRef<(0 | 1 | 2)[]>([]);

  const loadQuestions = useCallback(() => {
    setPhase('loading');
    setErrorMessage(null);
    const token = localStorage.getItem('mingus_token') ?? '';
    fetch('/api/connection-trend/questions', {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('load');
        return res.json() as Promise<ConnectionTrendQuestionsResponse>;
      })
      .then((json) => {
        const qs = Array.isArray(json.questions) ? json.questions : [];
        if (qs.length !== 7) throw new Error('questions');
        setQuestions(qs);
        answersRef.current = [];
        setStepIndex(0);
        setPhase('quiz');
      })
      .catch(() => {
        setErrorMessage('Could not load questions.');
        setPhase('error');
      });
  }, []);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const currentQuestion = questions[stepIndex];
  const total = questions.length;

  const submitAnswers = useCallback(
    async (finalAnswers: (0 | 1 | 2)[]) => {
      setPhase('submitting');
      const body: Record<string, number> = {};
      for (let i = 0; i < 7; i += 1) {
        body[`q${i + 1}`] = finalAnswers[i];
      }
      const minDelay = new Promise<void>((r) => {
        window.setTimeout(r, 500);
      });
      try {
        const resPromise = fetch(
          `/api/connection-trend/people/${encodeURIComponent(personId)}/assess`,
          {
            method: 'POST',
            credentials: 'include',
            headers: authJsonHeaders(),
            body: JSON.stringify(body),
          }
        );
        const [res] = await Promise.all([resPromise, minDelay]);
        if (!res.ok) throw new Error('assess');
        const json = (await res.json()) as ConnectionTrendAssessResponse;
        if (!json.assessment) throw new Error('assess');
        setResult(json.assessment);
        setPhase('result');
        onComplete();
      } catch {
        setErrorMessage('Something went wrong. Try again.');
        setPhase('error');
      }
    },
    [personId, onComplete]
  );

  const pickAnswer = (value: 0 | 1 | 2) => {
    if (!currentQuestion || phase !== 'quiz') return;
    const next = [...answersRef.current, value];
    answersRef.current = next;
    if (stepIndex + 1 >= total) {
      void submitAnswers(next);
      return;
    }
    setStepIndex((i) => i + 1);
  };

  const handleClose = () => {
    onClose();
  };

  const insightMessage = result?.pattern_insight?.insight_message ?? null;
  const financialNote = result?.pattern_insight?.financial_note ?? null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Connection trend observation"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div
        className="flex h-[100dvh] max-h-[100dvh] w-full max-w-none flex-col rounded-none border-0 border-t border-[#2a2030] bg-[#0d0a08] shadow-2xl sm:h-auto sm:max-h-[90vh] sm:max-w-lg sm:rounded-2xl sm:border"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[#2a2030] px-4 py-3">
          {phase === 'quiz' && total > 0 ? (
            <p className="text-sm text-[#9a8f7e]">
              {stepIndex + 1} of {total}
            </p>
          ) : (
            <span className="text-sm text-transparent"> </span>
          )}
          <button
            type="button"
            onClick={handleClose}
            className="min-h-11 min-w-11 shrink-0 rounded-lg border border-[#2a2030] p-2 text-[#F0E8D8] transition hover:border-[#A78BFA]/40 hover:bg-[#1a1520] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#A78BFA] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d0a08]"
            aria-label="Close"
          >
            <XMarkIcon className="mx-auto h-6 w-6" />
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-6 pt-4">
          {phase === 'loading' ? (
            <div className="space-y-3 py-8" aria-busy="true">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-[#A78BFA] border-t-transparent" />
              <p className="text-center text-sm text-[#9a8f7e]">Loading…</p>
            </div>
          ) : null}

          {phase === 'error' ? (
            <div className="space-y-4 py-6">
              <p className="text-center text-sm text-[#F0E8D8]">{errorMessage}</p>
              <button
                type="button"
                onClick={() => loadQuestions()}
                className="min-h-11 w-full rounded-xl border border-[#A78BFA] bg-transparent px-4 py-3 text-sm font-semibold text-[#A78BFA] transition hover:bg-[#A78BFA]/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#A78BFA] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d0a08]"
              >
                Retry
              </button>
            </div>
          ) : null}

          {phase === 'quiz' && currentQuestion ? (
            <div className="space-y-5">
              <div>
                <h2 className="font-display text-lg font-semibold text-white">
                  What are you noticing about {nickname}?
                </h2>
                <p className="mt-1 text-sm italic text-[#9a8f7e]">
                  Answer honestly. This is just for you.
                </p>
              </div>
              <div className="flex flex-col items-center gap-1 py-1">
                <span className="sr-only">
                  Question {stepIndex + 1} of {total}
                </span>
                <div className="flex justify-center gap-1.5" aria-hidden>
                  {questions.map((q, i) => (
                    <span
                      key={q.id}
                      className={`h-2 w-2 rounded-full ${
                        i === stepIndex
                          ? 'bg-[#A78BFA]'
                          : i < stepIndex
                            ? 'bg-[#A78BFA]/50'
                            : 'bg-[#2a2030]'
                      }`}
                    />
                  ))}
                </div>
              </div>
              <p className="text-base leading-relaxed text-[#F0E8D8]">{currentQuestion.text}</p>
              <div className="flex flex-col gap-3">
                {currentQuestion.answers.map((label, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => pickAnswer(idx as 0 | 1 | 2)}
                    className="min-h-11 w-full rounded-xl border border-[#A78BFA]/35 bg-[#1a1520] px-4 py-3 text-left text-sm font-medium text-[#F0E8D8] transition hover:border-[#A78BFA] hover:bg-[#A78BFA]/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#A78BFA] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d0a08]"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {phase === 'submitting' ? (
            <div className="flex flex-col items-center gap-4 py-16" aria-busy="true">
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#A78BFA] border-t-transparent" />
              <p className="text-sm text-[#9a8f7e]">Saving your observation…</p>
            </div>
          ) : null}

          {phase === 'result' && result ? (
            <div className="space-y-5 py-2">
              <h2 className="text-center font-display text-lg font-semibold text-white">
                Your Connection Trend
              </h2>
              <div className="flex justify-center">
                <div className="origin-center scale-110">
                  <ConnectionTrendBadge
                    fadeTier={result.fade_tier}
                    patternType={result.pattern_type}
                    insightMessage={null}
                  />
                </div>
              </div>
              {insightMessage ? (
                <p className="text-center text-sm leading-relaxed text-[#F0E8D8]">{insightMessage}</p>
              ) : null}
              {financialNote ? (
                <div className="rounded-xl border border-[#D97706]/40 bg-[#D97706]/10 px-4 py-3 text-sm text-[#F0E8D8]">
                  {financialNote}
                </div>
              ) : null}
              <p className="text-center text-xs text-[#9a8f7e]">
                Based on your responses. Trust your instincts.
              </p>
              <button
                type="button"
                onClick={handleClose}
                className="min-h-11 w-full rounded-xl border border-[#A78BFA] bg-[#A78BFA] px-4 py-3 text-sm font-semibold text-[#0d0a08] transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d0a08]"
              >
                Close
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
