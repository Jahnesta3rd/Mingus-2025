import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../../hooks/useAuth';
import {
  buildGoalFormPrefill,
  persistOnboardingPrefill,
  type OnboardingModuleData,
} from '../../../hooks/useGoalFormPrefill.ts';
import GoalFormWithPrefill from '../../features/goalPlanning/components/GoalFormWithPrefill.jsx';
import RecommendationsWithFeatures from '../../features/goalPlanning/components/RecommendationsWithFeatures.jsx';
import useGoalAnalysis from '../../features/goalPlanning/hooks/useGoalAnalysis.js';
import { buildGoalAnalysisProfile } from '../../features/goalPlanning/utils/profileBuilder.js';
import { getGoalTypeOptions } from '../../features/goalPlanning/goalDefinitions/index.ts';
import { extractTrackedExpenseCategories } from '../../features/goalPlanning/utils/recommendationDisplayUtils.js';

const ALL_GOAL_TYPES = getGoalTypeOptions().map((option) => option.id);

export interface OnboardingGoalCompletionProps {
  onboardingData: OnboardingModuleData;
  onContinueToDashboard: () => void;
  onSkip: () => void;
}

export default function OnboardingGoalCompletion({
  onboardingData,
  onContinueToDashboard,
  onSkip,
}: OnboardingGoalCompletionProps) {
  const { user, getAccessToken } = useAuth();
  const [userProfile, setUserProfile] = useState<Record<string, unknown> | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [submittedGoal, setSubmittedGoal] = useState<object | null>(null);

  const trackedExpenseCategories = useMemo(
    () => extractTrackedExpenseCategories(onboardingData),
    [onboardingData],
  );

  const prefill = useMemo(
    () => buildGoalFormPrefill(onboardingData),
    [onboardingData],
  );

  const {
    status,
    goalAnalysis,
    recommendations,
    jobSuggestions,
    gigSuggestions,
    expenseSuggestions,
    error,
    progress,
    analyzeGoal,
    selectRecommendationPath,
  } = useGoalAnalysis(userProfile, { debounceMs: 0, getAccessToken });

  useEffect(() => {
    persistOnboardingPrefill(onboardingData);
  }, [onboardingData]);

  useEffect(() => {
    if (!user?.id) {
      setProfileLoading(false);
      return;
    }

    let cancelled = false;
    buildGoalAnalysisProfile({ userId: user.id, getAccessToken })
      .then((profile) => {
        if (!cancelled) {
          setUserProfile(profile);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setUserProfile({
            id: user.id,
            income: prefill.annualIncome ? Math.round((prefill.annualIncome ?? 0) / 12) : 5000,
            savings: prefill.currentSavings ?? 0,
            expenses: 3500,
            jobTitle: 'Professional',
            industry: 'General',
            skills: ['Communication'],
            availableHours: 10,
          });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setProfileLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [prefill.annualIncome, prefill.currentSavings, user?.id]);

  useEffect(() => {
    if (prefill.hasGoalInterest && prefill.suggestedGoalType) {
      setShowGoalForm(true);
    }
  }, [prefill.hasGoalInterest, prefill.suggestedGoalType]);

  const handleSubmit = useCallback((goal: object) => {
    if (!userProfile) {
      return;
    }
    setSubmittedGoal(goal);
    void analyzeGoal(goal);
  }, [analyzeGoal, userProfile]);

  const isAnalyzing = status === 'analyzing' || status === 'generating' || status === 'enriching';
  const showRecommendations = status === 'complete' && (recommendations?.paths?.length ?? 0) > 0;

  if (profileLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#5B2D8E]" aria-hidden />
        <p className="mt-4 text-sm text-[#64748B]">Preparing your personalized path…</p>
      </div>
    );
  }

  if (showRecommendations) {
    return (
      <div className="space-y-6 pb-8">
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
          <h1 className="font-serif text-2xl font-semibold text-[#1E293B]">Your personalized path</h1>
          <p className="mt-2 text-sm text-[#64748B]">
            Based on your onboarding answers, here are the most realistic ways to reach your goal.
          </p>
        </div>
        <RecommendationsWithFeatures
          goal={submittedGoal ?? undefined}
          analysis={goalAnalysis}
          recommendations={recommendations}
          jobSuggestions={jobSuggestions}
          gigSuggestions={gigSuggestions}
          expenseSuggestions={expenseSuggestions}
          selectedPathId={recommendations?.selectedPath}
          onSelectPath={selectRecommendationPath}
          trackedExpenseCategories={trackedExpenseCategories}
        />
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onContinueToDashboard}
            className="min-h-11 rounded-lg bg-[#5B2D8E] px-5 py-2 text-sm font-semibold text-white hover:bg-[#4B2474]"
          >
            Continue to dashboard
          </button>
        </div>
      </div>
    );
  }

  if (showGoalForm || isAnalyzing) {
    return (
      <div className="space-y-6 pb-8">
        <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
          <h1 className="font-serif text-2xl font-semibold text-[#1E293B]">Ready to see your personalized path?</h1>
          <p className="mt-2 text-sm text-[#64748B]">
            We captured details from onboarding. Refine anything below, then get your recommendations.
          </p>
        </div>

        {!isAnalyzing && (
          <GoalFormWithPrefill
            onboardingData={onboardingData}
            goalTypes={ALL_GOAL_TYPES}
            onSubmit={handleSubmit}
            isSubmitting={isAnalyzing}
            showAutoSubmit
            autoSubmitLabel="See My Recommendations"
          />
        )}

        {isAnalyzing && (
          <div className="rounded-xl border border-[#E2E8F0] bg-white p-8 text-center">
            <Loader2 className="mx-auto h-9 w-9 animate-spin text-[#5B2D8E]" aria-hidden />
            <h3 className="mt-4 font-serif text-xl text-[#1E293B]">Mapping your path</h3>
            <p className="mt-2 text-sm text-[#64748B]">{progress ?? 'Analyzing your goal…'}</p>
          </div>
        )}

        {(error || status === 'error') && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            {error ?? 'Unable to analyze your goal. Please try again.'}
          </div>
        )}

        <button
          type="button"
          onClick={onSkip}
          className="text-sm font-medium text-[#64748B] underline-offset-2 hover:text-[#5B2D8E] hover:underline"
        >
          Skip for now and go to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <h1 className="font-serif text-2xl font-semibold text-[#1E293B]">Set a financial goal?</h1>
      <p className="mt-2 text-sm text-[#64748B]">
        Mingus can map a personalized path to a home, car, business, and more. You can always do this later from the Goals tab.
      </p>
      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={() => setShowGoalForm(true)}
          className="min-h-11 rounded-lg bg-[#5B2D8E] px-5 py-2 text-sm font-semibold text-white hover:bg-[#4B2474]"
        >
          Set a financial goal
        </button>
        <button
          type="button"
          onClick={onSkip}
          className="min-h-11 rounded-lg border border-[#E2E8F0] px-5 py-2 text-sm font-semibold text-[#1E293B] hover:bg-[#F8FAFC]"
        >
          Skip for now
        </button>
      </div>
    </div>
  );
}
