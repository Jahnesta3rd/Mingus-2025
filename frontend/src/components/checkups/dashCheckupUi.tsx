import type { ReactNode } from 'react';

export function QuestionLabel({ children }: { children: ReactNode }) {
  return (
    <p
      className="text-[15px] font-medium leading-snug"
      style={{ color: 'var(--ink)', fontFamily: 'Manrope, system-ui, sans-serif' }}
    >
      {children}
    </p>
  );
}

export function SkipLink({ onClick, children = 'Skip' }: { onClick: () => void; children?: string }) {
  return (
    <div className="flex justify-end">
      <button
        type="button"
        onClick={onClick}
        className="text-[13px] underline-offset-2 hover:underline"
        style={{ color: 'var(--ink-mid)', fontFamily: 'Manrope, system-ui, sans-serif' }}
      >
        {children}
      </button>
    </div>
  );
}

export function CheckupQuestionBlock({
  children,
  conditional = false,
}: {
  children: ReactNode;
  conditional?: boolean;
}) {
  return (
    <section className={`space-y-3 ${conditional ? 'checkup-conditional-enter' : ''}`}>{children}</section>
  );
}

export function CheckupForm({ children }: { children: ReactNode }) {
  return <div className="flex flex-col gap-6">{children}</div>;
}

export function SubmitButton({
  busy,
  disabled,
  onClick,
  label = 'Submit',
}: {
  busy?: boolean;
  disabled?: boolean;
  onClick: () => void;
  label?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy || disabled}
      className="dash-checkup-primary mt-2 min-h-11 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"
      style={{ background: 'var(--mingus-purple)' }}
    >
      {busy ? 'Saving…' : label}
    </button>
  );
}

export function ScaleButtons({
  min,
  max,
  value,
  onChange,
  labels,
}: {
  min: number;
  max: number;
  value: number;
  onChange: (v: number) => void;
  labels?: Record<number, string>;
}) {
  const options = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {options.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            className={`min-h-11 min-w-[2.75rem] flex-1 rounded-xl border px-3 py-2 text-sm font-medium transition ${
              value === n ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)]' : ''
            }`}
            style={{ borderColor: value === n ? undefined : 'var(--line)' }}
            aria-pressed={value === n}
          >
            {n}
          </button>
        ))}
      </div>
      {labels ? (
        <div className="flex justify-between text-xs" style={{ color: 'var(--ink-mid)' }}>
          <span>{labels[min] ?? ''}</span>
          <span>{labels[max] ?? ''}</span>
        </div>
      ) : null}
    </div>
  );
}

export function EmojiMoodPicker({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  const moods = [
    { v: 1, emoji: '😔' },
    { v: 2, emoji: '😟' },
    { v: 3, emoji: '😐' },
    { v: 4, emoji: '🙂' },
    { v: 5, emoji: '😄' },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {moods.map(({ v, emoji }) => (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          className={`min-h-12 min-w-12 flex-1 rounded-xl border text-2xl transition ${
            value === v ? 'border-[var(--mingus-purple)] bg-[var(--soft-purple)]' : ''
          }`}
          style={{ borderColor: value === v ? undefined : 'var(--line)' }}
          aria-pressed={value === v}
          aria-label={`Mood ${v}`}
        >
          {emoji}
        </button>
      ))}
    </div>
  );
}

export function NumericStepper({
  value,
  onChange,
  min,
  max,
  step = 1,
}: {
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step?: number;
}) {
  const dec = () => onChange(Math.max(min, value - step));
  const inc = () => onChange(Math.min(max, value + step));
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={dec}
        disabled={value <= min}
        className="min-h-11 min-w-11 rounded-xl border text-lg font-semibold disabled:opacity-40"
        style={{ borderColor: 'var(--line)' }}
        aria-label="Decrease"
      >
        −
      </button>
      <span className="min-w-[3rem] text-center text-lg font-semibold">{value}</span>
      <button
        type="button"
        onClick={inc}
        disabled={value >= max}
        className="min-h-11 min-w-11 rounded-xl border text-lg font-semibold disabled:opacity-40"
        style={{ borderColor: 'var(--line)' }}
        aria-label="Increase"
      >
        +
      </button>
    </div>
  );
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
    <CheckupQuestionBlock>
      <QuestionLabel>{label}</QuestionLabel>
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
    </CheckupQuestionBlock>
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

export function DollarInput({
  value,
  onChange,
  placeholder = 'Amount in dollars',
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  id?: string;
}) {
  return (
    <input
      id={id}
      type="number"
      min={0}
      step={1}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-xl border px-4 py-3 text-sm"
      style={{ borderColor: 'var(--line)' }}
    />
  );
}

export function TextInput({
  value,
  onChange,
  placeholder,
  id,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  id?: string;
}) {
  return (
    <input
      id={id}
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-xl border px-4 py-3 text-sm"
      style={{ borderColor: 'var(--line)' }}
    />
  );
}
