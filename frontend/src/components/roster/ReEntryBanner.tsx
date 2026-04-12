import { useEffect, useRef, useState } from 'react';
import { connectionTrendFadeTierLabel } from './ConnectionTrendBadge';

export interface ReEntryBannerProps {
  nickname: string;
  reEntryType: 'zombie' | 'submarine';
  previousFadeTier: string;
  previousScore: number | null;
  daysSinceLast: number;
  onDismiss: () => void;
}

export default function ReEntryBanner({
  nickname,
  reEntryType,
  previousFadeTier,
  previousScore,
  daysSinceLast,
  onDismiss,
}: ReEntryBannerProps) {
  void previousScore;
  const [visible, setVisible] = useState(true);
  const onDismissRef = useRef(onDismiss);
  onDismissRef.current = onDismiss;

  useEffect(() => {
    if (!visible) return;
    const t = window.setTimeout(() => {
      setVisible(false);
      onDismissRef.current();
    }, 10000);
    return () => window.clearTimeout(t);
  }, [visible]);

  if (!visible) return null;

  const tierLabel =
    previousFadeTier.trim().length > 0
      ? connectionTrendFadeTierLabel(previousFadeTier)
      : 'an earlier point on the Fade Scale';

  const closing = ' Based on your responses. Trust your instincts.';

  const dismiss = () => {
    setVisible(false);
    onDismiss();
  };

  if (reEntryType === 'zombie') {
    return (
      <div
        className="relative mb-3 rounded-xl px-4 py-3 pr-10 text-sm leading-relaxed text-white shadow-sm"
        style={{ backgroundColor: '#1F2937' }}
        role="status"
      >
        <button
          type="button"
          onClick={dismiss}
          className="absolute right-2 top-2 flex min-h-11 min-w-11 items-center justify-center rounded-lg text-lg leading-none text-white/80 transition hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[#1F2937]"
          aria-label="Dismiss"
        >
          ×
        </button>
        <p className="font-medium">
          🧟 {nickname} is back after {daysSinceLast} {daysSinceLast === 1 ? 'day' : 'days'}.
        </p>
        <p className="mt-1 text-white/90">
          Their last Connection Trend score was {tierLabel}. Worth noting where things pick up.
        </p>
        <p className="mt-2 text-sm text-white/70">{closing.trim()}</p>
      </div>
    );
  }

  return (
    <div
      className="relative mb-3 rounded-xl px-4 py-3 pr-10 text-sm leading-relaxed shadow-sm"
      style={{ backgroundColor: '#DBEAFE', color: '#1e3a8a' }}
      role="status"
    >
      <button
        type="button"
        onClick={dismiss}
        className="absolute right-2 top-2 flex min-h-11 min-w-11 items-center justify-center rounded-lg text-lg leading-none text-[#1e3a8a]/70 transition hover:bg-blue-200/60 hover:text-[#1e3a8a] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        aria-label="Dismiss"
      >
        ×
      </button>
      <p className="font-medium">🌊 You&apos;ve tracked {nickname} before.</p>
      <p className="mt-1">
        They were at {tierLabel} last time. This round starts fresh — but the pattern is in your
        history.
      </p>
      <p className="mt-2 text-sm opacity-90">{closing.trim()}</p>
    </div>
  );
}
