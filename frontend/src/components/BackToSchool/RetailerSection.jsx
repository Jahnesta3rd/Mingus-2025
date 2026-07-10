import React from 'react';
import ProductCard from './ProductCard';
import styles from './ProductPickerUI.module.css';

const RETAILER_NAMES = {
  'h&m': 'H&M',
  nordstrom: 'Nordstrom',
  amazon: 'Amazon',
};

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(n);
}

/**
 * Products grouped under one retailer.
 */
export default function RetailerSection({
  retailer,
  items,
  total,
  onSwap,
  swapLoadingCategory,
}) {
  if (!items?.length) return null;

  return (
    <section className={styles.retailerSection}>
      <div className={styles.retailerHeader}>
        <h2>{RETAILER_NAMES[retailer] || retailer}</h2>
        <span className={styles.retailerTotal}>{formatMoney(total)}</span>
      </div>
      <div className={styles.productList}>
        {items.map((item) => (
          <ProductCard
            key={`${retailer}-${item.sku}-${item.category}`}
            item={item}
            onSwap={() => onSwap(retailer, item.category)}
            swapLoading={swapLoadingCategory === item.category}
          />
        ))}
      </div>
    </section>
  );
}
