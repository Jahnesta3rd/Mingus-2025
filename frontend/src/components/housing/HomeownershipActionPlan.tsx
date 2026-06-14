import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { csrfHeaders } from '../../utils/csrfHeaders';

export interface HomeownershipActionPlanProps {
  gapAnalysisId: number;
  userTier: 'budget' | 'mid_tier' | 'professional';
  onBack: () => void;
  className?: string;
}

interface PillarOne {
  title: string;
  invoke: boolean;
  monthly_target: number;
  current_monthly: number;
  gap: number;
  actions: string[];
  timeline_months: number;
}

interface PillarTwo {
  title: string;
  invoke: boolean;
  income_gap?: number;
  actions?: string[];
  timeline_months?: number;
}

interface PillarThree {
  title: string;
  invoke: boolean;
  monthly_target?: number;
  job_types?: string[];
  timeline_months?: number;
}

interface TimelineMilestone {
  month: number;
  milestone: string;
  pillar: string;
}

interface ActionPlan {
  summary: string;
  scenario_label: string;
  pillar_1: PillarOne;
  pillar_2: PillarTwo;
  pillar_3: PillarThree;
  unified_timeline: TimelineMilestone[];
}

interface ActionPlanResponse {
  plan: ActionPlan;
  cached: boolean;
}

