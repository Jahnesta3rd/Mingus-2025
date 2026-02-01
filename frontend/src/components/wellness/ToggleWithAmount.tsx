import React from 'react';

export interface ToggleWithAmountProps {
  label: string;
  isYes: boolean;
  amount: number | null;
  onToggle: (isYes: boolean) => void;
  onAmountChange: (value: number | null) => void;
  id?: string;
  currencyLabel?: string;
  placeholder?: string;
  className?: string;
}

/**
 * Yes/No toggle that reveals an amount input when Yes is selected.
 * Large touch targets, accessible.
 */
export const ToggleWithAmount: React.FC<ToggleWithAmountProps> = ({
  label,
  isYes,
  amount,
  onToggle,
  onAmountChange,
  id = 'toggle-amount',
  currencyLabel = 'Amount ($)',
  placeholder = '0',
  className = '',
}) => {
  const yesId = `${id}-yes`;
  const noId = `${id}-no`;
  const amountId = `${id}-amount`;

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9.]/g, '');
    if (raw === '') {
      onAmountChange(null);
      return;
    }
    const n = parseFloat(raw);
    if (!Number.isNaN(n) && n >= 0) onAmountChange(n);
  };

  const displayAmount = amount != null && !Number.isNaN(amount) ? String(amount) : '';

  return (
    <div className={`space-y-3 ${className}`} role="group" aria-label={label}>
      <div className="text-slate-200 font-medium">{label}</div>
      <div className="flex gap-2">
        <button
          type="button"
          id={noId}
          role="radio"
          aria-checked={!isYes}
          aria-label="No"
          onClick={() => {
            onToggle(false);
            onAmountChange(null);
          }}
          className={`
            min-h-[44px] flex-1 rounded-xl text-base font-semibold
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
            ${!isYes
              ? 'bg-violet-600 text-white ring-2 ring-violet-400'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }
          `}
        >
          No
        </button>
        <button
          type="button"
          id={yesId}
          role="radio"
          aria-checked={isYes}
          aria-label="Yes, about $___"
          onClick={() => onToggle(true)}
          className={`
            min-h-[44px] flex-1 rounded-xl text-base font-semibold
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
            ${isYes
              ? 'bg-violet-600 text-white ring-2 ring-violet-400'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }
          `}
        >
          Yes, about $___
        </button>
      </div>
      {isYes && (
        <div className="animate-fade-in-up">
          <label htmlFor={amountId} className="sr-only">
            {currencyLabel}
          </label>
          <input
            id={amountId}
            type="text"
            inputMode="decimal"
            placeholder={placeholder}
            value={displayAmount}
            onChange={handleAmountChange}
            className="w-full min-h-[44px] px-4 rounded-xl bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20"
            aria-label={currencyLabel}
          />
        </div>
      )}
    </div>
  );
};

export default ToggleWithAmount;
