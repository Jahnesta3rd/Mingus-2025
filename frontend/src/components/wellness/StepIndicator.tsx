import React from 'react';

export interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  ariaLabel?: string;
  className?: string;
}

/**
 * Progress indicator for multi-step forms.
 * Shows "Step X of Y" and a progress bar. Accessible and keyboard-friendly.
 */
export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  totalSteps,
  ariaLabel = `Step ${currentStep} of ${totalSteps}`,
  className = '',
}) => {
  const progressPercent = totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0;

  return (
    <div
      className={`flex flex-col gap-2 ${className}`}
      role="progressbar"
      aria-valuenow={currentStep}
      aria-valuemin={1}
      aria-valuemax={totalSteps}
      aria-label={ariaLabel}
    >
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-300 font-medium">
          Step {currentStep} of {totalSteps}
        </span>
        <span className="text-violet-400 font-semibold">
          {Math.round(progressPercent)}%
        </span>
      </div>
      <div
        className="h-2 w-full bg-slate-700 rounded-full overflow-hidden"
        aria-hidden="true"
      >
        <div
          className="h-full bg-violet-500 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
};

export default StepIndicator;
