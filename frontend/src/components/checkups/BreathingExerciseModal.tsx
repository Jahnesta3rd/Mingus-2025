import { useEffect, useState } from 'react';

export function BreathingExerciseModal({
  open,
  onComplete,
}: {
  open: boolean;
  onComplete: () => void;
}) {
  const [phase, setPhase] = useState<'inhale' | 'hold' | 'exhale'>('inhale');

  useEffect(() => {
    if (!open) return;
    setPhase('inhale');
    const timers = [
      window.setTimeout(() => setPhase('hold'), 4000),
      window.setTimeout(() => setPhase('exhale'), 6000),
    ];
    return () => timers.forEach(clearTimeout);
  }, [open]);

  if (!open) return null;

  const label =
    phase === 'inhale' ? 'Breathe in…' : phase === 'hold' ? 'Hold…' : 'Breathe out…';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="breathing-title"
    >
      <div
        className="w-full max-w-sm rounded-2xl border bg-white p-6 shadow-lg"
        style={{ borderColor: 'var(--line)' }}
      >
        <h2 id="breathing-title" className="font-display text-lg font-semibold">
          Take a moment
        </h2>
        <p className="mt-2 text-sm" style={{ color: 'var(--ink-mid)' }}>
          Financial anxiety is real. A few slow breaths can help before you move on.
        </p>
        <p className="mt-6 text-center text-base font-medium" style={{ color: 'var(--mingus-purple)' }}>
          {label}
        </p>
        <button
          type="button"
          onClick={onComplete}
          className="dash-checkup-primary mt-6 min-h-11 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white"
          style={{ background: 'var(--mingus-purple)' }}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
