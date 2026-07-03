import { useEffect, useState } from 'react';
import { AssessmentTrend } from './AssessmentTrend';

interface HistoryPoint {
  id: number;
  score: number | null;
  risk_level?: string | null;
  created_at: string | null;
}

interface TrendData {
  latest_score: number | null;
  previous_score?: number | null;
  delta?: number | null;
  trend?: 'up' | 'down' | 'stable';
  history: HistoryPoint[];
}

const ASSESSMENT_LABELS: Record<string, string> = {
  'ai-risk': 'AI Replacement Risk',
  'income-comparison': 'Income Comparison',
  'layoff-risk': 'Layoff Risk',
  'cuffing-season': 'Cuffing Season Score',
  'vehicle-financial-health': 'Vehicle Financial Health',
};

function getAuthToken(): string {
  return localStorage.getItem('mingus_token') ?? localStorage.getItem('auth_token') ?? '';
}

export function SavedAssessments() {
  const [trends, setTrends] = useState<Record<string, TrendData>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getAuthToken();
    fetch('/api/user/assessments/history', {
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => (res.ok ? res.json() : { trends: {} }))
      .then((data: { trends?: Record<string, TrendData> }) => {
        setTrends(data.trends || {});
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const entries = Object.entries(trends);

  return (
    <section className="rounded-2xl bg-white p-6 shadow-md">
      <h2 className="mb-4 text-lg font-semibold text-[#1E293B]">Your Saved Assessments</h2>
      {loading ? (
        <div className="h-16 animate-pulse rounded-xl bg-[#F8FAFC]" />
      ) : entries.length === 0 ? (
        <p className="text-sm text-[#64748B]">
          No assessments yet. Complete one to see results.
        </p>
      ) : (
        <div className="space-y-6">
          {entries.map(([atype, trend]) => (
            <div key={atype} className="rounded-xl border border-[#E2E8F0] p-4">
              <h3 className="text-base font-bold text-[#1E293B]">
                {ASSESSMENT_LABELS[atype] ?? atype}
              </h3>
              {trend.latest_score != null ? (
                <p className="mt-1 text-sm text-[#64748B]">
                  Latest:{' '}
                  <span className="font-bold text-[#5B2D8E]">{trend.latest_score}/100</span>
                  {trend.delta != null ? (
                    <span
                      className={
                        trend.delta > 0
                          ? 'text-green-600'
                          : trend.delta < 0
                            ? 'text-red-600'
                            : 'text-[#64748B]'
                      }
                    >
                      {' '}
                      ({trend.delta > 0 ? '+' : ''}
                      {trend.delta})
                    </span>
                  ) : null}
                </p>
              ) : null}
              <div className="mt-4">
                <AssessmentTrend assessmentType={atype} history={trend.history} />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
