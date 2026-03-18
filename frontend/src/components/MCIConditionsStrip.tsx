import React, { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Line, LineChart, ResponsiveContainer } from "recharts";
import { useMCI } from "../context/MCIContext";
import type { MCIDirection, MCISnapshot, MCISeverity } from "../types/mci";

interface MCIConditionsStripProps {
  userTier: "budget" | "mid" | "professional";
  className?: string;
}

type SeverityStyles = {
  badgeBg: string;
  badgeText: string;
  dotBg: string;
  arrowText: string;
};

const severityStyles: Record<MCISeverity, SeverityStyles> = {
  green: {
    badgeBg: "bg-green-100",
    badgeText: "text-green-800",
    dotBg: "bg-green-500",
    arrowText: "text-green-600",
  },
  amber: {
    badgeBg: "bg-amber-100",
    badgeText: "text-amber-800",
    dotBg: "bg-amber-500",
    arrowText: "text-amber-700",
  },
  red: {
    badgeBg: "bg-red-100",
    badgeText: "text-red-800",
    dotBg: "bg-red-500",
    arrowText: "text-red-700",
  },
};

const directionSymbol: Record<MCIDirection, string> = {
  up: "↑",
  down: "↓",
  flat: "→",
};

const severityToScore: Record<MCISeverity, number> = {
  green: 80,
  amber: 50,
  red: 20,
};

const sparklineStrokeBySeverity: Record<MCISeverity, string> = {
  green: "#059669",
  amber: "#D97706",
  red: "#DC2626",
};

const formatMonthDay = (isoDate: string) => {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-US", { month: "short", day: "2-digit" });
};

const formatMonthYear = (isoDate: string) => {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
};

const LockOverlay: React.FC = () => {
  return (
    <div className="absolute inset-0 flex items-center justify-center px-2">
      <div className="text-center">
        <div className="mx-auto mb-2 w-10 h-10 rounded-full bg-white/80 border border-gray-200 flex items-center justify-center">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden
          >
            <path
              d="M7 10V7.8C7 5.149 9.239 3 12 3C14.761 3 17 5.149 17 7.8V10"
              stroke="#6b7280"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M6.5 10H17.5C18.328 10 19 10.672 19 11.5V19C19 19.828 18.328 20.5 17.5 20.5H6.5C5.672 20.5 5 19.828 5 19V11.5C5 10.672 5.672 10 6.5 10Z"
              stroke="#6b7280"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <path
              d="M12 14V16"
              stroke="#6b7280"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div className="text-xs font-semibold text-gray-700">
          Upgrade to Mid-tier
        </div>
      </div>
    </div>
  );
};

