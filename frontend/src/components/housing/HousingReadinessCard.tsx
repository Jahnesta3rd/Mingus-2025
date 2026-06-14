import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Lock, X } from 'lucide-react';
import { useAuth, type AuthUserTier } from '../../hooks/useAuth';
import { useHousingCheckIn } from '../../hooks/useHousingCheckIn';
import { deriveUserTier } from '../fluency';

const CARD_GRADIENT =
  'bg-gradient-to-br from-[#3b0a14] via-[#4a1a42] to-[#1e1458]';

const PILLAR_ORDER = [
  { key: 'down_payment', label: 'Down Payment' },
  { key: 'dti', label: 'Debt-to-Income' },
  { key: 'credit', label: 'Credit Score' },
  { key: 'income', label: 'Income Stability' },
  { key: 'reserves', label: 'Cash Reserves' },
] as const;

type PillarKey = (typeof PILLAR_ORDER)[number]['key'];

interface PillarScore {
  score: number;
  weight: number;
}

interface RiskChip {
  band: string | null;
  modifier?: number;
  active_layoff?: boolean;
  verdict?: string | null;
  annual_repair_exposure?: number | null;
}

interface MonthlyAction {
  action: string;
  impact_score: number;
  dimension: string;
}

interface PlanPhase {
  phase_name: string;
  duration_months: number;
  goal: string;
  actions: string[];
}

interface MortgageEstimate {
  monthly_piti: number | null;
  front_end_dti: number | null;
}

interface ReadinessPlan {
  summary?: string;
  score_band?: string;
  plan_phases?: PlanPhase[];
  monthly_actions?: MonthlyAction[];
  quick_wins?: string[];
  watch_flags?: string[];
  projected_score?: number;
  mortgage_estimate?: MortgageEstimate;
}

