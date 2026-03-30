import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3,
  KeyRound,
  LineChart,
  MessageSquare,
  RefreshCw,
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
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Load failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

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
      </main>
    </div>
  );
};

export default BetaAdminDashboard;
