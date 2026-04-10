import React, { useState, useMemo } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { useAuth } from '../hooks/useAuth';
import LoadingSpinner from '../components/common/LoadingSpinner';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? '');

export type TierId = 'budget' | 'mid' | 'professional';

export interface TierOption {
  id: TierId;
  name: string;
  priceMonthly: number;
  amountCents: number;
  features: string[];
}

export const TIERS: TierOption[] = [
  {
    id: 'budget',
    name: 'Budget',
    priceMonthly: 15,
    amountCents: 1500,
    features: [
      'Core budget tracking & insights',
      'Monthly expense reports',
      'Basic goal setting',
      'Email support',
    ],
  },
  {
    id: 'mid',
    name: 'Mid-tier',
    priceMonthly: 35,
    amountCents: 3500,
    features: [
      'Everything in Budget',
      'Career & commute analytics',
      'Vehicle cost optimization',
      'Priority email support',
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    priceMonthly: 100,
    amountCents: 10000,
    features: [
      'Everything in Mid-tier',
      '1:1 financial coaching sessions',
      'Custom reports & exports',
      'Dedicated account manager',
    ],
  },
];

export function TierSelectionStep({
  selectedTier,
  onSelectTier,
  onContinue,
  loading,
  hideContinue = false,
}: {
  selectedTier: TierOption | null;
  onSelectTier: (tier: TierOption) => void;
  onContinue: () => void;
  loading?: boolean;
  /** When true, only tier cards are shown (e.g. embedded in a larger form). */
  hideContinue?: boolean;
}) {
  return (
    <div className="min-w-0 space-y-8">
      <div className="min-w-0">
        <h2 className="text-xl font-semibold text-gray-900 mb-1">Step 1 — Tier Selection</h2>
        <p className="text-gray-600 text-sm">Choose your plan.</p>
      </div>
      <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {TIERS.map((tier) => {
          const isSelected = selectedTier?.id === tier.id;
          return (
            <button
              key={tier.id}
              type="button"
              data-testid={`tier-${tier.id}`}
              onClick={() => onSelectTier(tier)}
              disabled={loading}
              className={`min-w-0 overflow-hidden text-left p-5 rounded-xl border-2 transition-all disabled:opacity-70 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 ${
                isSelected
                  ? 'border-violet-500 bg-violet-50 shadow-md ring-2 ring-violet-500/30'
                  : 'border-gray-300 bg-white hover:border-violet-400/50'
              }`}
            >
              <div className="min-w-0 font-semibold text-gray-900 break-words">{tier.name}</div>
              <div className="mt-2 min-w-0 text-2xl font-bold text-violet-600 break-words tabular-nums">
                ${tier.priceMonthly}/month
              </div>
              <ul className="mt-4 space-y-2 text-sm text-gray-600">
                {tier.features.map((f, i) => (
                  <li key={i} className="flex min-w-0 items-start gap-2">
                    <span className="shrink-0 text-violet-500 mt-0.5">•</span>
                    <span className="min-w-0 break-words">{f}</span>
                  </li>
                ))}
              </ul>
            </button>
          );
        })}
      </div>
      {!hideContinue && (
        <div className="flex justify-end">
          <button
            type="button"
            data-testid="checkout-continue"
            onClick={onContinue}
            disabled={loading}
            className="px-6 py-3 rounded-md font-medium text-white bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400"
          >
            Continue
          </button>
        </div>
      )}
    </div>
  );
}

function PaymentFormStep({
  clientSecret,
  tierName,
  userEmail,
  onBack,
}: {
  clientSecret: string;
  tierName: string;
  userEmail: string;
  onBack: () => void;
}) {
  const options = useMemo(
    () => ({
      clientSecret,
      appearance: {
        theme: 'stripe' as const,
        variables: {
          colorPrimary: '#7c3aed',
          colorBackground: '#ffffff',
          colorText: '#111827',
          colorDanger: '#dc2626',
          borderRadius: '6px',
        },
      },
      defaultValues: { email: userEmail || undefined },
    }),
    [clientSecret, userEmail]
  );

  return (
    <Elements stripe={stripePromise} options={options}>
      <PaymentFormInner tierName={tierName} onBack={onBack} />
    </Elements>
  );
}

function PaymentFormInner({ tierName, onBack }: { tierName: string; onBack: () => void }) {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripe || !elements) return;
    setError(null);
    setLoading(true);

    try {
      const { error: confirmError } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: window.location.origin + '/dashboard',
        },
      });
      if (confirmError) {
        setError(confirmError.message ?? 'Payment failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-1">Step 2 — Payment</h2>
        <p className="text-gray-600 text-sm">Complete payment for {tierName}.</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-md border border-gray-300 bg-white p-4 shadow-sm">
          <PaymentElement />
        </div>
        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-red-600 text-sm" role="alert">
            {error}
          </div>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            disabled={loading}
            className="px-4 py-2 rounded-md font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={!stripe || !elements || loading}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-md font-medium text-white bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                <span>Processing…</span>
              </>
            ) : (
              'Pay now'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function CheckoutPage() {
  const { user } = useAuth();
  const [step, setStep] = useState<1 | 2>(1);
  const [selectedTier, setSelectedTier] = useState<TierOption | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [intentError, setIntentError] = useState<string | null>(null);
  const [loadingIntent, setLoadingIntent] = useState(false);

  const handleContinue = async () => {
    // If no tier selected (e.g. state not updated by click), default to Budget so the request always fires
    const tier = selectedTier ?? TIERS[0];
    if (!selectedTier && typeof console !== 'undefined' && console.warn) {
      console.warn('Checkout: Continue clicked with no tier selected; using default Budget tier.');
    }
    setIntentError(null);
    setLoadingIntent(true);
    try {
      const res = await fetch('/api/create-payment-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          tierName: tier.name,
          amount: tier.amountCents,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setIntentError(data.error || 'Failed to start payment');
        return;
      }
      if (data.clientSecret) {
        if (!selectedTier) setSelectedTier(tier);
        setClientSecret(data.clientSecret);
        setStep(2);
      } else {
        setIntentError('Invalid response from server');
      }
    } catch (err) {
      setIntentError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setLoadingIntent(false);
    }
  };

  const handleBack = () => {
    setStep(1);
    setClientSecret(null);
    setIntentError(null);
  };

  const userEmail = user?.email ?? '';

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8 flex flex-col items-center sm:block">
          <img src="/mingus-logo.png" alt="Mingus" className="h-10 w-auto object-contain mb-4 sm:mb-0 sm:inline-block" />
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">Checkout</h1>
          <p className="mt-2 text-sm text-gray-600">Select your plan and complete payment.</p>
        </div>
        {intentError && (
          <div className="mb-6 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-red-600 text-sm" role="alert">
            {intentError}
          </div>
        )}
        {step === 1 && (
          <TierSelectionStep
            selectedTier={selectedTier}
            onSelectTier={setSelectedTier}
            onContinue={handleContinue}
            loading={loadingIntent}
          />
        )}
        {step === 1 && loadingIntent && (
          <div className="mt-6 flex items-center gap-2 text-gray-600">
            <LoadingSpinner size="sm" />
            <span>Preparing payment…</span>
          </div>
        )}
        {step === 2 && clientSecret && (
          <PaymentFormStep
            clientSecret={clientSecret}
            tierName={selectedTier!.name}
            userEmail={userEmail}
            onBack={handleBack}
          />
        )}
      </div>
    </div>
  );
}
