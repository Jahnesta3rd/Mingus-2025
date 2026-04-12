import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

import { useMCI } from '../context/MCIContext';
import type { MCIDirection, MCIConstituent, MCISeverity } from '../types/mci';

import BalanceEntryWidget from './BalanceEntryWidget';
import PeopleCostSummary from './roster/PeopleCostSummary';

// ========================================
// TYPES
// ========================================

interface DailyCashflowEntry {
  date: string;
  opening_balance: number;
  closing_balance: number;
  net_change: number;
  balance_status: 'healthy' | 'warning' | 'danger';
}

interface RelationshipCostBreakdownRow {
  nickname: string;
  monthly_cost: number;
  card_type: string;
  emoji?: string | null;
  pct_of_total_expenses?: number;
}

interface ForecastResponse {
  success: boolean;
  forecast?: {
    daily_cashflow?: DailyCashflowEntry[];
    monthly_summaries?: { month_key: string; total: number }[];
    vehicle_expense_totals?: { total: number; routine: number; repair: number };
    relationship_cost_breakdown?: RelationshipCostBreakdownRow[];
    [key: string]: unknown;
  };
}

/** One row for the monthly breakdown table (derived from daily_cashflow or API). */
interface MonthlyTableRow {
  month: string;
  month_label: string;
  opening_balance: number;
  total_income: number;
  total_expenses: number;
  closing_balance: number;
  worst_status: 'healthy' | 'warning' | 'danger';
}

/** Vehicle expense details API: GET /api/cash-flow/vehicle-expenses/{userEmail}/{monthKey} */
interface VehicleExpenseDetails {
  month: string;
  total_vehicle_cost: number;
  vehicles: Array<{
    vehicle_id: number;
    vehicle_name: string;
    total_cost: number;
    routine_cost: number;
    repair_cost: number;
    services?: unknown[];
  }>;
}

export interface FinancialForecastTabProps {
  userEmail: string;
  userTier: 'budget' | 'mid' | 'professional';
  className?: string;
}

// ========================================
// HELPERS
// ========================================

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function getStatusLabel(status: 'healthy' | 'warning' | 'danger'): string {
  switch (status) {
    case 'healthy':
      return 'ON TRACK';
    case 'warning':
      return 'WATCH THIS';
    case 'danger':
      return 'NEEDS ATTENTION';
    default:
      return 'ON TRACK';
  }
}

function getStatusClasses(status: 'healthy' | 'warning' | 'danger'): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-600 text-white';
    case 'warning':
      return 'bg-amber-400 text-amber-900';
    case 'danger':
      return 'bg-red-600 text-white';
    default:
      return 'bg-gray-500 text-white';
  }
}

function formatUsdShort(value: number): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
  if (value <= -1000) return `-$${(Math.abs(value) / 1000).toFixed(1)}k`;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

