import { StepShell } from '../StepShell';
import type { StepProps } from '../StepDefinitions';

export function PlaceholderStep({ stepLabel, onSubmit }: StepProps) {
  return (
    <StepShell
      heading={`${stepLabel} — coming soon`}
      description={`This step will collect your ${stepLabel.toLowerCase()} details. Implementation in progress.`}
    >
      <button
        type="button"
        className="min-h-11 rounded-lg border border-[#5B2D8E] px-4 py-2 text-sm font-medium text-[#5B2D8E] transition hover:bg-[#F5F0FB]"
        onClick={() => void onSubmit({})}
      >
        Skip step (placeholder)
      </button>
    </StepShell>
  );
}
