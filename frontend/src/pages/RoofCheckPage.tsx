import { Helmet } from "react-helmet-async";
import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { RoofCheckQuizPanel } from "../components/roof-check/RoofCheckQuizPanel";
import {
  calculateHousingWealthGap,
  calculateRoofScore,
  type HousingWealthGapResult,
} from "../components/roof-check/roofCheckScoring";
import { LandingSection } from "../components/landing/LandingSection";
import { useAuth } from "../hooks/useAuth";

const OG_DESCRIPTION =
  "12 questions about where you live — and what it means for your wealth. Roof Check feeds your Mingus Life Ledger.";

function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "test-token";
  return { "X-CSRF-Token": token };
}

type InsightRow = {
  id: string;
  module: string;
  insight_type: string;
  message: string;
  action_url: string | null;
  dismissed: boolean;
};

type ResultsState = {
  roof_score: number;
  housing_wealth_gap: HousingWealthGapResult;
  verdict: string;
  insights: InsightRow[];
  saved: boolean;
};

function scoreColorClass(score: number): string {
  if (score >= 75) return "text-emerald-400";
  if (score >= 55) return "text-amber-300";
  return "text-red-400";
}

export default function RoofCheckPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [panelKey, setPanelKey] = useState(0);
  const [flowError, setFlowError] = useState<string | null>(null);
  const [submitBusy, setSubmitBusy] = useState(false);
  const [results, setResults] = useState<ResultsState | null>(null);

  const onQuizComplete = useCallback(
    async (answers: Record<string, number>) => {
      if (authLoading) {
        setFlowError("Checking your session… please try again in a moment.");
        return;
      }

      if (!isAuthenticated) {
        const roof_score = calculateRoofScore(answers);
        const housing_wealth_gap = calculateHousingWealthGap(roof_score);
        setResults({
          roof_score,
          housing_wealth_gap,
          verdict: housing_wealth_gap.verdict,
          insights: [],
          saved: false,
        });
        setFlowError(null);
        return;
      }

      setSubmitBusy(true);
      setFlowError(null);
      try {
        const res = await fetch("/api/life-ledger/roof-check/submit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...csrfHeaders(),
          },
          credentials: "include",
          body: JSON.stringify({ answers }),
        });
        if (!res.ok) {
          let msg = `Could not save Roof Check (${res.status})`;
          try {
            const j = (await res.json()) as { error?: string };
            if (j.error) msg = j.error;
          } catch {
            /* ignore */
          }
          throw new Error(msg);
        }
        const data = (await res.json()) as {
          roof_score: number;
          housing_wealth_gap: HousingWealthGapResult;
          verdict: string;
          insights: InsightRow[];
        };
        setResults({
          roof_score: data.roof_score,
          housing_wealth_gap: data.housing_wealth_gap,
          verdict: data.verdict,
          insights: Array.isArray(data.insights) ? data.insights : [],
          saved: true,
        });
      } catch (e) {
        setFlowError(e instanceof Error ? e.message : "Submit failed");
      } finally {
        setSubmitBusy(false);
      }
    },
    [authLoading, isAuthenticated]
  );

  const retake = useCallback(() => {
    setResults(null);
    setFlowError(null);
    setPanelKey((k) => k + 1);
  }, []);

  const gap = results?.housing_wealth_gap;
  const annual = gap?.annual_wealth_gap ?? 0;
  const tenYr = gap?.ten_year_gap ?? 0;

  return (
    <>
      <Helmet>
        <title>Roof Check — Life Ledger | Mingus</title>
        <meta name="description" content={OG_DESCRIPTION} />
        <meta property="og:title" content="Roof Check — What Is Your Housing Situation Costing You?" />
        <meta property="og:description" content={OG_DESCRIPTION} />
        <meta property="og:type" content="website" />
      </Helmet>

      <div className="min-h-screen bg-[#0d0a08]">
        <main>
          <LandingSection className="py-14 sm:py-20">
            <div className="mx-auto max-w-xl text-center">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-[#C4A064]/90">Life Ledger · Roof</p>
              <h1 className="mt-4 font-display text-3xl font-semibold leading-tight text-[#f0e8d8] sm:text-4xl">
                What Is Your Housing Situation Costing You?
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-[#9a8f7e] sm:text-base">
                12 questions about where you live — and what it means for your wealth.
              </p>
            </div>
          </LandingSection>

          <section
            id="roof-check-quiz"
            tabIndex={-1}
            className="scroll-mt-4 border-t border-[#2a2030] pb-24 outline-none"
            aria-label="Roof Check assessment"
          >
            <LandingSection className="py-12 sm:py-16">
              <div className="mx-auto max-w-xl">
                {flowError && (
                  <div className="mb-8 rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                    {flowError}
                  </div>
                )}

                {!results && (
                  <div className="rounded-2xl border border-[#2a2030] bg-[#1a1520]/50 px-6 py-10 shadow-landing-card sm:px-10">
                    <RoofCheckQuizPanel
                      key={panelKey}
                      onComplete={onQuizComplete}
                      onError={setFlowError}
                      busy={submitBusy || authLoading}
                    />
                  </div>
                )}

                {results && gap && (
                  <div className="space-y-8 rounded-2xl border border-[#2a2030] bg-[#1a1520]/50 px-6 py-10 shadow-landing-card sm:px-10">
                    <div className="text-center">
                      <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">Your Roof Score</p>
                      <p
                        className={`mt-2 font-display text-5xl font-bold tabular-nums sm:text-6xl ${scoreColorClass(
                          results.roof_score
                        )}`}
                      >
                        {results.roof_score}
                      </p>
                      <p className="mt-3 inline-block rounded-full border border-[#C4A064]/40 bg-[#C4A064]/10 px-4 py-1.5 text-sm font-medium text-[#C4A064]">
                        {results.verdict}
                      </p>
                      <p className="mt-3 text-sm text-[#9a8f7e]">Out of 100 · higher reflects stronger housing wealth fit</p>
                    </div>

                    <div className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/60 px-4 py-4">
                      <p className="text-xs uppercase tracking-wider text-[#C4A064]/80">Housing wealth gap</p>
                      {annual > 0 ? (
                        <p className="mt-3 text-sm leading-relaxed text-[#f0e8d8]/95">
                          Your current housing situation may be costing you{" "}
                          <span className="font-semibold text-[#C4A064]">${annual.toLocaleString()}/year</span> in
                          wealth-building potential —{" "}
                          <span className="font-semibold text-[#C4A064]">${tenYr.toLocaleString()}</span> over 10 years
                          (illustrative, with growth assumptions).
                        </p>
                      ) : (
                        <p className="mt-3 text-sm leading-relaxed text-[#f0e8d8]/95">
                          Your answers place you in a strong housing position — we estimate minimal additional
                          wealth-building gap from housing choices right now.
                        </p>
                      )}
                      <p className="mt-2 text-xs leading-relaxed text-[#9a8f7e]">
                        Illustrative estimate vs. an optimized housing path — not an appraisal or tax advice.
                      </p>
                    </div>

                    {results.insights.filter((i) => i.module === "roof").length > 0 && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">Insights</p>
                        <ul className="mt-3 space-y-3">
                          {results.insights
                            .filter((i) => i.module === "roof")
                            .map((ins) => (
                              <li
                                key={ins.id}
                                className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/40 px-4 py-3 text-sm text-[#e8dcc8]"
                              >
                                {ins.message}
                              </li>
                            ))}
                        </ul>
                      </div>
                    )}

                    {!results.saved && (
                      <p className="text-center text-sm text-[#9a8f7e]">
                        Register for Mingus to save this to your Life Ledger and track changes over time.
                      </p>
                    )}

                    {results.saved && (
                      <p className="text-center text-sm text-emerald-400/90">Saved to your Life Ledger profile.</p>
                    )}

                    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-center">
                      {isAuthenticated ? (
                        <Link
                          to="/dashboard/tools?tab=housing"
                          className="inline-flex items-center justify-center rounded-xl bg-[#C4A064] px-5 py-3.5 text-center text-sm font-semibold text-[#0d0a08] transition hover:bg-[#d4b074]"
                        >
                          See your personalized home buying plan in Mingus Housing Intelligence
                        </Link>
                      ) : (
                        <Link
                          to="/register"
                          className="inline-flex items-center justify-center rounded-xl bg-[#C4A064] px-5 py-3.5 text-center text-sm font-semibold text-[#0d0a08] transition hover:bg-[#d4b074]"
                        >
                          Build your wealth plan — Start with Mingus
                        </Link>
                      )}
                      <button
                        type="button"
                        onClick={retake}
                        className="inline-flex items-center justify-center rounded-xl border border-[#2a2030] bg-transparent px-5 py-3.5 text-sm font-medium text-[#f0e8d8] transition hover:border-[#C4A064]/50"
                      >
                        Retake assessment
                      </button>
                    </div>
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
