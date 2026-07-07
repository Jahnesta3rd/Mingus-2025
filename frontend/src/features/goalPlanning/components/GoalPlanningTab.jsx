import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../../hooks/useAuth';
import GoalForm from './GoalForm.jsx';
import GoalFormWithPrefill from './GoalFormWithPrefill.jsx';
import RecommendationsWithFeatures from './RecommendationsWithFeatures.jsx';
import useGoalAnalysis from '../hooks/useGoalAnalysis.js';
import { buildGoalAnalysisProfile } from '../utils/profileBuilder.js';
import { getGoalTypeOptions } from '../goalDefinitions/index.ts';
import { readStoredOnboardingPrefill } from '../../../hooks/useGoalFormPrefill.ts';
import { extractTrackedExpenseCategories } from '../utils/recommendationDisplayUtils.js';
import styles from './GoalPlanningTab.module.css';

const ALL_GOAL_TYPES = getGoalTypeOptions().map((option) => option.id);

/**
 * Goal planning tab — form entry, analysis pipeline, and recommendations.
 */
export default function GoalPlanningTab() {
  const { user, getAccessToken } = useAuth();
  const [userProfile, setUserProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState('');

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
    clearAnalysis,
  } = useGoalAnalysis(userProfile, { debounceMs: 0, getAccessToken });

  useEffect(() => {
    if (!user?.id) {
      setProfileLoading(false);
      return;
    }

    let cancelled = false;
    setProfileLoading(true);
    setProfileError('');

    buildGoalAnalysisProfile({ userId: user.id, getAccessToken })
      .then((profile) => {
        if (!cancelled) {
          setUserProfile(profile);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProfileError('Unable to load your profile. Using defaults for analysis.');
          setUserProfile({
            id: user.id,
            income: 5000,
            savings: 0,
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
  }, [user?.id]);

  const storedPrefill = useMemo(() => readStoredOnboardingPrefill(), []);
  const hasOnboardingPrefill = Boolean(storedPrefill?.prefill?.defaultValues);
  const trackedExpenseCategories = useMemo(
    () => extractTrackedExpenseCategories(storedPrefill?.onboardingData),
    [storedPrefill],
  );

  const [submittedGoal, setSubmittedGoal] = useState(null);

  const handleSubmit = useCallback((goal) => {
    if (!userProfile) {
      return;
    }
    setSubmittedGoal(goal);
    void analyzeGoal(goal);
  }, [analyzeGoal, userProfile]);

  const isAnalyzing = status === 'analyzing' || status === 'generating' || status === 'enriching';
  const showForm = status === 'idle' || status === 'error';
  const showRecommendations = status === 'complete' && recommendations?.paths?.length > 0;

  const progressLabel = useMemo(() => {
    if (progress) {
      return progress;
    }
    switch (status) {
      case 'analyzing':
        return 'Analyzing goal gaps and feasibility…';
      case 'generating':
        return 'Generating recommendation paths…';
      case 'enriching':
        return 'Adding jobs, gigs, and expense suggestions…';
      default:
        return 'Working on your plan…';
    }
  }, [progress, status]);

  if (profileLoading) {
    return (
      <div className={styles.loadingPanel}>
        <Loader2 size={32} className={styles.spinner} aria-hidden />
        <h3>Loading your profile</h3>
        <p>Preparing goal analysis with your financial data…</p>
      </div>
    );
  }

  return (
    <div className={styles.tab}>
      {profileError && (
        <div className={styles.profileNotice} role="status">
          {profileError}
        </div>
      )}

      {showForm && (
        hasOnboardingPrefill ? (
          <GoalFormWithPrefill
            onboardingData={storedPrefill?.onboardingData}
            goalTypes={ALL_GOAL_TYPES}
            onSubmit={handleSubmit}
            isSubmitting={isAnalyzing}
            submitSuccess={status === 'complete'}
            showAutoSubmit
            autoSubmitLabel="See My Recommendations"
          />
        ) : (
          <GoalForm
            goalTypes={ALL_GOAL_TYPES}
            onSubmit={handleSubmit}
            isSubmitting={isAnalyzing}
            submitSuccess={status === 'complete'}
          />
        )
      )}

      {isAnalyzing && (
        <div className={styles.loadingPanel} role="status" aria-live="polite">
          <Loader2 size={36} className={styles.spinner} aria-hidden />
          <h3>Mapping your path</h3>
          <p>{progressLabel}</p>
        </div>
      )}

      {(error || status === 'error') && (
        <div className={styles.errorPanel} role="alert">
          {error ?? 'Something went wrong while analyzing your goal. Please try again.'}
        </div>
      )}

      {showRecommendations && (
        <RecommendationsWithFeatures
          goal={submittedGoal ?? storedPrefill?.prefill?.defaultValues}
          analysis={goalAnalysis}
          recommendations={recommendations}
          jobSuggestions={jobSuggestions}
          gigSuggestions={gigSuggestions}
          expenseSuggestions={expenseSuggestions}
          selectedPathId={recommendations?.selectedPath}
          onSelectPath={selectRecommendationPath}
          onStartOver={clearAnalysis}
          trackedExpenseCategories={trackedExpenseCategories}
        />
      )}
    </div>
  );
}
