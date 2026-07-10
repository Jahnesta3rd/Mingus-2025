import React from 'react';
import styles from './CheckoutUI.module.css';

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
 * Cart line items grouped by retailer with totals.
 */
export default function OrderSummary({ cartByRetailer, subtotal, discount, total }) {
  const entries = Object.entries(cartByRetailer || {});

  return (
    <div className={styles.orderSummary}>
      <h2>Order summary</h2>
      {entries.map(([retailer, items]) => {
        if (!items?.length) return null;
        const retailerTotal = items.reduce(
          (sum, item) =>
            sum + Number(item.price || 0) * (Number(item.quantity) || 1),
          0,
        );
        return (
          <div key={retailer} className={styles.retailerGroup}>
            <h3>{RETAILER_NAMES[retailer] || retailer}</h3>
            <ul>
              {items.map((item) => (
                <li
                  key={`${retailer}-${item.sku}-${item.category}`}
                  className={styles.lineItem}
                >
                  <span>
                    {item.name}
                    {Number(item.quantity) > 1 ? ` × ${item.quantity}` : ''}
                  </span>
                  <span>
                    {formatMoney(
                      Number(item.price || 0) * (Number(item.quantity) || 1),
                    )}
                  </span>
                </li>
              ))}
            </ul>
            <div className={styles.retailerTotal}>{formatMoney(retailerTotal)}</div>
          </div>
        );
      })}
      <div className={styles.totals}>
        <div className={styles.totalRow}>
          <span>Subtotal</span>
          <span>{formatMoney(subtotal)}</span>
        </div>
        {Number(discount) > 0 ? (
          <div className={styles.totalRow}>
            <span>Discount</span>
            <span className={styles.discount}>-{formatMoney(discount)}</span>
          </div>
        ) : null}
        <div className={`${styles.totalRow} ${styles.total}`}>
          <span>Total</span>
          <span>{formatMoney(total)}</span>
        </div>
      </div>
    </div>
  );
}
