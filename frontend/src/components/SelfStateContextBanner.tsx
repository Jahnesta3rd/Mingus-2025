import { useCallback, useState } from 'react';

const SESSION_DISMISS_KEY = 'vibe_checkups_self_context_banner_dismissed';

export interface SelfStateContextBannerProps {
  selfScore: number;
  mindScore: number;
  mindTrend: string;
}

function isDecliningTrend(mindTrend: string): boolean {
  return mindTrend === 'declining' || mindTrend === 'down';
}

export default function SelfStateContextBanner({
  selfScore,
  mindScore,
  mindTrend,
}: SelfStateContextBannerProps) {
  const [dismissed, setDismissed] = useState(() => {
    if (typeof sessionStorage === 'undefined') return false;
    return sessionStorage.getItem(SESSION_DISMISS_KEY) === '1';
  });

  const declining = isDecliningTrend(mindTrend);
  const lowMindNotDeclining = mindScore < 50 && !declining;

  if (!declining && !lowMindNotDeclining) {
    return null;
  }

  if (dismissed) {
    return null;
  }

  const onDismiss = useCallback(() => {
    sessionStorage.setItem(SESSION_DISMISS_KEY, '1');
    setDismissed(true);
  }, []);

  const isAmber = declining;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Self wellbeing context, overall score ${selfScore}`}
      className={`mb-5 rounded-xl border px-4 py-3 text-left text-sm leading-relaxed ${
        isAmber
          ? 'border-amber-200/80 bg-amber-50 text-amber-700'
          : 'border-blue-200/80 bg-blue-50 text-blue-700'
      }`}
    >
      <div className="flex gap-3">
        <span className="shrink-0 text-lg leading-none" aria-hidden>
          {isAmber ? '⚠️' : 'ℹ️'}
        </span>
        <div className="min-w-0 flex-1">
          <p>
            {isAmber
              ? 'Your stress levels have been elevated lately. Your checkup reflects how you see things right now — including your current state. Just something to keep in mind.'
              : "Your recent check-ins show some pressure in your week. That's real — and it's okay. Your responses here are still valuable data."}
          </p>
          <button
            type="button"
            onClick={onDismiss}
            className="mt-3 min-h-11 rounded-lg font-medium underline underline-offset-2 transition hover:opacity-80"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