const MCIConditionsStrip: React.FC<MCIConditionsStripProps> = ({
  userTier,
  className = "",
}) => {
  const { snapshot, loading, error, refresh } = useMCI();
  const [expanded, setExpanded] = useState(false);
  const [history, setHistory] = useState<MCISnapshot[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const unlockedSlugs = useMemo(
    () => new Set(["labor_market_strength", "housing_affordability_pressure"]),
    []
  );

  const constituents = useMemo(() => {
    const raw = snapshot?.constituents ?? [];
    // Sort by weight descending before rendering (stable sort keeps tied
    // weights in their original order from the backend).
    return [...raw].sort((a, b) => (b.weight ?? 0) - (a.weight ?? 0));
  }, [snapshot]);

  const compositeSeverity = snapshot?.composite_severity ?? "amber";
  const compStyles = severityStyles[compositeSeverity];

  const toggleExpanded = () => {
    if (loading) return;
    setExpanded((v) => !v);
  };

  // Professional tier only: fetch historical weekly snapshots for sparklines.
  useEffect(() => {
    if (userTier !== "professional") return;
    if (!snapshot) return;

    let cancelled = false;
    const loadHistory = async () => {
      setHistoryLoading(true);
      try {
        const tokenFromMingus = localStorage.getItem("mingus_token");
        const tokenFromAuth = localStorage.getItem("auth_token");
        const token = tokenFromMingus ?? tokenFromAuth ?? "";

        const res = await fetch(`/api/mci/history?t=${Date.now()}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!res.ok) {
          throw new Error("Failed to fetch MCI history");
        }

        const data = await res.json();
        if (cancelled) return;
        setHistory(Array.isArray(data) ? (data as MCISnapshot[]) : []);
      } catch {
        if (!cancelled) setHistory([]);
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    };

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [userTier, snapshot?.snapshot_date]);

  if (loading) {
    return (
      <div
        className={`border border-gray-200 rounded-xl p-4 bg-white shadow-sm ${className}`}
        aria-busy
      >
        <div className="animate-pulse bg-gray-200 rounded h-4 w-48" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`border border-gray-200 rounded-xl p-4 bg-white shadow-sm cursor-pointer ${className}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="text-gray-500 text-sm font-medium">
            Conditions unavailable
          </div>
          <button
            type="button"
            className="text-xs text-blue-600 hover:text-blue-700 cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              refresh();
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div
        className={`border border-gray-200 rounded-xl p-4 bg-white shadow-sm ${className}`}
      >
        <div className="text-gray-400 text-sm">Conditions unavailable</div>
      </div>
    );
  }

  const compositeScoreInt = Math.max(0, Math.min(100, Math.round(snapshot.composite_score)));

  return (
    <div
      className={`border border-gray-200 rounded-xl p-4 bg-white shadow-sm cursor-pointer ${className}`}
      onClick={toggleExpanded}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") toggleExpanded();
      }}
      aria-expanded={expanded}
    >
      {/* Collapsed Row */}
      <div className="flex items-center justify-between gap-4">
        {/* LEFT: composite score */}
          <div className="flex flex-col items-center">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center ${compStyles.badgeBg} ${compStyles.badgeText} font-semibold`}
            >
              {compositeScoreInt}
            </div>
            <div className="mt-1 text-xs text-gray-700 font-medium">Conditions</div>
          </div>

        {/* CENTER: headline + update */}
        <div className="flex-1 text-center">
          <div className="text-sm text-gray-700 truncate">
            {snapshot.composite_headline}
          </div>
          <div className="text-xs text-gray-400">
            Updated {formatMonthDay(snapshot.snapshot_date)}
          </div>
        </div>

        {/* RIGHT: expand toggle */}
        <div className="flex items-center gap-2">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-blue-600" aria-hidden />
          ) : (
            <ChevronDown className="w-4 h-4 text-blue-600" aria-hidden />
          )}
          <div className="text-xs text-blue-600 cursor-pointer select-none">
            {expanded ? "Hide conditions" : "View conditions"}
          </div>
        </div>
      </div>

      {/* Expanded: constituent grid */}
      <div
        className="overflow-hidden transition-all duration-300"
        style={{ maxHeight: expanded ? 1000 : 0, opacity: expanded ? 1 : 0.98 }}
      >
        <div className="pt-4">
          <div
            className={`grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`}
          >
            {constituents.map((c) => {
              const styles = severityStyles[c.severity];
              const isLocked = userTier === "budget" && !unlockedSlugs.has(c.slug);

              return (
                <div key={c.slug} className="relative">
                  <div className="border border-gray-100 rounded-lg p-3 bg-gray-50">
                    <div
                      className={isLocked ? "blur-sm opacity-50 pointer-events-none" : ""}
                    >
                      {/* Top row */}
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${styles.dotBg}`} />
                        <div className="text-sm font-medium text-gray-800">{c.name}</div>
                        <div className={`ml-auto text-sm ${styles.arrowText}`}>
                          {directionSymbol[c.direction]}
                        </div>
                      </div>

                      {/* Body */}
                      <div
                        className="mt-2 text-xs text-gray-600 overflow-hidden"
                        style={
                          {
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                          } as React.CSSProperties
                        }
                      >
                        {c.headline}
                      </div>

                      {/* Footer */}
                      <div className="mt-2 text-xs text-gray-400">
                        <div>Source: {c.source}</div>
                        <div>As of {formatMonthYear(c.as_of)}</div>
                      </div>

                      {/* Professional sparkline placeholder */}
                      {userTier === "professional" && (
                        (() => {
                          const sparklineData = history
                            .map((week) => {
                              const weeklyConstituent = week.constituents?.find(
                                (x) => x.slug === c.slug
                              );
                              if (!weeklyConstituent) return null;

                              const weeklySeverity = weeklyConstituent
                                .severity as MCISeverity;
                              const weight =
                                typeof weeklyConstituent.weight === "number"
                                  ? weeklyConstituent.weight
                                  : 0;

                              const score = severityToScore[weeklySeverity] ?? 0;
                              return { value: score * weight };
                            })
                            .filter((v): v is { value: number } => v !== null);

                          const showPlaceholder =
                            historyLoading || history.length === 0 || sparklineData.length === 0;

                          return (
                            <div className="mci-sparkline-slot mt-2">
                              {showPlaceholder ? (
                                <div className="text-xs text-gray-300 italic">Trend data</div>
                              ) : (
                                <ResponsiveContainer width="100%" height={48}>
                                  <LineChart
                                    data={sparklineData}
                                    margin={{
                                      top: 0,
                                      right: 0,
                                      bottom: 0,
                                      left: 0,
                                    }}
                                  >
                                    <Line
                                      type="monotone"
                                      dataKey="value"
                                      stroke={sparklineStrokeBySeverity[c.severity]}
                                      strokeWidth={2}
                                      dot={false}
                                      isAnimationActive={false}
                                    />
                                  </LineChart>
                                </ResponsiveContainer>
                              )}
                            </div>
                          );
                        })()
                      )}
                    </div>

                    {isLocked && (
                      <div className="absolute inset-0 rounded-lg">
                        <div className="absolute inset-0 bg-gray-50/60" />
                        <LockOverlay />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCIConditionsStrip;

