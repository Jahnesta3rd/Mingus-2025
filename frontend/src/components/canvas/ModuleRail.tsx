import type { ReactNode } from 'react';
import { CheckCircle2, SkipForward } from 'lucide-react';
import type { ModuleId, OnboardingState } from '../../types/modularOnboarding';
import { MODULE_ORDER } from '../../types/modularOnboarding';

export interface ModuleRailProps {
  modules: OnboardingState['modules'];
  currentModule: ModuleId | null;
  progressPct: number;
  completedCount: number;
  onJumpTo: (moduleId: ModuleId) => void;
}

function pillStateClasses(
  id: ModuleId,
  currentModule: ModuleId | null,
  status: OnboardingState['modules'][ModuleId]['status']
): string {
  const isActive =
    id === currentModule &&
    (status === 'active' || status === 'in_progress');
  if (isActive) {
    return 'bg-purple-100 text-purple-800 border-purple-400 ring-2 ring-purple-200';
  }
  if (status === 'complete') {
    return 'bg-green-100 text-green-800 border-green-400';
  }
  if (status === 'skipped') {
    return 'bg-amber-50 text-amber-700 border-amber-300';
  }
  return 'bg-slate-100 text-slate-500 border-slate-200';
}

export function ModuleRail({
  modules,
  currentModule,
  progressPct,
  completedCount,
  onJumpTo,
}: ModuleRailProps) {
  return (
    <div>
      <div className="overflow-x-auto pb-2">
        <div className="flex gap-2 min-w-max">
          {MODULE_ORDER.map((id) => {
            const st = modules[id].status;
            const isActive =
              id === currentModule &&
              (st === 'active' || st === 'in_progress');
            const stateClasses = pillStateClasses(id, currentModule, st);
            const displayName = modules[id].display_name;
            let icon: ReactNode = null;
            if (st === 'complete') {
              icon = (
                <CheckCircle2
                  size={14}
                  className="shrink-0 text-green-800"
                  aria-hidden
                />
              );
            } else if (st === 'skipped') {
              icon = (
                <SkipForward
                  size={14}
                  className="shrink-0 text-amber-700"
                  aria-hidden
                />
              );
            } else if (isActive) {
              icon = (
                <span
                  className="inline-block h-2 w-2 shrink-0 rounded-full bg-purple-800 animate-pulse"
                  aria-hidden
                />
              );
            }
            return (
              <button
                key={id}
                type="button"
                onClick={isActive ? undefined : () => onJumpTo(id)}
                disabled={isActive}
                className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full border font-medium text-sm whitespace-nowrap transition-colors ${stateClasses} ${
                  isActive
                    ? 'cursor-default'
                    : 'cursor-pointer hover:opacity-80'
                }`}
              >
                {icon}
                {displayName}
              </button>
            );
          })}
        </div>
      </div>
      <div className="mt-3">
        <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#5B2D8E] transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className="mt-1 text-xs text-slate-500">
          {completedCount} of 7 done
        </div>
      </div>
    </div>
  );
}
