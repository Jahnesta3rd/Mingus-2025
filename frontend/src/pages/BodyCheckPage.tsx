import { Helmet } from "react-helmet-async";
import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { BodyCheckQuizPanel } from "../components/body-check/BodyCheckQuizPanel";
import {
  calculateBodyScore,
  calculateHealthCostProjection,
  calculateProductivityImpact,
} from "../components/body-check/bodyCheckScoring";
import { LandingSection } from "../components/landing/LandingSection";
import { useAuth } from "../hooks/useAuth";

const OG_DESCRIPTION =
  "15 questions about your health habits — and what they mean for your finances. Body Check feeds your Mingus Life Ledger.";

const PLACEHOLDER_INCOME = 75_000;

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
  body_score: number;
  health_cost_projection: number;
  productivity_impact: {
    lost_days_per_month: number;
    annual_income_impact_pct: number;
  };
  insights: InsightRow[];
  saved: boolean;
};

function scoreColorClass(score: number): string {
  if (score >= 75) return "text-emerald-400";
  if (score >= 55) return "text-amber-300";
  return "text-red-400";
}

function formatLostDays(n: number): string {
  if (Number.isInteger(n)) return String(n);
  return n.toFixed(1);
}

export default function BodyCheckPage() {
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
        const body_score = calculateBodyScore(answers);
        const health_cost_projection = calculateHealthCostProjection(body_score);
        const productivity_impact = calculateProductivityImpact(body_score);
        setResults({
          body_score,
          health_cost_projection,
          productivity_impact,
          insights: [],
          saved: false,
        });
        setFlowError(null);
        return;
      }

      setSubmitBusy(true);
      setFlowError(null);
      try {
        const res = await fetch("/api/life-ledger/body-check/submit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...csrfHeaders(),
          },
          credentials: "include",
          body: JSON.stringify({ answers }),
        });
        if (!res.ok) {
          let msg = `Could not save Body Check (${res.status})`;
          try {
            const j = (await res.json()) as { error?: string };
            if (j.error) msg = j.error;
          } catch {
            /* ignore */
          }
          throw new Error(msg);
        }
        const data = (await res.json()) as {
          body_score: number;
          health_cost_projection: number;
          productivity_impact: ResultsState["productivity_impact"];
          insights: InsightRow[];
        };
        setResults({
          body_score: data.body_score,
          health_cost_projection: data.health_cost_projection,
          productivity_impact: data.productivity_impact,
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

  const incomeImpactDollars = results
    ? Math.round(PLACEHOLDER_INCOME * results.productivity_impact.annual_income_impact_pct)
    : 0;

  const dashboardHref = isAuthenticated ? "/dashboard" : "/register";
  const dashboardLabel = isAuthenticated
    ? "See this in your Mingus dashboard"
    : "Register to save and track over time";

  return (
    <>
      <Helmet>
        <title>Body Check — Life Ledger | Mingus</title>
        <meta name="description" content={OG_DESCRIPTION} />
        <meta property="og:title" content="Body Check — What Is Your Body Costing You?" />
        <meta property="og:description" content={OG_DESCRIPTION} />
        <meta property="og:type" content="website" />
      </Helmet>

      <div className="min-h-screen bg-[#0d0a08]">
        <main>
          <LandingSection className="py-14 sm:py-20">
            <div className="mx-auto max-w-xl text-center">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-[#C4A064]/90">Life Ledger · Body</p>
              <h1 className="mt-4 font-display text-3xl font-semibold leading-tight text-[#f0e8d8] sm:text-4xl">
                What Is Your Body Costing You?
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-[#9a8f7e] sm:text-base">
                15 questions about your health habits — and what they mean for your finances.
              </p>
            </div>
          </LandingSection>

          <section
            id="body-check-quiz"
            tabIndex={-1}
            className="scroll-mt-4 border-t border-[#2a2030] pb-24 outline-none"
            aria-label="Body Check assessment"
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
                    <BodyCheckQuizPanel
                      key={panelKey}
                      onComplete={onQuizComplete}
                      onError={setFlowError}
                      busy={submitBusy || authLoading}
                    />
                  </div>
                )}

                {results && (
                  <div className="space-y-8 rounded-2xl border border-[#2a2030] bg-[#1a1520]/50 px-6 py-10 shadow-landing-card sm:px-10">
                    <div className="text-center">
                      <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">Your Body Score</p>
                      <p
                        className={`mt-2 font-display text-5xl font-bold tabular-nums sm:text-6xl ${scoreColorClass(
                          results.body_score
                        )}`}
                      >
                        {results.body_score}
                      </p>
                      <p className="mt-2 text-sm text-[#9a8f7e]">Out of 100 · higher is stronger overall wellness habits</p>
                    </div>

                    <div className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/60 px-4 py-4">
                      <p className="text-xs uppercase tracking-wider text-[#C4A064]/80">Estimated annual health cost</p>
                      <p className="mt-1 font-display text-2xl font-semibold tabular-nums text-[#f0e8d8]">
                        ${results.health_cost_projection.toLocaleString()}
                        <span className="text-base font-normal text-[#9a8f7e]"> / year</span>
                      </p>
                      <p className="mt-2 text-xs leading-relaxed text-[#9a8f7e]">
                        Illustrative projection based on your score — not a medical or insurance estimate.
                      </p>
                    </div>

                    <div className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/60 px-4 py-4 text-left">
                      <p className="text-xs uppercase tracking-wider text-[#C4A064]/80">Productivity impact</p>
                      <p className="mt-3 text-sm leading-relaxed text-[#f0e8d8]/95">
                        Based on your score, you may be losing{" "}
                        <span className="font-semibold text-[#C4A064]">
                          {formatLostDays(results.productivity_impact.lost_days_per_month)} days/month
                        </span>{" "}
                        to health-related productivity loss — worth approximately{" "}
                        <span className="font-semibold text-[#C4A064]">
                          ${incomeImpactDollars.toLocaleString()}/year
                        </span>{" "}
                        assuming a ${PLACEHOLDER_INCOME.toLocaleString()} annual income placeholder.
                      </p>
                    </div>

                    {results.insights.filter((i) => i.module === "body").length > 0 && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">Insights</p>
                        <ul className="mt-3 space-y-3">
                          {results.insights
                            .filter((i) => i.module === "body")
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

                    <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
                      <Link
                        to={dashboardHref}
                        className="inline-flex items-center justify-center rounded-xl bg-[#C4A064] px-5 py-3.5 text-center text-sm font-semibold text-[#0d0a08] transition hover:bg-[#d4b074]"
                      >
                        {dashboardLabel}
                      </Link>
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
