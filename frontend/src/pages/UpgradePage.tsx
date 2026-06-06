import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { TIER_ORDER } from '../components/sections/PricingSection';
import { useAuth, type AuthUserTier } from '../hooks/useAuth';
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

const UpgradePage: React.FC = () => {
  const navigate = useNavigate();
  const { userTier, loading } = useAuth();
  const [selectedTier, setSelectedTier] = useState<TierOption | null>(null);

  const upgradeTiers = useMemo(() => {
    if (userTier === null) return [];
    return tiersAboveCurrent(userTier);
  }, [userTier]);

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

  if (upgradeTiers.length === 0) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-6 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-[#1E293B]">Upgrade your plan</h1>
        <p className="text-sm text-[#64748B]">
          You are on our highest tier. No further upgrades are available.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex text-sm font-semibold text-[#5B2D8E] hover:underline"
        >
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-2xl font-bold text-[#1E293B]">Upgrade your plan</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Choose a higher tier to unlock more features. You will complete payment on the next step.
        </p>
      </div>
      <div className="max-w-5xl rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <TierSelectionStep
          tiers={upgradeTiers}
          selectedTier={selectedTier}
          onSelectTier={setSelectedTier}
          onContinue={handleContinue}
        />
      </div>
    </div>
  );
};

export default UpgradePage;
