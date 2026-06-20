import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { TIER_ORDER } from '../components/sections/PricingSection';
import { useAuth, type AuthUserTier } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import type { UserProfileModules } from '../types/UserProfile';
import {
  TierSelectionStep,
  TIERS,
  type TierId,
  type TierOption,
} from './CheckoutPage';

function checkoutTierIdToOrderKey(tierId: TierId): keyof typeof TIER_ORDER {
  if (tierId === 'mid') return 'mid_tier';
  return tierId;
}

function tiersAboveCurrent(userTier: AuthUserTier): TierOption[] {
  const currentOrder = TIER_ORDER[userTier];
  return TIERS.filter(
    (tier) => TIER_ORDER[checkoutTierIdToOrderKey(tier.id)] > currentOrder
  );
}

const FROM_BACK_LABELS: Record<string, string> = {
  plans: '← Back to Plans',
  checklist: '← Back to Checklist',
  upsell: '← Back to Plans',
  dashboard: '← Back to dashboard',
};

function backLabelForFrom(from: string): string {
  return FROM_BACK_LABELS[from] ?? FROM_BACK_LABELS.dashboard;
}

interface FamilyAddonModuleCardProps {
  highlighted: boolean;
  hasAccess: boolean;
  checkoutLoading: boolean;
  onCheckout: () => void;
  onGoBack: () => void;
}

function FamilyAddonModuleCard({
  highlighted,
  hasAccess,
  checkoutLoading,
  onCheckout,
  onGoBack,
}: FamilyAddonModuleCardProps) {
  return (
    <div
      className={`rounded-xl border-2 bg-white p-5 transition-all ${
        highlighted ? 'border-purple-500 ring-2 ring-purple-500/30 shadow-md' : 'border-gray-300'
      }`}
    >
      <div className="text-2xl" aria-hidden="true">🍼</div>
      <h2 className="mt-2 text-lg font-semibold text-gray-900">New Parent Financial Checklist</h2>
      <p className="mt-1 text-sm text-gray-600">The 12 financial moves most parents miss</p>
      <p className="mt-3 text-2xl font-bold text-violet-600 tabular-nums">$12 / month</p>
      <ul className="mt-4 space-y-2 text-sm text-gray-600">
        <li>✓ 12-item New Parent Financial Checklist</li>
        <li>✓ Parenting &amp; childcare cost tracker</li>
        <li>✓ Family wellness ROI analysis</li>
      </ul>
      {hasAccess ? (
        <p className="mt-4 text-sm font-medium text-teal-600">Already included in your plan</p>
      ) : (
        <>
          <button
            type="button"
            onClick={onCheckout}
            disabled={checkoutLoading}
            className="mt-4 w-full rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {checkoutLoading ? 'Redirecting…' : 'Unlock Family Add-On'}
          </button>
          <button
            type="button"
            onClick={onGoBack}
            className="mt-2 w-full cursor-pointer text-center text-xs text-gray-400 underline"
          >
            Not now — go back
          </button>
        </>
      )}
    </div>
  );
}

const UpgradePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { userTier, loading, getAccessToken } = useAuth();
  const [selectedTier, setSelectedTier] = useState<TierOption | null>(null);
  const [modules, setModules] = useState<UserProfileModules | null>(null);
  const [familyCheckoutLoading, setFamilyCheckoutLoading] = useState(false);
  const familyCardRef = useRef<HTMLDivElement>(null);

  const highlightModule = searchParams.get('module') === 'family_addon';
  const from = searchParams.get('from') ?? 'dashboard';
  const backLabel = backLabelForFrom(from);

  const upgradeTiers = useMemo(() => {
    if (userTier === null) return [];
    return tiersAboveCurrent(userTier);
  }, [userTier]);

  const handleGoBack = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  useEffect(() => {
    const token = getAccessToken();
    fetch('/api/user/profile', {
      credentials: 'include',
      headers: {
        ...csrfHeaders(),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data: { profile?: { modules?: UserProfileModules } } | null) => {
        if (data?.profile?.modules) {
          setModules(data.profile.modules);
        }
      })
      .catch(() => {});
  }, [getAccessToken]);

  useEffect(() => {
    if (!highlightModule) return;
    const el = familyCardRef.current;
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [highlightModule, modules]);

  const startFamilyAddonCheckout = useCallback(async () => {
    setFamilyCheckoutLoading(true);
    try {
      const token = getAccessToken() ?? localStorage.getItem('mingus_token');
      const response = await fetch('/api/payments/create-checkout-session', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeaders(),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ module: 'family_addon', from }),
      });
      const data = (await response.json()) as { url?: string; error?: string };
      if (!response.ok || !data.url) {
        throw new Error(data.error || 'Checkout failed');
      }
      window.location.href = data.url;
    } catch {
      setFamilyCheckoutLoading(false);
    }
  }, [from, getAccessToken]);

  const handleContinue = () => {
    if (!selectedTier) return;
    navigate('/checkout', { state: { tierId: selectedTier.id }, replace: true });
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
        <p className="text-sm text-[#64748B]">Loading your plan…</p>
      </div>
    );
  }

  if (userTier === null) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-6 sm:px-6 lg:px-8">
        <p className="text-sm text-[#64748B]">We could not determine your current plan. Try again later.</p>
        <Link
          to="/dashboard"
          className="inline-flex text-sm font-semibold text-[#5B2D8E] hover:underline"
        >
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const hasFamilyAddon = modules?.family_addon === true;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <button
        type="button"
        onClick={handleGoBack}
        className="mb-6 flex cursor-pointer items-center gap-1 text-sm text-gray-500 transition-colors hover:text-purple-600"
      >
        <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        {backLabel}
      </button>

      <div>
        <h1 className="text-2xl font-bold text-[#1E293B]">Upgrade your plan</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add modules to your base plan or choose a higher tier for more features.
        </p>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-900">Module add-ons</h2>
        <p className="mt-1 text-sm text-gray-600">Unlock focused tools on top of your current plan.</p>
        <div ref={familyCardRef} className="mt-4 max-w-md">
          <FamilyAddonModuleCard
            highlighted={highlightModule}
            hasAccess={hasFamilyAddon}
            checkoutLoading={familyCheckoutLoading}
            onCheckout={() => void startFamilyAddonCheckout()}
            onGoBack={handleGoBack}
          />
        </div>
      </div>

      {upgradeTiers.length > 0 ? (
        <div className="max-w-5xl rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Higher tiers</h2>
          <p className="mt-1 mb-4 text-sm text-gray-600">
            Choose a higher tier to unlock more features. You will complete payment on the next step.
          </p>
          <TierSelectionStep
            tiers={upgradeTiers}
            selectedTier={selectedTier}
            onSelectTier={setSelectedTier}
            onContinue={handleContinue}
          />
        </div>
      ) : (
        <p className="text-sm text-[#64748B]">
          You are on our highest tier. Module add-ons above can still extend your plan.
        </p>
      )}
    </div>
  );
};

export default UpgradePage;
