import React, { useMemo } from 'react';
import {
  getModulesForGoalType,
  getModulesForPath,
} from '../utils/moduleRegistry.js';
import {
  buildGoalSummaryText,
  formatCurrency,
  getPathEnrichment,
} from '../utils/recommendationDisplayUtils.js';
import RecommendationPathCard from './RecommendationPathCard.jsx';
import TimelineProjection from './TimelineProjection.jsx';
import styles from './RecommendationsWithFeatures.module.css';

/**
 * Displays recommendation paths with Mingus module deep-links and path-specific actions.
 *
 * @param {object} props
 * @param {object} [props.goal]
 * @param {object} [props.analysis] - From goalAnalyzer
 * @param {object} [props.goalAnalysis] - Alias for analysis (backward compatible)
 * @param {object} props.recommendations
 * @param {object} props.jobSuggestions
 * @param {object} props.gigSuggestions
 * @param {object} props.expenseSuggestions
 * @param {string} [props.selectedPathId]
 * @param {(pathId: string) => void} props.onSelectPath
 * @param {() => void} [props.onStartOver]
 * @param {string[]} [props.trackedExpenseCategories]
 */
export function RecommendationsWithFeatures({
  goal,
  analysis,
  goalAnalysis,
  recommendations,
  jobSuggestions,
  gigSuggestions,
  expenseSuggestions,
  selectedPathId,
  onSelectPath,
  onStartOver,
  trackedExpenseCategories = [],
}) {
  const resolvedAnalysis = analysis ?? goalAnalysis;
  const paths = recommendations?.paths ?? [];
  const activePathId = selectedPathId ?? recommendations?.selectedPath ?? paths[0]?.pathId ?? null;

  const goalSummary = useMemo(
    () => buildGoalSummaryText(goal, resolvedAnalysis),
    [goal, resolvedAnalysis],
  );

  const goalTypeModules = useMemo(
    () => getModulesForGoalType(resolvedAnalysis?.goalType ?? goal?.type ?? ''),
    [goal?.type, resolvedAnalysis?.goalType],
  );

  const pathCards = useMemo(() => paths.map((path) => {
    const pathModules = getModulesForPath(path.pathId);
    const goalSpecificSupporting = goalTypeModules.filter(
      (module) => !pathModules.core.some((core) => core.id === module.id),
    );
    const enrichment = getPathEnrichment(
      path.pathId,
      jobSuggestions,
      gigSuggestions,
      expenseSuggestions,
      trackedExpenseCategories,
    );

    return {
      path,
      modules: {
        core: pathModules.core,
        supporting: [...pathModules.supporting, ...goalSpecificSupporting]
          .filter((module, index, list) => list.findIndex((item) => item.id === module.id) === index)
          .filter((module) => !pathModules.core.some((core) => core.id === module.id)),
      },
      enrichment,
    };
  }), [paths, goalTypeModules, jobSuggestions, gigSuggestions, expenseSuggestions, trackedExpenseCategories]);

  if (paths.length === 0) {
    return null;
  }

  const gaps = resolvedAnalysis?.gaps ?? {};

  const handleTogglePath = (pathId) => {
    if (activePathId === pathId) {
      return;
    }
    onSelectPath(pathId);
  };

  return (
    <div className={styles.recommendations}>
      <header className={styles.header}>
        <h3>Your path to this goal</h3>
        <p className={styles.goalSummary}>{goalSummary}</p>
      </header>

      <div className={styles.analysisSummary}>
        <dl>
          <div>
            <dt>Monthly to save</dt>
            <dd>{formatCurrency(gaps.monthlyToSave)}</dd>
          </div>
          <div>
            <dt>Savings gap</dt>
            <dd>{formatCurrency(gaps.savingsGap)}</dd>
          </div>
          <div>
            <dt>Income gap (annual)</dt>
            <dd>{formatCurrency(gaps.incomeGap)}</dd>
          </div>
          <div>
            <dt>Feasibility</dt>
            <dd>{gaps.feasible ? 'On track with changes' : 'Needs a plan'}</dd>
          </div>
        </dl>
      </div>

      {paths.length > 0 && (
        <TimelineProjection
          goal={goal}
          paths={paths}
          analysis={resolvedAnalysis}
          currentSavings={resolvedAnalysis?.presentState?.savings}
          selectedPathId={activePathId}
          onSelectPath={onSelectPath}
        />
      )}

      <div className={styles.pathList} role="list" aria-label="Recommendation paths">
        {pathCards.map(({ path, modules, enrichment }) => (
          <RecommendationPathCard
            key={path.pathId}
            path={path}
            isExpanded={path.pathId === activePathId}
            isSelected={path.pathId === activePathId}
            onToggle={() => handleTogglePath(path.pathId)}
            modules={modules}
            jobs={enrichment.jobs}
            gigs={enrichment.gigs}
            expenses={enrichment.expenses}
            expensesFilteredOut={enrichment.allExpensesFiltered}
            trackedCategories={trackedExpenseCategories}
          />
        ))}
      </div>

      {onStartOver && (
        <div className={styles.actions}>
          <button type="button" className={styles.secondaryButton} onClick={onStartOver}>
            Plan another goal
          </button>
        </div>
      )}
    </div>
  );
}

export default RecommendationsWithFeatures;
