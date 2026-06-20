import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';

export interface FamilyAddonUpsellCardProps {
  isVisible: boolean;
  onUpgrade: () => void;
  onDismiss: () => void;
}

export default function FamilyAddonUpsellCard({
  isVisible,
  onUpgrade,
  onDismiss,
}: FamilyAddonUpsellCardProps) {
  const [mounted, setMounted] = useState(isVisible);
  const [entered, setEntered] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setMounted(true);
      const frame = requestAnimationFrame(() => setEntered(true));
      return () => cancelAnimationFrame(frame);
    }
    setEntered(false);
    const timer = window.setTimeout(() => setMounted(false), 300);
    return () => window.clearTimeout(timer);
  }, [isVisible]);

  if (!mounted) {
    return null;
  }

  return (
    <div
      className={`relative rounded-xl border border-purple-200 bg-purple-50 p-5 transition-all duration-300 ease-out ${
        entered ? 'translate-y-0 opacity-100' : '-translate-y-5 opacity-0'
      }`}
      role="region"
      aria-label="Family add-on upsell"
    >
      <button
        type="button"
        onClick={onDismiss}
        className="absolute right-3 top-3 rounded p-1 text-purple-400 hover:text-purple-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-600"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>

      <div className="pr-8">
        <div className="mb-2 text-2xl" aria-hidden="true">
          🍼
        </div>
        <h3 className="text-base font-semibold text-purple-900">
          You&apos;re expecting — let&apos;s get your finances ready.
        </h3>
        <p className="mt-1 mb-3 text-sm text-purple-800">
          The New Parent Financial Checklist covers the 12 moves most parents miss — including
          time-sensitive windows that can cost thousands if you wait.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={onUpgrade}
            className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            Unlock checklist — $12/month
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-purple-500 underline"
          >
            Maybe later
          </button>
        </div>
      </div>
    </div>
  );
}
