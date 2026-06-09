export function StayOrGoPrompt({
  open,
  personName,
  onDismiss,
}: {
  open: boolean;
  personName: string;
  onDismiss: () => void;
}) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="stay-or-go-title"
    >
      <div
        className="w-full max-w-sm rounded-2xl border bg-white p-6 shadow-lg"
        style={{ borderColor: 'var(--line)' }}
      >
        <h2 id="stay-or-go-title" className="font-display text-lg font-semibold">
          Direction check
        </h2>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--ink-mid)' }}>
          Your last few check-ins with {personName} show uncertainty about where this relationship
          is heading. It may be worth a deeper conversation — or a look at what this connection
          costs you over time.
        </p>
        <button
          type="button"
          onClick={onDismiss}
          className="dash-checkup-primary mt-6 min-h-11 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white"
          style={{ background: 'var(--mingus-purple)' }}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
