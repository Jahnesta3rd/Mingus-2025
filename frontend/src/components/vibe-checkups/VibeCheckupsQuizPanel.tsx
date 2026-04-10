import { useCallback, useMemo, useState } from "react";
import { VIBE_CHECKUPS_QUESTIONS, type QuestionDef } from "./vibeCheckupsQuestions";
import type { Verdict } from "./vibeCheckupsTypes";

type VcPost = <T,>(path: string, body?: Record<string, unknown>) => Promise<T>;

type Utm = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

const STORAGE_TOKEN = "vibe_checkups_session_token";

type VibeCheckupsQuizPanelProps = {
  utm: Utm;
  vcPost: VcPost;
  onCompleteSession: (verdict: Verdict, sessionToken: string) => void;
  onError: (msg: string | null) => void;
};

export function VibeCheckupsQuizPanel({
  utm,
  vcPost,
  onCompleteSession,
  onError,
}: VibeCheckupsQuizPanelProps) {
  const [qIndex, setQIndex] = useState(0);
  const [sessionToken, setSessionToken] = useState<string | null>(() =>
    typeof sessionStorage !== "undefined" ? sessionStorage.getItem(STORAGE_TOKEN) : null
  );
  const [busy, setBusy] = useState(false);

  const totalQs = VIBE_CHECKUPS_QUESTIONS.length;
  const currentQ: QuestionDef | undefined = VIBE_CHECKUPS_QUESTIONS[qIndex];
  const progressPct = Math.round(((qIndex + 1) / totalQs) * 100);

  const startSession = useCallback(async () => {
    setBusy(true);
    onError(null);
    try {
      const res = await vcPost<{ session_token: string }>("/session/start", { ...utm });
      sessionStorage.setItem(STORAGE_TOKEN, res.session_token);
      setSessionToken(res.session_token);
      setQIndex(0);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Could not start session");
    } finally {
      setBusy(false);
    }
  }, [onError, utm, vcPost]);

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

  if (!sessionToken) {
    return (
      <div className="space-y-6 text-center">
        <p className="text-sm leading-relaxed text-[#9a8f7e]">
          25 questions. Your answers stay in this session until you choose to share your email for results.
        </p>
        <button
          type="button"
          onClick={() => void startSession()}
          disabled={busy}
          className="w-full rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] shadow-landing-card transition hover:bg-[#d4b074] disabled:opacity-45"
        >
          {busy ? "Starting…" : "Begin the checkup"}
        </button>
      </div>
    );
  }

  if (!currentQ) return null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between text-xs uppercase tracking-wider text-[#9a8f7e]">
        <span>{sectionLabel}</span>
        <span>
          {qIndex + 1} / {totalQs}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#2a2030]">
        <div
          className="h-full rounded-full bg-[#C4A064] transition-all duration-300"
          style={{ width: `${Math.min(100, progressPct)}%` }}
        />
      </div>
      <h3 className="font-display text-xl font-semibold text-[#f0e8d8] sm:text-2xl">{currentQ.title}</h3>
      <p className="text-sm leading-relaxed text-[#f0e8d8]/90 sm:text-base">{currentQ.hint}</p>
      <div className="grid gap-3">
        {currentQ.labels.map((label, idx) => (
          <button
            key={label}
            type="button"
            disabled={busy}
            onClick={() => void submitAnswer(idx)}
            className="rounded-xl border border-[#2a2030] bg-[#1a1520] px-4 py-3.5 text-left text-sm text-[#f0e8d8] transition hover:border-[#C4A064]/50 disabled:opacity-45"
          >
            <span className="mr-2 font-mono text-xs text-[#C4A064]">{idx}</span>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