export interface ReadinessScoreResponse {
  score: number;
  score_band: string | null;
  readiness_tier: string;
  overall_score: number;
  partial_data: boolean;
  pillars: Record<PillarKey, PillarScore>;
  career_risk: RiskChip;
  vehicle_risk: RiskChip;
  combined_modifier: number;
  plan: ReadinessPlan | null;
  plan_loading: boolean;
  generated_at: string | null;
  expires_at: string | null;
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function scoreColor(score: number): string {
  if (score < 20) return '#ef4444';
  if (score < 40) return '#f97316';
  if (score < 60) return '#f59e0b';
  if (score < 80) return '#84cc16';
  return '#22c55e';
}

function bandChipClasses(band: string | null | undefined): { text: string; dot: string } {
  const b = (band || '').toUpperCase();
  if (b === 'LOW' || b === 'STABLE') return { text: 'text-green-400', dot: 'bg-green-400' };
  if (b === 'MODERATE' || b === 'WATCH') return { text: 'text-amber-400', dot: 'bg-amber-400' };
  if (b === 'HIGH' || b === 'ELEVATED') return { text: 'text-orange-400', dot: 'bg-orange-400' };
  if (b === 'CRITICAL') return { text: 'text-red-400', dot: 'bg-red-400' };
  return { text: 'text-gray-400', dot: 'bg-gray-400' };
}

function formatUpdatedAt(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function careerChipExplanation(band: string | null | undefined, activeLayoff: boolean): string {
  if (activeLayoff) return 'Recent layoff activity at your employer — stabilize income before major housing moves.';
  const b = (band || '').toUpperCase();
  if (b === 'LOW') return 'Employment outlook looks stable for mortgage planning.';
  if (b === 'MODERATE') return 'Some career uncertainty — keep monitoring income stability.';
  if (b === 'HIGH' || b === 'ELEVATED') return 'Elevated career risk may affect lender confidence — build a buffer.';
  if (b === 'CRITICAL') return 'Critical career risk — prioritize job stability before buying.';
  return 'Career risk data unavailable.';
}

function vehicleChipExplanation(
  band: string | null | undefined,
  exposure: number | null | undefined,
  verdict: string | null | undefined,
): string {
  const b = (band || '').toUpperCase();
  const exp = exposure != null ? `$${Math.round(exposure).toLocaleString()}/yr repair exposure` : 'repair costs';
  if (b === 'STABLE' || b === 'LOW') return 'Vehicle costs look manageable relative to your housing timeline.';
  if (b === 'WATCH') return `Monitor vehicle costs — ${exp}.`;
  if (b === 'ELEVATED' || b === 'HIGH') return `Vehicle may need attention soon — ${exp}.`;
  if (b === 'CRITICAL') {
    return verdict === 'replace'
      ? `Vehicle flagged for replacement — ${exp}. Resolve before ramping savings.`
      : `Critical vehicle risk — ${exp}. Plan a repair-or-replace decision.`;
  }
  return 'Vehicle risk data unavailable.';
}

function isCriticalWatchFlag(flag: string): boolean {
  const lower = flag.toLowerCase();
  return lower.includes('critical') || lower.includes('replace') || lower.includes('layoff');
}

async function fetchReadinessScore(): Promise<ReadinessScoreResponse> {
  const res = await fetch('/api/housing/readiness-score', {
    credentials: 'include',
    headers: buildAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load readiness score');
  return (await res.json()) as ReadinessScoreResponse;
}

function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p className="text-xs font-semibold tracking-widest text-amber-400 uppercase">{children}</p>
  );
}

function AmberButton({
  children,
  onClick,
  className = '',
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border border-amber-400 bg-transparent px-4 py-2 text-sm font-semibold text-amber-400 transition hover:bg-amber-400/10 ${className}`}
    >
      {children}
    </button>
  );
}

function ScoreDial({ score, scoreBand }: { score: number; scoreBand: string | null }) {
  const arcLength = 157;
  const progress = (Math.min(100, Math.max(0, score)) / 100) * arcLength;
  const color = scoreColor(score);

  return (
    <div className="relative mx-auto flex w-44 flex-col items-center">
      <svg viewBox="0 0 120 72" className="h-24 w-40" aria-hidden>
        <path
          d="M 12 58 A 48 48 0 0 1 108 58"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <path
          d="M 12 58 A 48 48 0 0 1 108 58"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${arcLength}`}
        />
      </svg>
      <div className="absolute inset-x-0 top-8 text-center">
        <p className="text-4xl font-bold text-white">{score}</p>
        {scoreBand ? (
          <p className="mt-1 text-xs font-semibold tracking-widest text-amber-400 uppercase">
            {scoreBand}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ImpactDots({ score }: { score: number }) {
  const clamped = Math.min(10, Math.max(1, Math.round(score)));
  return (
    <div className="mt-2 flex gap-1" aria-label={`Impact ${clamped} of 10`}>
      {Array.from({ length: 10 }, (_, i) => (
        <span
          key={i}
          className={`h-2 w-2 rounded-full ${i < clamped ? 'bg-amber-400' : 'bg-white/15'}`}
        />
      ))}
    </div>
  );
}

function CardSkeleton() {
  return (
    <div className={`animate-pulse rounded-2xl p-5 ${CARD_GRADIENT}`}>
      <div className="mx-auto mb-4 h-24 w-40 rounded-full bg-white/10" />
      <div className="mb-3 h-4 rounded bg-white/10" />
      <div className="mb-6 h-3 w-2/3 rounded bg-white/10" />
      <div className="mb-2 h-2 rounded-full bg-white/10" />
      <div className="mb-2 h-2 rounded-full bg-white/10" />
      <div className="h-2 rounded-full bg-white/10" />
    </div>
  );
}

function RiskChipButton({
  label,
  band,
  expanded,
  explanation,
  onToggle,
}: {
  label: string;
  band: string | null | undefined;
  expanded: boolean;
  explanation: string;
  onToggle: () => void;
}) {
  const styles = bandChipClasses(band);
  return (
    <div className="min-w-0 flex-1">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-2 rounded-full bg-white/10 px-3 py-2 text-left"
      >
        <span className={`h-2 w-2 shrink-0 rounded-full ${styles.dot}`} />
        <span className={`truncate text-xs font-semibold ${styles.text}`}>
          {label} · {(band || 'N/A').toUpperCase()}
        </span>
      </button>
      {expanded ? (
        <p className="mt-2 px-1 text-xs leading-relaxed text-gray-400">{explanation}</p>
      ) : null}
    </div>
  );
}

function PlanSkeleton() {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-400">Building your action plan…</p>
      <div className="h-3 animate-pulse rounded bg-white/10" />
      <div className="h-3 w-5/6 animate-pulse rounded bg-white/10" />
      <div className="h-3 w-4/6 animate-pulse rounded bg-white/10" />
    </div>
  );
}

function BudgetOverlay({ onUpgrade }: { onUpgrade: () => void }) {
  return (
    <div className="mt-6 flex flex-col items-center rounded-2xl border border-amber-400/20 bg-white/5 px-4 py-8 text-center">
      <Lock className="mb-3 h-6 w-6 text-amber-400" aria-hidden />
      <p className="text-base font-semibold text-white">See exactly what to fix</p>
      <p className="mt-2 text-sm text-gray-400">Upgrade to Mid-Tier for your full action plan.</p>
      <AmberButton className="mt-5" onClick={onUpgrade}>
        Upgrade →
      </AmberButton>
    </div>
  );
}

export function HousingReadinessCard({ refreshTrigger = 0 }: { refreshTrigger?: number } = {}) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userTier: AuthUserTier = deriveUserTier(user);
  const isBudget = userTier === 'budget';

  const {
    data: housingProfile,
    loading: profileLoading,
    error: profileError,
    refetch: refetchProfile,
  } = useHousingCheckIn();

  const [data, setData] = useState<ReadinessScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [expandedRisk, setExpandedRisk] = useState<'career' | 'vehicle' | null>(null);
  const [expandedAction, setExpandedAction] = useState<number | null>(null);
  const [expandedPhase, setExpandedPhase] = useState<number | null>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => setFetchKey((k) => k + 1), []);

  const hasHousingProfile = Boolean(housingProfile?.profileComplete);

  useEffect(() => {
    if (profileLoading || !hasHousingProfile) {
      if (!profileLoading) setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(false);

    fetchReadinessScore()
      .then((payload) => {
        if (cancelled) return;
        setData(payload);
      })
      .catch(() => {
        if (cancelled) return;
        setData(null);
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [fetchKey, profileLoading, hasHousingProfile, refreshTrigger]);

  useEffect(() => {
    if (!hasHousingProfile || !data?.plan_loading) return undefined;

    const timer = window.setInterval(() => {
      refetch();
    }, 15000);

    return () => window.clearInterval(timer);
  }, [data?.plan_loading, hasHousingProfile, refetch]);

  const plan = data?.plan ?? null;
  const summaryText = plan?.summary ?? '';

  const scoreBandLabel = useMemo(
    () => data?.score_band ?? plan?.score_band ?? null,
    [data?.score_band, plan?.score_band],
  );

  if (profileLoading || (loading && hasHousingProfile && !data && !error)) {
    return <CardSkeleton />;
  }

  if (profileError) {
    return (
      <div className={`rounded-2xl p-5 text-center ${CARD_GRADIENT}`}>
        <p className="text-sm text-gray-300">Unable to load your readiness score.</p>
        <AmberButton className="mt-4" onClick={() => void refetchProfile()}>
          Retry
        </AmberButton>
      </div>
    );
  }

  if (!hasHousingProfile) {
    return (
      <div className={`rounded-2xl p-5 text-center ${CARD_GRADIENT}`}>
        <p className="text-base font-semibold text-white">Add your housing goals to see your score.</p>
        <AmberButton
          className="mt-4"
          onClick={() => navigate('/dashboard/tools?tab=housing')}
        >
          Set up housing →
        </AmberButton>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`rounded-2xl p-5 text-center ${CARD_GRADIENT}`}>
        <p className="text-sm text-gray-300">Unable to load your readiness score.</p>
        <AmberButton className="mt-4" onClick={refetch}>
          Retry
        </AmberButton>
      </div>
    );
  }

  const mortgage = plan?.mortgage_estimate;
  const hasMortgageEstimate =
    mortgage != null &&
    (mortgage.monthly_piti != null || mortgage.front_end_dti != null);

  return (
    <div className={`rounded-2xl p-5 ${CARD_GRADIENT}`}>
      {data.partial_data && !bannerDismissed ? (
        <div className="mb-4 flex items-start gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 p-3">
          <p className="flex-1 text-sm text-amber-300">
            Score based on partial data — complete your housing profile.
          </p>
          <button
            type="button"
            aria-label="Dismiss"
            className="text-amber-300/80 hover:text-amber-200"
            onClick={() => setBannerDismissed(true)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : null}

      {/* Section 1 — Score Dial */}
      <section>
        <Eyebrow>Purchase Readiness</Eyebrow>
        <div className="mt-4">
          <ScoreDial score={data.overall_score} scoreBand={scoreBandLabel} />
        </div>
        {summaryText ? (
          <button
            type="button"
            className="mt-3 w-full text-left"
            onClick={() => setSummaryExpanded((v) => !v)}
          >
            <p
              className={`text-sm text-gray-300 ${summaryExpanded ? '' : 'line-clamp-2'}`}
            >
              {summaryText}
            </p>
          </button>
        ) : null}
      </section>

      {/* Section 2 — Risk Alert Chips */}
      <section className="mt-6 flex gap-2">
        <RiskChipButton
          label="CAREER"
          band={data.career_risk.band}
          expanded={expandedRisk === 'career'}
          explanation={careerChipExplanation(
            data.career_risk.band,
            Boolean(data.career_risk.active_layoff),
          )}
          onToggle={() =>
            setExpandedRisk((prev) => (prev === 'career' ? null : 'career'))
          }
        />
        <RiskChipButton
          label="VEHICLE"
          band={data.vehicle_risk.band}
          expanded={expandedRisk === 'vehicle'}
          explanation={vehicleChipExplanation(
            data.vehicle_risk.band,
            data.vehicle_risk.annual_repair_exposure,
            data.vehicle_risk.verdict,
          )}
          onToggle={() =>
            setExpandedRisk((prev) => (prev === 'vehicle' ? null : 'vehicle'))
          }
        />
      </section>

      {/* Section 3 — Pillar Bars */}
      <section className={`mt-6 space-y-3 ${isBudget ? 'pointer-events-none blur-sm opacity-30' : ''}`}>
        {PILLAR_ORDER.map(({ key, label }) => {
          const pillar = data.pillars[key];
          const pct = Math.min(100, Math.max(0, pillar?.score ?? 0));
          return (
            <div key={key}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-sm text-gray-300">{label}</span>
                <span className="text-sm text-amber-400">{pct}</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/10">
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: scoreColor(pct) }}
                />
              </div>
            </div>
          );
        })}
      </section>

      {/* Section 4 / 5 — Plan Area or Budget Overlay */}
      {isBudget ? (
        <BudgetOverlay onUpgrade={() => navigate('/dashboard/upgrade')} />
      ) : (
        <section className="mt-6 space-y-6">
          {data.plan_loading && !plan ? (
            <PlanSkeleton />
          ) : null}

          {plan ? (
            <>
              {plan.monthly_actions && plan.monthly_actions.length > 0 ? (
                <div>
                  <Eyebrow>This Month</Eyebrow>
                  <div className="mt-3 space-y-2">
                    {plan.monthly_actions.slice(0, 3).map((item, idx) => (
                      <div key={idx}>
                        <button
                          type="button"
                          className="flex w-full items-center gap-2 rounded-xl bg-white/5 px-3 py-3 text-left"
                          onClick={() =>
                            setExpandedAction((prev) => (prev === idx ? null : idx))
                          }
                        >
                          <span className="flex-1 text-sm text-white">{item.action}</span>
                          <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
                        </button>
                        {expandedAction === idx ? (
                          <div className="px-3 pb-2">
                            <p className="text-xs text-amber-400">{item.dimension}</p>
                            <ImpactDots score={item.impact_score} />
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {plan.quick_wins && plan.quick_wins.length > 0 ? (
                <div>
                  <Eyebrow>30-Day Wins</Eyebrow>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {plan.quick_wins.map((win) => (
                      <span
                        key={win}
                        className="rounded-full border border-amber-400/50 bg-amber-400/10 px-3 py-1 text-xs text-amber-400"
                      >
                        {win}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {plan.plan_phases && plan.plan_phases.length > 0 ? (
                <div>
                  <Eyebrow>Your Plan</Eyebrow>
                  <div className="mt-3 flex gap-3 overflow-x-auto pb-1">
                    {plan.plan_phases.map((phase, idx) => {
                      const isCurrent = idx === 0;
                      return (
                        <button
                          key={phase.phase_name}
                          type="button"
                          className="min-w-[140px] shrink-0 text-left"
                          onClick={() =>
                            setExpandedPhase((prev) => (prev === idx ? null : idx))
                          }
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={`h-2.5 w-2.5 rounded-full ${
                                isCurrent ? 'bg-amber-400' : 'bg-gray-500'
                              }`}
                            />
                            <span
                              className={`text-sm font-medium ${
                                isCurrent ? 'text-white' : 'text-gray-400'
                              }`}
                            >
                              {phase.phase_name}
                            </span>
                          </div>
                          {expandedPhase === idx ? (
                            <div className="mt-2 pl-4">
                              <p className="text-sm text-gray-300">{phase.goal}</p>
                              <ul className="mt-2 space-y-1">
                                {phase.actions.slice(0, 2).map((action) => (
                                  <li key={action} className="text-sm text-gray-300">
                                    • {action}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {plan.watch_flags && plan.watch_flags.length > 0 ? (
                <div>
                  <Eyebrow>Watch</Eyebrow>
                  <ul className="mt-3 space-y-2">
                    {plan.watch_flags.map((flag) => (
                      <li
                        key={flag}
                        className={`flex gap-2 text-sm ${
                          isCriticalWatchFlag(flag) ? 'text-red-400' : 'text-gray-300'
                        }`}
                      >
                        <span aria-hidden>⚠</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div>
                {hasMortgageEstimate ? (
                  <p className="text-xs text-gray-400">
                    Est. monthly: $
                    {mortgage?.monthly_piti != null
                      ? Math.round(mortgage.monthly_piti).toLocaleString()
                      : '—'}{' '}
                    · DTI{' '}
                    {mortgage?.front_end_dti != null
                      ? `${Math.round(mortgage.front_end_dti * 100)}%`
                      : '—'}
                  </p>
                ) : (
                  <p className="text-xs text-gray-400">
                    Complete your housing profile for a mortgage estimate.
                  </p>
                )}
                {plan.projected_score != null ? (
                  <p className="mt-2 text-xs text-gray-400">
                    On track for {plan.projected_score}/100
                  </p>
                ) : null}
              </div>
            </>
          ) : data.plan_loading ? (
            <PlanSkeleton />
          ) : null}
        </section>
      )}

      {/* Section 7 — Refresh footer */}
      {data.generated_at ? (
        <p className="mt-4 text-right text-xs text-gray-600">
          Updated {formatUpdatedAt(data.generated_at)}
        </p>
      ) : null}
    </div>
  );
}

export default HousingReadinessCard;
