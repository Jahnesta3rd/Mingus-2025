import { Helmet } from "react-helmet-async";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import SelfStateContextBanner from "../components/SelfStateContextBanner";
import { FinalCta } from "../components/vibe-checkups/FinalCta";
import { HowItWorks } from "../components/vibe-checkups/HowItWorks";
import { LandingHero } from "../components/vibe-checkups/LandingHero";
import { ProjectionUnlock } from "../components/vibe-checkups/ProjectionUnlock";
import { ResultsGate } from "../components/vibe-checkups/ResultsGate";
import { ScrollProgress } from "../components/vibe-checkups/ScrollProgress";
import { SocialProofStrip } from "../components/vibe-checkups/SocialProofStrip";
import { VibeCheckupsQuizPanel } from "../components/vibe-checkups/VibeCheckupsQuizPanel";
import { useVibeCheckupsApi } from "../components/vibe-checkups/useVibeCheckupsApi";
import type { ProjectionRow, Verdict } from "../components/vibe-checkups/vibeCheckupsTypes";
import { LandingSection } from "../components/landing/LandingSection";
import { useCaptureVibeCheckupsUtm } from "../hooks/useCaptureVibeCheckupsUtm";

const OG_DESCRIPTION =
  "25 questions. Real talk. Find out if the person you're into is an emotional asset or a financial liability — and what the next 12 months could actually cost you.";

const STORAGE_LEAD = "vibe_checkups_lead_id";
const STORAGE_VERDICT = "vibe_checkups_verdict_json";
const STORAGE_PROJECTION = "vibe_checkups_projection_json";

interface SelfCardBannerPayload {
  self_score: number;
  mind_score: number | null;
  mind_trend: string;
}

function parseSelfCardForBanner(json: unknown): SelfCardBannerPayload | null {
  if (!json || typeof json !== "object") return null;
  const o = json as Record<string, unknown>;
  if ("error" in o) return null;
  const trendRaw = o.mind_trend;
  const mindTrend =
    trendRaw === "up" || trendRaw === "down" || trendRaw === "flat" || trendRaw === "declining"
      ? trendRaw
      : "flat";
  const selfScore = typeof o.self_score === "number" ? o.self_score : 0;
  const mindScore = typeof o.mind_score === "number" ? o.mind_score : null;
  return { self_score: selfScore, mind_score: mindScore, mind_trend: mindTrend };
}

function shouldShowSelfContextBanner(data: SelfCardBannerPayload): boolean {
  const declining = data.mind_trend === "declining" || data.mind_trend === "down";
  const lowMind = data.mind_score !== null && data.mind_score < 50;
  return declining || lowMind;
}

function scrollToQuizEl() {
  const el = document.getElementById("quiz");
  if (!el) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  el.focus({ preventScroll: true });
}

