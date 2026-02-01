import React from 'react';

const QUICK_AMOUNTS = [25, 50, 100, 150, 200] as const;

export interface SpendingInputProps {
  value: number | null;
  onChange: (value: number | null) => void;
  label: string;
  id: string;
  placeholder?: string;
  baselineHint?: number | null;
  showSkip?: boolean;
  quickAmounts?: readonly number[];
  className?: string;
}

/**
 * Currency input with quick-select buttons and optional baseline hint.
 * Null/skip = "I don't know"; 0 = valid $0. Large touch targets, accessible.
 */
export const SpendingInput: React.FC<SpendingInputProps> = ({
  value,
  onChange,
  label,
  id,
  placeholder = '~$100',
  baselineHint = null,
  showSkip = true,
  quickAmounts = QUICK_AMOUNTS,
  className = '',
}) => {
  const displayValue = value != null && !Number.isNaN(value) ? String(value) : '';

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9.]/g, '');
    if (raw === '') {
      onChange(null);
      return;
    }
    const n = parseFloat(raw);
    if (!Number.isNaN(n) && n >= 0) onChange(n);
  };

  const effectivePlaceholder = baselineHint != null && baselineHint > 0
    ? `Your avg: $${Math.round(baselineHint)}`
    : placeholder;

  return (
    <div className={`space-y-2 ${className}`}>
      <label htmlFor={id} className="block text-slate-200 font-medium">
        {label}
      </label>
      <div className="flex flex-wrap gap-2 items-center">
        {showSkip && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className={`
              min-h-[44px] px-3 rounded-xl text-sm font-medium
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
              ${value === null && displayValue === ''
                ? 'bg-violet-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }
            `}
            aria-pressed={value === null && displayValue === ''}
          >
            Skip
          </button>
        )}
        {quickAmounts.map((amt) => {
          const isSelected = value === amt;
          return (
            <button
              key={amt}
              type="button"
              onClick={() => onChange(amt)}
              className={`
                min-h-[44px] px-3 rounded-xl text-sm font-semibold
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
                ${isSelected
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }
              `}
              aria-pressed={isSelected}
              aria-label={`About $${amt}`}
            >
              ~${amt}
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => onChange(200)}
          className="
            min-h-[44px] px-3 rounded-xl text-sm font-semibold bg-slate-700 text-slate-300 hover:bg-slate-600
            focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
          "
          aria-label="About $200 or more"
        >
          ~$200+
        </button>
      </div>
      <input
        id={id}
        type="text"
        inputMode="decimal"
        placeholder={effectivePlaceholder}
        value={displayValue}
        onChange={handleInputChange}
        className="w-full min-h-[44px] px-4 rounded-xl bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
        aria-label={`${label} in dollars`}
      />
    </div>
  );
};

export default SpendingInput;