function formatChartDate(isoDate: string): string {
  const d = new Date(isoDate + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/** Build monthly table rows from daily_cashflow (group by month). */
function buildMonthlyTableRows(daily: DailyCashflowEntry[]): MonthlyTableRow[] {
  const byMonth = new Map<
    string,
    { opening_balance: number; closing_balance: number; income: number; expenses: number; statuses: ('healthy' | 'warning' | 'danger')[] }
  >();
  for (const e of daily) {
    const monthKey = e.date.slice(0, 7);
    const r = byMonth.get(monthKey);
    if (!r) {
      byMonth.set(monthKey, {
        opening_balance: e.opening_balance,
        closing_balance: e.closing_balance,
        income: e.net_change > 0 ? e.net_change : 0,
        expenses: e.net_change < 0 ? Math.abs(e.net_change) : 0,
        statuses: [e.balance_status],
      });
    } else {
      r.closing_balance = e.closing_balance;
      r.statuses.push(e.balance_status);
      if (e.net_change > 0) r.income += e.net_change;
      else if (e.net_change < 0) r.expenses += Math.abs(e.net_change);
    }
  }
  const order = { danger: 3, warning: 2, healthy: 1 };
  return Array.from(byMonth.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, r]) => {
      const worst = r.statuses.reduce((a, s) => (order[s] > order[a] ? s : a), 'healthy' as const);
      return {
        month,
        month_label: new Date(month + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        opening_balance: r.opening_balance,
        total_income: r.income,
        total_expenses: r.expenses,
        closing_balance: r.closing_balance,
        worst_status: worst,
      };
    });
}

function formatMciMonthDay(isoDate: string): string {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getMCIDotClasses(severity: MCISeverity): string {
  switch (severity) {
    case 'green':
      return 'bg-green-500';
    case 'amber':
      return 'bg-amber-500';
    case 'red':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
}

function getMCIDirectionClasses(direction: MCIDirection): string {
  switch (direction) {
    case 'up':
      return 'text-green-600';
    case 'down':
      return 'text-red-600';
    case 'flat':
      return 'text-gray-500';
    default:
      return 'text-gray-500';
  }
}

function getDirectionArrow(direction: MCIDirection): string {
  switch (direction) {
    case 'up':
      return '↑';
    case 'down':
      return '↓';
    case 'flat':
      return '→';
    default:
      return '→';
  }
}

function formatCardTypeLabel(cardType: string): string {
  const t = (cardType || '').trim().toLowerCase();
  if (t === 'kids') return 'Kids';
  if (t === 'person') return 'Person';
  if (!t) return 'Person';
  return t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function relationshipRowEmoji(row: RelationshipCostBreakdownRow): string {
  const e = row.emoji?.trim();
  if (e) return e;
  if (row.card_type === 'kids') return '👶';
  return '·';
}

interface MCIForecastPanelProps {
  userTier: 'budget' | 'mid' | 'professional';
}

function MCIForecastPanel({ userTier }: MCIForecastPanelProps) {
  const { snapshot, loading, error } = useMCI();

  const renderSkeleton = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4" role="status" aria-label="Loading market conditions">
      {[1, 2].map((i) => (
        <div key={i} className="rounded-xl border border-gray-100 p-4 bg-white shadow-sm animate-pulse">
          <div className="h-4 w-40 bg-gray-200 rounded mb-3" />
          <div className="h-3 w-24 bg-gray-200 rounded mb-2" />
          <div className="h-3 w-32 bg-gray-200 rounded mb-2" />
          <div className="h-3 w-28 bg-gray-200 rounded" />
        </div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="mb-6">
        {renderSkeleton()}
      </div>
    );
  }

  if (error || !snapshot) {
    return null;
  }

  const findConstituent = (slug: string): MCIConstituent | undefined =>
    snapshot.constituents.find((c) => c.slug === slug);

  const labor = findConstituent('labor_market_strength');
  const housing = findConstituent('housing_affordability_pressure');

  if (userTier === 'budget') {
    return (
      <div className="mb-6">
        <div className="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <div className="mt-1 w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center">
              {/* Simple inline lock icon */}
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
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
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-700">
                Upgrade to Mid-tier to see how market conditions affect your forecast
              </p>
              <a
                href="/#pricing"
                className="mt-3 inline-block rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
              >
                View Plans
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const renderInterpretation = (c: MCIConstituent, interpretKind: 'labor' | 'housing') => {
    if (interpretKind === 'labor') {
      if (c.severity === 'green') return 'Job market is strong — your income projection is stable.';
      if (c.severity === 'amber') return 'Job market is cooling — consider a conservative forecast.';
      return 'Layoff risk is elevated — review your emergency fund target.';
    }
    // housing
    if (c.severity === 'green') return 'Mortgage rates are favorable for your home buying timeline.';
    if (c.severity === 'amber') return 'Rates are elevated — re-run your affordability calculator.';
    return 'Rates are high — your rent vs. buy decision may have shifted.';
  };

  const renderConstituentCard = (c: MCIConstituent | undefined, kind: 'labor' | 'housing') => {
    if (!c) {
      return (
        <div className="border border-gray-100 rounded-xl p-4 bg-white shadow-sm">
          <p className="text-sm font-medium text-gray-700">{kind === 'labor' ? 'Labor unavailable' : 'Housing unavailable'}</p>
        </div>
      );
    }

    return (
      <div className="border border-gray-100 rounded-xl p-4 bg-white shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${getMCIDotClasses(c.severity)}`} aria-hidden />
            <div className="text-sm font-medium text-gray-800">{c.name}</div>
          </div>
          <div className={`text-sm font-medium ${getMCIDirectionClasses(c.direction)}`} aria-hidden>
            {getDirectionArrow(c.direction)}
          </div>
        </div>
        <div className="mt-2 text-sm font-medium text-gray-700">{c.headline}</div>
        <div className="mt-2 text-xs text-gray-600">{renderInterpretation(c, kind)}</div>
      </div>
    );
  };

  return (
    <div className="mb-6">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-700">Market conditions affecting your forecast</h3>
        <p className="text-xs text-gray-400">Updated {formatMciMonthDay(snapshot.snapshot_date)}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {renderConstituentCard(labor, 'labor')}
        {renderConstituentCard(housing, 'housing')}
      </div>
    </div>
  );
}

// ========================================
// COMPONENT
// ========================================

export default function FinancialForecastTab({
  userEmail,
  userTier,
  className = '',
}: FinancialForecastTabProps) {
  const [dailyCashflow, setDailyCashflow] = useState<DailyCashflowEntry[]>([]);
  const [monthlySummaries, setMonthlySummaries] = useState<{ month_key: string; total: number }[]>([]);
  const [vehicleExpenseTotals, setVehicleExpenseTotals] = useState<{
    total: number;
    routine: number;
    repair: number;
  } | null>(null);
  const [relationshipCostBreakdown, setRelationshipCostBreakdown] = useState<
    RelationshipCostBreakdownRow[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableExpanded, setTableExpanded] = useState(false);
  const [relationshipBreakdownExpanded, setRelationshipBreakdownExpanded] = useState(false);
  const [selectedMonthKey, setSelectedMonthKey] = useState(() =>
    new Date().toISOString().slice(0, 7)
  );
  const [vehicleDetails, setVehicleDetails] = useState<VehicleExpenseDetails | null>(null);
  const [vehicleDetailsLoading, setVehicleDetailsLoading] = useState(false);
  const [currentBalance, setCurrentBalance] = useState<number>(5000);
  const [balanceLastUpdated, setBalanceLastUpdated] = useState<string | null>(null);
  const [profileLoading, setProfileLoading] = useState<boolean>(true);

  const fetchForecast = useCallback(async () => {
    if (!userEmail) return;
    setLoading(true);
    setError(null);
    try {
      const primaryUrl = `/api/cash-flow/enhanced-forecast/${encodeURIComponent(userEmail)}?months=3`;
      const fallbackUrl = `/api/cash-flow/backward-compatibility/${encodeURIComponent(userEmail)}?months=3`;
      const token = localStorage.getItem('mingus_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token || 'test-token',
      };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      let res = await fetch(primaryUrl, { credentials: 'include', headers });
      if (!res.ok) {
        res = await fetch(fallbackUrl, { credentials: 'include', headers });
      }
      if (!res.ok) {
        throw new Error('Failed to load forecast');
      }
      const data: ForecastResponse = await res.json();
      const forecast = data.forecast;
      if (!forecast) throw new Error('No forecast data');

      setDailyCashflow(forecast.daily_cashflow ?? []);
      setMonthlySummaries(forecast.monthly_summaries ?? []);
      setVehicleExpenseTotals(forecast.vehicle_expense_totals ?? null);
      const relRaw = forecast.relationship_cost_breakdown;
      setRelationshipCostBreakdown(Array.isArray(relRaw) ? relRaw : []);
    } catch {
      setError('Unable to load your forecast. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [userEmail]);

  useEffect(() => {
    if (!userEmail) {
      setProfileLoading(false);
      return;
    }
    let cancelled = false;
    setProfileLoading(true);
    (async () => {
      try {
        const token = localStorage.getItem('mingus_token');
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
          'X-CSRF-Token': token || 'test-token',
        };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch('/api/user/profile', { credentials: 'include', headers });
        if (!res.ok) throw new Error('profile fetch failed');
        const data = (await res.json()) as {
          profile?: { current_balance?: unknown; balance_last_updated?: unknown };
          current_balance?: unknown;
          balance_last_updated?: unknown;
        };
        const prof = data.profile ?? data;
        const rawBal = prof.current_balance;
        const tsRaw = prof.balance_last_updated;

        if (cancelled) return;

        if (typeof rawBal === 'number' && Number.isFinite(rawBal)) {
          setCurrentBalance(rawBal);
        } else {
          setCurrentBalance(5000);
        }
        setBalanceLastUpdated(typeof tsRaw === 'string' && tsRaw ? tsRaw : null);
      } catch {
        if (!cancelled) {
          setCurrentBalance(5000);
          setBalanceLastUpdated(null);
        }
      } finally {
        if (!cancelled) setProfileLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userEmail]);

  useEffect(() => {
    fetchForecast();
  }, [fetchForecast]);

  const handleBalanceSaved = useCallback(
    (newBalance: number) => {
      setCurrentBalance(newBalance);
      setBalanceLastUpdated(new Date().toISOString());
      void fetchForecast();
    },
    [fetchForecast]
  );

  useEffect(() => {
    if (userTier !== 'professional' || !userEmail) return;
    setVehicleDetailsLoading(true);
    const token = localStorage.getItem('mingus_token');
    fetch(
      `/api/cash-flow/vehicle-expenses/${encodeURIComponent(userEmail)}/${encodeURIComponent(selectedMonthKey)}`,
      {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    )
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('Failed'))))
      .then((data: { details?: VehicleExpenseDetails }) => {
        setVehicleDetails(data?.details ?? null);
      })
      .catch(() => setVehicleDetails(null))
      .finally(() => setVehicleDetailsLoading(false));
  }, [userTier, userEmail, selectedMonthKey]);

  const todayEntry = dailyCashflow[0] ?? null;
  const todayStr = new Date().toISOString().slice(0, 10);
  const in30Days = new Date();
  in30Days.setDate(in30Days.getDate() + 30);
  const date30Str = in30Days.toISOString().slice(0, 10);
  const entry30 = dailyCashflow.find((e) => e.date === date30Str) ?? dailyCashflow[29] ?? null;
  const netChange30 = entry30 && todayEntry ? entry30.closing_balance - todayEntry.opening_balance : 0;

  const worstIn30 = dailyCashflow
    .slice(0, Math.min(31, dailyCashflow.length))
    .reduce<{ status: 'healthy' | 'warning' | 'danger'; date: string } | null>((worst, e) => {
      const order = { danger: 3, warning: 2, healthy: 1 };
      if (!worst || order[e.balance_status] > order[worst.status]) {
        return { status: e.balance_status, date: e.date };
      }
      return worst;
    }, null);
  const tightPeriod = (() => {
    if (!worstIn30 || !todayEntry || worstIn30.status === todayEntry.balance_status) return null;
    const start = new Date(worstIn30.date);
    const end = new Date(start);
    end.setDate(end.getDate() + 7);
    const mon = (d: Date) => d.toLocaleDateString('en-US', { month: 'short' });
    const day = (d: Date) => d.getDate();
    return `${mon(start)} ${day(start)}–${day(end)}`;
  })();

  // 90-day chart data (next 90 days from daily_cashflow)
  const chartData90 = dailyCashflow
    .slice(0, 90)
    .map((e) => ({ date: e.date, balance: e.closing_balance, status: e.balance_status }));
  const minBalance90 = chartData90.length > 0 ? Math.min(...chartData90.map((d) => d.balance)) : 0;
  const worstStatus90 =
    chartData90.length === 0
      ? 'healthy'
      : chartData90.some((d) => d.status === 'danger')
        ? 'danger'
        : chartData90.some((d) => d.status === 'warning')
          ? 'warning'
          : 'healthy';
  const areaGradientId = 'balance-area-gradient';
  const areaColor =
    minBalance90 >= 1000
      ? { from: '#16A34A', fromOpacity: 0.4 }
      : minBalance90 >= 0
        ? { from: '#D97706', fromOpacity: 0.3 }
        : { from: '#DC2626', fromOpacity: 0.3 };
  const strokeColor =
    worstStatus90 === 'danger' ? '#DC2626' : worstStatus90 === 'warning' ? '#D97706' : '#16A34A';

  const monthlyTableRows = buildMonthlyTableRows(dailyCashflow);
  const currentMonthKey = new Date().toISOString().slice(0, 7);

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-xl bg-white p-6 shadow-sm animate-pulse"
              role="status"
              aria-label="Loading"
            >
              <div className="mb-2 h-4 w-24 rounded bg-gray-200" />
              <div className="h-8 w-32 rounded bg-gray-200" />
              <div className="mt-2 h-4 w-28 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`rounded-xl bg-white p-6 shadow-sm ${className}`}>
        <p className="text-gray-700">{error}</p>
        <button
          type="button"
          onClick={fetchForecast}
          className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <BalanceEntryWidget
        userEmail={userEmail}
        initialBalance={currentBalance}
        lastUpdated={balanceLastUpdated}
        onBalanceSaved={handleBalanceSaved}
        isLoading={profileLoading}
        className="mb-6"
      />
      <MCIForecastPanel userTier={userTier} />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Card 1 — Today's Balance */}
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Today&apos;s Balance</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 tabular-nums">
            {todayEntry != null ? formatUsd(todayEntry.opening_balance) : formatUsd(0)}
          </p>
          <p className="mt-1 text-sm text-gray-400" aria-hidden>
            💳
          </p>
        </div>

        {/* Card 2 — 30-Day Forecast */}
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-500">30-Day Forecast</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 tabular-nums">
            {entry30 != null ? formatUsd(entry30.closing_balance) : formatUsd(0)}
          </p>
          <p
            className={`mt-1 text-sm font-medium ${netChange30 >= 0 ? 'text-green-600' : 'text-red-600'}`}
          >
            {netChange30 >= 0 ? '▲' : '▼'} {formatUsd(Math.abs(netChange30))} from today
          </p>
        </div>

        {/* Card 3 — Balance Status */}
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Balance Status</p>
          <div className="mt-2">
            <span
              className={`inline-block rounded-lg px-3 py-1.5 text-lg font-bold ${getStatusClasses(
                todayEntry?.balance_status ?? 'healthy'
              )}`}
            >
              {getStatusLabel(todayEntry?.balance_status ?? 'healthy')}
            </span>
          </div>
          {tightPeriod && (
            <p className="mt-2 text-sm text-gray-600">Tight period: {tightPeriod}</p>
          )}
        </div>
      </div>

      {userTier === 'budget' ? (
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-[#1E293B]">Who&apos;s in your forecast this month</p>
          <p className="mt-2 text-sm text-[#64748B]">
            See who&apos;s in your forecast and their approximate 30-day costs — included with Mid-tier and
            Professional.
          </p>
          <Link
            to="/settings/upgrade"
            className="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg bg-[#5B2D8E] px-4 text-sm font-semibold text-white hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
          >
            View upgrade options
          </Link>
        </div>
      ) : (
        <PeopleCostSummary userEmail={userEmail} />
      )}

      {relationshipCostBreakdown.length > 0 && (
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
            <h3 className="text-base font-semibold text-[#1E293B]">People in this forecast</h3>
            <button
              type="button"
              onClick={() => setRelationshipBreakdownExpanded((e) => !e)}
              className="shrink-0 text-left text-sm font-medium text-[#6D28D9] hover:underline sm:text-right"
              aria-expanded={relationshipBreakdownExpanded}
            >
              {relationshipBreakdownExpanded ? 'Hide breakdown ▲' : 'Show breakdown ▼'}
            </button>
          </div>
          <div
            className="overflow-hidden transition-all duration-300"
            style={{ maxHeight: relationshipBreakdownExpanded ? 2000 : 0 }}
          >
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[280px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-[#E2E8F0] text-left">
                    <th className="py-2 pr-2 font-semibold text-[#1E293B]">Person</th>
                    <th className="py-2 pr-2 font-semibold text-[#1E293B]">Card type</th>
                    <th className="py-2 pr-2 text-right font-semibold text-[#1E293B]">Per month</th>
                    <th className="py-2 text-right font-semibold text-[#1E293B]">% of total expenses</th>
                  </tr>
                </thead>
                <tbody>
                  {relationshipCostBreakdown.map((row, idx) => (
                    <tr key={`${row.nickname}-${idx}`} className="border-b border-[#E2E8F0]">
                      <td className="py-2 pr-2 text-[#1E293B]">
                        <span className="mr-2 text-lg leading-none align-middle" aria-hidden>
                          {relationshipRowEmoji(row)}
                        </span>
                        <span className="align-middle font-medium">{row.nickname}</span>
                      </td>
                      <td className="py-2 pr-2 text-[#64748B]">{formatCardTypeLabel(row.card_type)}</td>
                      <td className="py-2 pr-2 text-right tabular-nums text-[#1E293B]">
                        {formatUsd(row.monthly_cost)}
                      </td>
                      <td className="py-2 text-right tabular-nums text-[#64748B]">
                        {typeof row.pct_of_total_expenses === 'number'
                          ? `${row.pct_of_total_expenses.toFixed(1)}%`
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-[#E2E8F0] font-semibold text-[#1E293B]">
                    <td className="pt-3" colSpan={4}>
                      Total relationship costs:{' '}
                      <span className="tabular-nums">
                        {formatUsd(
                          relationshipCostBreakdown.reduce((s, r) => s + (r.monthly_cost || 0), 0)
                        )}
                        /month
                      </span>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 90-day balance chart — mid & professional only */}
      {(userTier === 'mid' || userTier === 'professional') && chartData90.length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">90-Day Balance Forecast</h3>
              <p className="text-sm text-gray-500">Projected closing balance for the next 90 days</p>
            </div>
            <div className="mt-2 flex flex-wrap gap-3 text-xs sm:mt-0">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-green-600" aria-hidden /> On Track
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-500" aria-hidden /> Watch
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-red-600" aria-hidden /> Attention
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData90} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <defs>
                <linearGradient id={areaGradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={areaColor.from} stopOpacity={areaColor.fromOpacity} />
                  <stop offset="100%" stopColor="white" stopOpacity={1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis
                dataKey="date"
                tickFormatter={(dateStr) => formatChartDate(dateStr)}
                tick={{ fontSize: 12, fill: '#6B7280' }}
                interval={13}
              />
              <YAxis
                tickFormatter={formatUsdShort}
                tick={{ fontSize: 12, fill: '#6B7280' }}
                width={52}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const p = payload[0].payload as {
                    date: string;
                    balance: number;
                    status: 'healthy' | 'warning' | 'danger';
                  };
                  const dateFormatted = new Date(p.date + 'T00:00:00').toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  });
                  return (
                    <div className="rounded-lg bg-white p-3 text-sm shadow-lg">
                      <div className="font-medium text-gray-700">Date: {dateFormatted}</div>
                      <div className="mt-1 text-gray-700">Balance: {formatUsd(p.balance)}</div>
                      <div className="mt-2">
                        <span
                          className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${getStatusClasses(p.status)}`}
                        >
                          {getStatusLabel(p.status)}
                        </span>
                      </div>
                    </div>
                  );
                }}
              />
              <ReferenceLine
                y={0}
                stroke="#9CA3AF"
                strokeDasharray="4 4"
                label={{ value: '$0', position: 'right' }}
              />
              <Area
                type="monotone"
                dataKey="balance"
                stroke={strokeColor}
                strokeWidth={2}
                fill={`url(#${areaGradientId})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {userTier === 'budget' && (
        <div className="rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 p-6 text-center">
          <p className="text-gray-600">
            Upgrade to Mid-tier to see your 90-day forecast chart
          </p>
          <a
            href="/#pricing"
            className="mt-3 inline-block rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            View Plans
          </a>
        </div>
      )}

      {/* Monthly breakdown table — all tiers; budget sees locked (first 3 blurred), mid/pro see full */}
      <div className="rounded-xl bg-white p-6 shadow-sm">
        <button
          type="button"
          onClick={() => setTableExpanded((e) => !e)}
          className="flex w-full items-center justify-between text-left"
          aria-expanded={tableExpanded}
        >
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Monthly Forecast Summary</h3>
            <p className="text-sm text-gray-500">Your projected cash flow for the next 12 months</p>
          </div>
          <span className="shrink-0 text-sm font-medium text-gray-600">
            {tableExpanded ? 'Hide monthly breakdown ▲' : 'Show monthly breakdown ▼'}
          </span>
        </button>
        <div
          className="overflow-hidden transition-all duration-300"
          style={{ maxHeight: tableExpanded ? 2000 : 0 }}
        >
          {userTier === 'budget' && (
            <>
              <div className="relative mt-4">
                <div className="pointer-events-none select-none blur-sm opacity-50">
                  <MonthlyTable rows={monthlyTableRows.slice(0, 3)} />
                </div>
                <div className="absolute inset-0 flex flex-col items-center justify-center rounded-lg bg-white/80 p-6 text-center">
                  <p className="text-gray-700 font-medium">
                    Upgrade to Mid-tier to unlock the full 12-month forecast
                  </p>
                  <a
                    href="/#pricing"
                    className="mt-3 inline-block rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
                  >
                    View Plans
                  </a>
                </div>
              </div>
            </>
          )}
          {(userTier === 'mid' || userTier === 'professional') && (
            <div className="mt-4">
              <MonthlyTable rows={monthlyTableRows} onSelectMonth={userTier === 'professional' ? setSelectedMonthKey : undefined} />
            </div>
          )}
        </div>
      </div>

      {/* Mid-tier: locked vehicle drill-down */}
      {userTier === 'mid' && (
        <div className="rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 p-6 text-center">
          <p className="text-gray-600">
            Upgrade to Professional to see vehicle expense detail by month
          </p>
          <a
            href="/#pricing"
            className="mt-3 inline-block rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            View Plans
          </a>
        </div>
      )}

      {/* Professional: vehicle expense detail */}
      {userTier === 'professional' && (
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900">
            Vehicle Expenses — {new Date((vehicleDetails?.month ?? selectedMonthKey) + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </h3>
          <div className="mt-3">
            <label htmlFor="vehicle-month-select" className="sr-only">
              Select month
            </label>
            <select
              id="vehicle-month-select"
              value={selectedMonthKey}
              onChange={(e) => setSelectedMonthKey(e.target.value)}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
            >
              {monthlyTableRows.length > 0
                ? monthlyTableRows.map((r) => (
                    <option key={r.month} value={r.month}>
                      {r.month_label}
                    </option>
                  ))
                : (
                    <option value={currentMonthKey}>
                      {new Date(currentMonthKey + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                    </option>
                  )}
            </select>
          </div>
          <div className="mt-4 min-h-[80px]">
            {vehicleDetailsLoading && (
              <p className="text-sm text-gray-500">Loading…</p>
            )}
            {!vehicleDetailsLoading && vehicleDetails && (
              <>
                {vehicleDetails.vehicles.length === 0 && vehicleDetails.total_vehicle_cost === 0 ? (
                  <p className="text-sm text-gray-500">No vehicle expenses recorded for this month</p>
                ) : (
                  <ul className="list-none space-y-2">
                    {vehicleDetails.vehicles.map((v) => (
                      <React.Fragment key={v.vehicle_id}>
                        {v.routine_cost > 0 && (
                          <li className="flex justify-between text-sm">
                            <span className="text-gray-700">{v.vehicle_name} — Routine</span>
                            <span className="tabular-nums text-gray-900">{formatUsd(v.routine_cost)}</span>
                          </li>
                        )}
                        {v.repair_cost > 0 && (
                          <li className="flex justify-between text-sm">
                            <span className="text-gray-700">{v.vehicle_name} — Repair</span>
                            <span className="tabular-nums text-gray-900">{formatUsd(v.repair_cost)}</span>
                          </li>
                        )}
                        {v.routine_cost === 0 && v.repair_cost === 0 && v.total_cost > 0 && (
                          <li className="flex justify-between text-sm">
                            <span className="text-gray-700">{v.vehicle_name}</span>
                            <span className="tabular-nums text-gray-900">{formatUsd(v.total_cost)}</span>
                          </li>
                        )}
                      </React.Fragment>
                    ))}
                    <li className="mt-2 flex justify-between border-t border-gray-200 pt-2 text-sm font-medium">
                      <span className="text-gray-900">Total</span>
                      <span className="tabular-nums text-gray-900">{formatUsd(vehicleDetails.total_vehicle_cost)}</span>
                    </li>
                  </ul>
                )}
              </>
            )}
            {!vehicleDetailsLoading && !vehicleDetails && (
              <p className="text-sm text-gray-500">No vehicle expenses recorded for this month</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MonthlyTable({
  rows,
  onSelectMonth,
}: {
  rows: MonthlyTableRow[];
  onSelectMonth?: (monthKey: string) => void;
}) {
  return (
    <div className="overflow-x-hidden">
      <table className="w-full table-fixed border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-gray-100">
          <tr>
            <th className="border-b border-gray-200 py-2 pl-2 text-left font-semibold text-gray-900">Month</th>
            <th className="hidden border-b border-gray-200 py-2 text-right font-semibold text-gray-900 sm:table-cell">Opening Balance</th>
            <th className="border-b border-gray-200 py-2 pr-2 text-right font-semibold text-gray-900">Income</th>
            <th className="border-b border-gray-200 py-2 text-right font-semibold text-gray-900">Expenses</th>
            <th className="border-b border-gray-200 py-2 text-right font-semibold text-gray-900">Closing Balance</th>
            <th className="border-b border-gray-200 py-2 text-right font-semibold text-gray-900">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={r.month}
              className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
            >
              <td className="border-b border-gray-100 py-2 pl-2 text-gray-900">
                {onSelectMonth ? (
                  <button
                    type="button"
                    onClick={() => onSelectMonth(r.month)}
                    className="font-medium text-blue-600 hover:underline"
                  >
                    {r.month_label}
                  </button>
                ) : (
                  r.month_label
                )}
              </td>
              <td className="hidden border-b border-gray-100 py-2 text-right tabular-nums text-gray-700 sm:table-cell">{formatUsd(r.opening_balance)}</td>
              <td className="border-b border-gray-100 py-2 pr-2 text-right tabular-nums text-gray-700">{formatUsd(r.total_income)}</td>
              <td className="border-b border-gray-100 py-2 text-right tabular-nums text-gray-700">{formatUsd(r.total_expenses)}</td>
              <td
                className={`border-b border-gray-100 py-2 text-right tabular-nums font-medium ${
                  r.closing_balance >= 500 ? 'text-green-600' : r.closing_balance >= 0 ? 'text-amber-600' : 'text-red-600'
                }`}
              >
                {formatUsd(r.closing_balance)}
              </td>
              <td className="border-b border-gray-100 py-2 text-right">
                <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${getStatusClasses(r.worst_status)}`}>
                  {getStatusLabel(r.worst_status)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

