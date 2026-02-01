import React from 'react';

export interface EmojiOption {
  emoji: string;
  value: number;
  label?: string;
}

export interface EmojiSelectorProps {
  options: EmojiOption[];
  value: number | null;
  onChange: (value: number) => void;
  label: string;
  id?: string;
  ariaLabel?: string;
  className?: string;
}

/**
 * Row of emoji buttons for selecting a single value (e.g. mood 2,4,6,8,10).
 * Large touch targets (min 44px), accessible.
 */
export const EmojiSelector: React.FC<EmojiSelectorProps> = ({
  options,
  value,
  onChange,
  label,
  id = 'emoji-selector',
  ariaLabel,
  className = '',
}) => {
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
        {options.map((opt) => {
          const isSelected = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={isSelected}
              aria-label={opt.label || `${opt.emoji} (${opt.value})`}
              onClick={() => onChange(opt.value)}
              className={`
                min-h-[44px] min-w-[44px] rounded-xl text-2xl font-medium
                transition-all duration-200 flex items-center justify-center
                focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
                ${isSelected
                  ? 'bg-violet-600 text-white ring-2 ring-violet-400 scale-105'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
                }
              `}
            >
              {opt.emoji}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default EmojiSelector;
