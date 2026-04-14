import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import type {
  ActionData,
  CardLoadState,
  CashNowData,
  FaithCardData,
  JobOption,
  RosterData,
  SnapshotData,
  SnapshotLoadStates,
} from '../types/snapshot';

// ─── CONSTANTS (define at the top of the file, outside the hook) ────

const TAX_MULTIPLIER: Record<string, number> = {
  budget: 0.76,
  mid_tier: 0.72,
  professional: 0.66,
};

const JOB_PROBABILITY: Record<string, number> = {
  budget: 0.4,
  mid_tier: 0.3,
  professional: 0.25,
};

const WELLNESS_SAVINGS: Record<string, number> = {
  budget: 1680,
  mid_tier: 5406,
  professional: 12784,
};

const SUBSCRIPTION_COST: Record<string, number> = {
  budget: 180,
  mid_tier: 420,
  professional: 1200,
};

function resolveSnapshotUserTier(user: ReturnType<typeof useAuth>['user']): string {
  if (user?.is_beta === true || user?.tier === 'professional') return 'professional';
  if (user?.tier === 'mid_tier') return 'mid_tier';
  return 'budget';
}

// ─── HOOK ────────────────────────────────────────────────────────────

export function useSnapshotData() {
  const { user, getAccessToken } = useAuth();
  const userId = user?.id;
  const userEmail = user?.email;
  const userTier = resolveSnapshotUserTier(user);

  // Initialize state
  const [data, setData] = useState<SnapshotData>({
    faith: null,
    vibe: null,
    cash: null,
    spending: null,
    roster: null,
    milestones: null,
    career: null,
    action: null,
  });

  const [loadStates, setLoadStates] = useState<SnapshotLoadStates>({
    faith: 'loading',
    vibe: 'loading',
    cash: 'loading',
    spending: 'loading',
    roster: 'loading',
    milestones: 'loading',
    career: 'loading',
    action: 'loading',
  });

  // Helper to set one card's state independently
  const setCard = (key: keyof SnapshotData, value: SnapshotData[keyof SnapshotData] | null, status: CardLoadState) => {
    setData((prev) => ({ ...prev, [key]: value }));
    setLoadStates((prev) => ({ ...prev, [key]: status }));
  };

  useEffect(() => {
    if (!userId || !userEmail) return;

    const token = getAccessToken();
    const headers: Record<string, string> = {
      ...csrfHeaders(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    Promise.allSettled([
      // ── 1. Faith Card ────────────────────────────────────────
      fetch('/api/faith-card/today', {
        credentials: 'include',
        headers,
      })
        .then((r) => r.json())
        .then((d) => {
          setCard('faith', d as FaithCardData, 'ready');
        })
        .catch(() => setCard('faith', null, 'error')),

      // ── 2. Vibe Check ────────────────────────────────────────
      fetch(`/api/vibe-tracker/correlation-summary?user_id=${userId}`, {
        credentials: 'include',
        headers,
      })
        .then((r) => r.json())
        .then((d) => {
          setCard('vibe', d.has_sufficient_data ? d : null, 'ready');
        })
        .catch(() => setCard('vibe', null, 'error')),

      // ── 3. Cash Now ──────────────────────────────────────────
      fetch(`/api/cash-flow/enhanced-forecast/${userEmail}`, {
        credentials: 'include',
        headers,
      })
        .then((r) => {
          if (!r.ok) throw new Error();
          return r.json();
        })
        .catch(() =>
          fetch(`/api/cash-flow/backward-compatibility/${userEmail}`, {
            credentials: 'include',
            headers,
          }).then((r) => r.json()),
        )
        .then((d) => {
          const thirtyDays = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
          const todayEntry = d.daily_cashflow?.[0];
          const flow = d.daily_cashflow;
          const entry30 =
            flow?.find((e: { date: string }) => e.date >= thirtyDays) ??
            (flow?.length ? flow[flow.length - 1] : undefined);
          const cashData: CashNowData = {
            todays_balance: todayEntry?.opening_balance ?? 0,
            balance_30_day: entry30?.closing_balance ?? 0,
            net_change_30: (entry30?.closing_balance ?? 0) - (todayEntry?.opening_balance ?? 0),
            balance_status: todayEntry?.balance_status ?? 'healthy',
            worst_status_30:
              d.daily_cashflow?.slice(0, 30).reduce((worst: string, e: { balance_status: string }) => {
                const order = ['healthy', 'warning', 'danger'];
                return order.indexOf(e.balance_status) > order.indexOf(worst) ? e.balance_status : worst;
              }, 'healthy') ?? 'healthy',
          };
          // Write balance status for bug report context
          localStorage.setItem('mingus_last_balance_status', cashData.balance_status);
          setCard('cash', cashData, 'ready');
        })
        .catch(() => setCard('cash', null, 'error')),

      // ── 4. Spending ──────────────────────────────────────────
      fetch(`/api/expenses/summary/${userEmail}`, {
        credentials: 'include',
        headers,
      })
        .then((r) => r.json())
        .then((d) => {
          const cats = (d.categories ?? [])
            .map((c: { name: string; amount: number }) => ({
              name: c.name,
              amount: c.amount,
              pct_of_income: d.income_monthly > 0 ? c.amount / d.income_monthly : 0,
            }))
            .sort((a: { amount: number }, b: { amount: number }) => b.amount - a.amount)
            .slice(0, 3);
          setCard(
            'spending',
            { income_monthly: d.income_monthly, top_categories: cats },
            'ready',
          );
        })
        .catch(() => setCard('spending', null, 'error')),

      // ── 5. Roster ────────────────────────────────────────────
      fetch('/api/vibe-tracker/people', {
        credentials: 'include',
        headers,
      })
        .then((r) => r.json())
        .then((d) => {
          const people = d.people ?? d ?? [];
          const totalAnnual = people.reduce((s: number, p: { estimated_annual_cost?: number }) => s + (p.estimated_annual_cost ?? 0), 0);
          const delta = people.reduce((s: number, p: { cost_delta_annual?: number }) => s + (p.cost_delta_annual ?? 0), 0);
          const rosterData: RosterData = {
            total_annual_cost: totalAnnual,
            total_monthly_cost: Math.round(totalAnnual / 12),
            relationship_cost_delta: delta,
            people: people.slice(0, 4).map(
              (p: {
                nickname: string;
                emoji?: string;
                estimated_annual_cost?: number;
                trend?: 'rising' | 'falling' | 'stable';
              }) => ({
                nickname: p.nickname,
                emoji: p.emoji ?? '👤',
                estimated_annual_cost: p.estimated_annual_cost ?? 0,
                trend: p.trend ?? 'stable',
              }),
            ),
            has_financial_drag: delta > 2000 && people.length > 0,
          };
          setCard('roster', rosterData, 'ready');
        })
        .catch(() => setCard('roster', null, 'error')),

      // ── 6. Milestones ────────────────────────────────────────
      Promise.all([
        fetch(`/api/special-dates/${userId}`, {
          credentials: 'include',
          headers,
        }).then((r) => r.json()),
        fetch(`/api/cash-flow/backward-compatibility/${userEmail}`, {
          credentials: 'include',
          headers,
        }).then((r) => r.json()),
      ])
        .then(([dates, cashflow]) => {
          const today = new Date();
          const getForecastImpact = (dateStr: string, cost: number) => {
            if (!cashflow?.daily_cashflow?.length || cost === 0) return null;
            const day = cashflow.daily_cashflow.find((cf: { date: string }) => cf.date === dateStr);
            if (!day) return null;
            const after = day.closing_balance - cost;
            if (after > 500) return 'covered';
            if (after >= 0) return 'tight';
            return 'shortfall';
          };
          const events = (dates.events ?? dates ?? [])
            .filter((e: { cost: number; date: string }) => e.cost > 0 && new Date(e.date) > today)
            .sort((a: { date: string }, b: { date: string }) => new Date(a.date).getTime() - new Date(b.date).getTime())
            .slice(0, 3)
            .map((e: { name?: string; title?: string; date: string; cost: number }) => ({
              title: e.name ?? e.title,
              date: e.date,
              cost: e.cost,
              days_away: Math.ceil((new Date(e.date).getTime() - today.getTime()) / 86400000),
              impact: getForecastImpact(e.date, e.cost),
            }));
          setCard('milestones', { upcoming: events, current_streak: dates.current_streak ?? 0 }, 'ready');
        })
        .catch(() => setCard('milestones', null, 'error')),

      // ── 7. Career ────────────────────────────────────────────
      fetch(`/api/career/recommendations/${userId}`, {
        credentials: 'include',
        headers,
      })
        .then((r) => r.json())
        .then((d) => {
          const currentSalary = d.current_salary ?? 0;
          const taxMult = TAX_MULTIPLIER[userTier] ?? 0.72;
          const jobProb = JOB_PROBABILITY[userTier] ?? 0.3;
          const wellness = WELLNESS_SAVINGS[userTier] ?? 5406;
          const subCost = SUBSCRIPTION_COST[userTier] ?? 420;

          const jobs: JobOption[] = (d.recommendations ?? [])
            .map(
              (rec: {
                id?: string;
                title: string;
                company_type?: string;
                company?: string;
                location: string;
                salary_min: number;
                salary_max: number;
                match_score?: number;
              }) => {
                const midSalary = (rec.salary_min + rec.salary_max) / 2;
                const grossUplift = midSalary - currentSalary;
                const afterTaxUplift = grossUplift * taxMult;
                const expectedCareer = afterTaxUplift * jobProb;
                const totalExpectedReturn = Math.round(expectedCareer + wellness);
                return {
                  id: rec.id ?? String(Math.random()),
                  title: rec.title,
                  company_type: rec.company_type ?? rec.company ?? '',
                  location: rec.location,
                  salary_low: rec.salary_min,
                  salary_high: rec.salary_max,
                  match_score: rec.match_score ?? 0,
                  income_lift_pct:
                    currentSalary > 0 ? ((midSalary - currentSalary) / currentSalary) * 100 : 0,
                  // Uses tier-specific tax rate (not flat 27%)
                  monthly_takehome_delta: Math.round((grossUplift * taxMult) / 12),
                  // ROI fields
                  total_expected_return: totalExpectedReturn,
                  roi_multiple: subCost > 0 ? Math.round(totalExpectedReturn / subCost) : 0,
                  payback_days: totalExpectedReturn > 0 ? Math.round((subCost / totalExpectedReturn) * 365) : 365,
                  capital_equivalent: Math.round(totalExpectedReturn / 0.104),
                  job_probability: jobProb,
                };
              },
            )
            .sort((a: JobOption, b: JobOption) => b.income_lift_pct - a.income_lift_pct)
            .slice(0, 3);

          setCard('career', { current_salary: currentSalary, jobs }, 'ready');
        })
        .catch(() => setCard('career', null, 'error')),
    ]).then(() => {
      // ── 8. Action (derived client-side after all fetches) ────
      setData((prev) => {
        const d = prev;
        let source = 'vibe';
        let text = 'Check in with your Vibe Checkup today.';
        const ctas: ActionData['ctas'] = [];

        if (d.milestones?.upcoming.some((e) => e.impact === 'shortfall')) {
          source = 'milestones';
          text = 'You have an upcoming expense your forecast may not cover.';
          ctas.push({ label: 'Review your forecast', tab: 'financial-forecast', urgency: 'high' });
        } else if (d.roster?.has_financial_drag) {
          source = 'roster';
          text = 'Your roster costs have increased while your savings rate dropped.';
          ctas.push({ label: 'Review your forecast', tab: 'financial-forecast', urgency: 'high' });
        } else if (d.career?.jobs?.[0]?.income_lift_pct && d.career.jobs[0].income_lift_pct >= 15) {
          source = 'career';
          text = 'A career move could meaningfully change your financial picture.';
          ctas.push({ label: 'See job matches', tab: 'job-recommendations', urgency: 'high' });
        } else if (d.cash?.balance_status === 'danger' || d.cash?.balance_status === 'warning') {
          source = 'cash';
          text = 'Your balance needs attention this month.';
          ctas.push({ label: 'Review your forecast', tab: 'financial-forecast', urgency: 'high' });
        }

        // Always add 1-2 secondary CTAs
        if (source !== 'career')
          ctas.push({
            label: 'Check job matches',
            tab: 'job-recommendations',
            urgency: 'medium',
          });
        ctas.push({ label: "Log today's check-in", tab: 'daily-outlook', urgency: 'low' });

        const actionData: ActionData = {
          action_text: text,
          action_source: source,
          ctas,
        };
        return { ...prev, action: actionData };
      });
      setLoadStates((prev) => ({ ...prev, action: 'ready' }));
    });
  }, [userId, userEmail, userTier]);

  // ── saveFavorite ─────────────────────────────────────────────
  // Called by Faith Card when user taps the heart button.
  // Posts to the faith-card favorite endpoint.
  // Returns true on success, false on failure — never throws.
  const saveFavorite = useCallback(
    async (verse: FaithCardData): Promise<boolean> => {
      try {
        const token = getAccessToken();
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        };
        const res = await fetch('/api/faith-card/favorite', {
          method: 'POST',
          credentials: 'include',
          headers,
          body: JSON.stringify({
            verse_reference: verse.verse_reference,
            verse_text: verse.verse_text,
            bridge_sentence: verse.bridge_sentence,
          }),
        });
        return res.ok;
      } catch {
        return false;
      }
    },
    [getAccessToken],
  );

  return { data, loadStates, saveFavorite };
}
