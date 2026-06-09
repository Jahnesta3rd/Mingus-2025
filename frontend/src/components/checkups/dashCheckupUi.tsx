import type { ReactNode } from 'react';

export function StepLabel({ step, total }: { step: number; total: number }) {
  return (
    <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--ink-mid)' }}>
      Question {step + 1} of {total}
    </p>
  );
}

export function StepTitle({ children }: { children: ReactNode }) {
  return <h2 className="font-display text-lg font-semibold leading-snug">{children}</h2>;
}

export function RangeStep({
  label,
  min,
  max,
  value,
  onChange,
  lowLabel,
  highLabel,
}: {
  label: string;
  min: number;
  max: number;
  value: number;
  onChange: (v: number) => void;
  lowLabel: string;
  highLabel: string;
}) {
  return (
    <section className="space-y-4">
      <StepTitle>{label}</StepTitle>
      <div className="flex justify-between text-xs" style={{ color: 'var(--ink-mid)' }}>
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[var(--mingus-purple)]"
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={value}
      />
      <p className="text-center text-sm font-medium">
        {value} / {max}
      </p>
    </section>
  );
}

export function OptionButtons({
  options,
  value,
  onChange,
}: {
  options: readonly { value: string; label: string }[];
  value: string | null;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition ${
            value === opt.value ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)] font-medium' : ''
          }`}
          style={{ borderColor: value === opt.value ? undefined : 'var(--line)' }}
          aria-pressed={value === opt.value}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export function YesNoButtons({
  value,
  onChange,
}: {
  value: boolean | null;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex gap-3">
      {[true, false].map((val) => (
        <button
          key={String(val)}
          type="button"
          onClick={() => onChange(val)}
          className={`min-h-11 flex-1 rounded-xl border px-4 py-3 text-sm font-medium transition ${
            value === val ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)]' : ''
          }`}
          style={{ borderColor: value === val ? undefined : 'var(--line)' }}
          aria-pressed={value === val}
        >
          {val ? 'Yes' : 'No'}
        </button>
      ))}
    </div>
  );
}

export function MultiSelectChips({
  options,
  selected,
  onToggle,
}: {
  options: readonly string[];
  selected: string[];
  onToggle: (label: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((label) => {
        const active = selected.includes(label);
        return (
          <button
            key={label}
            type="button"
            onClick={() => onToggle(label)}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              active ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)] font-medium' : ''
            }`}
            style={{ borderColor: active ? undefined : 'var(--line)' }}
            aria-pressed={active}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

export function StepNav({
  step,
  busy,
  canAdvance,
  onBack,
  onNext,
  isLast,
}: {
  step: number;
  busy: boolean;
  canAdvance: boolean;
  onBack: () => void;
  onNext: () => void;
  isLast: boolean;
}) {
  return (
    <div className="flex gap-3 pt-2">
      {step > 0 ? (
        <button
          type="button"
          onClick={onBack}
          disabled={busy}
          className="min-h-11 flex-1 rounded-xl border px-4 py-3 text-sm font-medium"
          style={{ borderColor: 'var(--line)' }}
        >
          Back
        </button>
      ) : null}
      <button
        type="button"
        onClick={onNext}
        disabled={busy || !canAdvance}
        className="dash-checkup-primary min-h-11 flex-1 rounded-xl px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"
        style={{ background: 'var(--mingus-purple)' }}
      >
        {busy ? 'Saving…' : isLast ? 'Save check-in' : 'Continue'}
      </button>
    </div>
  );
}
