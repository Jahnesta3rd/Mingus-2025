import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { VibeCheckupsQuizPanel } from '../vibe-checkups/VibeCheckupsQuizPanel';
import { QUICK_ONBOARDING_VIBE_QUESTIONS } from '../vibe-checkups/vibeCheckupsQuestions';
import { useVibeCheckupsApi } from '../vibe-checkups/useVibeCheckupsApi';
import type { Verdict } from '../vibe-checkups/vibeCheckupsTypes';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

const ONBOARDING_VC_STORAGE_KEY = 'vibe_checkups_onboarding_session_token';

export interface QuickVibeStepProps {
  personId: string;
  nickname: string;
  onAdvance: () => void;
  onSkip: () => void;
  setPageError: (msg: string | null) => void;
  onRefreshSetup: () => Promise<void>;
}

interface CaptureEmailResponse {
  lead_id: string;
  verdict_label: string;
  verdict_emoji: string;
  verdict_description: string;
  emotional_score: number;
  financial_score: number;
}

function buildAuthHeaders(getAccessToken: () => string | null): HeadersInit {
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

export default function QuickVibeStep({
  personId,
  nickname,
  onAdvance,
  onSkip,
  setPageError,
  onRefreshSetup,
}: QuickVibeStepProps) {
  const { vcPost } = useVibeCheckupsApi();
  const { user, getAccessToken } = useAuth();
  const [searchParams] = useSearchParams();
  const [quizError, setQuizError] = useState<string | null>(null);
  const [phase, setPhase] = useState<'quiz' | 'linking' | 'result' | 'error'>('quiz');
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [quizRemountKey, setQuizRemountKey] = useState(0);

  const utm = useMemo(
    () => ({
      utm_source: searchParams.get('utm_source') || undefined,
      utm_medium: searchParams.get('utm_medium') || undefined,
      utm_campaign: searchParams.get('utm_campaign') || undefined,
    }),
    [searchParams]
  );

  const email = (user?.email || '').trim();

  const linkAssessmentToPerson = useCallback(
    async (leadId: string) => {
      const res = await fetch(
        `/api/vibe-tracker/people/${encodeURIComponent(personId)}/assessment`,
        {
          method: 'POST',
          credentials: 'include',
          headers: buildAuthHeaders(getAccessToken),
          body: JSON.stringify({ lead_id: leadId }),
        }
      );
      if (res.status !== 201 && res.status !== 200) {
        throw new Error(await readErrorMessage(res));
      }
    },
    [getAccessToken, personId]
  );

  const onCompleteSession = useCallback(
    async (_v: Verdict, sessionToken: string) => {
      if (!email) {
        setPhase('error');
        setQuizError('Sign-in email not available. Skip the checkup or try again later.');
        return;
      }
      setPhase('linking');
      setQuizError(null);
      try {
        const captured = await vcPost<CaptureEmailResponse>(
          `/session/${encodeURIComponent(sessionToken)}/capture-email`,
          { email }
        );
        await linkAssessmentToPerson(captured.lead_id);
        await onRefreshSetup();
        setVerdict({
          emotional_score: captured.emotional_score,
          financial_score: captured.financial_score,
          verdict_label: captured.verdict_label,
          verdict_emoji: captured.verdict_emoji,
          verdict_description: captured.verdict_description,
        });
        setPhase('result');
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Could not save checkup';
        setPhase('error');
        setQuizError(msg);
      }
    },
    [email, linkAssessmentToPerson, onRefreshSetup, vcPost]
  );

  useEffect(() => {
    if (phase !== 'result' || !verdict) return;
    const t = window.setTimeout(() => {
      onAdvance();
    }, 2000);
    return () => window.clearTimeout(t);
  }, [phase, verdict, onAdvance]);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
          Let&apos;s get a quick read on {nickname}
        </h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Answer 5 quick questions about them — takes about a minute.
        </p>
      </div>

      {phase === 'quiz' && (
        <div
          key={quizRemountKey}
          className="rounded-xl border border-[#A78BFA]/50 bg-[#0D0A08] p-6 shadow-sm"
        >
          <VibeCheckupsQuizPanel
            utm={utm}
            vcPost={vcPost}
            onCompleteSession={onCompleteSession}
            onError={setQuizError}
            questions={QUICK_ONBOARDING_VIBE_QUESTIONS}
            sessionStorageKey={ONBOARDING_VC_STORAGE_KEY}
            autoStart
            introHint="5 quick questions. Your answers are saved when you finish."
          />
        </div>
      )}

      {phase === 'linking' && (
        <div
          className="rounded-xl border border-[#E2E8F0] bg-white p-6 text-center text-sm text-[#64748B] shadow-sm"
          aria-busy="true"
        >
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-[#E2E8F0] border-t-[#5B2D8E]" />
          Saving your checkup…
        </div>
      )}

      {phase === 'result' && verdict && (
        <div
          className="rounded-xl border border-[#A78BFA]/50 bg-[#0D0A08] p-6 text-center shadow-sm"
          role="status"
        >
          <div className="text-5xl" aria-hidden>
            {verdict.verdict_emoji}
          </div>
          <h2 className="mt-3 font-display text-xl font-semibold text-[#FFFFFF]">{verdict.verdict_label}</h2>
          <p className="mt-2 text-sm leading-relaxed text-[#9A8F7E]">{verdict.verdict_description}</p>
          <p className="mt-4 text-sm text-[#9A8F7E]">Continuing in a moment…</p>
        </div>
      )}

      {(quizError || phase === 'error') && quizError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-[#DC2626]" role="alert">
          {quizError}
          <button
            type="button"
            onClick={() => {
              setQuizError(null);
              setPhase('quiz');
              sessionStorage.removeItem(ONBOARDING_VC_STORAGE_KEY);
              setQuizRemountKey((k) => k + 1);
            }}
            className="mt-3 min-h-11 w-full rounded-lg border border-[#E2E8F0] bg-white text-[#1E293B] transition hover:bg-[#F8FAFC] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            Try again
          </button>
        </div>
      )}

      {phase === 'quiz' && (
        <button
          type="button"
          onClick={() => {
            setPageError(null);
            setQuizError(null);
            onSkip();
          }}
          className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        >
          Skip the checkup
        </button>
      )}
    </div>
  );
}
