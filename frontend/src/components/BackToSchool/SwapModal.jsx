import React from 'react';
import styles from './ProductPickerUI.module.css';

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(n);
}

function formatCategory(category) {
  return String(category || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Bottom-sheet modal to pick an alternative product within budget.
 */
export default function SwapModal({
  modal,
  onSwap,
  onClose,
  tierBudget,
  currentTotal,
}) {
  const { category, alternatives = [], currentItem } = modal || {};
  if (!currentItem) return null;

  const currentQty = Number(currentItem.quantity) || 1;
  const currentLine = Number(currentItem.price) * currentQty;

  return (
    <div
      className={styles.modalOverlay}
      onClick={onClose}
      role="presentation"
    >
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="swap-modal-title"
      >
        <div className={styles.modalHeader}>
          <h2 id="swap-modal-title">
            Choose a different {formatCategory(category)}
          </h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            Close
          </button>
        </div>

        <div className={styles.modalContent}>
          <div className={styles.currentSection}>
            <p className={styles.sectionLabel}>Currently selected</p>
            <div className={styles.selectedProduct}>
              {(currentItem.imageUrl || currentItem.image_url) ? (
                <img
                  src={currentItem.imageUrl || currentItem.image_url}
                  alt={currentItem.name}
                />
              ) : (
                <div className={styles.thumbPlaceholder} aria-hidden="true" />
              )}
              <div>
                <strong>{currentItem.name}</strong>
                <p>{formatMoney(currentItem.price)}</p>
              </div>
            </div>
          </div>

          <div className={styles.alternativesSection}>
            <p className={styles.sectionLabel}>Other options</p>
            {alternatives.length === 0 ? (
              <p className={styles.noAlternatives}>No other options available</p>
            ) : (
              alternatives.map((alt) => {
                const altPrice = Number(alt.price) || 0;
                const newLine = altPrice * currentQty;
                const newTotal = currentTotal - currentLine + newLine;
                const overBudget = newTotal > tierBudget;
                const imageSrc = alt.image_url || alt.imageUrl;
                const rating = Number(alt.rating);
                const reviews = alt.review_count ?? alt.reviewCount;

                return (
                  <div
                    key={alt.sku}
                    className={`${styles.alternativeProduct} ${
                      overBudget ? styles.overBudget : ''
                    }`}
                  >
                    {imageSrc ? (
                      <img src={imageSrc} alt={alt.name} />
                    ) : (
                      <div className={styles.thumbPlaceholder} aria-hidden="true" />
                    )}
                    <div className={styles.altInfo}>
                      <strong>{alt.name}</strong>
                      <p>{formatMoney(altPrice)}</p>
                      {!Number.isNaN(rating) ? (
                        <p className={styles.altRating}>
                          {rating.toFixed(1)}
                          {reviews != null ? ` (${reviews})` : ''}
                        </p>
                      ) : null}
                      {overBudget ? (
                        <p className={styles.overBudgetNote}>
                          Exceeds budget by {formatMoney(newTotal - tierBudget)}
                        </p>
                      ) : null}
                    </div>
                    <button
                      type="button"
                      className={styles.selectButton}
                      onClick={() => onSwap(alt)}
                      disabled={overBudget}
                    >
                      {overBudget ? 'Over budget' : 'Select'}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
