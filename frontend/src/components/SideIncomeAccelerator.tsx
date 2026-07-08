import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { createIccToDf1Handoff } from '../api/integrationAPI';
import {
  getSideIncomeRecommendations,
  type SideIncomeJob,
  type SideIncomeResponse,
} from '../api/sideIncomeAPI';
import { formatCurrency } from '../features/goalPlanning/utils/recommendationDisplayUtils.js';
import { useAuth } from '../hooks/useAuth';

export interface SideIncomeAcceleratorProps {
  monthlyGap: number;
  startupCostNeeded: number;
  timelineMonths: number;
  iccAssessmentId: string;
  partnerId: string;
  onJobSelected?: (job: SideIncomeJob) => void;
  className?: string;
}

const HOUR_OPTIONS = [5, 10, 15, 20] as const;
const DEFAULT_HANDOFF_URL = '/dashboard/tools?tab=debt&subTab=second-job';

function formatJobType(type: string): string {
  const labels: Record<string, string> = {
    gig: 'Gig',
    part_time: 'Part-time',
    freelance: 'Freelance',
    contract: 'Contract',
  };
  return labels[type] ?? type;
}

export default function SideIncomeAccelerator({
  monthlyGap,
  startupCostNeeded,
  timelineMonths,
  iccAssessmentId,
  partnerId,
  onJobSelected,
  className = '',
}: SideIncomeAcceleratorProps) {
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();
  const [step, setStep] = useState<'intake' | 'results' | 'selected'>('intake');
  const [isLoading, setIsLoading] = useState(false);
  const [isHandoffLoading, setIsHandoffLoading] = useState(false);
  const [hoursPerWeekAvailable, setHoursPerWeekAvailable] = useState<number>(10);
  const [recommendations, setRecommendations] = useState<SideIncomeResponse | null>(null);
  const [selectedJob, setSelectedJob] = useState<SideIncomeJob | null>(null);
  const [handoffMessage, setHandoffMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await getSideIncomeRecommendations(
        {
          monthlyGap,
          hoursPerWeekAvailable,
          startupCostNeeded,
          timelineMonths,
        },
        { getAccessToken },
      );
      setRecommendations(payload);
      setStep('results');
    } catch (err) {
      setRecommendations(null);
      setError(
        err instanceof Error ? err.message : 'Could not load side income recommendations.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [
    getAccessToken,
    hoursPerWeekAvailable,
    monthlyGap,
    startupCostNeeded,
    timelineMonths,
  ]);

  const handleSelectJob = useCallback(
    async (job: SideIncomeJob) => {
      setIsHandoffLoading(true);
      setError(null);
      try {
        const handoff = await createIccToDf1Handoff(
          {
            iccAssessmentId,
            personId: partnerId,
            selectedJob: job.title,
            df1JobType: String(job.type),
            targetMonthlyIncome: job.monthly_income,
            gapCoveragePct: job.icc_impact.gap_coverage_pct,
          },
          { getAccessToken },
        );
        setSelectedJob(job);
        setHandoffMessage(handoff.message);
        setStep('selected');
        onJobSelected?.(job);
        navigate(handoff.handoff_url || DEFAULT_HANDOFF_URL);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Could not save your side income selection. Please try again.',
        );
      } finally {
        setIsHandoffLoading(false);
      }
    },
    [getAccessToken, iccAssessmentId, navigate, onJobSelected, partnerId],
  );

  if (step === 'selected' && selectedJob) {
    return (
      <section
        className={`rounded-2xl border border-orange-200 bg-white p-6 shadow-sm ${className}`}
        aria-label="Side income selection confirmation"
      >
        <h2 className="text-lg font-semibold text-gray-900">You selected {selectedJob.title}</h2>
        {handoffMessage ? (
          <p className="mt-2 text-sm text-gray-600">{handoffMessage}</p>
        ) : null}
        <p className="mt-2 text-sm text-gray-600">
          Estimated income: {formatCurrency(selectedJob.monthly_income)}/month at{' '}
          {selectedJob.hours_per_week} hours/week.
        </p>
        <p className="mt-1 text-sm text-gray-600">First step: {selectedJob.first_step}</p>
        <button
          type="button"
          onClick={() => navigate(DEFAULT_HANDOFF_URL)}
          className="mt-4 rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-700"
        >
          Continue to setup
        </button>
      </section>
    );
  }

  if (step === 'results') {
    return (
      <section
        className={`rounded-2xl border border-orange-200 bg-white p-6 shadow-sm ${className}`}
        aria-label="Side income recommendations"
      >
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Side income to close your gap</h2>
          <p className="mt-1 text-sm text-gray-600">
            You need {formatCurrency(monthlyGap)}/month with a {timelineMonths}-month timeline and{' '}
            {formatCurrency(startupCostNeeded)} startup goal.
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center gap-2 py-8" role="status">
            <Loader2 className="h-5 w-5 animate-spin text-orange-600" aria-hidden />
            <span className="text-sm text-gray-600">Finding side income options...</span>
          </div>
        ) : null}

        {error ? (
          <div className="rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-700" role="alert">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => void fetchRecommendations()}
              className="mt-3 rounded-lg bg-orange-600 px-3 py-2 text-sm font-medium text-white"
            >
              Retry
            </button>
          </div>
        ) : null}

        {recommendations ? (
          <div className="grid gap-4 lg:grid-cols-3">
            {recommendations.matches.map((job, index) => {
              const isTop = index === 0;
              const impact = job.icc_impact;
              const combo = job.interim_housing_combo;
              return (
                <article
                  key={`${job.title}-${index}`}
                  className={`rounded-xl border p-4 ${
                    isTop ? 'border-orange-300 bg-orange-50/40' : 'border-gray-200 bg-white'
                  }`}
                >
                  {isTop ? (
                    <span className="mb-2 inline-flex rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800">
                      Best match
                    </span>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{job.title}</h3>
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                      {formatJobType(String(job.type))}
                    </span>
                  </div>
                  <p className="mt-2 text-xl font-bold text-orange-600">
                    {formatCurrency(job.monthly_income)}/month
                  </p>
                  <p className="text-sm text-gray-600">{job.hours_per_week} hours/week</p>
                  <p className="mt-1 text-sm text-gray-600">{job.schedule_fit}</p>
                  <p className="mt-2 text-sm text-gray-700">{job.why_it_fits}</p>

                  <div className="mt-4 rounded-lg border border-orange-100 bg-orange-50 p-3 text-sm">
                    <p className="font-semibold text-gray-900">ICC impact</p>
                    <p className="mt-1 text-gray-700">
                      Covers {impact.gap_coverage_pct.toFixed(0)}% of your{' '}
                      {formatCurrency(monthlyGap)}/month gap
                    </p>
                    <p className="mt-1 flex items-center gap-1 text-gray-700">
                      {impact.closes_monthly_gap ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" aria-hidden />
                      ) : null}
                      Timeline impact: {timelineMonths} →{' '}
                      {Math.max(0, Math.round(impact.timeline_acceleration_months))} months
                    </p>
                    {combo.months_to_startup_with_roommate != null ? (
                      <p className="mt-1 text-gray-700">
                        With roommate housing: ~
                        {Math.ceil(combo.months_to_startup_with_roommate)} months to startup
                      </p>
                    ) : null}
                  </div>

                  <button
                    type="button"
                    disabled={isHandoffLoading}
                    onClick={() => void handleSelectJob(job)}
                    className="mt-4 w-full rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-700 disabled:opacity-60"
                  >
                    {isHandoffLoading ? 'Saving selection...' : 'Get Started'}
                  </button>
                </article>
              );
            })}
          </div>
        ) : null}
      </section>
    );
  }

  return (
    <section
      className={`rounded-2xl border border-orange-200 bg-white p-6 shadow-sm ${className}`}
      aria-label="Side income intake"
    >
      <h2 className="text-lg font-semibold text-gray-900">How much time can you spare?</h2>
      <p className="mt-1 text-sm text-gray-600">
        We&apos;ll match side income ideas to your {formatCurrency(monthlyGap)}/month independence
        gap.
      </p>

      <fieldset className="mt-4">
        <legend className="mb-2 text-sm font-medium text-gray-700">
          Hours per week available
        </legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {HOUR_OPTIONS.map((hours) => (
            <label
              key={hours}
              className={`cursor-pointer rounded-lg border px-3 py-2 text-center text-sm ${
                hoursPerWeekAvailable === hours
                  ? 'border-orange-500 bg-orange-50 text-orange-800'
                  : 'border-gray-200 text-gray-700'
              }`}
            >
              <input
                type="radio"
                name="hours-per-week"
                value={hours}
                checked={hoursPerWeekAvailable === hours}
                onChange={() => setHoursPerWeekAvailable(hours)}
                className="sr-only"
              />
              {hours === 20 ? '20+ hrs' : `${hours} hrs`}
            </label>
          ))}
        </div>
      </fieldset>

      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        disabled={isLoading}
        onClick={() => void fetchRecommendations()}
        className="mt-5 w-full rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-700 disabled:opacity-60"
      >
        {isLoading ? 'Finding options...' : 'See side income options'}
      </button>
    </section>
  );
}
