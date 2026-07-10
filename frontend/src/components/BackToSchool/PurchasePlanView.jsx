import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import EarningsProgressBar from './EarningsProgressBar';
import JobDependencyWarning from './JobDependencyWarning';
import JobPickerModal from './JobPickerModal';
import Tier2PurchaseReminder from './Tier2PurchaseReminder';
import Tier2ReminderBanner from './Tier2ReminderBanner';
import TierCard from './TierCard';
import TimelineBreakdown from './TimelineBreakdown';
import { useJobCommitment } from './hooks/useJobCommitment';
import { usePurchasePlan } from './hooks/usePurchasePlan';
import { useTier2Reminder } from './hooks/useTier2Reminder';
import styles from './PurchasePlanView.module.css';

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

/**
 * BTS3 — displays the BTS2 tiered purchase plan (+ BTS7 job integration).
 *
 * @param {{ sessionId?: string }} props
 */
export default function PurchasePlanView({ sessionId: sessionIdProp }) {
  const { sessionId: sessionIdParam } = useParams();
  const sessionId = sessionIdProp || sessionIdParam;
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();
  const { plan, loading, error } = usePurchasePlan(sessionId, { getAccessToken });
  const {
    commitment,
    tier2Status,
    loading: jobLoading,
    error: jobError,
    createCommitment,
    recordDecision,
    setError: setJobError,
  } = useJobCommitment(sessionId, { getAccessToken });

  const {
    shouldShow: showTier2Banner,
    dismissReminder,
    loading: dismissLoading,
    reminder: tier2Reminder,
  } = useTier2Reminder(sessionId, {
    getAccessToken,
    tier2Date: plan?.tier2?.purchaseBy,
  });

  const [expandedTier, setExpandedTier] = useState(1);
  const [showJobPicker, setShowJobPicker] = useState(false);
  const [linkingJob, setLinkingJob] = useState(false);

  const handleShopTier = (tier) => {
    const tierKey = `tier${tier}`;
    const tierData = plan?.[tierKey];
    if (!tierData) return;

    let budget = tierData.budget;
    if (tier === 2 && commitment?.tier2BudgetWithEarnings != null) {
      budget = commitment.tier2BudgetWithEarnings;
    }

    navigate(`/bts/${sessionId}/shop/${tier}`, {
      state: {
        tier,
        tierKey,
        budget,
        items: tierData.items,
        purchaseBy: tierData.purchaseBy,
        commitment: commitment
          ? {
              jobTitle: commitment.jobTitle,
              actualEarnings: commitment.actualEarnings,
            }
          : undefined,
      },
    });
  };

  const toggleTier = (tier) => {
    setExpandedTier((current) => (current === tier ? null : tier));
  };

  const handleJobSelect = async (jobData) => {
    setLinkingJob(true);
    setJobError?.(null);
    try {
      await createCommitment({
        jobId: jobData.jobId,
        jobTitle: jobData.jobTitle,
        tier2Date: plan.tier2?.purchaseBy,
        tier2BaseBudget: plan.tier2?.budget,
        targetEarnings: jobData.targetEarnings,
      });
      setShowJobPicker(false);
    } catch {
      // error surfaced via hook
    } finally {
      setLinkingJob(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingSpinner} aria-busy="true">
          <div className={styles.spinner} />
          <p>Loading your shopping plan…</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className={styles.container}>
        <div className={styles.errorBox} role="alert">
          <p>{error || 'Failed to load plan'}</p>
          <div className={styles.errorActions}>
            <button type="button" onClick={() => navigate('/bts/setup')}>
              Back to setup
            </button>
            <button type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const summary = plan.summary || {};
  const tier2Dependent = Boolean(summary.jobDependent);
  const requiredEarnings =
    summary.jobEarningsRequired ??
    (Number(plan.tier2?.totalEstimated) > 0 ? plan.tier2.totalEstimated : null);

  const tier2JobSlot = (
    <>
      {!commitment ? (
        <button
          type="button"
          className={styles.addJobButton}
          onClick={(e) => {
            e.stopPropagation();
            setShowJobPicker(true);
          }}
        >
          Add side job to boost budget
        </button>
      ) : (
        <EarningsProgressBar commitment={commitment} />
      )}
      {jobError ? (
        <p className={styles.jobError} role="alert">
          {jobError}
        </p>
      ) : null}
    </>
  );

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Back to school</p>
        <h1 className={styles.heading}>Your 3-week shopping plan</h1>
        <p className={styles.subtitle}>
          Smart timing and budget so essentials land first — without stretching payday.
        </p>
      </header>

      {showTier2Banner ? (
        <Tier2ReminderBanner
          sessionId={sessionId}
          commitment={commitment || tier2Reminder?.commitment}
          tier2BaseBudget={
            tier2Reminder?.tier2BaseBudget ?? plan.tier2?.budget
          }
          tier2BudgetWithEarnings={
            commitment?.tier2BudgetWithEarnings ??
            tier2Reminder?.tier2BudgetWithEarnings
          }
          dismissLoading={dismissLoading}
          onDismiss={dismissReminder}
        />
      ) : null}

      <TimelineBreakdown plan={plan} />

      {tier2Status?.dateReached ? (
        <Tier2PurchaseReminder
          sessionId={sessionId}
          tier2Status={tier2Status}
          onDecision={recordDecision}
        />
      ) : null}

      <section className={styles.budgetSummary}>
        <h2>Budget breakdown</h2>
        <div className={styles.summaryGrid}>
          <div className={styles.summaryCard}>
            <p className={styles.label}>Total available</p>
            <p className={styles.amount}>
              {formatMoney(summary.totalBudgetAvailable)}
            </p>
          </div>
          <div className={styles.summaryCard}>
            <p className={styles.label}>Estimated spend</p>
            <p className={styles.amount}>
              {formatMoney(summary.totalEstimatedSpend)}
            </p>
          </div>
          <div className={styles.summaryCard}>
            <p className={styles.label}>Buffer remaining</p>
            <p className={`${styles.amount} ${styles.positive}`}>
              {formatMoney(summary.bufferRemaining)}
            </p>
          </div>
        </div>
      </section>

      <TierCard
        tier={1}
        data={plan.tier1}
        onExpand={() => toggleTier(1)}
        isExpanded={expandedTier === 1}
        onShop={handleShopTier}
      />
      <TierCard
        tier={2}
        data={plan.tier2}
        dependent={tier2Dependent}
        dependencyNote={plan.tier2?.contingency}
        onExpand={() => toggleTier(2)}
        isExpanded={expandedTier === 2}
        onShop={handleShopTier}
        footerExtra={tier2JobSlot}
        displayBudget={
          commitment?.tier2BudgetWithEarnings != null
            ? commitment.tier2BudgetWithEarnings
            : undefined
        }
      />

      {tier2Dependent ? (
        <JobDependencyWarning
          requiredEarnings={requiredEarnings}
          tier2Date={plan.tier2?.purchaseBy}
          fallback={summary.fallbackIfJobFails}
        />
      ) : null}

      <TierCard
        tier={3}
        data={plan.tier3}
        dependent
        dependencyNote={
          plan.tier3?.contingency || 'Only if Tier 2 complete and extra cash'
        }
        onExpand={() => toggleTier(3)}
        isExpanded={expandedTier === 3}
        onShop={handleShopTier}
      />

      {plan.warnings?.length > 0 ? (
        <section className={styles.warningsBox}>
          <h3>Important notes</h3>
          <ul className={styles.warningsList}>
            {plan.warnings.map((warning, idx) => (
              <li key={`${idx}-${warning.slice(0, 24)}`}>{warning}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className={styles.footer}>
        <button
          type="button"
          className={styles.primaryButton}
          onClick={() => handleShopTier(1)}
        >
          Start shopping Tier 1
        </button>
        <p className={styles.footerNote}>
          {jobLoading
            ? 'Refreshing job earnings…'
            : 'Next: browse recommended products and add to cart'}
        </p>
      </div>

      {showJobPicker ? (
        <JobPickerModal
          tier2BaseBudget={plan.tier2?.budget}
          onSelect={handleJobSelect}
          onClose={() => setShowJobPicker(false)}
          submitting={linkingJob}
        />
      ) : null}
    </div>
  );
}
