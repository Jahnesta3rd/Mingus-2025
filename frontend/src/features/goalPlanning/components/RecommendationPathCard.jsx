import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, ChevronUp, Calendar, TrendingUp } from 'lucide-react';
import {
  EXPENSE_CATEGORY_LABELS,
  formatCurrency,
  feasibilityClassName,
} from '../utils/recommendationDisplayUtils.js';
import styles from './RecommendationPathCard.module.css';

/**
 * @param {object} props
 * @param {object} props.path
 * @param {boolean} props.isExpanded
 * @param {boolean} props.isSelected
 * @param {() => void} props.onToggle
 * @param {{ core: object[], supporting: object[] }} props.modules
 * @param {object[]} [props.jobs]
 * @param {object[]} [props.gigs]
 * @param {object[]} [props.expenses]
 * @param {boolean} [props.expensesFilteredOut]
 * @param {string[]} [props.trackedCategories]
 */
export default function RecommendationPathCard({
  path,
  isExpanded,
  isSelected,
  onToggle,
  modules,
  jobs = [],
  gigs = [],
  expenses = [],
  expensesFilteredOut = false,
  trackedCategories = [],
}) {
  const feasibilityClass = styles[feasibilityClassName(path.feasibility)] ?? styles.feasibilityMedium;

  return (
    <article
      className={`${styles.card}${isSelected ? ` ${styles.cardSelected}` : ''}${isExpanded ? ` ${styles.cardExpanded}` : ''}`}
    >
      <button
        type="button"
        className={styles.headerButton}
        onClick={onToggle}
        aria-expanded={isExpanded}
      >
        <div className={styles.headerTop}>
          <div className={styles.titleBlock}>
            {path.mostRealistic && (
              <span className={styles.recommendedBadge}>⭐ Recommended</span>
            )}
            <h4 className={styles.title}>{path.title?.toUpperCase?.() ?? path.title}</h4>
            <p className={styles.description}>{path.description}</p>
          </div>
          <span className={styles.expandIcon} aria-hidden>
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </span>
        </div>

        <div className={styles.metrics}>
          <span className={styles.metric}>
            💰 <strong>{formatCurrency(path.monthlyBoost)}</strong>/month
          </span>
          <span className={styles.metricDivider}>|</span>
          <span className={styles.metric}>
            <Calendar size={14} aria-hidden />
            {' '}{path.timeline}
          </span>
          <span className={styles.metricDivider}>|</span>
          <span className={`${styles.metric} ${feasibilityClass}`}>
            <TrendingUp size={14} aria-hidden />
            {' '}{path.feasibility} feasibility
          </span>
        </div>
      </button>

      {isExpanded && (
        <div className={styles.body}>
          <div className={styles.columns}>
            <div className={styles.column}>
              <h5>Why this works</h5>
              <ul className={styles.list}>
                {(path.pros ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className={styles.column}>
              <h5>Trade-offs</h5>
              <ul className={styles.list}>
                {(path.cons ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          {(path.actionItems ?? []).length > 0 && (
            <div className={styles.block}>
              <h5>Action steps</h5>
              <ul className={styles.list}>
                {path.actionItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          <div className={styles.block}>
            <h5>Core Mingus modules</h5>
            <div className={styles.moduleGrid}>
              {modules.core.map((module) => (
                <Link key={module.id} to={module.path} className={styles.moduleCard}>
                  <strong>{module.name}</strong>
                  <span>{module.description}</span>
                  <span className={styles.moduleCta}>Open module →</span>
                </Link>
              ))}
            </div>
          </div>

          {modules.supporting.length > 0 && (
            <div className={styles.block}>
              <h5>Supporting modules</h5>
              <div className={styles.moduleGrid}>
                {modules.supporting.map((module) => (
                  <Link key={module.id} to={module.path} className={styles.moduleCard}>
                    <strong>{module.name}</strong>
                    <span>{module.description}</span>
                    <span className={styles.moduleCta}>Open module →</span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {(jobs.length > 0 || gigs.length > 0 || expenses.length > 0 || expensesFilteredOut) && (
            <div className={styles.block}>
              <h5>Action details</h5>

              {jobs.length > 0 && (
                <div className={styles.enrichmentGroup}>
                  <h6>Suggested roles</h6>
                  {jobs.slice(0, 3).map((job) => (
                    <div key={job.jobId ?? job.title} className={styles.enrichmentItem}>
                      <strong>{job.title}</strong>
                      <p>
                        {formatCurrency(job.expectedSalary)} expected
                        {job.incomeIncrease ? ` · +${formatCurrency(job.incomeIncrease)}/yr` : ''}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {gigs.length > 0 && (
                <div className={styles.enrichmentGroup}>
                  <h6>Side income ideas</h6>
                  {gigs.slice(0, 3).map((gig) => (
                    <div key={gig.gigId ?? gig.title} className={styles.enrichmentItem}>
                      <strong>{gig.title}</strong>
                      <p>
                        {gig.estimatedMonthlyIncome
                          ? `${formatCurrency(gig.estimatedMonthlyIncome)}/month`
                          : gig.description}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {expenses.length > 0 && (
                <div className={styles.enrichmentGroup}>
                  <h6>
                    Expense cuts
                    {trackedCategories.length > 0 && (
                      <span className={styles.trackedHint}>
                        {' '}(your tracked categories)
                      </span>
                    )}
                  </h6>
                  {expenses.slice(0, 4).map((cut) => {
                    const categoryKey = String(cut.categoryId ?? cut.category ?? '').toLowerCase();
                    const categoryLabel = EXPENSE_CATEGORY_LABELS[categoryKey] ?? cut.category ?? 'Expense';
                    return (
                      <div key={cut.suggestionId ?? cut.title ?? categoryKey} className={styles.enrichmentItem}>
                        <strong>{cut.title ?? categoryLabel}</strong>
                        <p>
                          Save {formatCurrency(cut.monthlySavings ?? cut.estimatedSavings ?? 0)}/month
                          {cut.description ? ` · ${cut.description}` : ''}
                        </p>
                      </div>
                    );
                  })}
                </div>
              )}

              {expensesFilteredOut && (
                <p className={styles.filteredNotice}>
                  Expense cuts are available, but none match categories you currently track.
                  Add recurring expenses in onboarding or the You tab to see personalized cuts.
                </p>
              )}
            </div>
          )}

          {(path.projections ?? []).length > 0 && (
            <div className={styles.block}>
              <h5>Timeline projection</h5>
              <div className={styles.projectionTableWrap}>
                <table className={styles.projectionTable}>
                  <thead>
                    <tr>
                      <th>Year</th>
                      <th>Cumulative savings</th>
                      <th>Goal reached</th>
                    </tr>
                  </thead>
                  <tbody>
                    {path.projections.slice(0, 5).map((row) => (
                      <tr key={row.year}>
                        <td>{row.year}</td>
                        <td>{formatCurrency(row.cumulativeSavings)}</td>
                        <td>{row.goalReached ? '✓ Yes' : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
