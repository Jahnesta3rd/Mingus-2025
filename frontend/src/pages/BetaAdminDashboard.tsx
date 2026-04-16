import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3,
  Bug,
  KeyRound,
  LineChart,
  MessageSquare,
  RefreshCw,
  Sparkles,
  Star,
  Users,
} from 'lucide-react';
import { csrfHeaders } from '../utils/csrfHeaders';

const HEADER_PURPLE = '#5B2D8E';

interface OverviewPayload {
  codes: {
    total: number;
    redeemed: number;
    available: number;
    redemption_rate: number;
  };
  users: {
    total_beta: number;
    active_last_7_days: number;
    active_last_24_hours: number;
  };
  feature_events: {
    total_events: number;
    unique_users_tracked: number;
    top_features: { name: string; count: number }[];
  };
  feedback: {
    ratings_submitted: number;
    nps_submitted: number;
    avg_nps_score: number | null;
    thumbs_up_pct: number | null;
  };
}

interface FeedbackInsightsPayload {
  nps_breakdown: { detractors: number; passives: number; promoters: number };
  would_pay: { yes: number; maybe: number; no: number };
  top_valuable_features: { name: string; count: number }[];
}

interface BetaUserRow {
  user_id: number;
  email: string;
  first_name: string;
  created_at: string;
  beta_batch: string;
  events_count: number;
  last_active: string | null;
  nps_score: number | null;
  top_feature: string | null;
}

interface FeatureRow {
  feature_name: string;
  total_views: number;
  unique_users: number;
  avg_rating: number | null;
  thumbs_up: number;
  thumbs_down: number;
}

type UserSortKey = 'joined' | 'events' | 'nps';

const PAGE_SIZE = 25;

interface VibeCheckupsWindowMetrics {
  quiz_sessions_started: number;
  quiz_sessions_completed: number;
  completion_rate: number;
  leads_captured: number;
  email_capture_rate: number;
  projection_unlocks: number;
  projection_unlock_rate: number;
  mingus_cta_clicks: number;
  mingus_cta_click_rate: number;
  mingus_converted: number;
  mingus_conversion_rate: number;
  mingus_conversion_of_cta_rate: number;
}

interface SpiritMetricsPayload {
  total_checkins_all_time: number;
  checkins_last_30_days: number;
  active_users_last_30_days: number;
  avg_streak_active_users: number;
  avg_practice_score: number;
  practice_type_breakdown: Record<string, number>;
  avg_corr_practice_savings: number;
  avg_corr_practice_stress: number;
  pct_users_with_positive_savings_corr: number;
}

function formatTopPractice(breakdown: Record<string, number>): string {
  const entries = Object.entries(breakdown || {});
  if (!entries.length) return '—';
  const [topKey, topCount] = entries.reduce<[string, number]>(
    (best, cur) => (cur[1] > best[1] ? [cur[0], cur[1]] : best),
    entries[0]
  );
  if (!topCount) return '—';
  const labels: Record<string, string> = {
    prayer: 'Prayer',
    meditation: 'Meditation',
    gratitude: 'Gratitude',
    affirmation: 'Affirmation',
  };
  return labels[topKey] || topKey;
}

interface VibeCheckupsAnalyticsPayload {
  windows: {
    last_7d: VibeCheckupsWindowMetrics;
    last_30d: VibeCheckupsWindowMetrics;
    all_time: VibeCheckupsWindowMetrics;
  };
  top_utm_breakdown_30d: {
    utm_source: string;
    utm_medium: string;
    count: number;
    lead_count: number;
    conversion_rate: number;
  }[];
  verdict_distribution: { verdict_label: string; count: number; pct: number }[];
}

const VERDICT_PIE_COLORS = ['#5B2D8E', '#C4A064', '#0d9488', '#ea580c', '#be123c', '#64748b'];

type BugReportStatus = 'open' | 'in_progress' | 'resolved' | 'wont_fix';

type BugReportFilter = 'all' | 'open' | 'in_progress' | 'resolved';

interface BugTicketListItem {
  ticket_number: string;
  user_name: string;
  user_email: string;
  user_tier: string;
  is_beta: boolean;
  description_preview: string;
  current_route: string | null;
  balance_status: string | null;
  last_feature: string | null;
  account_age_days: number | null;
  status: BugReportStatus;
  created_at: string | null;
  resolved_at: string | null;
}

interface BugReportsListPayload {
  tickets: BugTicketListItem[];
  total: number;
  page: number;
  pages: number;
  open_count: number;
  in_progress_count: number;
}

