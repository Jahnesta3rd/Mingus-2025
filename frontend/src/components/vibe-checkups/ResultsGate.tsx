import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import type { CaptureEmailResponse, Verdict } from "./vibeCheckupsTypes";
import { TrackThisPersonCard } from "./TrackThisPersonCard";

type VcPost = <T,>(path: string, body?: Record<string, unknown>) => Promise<T>;

function scoreTierClass(pct: number): string {
  if (pct >= 70) return "bg-emerald-400";
  if (pct >= 45) return "bg-amber-400";
  return "bg-rose-400";
}

function scoreTierGlow(pct: number): string {
  if (pct >= 70) return "shadow-[0_0_24px_rgba(52,211,153,0.25)]";
  if (pct >= 45) return "shadow-[0_0_24px_rgba(251,191,36,0.2)]";
  return "shadow-[0_0_24px_rgba(251,113,133,0.22)]";
}

type ResultsGateProps = {
  sessionToken: string;
  verdict: Verdict;
  leadId: string | null;
  vcPost: VcPost;
  onEmailCaptured: (leadId: string, next: Verdict) => void;
  onUnlockProjection: () => Promise<void>;
  unlockBusy: boolean;
  setUnlockBusy: (v: boolean) => void;
  setFlowError: (msg: string | null) => void;
};