interface GapAnalysisMeta {
  plan_generated_at: string | null;
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  return {
    ...csrfHeaders(),
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function formatCurrency(value: number): string {
  return `$${Math.round(Math.abs(value)).toLocaleString()}`;
}

function formatPlanDate(iso: string | null | undefined): string {
  if (!iso) return 'your last session';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return 'your last session';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function TimelineChip({ months }: { months: number }) {
  return (
    <span className="mt-3 inline-block rounded-full bg-teal-50 px-3 py-1 text-xs text-teal-700">
      Close in {months} months
    </span>
  );
}

function NumberedActions({ actions }: { actions: string[] }) {
  return (
    <ol className="mt-3 list-none space-y-1">
      {actions.map((action, idx) => (
        <li key={action} className="text-sm text-gray-700">
          {idx + 1}. {action}
        </li>
      ))}
    </ol>
  );
}

function PillarCard({ children }: { children: ReactNode }) {
  return (
    <div className="mt-4 rounded-xl border border-gray-200 bg-white p-5">{children}</div>
  );
}

export function HomeownershipActionPlan({
  gapAnalysisId,
  userTier: _userTier,
  onBack,
  className = '',
}: HomeownershipActionPlanProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [plan, setPlan] = useState<ActionPlan | null>(null);
  const [cached, setCached] = useState(false);
  const [planGeneratedAt, setPlanGeneratedAt] = useState<string | null>(null);
  const [fetchKey, setFetchKey] = useState(0);

  const fetchPlan = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch('/api/housing/action-plan', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify({ gap_analysis_id: gapAnalysisId }),
      });

      if (!res.ok) throw new Error('action plan failed');

      const data = (await res.json()) as ActionPlanResponse;
      setPlan(data.plan);
      setCached(Boolean(data.cached));

      if (data.cached) {
        try {
          const metaRes = await fetch(`/api/housing/gap-analysis/${gapAnalysisId}`, {
            credentials: 'include',
            headers: buildAuthHeaders(),
          });
          if (metaRes.ok) {
            const meta = (await metaRes.json()) as GapAnalysisMeta;
            setPlanGeneratedAt(meta.plan_generated_at);
          }
        } catch {
          setPlanGeneratedAt(null);
        }
      } else {
        setPlanGeneratedAt(new Date().toISOString());
      }
    } catch {
      setPlan(null);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [gapAnalysisId]);

  useEffect(() => {
    void fetchPlan();
  }, [fetchPlan, fetchKey]);

  const goToSecondJobs = () => {
    navigate('/dashboard/tools?tab=debt');
  };

  if (loading) {
    return (
      <div className={`flex flex-col items-center justify-center py-16 text-center ${className}`}>
        <div
          className="h-8 w-8 animate-spin rounded-full border-2 border-[#7C3AED] border-t-transparent"
          aria-hidden
        />
        <p className="mt-4 text-base font-medium text-gray-800">
          Building your homeownership plan...
        </p>
        <p className="mt-2 text-sm text-gray-400">
          This usually takes 10–20 seconds on first load.
        </p>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className={`py-12 text-center ${className}`}>
        <p className="text-sm text-gray-700">Unable to generate your plan. Please try again.</p>
        <button
          type="button"
          onClick={() => setFetchKey((k) => k + 1)}
          className="mt-4 rounded-full border border-[#7C3AED] px-5 py-2 text-sm font-medium text-[#7C3AED] hover:bg-purple-50"
        >
          Try again
        </button>
      </div>
    );
  }

  const timeline = [...(plan.unified_timeline || [])].sort((a, b) => a.month - b.month);

  return (
    <div className={className}>
      <button
        type="button"
        onClick={onBack}
        className="text-sm text-gray-500 hover:text-gray-700"
      >
        ← Back to calculator
      </button>

      <h1 className="mt-2 text-xl font-bold text-gray-800">Your Homeownership Action Plan</h1>

      {cached ? (
        <p className="mt-1 text-xs text-gray-400">
          Plan from {formatPlanDate(planGeneratedAt)}
        </p>
      ) : null}

      <p className="mt-1 text-sm font-medium text-[#7C3AED]">{plan.scenario_label}</p>
      <p className="mt-2 max-w-prose text-sm text-gray-600">{plan.summary}</p>

      <PillarCard>
        <h2 className="font-semibold text-gray-800">💰 Pillar 1 — Savings Acceleration</h2>
        {plan.pillar_1.invoke === false ? (
          <span className="mt-3 inline-block rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-500">
            Not required for your timeline
          </span>
        ) : (
          <>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="rounded-full bg-purple-50 px-3 py-1 text-xs text-purple-700">
                Target: {formatCurrency(plan.pillar_1.monthly_target)}/mo
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
                Current: {formatCurrency(plan.pillar_1.current_monthly)}/mo
              </span>
            </div>
            {plan.pillar_1.gap <= 0 ? (
              <p className="mt-2 text-sm text-green-700">✓ On track</p>
            ) : (
              <p className="mt-2 text-sm text-gray-600">
                Gap: {formatCurrency(plan.pillar_1.gap)}/month to close
              </p>
            )}
            <NumberedActions actions={plan.pillar_1.actions || []} />
            <TimelineChip months={plan.pillar_1.timeline_months} />
          </>
        )}
      </PillarCard>

      <PillarCard>
        <h2 className="font-semibold text-gray-800">📈 Pillar 2 — Career Income Growth</h2>
        {plan.pillar_2.invoke === false ? (
          <span className="mt-3 inline-block rounded-full bg-green-50 px-3 py-1 text-xs text-green-700">
            Your income is sufficient for this purchase
          </span>
        ) : (
          <>
            <p className="mt-2 text-sm text-gray-600">
              Income gap: {formatCurrency(plan.pillar_2.income_gap || 0)}/month
            </p>
            <NumberedActions actions={plan.pillar_2.actions || []} />
            {plan.pillar_2.timeline_months != null ? (
              <TimelineChip months={plan.pillar_2.timeline_months} />
            ) : null}
          </>
        )}
      </PillarCard>

      <PillarCard>
        <h2 className="font-semibold text-gray-800">⚡ Pillar 3 — Second Income Stream</h2>
        {plan.pillar_3.invoke === false ? (
          <span className="mt-3 inline-block rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-500">
            Not required for your current timeline
          </span>
        ) : (
          <>
            <p className="mt-2 text-sm text-gray-600">
              Target: {formatCurrency(plan.pillar_3.monthly_target || 0)}/month from a second
              income source
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {(plan.pillar_3.job_types || []).map((job) => (
                <span
                  key={job}
                  className="rounded-full bg-amber-50 px-3 py-1 text-xs text-amber-700"
                >
                  {job}
                </span>
              ))}
            </div>
            <button
              type="button"
              onClick={goToSecondJobs}
              className="mt-2 text-sm text-[#7C3AED] underline hover:text-[#6D28D9]"
            >
              Find second jobs →
            </button>
            {plan.pillar_3.timeline_months != null ? (
              <TimelineChip months={plan.pillar_3.timeline_months} />
            ) : null}
          </>
        )}
      </PillarCard>

      <h2 className="mt-6 font-semibold text-gray-800">Your Path to Closing Day</h2>
      <div className="relative mt-4 border-l-2 border-purple-100 pl-6">
        {timeline.map((item) => (
          <div key={`${item.month}-${item.milestone}`} className="relative pb-6 last:pb-0">
            <span
              className="absolute -left-[1.65rem] top-1 h-3 w-3 rounded-full bg-[#7C3AED]"
              aria-hidden
            />
            <p className="text-xs text-gray-400">Month {item.month}</p>
            <p className="text-sm text-gray-700">{item.milestone}</p>
            <span className="mt-1 inline-block rounded-full bg-purple-50 px-2 py-0.5 text-xs text-purple-600">
              {item.pillar}
            </span>
          </div>
        ))}
      </div>

      <p className="mt-6 text-center text-xs text-gray-400">
        Plan refreshes every 30 days. Based on your current financial profile. Not financial
        advice.
      </p>
    </div>
  );
}

export default HomeownershipActionPlan;