interface BugReportFull {
  id: number;
  ticket_number: string;
  user_id: number;
  user_email: string;
  user_name: string;
  user_tier: string;
  description: string;
  current_route: string | null;
  browser_info: string | null;
  balance_status: string | null;
  last_feature: string | null;
  onboarding_complete: boolean;
  account_age_days: number | null;
  is_beta: boolean;
  status: BugReportStatus;
  admin_notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return '—';
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return '—';
  const sec = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (sec < 60) return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} minute${min === 1 ? '' : 's'} ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} hour${hr === 1 ? '' : 's'} ago`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} day${day === 1 ? '' : 's'} ago`;
  const mo = Math.floor(day / 30);
  if (mo < 12) return `${mo} month${mo === 1 ? '' : 's'} ago`;
  const yr = Math.floor(day / 365);
  return `${yr} year${yr === 1 ? '' : 's'} ago`;
}

function formatScreenRoute(route: string | null, maxLen: number): string {
  if (!route) return '—';
  const s = route.trim();
  if (s.length <= maxLen) return s;
  return `${s.slice(0, maxLen)}…`;
}

function bugStatusBadgeClasses(status: BugReportStatus): string {
  switch (status) {
    case 'open':
      return 'bg-[#FEE2E2] text-red-700';
    case 'in_progress':
      return 'bg-[#FEF3C7] text-amber-800';
    case 'resolved':
      return 'bg-[#D1FAE5] text-green-800';
    case 'wont_fix':
    default:
      return 'bg-gray-100 text-gray-600';
  }
}

function tierPillClasses(tier: string): string {
  const t = (tier || '').toLowerCase();
  if (t.includes('premium') || t.includes('elite')) {
    return 'bg-purple-100 text-purple-800 border border-purple-200';
  }
  if (t.includes('pro') || t.includes('plus') || t.includes('standard')) {
    return 'bg-blue-100 text-blue-800 border border-blue-200';
  }
  return 'bg-gray-100 text-gray-700 border border-gray-200';
}

