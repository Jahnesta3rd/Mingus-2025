import React from 'react';
import styles from './CheckoutUI.module.css';

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
];

/**
 * Shipping address collection for BTS checkout.
 */
export default function ShippingForm({ form, error, updateField }) {
  return (
    <div className={styles.shippingForm}>
      <h2>Shipping address</h2>
      {error ? (
        <div className={styles.error} role="alert">
          {error}
        </div>
      ) : null}

      <div className={styles.row}>
        <label className={styles.field}>
          <span className={styles.label}>First name</span>
          <input
            type="text"
            autoComplete="given-name"
            value={form.firstName}
            onChange={(e) => updateField('firstName', e.target.value)}
            className={styles.input}
            required
          />
        </label>
        <label className={styles.field}>
          <span className={styles.label}>Last name</span>
          <input
            type="text"
            autoComplete="family-name"
            value={form.lastName}
            onChange={(e) => updateField('lastName', e.target.value)}
            className={styles.input}
            required
          />
        </label>
      </div>

      <label className={styles.field}>
        <span className={styles.label}>Address</span>
        <input
          type="text"
          autoComplete="street-address"
          value={form.address}
          onChange={(e) => updateField('address', e.target.value)}
          className={`${styles.input} ${styles.fullWidth}`}
          required
        />
      </label>

      <div className={styles.row}>
        <label className={styles.field}>
          <span className={styles.label}>City</span>
          <input
            type="text"
            autoComplete="address-level2"
            value={form.city}
            onChange={(e) => updateField('city', e.target.value)}
            className={styles.input}
            required
          />
        </label>
        <label className={styles.field}>
          <span className={styles.label}>State</span>
          <select
            value={form.state}
            onChange={(e) => updateField('state', e.target.value)}
            className={styles.input}
            required
          >
            <option value="">Select</option>
            {US_STATES.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className={styles.row}>
        <label className={styles.field}>
          <span className={styles.label}>ZIP</span>
          <input
            type="text"
            inputMode="numeric"
            autoComplete="postal-code"
            value={form.zip}
            onChange={(e) => updateField('zip', e.target.value)}
            className={styles.input}
            required
          />
        </label>
        <label className={styles.field}>
          <span className={styles.label}>Phone</span>
          <input
            type="tel"
            autoComplete="tel"
            value={form.phone}
            onChange={(e) => updateField('phone', e.target.value)}
            className={styles.input}
            required
          />
        </label>
      </div>
    </div>
  );
}
