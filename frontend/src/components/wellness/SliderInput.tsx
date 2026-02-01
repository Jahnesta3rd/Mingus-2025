import React, { useCallback } from 'react';

export interface SliderInputProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  leftEmoji?: string;
  rightEmoji?: string;
  label: string;
  id: string;
  ariaLabel?: string;
  className?: string;
}

/**
 * Reusable 1-10 slider with emoji endpoints. Large touch target, accessible.
 */
export const SliderInput: React.FC<SliderInputProps> = ({
  value,
  onChange,
  min = 1,
  max = 10,
  leftEmoji = '😫',
  rightEmoji = '😴',
  label,
  id,
  ariaLabel,
  className = '',
}) => {
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = parseInt(e.target.value, 10);
      if (!Number.isNaN(v)) onChange(v);
    },
    [onChange]
  );

  return (
    <div className={`space-y-3 ${className}`}>
      <label htmlFor={id} className="block text-slate-200 font-medium">
        {label}
      </label>
      <div className="flex items-center gap-3">
        <span className="text-2xl select-none" aria-hidden="true">
          {leftEmoji}
        </span>
        <input
          id={id}
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={handleChange}
          className="flex-1 h-12 accent-violet-500 min-w-0 touch-none"
          style={{ minHeight: '44px' }}
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={value}
          aria-label={ariaLabel || label}
        />
        <span className="text-2xl select-none" aria-hidden="true">
          {rightEmoji}
        </span>
      </div>
      <div className="flex justify-between text-xs text-slate-400">
        <span>{min}</span>
        <span aria-live="polite">{value}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};

export default SliderInput;
