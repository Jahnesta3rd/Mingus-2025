import React, { useId } from 'react';
import { Link } from 'react-router-dom';
import { Lock } from 'lucide-react';

export interface TierGateOverlayProps {
  requiredTier: 'mid_tier' | 'professional';
  feature: string;
  /** When set, shows a dismiss control (e.g. modal use). */
  onDismiss?: () => void;
  className?: string;
}

const TIER_LABEL: Record<TierGateOverlayProps['requiredTier'], string> = {
  mid_tier: 'Mid-tier',
  professional: 'Professional',
};

export function TierGateOverlay({
  requiredTier,
  feature,
  onDismiss,
  className = '',
}: TierGateOverlayProps) {
  const tierLabel = TIER_LABEL[requiredTier];
  const msgId = useId();

  return (
    <div
      className={`absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 rounded-xl bg-[#0f172a]/80 p-6 text-center backdrop-blur-[4px] ${className}`}
      role="region"
      aria-label={`Upgrade to ${tierLabel} for ${feature}`}
    >
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="absolute right-3 top-3 rounded-lg px-2 py-1 text-xs font-medium text-[#C4A064]/80 transition-colors hover:bg-[#C4A064]/10 hover:text-[#C4A064]"
        >
          Close
        </button>
      )}
      <Lock className="h-10 w-10 text-[#C4A064]" strokeWidth={1.75} aria-hidden />
      <p id={msgId} className="max-w-sm text-sm font-semibold leading-snug text-[#C4A064]">
        Upgrade to {tierLabel} to unlock {feature}
      </p>
      <Link
        to="/settings/upgrade"
        className="inline-flex items-center justify-center rounded-lg bg-[#C4A064] px-5 py-2.5 text-sm font-semibold text-[#0f172a] shadow-sm transition-colors hover:bg-[#b08d52]"
      >
        Upgrade Now
      </Link>
    </div>
  );
}
