import React from 'react';
import { SpendingInput } from './SpendingInput';

export interface SpendingCategoryProps {
  id: string;
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  baselineHint?: number | null;
  placeholder?: string;
  className?: string;
}

/**
 * Single spending category row: label + SpendingInput with quick amounts and baseline hint.
 */
export const SpendingCategory: React.FC<SpendingCategoryProps> = ({
  id,
  label,
  value,
  onChange,
  baselineHint = null,
  placeholder,
  className = '',
}) => {
  return (
    <div className={className}>
      <SpendingInput
        id={id}
        label={label}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        baselineHint={baselineHint}
        showSkip={true}
      />
    </div>
  );
};

export default SpendingCategory;
