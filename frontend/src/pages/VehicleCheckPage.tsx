import { Helmet } from "react-helmet-async";
import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { VehicleCheckQuizPanel } from "../components/vehicle-check/VehicleCheckQuizPanel";
import {
  calculateAnnualMaintenance,
  calculateVehicleScore,
  type AnnualMaintenanceResult,
} from "../components/vehicle-check/vehicleCheckScoring";
import { LandingSection } from "../components/landing/LandingSection";
import { useAuth } from "../hooks/useAuth";

const OG_DESCRIPTION =
  "10 questions about your vehicle — and what surprises may be coming. Vehicle Health feeds your Mingus Life Ledger.";

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
  vehicle_score: number;
  annual_maintenance: AnnualMaintenanceResult;
  insights: InsightRow[];
  saved: boolean;
};

function scoreColorClass(score: number): string {
  if (score >= 75) return "text-emerald-400";
  if (score >= 55) return "text-amber-300";
  return "text-red-400";
}

function riskBadgeClasses(risk: AnnualMaintenanceResult["risk_level"]): string {
  switch (risk) {
    case "Low":
      return "border-emerald-700/60 bg-emerald-950/40 text-emerald-200";
    case "Moderate":
      return "border-amber-700/50 bg-amber-950/35 text-amber-200";
    case "High":
      return "border-orange-700/50 bg-orange-950/35 text-orange-200";
    case "Critical":
    default:
      return "border-red-800/60 bg-red-950/40 text-red-200";
  }
}

export default function VehicleCheckPage() {
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
        const vehicle_score = calculateVehicleScore(answers);
        const annual_maintenance = calculateAnnualMaintenance(answers, vehicle_score);
        setResults({
          vehicle_score,
          annual_maintenance,
          insights: [],
          saved: false,
        });
        setFlowError(null);
        return;
      }

      setSubmitBusy(true);
      setFlowError(null);
      try {
        const res = await fetch("/api/life-ledger/vehicle-check/submit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...csrfHeaders(),
          },
          credentials: "include",
          body: JSON.stringify({ answers }),
        });
        if (!res.ok) {
          let msg = `Could not save Vehicle Health (${res.status})`;
          try {
            const j = (await res.json()) as { error?: string };
            if (j.error) msg = j.error;
          } catch {
            /* ignore */
          }
          throw new Error(msg);
        }
        const data = (await res.json()) as {
          vehicle_score: number;
          annual_maintenance: AnnualMaintenanceResult;
          insights: InsightRow[];
        };
        setResults({
          vehicle_score: data.vehicle_score,
          annual_maintenance: data.annual_maintenance,
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

  const dashboardHref = isAuthenticated ? "/dashboard?tab=vehicle" : "/register";
  const dashboardLabel = isAuthenticated
    ? "See your full Vehicle Analytics dashboard in Mingus"
    : "Track your vehicle costs in Mingus — Start free";

  return (
    <>
      <Helmet>
        <title>Vehicle Health — Life Ledger | Mingus</title>
        <meta name="description" content={OG_DESCRIPTION} />
        <meta property="og:title" content="Vehicle Health — What Is Your Vehicle Costing You?" />
        <meta property="og:description" content={OG_DESCRIPTION} />
        <meta property="og:type" content="website" />
      </Helmet>

      <div className="min-h-screen bg-[#0d0a08]">
        <main>
          <LandingSection className="py-14 sm:py-20">
            <div className="mx-auto max-w-xl text-center">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-[#C4A064]/90">
                Life Ledger · Vehicle
              </p>
              <h1 className="mt-4 font-display text-3xl font-semibold leading-tight text-[#f0e8d8] sm:text-4xl">
                What Is Your Vehicle Costing You?
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-[#9a8f7e] sm:text-base">
                10 questions about your vehicle — and what surprises may be coming.
              </p>
            </div>
          </LandingSection>

          <section
            id="vehicle-check-quiz"
            tabIndex={-1}
            className="scroll-mt-4 border-t border-[#2a2030] pb-24 outline-none"
            aria-label="Vehicle Health assessment"
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
                    <VehicleCheckQuizPanel
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
                      <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">Your Vehicle Score</p>
                      <p
                        className={`mt-2 font-display text-5xl font-bold tabular-nums sm:text-6xl ${scoreColorClass(
                          results.vehicle_score
                        )}`}
                      >
                        {results.vehicle_score}
                      </p>
                      <div className="mt-4 flex justify-center">
                        <span
                          className={`inline-flex rounded-full border px-4 py-1.5 text-xs font-semibold uppercase tracking-wider ${riskBadgeClasses(
                            results.annual_maintenance.risk_level
                          )}`}
                        >
                          {results.annual_maintenance.risk_level} risk
                        </span>
                      </div>
                    </div>

                    <div className="rounded-xl border border-[#2a2030] bg-[#0d0a08]/60 px-5 py-4">
                      <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">
                        Estimated annual maintenance
                      </p>
                      <p className="mt-1 font-display text-2xl font-semibold text-[#C4A064] tabular-nums">
                        ${results.annual_maintenance.annual_cost.toLocaleString()}
                      </p>
                      <p className="mt-2 text-sm text-[#9a8f7e]">
                        A planning estimate from your answers — not a quote or guarantee.
                      </p>
                    </div>

                    {results.annual_maintenance.top_risks.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-[#f0e8d8]">Top risks to watch</p>
                        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-[#c9bfb0] [&>li::marker]:text-[#C4A064]">
                          {results.annual_maintenance.top_risks.map((r) => (
                            <li key={r}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {results.insights.filter((i) => i.module === "vehicle").length > 0 && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-[#9a8f7e]">Insights</p>
                        <ul className="mt-3 space-y-3">
                          {results.insights
                            .filter((i) => i.module === "vehicle")
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
                        Create a free Mingus account to save this to your Life Ledger and pre-fill Vehicle Analytics.
                      </p>
                    )}

                    {results.saved && (
                      <p className="text-center text-sm text-emerald-400/90">Saved to your Life Ledger profile.</p>
                    )}

                    <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
                      <Link
                        to={dashboardHref}
                        className="inline-flex justify-center rounded-xl bg-[#C4A064] px-5 py-3 text-center text-sm font-semibold text-[#0d0a08] shadow-landing-card transition hover:bg-[#d4b074]"
                      >
                        {dashboardLabel}
                      </Link>
                      <button
                        type="button"
                        onClick={retake}
                        className="inline-flex justify-center rounded-xl border border-[#2a2030] px-5 py-3 text-sm font-medium text-[#f0e8d8] transition hover:border-[#C4A064]/40"
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
