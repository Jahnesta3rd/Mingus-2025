import React from 'react';

export type MoodValue = 'great' | 'okay' | 'meh';

export interface MoodButtonProps {
  emoji: string;
  label: string;
  value: MoodValue;
  selected: boolean;
  onSelect: () => void;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Emoji mood selector: "How do you feel about it?"
 * Large touch target, clear selected state.
 */
export const MoodButton: React.FC<MoodButtonProps> = ({
  emoji,
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
      aria-label={ariaLabel ?? `${emoji} ${label}${selected ? ' (selected)' : ''}`}
      className={`
        min-h-[48px] min-w-[80px] px-4 py-3 rounded-xl
        flex flex-col items-center justify-center gap-1
        text-base font-semibold
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
      <span className="text-2xl leading-none" aria-hidden>
        {emoji}
      </span>
      <span>{label}</span>
    </button>
  );
};

export default MoodButton;
