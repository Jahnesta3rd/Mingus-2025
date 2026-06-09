export function RenewalPrompt({
  variant,
  open,
  onDismiss,
}: {
  variant: 'renewal' | 'increased';
  open: boolean;
  onDismiss: () => void;
}) {
  if (!open) return null;

  const title = variant === 'renewal' ? 'Renewal window open' : 'Housing cost increased';
  const body =
    variant === 'renewal'
      ? 'Your lease is coming up for renewal within three months. Compare stay vs. move costs before you sign.'
      : 'Your housing costs rose recently. Check your waterfall to see how that change affects your monthly surplus.';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="renewal-title"
    >
      <div
        className="w-full max-w-sm rounded-2xl border bg-white p-6 shadow-lg"
        style={{ borderColor: 'var(--line)' }}
      >
        <h2 id="renewal-title" className="font-display text-lg font-semibold">
          {title}
        </h2>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--ink-mid)' }}>
          {body}
        </p>
        <button
          type="button"
          onClick={onDismiss}
          className="dash-checkup-primary mt-6 min-h-11 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white"
          style={{ background: 'var(--mingus-purple)' }}
        >
          Got it
        </button>
      </div>
    </div>
  );
}
