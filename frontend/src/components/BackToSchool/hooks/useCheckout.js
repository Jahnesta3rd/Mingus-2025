import { useState } from 'react';
import { csrfHeaders } from '../../../utils/csrfHeaders';

function resolveToken(getAccessToken) {
  const fromAuth = getAccessToken?.();
  if (fromAuth) return fromAuth;
  const fromStorage =
    localStorage.getItem('auth_token') || localStorage.getItem('mingus_token');
  if (fromStorage) return fromStorage;
  const cookies = document.cookie.split('; ');
  const tokenCookie = cookies.find((row) => row.startsWith('mingus_token='));
  return tokenCookie?.split('=')[1] || null;
}

async function parseError(response, fallback) {
  try {
    const body = await response.json();
    return body?.error || fallback;
  } catch {
    return fallback;
  }
}

/**
 * BTS9 checkout form state + API helpers.
 *
 * @param {{ getAccessToken?: () => string|null }} [options]
 */
export function useCheckout(options = {}) {
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    address: '',
    city: '',
    state: '',
    zip: '',
    phone: '',
    couponCode: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [paymentIntentId, setPaymentIntentId] = useState(null);
  const [clientSecret, setClientSecret] = useState(null);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError(null);
  };

  const createPaymentIntent = async (total, extra = {}) => {
    setLoading(true);
    setError(null);
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) throw new Error('Not logged in. Please log in and try again.');

      const response = await fetch('/api/bts/checkout/create-payment-intent', {
        method: 'POST',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
        body: JSON.stringify({
          total,
          sessionId: extra.sessionId,
          tier: extra.tier ?? 1,
        }),
      });

      if (!response.ok) {
        throw new Error(
          await parseError(response, 'Failed to create payment intent'),
        );
      }

      const data = await response.json();
      setPaymentIntentId(data.paymentIntentId);
      setClientSecret(data.clientSecret);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Payment setup failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const validateCoupon = async (couponCode) => {
    setLoading(true);
    setError(null);
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) throw new Error('Not logged in. Please log in and try again.');

      const response = await fetch('/api/bts/checkout/validate-coupon', {
        method: 'POST',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
        body: JSON.stringify({ couponCode }),
      });

      if (!response.ok) {
        throw new Error(await parseError(response, 'Invalid coupon'));
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Coupon validation failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const submitCheckout = async ({
    sessionId,
    tier,
    cartItems,
    subtotal,
    couponCode,
  }) => {
    setLoading(true);
    setError(null);
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) throw new Error('Not logged in. Please log in and try again.');
      if (!paymentIntentId) {
        throw new Error('Payment is not ready. Please try again.');
      }

      const response = await fetch('/api/bts/checkout/submit', {
        method: 'POST',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
        body: JSON.stringify({
          sessionId,
          tier,
          cartItems,
          shippingAddress: {
            firstName: form.firstName.trim(),
            lastName: form.lastName.trim(),
            address: form.address.trim(),
            city: form.city.trim(),
            state: form.state.trim().toUpperCase(),
            zip: form.zip.trim(),
            phone: form.phone.trim(),
          },
          paymentIntentId,
          subtotal,
          couponCode: couponCode || form.couponCode || null,
        }),
      });

      if (!response.ok) {
        throw new Error(await parseError(response, 'Checkout failed'));
      }

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Checkout failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    form,
    loading,
    error,
    setError,
    clientSecret,
    paymentIntentId,
    updateField,
    createPaymentIntent,
    validateCoupon,
    submitCheckout,
  };
}

export default useCheckout;
