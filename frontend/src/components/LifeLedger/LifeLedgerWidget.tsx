import React, { useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getAuthHeadersJson, useLifeLedger } from '../../hooks/useLifeLedger';
import LifeLedgerInsight from './LifeLedgerInsight';
import ModuleScoreCard, { LifeLedgerScoreRing, lifeLedgerScoreColor } from './ModuleScoreCard';
import TenYearProjection from './TenYearProjection';

function assessmentsComplete(profile: {
  vibe_score: number | null;
  body_score: number | null;
  roof_score: number | null;
  vehicle_score: number | null;
}): number {
  return [profile.vibe_score, profile.body_score, profile.roof_score, profile.vehicle_score].filter(
    (s) => s != null
  ).length;
}

export interface LifeLedgerWidgetProps {
  className?: string;
  /** First dashboard instance should set true (default) for scroll targets; omit on duplicate mounts. */
  anchorSectionId?: boolean;
}

const LifeLedgerWidget: React.FC<LifeLedgerWidgetProps> = ({
  className = '',
  anchorSectionId = true,
}) => {
  const { user, isAuthenticated } = useAuth();
  const { profile, insights, loading, error, refetch } = useLifeLedger(isAuthenticated);

  const tier: 'budget' | 'mid_tier' | 'professional' =
    user?.is_beta === true || user?.tier === 'professional'
      ? 'professional'
      : user?.tier === 'mid_tier'
        ? 'mid_tier'
        : 'budget';
  const isProfessional = tier === 'professional';
  const isBudget = tier === 'budget';

  const handleDismissInsight = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(`/api/life-ledger/dismiss-insight/${id}`, {
          method: 'POST',
          credentials: 'include',
          headers: getAuthHeadersJson(),
        });
        if (res.ok) await refetch();
      } catch (e) {
        console.error('Dismiss insight failed', e);
      }
    },
    [refetch]
  );

  const complete = profile ? assessmentsComplete(profile) : 0;
  const topInsights = insights.filter((i) => !i.dismissed).slice(0, 3);
  const score = profile?.life_ledger_score ?? 0;

  return (
    <div
      {...(anchorSectionId ? { id: 'life-ledger-dashboard-section' } : {})}
      className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6 ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-gray-900">Life Ledger Score</h2>
          {!loading && profile && (
            <p
              className="text-4xl sm:text-5xl font-bold tabular-nums mt-2"
              style={{ color: lifeLedgerScoreColor(score) }}
            >
              {score}
            </p>
          )}
          <p className="text-sm text-gray-600 mt-1 max-w-xl">
            Composite view across relationship, health, housing, and vehicle assessments.
          </p>
        </div>
        {!loading && profile && (
          <div className="flex flex-col items-center gap-2 flex-shrink-0 mx-auto sm:mx-0">
            <LifeLedgerScoreRing score={score} size={120} />
            <p className="text-xs text-gray-500 text-center max-w-[140px]">
              Based on {complete} of 4 assessments complete
            </p>
          </div>
        )}
      </div>

      {loading && (
        <div className="animate-pulse space-y-4">
          <div className="h-28 bg-gray-100 rounded-lg" />
          <div className="grid grid-cols-2 gap-3">
            <div className="h-36 bg-gray-100 rounded-xl" />
            <div className="h-36 bg-gray-100 rounded-xl" />
            <div className="h-36 bg-gray-100 rounded-xl" />
            <div className="h-36 bg-gray-100 rounded-xl" />
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {!loading && profile && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <ModuleScoreCard
              module="vibe"
              label="Vibe"
              icon="💑"
              score={profile.vibe_score}
              actionUrl="/dashboard/vibe-checkups"
            />
            <ModuleScoreCard
              module="body"
              label="Body"
              icon="💪"
              score={profile.body_score}
              actionUrl="/body-check"
            />
            <ModuleScoreCard
              module="roof"
              label="Roof"
              icon="🏠"
              score={isBudget ? null : profile.roof_score}
              actionUrl="/roof-check"
              locked={isBudget}
            />
            <ModuleScoreCard
              module="vehicle"
              label="Vehicle"
              icon="🚗"
              score={isBudget ? null : profile.vehicle_score}
              actionUrl="/vehicle-check"
              locked={isBudget}
            />
          </div>

          {isProfessional && <TenYearProjection profile={profile} />}

          {tier === 'mid_tier' && (
            <p className="text-xs text-gray-600 text-center">
              <Link to="/checkout" className="font-semibold text-violet-600 hover:underline">
                Upgrade to Professional
              </Link>{' '}
              for your 10-year life cost projection and full financial depth.
            </p>
          )}

          {topInsights.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Insights</h3>
              <div className="space-y-3">
                {topInsights.map((ins) => (
                  <LifeLedgerInsight
                    key={ins.id}
                    insight={{
                      id: ins.id,
                      module: ins.module,
                      message: ins.message,
                      action_url: ins.action_url,
                    }}
                    onDismiss={handleDismissInsight}
                  />
                ))}
              </div>
            </div>
          )}

          {complete < 4 && (
            <div className="rounded-lg bg-violet-50 border border-violet-100 px-4 py-3 text-center">
              <p className="text-sm font-medium text-violet-900">
                Complete all 4 assessments for your full Life Ledger Score
              </p>
              {isBudget && (
                <p className="text-xs text-violet-800/90 mt-1">
                  Upgrade to unlock Roof and Vehicle modules.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default LifeLedgerWidget;