export function ResultsGate({
  sessionToken,
  verdict,
  leadId,
  vcPost,
  onEmailCaptured,
  onUnlockProjection,
  unlockBusy,
  setUnlockBusy,
  setFlowError,
}: ResultsGateProps) {
  const { user } = useAuth();
  const scoresUnlocked = Boolean(leadId);
  const isLoggedIn = Boolean(user?.isAuthenticated);
  const canTrack =
    isLoggedIn && (user?.tier === "mid_tier" || user?.tier === "professional");
  const isBudgetTier = isLoggedIn && user?.tier === "budget";
  const [email, setEmail] = useState("");
  const [submitBusy, setSubmitBusy] = useState(false);
  const [barEmo, setBarEmo] = useState(0);
  const [barFin, setBarFin] = useState(0);

  const reducedMotion = useMemo(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    []
  );

  useEffect(() => {
    if (!scoresUnlocked) {
      setBarEmo(0);
      setBarFin(0);
      return;
    }
    if (reducedMotion) {
      setBarEmo(verdict.emotional_score);
      setBarFin(verdict.financial_score);
      return;
    }
    let cancelled = false;
    const start = performance.now();
    const duration = 1200;
    const targetE = verdict.emotional_score;
    const targetF = verdict.financial_score;
    const tick = (now: number) => {
      if (cancelled) return;
      const t = Math.min(1, (now - start) / duration);
      const ease = 1 - (1 - t) ** 2;
      setBarEmo(Math.round(targetE * ease));
      setBarFin(Math.round(targetF * ease));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    return () => {
      cancelled = true;
    };
  }, [scoresUnlocked, verdict.emotional_score, verdict.financial_score, reducedMotion]);

  const captureEmail = useCallback(async () => {
    setSubmitBusy(true);
    setFlowError(null);
    try {
      const res = await vcPost<CaptureEmailResponse>(
        `/session/${encodeURIComponent(sessionToken)}/capture-email`,
        { email: email.trim() }
      );
      onEmailCaptured(res.lead_id, {
        emotional_score: res.emotional_score,
        financial_score: res.financial_score,
        verdict_label: res.verdict_label,
        verdict_emoji: res.verdict_emoji,
        verdict_description: res.verdict_description,
      });
    } catch (e) {
      setFlowError(e instanceof Error ? e.message : "Could not save email");
    } finally {
      setSubmitBusy(false);
    }
  }, [email, onEmailCaptured, sessionToken, setFlowError, vcPost]);

  const onUnlockClick = useCallback(async () => {
    setUnlockBusy(true);
    setFlowError(null);
    try {
      await onUnlockProjection();
    } catch (e) {
      setFlowError(e instanceof Error ? e.message : "Could not unlock projection");
    } finally {
      setUnlockBusy(false);
    }
  }, [onUnlockProjection, setFlowError, setUnlockBusy]);

  return (
    <div className="mx-auto max-w-lg space-y-8 text-center">
      <style>
        {`
          @keyframes vcVerdictEmoji {
            0% { transform: scale(0); opacity: 0; }
            55% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
          }
          @keyframes vcFadeUp {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>

      {/* Phase 1 — verdict reveal (scores hidden until email) */}
      <div className="space-y-5">
        <div
          className="text-7xl sm:text-8xl leading-none"
          style={{
            animation: reducedMotion ? undefined : "vcVerdictEmoji 600ms ease-out forwards",
            transform: reducedMotion ? "scale(1)" : undefined,
            opacity: reducedMotion ? 1 : undefined,
          }}
          aria-hidden
        >
          {verdict.verdict_emoji}
        </div>
        <h2
          className="font-display text-2xl font-semibold text-[#f0e8d8] sm:text-[1.65rem]"
          style={{
            animation: reducedMotion ? undefined : "vcFadeUp 0.55s ease-out 0.35s forwards",
            opacity: reducedMotion ? 1 : 0,
          }}
        >
          {verdict.verdict_label}
        </h2>
        <p
          className="text-left text-sm leading-relaxed text-[#f0e8d8]/95 sm:text-base"
          style={{
            animation: reducedMotion ? undefined : "vcFadeUp 0.55s ease-out 0.55s forwards",
            opacity: reducedMotion ? 1 : 0,
          }}
        >
          {verdict.verdict_description}
        </p>
      </div>

      {!scoresUnlocked && (
        <div
          className="space-y-5 border-t border-[#2a2030] pt-8 text-left"
          style={{
            animation: reducedMotion ? undefined : "vcFadeUp 0.6s ease-out 0.75s forwards",
            opacity: reducedMotion ? 1 : 0,
          }}
        >
          <p className="text-center font-display text-lg font-medium leading-snug text-[#f0e8d8]">
            Want to see your full scores and 12-month financial projection?
          </p>
          <label className="block text-xs font-medium uppercase tracking-wider text-[#9a8f7e]" htmlFor="vc-results-email">
            Email
          </label>
          <input
            id="vc-results-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full rounded-xl border border-[#2a2030] bg-[#1a1520] px-4 py-3.5 text-[#f0e8d8] outline-none ring-[#C4A064]/40 placeholder:text-[#9a8f7e] focus:ring-2"
          />
          <button
            type="button"
            disabled={submitBusy || !email.trim()}
            onClick={() => void captureEmail()}
            className="w-full rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] shadow-landing-card transition hover:bg-[#d4b074] disabled:opacity-45"
          >
            {submitBusy ? "Sending…" : "Show My Results"}
          </button>
          <p className="text-center text-xs leading-relaxed text-[#9a8f7e]">
            No spam. One email with your results, then we&apos;ll check in once.
          </p>
        </div>
      )}

      {/* Phase 2 — scores + projection CTA */}
      {scoresUnlocked && (
        <div className="space-y-8 border-t border-[#2a2030] pt-8 text-left">
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-sm font-medium text-[#f0e8d8]">Emotional match</span>
                <span className="font-display text-lg tabular-nums text-[#C4A064]">{barEmo}%</span>
              </div>
              <div
                className="h-2.5 overflow-hidden rounded-full bg-[#2a2030]/80"
                aria-hidden
              >
                <div
                  className={`h-full rounded-full transition-[width] duration-75 ${scoreTierClass(verdict.emotional_score)} ${scoreTierGlow(verdict.emotional_score)}`}
                  style={{ width: `${barEmo}%` }}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-sm font-medium text-[#f0e8d8]">Financial match</span>
                <span className="font-display text-lg tabular-nums text-[#C4A064]">{barFin}%</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-[#2a2030]/80" aria-hidden>
                <div
                  className={`h-full rounded-full transition-[width] duration-75 ${scoreTierClass(verdict.financial_score)} ${scoreTierGlow(verdict.financial_score)}`}
                  style={{ width: `${barFin}%` }}
                />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-[#2a2030] bg-[#1a1520]/80 px-5 py-6 text-center shadow-landing-card">
            <p className="font-display text-base font-medium leading-snug text-[#f0e8d8]">
              Your 12-month relationship cost projection is ready
            </p>
            <button
              type="button"
              disabled={unlockBusy}
              onClick={() => void onUnlockClick()}
              className="mt-5 w-full rounded-xl border border-[#C4A064]/50 bg-[#C4A064]/12 py-3.5 text-sm font-semibold text-[#C4A064] transition hover:border-[#C4A064] hover:bg-[#C4A064]/10 disabled:opacity-45"
            >
              {unlockBusy ? "Opening…" : "See My Financial Projection — Free"}
            </button>
          </div>

          {canTrack && leadId ? (
            <TrackThisPersonCard leadId={leadId} onTracked={() => {}} onSkip={() => {}} />
          ) : null}

          {isBudgetTier ? (
            <div className="rounded-2xl border border-[#2a2030] bg-[#1a1520]/80 px-5 py-5 text-center shadow-landing-card">
              <p className="font-display text-sm font-medium text-[#f0e8d8]">
                Track this person over time with Mingus Mid-tier
              </p>
              <p className="mt-2 text-xs leading-relaxed text-[#9a8f7e]">
                See if your compatibility improves — or know when to move on.
              </p>
              <a
                href="/settings/upgrade"
                className="mt-4 inline-block text-sm font-semibold text-[#C4A064] underline-offset-2 hover:underline"
              >
                Upgrade
              </a>
            </div>
          ) : null}

          {!isLoggedIn ? (
            <div className="rounded-2xl border border-[#2a2030] bg-[#1a1520]/80 px-5 py-5 text-center shadow-landing-card">
              <p className="text-sm font-medium text-[#f0e8d8]">
                Create a free account to save your checkup history and trends
              </p>
              <a
                href="/register"
                className="mt-4 inline-block text-sm font-semibold text-[#C4A064] underline-offset-2 hover:underline"
              >
                Sign up
              </a>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
