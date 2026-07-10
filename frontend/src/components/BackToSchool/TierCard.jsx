import React from 'react';
import styles from './PurchasePlanView.module.css';

function formatDate(dateStr) {
  try {
    const [year, month, day] = String(dateStr).split('-');
    const date = new Date(Number(year), Number(month) - 1, Number(day));
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

function formatCategory(category) {
  return String(category || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());
}

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

const TIER_LABELS = {
  1: 'Tier 1: Essentials',
  2: 'Tier 2: Important',
  3: 'Tier 3: Nice-to-have',
};

const TIER_DESCRIPTIONS = {
  1: 'Must-have items your child needs to start school',
  2: 'Important but can be delayed 1 week',
  3: 'Nice additions (optional, budget permitting)',
};

const TIER_COLORS = {
  1: 'critical',
  2: 'important',
  3: 'niceTohave',
};

/**
 * Expandable tier card for the purchase plan.
 */
export default function TierCard({
  tier,
  data,
  dependent = false,
  dependencyNote,
  onExpand,
  isExpanded = false,
  onShop,
  footerExtra = null,
  displayBudget,
}) {
  if (!data) return null;

  const budgetValue =
    displayBudget != null && displayBudget !== '' ? displayBudget : data.budget;

  return (
    <article
      className={`${styles.tierCard} ${styles[TIER_COLORS[tier]]} ${
        isExpanded ? styles.expanded : ''
      }`}
    >
      <button type="button" className={styles.tierHeader} onClick={onExpand}>
        <div className={styles.tierInfo}>
          <h3 className={styles.tierTitle}>{TIER_LABELS[tier]}</h3>
          <p className={styles.tierDescription}>{TIER_DESCRIPTIONS[tier]}</p>
          <p className={styles.tierDate}>By {formatDate(data.purchaseBy)}</p>
          {dependent ? (
            <span className={styles.dependencyBadge}>
              {dependencyNote || data.contingency || 'Contingent'}
            </span>
          ) : null}
        </div>
        <div className={styles.tierStats}>
          <div className={styles.statItem}>
            <p className={styles.statLabel}>Budget</p>
            <p className={styles.statValue}>{formatMoney(budgetValue)}</p>
          </div>
          <div className={styles.statItem}>
            <p className={styles.statLabel}>Est.</p>
            <p className={styles.statValue}>{formatMoney(data.totalEstimated)}</p>
          </div>
          <span className={styles.expandIcon} aria-hidden="true">
            {isExpanded ? '▾' : '▸'}
          </span>
        </div>
      </button>

      {isExpanded ? (
        <div className={styles.tierContent}>
          {data.justification ? (
            <p className={styles.tierJustification}>{data.justification}</p>
          ) : null}

          <div className={styles.itemsList}>
            <h4>Items to buy</h4>
            {(data.items || []).map((item, idx) => (
              <div key={`${item.category}-${idx}`} className={styles.itemRow}>
                <div className={styles.itemDetails}>
                  <span className={styles.itemCategory}>
                    {formatCategory(item.category)}
                  </span>
                  <span className={styles.itemQty}>× {item.quantity}</span>
                  {item.note ? <span className={styles.itemNoteInline}>{item.note}</span> : null}
                </div>
                <div className={styles.itemCost}>{formatMoney(item.estimatedCost)}</div>
              </div>
            ))}
          </div>

          <div className={styles.tierFooter}>
            <div className={styles.tierTotals}>
              <span>Subtotal</span>
              <span className={styles.bold}>{formatMoney(data.totalEstimated)}</span>
            </div>
            {Number(data.remaining) > 0 ? (
              <div className={styles.tierRemaining}>
                <span>Remaining</span>
                <span className={styles.positive}>{formatMoney(data.remaining)}</span>
              </div>
            ) : null}
            {footerExtra}
            {typeof onShop === 'function' ? (
              <button
                type="button"
                className={styles.tierShopButton}
                onClick={(e) => {
                  e.stopPropagation();
                  onShop(tier);
                }}
              >
                Shop Tier {tier}
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </article>
  );
}
