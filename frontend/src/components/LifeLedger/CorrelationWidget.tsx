import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useLifeCorrelation, type LifeCorrelationItem } from '../../hooks/useLifeCorrelation';
import CorrelationInsightCard from './CorrelationInsightCard';
import ScoreTimelineChart from './ScoreTimelineChart';

function resolveTier(user: ReturnType<typeof useAuth>['user']): 'budget' | 'mid_tier' | 'professional' {
  if (user?.is_beta === true || user?.tier === 'professional') return 'professional';
  if (user?.tier === 'mid_tier') return 'mid_tier';
  return 'budget';
}

const strengthRank = (s: string): number => {
  const x = s.toLowerCase();
  if (x === 'strong') return 0;
  if (x === 'moderate') return 1;
  return 2;
};

const MID_PREVIEW_PLACEHOLDERS: LifeCorrelationItem[] = [
  {
    type: 'FITNESS_VIBE_POSITIVE',
    strength: 'strong',
    description: 'Movement and emotional check-in scores trended together in your history.',
    insight_message:
      'When you have enough data, we surface how physical momentum and relationship energy move in sync.',
  },
  {
    type: 'FINANCIAL_VIBE_POSITIVE',
    strength: 'moderate',
    description: 'Savings clarity and financial compatibility patterns may emerge over time.',
    insight_message: 'Upgrade to see how your financial habits line up with who you are choosing.',
  },
  {
    type: 'WELLNESS_VIBE_POSITIVE',
    strength: 'mild',
    description: 'Wellness and emotional scores can tell a story when tracked consistently.',
    insight_message: 'Professional unlocks the full set of observational cards for your timeline.',
  },
];

