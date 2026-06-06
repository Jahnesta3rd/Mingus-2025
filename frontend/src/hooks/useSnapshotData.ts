import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import type {
  ActionData,
  CardLoadState,
  CashNowData,
  FaithCardData,
  HousingActionData,
  MilestonesData,
  RosterData,
  SnapshotData,
  SnapshotLoadStates,
  SpendingData,
  VibeCheckData,
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

function normalizeMonthly(amount: number, frequency: string): number {
  switch ((frequency || 'monthly').toLowerCase()) {
    case 'weekly':
      return (amount * 52) / 12;
    case 'biweekly':
      return (amount * 26) / 12;
    case 'semimonthly':
      return amount * 2;
    case 'annual':
      return amount / 12;
    case 'monthly':
    default:
      return amount;
  }
}

function resolveSnapshotUserTier(user: ReturnType<typeof useAuth>['user']): string {
  if (user?.is_beta === true || user?.tier === 'professional') return 'professional';
  if (user?.tier === 'mid_tier') return 'mid_tier';
  return 'budget';
}

// ─── HOOK ────────────────────────────────────────────────────────────

export function useSnapshotData(opts?: { reloadKey?: number }) {
  const reloadKey = opts?.reloadKey ?? 0;
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
    housing: null,
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
    housing: 'loading',
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
        .then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        })
        .then((d) => {
          setCard('faith', d as FaithCardData, 'ready');
        })
        .catch(() => setCard('faith', null, 'error')),

      // ── 2. Vibe Check ────────────────────────────────────────
      fetch('/api/life-ready-score', {
        credentials: 'include',
        headers,
      })
        .then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        })
        .then((d) => {
          if (!d.has_sufficient_data) {
            setCard('vibe', null, 'ready');
            return;
          }
          const vibeScore = d.components?.vibe?.score ?? 0;
          const wellnessScore = d.components?.wellness?.score ?? 0;
          const financialScore = d.components?.financial?.score ?? 0;
          const overallScore =
            d.life_ready_score ??
            Math.round((vibeScore + wellnessScore + financialScore) / 3);
          const verdict =
            overallScore >= 75
              ? 'On track'
              : overallScore >= 50
                ? 'Watch closely'
                : overallScore >= 25
                  ? 'Needs attention'
                  : 'Critical';
          setCard(
            'vibe',
            {
              score: overallScore,
              verdict,
              wellness_score: wellnessScore,
              financial_score: financialScore,
              emotional_score: vibeScore,
              headline_insight: d.headline ?? null,
            } as VibeCheckData,
            'ready',
          );
        })
        .catch(() => setCard('vibe', null, 'error')),

      // ── 3. Cash Now ──────────────────────────────────────────
      fetch(`/api/cash-flow/enhanced-forecast/${userEmail}`, {
        credentials: 'include',
        headers,
      })
        .then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        })
        .catch(() =>
          fetch(`/api/cash-flow/backward-compatibility/${userEmail}`, {
            credentials: 'include',
            headers,
          }).then((r) => {
            if (!r.ok) throw new Error(`${r.status}`);
            return r.json();
          }),
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
      Promise.all([
        fetch('/api/financial-setup/income', {
          credentials: 'include',
          headers,
        }).then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        }),
        fetch('/api/financial-setup/expenses', {
          credentials: 'include',
          headers,
        }).then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        }),
      ])
        .then(([incomeData, expensesData]) => {
          const incomeRows = incomeData.income ?? [];
          const income_monthly = incomeRows.reduce(
            (sum: number, row: { amount?: number; frequency?: string; is_active?: boolean }) => {
              if (row.is_active === false) return sum;
              const amount = Number(row.amount) || 0;
              return sum + normalizeMonthly(amount, row.frequency ?? 'monthly');
            },
            0,
          );

          const byCategory = new Map<string, number>();
          for (const row of expensesData.expenses ?? []) {
            if (row.is_active === false) continue;
            const amount = Number(row.amount) || 0;
            const monthly = normalizeMonthly(amount, row.frequency ?? 'monthly');
            const cat = (row.category as string) || 'other';
            byCategory.set(cat, (byCategory.get(cat) ?? 0) + monthly);
          }

          const top_categories = [...byCategory.entries()]
            .map(([name, amount]) => ({
              name,
              amount,
              pct_of_income: income_monthly > 0 ? amount / income_monthly : 0,
            }))
            .sort((a, b) => b.amount - a.amount)
            .slice(0, 3);

          setCard('spending', { income_monthly, top_categories } as SpendingData, 'ready');
        })
        .catch(() => setCard('spending', null, 'error')),

      // ── 5. Roster ────────────────────────────────────────────
      fetch('/api/vibe-tracker/people', {
        credentials: 'include',
        headers,
      })
        .then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        })
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
        fetch('/api/user/profile', {
          credentials: 'include',
          headers,
        }).then((r) => {
          if (!r.ok) throw new Error(`${r.status}`);
          return r.json();
        }),
        fetch(`/api/gamification/milestones?userId=${encodeURIComponent(String(userId))}`, {
          credentials: 'include',
          headers,
        })
          .then((r) => {
            if (!r.ok) return { current_streak: 0 };
            return r.json();
          })
          .catch(() => ({ current_streak: 0 })),
      ])
        .then(([profile, milestonesData]) => {
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          const important =
            profile?.profile?.important_dates ?? profile?.important_dates ?? {};
          const customs = important.customEvents ?? important.custom_events ?? [];
          const events = customs
            .filter((e: { cost?: number; date?: string }) => (e.cost ?? 0) > 0 && e.date && new Date(e.date) > today)
            .sort((a: { date: string }, b: { date: string }) => new Date(a.date).getTime() - new Date(b.date).getTime())
            .slice(0, 3)
            .map((e: { name?: string; title?: string; date: string; cost: number }) => ({
              title: e.name ?? e.title ?? 'Event',
              date: e.date,
              cost: e.cost,
              days_away: Math.ceil((new Date(e.date).getTime() - today.getTime()) / 86400000),
              impact: null,
            }));
          const current_streak =
            milestonesData?.current_streak ?? milestonesData?.data?.current_streak ?? 0;
          setCard('milestones', { upcoming: events, current_streak } as MilestonesData, 'ready');
        })
        .catch(() => setCard('milestones', null, 'error')),

      // ── 7. Career ────────────────────────────────────────────
      Promise.resolve().then(() => {
        // Career card: no backend endpoint exists for this shape yet (see #155).
        // Render the empty/CTA state until three-tier or resume pipeline exposes a GET.
        setCard('career', null, 'ready');
      }),

      // ── 8. Housing ───────────────────────────────────────────
      fetch('/api/housing/profile', {
        credentials: 'include',
        headers,
      })
        .then((r) => {
          if (!r.ok) throw new Error('housing fetch failed');
          return r.json();
        })
        .then((d) => {
          const target_price = d.target_price ?? null;
          const saved = d.down_payment_saved ?? 0;
          const target = target_price ? target_price * 0.2 : 0;
          const gap = Math.max(0, target - saved);
          const timeline = d.target_timeline_months ?? null;
          const housing: HousingActionData = {
            has_buy_goal: d.has_buy_goal ?? false,
            target_price,
            target_timeline_months: timeline,
            down_payment_saved: saved,
            down_payment_target: target,
            down_payment_gap: gap,
            monthly_needed:
              gap > 0 && timeline && timeline > 0 ? Math.round(gap / timeline) : null,
          };
          setCard('housing', housing, 'ready');
        })
        .catch(() => setCard('housing', null, 'ready')),
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
        } else if (
          d.housing?.has_buy_goal === true &&
          (d.housing?.down_payment_gap ?? 0) > 0 &&
          d.housing?.monthly_needed !== null
        ) {
          source = 'housing';
          text = `You need $${d.housing.monthly_needed.toLocaleString()}/mo to reach your down payment goal${
            d.housing.target_timeline_months
              ? ` in ${d.housing.target_timeline_months} months`
              : ''
          }.`;
          ctas.push({
            label: 'See your down payment plan',
            tab: 'housing',
            urgency: 'high',
          });
        } else if (d.roster?.has_financial_drag) {
          source = 'roster';
          text = 'Your roster costs have increased while your savings rate dropped.';
          ctas.push({ label: 'Review your forecast', tab: 'financial-forecast', urgency: 'high' });
        } else if (d.career && d.career.jobs?.length > 0 && d.career.jobs[0].income_lift_pct >= 15) {
          source = 'career';
          text = 'A career move could meaningfully change your financial picture.';
          ctas.push({ label: 'See job matches', tab: 'job-recommendations', urgency: 'high' });
        } else if (d.cash?.balance_status === 'danger' || d.cash?.balance_status === 'warning') {
          source = 'cash';
          text = 'Your balance needs attention this month.';
          ctas.push({ label: 'Review your forecast', tab: 'financial-forecast', urgency: 'high' });
        }

        // Always add 1-2 secondary CTAs
        if (source !== 'career' && source !== 'housing')
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
  }, [userId, userEmail, userTier, reloadKey]);

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
