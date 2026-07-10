import React, { useState } from 'react';
import { CardElement, useElements, useStripe } from '@stripe/react-stripe-js';
import styles from './CheckoutUI.module.css';

/**
 * Stripe card payment for BTS checkout (requires Elements + clientSecret parent).
 */
export default function PaymentForm({
  clientSecret,
  total,
  onPaymentSuccess,
  onPaymentError,
}) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    if (!stripe || !elements || !clientSecret) return;

    setLoading(true);
    try {
      const card = elements.getElement(CardElement);
      if (!card) {
        onPaymentError('Card form is not ready. Please try again.');
        return;
      }

      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: { card },
      });

      if (result.error) {
        onPaymentError(result.error.message || 'Payment failed');
      } else if (result.paymentIntent?.status === 'succeeded') {
        await onPaymentSuccess(result.paymentIntent);
      } else {
        onPaymentError(
          `Payment incomplete (status: ${result.paymentIntent?.status || 'unknown'})`,
        );
      }
    } catch (err) {
      onPaymentError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.paymentForm}>
      <h2>Payment</h2>
      <p className={styles.paymentNote}>
        Test card: 4242 4242 4242 4242 · any future expiry · any CVC
      </p>
      <div className={styles.cardElement}>
        <CardElement
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#1a1a2e',
                '::placeholder': { color: '#8a8aa3' },
              },
              invalid: { color: '#991b1b' },
            },
          }}
        />
      </div>
      <button
        type="button"
        onClick={handlePayment}
        disabled={!stripe || !clientSecret || loading}
        className={styles.payButton}
      >
        {loading ? 'Processing…' : `Pay $${Number(total).toFixed(2)}`}
      </button>
    </div>
  );
}