function readStoredJson<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function VibeCheckupsPage() {
  useCaptureVibeCheckupsUtm();
  const { vcPost } = useVibeCheckupsApi();
  const [searchParams] = useSearchParams();

  const utm = useMemo(
    () => ({
      utm_source: searchParams.get("utm_source") || undefined,
      utm_medium: searchParams.get("utm_medium") || undefined,
      utm_campaign: searchParams.get("utm_campaign") || undefined,
    }),
    [searchParams]
  );

  const [funnelPhase, setFunnelPhase] = useState<"landing" | "outcomes" | "projection">(() => {
    const proj = readStoredJson<ProjectionRow[]>(STORAGE_PROJECTION);
    if (proj?.length) return "projection";
    const v = readStoredJson<Verdict>(STORAGE_VERDICT);
    if (v) return "outcomes";
    return "landing";
  });

  const [sessionToken, setSessionToken] = useState<string | null>(() =>
    typeof sessionStorage !== "undefined" ? sessionStorage.getItem("vibe_checkups_session_token") : null
  );
  const [verdict, setVerdict] = useState<Verdict | null>(() => readStoredJson<Verdict>(STORAGE_VERDICT));
  const [leadId, setLeadId] = useState<string | null>(() => sessionStorage.getItem(STORAGE_LEAD));
  const [projection, setProjection] = useState<ProjectionRow[] | null>(() =>
    readStoredJson<ProjectionRow[]>(STORAGE_PROJECTION)
  );
  const [flowError, setFlowError] = useState<string | null>(null);
  const [unlockBusy, setUnlockBusy] = useState(false);
  const [selfCardBanner, setSelfCardBanner] = useState<SelfCardBannerPayload | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const token = localStorage.getItem("mingus_token");
        const headers: HeadersInit = {
          "Content-Type": "application/json",
          "X-CSRF-Token": token || "test-token",
        };
        if (token) headers.Authorization = `Bearer ${token}`;

        const res = await fetch("/api/self-card", { credentials: "include", headers });
        if (!res.ok || cancelled) return;
        const json: unknown = await res.json();
        const parsed = parseSelfCardForBanner(json);
        if (!cancelled) setSelfCardBanner(parsed);
      } catch {
        if (!cancelled) setSelfCardBanner(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onCta = useCallback(() => {
    setFunnelPhase("outcomes");
    scrollToQuizEl();
  }, []);

  const onCompleteSession = useCallback((v: Verdict, token: string) => {
    setVerdict(v);
    sessionStorage.setItem(STORAGE_VERDICT, JSON.stringify(v));
    setSessionToken(token);
    setFunnelPhase("outcomes");
    scrollToQuizEl();
  }, []);

  const onEmailCaptured = useCallback((id: string, next: Verdict) => {
    sessionStorage.setItem(STORAGE_LEAD, id);
    sessionStorage.setItem(STORAGE_VERDICT, JSON.stringify(next));
    setLeadId(id);
    setVerdict(next);
  }, []);

  const trackLeadEvent = useCallback(
    async (event_type: string, event_data?: Record<string, unknown>) => {
      const id = leadId ?? sessionStorage.getItem(STORAGE_LEAD);
      if (!id) return;
      try {
        await vcPost(`/lead/${encodeURIComponent(id)}/track-event`, {
          event_type,
          event_data: event_data ?? {},
        });
      } catch {
        /* non-blocking */
      }
    },
    [leadId, vcPost]
  );

  const unlockProjection = useCallback(async () => {
    const id = leadId ?? sessionStorage.getItem(STORAGE_LEAD);
    if (!id) throw new Error("Missing lead");
    const res = await vcPost<{ projection_data: ProjectionRow[] }>(
      `/lead/${encodeURIComponent(id)}/unlock-projection`,
      {}
    );
    sessionStorage.setItem(STORAGE_PROJECTION, JSON.stringify(res.projection_data));
    setProjection(res.projection_data);
    setFunnelPhase("projection");
    void trackLeadEvent("projection_unlocked", {});
  }, [leadId, trackLeadEvent, vcPost]);

  const resetFlow = useCallback(() => {
    sessionStorage.removeItem("vibe_checkups_session_token");
    sessionStorage.removeItem(STORAGE_LEAD);
    sessionStorage.removeItem(STORAGE_VERDICT);
    sessionStorage.removeItem(STORAGE_PROJECTION);
    setSessionToken(null);
    setLeadId(null);
    setVerdict(null);
    setProjection(null);
    setFlowError(null);
    setFunnelPhase("landing");
  }, []);

  const showOutcomes = funnelPhase === "outcomes" || funnelPhase === "projection";

  return (
    <>
      <Helmet>
        <title>Vibe Checkups — Is This Person Worth It?</title>
        <meta name="description" content={OG_DESCRIPTION} />
        <meta property="og:title" content="Vibe Checkups — Is This Person Worth It?" />
        <meta property="og:description" content={OG_DESCRIPTION} />
        <meta property="og:image" content="/vibe-checkups-og.png" />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Vibe Checkups — Is This Person Worth It?" />
        <meta name="twitter:description" content={OG_DESCRIPTION} />
        <meta name="twitter:image" content="/vibe-checkups-og.png" />
      </Helmet>

      <div className="min-h-screen bg-[#0d0a08]">
        <ScrollProgress />
        <main>
          {funnelPhase === "landing" && (
            <>
              <LandingHero onPrimaryCta={onCta} />
              <SocialProofStrip />
              <HowItWorks />
              <FinalCta onCta={onCta} />
            </>
          )}

          <section
            id="quiz"
            tabIndex={-1}
            className="scroll-mt-4 border-t border-[#2a2030] pb-24 outline-none"
            aria-label="Vibe Checkups assessment"
          >
            <LandingSection className="py-16 sm:py-20">
              <div className="mx-auto max-w-xl">
                {funnelPhase === "landing" && (
                  <div className="rounded-2xl border border-[#2a2030] bg-[#1a1520]/50 px-6 py-10 text-center shadow-landing-card sm:px-10">
                    <h2 className="font-display text-xl font-semibold text-[#f0e8d8] sm:text-2xl">
                      Ready when you are
                    </h2>
                    <p className="mt-3 text-sm leading-relaxed text-[#9a8f7e]">
                      Take the checkup below, or scroll back up to read how it works first.
                    </p>
                    {selfCardBanner && shouldShowSelfContextBanner(selfCardBanner) && (
                      <SelfStateContextBanner
                        selfScore={selfCardBanner.self_score}
                        mindScore={selfCardBanner.mind_score ?? 50}
                        mindTrend={selfCardBanner.mind_trend}
                      />
                    )}
                    <button
                      type="button"
                      onClick={onCta}
                      className="mt-6 flex min-h-11 w-full items-center justify-center rounded-xl bg-[#5B2D8E] px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-[#4a2673]"
                    >
                      Start the checkup
                    </button>
                  </div>
                )}

                {showOutcomes && (
                  <div className="space-y-12">
                    {!verdict && (
                      <VibeCheckupsQuizPanel
                        utm={utm}
                        vcPost={vcPost}
                        onCompleteSession={onCompleteSession}
                        onError={setFlowError}
                      />
                    )}

                    {verdict && sessionToken && funnelPhase !== "projection" && (
                      <ResultsGate
                        sessionToken={sessionToken}
                        verdict={verdict}
                        leadId={leadId}
                        vcPost={vcPost}
                        onEmailCaptured={onEmailCaptured}
                        onUnlockProjection={unlockProjection}
                        unlockBusy={unlockBusy}
                        setUnlockBusy={setUnlockBusy}
                        setFlowError={setFlowError}
                      />
                    )}

                    {funnelPhase === "projection" && projection && leadId && (
                      <ProjectionUnlock
                        projection={projection}
                        verdict={verdict}
                        onRestart={resetFlow}
                        leadId={leadId}
                        vcPost={vcPost}
                      />
                    )}

                    {flowError && (
                      <div
                        className="rounded-xl border border-rose-500/40 bg-rose-950/30 px-4 py-3 text-sm text-[#f0e8d8]"
                        role="alert"
                      >
                        {flowError}
                      </div>
                    )}

                    {showOutcomes && funnelPhase !== "projection" && (
                      <button
                        type="button"
                        onClick={resetFlow}
                        className="w-full text-center text-sm text-[#9a8f7e] underline-offset-4 hover:underline"
                      >
                        Leave and discard saved progress
                      </button>
                    )}
                  </div>
                )}
              </div>
            </LandingSection>
          </section>
        </main>
      </div>
    </>
  );
}
export default VibeCheckupsPage;
