import React from 'react';

export type NumberOption = number | { label: string; value: number };

export interface NumberSelectorProps {
  options: NumberOption[];
  value: number | null;
  onChange: (value: number) => void;
  label: string;
  id?: string;
  ariaLabel?: string;
  className?: string;
}

function normalizeOption(opt: NumberOption): { label: string; value: number } {
  if (typeof opt === 'number') return { label: String(opt), value: opt };
  return opt;
}

/**
 * Row of number/range buttons (e.g. 0-7 days, or "0", "15", "30" minutes).
 * Large touch targets (min 44px), accessible.
 */
export const NumberSelector: React.FC<NumberSelectorProps> = ({
  options,
  value,
  onChange,
  label,
  id = 'number-selector',
  ariaLabel,
  className = '',
}) => {
  const normalized = options.map(normalizeOption);

  return (
    <div className={`space-y-3 ${className}`} role="group" aria-label={ariaLabel || label}>
      <div className="text-slate-200 font-medium" id={`${id}-label`}>
        {label}
      </div>
      <div
        className="flex flex-wrap gap-2"
        role="radiogroup"
        aria-labelledby={`${id}-label`}
      >
        {normalized.map((opt) => {
          const isSelected = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={isSelected}
              aria-label={opt.label}
              onClick={() => onChange(opt.value)}
              className={`
                min-h-[44px] px-4 rounded-xl text-base font-semibold
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
                ${isSelected
                  ? 'bg-violet-600 text-white ring-2 ring-violet-400'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
                }
              `}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default NumberSelector;