function VerdictPieChart({
  slices,
}: {
  slices: { verdict_label: string; count: number; pct: number }[];
}) {
  if (!slices.length) {
    return <p className="text-sm text-gray-500">No verdict data yet.</p>;
  }
  let deg = 0;
  const parts = slices.map((s, i) => {
    const span = Math.max(0, s.pct) * 360;
    const from = deg;
    deg += span;
    const color = VERDICT_PIE_COLORS[i % VERDICT_PIE_COLORS.length];
    return `${color} ${from}deg ${deg}deg`;
  });
  return (
    <div className="flex flex-col sm:flex-row gap-6 items-center">
      <div
        className="h-44 w-44 shrink-0 rounded-full border border-gray-200 shadow-inner"
        style={{ background: `conic-gradient(${parts.join(', ')})` }}
        aria-hidden
      />
      <ul className="text-sm space-y-2 flex-1 min-w-0">
        {slices.map((s, i) => (
          <li key={s.verdict_label} className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-sm shrink-0"
              style={{ backgroundColor: VERDICT_PIE_COLORS[i % VERDICT_PIE_COLORS.length] }}
            />
            <span className="text-gray-800 truncate">{s.verdict_label}</span>
            <span className="text-gray-500 ml-auto tabular-nums">
              {(s.pct * 100).toFixed(1)}% ({s.count})
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const BetaAdminDashboard: React.FC = () => {
  const [overview, setOverview] = useState<OverviewPayload | null>(null);
  const [feedbackInsights, setFeedbackInsights] = useState<FeedbackInsightsPayload | null>(null);
  const [users, setUsers] = useState<BetaUserRow[]>([]);
  const [features, setFeatures] = useState<FeatureRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [userSort, setUserSort] = useState<{ key: UserSortKey; dir: 'asc' | 'desc' }>({
    key: 'joined',
    dir: 'desc',
  });
  const [userPage, setUserPage] = useState(0);
  const [vibeAnalytics, setVibeAnalytics] = useState<VibeCheckupsAnalyticsPayload | null>(null);
  const [spiritMetrics, setSpiritMetrics] = useState<SpiritMetricsPayload | null>(null);

  const [bugReports, setBugReports] = useState<BugReportsListPayload | null>(null);
  const [bugListLoading, setBugListLoading] = useState(false);
  const [bugListError, setBugListError] = useState<string | null>(null);
  const [bugFilter, setBugFilter] = useState<BugReportFilter>('all');
  const [bugPage, setBugPage] = useState(1);
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null);
  const [bugDetails, setBugDetails] = useState<Record<string, BugReportFull>>({});
  const [detailLoadingTicket, setDetailLoadingTicket] = useState<string | null>(null);
  const [notesDraft, setNotesDraft] = useState<Record<string, string>>({});
  const [savingNotesFor, setSavingNotesFor] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const [o, fi, u, f] = await Promise.all([
        fetch('/api/admin/beta/overview', { credentials: 'include', headers: { ...csrfHeaders() } }),
        fetch('/api/admin/beta/feedback-insights', {
          credentials: 'include',
          headers: { ...csrfHeaders() },
        }),
        fetch('/api/admin/beta/users', { credentials: 'include', headers: { ...csrfHeaders() } }),
        fetch('/api/admin/beta/features', { credentials: 'include', headers: { ...csrfHeaders() } }),
      ]);
      if (!o.ok || !fi.ok || !u.ok || !f.ok) {
        const msg =
          o.status === 403 ||
          fi.status === 403 ||
          u.status === 403 ||
          f.status === 403
            ? 'Admin access required'
            : 'Failed to load dashboard data';
        throw new Error(msg);
      }
      setOverview(await o.json());
      setFeedbackInsights(await fi.json());
      setUsers(await u.json());
      setFeatures(await f.json());

      try {
        const sm = await fetch('/api/admin/spirit-metrics', {
          credentials: 'include',
          headers: { ...csrfHeaders() },
        });
        if (sm.ok) {
          setSpiritMetrics((await sm.json()) as SpiritMetricsPayload);
        } else {
          setSpiritMetrics(null);
        }
      } catch {
        setSpiritMetrics(null);
      }

      try {
        const vc = await fetch('/api/vibe-checkups/analytics/summary', {
          credentials: 'include',
          headers: { ...csrfHeaders() },
        });
        if (vc.ok) {
          setVibeAnalytics((await vc.json()) as VibeCheckupsAnalyticsPayload);
        } else {
          setVibeAnalytics(null);
        }
      } catch {
        setVibeAnalytics(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setExpandedTicket(null);
    let cancelled = false;
    (async () => {
      setBugListLoading(true);
      setBugListError(null);
      try {
        const qs = new URLSearchParams();
        qs.set('status', bugFilter);
        qs.set('page', String(bugPage));
        qs.set('per_page', '25');
        const res = await fetch(`/api/admin/beta/bug-reports?${qs.toString()}`, {
          credentials: 'include',
          headers: { ...csrfHeaders() },
        });
        if (cancelled) return;
        if (res.status === 403) {
          setBugListError('Admin access required');
          setBugReports(null);
          return;
        }
        if (!res.ok) {
          setBugListError('Failed to load bug reports');
          setBugReports(null);
          return;
        }
        setBugReports((await res.json()) as BugReportsListPayload);
      } catch {
        if (!cancelled) {
          setBugListError('Failed to load bug reports');
          setBugReports(null);
        }
      } finally {
        if (!cancelled) setBugListLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [bugFilter, bugPage]);

  useEffect(() => {
    if (!expandedTicket) return;
    let cancelled = false;
    (async () => {
      setDetailLoadingTicket(expandedTicket);
      try {
        const res = await fetch(
          `/api/admin/beta/bug-reports/${encodeURIComponent(expandedTicket)}`,
          { credentials: 'include', headers: { ...csrfHeaders() } }
        );
        if (cancelled || !res.ok) return;
        const data = (await res.json()) as BugReportFull;
        if (cancelled) return;
        setBugDetails((p) => ({ ...p, [expandedTicket]: data }));
        setNotesDraft((p) => ({ ...p, [expandedTicket]: data.admin_notes ?? '' }));
      } finally {
        if (!cancelled) setDetailLoadingTicket(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [expandedTicket]);

  const setBugFilterAndResetPage = (f: BugReportFilter) => {
    setBugFilter(f);
    setBugPage(1);
  };

  const patchTicketStatus = async (ticket: string, status: BugReportStatus) => {
    const res = await fetch(`/api/bug-report/${encodeURIComponent(ticket)}/status`, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) return;
    const updated = (await res.json()) as BugReportFull;
    setBugReports((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        tickets: prev.tickets.map((t) =>
          t.ticket_number === ticket
            ? { ...t, status: updated.status, resolved_at: updated.resolved_at }
            : t
        ),
      };
    });
    setBugDetails((p) => ({ ...p, [ticket]: updated }));
  };

  const saveAdminNotes = async (ticket: string) => {
    const detail = bugDetails[ticket];
    const row = bugReports?.tickets.find((t) => t.ticket_number === ticket);
    const status = detail?.status ?? row?.status;
    if (!status) return;
    setSavingNotesFor(ticket);
    try {
      const res = await fetch(`/api/bug-report/${encodeURIComponent(ticket)}/status`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
        body: JSON.stringify({
          status,
          admin_notes: notesDraft[ticket] ?? '',
        }),
      });
      if (!res.ok) return;
      const updated = (await res.json()) as BugReportFull;
      setBugDetails((p) => ({ ...p, [ticket]: updated }));
      setNotesDraft((p) => ({ ...p, [ticket]: updated.admin_notes ?? '' }));
    } finally {
      setSavingNotesFor(null);
    }
  };

  const sortedUsers = useMemo(() => {
    const list = [...users];
    const { key, dir } = userSort;
    const mul = dir === 'asc' ? 1 : -1;
    list.sort((a, b) => {
      if (key === 'joined') {
        return mul * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      }
      if (key === 'events') {
        return mul * (a.events_count - b.events_count);
      }
      const an = a.nps_score ?? -1;
      const bn = b.nps_score ?? -1;
      return mul * (an - bn);
    });
    return list;
  }, [users, userSort]);

  const userPageCount = Math.ceil(sortedUsers.length / PAGE_SIZE) || 1;
  const pagedUsers = useMemo(() => {
    const start = userPage * PAGE_SIZE;
    return sortedUsers.slice(start, start + PAGE_SIZE);
  }, [sortedUsers, userPage]);

  useEffect(() => {
    setUserPage(0);
  }, [users.length, userSort]);

  useEffect(() => {
    if (userPage >= userPageCount) setUserPage(Math.max(0, userPageCount - 1));
  }, [userPage, userPageCount]);

  const toggleUserSort = (key: UserSortKey) => {
    setUserSort((prev) =>
      prev.key === key ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' }
    );
  };

  const maxViews = useMemo(
    () => features.reduce((m, r) => Math.max(m, r.total_views), 0),
    [features]
  );

  const sortIndicator = (key: UserSortKey) =>
    userSort.key === key ? (userSort.dir === 'asc' ? ' ↑' : ' ↓') : '';

  if (loading && !overview) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center text-gray-600">
        Loading dashboard…
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-red-600">{error}</p>
        <button
          type="button"
          onClick={() => void load()}
          className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm"
        >
          Retry
        </button>
        <Link to="/dashboard" className="text-sm text-[#5B2D8E] underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const codes = overview?.codes;
  const betaUsersCount = overview?.users.total_beta ?? 0;
  const active7 = overview?.users.active_last_7_days ?? 0;
  const avgNps = overview?.feedback.avg_nps_score;
  const npsB = feedbackInsights?.nps_breakdown ?? { detractors: 0, passives: 0, promoters: 0 };
  const wp = feedbackInsights?.would_pay ?? { yes: 0, maybe: 0, no: 0 };
  const topVf = feedbackInsights?.top_valuable_features ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="text-white shadow-sm" style={{ backgroundColor: HEADER_PURPLE }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Beta admin</h1>
            <p className="text-sm text-white/80 mt-1">Codes, beta users, telemetry, and feedback</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => void load()}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white/15 hover:bg-white/25 text-sm font-medium disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <Link
              to="/dashboard"
              className="text-sm font-medium px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20"
            >
              Main dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {/* Section 1 — Overview cards */}
        <section aria-label="Overview statistics">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex gap-4">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-lg shrink-0"
                style={{ backgroundColor: `${HEADER_PURPLE}18` }}
              >
                <KeyRound className="w-6 h-6" style={{ color: HEADER_PURPLE }} />
              </div>
              <div>
                <p className="text-sm text-gray-500 font-medium">Codes redeemed</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {codes?.redeemed ?? 0} / {codes?.total ?? 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {((codes?.redemption_rate ?? 0) * 100).toFixed(1)}% redemption rate
                </p>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex gap-4">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-lg shrink-0"
                style={{ backgroundColor: `${HEADER_PURPLE}18` }}
              >
                <Users className="w-6 h-6" style={{ color: HEADER_PURPLE }} />
              </div>
              <div>
                <p className="text-sm text-gray-500 font-medium">Beta users</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{betaUsersCount}</p>
                <p className="text-xs text-gray-500 mt-1">Total with beta access</p>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex gap-4">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-lg shrink-0"
                style={{ backgroundColor: `${HEADER_PURPLE}18` }}
              >
                <LineChart className="w-6 h-6" style={{ color: HEADER_PURPLE }} />
              </div>
              <div>
                <p className="text-sm text-gray-500 font-medium">Active (7 days)</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{active7}</p>
                <p className="text-xs text-gray-500 mt-1">Beta users with telemetry</p>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex gap-4">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-lg shrink-0"
                style={{ backgroundColor: `${HEADER_PURPLE}18` }}
              >
                <MessageSquare className="w-6 h-6" style={{ color: HEADER_PURPLE }} />
              </div>
              <div>
                <p className="text-sm text-gray-500 font-medium">Avg NPS score</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {avgNps == null ? '—' : avgNps.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 mt-1">From submitted surveys</p>
              </div>
            </div>
          </div>
        </section>

        {/* Spirit & Finance aggregate metrics */}
        <section
          aria-label="Spirit and finance metrics"
          className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5" style={{ color: HEADER_PURPLE }} />
            <h2 className="text-lg font-semibold text-gray-900">Spirit &amp; Finance Metrics</h2>
          </div>
          <div className="p-5">
            {!spiritMetrics ? (
              <p className="text-sm text-gray-500">
                Metrics unavailable (requires admin access and spirit check-in data).
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                <div className="flex justify-between gap-4 border-b border-gray-100 pb-3 sm:border-0 sm:pb-0">
                  <span className="text-gray-500 font-medium">Check-Ins (Last 30 Days)</span>
                  <span className="text-gray-900 font-semibold tabular-nums">
                    {spiritMetrics.checkins_last_30_days}
                  </span>
                </div>
                <div className="flex justify-between gap-4 border-b border-gray-100 pb-3 sm:border-0 sm:pb-0">
                  <span className="text-gray-500 font-medium">Active Users</span>
                  <span className="text-gray-900 font-semibold tabular-nums">
                    {spiritMetrics.active_users_last_30_days}
                  </span>
                </div>
                <div className="flex justify-between gap-4 border-b border-gray-100 pb-3 sm:border-0 sm:pb-0">
                  <span className="text-gray-500 font-medium">Avg Streak</span>
                  <span className="text-gray-900 font-semibold tabular-nums">
                    {spiritMetrics.avg_streak_active_users.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between gap-4 border-b border-gray-100 pb-3 sm:border-0 sm:pb-0">
                  <span className="text-gray-500 font-medium">Avg Practice Score</span>
                  <span className="text-gray-900 font-semibold tabular-nums">
                    {spiritMetrics.avg_practice_score.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between gap-4 border-b border-gray-100 pb-3 sm:border-0 sm:pb-0">
                  <span className="text-gray-500 font-medium">Most Popular Practice</span>
                  <span className="text-gray-900 font-semibold text-right">
                    {formatTopPractice(spiritMetrics.practice_type_breakdown)}
                  </span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-gray-500 font-medium">% Users with Positive Savings Correlation</span>
                  <span className="text-gray-900 font-semibold tabular-nums">
                    {spiritMetrics.pct_users_with_positive_savings_corr.toFixed(1)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Vibe Checkups funnel */}
        {vibeAnalytics && (
          <section
            aria-label="Vibe Checkups analytics"
            className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden space-y-0"
          >
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Vibe Checkups</h2>
              <p className="text-sm text-gray-500 mt-1">
                Love Ledger funnel — sessions, capture, projection unlock, and Mingus upsell
              </p>
            </div>
            <div className="p-5 overflow-x-auto">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Funnel metrics by window</h3>
              <table className="min-w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="text-gray-600 border-b border-gray-200">
                    <th className="py-2 pr-4 font-medium">Metric</th>
                    <th className="py-2 pr-4 font-medium text-right">Last 7d</th>
                    <th className="py-2 pr-4 font-medium text-right">Last 30d</th>
                    <th className="py-2 font-medium text-right">All time</th>
                  </tr>
                </thead>
                <tbody className="text-gray-800">
                  {(
                    [
                      ['Quiz sessions started', 'quiz_sessions_started', false],
                      ['Quiz sessions completed', 'quiz_sessions_completed', false],
                      ['Completion rate', 'completion_rate', true],
                      ['Leads (email captured)', 'leads_captured', false],
                      ['Email capture rate', 'email_capture_rate', true],
                      ['Projection unlocks', 'projection_unlocks', false],
                      ['Projection unlock rate', 'projection_unlock_rate', true],
                      ['Mingus CTA clicks (distinct leads)', 'mingus_cta_clicks', false],
                      ['Mingus CTA click rate', 'mingus_cta_click_rate', true],
                      ['Mingus conversions', 'mingus_converted', false],
                      ['Mingus conversion rate (of leads)', 'mingus_conversion_rate', true],
                      ['Mingus conversion of CTA', 'mingus_conversion_of_cta_rate', true],
                    ] as const
                  ).map(([label, key, isRate]) => {
                    const w7 = vibeAnalytics.windows.last_7d[key];
                    const w30 = vibeAnalytics.windows.last_30d[key];
                    const wa = vibeAnalytics.windows.all_time[key];
                    const fmt = (v: number) =>
                      isRate ? `${(Number(v) * 100).toFixed(1)}%` : String(v);
                    return (
                      <tr key={key} className="border-b border-gray-100">
                        <td className="py-2 pr-4">{label}</td>
                        <td className="py-2 pr-4 text-right tabular-nums">{fmt(w7)}</td>
                        <td className="py-2 pr-4 text-right tabular-nums">{fmt(w30)}</td>
                        <td className="py-2 text-right tabular-nums">{fmt(wa)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="px-5 pb-5">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Top UTM sources (last 30 days)
              </h3>
              <div className="overflow-x-auto rounded-lg border border-gray-100">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left text-gray-600">
                      <th className="px-4 py-2 font-medium">utm_source</th>
                      <th className="px-4 py-2 font-medium">utm_medium</th>
                      <th className="px-4 py-2 font-medium text-right">Sessions</th>
                      <th className="px-4 py-2 font-medium text-right">Leads</th>
                      <th className="px-4 py-2 font-medium text-right">Mingus conv. rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vibeAnalytics.top_utm_breakdown_30d.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                          No UTM-tagged sessions in the last 30 days.
                        </td>
                      </tr>
                    ) : (
                      vibeAnalytics.top_utm_breakdown_30d.map((row, idx) => (
                        <tr
                          key={`${row.utm_source}-${row.utm_medium}-${idx}`}
                          className="border-t border-gray-100"
                        >
                          <td className="px-4 py-2 text-gray-900">{row.utm_source}</td>
                          <td className="px-4 py-2 text-gray-700">{row.utm_medium}</td>
                          <td className="px-4 py-2 text-right tabular-nums">{row.count}</td>
                          <td className="px-4 py-2 text-right tabular-nums">{row.lead_count}</td>
                          <td className="px-4 py-2 text-right tabular-nums">
                            {(row.conversion_rate * 100).toFixed(1)}%
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="px-5 pb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Verdict distribution</h3>
              <VerdictPieChart slices={vibeAnalytics.verdict_distribution} />
            </div>
          </section>
        )}

        {/* Section 2 — Beta users */}
        <section aria-label="Beta users" className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Beta users</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-gray-600">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Batch</th>
                  <th className="px-4 py-3 font-medium">
                    <button
                      type="button"
                      onClick={() => toggleUserSort('joined')}
                      className="hover:text-[#5B2D8E] font-medium"
                    >
                      Joined{sortIndicator('joined')}
                    </button>
                  </th>
                  <th className="px-4 py-3 font-medium text-right">
                    <button
                      type="button"
                      onClick={() => toggleUserSort('events')}
                      className="hover:text-[#5B2D8E] font-medium"
                    >
                      Events{sortIndicator('events')}
                    </button>
                  </th>
                  <th className="px-4 py-3 font-medium">Last active</th>
                  <th className="px-4 py-3 font-medium text-right">
                    <button
                      type="button"
                      onClick={() => toggleUserSort('nps')}
                      className="hover:text-[#5B2D8E] font-medium"
                    >
                      NPS{sortIndicator('nps')}
                    </button>
                  </th>
                  <th className="px-4 py-3 font-medium">Top feature</th>
                </tr>
              </thead>
              <tbody>
                {pagedUsers.map((row) => (
                  <tr
                    key={row.user_id}
                    className="border-t border-gray-100 hover:bg-purple-50/60 transition-colors"
                  >
                    <td className="px-4 py-3 text-gray-900">{row.first_name || '—'}</td>
                    <td className="px-4 py-3 text-gray-700">{row.email}</td>
                    <td className="px-4 py-3 text-gray-600">{row.beta_batch || '—'}</td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {row.created_at
                        ? new Date(row.created_at).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">{row.events_count}</td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {row.last_active
                        ? new Date(row.last_active).toLocaleString()
                        : 'No activity'}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {row.nps_score ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 font-mono text-xs">
                      {row.top_feature ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {sortedUsers.length > PAGE_SIZE && (
            <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-600">
              <span>
                Page {userPage + 1} of {userPageCount} ({sortedUsers.length} users)
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={userPage <= 0}
                  onClick={() => setUserPage((p) => Math.max(0, p - 1))}
                  className="px-3 py-1 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  disabled={userPage >= userPageCount - 1}
                  onClick={() => setUserPage((p) => Math.min(userPageCount - 1, p + 1))}
                  className="px-3 py-1 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Section 3 — Features */}
        <section
          aria-label="Feature engagement"
          className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Feature engagement</h2>
            <p className="text-sm text-gray-500 mt-1">Sorted by views (telemetry)</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-gray-600">
                  <th className="px-4 py-3 font-medium">Feature</th>
                  <th className="px-4 py-3 font-medium w-40">Share</th>
                  <th className="px-4 py-3 font-medium text-right">Views</th>
                  <th className="px-4 py-3 font-medium text-right">Unique users</th>
                  <th className="px-4 py-3 font-medium text-right">👍</th>
                  <th className="px-4 py-3 font-medium text-right">👎</th>
                  <th className="px-4 py-3 font-medium text-right">Avg rating</th>
                </tr>
              </thead>
              <tbody>
                {features.map((row) => {
                  const pct = maxViews > 0 ? (row.total_views / maxViews) * 100 : 0;
                  return (
                    <tr key={row.feature_name} className="border-t border-gray-100">
                      <td className="px-4 py-3 font-mono text-xs text-gray-900">
                        {row.feature_name}
                      </td>
                      <td className="px-4 py-3 align-middle">
                        <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${pct}%`,
                              backgroundColor: HEADER_PURPLE,
                            }}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-900">{row.total_views}</td>
                      <td className="px-4 py-3 text-right text-gray-700">{row.unique_users}</td>
                      <td className="px-4 py-3 text-right">{row.thumbs_up}</td>
                      <td className="px-4 py-3 text-right">{row.thumbs_down}</td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {row.avg_rating == null ? '—' : row.avg_rating.toFixed(1)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {features.length === 0 && (
            <p className="px-5 py-8 text-center text-gray-500 text-sm">No feature telemetry yet.</p>
          )}
        </section>

        {/* Section 4 — Feedback */}
        <section
          aria-label="Quick feedback stats"
          className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-6"
        >
          <h2 className="text-lg font-semibold text-gray-900">Quick feedback stats</h2>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">NPS breakdown</h3>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                Detractors (0–6): {npsB.detractors}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-900">
                Passives (7–8): {npsB.passives}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                Promoters (9–10): {npsB.promoters}
              </span>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Would pay</h3>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800 border border-gray-200">
                Yes: {wp.yes}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800 border border-gray-200">
                Maybe: {wp.maybe}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800 border border-gray-200">
                No: {wp.no}
              </span>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Most valuable feature (top 3)</h3>
            {topVf.length === 0 ? (
              <p className="text-sm text-gray-500">No responses yet.</p>
            ) : (
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-800">
                {topVf.map((item) => (
                  <li key={item.name}>
                    <span className="font-mono text-xs">{item.name}</span>
                    <span className="text-gray-500"> ({item.count})</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </section>

        {/* Section 5 — Bug reports */}
        <section
          aria-label="Bug reports"
          className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-gray-100 flex flex-wrap items-center gap-3 justify-between gap-y-2">
            <div className="flex items-center gap-2 min-w-0">
              <Bug className="w-5 h-5 shrink-0" style={{ color: HEADER_PURPLE }} />
              <h2 className="text-lg font-semibold text-gray-900">Bug Reports</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                {bugReports?.open_count ?? 0} open
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-900">
                {bugReports?.in_progress_count ?? 0} in progress
              </span>
            </div>
          </div>

          <div className="px-5 pt-3 pb-2 border-b border-gray-100 flex flex-wrap gap-1">
            {(
              [
                ['all', 'All'],
                ['open', 'Open'],
                ['in_progress', 'In Progress'],
                ['resolved', 'Resolved'],
              ] as const
            ).map(([key, label]) => {
              const active = bugFilter === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setBugFilterAndResetPage(key)}
                  className={`px-3 py-2 text-sm font-medium rounded-t-md border-b-2 -mb-px transition-colors ${
                    active
                      ? 'text-[#5B2D8E] border-[#5B2D8E]'
                      : 'text-gray-600 border-transparent hover:text-gray-800'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {bugListError && (
            <p className="px-5 py-4 text-sm text-red-600 border-b border-gray-100">{bugListError}</p>
          )}

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-gray-600">
                  <th className="px-4 py-3 font-medium">Ticket</th>
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Tier</th>
                  <th className="px-4 py-3 font-medium">Screen</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {bugListLoading && !bugReports ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      Loading bug reports…
                    </td>
                  </tr>
                ) : bugReports && bugReports.tickets.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-500">
                      {bugFilter === 'all'
                        ? 'No tickets'
                        : `No ${bugFilter === 'in_progress' ? 'in progress' : bugFilter} tickets`}
                    </td>
                  </tr>
                ) : (
                  bugReports?.tickets.map((row) => {
                    const expanded = expandedTicket === row.ticket_number;
                    const detail = bugDetails[row.ticket_number];
                    const loadingDetail = detailLoadingTicket === row.ticket_number;
                    const statusBtn = (s: BugReportStatus) => {
                      const cur = detail?.status ?? row.status;
                      const isCur = cur === s;
                      const labels: Record<BugReportStatus, string> = {
                        open: 'Open',
                        in_progress: 'In progress',
                        resolved: 'Resolved',
                        wont_fix: "Won't fix",
                      };
                      return (
                        <button
                          key={s}
                          type="button"
                          className={`w-full text-left text-sm font-medium px-3 py-2 rounded-lg border transition-colors ${
                            isCur
                              ? 'bg-[#5B2D8E] text-white border-[#5B2D8E]'
                              : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                          }`}
                          onClick={() => void patchTicketStatus(row.ticket_number, s)}
                        >
                          {labels[s]}
                        </button>
                      );
                    };
                    const formatStatusLabel = (s: BugReportStatus) =>
                      s === 'in_progress'
                        ? 'In progress'
                        : s === 'wont_fix'
                          ? "Won't fix"
                          : `${s.charAt(0).toUpperCase()}${s.slice(1)}`;
                    return (
                      <React.Fragment key={row.ticket_number}>
                        <tr
                          role="button"
                          tabIndex={0}
                          onClick={() =>
                            setExpandedTicket((cur) =>
                              cur === row.ticket_number ? null : row.ticket_number
                            )
                          }
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              setExpandedTicket((cur) =>
                                cur === row.ticket_number ? null : row.ticket_number
                              );
                            }
                          }}
                          className={`border-t border-gray-100 transition-colors cursor-pointer ${
                            expanded ? 'bg-purple-50/80' : 'hover:bg-purple-50/60'
                          }`}
                        >
                          <td className="px-4 py-3 align-top whitespace-nowrap">
                            <span
                              className="font-mono font-bold text-[13px]"
                              style={{ color: HEADER_PURPLE }}
                            >
                              {row.ticket_number}
                            </span>
                          </td>
                          <td className="px-4 py-3 align-top">
                            <p className="font-bold text-[13px] text-gray-900">{row.user_name}</p>
                            <p className="text-[11px] text-gray-500 mt-0.5 break-all">
                              {row.user_email}
                            </p>
                          </td>
                          <td className="px-4 py-3 align-top whitespace-nowrap">
                            <div className="flex items-center gap-1">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${tierPillClasses(
                                  row.user_tier
                                )}`}
                              >
                                {row.user_tier}
                              </span>
                              {row.is_beta ? (
                                <Star
                                  className="w-3.5 h-3.5 text-amber-500 shrink-0"
                                  fill="currentColor"
                                  aria-label="Beta user"
                                />
                              ) : null}
                            </div>
                          </td>
                          <td className="px-4 py-3 align-top text-gray-500 text-[12px] max-w-[10rem] break-all">
                            {formatScreenRoute(row.current_route, 30)}
                          </td>
                          <td className="px-4 py-3 align-top whitespace-nowrap">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${bugStatusBadgeClasses(
                                row.status
                              )}`}
                            >
                              {formatStatusLabel(row.status)}
                            </span>
                          </td>
                          <td className="px-4 py-3 align-top text-gray-600 whitespace-nowrap">
                            {formatRelativeTime(row.created_at)}
                          </td>
                        </tr>
                        {expanded ? (
                          <tr className="border-t border-gray-100 bg-gray-50/80">
                            <td colSpan={6} className="px-4 py-4">
                              {loadingDetail ? (
                                <p className="text-sm text-gray-500">Loading details…</p>
                              ) : detail ? (
                                <div className="flex flex-col lg:flex-row gap-6">
                                  <div className="flex-1 min-w-0 lg:max-w-[60%]">
                                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-2">
                                      What they reported
                                    </p>
                                    <div className="bg-white rounded-lg p-3 text-sm text-gray-900 border border-gray-100 whitespace-pre-wrap break-words">
                                      {detail.description}
                                    </div>
                                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                      <div>
                                        <span className="text-gray-500">Balance status</span>
                                        <p className="font-medium text-gray-900">
                                          {detail.balance_status ?? '—'}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">Last feature</span>
                                        <p className="font-medium text-gray-900 break-all">
                                          {detail.last_feature ?? '—'}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">Account age</span>
                                        <p className="font-medium text-gray-900">
                                          {detail.account_age_days != null
                                            ? `${detail.account_age_days} days`
                                            : '—'}
                                        </p>
                                      </div>
                                      <div>
                                        <span className="text-gray-500">Beta user</span>
                                        <p className="font-medium text-gray-900">
                                          {detail.is_beta ? 'Yes' : 'No'}
                                        </p>
                                      </div>
                                      <div className="sm:col-span-2">
                                        <span className="text-gray-500">Browser</span>
                                        <p className="font-medium text-gray-900 break-all">
                                          {detail.browser_info ?? '—'}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                  <div className="w-full lg:w-[40%] shrink-0 min-w-0">
                                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-2">
                                      Update status
                                    </p>
                                    <div className="flex flex-col gap-2">
                                      {statusBtn('open')}
                                      {statusBtn('in_progress')}
                                      {statusBtn('resolved')}
                                      {statusBtn('wont_fix')}
                                    </div>
                                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mt-4 mb-2">
                                      Admin notes
                                    </p>
                                    <textarea
                                      className="w-full border border-gray-200 rounded-lg text-sm p-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#5B2D8E]/30"
                                      rows={3}
                                      placeholder="Internal notes (not visible to user)..."
                                      value={notesDraft[row.ticket_number] ?? ''}
                                      onChange={(e) =>
                                        setNotesDraft((p) => ({
                                          ...p,
                                          [row.ticket_number]: e.target.value,
                                        }))
                                      }
                                      onClick={(e) => e.stopPropagation()}
                                    />
                                    <button
                                      type="button"
                                      disabled={savingNotesFor === row.ticket_number}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        void saveAdminNotes(row.ticket_number);
                                      }}
                                      className="mt-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50"
                                    >
                                      {savingNotesFor === row.ticket_number ? 'Saving…' : 'Save Notes'}
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <p className="text-sm text-gray-500">Could not load ticket.</p>
                              )}
                            </td>
                          </tr>
                        ) : null}
                      </React.Fragment>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {bugReports && bugReports.pages > 1 ? (
            <div className="grid grid-cols-3 items-center gap-2 px-5 py-3 border-t border-gray-100 text-sm text-gray-600">
              <button
                type="button"
                disabled={bugPage <= 1 || bugListLoading}
                onClick={() => setBugPage((p) => Math.max(1, p - 1))}
                className="justify-self-start px-3 py-1 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="text-center tabular-nums">
                Page {bugPage} of {bugReports.pages}
              </span>
              <button
                type="button"
                disabled={bugPage >= bugReports.pages || bugListLoading}
                onClick={() => setBugPage((p) => p + 1)}
                className="justify-self-end px-3 py-1 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
};

export default BetaAdminDashboard;
