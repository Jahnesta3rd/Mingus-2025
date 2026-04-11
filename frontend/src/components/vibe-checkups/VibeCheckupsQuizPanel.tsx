import { useCallback, useEffect, useMemo, useState } from "react";
import { VIBE_CHECKUPS_QUESTIONS, type QuestionDef } from "./vibeCheckupsQuestions";
import type { Verdict } from "./vibeCheckupsTypes";

type VcPost = <T,>(path: string, body?: Record<string, unknown>) => Promise<T>;

type Utm = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

const DEFAULT_STORAGE_KEY = "vibe_checkups_session_token";

export type VibeCheckupsQuizPanelProps = {
  utm: Utm;
  vcPost: VcPost;
  onCompleteSession: (verdict: Verdict, sessionToken: string) => void;
  onError: (msg: string | null) => void;
  /** Defaults to full Vibe Checkups question set. */
  questions?: QuestionDef[];
  /** Isolate session token when embedding (e.g. onboarding). */
  sessionStorageKey?: string;
  /** Skip the intro screen and start the session immediately. */
  autoStart?: boolean;
  /** Override intro copy when there is no active session yet. */
  introHint?: string;
};

export function VibeCheckupsQuizPanel({
  utm,
  vcPost,
  onCompleteSession,
  onError,
  questions: questionsProp,
  sessionStorageKey = DEFAULT_STORAGE_KEY,
  autoStart = false,
  introHint,
}: VibeCheckupsQuizPanelProps) {
  const questions = questionsProp ?? VIBE_CHECKUPS_QUESTIONS;
  const [qIndex, setQIndex] = useState(0);
  const [sessionToken, setSessionToken] = useState<string | null>(() =>
    typeof sessionStorage !== "undefined" ? sessionStorage.getItem(sessionStorageKey) : null
  );
  const [busy, setBusy] = useState(false);

  const totalQs = questions.length;
  const currentQ: QuestionDef | undefined = questions[qIndex];
  const progressPct = Math.round(((qIndex + 1) / totalQs) * 100);

  const startSession = useCallback(async () => {
    setBusy(true);
    onError(null);
    try {
      const res = await vcPost<{ session_token: string }>("/session/start", { ...utm });
      sessionStorage.setItem(sessionStorageKey, res.session_token);
      setSessionToken(res.session_token);
      setQIndex(0);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Could not start session");
    } finally {
      setBusy(false);
    }
  }, [onError, sessionStorageKey, utm, vcPost]);

  useEffect(() => {
    if (!autoStart || sessionToken || busy) return;
    void startSession();
  }, [autoStart, busy, sessionToken, startSession]);

  const submitAnswer = useCallback(
    async (choice: number) => {
      if (!sessionToken || !currentQ) return;
      setBusy(true);
      onError(null);
      const value = currentQ.axis === "emotional" ? choice : 0;
      const financial = currentQ.axis === "financial" ? choice : 0;
      try {
        await vcPost(`/session/${encodeURIComponent(sessionToken)}/answer`, {
          question_id: currentQ.id,
          value,
          financial,
        });
        if (qIndex + 1 >= totalQs) {
          const complete = await vcPost<Verdict>(
            `/session/${encodeURIComponent(sessionToken)}/complete`,
            {}
          );
          onCompleteSession(complete, sessionToken);
        } else {
          setQIndex((i) => i + 1);
        }
      } catch (e) {
        onError(e instanceof Error ? e.message : "Could not save answer");
      } finally {
        setBusy(false);
      }
    },
    [currentQ, onCompleteSession, onError, qIndex, sessionToken, totalQs, vcPost]
  );

  const sectionLabel = useMemo(() => {
    if (!currentQ) return "";
    if (currentQ.section === "emotional") return "Emotional fit";
    if (currentQ.section === "financial") return "Money fit";
    return "Projection tuning";
  }, [currentQ]);

  const defaultIntro =
    introHint ??
    `${totalQs} questions. Your answers stay in this session until you choose to share your email for results.`;

  if (!sessionToken) {
    if (autoStart) {
      return (
        <div className="space-y-4" aria-busy="true">
          <div className="h-4 w-3/4 animate-pulse rounded bg-[#2a2030]" />
          <div className="h-1.5 animate-pulse rounded-full bg-[#2a2030]" />
          <div className="h-24 animate-pulse rounded-xl bg-[#2a2030]/80" />
        </div>
      );
    }
    return (
      <div className="space-y-6 text-center">
        <p className="text-sm leading-relaxed text-[#9A8F7E]">{defaultIntro}</p>
        <button
          type="button"
          onClick={() => void startSession()}
          disabled={busy}
          className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-95 disabled:opacity-45"
        >
          {busy ? "Starting…" : "Begin the checkup"}
        </button>
      </div>
    );
  }

  if (!currentQ) return null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between text-xs uppercase tracking-wider text-[#9A8F7E]">
        <span>{sectionLabel}</span>
        <span>
          {qIndex + 1} / {totalQs}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#2a2030]">
        <div
          className="h-full rounded-full bg-[#7C3AED] transition-all duration-300"
          style={{ width: `${Math.min(100, progressPct)}%` }}
        />
      </div>
      <h3 className="font-display text-xl font-semibold text-[#FFFFFF] sm:text-2xl">{currentQ.title}</h3>
      <p className="text-sm leading-relaxed text-[#FFFFFF]/90 sm:text-base">{currentQ.hint}</p>
      <div className="grid gap-3">
        {currentQ.labels.map((label, idx) => (
          <button
            key={label}
            type="button"
            disabled={busy}
            onClick={() => void submitAnswer(idx)}
            className="min-h-11 rounded-xl border border-[#A78BFA]/40 bg-[#1a1520] px-4 py-3.5 text-left text-sm text-[#FFFFFF] transition hover:border-[#A78BFA] disabled:opacity-45"
          >
            <span className="mr-2 font-mono text-xs text-[#A78BFA]">{idx}</span>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
