import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Home, TrendingDown } from 'lucide-react';
import {
  dismissCard,
  getAssessment,
  getShouldRecommend,
  type IndependenceAssessment,
  type IndependenceRecommendation,
} from '../api/independenceCostAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface IndependenceCostCardProps {
  onPurchaseClick: () => void;
  onExploreSideIncome?: (params: {
    monthlyGap: number;
    startupCostNeeded: number;
    timelineMonths: number;
    partnerId: string;
    iccAssessmentId: string;
  }) => void;
  className?: string;
}

function monthsToSaveStartup(startupCost: number, gap: number): number | null {
  if (!Number.isFinite(startupCost) || !Number.isFinite(gap) || gap <= 0) {
    return null;
  }
  return Math.ceil(startupCost / gap);
}

function getOtherMonthly(monthlyCosts: IndependenceAssessment['monthly_costs']) {
  return monthlyCosts.other_essentials ?? monthlyCosts.other ?? 0;
}

function getVibeScores(vibeData?: IndependenceAssessment['vibe_data']): number[] {
  return vibeData?.scores_12_weeks ?? vibeData?.emotional_scores ?? [];
}

function getStartupTotal(startupCosts: IndependenceAssessment['startup_costs']): number {
  if (startupCosts.total_startup_cost != null) {
    return startupCosts.total_startup_cost;
  }
  if (startupCosts.total_with_car != null) {
    return startupCosts.total_with_car;
  }
  if (startupCosts.total_without_car != null) {
    return startupCosts.total_without_car;
  }
  return 0;
}

function getCarStartupTotal(startupCosts: IndependenceAssessment['startup_costs']): number {
  const transport = startupCosts.transportation;
  if (transport) {
    return (
      (transport.car_purchase ?? 0) +
      (transport.car_insurance_deposit ?? 0) +
      (transport.registration ?? 0) +
      (transport.maintenance_fund ?? 0)
    );
  }
  return (
    (startupCosts.car_purchase ?? 0) +
    (startupCosts.car_insurance_deposit ?? 0) +
    (startupCosts.registration ?? 0) +
    (startupCosts.car_maintenance_fund ?? 0)
  );
}