const CorrelationWidget: React.FC = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const tier = resolveTier(user);
  const enabled = isAuthenticated && tier !== 'budget';
  const { summary, snapshots, loading, error, refetch } = useLifeCorrelation(enabled, tier);

  const monthsApprox = useMemo(() => {
    const days = summary?.date_range_days ?? 0;
    if (days > 0) return Math.max(1, Math.round(days / 30));
    const n = summary?.snapshots_count ?? 0;
    return Math.max(1, n > 0 ? Math.min(n, 12) : 1);
  }, [summary]);

  const sortedCorrelations = useMemo(() => {
    const list = summary?.correlations ?? [];
    return [...list].sort((a, b) => strengthRank(a.strength) - strengthRank(b.strength)).slice(0, 4);
  }, [summary]);

  const snapshotsCount = summary?.snapshots_count ?? 0;

  if (authLoading) {
    return (
      <div className="w-full rounded-xl border border-[#9a8f7e]/25 bg-[#0d0a08] p-6 animate-pulse">
        <div className="h-5 bg-[#1a1512] rounded w-1/3 mb-3" />
        <div className="h-3 bg-[#1a1512] rounded w-2/3" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (tier === 'budget') {
    return (
      <div className="w-full rounded-xl border border-[#C4A064]/35 bg-[#0d0a08] p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[#C4A064]" aria-hidden>
            ✦
          </span>
          <h2 className="text-lg font-semibold text-[#F0E8D8]">Life Correlation</h2>
        </div>
        <p className="text-sm text-[#9a8f7e] mb-3">How your growth shows up in who you&apos;re choosing</p>
        <p className="text-[#F0E8D8] text-sm leading-relaxed mb-2">
          Discover how your fitness and finances affect your relationship choices
        </p>
        <p className="text-xs text-[#9a8f7e] mb-4">Available on Mid-tier and above</p>
        <Link
          to="/settings/upgrade"
          className="inline-flex items-center justify-center rounded-lg bg-[#C4A064] px-4 py-2 text-sm font-semibold text-[#0d0a08] hover:bg-[#d4b074] transition-colors"
        >
          Upgrade
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl border border-[#9a8f7e]/25 bg-[#0d0a08] p-6 shadow-lg text-left">
      <header className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[#C4A064]" aria-hidden>
            ✦
          </span>
          <h2 className="text-lg font-semibold text-[#F0E8D8]">Life Correlation</h2>
        </div>
        <p className="text-sm text-[#9a8f7e]">How your growth shows up in who you&apos;re choosing</p>
      </header>

      {loading && (
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-[#1a1512] rounded w-3/4" />
          <div className="h-24 bg-[#1a1512] rounded" />
          <div className="h-4 bg-[#1a1512] rounded w-1/2" />
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-amber-900/40 bg-[#1a1512] p-4 text-sm text-[#F0E8D8]">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-3 text-[#C4A064] underline text-sm font-medium hover:text-[#d4b074]"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && summary && !summary.has_sufficient_data && (
        <section className="space-y-4">
          <h3 className="text-xl font-semibold text-[#F0E8D8]">Your Correlation Engine is warming up</h3>
          <p className="text-sm leading-relaxed text-[#F0E8D8]/90">
            As you complete assessments and update your profile, we&apos;ll start detecting patterns between your
            fitness, finances, and relationship quality.
          </p>
          <div className="rounded-lg bg-[#1a1512] border border-[#9a8f7e]/20 px-4 py-3">
            <p className="text-sm text-[#C4A064] font-medium">
              {Math.min(snapshotsCount, 3)} of 3 data points recorded
            </p>
            <div className="mt-2 h-2 rounded-full bg-[#0d0a08] overflow-hidden">
              <div
                className="h-full bg-[#C4A064] transition-all duration-500"
                style={{ width: `${Math.min(100, (Math.min(snapshotsCount, 3) / 3) * 100)}%` }}
              />
            </div>
          </div>
          <Link
            to="/vibe-checkups"
            className="inline-flex items-center justify-center rounded-lg bg-[#C4A064] px-4 py-2.5 text-sm font-semibold text-[#0d0a08] hover:bg-[#d4b074] transition-colors"
          >
            Complete a checkup
          </Link>
        </section>
      )}

      {!loading && !error && summary && summary.has_sufficient_data && tier === 'mid_tier' && (
        <section className="space-y-4">
          <h3 className="text-xl font-semibold text-[#F0E8D8]">We&apos;ve found a pattern in your data</h3>
          <p className="text-[#F0E8D8] text-sm leading-relaxed border-l-4 border-[#C4A064] pl-4 py-1">
            {summary.headline_insight}
          </p>
          <div className="space-y-3">
            {MID_PREVIEW_PLACEHOLDERS.map((c, i) => (
              <CorrelationInsightCard key={i} correlation={c} monthsApprox={monthsApprox} blurred />
            ))}
          </div>
          <Link
            to="/settings/upgrade"
            className="inline-flex items-center justify-center rounded-lg bg-[#C4A064] px-4 py-2.5 text-sm font-semibold text-[#0d0a08] hover:bg-[#d4b074] transition-colors"
          >
            See the full picture
          </Link>
        </section>
      )}

      {!loading && !error && summary && summary.has_sufficient_data && tier === 'professional' && (
        <section className="space-y-6">
          <div>
            <h3 className="text-xl font-semibold text-[#F0E8D8]">Your Life Correlation Report</h3>
            <p className="text-sm text-[#9a8f7e] mt-1">Based on {monthsApprox} months of your data</p>
          </div>

          <div className="rounded-lg border border-[#9a8f7e]/20 bg-[#1a1512]/60 p-3">
            <ScoreTimelineChart snapshots={snapshots ?? []} />
          </div>

          <div className="space-y-3">
            {sortedCorrelations.length === 0 ? (
              <p className="text-sm text-[#F0E8D8]/90">No strong patterns detected yet — keep tracking.</p>
            ) : (
              sortedCorrelations.map((c) => (
                <CorrelationInsightCard key={`${c.type}-${c.description.slice(0, 24)}`} correlation={c} monthsApprox={monthsApprox} />
              ))
            )}
          </div>

          <p className="text-xs leading-relaxed text-[#9a8f7e] pt-2 border-t border-[#9a8f7e]/20">
            These observations are based on your self-reported data. They reflect patterns, not predictions. Trust your
            own judgment.
          </p>
        </section>
      )}
    </div>
  );
};

export default CorrelationWidget;
