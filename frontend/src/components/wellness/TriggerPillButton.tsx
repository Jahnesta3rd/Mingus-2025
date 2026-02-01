import React from 'react';

export type TriggerValue =
  | 'planned'
  | 'needed'
  | 'impulse'
  | 'treat'
  | 'stressed'
  | 'bored';

export interface TriggerPillButtonProps {
  label: string;
  value: TriggerValue;
  selected: boolean;
  onSelect: () => void;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Single trigger option pill: "Why did you buy this?"
 * Large touch target, clear selected state.
 */
export const TriggerPillButton: React.FC<TriggerPillButtonProps> = ({
  label,
  value,
  selected,
  onSelect,
  className = '',
  ariaLabel,
}) => {
  return (
    <button
      type="button"
      onClick={onSelect}
      value={value}
      aria-pressed={selected}
      aria-label={ariaLabel ?? `${label}${selected ? ' (selected)' : ''}`}
      className={`
        min-h-[44px] px-4 py-2.5 rounded-full text-sm font-semibold
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
        active:scale-[0.98]
        ${selected
          ? 'bg-violet-600 text-white ring-2 ring-violet-400'
          : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-slate-100'
        }
        ${className}
      `}
    >
      {label}
    </button>
  );
};

export default TriggerPillButton;
