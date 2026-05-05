interface ProgressIndicatorProps {
  currentIndex: number;
  total: number;
  stepLabel: string;
}

export function ProgressIndicator({ currentIndex, total, stepLabel }: ProgressIndicatorProps) {
  const clampedCurrent = Math.max(0, Math.min(currentIndex, total - 1));
  const valueNow = clampedCurrent + 1;
  const progressPct = total > 0 ? Math.round(((clampedCurrent + 1) / total) * 100) : 0;

  return (
    <div
      className="w-full"
      role="progressbar"
      aria-valuenow={valueNow}
      aria-valuemin={1}
      aria-valuemax={Math.max(total, 1)}
      aria-label={`Onboarding progress: step ${valueNow} of ${total}`}
    >
      <div className="hidden md:block">
        <div className="flex items-center justify-between gap-2">
          {Array.from({ length: total }).map((_, idx) => {
            const isCurrent = idx === clampedCurrent;
            const isCompleted = idx < clampedCurrent;
            const className = isCurrent
              ? 'bg-[#5B2D8E] border-[#5B2D8E]'
              : isCompleted
                ? 'bg-[#8A67B3] border-[#8A67B3]'
                : 'bg-white border-[#6B7280]';
            return (
              <span
                key={idx}
                className={`h-4 w-4 rounded-full border-2 ${className}`}
                aria-hidden="true"
              />
            );
          })}
        </div>
      </div>

      <div className="md:hidden">
        <p className="text-sm font-medium text-slate-900">
          Step {valueNow} of {total}: {stepLabel}
        </p>
        <div className="mt-2 h-1.5 w-full rounded-full bg-slate-200" aria-hidden="true">
          <div
            className="h-1.5 rounded-full bg-[#5B2D8E] transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