export default function IndependenceCostCard({
  onPurchaseClick,
  onExploreSideIncome,
  className = '',
}: IndependenceCostCardProps) {
  const { getAccessToken } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isDismissed, setIsDismissed] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [recommendation, setRecommendation] = useState<IndependenceRecommendation | null>(null);
  const [assessment, setAssessment] = useState<IndependenceAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [breakdownError, setBreakdownError] = useState<string | null>(null);
  const [breakdownLoading, setBreakdownLoading] = useState(false);
  const [dismissError, setDismissError] = useState<string | null>(null);
  const [dismissBusy, setDismissBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const payload = await getShouldRecommend({ getAccessToken });
        if (cancelled) return;
        if (!payload.should_recommend) {
          setRecommendation(null);
          setIsLoading(false);
          return;
        }
        setRecommendation(payload);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load recommendation');
        setRecommendation(null);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  const savingsMonths = useMemo(() => {
    if (!recommendation) return null;
    return monthsToSaveStartup(
      recommendation.startup_cost ?? 0,
      recommendation.gap ?? 0,
    );
  }, [recommendation]);

  const handleExploreSideIncome = useCallback(() => {
    if (!recommendation || !onExploreSideIncome) return;
    const gap = recommendation.gap ?? 0;
    const startupCost = recommendation.startup_cost ?? 0;
    const partnerId = recommendation.partner_id;
    const iccAssessmentId = recommendation.icc_assessment_id;
    if (gap <= 0 || !partnerId || !iccAssessmentId) return;
    onExploreSideIncome({
      monthlyGap: gap,
      startupCostNeeded: startupCost,
      timelineMonths: savingsMonths ?? 12,
      partnerId,
      iccAssessmentId,
    });
  }, [onExploreSideIncome, recommendation, savingsMonths]);

  const handleDismiss = useCallback(async () => {
    if (dismissBusy) return;
    setDismissBusy(true);
    setDismissError(null);
    try {
      await dismissCard({ getAccessToken });
      setIsDismissed(true);
    } catch (err) {
      setDismissError(
        err instanceof Error ? err.message : 'Could not dismiss this card. Please try again.',
      );
    } finally {
      setDismissBusy(false);
    }
  }, [dismissBusy, getAccessToken]);

  const handleToggleBreakdown = useCallback(async () => {
    if (!recommendation?.partner_id) return;

    const nextExpanded = !isExpanded;
    setIsExpanded(nextExpanded);
    if (!nextExpanded) return;

    if (assessment) {
      setBreakdownError(null);
      return;
    }

    setBreakdownLoading(true);
    setBreakdownError(null);
    try {
      const payload = await getAssessment(recommendation.partner_id, { getAccessToken });
      setAssessment(payload);
    } catch (err) {
      setBreakdownError(
        err instanceof Error ? err.message : 'Failed to load detailed breakdown.',
      );
      setIsExpanded(true);
    } finally {
      setBreakdownLoading(false);
    }
  }, [assessment, getAccessToken, isExpanded, recommendation?.partner_id]);

  if (isLoading) {
    return (
      <div
        className={`mx-auto my-4 flex max-w-[600px] items-center justify-center rounded-2xl border-2 border-orange-200 bg-white p-6 shadow-sm ${className}`}
        role="status"
        aria-live="polite"
        aria-label="Loading independence cost recommendation"
      >
        <div
          className="h-8 w-8 animate-spin rounded-full border-2 border-orange-200 border-t-orange-500"
          aria-hidden
        />
      </div>
    );
  }

  if (error || isDismissed || !recommendation?.should_recommend) {
    return null;
  }

  const partnerName = recommendation.partner_name ?? 'your partner';
  const city = recommendation.city ?? 'your area';
  const monthlyCost = recommendation.monthly_cost ?? 0;
  const currentCost = recommendation.current_cost ?? 0;
  const gap = recommendation.gap ?? 0;
  const startupCost = recommendation.startup_cost ?? 0;
  const ctaLabel = recommendation.cta ?? 'Explore RFR Module';

  const vibeScores = getVibeScores(assessment?.vibe_data);
  const carStartupTotal = assessment ? getCarStartupTotal(assessment.startup_costs) : 0;

  return (
    <section
      role="region"
      aria-label="Independence cost recommendation"
      className={`mx-auto my-4 w-full max-w-[600px] rounded-2xl border-2 border-orange-200 bg-white p-6 shadow-sm ${className}`}
      aria-labelledby="independence-cost-card-title"
    >
      <div className="mb-4 flex items-start gap-3">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-orange-50 text-orange-600"
          aria-hidden
        >
          <Home size={20} />
          <TrendingDown size={16} className="-ml-1" />
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-orange-600">
            Independence planning
          </p>
          <h2 id="independence-cost-card-title" className="text-lg font-semibold text-gray-900">
            Living independently in {city}
          </h2>
        </div>
      </div>

      <p className="text-sm leading-relaxed text-gray-700">
        Over 3 months, your energy with <strong>{partnerName}</strong> has been steadily
        declining.
      </p>
      <p className="mt-2 text-sm leading-relaxed text-gray-700">
        If independence becomes necessary, here&apos;s what you&apos;d need to establish it in{' '}
        <strong>{city}</strong>:
      </p>

      <div className="mt-4 rounded-xl border border-orange-100 bg-orange-50/60 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-600">
          Upfront costs
        </h3>
        <p className="mt-1 text-2xl font-bold text-gray-900">{formatCurrency(startupCost)}</p>
        <p className="text-sm text-gray-600">Move out &amp; set up</p>
        {savingsMonths != null ? (
          <p className="mt-1 text-sm text-gray-500">
            Could save this in ~{savingsMonths} month{savingsMonths === 1 ? '' : 's'} at current
            pace
          </p>
        ) : null}
      </div>

      <div className="mt-4 rounded-xl border border-gray-100 bg-gray-50 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-600">
          Monthly costs
        </h3>
        <div className="mt-2 space-y-1 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">Living alone</span>
            <span className="font-medium text-gray-900">{formatCurrency(monthlyCost)}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">You&apos;re paying now</span>
            <span className="font-medium text-gray-900">{formatCurrency(currentCost)}</span>
          </div>
          <div className="flex items-center justify-between gap-4 border-t border-gray-200 pt-2">
            <span className="flex items-center gap-1 font-semibold text-gray-900">
              <TrendingDown size={16} className="text-orange-600" aria-hidden />
              Additional gap
            </span>
            <span className="text-xl font-bold text-orange-600">{formatCurrency(gap)}</span>
          </div>
        </div>
      </div>

      {recommendation.message ? (
        <p className="mt-3 text-sm text-gray-600">{recommendation.message}</p>
      ) : null}

      <div className="mt-5 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={onPurchaseClick}
          className="flex-1 rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
        >
          {ctaLabel}
        </button>
        <button
          type="button"
          onClick={handleDismiss}
          disabled={dismissBusy}
          className="rounded-lg px-4 py-2.5 text-sm font-medium text-gray-500 underline hover:text-gray-700 disabled:opacity-60"
        >
          Dismiss
        </button>
      </div>

      {onExploreSideIncome && gap > 0 ? (
        <button
          type="button"
          onClick={handleExploreSideIncome}
          className="mt-3 w-full rounded-lg border border-orange-200 bg-orange-50 px-4 py-2.5 text-sm font-semibold text-orange-800 hover:bg-orange-100"
        >
          Explore side income to close your {formatCurrency(gap)} gap →
        </button>
      ) : null}

      {dismissError ? (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {dismissError}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleToggleBreakdown}
        aria-expanded={isExpanded}
        aria-controls="independence-cost-breakdown"
        className="mt-4 flex w-full items-center justify-center gap-1 text-sm font-medium text-orange-700 hover:text-orange-800"
      >
        <span aria-hidden>{isExpanded ? '▲' : '▼'}</span>
        See detailed breakdown
      </button>

      {isExpanded ? (
        <div id="independence-cost-breakdown" className="mt-4 border-t border-gray-100 pt-4">
          {breakdownLoading ? (
            <div className="flex justify-center py-4" role="status" aria-live="polite">
              <div
                className="h-6 w-6 animate-spin rounded-full border-2 border-orange-200 border-t-orange-500"
                aria-hidden
              />
            </div>
          ) : null}

          {breakdownError ? (
            <p className="text-sm text-red-600" role="alert">
              {breakdownError}
            </p>
          ) : null}

          {assessment ? (
            <div className="space-y-5 text-sm">
              <div>
                <h4 className="font-semibold text-gray-900">Startup costs breakdown</h4>
                <ul className="mt-2 space-y-1 text-gray-700">
                  <li className="flex justify-between gap-4">
                    <span>Moving &amp; rental deposits</span>
                    <span>
                      {formatCurrency(
                        (assessment.startup_costs.moving ?? 0) +
                          (assessment.startup_costs.rental_deposits ?? 0),
                      )}
                    </span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Furniture &amp; appliances</span>
                    <span>
                      {formatCurrency(
                        (assessment.startup_costs.furniture_basics ?? 0) +
                          (assessment.startup_costs.kitchen_appliances ?? 0) +
                          (assessment.startup_costs.household_items ?? 0),
                      )}
                    </span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Emergency fund</span>
                    <span>{formatCurrency(assessment.startup_costs.emergency_fund ?? 0)}</span>
                  </li>
                  {carStartupTotal > 0 ? (
                    <li className="flex justify-between gap-4">
                      <span>Car (if needed)</span>
                      <span>{formatCurrency(carStartupTotal)}</span>
                    </li>
                  ) : null}
                  <li className="flex justify-between gap-4 border-t border-gray-200 pt-1 font-semibold text-gray-900">
                    <span>Total</span>
                    <span>{formatCurrency(getStartupTotal(assessment.startup_costs))}</span>
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900">Monthly costs breakdown</h4>
                <ul className="mt-2 space-y-1 text-gray-700">
                  <li className="flex justify-between gap-4">
                    <span>Housing</span>
                    <span>{formatCurrency(assessment.monthly_costs.housing ?? 0)}</span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Food</span>
                    <span>{formatCurrency(assessment.monthly_costs.food ?? 0)}</span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Utilities</span>
                    <span>{formatCurrency(assessment.monthly_costs.utilities ?? 0)}</span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Transportation</span>
                    <span>{formatCurrency(assessment.monthly_costs.transportation ?? 0)}</span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Phone / Internet</span>
                    <span>{formatCurrency(assessment.monthly_costs.phone_internet ?? 0)}</span>
                  </li>
                  <li className="flex justify-between gap-4">
                    <span>Other essentials</span>
                    <span>{formatCurrency(getOtherMonthly(assessment.monthly_costs))}</span>
                  </li>
                  <li className="flex justify-between gap-4 border-t border-gray-200 pt-1 font-semibold text-gray-900">
                    <span>Total</span>
                    <span>{formatCurrency(assessment.monthly_costs.total_monthly ?? 0)}</span>
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900">Vibe data</h4>
                <p className="mt-1 text-gray-700">Steady decline over 3 months</p>
                {vibeScores.length > 0 ? (
                  <p className="mt-1 text-xs text-gray-500">
                    Emotional scores (12 weeks): {vibeScores.join(' → ')}
                  </p>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
