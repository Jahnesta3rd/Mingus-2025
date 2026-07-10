import React, { useMemo, useState } from 'react';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import OrderConfirmation from './OrderConfirmation';
import OrderSummary from './OrderSummary';
import PaymentForm from './PaymentForm';
import ShippingForm from './ShippingForm';
import { useCheckout } from './hooks/useCheckout';
import styles from './CheckoutUI.module.css';

const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? '',
);

function validateShippingLocal(form) {
  const required = [
    'firstName',
    'lastName',
    'address',
    'city',
    'state',
    'zip',
    'phone',
  ];
  for (const field of required) {
    if (!String(form[field] || '').trim()) {
      return `Please fill in ${field.replace(/([A-Z])/g, ' $1').toLowerCase()}`;
    }
  }
  if (String(form.state).trim().length !== 2) {
    return 'State must be a 2-character code';
  }
  const zipDigits = String(form.zip).replace(/\D/g, '');
  if (zipDigits.length < 5) return 'Enter a valid ZIP code';
  const phoneDigits = String(form.phone).replace(/\D/g, '');
  if (phoneDigits.length < 10) return 'Enter a valid phone number';
  return null;
}

/**
 * BTS9 — Tier 1 checkout: review → shipping → Stripe payment → confirmation.
 */
export default function CheckoutUI() {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { getAccessToken } = useAuth();

  const cartData = location.state || {};
  const tier = Number(cartData.tier) || 1;
  const cartByRetailer = cartData.cart || {};
  const subtotal = Number(cartData.total) || 0;

  const [step, setStep] = useState('review');
  const [couponApplied, setCouponApplied] = useState(null);
  const [discount, setDiscount] = useState(0);
  const [orderId, setOrderId] = useState(null);

  const checkout = useCheckout({ getAccessToken });
  const total = Math.max(0, subtotal - discount);

  const hasItems = useMemo(
    () =>
      Object.values(cartByRetailer).some(
        (items) => Array.isArray(items) && items.length > 0,
      ),
    [cartByRetailer],
  );

  if (!hasItems && step !== 'confirm') {
    return (
      <div className={styles.container}>
        <div className={styles.content}>
          <p className={styles.eyebrow}>Back to school</p>
          <h1 className={styles.heading}>Checkout</h1>
          <div className={styles.error} role="alert">
            No cart found. Return to shopping and approve your Tier {tier} picks
            first.
          </div>
          <div className={styles.actions}>
            <button
              type="button"
              className={styles.primaryButton}
              onClick={() =>
                navigate(`/bts/${sessionId}/shop/${cartData.tierKey || tier}`)
              }
            >
              Back to shopping
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleApplyCoupon = async () => {
    try {
      const result = await checkout.validateCoupon(checkout.form.couponCode);
      const discountAmount = subtotal * Number(result.discountPercent);
      setDiscount(discountAmount);
      setCouponApplied(result.code);
    } catch {
      setCouponApplied(null);
      setDiscount(0);
    }
  };

  const handleProceedToPayment = async () => {
    const localError = validateShippingLocal(checkout.form);
    if (localError) {
      checkout.setError(localError);
      return;
    }
    try {
      await checkout.createPaymentIntent(total, { sessionId, tier });
      setStep('payment');
    } catch {
      // error already set on checkout
    }
  };

  const handlePaymentSuccess = async () => {
    try {
      const result = await checkout.submitCheckout({
        sessionId,
        tier,
        cartItems: cartByRetailer,
        subtotal,
        couponCode: couponApplied || checkout.form.couponCode || null,
      });
      setOrderId(result.orderId);
      setStep('confirm');
    } catch {
      // error already set
    }
  };

  if (step === 'confirm' && orderId) {
    return (
      <OrderConfirmation
        orderId={orderId}
        sessionId={sessionId}
        tier={tier}
        total={total}
      />
    );
  }

  if (step === 'payment' && checkout.clientSecret) {
    return (
      <Elements
        stripe={stripePromise}
        options={{ clientSecret: checkout.clientSecret }}
      >
        <div className={styles.container}>
          <div className={styles.content}>
            <p className={styles.eyebrow}>Back to school · Tier {tier}</p>
            <h1 className={styles.heading}>Payment</h1>
            <OrderSummary
              cartByRetailer={cartByRetailer}
              subtotal={subtotal}
              discount={discount}
              total={total}
            />
            {checkout.error ? (
              <div className={styles.error} role="alert">
                {checkout.error}
              </div>
            ) : null}
            <PaymentForm
              clientSecret={checkout.clientSecret}
              total={total}
              onPaymentSuccess={handlePaymentSuccess}
              onPaymentError={(msg) => checkout.setError(msg)}
            />
            <div className={styles.actions}>
              <button
                type="button"
                onClick={() => setStep('shipping')}
                className={styles.secondaryButton}
              >
                Back
              </button>
            </div>
          </div>
        </div>
      </Elements>
    );
  }

  if (step === 'shipping') {
    return (
      <div className={styles.container}>
        <div className={styles.content}>
          <p className={styles.eyebrow}>Back to school · Tier {tier}</p>
          <h1 className={styles.heading}>Shipping</h1>
          <ShippingForm
            form={checkout.form}
            error={checkout.error}
            updateField={checkout.updateField}
          />
          <div className={styles.actions}>
            <button
              type="button"
              onClick={() => setStep('review')}
              className={styles.secondaryButton}
            >
              Back
            </button>
            <button
              type="button"
              onClick={handleProceedToPayment}
              disabled={checkout.loading}
              className={styles.primaryButton}
            >
              {checkout.loading ? 'Preparing payment…' : 'Continue to payment'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // review (default)
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <p className={styles.eyebrow}>Back to school · Tier {tier}</p>
        <h1 className={styles.heading}>Review your order</h1>
        <OrderSummary
          cartByRetailer={cartByRetailer}
          subtotal={subtotal}
          discount={discount}
          total={total}
        />

        <div className={styles.couponSection}>
          <input
            type="text"
            placeholder="Coupon code (optional)"
            value={checkout.form.couponCode}
            onChange={(e) => checkout.updateField('couponCode', e.target.value)}
            className={styles.couponInput}
          />
          <button
            type="button"
            onClick={handleApplyCoupon}
            disabled={!checkout.form.couponCode || checkout.loading}
            className={styles.couponButton}
          >
            {checkout.loading ? 'Checking…' : 'Apply'}
          </button>
        </div>
        {couponApplied ? (
          <p className={styles.success}>
            Coupon {couponApplied} applied — saved ${discount.toFixed(2)}
          </p>
        ) : null}
        {checkout.error ? (
          <p className={styles.error} role="alert">
            {checkout.error}
          </p>
        ) : null}

        <div className={styles.actions}>
          <button
            type="button"
            onClick={() =>
              navigate(`/bts/${sessionId}/shop/${cartData.tierKey || tier}`)
            }
            className={styles.secondaryButton}
          >
            Back to cart
          </button>
          <button
            type="button"
            onClick={() => {
              checkout.setError(null);
              setStep('shipping');
            }}
            className={styles.primaryButton}
            disabled={subtotal <= 0}
          >
            Continue to shipping
          </button>
        </div>
      </div>
    </div>
  );
}
