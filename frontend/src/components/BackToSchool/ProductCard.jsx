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

function formatRating(rating, reviewCount) {
  const r = Number(rating);
  if (Number.isNaN(r)) return null;
  const count = reviewCount != null ? ` (${reviewCount})` : '';
  return `${r.toFixed(1)}${count}`;
}

/**
 * Single recommended product card with swap action.
 */
export default function ProductCard({ item, onSwap, swapLoading = false }) {
  const imageSrc = item.imageUrl || item.image_url;
  const ratingLabel = formatRating(item.rating, item.reviewCount ?? item.review_count);

  return (
    <article className={styles.productCard}>
      {imageSrc ? (
        <img src={imageSrc} alt={item.name || 'Product'} className={styles.productImage} />
      ) : (
        <div className={styles.productImagePlaceholder} aria-hidden="true" />
      )}
      <div className={styles.productInfo}>
        <p className={styles.categoryLabel}>
          {String(item.category || '')
            .replace(/_/g, ' ')
            .replace(/\b\w/g, (c) => c.toUpperCase())}
        </p>
        <h4>{item.name}</h4>
        {item.reason ? <p className={styles.reason}>{item.reason}</p> : null}
        <div className={styles.priceRow}>
          <span className={styles.price}>{formatMoney(item.price)}</span>
          {Number(item.quantity) > 1 ? (
            <span className={styles.quantity}>× {item.quantity}</span>
          ) : null}
        </div>
        {ratingLabel ? <p className={styles.rating}>{ratingLabel}</p> : null}
        <button
          type="button"
          className={styles.swapButton}
          onClick={onSwap}
          disabled={swapLoading}
        >
          {swapLoading ? 'Loading…' : 'Swap item'}
        </button>
      </div>
    </article>
  );
}
